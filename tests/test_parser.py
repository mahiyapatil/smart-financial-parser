"""
Integration tests for the FinancialParser.
Tests end-to-end parsing workflows.
"""

import pytest
import pandas as pd
from pathlib import Path
from decimal import Decimal
from datetime import datetime

from src.parser import FinancialParser
from src.validators import CleanTransaction


class TestFinancialParser:
    """Test the main parser functionality."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        return FinancialParser(audit_log_path="logs/test_audit.log")

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a temporary CSV file for testing."""
        csv_content = """ Date ,Merchant Name,Amount  ,Category
2023-01-15,AMAZON.COM,$45.99,Shopping
Jan 17th 2023,UBER *TRIP,$12.30,Transportation
01/18/2023,Starbucks,5.50,Food
"""
        csv_file = tmp_path / "test_transactions.csv"
        csv_file.write_text(csv_content)
        return str(csv_file)

    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly."""
        assert parser is not None
        assert parser.stats['total_rows'] == 0
        assert parser.stats['successful_parses'] == 0

    def test_load_csv(self, parser, sample_csv):
        """Test CSV loading functionality."""
        df = parser.load_csv(sample_csv)
        assert len(df) == 3
        assert 'Date' in df.columns
        assert 'Merchant Name' in df.columns

    def test_parse_transaction_success(self, parser):
        """Test parsing a valid transaction."""
        row = {
            'Date': '2023-01-15',
            'Merchant Name': 'Amazon',
            'Amount': '$45.99',
            'Category': 'Shopping'
        }

        result = parser.parse_transaction(row, 1)

        assert result is not None
        assert isinstance(result, CleanTransaction)
        assert result.amount == Decimal('45.99')
        assert result.normalized_merchant == 'Amazon'

    def test_parse_transaction_with_errors(self, parser):
        """Test parsing transaction with missing data."""
        row = {
            'Date': '',  # Missing date
            'Merchant Name': 'Test Merchant',
            'Amount': '45.99',
            'Category': 'Shopping'
        }

        result = parser.parse_transaction(row, 1)
        assert result is None  # Should fail gracefully
        assert parser.stats['failed_parses'] == 1

    def test_parse_file_integration(self, parser, sample_csv):
        """Test end-to-end file parsing."""
        output_file = "data/processed/test_output.csv"

        clean_transactions = parser.parse_file(sample_csv, output_file)

        # Verify parsing stats
        assert len(clean_transactions) > 0
        assert parser.stats['successful_parses'] > 0

        # Verify all transactions are CleanTransaction objects
        for txn in clean_transactions:
            assert isinstance(txn, CleanTransaction)

    def test_save_clean_data(self, parser, tmp_path):
        """Test saving cleaned data to CSV."""
        # Create sample clean transactions
        transactions = [
            CleanTransaction(
                date=datetime(2023, 1, 15),
                merchant_name="AMAZON.COM",
                normalized_merchant="Amazon",
                amount=Decimal("45.99"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=datetime(2023, 1, 16),
                merchant_name="Starbucks",
                normalized_merchant="Starbucks",
                amount=Decimal("5.50"),
                currency="USD",
                category="Food",
                is_refund=False
            )
        ]

        output_file = tmp_path / "output.csv"
        parser.save_clean_data(transactions, str(output_file))

        # Verify file was created and contains data
        assert output_file.exists()
        df = pd.read_csv(output_file)
        assert len(df) == 2
        assert 'normalized_merchant' in df.columns

    def test_get_stats(self, parser):
        """Test retrieving parser statistics."""
        stats = parser.get_stats()

        assert isinstance(stats, dict)
        assert 'total_rows' in stats
        assert 'successful_parses' in stats
        assert 'failed_parses' in stats
        assert 'errors' in stats


class TestParserErrorHandling:
    """Test parser's error handling capabilities."""

    @pytest.fixture
    def parser(self):
        return FinancialParser(audit_log_path="logs/test_audit.log")

    def test_malformed_csv(self, parser, tmp_path):
        """Test handling of malformed CSV file."""
        # Create CSV with inconsistent columns
        malformed_csv = tmp_path / "malformed.csv"
        malformed_csv.write_text("Date,Merchant\n2023-01-15\n")  # Missing column

        # Should not crash
        df = parser.load_csv(str(malformed_csv))
        assert df is not None

    def test_unicode_handling(self, parser):
        """Test handling of unicode characters."""
        row = {
            'Date': '2023-01-15',
            'Merchant Name': 'Café Résumé 🌮',
            'Amount': '€45.50',
            'Category': 'Food'
        }

        result = parser.parse_transaction(row, 1)
        assert result is not None
        assert result.normalized_merchant is not None

    def test_empty_file_handling(self, parser, tmp_path):
        """Test handling of empty CSV file."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("Date,Merchant Name,Amount,Category\n")

        clean_transactions = parser.parse_file(str(empty_csv))
        assert len(clean_transactions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
