#!/usr/bin/env python3
"""
Test Script for SQLCoder-2 Integration

This script tests the SQLCoder-2 retriever integration with the WINCASA system,
focusing on JOIN-aware prompting and Firebird SQL generation.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from firebird_sql_agent_direct import FirebirdDirectSQLAgent
from sqlcoder_retriever import SQLCoderRetriever


def test_sqlcoder_basic():
    """Test basic SQLCoder functionality without full agent integration."""
    print("=== Testing SQLCoder-2 Basic Functionality ===")
    
    try:
        # Create minimal test documents
        from langchain_core.documents import Document
        
        test_docs = [
            Document(
                page_content="""Entity Name: BEWOHNER
Description: Tenant information table
Columns:
  - BWO (Type: INTEGER): Property reference linking to OBJEKTE.ONR
  - BSTR (Type: VARCHAR): Street name and house number
  - BPLZORT (Type: VARCHAR): ZIP code and city name
  - NAME (Type: VARCHAR): Tenant last name
  - VORNAME (Type: VARCHAR): Tenant first name
Relations:
  - BEWOHNER -> OBJEKTE: BWO = ONR""",
                metadata={'type': 'yaml_definition', 'source': 'bewohner.yaml'}
            ),
            Document(
                page_content="""Entity Name: OBJEKTE
Description: Property objects table
Columns:
  - ONR (Type: INTEGER): Primary key object number
  - OSTR (Type: VARCHAR): Property street address
  - OPLZORT (Type: VARCHAR): Property ZIP and city
Relations:
  - OBJEKTE -> BEWOHNER: ONR = BWO
  - OBJEKTE -> EIGENTUEMER: via VEREIG table""",
                metadata={'type': 'yaml_definition', 'source': 'objekte.yaml'}
            )
        ]
        
        # Initialize SQLCoder retriever
        print("Initializing SQLCoder retriever...")
        sqlcoder = SQLCoderRetriever(
            model_name="defog/sqlcoder2",
            parsed_docs=test_docs,
            use_quantization=True,
            max_new_tokens=256,
            temperature=0.1
        )
        
        # Test queries
        test_queries = [
            "Wie viele Bewohner gibt es insgesamt?",
            "Zeige mir alle Bewohner in der Marienstraße",
            "Welche Objekte haben mehr als 2 Bewohner?",
            "Finde Bewohner und ihre Objektadressen"
        ]
        
        print(f"\nTesting {len(test_queries)} queries with SQLCoder-2...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test Query {i}: {query} ---")
            
            start_time = time.time()
            docs = sqlcoder.get_relevant_documents(query)
            end_time = time.time()
            
            for doc in docs:
                print(f"Generated Content:\n{doc.page_content}")
                print(f"Metadata: {doc.metadata}")
                print(f"Generation Time: {end_time - start_time:.2f}s")
        
        print("\n✅ SQLCoder basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ SQLCoder basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sqlcoder_agent_integration():
    """Test SQLCoder integration with the full FirebirdDirectSQLAgent."""
    print("\n=== Testing SQLCoder-2 Agent Integration ===")
    
    try:
        # Database connection
        db_connection = "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB"
        
        # Initialize agent with SQLCoder mode
        print("Initializing FirebirdDirectSQLAgent with SQLCoder mode...")
        agent = FirebirdDirectSQLAgent(
            db_connection_string=db_connection,
            llm="gpt-4",  # Fallback LLM for agent reasoning
            retrieval_mode='sqlcoder',
            use_enhanced_knowledge=True
        )
        
        if not agent or not agent.sql_agent:
            print("❌ Agent initialization failed")
            return False
        
        print("✅ Agent initialized successfully")
        
        # Test queries with different complexity levels
        test_queries = [
            {
                "query": "Wie viele Wohnungen gibt es insgesamt?",
                "expected_pattern": "COUNT",
                "complexity": "simple"
            },
            {
                "query": "Zeige mir die ersten 3 Bewohner mit ihren Adressen",
                "expected_pattern": "FIRST 3",
                "complexity": "medium"
            },
            {
                "query": "Welche Bewohner wohnen in Objekten in Essen?",
                "expected_pattern": "JOIN.*LIKE",
                "complexity": "complex"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            complexity = test_case["complexity"]
            
            print(f"\n--- Agent Test {i} ({complexity}): {query} ---")
            
            start_time = time.time()
            response = agent.query(query, retrieval_mode_override='sqlcoder')
            end_time = time.time()
            
            # Analyze response
            success = response.get('error') is None
            generated_sql = response.get('generated_sql', '')
            agent_answer = response.get('agent_final_answer', '')
            
            result = {
                'query': query,
                'complexity': complexity,
                'success': success,
                'sql': generated_sql,
                'answer': agent_answer,
                'time': end_time - start_time,
                'error': response.get('error')
            }
            results.append(result)
            
            print(f"Success: {'✅' if success else '❌'}")
            print(f"Generated SQL: {generated_sql}")
            print(f"Agent Answer: {agent_answer}")
            print(f"Execution Time: {result['time']:.2f}s")
            
            if not success:
                print(f"Error: {result['error']}")
        
        # Summary
        successful_queries = sum(1 for r in results if r['success'])
        total_queries = len(results)
        success_rate = (successful_queries / total_queries) * 100
        avg_time = sum(r['time'] for r in results) / total_queries
        
        print(f"\n=== SQLCoder Agent Integration Summary ===")
        print(f"Success Rate: {successful_queries}/{total_queries} ({success_rate:.1f}%)")
        print(f"Average Execution Time: {avg_time:.2f}s")
        
        # Check if success rate meets target
        if success_rate >= 75.0:
            print("🎯 Target success rate (75%) achieved!")
        else:
            print(f"⚠️ Below target success rate (75%). Current: {success_rate:.1f}%")
        
        return success_rate >= 50.0  # Minimum acceptable rate
        
    except Exception as e:
        print(f"❌ SQLCoder agent integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_join_aware_prompting():
    """Test JOIN-aware prompting capabilities specifically."""
    print("\n=== Testing JOIN-Aware Prompting ===")
    
    try:
        # Create test documents with relationships
        from langchain_core.documents import Document
        
        test_docs = [
            Document(
                page_content="""Entity Name: BEWOHNER
Columns:
  - BWO (Type: INTEGER): Object reference
  - NAME (Type: VARCHAR): Last name
Relations:
  - BEWOHNER -> OBJEKTE: BWO = ONR""",
                metadata={'type': 'yaml_definition', 'source': 'bewohner.yaml'}
            ),
            Document(
                page_content="""Entity Name: EIGENTUEMER
Columns:
  - ENR (Type: INTEGER): Owner ID
  - NAME (Type: VARCHAR): Owner name
Relations:
  - EIGENTUEMER -> VEREIG: ENR = VENR
  - EIGENTUEMER -> OBJEKTE: via VEREIG table""",
                metadata={'type': 'yaml_definition', 'source': 'eigentuemer.yaml'}
            ),
            Document(
                page_content="""Entity Name: VEREIG
Columns:
  - VENR (Type: INTEGER): Owner reference
  - VONR (Type: INTEGER): Object reference
Relations:
  - VEREIG -> EIGENTUEMER: VENR = ENR
  - VEREIG -> OBJEKTE: VONR = ONR""",
                metadata={'type': 'yaml_definition', 'source': 'vereig.yaml'}
            )
        ]
        
        sqlcoder = SQLCoderRetriever(
            parsed_docs=test_docs,
            use_quantization=True
        )
        
        # Test complex JOIN queries
        join_queries = [
            "Zeige Eigentümer und ihre Objekte",
            "Welche Bewohner und Eigentümer gehören zum gleichen Objekt?",
            "Finde alle Eigentümer mit mehr als einem Objekt"
        ]
        
        print("Testing JOIN-aware prompting...")
        
        for query in join_queries:
            print(f"\nJOIN Query: {query}")
            docs = sqlcoder.get_relevant_documents(query)
            
            for doc in docs:
                sql_content = doc.page_content
                print(f"Generated SQL: {sql_content}")
                
                # Check for JOIN patterns
                has_join = 'JOIN' in sql_content.upper()
                has_proper_syntax = 'ON' in sql_content.upper()
                
                print(f"Contains JOIN: {'✅' if has_join else '❌'}")
                print(f"Proper JOIN syntax: {'✅' if has_proper_syntax else '❌'}")
        
        print("\n✅ JOIN-aware prompting test completed")
        return True
        
    except Exception as e:
        print(f"❌ JOIN-aware prompting test failed: {e}")
        return False


def main():
    """Run all SQLCoder integration tests."""
    print("🚀 Starting SQLCoder-2 Integration Tests")
    print("=" * 50)
    
    # Check if required dependencies are available
    try:
        import torch
        import transformers
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ Transformers version: {transformers.__version__}")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install torch transformers accelerate bitsandbytes")
        return False
    
    # Run tests
    tests = [
        ("SQLCoder Basic Functionality", test_sqlcoder_basic),
        ("JOIN-Aware Prompting", test_join_aware_prompting),
        ("Agent Integration", test_sqlcoder_agent_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Final summary
    print("\n" + "="*60)
    print("🏁 SQLCoder-2 Integration Test Summary")
    print("="*60)
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    overall_success = passed_tests / total_tests
    print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({overall_success*100:.1f}%)")
    
    if overall_success >= 0.8:
        print("🎉 SQLCoder-2 integration is ready for production!")
    elif overall_success >= 0.6:
        print("⚠️ SQLCoder-2 integration needs optimization before production")
    else:
        print("❌ SQLCoder-2 integration requires significant work")
    
    return overall_success >= 0.6


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)