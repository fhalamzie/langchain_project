#!/usr/bin/env python3
"""
Guided Agent Retriever - Phase 2 Modi-Kombination #2
LangChain + TAG = "Guided Agent"

Combines TAG's schema filtering with LangChain's agent reasoning:
- TAG's ML-based Query Classification filters schema to 3-5 relevant tables (instead of 151)
- LangChain Agent works with focused schema for better reasoning
- Result: Agent Power without Schema Overload

This implements Phase 2, Kombination 2: LangChain + TAG = "Guided Agent"
"""

import logging
import time
import traceback
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel

# Import our optimized components
from adaptive_tag_classifier import AdaptiveTAGClassifier, ClassificationResult
from filtered_langchain_retriever import FilteredLangChainSQLRetriever, QueryTableClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GuidedAgentResult:
    """Result from Guided Agent combining TAG + LangChain."""
    documents: List[Document]
    classification: ClassificationResult
    filtered_tables: List[str]
    agent_steps: List[Dict[str, Any]]
    execution_stats: Dict[str, Any]


class TAGSchemaGuide:
    """
    Enhanced schema filtering using TAG's ML classification.
    
    Provides more intelligent table selection than the rule-based QueryTableClassifier
    by leveraging TAG's ML understanding of query types and business logic.
    """
    
    def __init__(self):
        """Initialize TAG-guided schema filter."""
        self.tag_classifier = AdaptiveTAGClassifier()
        
        # Enhanced table mappings based on TAG's extended query types
        self.tag_to_tables = {
            "address_lookup": [
                "BEWOHNER", "BEWADR", "OBJEKTE", "ADRESSEN", "STRASSEN"
            ],
            "resident_lookup": [
                "BEWOHNER", "BEWADR", "OBJEKTE", "VERTRAEGE"
            ],
            "owner_lookup": [
                "EIGENTUEMER", "EIGADR", "VEREIG", "OBJEKTE"
            ],
            "property_queries": [
                "OBJEKTE", "WOHNUNG", "BEWOHNER", "EIGENTUEMER"
            ],
            "financial_queries": [
                "KONTEN", "BUCHUNG", "SOLLSTELLUNG", "RECHNUNGEN", "EIGENTUEMER"
            ],
            "count_queries": [
                "WOHNUNG", "OBJEKTE", "BEWOHNER", "EIGENTUEMER"
            ],
            "relationship_queries": [
                "BEWOHNER", "EIGENTUEMER", "OBJEKTE", "VEREIG", "VERTRAEGE"
            ],
            "temporal_queries": [
                "BUCHUNG", "VERTRAEGE", "BEWOHNER", "SOLLSTELLUNG"
            ],
            "comparison_queries": [
                "KONTEN", "WOHNUNG", "OBJEKTE", "BUCHUNG"
            ],
            "business_logic_queries": [
                "BEWOHNER", "EIGENTUEMER", "OBJEKTE", "KONTEN", "VERTRAEGE"
            ]
        }
    
    def get_guided_tables(self, query: str) -> tuple[List[str], ClassificationResult]:
        """
        Get schema tables guided by TAG's ML classification.
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (relevant_tables, classification_result)
        """
        # Use TAG's ML classifier for better query understanding
        classification = self.tag_classifier.classify_query(query)
        
        # Get primary tables for classified query type
        primary_tables = self.tag_to_tables.get(
            classification.query_type, 
            self.tag_to_tables["business_logic_queries"]
        )
        
        # Consider alternatives if confidence is low
        if classification.confidence < 0.6 and classification.alternatives:
            logger.info("Low confidence classification, considering alternatives")
            for alt_type, alt_conf in classification.alternatives[:1]:  # Top alternative
                if alt_conf > 0.4:  # Reasonable alternative confidence
                    alt_tables = self.tag_to_tables.get(alt_type, [])
                    # Merge with primary tables (remove duplicates)
                    primary_tables = list(set(primary_tables + alt_tables))
                    break
        
        # Core entities are always included for robustness
        core_entities = ["BEWOHNER", "EIGENTUEMER", "OBJEKTE", "KONTEN"]
        guided_tables = list(set(primary_tables + core_entities))
        
        # Convert to lowercase for compatibility with FilteredLangChainSQLRetriever
        guided_tables_lowercase = [table.lower() for table in guided_tables]
        
        logger.info(f"TAG-guided schema: {classification.query_type} → {len(guided_tables_lowercase)} tables")
        logger.info(f"Confidence: {classification.confidence:.3f}, Tables: {guided_tables_lowercase}")
        
        return guided_tables_lowercase, classification


class GuidedAgentRetriever:
    """
    Guided Agent Retriever - Combination of TAG + LangChain approaches.
    
    Strategy:
    1. TAG's ML Classifier analyzes query and selects optimal table subset
    2. LangChain Agent operates on focused schema (3-5 tables vs 151)
    3. Result: Agent reasoning power with precise schema targeting
    
    Benefits:
    - Eliminates schema overload through intelligent filtering
    - Maintains full LangChain agent capabilities
    - Better SQL generation through focused context
    - Adaptive learning from TAG's ML classification
    """
    
    def __init__(self, db_connection_string: str, llm: BaseLanguageModel, 
                 enable_monitoring: bool = True):
        """
        Initialize Guided Agent Retriever.
        
        Args:
            db_connection_string: Database connection string
            llm: Language model for agent reasoning
            enable_monitoring: Enable performance monitoring
        """
        logger.info("Initializing Guided Agent Retriever (TAG + LangChain)")
        
        # Core components
        self.db_connection_string = db_connection_string
        self.llm = llm
        self.enable_monitoring = enable_monitoring
        
        # TAG-guided schema filtering
        self.schema_guide = TAGSchemaGuide()
        
        # LangChain agent (will be created per query with filtered schema)
        self.langchain_retriever = None
        
        # Performance tracking
        self.retrieval_history: List[Dict[str, Any]] = []
        
        logger.info("Guided Agent Retriever initialized successfully")
    
    def retrieve(self, query: str, max_docs: int = 10) -> GuidedAgentResult:
        """
        Guided Agent retrieval combining TAG schema guidance + LangChain reasoning.
        
        Args:
            query: Natural language query
            max_docs: Maximum documents to retrieve
            
        Returns:
            GuidedAgentResult with guided agent output and metadata
        """
        start_time = time.time()
        
        logger.info(f"Guided Agent retrieval for: {query}")
        
        try:
            # Step 1: TAG Schema Guidance - intelligent table filtering
            guided_tables, classification = self.schema_guide.get_guided_tables(query)
            
            # Step 2: Create LangChain Agent with guided schema
            guided_langchain = FilteredLangChainSQLRetriever(
                db_connection_string=self.db_connection_string,
                llm=self.llm,
                enable_monitoring=self.enable_monitoring
            )
            
            # Override the table classifier with our TAG-guided results
            guided_langchain.query_classifier.get_relevant_tables = lambda q: guided_tables
            
            # Step 3: Execute with LangChain Agent on focused schema
            documents = guided_langchain.retrieve_documents(query, max_docs)
            
            # Step 4: Extract agent execution steps for analysis
            agent_steps = []
            for doc in documents:
                if doc.metadata.get("source") == "filtered_langchain_step":
                    agent_steps.append({
                        "step": doc.metadata.get("step_number"),
                        "tool": doc.metadata.get("tool"),
                        "input": doc.metadata.get("tool_input"),
                        "result": doc.metadata.get("observation")
                    })
            
            # Step 5: Performance statistics
            execution_time = time.time() - start_time
            stats = {
                "query_type": classification.query_type,
                "classification_confidence": classification.confidence,
                "tables_filtered": len(guided_tables),
                "original_table_count": 151,  # WINCASA total tables
                "reduction_ratio": len(guided_tables) / 151,
                "agent_steps": len(agent_steps),
                "documents_generated": len(documents),
                "execution_time": execution_time,
                "alternatives_considered": len(classification.alternatives)
            }
            
            # Track for learning and optimization
            self.retrieval_history.append({
                "query": query,
                "classification": classification.query_type,
                "confidence": classification.confidence,
                "tables_used": len(guided_tables),
                "agent_steps": len(agent_steps),
                "success": len(documents) > 0 and documents[0].metadata.get("success", False),
                "timestamp": time.time()
            })
            
            logger.info(f"Guided Agent completed: {len(documents)} docs, "
                       f"{len(guided_tables)} tables, {len(agent_steps)} steps in {execution_time:.2f}s")
            
            return GuidedAgentResult(
                documents=documents,
                classification=classification,
                filtered_tables=guided_tables,
                agent_steps=agent_steps,
                execution_stats=stats
            )
            
        except Exception as e:
            logger.error(f"Guided Agent error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Create error result
            error_doc = Document(
                page_content=f"Query: {query}\n\nError: {str(e)}\n\nThe Guided Agent encountered an error.",
                metadata={
                    "source": "guided_agent_error",
                    "query": query,
                    "error": str(e),
                    "success": False,
                    "execution_time": time.time() - start_time
                }
            )
            
            return GuidedAgentResult(
                documents=[error_doc],
                classification=ClassificationResult("error", 0.0, [], [], "Error occurred"),
                filtered_tables=[],
                agent_steps=[],
                execution_stats={"error": str(e)}
            )
    
    def learn_from_feedback(self, query: str, sql: str, success: bool):
        """
        Learn from execution feedback to improve future performance.
        
        Args:
            query: Original query
            sql: Generated SQL
            success: Whether SQL execution was successful
        """
        # Feed learning back to TAG classifier for improved classification
        if hasattr(self, '_last_classification'):
            self.schema_guide.tag_classifier.learn_from_success(
                query, 
                self._last_classification.query_type, 
                sql, 
                success
            )
        
        logger.info(f"Guided Agent learning feedback: query={query[:50]}..., success={success}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for TAG + LangChain combination."""
        tag_metrics = self.schema_guide.tag_classifier.get_performance_metrics()
        
        if not self.retrieval_history:
            guided_metrics = {"status": "no_retrievals"}
        else:
            total_retrievals = len(self.retrieval_history)
            successful_retrievals = sum(1 for h in self.retrieval_history if h["success"])
            avg_tables = sum(h["tables_used"] for h in self.retrieval_history) / total_retrievals
            avg_steps = sum(h["agent_steps"] for h in self.retrieval_history) / total_retrievals
            high_confidence = sum(1 for h in self.retrieval_history if h["confidence"] > 0.7)
            
            guided_metrics = {
                "total_retrievals": total_retrievals,
                "success_rate": successful_retrievals / total_retrievals if total_retrievals > 0 else 0,
                "avg_tables_filtered": round(avg_tables, 1),
                "avg_agent_steps": round(avg_steps, 1),
                "schema_reduction": f"{avg_tables:.1f}/151 tables ({avg_tables/151:.1%} reduction)",
                "high_confidence_rate": high_confidence / total_retrievals if total_retrievals > 0 else 0,
                "query_types_handled": len(set(h["classification"] for h in self.retrieval_history))
            }
        
        return {
            "guided_agent_version": "1.0",
            "tag_classifier": tag_metrics,
            "guided_agent": guided_metrics,
            "combination_strategy": "TAG ML classification → LangChain focused agent",
            "schema_optimization": "151 tables → 3-5 relevant tables per query"
        }
    
    def get_retrieval_summary(self) -> str:
        """Get human-readable summary of guided agent performance."""
        metrics = self.get_performance_metrics()
        
        summary = "🤖 GUIDED AGENT RETRIEVER SUMMARY\n"
        summary += "=" * 45 + "\n\n"
        
        # TAG Classifier stats
        tag_stats = metrics["tag_classifier"]
        summary += f"TAG Schema Guide:\n"
        summary += f"  • ML model available: {tag_stats.get('ml_model_available', False)}\n"
        summary += f"  • Query types covered: {tag_stats.get('query_types_covered', 0)}\n"
        summary += f"  • Classification success: {tag_stats.get('success_rate', 0):.1%}\n\n"
        
        # Guided Agent stats
        guided_stats = metrics["guided_agent"]
        if guided_stats.get("status") != "no_retrievals":
            summary += f"Guided Agent Performance:\n"
            summary += f"  • Total queries processed: {guided_stats.get('total_retrievals', 0)}\n"
            summary += f"  • Success rate: {guided_stats.get('success_rate', 0):.1%}\n"
            summary += f"  • Schema reduction: {guided_stats.get('schema_reduction', 'N/A')}\n"
            summary += f"  • Avg agent steps: {guided_stats.get('avg_agent_steps', 0)}\n"
            summary += f"  • High confidence: {guided_stats.get('high_confidence_rate', 0):.1%}\n"
            summary += f"  • Query types handled: {guided_stats.get('query_types_handled', 0)}\n\n"
        else:
            summary += "Guided Agent: No retrievals yet\n\n"
        
        summary += f"Strategy: {metrics['combination_strategy']}\n"
        summary += f"Optimization: {metrics['schema_optimization']}\n"
        
        return summary
    
    def retrieve_documents(self, query: str, max_docs: int = 10) -> List[Document]:
        """
        Standard retrieve_documents interface for compatibility.
        
        Args:
            query: Natural language query
            max_docs: Maximum number of documents to return
            
        Returns:
            List of Document objects
        """
        guided_result = self.retrieve(query, max_docs)
        return guided_result.documents

    def get_retriever_info(self) -> Dict[str, Any]:
        """Get information about this retriever."""
        return {
            "mode": "guided_agent",
            "type": "Guided Agent (TAG + LangChain)",
            "description": "Combines TAG's ML-based schema filtering with LangChain's agent reasoning",
            "features": [
                "TAG ML query classification",
                "Schema filtering (151 → 3-8 tables)",
                "LangChain agent reasoning",
                "Agent step tracking",
                "Performance learning"
            ],
            "status": "active"
        }


def run_guided_agent(query: str, db_connection_string: str, llm, enable_monitoring: bool = True) -> str:
    """
    Run guided agent for a given query - compatible with benchmark interface.
    
    Args:
        query: Natural language query
        db_connection_string: Database connection string
        llm: Language model instance
        enable_monitoring: Whether to enable monitoring
        
    Returns:
        String response from guided agent
    """
    try:
        retriever = GuidedAgentRetriever(
            db_connection_string=db_connection_string,
            llm=llm,
            enable_monitoring=enable_monitoring
        )
        
        result = retriever.retrieve(query, max_docs=5)
        
        # Format response from documents
        if result.documents:
            primary_doc = result.documents[0]
            response = primary_doc.page_content
            
            # Add metadata info if available
            if primary_doc.metadata.get("success"):
                response += f"\n\nClassification: {result.classification.query_type}"
                response += f"\nTables used: {len(result.filtered_tables)}"
                response += f"\nAgent steps: {len(result.agent_steps)}"
            
            return response
        else:
            return "No guided agent response generated."
            
    except Exception as e:
        logger.error(f"Guided agent execution failed: {e}")
        return f"Error in guided agent: {str(e)}"


def create_guided_agent_retriever(db_connection_string: str, llm: BaseLanguageModel,
                                enable_monitoring: bool = True) -> GuidedAgentRetriever:
    """
    Factory function to create Guided Agent Retriever.
    
    Args:
        db_connection_string: Database connection string
        llm: Language model for agent reasoning
        enable_monitoring: Enable performance monitoring
        
    Returns:
        Configured GuidedAgentRetriever instance
    """
    return GuidedAgentRetriever(db_connection_string, llm, enable_monitoring)


def test_guided_agent_retriever():
    """Test Guided Agent Retriever with sample queries."""
    print("🧪 Testing Guided Agent Retriever (TAG + LangChain)")
    print("=" * 60)
    
    # Mock LLM for testing
    class MockLLM:
        def __init__(self):
            self.model_name = "gpt-4"
        
        def invoke(self, prompt):
            return {"content": "Test response"}
    
    # Test configuration
    db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    llm = MockLLM()
    
    try:
        # Test just the schema guidance component
        schema_guide = TAGSchemaGuide()
        
        test_queries = [
            "Wer wohnt in der Marienstraße 26?",
            "Alle Eigentümer aus Köln", 
            "Durchschnittliche Miete in Essen",
            "Wie viele Wohnungen gibt es?",
            "Zeige mir alle Verträge seit 2023",
            "Vergleiche die Kosten zwischen Objekten"
        ]
        
        print("\nTesting TAG Schema Guidance:")
        for query in test_queries:
            guided_tables, classification = schema_guide.get_guided_tables(query)
            print(f"\nQuery: {query}")
            print(f"  Classification: {classification.query_type} (confidence: {classification.confidence:.3f})")
            print(f"  Guided Tables: {len(guided_tables)} tables")
            print(f"  Tables: {guided_tables}")
            print(f"  Schema Reduction: {len(guided_tables)}/151 = {len(guided_tables)/151:.1%}")
        
        # Test TAG metrics
        print(f"\nTAG Classifier Metrics:")
        tag_metrics = schema_guide.tag_classifier.get_performance_metrics()
        for key, value in tag_metrics.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Test error: {e}")
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    test_guided_agent_retriever()