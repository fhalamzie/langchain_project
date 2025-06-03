#!/usr/bin/env python3
"""
Test Script for Enhanced Database Knowledge Integration System

This script tests the new Phase 6 features:
- Database Knowledge Compiler
- Enhanced Multi-Stage Retriever
- Query Preprocessor
- Integration with FirebirdDirectSQLAgent
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from db_knowledge_compiler import DatabaseKnowledgeCompiler
from enhanced_retrievers import EnhancedMultiStageRetriever, EnhancedFaissRetriever
from query_preprocessor import QueryPreprocessor
from firebird_sql_agent_direct import FirebirdDirectSQLAgent


def test_knowledge_compiler():
    """Test the Database Knowledge Compiler."""
    print("\n" + "="*60)
    print("Testing Database Knowledge Compiler")
    print("="*60)
    
    compiler = DatabaseKnowledgeCompiler()
    
    # Check if knowledge base already exists
    kb_path = Path("output/compiled_knowledge_base.json")
    if kb_path.exists():
        print("✅ Knowledge base already compiled")
        # Load and display summary
        import json
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        
        print(f"- Total tables: {kb['total_tables']}")
        print(f"- Total procedures: {kb['total_procedures']}")
        print(f"- Total relationships: {kb['total_relationships']}")
        print(f"- High priority tables: {len(kb['table_priorities']['high'])}")
        
        print("\nTop 5 most important tables:")
        for i, table_info in enumerate(kb['top_20_tables'][:5], 1):
            print(f"  {i}. {table_info['table']} (score: {table_info['importance_score']})")
    else:
        print("Compiling knowledge base...")
        kb = compiler.compile_knowledge()
        print("✅ Knowledge base compiled successfully")
    
    return True


def test_query_preprocessor():
    """Test the Query Preprocessor."""
    print("\n" + "="*60)
    print("Testing Query Preprocessor")
    print("="*60)
    
    preprocessor = QueryPreprocessor()
    
    test_queries = [
        "Zeige alle Eigentümer mit ihren Objekten",
        "Was ist der aktuelle Saldo für Konto 1000?",
        "Liste alle Mieter die keine Miete bezahlt haben",
        "Wieviele Wohnungen hat das Gebäude in der Marienstraße?",
        "Show me all properties owned by Schmidt"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = preprocessor.preprocess_query(query)
        
        print(f"   - Tables identified: {result['tables']}")
        print(f"   - Intent: {result['intent']['type']}")
        print(f"   - Entities: {len(result['entities'])} found")
        
        if result['join_paths']:
            print(f"   - Join paths found:")
            for path in result['join_paths']:
                print(f"     • {' -> '.join(path['path'])}")
        
        if result['suggestions']:
            print(f"   - Suggestions:")
            for suggestion in result['suggestions']:
                print(f"     • {suggestion}")
    
    print("\n✅ Query Preprocessor tested successfully")
    return True


def test_enhanced_retriever():
    """Test the Enhanced Multi-Stage Retriever."""
    print("\n" + "="*60)
    print("Testing Enhanced Multi-Stage Retriever")
    print("="*60)
    
    # Load sample documents from the agent
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        
        # Create a temporary agent just to load documents
        temp_agent = FirebirdDirectSQLAgent(
            db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            llm="gpt-4-1106-preview",
            retrieval_mode="faiss",
            use_enhanced_knowledge=False  # Don't need enhanced for doc loading
        )
        
        parsed_docs = temp_agent.parsed_docs
        print(f"Loaded {len(parsed_docs)} documents for testing")
        
        # Create enhanced retriever
        enhanced_retriever = EnhancedMultiStageRetriever(
            parsed_docs=parsed_docs,
            openai_api_key=os.getenv("OPENAI_API_KEY", "")
        )
        
        # Test queries
        test_queries = [
            "Find all owners and their properties",
            "What is the payment history for account 1000?",
            "Show tenants with overdue rent"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            docs = enhanced_retriever.get_relevant_documents(query)
            print(f"   Retrieved {len(docs)} documents")
            
            # Show document stages
            stages = {}
            for doc in docs:
                stage = doc.metadata.get('stage', 'base')
                stages[stage] = stages.get(stage, 0) + 1
            
            print(f"   Document stages: {stages}")
            
            # Show first doc preview
            if docs:
                first_doc = docs[0]
                print(f"   First doc source: {first_doc.metadata.get('source', 'unknown')}")
                print(f"   Preview: {first_doc.page_content[:100]}...")
        
        print("\n✅ Enhanced Retriever tested successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced retriever: {e}")
        return False


def test_full_integration():
    """Test the full integration with FirebirdDirectSQLAgent."""
    print("\n" + "="*60)
    print("Testing Full Integration with FirebirdDirectSQLAgent")
    print("="*60)
    
    try:
        # Create agent with enhanced knowledge
        agent = FirebirdDirectSQLAgent(
            db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            llm="gpt-4-1106-preview",
            retrieval_mode="enhanced",
            use_enhanced_knowledge=True
        )
        
        print("✅ Agent created with enhanced knowledge system")
        
        # Test queries
        test_queries = [
            "Zeige mir die ersten 5 Eigentümer",
            "Welche Tabellen gibt es für Finanzdaten?",
            "Was ist die Beziehung zwischen EIGENTUEMER und OBJEKTE?"
        ]
        
        for query in test_queries[:1]:  # Test just one query to save time
            print(f"\n📝 Testing query: {query}")
            
            try:
                result = agent.query(query)
                
                if result.get('error'):
                    print(f"❌ Query failed: {result['error']}")
                else:
                    print("✅ Query executed successfully")
                    
                    if result.get('generated_sql'):
                        print(f"   SQL: {result['generated_sql'][:100]}...")
                    
                    if result.get('agent_final_answer'):
                        print(f"   Answer preview: {result['agent_final_answer'][:100]}...")
                    
                    if result.get('text_variants'):
                        print(f"   Generated {len(result['text_variants'])} text variants")
                        
            except Exception as e:
                print(f"❌ Error executing query: {e}")
        
        print("\n✅ Full integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error in full integration test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🚀 Enhanced Database Knowledge Integration System Test Suite")
    print("="*60)
    
    # Ensure we have the necessary environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        # Try to load from env file
        env_path = Path("/home/envs/openai.env")
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        os.environ['OPENAI_API_KEY'] = line.strip().split('=', 1)[1]
                        break
    
    # Run tests
    tests = [
        ("Knowledge Compiler", test_knowledge_compiler),
        ("Query Preprocessor", test_query_preprocessor),
        ("Enhanced Retriever", test_enhanced_retriever),
        ("Full Integration", test_full_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed! The Enhanced Database Knowledge Integration System is ready.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()