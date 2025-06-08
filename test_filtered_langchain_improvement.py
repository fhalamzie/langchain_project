#!/usr/bin/env python3
"""
Test Suite for Filtered LangChain Improvement - Task 1.4

Tests the schema filtering optimization that reduces table loading
from 151 to 3-8 relevant tables based on query classification.

Verifies:
1. Query classification accuracy
2. Table filtering effectiveness  
3. Business logic integration
4. Performance improvements
5. Integration with existing system
"""

import json
import time
import traceback
from typing import Dict, List

def test_query_classification():
    """Test query classification accuracy for different WINCASA scenarios"""
    print("🎯 Testing Query Classification...")
    
    try:
        from filtered_langchain_retriever import QueryTableClassifier
        
        classifier = QueryTableClassifier()
        
        test_cases = [
            # Address lookups
            ("Wo wohnt Herr Schmidt?", "address_lookup"),
            ("Zeige mir die Adresse von Objekt 123", "address_lookup"),
            ("In welcher Straße liegt das Objekt?", "address_lookup"),
            
            # Owner lookups
            ("Wem gehört das Objekt in der Musterstraße?", "owner_lookup"),
            ("Zeige alle Eigentümer", "owner_lookup"),
            ("Wer ist der Besitzer von Wohnung 123?", "owner_lookup"),
            
            # Financial queries
            ("Wie hoch sind die Mietkosten?", "financial_query"),
            ("Zeige alle offenen Rechnungen", "financial_query"),
            ("Welche Zahlungen sind eingegangen?", "financial_query"),
            
            # Property counts
            ("Wie viele Wohnungen gibt es?", "property_count"),
            ("Anzahl der Objekte insgesamt", "property_count"),
            ("How many apartments do we have?", "property_count"),
            
            # Resident info
            ("Zeige alle Bewohner", "resident_info"),
            ("Wer wohnt in Objekt 456?", "resident_info"),
            ("Kontaktdaten von Mieter Müller", "resident_info"),
            
            # Maintenance requests
            ("Welche Schäden sind gemeldet?", "maintenance_requests"),
            ("Zeige offene Reparaturen", "maintenance_requests"),
            ("Defekte Heizung in Wohnung 789", "maintenance_requests"),
        ]
        
        correct_classifications = 0
        total_tests = len(test_cases)
        
        print(f"📊 Testing {total_tests} classification scenarios...")
        
        for query, expected_type in test_cases:
            classified_type = classifier.classify_query(query)
            is_correct = classified_type == expected_type
            
            if is_correct:
                correct_classifications += 1
                print(f"✅ '{query[:30]}...' → {classified_type}")
            else:
                print(f"❌ '{query[:30]}...' → {classified_type} (expected: {expected_type})")
        
        accuracy = (correct_classifications / total_tests) * 100
        print(f"\n📈 Classification Accuracy: {accuracy:.1f}% ({correct_classifications}/{total_tests})")
        
        return accuracy >= 80  # Expect at least 80% accuracy
        
    except Exception as e:
        print(f"❌ Query classification test failed: {e}")
        return False


def test_table_filtering():
    """Test table filtering reduces schema from 151 to 3-8 tables"""
    print("\n📊 Testing Table Filtering...")
    
    try:
        from filtered_langchain_retriever import QueryTableClassifier
        
        classifier = QueryTableClassifier()
        
        test_queries = [
            "Wie viele Wohnungen gibt es?",
            "Wo wohnt Herr Schmidt?", 
            "Wem gehört das Objekt?",
            "Wie hoch sind die Kosten?",
            "Zeige alle Bewohner",
            "Welche Schäden sind gemeldet?"
        ]
        
        filtering_results = []
        
        for query in test_queries:
            relevant_tables = classifier.get_relevant_tables(query)
            query_type = classifier.classify_query(query)
            
            result = {
                "query": query[:30] + "...",
                "type": query_type,
                "tables": len(relevant_tables),
                "table_list": relevant_tables
            }
            filtering_results.append(result)
            
            # Verify filtering criteria
            tables_count = len(relevant_tables)
            in_range = 3 <= tables_count <= 8
            
            if in_range:
                print(f"✅ {query[:30]}... → {tables_count} tables ({query_type})")
            else:
                print(f"❌ {query[:30]}... → {tables_count} tables (should be 3-8)")
        
        # Calculate average reduction
        average_tables = sum(len(r["table_list"]) for r in filtering_results) / len(filtering_results)
        reduction_percentage = ((151 - average_tables) / 151) * 100
        
        print(f"\n📊 Schema Reduction Analysis:")
        print(f"   Original tables: 151")
        print(f"   Average filtered: {average_tables:.1f}")
        print(f"   Reduction: {reduction_percentage:.1f}%")
        
        # Verify all filtered table counts are in range
        all_in_range = all(3 <= len(r["table_list"]) <= 8 for r in filtering_results)
        
        return all_in_range and reduction_percentage >= 90  # Expect >90% reduction
        
    except Exception as e:
        print(f"❌ Table filtering test failed: {e}")
        return False


def test_business_logic_mapping():
    """Test that business logic correctly maps to WINCASA table groups"""
    print("\n🏢 Testing Business Logic Mapping...")
    
    try:
        from filtered_langchain_retriever import QueryTableClassifier
        
        classifier = QueryTableClassifier()
        
        # Test core WINCASA business requirements
        business_scenarios = [
            {
                "scenario": "Address Lookup",
                "query": "Wo wohnt Herr Schmidt?",
                "required_tables": ["BEWOHNER", "OBJEKTE", "ADRESSEN"],
                "expected_type": "address_lookup"
            },
            {
                "scenario": "Owner Information", 
                "query": "Wem gehört das Objekt?",
                "required_tables": ["EIGENTUEMER", "OBJEKTE"],
                "expected_type": "owner_lookup"
            },
            {
                "scenario": "Financial Data",
                "query": "Zeige alle Rechnungen",
                "required_tables": ["KONTEN", "BUCHUNGEN", "RECHNUNGEN"],
                "expected_type": "financial_query"
            },
            {
                "scenario": "Property Statistics",
                "query": "Wie viele Wohnungen gibt es?",
                "required_tables": ["OBJEKTE"],
                "expected_type": "property_count"
            }
        ]
        
        passed_scenarios = 0
        
        for scenario in business_scenarios:
            query = scenario["query"]
            required_tables = scenario["required_tables"]
            expected_type = scenario["expected_type"]
            
            # Get classification and tables
            classified_type = classifier.classify_query(query)
            relevant_tables = classifier.get_relevant_tables(query)
            
            # Check type classification
            type_correct = classified_type == expected_type
            
            # Check that required tables are included
            tables_included = all(table in relevant_tables for table in required_tables)
            
            scenario_passed = type_correct and tables_included
            
            if scenario_passed:
                passed_scenarios += 1
                print(f"✅ {scenario['scenario']}: {classified_type} with {len(relevant_tables)} tables")
            else:
                print(f"❌ {scenario['scenario']}: Failed")
                if not type_correct:
                    print(f"   Wrong type: {classified_type} (expected: {expected_type})")
                if not tables_included:
                    missing = [t for t in required_tables if t not in relevant_tables]
                    print(f"   Missing tables: {missing}")
        
        success_rate = (passed_scenarios / len(business_scenarios)) * 100
        print(f"\n📈 Business Logic Success Rate: {success_rate:.1f}% ({passed_scenarios}/{len(business_scenarios)})")
        
        return success_rate >= 100  # All scenarios must pass
        
    except Exception as e:
        print(f"❌ Business logic mapping test failed: {e}")
        return False


def test_integration_compatibility():
    """Test integration with existing WINCASA system components"""
    print("\n🔗 Testing Integration Compatibility...")
    
    try:
        from filtered_langchain_retriever import FilteredLangChainSQLRetriever
        
        # Test basic initialization
        retriever = FilteredLangChainSQLRetriever(
            db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            llm=None,  # Mock LLM for testing
            enable_monitoring=False
        )
        
        # Test retriever info method
        info = retriever.get_retriever_info()
        
        required_info_fields = [
            "mode", "type", "description", "optimization", 
            "tables_reduction", "features", "table_groups"
        ]
        
        info_complete = all(field in info for field in required_info_fields)
        
        # Test compatibility methods
        has_get_relevant_documents = hasattr(retriever, 'get_relevant_documents')
        has_retrieve_documents = hasattr(retriever, 'retrieve_documents')
        
        # Test query classifier integration
        classifier_exists = hasattr(retriever, 'query_classifier')
        
        integration_checks = [
            ("Retriever info complete", info_complete),
            ("Has BaseRetriever compatibility", has_get_relevant_documents),
            ("Has retrieve_documents method", has_retrieve_documents),
            ("Query classifier integrated", classifier_exists),
            ("Mode correctly set", info.get("mode") == "filtered_langchain"),
        ]
        
        passed_checks = 0
        for check_name, passed in integration_checks:
            if passed:
                print(f"✅ {check_name}")
                passed_checks += 1
            else:
                print(f"❌ {check_name}")
        
        integration_success = passed_checks == len(integration_checks)
        
        print(f"\n📈 Integration Compatibility: {passed_checks}/{len(integration_checks)} checks passed")
        
        return integration_success
        
    except Exception as e:
        print(f"❌ Integration compatibility test failed: {e}")
        return False


def test_performance_optimization():
    """Test performance improvements from schema filtering"""
    print("\n⚡ Testing Performance Optimization...")
    
    try:
        from filtered_langchain_retriever import QueryTableClassifier
        
        classifier = QueryTableClassifier()
        
        # Simulate performance comparison
        test_queries = [
            "Wie viele Wohnungen gibt es?",
            "Wo wohnt Herr Schmidt?",
            "Wem gehört das Objekt?",
            "Zeige alle Bewohner",
            "Welche Rechnungen sind offen?"
        ]
        
        performance_results = []
        
        for query in test_queries:
            start_time = time.time()
            
            # Simulate original LangChain (all 151 tables)
            original_table_count = 151
            
            # Get filtered table count
            relevant_tables = classifier.get_relevant_tables(query)
            filtered_table_count = len(relevant_tables)
            
            classification_time = time.time() - start_time
            
            # Calculate theoretical performance improvement
            table_reduction = ((original_table_count - filtered_table_count) / original_table_count) * 100
            
            # Estimate context reduction (tables correlate with context size)
            estimated_context_reduction = table_reduction * 0.8  # Conservative estimate
            
            result = {
                "query": query[:30] + "...",
                "original_tables": original_table_count,
                "filtered_tables": filtered_table_count,
                "table_reduction_percent": table_reduction,
                "estimated_context_reduction_percent": estimated_context_reduction,
                "classification_time_ms": classification_time * 1000
            }
            
            performance_results.append(result)
            
            print(f"📊 {query[:30]}...")
            print(f"   Tables: {original_table_count} → {filtered_table_count} ({table_reduction:.1f}% reduction)")
            print(f"   Estimated context reduction: {estimated_context_reduction:.1f}%")
        
        # Calculate averages
        avg_table_reduction = sum(r["table_reduction_percent"] for r in performance_results) / len(performance_results)
        avg_context_reduction = sum(r["estimated_context_reduction_percent"] for r in performance_results) / len(performance_results)
        avg_classification_time = sum(r["classification_time_ms"] for r in performance_results) / len(performance_results)
        
        print(f"\n📈 Performance Summary:")
        print(f"   Average table reduction: {avg_table_reduction:.1f}%")
        print(f"   Average context reduction: {avg_context_reduction:.1f}%") 
        print(f"   Average classification time: {avg_classification_time:.2f}ms")
        
        # Success criteria: >90% table reduction, <10ms classification
        performance_good = avg_table_reduction >= 90 and avg_classification_time < 10
        
        return performance_good
        
    except Exception as e:
        print(f"❌ Performance optimization test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all tests for Filtered LangChain implementation"""
    print("🧪 Comprehensive Test Suite: Filtered LangChain Implementation (Task 1.4)")
    print("=" * 80)
    
    tests = [
        ("Query Classification", test_query_classification),
        ("Table Filtering", test_table_filtering), 
        ("Business Logic Mapping", test_business_logic_mapping),
        ("Integration Compatibility", test_integration_compatibility),
        ("Performance Optimization", test_performance_optimization),
    ]
    
    results = []
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            start_time = time.time()
            passed = test_func()
            duration = time.time() - start_time
            
            results.append({
                "test": test_name,
                "passed": passed,
                "duration": duration
            })
            
            if passed:
                passed_tests += 1
                print(f"✅ {test_name} PASSED ({duration:.2f}s)")
            else:
                print(f"❌ {test_name} FAILED ({duration:.2f}s)")
                
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
            results.append({
                "test": test_name,
                "passed": False,
                "duration": 0,
                "error": str(e)
            })
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL TEST RESULTS - Task 1.4: LangChain → Filtered Agent")
    print('='*80)
    
    success_rate = (passed_tests / len(tests)) * 100
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} {result['test']} ({result['duration']:.2f}s)")
    
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{len(tests)} tests passed)")
    
    if success_rate >= 80:
        print("🎉 Task 1.4 Implementation: READY FOR INTEGRATION")
        print("📈 Schema filtering successfully reduces context overload")
        print("⚡ Performance optimization achieved through intelligent table selection")
    else:
        print("⚠️ Task 1.4 Implementation: NEEDS IMPROVEMENT")
        print("🔧 Review failed tests before integration")
    
    return success_rate >= 80


if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)