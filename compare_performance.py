#!/usr/bin/env python3
"""
Performance comparison script.
Benchmarks parser performance on both synthetic and real-world datasets.
"""

from src.parser import FinancialParser
from src.analyzer import TransactionAnalyzer
from src.utils import setup_logging
import time

def benchmark_dataset(name, input_file, output_file):
    """
    Benchmark parser performance on a single dataset.

    Returns:
        dict with performance metrics
    """
    print(f"\n{'='*70}")
    print(f" BENCHMARKING: {name}")
    print(f"{'='*70}")

    parser = FinancialParser()

    try:
        # Parse with timing
        start_time = time.time()
        clean_transactions = parser.parse_file(input_file, output_file)
        total_time = time.time() - start_time

        # Get stats
        stats = parser.get_stats()

        # Analyze
        analyzer = TransactionAnalyzer()
        summary = analyzer.analyze(clean_transactions)

        # Gather metrics
        metrics = {
            'name': name,
            'input_file': input_file,
            'total_transactions': stats['total_rows'],
            'successful_parses': stats['successful_parses'],
            'failed_parses': stats['failed_parses'],
            'success_rate': (stats['successful_parses'] / stats['total_rows'] * 100) if stats['total_rows'] > 0 else 0,
            'csv_load_time': stats['performance'].get('csv_load_time', 0),
            'parse_time': stats['performance'].get('parse_time', 0),
            'save_time': stats['performance'].get('save_time', 0),
            'total_time': stats['performance'].get('total_time', 0),
            'transactions_per_second': stats['performance'].get('transactions_per_second', 0),
            'unique_merchants': summary.merchants_normalized,
            'total_volume': float(summary.total_spending),
            'anomalies_detected': summary.anomalies_detected,
            'anomaly_rate': (summary.anomalies_detected / len(clean_transactions) * 100) if clean_transactions else 0,
            'avg_transaction': float(summary.total_spending / max(1, summary.total_transactions))
        }

        # Display metrics
        print(f"\n RESULTS:")
        print(f"   Transactions:        {metrics['total_transactions']:,}")
        print(f"   Success Rate:        {metrics['success_rate']:.1f}%")
        print(f"   Unique Merchants:    {metrics['unique_merchants']:,}")
        print(f"   Transaction Volume:  ${metrics['total_volume']:,.2f}")
        print(f"   Avg Transaction:     ${metrics['avg_transaction']:,.2f}")
        print(f"   Anomaly Rate:        {metrics['anomaly_rate']:.1f}%")

        print(f"\n  PERFORMANCE:")
        print(f"   CSV Load:            {metrics['csv_load_time']:.3f}s")
        print(f"   Parse Time:          {metrics['parse_time']:.3f}s")
        print(f"   Save Time:           {metrics['save_time']:.3f}s")
        print(f"   Total Time:          {metrics['total_time']:.3f}s")
        print(f"   Throughput:          {metrics['transactions_per_second']:.1f} txns/sec")

        return metrics

    except FileNotFoundError:
        print(f" File not found: {input_file}")
        return None
    except Exception as e:
        print(f" Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def compare_datasets(results):
    """
    Compare performance between datasets.

    Args:
        results: list of metric dictionaries
    """
    if len(results) < 2:
        print("\n  Need at least 2 datasets to compare")
        return

    print(f"\n{'='*70}")
    print(" PERFORMANCE COMPARISON")
    print(f"{'='*70}")

    # Create comparison table
    print(f"\n{'Metric':<30} {'Retail':<20} {'Financial':<20} {'Difference':<15}")
    print("-" * 85)

    retail = results[0]
    financial = results[1]

    # Transaction count
    print(f"{'Transactions':<30} {retail['total_transactions']:<20,} {financial['total_transactions']:<20,} {financial['total_transactions'] - retail['total_transactions']:>+14,}")

    # Success rate
    print(f"{'Success Rate':<30} {retail['success_rate']:<19.1f}% {financial['success_rate']:<19.1f}% {financial['success_rate'] - retail['success_rate']:>+13.1f}%")

    # Unique merchants
    print(f"{'Unique Merchants':<30} {retail['unique_merchants']:<20,} {financial['unique_merchants']:<20,} {financial['unique_merchants'] - retail['unique_merchants']:>+14,}")

    # Transaction volume
    print(f"{'Transaction Volume':<30} ${retail['total_volume']:<19,.2f} ${financial['total_volume']:<19,.2f} ${financial['total_volume'] - retail['total_volume']:>+13,.2f}")

    # Avg transaction
    print(f"{'Avg Transaction':<30} ${retail['avg_transaction']:<19,.2f} ${financial['avg_transaction']:<19,.2f} ${financial['avg_transaction'] - retail['avg_transaction']:>+13,.2f}")

    # Anomaly rate
    print(f"{'Anomaly Rate':<30} {retail['anomaly_rate']:<19.1f}% {financial['anomaly_rate']:<19.1f}% {financial['anomaly_rate'] - retail['anomaly_rate']:>+13.1f}%")

    print()
    print("-" * 85)
    print("TIMING COMPARISON (seconds)")
    print("-" * 85)

    # Parse time
    speedup = retail['parse_time'] / financial['parse_time'] if financial['parse_time'] > 0 else 0
    print(f"{'Parse Time':<30} {retail['parse_time']:<19.3f}s {financial['parse_time']:<19.3f}s {speedup:>13.2f}x faster")

    # Total time
    speedup_total = retail['total_time'] / financial['total_time'] if financial['total_time'] > 0 else 0
    print(f"{'Total Time':<30} {retail['total_time']:<19.3f}s {financial['total_time']:<19.3f}s {speedup_total:>13.2f}x faster")

    # Throughput
    print(f"{'Throughput':<30} {retail['transactions_per_second']:<19.1f} txns/s {financial['transactions_per_second']:<19.1f} txns/s {financial['transactions_per_second'] / retail['transactions_per_second']:>13.2f}x faster")

    print()
    print("=" * 85)
    print("\n KEY INSIGHTS:")

    # Adaptive threshold detection
    if financial['avg_transaction'] > 50000:
        print("   Financial dataset auto-detected (avg txn >$50K)")
        print("   Applied enterprise thresholds ($500K/$200K/$100K)")
    else:
        print("   Retail dataset auto-detected (avg txn <$50K)")
        print("   Applied retail thresholds ($5K/$2K/$1K)")

    # Scale comparison
    scale_factor = financial['total_transactions'] / retail['total_transactions']
    print(f"\n   Dataset scale: {scale_factor:.0f}x larger (financial vs retail)")

    # Performance scaling
    if speedup_total < 0.5:
        print(f"   Parser scales efficiently: {speedup_total:.2f}x time for {scale_factor:.0f}x data")

    # Merchant tracking
    merchant_ratio = financial['unique_merchants'] / retail['unique_merchants']
    print(f"   Merchant tracking: {merchant_ratio:.0f}x more unique accounts in financial data")

    print()

def main():
    """Run performance comparison."""
    # Setup logging
    setup_logging(log_level="WARNING")  # Reduce noise for benchmarking

    print("=" * 70)
    print("⚡ FINANCIAL PARSER PERFORMANCE BENCHMARK")
    print("=" * 70)
    print("\nComparing parser performance across dataset types:")
    print("  1. Retail (Synthetic) - Small scale, edge cases")
    print("  2. Financial (Kaggle)  - Enterprise scale, real-world")

    results = []

    # Benchmark 1: Synthetic retail data
    result1 = benchmark_dataset(
        "Retail (Synthetic)",
        "data/raw/transactions_messy.csv",
        "data/processed/benchmark_retail.csv"
    )
    if result1:
        results.append(result1)

    # Benchmark 2: Kaggle financial data
    result2 = benchmark_dataset(
        "Financial (Kaggle)",
        "data/raw/kaggle_converted.csv",
        "data/processed/benchmark_financial.csv"
    )
    if result2:
        results.append(result2)

    # Compare results
    if len(results) >= 2:
        compare_datasets(results)

    print("\n" + "=" * 70)
    print(" BENCHMARK COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()