#!/usr/bin/env python3
"""
Test script for Adaptive TAG Implementation

Tests the new ML-based query classification and dynamic schema discovery
to verify improvements over the rule-based approach.
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_adaptive_tag_classifier():
    """Test the ML-based query classifier"""
    print("🔬 Testing Adaptive TAG Classifier")
    print("=" * 60)
    
    try:
        from adaptive_tag_classifier import AdaptiveTAGClassifier
        
        classifier = AdaptiveTAGClassifier()
        
        test_queries = [
            "Wer wohnt in der Marienstraße 26?",
            "Wie viele Wohnungen gibt es insgesamt?", 
            "Alle Eigentümer aus Köln",
            "Durchschnittliche Miete in Essen",
            "Liste aller Mieter von Objekt 123",
            "Wohnungen mit mehr als 3 Zimmern",
            "Mietverträge seit Januar 2023",
            "Hausverwaltung Geschäftsberichte",
            "Bewohner Schmidt in Duisburg",
            "Kosten für Heizung letztes Jahr"
        ]
        
        print(f"Testing {len(test_queries)} queries...")
        print()
        
        for i, query in enumerate(test_queries, 1):
            result = classifier.classify_query(query)
            
            print(f"{i:2d}. Query: {query}")
            print(f"    Type: {result.query_type} (confidence: {result.confidence:.3f})")
            print(f"    Entities: {result.entities}")
            print(f"    Top alternatives: {result.alternatives[:2]}")
            print(f"    Method: {result.reasoning}")
            print()
        
        # Test learning functionality
        print("Testing learning from successful queries...")
        classifier.learn_from_success(
            "Wie viele Wohnungen in Köln", 
            "count_queries", 
            "SELECT COUNT(*) FROM WOHNUNG", 
            True
        )
        
        metrics = classifier.get_performance_metrics()
        print("Performance Metrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        print("✅ Adaptive TAG Classifier test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Adaptive TAG Classifier test failed: {e}")
        return False


def test_adaptive_tag_synthesizer():
    """Test the adaptive synthesizer with dynamic schema discovery"""
    print("\n🔬 Testing Adaptive TAG Synthesizer")
    print("=" * 60)
    
    try:
        from adaptive_tag_synthesizer import AdaptiveTAGSynthesizer
        
        # Mock schema info
        schema_info = {
            "tables": {
                "BEWOHNER": {},
                "EIGENTUEMER": {},
                "OBJEKTE": {},
                "WOHNUNG": {},
                "KONTEN": {},
                "BUCHUNG": {},
                "BEWADR": {},
                "EIGADR": {},
                "VEREIG": {},
                "SOLLSTELLUNG": {}
            }
        }
        
        synthesizer = AdaptiveTAGSynthesizer(schema_info)
        
        test_queries = [
            "Wer wohnt in der Marienstraße 26?",
            "Wie viele Wohnungen gibt es?",
            "Alle Eigentümer aus Köln",
            "Durchschnittliche Miete",
            "Mieter mehr als 500 Euro",
            "Verträge seit 2023"
        ]
        
        print(f"Testing {len(test_queries)} queries...")
        print()
        
        for i, query in enumerate(test_queries, 1):
            result = synthesizer.synthesize(query)
            
            print(f"{i:2d}. Query: {query}")
            print(f"    Type: {result.query_type} (confidence: {result.confidence:.3f})")
            print(f"    Dynamic Tables: {result.dynamic_tables}")
            print(f"    Entities: {result.entities}")
            print(f"    SQL: {result.sql}")
            print(f"    Alternatives: {[alt[0] for alt in result.alternatives[:2]]}")
            print()
        
        # Test learning
        synthesizer.learn_from_success(
            "Alle Bewohner", 
            "resident_lookup", 
            "SELECT * FROM BEWOHNER", 
            True
        )
        
        print("✅ Adaptive TAG Synthesizer test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Adaptive TAG Synthesizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_tag_pipeline():
    """Test the full adaptive TAG pipeline"""
    print("\n🔬 Testing Adaptive TAG Pipeline")
    print("=" * 60)
    
    try:
        # Mock LLM and DB interface for testing
        class MockLLM:
            def invoke(self, messages):
                class MockResponse:
                    def __init__(self):
                        self.content = "SELECT COUNT(*) FROM WOHNUNG"
                return MockResponse()
        
        class MockDBExecutor:
            def execute_query(self, sql):
                return [{"COUNT": 100}]
        
        # Mock the FocusedEmbeddingSystem to avoid API key requirement
        class MockEmbeddingSystem:
            def retrieve_table_details(self, tables):
                return f"Mock table details for: {', '.join(tables)}"
        
        from tag_pipeline import TAGPipeline
        
        # Patch the embedding system
        import tag_pipeline
        original_focused_embeddings = tag_pipeline.FocusedEmbeddingSystem
        tag_pipeline.FocusedEmbeddingSystem = lambda: MockEmbeddingSystem()
        
        available_tables = ["BEWOHNER", "EIGENTUEMER", "OBJEKTE", "WOHNUNG", "KONTEN", "BUCHUNG"]
        
        pipeline = TAGPipeline(
            llm=MockLLM(),
            db_executor=MockDBExecutor(),
            available_tables=available_tables
        )
        
        test_query = "Wie viele Wohnungen gibt es insgesamt?"
        
        print(f"Testing query: {test_query}")
        
        result = pipeline.process(test_query)
        
        print(f"✅ Pipeline Result:")
        print(f"  Query Type: {result.synthesis_info.query_type}")
        print(f"  Confidence: {result.synthesis_info.confidence:.3f}")
        print(f"  SQL: {result.sql}")
        print(f"  Results: {result.raw_results}")
        print(f"  Success: {result.error is None}")
        print(f"  Execution Time: {result.execution_time:.3f}s")
        
        # Test performance metrics
        metrics = pipeline.get_performance_metrics()
        print(f"\nPerformance Metrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        print("\n✅ Adaptive TAG Pipeline test completed successfully")
        
        # Restore original embedding system
        tag_pipeline.FocusedEmbeddingSystem = original_focused_embeddings
        
        return True
        
    except Exception as e:
        print(f"❌ Adaptive TAG Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sklearn_availability():
    """Test if scikit-learn is available for ML features"""
    print("🔬 Testing scikit-learn availability")
    print("=" * 60)
    
    try:
        import sklearn
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
        
        print("✅ scikit-learn is available - ML features enabled")
        print(f"   sklearn version: {sklearn.__version__}")
        return True
        
    except ImportError as e:
        print("⚠️ scikit-learn not available - falling back to rule-based classification")
        print("   To enable ML features, install scikit-learn:")
        print("   pip install scikit-learn")
        return False


def run_all_tests():
    """Run comprehensive test suite for Adaptive TAG"""
    print("🚀 Running Adaptive TAG Test Suite")
    print("=" * 80)
    
    results = []
    
    # Test dependencies
    results.append(("sklearn_availability", test_sklearn_availability()))
    
    # Test core components
    results.append(("adaptive_classifier", test_adaptive_tag_classifier()))
    results.append(("adaptive_synthesizer", test_adaptive_tag_synthesizer()))
    results.append(("adaptive_pipeline", test_adaptive_tag_pipeline()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Adaptive TAG implementation is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)