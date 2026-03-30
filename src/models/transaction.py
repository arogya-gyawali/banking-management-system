"""
transaction.py — Transaction entity for the Banking Management System.

Each deposit, withdrawal, transfer, interest application, loan payment,
or card charge is captured as an immutable Transaction record.  Once
created, a Transaction's core fields (amount, type, accounts) do not
change — only the status may transition from PENDING → COMPLETED | FAILED.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.utils.enums import TransactionStatus, TransactionType


class Transaction:
    """
    An immutable record of a single financial operation.

    Attributes:
        _transaction_id (str):
            Unique identifier (e.g. "TXN-0001").
        _timestamp (datetime):
            UTC time the transaction was created.
        _amount (Decimal):
            Monetary value of the transaction (always positive).
        _transaction_type (TransactionType):
            Category such as DEPOSIT, WITHDRAWAL, TRANSFER, etc.
        _source_account (Optional[str]):
            Account number funds are drawn from (None for deposits).
        _target_account (Optional[str]):
            Account number funds are sent to (None for withdrawals).
        _description (str):
            Human-readable note describing the transaction.
        _status (TransactionStatus):
            Current lifecycle state (PENDING, COMPLETED, or FAILED).
    """

    def __init__(
        self,
        transaction_id: str,
        amount: Decimal,
        transaction_type: TransactionType,
        description: str = "",
        source_account: Optional[str] = None,
        target_account: Optional[str] = None,
    ) -> None:
        """
        Create a new Transaction.

        Args:
            transaction_id: Unique ID assigned by the IdGenerator.
            amount: Positive monetary value.
            transaction_type: Category of this transaction.
            description: Free-text note (default "").
            source_account: Originating account number, if applicable.
            target_account: Destination account number, if applicable.

        Raises:
            ValueError: If *amount* is not positive.
        """
        if amount <= 0:
            raise ValueError(f"Transaction amount must be positive, got {amount}.")

        self._transaction_id: str = transaction_id
        self._timestamp: datetime = datetime.now()
        self._amount: Decimal = amount
        self._transaction_type: TransactionType = transaction_type
        self._source_account: Optional[str] = source_account
        self._target_account: Optional[str] = target_account
        self._description: str = description
        self._status: TransactionStatus = TransactionStatus.PENDING

    # ------------------------------------------------------------------ #
    #  Properties (read-only access to private attributes)
    # ------------------------------------------------------------------ #

    @property
    def transaction_id(self) -> str:
        """Return the unique transaction identifier."""
        return self._transaction_id

    @property
    def timestamp(self) -> datetime:
        """Return the UTC timestamp of creation."""
        return self._timestamp

    @property
    def amount(self) -> Decimal:
        """Return the transaction amount."""
        return self._amount

    @property
    def transaction_type(self) -> TransactionType:
        """Return the transaction category."""
        return self._transaction_type

    @property
    def source_account(self) -> Optional[str]:
        """Return the source account number, or None."""
        return self._source_account

    @property
    def target_account(self) -> Optional[str]:
        """Return the target account number, or None."""
        return self._target_account

    @property
    def description(self) -> str:
        """Return the human-readable description."""
        return self._description

    @property
    def status(self) -> TransactionStatus:
        """Return the current lifecycle status."""
        return self._status

    # ------------------------------------------------------------------ #
    #  Status transitions
    # ------------------------------------------------------------------ #

    def complete(self) -> None:
        """
        Mark this transaction as successfully completed.

        Raises:
            RuntimeError: If the transaction is not in PENDING status.
        """
        if self._status != TransactionStatus.PENDING:
            raise RuntimeError(
                f"Cannot complete transaction {self._transaction_id}: "
                f"current status is {self._status.value}."
            )
        self._status = TransactionStatus.COMPLETED

    def fail(self) -> None:
        """
        Mark this transaction as failed.

        Raises:
            RuntimeError: If the transaction is not in PENDING status.
        """
        if self._status != TransactionStatus.PENDING:
            raise RuntimeError(
                f"Cannot fail transaction {self._transaction_id}: "
                f"current status is {self._status.value}."
            )
        self._status = TransactionStatus.FAILED

    # ------------------------------------------------------------------ #
    #  Utility methods
    # ------------------------------------------------------------------ #

    def generate_receipt(self) -> str:
        """
        Return a formatted, human-readable receipt string.

        Returns:
            Multi-line receipt summarising the transaction.
        """
        lines = [
            "=" * 40,
            "       TRANSACTION RECEIPT",
            "=" * 40,
            f"  ID          : {self._transaction_id}",
            f"  Date        : {self._timestamp:%Y-%m-%d %H:%M:%S}",
            f"  Type        : {self._transaction_type.value.upper()}",
            f"  Amount      : ${self._amount:,.2f}",
            f"  Status      : {self._status.value.upper()}",
        ]
        if self._source_account:
            lines.append(f"  From        : {self._source_account}")
        if self._target_account:
            lines.append(f"  To          : {self._target_account}")
        if self._description:
            lines.append(f"  Description : {self._description}")
        lines.append("=" * 40)
        return "\n".join(lines)

    def serialize(self) -> dict:
        """
        Convert the transaction to a plain dictionary.

        Useful for JSON export, logging, or persistence.

        Returns:
            A dict with all transaction fields as serialisable types.
        """
        return {
            "transaction_id": self._transaction_id,
            "timestamp": self._timestamp.isoformat(),
            "amount": str(self._amount),
            "transaction_type": self._transaction_type.value,
            "source_account": self._source_account,
            "target_account": self._target_account,
            "description": self._description,
            "status": self._status.value,
        }

    # ------------------------------------------------------------------ #
    #  Dunder methods
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self._transaction_id!r}, "
            f"type={self._transaction_type.value}, "
            f"amount={self._amount}, "
            f"status={self._status.value})"
        )

    def __str__(self) -> str:
        return (
            f"[{self._transaction_id}] {self._transaction_type.value.upper()} "
            f"${self._amount:,.2f} — {self._status.value}"
        )