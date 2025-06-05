"""
Pytest configuration and shared fixtures for WINCASA LangChain tests.

This module defines pytest fixtures that are shared across all test modules,
including database connections, mock configurations, and test data setup.
"""

import os
import tempfile
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest

# Import responses only if available
try:
    import responses

    RESPONSES_AVAILABLE = True
except ImportError:
    RESPONSES_AVAILABLE = False


@pytest.fixture(scope="session")
def test_env_vars() -> Dict[str, str]:
    """Provide test environment variables."""
    return {
        "OPENAI_API_KEY": "test-openai-key-12345",
        "OPENROUTER_API_KEY": "test-openrouter-key-12345",
        "TEST_MODE": "true",
        "FIREBIRD_SERVER": "localhost",
        "FIREBIRD_PORT": "3050",
        "FIREBIRD_USER": "SYSDBA",
        "FIREBIRD_PASSWORD": "masterkey",
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(test_env_vars):
    """Setup test environment variables for all tests."""
    original_env = {}
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Cleanup
    for key in test_env_vars:
        if original_env[key] is not None:
            os.environ[key] = original_env[key]
        else:
            os.environ.pop(key, None)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_firebird_connection():
    """Mock Firebird database connection."""
    try:
        with patch("fdb.connect") as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            yield mock_conn, mock_cursor
    except ImportError:
        # If fdb is not available, provide mock objects anyway
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        yield mock_conn, mock_cursor


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for LLM testing."""
    try:
        with patch("openai.OpenAI") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [
                Mock(message=Mock(content="SELECT * FROM test_table;"))
            ]
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client
            yield mock_client
    except ImportError:
        # If openai is not available, provide mock anyway
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="SELECT * FROM test_table;"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        yield mock_client


@pytest.fixture
def mock_phoenix_tracer():
    """Mock Phoenix tracer for monitoring tests."""
    try:
        with patch("phoenix.otel.register") as mock_register:
            mock_tracer = Mock()
            mock_register.return_value = mock_tracer
            yield mock_tracer
    except ImportError:
        # If phoenix is not available, provide mock anyway
        mock_tracer = Mock()
        yield mock_tracer


@pytest.fixture
def sample_database_schema():
    """Provide sample database schema for testing."""
    return {
        "tables": [
            {
                "name": "APARTMENTS",
                "columns": [
                    {"name": "ID", "type": "INTEGER", "primary_key": True},
                    {"name": "APARTMENT_NUMBER", "type": "VARCHAR(10)"},
                    {"name": "BUILDING_ID", "type": "INTEGER"},
                    {"name": "AREA_SQM", "type": "DECIMAL(10,2)"},
                ],
            },
            {
                "name": "RESIDENTS",
                "columns": [
                    {"name": "ID", "type": "INTEGER", "primary_key": True},
                    {"name": "FIRST_NAME", "type": "VARCHAR(50)"},
                    {"name": "LAST_NAME", "type": "VARCHAR(50)"},
                    {"name": "APARTMENT_ID", "type": "INTEGER"},
                ],
            },
        ]
    }


@pytest.fixture
def sample_retrieval_context():
    """Provide sample retrieval context for testing."""
    return {
        "documents": [
            {
                "content": "APARTMENTS table contains apartment information",
                "metadata": {"table": "APARTMENTS", "relevance": 0.9},
            },
            {
                "content": "RESIDENTS table contains resident information",
                "metadata": {"table": "RESIDENTS", "relevance": 0.8},
            },
        ],
        "mode": "enhanced",
        "total_docs": 2,
    }


@pytest.fixture
def responses_mock():
    """Provide responses mock for HTTP API testing."""
    if RESPONSES_AVAILABLE:
        with responses.RequestsMock() as rsps:
            yield rsps
    else:
        pytest.skip("responses library not available")


# Markers for test organization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration tests with external services"
    )
    config.addinivalue_line("markers", "system: End-to-end system tests")
    config.addinivalue_line("markers", "slow: Tests that take more than 1 second")
    config.addinivalue_line("markers", "firebird: Tests requiring Firebird database")
    config.addinivalue_line("markers", "llm: Tests requiring LLM API access")
    config.addinivalue_line("markers", "phoenix: Tests for Phoenix monitoring")
    config.addinivalue_line("markers", "retrieval: Tests for retrieval modes")
    config.addinivalue_line("markers", "langchain: Tests for LangChain integration")


# Skip slow tests by default
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers."""
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--runllm", action="store_true", default=False, help="run LLM integration tests"
    )
    parser.addoption(
        "--runfirebird", action="store_true", default=False, help="run Firebird tests"
    )
