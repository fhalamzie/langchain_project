#!/usr/bin/env python3
"""
Standard database connection module for WINCASA
Uses firebird-driver exclusively for Firebird 5.0 database access
"""

import os
from contextlib import contextmanager
import atexit

# Global connection pool
_connection_pool = []
_max_pool_size = 5

def cleanup_connections():
    """Clean up any remaining connections on exit"""
    global _connection_pool
    for conn in _connection_pool:
        try:
            conn.close()
        except:
            pass
    _connection_pool = []

atexit.register(cleanup_connections)


def get_connection():
    """
    Get a database connection to WINCASA2022.FDB
    
    Returns:
        Database connection object using firebird-driver
    """
    # Load path configuration
    import json
    with open('config/sql_paths.json', 'r') as f:
        path_config = json.load(f)
    
    db_path = path_config['database_path']
    
    # Use firebird-driver (handles NUMERIC correctly)
    import firebird.driver
    
    # Configure for embedded mode (direct connection)
    # According to docs, default is already embedded when no host specified
    return firebird.driver.connect(
        database=db_path,
        user='SYSDBA',
        password='masterkey',
        charset='ISO8859_1'
    )


@contextmanager
def get_cursor():
    """
    Context manager for database cursor with proper transaction management
    
    Yields:
        Database cursor using firebird-driver
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        # Commit the transaction to avoid implicit rollback
        conn.commit()
    except Exception:
        # Rollback on error
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def execute_query(query, params=None):
    """
    Execute a query and return all results
    
    Args:
        query (str): SQL query to execute
        params (tuple): Optional query parameters
        
    Returns:
        List of result rows
    """
    with get_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()


def execute_query_single(query, params=None):
    """
    Execute a query and return single result
    
    Args:
        query (str): SQL query to execute
        params (tuple): Optional query parameters
        
    Returns:
        Single result row or None
    """
    with get_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()


# Test the connection on import
if __name__ == "__main__":
    print("Testing database connection with firebird-driver...")
    try:
        result = execute_query_single("SELECT COUNT(*) FROM BUCHUNG")
        print(f"✅ Success! BUCHUNG table has {result[0]} rows")
        
        # Test aggregation with NUMERIC fields
        result = execute_query_single("SELECT SUM(BETRAG) FROM BUCHUNG WHERE ONRSOLL = 10")
        print(f"✅ SUM aggregation works! Total: {result[0]}")
    except Exception as e:
        print(f"❌ Error: {e}")