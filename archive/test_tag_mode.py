#!/usr/bin/env python3
"""
Test script for TAG retrieval mode.
Demonstrates improved SQL generation with focused context.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv('/home/envs/openai.env')

# Add project paths
project_root = Path(__file__).parent
archive_path = project_root / "archive"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(archive_path))

from tag_retrieval_mode import TAGRetrievalMode
from langchain_openai import ChatOpenAI


def test_tag_mode():
    """Test TAG mode with various queries."""
    
    print("🚀 TAG MODE TEST - Focused Context for Better SQL Generation")
    print("=" * 80)
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Mock DB interface (in real usage, this would be FDB interface)
    class MockDBInterface:
        def execute_query(self, sql):
            # Simulate some results
            if "COUNT(*)" in sql and "WOHNUNG" in sql:
                return [{"COUNT": 517}]
            elif "BEWOHNER" in sql and "LIKE" in sql:
                return [
                    {"BNAME": "Müller", "BVNAME": "Hans", "BSTR": "Marienstraße 26", "BPLZORT": "45307 Essen"},
                    {"BNAME": "Schmidt", "BVNAME": "Anna", "BSTR": "Marienstraße 26", "BPLZORT": "45307 Essen"}
                ]
            elif "EIGENTUEMER" in sql:
                return [
                    {"NAME": "Immobilien GmbH", "ORT": "Köln"},
                    {"NAME": "Wohnbau AG", "ORT": "Köln"}
                ]
            return []
    
    # Mock schema info
    schema_info = {
        "tables": {
            "BEWOHNER": {"description": "Bewohner/Mieter"},
            "EIGENTUEMER": {"description": "Eigentümer"},
            "WOHNUNG": {"description": "Wohnungen"},
            "OBJEKTE": {"description": "Gebäude/Objekte"},
            "KONTEN": {"description": "Konten"},
            "BUCHUNG": {"description": "Buchungen"}
        }
    }
    
    # Initialize TAG mode
    tag_mode = TAGRetrievalMode(
        llm=llm,
        db_interface=MockDBInterface(),
        schema_info=schema_info
    )
    
    # Test queries
    test_queries = [
        "Wer wohnt in der Marienstr. 26, 45307 Essen",
        "Wie viele Wohnungen gibt es insgesamt?",
        "Liste aller Eigentümer aus Köln",
        "Wer wohnt in der Marienstraße 26",
        "Durchschnittliche Miete in Essen"
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        try:
            # Process with TAG mode
            result = tag_mode.process_query(query)
            
            print(f"✅ Success: {result['success']}")
            print(f"🔍 Query Type: {result['metadata']['query_type']}")
            print(f"📊 Tables Used: {', '.join(result['metadata']['tables_used'])}")
            print(f"🔧 SQL: {result['sql_query']}")
            print(f"💬 Answer: {result['answer']}")
            print(f"⏱️  Time: {result['execution_time']:.2f}s")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({"success": False, "error": str(e)})
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for r in results if r.get("success", False))
    total = len(results)
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"\n✅ Success Rate: {successful}/{total} ({success_rate:.1f}%)")
    
    # Show focused context example
    print("\n" + "=" * 80)
    print("FOCUSED CONTEXT EXAMPLE")
    print("=" * 80)
    
    example_query = "Wer wohnt in der Marienstraße 26"
    context = tag_mode.get_context_for_query(example_query)
    print(f"Query: {example_query}")
    print(f"Focused Context:\n{context}")
    
    return results


if __name__ == "__main__":
    test_tag_mode()