"""
enums.py — Enumeration types for the Banking Management System.

Defines all the status and category enums used across models and services.
These enums enforce type safety and prevent invalid string-based states
throughout the system.
"""

from enum import Enum


class AccountType(Enum):
    """Supported account types within the banking system."""

    SAVINGS = "savings"
    CHECKING = "checking"


class TransactionType(Enum):
    """Categories of financial transactions."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    INTEREST = "interest"
    LOAN_PAYMENT = "loan_payment"
    CARD_CHARGE = "card_charge"


class TransactionStatus(Enum):
    """Lifecycle states of a transaction."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class LoanStatus(Enum):
    """Lifecycle states of a loan application."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class Role(Enum):
    """User roles for authentication and authorization."""

    CUSTOMER = "customer"
    ADMIN = "admin"