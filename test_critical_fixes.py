#!/usr/bin/env python3
"""
Test script to validate critical fixes for WINCASA system
Tests database connection, system prompts, and query generation
"""

import os
import sys
import json

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from wincasa.data.db_singleton import get_db_connection, execute_query, get_connection_status
from wincasa.core.llm_handler import WincasaLLMHandler
from wincasa.utils.config_loader import WincasaConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and basic queries"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    
    try:
        # Test connection status
        status = get_connection_status()
        print(f"Connection status: {status}")
        
        # Test simple query with correct table names
        print("\nTesting BEWOHNER table query...")
        result = execute_query("SELECT FIRST 5 MIETERNR, BNAME, BSTR, BPLZORT, Z1 FROM BEWOHNER WHERE EIGNR > -1")
        print(f"✅ Query successful! Found {len(result)} rows")
        for row in result[:3]:
            print(f"  - {row[1]} ({row[0]}): {row[2]}, {row[3]} - Kaltmiete: {row[4]}")
        
        # Test EIGADR table
        print("\nTesting EIGADR table query...")
        result = execute_query("SELECT FIRST 5 EIGNR, ENAME, ESTR, EPLZORT FROM EIGADR")
        print(f"✅ Query successful! Found {len(result)} rows")
        
        # Test OBJEKTE table
        print("\nTesting OBJEKTE table query...")
        result = execute_query("SELECT FIRST 5 ONR, OBEZ, OSTRASSE, OPLZORT FROM OBJEKTE")
        print(f"✅ Query successful! Found {len(result)} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_system_prompts():
    """Test if system prompts are loaded correctly"""
    print("\n" + "="*60)
    print("TEST 2: System Prompts Loading")
    print("="*60)
    
    try:
        config = WincasaConfig()
        
        # Check all VERSION files
        prompts_to_check = [
            'VERSION_A_JSON_SYSTEM.md',
            'VERSION_A_JSON_VANILLA.md', 
            'VERSION_B_SQL_SYSTEM.md',
            'VERSION_B_SQL_VANILLA.md'
        ]
        
        all_good = True
        for prompt_file in prompts_to_check:
            path = os.path.join(os.path.dirname(__file__), 'src', 'wincasa', 'utils', prompt_file)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    content = f.read()
                    # Check for critical corrections
                    has_bewohner = 'BEWOHNER' in content
                    has_eigadr = 'EIGADR' in content
                    has_z1 = 'Z1' in content
                    has_warnings = 'NIEMALS' in content or 'NICHT' in content
                    
                    if has_bewohner and has_eigadr and has_z1 and has_warnings:
                        print(f"✅ {prompt_file}: Contains correct schema information")
                    else:
                        print(f"❌ {prompt_file}: Missing critical schema corrections")
                        all_good = False
            else:
                print(f"❌ {prompt_file}: File not found at {path}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ System prompts test failed: {e}")
        return False

def test_llm_query_generation():
    """Test if LLM generates correct SQL with new prompts"""
    print("\n" + "="*60)
    print("TEST 3: LLM Query Generation")
    print("="*60)
    
    try:
        handler = WincasaLLMHandler()
        
        # Test queries
        test_queries = [
            "Zeige alle Mieter",
            "Liste aller Eigentümer",
            "Summe der Kaltmiete",
            "Finde Leerstand"
        ]
        
        all_good = True
        for query in test_queries:
            print(f"\nTesting: '{query}'")
            
            # Try SQL_SYSTEM mode
            result = handler.query_llm(query, mode='SQL_SYSTEM')
            
            if 'sql' in result:
                sql = result['sql']
                print(f"Generated SQL: {sql[:100]}...")
                
                # Check for correct table names
                has_correct_tables = any(table in sql.upper() for table in ['BEWOHNER', 'EIGADR', 'OBJEKTE', 'WOHNUNG'])
                has_wrong_tables = any(table in sql.upper() for table in ['OWNERS', 'TENANTS'])
                
                if has_correct_tables and not has_wrong_tables:
                    print("✅ SQL uses correct table names")
                else:
                    print("❌ SQL contains incorrect table names")
                    all_good = False
                    
                # Check for Z1 instead of KALTMIETE field
                if 'KALTMIETE' in query.upper():
                    if 'Z1' in sql:
                        print("✅ Correctly uses Z1 for Kaltmiete")
                    else:
                        print("❌ Does not use Z1 for Kaltmiete")
                        all_good = False
            else:
                print("❌ No SQL generated")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ LLM query generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("WINCASA CRITICAL FIX VALIDATION")
    print("="*80)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("System Prompts", test_system_prompts),
        ("LLM Query Generation", test_llm_query_generation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED - System should now work correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Additional fixes needed")
    print("="*80)

if __name__ == "__main__":
    main()