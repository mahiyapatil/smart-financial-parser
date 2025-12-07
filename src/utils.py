"""
Utility functions for logging, audit trails, and error handling.
Implements production-grade observability practices.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide logging.

    Sets up both console and file logging with proper formatting.
    """
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Configure logging format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # File handler - detailed logs
    file_handler = logging.FileHandler("logs/parser.log", mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Console handler - less verbose
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Logging initialized")


class AuditLogger:
    """
    Audit logger for tracking all parsing operations.

    Creates a JSON audit trail for compliance and debugging.
    Security best practice: all data transformations should be auditable.
    """

    def __init__(self, log_path: str):
        """Initialize audit logger with file path."""
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create or append to audit log
        if not self.log_path.exists():
            self.log_path.write_text("")

    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event (e.g., 'parse_started', 'transaction_parsed')
            data: Event-specific data to log
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }

        # Append to audit log
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(audit_entry) + "\n")

    def get_events(self, event_type: str = None) -> list:
        """
        Retrieve audit events, optionally filtered by type.

        Args:
            event_type: Optional filter for specific event types

        Returns:
            List of matching audit events
        """
        if not self.log_path.exists():
            return []

        events = []
        with open(self.log_path, 'r') as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    if event_type is None or event['event_type'] == event_type:
                        events.append(event)

        return events


class DataIntegrityChecker:
    """
    Validate data integrity throughout the pipeline.
    Security best practice: validate all inputs and outputs.
    """

    @staticmethod
    def check_csv_integrity(filepath: str) -> Dict[str, Any]:
        """
        Perform integrity checks on input CSV file.

        Returns:
            Dict with integrity check results
        """
        checks = {
            "file_exists": Path(filepath).exists(),
            "is_readable": False,
            "has_header": False,
            "row_count": 0,
            "issues": []
        }

        if not checks["file_exists"]:
            checks["issues"].append("File does not exist")
            return checks

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            checks["is_readable"] = True
            checks["row_count"] = len(lines) - 1  # Exclude header

            if lines:
                header = lines[0].strip()
                required_columns = ['date', 'merchant', 'amount']

                header_lower = header.lower()
                checks["has_header"] = any(col in header_lower for col in required_columns)

                if not checks["has_header"]:
                    checks["issues"].append("Missing required columns in header")

        except Exception as e:
            checks["issues"].append(f"Error reading file: {str(e)}")

        return checks

    @staticmethod
    def sanitize_input(value: str, max_length: int = 500) -> str:
        """
        Sanitize string input to prevent injection attacks.

        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Truncate to max length
        value = value[:max_length]

        # Remove potentially dangerous characters
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onload=']
        value_lower = value.lower()

        for pattern in dangerous_patterns:
            if pattern in value_lower:
                logging.warning(f"Dangerous pattern detected and removed: {pattern}")
                value = value.replace(pattern, '')

        return value.strip()


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as currency string.

    Args:
        amount: Numeric amount
        currency: Currency code (USD, EUR, etc.)

    Returns:
        Formatted currency string
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }

    symbol = symbols.get(currency, "$")
    return f"{symbol}{abs(amount):,.2f}"
