#!/usr/bin/env python3
"""
SQL Validation Layer using sqlglot for Firebird dialect

Purpose: Validate and automatically fix SQL syntax for Firebird,
ensuring compliance with Firebird-specific requirements.

NOTE: This complements the existing YAML knowledge base, not replaces it.
YAMLs contain critical detailed information for complex queries.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, NamedTuple, Optional

import sqlglot
from sqlglot import parse_one, transpile


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


class SQLValidator:
    """
    SQL validation and automatic fixing for Firebird dialect

    Purpose: Complement existing YAML knowledge with syntax validation

    Key Features:
    - Parse SQL with sqlglot for Firebird dialect
    - Validate table names against database schema
    - Check Firebird-specific syntax compliance
    - Automatic syntax fixing (LIMIT → FIRST, etc.)
    """

    # Core WINCASA tables - basic validation set
    KNOWN_TABLES = {
        "BEWOHNER": ["BWO", "BNAME", "BVNAME", "BSTR", "BPLZORT"],
        "EIGENTUEMER": ["ENR", "ENAME", "EVNAME"],
        "WOHNUNG": ["WNR", "ONR", "WBEZEICHNUNG"],
        "OBJEKTE": ["ONR", "OBEZEICHNUNG", "OSTR", "OPLZORT"],
        "KONTEN": ["KNR", "ONR", "KBEZEICHNUNG"],
        "BUCHUNG": ["BKNR", "KNR", "BBETRAG", "BDATUM"],
        "VEREIG": ["ENR", "ONR"],
        "BEWADR": ["BWO", "BSTR", "BPLZORT"],
        "EIGADR": ["ENR", "ESTR", "EPLZORT"],
    }

    # Firebird-specific syntax rules
    FIREBIRD_RULES = {
        "limit_syntax": {
            "pattern": r"\bLIMIT\s+(\d+)\b",
            "replacement": r"FIRST \1",
            "description": "Convert LIMIT to FIRST for Firebird",
        },
        "offset_syntax": {
            "pattern": r"\bOFFSET\s+(\d+)\b",
            "replacement": r"SKIP \1",
            "description": "Convert OFFSET to SKIP for Firebird",
        },
    }

    def __init__(self, available_tables: Optional[List[str]] = None):
        """Initialize validator with known tables"""
        self.available_tables = available_tables or list(self.KNOWN_TABLES.keys())

    def validate_and_fix(self, sql: str) -> ValidationResult:
        """
        Main validation method - validates SQL and applies automatic fixes
        """

        if not sql or not sql.strip():
            return ValidationResult(
                valid=False, original_sql=sql, error="Empty SQL query"
            )

        original_sql = sql.strip()
        fixed_sql = original_sql
        issues = []
        suggestions = []

        try:
            # Step 1: Apply Firebird-specific syntax fixes
            fixed_sql, syntax_issues = self._apply_firebird_syntax_fixes(fixed_sql)
            issues.extend(syntax_issues)

            # Step 2: Parse SQL with sqlglot
            try:
                parsed = parse_one(fixed_sql, dialect="firebird")
            except Exception as parse_error:
                # Try standard SQL if Firebird parsing fails
                try:
                    parsed = parse_one(fixed_sql)
                    issues.append("Parsed as standard SQL (Firebird dialect failed)")
                except Exception:
                    return ValidationResult(
                        valid=False,
                        original_sql=original_sql,
                        fixed_sql=fixed_sql,
                        issues=issues,
                        error=f"SQL parsing failed: {parse_error}",
                    )

            # Step 3: Validate table names
            table_issues = self._validate_tables(parsed)
            issues.extend(table_issues)

            # Step 4: Validate basic SQL structure
            structure_issues = self._validate_sql_structure(fixed_sql)
            issues.extend(structure_issues)

            # Step 5: Generate suggestions
            suggestions = self._generate_suggestions(issues, fixed_sql)

            # Determine if valid (only critical errors make it invalid)
            critical_issues = [
                issue for issue in issues if "does not exist" in issue.lower()
            ]
            is_valid = len(critical_issues) == 0

            return ValidationResult(
                valid=is_valid,
                original_sql=original_sql,
                fixed_sql=fixed_sql if fixed_sql != original_sql else None,
                issues=issues,
                suggestions=suggestions,
            )

        except Exception as e:
            return ValidationResult(
                valid=False,
                original_sql=original_sql,
                error=f"Validation error: {str(e)}",
            )

    def _apply_firebird_syntax_fixes(self, sql: str) -> tuple[str, List[str]]:
        """Apply Firebird-specific syntax corrections"""

        fixed_sql = sql
        issues = []

        for rule_name, rule in self.FIREBIRD_RULES.items():
            pattern = rule["pattern"]
            replacement = rule["replacement"]
            description = rule["description"]

            if re.search(pattern, fixed_sql, re.IGNORECASE):
                fixed_sql = re.sub(pattern, replacement, fixed_sql, flags=re.IGNORECASE)
                issues.append(f"Fixed: {description}")

        return fixed_sql, issues

    def _validate_tables(self, parsed_sql) -> List[str]:
        """Validate that all referenced tables exist"""

        issues = []

        # Extract table names from parsed SQL
        tables = self._extract_table_names(parsed_sql)

        for table in tables:
            table_upper = table.upper()
            if table_upper not in [t.upper() for t in self.available_tables]:
                issues.append(f"Table '{table}' not found")
                # Suggest similar table names
                similar = self._find_similar_table_names(table_upper)
                if similar:
                    issues.append(f"  → Suggestions: {', '.join(similar)}")

        return issues

    def _extract_table_names(self, parsed_sql) -> List[str]:
        """Extract table names from SQL"""

        tables = []
        sql_str = str(parsed_sql).upper()

        # Simple regex extraction for common patterns
        patterns = [
            r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"\bUPDATE\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"\bINSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sql_str, re.IGNORECASE)
            tables.extend(matches)

        return list(set(tables))

    def _validate_sql_structure(self, sql: str) -> List[str]:
        """Validate basic SQL structure"""

        issues = []
        sql_upper = sql.upper()

        # Check for valid SQL statement type
        valid_starts = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        if not any(sql_upper.strip().startswith(start) for start in valid_starts):
            issues.append("SQL does not start with valid statement type")

        # Check for balanced parentheses
        if sql.count("(") != sql.count(")"):
            issues.append("Unbalanced parentheses")

        return issues

    def _find_similar_table_names(self, table_name: str) -> List[str]:
        """Find similar table names"""

        similar = []
        table_lower = table_name.lower()

        for known_table in self.available_tables:
            known_lower = known_table.lower()

            if table_lower in known_lower or known_lower in table_lower:
                similar.append(known_table)

        return similar[:3]

    def _generate_suggestions(self, issues: List[str], sql: str) -> List[str]:
        """Generate helpful suggestions"""

        suggestions = []

        if any("not found" in issue for issue in issues):
            suggestions.append("Check table names against database schema")

        if any("LIMIT" in issue for issue in issues):
            suggestions.append("Use FIRST instead of LIMIT for Firebird")

        return suggestions


def test_sql_validator():
    """Test the SQL validator with various queries"""

    validator = SQLValidator()

    test_cases = [
        "SELECT BNAME FROM BEWOHNER WHERE BSTR LIKE '%Marienstraße%'",
        "SELECT * FROM WOHNUNG LIMIT 10",
        "SELECT COUNT(*) FROM WOHNUNG",
        "SELECT * FROM NONEXISTENT_TABLE",
    ]

    print("🔍 TESTING SQL VALIDATION LAYER")
    print("=" * 50)

    for i, sql in enumerate(test_cases, 1):
        print(f"\nTest {i}: {sql}")
        result = validator.validate_and_fix(sql)

        status = "✅ VALID" if result.valid else "❌ INVALID"
        print(f"  Status: {status}")

        if result.fixed_sql:
            print(f"  Fixed: {result.fixed_sql}")

        if result.issues:
            print(f"  Issues: {'; '.join(result.issues)}")


if __name__ == "__main__":
    test_sql_validator()
