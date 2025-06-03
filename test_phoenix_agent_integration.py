#!/usr/bin/env python3
"""
Unit tests for Phoenix monitoring integration in firebird_sql_agent_direct.py and enhanced_retrievers.py

Tests the integration of Phoenix monitoring into:
- FirebirdDirectSQLAgent query execution
- Enhanced retriever document retrieval
- FAISS retriever document retrieval
- Callback handler LLM tracking
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import time
from typing import List, Dict, Any

from langchain_core.documents import Document


class TestFirebirdAgentPhoenixIntegration(unittest.TestCase):
    """Test Phoenix monitoring in FirebirdDirectSQLAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_fdb_interface = Mock()
        self.mock_llm = Mock()
        self.mock_monitor = Mock()
        
        # Patch get_monitor to return our mock
        self.monitor_patcher = patch('firebird_sql_agent_direct.get_monitor')
        self.mock_get_monitor = self.monitor_patcher.start()
        self.mock_get_monitor.return_value = self.mock_monitor
        
        # Patch other dependencies
        self.patches = [
            patch('firebird_sql_agent_direct.FDBDirectInterface'),
            patch('firebird_sql_agent_direct.OpenAIEmbeddings'),
            patch('firebird_sql_agent_direct.DatabaseKnowledgeCompiler')
        ]
        
        for p in self.patches:
            p.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.monitor_patcher.stop()
        for p in self.patches:
            p.stop()
    
    @patch('firebird_sql_agent_direct.FirebirdDirectSQLAgent._load_and_parse_documentation')
    @patch('firebird_sql_agent_direct.FirebirdDirectSQLAgent._initialize_components')
    def test_query_tracking(self, mock_init_components, mock_load_docs):
        """Test that queries are tracked with Phoenix."""
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        
        # Create agent
        agent = FirebirdDirectSQLAgent(
            db_connection_string="test://db",
            llm=self.mock_llm,
            retrieval_mode="enhanced"
        )
        
        # Mock agent components
        agent.sql_agent = Mock()
        agent.sql_agent.invoke.return_value = {
            "output": "Test result"
        }
        agent.active_retriever = Mock()
        agent.active_retriever.get_relevant_documents.return_value = []
        agent.callback_handler = Mock()
        agent.callback_handler.sql_query = "SELECT * FROM test"
        agent.callback_handler.full_log = []
        
        # Execute query
        result = agent.query("Test query")
        
        # Verify Phoenix monitoring calls
        # Should track retrieval
        self.mock_monitor.track_retrieval.assert_called()
        retrieval_call = self.mock_monitor.track_retrieval.call_args
        self.assertEqual(retrieval_call[1]['retrieval_mode'], 'enhanced')
        self.assertEqual(retrieval_call[1]['query'], 'Test query')
        self.assertTrue(retrieval_call[1]['success'])
        
        # Should track query execution
        self.mock_monitor.track_query_execution.assert_called()
        query_call = self.mock_monitor.track_query_execution.call_args
        self.assertEqual(query_call[1]['query'], 'Test query')
        self.assertEqual(query_call[1]['sql'], 'SELECT * FROM test')
        self.assertTrue(query_call[1]['success'])
    
    def test_fdb_query_tool_tracking(self):
        """Test that FDBQueryTool tracks SQL execution."""
        from firebird_sql_agent_direct import FDBQueryTool
        
        # Create tool
        tool = FDBQueryTool(fdb_interface=self.mock_fdb_interface)
        
        # Mock successful query
        self.mock_fdb_interface.run_sql.return_value = [(1, 'test')]
        self.mock_fdb_interface.get_column_names.return_value = ['id', 'name']
        
        # Execute query
        result = tool._run("SELECT * FROM test")
        
        # Verify tracking
        self.mock_monitor.track_query_execution.assert_called_once()
        call_args = self.mock_monitor.track_query_execution.call_args[1]
        self.assertEqual(call_args['sql'], "SELECT * FROM test")
        self.assertEqual(call_args['rows_returned'], 1)
        self.assertTrue(call_args['success'])
    
    def test_callback_handler_llm_tracking(self):
        """Test that DirectFDBCallbackHandler tracks LLM calls."""
        from firebird_sql_agent_direct import DirectFDBCallbackHandler
        
        # Create handler
        handler = DirectFDBCallbackHandler()
        
        # Simulate LLM start
        handler.on_llm_start(
            serialized={"name": "gpt-4"},
            prompts=["Test prompt"]
        )
        
        # Simulate LLM end
        mock_response = Mock()
        mock_response.generations = [[Mock(text="Test response")]]
        handler.on_llm_end(mock_response)
        
        # Verify tracking
        self.mock_monitor.track_llm_call.assert_called_once()
        call_args = self.mock_monitor.track_llm_call.call_args[1]
        self.assertEqual(call_args['model'], 'gpt-4')
        self.assertIn('Test prompt', call_args['prompt'])
        self.assertIn('Test response', call_args['response'])
        self.assertGreater(call_args['tokens_used'], 0)
        self.assertGreater(call_args['duration'], 0)


class TestEnhancedRetrieversPhoenixIntegration(unittest.TestCase):
    """Test Phoenix monitoring in enhanced retrievers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_monitor = Mock()
        
        # Patch get_monitor
        self.monitor_patcher = patch('enhanced_retrievers.get_monitor')
        self.mock_get_monitor = self.monitor_patcher.start()
        self.mock_get_monitor.return_value = self.mock_monitor
        
        # Create test documents
        self.test_docs = [
            Document(
                page_content="Test document 1",
                metadata={"source": "test1.yaml", "score": 0.9}
            ),
            Document(
                page_content="Test document 2", 
                metadata={"source": "test2.yaml", "score": 0.8}
            )
        ]
    
    def tearDown(self):
        """Clean up patches."""
        self.monitor_patcher.stop()
    
    @patch('enhanced_retrievers.OpenAIEmbeddings')
    @patch('enhanced_retrievers.FAISS')
    def test_enhanced_multi_stage_retriever_tracking(self, mock_faiss, mock_embeddings):
        """Test Phoenix tracking in EnhancedMultiStageRetriever."""
        from enhanced_retrievers import EnhancedMultiStageRetriever
        
        # Mock FAISS stores
        mock_store = Mock()
        mock_store.similarity_search.return_value = self.test_docs
        mock_faiss.from_documents.return_value = mock_store
        
        # Create retriever with minimal setup
        retriever = EnhancedMultiStageRetriever(
            parsed_docs=self.test_docs,
            openai_api_key="test-key"
        )
        
        # Mock the stage methods to return test docs
        retriever._stage1_schema_retrieval = Mock(return_value=self.test_docs[:1])
        retriever._stage2_query_specific = Mock(return_value=self.test_docs[1:])
        retriever._stage3_historical_patterns = Mock(return_value=[])
        
        # Get documents
        results = retriever.get_relevant_documents("test query")
        
        # Verify Phoenix tracking
        self.mock_monitor.track_retrieval.assert_called_once()
        call_args = self.mock_monitor.track_retrieval.call_args[1]
        self.assertEqual(call_args['retrieval_mode'], 'enhanced')
        self.assertEqual(call_args['query'], 'test query')
        self.assertEqual(call_args['documents_retrieved'], 2)
        self.assertEqual(call_args['relevance_scores'], [0.9, 0.8])
        self.assertTrue(call_args['success'])
        self.assertGreater(call_args['duration'], 0)
    
    @patch('enhanced_retrievers.OpenAIEmbeddings')
    @patch('enhanced_retrievers.FaissDocumentationRetriever.__init__')
    @patch('enhanced_retrievers.FaissDocumentationRetriever._get_relevant_documents')
    def test_enhanced_faiss_retriever_tracking(self, mock_get_docs, mock_init, mock_embeddings):
        """Test Phoenix tracking in EnhancedFaissRetriever."""
        from enhanced_retrievers import EnhancedFaissRetriever
        
        # Mock parent class
        mock_init.return_value = None
        mock_get_docs.return_value = self.test_docs
        
        # Create retriever
        retriever = EnhancedFaissRetriever(
            parsed_docs=self.test_docs,
            openai_api_key="test-key"
        )
        retriever._enhanced_docs = self.test_docs
        
        # Get documents
        results = retriever._get_relevant_documents("test query")
        
        # Verify Phoenix tracking
        self.mock_monitor.track_retrieval.assert_called_once()
        call_args = self.mock_monitor.track_retrieval.call_args[1]
        self.assertEqual(call_args['retrieval_mode'], 'faiss')
        self.assertEqual(call_args['query'], 'test query')
        self.assertEqual(call_args['documents_retrieved'], 2)
        self.assertEqual(call_args['relevance_scores'], [0.9, 0.8])
        self.assertTrue(call_args['success'])
    
    def test_retrieval_error_tracking(self):
        """Test that retrieval errors are tracked."""
        from enhanced_retrievers import EnhancedMultiStageRetriever
        
        # Create retriever that will fail
        with patch('enhanced_retrievers.EnhancedMultiStageRetriever._stage1_schema_retrieval') as mock_stage1:
            mock_stage1.side_effect = Exception("Test error")
            
            retriever = EnhancedMultiStageRetriever(
                parsed_docs=[],
                openai_api_key="test-key"
            )
            
            # Attempt retrieval (should fail)
            with self.assertRaises(Exception):
                retriever.get_relevant_documents("test query")
            
            # Verify error tracking
            self.mock_monitor.track_retrieval.assert_called_once()
            call_args = self.mock_monitor.track_retrieval.call_args[1]
            self.assertEqual(call_args['retrieval_mode'], 'enhanced')
            self.assertEqual(call_args['query'], 'test query')
            self.assertEqual(call_args['documents_retrieved'], 0)
            self.assertEqual(call_args['relevance_scores'], [])
            self.assertFalse(call_args['success'])


class TestPhoenixIntegrationEndToEnd(unittest.TestCase):
    """End-to-end integration tests with mocked Phoenix."""
    
    @patch('phoenix_monitoring.px')
    @patch('phoenix_monitoring.PHOENIX_AVAILABLE', True)
    def test_full_query_flow_monitoring(self, mock_px):
        """Test complete query flow with all monitoring points."""
        from phoenix_monitoring import PhoenixMonitor
        from firebird_sql_agent_direct import DirectFDBCallbackHandler
        
        # Create real monitor
        monitor = PhoenixMonitor(enable_ui=False)
        
        # Create callback handler
        handler = DirectFDBCallbackHandler()
        
        # Simulate query flow
        # 1. Track retrieval
        monitor.track_retrieval(
            retrieval_mode="enhanced",
            query="Find users",
            documents_retrieved=3,
            relevance_scores=[0.9, 0.8, 0.7],
            duration=1.5,
            success=True
        )
        
        # 2. Track LLM call (through handler)
        handler.on_llm_start({}, ["Generate SQL for finding users"])
        time.sleep(0.1)  # Simulate processing
        mock_response = Mock()
        mock_response.generations = [[Mock(text="SELECT * FROM users")]]
        handler.on_llm_end(mock_response)
        
        # 3. Track SQL execution
        monitor.track_query_execution(
            query="Find users",
            sql="SELECT * FROM users",
            execution_time=0.5,
            rows_returned=10,
            success=True
        )
        
        # Get final metrics
        summary = monitor.get_metrics_summary()
        
        # Verify complete tracking
        self.assertEqual(summary['total_queries'], 1)
        self.assertEqual(summary['success_rate'], 1.0)
        self.assertGreater(summary['total_tokens'], 0)
        self.assertIn('enhanced', summary['retrieval_performance'])
        
        enhanced_stats = summary['retrieval_performance']['enhanced']
        self.assertEqual(enhanced_stats['total_retrievals'], 1)
        self.assertEqual(enhanced_stats['successful_retrievals'], 1)
        self.assertAlmostEqual(enhanced_stats['avg_relevance'], 0.8, places=1)


if __name__ == '__main__':
    unittest.main()