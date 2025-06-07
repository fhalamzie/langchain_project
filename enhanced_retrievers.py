#!/usr/bin/env python3
"""
Enhanced Retrievers Module - Legacy compatibility import
Provides the EnhancedRetriever class for backward compatibility.
"""

from contextual_enhanced_retriever import ContextualEnhancedRetriever

# Alias for backward compatibility
EnhancedRetriever = ContextualEnhancedRetriever

# Export for import compatibility
__all__ = ['EnhancedRetriever', 'ContextualEnhancedRetriever']