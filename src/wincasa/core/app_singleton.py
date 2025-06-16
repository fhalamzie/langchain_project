#!/usr/bin/env python3
"""
WINCASA App Singleton
Global singleton instance to prevent re-initialization issues
"""

import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global variables for singleton pattern
_app_instance: Optional['WincasaStreamlitApp'] = None
_query_engine_instance: Optional['WincasaQueryEngine'] = None
_lock = threading.Lock()

def get_wincasa_app():
    """
    Returns a thread-safe, globally unique instance of WincasaStreamlitApp.
    Initialization is guaranteed to happen only once per process.
    
    This completely bypasses Streamlit's caching issues and ensures
    true singleton behavior across all sessions.
    """
    global _app_instance
    
    # Double-checked locking for performance
    if _app_instance is None:
        with _lock:
            if _app_instance is None:
                logger.info("🚀 Creating SINGLETON WincasaStreamlitApp instance...")
                
                # Import here to avoid circular imports
                from wincasa.core.streamlit_app import WincasaStreamlitApp
                
                _app_instance = WincasaStreamlitApp()
                logger.info("✅ SINGLETON WincasaStreamlitApp created successfully")
    
    return _app_instance

def get_query_engine():
    """
    Returns a thread-safe, globally unique instance of WincasaQueryEngine.
    This prevents the heavy re-initialization that was happening in lazy loading.
    """
    global _query_engine_instance
    
    if _query_engine_instance is None:
        with _lock:
            if _query_engine_instance is None:
                logger.info("🚀 Creating SINGLETON WincasaQueryEngine instance...")
                
                # Import here to avoid circular imports
                from wincasa.core.wincasa_query_engine import WincasaQueryEngine
                
                _query_engine_instance = WincasaQueryEngine(debug_mode=False)
                logger.info("✅ SINGLETON WincasaQueryEngine created successfully")
    else:
        logger.debug("🎯 Returning existing SINGLETON WincasaQueryEngine instance")
    
    return _query_engine_instance

def reset_singleton():
    """Reset singleton for testing purposes only"""
    global _app_instance, _query_engine_instance
    with _lock:
        _app_instance = None
        _query_engine_instance = None
        logger.info("🔄 Singleton reset")