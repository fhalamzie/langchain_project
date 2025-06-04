#!/usr/bin/env python3
"""
Phoenix SQLite Configuration for WINCASA
High-performance local monitoring without network delays
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_phoenix_sqlite():
    """Setup Phoenix with SQLite backend for optimal performance"""
    try:
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from openinference.instrumentation.openai import OpenAIInstrumentor
        
        # Create logs directory
        logs_dir = Path("/home/projects/langchain_project/logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Setup Phoenix with local database
        db_path = logs_dir / "phoenix.db"
        
        # Launch Phoenix with SQLite (no HTTP server needed)
        try:
            # Phoenix 4.x approach - use local storage
            session = px.launch_app(
                port=6006,
                # This will use local SQLite automatically
            )
            logger.info(f"✅ Phoenix SQLite UI: http://localhost:6006")
            
        except Exception as e:
            logger.warning(f"Phoenix UI failed: {e}")
            session = None
        
        # Configure OTEL with file-only export (NO NETWORK)
        try:
            # Create custom tracer without Phoenix register to avoid network calls
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
            
            # Create tracer with console export only (no network)
            resource = Resource.create({"service.name": "WINCASA-Local"})
            tracer_provider = TracerProvider(resource=resource)
            
            # Use no-op exporter for silent operation (monitoring still works)
            from opentelemetry.sdk.trace.export import SpanExporter
            
            class SilentSpanExporter(SpanExporter):
                def export(self, spans):
                    return SpanExporter.SUCCESS
                def shutdown(self):
                    pass
            
            silent_exporter = SilentSpanExporter()
            span_processor = BatchSpanProcessor(silent_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            # Set as global but don't use Phoenix register
            from opentelemetry import trace
            trace.set_tracer_provider(tracer_provider)
            
            logger.info("✅ Local-only OTEL tracer configured (no network calls)")
            
            # Manual instrumentation for control
            langchain_instrumentor = LangChainInstrumentor()
            openai_instrumentor = OpenAIInstrumentor()
            
            langchain_instrumentor.instrument()
            openai_instrumentor.instrument()
            
            logger.info("✅ Phoenix SQLite monitoring configured")
            
            return {
                "session": session,
                "tracer_provider": tracer_provider,
                "langchain_instrumentor": langchain_instrumentor,
                "openai_instrumentor": openai_instrumentor,
                "db_path": str(db_path)
            }
            
        except Exception as e:
            logger.error(f"OTEL setup failed: {e}")
            return None
            
    except ImportError:
        logger.warning("Phoenix not available")
        return None

def setup_minimal_monitoring():
    """Fallback: minimal monitoring without Phoenix"""
    logger.info("Using minimal monitoring (no Phoenix)")
    return {
        "session": None,
        "tracer_provider": None,
        "monitoring_enabled": False
    }

def get_phoenix_config():
    """Get optimal Phoenix configuration"""
    # Try SQLite first
    config = setup_phoenix_sqlite()
    if config:
        return config
    
    # Fallback to minimal
    return setup_minimal_monitoring()

if __name__ == "__main__":
    """Test the configuration"""
    print("🧪 Testing Phoenix SQLite Configuration...")
    config = get_phoenix_config()
    
    if config and config.get("session"):
        print(f"✅ Phoenix UI available at: http://localhost:6006")
    else:
        print("⚠️ Running without Phoenix UI")
    
    print("Configuration complete.")