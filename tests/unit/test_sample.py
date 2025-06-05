"""
Sample unit test demonstrating the testing framework setup.

This module contains example tests to validate the pytest configuration,
fixtures, and testing patterns for the WINCASA LangChain project.
"""

import os
from unittest.mock import Mock, patch

import pytest


class TestSampleUnit:
    """Sample unit test class demonstrating testing patterns."""

    @pytest.mark.unit
    def test_environment_setup(self, test_env_vars):
        """Test that environment variables are properly configured."""
        assert os.environ.get("TEST_MODE") == "true"
        assert "OPENAI_API_KEY" in os.environ
        assert os.environ["OPENAI_API_KEY"] == "test-openai-key-12345"

    @pytest.mark.unit
    def test_mock_firebird_connection(self, mock_firebird_connection):
        """Test Firebird connection mocking."""
        mock_conn, mock_cursor = mock_firebird_connection

        # Test connection is mocked
        assert mock_conn is not None
        assert mock_cursor is not None

        # Test cursor methods are available
        mock_cursor.execute.return_value = None
        mock_cursor.fetchall.return_value = []

        mock_cursor.execute("SELECT 1 FROM RDB$DATABASE")
        mock_cursor.execute.assert_called_once()

    @pytest.mark.unit
    def test_sample_database_schema(self, sample_database_schema):
        """Test sample database schema fixture."""
        schema = sample_database_schema

        assert "tables" in schema
        assert len(schema["tables"]) == 2

        apartments_table = schema["tables"][0]
        assert apartments_table["name"] == "APARTMENTS"
        assert len(apartments_table["columns"]) == 4

    @pytest.mark.unit
    def test_retrieval_context_fixture(self, sample_retrieval_context):
        """Test sample retrieval context fixture."""
        context = sample_retrieval_context

        assert context["mode"] == "enhanced"
        assert context["total_docs"] == 2
        assert len(context["documents"]) == 2

        first_doc = context["documents"][0]
        assert "content" in first_doc
        assert "metadata" in first_doc
        assert first_doc["metadata"]["relevance"] >= 0.8

    @pytest.mark.unit
    def test_http_mocking(self, responses_mock):
        """Test HTTP API mocking with responses."""
        try:
            import requests

            # Setup mock response
            responses_mock.add(
                responses_mock.GET,
                "https://api.example.com/test",
                json={"status": "ok"},
                status=200,
            )

            # Make request
            response = requests.get("https://api.example.com/test")

            assert response.status_code == 200
            assert response.json()["status"] == "ok"
        except ImportError:
            pytest.skip("requests library not available")

    @pytest.mark.unit
    def test_temp_directory(self, temp_dir):
        """Test temporary directory fixture."""
        import os
        import tempfile

        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)

        # Create test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        assert os.path.exists(test_file)


@pytest.mark.unit
def test_basic_functionality():
    """Test basic Python functionality."""
    assert 1 + 1 == 2
    assert "test" in "testing"
    assert [1, 2, 3] == [1, 2, 3]


@pytest.mark.unit
def test_string_operations():
    """Test string operations."""
    test_string = "WINCASA LangChain Agent"

    assert test_string.startswith("WINCASA")
    assert "LangChain" in test_string
    assert test_string.endswith("Agent")
    assert len(test_string.split()) == 3


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("test", "TEST"),
        ("HELLO", "HELLO"),
        ("MixedCase", "MIXEDCASE"),
        ("", ""),
    ],
)
def test_parametrized_string_upper(input_value, expected):
    """Test parametrized string uppercase conversion."""
    assert input_value.upper() == expected


@pytest.mark.unit
def test_mock_usage():
    """Test mock object usage patterns."""
    mock_obj = Mock()

    # Configure mock
    mock_obj.method.return_value = "mocked_value"
    mock_obj.property = "test_property"

    # Test mock behavior
    assert mock_obj.method() == "mocked_value"
    assert mock_obj.property == "test_property"

    # Verify calls
    mock_obj.method.assert_called_once()


@pytest.mark.unit
def test_exception_handling():
    """Test exception handling patterns."""

    def divide_by_zero():
        return 1 / 0

    with pytest.raises(ZeroDivisionError):
        divide_by_zero()

    def custom_error():
        raise ValueError("Custom error message")

    with pytest.raises(ValueError, match="Custom error message"):
        custom_error()
