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
from langchain.agents import AgentType
from langchain_community.utilities import SQLDatabase
from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel
from langchain.callbacks.base import BaseCallbackHandler

from phoenix_monitoring import get_monitor
from global_context import get_compact_global_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            self.monitor.log_retrieval_event(
                mode="langchain",
                query=str(outputs.get('input', 'unknown')),
                documents_retrieved=len(self.agent_steps),
                duration_seconds=duration,
                success=True,
                metadata={
                    "agent_steps": len(self.agent_steps),
                    "final_output": outputs.get('output', 'no output')
                }
            )
    
    def on_chain_error(self, error, **kwargs):
        """Called when chain encounters an error"""
        duration = time.time() - self.start_time if self.start_time else 0
        logger.error(f"❌ Chain Error after {duration:.2f}s: {error}")
        
        if self.monitor:
            self.monitor.log_retrieval_event(
                mode="langchain", 
                query="error_query",
                documents_retrieved=0,
                duration_seconds=duration,
                success=False,
                metadata={
                    "error": str(error),
                    "agent_steps": len(self.agent_steps)
                }
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
    
    def _initialize_database(self):
        """Initialize the SQL database connection"""
        try:
            # Use the connection string as-is for LangChain SQLDatabase
            # The system expects server-style connections with localhost:3050
            langchain_connection = self.db_connection_string
            
            logger.info(f"🔌 Connecting to database: {langchain_connection}")
            self.db = SQLDatabase.from_uri(langchain_connection)
            
            # Test the connection
            table_names = self.db.get_usable_table_names()
            logger.info(f"✅ Database connected. Found {len(table_names)} tables")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _create_agent(self):
        """Create the LangChain SQL Database Agent"""
        try:
            logger.info("🤖 Creating LangChain SQL Database Agent...")
            
            # Prepare callbacks
            callbacks = [self.callback_handler] if self.callback_handler else []
            
            self.agent = create_sql_agent(
                llm=self.llm,
                db=self.db,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                max_iterations=3,  # Limit iterations to prevent infinite loops
                max_execution_time=30,  # 30 second timeout
                callbacks=callbacks,
                handle_parsing_errors=True,  # Handle LLM parsing errors gracefully
                return_intermediate_steps=True  # For monitoring
            )
            
            logger.info("✅ LangChain SQL Agent created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create SQL agent: {e}")
            raise
    
    def _enhance_query_with_context(self, user_query: str) -> str:
        """
        Enhance user query with WINCASA-specific context for better understanding.
        
        Args:
            user_query: Original user query
            
        Returns:
            Enhanced query with context
        """
        global_context = get_compact_global_context()
        
        enhanced_query = f"""
{global_context}

Based on the WINCASA database context above, please answer this query:
{user_query}

Important guidelines:
- Use Firebird SQL syntax (e.g., FIRST instead of LIMIT)
- Focus on the core entities: BEWOHNER, EIGENTUEMER, OBJEKTE, KONTEN
- Consider the key relationships shown in the context
- Return practical, business-relevant results
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
                self.monitor.log_retrieval_event(
                    mode="langchain",
                    query=query,
                    documents_retrieved=0,
                    duration_seconds=time.time() - start_time,
                    success=False,
                    metadata={"error": str(e)}
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
                "Automatic schema introspection",
                "Built-in error recovery",
                "Chain-of-thought SQL reasoning",
                "Firebird SQL dialect support",
                "WINCASA context integration"
            ],
            "monitoring_enabled": self.monitor is not None
        }


def test_langchain_sql_retriever():
    """Test the LangChain SQL retriever with sample queries"""
    print("🧪 Testing LangChain SQL Database Agent Retriever...")
    
    # Setup (mock for testing - replace with actual config)
    db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
    
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