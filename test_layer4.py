#!/usr/bin/env python3
"""Consolidated test for Layer 4 queries - combines best of comprehensive and final tests"""

import json
import os
import re
import sys
from datetime import datetime

import firebird.driver
from database_connection import get_connection

# Load path configuration
with open('config/sql_paths.json', 'r') as f:
    PATH_CONFIG = json.load(f)

def clean_unicode_from_sql(sql_content):
    """Remove all Unicode characters from SQL content"""
    # Common Unicode characters that cause issues
    unicode_chars = {
        '\u2705': '[OK]',  # ✅
        '\u2192': '->',    # →
        '\u2013': '-',     # –
        '\u2014': '--',    # —
        '\u201c': '"',     # "
        '\u201d': '"',     # "
        '\u2018': "'",     # '
        '\u2019': "'",     # '
        '\xfc': 'ue',      # ü
        '\xf6': 'oe',      # ö
        '\xe4': 'ae',      # ä
        '\xdf': 'ss',      # ß
    }
    
    cleaned = sql_content
    for unicode_char, replacement in unicode_chars.items():
        cleaned = cleaned.replace(unicode_char, replacement)
    
    # Remove any remaining non-ASCII characters
    cleaned = ''.join(char if ord(char) < 128 else '?' for char in cleaned)
    
    return cleaned

def extract_query_from_file(file_path):
    """Extract SQL query from file, removing comments"""
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Clean Unicode
    sql_content = clean_unicode_from_sql(sql_content)
    
    # Extract query (remove comments)
    sql_lines = []
    in_final_comment = False
    for line in sql_content.split('\n'):
        if line.strip().startswith('/*') and any(word in line for word in ['ERWARTETES', 'LAYER 4', 'EXPECTED']):
            in_final_comment = True
        if not in_final_comment:
            sql_lines.append(line)
    
    query = '\n'.join(sql_lines).strip()
    while query.endswith(';'):
        query = query[:-1].strip()
    
    return query

def test_single_query(sql_file, conn):
    """Test a single SQL query"""
    try:
        query = extract_query_from_file(sql_file)
        
        # Execute query
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch sample results
        rows = cursor.fetchmany(5)
        cursor.close()
        
        return {
            'status': 'SUCCESS',
            'rows_sample': len(rows),
            'error': None
        }
        
    except Exception as e:
        return {
            'status': 'FAILED',
            'rows_sample': 0,
            'error': str(e)
        }

def test_all_layer4_queries():
    """Test all Layer 4 queries and report results"""
    
    sql_dir = PATH_CONFIG['sql_queries_dir']
    
    # Get all SQL files
    sql_files = [f for f in os.listdir(sql_dir) if f.endswith('.sql')]
    sql_files.sort()
    
    # Output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"layer4_test_{timestamp}.txt"
    
    print(f"🧪 Testing {len(sql_files)} Layer 4 queries...")
    print(f"📊 Results will be saved to: {output_file}")
    
    with open(output_file, 'w') as out:
        out.write(f"Layer 4 Consolidated Test - {datetime.now()}\n")
        out.write("=" * 60 + "\n\n")
        
        total = len(sql_files)
        working = 0
        results = {}
        
        # Get connection once
        try:
            conn = get_connection()
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return
        
        for sql_file in sql_files:
            print(f"Testing {sql_file}...", end='')
            
            result = test_single_query(os.path.join(sql_dir, sql_file), conn)
            results[sql_file] = result
            
            if result['status'] == 'SUCCESS':
                working += 1
                print(" ✅")
                out.write(f"✅ {sql_file}: WORKING ({result['rows_sample']} sample rows)\n")
            else:
                print(" ❌")
                out.write(f"❌ {sql_file}: FAILED\n")
                out.write(f"   Error: {result['error']}\n")
        
        # Summary
        out.write("\n" + "=" * 60 + "\n")
        out.write(f"SUMMARY: {working}/{total} queries working ({working/total*100:.1f}%)\n")
        
        # Close connection
        conn.close()
        
    print(f"\n📊 Summary: {working}/{total} queries working ({working/total*100:.1f}%)")
    print(f"📄 Full results saved to: {output_file}")

if __name__ == "__main__":
    test_all_layer4_queries()