"""
Unit tests for utility functions.
Tests logging, audit trails, and data integrity checks.
"""

import pytest
import json
import logging
from pathlib import Path
from datetime import datetime

from src.utils import setup_logging, AuditLogger, DataIntegrityChecker, format_currency


class TestSetupLogging:
    """Test logging configuration."""

    def test_setup_logging_creates_logs_directory(self, tmp_path, monkeypatch):
        """Test that setup_logging creates logs directory."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Setup logging
        setup_logging(log_level="INFO")

        # Check logs directory exists
        assert (tmp_path / "logs").exists()

    def test_setup_logging_creates_log_file(self, tmp_path, monkeypatch):
        """Test that log file is created."""
        monkeypatch.chdir(tmp_path)

        setup_logging(log_level="DEBUG")

        # Log file should exist
        assert (tmp_path / "logs" / "parser.log").exists()

    def test_setup_logging_with_different_levels(self, tmp_path, monkeypatch):
        """Test logging with different log levels."""
        monkeypatch.chdir(tmp_path)

        # Should not raise error with different levels
        setup_logging(log_level="DEBUG")
        setup_logging(log_level="INFO")
        setup_logging(log_level="WARNING")
        setup_logging(log_level="ERROR")


class TestAuditLogger:
    """Test audit logging functionality."""

    @pytest.fixture
    def audit_logger(self, tmp_path):
        """Create audit logger with temp directory."""
        log_path = tmp_path / "test_audit.log"
        return AuditLogger(str(log_path))

    def test_audit_logger_initialization(self, tmp_path):
        """Test audit logger creates file and directory."""
        log_path = tmp_path / "logs" / "audit.log"
        logger = AuditLogger(str(log_path))

        # Directory should be created
        assert log_path.parent.exists()
        # File should exist (empty)
        assert log_path.exists()

    def test_log_event(self, audit_logger, tmp_path):
        """Test logging an event."""
        test_data = {
            "transaction_id": 123,
            "amount": 45.99,
            "merchant": "Test Store"
        }

        audit_logger.log_event("test_event", test_data)

        # Read the log file
        with open(audit_logger.log_path, 'r') as f:
            log_content = f.read()

        # Verify event was logged
        assert "test_event" in log_content
        assert "transaction_id" in log_content
        assert "45.99" in log_content

    def test_log_event_creates_valid_json(self, audit_logger):
        """Test that logged events are valid JSON."""
        audit_logger.log_event("parse_started", {"file": "test.csv"})

        # Read and parse JSON
        with open(audit_logger.log_path, 'r') as f:
            line = f.readline()
            event = json.loads(line)

        # Verify structure
        assert "timestamp" in event
        assert "event_type" in event
        assert "data" in event
        assert event["event_type"] == "parse_started"
        assert event["data"]["file"] == "test.csv"

    def test_log_multiple_events(self, audit_logger):
        """Test logging multiple events."""
        events = [
            ("event1", {"key1": "value1"}),
            ("event2", {"key2": "value2"}),
            ("event3", {"key3": "value3"})
        ]

        for event_type, data in events:
            audit_logger.log_event(event_type, data)

        # Read all events
        with open(audit_logger.log_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 3

        # Verify each is valid JSON
        for line in lines:
            event = json.loads(line)
            assert "timestamp" in event
            assert "event_type" in event

    def test_get_events_all(self, audit_logger):
        """Test retrieving all events."""
        # Log some events
        audit_logger.log_event("event1", {"data": 1})
        audit_logger.log_event("event2", {"data": 2})
        audit_logger.log_event("event3", {"data": 3})

        # Get all events
        all_events = audit_logger.get_events()

        assert len(all_events) == 3
        assert all_events[0]["event_type"] == "event1"
        assert all_events[1]["event_type"] == "event2"
        assert all_events[2]["event_type"] == "event3"

    def test_get_events_filtered(self, audit_logger):
        """Test retrieving filtered events."""
        # Log mixed events
        audit_logger.log_event("parse_started", {"file": "test1.csv"})
        audit_logger.log_event("transaction_parsed", {"id": 1})
        audit_logger.log_event("parse_started", {"file": "test2.csv"})
        audit_logger.log_event("transaction_parsed", {"id": 2})

        # Get only parse_started events
        parse_events = audit_logger.get_events(event_type="parse_started")

        assert len(parse_events) == 2
        assert all(e["event_type"] == "parse_started" for e in parse_events)

    def test_get_events_empty_log(self, tmp_path):
        """Test get_events on non-existent log."""
        logger = AuditLogger(str(tmp_path / "nonexistent.log"))

        # Delete the file
        Path(logger.log_path).unlink()

        events = logger.get_events()
        assert events == []


class TestDataIntegrityChecker:
    """Test data integrity checking functionality."""

    def test_check_csv_integrity_valid_file(self, tmp_path):
        """Test integrity check on valid CSV."""
        csv_file = tmp_path / "valid.csv"
        csv_file.write_text("Date,Merchant Name,Amount\n2023-01-15,Test,45.99\n")

        result = DataIntegrityChecker.check_csv_integrity(str(csv_file))

        assert result["file_exists"] == True
        assert result["is_readable"] == True
        assert result["has_header"] == True
        assert result["row_count"] == 1
        assert len(result["issues"]) == 0

    def test_check_csv_integrity_missing_file(self, tmp_path):
        """Test integrity check on non-existent file."""
        result = DataIntegrityChecker.check_csv_integrity(str(tmp_path / "missing.csv"))

        assert result["file_exists"] == False
        assert "File does not exist" in result["issues"]

    def test_check_csv_integrity_missing_headers(self, tmp_path):
        """Test integrity check with missing required headers."""
        csv_file = tmp_path / "no_headers.csv"
        csv_file.write_text("Column1,Column2,Column3\n1,2,3\n")

        result = DataIntegrityChecker.check_csv_integrity(str(csv_file))

        assert result["file_exists"] == True
        assert result["is_readable"] == True
        assert result["has_header"] == False
        assert "Missing required columns" in result["issues"][0]

    def test_check_csv_integrity_row_count(self, tmp_path):
        """Test row count calculation."""
        csv_file = tmp_path / "multi_row.csv"
        csv_file.write_text("Date,Merchant,Amount\n2023-01-15,A,10\n2023-01-16,B,20\n2023-01-17,C,30\n")

        result = DataIntegrityChecker.check_csv_integrity(str(csv_file))

        assert result["row_count"] == 3  # Excludes header

    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        result = DataIntegrityChecker.sanitize_input("  Test String  ")
        assert result == "Test String"

    def test_sanitize_input_removes_script_tags(self):
        """Test that script tags are detected and removed."""
        dangerous = "<script>alert('xss')</script>"
        result = DataIntegrityChecker.sanitize_input(dangerous)

        # Should not contain dangerous patterns
        assert "<script" not in result.lower()
        assert "alert" in result  # Content remains, tags removed

    def test_sanitize_input_removes_javascript(self):
        """Test that javascript: protocol is removed."""
        dangerous = "javascript:alert('xss')"
        result = DataIntegrityChecker.sanitize_input(dangerous)

        assert "javascript:" not in result.lower()

    def test_sanitize_input_removes_onerror(self):
        """Test that onerror handlers are removed."""
        dangerous = "image.jpg' onerror='alert(1)"
        result = DataIntegrityChecker.sanitize_input(dangerous)

        assert "onerror=" not in result.lower()

    def test_sanitize_input_truncates_long_strings(self):
        """Test that very long strings are truncated."""
        long_string = "A" * 1000
        result = DataIntegrityChecker.sanitize_input(long_string, max_length=100)

        assert len(result) == 100

    def test_sanitize_input_handles_non_strings(self):
        """Test sanitization converts non-strings."""
        result = DataIntegrityChecker.sanitize_input(12345)
        assert result == "12345"

        result = DataIntegrityChecker.sanitize_input(45.99)
        assert result == "45.99"


class TestFormatCurrency:
    """Test currency formatting utility."""

    def test_format_currency_usd(self):
        """Test USD formatting."""
        result = format_currency(45.99, "USD")
        assert result == "$45.99"

    def test_format_currency_eur(self):
        """Test EUR formatting."""
        result = format_currency(45.50, "EUR")
        assert result == "€45.50"

    def test_format_currency_gbp(self):
        """Test GBP formatting."""
        result = format_currency(67.80, "GBP")
        assert result == "£67.80"

    def test_format_currency_jpy(self):
        """Test JPY formatting."""
        result = format_currency(1000, "JPY")
        assert result == "¥1,000.00"

    def test_format_currency_with_commas(self):
        """Test large amounts get comma separators."""
        result = format_currency(2500.00, "USD")
        assert result == "$2,500.00"

    def test_format_currency_negative_amounts(self):
        """Test negative amounts are displayed as positive."""
        result = format_currency(-45.99, "USD")
        assert result == "$45.99"  # abs() used

    def test_format_currency_unknown_currency(self):
        """Test unknown currency defaults to $."""
        result = format_currency(45.99, "XXX")
        assert result == "$45.99"

    def test_format_currency_rounds_properly(self):
        """Test decimal rounding."""
        result = format_currency(45.996, "USD")
        assert result == "$46.00"  # Rounds to 2 decimal places


if __name__ == "__main__":
    pytest.main([__file__, "-v"])