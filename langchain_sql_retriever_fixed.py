#!/usr/bin/env python3
"""
LangChain SQL Database Agent Integration (Fixed Version)

This module implements the LangChain SQL Database Agent as the 5th retrieval mode
for the WINCASA system, providing automatic error recovery and schema introspection.

This version fixes the Pydantic validation issues by not inheriting from BaseDocumentationRetriever
but implementing the same interface.
"""

import os
import json
import time
import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import AgentType
from langchain_community.utilities import SQLDatabase
from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel
from langchain.callbacks.base import BaseCallbackHandler
# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional advanced imports
try:
    from langgraph.prebuilt import create_react_agent
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available - using classic SQL agent")

try:
    from langchain import hub
    HUB_AVAILABLE = True
except ImportError:
    HUB_AVAILABLE = False
    logger.warning("LangChain Hub not available - using default prompts")

from phoenix_monitoring import get_monitor
from global_context import get_compact_global_context


class LangChainSQLCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for LangChain SQL Agent monitoring"""
    
    def __init__(self, monitor=None):
        self.monitor = monitor
        self.start_time = None
        self.agent_steps = []
        
    def on_agent_action(self, action, **kwargs):
        """Called when agent takes an action"""
        self.agent_steps.append({
            "tool": action.tool,
            "tool_input": action.tool_input,
            "log": action.log,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"🔧 Agent Action: {action.tool} with input: {action.tool_input}")
        
    def on_agent_finish(self, finish, **kwargs):
        """Called when agent finishes"""
        logger.info(f"✅ Agent Finished: {finish.return_values}")
        
    def on_chain_start(self, serialized, inputs, **kwargs):
        """Called when chain starts"""
        self.start_time = time.time()
        logger.info(f"🚀 Chain Started with inputs: {inputs}")
        
    def on_chain_end(self, outputs, **kwargs):
        """Called when chain ends"""
        duration = time.time() - self.start_time if self.start_time else 0
        logger.info(f"⏱️ Chain completed in {duration:.2f}s")
        
        if self.monitor:
            self.monitor.track_retrieval(
                retrieval_mode="langchain",
                query=str(outputs.get('input', 'unknown')),
                documents_retrieved=len(self.agent_steps),
                relevance_scores=[1.0] * len(self.agent_steps),  # Default relevance scores
                duration=duration,
                success=True
            )
    
    def on_chain_error(self, error, **kwargs):
        """Called when chain encounters an error"""
        duration = time.time() - self.start_time if self.start_time else 0
        logger.error(f"❌ Chain Error after {duration:.2f}s: {error}")
        
        if self.monitor:
            self.monitor.track_retrieval(
                retrieval_mode="langchain", 
                query="error_query",
                documents_retrieved=0,
                relevance_scores=[],
                duration=duration,
                success=False
            )


class LangChainSQLRetriever:
    """
    LangChain SQL Database Agent retriever with automatic error recovery.
    
    This implements the 5th retrieval mode using LangChain's native SQL Database Agent
    for improved schema introspection and error handling.
    
    This version doesn't inherit from BaseRetriever to avoid Pydantic validation issues.
    """
    
    def __init__(self, 
                 db_connection_string: str,
                 llm: BaseLanguageModel,
                 enable_monitoring: bool = True):
        """
        Initialize LangChain SQL Database Agent retriever.
        
        Args:
            db_connection_string: Database connection string (Firebird format)
            llm: Language model for SQL generation
            enable_monitoring: Whether to enable Phoenix monitoring
        """
        self.db_connection_string = db_connection_string
        self.llm = llm
        self.enable_monitoring = enable_monitoring
        
        self.db = None
        self.agent = None
        self.monitor = None
        self.callback_handler = None
        
        if enable_monitoring:
            try:
                self.monitor = get_monitor(enable_ui=False)
                self.callback_handler = LangChainSQLCallbackHandler(self.monitor)
                logger.info("✅ Phoenix monitoring enabled for LangChain SQL Agent")
            except Exception as e:
                logger.warning(f"⚠️ Phoenix monitoring not available: {e}")
                self.monitor = None
        
        self._initialize_database()
        self._create_agent()
    
    def _convert_to_server_connection(self, connection_string: str) -> str:
        """
        Convert embedded connection string to server connection for LangChain.
        
        Args:
            connection_string: Original connection string (embedded format)
            
        Returns:
            Server-style connection string for LangChain SQLDatabase
        """
        try:
            # If already a server connection, return as-is
            if "localhost:3050" in connection_string and connection_string.count("localhost:3050") == 1:
                logger.info(f"🔄 Already server connection, returning as-is")
                return connection_string
                
            # Extract database path from various formats
            if "firebird+fdb://" in connection_string:
                # Format: firebird+fdb://user:pass@/path/to/db.fdb or firebird+fdb://user:pass@localhost:3050//path/to/db.fdb
                parts = connection_string.split("@")
                if len(parts) >= 2:
                    db_path = parts[1]
                    
                    # Clean up any existing server references
                    if "localhost:3050" in db_path:
                        db_path = db_path.replace("localhost:3050", "")
                    
                    # Ensure proper path format for Firebird server (needs double slash)
                    if not db_path.startswith("//"):
                        if db_path.startswith("/"):
                            db_path = "/" + db_path  # Make it //path
                        else:
                            db_path = "//" + db_path  # Add double slash
                    
                    # Extract credentials
                    cred_part = parts[0].replace("firebird+fdb://", "")
                    if ":" in cred_part:
                        user, password = cred_part.split(":", 1)
                    else:
                        user, password = "sysdba", "masterkey"
                    
                    # Convert to server connection - use firebird dialect instead of firebird+fdb
                    server_connection = f"firebird://{user}:{password}@localhost:3050{db_path}"
                    logger.info(f"🔄 Converted to server connection: {server_connection}")
                    return server_connection
            
            # Fallback: try to construct server connection
            logger.warning(f"⚠️ Unknown connection format: {connection_string}")
            return f"firebird://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
            
        except Exception as e:
            logger.error(f"❌ Failed to convert connection string: {e}")
            # Return a default server connection as fallback
            return f"firebird://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    
    def _initialize_database(self):
        """Initialize the SQL database connection"""
        try:
            # Convert embedded connection string to server-style for LangChain
            # LangChain SQLDatabase requires server connections, not embedded
            langchain_connection = self._convert_to_server_connection(self.db_connection_string)
            
            logger.info(f"🔌 Connecting to database: {langchain_connection}")
            
            # Try with custom settings to avoid metadata introspection issues
            from sqlalchemy import create_engine, text
            
            # Create engine with minimal reflection to avoid Firebird metadata issues
            engine = create_engine(
                langchain_connection,
                pool_pre_ping=True,
                # Use minimal reflection options
                execution_options={
                    "autocommit": False,
                    "isolation_level": "READ_COMMITTED"
                }
            )
            
            # Test basic connection
            with engine.connect() as conn:
                # Simple test query
                result = conn.execute(text("SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0"))
                table_count = result.scalar()
                logger.info(f"✅ Basic database connection successful. Found ~{table_count} user tables")
            
            # Create SQLDatabase with custom settings
            self.db = SQLDatabase(
                engine=engine,
                sample_rows_in_table_info=1,  # Minimal sampling
                max_string_length=100,
                lazy_table_reflection=True  # Don't reflect all tables immediately
            )
            
            # Test basic functionality
            try:
                # Try to get a simple list of tables without full metadata
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT TRIM(RDB$RELATION_NAME) 
                        FROM RDB$RELATIONS 
                        WHERE RDB$SYSTEM_FLAG = 0 
                        AND RDB$RELATION_TYPE = 0
                        ORDER BY RDB$RELATION_NAME
                        ROWS 10
                    """))
                    sample_tables = [row[0] for row in result]
                    logger.info(f"✅ Found sample tables: {sample_tables[:5]}...")
            except Exception as sample_error:
                logger.warning(f"⚠️ Could not get sample tables: {sample_error}")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            logger.warning(f"Note: LangChain requires Firebird server on localhost:3050")
            
            # Create fallback dummy database for testing/documentation purposes
            logger.info("🔄 Creating fallback LangChain retriever for testing/documentation purposes")
            self.db = None
            self.fallback_mode = True
    
    def _create_agent(self):
        """Create the LangChain SQL Database Agent with enhanced Context7 best practices"""
        try:
            logger.info("🤖 Creating enhanced LangChain SQL Database Agent...")
            
            if not self.db:
                logger.error("❌ Cannot create agent without database connection")
                return
            
            # Create SQL Database Toolkit with enhanced features
            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
            tools = toolkit.get_tools()
            
            # Get enhanced system prompt from LangChain Hub with WINCASA customizations
            enhanced_system_message = None
            
            if HUB_AVAILABLE:
                try:
                    prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
                    system_message = prompt_template.format(
                        dialect="Firebird",
                        top_k=5
                    )
                    
                    # Add WINCASA-specific instructions
                    wincasa_instructions = """\n\nWINDASA Database Context:
- Use Firebird SQL syntax (FIRST instead of LIMIT)
- Core entities: BEWOHNER (residents), EIGENTUEMER (owners), OBJEKTE (properties), KONTEN (accounts)
- Key relationship: ONR connects residents to properties
- Always check table structure before querying
- Use proper JOIN syntax for multi-table queries
- Consider German language field names and business context
"""
                    
                    enhanced_system_message = system_message + wincasa_instructions
                    logger.info("✅ Using LangChain Hub system prompt")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not pull system prompt from hub: {e}")
            
            # Fallback to default system message if hub not available
            if not enhanced_system_message:
                enhanced_system_message = f"""You are an agent designed to interact with a Firebird SQL database for the WINCASA property management system.
Given an input question, create a syntactically correct Firebird query to run, then look at the results and return the answer.
Always limit your query to at most 5 results using FIRST instead of LIMIT.
Core entities: BEWOHNER (residents), EIGENTUEMER (owners), OBJEKTE (properties), KONTEN (accounts).
Always examine the table schema before querying. Do NOT make any DML statements."""
                logger.info("✅ Using fallback system prompt")
            
            # Prepare callbacks
            callbacks = [self.callback_handler] if self.callback_handler else []
            
            # Create ReAct agent with enhanced system prompt and tools
            if LANGGRAPH_AVAILABLE:
                try:
                    # Based on Context7 documentation, create_react_agent expects model, tools, prompt parameters
                    self.agent = create_react_agent(
                        model=self.llm,  # Changed from 'llm' to 'model' 
                        tools=tools,
                        prompt=enhanced_system_message
                    )
                    logger.info("✅ Enhanced LangGraph ReAct SQL Agent created successfully")
                except Exception as react_error:
                    logger.warning(f"⚠️ LangGraph ReAct agent failed: {react_error}")
                    logger.warning(f"Error details: {react_error}")
                    self.agent = None
            else:
                logger.info("⚠️ LangGraph not available, falling back to classic agent")
            
            # Fallback to traditional create_sql_agent if LangGraph not available
            if not self.agent:
                try:
                    self.agent = create_sql_agent(
                        llm=self.llm,
                        db=self.db,
                        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                        verbose=True,
                        max_iterations=3,
                        max_execution_time=30,
                        callbacks=callbacks,
                        handle_parsing_errors=True,
                        return_intermediate_steps=True
                    )
                    logger.info("✅ Classic SQL Agent created successfully")
                except Exception as classic_error:
                    logger.error(f"❌ Classic SQL Agent also failed: {classic_error}")
                    raise
            
        except Exception as e:
            logger.error(f"❌ Failed to create SQL agent: {e}")
            raise
    
    def _enhance_query_with_context(self, user_query: str) -> str:
        """
        Enhance user query with WINCASA-specific context and Context7 best practices.
        
        Args:
            user_query: Original user query
            
        Returns:
            Enhanced query with context
        """
        global_context = get_compact_global_context()
        
        enhanced_query = f"""
WINDASA Property Management Database Context:
{global_context}

User Query: {user_query}

SQL Generation Guidelines:
1. ALWAYS start by examining the table structure using schema tools
2. Use Firebird SQL syntax (FIRST instead of LIMIT)
3. Focus on core entities: BEWOHNER, EIGENTUEMER, OBJEKTE, KONTEN
4. Key relationships: ONR connects residents to properties
5. German field names - translate concepts appropriately
6. Limit results to 5 unless user specifies otherwise
7. Use proper JOINs for multi-table queries
8. Return business-relevant, user-friendly results

Please answer the user's query step by step.
"""
        
        return enhanced_query
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Compatibility method for BaseRetriever interface.
        """
        return self.retrieve_documents(query)
    
    def retrieve_documents(self, query: str, max_docs: int = 10) -> List[Document]:
        """
        Retrieve documents using LangChain SQL Database Agent.
        
        This method converts the SQL agent's query execution into Document format
        for compatibility with the existing retrieval framework.
        
        Args:
            query: User query to process
            max_docs: Maximum documents to return (not applicable for SQL agent)
            
        Returns:
            List of documents containing query results and metadata
        """
        start_time = time.time()
        documents = []
        
        try:
            logger.info(f"🔍 Processing query with LangChain SQL Agent: {query}")
            
            # Enhance query with WINCASA context
            enhanced_query = self._enhance_query_with_context(query)
            
            # Execute query using the agent
            # For LangGraph agents, use the messages format
            if LANGGRAPH_AVAILABLE and hasattr(self.agent, 'invoke'):
                try:
                    # LangGraph ReAct agents expect messages format
                    result = self.agent.invoke({
                        "messages": [("user", enhanced_query)]
                    })
                    # Extract the final message for compatibility
                    if "messages" in result and result["messages"]:
                        agent_output = result["messages"][-1].content if hasattr(result["messages"][-1], 'content') else str(result["messages"][-1])
                        result = {"output": agent_output, "intermediate_steps": []}
                except Exception as langgraph_error:
                    logger.warning(f"⚠️ LangGraph invocation failed, trying classic format: {langgraph_error}")
                    # Fallback to classic format
                    result = self.agent.invoke({
                        "input": enhanced_query
                    })
            else:
                # Classic agent format
                result = self.agent.invoke({
                    "input": enhanced_query
                })
            
            # Extract results
            agent_output = result.get("output", "No output generated")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Create primary result document
            main_doc = Document(
                page_content=f"Query: {query}\n\nResult: {agent_output}",
                metadata={
                    "source": "langchain_sql_agent",
                    "query": query,
                    "result": agent_output,
                    "retrieval_mode": "langchain",
                    "execution_time": time.time() - start_time,
                    "agent_steps": len(intermediate_steps),
                    "success": True
                }
            )
            documents.append(main_doc)
            
            # Add intermediate steps as separate documents for transparency
            for i, (action, observation) in enumerate(intermediate_steps):
                step_doc = Document(
                    page_content=f"Step {i+1}: {action.tool}\nInput: {action.tool_input}\nResult: {observation}",
                    metadata={
                        "source": "langchain_agent_step",
                        "step_number": i + 1,
                        "tool": action.tool,
                        "tool_input": str(action.tool_input),
                        "observation": str(observation),
                        "retrieval_mode": "langchain"
                    }
                )
                documents.append(step_doc)
            
            logger.info(f"✅ LangChain SQL Agent completed. Generated {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"❌ LangChain SQL Agent error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Create error document
            error_doc = Document(
                page_content=f"Query: {query}\n\nError: {str(e)}\n\nThe LangChain SQL Agent encountered an error while processing this query.",
                metadata={
                    "source": "langchain_sql_agent_error",
                    "query": query,
                    "error": str(e),
                    "retrieval_mode": "langchain",
                    "execution_time": time.time() - start_time,
                    "success": False
                }
            )
            documents.append(error_doc)
            
            # Log error to monitoring
            if self.monitor:
                self.monitor.track_retrieval(
                    retrieval_mode="langchain",
                    query=query,
                    documents_retrieved=0,
                    relevance_scores=[],
                    duration=time.time() - start_time,
                    success=False
                )
        
        return documents[:max_docs]  # Respect max_docs parameter
    
    def get_retriever_info(self) -> Dict[str, Any]:
        """Get information about this retriever"""
        table_count = 0
        if self.db:
            try:
                table_count = len(self.db.get_usable_table_names())
            except:
                pass
        
        return {
            "mode": "langchain",
            "type": "LangChain SQL Database Agent",
            "description": "Native LangChain SQL agent with error recovery and schema introspection",
            "database_connection": self.db_connection_string,
            "tables_available": table_count,
            "features": [
                "Enhanced LangGraph ReAct Agent",
                "Context7 best practices integration", 
                "Automatic schema introspection",
                "Built-in error recovery",
                "Chain-of-thought SQL reasoning",
                "Firebird SQL dialect support",
                "WINCASA context integration",
                "LangChain Hub system prompts",
                "SQLDatabaseToolkit integration"
            ],
            "monitoring_enabled": self.monitor is not None
        }


class LangChainSQLRetrieverFallback:
    """
    Fallback LangChain SQL retriever that provides info but can't execute queries.
    
    Used when database connection fails but we still want to maintain the
    LangChain mode functionality for testing and documentation.
    """
    
    def __init__(self, db_connection_string: str, llm, error_message: str):
        self.db_connection_string = db_connection_string
        self.llm = llm
        self.error_message = error_message
        self.monitor = None
        
    def get_relevant_documents(self, query: str):
        """Compatibility method for BaseRetriever interface"""
        return self.retrieve_documents(query)
        
    def retrieve_documents(self, query: str, max_docs: int = 10):
        """Return error documents explaining the connection issue"""
        from langchain_core.documents import Document
        
        error_doc = Document(
            page_content=f"Query: {query}\n\nLangChain SQL Database Agent Error:\n{self.error_message}\n\nThis is a fallback mode. The LangChain integration is properly configured but requires a Firebird server connection to function.",
            metadata={
                "source": "langchain_sql_agent_fallback",
                "query": query,
                "error": self.error_message,
                "retrieval_mode": "langchain",
                "success": False,
                "fallback": True
            }
        )
        
        return [error_doc]
    
    def get_retriever_info(self):
        """Get information about this fallback retriever"""
        return {
            "mode": "langchain",
            "type": "LangChain SQL Database Agent (Fallback)",
            "description": "Fallback mode - configured but no database connection",
            "database_connection": self.db_connection_string,
            "tables_available": 0,
            "features": [
                "Configuration validated",
                "Connection string conversion",
                "Ready for server connection",
                "Firebird SQL dialect support",
                "WINCASA context integration"
            ],
            "monitoring_enabled": False,
            "status": "fallback",
            "error": self.error_message
        }


def test_langchain_sql_retriever():
    """Test the enhanced LangChain SQL retriever with Context7 best practices"""
    print("🧪 Testing Enhanced LangChain SQL Database Agent Retriever...")
    print("✨ Featuring Context7 best practices and LangGraph ReAct Agent")
    
    # Setup (server connection required for LangChain)
    db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050/home/projects/langchain_project/WINCASA2022.FDB"
    
    try:
        from llm_interface import LLMInterface
        
        llm_interface = LLMInterface("gpt-4")
        llm = llm_interface.llm
        
        retriever = LangChainSQLRetriever(
            db_connection_string=db_connection,
            llm=llm,
            enable_monitoring=True
        )
        
        # Test queries
        test_queries = [
            "Wie viele Wohnungen gibt es insgesamt?",
            "Zeige die ersten 2 Bewohner",
            "Welche Eigentümer gibt es?"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print("="*60)
            
            docs = retriever.retrieve_documents(query, max_docs=5)
            
            for i, doc in enumerate(docs):
                print(f"\nDocument {i+1}:")
                print(f"Source: {doc.metadata.get('source', 'unknown')}")
                print(f"Content: {doc.page_content[:200]}...")
                if doc.metadata.get('success'):
                    print("✅ Success")
                else:
                    print("❌ Error")
        
        print(f"\n{'='*60}")
        print("Retriever Info:")
        print(json.dumps(retriever.get_retriever_info(), indent=2))
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    test_langchain_sql_retriever()