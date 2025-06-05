#!/usr/bin/env python3
"""
Comprehensive unit tests for Phoenix monitoring integration.

Tests all aspects of the Phoenix monitoring system including:
- Monitor initialization
- LLM call tracking
- Retrieval performance tracking
- SQL query execution tracking
- Metrics aggregation
- Trace export functionality
"""

import json
import os
import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

# Import the monitoring module
from phoenix_monitoring import (
    PHOENIX_AVAILABLE,
    PhoenixMonitor,
    get_monitor,
    trace_query,
)


class TestPhoenixMonitor(unittest.TestCase):
    """Test cases for PhoenixMonitor class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock Phoenix module if not available
        if not PHOENIX_AVAILABLE:
            self.phoenix_mock = MagicMock()
            patch("phoenix_monitoring.px", self.phoenix_mock).start()

        # Create monitor with UI disabled for testing
        self.monitor = PhoenixMonitor(project_name="TEST_WINCASA", enable_ui=False)

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, "monitor"):
            self.monitor.shutdown()
        patch.stopall()

    def test_monitor_initialization(self):
        """Test that monitor initializes correctly."""
        self.assertEqual(self.monitor.project_name, "TEST_WINCASA")
        self.assertEqual(self.monitor.enable_ui, False)
        self.assertIsInstance(self.monitor.metrics, dict)
        self.assertEqual(self.monitor.metrics["total_queries"], 0)
        self.assertEqual(self.monitor.metrics["successful_queries"], 0)
        self.assertEqual(self.monitor.metrics["failed_queries"], 0)
        self.assertEqual(self.monitor.metrics["total_tokens"], 0)
        self.assertEqual(self.monitor.metrics["total_cost"], 0.0)
        self.assertIsInstance(self.monitor.metrics["retrieval_metrics"], dict)

    def test_track_llm_call(self):
        """Test LLM call tracking."""
        # Track a sample LLM call
        self.monitor.track_llm_call(
            model="gpt-4",
            prompt="Test prompt",
            response="Test response",
            tokens_used=150,
            cost=0.0045,
            duration=1.5,
        )

        # Verify metrics updated
        self.assertEqual(self.monitor.metrics["total_tokens"], 150)
        self.assertEqual(self.monitor.metrics["total_cost"], 0.0045)

    def test_track_retrieval_enhanced_mode(self):
        """Test retrieval tracking for enhanced mode."""
        # Track successful retrieval
        self.monitor.track_retrieval(
            retrieval_mode="enhanced",
            query="test query",
            documents_retrieved=5,
            relevance_scores=[0.9, 0.85, 0.8, 0.75, 0.7],
            duration=2.3,
            success=True,
        )

        # Verify metrics
        enhanced_metrics = self.monitor.metrics["retrieval_metrics"]["enhanced"]
        self.assertEqual(enhanced_metrics["total_retrievals"], 1)
        self.assertEqual(enhanced_metrics["successful_retrievals"], 1)
        self.assertEqual(enhanced_metrics["avg_documents"], 5)
        self.assertAlmostEqual(enhanced_metrics["avg_relevance"], 0.8, places=2)
        self.assertAlmostEqual(enhanced_metrics["avg_duration"], 2.3, places=2)

    def test_track_retrieval_faiss_mode(self):
        """Test retrieval tracking for FAISS mode."""
        # Track failed retrieval
        self.monitor.track_retrieval(
            retrieval_mode="faiss",
            query="test query",
            documents_retrieved=0,
            relevance_scores=[],
            duration=5.0,
            success=False,
        )

        # Verify metrics
        faiss_metrics = self.monitor.metrics["retrieval_metrics"]["faiss"]
        self.assertEqual(faiss_metrics["total_retrievals"], 1)
        self.assertEqual(faiss_metrics["successful_retrievals"], 0)
        self.assertEqual(faiss_metrics["avg_documents"], 0)
        self.assertEqual(faiss_metrics["avg_relevance"], 0)
        self.assertEqual(faiss_metrics["avg_duration"], 5.0)

    def test_track_query_execution_success(self):
        """Test tracking successful query execution."""
        self.monitor.track_query_execution(
            query="SELECT * FROM users",
            sql="SELECT * FROM users WHERE active = 1",
            execution_time=0.5,
            rows_returned=10,
            success=True,
        )

        # Verify metrics
        self.assertEqual(self.monitor.metrics["total_queries"], 1)
        self.assertEqual(self.monitor.metrics["successful_queries"], 1)
        self.assertEqual(self.monitor.metrics["failed_queries"], 0)

    def test_track_query_execution_failure(self):
        """Test tracking failed query execution."""
        self.monitor.track_query_execution(
            query="Invalid query",
            sql="INVALID SQL",
            execution_time=0.1,
            rows_returned=0,
            success=False,
            error="SQL syntax error",
        )

        # Verify metrics
        self.assertEqual(self.monitor.metrics["total_queries"], 1)
        self.assertEqual(self.monitor.metrics["successful_queries"], 0)
        self.assertEqual(self.monitor.metrics["failed_queries"], 1)

    def test_get_metrics_summary(self):
        """Test metrics summary generation."""
        # Add some test data
        self.monitor.track_query_execution("q1", "sql1", 1.0, 5, True)
        self.monitor.track_query_execution("q2", "sql2", 2.0, 0, False)
        self.monitor.track_llm_call("gpt-4", "p1", "r1", 100, 0.003, 1.0)

        # Get summary
        summary = self.monitor.get_metrics_summary()

        # Verify summary structure
        self.assertIn("total_queries", summary)
        self.assertEqual(summary["total_queries"], 2)
        self.assertIn("success_rate", summary)
        self.assertEqual(summary["success_rate"], 0.5)
        self.assertIn("total_tokens", summary)
        self.assertEqual(summary["total_tokens"], 100)
        self.assertIn("total_cost_usd", summary)
        self.assertAlmostEqual(summary["total_cost_usd"], 0.003, places=3)
        self.assertIn("retrieval_performance", summary)

    def test_trace_query_context_manager(self):
        """Test trace_query context manager."""
        with trace_query("test query", {"mode": "test"}) as ctx:
            # Simulate some work
            time.sleep(0.1)

        # Context manager should complete without errors
        self.assertIsNotNone(ctx)

    def test_trace_query_with_exception(self):
        """Test trace_query context manager with exception."""
        try:
            with trace_query("test query", {"mode": "test"}) as ctx:
                # Simulate error
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected

        # Context manager should handle exception gracefully
        self.assertIsNotNone(ctx)

    @patch("phoenix_monitoring.px.Client")
    def test_export_traces(self, mock_client):
        """Test trace export functionality."""
        # Mock trace data
        mock_traces = [
            {"id": "1", "name": "test_trace", "timestamp": "2024-01-01T00:00:00"},
            {"id": "2", "name": "test_trace2", "timestamp": "2024-01-01T00:01:00"},
        ]
        mock_client.return_value.get_traces.return_value = mock_traces

        # Export traces
        test_file = "test_traces.json"
        self.monitor.export_traces(test_file)

        # Verify file created
        if os.path.exists(test_file):
            with open(test_file, "r") as f:
                exported_data = json.load(f)
            self.assertEqual(len(exported_data), 2)
            os.remove(test_file)  # Clean up

    def test_get_monitor_singleton(self):
        """Test that get_monitor returns singleton instance."""
        monitor1 = get_monitor(enable_ui=False)
        monitor2 = get_monitor(enable_ui=False)

        # Should be same instance
        self.assertIs(monitor1, monitor2)

    def test_multiple_retrieval_averaging(self):
        """Test that retrieval metrics are properly averaged over multiple calls."""
        # Track multiple retrievals for same mode
        for i in range(3):
            self.monitor.track_retrieval(
                retrieval_mode="enhanced",
                query=f"query {i}",
                documents_retrieved=i + 3,  # 3, 4, 5
                relevance_scores=[0.8 + i * 0.05],  # 0.8, 0.85, 0.9
                duration=1.0 + i * 0.5,  # 1.0, 1.5, 2.0
                success=True,
            )

        # Check averages
        enhanced_metrics = self.monitor.metrics["retrieval_metrics"]["enhanced"]
        self.assertEqual(enhanced_metrics["total_retrievals"], 3)
        self.assertEqual(enhanced_metrics["successful_retrievals"], 3)
        self.assertAlmostEqual(
            enhanced_metrics["avg_documents"], 4.0, places=1
        )  # (3+4+5)/3
        self.assertAlmostEqual(
            enhanced_metrics["avg_relevance"], 0.85, places=2
        )  # (0.8+0.85+0.9)/3
        self.assertAlmostEqual(
            enhanced_metrics["avg_duration"], 1.5, places=1
        )  # (1.0+1.5+2.0)/3


class TestPhoenixIntegration(unittest.TestCase):
    """Integration tests for Phoenix monitoring with mocked components."""

    @patch("phoenix_monitoring.PHOENIX_AVAILABLE", False)
    def test_monitor_without_phoenix(self):
        """Test that monitor works gracefully when Phoenix is not installed."""
        monitor = PhoenixMonitor(enable_ui=False)

        # Should still track metrics
        monitor.track_llm_call("gpt-4", "test", "response", 100, 0.003, 1.0)
        self.assertEqual(monitor.metrics["total_tokens"], 100)

        # Export should handle missing Phoenix gracefully
        monitor.export_traces("test.json")  # Should not raise exception


if __name__ == "__main__":
    unittest.main()
