#!/usr/bin/env python3
"""
Detailed Response Test - Show Full Answers from All 9 WINCASA Modes
================================================================

This script shows the complete response text from each retrieval mode
for the 3 key test questions, allowing users to see exactly what 
each mode is saying rather than just whether it works or not.

Based on the verified working patterns from quick_3question_benchmark_final.py
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
        ),
        Document(
            page_content="""
table_name: OBJEKTE
description: Property objects and buildings
columns:
  - ONR: Object number (primary key)
  - ONAME: Object name/address
  - ORT: City location
sample_data:
  - Various residential buildings across multiple cities
            """,
            metadata={"table_name": "OBJEKTE", "query_type": "general_property", "source": "OBJEKTE.yaml"}
        ),
        Document(
            page_content="""
table_name: KONTEN
description: Financial accounts for properties
columns:
  - KONTO_NR: Account number
  - ONR: Object number
  - SALDO: Account balance
sample_data:
  - Property management financial data
            """,
            metadata={"table_name": "KONTEN", "query_type": "financial_query", "source": "KONTEN.yaml"}
        )
    ]

def get_full_response_from_mode(mode_name: str, retriever, question: str, llm):
    """Get the complete response from a retrieval mode."""
    print(f"  🔍 Testing {mode_name}...")
    start_time = time.time()
    
    try:
        # Get response from retriever using the same logic as the benchmark
        response = None
        
        if hasattr(retriever, 'get_response'):
            response = retriever.get_response(question)
        elif hasattr(retriever, 'query'):
            response = retriever.query(question)
        elif hasattr(retriever, 'retrieve'):
            result = retriever.retrieve(question)
            # Handle different result types
            if hasattr(result, 'documents'):
                # Custom result objects (SmartEnhancedResult, ContextualVectorResult)
                docs = result.documents
            elif isinstance(result, list):
                # Plain list of documents
                docs = result
            else:
                docs = []
            
            # Generate response from docs
            if docs:
                context = "\n".join([doc.page_content for doc in docs[:2]])  # Use top 2 docs
                response = llm.invoke(f"Based on this context:\n{context}\n\nAnswer: {question}")
            else:
                response = "No relevant documents found"
        else:
            response = "Mode interface not found"
        
        execution_time = time.time() - start_time
        
        # Convert response to string and clean it up
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        return {
            'success': True,
            'response': response_text,
            'time': execution_time
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            'success': False,
            'response': f"ERROR: {str(e)}",
            'time': execution_time
        }

def print_separator(title, char="="):
    """Print a formatted separator with title."""
    width = 80
    title_len = len(title) + 2  # space on each side
    padding = (width - title_len) // 2
    print(f"\n{char * padding} {title} {char * padding}")

def print_response_box(mode_name, question, result):
    """Print a formatted response box."""
    print(f"\n┌─ {mode_name} ─ {question}")
    print("│")
    
    if result['success']:
        print(f"│ ⏱️  Response Time: {result['time']:.2f}s")
        print("│")
        print("│ 📝 Full Response:")
        # Split response into lines and prefix each with │
        response_lines = result['response'].split('\n')
        for line in response_lines:
            # Wrap long lines
            if len(line) > 75:
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + word) > 75:
                        if current_line:
                            print(f"│ {current_line}")
                            current_line = word
                        else:
                            print(f"│ {word}")
                    else:
                        current_line += (" " + word) if current_line else word
                if current_line:
                    print(f"│ {current_line}")
            else:
                print(f"│ {line}")
    else:
        print(f"│ ❌ Failed in {result['time']:.2f}s")
        print(f"│ Error: {result['response']}")
    
    print("└" + "─" * 78)

def run_detailed_response_test():
    """Run the detailed response test showing full answers."""
    print_separator("DETAILED RESPONSE TEST - ALL 9 WINCASA MODES")
    print("Purpose: Show complete response text from each mode")
    print("Questions: 3 core test questions")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize LLM and common components
    print("\n🔧 Initializing system components...")
    llm = get_gemini_llm()
    db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    openai_api_key = os.getenv('OPENAI_API_KEY')
    mock_docs = create_mock_documents()
    
    # Test each question with all modes
    for question_idx, question in enumerate(TEST_QUESTIONS, 1):
        print_separator(f"QUESTION {question_idx}: {question}", "=")
        
        # Mode 1: Enhanced (Original)
        try:
            from contextual_enhanced_retriever import ContextualEnhancedRetriever
            retriever = ContextualEnhancedRetriever(mock_docs, openai_api_key)
            result = get_full_response_from_mode("Enhanced", retriever, question, llm)
            print_response_box("Enhanced", question, result)
        except Exception as e:
            print_response_box("Enhanced", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Mode 2: Contextual Enhanced
        try:
            from contextual_enhanced_retriever import ContextualEnhancedRetriever
            retriever = ContextualEnhancedRetriever(mock_docs, openai_api_key)
            result = get_full_response_from_mode("Contextual Enhanced", retriever, question, llm)
            print_response_box("Contextual Enhanced", question, result)
        except Exception as e:
            print_response_box("Contextual Enhanced", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Mode 3: Hybrid FAISS
        try:
            from hybrid_faiss_retriever import HybridFAISSRetriever
            retriever = HybridFAISSRetriever(mock_docs, openai_api_key)
            result = get_full_response_from_mode("Hybrid FAISS", retriever, question, llm)
            print_response_box("Hybrid FAISS", question, result)
        except Exception as e:
            print_response_box("Hybrid FAISS", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Mode 4: Filtered LangChain (database mode)
        try:
            from filtered_langchain_retriever import FilteredLangChainSQLRetriever
            retriever = FilteredLangChainSQLRetriever(
                db_connection_string=db_connection, 
                llm=llm, 
                enable_monitoring=False
            )
            result = get_full_response_from_mode("Filtered LangChain", retriever, question, llm)
            print_response_box("Filtered LangChain", question, result)
        except Exception as e:
            print_response_box("Filtered LangChain", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Mode 5: TAG Classifier
        try:
            from adaptive_tag_classifier import AdaptiveTAGClassifier
            classifier = AdaptiveTAGClassifier()
            start_time = time.time()
            classification = classifier.classify_query(question)
            execution_time = time.time() - start_time
            
            # Format classification as a readable response
            response_text = f"Query Classification Result:\n"
            response_text += f"• Query Type: {classification.query_type}\n"
            response_text += f"• Confidence Score: {classification.confidence:.3f}\n"
            response_text += f"• Required Tables: {classification.required_tables}\n"
            if hasattr(classification, 'suggested_approach'):
                response_text += f"• Suggested Approach: {classification.suggested_approach}\n"
            
            result = {
                'success': True,
                'response': response_text,
                'time': execution_time
            }
            print_response_box("TAG Classifier", question, result)
        except Exception as e:
            print_response_box("TAG Classifier", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Mode 6: Smart Fallback
        try:
            from smart_fallback_retriever import SmartFallbackRetriever
            retriever = SmartFallbackRetriever(db_connection)
            result = get_full_response_from_mode("Smart Fallback", retriever, question, llm)
            print_response_box("Smart Fallback", question, result)
        except Exception as e:
            print_response_box("Smart Fallback", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Mode 7: Smart Enhanced
        try:
            from smart_enhanced_retriever import SmartEnhancedRetriever
            retriever = SmartEnhancedRetriever(mock_docs, openai_api_key)
            result = get_full_response_from_mode("Smart Enhanced", retriever, question, llm)
            print_response_box("Smart Enhanced", question, result)
        except Exception as e:
            print_response_box("Smart Enhanced", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Mode 8: Guided Agent
        try:
            from guided_agent_retriever import GuidedAgentRetriever
            retriever = GuidedAgentRetriever(
                db_connection_string=db_connection, 
                llm=llm, 
                enable_monitoring=False
            )
            result = get_full_response_from_mode("Guided Agent", retriever, question, llm)
            print_response_box("Guided Agent", question, result)
        except Exception as e:
            print_response_box("Guided Agent", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Mode 9: Contextual Vector
        try:
            from contextual_vector_retriever import ContextualVectorRetriever
            retriever = ContextualVectorRetriever(mock_docs, openai_api_key)
            result = get_full_response_from_mode("Contextual Vector", retriever, question, llm)
            print_response_box("Contextual Vector", question, result)
        except Exception as e:
            print_response_box("Contextual Vector", question, {'success': False, 'response': str(e), 'time': 0})
        
        # Add spacing between questions
        if question_idx < len(TEST_QUESTIONS):
            print("\n" + "─" * 80)
    
    # Final summary
    print_separator("TEST COMPLETED")
    print(f"✅ Tested all 9 modes with {len(TEST_QUESTIONS)} questions")
    print(f"📋 Full response text shown for each mode")
    print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n💡 This test shows actual response content from each mode.")
    print(f"   Use this to compare quality and accuracy of different approaches.")

if __name__ == "__main__":
    run_detailed_response_test()