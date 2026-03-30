"""
account.py — Account hierarchy for the Banking Management System.

Defines the abstract Account base class and its two concrete subclasses:
SavingsAccount (earns interest, enforces a minimum balance) and
CurrentAccount (supports overdraft).  Each account records transactions
by storing transaction IDs; the actual Transaction objects live in the
TransactionManager.

Design notes
------------
- ``deposit`` and ``withdraw`` are abstract — each subclass implements
  its own balance-validation rules.
- ``transfer`` is concrete on the base class because the logic (withdraw
  from self, deposit into target) is identical for both account types.
  Subclasses only need to override withdraw/deposit behaviour.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional, Tuple

from src.utils.enums import TransactionType


class Account(ABC):
    """
    Abstract base class for all bank accounts.

    Attributes:
        _account_number (str):
            Unique identifier (e.g. "ACCT-0001").
        _customer_id (str):
            ID of the customer who owns this account.
        _balance (Decimal):
            Current available balance.
        _transaction_ids (List[str]):
            Ordered list of transaction IDs linked to this account.
        _is_active (bool):
            Whether the account is open and usable.
        _minimum_balance (Decimal):
            Lowest allowed balance (overridden by subclasses).
    """

    def __init__(
        self,
        account_number: str,
        customer_id: str,
        initial_deposit: Decimal = Decimal("0.00"),
    ) -> None:
        """
        Initialise a new Account.

        Args:
            account_number: Unique account number from IdGenerator.
            customer_id: Owning customer's ID.
            initial_deposit: Opening balance (default 0.00).

        Raises:
            ValueError: If *initial_deposit* is negative.
        """
        if initial_deposit < 0:
            raise ValueError("Initial deposit cannot be negative.")

        self._account_number: str = account_number
        self._customer_id: str = customer_id
        self._balance: Decimal = initial_deposit
        self._transaction_ids: List[str] = []
        self._is_active: bool = True
        self._minimum_balance: Decimal = Decimal("0.00")

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def account_number(self) -> str:
        """Return the unique account number."""
        return self._account_number

    @property
    def customer_id(self) -> str:
        """Return the owning customer's ID."""
        return self._customer_id

    @property
    def balance(self) -> Decimal:
        """Return the current balance."""
        return self._balance

    @property
    def is_active(self) -> bool:
        """Return whether the account is open."""
        return self._is_active

    @property
    def transaction_ids(self) -> List[str]:
        """Return a copy of the transaction ID list."""
        return list(self._transaction_ids)

    # ------------------------------------------------------------------ #
    #  Public helpers
    # ------------------------------------------------------------------ #

    def get_balance(self) -> Decimal:
        """
        Return the current account balance.

        Returns:
            The balance as a Decimal.
        """
        return self._balance

    def add_transaction_id(self, transaction_id: str) -> None:
        """
        Append a transaction ID to this account's history.

        Args:
            transaction_id: The ID to record.
        """
        self._transaction_ids.append(transaction_id)

    def close(self) -> None:
        """
        Deactivate this account.

        Raises:
            RuntimeError: If the account is already closed.
        """
        if not self._is_active:
            raise RuntimeError(
                f"Account {self._account_number} is already closed."
            )
        self._is_active = False

    # ------------------------------------------------------------------ #
    #  Validation helpers (used by subclasses)
    # ------------------------------------------------------------------ #

    def _validate_active(self) -> None:
        """
        Raise if the account is closed.

        Raises:
            RuntimeError: If *_is_active* is False.
        """
        if not self._is_active:
            raise RuntimeError(
                f"Account {self._account_number} is closed."
            )

    @staticmethod
    def _validate_amount(amount: Decimal) -> None:
        """
        Raise if *amount* is not a positive number.

        Args:
            amount: The value to check.

        Raises:
            ValueError: If amount is zero or negative.
        """
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}.")

    # ------------------------------------------------------------------ #
    #  Abstract interface
    # ------------------------------------------------------------------ #

    @abstractmethod
    def deposit(self, amount: Decimal, description: str = "") -> dict:
        """
        Deposit funds into the account.

        Args:
            amount: Positive amount to deposit.
            description: Optional note.

        Returns:
            A dict with keys needed to build a Transaction externally.
        """
        ...

    @abstractmethod
    def withdraw(self, amount: Decimal, description: str = "") -> dict:
        """
        Withdraw funds from the account.

        Args:
            amount: Positive amount to withdraw.
            description: Optional note.

        Returns:
            A dict with keys needed to build a Transaction externally.
        """
        ...

    def transfer_out(self, amount: Decimal, target_account_number: str) -> dict:
        """
        Prepare the *debit* side of a transfer (withdraw from this account).

        The AccountManager orchestrates the full transfer by calling
        ``transfer_out`` on the source and ``deposit`` on the target.

        Args:
            amount: Positive amount to transfer.
            target_account_number: The destination account number.

        Returns:
            A dict with transaction metadata for the debit leg.
        """
        result = self.withdraw(amount, f"Transfer to {target_account_number}")
        result["target_account"] = target_account_number
        result["transaction_type"] = TransactionType.TRANSFER
        return result

    # ------------------------------------------------------------------ #
    #  Dunder methods
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"number={self._account_number!r}, "
            f"balance={self._balance})"
        )

    def __str__(self) -> str:
        status = "Active" if self._is_active else "Closed"
        return (
            f"[{self._account_number}] {self.__class__.__name__} — "
            f"${self._balance:,.2f} ({status})"
        )


# ====================================================================== #
#  SAVINGS ACCOUNT
# ====================================================================== #


class SavingsAccount(Account):
    """
    A savings account that earns interest and enforces a minimum balance.

    Attributes:
        _interest_rate (Decimal):
            Annual interest rate as a decimal (e.g. 0.025 = 2.5 %).
        _minimum_balance (Decimal):
            The lowest balance allowed after a withdrawal.
    """

    def __init__(
        self,
        account_number: str,
        customer_id: str,
        initial_deposit: Decimal = Decimal("0.00"),
        interest_rate: Decimal = Decimal("0.025"),
        minimum_balance: Decimal = Decimal("100.00"),
    ) -> None:
        """
        Create a SavingsAccount.

        Args:
            account_number: Unique account number.
            customer_id: Owning customer's ID.
            initial_deposit: Opening balance.
            interest_rate: Annual rate as a decimal (default 2.5 %).
            minimum_balance: Minimum allowed balance (default $100).

        Raises:
            ValueError: If *initial_deposit* < *minimum_balance*.
        """
        super().__init__(account_number, customer_id, initial_deposit)
        self._interest_rate: Decimal = interest_rate
        self._minimum_balance: Decimal = minimum_balance

        if initial_deposit < minimum_balance:
            raise ValueError(
                f"Initial deposit (${initial_deposit}) is below the "
                f"minimum balance (${minimum_balance})."
            )

    @property
    def interest_rate(self) -> Decimal:
        """Return the annual interest rate."""
        return self._interest_rate

    @property
    def minimum_balance(self) -> Decimal:
        """Return the minimum balance requirement."""
        return self._minimum_balance

    # ------------------------------------------------------------------ #
    #  Overrides
    # ------------------------------------------------------------------ #

    def deposit(self, amount: Decimal, description: str = "") -> dict:
        """
        Deposit funds into the savings account.

        Args:
            amount: Positive amount to deposit.
            description: Optional note.

        Returns:
            Dict with transaction metadata.

        Raises:
            RuntimeError: If the account is closed.
            ValueError: If amount is not positive.
        """
        self._validate_active()
        self._validate_amount(amount)

        self._balance += amount
        return {
            "amount": amount,
            "transaction_type": TransactionType.DEPOSIT,
            "target_account": self._account_number,
            "source_account": None,
            "description": description or "Savings deposit",
        }

    def withdraw(self, amount: Decimal, description: str = "") -> dict:
        """
        Withdraw funds, enforcing the minimum-balance rule.

        Args:
            amount: Positive amount to withdraw.
            description: Optional note.

        Returns:
            Dict with transaction metadata.

        Raises:
            RuntimeError: If the account is closed.
            ValueError: If amount is not positive or would breach minimum balance.
        """
        self._validate_active()
        self._validate_amount(amount)

        if self._balance - amount < self._minimum_balance:
            raise ValueError(
                f"Insufficient funds. Withdrawal of ${amount:,.2f} would leave "
                f"${self._balance - amount:,.2f}, which is below the minimum "
                f"balance of ${self._minimum_balance:,.2f}."
            )

        self._balance -= amount
        return {
            "amount": amount,
            "transaction_type": TransactionType.WITHDRAWAL,
            "source_account": self._account_number,
            "target_account": None,
            "description": description or "Savings withdrawal",
        }

    # ------------------------------------------------------------------ #
    #  Interest
    # ------------------------------------------------------------------ #

    def apply_interest(self) -> dict:
        """
        Calculate and add interest to the balance.

        Interest = balance × annual_rate  (simplified; not compounded
        per period for this project).

        Returns:
            Dict with transaction metadata for the interest credit.

        Raises:
            RuntimeError: If the account is closed.
        """
        self._validate_active()

        interest = (self._balance * self._interest_rate).quantize(Decimal("0.01"))
        if interest <= 0:
            raise ValueError("No interest to apply on current balance.")

        self._balance += interest
        return {
            "amount": interest,
            "transaction_type": TransactionType.INTEREST,
            "target_account": self._account_number,
            "source_account": None,
            "description": (
                f"Interest applied at {self._interest_rate * 100:.2f}%"
            ),
        }


# ====================================================================== #
#  CURRENT (CHECKING) ACCOUNT
# ====================================================================== #


class CurrentAccount(Account):
    """
    A checking account that supports overdraft.

    Attributes:
        _overdraft_limit (Decimal):
            Maximum amount the balance may go negative (e.g. 500.00
            means the effective floor is −$500).
    """

    def __init__(
        self,
        account_number: str,
        customer_id: str,
        initial_deposit: Decimal = Decimal("0.00"),
        overdraft_limit: Decimal = Decimal("500.00"),
    ) -> None:
        """
        Create a CurrentAccount (checking).

        Args:
            account_number: Unique account number.
            customer_id: Owning customer's ID.
            initial_deposit: Opening balance (default 0.00).
            overdraft_limit: Overdraft ceiling (default $500).
        """
        super().__init__(account_number, customer_id, initial_deposit)
        self._overdraft_limit: Decimal = overdraft_limit

    @property
    def overdraft_limit(self) -> Decimal:
        """Return the overdraft limit."""
        return self._overdraft_limit

    # ------------------------------------------------------------------ #
    #  Overrides
    # ------------------------------------------------------------------ #

    def deposit(self, amount: Decimal, description: str = "") -> dict:
        """
        Deposit funds into the checking account.

        Args:
            amount: Positive amount to deposit.
            description: Optional note.

        Returns:
            Dict with transaction metadata.

        Raises:
            RuntimeError: If the account is closed.
            ValueError: If amount is not positive.
        """
        self._validate_active()
        self._validate_amount(amount)

        self._balance += amount
        return {
            "amount": amount,
            "transaction_type": TransactionType.DEPOSIT,
            "target_account": self._account_number,
            "source_account": None,
            "description": description or "Checking deposit",
        }

    def withdraw(self, amount: Decimal, description: str = "") -> dict:
        """
        Withdraw funds, allowing overdraft up to the limit.

        The effective floor is ``-overdraft_limit``.  If the withdrawal
        would push the balance below that floor, it is rejected.

        Args:
            amount: Positive amount to withdraw.
            description: Optional note.

        Returns:
            Dict with transaction metadata.  Includes an ``overdraft_used``
            flag when the balance goes negative.

        Raises:
            RuntimeError: If the account is closed.
            ValueError: If amount is not positive or exceeds overdraft.
        """
        self._validate_active()
        self._validate_amount(amount)

        new_balance = self._balance - amount
        if new_balance < -self._overdraft_limit:
            raise ValueError(
                f"Overdraft limit exceeded. Withdrawal of ${amount:,.2f} "
                f"would result in a balance of ${new_balance:,.2f}, "
                f"but the overdraft limit is ${self._overdraft_limit:,.2f}."
            )

        overdraft_used = new_balance < 0
        self._balance = new_balance

        desc = description or "Checking withdrawal"
        if overdraft_used:
            desc += " [overdraft used]"

        return {
            "amount": amount,
            "transaction_type": TransactionType.WITHDRAWAL,
            "source_account": self._account_number,
            "target_account": None,
            "description": desc,
            "overdraft_used": overdraft_used,
        }