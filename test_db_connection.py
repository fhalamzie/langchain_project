#!/usr/bin/env python3
"""
Test database connection and fix connection shutdown issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from wincasa.data.db_singleton import get_db_connection, close_db_connection

def test_connection():
    """Test database connection and reset if needed"""
    print("Testing database connection...")
    
    try:
        # First close any existing connections
        close_db_connection()
        print("✅ Closed existing connections")
        
        # Get new connection
        conn = get_db_connection()
        print("✅ Got database connection")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM BEWOHNER")
        result = cursor.fetchone()
        cursor.close()
        
        print(f"✅ BEWOHNER table has {result[0]} records")
        print("✅ Database connection is working properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)