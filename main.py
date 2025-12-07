"""
Main entry point for financial transaction parser.
Demonstrates end-to-end parsing with analytics.
"""

import sys
from pathlib import Path

from src.parser import FinancialParser
from src.analyzer import TransactionAnalyzer
from src.utils import setup_logging

def main():
    """Run the complete parsing and analysis pipeline."""
    # Setup logging
    setup_logging(log_level="INFO")

    # Get input/output paths from command line or use defaults
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = "data/raw/transactions_messy.csv"
        output_file = "data/processed/transactions_clean.csv"

    print("=" * 70)
    print("Financial Transaction Parser - Palo Alto Networks Interview")
    print("=" * 70)
    print(f"📥 Input:  {input_file}")
    print(f"📤 Output: {output_file}")
    print()

    # Step 1: Parse transactions
    print("🔄 Parsing transactions...")
    parser = FinancialParser()

    try:
        clean_transactions = parser.parse_file(input_file, output_file)

        if not clean_transactions:
            print("❌ No transactions were successfully parsed!")
            sys.exit(1)

        # Display parsing stats
        stats = parser.get_stats()
        success_rate = (stats['successful_parses'] / stats['total_rows'] * 100) if stats['total_rows'] > 0 else 0

        print(f"\n✅ Parsing complete!")
        print(f"   Total rows: {stats['total_rows']}")
        print(f"   Successful: {stats['successful_parses']} ({success_rate:.1f}%)")
        print(f"   Failed: {stats['failed_parses']}")

        if stats['errors']:
            print(f"\n⚠️  Errors encountered during parsing:")
            for error in stats['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(stats['errors']) > 5:
                print(f"   ... and {len(stats['errors']) - 5} more errors")

        # Display performance metrics
        parser.print_performance_summary()

        # Step 2: Run analytics
        print("\n📊 Running analytics...")
        analyzer = TransactionAnalyzer()
        summary = analyzer.analyze(clean_transactions)

        # Generate and display report
        report = analyzer.generate_report(summary)
        print(report)

        # Category breakdown
        print("\nSPENDING BY CATEGORY")
        print("-" * 60)
        categories = analyzer.get_category_breakdown(clean_transactions)
        for category, amount in list(categories.items())[:5]:  # Top 5
            print(f"{category:30s} ${amount:>15,.2f}")

        print()

        # Merchant breakdown
        print("\nTOP MERCHANTS")
        print("-" * 60)
        merchants = analyzer.get_merchant_breakdown(clean_transactions)
        for merchant, amount in list(merchants.items())[:5]:  # Top 5
            print(f"{merchant:30s} ${amount:>15,.2f}")

        print()

        # Risk assessment
        risk = analyzer.get_risk_assessment(clean_transactions)
        risk_emoji = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "🔍", "MINIMAL": "✅"}
        print(f"\n{risk_emoji.get(risk['risk_level'], '📊')} RISK ASSESSMENT: {risk['risk_level']}")
        print(f"   Risk Score: {risk['risk_score']}/100")
        print(f"   Anomaly Rate: {risk['anomaly_rate']*100:.1f}%")
        if risk['risk_factors']:
            print(f"   Factors:")
            for factor in risk['risk_factors']:
                print(f"     - {factor}")

        print()

        # Final output information
        print(f"💾 Clean data saved to: {output_file}")
        print(f"📋 Audit log saved to: logs/audit.log")
        print(f"📝 Application log saved to: logs/parser.log")

        print()
        print("=" * 70)
        print("Financial Transaction Parser - Complete")
        print("=" * 70)

    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found!")
        print(f"   Please check the file path and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()