#!/usr/bin/env python3
"""
WINCASA Codebase Analysis with Code Quality Tools

This script analyzes the existing WINCASA codebase and shows what
Black, isort, flake8, and bandit would find and fix.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List


def analyze_file_with_black_rules(file_path: str) -> Dict[str, Any]:
    """Analyze a file for Black formatting issues."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return {"error": str(e), "issues": []}

    issues = []

    for i, line in enumerate(lines, 1):
        # Check line length
        if len(line.rstrip()) > 88:
            issues.append(f"Line {i}: Line too long ({len(line.rstrip())} > 88 chars)")

        # Check for multiple statements on one line
        if ";" in line and not line.strip().startswith("#"):
            issues.append(f"Line {i}: Multiple statements on one line")

        # Check spacing around operators
        if (
            "=" in line
            and not any(op in line for op in ["==", "!=", "<=", ">="])
            and not line.strip().startswith("#")
        ):
            if " = " not in line and "=" in line:
                issues.append(f"Line {i}: Missing spaces around assignment operator")

        # Check for comma spacing
        if "," in line and not line.strip().startswith("#"):
            # Simple check for missing space after comma
            if re.search(r",[^\s\]]", line):
                issues.append(f"Line {i}: Missing space after comma")

    return {
        "file": file_path,
        "total_lines": len(lines),
        "issues": issues[:10],  # Limit to first 10
        "issues_count": len(issues),
    }


def analyze_file_imports(file_path: str) -> Dict[str, Any]:
    """Analyze imports for isort issues."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return {"error": str(e), "issues": []}

    imports = []
    issues = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            imports.append((i, stripped))

    if len(imports) > 1:
        # Check if imports are grouped properly
        stdlib_imports = []
        third_party_imports = []
        local_imports = []

        stdlib_modules = {
            "sys",
            "os",
            "json",
            "time",
            "datetime",
            "pathlib",
            "typing",
            "re",
            "tempfile",
            "subprocess",
        }

        for line_num, import_line in imports:
            if "import " in import_line:
                module = import_line.split("import ")[1].split(" as ")[0].split(".")[0]
                if module in stdlib_modules:
                    stdlib_imports.append((line_num, import_line))
                else:
                    third_party_imports.append((line_num, import_line))

        # Check if imports are properly separated
        if stdlib_imports and third_party_imports:
            stdlib_lines = [x[0] for x in stdlib_imports]
            third_party_lines = [x[0] for x in third_party_imports]

            if max(stdlib_lines) > min(third_party_lines):
                issues.append(
                    "Imports not properly grouped (stdlib mixed with third-party)"
                )

    return {
        "file": file_path,
        "imports_count": len(imports),
        "issues": issues,
        "issues_count": len(issues),
    }


def analyze_file_security(file_path: str) -> Dict[str, Any]:
    """Analyze file for security issues (bandit-style)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
    except Exception as e:
        return {"error": str(e), "issues": []}

    issues = []

    for i, line in enumerate(lines, 1):
        # Check for eval/exec usage
        if "eval(" in line or "exec(" in line:
            issues.append(
                {
                    "line": i,
                    "severity": "HIGH",
                    "issue": "Dangerous eval/exec usage",
                    "code": (
                        line.strip()[:60] + "..."
                        if len(line.strip()) > 60
                        else line.strip()
                    ),
                }
            )

        # Check for hardcoded passwords/secrets
        if (
            any(
                keyword in line.lower()
                for keyword in ["password", "secret", "key", "token"]
            )
            and "=" in line
        ):
            if not any(
                safe in line.lower() for safe in ["os.environ", "getenv", "config"]
            ):
                issues.append(
                    {
                        "line": i,
                        "severity": "MEDIUM",
                        "issue": "Possible hardcoded credential",
                        "code": (
                            line.strip()[:60] + "..."
                            if len(line.strip()) > 60
                            else line.strip()
                        ),
                    }
                )

        # Check for subprocess without shell=False
        if "subprocess." in line and "shell=True" in line:
            issues.append(
                {
                    "line": i,
                    "severity": "HIGH",
                    "issue": "Subprocess with shell=True (injection risk)",
                    "code": (
                        line.strip()[:60] + "..."
                        if len(line.strip()) > 60
                        else line.strip()
                    ),
                }
            )

        # Check for SQL string concatenation
        if re.search(r'["\'].*SELECT.*["\'].*\+', line, re.IGNORECASE):
            issues.append(
                {
                    "line": i,
                    "severity": "MEDIUM",
                    "issue": "Possible SQL injection via string concatenation",
                    "code": (
                        line.strip()[:60] + "..."
                        if len(line.strip()) > 60
                        else line.strip()
                    ),
                }
            )

    return {
        "file": file_path,
        "issues": issues[:5],  # Limit to first 5
        "issues_count": len(issues),
    }


def analyze_codebase_files(file_paths: List[str]) -> Dict[str, Any]:
    """Analyze multiple files and provide summary."""
    results = {
        "files_analyzed": 0,
        "total_issues": 0,
        "black_issues": 0,
        "isort_issues": 0,
        "security_issues": 0,
        "file_results": [],
    }

    for file_path in file_paths:
        if not os.path.exists(file_path):
            continue

        print(f"📁 Analyzing: {file_path}")

        # Analyze with different tools
        black_result = analyze_file_with_black_rules(file_path)
        isort_result = analyze_file_imports(file_path)
        security_result = analyze_file_security(file_path)

        file_analysis = {
            "file": file_path,
            "lines": black_result.get("total_lines", 0),
            "black": black_result,
            "isort": isort_result,
            "security": security_result,
        }

        results["file_results"].append(file_analysis)
        results["files_analyzed"] += 1
        results["black_issues"] += black_result.get("issues_count", 0)
        results["isort_issues"] += isort_result.get("issues_count", 0)
        results["security_issues"] += security_result.get("issues_count", 0)
        results["total_issues"] += (
            black_result.get("issues_count", 0)
            + isort_result.get("issues_count", 0)
            + security_result.get("issues_count", 0)
        )

    return results


def main():
    """Run codebase analysis."""
    print("🔍 WINCASA Codebase Analysis with Code Quality Tools")
    print("=" * 60)

    # Core WINCASA files to analyze
    core_files = [
        "firebird_sql_agent_direct.py",
        "enhanced_retrievers.py",
        "fdb_direct_interface.py",
        "langchain_sql_retriever_fixed.py",
        "global_context.py",
        "phoenix_monitoring.py",
        "llm_interface.py",
        "enhanced_qa_ui.py",
        "streamlit_qa_app.py",
    ]

    # Find existing files
    existing_files = []
    for file_path in core_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)

    if not existing_files:
        print("❌ No core WINCASA files found for analysis")
        return

    print(f"📋 Found {len(existing_files)} core files to analyze")
    print()

    # Analyze files
    results = analyze_codebase_files(existing_files)

    # Display results
    print(f"\n📊 Analysis Summary")
    print("=" * 30)
    print(f"Files Analyzed: {results['files_analyzed']}")
    print(f"Total Issues Found: {results['total_issues']}")
    print(f"  • Black (formatting): {results['black_issues']}")
    print(f"  • isort (imports): {results['isort_issues']}")
    print(f"  • Security issues: {results['security_issues']}")

    # Detailed results
    print(f"\n🔍 Detailed Results by File")
    print("=" * 40)

    for file_result in results["file_results"]:
        file_name = file_result["file"]
        lines = file_result["lines"]

        print(f"\n📄 {file_name} ({lines} lines)")

        # Black issues
        black_issues = file_result["black"]["issues"]
        if black_issues:
            print(f"  🎨 Black formatting issues ({len(black_issues)}):")
            for issue in black_issues[:3]:  # Show first 3
                print(f"    • {issue}")
            if len(black_issues) > 3:
                print(f"    • ... and {len(black_issues) - 3} more")

        # Import issues
        isort_issues = file_result["isort"]["issues"]
        if isort_issues:
            print(f"  📦 Import issues ({len(isort_issues)}):")
            for issue in isort_issues:
                print(f"    • {issue}")

        # Security issues
        security_issues = file_result["security"]["issues"]
        if security_issues:
            print(f"  🛡️ Security issues ({len(security_issues)}):")
            for issue in security_issues:
                print(
                    f"    • Line {issue['line']}: {issue['issue']} ({issue['severity']})"
                )
                print(f"      Code: {issue['code']}")

        if not black_issues and not isort_issues and not security_issues:
            print(f"  ✅ No issues found")

    # Recommendations
    print(f"\n🎯 Recommendations")
    print("=" * 20)

    if results["total_issues"] == 0:
        print("✅ Codebase looks clean! No major issues found.")
    else:
        print(f"📋 Found {results['total_issues']} total issues that could be fixed:")

        if results["black_issues"] > 0:
            print(
                f"  🎨 Run 'black .' to fix {results['black_issues']} formatting issues"
            )

        if results["isort_issues"] > 0:
            print(
                f"  📦 Run 'isort .' to fix {results['isort_issues']} import organization issues"
            )

        if results["security_issues"] > 0:
            print(
                f"  🛡️ Review and fix {results['security_issues']} security issues manually"
            )

    print(f"\n🚀 Next Steps:")
    print("  1. Install tools: pip install black isort flake8 bandit")
    print("  2. Run tools: ./run_tests.sh format-fix")
    print("  3. Review security issues manually")
    print("  4. Setup pre-commit hooks: ./run_tests.sh pre-commit")


if __name__ == "__main__":
    main()
