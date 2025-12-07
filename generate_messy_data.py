"""
Generate chaotic financial transaction data for testing the parser.
This creates edge cases that a robust parser must handle.
"""

import csv
from pathlib import Path


def generate_messy_transactions():
    """Generate intentionally messy financial data with multiple edge cases."""

    transactions = [
        # Standard formats
        ["2023-01-15", "AMAZON.COM", "$45.99", "Shopping"],
        ["2023-01-16", "Starbucks", "5.50", "Food"],

        # Date format variations
        ["Jan 17th, 2023", "UBER *TRIP", "$12.30", "Transportation"],
        ["01/18/2023", "Uber Technologies", "USD 15.75", "Transportation"],
        ["2023.01.19", "UBER EATS", "  $28.50  ", "Food"],
        ["18-Jan-23", "uber", "22.00", "Transportation"],

        # Merchant name variations (same company, different formats)
        ["2023-01-20", "AMZN Mktp US*2X3Y4Z", "$67.89", "Shopping"],
        ["2023-01-21", "Amazon Web Services", "0.99", "Technology"],
        ["2023-01-22", "AMZ*Amazon.com", "$ 123.45", "Shopping"],

        # Amount edge cases
        ["2023-01-23", "Whole Foods", "-10.00", "Food"],  # Refund
        ["2023-01-24", "Target", "€45.50", "Shopping"],  # Euro symbol
        ["2023-01-25", "Shell Gas", "  52.30  ", "Transportation"],
        ["2023-01-26", "McDonald's", "$3.99 ", "Food"],
        ["2023-01-27", "Apple.com/bill", "99.99 USD", "Technology"],

        # Special characters and unicode
        ["2023-01-28", "Café Résumé", "$18.75", "Food"],
        ["2023-01-29", "José's Tacos 🌮", "25.50", "Food"],
        ["2023-01-30", "H&M Store #4512", "£67.80", "Shopping"],

        # Empty and malformed entries
        ["2023-01-31", "", "34.56", "Unknown"],
        ["2023-02-01", "Netflix", "", "Entertainment"],
        ["", "Spotify", "9.99", "Entertainment"],

        # Month boundary cases
        ["2023-01-31", "CVS Pharmacy", "$45.67", "Health"],
        ["2023-02-01", "CVS/pharmacy", "12.34", "Health"],

        # Inconsistent spacing and casing
        ["2023-02-02", "  WAL-MART  ", "  $ 156.78  ", "Shopping"],
        ["2023-02-03", "walmart.com", "89.99", "Shopping"],
        ["2023-02-04", "WALMART SUPERCENTER", "$234.56", "Shopping"],

        # Large amounts
        ["2023-02-05", "RENT PAYMENT", "$2,500.00", "Housing"],
        ["2023-02-06", "Salary Deposit", "-$5,000.00", "Income"],

        # Odd date formats
        ["02-07-2023", "Delta Airlines", "$450.00", "Travel"],
        ["2/8/23", "Hilton Hotels", "320.50", "Travel"],
        ["February 9, 2023", "Enterprise Rent-A-Car", "$180.00", "Transportation"],

        # Duplicate-looking but different
        ["2023-02-10", "Chipotle Mexican Grill", "$15.25", "Food"],
        ["2023-02-10", "CHIPOTLE 2347", "12.50", "Food"],
        ["2023-02-11", "Chipotle", "$18.00", "Food"],

        # Missing category
        ["2023-02-12", "Unknown Merchant ABC", "67.89", ""],

        # Very long merchant name
        ["2023-02-13", "THE REALLY LONG NAME MERCHANT STORE LOCATION 4512 TRANSACTION ID 889XYZ", "$45.00", "Shopping"],

        # Special characters in amounts
        ["2023-02-14", "Restaurant Deluxe", "($50.00)", "Food"],  # Negative in parens
        ["2023-02-15", "Gym Membership", "45.00-", "Health"],  # Negative trailing
    ]

    return transactions


def save_to_csv(filename="data/raw/transactions_messy.csv"):
    """Save messy transactions to CSV file."""
    transactions = generate_messy_transactions()

    # Create directory if it doesn't exist
    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header with inconsistent casing and spacing
        writer.writerow([" Date ", "Merchant Name", "Amount  ", "Category"])
        writer.writerows(transactions)

    print(f"✅ Generated {len(transactions)} messy transactions in '{filename}'")
    print(f"📊 Edge cases included:")
    print(f"   - Multiple date formats (ISO, US, EU, natural language)")
    print(f"   - Merchant name variations (UBER, Uber, uber)")
    print(f"   - Currency symbols ($, €, £, USD)")
    print(f"   - Negative amounts (refunds)")
    print(f"   - Unicode characters (café, emojis)")
    print(f"   - Empty/missing values")
    print(f"   - Whitespace inconsistencies")
    print(f"   - Month boundary dates")
    print(f"   - Large amounts with commas")


if __name__ == "__main__":
    save_to_csv()
