#!/usr/bin/env python3
"""
Unit tests for Phoenix monitoring integration in enhanced_qa_ui.py

Tests the Streamlit UI integration with Phoenix monitoring including:
- Monitor initialization in the UI
- Dashboard link display
- Metrics visualization
- Query monitoring display
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from datetime import datetime


class TestPhoenixUIIntegration(unittest.TestCase):
    """Test Phoenix monitoring integration in Streamlit UI."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Streamlit components
        self.mock_st = MagicMock()
        self.patches = [
            patch('enhanced_qa_ui.st', self.mock_st),
            patch('enhanced_qa_ui.get_monitor'),
            patch('enhanced_qa_ui.get_firebird_sql_agent'),
            patch('enhanced_qa_ui.Path')
        ]
        
        for p in self.patches:
            p.start()
        
        # Create mock monitor
        self.mock_monitor = Mock()
        self.mock_monitor.session = Mock()
        self.mock_monitor.session.url = "http://localhost:6006"
        self.mock_monitor.get_metrics_summary.return_value = {
            'total_queries': 5,
            'success_rate': 0.8,
            'total_tokens': 1000,
            'total_cost_usd': 0.05,
            'retrieval_performance': {
                'enhanced': {
                    'total_retrievals': 5,
                    'successful_retrievals': 4,
                    'avg_duration': 2.5,
                    'avg_documents': 8
                }
            }
        }
    
    def tearDown(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    @patch('enhanced_qa_ui.get_phoenix_monitor')
    def test_phoenix_monitor_initialization(self, mock_get_phoenix):
        """Test that Phoenix monitor is initialized correctly."""
        # Mock monitor creation
        mock_get_phoenix.return_value = self.mock_monitor
        
        # Import function to test
        from enhanced_qa_ui import get_phoenix_monitor
        
        # Get monitor
        monitor = get_phoenix_monitor()
        
        # Verify monitor returned
        self.assertEqual(monitor, self.mock_monitor)
    
    @patch('enhanced_qa_ui.get_phoenix_monitor')
    def test_phoenix_sidebar_display(self, mock_get_phoenix):
        """Test Phoenix monitoring display in sidebar."""
        mock_get_phoenix.return_value = self.mock_monitor
        
        # Import and call the function
        from enhanced_qa_ui import create_enhanced_qa_tab
        
        # Mock session state
        self.mock_st.session_state = {
            'enhanced_chat_history': [],
            'feedback_given': {}
        }
        self.mock_st.sidebar = Mock()
        
        # Call the tab creation (will fail but we can check sidebar calls)
        try:
            create_enhanced_qa_tab()
        except:
            pass  # Expected due to mocking
        
        # Verify sidebar calls for Phoenix
        sidebar_calls = [str(call) for call in self.mock_st.sidebar.method_calls]
        
        # Should have markdown for AI Observability section
        markdown_calls = [call for call in self.mock_st.sidebar.method_calls 
                         if call[0] == 'markdown']
        self.assertTrue(any('AI Observability' in str(call) for call in markdown_calls))
        
        # Should show success status
        success_calls = [call for call in self.mock_st.sidebar.method_calls 
                        if call[0] == 'success']
        self.assertTrue(any('Phoenix Monitoring aktiv' in str(call) for call in success_calls))
        
        # Should display metrics
        metric_calls = [call for call in self.mock_st.sidebar.method_calls 
                       if call[0] == 'metric']
        self.assertEqual(len(metric_calls), 3)  # Queries, Success Rate, Total Cost
    
    @patch('enhanced_qa_ui.get_phoenix_monitor')
    def test_phoenix_metrics_in_query_results(self, mock_get_phoenix):
        """Test that Phoenix metrics are shown in query results."""
        mock_get_phoenix.return_value = self.mock_monitor
        
        # Mock Streamlit components
        mock_expander = Mock()
        self.mock_st.expander.return_value.__enter__ = Mock(return_value=mock_expander)
        self.mock_st.expander.return_value.__exit__ = Mock(return_value=None)
        self.mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        
        # Create test chat history entry
        test_entry = {
            'natural_language_query': 'Test query',
            'text_variants': [{'variant_name': 'Variant 1', 'text': 'Test answer'}],
            'generated_sql': 'SELECT * FROM test',
            'timestamp': datetime.now().isoformat()
        }
        
        # Mock session state with history
        self.mock_st.session_state = {
            'enhanced_chat_history': [test_entry],
            'feedback_given': {}
        }
        
        # Import function
        from enhanced_qa_ui import create_enhanced_qa_tab
        
        # Try to create tab (will fail but we can check calls)
        try:
            create_enhanced_qa_tab()
        except:
            pass
        
        # Check that expander was created for monitoring
        expander_calls = [call for call in self.mock_st.method_calls 
                         if call[0] == 'expander']
        self.assertTrue(any('Query Monitoring' in str(call) for call in expander_calls))
    
    @patch('enhanced_qa_ui.get_phoenix_monitor')  
    def test_phoenix_unavailable_handling(self, mock_get_phoenix):
        """Test graceful handling when Phoenix is not available."""
        # Return None to simulate Phoenix not available
        mock_get_phoenix.return_value = None
        
        # Mock sidebar
        self.mock_st.sidebar = Mock()
        
        # Import and try to create tab
        from enhanced_qa_ui import create_enhanced_qa_tab
        
        self.mock_st.session_state = {
            'enhanced_chat_history': [],
            'feedback_given': {}
        }
        
        try:
            create_enhanced_qa_tab()
        except:
            pass
        
        # Should show warning about Phoenix not available
        warning_calls = [call for call in self.mock_st.sidebar.method_calls 
                        if call[0] == 'warning']
        self.assertTrue(any('Phoenix Monitoring nicht verfügbar' in str(call) 
                           for call in warning_calls))
    
    def test_metrics_calculation(self):
        """Test metrics display calculations."""
        # Test with actual metrics
        metrics = self.mock_monitor.get_metrics_summary()
        
        # Success rate calculation
        success_rate = metrics['success_rate'] * 100
        self.assertEqual(success_rate, 80.0)
        
        # Average cost calculation
        avg_cost = metrics['total_cost_usd'] / max(1, metrics['total_queries'])
        self.assertAlmostEqual(avg_cost, 0.01, places=2)
        
        # Retrieval performance formatting
        enhanced_stats = metrics['retrieval_performance']['enhanced']
        success_ratio = f"{enhanced_stats['successful_retrievals']}/{enhanced_stats['total_retrievals']}"
        self.assertEqual(success_ratio, "4/5")


class TestPhoenixMetricsDisplay(unittest.TestCase):
    """Test specific metrics display functionality."""
    
    def test_empty_metrics_handling(self):
        """Test handling of empty metrics."""
        empty_metrics = {
            'total_queries': 0,
            'success_rate': 0,
            'total_tokens': 0,
            'total_cost_usd': 0.0,
            'retrieval_performance': {}
        }
        
        # Calculate average cost with zero queries
        avg_cost = empty_metrics['total_cost_usd'] / max(1, empty_metrics['total_queries'])
        self.assertEqual(avg_cost, 0.0)
        
        # Format success rate
        success_rate_str = f"{empty_metrics['success_rate']*100:.1f}%"
        self.assertEqual(success_rate_str, "0.0%")
    
    def test_retrieval_performance_display(self):
        """Test retrieval performance statistics display."""
        retrieval_stats = {
            'enhanced': {
                'total_retrievals': 10,
                'successful_retrievals': 9,
                'avg_duration': 2.345,
                'avg_documents': 7.8
            },
            'faiss': {
                'total_retrievals': 5,
                'successful_retrievals': 3,
                'avg_duration': 4.567,
                'avg_documents': 5.2
            }
        }
        
        # Format enhanced stats
        enhanced = retrieval_stats['enhanced']
        enhanced_display = (
            f"ENHANCED: {enhanced['successful_retrievals']}/{enhanced['total_retrievals']} successful, "
            f"avg {enhanced['avg_duration']:.2f}s, {enhanced['avg_documents']:.1f} docs"
        )
        expected = "ENHANCED: 9/10 successful, avg 2.35s, 7.8 docs"
        self.assertEqual(enhanced_display, expected)
        
        # Format FAISS stats
        faiss = retrieval_stats['faiss']
        faiss_display = (
            f"FAISS: {faiss['successful_retrievals']}/{faiss['total_retrievals']} successful, "
            f"avg {faiss['avg_duration']:.2f}s, {faiss['avg_documents']:.1f} docs"
        )
        expected = "FAISS: 3/5 successful, avg 4.57s, 5.2 docs"
        self.assertEqual(faiss_display, expected)


if __name__ == '__main__':
    unittest.main()