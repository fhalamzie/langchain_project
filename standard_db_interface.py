#!/usr/bin/env python3
"""
Standard Database Interface for WINCASA System
==============================================

Provides a unified interface for all database operations using SQLAlchemy
connection pooling to eliminate the recurring permission issues caused by
direct fdb.connect() calls.

This module ensures ALL database access goes through the same tested
connection method that works across all retrieval modes.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from database_connection_pool import FirebirdConnectionPool

# Configure logging
logger = logging.getLogger(__name__)

# Standard database connection string
DB_CONNECTION_STRING = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"

class StandardDatabaseInterface:
    """Standardized database interface using connection pooling."""
    
    def __init__(self, connection_string: str = None):
        """Initialize with standardized connection."""
        self.connection_string = connection_string or DB_CONNECTION_STRING
        self._pool = None
    
    @property
    def pool(self):
        """Lazy initialization of connection pool."""
        if self._pool is None:
            self._pool = FirebirdConnectionPool(self.connection_string)
        return self._pool
    
    def execute_query(self, sql_query: str) -> Tuple[bool, List[Dict], str]:
        """
        Execute SQL query and return results in standard format.
        
        Returns:
            Tuple[bool, List[Dict], str]: (success, results, message)
        """
        try:
            logger.info(f"Executing SQL: {sql_query}")
            
            # Execute query using connection pool
            results = self.pool.execute_query(sql_query)
            
            message = f"Found {len(results)} rows"
            logger.info(f"Query successful: {message}")
            return True, results, message
            
        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            success, results, _ = self.execute_query("SELECT COUNT(*) as TEST FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
            return success and len(results) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Global instance for easy import
db_interface = StandardDatabaseInterface()

def execute_sql(sql_query: str) -> Tuple[bool, List[Dict], str]:
    """
    Convenience function for executing SQL queries.
    
    This is the function ALL tests and modules should use instead of
    direct fdb.connect() calls.
    """
    return db_interface.execute_query(sql_query)

def test_database_connection() -> bool:
    """Test if database is accessible."""
    return db_interface.test_connection()

def get_apartment_count() -> Optional[int]:
    """Get total apartment count - commonly used query."""
    success, results, _ = execute_sql("SELECT COUNT(*) as APARTMENT_COUNT FROM WOHNUNG")
    if success and results:
        return results[0]['APARTMENT_COUNT']
    return None

def get_resident_by_address(street: str, city: str = None) -> List[Dict]:
    """Get residents by address - commonly used query."""
    if city:
        sql = f"SELECT VNAMEMIETER, VNAMEVERMIETER, BSTR, BPLZORT FROM BEWOHNER WHERE BSTR LIKE '%{street}%' AND BPLZORT LIKE '%{city}%'"
    else:
        sql = f"SELECT VNAMEMIETER, VNAMEVERMIETER, BSTR, BPLZORT FROM BEWOHNER WHERE BSTR LIKE '%{street}%'"
    
    success, results, _ = execute_sql(sql)
    return results if success else []

def get_owners_by_city(city: str) -> List[Dict]:
    """Get owners by city - commonly used query."""
    sql = f"SELECT NAME, VNAME, ORT, EMAIL FROM EIGENTUEMER WHERE ORT LIKE '%{city}%'"
    success, results, _ = execute_sql(sql)
    return results if success else []

# Backwards compatibility function for existing code
def execute_sql_direct(sql_query: str) -> Tuple[bool, List[Dict], str]:
    """
    Backwards compatibility wrapper.
    
    DEPRECATED: Use execute_sql() instead.
    """
    logger.warning("execute_sql_direct() is deprecated. Use execute_sql() instead.")
    return execute_sql(sql_query)