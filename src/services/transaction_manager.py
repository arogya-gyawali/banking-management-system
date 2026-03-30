"""
transaction_manager.py — Transaction recording and retrieval service.

The TransactionManager is the single source of truth for all Transaction
objects.  Other services create Transaction instances and hand them here
for storage and lookup.
"""

from typing import Dict, List

from src.models.transaction import Transaction


class TransactionManager:
    """
    Central registry for all transactions.

    Attributes:
        _transactions (Dict[str, Transaction]):
            Transaction ID → Transaction mapping.
    """

    def __init__(self) -> None:
        self._transactions: Dict[str, Transaction] = {}

    # ------------------------------------------------------------------ #
    #  Recording
    # ------------------------------------------------------------------ #

    def record_transaction(self, tx: Transaction) -> None:
        """
        Store a transaction.

        Args:
            tx: The Transaction instance to record.

        Raises:
            ValueError: If a transaction with the same ID already exists.
        """
        if tx.transaction_id in self._transactions:
            raise ValueError(
                f"Transaction {tx.transaction_id} already recorded."
            )
        self._transactions[tx.transaction_id] = tx

    # ------------------------------------------------------------------ #
    #  Retrieval
    # ------------------------------------------------------------------ #

    def get_transaction(self, transaction_id: str) -> Transaction:
        """
        Retrieve a single transaction by ID.

        Args:
            transaction_id: The transaction's unique ID.

        Returns:
            The matching Transaction.

        Raises:
            KeyError: If the transaction is not found.
        """
        if transaction_id not in self._transactions:
            raise KeyError(f"Transaction {transaction_id} not found.")
        return self._transactions[transaction_id]

    def get_transactions_for_account(
        self, account_number: str
    ) -> List[Transaction]:
        """
        Return all transactions involving a given account (as source or target).

        Args:
            account_number: The account number to filter by.

        Returns:
            A chronologically ordered list of matching transactions.
        """
        return [
            tx
            for tx in self._transactions.values()
            if tx.source_account == account_number
            or tx.target_account == account_number
        ]

    def get_all_transactions(self) -> List[Transaction]:
        """Return every recorded transaction."""
        return list(self._transactions.values())

    # ------------------------------------------------------------------ #
    #  Dunder
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return f"TransactionManager(count={len(self._transactions)})"