#!/usr/bin/env python3
"""Test SQL mode queries for WINCASA system"""

import sys
import os
sys.path.append('src')

from wincasa.core.llm_handler import WincasaLLMHandler
from wincasa.data.sql_executor import WincasaSQLExecutor

def test_sql_queries():
    """Test critical SQL queries directly"""
    
    print("=== Testing SQL Mode Queries ===\n")
    
    # Initialize components
    llm_handler = WincasaLLMHandler(mode="sql_standard")
    sql_executor = WincasaSQLExecutor()
    
    # Test queries
    test_queries = [
        "Wer wohnt in der Marienstraße 26?",
        "Zeige alle aktiven Mieter in Marienstraße 26",
        "Liste alle Mieter mit Objekt ONR=18",
        "Kontaktdaten von Wolfgang Borowski",
        "Mieter ohne Email-Adresse"
    ]
    
    for query in test_queries:
        print(f"\n📍 Query: {query}")
        
        # Generate SQL
        try:
            result = llm_handler.process_query(query)
            
            if result.get('success'):
                sql = result.get('sql', '')
                print(f"✅ Generated SQL:\n{sql}")
                
                # Execute SQL
                exec_result = sql_executor.execute_query(sql)
                if exec_result['success']:
                    print(f"✅ Results: {exec_result['row_count']} rows")
                    if exec_result['data'] and len(exec_result['data']) > 0:
                        print(f"   First row: {exec_result['data'][0]}")
                else:
                    print(f"❌ SQL Execution Error: {exec_result['error']}")
            else:
                print(f"❌ LLM Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test specific known issues
    print("\n\n=== Testing Known SQL Issues ===")
    
    # Issue 1: B.AKTIV field
    print("\n1. Testing B.AKTIV field issue:")
    test_sql = "SELECT * FROM BEWOHNER B WHERE B.VENDE IS NULL"
    exec_result = sql_executor.execute_query(test_sql)
    print(f"   Valid query (VENDE IS NULL): {exec_result['success']}")
    
    test_sql = "SELECT * FROM BEWOHNER B WHERE B.AKTIV = 1"
    exec_result = sql_executor.execute_query(test_sql)
    print(f"   Invalid query (B.AKTIV): {exec_result['success']}")
    if not exec_result['success']:
        print(f"   Error: {exec_result['error']}")
    
    # Issue 2: Address fields
    print("\n2. Testing address field names:")
    test_sql = "SELECT BSTR, BPLZORT FROM BEWOHNER WHERE BEWNR = 1"
    exec_result = sql_executor.execute_query(test_sql)
    print(f"   Valid fields (BSTR, BPLZORT): {exec_result['success']}")
    
    test_sql = "SELECT ADRESSE, STREET FROM BEWOHNER WHERE BEWNR = 1"
    exec_result = sql_executor.execute_query(test_sql)
    print(f"   Invalid fields (ADRESSE, STREET): {exec_result['success']}")
    if not exec_result['success']:
        print(f"   Error: {exec_result['error']}")

if __name__ == "__main__":
    test_sql_queries()