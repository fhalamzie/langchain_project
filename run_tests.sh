#!/bin/bash
# WINCASA Testing & Code Quality Runner Script
# Convenience script for running tests and code quality checks

set -e  # Exit on any error

echo "🚀 WINCASA Testing & Code Quality Runner"
echo "======================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a tool is available
check_tool() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✅ $1 is available${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $1 is not available${NC}"
        return 1
    fi
}

# Function to run a command with error handling
run_command() {
    local cmd="$1"
    local description="$2"
    
    echo -e "\n${YELLOW}📋 $description${NC}"
    echo "Command: $cmd"
    
    if eval "$cmd"; then
        echo -e "${GREEN}✅ $description completed successfully${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
        return 1
    fi
}

# Parse command line arguments
case "${1:-help}" in
    "test"|"tests")
        echo -e "\n🧪 Running Tests"
        echo "==============="
        
        # Basic tests without coverage
        run_command "python3 -m pytest tests/ -v --no-cov" "Unit Tests"
        
        # If pytest-cov is available, run with coverage
        if python3 -m pytest --cov=. --help &> /dev/null; then
            echo -e "\n📊 Running Tests with Coverage"
            echo "=============================="
            run_command "python3 -m pytest tests/ --cov=tests --cov-report=term-missing --cov-fail-under=50" "Tests with Coverage"
        fi
        ;;
        
    "format"|"fmt")
        echo -e "\n🎨 Code Formatting"
        echo "=================="
        
        if check_tool "black"; then
            run_command "black --check --diff ." "Black Code Formatting Check"
        else
            echo "Install with: pip install black"
        fi
        
        if check_tool "isort"; then
            run_command "isort --check-only --diff ." "Import Sorting Check"
        else
            echo "Install with: pip install isort"
        fi
        ;;
        
    "format-fix"|"fix")
        echo -e "\n🔧 Auto-fixing Code Format"
        echo "==========================="
        
        if check_tool "black"; then
            run_command "black ." "Auto-format with Black"
        fi
        
        if check_tool "isort"; then
            run_command "isort ." "Auto-sort imports with isort"
        fi
        ;;
        
    "lint")
        echo -e "\n🔍 Code Linting"
        echo "==============="
        
        if check_tool "flake8"; then
            run_command "flake8 ." "Flake8 Linting"
        else
            echo "Install with: pip install flake8"
        fi
        
        if check_tool "bandit"; then
            run_command "bandit -r . -x tests/" "Security Linting (Bandit)"
        else
            echo "Install with: pip install bandit"
        fi
        ;;
        
    "pre-commit")
        echo -e "\n🔗 Pre-commit Hooks"
        echo "==================="
        
        if check_tool "pre-commit"; then
            run_command "pre-commit install" "Install Pre-commit Hooks"
            run_command "pre-commit run --all-files" "Run All Pre-commit Hooks"
        else
            echo "Install with: pip install pre-commit"
        fi
        ;;
        
    "validate"|"check")
        echo -e "\n✅ Validation Check"
        echo "==================="
        
        run_command "python3 validate_setup.py" "Setup Validation"
        ;;
        
    "install"|"setup")
        echo -e "\n📦 Installing Dependencies"
        echo "=========================="
        
        echo "Installing testing and code quality dependencies..."
        pip install pytest pytest-cov pytest-mock responses black isort flake8 bandit pre-commit --user
        
        echo -e "\n🔗 Setting up pre-commit hooks..."
        pre-commit install
        ;;
        
    "all")
        echo -e "\n🎯 Running All Checks"
        echo "===================="
        
        # Validation first
        run_command "python3 validate_setup.py" "Setup Validation"
        
        # Tests
        run_command "python3 -m pytest tests/ -v --no-cov" "Unit Tests"
        
        # Linting (if available)
        if check_tool "flake8"; then
            run_command "flake8 . --exit-zero" "Flake8 Linting (warnings only)"
        fi
        
        if check_tool "bandit"; then
            run_command "bandit -r . -x tests/ --exit-zero" "Security Check (warnings only)"
        fi
        
        echo -e "\n${GREEN}🎉 All checks completed!${NC}"
        ;;
        
    "help"|*)
        cat << EOF

🚀 WINCASA Testing & Code Quality Runner

Usage: $0 [command]

Commands:
  test, tests       Run pytest tests
  format, fmt       Check code formatting (black, isort)
  format-fix, fix   Auto-fix code formatting
  lint              Run linting (flake8, bandit)
  pre-commit        Setup and run pre-commit hooks
  validate, check   Validate setup configuration
  install, setup    Install all dependencies
  all               Run all checks and tests
  help              Show this help message

Examples:
  $0 test           # Run tests
  $0 format-fix     # Auto-format code
  $0 all           # Run everything
  $0 validate      # Check setup

Dependencies Installation:
  pip install pytest pytest-cov pytest-mock responses black isort flake8 bandit pre-commit

EOF
        ;;
esac