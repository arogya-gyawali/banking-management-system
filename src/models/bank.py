"""
bank.py — Bank aggregate root for the Banking Management System.

The Bank class is the top-level container that owns all domain entities:
customers, accounts, loans, and cards.  It delegates ID generation to
an IdGenerator and provides lookup / lifecycle methods for each entity.
"""

from decimal import Decimal
from typing import Dict, Optional

from src.models.account import Account, CurrentAccount, SavingsAccount
from src.models.card import Card
from src.models.customer import Customer
from src.models.loan import Loan
from src.utils.enums import AccountType
from src.utils.id_generator import IdGenerator


class Bank:
    """
    Central aggregate that stores and manages all entities.

    Attributes:
        _bank_name (str):
            Name of the bank.
        _branch_code (str):
            Branch identifier.
        _customers (Dict[str, Customer]):
            Customer ID → Customer mapping.
        _accounts (Dict[str, Account]):
            Account number → Account mapping.
        _loans (Dict[str, Loan]):
            Loan ID → Loan mapping.
        _cards (Dict[str, Card]):
            Card number → Card mapping.
        _id_generator (IdGenerator):
            Shared ID generator instance.
    """

    def __init__(self, bank_name: str, branch_code: str) -> None:
        """
        Create a Bank.

        Args:
            bank_name: Display name of the bank.
            branch_code: Branch identifier string.
        """
        self._bank_name: str = bank_name
        self._branch_code: str = branch_code
        self._customers: Dict[str, Customer] = {}
        self._accounts: Dict[str, Account] = {}
        self._loans: Dict[str, Loan] = {}
        self._cards: Dict[str, Card] = {}
        self._id_generator: IdGenerator = IdGenerator()

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def bank_name(self) -> str:
        return self._bank_name

    @property
    def branch_code(self) -> str:
        return self._branch_code

    @property
    def id_generator(self) -> IdGenerator:
        """Expose the generator so services can mint IDs."""
        return self._id_generator

    # ------------------------------------------------------------------ #
    #  Customer management
    # ------------------------------------------------------------------ #

    def add_customer(self, customer: Customer) -> None:
        """
        Register an existing Customer object with the bank.

        Args:
            customer: The Customer instance to add.

        Raises:
            ValueError: If a customer with the same ID already exists.
        """
        if customer.customer_id in self._customers:
            raise ValueError(
                f"Customer {customer.customer_id} already exists."
            )
        self._customers[customer.customer_id] = customer

    def remove_customer(self, customer_id: str) -> None:
        """
        Remove a customer from the bank.

        Args:
            customer_id: ID of the customer to remove.

        Raises:
            KeyError: If the customer does not exist.
        """
        if customer_id not in self._customers:
            raise KeyError(f"Customer {customer_id} not found.")
        del self._customers[customer_id]

    def offboard_customer(self, customer_id: str) -> None:
        """
        Fully remove a customer and all their associated data.

        Checks that the customer has no remaining funds or outstanding
        loan balance before proceeding.  On success, closes all accounts,
        cancels all cards, removes pending loans, and deletes the customer.

        Args:
            customer_id: ID of the customer to offboard.

        Raises:
            KeyError: If the customer does not exist.
            ValueError: If the customer has a non-zero account balance or
                        an outstanding loan balance.
        """
        customer = self._customers.get(customer_id)
        if customer is None:
            raise KeyError(f"Customer {customer_id} not found.")

        for acct_num in customer.account_numbers:
            acct = self._accounts.get(acct_num)
            if acct and acct.balance > 0:
                raise ValueError(
                    f"Account {acct_num} still has a balance of "
                    f"${acct.balance:,.2f}. The customer must withdraw "
                    f"all funds before their account can be closed."
                )

        for loan in self.get_loans_for_customer(customer_id):
            if loan.remaining_balance > 0:
                raise ValueError(
                    f"Loan {loan.loan_id} has an outstanding balance of "
                    f"${loan.remaining_balance:,.2f}. It must be repaid "
                    f"before the customer can be removed."
                )

        for acct_num in list(customer.account_numbers):
            acct = self._accounts.get(acct_num)
            if acct and acct.is_active:
                acct.close()
            if acct_num in self._accounts:
                del self._accounts[acct_num]

        cards_to_remove = [
            card_num for card_num, card in self._cards.items()
            if card.customer_id == customer_id
        ]
        for card_num in cards_to_remove:
            del self._cards[card_num]

        loans_to_remove = [
            loan.loan_id for loan in self.get_loans_for_customer(customer_id)
        ]
        for loan_id in loans_to_remove:
            del self._loans[loan_id]

        del self._customers[customer_id]

    def find_customer(self, customer_id: str) -> Optional[Customer]:
        """
        Look up a customer by ID.

        Args:
            customer_id: The customer's unique ID.

        Returns:
            The Customer instance, or None if not found.
        """
        return self._customers.get(customer_id)

    def get_all_customers(self) -> list:
        """Return a list of all registered customers."""
        return list(self._customers.values())

    # ------------------------------------------------------------------ #
    #  Account management
    # ------------------------------------------------------------------ #

    def create_account(
        self,
        customer_id: str,
        account_type: AccountType,
        initial_deposit: Decimal = Decimal("0.00"),
        **kwargs,
    ) -> Account:
        """
        Open a new account and link it to a customer.

        Args:
            customer_id: Owning customer's ID.
            account_type: SAVINGS or CHECKING.
            initial_deposit: Opening balance.
            **kwargs: Additional params forwarded to the account constructor
                      (e.g. interest_rate, overdraft_limit).

        Returns:
            The newly created Account instance.

        Raises:
            KeyError: If the customer does not exist.
            ValueError: On invalid account_type or deposit.
        """
        customer = self._customers.get(customer_id)
        if customer is None:
            raise KeyError(f"Customer {customer_id} not found.")

        for acct_num in customer.account_numbers:
            existing = self._accounts.get(acct_num)
            if existing is not None and existing.account_type == account_type:
                raise ValueError(
                    f"Customer {customer_id} already has a "
                    f"{account_type.value} account ({acct_num})."
                )

        account_number = self._id_generator.generate_account_number()

        if account_type == AccountType.SAVINGS:
            account = SavingsAccount(
                account_number, customer_id, initial_deposit, **kwargs
            )
        elif account_type == AccountType.CHECKING:
            account = CurrentAccount(
                account_number, customer_id, initial_deposit, **kwargs
            )
        else:
            raise ValueError(f"Unknown account type: {account_type}")

        self._accounts[account_number] = account
        customer.add_account(account_number)
        return account

    def find_account(self, account_number: str) -> Optional[Account]:
        """
        Look up an account by number.

        Args:
            account_number: The account's unique number.

        Returns:
            The Account instance, or None if not found.
        """
        return self._accounts.get(account_number)

    def close_account(self, account_number: str) -> None:
        """
        Close (deactivate) an account.

        Args:
            account_number: The account to close.

        Raises:
            KeyError: If the account does not exist.
        """
        account = self._accounts.get(account_number)
        if account is None:
            raise KeyError(f"Account {account_number} not found.")
        account.close()

    # ------------------------------------------------------------------ #
    #  Loan management
    # ------------------------------------------------------------------ #

    def add_loan(self, loan: Loan) -> None:
        """Register a Loan with the bank."""
        self._loans[loan.loan_id] = loan

    def find_loan(self, loan_id: str) -> Optional[Loan]:
        """Look up a loan by ID."""
        return self._loans.get(loan_id)

    def get_loans_for_customer(self, customer_id: str) -> list:
        """Return all loans belonging to a customer."""
        return [
            loan for loan in self._loans.values()
            if loan.customer_id == customer_id
        ]

    # ------------------------------------------------------------------ #
    #  Card management
    # ------------------------------------------------------------------ #

    def add_card(self, card: Card) -> None:
        """Register a Card with the bank."""
        self._cards[card.card_number] = card

    def find_card(self, card_number: str) -> Optional[Card]:
        """Look up a card by number."""
        return self._cards.get(card_number)

    # ------------------------------------------------------------------ #
    #  Persistence placeholder
    # ------------------------------------------------------------------ #

    def save_state(self) -> None:
        """
        Persist the bank's current state.

        Note:
            This is a placeholder — a real implementation would write
            to a database or JSON file.
        """
        print(
            f"[Bank] State saved — {len(self._customers)} customers, "
            f"{len(self._accounts)} accounts, {len(self._loans)} loans, "
            f"{len(self._cards)} cards."
        )

    # ------------------------------------------------------------------ #
    #  Dunder methods
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return f"Bank(name={self._bank_name!r}, branch={self._branch_code!r})"

    def __str__(self) -> str:
        return (
            f"{self._bank_name} (Branch: {self._branch_code}) — "
            f"{len(self._customers)} customer(s), "
            f"{len(self._accounts)} account(s)"
        )