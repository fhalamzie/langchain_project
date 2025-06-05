#!/usr/bin/env python3
"""
TAG Pipeline Integration - Connects SYN, EXEC, and GEN modules
for improved SQL generation accuracy.

This pipeline orchestrates the TAG architecture:
1. SYN (Synthesis) - Query classification and targeted context
2. EXEC (Execution) - SQL execution using existing FDB interface  
3. GEN (Generation) - Natural language response formatting
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add archive to path to import existing implementations
archive_path = Path(__file__).parent / "archive"
sys.path.insert(0, str(archive_path))

from tag_synthesizer import QuerySynthesizer, SynthesisResult
from tag_generator import ResponseGenerator, GenerationResult
from sql_validator import SQLValidator, ValidationResult
from optimized_system_prompt import OPTIMIZED_SYSTEM_PROMPT
from focused_embeddings import FocusedEmbeddingSystem

logger = logging.getLogger(__name__)


@dataclass
class TAGResult:
    """Complete result from TAG pipeline processing"""
    query: str
    sql: str
    raw_results: List[Dict]
    response: str
    synthesis_info: SynthesisResult
    validation_info: Optional[ValidationResult] = None
    execution_time: float = 0.0
    error: Optional[str] = None


class TAGPipeline:
    """
    TAG Pipeline orchestrates the complete query processing flow.
    
    Key innovation: Replaces overwhelming 498 YAML context with
    focused, query-type-specific schemas delivered precisely when needed.
    """
    
    def __init__(self, llm, db_executor, available_tables: List[str]):
        """
        Initialize TAG Pipeline with required components.
        
        Args:
            llm: Language model for SQL generation
            db_executor: Database executor (FDB interface)
            available_tables: List of available table names
        """
        self.llm = llm
        self.db_executor = db_executor
        self.available_tables = available_tables
        
        # Initialize TAG components
        self.synthesizer = QuerySynthesizer()
        self.validator = SQLValidator()
        self.generator = ResponseGenerator()
        self.embedding_system = FocusedEmbeddingSystem()
        
        logger.info("TAG Pipeline initialized with %d available tables", 
                   len(available_tables))
    
    def process(self, query: str) -> TAGResult:
        """
        Process query through complete TAG pipeline.
        
        Args:
            query: Natural language query
            
        Returns:
            TAGResult with complete processing information
        """
        import time
        start_time = time.time()
        
        try:
            # Phase 1: SYN (Synthesis) - Classify and get targeted context
            logger.info("TAG Phase 1: Synthesis for query: %s", query)
            synthesis = self.synthesizer.synthesize(query)
            
            # Get focused context for needed tables only
            needed_tables = synthesis.schema_context.get("primary_tables", [])
            detailed_context = self.embedding_system.retrieve_table_details(needed_tables)
            
            # Generate SQL with focused prompt + targeted details
            focused_prompt = OPTIMIZED_SYSTEM_PROMPT + "\n\nRELEVANT TABLE DETAILS:\n" + detailed_context
            
            # Use LLM to generate SQL
            messages = [
                {"role": "system", "content": focused_prompt},
                {"role": "user", "content": f"Generate SQL for: {query}"}
            ]
            
            llm_response = self.llm.invoke(messages)
            generated_sql = self._extract_sql(llm_response.content)
            
            # Update synthesis result with generated SQL
            synthesis.sql = generated_sql
            
            # Validate and fix SQL if needed
            validation = self.validator.validate_and_fix(
                generated_sql, 
                self.available_tables
            )
            
            if not validation.valid and validation.fixed_sql:
                logger.info("SQL validation found issues, using fixed SQL")
                final_sql = validation.fixed_sql
            else:
                final_sql = generated_sql
            
            # Phase 2: EXEC (Execution) - Use existing FDB interface
            logger.info("TAG Phase 2: Executing SQL: %s", final_sql)
            results = self._execute_sql(final_sql)
            
            # Phase 3: GEN (Generation) - Format response
            logger.info("TAG Phase 3: Generating response")
            response = self.generator.generate(
                results, 
                synthesis.query_type, 
                query
            )
            
            execution_time = time.time() - start_time
            
            return TAGResult(
                query=query,
                sql=final_sql,
                raw_results=results,
                response=response,
                synthesis_info=synthesis,
                validation_info=validation,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error("TAG Pipeline error: %s", str(e))
            execution_time = time.time() - start_time
            
            # Return error result
            return TAGResult(
                query=query,
                sql="",
                raw_results=[],
                response=f"Fehler bei der Verarbeitung: {str(e)}",
                synthesis_info=SynthesisResult(
                    sql="",
                    query_type="error",
                    entities=[],
                    schema_context={},
                    confidence=0.0,
                    reasoning="Pipeline error"
                ),
                execution_time=execution_time,
                error=str(e)
            )
    
    def _extract_sql(self, llm_response: str) -> str:
        """Extract SQL from LLM response."""
        # Remove markdown code blocks if present
        if "```sql" in llm_response:
            sql = llm_response.split("```sql")[1].split("```")[0].strip()
        elif "```" in llm_response:
            sql = llm_response.split("```")[1].split("```")[0].strip()
        else:
            sql = llm_response.strip()
        
        # Remove any leading SQL keyword duplication
        lines = sql.split('\n')
        clean_lines = [line for line in lines if line.strip()]
        return '\n'.join(clean_lines)
    
    def _execute_sql(self, sql: str) -> List[Dict]:
        """Execute SQL using the database executor."""
        try:
            # Use the provided db_executor
            result = self.db_executor.execute_query(sql)
            
            # Convert to list of dicts if needed
            if hasattr(result, 'fetchall'):
                rows = result.fetchall()
                if rows and hasattr(result, 'description'):
                    columns = [desc[0] for desc in result.description]
                    return [dict(zip(columns, row)) for row in rows]
                return []
            elif isinstance(result, list):
                return result
            else:
                return []
                
        except Exception as e:
            logger.error("SQL execution error: %s", str(e))
            raise
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        return {
            "pipeline": "TAG",
            "components": {
                "synthesizer": "active",
                "validator": "active", 
                "generator": "active",
                "embedding_system": "focused"
            },
            "tables_available": len(self.available_tables)
        }