"""
id_generator.py — Unique identifier generation for the Banking Management System.

Provides the IdGenerator class, which creates unique, prefixed IDs for every
entity in the system (customers, accounts, transactions, loans, cards).
Each generator maintains its own counter so IDs are sequential and
human-readable during development and testing.
"""

import uuid


class IdGenerator:
    """
    Generates unique identifiers for all major entities.

    Each entity type receives a distinct prefix so IDs are instantly
    recognisable in logs and output:
        Customer  → "CUST-0001"
        Account   → "ACCT-0001"
        Transaction → "TXN-0001"
        Loan      → "LOAN-0001"
        Card      → "CARD-0001"

    Attributes:
        _counters (dict[str, int]): Maps each prefix to its running count.
    """

    def __init__(self) -> None:
        self._counters: dict[str, int] = {
            "CUST": 0,
            "ACCT": 0,
            "TXN": 0,
            "LOAN": 0,
            "CARD": 0,
        }

    def _next_id(self, prefix: str) -> str:
        """
        Increment the counter for *prefix* and return the formatted ID.

        Args:
            prefix: The entity prefix (e.g. "CUST", "ACCT").

        Returns:
            A string like "CUST-0001".
        """
        self._counters[prefix] += 1
        return f"{prefix}-{self._counters[prefix]:04d}"

    def generate_customer_id(self) -> str:
        """Return the next unique customer ID (e.g. 'CUST-0001')."""
        return self._next_id("CUST")

    def generate_account_number(self) -> str:
        """Return the next unique account number (e.g. 'ACCT-0001')."""
        return self._next_id("ACCT")

    def generate_transaction_id(self) -> str:
        """Return the next unique transaction ID (e.g. 'TXN-0001')."""
        return self._next_id("TXN")

    def generate_loan_id(self) -> str:
        """Return the next unique loan ID (e.g. 'LOAN-0001')."""
        return self._next_id("LOAN")

    def generate_card_number(self) -> str:
        """Return the next unique card number (e.g. 'CARD-0001')."""
        return self._next_id("CARD")