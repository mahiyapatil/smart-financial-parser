"""
Unit tests for Pydantic validation schemas.
Tests data validation and type safety.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

from src.validators import RawTransaction, CleanTransaction, TransactionSummary


class TestRawTransaction:
    """Test raw transaction validation schema."""

    def test_valid_raw_transaction(self):
        """Test creating a valid raw transaction."""
        txn = RawTransaction(
            date="2023-01-15",
            merchant_name="Amazon",
            amount="45.99",
            category="Shopping"
        )

        assert txn.date == "2023-01-15"
        assert txn.merchant_name == "Amazon"
        assert txn.amount == "45.99"
        assert txn.category == "Shopping"

    def test_whitespace_stripping(self):
        """Test that whitespace is automatically stripped."""
        txn = RawTransaction(
            date="  2023-01-15  ",
            merchant_name="  Amazon  ",
            amount="  45.99  ",
            category="  Shopping  "
        )

        assert txn.date == "2023-01-15"
        assert txn.merchant_name == "Amazon"
        assert txn.amount == "45.99"
        assert txn.category == "Shopping"

    def test_empty_date_raises_error(self):
        """Test that empty date raises validation error."""
        with pytest.raises(ValidationError):
            RawTransaction(
                date="",
                merchant_name="Amazon",
                amount="45.99",
                category="Shopping"
            )

    def test_empty_merchant_defaults(self):
        """Test that empty merchant gets default value."""
        txn = RawTransaction(
            date="2023-01-15",
            merchant_name="",
            amount="45.99",
            category="Shopping"
        )

        assert txn.merchant_name == "UNKNOWN_MERCHANT"

    def test_empty_amount_raises_error(self):
        """Test that empty amount raises validation error."""
        with pytest.raises(ValidationError):
            RawTransaction(
                date="2023-01-15",
                merchant_name="Amazon",
                amount="",
                category="Shopping"
            )

    def test_missing_category_defaults(self):
        """Test that missing category defaults to empty string."""
        txn = RawTransaction(
            date="2023-01-15",
            merchant_name="Amazon",
            amount="45.99"
        )

        assert txn.category == ""


class TestCleanTransaction:
    """Test clean transaction validation schema."""

    def test_valid_clean_transaction(self):
        """Test creating a valid clean transaction."""
        txn = CleanTransaction(
            date=datetime(2023, 1, 15),
            merchant_name="AMAZON.COM",
            normalized_merchant="Amazon",
            amount=Decimal("45.99"),
            currency="USD",
            category="Shopping",
            is_refund=False
        )

        assert txn.date.year == 2023
        assert txn.normalized_merchant == "Amazon"
        assert txn.amount == Decimal("45.99")
        assert txn.currency == "USD"

    def test_merchant_name_sanitization(self):
        """Test that dangerous characters are removed from merchant names."""
        txn = CleanTransaction(
            date=datetime(2023, 1, 15),
            merchant_name="Test<script>alert('xss')</script>",
            normalized_merchant="Test",
            amount=Decimal("45.99"),
            currency="USD",
            category="Shopping"
        )

        # Should have removed dangerous characters
        assert '<' not in txn.merchant_name
        assert '>' not in txn.merchant_name
        # Note: The word "script" remains but dangerous tags are removed
        # This is acceptable - we're removing injection vectors, not all words

    def test_amount_validation_max(self):
        """Test that amounts exceeding maximum are rejected."""
        with pytest.raises(ValidationError):
            CleanTransaction(
                date=datetime(2023, 1, 15),
                merchant_name="Test",
                normalized_merchant="Test",
                amount=Decimal("9999999.99"),  # Too large
                currency="USD",
                category="Shopping"
            )

    def test_currency_code_validation(self):
        """Test that currency code must be 3 uppercase letters."""
        # Valid currency
        txn = CleanTransaction(
            date=datetime(2023, 1, 15),
            merchant_name="Test",
            normalized_merchant="Test",
            amount=Decimal("45.99"),
            currency="EUR",
            category="Shopping"
        )
        assert txn.currency == "EUR"

        # Invalid currency format should raise error
        with pytest.raises(ValidationError):
            CleanTransaction(
                date=datetime(2023, 1, 15),
                merchant_name="Test",
                normalized_merchant="Test",
                amount=Decimal("45.99"),
                currency="us",  # Not 3 uppercase letters
                category="Shopping"
            )

    def test_default_values(self):
        """Test that default values are set correctly."""
        txn = CleanTransaction(
            date=datetime(2023, 1, 15),
            merchant_name="Test",
            normalized_merchant="Test",
            amount=Decimal("45.99")
        )

        assert txn.currency == "USD"  # Default
        assert txn.category == "Uncategorized"  # Default
        assert txn.is_refund == False  # Default
        assert txn.is_anomaly == False  # Default

    def test_anomaly_fields(self):
        """Test anomaly detection fields."""
        txn = CleanTransaction(
            date=datetime(2023, 1, 15),
            merchant_name="Test",
            normalized_merchant="Test",
            amount=Decimal("5000.00"),
            is_anomaly=True,
            anomaly_reason="Large transaction"
        )

        assert txn.is_anomaly == True
        assert txn.anomaly_reason == "Large transaction"

    def test_json_serialization(self):
        """Test that transaction can be serialized to JSON."""
        txn = CleanTransaction(
            date=datetime(2023, 1, 15),
            merchant_name="Amazon",
            normalized_merchant="Amazon",
            amount=Decimal("45.99"),
            currency="USD",
            category="Shopping"
        )

        # Should be able to convert to dict
        txn_dict = txn.model_dump()
        assert isinstance(txn_dict, dict)
        assert 'date' in txn_dict
        assert 'amount' in txn_dict


class TestTransactionSummary:
    """Test transaction summary validation schema."""

    def test_valid_summary(self):
        """Test creating a valid transaction summary."""
        summary = TransactionSummary(
            total_transactions=10,
            date_range=(datetime(2023, 1, 1), datetime(2023, 1, 31)),
            total_spending=Decimal("1000.00"),
            total_refunds=Decimal("50.00"),
            net_spending=Decimal("950.00"),
            top_category="Shopping",
            top_category_spending=Decimal("500.00"),
            anomalies_detected=2,
            merchants_normalized=8
        )

        assert summary.total_transactions == 10
        assert summary.top_category == "Shopping"
        assert summary.anomalies_detected == 2

    def test_non_negative_validation(self):
        """Test that counts cannot be negative."""
        with pytest.raises(ValidationError):
            TransactionSummary(
                total_transactions=-5,  # Cannot be negative
                date_range=(datetime(2023, 1, 1), datetime(2023, 1, 31)),
                total_spending=Decimal("1000.00"),
                total_refunds=Decimal("50.00"),
                net_spending=Decimal("950.00"),
                top_category="Shopping",
                top_category_spending=Decimal("500.00"),
                anomalies_detected=0,
                merchants_normalized=5
            )

    def test_summary_serialization(self):
        """Test that summary can be serialized."""
        summary = TransactionSummary(
            total_transactions=10,
            date_range=(datetime(2023, 1, 1), datetime(2023, 1, 31)),
            total_spending=Decimal("1000.00"),
            total_refunds=Decimal("50.00"),
            net_spending=Decimal("950.00"),
            top_category="Shopping",
            top_category_spending=Decimal("500.00"),
            anomalies_detected=2,
            merchants_normalized=8
        )

        summary_dict = summary.model_dump()
        assert isinstance(summary_dict, dict)
        assert summary_dict['total_transactions'] == 10


class TestValidationEdgeCases:
    """Test edge cases in validation."""

    def test_very_long_merchant_name(self):
        """Test that very long merchant names are handled."""
        long_name = "A" * 250  # 250 characters

        # Should be rejected (max 200)
        with pytest.raises(ValidationError):
            CleanTransaction(
                date=datetime(2023, 1, 15),
                merchant_name=long_name,
                normalized_merchant="Test",
                amount=Decimal("45.99")
            )

    def test_special_characters_sanitized(self):
        """Test that special characters are properly sanitized."""
        txn = CleanTransaction(
            date=datetime(2023, 1, 15),
            merchant_name='Test "Merchant" <with> \\slashes\\',
            normalized_merchant="Test Merchant",
            amount=Decimal("45.99")
        )

        # Dangerous characters should be removed
        assert '"' not in txn.merchant_name
        assert '<' not in txn.merchant_name
        assert '>' not in txn.merchant_name
        assert '\\' not in txn.merchant_name

    def test_decimal_precision(self):
        """Test that decimal amounts are validated for precision."""
        # Pydantic v2 enforces decimal_places=2 strictly
        # So 3 decimal places should raise an error
        with pytest.raises(ValidationError):
            CleanTransaction(
                date=datetime(2023, 1, 15),
                merchant_name="Test",
                normalized_merchant="Test",
                amount=Decimal("45.999")  # 3 decimal places - should fail
            )

        # But 2 decimal places should work
        txn = CleanTransaction(
            date=datetime(2023, 1, 15),
            merchant_name="Test",
            normalized_merchant="Test",
            amount=Decimal("45.99")  # 2 decimal places - should work
        )
        assert txn.amount == Decimal("45.99")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])