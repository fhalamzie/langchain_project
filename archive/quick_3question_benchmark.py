#!/usr/bin/env python3
"""
Quick 3-Question Benchmark Test for All 9 WINCASA Modes
=======================================================

Tests 3 key questions across all 9 retrieval modes to compare performance and results.
Focus on real database execution and end-to-end results.
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from gemini_llm import get_gemini_llm

# Load environment variables
load_dotenv('/home/envs/openai.env')

# Test questions
TEST_QUESTIONS = [
    "Wer wohnt in der Marienstraße 26, 45307 Essen?",
    "Wie viele Wohnungen gibt es insgesamt?", 
    "Zeige mir alle Bewohner mit ihren Adressdaten"
]

def execute_sql_direct(sql_query: str):
    """Execute SQL directly against Firebird database."""
    try:
        import fdb
        con = fdb.connect(
            host='localhost',
            port=3050,
            database='/home/projects/langchain_project/WINCASA2022.FDB',
            user='sysdba',
            password='masterkey'
        )
        cur = con.cursor()
        cur.execute(sql_query)
        results = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        
        # Format as list of dicts
        formatted_results = []
        for row in results:
            formatted_results.append(dict(zip(columns, row)))
        
        con.close()
        return formatted_results
    except Exception as e:
        return f"Error: {str(e)}"

def test_mode_with_question(mode_name: str, retriever, question: str, llm):
    """Test a specific mode with a question."""
    try:
        start_time = time.time()
        
        # Get response from retriever
        if hasattr(retriever, 'get_response'):
            response = retriever.get_response(question)
        elif hasattr(retriever, 'query'):
            response = retriever.query(question)
        elif hasattr(retriever, 'retrieve'):
            docs = retriever.retrieve(question)
            # Use LLM to generate response from docs
            context = "\n".join([doc.page_content for doc in docs])
            response = llm.invoke(f"Based on this context:\n{context}\n\nAnswer: {question}")
        else:
            response = "Mode not properly configured"
        
        execution_time = time.time() - start_time
        
        # Extract SQL if it's a dict response
        sql_query = None
        if isinstance(response, dict):
            sql_query = response.get('sql_query', response.get('sql', ''))
            response = response.get('response', response.get('answer', str(response)))
        
        # Try to execute SQL if found
        if sql_query and sql_query.strip().upper().startswith('SELECT'):
            db_results = execute_sql_direct(sql_query)
            if not isinstance(db_results, str):  # No error
                response += f"\n\nDatabase results: {len(db_results)} rows found"
        
        return {
            'success': True,
            'response': str(response)[:200] + "..." if len(str(response)) > 200 else str(response),
            'execution_time': execution_time,
            'sql_query': sql_query
        }
    except Exception as e:
        return {
            'success': False,
            'response': f"Error: {str(e)[:100]}...",
            'execution_time': 0,
            'sql_query': None
        }

def run_benchmark():
    """Run the 3-question benchmark across all 9 modes."""
    print("🎯 WINCASA 3-QUESTION BENCHMARK")
    print("="*80)
    print(f"Testing {len(TEST_QUESTIONS)} questions across 9 retrieval modes")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    llm = get_gemini_llm()
    db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    
    # Define modes to test
    modes = [
        {
            'name': 'Enhanced',
            'init': lambda: __import__('enhanced_retrievers').EnhancedRetriever()
        },
        {
            'name': 'Contextual Enhanced', 
            'init': lambda: __import__('contextual_enhanced_retriever').ContextualEnhancedRetriever()
        },
        {
            'name': 'Hybrid FAISS',
            'init': lambda: __import__('hybrid_faiss_retriever').HybridFAISSRetriever()
        },
        {
            'name': 'Filtered LangChain',
            'init': lambda: __import__('filtered_langchain_retriever').FilteredLangChainSQLRetriever(
                db_connection_string=db_connection, llm=llm, enable_monitoring=False
            )
        },
        {
            'name': 'TAG Classifier',
            'init': lambda: __import__('tag_retrieval_mode').TAGRetriever()
        },
        {
            'name': 'Smart Fallback',
            'init': lambda: __import__('smart_fallback_retriever').SmartFallbackRetriever(db_connection, llm)
        },
        {
            'name': 'Smart Enhanced',
            'init': lambda: __import__('smart_enhanced_retriever').SmartEnhancedRetriever()
        },
        {
            'name': 'Guided Agent',
            'init': lambda: __import__('guided_agent_retriever').GuidedAgentRetriever(
                db_connection_string=db_connection, llm=llm, enable_monitoring=False
            )
        },
        {
            'name': 'Contextual Vector',
            'init': lambda: __import__('contextual_vector_retriever').ContextualVectorRetriever()
        }
    ]
    
    results = {}
    
    for question_idx, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n📋 QUESTION {question_idx}: {question}")
        print("-"*80)
        
        results[question] = {}
        
        for mode_idx, mode_config in enumerate(modes, 1):
            mode_name = mode_config['name']
            print(f"  {mode_idx}. Testing {mode_name}...", end=" ")
            
            try:
                retriever = mode_config['init']()
                result = test_mode_with_question(mode_name, retriever, question, llm)
                results[question][mode_name] = result
                
                if result['success']:
                    print(f"✅ {result['execution_time']:.2f}s")
                else:
                    print(f"❌ Failed")
                    
            except Exception as e:
                results[question][mode_name] = {
                    'success': False,
                    'response': f"Init error: {str(e)[:50]}...",
                    'execution_time': 0,
                    'sql_query': None
                }
                print(f"❌ Init failed")
    
    # Summary report
    print("\n" + "="*80)
    print("📊 BENCHMARK SUMMARY")
    print("="*80)
    
    # Success rates by mode
    mode_success_rates = {}
    for mode_config in modes:
        mode_name = mode_config['name']
        successes = sum(1 for q in TEST_QUESTIONS if results[q].get(mode_name, {}).get('success', False))
        mode_success_rates[mode_name] = successes / len(TEST_QUESTIONS) * 100
    
    print("\n🎯 SUCCESS RATES BY MODE:")
    print("-"*50)
    for mode_name, success_rate in sorted(mode_success_rates.items(), key=lambda x: x[1], reverse=True):
        print(f"{mode_name:20s} {success_rate:6.1f}% ({int(success_rate/100*3)}/3)")
    
    # Average execution times
    print("\n⚡ AVERAGE EXECUTION TIMES:")
    print("-"*50)
    mode_times = {}
    for mode_config in modes:
        mode_name = mode_config['name']
        times = [results[q].get(mode_name, {}).get('execution_time', 0) 
                for q in TEST_QUESTIONS 
                if results[q].get(mode_name, {}).get('success', False)]
        avg_time = sum(times) / len(times) if times else 0
        mode_times[mode_name] = avg_time
    
    for mode_name, avg_time in sorted(mode_times.items(), key=lambda x: x[1]):
        print(f"{mode_name:20s} {avg_time:6.2f}s")
    
    # Best performing mode
    best_mode = max(mode_success_rates.items(), key=lambda x: x[1])
    fastest_mode = min(mode_times.items(), key=lambda x: x[1] if x[1] > 0 else float('inf'))
    
    print(f"\n🏆 BEST SUCCESS RATE: {best_mode[0]} ({best_mode[1]:.1f}%)")
    print(f"🚀 FASTEST MODE: {fastest_mode[0]} ({fastest_mode[1]:.2f}s)")
    
    # Question-specific results
    print("\n📋 DETAILED RESULTS BY QUESTION:")
    print("="*80)
    for question in TEST_QUESTIONS:
        print(f"\nQuestion: {question}")
        print("-"*60)
        for mode_config in modes:
            mode_name = mode_config['name']
            result = results[question].get(mode_name, {})
            status = "✅" if result.get('success', False) else "❌"
            time_str = f"{result.get('execution_time', 0):.2f}s"
            response = result.get('response', 'No response')[:100]
            print(f"  {status} {mode_name:20s} {time_str:8s} {response}")
    
    print(f"\n🎯 BENCHMARK COMPLETED at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return results

if __name__ == "__main__":
    results = run_benchmark()