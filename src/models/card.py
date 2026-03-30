"""
card.py — Card hierarchy for the Banking Management System.

Defines the abstract Card base class and its two concrete subclasses:
DebitCard (linked to an account, charges draw from that balance) and
CreditCard (has its own credit limit and outstanding balance).

PIN security
------------
PINs are stored as SHA-256 hashes.  The ``validate_pin`` method hashes
the caller's input and compares it to the stored hash — the raw PIN is
never persisted.
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from src.utils.enums import TransactionType


class Card(ABC):
    """
    Abstract base class for payment cards.

    Attributes:
        _card_number (str):
            Unique identifier (e.g. "CARD-0001").
        _expiry (date):
            Card expiration date.
        _pin_hash (str):
            SHA-256 hash of the card's PIN.
        _is_blocked (bool):
            Whether the card has been blocked.
        _issued_to_customer_id (str):
            Customer who holds this card.
    """

    def __init__(
        self,
        card_number: str,
        issued_to_customer_id: str,
        pin: str,
        expiry_years: int = 3,
    ) -> None:
        """
        Initialise a Card.

        Args:
            card_number: Unique card number from IdGenerator.
            issued_to_customer_id: Holder's customer ID.
            pin: 4-digit PIN string (will be hashed immediately).
            expiry_years: Years until expiry (default 3).

        Raises:
            ValueError: If *pin* is not exactly 4 digits.
        """
        if not (pin.isdigit() and len(pin) == 4):
            raise ValueError("PIN must be exactly 4 digits.")

        self._card_number: str = card_number
        self._issued_to_customer_id: str = issued_to_customer_id
        self._pin_hash: str = self._hash_pin(pin)
        self._expiry: date = date.today() + timedelta(days=365 * expiry_years)
        self._is_blocked: bool = False

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def card_number(self) -> str:
        return self._card_number

    @property
    def expiry(self) -> date:
        return self._expiry

    @property
    def is_blocked(self) -> bool:
        return self._is_blocked

    @property
    def issued_to_customer_id(self) -> str:
        return self._issued_to_customer_id

    # ------------------------------------------------------------------ #
    #  PIN helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hash_pin(pin: str) -> str:
        """Return the SHA-256 hex digest of *pin*."""
        return hashlib.sha256(pin.encode()).hexdigest()

    def validate_pin(self, pin: str) -> bool:
        """
        Check whether *pin* matches the stored hash.

        Args:
            pin: The 4-digit PIN to validate.

        Returns:
            True if the PIN is correct, False otherwise.
        """
        return self._hash_pin(pin) == self._pin_hash

    # ------------------------------------------------------------------ #
    #  Card management
    # ------------------------------------------------------------------ #

    def block(self, reason: str = "Blocked by admin") -> None:
        """
        Block this card so no further charges can be made.

        Args:
            reason: Explanation for the block (logged, not stored here).

        Raises:
            RuntimeError: If the card is already blocked.
        """
        if self._is_blocked:
            raise RuntimeError(
                f"Card {self._card_number} is already blocked."
            )
        self._is_blocked = True

    def _validate_usable(self, pin: str) -> None:
        """
        Ensure the card is not blocked, not expired, and the PIN is correct.

        Args:
            pin: The 4-digit PIN entered by the customer.

        Raises:
            RuntimeError: If the card is blocked or expired.
            ValueError: If the PIN is incorrect.
        """
        if self._is_blocked:
            raise RuntimeError(f"Card {self._card_number} is blocked.")
        if date.today() > self._expiry:
            raise RuntimeError(f"Card {self._card_number} has expired.")
        if not self.validate_pin(pin):
            raise ValueError("Invalid PIN.")

    # ------------------------------------------------------------------ #
    #  Abstract charge interface
    # ------------------------------------------------------------------ #

    @abstractmethod
    def charge(self, amount: Decimal, pin: str) -> dict:
        """
        Charge an amount to this card.

        Args:
            amount: Positive charge amount.
            pin: Customer's 4-digit PIN for authorisation.

        Returns:
            Dict with transaction metadata.
        """
        ...

    # ------------------------------------------------------------------ #
    #  Dunder methods
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"number={self._card_number!r}, "
            f"blocked={self._is_blocked})"
        )

    def __str__(self) -> str:
        status = "BLOCKED" if self._is_blocked else "Active"
        return (
            f"[{self._card_number}] {self.__class__.__name__} — "
            f"{status}, expires {self._expiry}"
        )


# ====================================================================== #
#  DEBIT CARD
# ====================================================================== #


class DebitCard(Card):
    """
    A debit card linked to a specific bank account.

    Charges draw directly from the linked account's balance. The actual
    balance deduction is handled by the AccountManager — this class only
    validates the card state and returns transaction metadata.

    Attributes:
        _linked_account_number (str):
            The account from which charges are debited.
    """

    def __init__(
        self,
        card_number: str,
        issued_to_customer_id: str,
        pin: str,
        linked_account_number: str,
        expiry_years: int = 3,
    ) -> None:
        super().__init__(card_number, issued_to_customer_id, pin, expiry_years)
        self._linked_account_number: str = linked_account_number

    @property
    def linked_account_number(self) -> str:
        return self._linked_account_number

    def charge(self, amount: Decimal, pin: str) -> dict:
        """
        Authorise a debit-card charge.

        Args:
            amount: Positive charge amount.
            pin: 4-digit PIN.

        Returns:
            Dict with transaction metadata; the caller is responsible
            for actually withdrawing from the linked account.

        Raises:
            RuntimeError: If the card is blocked or expired.
            ValueError: If the PIN is wrong or amount is invalid.
        """
        self._validate_usable(pin)
        if amount <= 0:
            raise ValueError("Charge amount must be positive.")

        return {
            "amount": amount,
            "transaction_type": TransactionType.CARD_CHARGE,
            "source_account": self._linked_account_number,
            "target_account": None,
            "description": f"Debit card charge ({self._card_number})",
        }


# ====================================================================== #
#  CREDIT CARD
# ====================================================================== #


class CreditCard(Card):
    """
    A credit card with a credit limit and outstanding balance.

    Attributes:
        _credit_limit (Decimal):
            Maximum amount that can be owed.
        _outstanding_balance (Decimal):
            Current amount owed (increases with charges, decreases
            with payments).
    """

    def __init__(
        self,
        card_number: str,
        issued_to_customer_id: str,
        pin: str,
        credit_limit: Decimal = Decimal("5000.00"),
        expiry_years: int = 3,
    ) -> None:
        super().__init__(card_number, issued_to_customer_id, pin, expiry_years)
        self._credit_limit: Decimal = credit_limit
        self._outstanding_balance: Decimal = Decimal("0.00")

    @property
    def credit_limit(self) -> Decimal:
        return self._credit_limit

    @property
    def outstanding_balance(self) -> Decimal:
        return self._outstanding_balance

    @property
    def available_credit(self) -> Decimal:
        """Return the remaining credit available for charges."""
        return self._credit_limit - self._outstanding_balance

    def charge(self, amount: Decimal, pin: str) -> dict:
        """
        Authorise a credit-card charge against the credit limit.

        Args:
            amount: Positive charge amount.
            pin: 4-digit PIN.

        Returns:
            Dict with transaction metadata.

        Raises:
            RuntimeError: If the card is blocked or expired.
            ValueError: If the PIN is wrong, amount is invalid, or
                        the charge would exceed the credit limit.
        """
        self._validate_usable(pin)
        if amount <= 0:
            raise ValueError("Charge amount must be positive.")
        if amount > self.available_credit:
            raise ValueError(
                f"Charge of ${amount:,.2f} exceeds available credit "
                f"(${self.available_credit:,.2f})."
            )

        self._outstanding_balance += amount
        return {
            "amount": amount,
            "transaction_type": TransactionType.CARD_CHARGE,
            "source_account": None,
            "target_account": None,
            "description": f"Credit card charge ({self._card_number})",
        }

    def make_payment(self, amount: Decimal) -> dict:
        """
        Pay down the outstanding balance.

        Args:
            amount: Positive payment amount.

        Returns:
            Dict with transaction metadata.

        Raises:
            ValueError: If amount ≤ 0 or exceeds outstanding balance.
        """
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        if amount > self._outstanding_balance:
            raise ValueError(
                f"Payment (${amount:,.2f}) exceeds outstanding balance "
                f"(${self._outstanding_balance:,.2f})."
            )

        self._outstanding_balance -= amount
        return {
            "amount": amount,
            "transaction_type": TransactionType.LOAN_PAYMENT,
            "description": (
                f"Credit card payment ({self._card_number}). "
                f"Remaining: ${self._outstanding_balance:,.2f}"
            ),
        }