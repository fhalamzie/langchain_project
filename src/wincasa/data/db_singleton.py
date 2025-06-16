#!/usr/bin/env python3
"""
WINCASA Database Connection Singleton
Ensures only one Firebird embedded connection across all components
"""

import threading
import logging
import time
from typing import Optional
import firebird.driver
from wincasa.utils.config_loader import WincasaConfig

logger = logging.getLogger(__name__)

# Global singleton instance
_db_connection: Optional[firebird.driver.Connection] = None
_db_lock = threading.Lock()
_config = WincasaConfig()
_last_connection_check = 0
_connection_check_interval = 60  # Check connection every 60 seconds

def get_db_connection() -> firebird.driver.Connection:
    """
    Returns a thread-safe, globally unique Firebird database connection.
    This solves the embedded Firebird limitation of one connection per process.
    
    Now includes connection health checking and automatic reconnection.
    """
    global _db_connection, _last_connection_check
    
    current_time = time.time()
    need_check = (current_time - _last_connection_check) > _connection_check_interval
    
    # Double-checked locking for performance
    if _db_connection is None or not _is_connection_healthy(_db_connection) or need_check:
        with _db_lock:
            # Re-check after acquiring lock
            if _db_connection is None or not _is_connection_healthy(_db_connection):
                logger.info("🔌 Creating SINGLETON Firebird database connection...")
                _db_connection = _create_connection()
            elif need_check:
                # Check if connection is still healthy
                if not _is_connection_healthy(_db_connection):
                    logger.warning("⚠️ Database connection unhealthy, reconnecting...")
                    _close_connection_safely(_db_connection)
                    _db_connection = _create_connection()
                _last_connection_check = current_time
    else:
        logger.debug("🎯 Returning existing SINGLETON database connection")
    
    return _db_connection

def _create_connection() -> firebird.driver.Connection:
    """Create a new database connection"""
    try:
        db_config = _config.get_db_config()
        
        conn = firebird.driver.connect(
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            charset=db_config['charset']
        )
        
        logger.info("✅ SINGLETON database connection created successfully")
        return conn
        
    except Exception as e:
        logger.error(f"❌ Failed to create database connection: {e}")
        raise

def _is_connection_healthy(conn: firebird.driver.Connection) -> bool:
    """Check if connection is still healthy"""
    if conn is None:
        return False
    
    # Firebird driver doesn't have 'closed' attribute, check by trying to use it
    try:
        # Simple health check query
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM RDB$DATABASE")
        cursor.fetchone()
        cursor.close()
        return True
    except Exception as e:
        logger.debug(f"Connection health check failed: {e}")
        return False

def _close_connection_safely(conn: Optional[firebird.driver.Connection]):
    """Safely close a connection"""
    if conn:
        try:
            conn.close()
            logger.info("🔒 Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

def close_db_connection():
    """Close the singleton database connection"""
    global _db_connection
    with _db_lock:
        _close_connection_safely(_db_connection)
        _db_connection = None

def execute_query(query: str, params: dict = None) -> list:
    """
    Execute a query using the singleton connection.
    Returns results as a list of tuples.
    
    Now includes automatic retry on connection errors.
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = get_db_connection()
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
            
        except firebird.driver.DatabaseError as e:
            error_msg = str(e).lower()
            if 'connection shutdown' in error_msg or 'connection lost' in error_msg:
                retry_count += 1
                logger.warning(f"Database connection error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    # Force reconnection
                    with _db_lock:
                        _close_connection_safely(_db_connection)
                        _db_connection = None
                    time.sleep(0.5 * retry_count)  # Exponential backoff
                    continue
            
            logger.error(f"Query execution error: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            # Try to rollback on error
            try:
                conn.rollback()
            except:
                pass
            raise
    
    raise Exception(f"Failed to execute query after {max_retries} retries")

def get_connection_status() -> dict:
    """Get current connection status information"""
    global _db_connection, _last_connection_check
    
    with _db_lock:
        is_healthy = _is_connection_healthy(_db_connection)
        status = {
            'connected': _db_connection is not None and is_healthy,
            'healthy': is_healthy,
            'last_check': _last_connection_check,
            'check_interval': _connection_check_interval
        }
        
        return status