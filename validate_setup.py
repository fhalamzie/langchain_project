#!/usr/bin/env python3
"""
Validation script for WINCASA testing and code quality setup.

This script validates the configuration files and testing framework setup
without requiring all dependencies to be installed.
"""

import os
import sys
import yaml
import configparser
from pathlib import Path
import subprocess


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and report status."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False


def validate_yaml_config(file_path: str) -> bool:
    """Validate YAML configuration file."""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        print(f"✅ YAML syntax valid: {file_path}")
        return True
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error in {file_path}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False


def validate_ini_config(file_path: str) -> bool:
    """Validate INI configuration file."""
    try:
        config = configparser.ConfigParser()
        config.read(file_path)
        print(f"✅ INI syntax valid: {file_path}")
        return True
    except configparser.Error as e:
        print(f"❌ INI syntax error in {file_path}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False


def check_python_syntax(file_path: str) -> bool:
    """Check Python file syntax."""
    try:
        with open(file_path, 'r') as f:
            compile(f.read(), file_path, 'exec')
        print(f"✅ Python syntax valid: {file_path}")
        return True
    except SyntaxError as e:
        print(f"❌ Python syntax error in {file_path}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False


def check_tool_availability() -> dict:
    """Check availability of testing and code quality tools."""
    tools = {
        'pytest': 'python3 -m pytest --version',
        'black': 'python3 -m black --version', 
        'isort': 'python3 -m isort --version',
        'flake8': 'python3 -m flake8 --version',
        'bandit': 'python3 -m bandit --version',
        'pre-commit': 'pre-commit --version'
    }
    
    results = {}
    print("\n🔧 Tool Availability Check:")
    
    for tool, command in tools.items():
        try:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"✅ {tool}: {version}")
                results[tool] = True
            else:
                print(f"❌ {tool}: Not available")
                results[tool] = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ {tool}: Not available")
            results[tool] = False
    
    return results


def validate_project_structure() -> bool:
    """Validate project directory structure."""
    print("\n📁 Project Structure Validation:")
    
    required_dirs = [
        "tests",
        "tests/unit", 
        "tests/integration",
        "integration_tests"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"✅ Directory: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            all_good = False
    
    return all_good


def validate_test_files() -> bool:
    """Validate test file syntax."""
    print("\n🧪 Test File Validation:")
    
    test_files = [
        "tests/conftest.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/unit/test_sample.py"
    ]
    
    all_good = True
    for test_file in test_files:
        if not check_python_syntax(test_file):
            all_good = False
    
    return all_good


def validate_config_files() -> bool:
    """Validate all configuration files."""
    print("\n⚙️ Configuration File Validation:")
    
    config_checks = [
        ("pytest.ini", "pytest configuration", validate_ini_config),
        ("pyproject.toml", "pyproject.toml configuration", check_file_exists),
        (".pre-commit-config.yaml", "pre-commit configuration", validate_yaml_config),
        ("requirements.txt", "requirements file", check_file_exists)
    ]
    
    all_good = True
    for file_path, description, validator in config_checks:
        if validator == check_file_exists:
            if not check_file_exists(file_path, description):
                all_good = False
        else:
            if not validator(file_path):
                all_good = False
    
    return all_good


def run_basic_pytest_check() -> bool:
    """Run basic pytest collection check."""
    print("\n🧪 Pytest Collection Test:")
    
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            test_count = sum(1 for line in lines if 'test' in line.lower())
            print(f"✅ Pytest collection successful - {test_count} tests found")
            return True
        else:
            print(f"❌ Pytest collection failed:")
            print(result.stderr)
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ Pytest collection failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🚀 WINCASA Testing & Code Quality Setup Validation")
    print("=" * 60)
    
    os.chdir('/home/projects/langchain_project')
    
    checks = [
        ("Project Structure", validate_project_structure),
        ("Configuration Files", validate_config_files), 
        ("Test Files", validate_test_files),
        ("Tool Availability", lambda: check_tool_availability() and True),
        ("Pytest Collection", run_basic_pytest_check)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results[check_name] = False
    
    # Summary
    print("\n📊 Validation Summary:")
    print("=" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All validation checks passed! Setup is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)