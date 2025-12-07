"""
Normalization functions for dates, merchants, and amounts.
Uses industry-standard libraries to handle ambiguity efficiently.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from dateutil import parser as date_parser
from rapidfuzz import fuzz, process
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class DateNormalizer:
    """Normalize dates from various formats to ISO standard."""

    @staticmethod
    def normalize(date_str: str) -> Optional[datetime]:
        """
        Parse date from any reasonable format to datetime object.

        Handles:
        - ISO: 2023-01-15
        - US: 01/15/2023, 1/15/23
        - EU: 15-01-2023
        - Natural: Jan 15th, 2023
        - Various separators: ., -, /
        """
        if not date_str or date_str.strip() == "":
            logger.warning("Empty date string provided")
            return None

        try:
            # Dateutil.parser is very flexible + handles most formats
            parsed_date = date_parser.parse(date_str, fuzzy=True)

            # Sanity check --> reject dates too far in the past or future
            if parsed_date.year < 2000 or parsed_date.year > 2030:
                logger.warning(f"Date {date_str} parsed to suspicious year: {parsed_date.year}")
                return None

            return parsed_date

        except (ValueError, OverflowError) as e:
            logger.error(f"Failed to parse date '{date_str}': {e}")
            return None


class AmountNormalizer:
    """Normalize monetary amounts from various formats."""

    # Currency symbols
    CURRENCY_SYMBOLS = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR'
    }

    @staticmethod
    def normalize(amount_str: str) -> Tuple[Optional[Decimal], str, bool]:
        """
        Parse amount string and return (amount, currency, is_negative).

        Handles:
        - Currency symbols: $, €, £
        - Currency codes: USD, EUR
        - Negative indicators: -, (), trailing minus
        - Whitespace and commas
        - Decimal points

        Returns:
            (Decimal amount, currency code, is_negative flag)
        """
        if not amount_str or amount_str.strip() == "":
            logger.warning("Empty amount string provided")
            return None, "USD", False

        original = amount_str
        amount_str = amount_str.strip()

        # Detect currency
        currency = "USD"  # Default
        for symbol, code in AmountNormalizer.CURRENCY_SYMBOLS.items():
            if symbol in amount_str:
                currency = code
                amount_str = amount_str.replace(symbol, '')
                break

        # Check for currency codes (USD, EUR, etc.)
        currency_code_match = re.search(r'\b([A-Z]{3})\b', amount_str)
        if currency_code_match:
            currency = currency_code_match.group(1)
            amount_str = amount_str.replace(currency, '')

        # Detect negative amount (multiple formats)
        is_negative = False

        # Parentheses indicate negative: ($50.00)
        if '(' in amount_str and ')' in amount_str:
            is_negative = True
            amount_str = amount_str.replace('(', '').replace(')', '')

        # Trailing minus: 50.00-
        if amount_str.endswith('-'):
            is_negative = True
            amount_str = amount_str[:-1]

        # Leading minus: -50.00
        if amount_str.startswith('-'):
            is_negative = True
            amount_str = amount_str[1:]
        amount_str = amount_str.replace(' ', '').replace(',', '')

        # Parse to Decimal
        try:
            amount = Decimal(amount_str)

            # Apply negative if detected
            if is_negative:
                amount = -abs(amount)

            # Round to 2 decimal places
            amount = amount.quantize(Decimal('0.01'))

            return amount, currency, (amount < 0)

        except (InvalidOperation, ValueError) as e:
            logger.error(f"Failed to parse amount '{original}': {e}")
            return None, currency, False


class MerchantNormalizer:
    """Normalize merchant names using fuzzy matching."""

    # Known merchant patterns such as company name --> normalized name
    KNOWN_MERCHANTS = {
        # Amazon variations
        'amazon': 'Amazon',
        'amzn': 'Amazon',
        'amazon.com': 'Amazon',
        'amazon web services': 'Amazon AWS',
        'aws': 'Amazon AWS',

        # Uber variations
        'uber': 'Uber',
        'uber trip': 'Uber',
        'uber technologies': 'Uber',
        'uber eats': 'Uber Eats',

        # Walmart variations
        'walmart': 'Walmart',
        'wal-mart': 'Walmart',
        'walmart.com': 'Walmart',
        'walmart supercenter': 'Walmart',

        # Starbucks
        'starbucks': 'Starbucks',
        'sbux': 'Starbucks',

        # CVS
        'cvs': 'CVS Pharmacy',
        'cvs pharmacy': 'CVS Pharmacy',
        'cvs/pharmacy': 'CVS Pharmacy',

        # Chipotle
        'chipotle': 'Chipotle',
        'chipotle mexican grill': 'Chipotle',

        # Common merchants
        'target': 'Target',
        'whole foods': 'Whole Foods',
        'mcdonalds': "McDonald's",
        'apple.com': 'Apple',
        'netflix': 'Netflix',
        'spotify': 'Spotify',
        'shell': 'Shell',
        'delta': 'Delta Airlines',
        'hilton': 'Hilton Hotels',
    }

    @staticmethod
    def normalize(merchant_name: str) -> str:
        """
        Normalize merchant name using fuzzy matching against known merchants.

        Process:
        1. Clean the input (lowercase, remove special chars)
        2. Check for exact match in known merchants
        3. Use fuzzy matching if no exact match
        4. Return best match or cleaned original

        **NEW**: Handles financial account IDs (C1234567890, M9876543210)
        """
        if not merchant_name or merchant_name.strip() == "":
            return "Unknown Merchant"

        # Store original to fallback
        original = merchant_name.strip()

        # **FIX 1: Accept financial account IDs from datasets like PaySim**
        # Pattern: C or M followed by 8-10 digits (e.g., C834976624, M215391829)
        if re.match(r'^[CM]\d{8,10}$', original):
            logger.info(f"Keeping financial account ID: '{original}'")
            return original

        # Clean: lowercase, remove extra whitespace
        cleaned = ' '.join(merchant_name.lower().split())

        # Remove common transaction IDs and codes
        # Pattern: numbers, asterisks, special transaction codes
        cleaned = re.sub(r'\*[A-Z0-9]+', '', cleaned)  # *TRIP, *2X3Y4Z
        cleaned = re.sub(r'#\d+', '', cleaned)  # #4512
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Check exact match
        for pattern, normalized in MerchantNormalizer.KNOWN_MERCHANTS.items():
            if pattern in cleaned:
                logger.info(f"Normalized '{original}' -> '{normalized}' (exact match)")
                return normalized

        # Fuzzy matching against known merchants
        # Rapidfuzz for efficient fuzzy string matching
        best_match = process.extractOne(
            cleaned,
            MerchantNormalizer.KNOWN_MERCHANTS.keys(),
            scorer=fuzz.token_sort_ratio,
            score_cutoff=75  # Accept matches above 75% similarity
        )

        if best_match:
            matched_pattern, score, _ = best_match
            normalized = MerchantNormalizer.KNOWN_MERCHANTS[matched_pattern]
            logger.info(f"Normalized '{original}' -> '{normalized}' (fuzzy match: {score}%)")
            return normalized

        # No good match found --> return cleaned version of original
        # Title case --> better readability
        cleaned_title = ' '.join(word.capitalize() for word in cleaned.split())
        logger.info(f"No normalization found for '{original}', using: '{cleaned_title}'")
        return cleaned_title


class CategoryInferencer:
    """Infer transaction category from merchant name."""

    CATEGORY_KEYWORDS = {
        'Food': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonalds',
                 'chipotle', 'pizza', 'food', 'eats', 'diner', 'taco'],
        'Transportation': ['uber', 'lyft', 'taxi', 'gas', 'shell', 'exxon',
                           'parking', 'airlines', 'delta', 'united', 'rental'],
        'Shopping': ['amazon', 'walmart', 'target', 'store', 'retail',
                     'mall', 'shop', 'h&m', 'clothing'],
        'Technology': ['apple', 'microsoft', 'aws', 'google', 'adobe',
                       'software', 'cloud'],
        'Entertainment': ['netflix', 'spotify', 'hulu', 'movie', 'theater',
                          'game', 'concert'],
        'Health': ['cvs', 'pharmacy', 'walgreens', 'hospital', 'medical',
                   'doctor', 'gym', 'fitness'],
        'Travel': ['hotel', 'hilton', 'marriott', 'airbnb', 'airlines',
                   'booking'],
        'Housing': ['rent', 'mortgage', 'utilities', 'electric', 'water'],
    }

    @staticmethod
    def infer(merchant_name: str, existing_category: str = "") -> str:
        """
        Infer category from merchant name if not provided.

        Uses keyword matching to categorize transactions.
        """
        # If category already provided and not empty then use
        if existing_category and existing_category.strip():
            return existing_category.strip()

        merchant_lower = merchant_name.lower()

        # Check category's keywords
        for category, keywords in CategoryInferencer.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in merchant_lower:
                    return category

        return "Uncategorized"