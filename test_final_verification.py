#!/usr/bin/env python3
"""
Final verification test - Enhanced knowledge system with fixed retriever
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/envs/openrouter.env')
load_dotenv('/home/envs/openai.env')

# Set up path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from firebird_sql_agent_direct import FirebirdDirectSQLAgent

def test_enhanced_system():
    """Test the enhanced knowledge system with fixed retriever."""
    print("Testing ENHANCED KNOWLEDGE SYSTEM (with fixed retriever)...")
    
    # Use enhanced configuration
    db_connection_string = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    llm_model_name = "gpt-4o-mini"
    retrieval_mode = "faiss"  # Enhanced FAISS
    use_enhanced_knowledge = True  # This enables the enhanced system
    
    print(f"Parameters:")
    print(f"  DB: {db_connection_string}")
    print(f"  LLM: {llm_model_name}")
    print(f"  Retrieval: {retrieval_mode}")
    print(f"  Enhanced Knowledge: {use_enhanced_knowledge}")
    
    try:
        # Create agent with enhanced configuration
        agent = FirebirdDirectSQLAgent(
            db_connection_string=db_connection_string,
            llm=llm_model_name,
            retrieval_mode=retrieval_mode,
            use_enhanced_knowledge=use_enhanced_knowledge
        )
        
        print(f"\n✅ Enhanced agent initialized successfully!")
        print(f"   FDB Interface: {type(agent.fdb_interface)}")
        print(f"   LLM: {type(agent.llm)}")
        print(f"   Active Retriever: {type(agent.active_retriever)}")
        print(f"   Documents loaded: {len(agent.parsed_docs)}")
        
        # Test multiple address queries
        test_queries = [
            "Wer wohnt in der Marienstraße 26?",
            "Zeige mir alle Bewohner in Essen",
            "Welche Tabellen enthalten Personendaten?"
        ]
        
        results = []
        for i, test_query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"🔍 Test Query {i}: {test_query}")
            print(f"{'='*60}")
            
            result = agent.query(test_query)
            results.append(result)
            
            print(f"\n🎯 Final Answer:")
            print(result.get('agent_final_answer', 'No final answer'))
            
            print(f"\n💾 Generated SQL:")
            print(result.get('generated_sql', 'No SQL generated'))
            
            # Check if we got good results
            final_answer = result.get('agent_final_answer', '')
            if i == 1 and 'Petra Nabakowski' in str(final_answer):
                print(f"✅ Query {i}: SUCCESS! Found correct residents")
            elif i == 2 and 'Bewohner' in str(final_answer):
                print(f"✅ Query {i}: SUCCESS! Found residents in Essen")
            elif i == 3 and ('BEWOHNER' in str(final_answer) or 'EIGENTUEMER' in str(final_answer)):
                print(f"✅ Query {i}: SUCCESS! Found person tables")
            else:
                print(f"❓ Query {i}: Check result")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_enhanced_system()