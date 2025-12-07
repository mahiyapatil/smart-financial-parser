"""
Pydantic validation schemas for financial transactions.
Ensures data integrity and type safety throughout the pipeline.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class RawTransaction(BaseModel):
    """Schema for raw, unvalidated transaction data from CSV."""

    model_config = ConfigDict(str_strip_whitespace=True)

    date: str
    merchant_name: str
    amount: str
    category: str = ""

    @field_validator('date')
    @classmethod
    def validate_date_not_empty(cls, v: str) -> str:
        """Ensure date field is not empty."""
        if not v or v.strip() == "":
            raise ValueError("Date cannot be empty")
        return v.strip()

    @field_validator('merchant_name')
    @classmethod
    def validate_merchant_not_empty(cls, v: str) -> str:
        """Ensure merchant name is not empty."""
        if not v or v.strip() == "":
            return "UNKNOWN_MERCHANT"
        return v.strip()

    @field_validator('amount')
    @classmethod
    def validate_amount_not_empty(cls, v: str) -> str:
        """Ensure amount field has some value."""
        if not v or v.strip() == "":
            raise ValueError("Amount cannot be empty")
        return v.strip()


class CleanTransaction(BaseModel):
    """Schema for normalized, validated transaction data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    date: datetime
    merchant_name: str = Field(..., min_length=1, max_length=200)
    normalized_merchant: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., decimal_places=2)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    category: str = Field(default="Uncategorized")
    is_refund: bool = Field(default=False)
    is_anomaly: bool = Field(default=False)
    anomaly_reason: Optional[str] = None

    @field_validator('amount')
    @classmethod
    def validate_amount_range(cls, v: Decimal) -> Decimal:
        """Validate amount is within reasonable bounds."""
        if abs(v) > 999999.99:
            raise ValueError(f"Amount {v} exceeds maximum allowed value")
        return v

    @field_validator('merchant_name')
    @classmethod
    def sanitize_merchant_name(cls, v: str) -> str:
        """Sanitize merchant name to prevent injection attacks."""
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '\\', ';']
        for char in dangerous_chars:
            v = v.replace(char, '')
        return v.strip()


class TransactionSummary(BaseModel):
    """Schema for analytics summary report."""

    total_transactions: int = Field(..., ge=0)
    date_range: tuple[datetime, datetime]
    total_spending: Decimal
    total_refunds: Decimal
    net_spending: Decimal
    top_category: str
    top_category_spending: Decimal
    anomalies_detected: int = Field(..., ge=0)
    merchants_normalized: int = Field(..., ge=0)