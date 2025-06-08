#!/usr/bin/env python3
"""
Working Modes Response Summary
============================

Simple script to show responses from the 3 main working modes:
- Smart Enhanced (provides detailed answers)
- Guided Agent (provides analysis and SQL)
- Contextual Vector (provides direct answers)

Based on the detailed_response_test.py findings.
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from gemini_llm import get_gemini_llm
from langchain_core.documents import Document

# Load environment variables
load_dotenv('/home/envs/openai.env')

# Test questions - same 3 core questions
TEST_QUESTIONS = [
    "Wie viele Wohnungen gibt es?",
    "Liste der Eigentümer", 
    "Bewohner Marienstr. 26"
]

def create_mock_documents():
    """Create mock documents for retrievers that need document collections."""
    return [
        Document(
            page_content="""
table_name: WOHNUNG
description: Apartment/housing units database
columns:
  - WHG_NR: Apartment number
  - ONR: Object number
  - QMWFL: Living space in square meters
  - ZIMMER: Number of rooms
sample_data:
  - Total apartments: 1250 units
  - Average rent: €850/month
            """,
            metadata={"table_name": "WOHNUNG", "query_type": "property_count", "source": "WOHNUNG.yaml"}
        ),
        Document(
            page_content="""
table_name: BEWOHNER
description: Residents and tenants database
columns:
  - BNAME: Last name
  - BVNAME: First name
  - BSTR: Street address
  - BPLZORT: Postal code and city
  - ONR: Object number
sample_data:
  - "Petra Nabakowski" lives at "Marienstr. 26, 45307 Essen"
            """,
            metadata={"table_name": "BEWOHNER", "query_type": "address_lookup", "source": "BEWOHNER.yaml"}
        ),
        Document(
            page_content="""
table_name: EIGENTUEMER
description: Property owners database
columns:
  - NAME: Owner name
  - VNAME: First name
  - ORT: City
  - EMAIL: Contact email
sample_data:
  - "Immobilien GmbH" from "Köln"
  - "Weber, Klaus" from "Düsseldorf"
            """,
            metadata={"table_name": "EIGENTUEMER", "query_type": "owner_lookup", "source": "EIGENTUEMER.yaml"}
        )
    ]

def test_smart_enhanced(question, llm, mock_docs, openai_api_key):
    """Test Smart Enhanced mode."""
    try:
        from smart_enhanced_retriever import SmartEnhancedRetriever
        retriever = SmartEnhancedRetriever(mock_docs, openai_api_key)
        
        start_time = time.time()
        result = retriever.retrieve(question)
        
        # Handle different result types
        if hasattr(result, 'documents'):
            docs = result.documents
        elif isinstance(result, list):
            docs = result
        else:
            docs = []
        
        # Generate response from docs
        if docs:
            context = "\n".join([doc.page_content for doc in docs[:2]])
            response = llm.invoke(f"Based on this context:\n{context}\n\nAnswer: {question}")
            response_text = response.content if hasattr(response, 'content') else str(response)
        else:
            response_text = "No relevant documents found"
        
        execution_time = time.time() - start_time
        return True, response_text, execution_time
        
    except Exception as e:
        return False, str(e), 0

def test_guided_agent(question, llm, db_connection):
    """Test Guided Agent mode."""
    try:
        from guided_agent_retriever import GuidedAgentRetriever
        retriever = GuidedAgentRetriever(
            db_connection_string=db_connection, 
            llm=llm, 
            enable_monitoring=False
        )
        
        start_time = time.time()
        result = retriever.retrieve(question)
        
        # Handle different result types
        if hasattr(result, 'documents'):
            docs = result.documents
        elif isinstance(result, list):
            docs = result
        else:
            docs = []
        
        # Generate response from docs
        if docs:
            context = "\n".join([doc.page_content for doc in docs[:2]])
            response = llm.invoke(f"Based on this context:\n{context}\n\nAnswer: {question}")
            response_text = response.content if hasattr(response, 'content') else str(response)
        else:
            response_text = "No relevant documents found"
        
        execution_time = time.time() - start_time
        return True, response_text, execution_time
        
    except Exception as e:
        return False, str(e), 0

def test_contextual_vector(question, llm, mock_docs, openai_api_key):
    """Test Contextual Vector mode."""
    try:
        from contextual_vector_retriever import ContextualVectorRetriever
        retriever = ContextualVectorRetriever(mock_docs, openai_api_key)
        
        start_time = time.time()
        result = retriever.retrieve(question)
        
        # Handle different result types
        if hasattr(result, 'documents'):
            docs = result.documents
        elif isinstance(result, list):
            docs = result
        else:
            docs = []
        
        # Generate response from docs
        if docs:
            context = "\n".join([doc.page_content for doc in docs[:2]])
            response = llm.invoke(f"Based on this context:\n{context}\n\nAnswer: {question}")
            response_text = response.content if hasattr(response, 'content') else str(response)
        else:
            response_text = "No relevant documents found"
        
        execution_time = time.time() - start_time
        return True, response_text, execution_time
        
    except Exception as e:
        return False, str(e), 0

def print_mode_response(mode_name, question, success, response, exec_time):
    """Print a formatted response for a mode."""
    print(f"\n{'=' * 60}")
    print(f"🔍 {mode_name.upper()}")
    print(f"❓ Question: {question}")
    print(f"⏱️  Time: {exec_time:.2f}s")
    print(f"{'=' * 60}")
    
    if success:
        # Format the response nicely
        lines = response.split('\n')
        for line in lines:
            if line.strip():
                print(f"   {line}")
            else:
                print()
    else:
        print(f"❌ ERROR: {response}")

def main():
    """Main function to test the 3 working modes."""
    print("🎯 WORKING MODES RESPONSE COMPARISON")
    print("=" * 60)
    print("Testing the 3 modes that actually provide responses:")
    print("• Smart Enhanced - Detailed German responses")
    print("• Guided Agent - Analysis with SQL generation")  
    print("• Contextual Vector - Direct, concise answers")
    print(f"\nStarted: {datetime.now().strftime('%H:%M:%S')}")
    
    # Initialize components
    llm = get_gemini_llm()
    db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    openai_api_key = os.getenv('OPENAI_API_KEY')
    mock_docs = create_mock_documents()
    
    for question in TEST_QUESTIONS:
        print(f"\n\n{'#' * 80}")
        print(f"📋 TESTING QUESTION: {question}")
        print(f"{'#' * 80}")
        
        # Test Smart Enhanced
        success, response, exec_time = test_smart_enhanced(question, llm, mock_docs, openai_api_key)
        print_mode_response("Smart Enhanced", question, success, response, exec_time)
        
        # Test Guided Agent 
        success, response, exec_time = test_guided_agent(question, llm, db_connection)
        print_mode_response("Guided Agent", question, success, response, exec_time)
        
        # Test Contextual Vector
        success, response, exec_time = test_contextual_vector(question, llm, mock_docs, openai_api_key)
        print_mode_response("Contextual Vector", question, success, response, exec_time)
    
    print(f"\n\n{'=' * 80}")
    print("✅ COMPARISON COMPLETED")
    print("=" * 80)
    print("Summary:")
    print("• Smart Enhanced: Provides detailed, conversational responses in German")
    print("• Guided Agent: Provides analysis and explains database connectivity issues")
    print("• Contextual Vector: Provides direct, concise answers (often SQL queries)")
    print(f"\nCompleted: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()