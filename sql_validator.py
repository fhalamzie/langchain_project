"""
SQLGlot Validation Framework for Firebird SQL
Implements Task 1.3 from the roadmap - SQL syntax validation and automatic fixing.

This module provides comprehensive SQL validation, syntax correction, and 
Firebird-specific dialect handling using SQLGlot parsing technology.
"""

import re
from typing import Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import sqlglot
    from sqlglot import parse_one, transpile, ParseError
    from sqlglot.dialects import Dialect
    from sqlglot.expressions import Expression
    SQLGLOT_AVAILABLE = True
except ImportError:
    print("⚠️ SQLGlot not available. SQL validation will be limited.")
    SQLGLOT_AVAILABLE = False
    sqlglot = None
    parse_one = None
    transpile = None
    ParseError = None
    Dialect = None
    Expression = None

# Import database interface for schema validation
try:
    from fdb_direct_interface import FDBDirectInterface
except ImportError:
    print("⚠️ FDB Direct Interface not available for schema validation.")
    FDBDirectInterface = None


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class ValidationIssue:
    """Represents a SQL validation issue."""
    severity: ValidationSeverity
    code: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ValidationResult:
    """Result of SQL validation process."""
    original_sql: str
    is_valid: bool
    issues: List[ValidationIssue]
    fixed_sql: Optional[str] = None
    parse_tree: Optional[Expression] = None
    dialect_used: str = "firebird"
    
    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues.""" 
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]


class FirebirdSQLValidator:
    """
    Comprehensive SQL validator for Firebird dialect with automatic fixing capabilities.
    
    Uses SQLGlot for parsing and syntax validation, with additional Firebird-specific
    checks and automatic corrections for common issues.
    """
    
    def __init__(self, db_interface: Optional[FDBDirectInterface] = None):
        """
        Initialize the Firebird SQL validator.
        
        Args:
            db_interface: Optional database interface for schema validation
        """
        self.db_interface = db_interface
        self.known_tables: Set[str] = set()
        self.table_columns: Dict[str, Set[str]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Firebird-specific keywords and functions
        self.firebird_keywords = {
            'FIRST', 'SKIP', 'ROWS', 'RDB$', 'MON$', 'CURRENT_DATE', 'CURRENT_TIME',
            'CURRENT_TIMESTAMP', 'CURRENT_USER', 'CURRENT_ROLE', 'CURRENT_CONNECTION',
            'CURRENT_TRANSACTION', 'CHAR_LENGTH', 'CHARACTER_LENGTH', 'BIT_LENGTH',
            'OCTET_LENGTH', 'POSITION', 'SUBSTRING', 'UPPER', 'LOWER', 'TRIM',
            'EXTRACT', 'CAST', 'COALESCE', 'NULLIF', 'IIF', 'DECODE'
        }
        
        # Common SQL to Firebird transformations
        self.firebird_transforms = {
            'LIMIT': 'FIRST',
            'OFFSET': 'SKIP',
            'TOP': 'FIRST',
            'LENGTH': 'CHAR_LENGTH',
            'LEN': 'CHAR_LENGTH',
            'ISNULL': 'COALESCE',
            'IFNULL': 'COALESCE',
            'NVL': 'COALESCE'
        }
        
        # Pre-load schema if database interface is available
        if self.db_interface:
            self._load_schema_metadata()
    
    def _load_schema_metadata(self) -> None:
        """Load schema metadata from the database for validation."""
        try:
            if self.db_interface:
                # Get table names
                tables = self.db_interface.get_table_names()
                self.known_tables = set(table.upper() for table in tables)
                
                # Get column information for key tables
                priority_tables = ['BEWOHNER', 'OBJEKTE', 'EIGENTUEMER', 'KONTEN', 'WOHNUNG']
                for table in priority_tables:
                    if table in self.known_tables:
                        table_info = self.db_interface.get_table_info([table])
                        # Parse column names from table info
                        columns = self._parse_columns_from_table_info(table_info)
                        self.table_columns[table] = columns
                
                self.logger.info(f"Loaded schema: {len(self.known_tables)} tables, "
                               f"{len(self.table_columns)} with column info")
        
        except Exception as e:
            self.logger.warning(f"Failed to load schema metadata: {e}")
    
    def _parse_columns_from_table_info(self, table_info: str) -> Set[str]:
        """Parse column names from table info string."""
        columns = set()
        lines = table_info.split('\n')
        
        for line in lines:
            # Look for column definitions (lines starting with "  - ")
            if line.strip().startswith('- '):
                # Extract column name (before the colon)
                parts = line.split(':')
                if len(parts) >= 2:
                    column_name = parts[0].replace('- ', '').strip()
                    columns.add(column_name.upper())
        
        return columns
    
    def validate_sql(self, sql: str) -> ValidationResult:
        """
        Validate SQL syntax and apply Firebird-specific checks.
        
        Args:
            sql: SQL statement to validate
            
        Returns:
            ValidationResult with issues and potential fixes
        """
        issues = []
        fixed_sql = sql
        parse_tree = None
        
        # Basic input validation
        if not sql or not sql.strip():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="EMPTY_SQL",
                message="SQL statement is empty",
                auto_fixable=False
            ))
            return ValidationResult(
                original_sql=sql,
                is_valid=False,
                issues=issues,
                fixed_sql=None
            )
        
        # Firebird-specific pre-validation fixes
        fixed_sql, pre_issues = self._apply_firebird_pre_fixes(sql)
        issues.extend(pre_issues)
        
        # SQLGlot parsing validation
        if SQLGLOT_AVAILABLE:
            parse_result = self._validate_with_sqlglot(fixed_sql)
            issues.extend(parse_result["issues"])
            if parse_result["parse_tree"]:
                parse_tree = parse_result["parse_tree"]
                fixed_sql = parse_result.get("fixed_sql", fixed_sql)
        
        # Firebird-specific validations
        firebird_issues = self._validate_firebird_specifics(fixed_sql)
        issues.extend(firebird_issues)
        
        # Schema validation (if database interface available)
        if self.db_interface and self.known_tables:
            schema_issues = self._validate_against_schema(fixed_sql)
            issues.extend(schema_issues)
        
        # Security validation
        security_issues = self._validate_security(fixed_sql)
        issues.extend(security_issues)
        
        # Determine if SQL is valid (no errors)
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(
            original_sql=sql,
            is_valid=is_valid,
            issues=issues,
            fixed_sql=fixed_sql if fixed_sql != sql else None,
            parse_tree=parse_tree,
            dialect_used="firebird"
        )
    
    def _apply_firebird_pre_fixes(self, sql: str) -> Tuple[str, List[ValidationIssue]]:
        """Apply common Firebird-specific fixes before parsing."""
        issues = []
        fixed_sql = sql
        
        # LIMIT to FIRST conversion
        limit_pattern = r'\\bLIMIT\\s+(\\d+)\\b'
        limit_matches = list(re.finditer(limit_pattern, fixed_sql, re.IGNORECASE))
        if limit_matches:
            for match in reversed(limit_matches):  # Process from end to maintain positions
                limit_value = match.group(1)
                # Replace LIMIT with FIRST at the beginning of SELECT
                select_pattern = r'\\bSELECT\\b'
                fixed_sql = re.sub(
                    select_pattern,
                    f'SELECT FIRST {limit_value}',
                    fixed_sql,
                    count=1,
                    flags=re.IGNORECASE
                )
                # Remove the LIMIT clause
                fixed_sql = fixed_sql[:match.start()] + fixed_sql[match.end():]
                
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    code="LIMIT_TO_FIRST",
                    message=f"Converted LIMIT {limit_value} to FIRST {limit_value} for Firebird compatibility",
                    suggestion=f"Use FIRST {limit_value} instead of LIMIT {limit_value}",
                    auto_fixable=True
                ))
        
        # OFFSET to SKIP conversion (after FIRST)
        offset_pattern = r'\\bOFFSET\\s+(\\d+)\\b'
        offset_matches = list(re.finditer(offset_pattern, fixed_sql, re.IGNORECASE))
        if offset_matches:
            for match in reversed(offset_matches):
                offset_value = match.group(1)
                # Add SKIP after FIRST
                first_pattern = r'\\bFIRST\\s+(\\d+)\\b'
                if re.search(first_pattern, fixed_sql, re.IGNORECASE):
                    fixed_sql = re.sub(
                        first_pattern,
                        f'FIRST \\\\1 SKIP {offset_value}',
                        fixed_sql,
                        flags=re.IGNORECASE
                    )
                else:
                    # Add SKIP without FIRST (less common)
                    fixed_sql = re.sub(
                        r'\\bSELECT\\b',
                        f'SELECT SKIP {offset_value}',
                        fixed_sql,
                        count=1,
                        flags=re.IGNORECASE
                    )
                
                # Remove OFFSET clause
                fixed_sql = fixed_sql[:match.start()] + fixed_sql[match.end():]
                
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    code="OFFSET_TO_SKIP",
                    message=f"Converted OFFSET {offset_value} to SKIP {offset_value} for Firebird compatibility",
                    suggestion=f"Use SKIP {offset_value} instead of OFFSET {offset_value}",
                    auto_fixable=True
                ))
        
        # Function name transformations
        for std_func, fb_func in self.firebird_transforms.items():
            if std_func.upper() in ['LENGTH', 'LEN', 'ISNULL', 'IFNULL', 'NVL']:
                pattern = rf'\\b{re.escape(std_func)}\\b'
                if re.search(pattern, fixed_sql, re.IGNORECASE):
                    fixed_sql = re.sub(pattern, fb_func, fixed_sql, flags=re.IGNORECASE)
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        code="FUNCTION_CONVERSION",
                        message=f"Converted {std_func} to {fb_func} for Firebird compatibility",
                        suggestion=f"Use {fb_func} instead of {std_func}",
                        auto_fixable=True
                    ))
        
        return fixed_sql, issues
    
    def _validate_with_sqlglot(self, sql: str) -> Dict:
        """Validate SQL using SQLGlot parser."""
        result = {
            "issues": [],
            "parse_tree": None,
            "fixed_sql": sql
        }
        
        try:
            # Try parsing with Firebird dialect
            parse_tree = parse_one(sql, dialect="firebird", read="firebird")
            result["parse_tree"] = parse_tree
            
            # Check for common syntax issues
            if parse_tree:
                syntax_issues = self._analyze_parse_tree(parse_tree)
                result["issues"].extend(syntax_issues)
        
        except ParseError as e:
            result["issues"].append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="PARSE_ERROR",
                message=f"SQL parsing failed: {str(e)}",
                auto_fixable=False
            ))
            
            # Try to suggest fixes for common parse errors
            suggestion = self._suggest_parse_fix(sql, str(e))
            if suggestion:
                result["issues"][-1].suggestion = suggestion
        
        except Exception as e:
            result["issues"].append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="VALIDATION_ERROR",
                message=f"Validation process error: {str(e)}",
                auto_fixable=False
            ))
        
        return result
    
    def _analyze_parse_tree(self, parse_tree: Expression) -> List[ValidationIssue]:
        """Analyze the parsed SQL tree for potential issues."""
        issues = []
        
        # Check for SELECT without FROM (should be rare in real queries)
        if hasattr(parse_tree, 'find') and parse_tree.find(sqlglot.expressions.Select):
            select_nodes = parse_tree.find_all(sqlglot.expressions.Select)
            for select in select_nodes:
                if not select.find(sqlglot.expressions.From):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        code="SELECT_WITHOUT_FROM",
                        message="SELECT statement without FROM clause",
                        suggestion="Add FROM clause or use SELECT from system tables"
                    ))
        
        # Check for potential performance issues
        issues.extend(self._check_performance_issues(parse_tree))
        
        return issues
    
    def _check_performance_issues(self, parse_tree: Expression) -> List[ValidationIssue]:
        """Check for potential performance issues in the query."""
        issues = []
        
        # Look for SELECT * which might be inefficient
        if "SELECT *" in str(parse_tree).upper():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.SUGGESTION,
                code="SELECT_STAR",
                message="Using SELECT * may impact performance",
                suggestion="Consider selecting only required columns",
                auto_fixable=False
            ))
        
        # Look for missing WHERE clauses on large tables
        large_tables = {'BEWOHNER', 'KONTEN', 'BUCHUNG', 'SOLLSTELLUNG'}
        if hasattr(parse_tree, 'find_all'):
            from_clauses = parse_tree.find_all(sqlglot.expressions.From)
            for from_clause in from_clauses:
                table_name = str(from_clause).upper()
                if any(large_table in table_name for large_table in large_tables):
                    # Check if there's a WHERE clause
                    if not parse_tree.find(sqlglot.expressions.Where):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            code="MISSING_WHERE_LARGE_TABLE",
                            message=f"Query on large table {table_name} without WHERE clause",
                            suggestion="Consider adding WHERE clause to limit results",
                            auto_fixable=False
                        ))
        
        return issues
    
    def _suggest_parse_fix(self, sql: str, error_msg: str) -> Optional[str]:
        """Suggest fixes for common parse errors."""
        error_lower = error_msg.lower()
        
        if "unexpected token" in error_lower:
            return "Check for missing commas, parentheses, or quotes"
        elif "expected" in error_lower and "got" in error_lower:
            return "Verify SQL syntax around the mentioned token"
        elif "unterminated" in error_lower:
            return "Check for missing closing quotes or parentheses"
        
        return None
    
    def _validate_firebird_specifics(self, sql: str) -> List[ValidationIssue]:
        """Validate Firebird-specific syntax requirements."""
        issues = []
        sql_upper = sql.upper()
        
        # Check for proper FIRST/SKIP usage
        if 'FIRST' in sql_upper:
            # FIRST should come right after SELECT
            if not re.search(r'\\bSELECT\\s+FIRST\\b', sql, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="FIRST_PLACEMENT",
                    message="FIRST should immediately follow SELECT",
                    suggestion="Move FIRST to right after SELECT keyword"
                ))
        
        # Check for Firebird system table access patterns
        if 'RDB$' in sql_upper or 'MON$' in sql_upper:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                code="SYSTEM_TABLE_ACCESS",
                message="Accessing Firebird system tables",
                suggestion="Ensure proper permissions for system table access"
            ))
        
        # Check for proper string concatenation
        if '||' in sql and '+' in sql:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="MIXED_CONCATENATION",
                message="Mixed string concatenation operators (|| and +)",
                suggestion="Use || for string concatenation in Firebird"
            ))
        
        # Check for DATE/TIME literal formats
        date_patterns = [
            r"'\\d{4}-\\d{2}-\\d{2}'",  # YYYY-MM-DD
            r"'\\d{2}/\\d{2}/\\d{4}'",  # MM/DD/YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, sql):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.SUGGESTION,
                    code="DATE_LITERAL_FORMAT",
                    message="Consider using DATE literal format",
                    suggestion="Use DATE 'YYYY-MM-DD' format for clarity"
                ))
                break
        
        return issues
    
    def _validate_against_schema(self, sql: str) -> List[ValidationIssue]:
        """Validate SQL against known database schema."""
        issues = []
        
        # Extract table names from SQL
        table_pattern = r'\\b(FROM|JOIN|UPDATE|INSERT\\s+INTO)\\s+([A-Za-z_][A-Za-z0-9_]*)'
        matches = re.findall(table_pattern, sql, re.IGNORECASE)
        
        referenced_tables = set()
        for match in matches:
            table_name = match[1].upper()
            referenced_tables.add(table_name)
            
            # Check if table exists
            if table_name not in self.known_tables:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="UNKNOWN_TABLE",
                    message=f"Table '{table_name}' not found in schema",
                    suggestion="Verify table name spelling and case"
                ))
        
        # Check column references (basic pattern matching)
        for table in referenced_tables:
            if table in self.table_columns:
                # Look for column references with table prefix
                column_pattern = rf'\\b{re.escape(table)}\\.([A-Za-z_][A-Za-z0-9_]*)'
                column_matches = re.findall(column_pattern, sql, re.IGNORECASE)
                
                for column in column_matches:
                    column_upper = column.upper()
                    if column_upper not in self.table_columns[table]:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            code="UNKNOWN_COLUMN",
                            message=f"Column '{column}' not found in table '{table}'",
                            suggestion="Verify column name spelling and case"
                        ))
        
        return issues
    
    def _validate_security(self, sql: str) -> List[ValidationIssue]:
        """Validate SQL for security concerns."""
        issues = []
        sql_upper = sql.upper()
        
        # Check for DML operations (should be prevented in read-only context)
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if f' {keyword} ' in f' {sql_upper} ':
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="DML_NOT_ALLOWED",
                    message=f"{keyword} operations are not allowed",
                    suggestion="Use only SELECT statements for queries"
                ))
        
        # Check for potential SQL injection patterns
        injection_patterns = [
            r"';\\s*--",  # Comment injection
            r"\\bOR\\s+1\\s*=\\s*1",  # Classic OR injection
            r"\\bUNION\\s+SELECT",  # Union-based injection
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="POTENTIAL_INJECTION",
                    message="SQL contains patterns that may indicate injection attempts",
                    suggestion="Ensure all user input is properly sanitized"
                ))
        
        return issues
    
    def validate_and_fix(self, sql: str) -> ValidationResult:
        """
        Validate SQL and automatically apply fixes where possible.
        
        Args:
            sql: SQL statement to validate and fix
            
        Returns:
            ValidationResult with validation status and fixed SQL
        """
        # First validation pass
        result = self.validate_sql(sql)
        
        # Apply automatic fixes for auto-fixable issues
        if result.fixed_sql and any(issue.auto_fixable for issue in result.issues):
            # Re-validate the fixed SQL to ensure it's still valid
            fixed_result = self.validate_sql(result.fixed_sql)
            
            # If the fix introduced new errors, keep the original
            if not fixed_result.has_errors() or len(fixed_result.get_errors()) <= len(result.get_errors()):
                result.fixed_sql = fixed_result.fixed_sql or result.fixed_sql
                # Update issues to reflect the fixes applied
                result.issues = [issue for issue in result.issues if not issue.auto_fixable] + fixed_result.issues
        
        return result
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """Generate a human-readable validation summary."""
        lines = []
        lines.append(f"SQL Validation Summary:")
        lines.append(f"Status: {'✓ VALID' if result.is_valid else '✗ INVALID'}")
        lines.append(f"Dialect: {result.dialect_used}")
        
        if result.issues:
            error_count = len(result.get_errors())
            warning_count = len(result.get_warnings())
            
            lines.append(f"Issues: {error_count} errors, {warning_count} warnings")
            
            for issue in result.issues:
                symbol = "✗" if issue.severity == ValidationSeverity.ERROR else "⚠" if issue.severity == ValidationSeverity.WARNING else "ℹ"
                lines.append(f"  {symbol} {issue.code}: {issue.message}")
                if issue.suggestion:
                    lines.append(f"    Suggestion: {issue.suggestion}")
        else:
            lines.append("No issues found")
        
        if result.fixed_sql and result.fixed_sql != result.original_sql:
            lines.append("\\n🔧 Automatic fixes applied")
        
        return "\\n".join(lines)


# Global validator instance
sql_validator = FirebirdSQLValidator()


def validate_firebird_sql(sql: str, db_interface: Optional[FDBDirectInterface] = None) -> ValidationResult:
    """
    Convenience function to validate Firebird SQL.
    
    Args:
        sql: SQL statement to validate
        db_interface: Optional database interface for schema validation
        
    Returns:
        ValidationResult with validation details
    """
    if db_interface and sql_validator.db_interface != db_interface:
        # Create a new validator with the provided database interface
        validator = FirebirdSQLValidator(db_interface)
        return validator.validate_and_fix(sql)
    else:
        return sql_validator.validate_and_fix(sql)


if __name__ == "__main__":
    # Test the SQL validator
    print("=== Firebird SQL Validator Test ===\\n")
    
    test_queries = [
        # Valid Firebird SQL
        "SELECT FIRST 10 * FROM BEWOHNER WHERE VBEGINN IS NOT NULL",
        
        # SQL with LIMIT (should be fixed to FIRST)
        "SELECT * FROM OBJEKTE LIMIT 5",
        
        # SQL with OFFSET (should be fixed to SKIP)
        "SELECT * FROM WOHNUNG LIMIT 10 OFFSET 20",
        
        # SQL with unsupported function (should be fixed)
        "SELECT LENGTH(BSTR) FROM BEWOHNER",
        
        # Invalid SQL (syntax error)
        "SELECT * FROM BEWOHNER WHERE",
        
        # Potentially dangerous SQL
        "DROP TABLE BEWOHNER",
        
        # Complex query
        "SELECT B.BEWNR, B.VNAME, O.OSTR FROM BEWOHNER B JOIN OBJEKTE O ON B.BWO = O.ONR WHERE B.VBEGINN IS NOT NULL"
    ]
    
    for i, sql in enumerate(test_queries, 1):
        print(f"Test {i}: {sql}")
        result = validate_firebird_sql(sql)
        print(sql_validator.get_validation_summary(result))
        
        if result.fixed_sql and result.fixed_sql != sql:
            print(f"Fixed SQL: {result.fixed_sql}")
        
        print("-" * 60)