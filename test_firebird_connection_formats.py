#!/usr/bin/env python3
"""
Test script to determine the correct SQLAlchemy connection string format for Firebird server connections.

This script tests various connection string formats to identify which one works with
SQLAlchemy and Firebird server running on localhost:3050.
"""

import os
import sys
import traceback
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

def test_connection_format(connection_string, format_name):
    """
    Test a specific connection string format.
    
    Args:
        connection_string: The connection string to test
        format_name: Descriptive name for this format
        
    Returns:
        tuple: (success, error_message, result)
    """
    print(f"\n{'='*60}")
    print(f"Testing {format_name}")
    print(f"Connection: {connection_string}")
    print('='*60)
    
    try:
        # Parse URL first
        parsed = make_url(connection_string)
        print(f"✅ URL parsing successful:")
        print(f"  Host: {parsed.host}")
        print(f"  Port: {parsed.port}")
        print(f"  Database: {parsed.database}")
        print(f"  Username: {parsed.username}")
        print(f"  Password: {parsed.password}")
        print(f"  Drivername: {parsed.drivername}")
        
        # Create engine
        print("\n🔧 Creating SQLAlchemy engine...")
        engine = create_engine(connection_string, echo=False)
        
        # Test connection
        print("🔌 Testing database connection...")
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute(text("SELECT rdb$relation_id FROM rdb$database"))
            db_id = result.fetchone()
            print(f"✅ Connection successful! Database ID: {db_id[0] if db_id else 'N/A'}")
            
            # Test table count
            result = connection.execute(text("""
                SELECT COUNT(*) FROM rdb$relations 
                WHERE rdb$view_blr IS NULL 
                AND (rdb$system_flag IS NULL OR rdb$system_flag = 0)
                AND rdb$relation_name NOT STARTING WITH 'RDB$'
                AND rdb$relation_name NOT STARTING WITH 'MON$'
            """))
            table_count = result.fetchone()
            print(f"✅ Found {table_count[0] if table_count else 0} user tables")
            
        return True, None, {"db_id": db_id[0] if db_id else None, "table_count": table_count[0] if table_count else 0}
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Failed: {error_msg}")
        return False, error_msg, None

def main():
    """Test various connection string formats"""
    print("🔥 Firebird SQLAlchemy Connection String Format Tester")
    print("=" * 80)
    
    # Test formats based on research and existing code patterns
    test_formats = [
        # Format 1: Current working format from codebase (double slash)
        (
            "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            "Current Working Format (Double Slash)"
        ),
        
        # Format 2: Single slash format
        (
            "firebird+fdb://sysdba:masterkey@localhost:3050/home/projects/langchain_project/WINCASA2022.FDB",
            "Single Slash Format"
        ),
        
        # Format 3: firebird dialect (without +fdb)
        (
            "firebird://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            "Firebird Dialect (No +fdb, Double Slash)"
        ),
        
        # Format 4: firebird dialect single slash
        (
            "firebird://sysdba:masterkey@localhost:3050/home/projects/langchain_project/WINCASA2022.FDB",
            "Firebird Dialect (No +fdb, Single Slash)"
        ),
        
        # Format 5: Windows-style absolute path (for comparison)
        (
            "firebird+fdb://sysdba:masterkey@localhost:3050//C:/path/to/database.fdb",
            "Windows-style Path (Testing Path Handling)"
        ),
        
        # Format 6: With query parameters
        (
            "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB?charset=UTF8",
            "With Query Parameters"
        ),
        
        # Format 7: Alternative credentials
        (
            "firebird+fdb://SYSDBA:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            "Alternative Credentials (UPPERCASE)"
        ),
        
        # Format 8: IP address instead of localhost
        (
            "firebird+fdb://sysdba:masterkey@127.0.0.1:3050//home/projects/langchain_project/WINCASA2022.FDB",
            "IP Address Instead of Localhost"
        ),
    ]
    
    results = []
    successful_formats = []
    
    for connection_string, format_name in test_formats:
        success, error, result = test_connection_format(connection_string, format_name)
        results.append((format_name, connection_string, success, error, result))
        
        if success:
            successful_formats.append((format_name, connection_string))
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 SUMMARY OF RESULTS")
    print("=" * 80)
    
    if successful_formats:
        print(f"✅ {len(successful_formats)} format(s) worked successfully:")
        for i, (name, conn_str) in enumerate(successful_formats, 1):
            print(f"\n{i}. {name}")
            print(f"   Connection: {conn_str}")
    else:
        print("❌ No formats worked successfully!")
    
    print(f"\n❌ {len(results) - len(successful_formats)} format(s) failed:")
    for name, conn_str, success, error, result in results:
        if not success:
            print(f"\n• {name}")
            print(f"  Error: {error}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("🔍 ANALYSIS AND RECOMMENDATIONS")
    print("=" * 80)
    
    if successful_formats:
        best_format = successful_formats[0]
        print(f"✅ RECOMMENDED FORMAT:")
        print(f"   {best_format[1]}")
        print(f"\nThis format should be used for SQLAlchemy Firebird server connections.")
        
        # Parse the successful format for analysis
        try:
            parsed = make_url(best_format[1])
            print(f"\n🔍 Format Analysis:")
            print(f"   Dialect: {parsed.drivername}")
            print(f"   Host: {parsed.host}")
            print(f"   Port: {parsed.port}")
            print(f"   Database Path: {parsed.database}")
            print(f"   Key Pattern: Use '//' before absolute path for server connections")
        except Exception as e:
            print(f"   Analysis error: {e}")
    else:
        print("❌ No working format found. Possible issues:")
        print("   1. Firebird server not running on localhost:3050")
        print("   2. Authentication credentials incorrect")
        print("   3. Database file not accessible")
        print("   4. SQLAlchemy Firebird driver not properly installed")
    
    return 0 if successful_formats else 1

if __name__ == "__main__":
    exit(main())