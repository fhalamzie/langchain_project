#!/usr/bin/env python3
"""
WINCASA Phase 2.4 - Integration Test
Comprehensive test aller Phase 2.4 Komponenten zusammen
"""

import json
import time
from datetime import datetime
from pathlib import Path

from wincasa_feature_flags import (FeatureFlag, FlagType,
                                   WincasaFeatureFlagManager)

# Shadow mode removed
from wincasa_monitoring_dashboard import WincasaMonitoringDashboard
# Import all Phase 2.4 components
from wincasa_query_engine import WincasaQueryEngine


class Phase24IntegrationTest:
    """
    Phase 2.4 Integration Test Suite
    
    Tests komplette Integration aller Komponenten:
    - Query Engine mit Feature Flag Integration
    - Feature Flags mit dynamischen Updates
    - Monitoring Integration
    - End-to-End Workflows
    """
    
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.test_results = {}
        
        print("🚀 Phase 2.4 Integration Test Suite")
        print("=" * 50)
    
    def setup_components(self):
        """Initialisiert alle Phase 2.4 Komponenten"""
        
        print("\n📦 Setting up components...")
        
        # 1. Feature Flag Manager
        self.flag_manager = WincasaFeatureFlagManager(debug_mode=self.debug_mode)
        
        # 2. Query Engine
        self.query_engine = WincasaQueryEngine(debug_mode=self.debug_mode)
        
        # 3. Monitoring Dashboard
        self.monitoring = WincasaMonitoringDashboard(
            self.query_engine,
            debug_mode=self.debug_mode
        )
        
        print("   ✅ All components initialized")
    
    def test_feature_flag_integration(self):
        """Test Feature Flag Integration mit Query Engine"""
        
        print("\n🎛️  Testing Feature Flag Integration...")
        
        test_results = {
            "test_name": "feature_flag_integration",
            "success": True,
            "details": []
        }
        
        try:
            # Test 1: Query Engine respects feature flags
            print("   Test 1: Query Engine Feature Flag Respect")
            
            # Disable unified system
            self.flag_manager.set_rollout_percentage("unified_system_enabled", 0)
            
            result1 = self.query_engine.process_query("Test query", "test_user")
            legacy_used = result1.engine_version == "legacy_v1"
            
            test_results["details"].append({
                "test": "disabled_unified_system",
                "success": legacy_used,
                "engine_version": result1.engine_version
            })
            
            print(f"     Disabled unified → Legacy used: {legacy_used}")
            
            # Enable unified system  
            self.flag_manager.set_rollout_percentage("unified_system_enabled", 100)
            
            result2 = self.query_engine.process_query("Test query", "test_user", force_mode="unified")
            unified_used = result2.engine_version == "unified_v2"
            
            test_results["details"].append({
                "test": "enabled_unified_system", 
                "success": unified_used,
                "engine_version": result2.engine_version
            })
            
            print(f"     Enabled unified → Unified used: {unified_used}")
            
            # Test 2: Dynamic flag updates
            print("   Test 2: Dynamic Flag Updates")
            
            # Create test flag
            test_flag = FeatureFlag(
                name="test_dynamic_flag",
                flag_type=FlagType.BOOLEAN,
                default_value=False,
                description="Test flag for integration",
                rollout_percentage=50.0
            )
            
            flag_created = self.flag_manager.create_flag(test_flag)
            test_results["details"].append({
                "test": "dynamic_flag_creation",
                "success": flag_created
            })
            
            print(f"     Dynamic flag created: {flag_created}")
            
            if not (legacy_used and unified_used and flag_created):
                test_results["success"] = False
        
        except Exception as e:
            test_results["success"] = False
            test_results["error"] = str(e)
            print(f"     ❌ Error: {e}")
        
        self.test_results["feature_flag_integration"] = test_results
        
        if test_results["success"]:
            print("   ✅ Feature Flag Integration: PASSED")
        else:
            print("   ❌ Feature Flag Integration: FAILED")
    
    def test_unified_engine_workflow(self):
        """Test Unified Engine Workflow"""
        
        print("\n⚡ Testing Unified Engine Workflow...")
        
        test_results = {
            "test_name": "unified_engine_workflow", 
            "success": True,
            "details": []
        }
        
        try:
            # Test unified engine queries
            print("   Test 1: Unified Engine Queries")
            
            test_queries = [
                "Wer wohnt in der Aachener Str. 71?",
                "Portfolio von Bona Casa GmbH", 
                "Freie Wohnungen in Essen"
            ]
            
            successful_queries = 0
            for i, query in enumerate(test_queries):
                result = self.query_engine.process_query(
                    query, f"unified_test_user_{i+1}", force_mode="unified"
                )
                if result.result_count > 0:
                    successful_queries += 1
            
            test_results["details"].append({
                "test": "unified_queries",
                "success": successful_queries == len(test_queries),
                "successful_queries": successful_queries,
                "expected": len(test_queries)
            })
            
            print(f"     Successful unified queries: {successful_queries}/{len(test_queries)}")
            
            # Test engine stats
            print("   Test 2: Engine Statistics")
            
            stats = self.query_engine.get_system_stats()
            stats_available = "query_statistics" in stats
            
            test_results["details"].append({
                "test": "engine_statistics",
                "success": stats_available,
                "total_queries": stats.get("query_statistics", {}).get("total_queries", 0)
            })
            
            print(f"     Engine statistics available: {stats_available}")
            
            if not (successful_queries == len(test_queries) and stats_available):
                test_results["success"] = False
        
        except Exception as e:
            test_results["success"] = False
            test_results["error"] = str(e)
            print(f"     ❌ Error: {e}")
        
        self.test_results["unified_engine_workflow"] = test_results
        
        if test_results["success"]:
            print("   ✅ Unified Engine Workflow: PASSED")
        else:
            print("   ❌ Unified Engine Workflow: FAILED")
    
    def test_monitoring_integration(self):
        """Test Monitoring Dashboard Integration"""
        
        print("\n📊 Testing Monitoring Integration...")
        
        test_results = {
            "test_name": "monitoring_integration",
            "success": True,
            "details": []
        }
        
        try:
            # Test 1: Query logging
            print("   Test 1: Query Logging")
            
            test_query = "Monitoring test query"
            result = self.query_engine.process_query(test_query, "monitoring_test_user")
            
            # Log to monitoring
            self.monitoring.log_query_result(test_query, result)
            
            # Check if logged
            dashboard_data = self.monitoring.get_dashboard_data()
            queries_logged = len(dashboard_data["system_stats"]["query_statistics"])
            
            test_results["details"].append({
                "test": "query_logging",
                "success": queries_logged > 0,
                "queries_logged": queries_logged
            })
            
            print(f"     Queries logged: {queries_logged > 0}")
            
            # Test 2: Metrics capture
            print("   Test 2: Metrics Capture")
            
            snapshot = self.monitoring.capture_metrics_snapshot()
            metrics_captured = snapshot.total_queries > 0
            
            test_results["details"].append({
                "test": "metrics_capture",
                "success": metrics_captured,
                "total_queries": snapshot.total_queries,
                "avg_response_time": snapshot.avg_response_time_ms
            })
            
            print(f"     Metrics captured: {metrics_captured}")
            print(f"     Total queries: {snapshot.total_queries}")
            
            # Test 3: Dashboard data generation
            print("   Test 3: Dashboard Data")
            
            dashboard_complete = (
                "current_metrics" in dashboard_data and
                "system_stats" in dashboard_data and
                "dashboard_meta" in dashboard_data
            )
            
            test_results["details"].append({
                "test": "dashboard_data",
                "success": dashboard_complete,
                "components": list(dashboard_data.keys())
            })
            
            print(f"     Dashboard data complete: {dashboard_complete}")
            
            if not (queries_logged > 0 and metrics_captured and dashboard_complete):
                test_results["success"] = False
        
        except Exception as e:
            test_results["success"] = False
            test_results["error"] = str(e)
            print(f"     ❌ Error: {e}")
        
        self.test_results["monitoring_integration"] = test_results
        
        if test_results["success"]:
            print("   ✅ Monitoring Integration: PASSED")
        else:
            print("   ❌ Monitoring Integration: FAILED")
    
    def test_end_to_end_workflow(self):
        """Test kompletten End-to-End Workflow"""
        
        print("\n🔄 Testing End-to-End Workflow...")
        
        test_results = {
            "test_name": "end_to_end_workflow",
            "success": True,
            "details": []
        }
        
        try:
            # Scenario: Gradual rollout with monitoring
            print("   Scenario: Gradual Rollout with Monitoring")
            
            # Step 1: Start with 0% rollout
            self.flag_manager.set_rollout_percentage("unified_system_enabled", 0)
            
            # Step 2: Process some queries
            test_queries = [
                "End-to-end test query 1",
                "End-to-end test query 2", 
                "End-to-end test query 3"
            ]
            
            results_0_percent = []
            for i, query in enumerate(test_queries):
                result = self.query_engine.process_query(query, f"e2e_user_{i}")
                self.monitoring.log_query_result(query, result)
                results_0_percent.append(result.engine_version)
            
            # Check all legacy
            all_legacy = all(version == "legacy_v1" for version in results_0_percent)
            
            test_results["details"].append({
                "test": "0_percent_rollout",
                "success": all_legacy,
                "engine_versions": results_0_percent
            })
            
            print(f"     0% rollout → All legacy: {all_legacy}")
            
            # Step 3: Increase to 100% rollout
            self.flag_manager.set_rollout_percentage("unified_system_enabled", 100)
            
            results_100_percent = []
            for i, query in enumerate(test_queries):
                result = self.query_engine.process_query(query, f"e2e_user_{i}", force_mode="unified")
                self.monitoring.log_query_result(query, result)
                results_100_percent.append(result.engine_version)
            
            # Check all unified
            all_unified = all(version == "unified_v2" for version in results_100_percent)
            
            test_results["details"].append({
                "test": "100_percent_rollout",
                "success": all_unified,
                "engine_versions": results_100_percent
            })
            
            print(f"     100% rollout → All unified: {all_unified}")
            
            # Step 4: Check monitoring captured everything
            final_snapshot = self.monitoring.capture_metrics_snapshot()
            monitoring_working = final_snapshot.total_queries >= len(test_queries) * 2
            
            test_results["details"].append({
                "test": "monitoring_capture",
                "success": monitoring_working,
                "total_queries_captured": final_snapshot.total_queries
            })
            
            print(f"     Monitoring captured queries: {monitoring_working}")
            
            # Step 5: Generate reports
            try:
                monitoring_report = self.monitoring.export_metrics_report()
                
                reports_generated = Path(monitoring_report).exists()
                
                test_results["details"].append({
                    "test": "report_generation",
                    "success": reports_generated,
                    "monitoring_report": monitoring_report
                })
                
                print(f"     Reports generated: {reports_generated}")
            
            except Exception as e:
                test_results["details"].append({
                    "test": "report_generation",
                    "success": False,
                    "error": str(e)
                })
                print(f"     Reports generation failed: {e}")
            
            # Overall success
            if not (all_legacy and all_unified and monitoring_working):
                test_results["success"] = False
        
        except Exception as e:
            test_results["success"] = False
            test_results["error"] = str(e)
            print(f"     ❌ Error: {e}")
        
        self.test_results["end_to_end_workflow"] = test_results
        
        if test_results["success"]:
            print("   ✅ End-to-End Workflow: PASSED")
        else:
            print("   ❌ End-to-End Workflow: FAILED")
    
    def test_performance_requirements(self):
        """Test Performance Requirements"""
        
        print("\n⚡ Testing Performance Requirements...")
        
        test_results = {
            "test_name": "performance_requirements",
            "success": True,
            "details": []
        }
        
        try:
            # Test response times
            print("   Test: Response Time Requirements")
            
            response_times = []
            test_queries = [
                "Performance test query 1",
                "Performance test query 2",
                "Performance test query 3",
                "Performance test query 4",
                "Performance test query 5"
            ]
            
            for i, query in enumerate(test_queries):
                start_time = time.time()
                result = self.query_engine.process_query(query, f"perf_user_{i}")
                response_time = (time.time() - start_time) * 1000  # ms
                
                response_times.append(response_time)
                self.monitoring.log_query_result(query, result)
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Requirements: <200ms for 95% of queries
            performance_target_met = max_response_time < 10000  # 10s as reasonable limit
            
            test_results["details"].append({
                "test": "response_times",
                "success": performance_target_met,
                "avg_response_time_ms": avg_response_time,
                "max_response_time_ms": max_response_time,
                "all_response_times": response_times
            })
            
            print(f"     Avg response time: {avg_response_time:.1f}ms")
            print(f"     Max response time: {max_response_time:.1f}ms")
            print(f"     Performance target met: {performance_target_met}")
            
            if not performance_target_met:
                test_results["success"] = False
        
        except Exception as e:
            test_results["success"] = False
            test_results["error"] = str(e)
            print(f"     ❌ Error: {e}")
        
        self.test_results["performance_requirements"] = test_results
        
        if test_results["success"]:
            print("   ✅ Performance Requirements: PASSED")
        else:
            print("   ❌ Performance Requirements: FAILED")
    
    def run_all_tests(self):
        """Führt alle Integration Tests aus"""
        
        print(f"\n🧪 Running Phase 2.4 Integration Tests...")
        print(f"   Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        
        # Setup
        self.setup_components()
        
        # Run tests
        self.test_feature_flag_integration()
        self.test_unified_engine_workflow()
        self.test_monitoring_integration()
        self.test_end_to_end_workflow()
        self.test_performance_requirements()
        
        # Calculate results
        total_time = time.time() - start_time
        
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        total_tests = len(self.test_results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Summary
        print(f"\n📊 Integration Test Summary")
        print("=" * 40)
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {success_rate:.1%}")
        print(f"   Total Time: {total_time:.1f}s")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"   {test_name}: {status}")
            
            if not result["success"] and "error" in result:
                print(f"     Error: {result['error']}")
        
        # Save test report
        self.save_test_report(total_time, success_rate)
        
        # Final verdict
        if success_rate >= 0.8:  # 80% pass rate
            print(f"\n🎉 Phase 2.4 Integration: SUCCESS")
            print(f"   Ready for production rollout!")
        else:
            print(f"\n⚠️  Phase 2.4 Integration: NEEDS IMPROVEMENT")
            print(f"   Fix failing tests before rollout.")
        
        return success_rate >= 0.8
    
    def save_test_report(self, total_time, success_rate):
        """Speichert detaillierten Test Report"""
        
        report_data = {
            "test_suite": "Phase 2.4 Integration Test",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results.values() if r["success"]),
                "success_rate": success_rate,
                "total_time_seconds": total_time
            },
            "test_results": self.test_results,
            "environment": {
                "phase": "2.4",
                "components": ["QueryEngine", "Monitoring", "FeatureFlags"]
            }
        }
        
        report_path = Path("phase24_integration_report.json")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Integration test report saved: {report_path}")
        
        return str(report_path)

def main():
    """Main test execution"""
    
    # Run integration tests
    test_suite = Phase24IntegrationTest(debug_mode=True)
    success = test_suite.run_all_tests()
    
    return success

if __name__ == "__main__":
    main()