#!/usr/bin/env python3
"""
Simple SQL Validator for Firebird dialect

A lightweight SQL validator that doesn't require external dependencies
like sqlglot. Provides basic SQL validation and Firebird-specific fixes.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ValidationResult:
    """Result of SQL validation process"""
    valid: bool
    original_sql: str
    fixed_sql: Optional[str] = None
    issues: List[str] = None
    suggestions: List[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.suggestions is None:
            self.suggestions = []


class SimpleSQLValidator:
    """
    Simple SQL validator for Firebird SQL with basic syntax checking
    and common error corrections.
    """
    
    def __init__(self):
        # Common Firebird SQL patterns and fixes
        self.firebird_fixes = [
            # MySQL LIMIT to Firebird FIRST
            (r'\bLIMIT\s+(\d+)\b', r'FIRST \1'),
            # Standard quote handling
            (r'`([^`]+)`', r'"\1"'),
            # Date format fixes
            (r"'(\d{4}-\d{2}-\d{2})'", r"DATE '\1'"),
        ]
        
        # Basic SQL structure validation patterns
        self.basic_patterns = {
            'select': r'\bSELECT\b',
            'from': r'\bFROM\b',
            'where': r'\bWHERE\b',
            'join': r'\b(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN\b',
            'group_by': r'\bGROUP\s+BY\b',
            'order_by': r'\bORDER\s+BY\b',
            'having': r'\bHAVING\b'
        }
        
        # Table names that should exist (for basic validation)
        self.known_tables = {
            'BEWOHNER', 'EIGENTUEMER', 'OBJEKTE', 'WOHNUNG', 
            'KONTEN', 'BUCHUNG', 'BEWADR', 'EIGADR', 'VEREIG', 'SOLLSTELLUNG'
        }
    
    def validate_and_fix(self, sql: str, available_tables: List[str] = None) -> ValidationResult:
        """
        Validate SQL and apply basic Firebird fixes.
        
        Args:
            sql: SQL query to validate
            available_tables: List of available table names
            
        Returns:
            ValidationResult with validation status and fixes
        """
        if not sql or not sql.strip():
            return ValidationResult(
                valid=False,
                original_sql=sql,
                error="Empty SQL query"
            )
        
        original_sql = sql.strip()
        fixed_sql = original_sql
        issues = []
        suggestions = []
        
        try:
            # Apply Firebird-specific fixes
            for pattern, replacement in self.firebird_fixes:
                new_sql = re.sub(pattern, replacement, fixed_sql, flags=re.IGNORECASE)
                if new_sql != fixed_sql:
                    issues.append(f"Applied Firebird fix: {pattern} -> {replacement}")
                    fixed_sql = new_sql
            
            # Basic structure validation
            valid = self._validate_basic_structure(fixed_sql)
            
            if not valid:
                issues.append("Invalid basic SQL structure")
            
            # Table existence check
            table_issues = self._validate_table_names(fixed_sql, available_tables)
            issues.extend(table_issues)
            
            # Add suggestions for improvements
            suggestions.extend(self._generate_suggestions(fixed_sql))
            
            return ValidationResult(
                valid=valid and len(table_issues) == 0,
                original_sql=original_sql,
                fixed_sql=fixed_sql if fixed_sql != original_sql else None,
                issues=issues,
                suggestions=suggestions
            )
            
        except Exception as e:
            return ValidationResult(
                valid=False,
                original_sql=original_sql,
                error=f"Validation error: {str(e)}"
            )
    
    def _validate_basic_structure(self, sql: str) -> bool:
        """Validate basic SQL structure"""
        sql_upper = sql.upper()
        
        # Must have SELECT
        if not re.search(self.basic_patterns['select'], sql_upper):
            return False
        
        # Must have FROM (unless it's a simple expression)
        if 'COUNT(' not in sql_upper and not re.search(self.basic_patterns['from'], sql_upper):
            return False
        
        # Check for balanced parentheses
        open_count = sql.count('(')
        close_count = sql.count(')')
        if open_count != close_count:
            return False
        
        return True
    
    def _validate_table_names(self, sql: str, available_tables: List[str] = None) -> List[str]:
        """Validate that referenced tables exist"""
        issues = []
        
        # Use provided tables or fall back to known tables
        valid_tables = set(available_tables) if available_tables else self.known_tables
        
        # Extract table names from FROM and JOIN clauses
        table_pattern = r'\b(?:FROM|JOIN)\s+([A-Z_][A-Z0-9_]*)\b'
        found_tables = re.findall(table_pattern, sql.upper())
        
        for table in found_tables:
            if table not in valid_tables:
                issues.append(f"Unknown table referenced: {table}")
        
        return issues
    
    def _generate_suggestions(self, sql: str) -> List[str]:
        """Generate suggestions for SQL improvement"""
        suggestions = []
        sql_upper = sql.upper()
        
        # Suggest using LIKE for string matching
        if 'WHERE' in sql_upper and '=' in sql_upper and ('BSTR' in sql_upper or 'BPLZORT' in sql_upper):
            suggestions.append("Consider using LIKE patterns for address fields (BSTR, BPLZORT)")
        
        # Suggest proper date handling
        if any(year in sql for year in ['2023', '2024', '2025']):
            suggestions.append("Consider using proper DATE format for date comparisons")
        
        # Suggest indexes for large tables
        if 'FROM BEWOHNER' in sql_upper and 'WHERE' not in sql_upper:
            suggestions.append("Consider adding WHERE clause to limit results from large tables")
        
        return suggestions
    
    def validate_syntax_only(self, sql: str) -> bool:
        """Quick syntax-only validation"""
        try:
            # Very basic syntax checks
            sql = sql.strip()
            if not sql:
                return False
            
            # Check for basic SQL keywords
            sql_upper = sql.upper()
            if not sql_upper.startswith('SELECT'):
                return False
            
            # Check balanced quotes
            single_quotes = sql.count("'")
            double_quotes = sql.count('"')
            
            if single_quotes % 2 != 0 or double_quotes % 2 != 0:
                return False
            
            return True
            
        except Exception:
            return False


def test_simple_sql_validator():
    """Test the simple SQL validator"""
    print("🧪 Testing Simple SQL Validator")
    print("=" * 50)
    
    validator = SimpleSQLValidator()
    
    test_cases = [
        # Valid SQL
        "SELECT COUNT(*) FROM WOHNUNG",
        "SELECT BNAME, BVNAME FROM BEWOHNER WHERE BSTR LIKE '%Marien%'",
        
        # SQL needing Firebird fixes
        "SELECT * FROM BEWOHNER LIMIT 10",
        "SELECT * FROM BEWOHNER WHERE BDATUM = '2023-01-01'",
        
        # Invalid SQL
        "",
        "INVALID SQL QUERY",
        "SELECT * FROM",
        "SELECT * FROM UNKNOWN_TABLE",
    ]
    
    for i, sql in enumerate(test_cases, 1):
        print(f"{i}. SQL: {sql}")
        result = validator.validate_and_fix(sql)
        print(f"   Valid: {result.valid}")
        if result.fixed_sql:
            print(f"   Fixed: {result.fixed_sql}")
        if result.issues:
            print(f"   Issues: {result.issues}")
        if result.suggestions:
            print(f"   Suggestions: {result.suggestions}")
        if result.error:
            print(f"   Error: {result.error}")
        print()
    
    print("✅ Simple SQL Validator test completed")


if __name__ == "__main__":
    test_simple_sql_validator()