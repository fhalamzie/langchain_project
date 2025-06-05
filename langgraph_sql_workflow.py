#!/usr/bin/env python3
"""
LangGraph SQL Workflow for WINCASA System

This module implements a LangGraph-based workflow for processing natural language 
database queries with enhanced context retrieval, business logic validation, 
and SQL generation with error recovery.

Features:
- State machine-based query processing
- Business glossar integration
- FK-graph analysis for JOIN optimization
- Multi-hop retrieval with context validation
- SQL validation and error recovery
- Phoenix monitoring integration
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict, Annotated
from pathlib import Path

# LangGraph imports
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph not available - workflow mode disabled")

# WINCASA imports
from business_glossar import extract_business_entities, WINCASA_GLOSSAR
from global_context import get_compact_global_context
from enhanced_retrievers import EnhancedMultiStageRetriever
from sql_validator import FirebirdSQLValidator
from phoenix_monitoring import get_monitor, trace_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryState(TypedDict):
    """State for the LangGraph SQL workflow"""
    # Input
    user_query: str
    
    # Processing steps
    business_entities: List[str]
    business_mappings: Dict[str, str]
    required_tables: List[str]
    join_paths: List[str]
    
    # Context retrieval
    retrieved_context: str
    context_quality: float
    
    # SQL generation
    generated_sql: str
    sql_valid: bool
    sql_errors: List[str]
    
    # Execution
    sql_results: Any
    final_answer: str
    
    # Metadata
    execution_time: float
    iterations: int
    success: bool
    error_message: Optional[str]


class LangGraphSQLWorkflow:
    """
    LangGraph-based SQL workflow for enhanced query processing.
    
    This workflow implements a state machine that processes natural language
    queries through multiple stages with error recovery and validation.
    """
    
    def __init__(self, 
                 db_interface,
                 llm,
                 enable_monitoring: bool = True,
                 max_iterations: int = 3):
        """
        Initialize the LangGraph SQL workflow.
        
        Args:
            db_interface: Database interface for executing queries
            llm: Language model for SQL generation
            enable_monitoring: Enable Phoenix monitoring
            max_iterations: Maximum retry iterations
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is required for workflow mode")
            
        self.db_interface = db_interface
        self.llm = llm
        self.enable_monitoring = enable_monitoring
        self.max_iterations = max_iterations
        
        # Initialize components
        self._initialize_components()
        
        # Build workflow
        self.workflow = self._build_workflow()
        
    def _initialize_components(self):
        """Initialize workflow components"""
        # Enhanced retriever
        try:
            self.retriever = EnhancedMultiStageRetriever(
                parsed_docs=[],  # Will be loaded separately
                openai_api_key=os.getenv("OPENAI_API_KEY", "")
            )
        except Exception as e:
            logger.warning(f"Could not initialize retriever: {e}")
            self.retriever = None
            
        # SQL validator
        try:
            self.sql_validator = FirebirdSQLValidator()
        except Exception as e:
            logger.warning(f"Could not initialize SQL validator: {e}")
            self.sql_validator = None
            
        # Phoenix monitor
        if self.enable_monitoring:
            try:
                self.monitor = get_monitor(enable_ui=False)
            except Exception as e:
                logger.warning(f"Could not initialize monitor: {e}")
                self.monitor = None
        else:
            self.monitor = None
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        # Create workflow
        workflow = StateGraph(QueryState)
        
        # Add nodes
        workflow.add_node("extract_entities", self._extract_business_entities)
        workflow.add_node("find_tables", self._find_required_tables)
        workflow.add_node("retrieve_context", self._retrieve_enhanced_context)
        workflow.add_node("generate_sql", self._generate_sql_query)
        workflow.add_node("validate_sql", self._validate_sql_query)
        workflow.add_node("execute_sql", self._execute_sql_query)
        workflow.add_node("format_answer", self._format_final_answer)
        workflow.add_node("handle_error", self._handle_error_recovery)
        
        # Define edges
        workflow.add_edge(START, "extract_entities")
        workflow.add_edge("extract_entities", "find_tables")
        workflow.add_edge("find_tables", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_sql")
        
        # Conditional edge for SQL validation
        workflow.add_conditional_edges(
            "generate_sql",
            self._should_validate_sql,
            {
                "validate": "validate_sql",
                "skip_validation": "execute_sql"
            }
        )
        
        # Conditional edge after validation
        workflow.add_conditional_edges(
            "validate_sql", 
            self._validation_decision,
            {
                "valid": "execute_sql",
                "invalid": "handle_error",
                "max_retries": END
            }
        )
        
        # Conditional edge after execution
        workflow.add_conditional_edges(
            "execute_sql",
            self._execution_decision,
            {
                "success": "format_answer",
                "error": "handle_error",
                "max_retries": END
            }
        )
        
        workflow.add_edge("format_answer", END)
        workflow.add_edge("handle_error", "generate_sql")  # Retry loop
        
        # Compile workflow
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)
    
    # Node implementations
    def _extract_business_entities(self, state: QueryState) -> Dict[str, Any]:
        """Extract business entities from user query"""
        logger.info("🔍 Extracting business entities...")
        
        entities = extract_business_entities(state["user_query"])
        mappings = {}
        
        for entity in entities:
            if entity in WINCASA_GLOSSAR:
                mappings[entity] = WINCASA_GLOSSAR[entity]
        
        return {
            "business_entities": entities,
            "business_mappings": mappings
        }
    
    def _find_required_tables(self, state: QueryState) -> Dict[str, Any]:
        """Find required tables based on business entities"""
        logger.info("📊 Finding required tables...")
        
        tables = []
        join_paths = []
        
        # Extract tables from business mappings
        for entity, mapping in state["business_mappings"].items():
            if "FROM" in mapping or "JOIN" in mapping:
                # Extract table names from SQL snippets
                words = mapping.split()
                for i, word in enumerate(words):
                    if word.upper() in ["FROM", "JOIN"] and i + 1 < len(words):
                        table = words[i + 1].strip()
                        if table not in tables:
                            tables.append(table)
        
        # Add default tables if none found
        if not tables:
            tables = ["BEWOHNER", "WOHNUNG", "OBJEKTE"]  # Default WINCASA tables
        
        return {
            "required_tables": tables,
            "join_paths": join_paths
        }
    
    def _retrieve_enhanced_context(self, state: QueryState) -> Dict[str, Any]:
        """Retrieve enhanced context using multi-stage retrieval"""
        logger.info("📚 Retrieving enhanced context...")
        
        context = ""
        quality = 0.0
        
        if self.retriever:
            try:
                docs = self.retriever.get_relevant_documents(state["user_query"])
                context = "\n\n".join([doc.page_content for doc in docs])
                quality = len(docs) / 10.0  # Simple quality score
            except Exception as e:
                logger.warning(f"Retrieval failed: {e}")
        
        # Fallback to global context
        if not context:
            try:
                context = get_compact_global_context()
                quality = 0.5  # Medium quality for global context
            except Exception as e:
                logger.warning(f"Global context failed: {e}")
                context = "Basic WINCASA database context"
                quality = 0.1
        
        return {
            "retrieved_context": context,
            "context_quality": quality
        }
    
    def _generate_sql_query(self, state: QueryState) -> Dict[str, Any]:
        """Generate SQL query using LLM"""
        logger.info("🔧 Generating SQL query...")
        
        # Build enhanced prompt
        prompt = self._build_sql_prompt(state)
        
        try:
            response = self.llm.invoke(prompt)
            sql = self._extract_sql_from_response(response.content)
            
            return {
                "generated_sql": sql,
                "iterations": state.get("iterations", 0) + 1
            }
        except Exception as e:
            return {
                "generated_sql": "",
                "error_message": str(e),
                "iterations": state.get("iterations", 0) + 1
            }
    
    def _validate_sql_query(self, state: QueryState) -> Dict[str, Any]:
        """Validate SQL query syntax and semantics"""
        logger.info("✅ Validating SQL query...")
        
        if not self.sql_validator:
            return {"sql_valid": True, "sql_errors": []}
        
        try:
            result = self.sql_validator.validate_and_fix(state["generated_sql"])
            return {
                "sql_valid": result.valid,
                "sql_errors": result.issues if hasattr(result, 'issues') else [],
                "generated_sql": result.fixed_sql if hasattr(result, 'fixed_sql') else state["generated_sql"]
            }
        except Exception as e:
            return {
                "sql_valid": False,
                "sql_errors": [str(e)]
            }
    
    def _execute_sql_query(self, state: QueryState) -> Dict[str, Any]:
        """Execute SQL query against database"""
        logger.info("🚀 Executing SQL query...")
        
        try:
            results = self.db_interface.run_sql(state["generated_sql"])
            return {
                "sql_results": results,
                "success": True
            }
        except Exception as e:
            return {
                "sql_results": None,
                "success": False,
                "error_message": str(e)
            }
    
    def _format_final_answer(self, state: QueryState) -> Dict[str, Any]:
        """Format final answer for user"""
        logger.info("📝 Formatting final answer...")
        
        if state["success"] and state["sql_results"]:
            answer = f"Query executed successfully. Found {len(state['sql_results'])} results."
            if state["sql_results"]:
                answer += f"\n\nSample result: {state['sql_results'][0]}"
        else:
            answer = f"Query failed: {state.get('error_message', 'Unknown error')}"
        
        return {
            "final_answer": answer,
            "execution_time": time.time()  # Would need start time
        }
    
    def _handle_error_recovery(self, state: QueryState) -> Dict[str, Any]:
        """Handle error recovery and retry logic"""
        logger.info("🔄 Handling error recovery...")
        
        iterations = state.get("iterations", 0)
        
        if iterations >= self.max_iterations:
            return {
                "success": False,
                "final_answer": f"Max retries ({self.max_iterations}) exceeded. Last error: {state.get('error_message', 'Unknown')}"
            }
        
        # Reset for retry
        return {
            "generated_sql": "",
            "sql_valid": False,
            "sql_errors": [],
            "error_message": None
        }
    
    # Conditional edge functions
    def _should_validate_sql(self, state: QueryState) -> str:
        """Decide whether to validate SQL"""
        if self.sql_validator and state.get("generated_sql"):
            return "validate"
        return "skip_validation"
    
    def _validation_decision(self, state: QueryState) -> str:
        """Decide next step after validation"""
        iterations = state.get("iterations", 0)
        
        if iterations >= self.max_iterations:
            return "max_retries"
        
        if state.get("sql_valid", False):
            return "valid"
        else:
            return "invalid"
    
    def _execution_decision(self, state: QueryState) -> str:
        """Decide next step after execution"""
        iterations = state.get("iterations", 0)
        
        if iterations >= self.max_iterations:
            return "max_retries"
        
        if state.get("success", False):
            return "success"
        else:
            return "error"
    
    # Helper methods
    def _build_sql_prompt(self, state: QueryState) -> str:
        """Build enhanced SQL generation prompt"""
        context = state.get("retrieved_context", "")
        entities = state.get("business_entities", [])
        mappings = state.get("business_mappings", {})
        
        prompt = f"""
Generate a Firebird SQL query for this natural language request:
"{state['user_query']}"

BUSINESS CONTEXT:
Extracted entities: {entities}
Business mappings: {mappings}

DATABASE CONTEXT:
{context[:1000]}...

REQUIREMENTS:
- Use Firebird SQL dialect (FIRST n, not LIMIT)
- Include proper JOINs for related tables
- Apply business logic from mappings
- Return only the SQL query, no explanation

SQL Query:"""
        
        return prompt
    
    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Simple extraction - look for SQL keywords
        lines = response.strip().split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP', 'ORDER']):
                sql_lines.append(line)
            elif sql_lines and line:  # Continue if we've started collecting SQL
                sql_lines.append(line)
        
        return '\n'.join(sql_lines) if sql_lines else response.strip()
    
    def process_query(self, user_query: str, config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a natural language query through the LangGraph workflow.
        
        Args:
            user_query: Natural language query
            config: Optional configuration for workflow execution
            
        Returns:
            Dict with query results and metadata
        """
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph workflow not available")
        
        start_time = time.time()
        
        # Set up config
        if config is None:
            config = {"configurable": {"thread_id": "wincasa_query"}}
        
        # Initial state
        initial_state = {
            "user_query": user_query,
            "business_entities": [],
            "business_mappings": {},
            "required_tables": [],
            "join_paths": [],
            "retrieved_context": "",
            "context_quality": 0.0,
            "generated_sql": "",
            "sql_valid": False,
            "sql_errors": [],
            "sql_results": None,
            "final_answer": "",
            "execution_time": 0.0,
            "iterations": 0,
            "success": False,
            "error_message": None
        }
        
        try:
            # Execute workflow
            if self.monitor:
                with trace_query(user_query, self.monitor):
                    final_state = self.workflow.invoke(initial_state, config=config)
            else:
                final_state = self.workflow.invoke(initial_state, config=config)
            
            # Add execution time
            final_state["execution_time"] = time.time() - start_time
            
            return {
                "answer": final_state.get("final_answer", "No answer generated"),
                "sql_query": final_state.get("generated_sql", ""),
                "raw_results": final_state.get("sql_results", []),
                "retrieval_mode": "langgraph",
                "documents_retrieved": len(final_state.get("retrieved_context", "").split("\n\n")),
                "execution_time": final_state["execution_time"],
                "success": final_state.get("success", False),
                "iterations": final_state.get("iterations", 0),
                "business_entities": final_state.get("business_entities", []),
                "context_quality": final_state.get("context_quality", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "answer": f"Workflow execution failed: {str(e)}",
                "sql_query": "",
                "raw_results": [],
                "retrieval_mode": "langgraph", 
                "documents_retrieved": 0,
                "execution_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }


def test_langgraph_workflow():
    """Test function for LangGraph workflow"""
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph not available for testing")
        return False
    
    print("🧪 Testing LangGraph SQL Workflow...")
    
    # Mock components
    class MockDBInterface:
        def run_sql(self, sql):
            return [{"count": 517}]
    
    class MockLLM:
        def invoke(self, prompt):
            class Response:
                content = "SELECT COUNT(*) FROM WOHNUNG"
            return Response()
    
    try:
        # Create workflow
        workflow = LangGraphSQLWorkflow(
            db_interface=MockDBInterface(),
            llm=MockLLM(),
            enable_monitoring=False
        )
        
        # Test query
        result = workflow.process_query("Wie viele Wohnungen gibt es?")
        
        print(f"✅ Workflow result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False


if __name__ == "__main__":
    test_langgraph_workflow()