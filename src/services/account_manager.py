"""
account_manager.py — High-level account operations service.

The AccountManager sits between the caller (main.py / UI) and the
domain models.  It orchestrates multi-step operations such as transfers
(which touch two accounts and produce two transactions) and ensures
every mutation is properly logged through the TransactionManager.
"""

from decimal import Decimal
from typing import List, Tuple

from src.models.account import Account
from src.models.bank import Bank
from src.models.transaction import Transaction
from src.services.transaction_manager import TransactionManager
from src.utils.enums import AccountType, TransactionType


class AccountManager:
    """
    Coordinates account operations and transaction recording.

    Attributes:
        _bank (Bank):
            The Bank aggregate that owns all accounts.
        _transaction_manager (TransactionManager):
            The central transaction store.
    """

    def __init__(
        self, bank: Bank, transaction_manager: TransactionManager
    ) -> None:
        """
        Create an AccountManager.

        Args:
            bank: The Bank instance to operate on.
            transaction_manager: Shared TransactionManager for recording.
        """
        self._bank: Bank = bank
        self._transaction_manager: TransactionManager = transaction_manager

    # ------------------------------------------------------------------ #
    #  Account creation
    # ------------------------------------------------------------------ #

    def create_account(
        self,
        customer_id: str,
        account_type: AccountType,
        initial_deposit: Decimal = Decimal("0.00"),
        **kwargs,
    ) -> Account:
        """
        Open a new account through the Bank and optionally log an
        initial-deposit transaction.

        Args:
            customer_id: Owning customer's ID.
            account_type: SAVINGS or CHECKING.
            initial_deposit: Opening balance.
            **kwargs: Extra params forwarded to the account constructor.

        Returns:
            The newly created Account.
        """
        account = self._bank.create_account(
            customer_id, account_type, initial_deposit, **kwargs
        )

        # Log the initial deposit if non-zero
        if initial_deposit > 0:
            tx = self._build_transaction(
                amount=initial_deposit,
                transaction_type=TransactionType.DEPOSIT,
                target_account=account.account_number,
                description="Initial deposit on account opening",
            )
            tx.complete()
            self._transaction_manager.record_transaction(tx)
            account.add_transaction_id(tx.transaction_id)

        return account

    # ------------------------------------------------------------------ #
    #  Deposit
    # ------------------------------------------------------------------ #

    def deposit(
        self,
        account_number: str,
        amount: Decimal,
        description: str = "",
    ) -> Transaction:
        """
        Deposit funds into an account.

        Args:
            account_number: Target account.
            amount: Positive amount to deposit.
            description: Optional note.

        Returns:
            The completed Transaction record.

        Raises:
            KeyError: If the account does not exist.
            ValueError / RuntimeError: Propagated from Account.deposit.
        """
        account = self._get_account(account_number)
        meta = account.deposit(amount, description)

        tx = self._build_transaction(**meta)
        tx.complete()
        self._transaction_manager.record_transaction(tx)
        account.add_transaction_id(tx.transaction_id)
        return tx

    # ------------------------------------------------------------------ #
    #  Withdrawal
    # ------------------------------------------------------------------ #

    def withdraw(
        self,
        account_number: str,
        amount: Decimal,
        description: str = "",
    ) -> Transaction:
        """
        Withdraw funds from an account.

        Args:
            account_number: Source account.
            amount: Positive amount to withdraw.
            description: Optional note.

        Returns:
            The completed Transaction record.

        Raises:
            KeyError: If the account does not exist.
            ValueError / RuntimeError: Propagated from Account.withdraw.
        """
        account = self._get_account(account_number)
        meta = account.withdraw(amount, description)

        tx = self._build_transaction(**meta)
        tx.complete()
        self._transaction_manager.record_transaction(tx)
        account.add_transaction_id(tx.transaction_id)
        return tx

    # ------------------------------------------------------------------ #
    #  Transfer
    # ------------------------------------------------------------------ #

    def transfer(
        self,
        source_account_number: str,
        target_account_number: str,
        amount: Decimal,
    ) -> Tuple[Transaction, Transaction]:
        """
        Transfer funds between two accounts.

        Creates two transactions: a debit on the source and a credit
        on the target.  If the withdrawal succeeds but the deposit
        fails, the withdrawal is rolled back.

        Args:
            source_account_number: Account to withdraw from.
            target_account_number: Account to deposit into.
            amount: Positive amount to transfer.

        Returns:
            A tuple of (debit_transaction, credit_transaction).

        Raises:
            KeyError: If either account does not exist.
            ValueError: If source == target, or amount/balance issues.
        """
        if source_account_number == target_account_number:
            raise ValueError("Cannot transfer to the same account.")

        source = self._get_account(source_account_number)
        target = self._get_account(target_account_number)

        # --- Debit leg ---
        debit_meta = source.withdraw(
            amount, f"Transfer to {target_account_number}"
        )
        debit_meta["transaction_type"] = TransactionType.TRANSFER
        debit_meta["target_account"] = target_account_number

        # --- Credit leg ---
        try:
            credit_meta = target.deposit(
                amount, f"Transfer from {source_account_number}"
            )
        except Exception:
            # Roll back the withdrawal
            source._balance += amount
            raise

        credit_meta["transaction_type"] = TransactionType.TRANSFER
        credit_meta["source_account"] = source_account_number

        # --- Record both ---
        debit_tx = self._build_transaction(**debit_meta)
        debit_tx.complete()
        self._transaction_manager.record_transaction(debit_tx)
        source.add_transaction_id(debit_tx.transaction_id)

        credit_tx = self._build_transaction(**credit_meta)
        credit_tx.complete()
        self._transaction_manager.record_transaction(credit_tx)
        target.add_transaction_id(credit_tx.transaction_id)

        return debit_tx, credit_tx

    # ------------------------------------------------------------------ #
    #  Balance inquiry
    # ------------------------------------------------------------------ #

    def get_balance(self, account_number: str) -> Decimal:
        """
        Return the current balance of an account.

        Args:
            account_number: The account to query.

        Returns:
            The account balance as a Decimal.
        """
        return self._get_account(account_number).get_balance()

    def get_transaction_history(
        self, account_number: str
    ) -> List[Transaction]:
        """
        Return all transactions for an account in chronological order.

        Args:
            account_number: The account to query.

        Returns:
            List of Transaction objects.
        """
        return self._transaction_manager.get_transactions_for_account(
            account_number
        )

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    def _get_account(self, account_number: str) -> Account:
        """
        Retrieve an account or raise a clear error.

        Raises:
            KeyError: If the account is not found.
        """
        account = self._bank.find_account(account_number)
        if account is None:
            raise KeyError(f"Account {account_number} not found.")
        return account

    def _build_transaction(self, **kwargs) -> Transaction:
        """
        Create a Transaction using the bank's ID generator.

        Accepts the same keyword arguments as the Transaction
        constructor (minus transaction_id, which is generated here).
        Strips any extra keys (e.g. 'overdraft_used') before passing
        to the constructor.
        """
        allowed_keys = {
            "amount",
            "transaction_type",
            "description",
            "source_account",
            "target_account",
        }
        filtered = {k: v for k, v in kwargs.items() if k in allowed_keys}
        tx_id = self._bank.id_generator.generate_transaction_id()
        return Transaction(transaction_id=tx_id, **filtered)