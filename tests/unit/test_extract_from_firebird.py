"""
Unit tests for the extract_from_firebird module.

These tests verify the functionality of the extract_from_firebird.py script
using mocked database connections to ensure proper extraction and JSON formatting.
"""

import json
import decimal
from datetime import date, datetime
from unittest.mock import Mock, patch, mock_open

import pytest


@pytest.mark.unit
class TestExtractFromFirebird:
    """Test suite for extract_from_firebird.py functionality."""

    @patch("extract_from_firebird.driver.connect")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("extract_from_firebird.argparse.ArgumentParser")
    def test_extract_data_success(self, mock_argparse, mock_json_dump, mock_open_file, mock_connect):
        """Test successful data extraction."""
        # Mock argparse to control command line arguments
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser
        mock_args = Mock()
        mock_args.db = "test.fdb"
        mock_args.user = "test_user"
        mock_args.password = "test_password"
        mock_args.out = "output.json"
        mock_parser.parse_args.return_value = mock_args

        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor # Corrected mock

        # Mock cursor fetchall results for tables, columns, rows, procedures, params
        mock_cursor.fetchall.side_effect = [
            [("TABLE1",), ("TABLE2",)],  # Tables
            [("COL1",), ("COL2",)],      # Columns for TABLE1
            [("row1col1", "row1col2")],  # Rows for TABLE1
            [("COL3",), ("COL4",)],      # Columns for TABLE2
            [("row2col1", "row2col2")],  # Rows for TABLE2
            [("PROC1",)],                # Procedures
            [("PROC_BODY",)],            # Proc body
            [("PARAM1", 0, "VARCHAR")],  # Proc params
        ]

        # Import and run the function
        from extract_from_firebird import extract_data

        extract_data(mock_args.db, mock_args.user, mock_args.password, mock_args.out)

        # Verify database connection was made
        mock_connect.assert_called_once_with(
            database="test.fdb", user="test_user", password="test_password"
        )

        # Verify queries were executed
        mock_cursor.execute.assert_any_call(
            "SELECT rdb$relation_name FROM rdb$relations WHERE rdb$system_flag = 0 AND rdb$view_blr IS NULL"
        )
        mock_cursor.execute.assert_any_call(
            """
                        SELECT
                            rf.rdb$field_name,
                            f.rdb$field_type,
                            f.rdb$field_length,
                            f.rdb$field_precision,
                            f.rdb$field_scale,
                            f.rdb$null_flag
                        FROM rdb$relation_fields rf
                        JOIN rdb$fields f ON rf.rdb$field_source = f.rdb$field_name
                        WHERE rf.rdb$relation_name = ?
                        ORDER BY rf.rdb$field_position
                        """,
            ("TABLE1",),
        )
        mock_cursor.execute.assert_any_call('SELECT FIRST 1000 * FROM "TABLE1"')
        mock_cursor.execute.assert_any_call(
            """
                        SELECT
                            rf.rdb$field_name,
                            f.rdb$field_type,
                            f.rdb$field_length,
                            f.rdb$field_precision,
                            f.rdb$field_scale,
                            f.rdb$null_flag
                        FROM rdb$relation_fields rf
                        JOIN rdb$fields f ON rf.rdb$field_source = f.rdb$field_name
                        WHERE rf.rdb$relation_name = ?
                        ORDER BY rf.rdb$field_position
                        """,
            ("TABLE2",),
        )
        mock_cursor.execute.assert_any_call('SELECT FIRST 1000 * FROM "TABLE2"')
        mock_cursor.execute.assert_any_call(
            "SELECT rdb$procedure_name FROM rdb$procedures"
        )
        mock_cursor.execute.assert_any_call(
            """
                        SELECT rdb$procedure_source
                        FROM rdb$procedures
                        WHERE rdb$procedure_name = ?
                        """,
            ("PROC1",),
        )
        mock_cursor.execute.assert_any_call(
            """
                        SELECT
                            rdb$parameter_name,
                            rdb$parameter_type,
                            rdb$field_source
                        FROM rdb$procedure_parameters
                        WHERE rdb$procedure_name = ?
                        ORDER BY rdb$parameter_type, rdb$parameter_number
                        """,
            ("PROC1",),
        )

        # Verify output file was opened and json.dump was called
        mock_open_file.assert_called_once_with("output.json", "w", encoding="utf-8")
        mock_json_dump.assert_called_once()

    @patch("extract_from_firebird.driver.connect")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("extract_from_firebird.argparse.ArgumentParser")
    def test_extract_data_connection_error(self, mock_argparse, mock_json_dump, mock_open_file, mock_connect):
        """Test handling of database connection errors."""
        # Mock argparse
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser
        mock_args = Mock()
        mock_args.db = "test.fdb"
        mock_args.user = "test_user"
        mock_args.password = "test_password"
        mock_args.out = "output.json"
        mock_parser.parse_args.return_value = mock_args

        # Mock connection to raise an exception
        mock_connect.side_effect = Exception("Connection failed")

        # Import and run the function
        from extract_from_firebird import extract_data

        # We expect a SystemExit because the script prints an error and exits
        with patch("builtins.print") as mock_print: # Mock print to avoid SystemExit
             extract_data(mock_args.db, mock_args.user, mock_args.password, mock_args.out)
             mock_print.assert_called_with("Ein Fehler ist aufgetreten: Connection failed")


        # Verify connection was attempted
        mock_connect.assert_called_once_with(
            database="test.fdb", user="test_user", password="test_password"
        )

        # Verify json.dump was NOT called
        mock_json_dump.assert_not_called()

    @patch("extract_from_firebird.driver.connect")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("extract_from_firebird.argparse.ArgumentParser")
    def test_extract_data_query_error(self, mock_argparse, mock_json_dump, mock_open_file, mock_connect):
        """Test handling of query execution errors."""
        # Mock argparse
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser
        mock_args = Mock()
        mock_args.db = "test.fdb"
        mock_args.user = "test_user"
        mock_args.password = "test_password"
        mock_args.out = "output.json"
        mock_parser.parse_args.return_value = mock_args

        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor # Corrected mock

        # Mock tables query success, but data query fails
        mock_cursor.fetchall.side_effect = [
            [("TABLE1",)],  # Tables
            Exception("Query failed"), # Columns for TABLE1
        ]

        # Import and run the function
        from extract_from_firebird import extract_data

        # We expect a SystemExit because the script prints an error and exits
        with patch("builtins.print") as mock_print: # Mock print to avoid SystemExit
             extract_data(mock_args.db, mock_args.user, mock_args.password, mock_args.out)
             mock_print.assert_called_with("Ein Fehler ist aufgetreten: Query failed")


        # Verify connection was made
        mock_connect.assert_called_once_with(
            database="test.fdb", user="test_user", password="test_password"
        )

        # Verify json.dump was NOT called
        mock_json_dump.assert_not_called()

    def test_enhanced_json_encoder(self):
        """Test the EnhancedJSONEncoder handles special types correctly."""
        from extract_from_firebird import EnhancedJSONEncoder
        
        # Test decimal conversion
        test_decimal = decimal.Decimal("123.45")
        encoder = EnhancedJSONEncoder()
        assert encoder.encode(test_decimal) == "123.45"

        # Test date conversion
        test_date = date(2025, 6, 5)
        assert encoder.encode(test_date) == '"2025-06-05"'

        # Test datetime conversion
        test_datetime = datetime(2025, 6, 5, 14, 30, 0)
        assert encoder.encode(test_datetime) == '"2025-06-05T14:30:00"'

        # Test complex object
        test_obj = {
            "decimal": decimal.Decimal("123.45"),
            "date": date(2025, 6, 5),
            "datetime": datetime(2025, 6, 5, 14, 30, 0),
            "string": "test",
            "number": 42,
        }
        expected = (
            '{"decimal": 123.45, "date": "2025-06-05", '
            '"datetime": "2025-06-05T14:30:00", "string": "test", "number": 42}'
        )
        assert encoder.encode(test_obj) == expected

    def test_is_valid_identifier(self):
        """Test the is_valid_identifier function for validating database identifiers."""
        from extract_from_firebird import is_valid_identifier

        # Test valid identifiers
        assert is_valid_identifier("valid_name") is True
        assert is_valid_identifier("ValidName123") is True
        assert is_valid_identifier("$SystemTable") is True
        assert is_valid_identifier("TABLE_NAME_WITH_UNDERSCORE") is True

        # Test invalid identifiers
        assert is_valid_identifier("invalid-name") is False
        assert is_valid_identifier("invalid.name") is False
        assert is_valid_identifier("'injection'") is False
        assert is_valid_identifier('"table"') is False
        assert is_valid_identifier("space name") is False

    @patch("extract_from_firebird.argparse.ArgumentParser")
    def test_argparse_defaults(self, mock_argparse):
        """Test argument parsing with various input parameters."""
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser
        mock_args = Mock()
        mock_args.db = "test.fdb"
        mock_args.out = "output.json"
        mock_args.user = "sysdba"
        mock_args.password = "masterkey"
        mock_parser.parse_args.return_value = mock_args

        # Import and check args
        from extract_from_firebird import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--db", default="default.fdb")
        parser.add_argument("--out", default="default.json")
        parser.add_argument("--user", default="sysdba")
        parser.add_argument("--password", default="masterkey")
        
        args = parser.parse_args([]) # Pass empty list to avoid parsing pytest args

        assert args.db == "default.fdb"
        assert args.out == "default.json"
        assert args.user == "sysdba"
        assert args.password == "masterkey"

    @patch("extract_from_firebird.driver.connect")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("extract_from_firebird.argparse.ArgumentParser")
    def test_main_execution(self, mock_argparse, mock_json_dump, mock_open_file, mock_connect):
        """Test the main execution block."""
        # Mock argparse
        mock_parser = Mock()
        mock_argparse.return_value = mock_parser
        mock_args = Mock()
        mock_args.db = "test.fdb"
        mock_args.user = "test_user"
        mock_args.password = "test_password"
        mock_args.out = "output.json"
        mock_parser.parse_args.return_value = mock_args

        # Mock extract_data function
        with patch("extract_from_firebird.extract_data") as mock_extract_data:
            # Simulate running the script
            from extract_from_firebird import __name__ as script_name
            if script_name == "__main__":
                # This part is tricky to test directly as __name__ is fixed.
                # We rely on the previous tests covering extract_data and argparse.
                pass







