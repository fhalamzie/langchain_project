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

# Import adaptive components
from adaptive_tag_synthesizer import AdaptiveTAGSynthesizer, AdaptiveSynthesisResult

# Fallback imports from archive
from tag_generator import ResponseGenerator, GenerationResult
from optimized_system_prompt import OPTIMIZED_SYSTEM_PROMPT
from focused_embeddings import FocusedEmbeddingSystem

# Use simple SQL validator instead of sqlglot-dependent one
from simple_sql_validator import SimpleSQLValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class TAGResult:
    """Complete result from TAG pipeline processing"""
    query: str
    sql: str
    raw_results: List[Dict]
    response: str
    synthesis_info: AdaptiveSynthesisResult
    validation_info: Optional[ValidationResult] = None
    execution_time: float = 0.0
    error: Optional[str] = None


class TAGPipeline:
    """
    Adaptive TAG Pipeline with ML-based classification and dynamic schema discovery.
    
    Key innovations:
    1. ML-based query classification instead of rule-based patterns
    2. Dynamic schema discovery that learns from successful queries
    3. Extended query type coverage (10+ types vs original 5)
    4. Confidence-based fallback strategies
    """
    
    def __init__(self, llm, db_executor, available_tables: List[str]):
        """
        Initialize Adaptive TAG Pipeline with enhanced components.
        
        Args:
            llm: Language model for SQL generation
            db_executor: Database executor (FDB interface)
            available_tables: List of available table names
        """
        self.llm = llm
        self.db_executor = db_executor
        self.available_tables = available_tables
        
        # Create schema info for adaptive components
        schema_info = {"tables": {table: {} for table in available_tables}}
        
        # Initialize adaptive TAG components
        self.synthesizer = AdaptiveTAGSynthesizer(schema_info)
        self.validator = SimpleSQLValidator()
        self.generator = ResponseGenerator()
        self.embedding_system = FocusedEmbeddingSystem()
        
        logger.info("Adaptive TAG Pipeline initialized with %d available tables", 
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
            # Phase 1: Adaptive SYN (Synthesis) - ML classification and dynamic schema discovery
            logger.info("Adaptive TAG Phase 1: ML Synthesis for query: %s", query)
            synthesis = self.synthesizer.synthesize(query)
            
            # Get dynamically discovered relevant tables
            needed_tables = synthesis.dynamic_tables
            detailed_context = self.embedding_system.retrieve_table_details(needed_tables)
            
            # Generate enhanced prompt with ML insights
            enhanced_prompt = self._build_enhanced_prompt(synthesis, detailed_context)
            
            # Use LLM to generate SQL with enhanced context
            messages = [
                {"role": "system", "content": enhanced_prompt},
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
            logger.info("Adaptive TAG Phase 3: Generating response")
            response = self.generator.generate(
                results, 
                synthesis.query_type, 
                query
            )
            
            execution_time = time.time() - start_time
            
            # Learn from this execution for future improvements
            success = len(results) > 0 and not validation or validation.valid
            self.synthesizer.learn_from_success(query, synthesis.query_type, final_sql, success)
            
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
            
            # Return error result with adaptive synthesis structure
            from adaptive_tag_synthesizer import AdaptiveSynthesisResult
            
            return TAGResult(
                query=query,
                sql="",
                raw_results=[],
                response=f"Fehler bei der Verarbeitung: {str(e)}",
                synthesis_info=AdaptiveSynthesisResult(
                    sql="",
                    query_type="error",
                    entities=[],
                    schema_context={},
                    confidence=0.0,
                    reasoning="Pipeline error",
                    alternatives=[],
                    dynamic_tables=[],
                    relationship_map={}
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
    
    def _build_enhanced_prompt(self, synthesis: AdaptiveSynthesisResult, detailed_context: str) -> str:
        """
        Build enhanced prompt with ML classification insights and dynamic schema discovery.
        
        Args:
            synthesis: Adaptive synthesis result with ML classification
            detailed_context: Retrieved table details
            
        Returns:
            Enhanced system prompt
        """
        base_prompt = OPTIMIZED_SYSTEM_PROMPT
        
        # Add ML classification insights
        ml_insights = f"""
ML CLASSIFICATION INSIGHTS:
- Query Type: {synthesis.query_type} (confidence: {synthesis.confidence:.3f})
- Extracted Entities: {', '.join(synthesis.entities)}
- Alternative Classifications: {', '.join([f"{alt[0]}({alt[1]:.2f})" for alt in synthesis.alternatives[:2]])}
- Reasoning: {synthesis.reasoning}

DYNAMIC SCHEMA DISCOVERY:
- Relevant Tables: {', '.join(synthesis.dynamic_tables)}
- Table Relationships: {synthesis.relationship_map}
- Query Type Schema: {synthesis.schema_context.get('description', 'N/A')}

CRITICAL RULES FROM ML ANALYSIS:
{chr(10).join(f"- {rule}" for rule in synthesis.schema_context.get('critical_rules', []))}
"""
        
        # Add focused table details
        table_details = f"\nRELEVANT TABLE DETAILS:\n{detailed_context}"
        
        # Combine all components
        enhanced_prompt = base_prompt + ml_insights + table_details
        
        return enhanced_prompt
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get enhanced performance metrics for adaptive TAG pipeline."""
        base_metrics = {
            "pipeline": "Adaptive TAG",
            "components": {
                "synthesizer": "adaptive_ml",
                "validator": "active", 
                "generator": "active",
                "embedding_system": "focused"
            },
            "tables_available": len(self.available_tables)
        }
        
        # Add adaptive synthesizer metrics
        if hasattr(self.synthesizer, 'classifier'):
            classifier_metrics = self.synthesizer.classifier.get_performance_metrics()
            base_metrics["ml_classification"] = classifier_metrics
        
        return base_metrics