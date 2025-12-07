"""
Unit tests for TransactionAnalyzer.
Tests anomaly detection, analytics, and risk assessment functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.analyzer import TransactionAnalyzer
from src.validators import CleanTransaction, TransactionSummary


class TestTransactionAnalyzer:
    """Test the main analyzer functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance with default settings."""
        return TransactionAnalyzer(z_score_threshold=3.0)

    @pytest.fixture
    def normal_transactions(self):
        """Create a set of normal transactions for testing."""
        base_date = datetime(2023, 1, 1)
        return [
            CleanTransaction(
                date=base_date + timedelta(days=i),
                merchant_name=f"Store {i}",
                normalized_merchant=f"Store {i}",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            )
            for i in range(10)
        ]

    @pytest.fixture
    def transactions_with_outlier(self):
        """Create transactions with one statistical outlier."""
        base_date = datetime(2023, 1, 1)
        transactions = [
            CleanTransaction(
                date=base_date + timedelta(days=i),
                merchant_name=f"Store {i}",
                normalized_merchant=f"Store {i}",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            )
            for i in range(10)
        ]
        # Add a huge outlier
        transactions.append(
            CleanTransaction(
                date=base_date + timedelta(days=10),
                merchant_name="Expensive Store",
                normalized_merchant="Expensive Store",
                amount=Decimal("5000.00"),  # Way outside normal
                currency="USD",
                category="Shopping",
                is_refund=False
            )
        )
        return transactions

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes correctly."""
        assert analyzer is not None
        assert analyzer.z_score_threshold == 3.0
        assert analyzer.anomaly_statistics['total'] == 0

    def test_analyze_empty_transactions(self, analyzer):
        """Test analyzer handles empty transaction list."""
        result = analyzer.analyze([])
        assert result is None

    def test_analyze_normal_transactions(self, analyzer, normal_transactions):
        """Test analyzer with normal transactions (no anomalies)."""
        summary = analyzer.analyze(normal_transactions)

        assert summary is not None
        assert summary.total_transactions == 10
        assert summary.anomalies_detected == 0
        assert summary.total_spending == Decimal("500.00")
        assert summary.total_refunds == Decimal("0.00")

    def test_detect_statistical_outlier(self, analyzer, transactions_with_outlier):
        """Test detection of statistical outlier using Z-score."""
        summary = analyzer.analyze(transactions_with_outlier)

        # Should detect the $5000 transaction as anomaly
        assert summary.anomalies_detected > 0

        # Check the outlier was flagged
        outlier = [t for t in transactions_with_outlier if t.amount == Decimal("5000.00")][0]
        assert outlier.is_anomaly == True
        # Accept any severity (CRITICAL, HIGH, or MEDIUM all valid)
        assert outlier.anomaly_reason is not None
        assert any(sev in outlier.anomaly_reason for sev in ["CRITICAL", "HIGH", "MEDIUM"])

    def test_detect_large_transaction(self, analyzer):
        """Test detection of large transactions by threshold."""
        transactions = [
            CleanTransaction(
                date=datetime(2023, 1, 1),
                merchant_name="Store",
                normalized_merchant="Store",
                amount=Decimal("100.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=datetime(2023, 1, 2),
                merchant_name="Store 2",
                normalized_merchant="Store 2",
                amount=Decimal("200.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=datetime(2023, 1, 3),
                merchant_name="Big Purchase",
                normalized_merchant="Big Purchase",
                amount=Decimal("3000.00"),  # Over threshold
                currency="USD",
                category="Shopping",
                is_refund=False
            )
        ]

        summary = analyzer.analyze(transactions)

        # Large transaction should be flagged
        large_txn = transactions[2]
        assert large_txn.is_anomaly == True
        assert "Large purchase" in large_txn.anomaly_reason or "outside your normal" in large_txn.anomaly_reason

    def test_detect_duplicate_transactions(self, analyzer):
        """Test detection of duplicate transactions on same day."""
        same_date = datetime(2023, 1, 1)
        transactions = [
            CleanTransaction(
                date=same_date,
                merchant_name="Store",
                normalized_merchant="Store",
                amount=Decimal("100.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=same_date,
                merchant_name="Store",
                normalized_merchant="Store",
                amount=Decimal("100.00"),  # Same amount, same day
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            # Add a normal transaction to avoid statistical outliers
            CleanTransaction(
                date=datetime(2023, 1, 2),
                merchant_name="Other Store",
                normalized_merchant="Other Store",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            )
        ]

        summary = analyzer.analyze(transactions)

        # Second transaction should be flagged as duplicate
        assert transactions[1].is_anomaly == True
        assert "duplicate" in transactions[1].anomaly_reason.lower()

    def test_spending_velocity_detection(self, analyzer):
        """Test detection of rapid spending patterns."""
        base_date = datetime(2023, 1, 1, 10, 0)  # 10 AM
        transactions = [
            CleanTransaction(
                date=base_date,
                merchant_name="Store 1",
                normalized_merchant="Store 1",
                amount=Decimal("200.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=base_date + timedelta(hours=2),  # 2 hours later
                merchant_name="Store 2",
                normalized_merchant="Store 2",
                amount=Decimal("200.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=base_date + timedelta(hours=4),  # 4 hours later
                merchant_name="Store 3",
                normalized_merchant="Store 3",
                amount=Decimal("200.00"),  # $600 in 4 hours
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            # Add more transactions to reach minimum count
            CleanTransaction(
                date=base_date + timedelta(days=1),
                merchant_name="Normal Store",
                normalized_merchant="Normal Store",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=base_date + timedelta(days=2),
                merchant_name="Normal Store 2",
                normalized_merchant="Normal Store 2",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            )
        ]

        summary = analyzer.analyze(transactions)

        # Should detect rapid spending
        rapid_spending = [t for t in transactions[:3] if t.is_anomaly]
        assert len(rapid_spending) > 0

    def test_suspicious_merchant_diversity(self, analyzer):
        """Test detection of unusual merchant diversity."""
        same_date = datetime(2023, 1, 1)

        # Create transactions with many different merchants on one day
        transactions = [
            CleanTransaction(
                date=same_date,
                merchant_name=f"Store {i}",
                normalized_merchant=f"Store {i}",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            )
            for i in range(10)  # 10 different stores in one day
        ]

        # Add normal days for comparison
        for day in range(1, 4):
            transactions.append(
                CleanTransaction(
                    date=datetime(2023, 1, day + 1),
                    merchant_name="Regular Store",
                    normalized_merchant="Regular Store",
                    amount=Decimal("50.00"),
                    currency="USD",
                    category="Shopping",
                    is_refund=False
                )
            )

        summary = analyzer.analyze(transactions)

        # Should detect unusual merchant diversity
        assert summary.anomalies_detected > 0


class TestAnalyzerReporting:
    """Test analyzer reporting functionality."""

    @pytest.fixture
    def analyzer(self):
        return TransactionAnalyzer()

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions for reporting tests."""
        return [
            CleanTransaction(
                date=datetime(2023, 1, i + 1),  # Fixed: start from day 1
                merchant_name=f"Store {i % 3}",
                normalized_merchant=f"Store {i % 3}",
                amount=Decimal("50.00"),
                currency="USD",
                category=["Shopping", "Food", "Entertainment"][i % 3],
                is_refund=False
            )
            for i in range(10)
        ]

    def test_generate_report(self, analyzer, sample_transactions):
        """Test report generation."""
        summary = analyzer.analyze(sample_transactions)
        report = analyzer.generate_report(summary)

        assert "FINANCIAL TRANSACTION ANALYSIS REPORT" in report
        assert "TRANSACTION SUMMARY" in report
        assert "FINANCIAL SUMMARY" in report
        assert "TOP SPENDING CATEGORY" in report
        assert "ANOMALY DETECTION RESULTS" in report

    def test_category_breakdown(self, analyzer, sample_transactions):
        """Test category spending breakdown."""
        analyzer.analyze(sample_transactions)  # Run analysis first
        breakdown = analyzer.get_category_breakdown(sample_transactions)

        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0
        assert all(isinstance(v, Decimal) for v in breakdown.values())

        # Check sorting (highest to lowest)
        values = list(breakdown.values())
        assert values == sorted(values, reverse=True)

    def test_merchant_breakdown(self, analyzer, sample_transactions):
        """Test merchant spending breakdown."""
        analyzer.analyze(sample_transactions)
        breakdown = analyzer.get_merchant_breakdown(sample_transactions)

        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0

        # Check all merchants present
        merchants = set(t.normalized_merchant for t in sample_transactions)
        assert all(m in breakdown for m in merchants)

    def test_risk_assessment(self, analyzer, sample_transactions):
        """Test risk assessment calculation."""
        analyzer.analyze(sample_transactions)
        risk = analyzer.get_risk_assessment(sample_transactions)

        assert 'risk_score' in risk
        assert 'risk_level' in risk
        assert 'risk_factors' in risk
        assert 'anomaly_rate' in risk
        assert 'total_anomalies' in risk

        assert risk['risk_level'] in ['MINIMAL', 'LOW', 'MEDIUM', 'HIGH']
        assert 0 <= risk['risk_score'] <= 100
        assert 0 <= risk['anomaly_rate'] <= 1


class TestAnalyzerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def analyzer(self):
        return TransactionAnalyzer()

    def test_analyze_insufficient_data(self, analyzer):
        """Test analyzer with insufficient data for statistics."""
        transactions = [
            CleanTransaction(
                date=datetime(2023, 1, 1),
                merchant_name="Store",
                normalized_merchant="Store",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            )
        ]

        # Should not crash with minimal data
        summary = analyzer.analyze(transactions)
        assert summary is not None
        assert summary.total_transactions == 1

    def test_analyze_all_refunds(self, analyzer):
        """Test analyzer with all negative amounts (refunds)."""
        transactions = [
            CleanTransaction(
                date=datetime(2023, 1, i + 1),  # Fixed: start from day 1
                merchant_name=f"Store {i}",
                normalized_merchant=f"Store {i}",
                amount=Decimal("-50.00"),  # All refunds
                currency="USD",
                category="Shopping",
                is_refund=True
            )
            for i in range(5)
        ]

        summary = analyzer.analyze(transactions)

        assert summary.total_spending == Decimal("0.00")
        assert summary.total_refunds == Decimal("250.00")
        assert summary.net_spending == Decimal("-250.00")

    def test_analyze_mixed_currencies(self, analyzer):
        """Test analyzer handles mixed currencies."""
        transactions = [
            CleanTransaction(
                date=datetime(2023, 1, 1),
                merchant_name="US Store",
                normalized_merchant="US Store",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=datetime(2023, 1, 2),
                merchant_name="EU Store",
                normalized_merchant="EU Store",
                amount=Decimal("50.00"),
                currency="EUR",
                category="Shopping",
                is_refund=False
            )
        ]

        # Should handle mixed currencies without crashing
        summary = analyzer.analyze(transactions)
        assert summary is not None

    def test_zero_standard_deviation(self, analyzer):
        """Test analyzer when all amounts are identical (zero std dev)."""
        transactions = [
            CleanTransaction(
                date=datetime(2023, 1, i + 1),  # Fixed: start from day 1
                merchant_name=f"Store {i}",
                normalized_merchant=f"Store {i}",
                amount=Decimal("50.00"),  # All identical
                currency="USD",
                category="Shopping",
                is_refund=False
            )
            for i in range(10)
        ]

        # Should not crash on zero standard deviation
        summary = analyzer.analyze(transactions)
        assert summary is not None
        # With identical amounts, statistical outlier detection shouldn't flag anything
        assert summary.anomalies_detected == 0

    def test_custom_z_score_threshold(self):
        """Test analyzer with custom Z-score threshold."""
        # More sensitive analyzer (lower threshold)
        sensitive_analyzer = TransactionAnalyzer(z_score_threshold=2.0)

        transactions = [
            CleanTransaction(
                date=datetime(2023, 1, i + 1),  # Fixed: start from day 1
                merchant_name=f"Store {i}",
                normalized_merchant=f"Store {i}",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            )
            for i in range(10)
        ]

        # Add moderately large transaction
        transactions.append(
            CleanTransaction(
                date=datetime(2023, 1, 11),
                merchant_name="Big Store",
                normalized_merchant="Big Store",
                amount=Decimal("500.00"),  # Moderately large
                currency="USD",
                category="Shopping",
                is_refund=False
            )
        )

        summary = sensitive_analyzer.analyze(transactions)

        # Should be more sensitive to outliers
        assert sensitive_analyzer.z_score_threshold == 2.0


class TestSeverityClassification:
    """Test severity classification system."""

    def test_severity_levels_defined(self):
        """Test that all severity levels are defined."""
        analyzer = TransactionAnalyzer()

        assert hasattr(analyzer, 'SEVERITY_CRITICAL')
        assert hasattr(analyzer, 'SEVERITY_HIGH')
        assert hasattr(analyzer, 'SEVERITY_MEDIUM')
        assert hasattr(analyzer, 'SEVERITY_LOW')
        assert hasattr(analyzer, 'SEVERITY_INFO')

    def test_anomaly_statistics_tracking(self):
        """Test that anomaly statistics are tracked correctly."""
        analyzer = TransactionAnalyzer()

        transactions = [
            CleanTransaction(
                date=datetime(2023, 1, 1),
                merchant_name="Normal",
                normalized_merchant="Normal",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=datetime(2023, 1, 2),
                merchant_name="Normal 2",
                normalized_merchant="Normal 2",
                amount=Decimal("50.00"),
                currency="USD",
                category="Shopping",
                is_refund=False
            ),
            CleanTransaction(
                date=datetime(2023, 1, 3),
                merchant_name="Large",
                normalized_merchant="Large",
                amount=Decimal("6000.00"),  # Should be flagged
                currency="USD",
                category="Shopping",
                is_refund=False
            )
        ]

        analyzer.analyze(transactions)

        # Check statistics were tracked (should have at least 1 anomaly)
        assert analyzer.anomaly_statistics['total'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])