#!/usr/bin/env python3
"""Comprehensive test of WINCASA system"""

import sys
import os
import json
import time
sys.path.append('src')

from wincasa.core.wincasa_query_engine import WincasaQueryEngine
from wincasa.data.sql_executor import WincasaSQLExecutor
from wincasa.data.data_access_layer import WincasaDataAccess

def test_marienstrasse_26():
    """Test the critical Marienstraße 26 query that should find 5 tenants"""
    print("=== Testing Marienstraße 26 Query ===\n")
    
    # Test 1: Through Query Engine
    print("1. Testing through Query Engine:")
    engine = WincasaQueryEngine()
    result = engine.process_query("wer wohnt marienstr 26")
    
    print(f"   Result count: {result.result_count}")
    print(f"   Success: {result.result_count > 0}")
    print(f"   Answer preview: {result.answer[:100]}...")
    
    # Test 2: Through Data Access Layer
    print("\n2. Testing through Data Access Layer:")
    dal = WincasaDataAccess(source="json")
    result = dal.search_tenants_by_address("Marienstraße 26")
    
    print(f"   Found: {len(result['data'])} tenants")
    if result['data']:
        print("   Tenants:")
        for tenant in result['data']:
            # Try multiple name fields
            last_name = tenant.get('NACHNAME', tenant.get('BEWNAME', tenant.get('name', 'N/A')))
            first_name = tenant.get('VORNAME', tenant.get('BEWVNAME', ''))
            name = f"{first_name} {last_name}".strip() if first_name else last_name
            addr = tenant.get('OBJEKT_STRASSE', tenant.get('adresse', 'N/A'))
            unit = tenant.get('WOHNUNGSBEZEICHNUNG', tenant.get('ENR', ''))
            print(f"     - {name} at {addr} {unit}")
    
    # Test 3: Direct SQL Query
    print("\n3. Testing through direct SQL:")
    sql_exec = WincasaSQLExecutor()
    
    # Check if we have correct field names
    sql = """
    SELECT 
        B.KNR,
        B.BNAME AS NACHNAME,
        B.BVNAME AS VORNAME,
        O.OSTRASSE,
        O.OPLZORT,
        O.ONR
    FROM BEWOHNER B
    JOIN OBJEKTE O ON B.ONR = O.ONR
    WHERE O.ONR = 18  -- Marienstraße 26 is ONR=18
    AND B.VENDE IS NULL  -- Active tenants
    """
    
    result = sql_exec.execute_query(sql)
    print(f"   SQL Success: {result['success']}")
    print(f"   Rows found: {result['row_count']}")
    if result['success'] and result['data']:
        for row in result['data']:
            print(f"     - {row}")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n\n=== Testing Edge Cases ===\n")
    
    engine = WincasaQueryEngine()
    
    test_cases = [
        # Empty query
        ("", "Empty query"),
        # Special characters
        ("Wer wohnt in der Straße mit @#$%", "Special characters"),
        # Very long query
        ("a" * 1000, "Very long query"),
        # SQL injection attempt
        ("'; DROP TABLE BEWOHNER; --", "SQL injection"),
        # Mixed language
        ("Show all tenants in Marienstraße", "Mixed language"),
        # Typos
        ("wher livs marienstrase 26", "With typos"),
    ]
    
    for query, description in test_cases:
        print(f"\n📍 {description}: '{query[:50]}...'")
        try:
            result = engine.process_query(query)
            print(f"   ✅ Handled: {result.result_count} results")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_performance():
    """Test system performance"""
    print("\n\n=== Testing Performance ===\n")
    
    engine = WincasaQueryEngine()
    
    queries = [
        "wer wohnt marienstr 26",
        "tel borowski",
        "miete nabakowski",
        "einheiten sundeki",
        "weg neusser str"
    ]
    
    times = []
    
    for query in queries:
        start = time.time()
        result = engine.process_query(query)
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)
        print(f"Query: '{query}' - {elapsed:.1f}ms")
    
    avg_time = sum(times) / len(times)
    print(f"\nAverage response time: {avg_time:.1f}ms")
    print(f"Min: {min(times):.1f}ms, Max: {max(times):.1f}ms")

def test_version_files():
    """Test VERSION file loading"""
    print("\n\n=== Testing VERSION Files ===\n")
    
    from wincasa.utils.config_loader import WincasaConfig
    
    config = WincasaConfig()
    
    modes = ['json_standard', 'json_vanilla', 'sql_standard', 'sql_vanilla']
    
    for mode in modes:
        print(f"\n{mode}:")
        # Temporarily set mode
        os.environ['SYSTEM_MODE'] = mode
        config = WincasaConfig()  # Reload with new mode
        
        prompt = config.load_system_prompt()
        if prompt:
            print(f"   ✅ Loaded ({len(prompt)} chars)")
            # Check for common SQL errors
            if 'sql' in mode:
                has_aktiv_warning = 'B.AKTIV' in prompt or 'AKTIV Feld' in prompt
                has_address_warning = 'BSTR' in prompt or 'BPLZORT' in prompt
                print(f"   Has AKTIV warning: {has_aktiv_warning}")
                print(f"   Has address field info: {has_address_warning}")
        else:
            print(f"   ❌ Failed to load")

def main():
    """Run all tests"""
    print("WINCASA Comprehensive System Test\n")
    print("=" * 80)
    
    test_marienstrasse_26()
    test_edge_cases()
    test_performance()
    test_version_files()
    
    print("\n" + "=" * 80)
    print("Test complete!")

if __name__ == "__main__":
    main()