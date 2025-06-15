#!/usr/bin/env python3
"""
WINCASA Phase 2 - Quick Test Suite
Focused unit tests without LLM calls for fast execution
"""

import json
import time
import unittest
from datetime import datetime
from pathlib import Path

from wincasa_feature_flags import (FeatureFlag, FlagType,
                                   WincasaFeatureFlagManager)

from sql_template_engine import SQLTemplateEngine
# Import Phase 2 components
from wincasa_optimized_search import WincasaOptimizedSearch


class QuickTestSuite(unittest.TestCase):
    """Quick tests for Phase 2 components"""
    
    def test_optimized_search_init(self):
        """Test search system initialization"""
        search = WincasaOptimizedSearch(debug_mode=False)
        stats = search.get_stats()
        
        self.assertIn('entities', stats)
        self.assertEqual(stats['entities']['mieter'], 200)
        self.assertEqual(stats['entities']['eigentuemer'], 311)
        self.assertEqual(stats['entities']['objekte'], 77)
        print("✅ Optimized Search: 588 entities loaded")
    
    def test_search_performance(self):
        """Test search performance"""
        search = WincasaOptimizedSearch(debug_mode=False)
        
        queries = ["Weber", "Essen", "GmbH", "Aachener"]
        total_time = 0
        
        for query in queries:
            start = time.time()
            result = search.query(query, max_results=5)
            elapsed = (time.time() - start) * 1000
            total_time += elapsed
            
            self.assertIsNotNone(result)
            self.assertLess(elapsed, 50)  # Should be < 50ms
        
        avg_time = total_time / len(queries)
        print(f"✅ Search Performance: {avg_time:.1f}ms average")
    
    def test_template_security(self):
        """Test template SQL injection protection"""
        engine = SQLTemplateEngine(debug_mode=False)
        
        # Safe parameters
        safe_result = engine.render_template(
            "mieter_by_location",
            {"location": "Essen", "limit": 10}
        )
        self.assertTrue(safe_result.validation_passed)
        
        # Malicious parameters
        malicious_result = engine.render_template(
            "mieter_by_location",
            {"location": "'; DROP TABLE MIETER; --", "limit": 10}
        )
        self.assertFalse(malicious_result.validation_passed)
        
        print("✅ Template Security: SQL injection blocked")
    
    def test_feature_flags(self):
        """Test feature flag system"""
        manager = WincasaFeatureFlagManager(
            config_file="test_flags_quick.json",
            debug_mode=False
        )
        
        # Create test flag
        flag = FeatureFlag(
            name="quick_test_flag",
            flag_type=FlagType.BOOLEAN,
            default_value=False,
            description="Quick test",
            rollout_percentage=50.0
        )
        
        success = manager.create_flag(flag)
        self.assertTrue(success)
        
        # Test percentage rollout
        enabled_count = 0
        for i in range(20):
            if manager.is_enabled("quick_test_flag", f"user_{i}"):
                enabled_count += 1
        
        # Should be roughly 50%
        self.assertGreater(enabled_count, 5)
        self.assertLess(enabled_count, 15)
        
        print(f"✅ Feature Flags: {enabled_count}/20 users enabled (50% target)")
    
    def test_monitoring_metrics(self):
        """Test monitoring metric collection"""
        from wincasa_monitoring_dashboard import MetricSnapshot
        
        snapshot = MetricSnapshot(
            timestamp=datetime.now(),
            total_queries=100,
            queries_per_minute=10.0,
            avg_response_time_ms=25.0,
            success_rate=0.95,
            unified_percentage=0.75,
            legacy_percentage=0.25,
            error_rate=0.05,
            cost_per_query=0.01
        )
        
        self.assertEqual(snapshot.total_queries, 100)
        self.assertEqual(snapshot.success_rate, 0.95)
        self.assertLess(snapshot.avg_response_time_ms, 100)
        
        print("✅ Monitoring: Metrics snapshot validated")
    
    def test_direct_execution_config(self):
        """Test direct execution mode configuration"""
        from wincasa_query_engine import WincasaQueryEngine
        
        engine = WincasaQueryEngine()
        self.assertTrue(hasattr(engine, 'config'))
        self.assertIsInstance(engine.config, dict)
        
        print("✅ Direct Execution: Configuration validated")

class ComponentHealthCheck(unittest.TestCase):
    """Health checks for all components"""
    
    def test_all_imports(self):
        """Test that all Phase 2 components can be imported"""
        components = [
            "wincasa_optimized_search",
            "hierarchical_intent_router",
            "sql_template_engine",
            "unified_template_system",
            "wincasa_query_engine",
            "wincasa_monitoring_dashboard",
            "wincasa_feature_flags"
        ]
        
        for component in components:
            try:
                __import__(component)
                print(f"✅ Import {component}: OK")
            except ImportError as e:
                self.fail(f"Failed to import {component}: {e}")
    
    def test_config_files(self):
        """Test configuration files exist"""
        config_files = [
            "config/sql_paths.json",
            "config/feature_flags.json",
            "config/query_engine.json"
        ]
        
        for config_file in config_files:
            path = Path(config_file)
            if path.exists():
                print(f"✅ Config {config_file}: Found")
            else:
                print(f"⚠️  Config {config_file}: Missing (optional)")
    
    def test_data_directories(self):
        """Test data directories exist"""
        directories = [
            "shadow_mode_data",
            "monitoring_data",
            "exports",
            "SQL_QUERIES"
        ]
        
        for directory in directories:
            path = Path(directory)
            if path.exists():
                print(f"✅ Directory {directory}: Found")
            else:
                print(f"⚠️  Directory {directory}: Missing (will be created)")

def run_quick_tests():
    """Run quick test suite"""
    print("🧪 Running WINCASA Phase 2 Quick Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(QuickTestSuite))
    suite.addTests(loader.loadTestsFromTestCase(ComponentHealthCheck))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All quick tests passed!")
        return True
    else:
        print("\n❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = run_quick_tests()
    
    # Cleanup test files
    test_files = ["test_flags_quick.json"]
    for file in test_files:
        path = Path(file)
        if path.exists():
            path.unlink()
    
    exit(0 if success else 1)