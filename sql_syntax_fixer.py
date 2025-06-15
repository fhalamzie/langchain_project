#!/usr/bin/env python3
"""
SQL Syntax Fixer for Firebird
Fixes common SQL generation errors before execution
"""

import re
import logging

# Removed: hardcoded column mapper - let LLM decide columns based on schema

logger = logging.getLogger(__name__)


class FirebirdSQLFixer:
    """Fixes common SQL syntax errors for Firebird database."""
    
    @staticmethod
    def fix_join_syntax(sql: str) -> str:
        """Fix common JOIN syntax errors.
        
        Patterns fixed:
        - 'JOIN table ON AS alias' -> 'JOIN table AS alias'
        - 'JOIN table ON alias ON' -> 'JOIN table alias ON'
        - 'FROM table AS t1 JOIN table ON AS t2' -> 'FROM table AS t1 JOIN table AS t2'
        """
        # Fix "JOIN table ON alias ON" pattern (common LLM error)
        sql = re.sub(r'\bJOIN\s+(\w+)\s+ON\s+(\w+)\s+ON\b', r'JOIN \1 \2 ON', sql, flags=re.IGNORECASE)
        
        # Fix "ON AS" pattern
        sql = re.sub(r'\bON\s+AS\s+(\w+)\s+ON\b', r'AS \1 ON', sql, flags=re.IGNORECASE)
        
        # Fix "JOIN table ON AS"
        sql = re.sub(r'\bJOIN\s+(\w+)\s+ON\s+AS\s+(\w+)', r'JOIN \1 AS \2', sql, flags=re.IGNORECASE)
        
        return sql
    
    @staticmethod
    def fix_column_names(sql: str) -> str:
        """Minimal column fixes - let LLM learn correct column names from schema."""
        # Only fix obvious syntax errors, not column name mappings
        return sql
    
    @staticmethod
    def fix_limit_syntax(sql: str) -> str:
        """Convert LIMIT to Firebird's FIRST syntax."""
        # Convert "LIMIT n" to "FIRST n"
        limit_match = re.search(r'\bLIMIT\s+(\d+)\b', sql, re.IGNORECASE)
        if limit_match:
            limit_num = limit_match.group(1)
            # Remove LIMIT from end
            sql = re.sub(r'\s*LIMIT\s+\d+\s*;?\s*$', '', sql, flags=re.IGNORECASE)
            # Add FIRST after SELECT
            sql = re.sub(r'\bSELECT\b', f'SELECT FIRST {limit_num}', sql, flags=re.IGNORECASE)
        
        return sql
    
    @staticmethod
    def ensure_semicolon(sql: str) -> str:
        """Ensure SQL ends with semicolon."""
        sql = sql.strip()
        if not sql.endswith(';'):
            sql += ';'
        return sql
    
    @classmethod
    def fix_sql(cls, sql: str) -> str:
        """Apply all fixes to SQL query."""
        if not sql:
            return sql
            
        original = sql
        
        # Apply minimal fixes - no hardcoded column mapping
        sql = cls.fix_join_syntax(sql)
        sql = cls.fix_limit_syntax(sql)
        sql = cls.ensure_semicolon(sql)
        
        if sql != original:
            logger.debug(f"Fixed SQL: {original} -> {sql}")  # Changed to debug level to reduce log clutter
            
        return sql


# Example usage and tests
if __name__ == "__main__":
    test_cases = [
        # JOIN syntax errors
        "SELECT t1.* FROM EIGADR AS t1 INNER JOIN EIGENTUEMER ON AS t2 ON t1.EIGNR = t2.EIGNR",
        "SELECT * FROM BEWOHNER AS T1 JOIN OBJEKTE ON AS T2 ON T1.ONR = T2.ONR",
        
        # LIMIT syntax
        "SELECT * FROM BEWOHNER LIMIT 10",
        
        # Missing semicolon
        "SELECT COUNT(*) FROM WOHNUNG"
    ]
    
    fixer = FirebirdSQLFixer()
    
    print("🔧 Firebird SQL Syntax Fixer Tests")
    print("=" * 60)
    
    for i, test_sql in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Original: {test_sql}")
        fixed = fixer.fix_sql(test_sql)
        print(f"Fixed:    {fixed}")
        
    print("\n✅ SQL Fixer ready for integration")