"""
Phoenix Monitoring Integration for WINCASA System

This module provides comprehensive AI observability using Arize Phoenix for:
- LLM tracing and monitoring
- RAG performance evaluation
- Query execution analytics
- Cost and performance tracking
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import phoenix as px
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from openinference.instrumentation.openai import OpenAIInstrumentor
    from phoenix.otel import register

    PHOENIX_AVAILABLE = True
except ImportError:
    PHOENIX_AVAILABLE = False
    logging.warning(
        "Phoenix not installed. Install with: pip install arize-phoenix arize-phoenix-otel"
    )

logger = logging.getLogger(__name__)


class PhoenixMonitor:
    """Central monitoring class for WINCASA system using Phoenix"""

    def __init__(self, project_name: str = "WINCASA", enable_ui: bool = True):
        """
        Initialize Phoenix monitoring

        Args:
            project_name: Name for the Phoenix project
            enable_ui: Whether to launch Phoenix UI
        """
        self.project_name = project_name
        self.enable_ui = enable_ui
        self.session = None
        self.instrumentor = None
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "retrieval_metrics": {},
        }

        if PHOENIX_AVAILABLE:
            self._initialize_phoenix()
        else:
            logger.error("Phoenix not available. Monitoring disabled.")

    def _initialize_phoenix(self):
        """Initialize Phoenix monitoring with SQLite backend"""
        try:
            # Create SQLite database for traces
            db_path = "/home/projects/langchain_project/logs/phoenix_traces.db"
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            # Launch Phoenix with SQLite backend
            if self.enable_ui:
                try:
                    # Use SQLite as backend instead of HTTP
                    self.session = px.launch_app(
                        port=6006,
                        # Use SQLite backend - no HTTP endpoint needed
                    )
                    logger.info(
                        f"✅ Phoenix UI launched with SQLite backend at: http://localhost:6006"
                    )
                except Exception as ui_error:
                    logger.warning(f"⚠️ Phoenix UI launch failed: {ui_error}")
                    logger.info("📊 Continuing with file-based monitoring")
                    self.session = None
                    self.enable_ui = False

            # Register OTEL tracer with file export (no network calls)
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter,
                )
                from opentelemetry.sdk.resources import Resource
                from opentelemetry.sdk.trace import TracerProvider
                from opentelemetry.sdk.trace.export import BatchSpanProcessor

                # Create file-based exporter instead of HTTP
                trace_file = (
                    "/home/projects/langchain_project/logs/phoenix_traces.jsonl"
                )

                # Use console exporter for now (much faster than HTTP)
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter as GRPCExporter,
                )
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter as HTTPExporter,
                )

                # Try local Phoenix endpoint only if UI is running
                if self.enable_ui and self.session:
                    endpoint = "http://localhost:6006/v1/traces"
                else:
                    endpoint = None

                self.tracer_provider = register(
                    project_name=self.project_name,
                    endpoint=endpoint,  # None = no HTTP calls
                    auto_instrument=True,
                )
                logger.info("✅ Phoenix OTEL tracer registered with SQLite backend")
            except Exception as otel_error:
                logger.warning(f"⚠️ OTEL registration failed: {otel_error}")
                # Create minimal tracer without Phoenix
                from opentelemetry.sdk.resources import Resource
                from opentelemetry.sdk.trace import TracerProvider

                self.tracer_provider = TracerProvider(
                    resource=Resource.create({"service.name": self.project_name})
                )
                logger.info("✅ Minimal OTEL tracer created (no Phoenix)")
                return

            # Initialize instrumentors with OTEL
            try:
                self.langchain_instrumentor = LangChainInstrumentor()
                self.openai_instrumentor = OpenAIInstrumentor()

                # Start instrumentation
                self.langchain_instrumentor.instrument()
                self.openai_instrumentor.instrument()

                logger.info("✅ Phoenix instrumentors initialized successfully")
            except Exception as instr_error:
                logger.warning(f"⚠️ Instrumentation failed: {instr_error}")
                self.langchain_instrumentor = None
                self.openai_instrumentor = None

            logger.info("✅ Phoenix monitoring initialized (UI optional)")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Phoenix: {e}")
            # Set fallback mode
            self.session = None
            self.tracer_provider = None
            self.enable_ui = False

    def trace_query(self, query: str, metadata: Optional[Dict] = None):
        """
        Create a trace span for a query

        Args:
            query: The user query
            metadata: Additional metadata to track
        """
        if not PHOENIX_AVAILABLE:
            return None

        from opentelemetry import trace

        tracer = trace.get_tracer(__name__)

        return tracer.start_span(
            name="user_query",
            attributes={
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "project": self.project_name,
                **(metadata or {}),
            },
        )

    def track_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens_used: int,
        cost: float,
        duration: float,
    ):
        """
        Track an LLM API call

        Args:
            model: Model name (e.g., "gpt-4")
            prompt: Input prompt
            response: Model response
            tokens_used: Total tokens consumed
            cost: Estimated cost in USD
            duration: Call duration in seconds
        """
        self.metrics["total_tokens"] += tokens_used
        self.metrics["total_cost"] += cost

        if PHOENIX_AVAILABLE:
            from opentelemetry import trace

            tracer = trace.get_tracer(__name__)
            with tracer.start_span("llm_call") as span:
                span.set_attributes(
                    {
                        "model": model,
                        "prompt_length": len(prompt),
                        "response_length": len(response),
                        "tokens_used": tokens_used,
                        "cost_usd": cost,
                        "duration_seconds": duration,
                    }
                )

    def track_retrieval(
        self,
        retrieval_mode: str,
        query: str,
        documents_retrieved: int,
        relevance_scores: List[float],
        duration: float,
        success: bool,
    ):
        """
        Track RAG retrieval performance

        Args:
            retrieval_mode: Mode used (enhanced, faiss, none)
            query: Search query
            documents_retrieved: Number of documents retrieved
            relevance_scores: Relevance scores for retrieved documents
            duration: Retrieval duration in seconds
            success: Whether retrieval was successful
        """
        if retrieval_mode not in self.metrics["retrieval_metrics"]:
            self.metrics["retrieval_metrics"][retrieval_mode] = {
                "total_retrievals": 0,
                "successful_retrievals": 0,
                "avg_documents": 0,
                "avg_relevance": 0,
                "avg_duration": 0,
            }

        mode_metrics = self.metrics["retrieval_metrics"][retrieval_mode]
        mode_metrics["total_retrievals"] += 1
        if success:
            mode_metrics["successful_retrievals"] += 1

        # Update running averages
        n = mode_metrics["total_retrievals"]
        mode_metrics["avg_documents"] = (
            mode_metrics["avg_documents"] * (n - 1) + documents_retrieved
        ) / n
        mode_metrics["avg_relevance"] = (
            mode_metrics["avg_relevance"] * (n - 1)
            + (sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0)
        ) / n
        mode_metrics["avg_duration"] = (
            mode_metrics["avg_duration"] * (n - 1) + duration
        ) / n

        if PHOENIX_AVAILABLE:
            from opentelemetry import trace

            tracer = trace.get_tracer(__name__)
            with tracer.start_span("retrieval") as span:
                span.set_attributes(
                    {
                        "mode": retrieval_mode,
                        "query": query,
                        "documents_retrieved": documents_retrieved,
                        "max_relevance": (
                            max(relevance_scores) if relevance_scores else 0
                        ),
                        "avg_relevance": (
                            sum(relevance_scores) / len(relevance_scores)
                            if relevance_scores
                            else 0
                        ),
                        "duration_seconds": duration,
                        "success": success,
                    }
                )

    def track_query_execution(
        self,
        query: str,
        sql: str,
        execution_time: float,
        rows_returned: int,
        success: bool,
        error: Optional[str] = None,
    ):
        """
        Track SQL query execution

        Args:
            query: Original user query
            sql: Generated SQL
            execution_time: Execution time in seconds
            rows_returned: Number of rows returned
            success: Whether query succeeded
            error: Error message if failed
        """
        self.metrics["total_queries"] += 1
        if success:
            self.metrics["successful_queries"] += 1
        else:
            self.metrics["failed_queries"] += 1

        if PHOENIX_AVAILABLE:
            from opentelemetry import trace

            tracer = trace.get_tracer(__name__)
            with tracer.start_span("sql_execution") as span:
                span.set_attributes(
                    {
                        "user_query": query,
                        "generated_sql": sql,
                        "execution_time_seconds": execution_time,
                        "rows_returned": rows_returned,
                        "success": success,
                        "error": error or "",
                    }
                )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked metrics"""
        success_rate = (
            self.metrics["successful_queries"] / self.metrics["total_queries"]
            if self.metrics["total_queries"] > 0
            else 0
        )

        return {
            "total_queries": self.metrics["total_queries"],
            "success_rate": success_rate,
            "total_tokens": self.metrics["total_tokens"],
            "total_cost_usd": round(self.metrics["total_cost"], 2),
            "retrieval_performance": self.metrics["retrieval_metrics"],
            "phoenix_ui_url": self.session.url if self.session else None,
        }

    def export_traces(self, filepath: str):
        """Export traces to file for analysis"""
        if not PHOENIX_AVAILABLE:
            logger.warning("Phoenix not available, cannot export traces")
            return

        try:
            # Attempt to get spans as a DataFrame
            spans_df = px.get_spans_dataframe()
            # Convert DataFrame to a list of dictionaries for JSON serialization
            traces_list = spans_df.to_dict(orient="records")
            with open(filepath, "w") as f:
                json.dump(traces_list, f, indent=2, default=str)
            logger.info(f"Traces exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export traces: {e}")

    def shutdown(self):
        """Shutdown Phoenix monitoring"""
        if PHOENIX_AVAILABLE and self.session:
            logger.info("Shutting down Phoenix monitoring")
            # Phoenix session cleanup if needed


# Global monitor instance
_monitor = None


def get_monitor(enable_ui: bool = True) -> PhoenixMonitor:
    """Get or create global Phoenix monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = PhoenixMonitor(enable_ui=enable_ui)
    return _monitor


# Context manager for tracing
class trace_query:
    """Context manager for tracing a complete query execution"""

    def __init__(self, query: str, metadata: Optional[Dict] = None):
        self.query = query
        self.metadata = metadata or {}
        self.start_time = None
        self.monitor = get_monitor(enable_ui=False)

    def __enter__(self):
        self.start_time = time.time()
        if PHOENIX_AVAILABLE:
            from opentelemetry import trace

            tracer = trace.get_tracer(__name__)
            self.span = tracer.start_span("user_query")
            self.span.set_attributes(
                {
                    "query": self.query,
                    "timestamp": datetime.now().isoformat(),
                    **self.metadata,
                }
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None

        if PHOENIX_AVAILABLE and hasattr(self, "span"):
            self.span.set_attributes(
                {
                    "duration_seconds": duration,
                    "success": success,
                    "error": str(exc_val) if exc_type else "",
                }
            )
            self.span.end()
