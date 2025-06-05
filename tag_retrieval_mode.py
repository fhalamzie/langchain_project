#!/usr/bin/env python3
"""
TAG Retrieval Mode Integration

Integrates the TAG pipeline as a new retrieval mode for the 
FirebirdDirectSQLAgent, providing focused context instead of
overwhelming YAML documents.
"""

import logging
from typing import Dict, List, Any, Optional
from tag_pipeline import TAGPipeline, TAGResult

logger = logging.getLogger(__name__)


class TAGRetrievalMode:
    """
    TAG retrieval mode implementation for FirebirdDirectSQLAgent.
    
    This mode uses the TAG architecture (SYN→EXEC→GEN) to provide
    focused, query-type-specific context instead of retrieving all
    498 YAML documents.
    """
    
    def __init__(self, llm, db_interface, schema_info: Dict[str, Any]):
        """
        Initialize TAG retrieval mode.
        
        Args:
            llm: Language model instance
            db_interface: Database interface (FDB)
            schema_info: Schema information including table names
        """
        self.llm = llm
        self.db_interface = db_interface
        self.schema_info = schema_info
        
        # Extract available tables
        self.available_tables = list(schema_info.get("tables", {}).keys())
        
        # Initialize TAG pipeline
        self.pipeline = TAGPipeline(
            llm=llm,
            db_executor=db_interface,
            available_tables=self.available_tables
        )
        
        logger.info("TAG retrieval mode initialized with %d tables", 
                   len(self.available_tables))
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process query using TAG pipeline.
        
        Args:
            query: Natural language query
            
        Returns:
            Dict with results matching FirebirdDirectSQLAgent format
        """
        try:
            # Process through TAG pipeline
            result: TAGResult = self.pipeline.process(query)
            
            # Convert to agent format
            return {
                "success": result.error is None,
                "query": result.query,
                "sql_query": result.sql,
                "results": result.raw_results,
                "answer": result.response,
                "execution_time": result.execution_time,
                "retrieval_mode": "tag",
                "metadata": {
                    "query_type": result.synthesis_info.query_type,
                    "confidence": result.synthesis_info.confidence,
                    "entities": result.synthesis_info.entities,
                    "validation_performed": result.validation_info is not None,
                    "tables_used": result.synthesis_info.schema_context.get(
                        "primary_tables", []
                    )
                }
            }
            
        except Exception as e:
            logger.error("TAG retrieval mode error: %s", str(e))
            return {
                "success": False,
                "query": query,
                "sql_query": "",
                "results": [],
                "answer": f"Fehler im TAG-Modus: {str(e)}",
                "execution_time": 0.0,
                "retrieval_mode": "tag",
                "error": str(e)
            }
    
    def get_context_for_query(self, query: str) -> str:
        """
        Get focused context for a query (for compatibility).
        
        Args:
            query: Natural language query
            
        Returns:
            Focused context string
        """
        # Use synthesizer to classify query
        synthesis = self.pipeline.synthesizer.synthesize(query)
        
        # Get focused context
        needed_tables = synthesis.schema_context.get("primary_tables", [])
        detailed_context = self.pipeline.embedding_system.retrieve_table_details(
            needed_tables
        )
        
        return f"""
Query Type: {synthesis.query_type}
Relevant Tables: {', '.join(needed_tables)}

{detailed_context}
"""
    
    @staticmethod
    def create_from_agent_config(llm, db_interface, schema_info) -> 'TAGRetrievalMode':
        """
        Factory method to create TAG mode from agent configuration.
        
        Args:
            llm: Language model from agent
            db_interface: Database interface from agent
            schema_info: Schema information from agent
            
        Returns:
            TAGRetrievalMode instance
        """
        return TAGRetrievalMode(llm, db_interface, schema_info)