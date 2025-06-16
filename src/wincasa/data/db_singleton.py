#!/usr/bin/env python3
"""
WINCASA Database Connection Singleton
Ensures only one Firebird embedded connection across all components
"""

import threading
import logging
from typing import Optional
import firebird.driver
from wincasa.utils.config_loader import WincasaConfig

logger = logging.getLogger(__name__)

# Global singleton instance
_db_connection: Optional[firebird.driver.Connection] = None
_db_lock = threading.Lock()
_config = WincasaConfig()

def get_db_connection() -> firebird.driver.Connection:
    """
    Returns a thread-safe, globally unique Firebird database connection.
    This solves the embedded Firebird limitation of one connection per process.
    """
    global _db_connection
    
    # Double-checked locking for performance
    if _db_connection is None or _db_connection.closed:
        with _db_lock:
            if _db_connection is None or _db_connection.closed:
                logger.info("🔌 Creating SINGLETON Firebird database connection...")
                
                try:
                    db_config = _config.get_db_config()
                    
                    _db_connection = firebird.driver.connect(
                        database=db_config['database'],
                        user=db_config['user'],
                        password=db_config['password'],
                        charset=db_config['charset']
                    )
                    
                    logger.info("✅ SINGLETON database connection created successfully")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create database connection: {e}")
                    raise
    else:
        logger.debug("🎯 Returning existing SINGLETON database connection")
    
    return _db_connection

def close_db_connection():
    """Close the singleton database connection"""
    global _db_connection
    with _db_lock:
        if _db_connection and not _db_connection.closed:
            try:
                _db_connection.close()
                logger.info("🔒 SINGLETON database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
        _db_connection = None

def execute_query(query: str, params: dict = None) -> list:
    """
    Execute a query using the singleton connection.
    Returns results as a list of tuples.
    """
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        
        # Commit if it was a write operation
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
        
        return results
        
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        # Try to rollback on error
        try:
            conn.rollback()
        except:
            pass
        raise