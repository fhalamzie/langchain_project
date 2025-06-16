#!/usr/bin/env python3
"""
Sequential Mode Testing
Tests all 6 WINCASA modes sequentially to avoid database conflicts
"""

import requests
import time
import json
import pandas as pd
from datetime import datetime

# Test queries
TEST_QUERIES = [
    "Wer sind die aktuellen Mieter von Objekt 001?",
    "Zeige mir alle Objekte im Portfolio",
    "Welche Mieter haben Mietrückstände?",
    "Wie hoch sind die Mieteinnahmen von Objekt 002?",
    "Welche Wohnungen stehen aktuell leer?",
    "Zeige die Eigentümer von Objekt 003",
    "Welche Beschlüsse wurden 2024 gefasst?",
    "Wie hoch ist die Instandhaltungsrücklage?",
    "Welche Konten haben negative Salden?",
    "Zeige alle Beiräte der WEG"
]

# All 6 modes
MODES = [
    "json_standard",    # Mode 1
    "json_vanilla",     # Mode 2  
    "sql_standard",     # Mode 3
    "sql_vanilla",      # Mode 4
    "optimized_search", # Mode 5
    "semantic_template" # Mode 6
]

BASE_URL = "http://localhost:8667"

def test_mode(mode, query):
    """Test a single query in a specific mode"""
    print(f"  Testing mode: {mode}")
    
    try:
        # Wait a bit between requests to avoid conflicts
        time.sleep(2)
        
        payload = {
            "query": query,
            "mode": mode,
            "debug": True
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/query", json=payload, timeout=30)
        end_time = time.time()
        
        duration = round((end_time - start_time) * 1000, 2)  # ms
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract key metrics
            answer = result.get('answer', 'No answer')
            status = result.get('status', 'unknown')
            layer = result.get('layer_info', {}).get('active_layer', 'unknown')
            
            # Determine success based on content
            has_data = bool(answer and answer != "Keine Datensätze gefunden" and len(answer.strip()) > 50)
            
            return {
                "mode": mode,
                "status": "SUCCESS" if has_data else "EMPTY",
                "duration_ms": duration,
                "layer": layer,
                "answer_length": len(answer),
                "answer_preview": answer[:100] + "..." if len(answer) > 100 else answer
            }
        else:
            return {
                "mode": mode,
                "status": "ERROR",
                "duration_ms": duration,
                "layer": "unknown",
                "answer_length": 0,
                "answer_preview": f"HTTP {response.status_code}: {response.text[:100]}"
            }
            
    except Exception as e:
        return {
            "mode": mode,
            "status": "EXCEPTION",
            "duration_ms": 0,
            "layer": "unknown", 
            "answer_length": 0,
            "answer_preview": str(e)[:100]
        }

def main():
    print("=== WINCASA Sequential Mode Testing ===")
    print(f"Testing {len(TEST_QUERIES)} queries across {len(MODES)} modes")
    print(f"Total tests: {len(TEST_QUERIES) * len(MODES)}")
    print()
    
    results = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"Query {i}/{len(TEST_QUERIES)}: {query}")
        
        for mode in MODES:
            result = test_mode(mode, query)
            result['query_num'] = i
            result['query'] = query
            results.append(result)
            print(f"    {result['mode']}: {result['status']} ({result['duration_ms']}ms)")
        
        print()
        time.sleep(3)  # Pause between queries
    
    # Generate summary report
    print("=== SUMMARY REPORT ===")
    
    # Results by mode
    df = pd.DataFrame(results)
    
    print("\n1. SUCCESS RATE BY MODE:")
    success_by_mode = df.groupby('mode')['status'].apply(lambda x: (x == 'SUCCESS').sum()).sort_values(ascending=False)
    for mode, count in success_by_mode.items():
        percentage = (count / len(TEST_QUERIES)) * 100
        print(f"   {mode}: {count}/{len(TEST_QUERIES)} ({percentage:.1f}%)")
    
    print("\n2. AVERAGE RESPONSE TIME BY MODE:")
    avg_time_by_mode = df[df['status'] == 'SUCCESS'].groupby('mode')['duration_ms'].mean().sort_values()
    for mode, avg_time in avg_time_by_mode.items():
        print(f"   {mode}: {avg_time:.1f}ms")
    
    print("\n3. ERROR SUMMARY:")
    error_summary = df[df['status'] != 'SUCCESS']['status'].value_counts()
    for status, count in error_summary.items():
        print(f"   {status}: {count}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sequential_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n4. DETAILED RESULTS saved to: {filename}")
    
    # Generate comparison table
    pivot_table = df.pivot_table(
        values='status', 
        index='query',
        columns='mode',
        aggfunc=lambda x: x.iloc[0],
        fill_value='MISSING'
    )
    
    print("\n5. RESULTS MATRIX:")
    print(pivot_table.to_string())

if __name__ == "__main__":
    main()