"""
Core financial transaction parser.
Orchestrates the normalization pipeline with robust error handling.
"""

import pandas as pd
import logging
import time
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from src.validators import RawTransaction, CleanTransaction
from src.normalizers import DateNormalizer, AmountNormalizer, MerchantNormalizer, CategoryInferencer
from src.utils import AuditLogger, setup_logging

logger = logging.getLogger(__name__)


class FinancialParser:
    """Main parser for financial transactions."""

    def __init__(self, audit_log_path: str = "logs/audit.log"):
        """Initialize parser with logging."""
        self.audit_logger = AuditLogger(audit_log_path)
        self.date_normalizer = DateNormalizer()
        self.amount_normalizer = AmountNormalizer()
        self.merchant_normalizer = MerchantNormalizer()
        self.category_inferencer = CategoryInferencer()

        self.stats = {
            'total_rows': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'normalizations': 0,
            'errors': [],
            'performance': {}  # NEW: Performance metrics
        }

    def load_csv(self, filepath: str) -> pd.DataFrame:
        """
        Load CSV file with robust error handling.

        Handles:
        - Different encodings
        - Missing headers
        - Extra whitespace
        """
        load_start = time.time()

        try:
            # Try UTF-8 first
            df = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 for special characters
            logger.warning(f"UTF-8 decode failed, trying latin-1 encoding")
            df = pd.read_csv(filepath, encoding='latin-1')

        # Clean column names (strip whitespace, lowercase)
        df.columns = df.columns.str.strip()

        load_time = time.time() - load_start
        self.stats['performance']['csv_load_time'] = load_time

        # Log data quality metrics
        self.stats['total_rows'] = len(df)
        self.audit_logger.log_event('csv_loaded', {
            'filepath': filepath,
            'rows': len(df),
            'columns': list(df.columns),
            'load_time_seconds': round(load_time, 3)
        })

        logger.info(f"Loaded {len(df)} transactions from '{filepath}' in {load_time:.3f}s")
        return df

    def parse_transaction(self, row: Dict[str, Any], row_num: int) -> CleanTransaction | None:
        """
        Parse a single transaction row with comprehensive error handling.

        Returns:
            CleanTransaction object or None if parsing fails
        """
        try:
            # Step 1: Validate raw input
            raw = RawTransaction(
                date=str(row.get('Date', '')),
                merchant_name=str(row.get('Merchant', row.get('Merchant Name', ''))),
                amount=str(row.get('Amount', '')),
                category=str(row.get('Category', ''))
            )

            # Step 2: Normalize date
            normalized_date = self.date_normalizer.normalize(raw.date)
            if not normalized_date:
                raise ValueError(f"Could not parse date: {raw.date}")

            # Step 3: Normalize amount
            amount, currency, is_negative = self.amount_normalizer.normalize(raw.amount)
            if amount is None:
                raise ValueError(f"Could not parse amount: {raw.amount}")

            # Step 4: Normalize merchant name
            normalized_merchant = self.merchant_normalizer.normalize(raw.merchant_name)
            self.stats['normalizations'] += 1

            # Step 5: Infer category if missing
            category = self.category_inferencer.infer(
                normalized_merchant,
                raw.category
            )

            # Step 6: Create clean transaction
            clean = CleanTransaction(
                date=normalized_date,
                merchant_name=raw.merchant_name,
                normalized_merchant=normalized_merchant,
                amount=amount,
                currency=currency,
                category=category,
                is_refund=is_negative
            )

            self.stats['successful_parses'] += 1

            # Audit log
            self.audit_logger.log_event('transaction_parsed', {
                'row': row_num,
                'original_merchant': raw.merchant_name,
                'normalized_merchant': normalized_merchant,
                'amount': float(amount),
                'date': normalized_date.isoformat()
            })

            return clean

        except Exception as e:
            self.stats['failed_parses'] += 1
            error_msg = f"Row {row_num}: {str(e)}"
            self.stats['errors'].append(error_msg)

            logger.error(f"Failed to parse transaction: {error_msg}")
            self.audit_logger.log_event('parse_error', {
                'row': row_num,
                'error': str(e),
                'data': row
            })

            return None

    def parse_file(self, input_path: str, output_path: str = None) -> List[CleanTransaction]:
        """
        Parse entire CSV file and optionally save cleaned output.

        Args:
            input_path: Path to messy CSV file
            output_path: Optional path to save cleaned CSV

        Returns:
            List of successfully parsed transactions
        """
        # Start overall timer
        total_start_time = time.time()

        logger.info(f"Starting parse of '{input_path}'")
        self.audit_logger.log_event('parse_started', {
            'input_file': input_path,
            'timestamp': datetime.now().isoformat()
        })

        # Load CSV (timed internally)
        df = self.load_csv(input_path)

        # Parse each transaction (timed)
        parse_start_time = time.time()
        clean_transactions = []
        for idx, row in df.iterrows():
            clean_txn = self.parse_transaction(row.to_dict(), idx + 2)  # +2 for header row
            if clean_txn:
                clean_transactions.append(clean_txn)

        parse_time = time.time() - parse_start_time
        self.stats['performance']['parse_time'] = parse_time
        self.stats['performance']['transactions_per_second'] = (
            len(clean_transactions) / parse_time if parse_time > 0 else 0
        )

        # Calculate total time
        total_time = time.time() - total_start_time
        self.stats['performance']['total_time'] = total_time

        # Log summary with performance metrics
        success_rate = (self.stats['successful_parses'] / self.stats['total_rows'] * 100) if self.stats['total_rows'] > 0 else 0

        logger.info(
            f"Parse complete: {self.stats['successful_parses']}/{self.stats['total_rows']} successful ({success_rate:.1f}%)")
        logger.info(f"⏱️  Performance: {total_time:.3f}s total ({self.stats['performance']['transactions_per_second']:.1f} txns/sec)")

        self.audit_logger.log_event('parse_completed', {
            'total_rows': self.stats['total_rows'],
            'successful': self.stats['successful_parses'],
            'failed': self.stats['failed_parses'],
            'success_rate': f"{success_rate:.1f}%",
            'normalizations': self.stats['normalizations'],
            'performance': {
                'csv_load_time': round(self.stats['performance']['csv_load_time'], 3),
                'parse_time': round(parse_time, 3),
                'total_time': round(total_time, 3),
                'transactions_per_second': round(self.stats['performance']['transactions_per_second'], 1)
            }
        })

        # Save cleaned data if output path provided (timed)
        if output_path and clean_transactions:
            save_start_time = time.time()
            self.save_clean_data(clean_transactions, output_path)
            save_time = time.time() - save_start_time
            self.stats['performance']['save_time'] = save_time
            logger.info(f"💾 Saved output in {save_time:.3f}s")

        return clean_transactions

    def save_clean_data(self, transactions: List[CleanTransaction], output_path: str):
        """Save cleaned transactions to CSV."""
        # Convert to dict format
        data = [txn.model_dump() for txn in transactions]

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Reorder columns for readability
        column_order = [
            'date', 'normalized_merchant', 'merchant_name',
            'amount', 'currency', 'category',
            'is_refund', 'is_anomaly', 'anomaly_reason'
        ]
        df = df[column_order]

        # Save
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

        logger.info(f"Saved {len(transactions)} clean transactions to '{output_path}'")
        self.audit_logger.log_event('clean_data_saved', {
            'output_file': output_path,
            'transaction_count': len(transactions)
        })

    def get_stats(self) -> Dict[str, Any]:
        """Return parsing statistics including performance metrics."""
        return self.stats

    def print_performance_summary(self):
        """Print a formatted performance summary."""
        perf = self.stats['performance']

        print("\n" + "=" * 70)
        print("⏱️  PERFORMANCE SUMMARY")
        print("=" * 70)
        print(f"CSV Loading:        {perf.get('csv_load_time', 0):.3f}s")
        print(f"Transaction Parse:  {perf.get('parse_time', 0):.3f}s")
        print(f"Data Saving:        {perf.get('save_time', 0):.3f}s")
        print(f"Total Time:         {perf.get('total_time', 0):.3f}s")
        print(f"Throughput:         {perf.get('transactions_per_second', 0):.1f} transactions/sec")
        print("=" * 70)