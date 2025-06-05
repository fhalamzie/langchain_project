#!/usr/bin/env python3
"""
Code Quality Tools Demonstration Script

This script simulates what Black, isort, flake8, and bandit would report
when analyzing code quality issues.
"""

import os
import re
from pathlib import Path


def simulate_black_analysis(file_path: str) -> dict:
    """Simulate Black code formatter analysis."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for common formatting issues Black would fix
    if 'import sys,os' in content:
        issues.append("Line 3: Multiple imports on single line")
    
    if 'class   BadlyFormattedClass' in content:
        issues.append("Line 8: Extra whitespace around class definition")
    
    if '__init__(self,name,age,' in content:
        issues.append("Line 9: Missing spaces after commas in function parameters")
    
    if 'self.name=name' in content:
        issues.append("Line 10: Missing spaces around assignment operator")
    
    if 'if data==None:return None' in content:
        issues.append("Line 18: Multiple statements on single line")
    
    if 'very_long_variable_name_that_makes_this_line_extremely_long = param1 + param2' in content:
        issues.append("Line 35: Line too long (would be wrapped)")
    
    if "result={'param1':param1" in content:
        issues.append("Line 38: Missing spaces in dictionary")
    
    return {
        "tool": "Black",
        "description": "Code formatter (opinionated, zero-config)",
        "issues_found": len(issues),
        "issues": issues,
        "would_fix": [
            "Consistent line length (88 characters)",
            "Proper spacing around operators",
            "Consistent quote usage", 
            "Proper line wrapping",
            "Standardized formatting"
        ]
    }


def simulate_isort_analysis(file_path: str) -> dict:
    """Simulate isort import sorting analysis."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check import order issues
    lines = content.split('\n')
    import_section = []
    for i, line in enumerate(lines[:20]):  # Check first 20 lines
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_section.append((i+1, line.strip()))
    
    if len(import_section) > 0:
        issues.append("Lines 3-6: Imports not properly sorted")
        issues.append("Line 3: Standard library imports mixed with third-party")
        issues.append("Line 6: Multiple imports should be separated by category")
    
    return {
        "tool": "isort",
        "description": "Import sorting (Black-compatible profile)",
        "issues_found": len(issues),
        "issues": issues,
        "would_fix": [
            "Sort imports alphabetically within sections",
            "Separate standard library, third-party, and local imports",
            "Consistent import formatting",
            "Remove duplicate imports"
        ]
    }


def simulate_flake8_analysis(file_path: str) -> dict:
    """Simulate flake8 linting analysis."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    issues = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for common flake8 issues
        if len(line) > 88:
            issues.append(f"Line {i}: E501 line too long ({len(line)} > 88 characters)")
        
        if 'import sys,os' in line:
            issues.append(f"Line {i}: E401 multiple imports on one line")
        
        if '  ' in line and line.strip():
            if '    ' not in line and line.startswith('  '):
                issues.append(f"Line {i}: E111 indentation is not a multiple of four")
        
        if line.rstrip() != line:
            issues.append(f"Line {i}: W291 trailing whitespace")
        
        if ' =' in line and '==' not in line and '!=' not in line:
            if not ' = ' in line:
                issues.append(f"Line {i}: E225 missing whitespace around operator")
    
    # Check for unused imports
    if 'import numpy as np' in content and 'np.' not in content:
        issues.append("Line 4: F401 'numpy as np' imported but unused")
    
    if 'import yaml' in content and 'yaml.' not in content:
        issues.append("Line 6: F401 'yaml' imported but unused")
    
    # Check for missing docstrings
    if 'class BadlyFormattedClass:' in content:
        if '"""' not in content.split('class BadlyFormattedClass:')[1].split('def')[0]:
            issues.append("Line 8: D101 Missing docstring in public class")
    
    return {
        "tool": "flake8", 
        "description": "Python linting (syntax, style, complexity)",
        "issues_found": len(issues),
        "issues": issues[:15],  # Limit to first 15 for readability
        "categories": [
            "E series: PEP 8 style violations",
            "W series: Warning level issues",
            "F series: PyFlakes errors (unused imports, etc.)",
            "D series: Docstring issues"
        ]
    }


def simulate_bandit_analysis(file_path: str) -> dict:
    """Simulate bandit security analysis."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    issues = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for security issues
        if 'eval(' in line:
            issues.append({
                "line": i,
                "issue": "B307",
                "severity": "HIGH",
                "description": "Use of eval() is dangerous and should be avoided"
            })
        
        if 'password' in line.lower() and '=' in line:
            issues.append({
                "line": i,
                "issue": "B106", 
                "severity": "MEDIUM",
                "description": "Possible hardcoded password"
            })
        
        if 'exec(' in line:
            issues.append({
                "line": i,
                "issue": "B102",
                "severity": "HIGH", 
                "description": "Use of exec() is dangerous"
            })
    
    return {
        "tool": "bandit",
        "description": "Security vulnerability scanner",
        "issues_found": len(issues),
        "issues": issues,
        "security_categories": [
            "Code injection vulnerabilities",
            "Hardcoded credentials",
            "Insecure random number generation",
            "SQL injection risks",
            "Shell injection risks"
        ]
    }


def demonstrate_pre_commit_workflow():
    """Demonstrate pre-commit hook workflow."""
    return {
        "tool": "pre-commit",
        "description": "Automated git hooks for code quality",
        "workflow": [
            "1. Developer runs: git add .",
            "2. Developer runs: git commit -m 'message'", 
            "3. Pre-commit hooks execute automatically:",
            "   - trailing-whitespace: Remove trailing spaces",
            "   - end-of-file-fixer: Ensure files end with newline",
            "   - check-yaml: Validate YAML syntax", 
            "   - black: Auto-format Python code",
            "   - isort: Sort imports automatically",
            "   - flake8: Check code quality",
            "   - bandit: Scan for security issues",
            "4. If issues found: commit is blocked, files are fixed",
            "5. Developer reviews changes and commits again",
            "6. If all checks pass: commit succeeds"
        ],
        "benefits": [
            "Automatic code quality enforcement",
            "Consistent formatting across team",
            "Early security issue detection", 
            "No manual formatting needed",
            "Prevents bad code from entering repository"
        ]
    }


def main():
    """Run code quality tools demonstration."""
    print("🛠️ Code Quality Tools Demonstration")
    print("=" * 50)
    
    file_path = "sample_bad_code.py"
    
    # Simulate each tool
    tools = [
        simulate_black_analysis(file_path),
        simulate_isort_analysis(file_path),
        simulate_flake8_analysis(file_path),
        simulate_bandit_analysis(file_path)
    ]
    
    for tool_result in tools:
        print(f"\n🔧 {tool_result['tool']}")
        print(f"Description: {tool_result['description']}")
        print(f"Issues Found: {tool_result['issues_found']}")
        
        if 'issues' in tool_result and tool_result['issues']:
            print("\nIssues Detected:")
            for issue in tool_result['issues'][:10]:  # Show first 10
                if isinstance(issue, dict):
                    print(f"  • Line {issue['line']}: {issue['issue']} ({issue['severity']}) - {issue['description']}")
                else:
                    print(f"  • {issue}")
        
        if 'would_fix' in tool_result:
            print("\nWould Fix:")
            for fix in tool_result['would_fix']:
                print(f"  ✅ {fix}")
        
        if 'categories' in tool_result:
            print("\nError Categories:")
            for category in tool_result['categories']:
                print(f"  📋 {category}")
        
        if 'security_categories' in tool_result:
            print("\nSecurity Categories Checked:")
            for category in tool_result['security_categories']:
                print(f"  🛡️ {category}")
    
    # Pre-commit workflow
    print(f"\n🔗 Pre-commit Hooks Workflow")
    print("=" * 30)
    
    workflow = demonstrate_pre_commit_workflow()
    print(f"Description: {workflow['description']}")
    
    print("\nWorkflow Steps:")
    for step in workflow['workflow']:
        print(f"  {step}")
    
    print("\nBenefits:")
    for benefit in workflow['benefits']:
        print(f"  ✅ {benefit}")
    
    print(f"\n📊 Summary")
    print("=" * 20)
    total_issues = sum(tool['issues_found'] for tool in tools)
    print(f"Total Issues Found: {total_issues}")
    print(f"Tools Configured: {len(tools) + 1} (including pre-commit)")
    print(f"Security Issues: {tools[3]['issues_found']}")
    print(f"Style Issues: {tools[0]['issues_found'] + tools[1]['issues_found']}")
    print(f"Code Quality Issues: {tools[2]['issues_found']}")


if __name__ == "__main__":
    main()