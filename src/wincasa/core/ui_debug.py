#!/usr/bin/env python3
"""
WINCASA UI Debug Module
Extensive debugging and diagnostics for UI issues
"""

import logging
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st

logger = logging.getLogger(__name__)

class UIDebugger:
    """Comprehensive UI debugging and issue tracking"""
    
    def __init__(self):
        self.debug_logs = []
        self.interaction_count = 0
        self.error_count = 0
        self.performance_metrics = {}
        
    def log_interaction(self, event_type: str, details: Dict[str, Any]):
        """Log UI interactions for debugging"""
        self.interaction_count += 1
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'interaction_id': self.interaction_count,
            'event_type': event_type,
            'details': details,
            'session_id': getattr(st.session_state, 'session_id', 'unknown'),
            'user_id': getattr(st.session_state, 'user_id', 'unknown')
        }
        
        self.debug_logs.append(log_entry)
        logger.info(f"UI_DEBUG: {event_type} - {details}")
        
        # Keep only last 100 entries
        if len(self.debug_logs) > 100:
            self.debug_logs = self.debug_logs[-100:]
    
    def log_error(self, error_type: str, error_msg: str, context: Dict[str, Any] = None):
        """Log UI errors with context"""
        self.error_count += 1
        
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_id': self.error_count,
            'error_type': error_type,
            'error_msg': error_msg,
            'context': context or {},
            'traceback': traceback.format_exc(),
            'session_id': getattr(st.session_state, 'session_id', 'unknown')
        }
        
        self.debug_logs.append(error_entry)
        logger.error(f"UI_ERROR: {error_type} - {error_msg} | Context: {context}")
    
    def measure_performance(self, operation_name: str):
        """Context manager for performance measurement"""
        return PerformanceMeasurer(self, operation_name)
    
    def log_button_state(self, button_name: str, button_key: str, clicked: bool):
        """Track button states and clicks"""
        self.log_interaction('button_interaction', {
            'button_name': button_name,
            'button_key': button_key,
            'clicked': clicked,
            'timestamp': time.time()
        })
    
    def log_session_state_change(self, key: str, old_value: Any, new_value: Any):
        """Track session state changes"""
        self.log_interaction('session_state_change', {
            'key': key,
            'old_value': str(old_value)[:100],  # Truncate long values
            'new_value': str(new_value)[:100],
            'value_type': type(new_value).__name__
        })
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """Get summary of debug information"""
        recent_logs = self.debug_logs[-20:] if self.debug_logs else []
        
        return {
            'total_interactions': self.interaction_count,
            'total_errors': self.error_count,
            'recent_logs': recent_logs,
            'performance_metrics': self.performance_metrics,
            'session_info': {
                'session_id': getattr(st.session_state, 'session_id', 'unknown'),
                'user_id': getattr(st.session_state, 'user_id', 'unknown'),
                'initialized': getattr(st.session_state, '_wincasa_initialized', False)
            }
        }
    
    def render_debug_panel(self):
        """Render debug panel in Streamlit"""
        if not st.session_state.get('debug_mode', False):
            return
            
        with st.expander("🔧 UI Debug Panel", expanded=False):
            summary = self.get_debug_summary()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Interactions", summary['total_interactions'])
                st.metric("Total Errors", summary['total_errors'])
            
            with col2:
                st.metric("Session ID", summary['session_info']['session_id'])
                st.metric("Initialized", summary['session_info']['initialized'])
            
            with col3:
                if summary['performance_metrics']:
                    avg_time = sum(summary['performance_metrics'].values()) / len(summary['performance_metrics'])
                    st.metric("Avg Response Time", f"{avg_time:.2f}ms")
            
            # Recent logs
            if summary['recent_logs']:
                st.subheader("Recent Activity")
                for log in summary['recent_logs'][-5:]:
                    event_type = log.get('event_type', log.get('error_type', 'unknown'))
                    timestamp = log['timestamp'][-8:-3]  # HH:MM format
                    
                    if 'error_type' in log:
                        st.error(f"🔴 {timestamp} | {event_type}: {log.get('error_msg', '')}")
                    else:
                        st.info(f"🔵 {timestamp} | {event_type}: {log.get('details', {})}")

class PerformanceMeasurer:
    """Context manager for measuring operation performance"""
    
    def __init__(self, debugger: UIDebugger, operation_name: str):
        self.debugger = debugger
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.debugger.performance_metrics[self.operation_name] = duration_ms
            
            self.debugger.log_interaction('performance_measurement', {
                'operation': self.operation_name,
                'duration_ms': round(duration_ms, 2),
                'success': exc_type is None
            })
            
            if exc_type:
                self.debugger.log_error('performance_error', 
                                      f"Operation {self.operation_name} failed", 
                                      {'duration_ms': duration_ms, 'exception': str(exc_val)})

# Global debugger instance
ui_debugger = UIDebugger()

def debug_button_click(button_name: str, button_key: str, clicked: bool):
    """Convenience function for button debugging"""
    ui_debugger.log_button_state(button_name, button_key, clicked)

def debug_session_change(key: str, old_value: Any, new_value: Any):
    """Convenience function for session state debugging"""
    ui_debugger.log_session_state_change(key, old_value, new_value)

def debug_error(error_type: str, error_msg: str, context: Dict[str, Any] = None):
    """Convenience function for error logging"""
    ui_debugger.log_error(error_type, error_msg, context)

def debug_interaction(event_type: str, details: Dict[str, Any]):
    """Convenience function for general interaction logging"""
    ui_debugger.log_interaction(event_type, details)

def measure_performance(operation_name: str):
    """Convenience function for performance measurement"""
    return ui_debugger.measure_performance(operation_name)

def render_debug_panel():
    """Convenience function to render debug panel"""
    ui_debugger.render_debug_panel()