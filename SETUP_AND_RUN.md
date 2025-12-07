# Quick Setup & Run Guide

This guide gets you from zero to running in under 5 minutes.

## Fast Track (Copy-Paste Ready)

```bash
# 1. Install dependencies
pip install pandas pydantic python-dateutil rapidfuzz pytest pytest-cov

# 2. Create directory structure (if not already created)
mkdir -p data/raw data/processed logs

# 3. Generate test data
python generate_messy_data.py

# 4. Run the parser
python main.py

# 5. Run tests
pytest tests/ -v
```

## Full Setup Instructions

### Step 1: Environment Setup

```bash
# Optional: Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
python -c "import pandas, pydantic, dateutil, rapidfuzz; print('✅ All dependencies installed')"
```

### Step 3: Generate Test Data

```bash
python generate_messy_data.py
```

**Output:**
```
Generated 40 messy transactions in 'transactions_messy.csv'
Edge cases included:
   - Multiple date formats (ISO, US, EU, natural language)
   - Merchant name variations (UBER, Uber, uber)
   - Currency symbols ($, €, £, USD)
   - Negative amounts (refunds)
   - Unicode characters (café, emojis)
   - Empty/missing values
   - Whitespace inconsistencies
   - Month boundary dates
   - Large amounts with commas
```

### Step 4: Run Parser

```bash
# Basic usage (uses defaults)
python main.py

# Specify input/output files
python main.py data/raw/transactions_messy.csv data/processed/transactions_clean.csv
```

**Expected Output:**
```
Parsing transactions...

Parsing Complete!
   Total Rows:      40
   Successful:      38
   Failed:          2
   Normalizations:  38

Running analytics...

============================================================
FINANCIAL TRANSACTION ANALYSIS REPORT
============================================================

Analysis Period: 2023-01-15 to 2023-02-15

TRANSACTION SUMMARY
------------------------------------------------------------
Total Transactions:            38
Unique Merchants:              25

FINANCIAL SUMMARY
------------------------------------------------------------
Total Spending:          $8,234.56
Total Refunds:             $260.00
Net Spending:            $7,974.56

TOP SPENDING CATEGORY
------------------------------------------------------------
Category:                Shopping
Amount:                  $3,456.78

Clean data saved to: data/processed/transactions_clean.csv
Audit log saved to: logs/audit.log
Application log saved to: logs/parser.log
```

### Step 5: Run Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_normalizers.py -v
```

## Verify Everything Works

### Check Output Files

```bash
# View cleaned CSV
head -n 10 data/processed/transactions_clean.csv

# View audit log (last 5 entries)
tail -n 5 logs/audit.log

# View application log
tail -n 20 logs/parser.log
```

### Validate Data Quality

```bash
# Count transactions
wc -l data/processed/transactions_clean.csv

# Check for anomalies
grep "True" data/processed/transactions_clean.csv | wc -l

# View unique normalized merchants
cut -d',' -f2 data/processed/transactions_clean.csv | sort -u
```

## Common Use Cases

### Use Case 1: Parse Your Own Data

```bash
# 1. Prepare your CSV with these columns:
#    Date, Merchant Name, Amount, Category

# 2. Place it in data/raw/

# 3. Run parser
python main.py data/raw/your_file.csv data/processed/your_output.csv
```

### Use Case 2: Adjust Anomaly Sensitivity

Edit `main.py` and modify:
```python
# More sensitive (flag more transactions)
analyzer = TransactionAnalyzer(z_score_threshold=2.0)

# Less sensitive (flag only extreme outliers)
analyzer = TransactionAnalyzer(z_score_threshold=4.0)
```

### Use Case 3: Add Custom Merchant Mappings

Edit `src/normalizers.py`:
```python
KNOWN_MERCHANTS = {
    # Add your merchants here
    'your merchant name': 'Normalized Name',
    'acme corp': 'Acme Corporation',
    # ...
}
```

### Use Case 4: Debug Failed Parses

```bash
# Check application log for errors
grep "ERROR" logs/parser.log

# Check audit log for specific transaction
grep "row_num: 15" logs/audit.log
```

## Testing Individual Components

### Test Date Normalization
```python
from src.normalizers import DateNormalizer

# Test various formats
print(DateNormalizer.normalize("Jan 15, 2023"))
print(DateNormalizer.normalize("2023-01-15"))
print(DateNormalizer.normalize("01/15/2023"))
```

### Test Amount Parsing
```python
from src.normalizers import AmountNormalizer

# Test different amount formats
print(AmountNormalizer.normalize("$45.99"))
print(AmountNormalizer.normalize("($50.00)"))  # Negative
print(AmountNormalizer.normalize("€45.50"))    # Euro
```

### Test Merchant Normalization
```python
from src.normalizers import MerchantNormalizer

# Test fuzzy matching
print(MerchantNormalizer.normalize("UBER *TRIP"))
print(MerchantNormalizer.normalize("AMZN Mktp US*2X3Y4Z"))
print(MerchantNormalizer.normalize("walmart.com"))
```

## Understanding the Output

### Clean CSV Structure
```
date                  - ISO 8601 timestamp
normalized_merchant   - Canonical merchant name
merchant_name         - Original merchant name (preserved)
amount               - Decimal with 2 places
currency             - 3-letter currency code
category             - Inferred or provided category
is_refund            - Boolean flag for negative amounts
is_anomaly           - Boolean flag for suspicious transactions
anomaly_reason       - Explanation if flagged
```

### Audit Log Structure
```json
{
  "timestamp": "2024-12-06T14:30:45.123456",
  "event_type": "transaction_parsed",
  "data": {
    "row": 5,
    "original_merchant": "UBER *TRIP",
    "normalized_merchant": "Uber",
    "amount": 12.30,
    "date": "2023-01-17T00:00:00"
  }
}
```

## Troubleshooting

### Issue: Import errors
```bash
# Solution: Ensure all dependencies installed
pip install -r requirements.txt
```

### Issue: "File not found"
```bash
# Solution: Generate test data first
python generate_messy_data.py
```

### Issue: Tests failing
```bash
# Solution: Check Python version (requires 3.9+)
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: Unicode errors on Windows
```bash
# Solution: Set UTF-8 encoding
set PYTHONIOENCODING=utf-8
python main.py
```

### Issue: ModuleNotFoundError for 'src'
```bash
# Solution: Make sure you have __init__.py in src/ folder
touch src/__init__.py

# And run from the project root directory
cd financial-parser
python main.py
```

## Next Steps

1. **Review the code**: Start with `main.py` and follow the flow
2. **Read the tests**: `tests/test_normalizers.py` shows edge case handling
3. **Check logs**: See how the system tracks operations
4. **Experiment**: Try different input data and configurations
5. **Extend**: Add your own merchants, categories, or validation rules

## Support

If you encounter issues:
1. Check `logs/parser.log` for error details
2. Review `logs/audit.log` for transaction-level debugging
3. Run tests to verify system integrity: `pytest tests/ -v`
4. Ensure all imports use `src.` prefix (e.g., `from src.parser import ...`)

## Running All Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Open coverage report in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

**Expected test results:**
```
tests/test_normalizers.py::TestDateNormalizer::test_iso_format PASSED
tests/test_normalizers.py::TestAmountNormalizer::test_simple_dollar PASSED
tests/test_normalizers.py::TestMerchantNormalizer::test_uber_variations PASSED
tests/test_parser.py::TestFinancialParser::test_parse_transaction_success PASSED
tests/test_validators.py::TestCleanTransaction::test_valid_clean_transaction PASSED
tests/test_utils.py::TestAuditLogger::test_log_event PASSED

==================== 115 passed in 0.76s ====================
```

---
For the full technical documentation, see `README.md`.
For before/after data quality comparison, see `DATA_QUALITY_COMPARISON.md`.