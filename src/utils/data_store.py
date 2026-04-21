"""
data_store.py — JSON-based persistence for the Banking Management System.

Saves and loads the entire bank state (customers, accounts, transactions,
loans, cards, users, and ID counters) to a JSON file so data survives
between Streamlit sessions.
"""

import json
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict

from src.models.account import CurrentAccount, SavingsAccount
from src.models.bank import Bank
from src.models.card import CreditCard, DebitCard
from src.models.customer import Customer
from src.models.loan import Loan
from src.models.transaction import Transaction
from src.models.user import User
from src.services.auth_service import AuthService
from src.services.transaction_manager import TransactionManager
from src.utils.enums import (
    LoanStatus,
    Role,
    TransactionStatus,
    TransactionType,
)

DEFAULT_PATH = "data/bank_state.json"


class DataStore:
    """
    Handles serialization and deserialization of the entire bank state.

    All entities are converted to plain dicts for JSON storage and
    reconstructed on load, preserving private attribute values.
    """

    def __init__(self, filepath: str = DEFAULT_PATH) -> None:
        """
        Create a DataStore pointing at the given file path.

        Args:
            filepath: Path to the JSON file used for persistence.
                      Defaults to ``data/bank_state.json``.
        """
        self._filepath = filepath

    # ================================================================== #
    #  SAVE
    # ================================================================== #

    def save(
        self,
        bank: Bank,
        auth: AuthService,
        tx_manager: TransactionManager,
    ) -> None:
        """
        Serialize the entire bank state and write it to the JSON file.

        Converts every entity (customers, accounts, transactions, loans,
        cards, users, and ID counters) into plain dicts and dumps them
        as formatted JSON.  The output directory is created automatically
        if it does not already exist.

        Args:
            bank: The Bank aggregate containing all domain entities.
            auth: The AuthService holding registered users and sessions.
            tx_manager: The TransactionManager holding all transactions.
        """
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)

        state: Dict[str, Any] = {
            "bank": {
                "bank_name": bank.bank_name,
                "branch_code": bank.branch_code,
                "id_counters": bank.id_generator._counters,
            },
            "customers": {
                cid: self._serialize_customer(c)
                for cid, c in bank._customers.items()
            },
            "accounts": {
                anum: self._serialize_account(a)
                for anum, a in bank._accounts.items()
            },
            "transactions": {
                tid: self._serialize_transaction(t)
                for tid, t in tx_manager._transactions.items()
            },
            "loans": {
                lid: self._serialize_loan(loan)
                for lid, loan in bank._loans.items()
            },
            "cards": {
                cnum: self._serialize_card(card)
                for cnum, card in bank._cards.items()
            },
            "users": {
                uname: self._serialize_user(u)
                for uname, u in auth._users.items()
            },
        }

        with open(self._filepath, "w") as f:
            json.dump(state, f, indent=2, default=str)

    # ================================================================== #
    #  LOAD
    # ================================================================== #

    def load(self) -> tuple:
        """
        Read state from disk and reconstruct all objects.

        Returns:
            (bank, auth_service, transaction_manager) tuple.
            If no save file exists, returns freshly initialized objects
            with a default admin account.
        """
        if not os.path.exists(self._filepath):
            return self._create_fresh_state()

        with open(self._filepath, "r") as f:
            state = json.load(f)

        if not state or "bank" not in state:
            return self._create_fresh_state()

        # --- Bank ---
        bank_data = state["bank"]
        bank = Bank(bank_data["bank_name"], bank_data["branch_code"])
        bank._id_generator._counters = {
            k: int(v) for k, v in bank_data["id_counters"].items()
        }

        # --- Customers ---
        for cid, cdata in state.get("customers", {}).items():
            customer = Customer.__new__(Customer)
            customer._customer_id = cid
            customer._first_name = cdata["first_name"]
            customer._last_name = cdata["last_name"]
            customer._email = cdata["email"]
            customer._phone = cdata["phone"]
            customer._account_numbers = cdata.get("account_numbers", [])
            bank._customers[cid] = customer

        # --- Accounts ---
        for anum, adata in state.get("accounts", {}).items():
            if adata["type"] == "savings":
                account = SavingsAccount.__new__(SavingsAccount)
                account._account_number = anum
                account._customer_id = adata["customer_id"]
                account._balance = Decimal(adata["balance"])
                account._transaction_ids = adata.get("transaction_ids", [])
                account._is_active = adata["is_active"]
                account._interest_rate = Decimal(adata["interest_rate"])
                account._minimum_balance = Decimal(adata["minimum_balance"])
            else:
                account = CurrentAccount.__new__(CurrentAccount)
                account._account_number = anum
                account._customer_id = adata["customer_id"]
                account._balance = Decimal(adata["balance"])
                account._transaction_ids = adata.get("transaction_ids", [])
                account._is_active = adata["is_active"]
                account._overdraft_limit = Decimal(adata["overdraft_limit"])
                account._minimum_balance = Decimal("0.00")
            bank._accounts[anum] = account

        # --- Transactions ---
        tx_manager = TransactionManager()
        for tid, tdata in state.get("transactions", {}).items():
            tx = Transaction.__new__(Transaction)
            tx._transaction_id = tid
            tx._timestamp = datetime.fromisoformat(tdata["timestamp"])
            tx._amount = Decimal(tdata["amount"])
            tx._transaction_type = TransactionType(tdata["transaction_type"])
            tx._source_account = tdata.get("source_account")
            tx._target_account = tdata.get("target_account")
            tx._description = tdata.get("description", "")
            tx._status = TransactionStatus(tdata["status"])
            tx_manager._transactions[tid] = tx

        # --- Loans ---
        for lid, ldata in state.get("loans", {}).items():
            loan = Loan.__new__(Loan)
            loan._loan_id = lid
            loan._customer_id = ldata["customer_id"]
            loan._principal = Decimal(ldata["principal"])
            loan._interest_rate = Decimal(ldata["interest_rate"])
            loan._duration_months = ldata["duration_months"]
            loan._emi = Decimal(ldata["emi"])
            loan._remaining_balance = Decimal(ldata["remaining_balance"])
            loan._status = LoanStatus(ldata["status"])
            loan._rejection_reason = ldata.get("rejection_reason")
            bank._loans[lid] = loan

        # --- Cards ---
        for cnum, cdata in state.get("cards", {}).items():
            if cdata["type"] == "debit":
                card = DebitCard.__new__(DebitCard)
                card._card_number = cnum
                card._issued_to_customer_id = cdata["customer_id"]
                card._pin_hash = cdata["pin_hash"]
                card._expiry = date.fromisoformat(cdata["expiry"])
                card._is_blocked = cdata["is_blocked"]
                card._linked_account_number = cdata["linked_account_number"]
            else:
                card = CreditCard.__new__(CreditCard)
                card._card_number = cnum
                card._issued_to_customer_id = cdata["customer_id"]
                card._pin_hash = cdata["pin_hash"]
                card._expiry = date.fromisoformat(cdata["expiry"])
                card._is_blocked = cdata["is_blocked"]
                card._credit_limit = Decimal(cdata["credit_limit"])
                card._outstanding_balance = Decimal(cdata["outstanding_balance"])
            bank._cards[cnum] = card

        # --- Users ---
        auth = AuthService()
        for uname, udata in state.get("users", {}).items():
            user = User.__new__(User)
            user._username = uname
            user._password_hash = udata["password_hash"]
            user._role = Role(udata["role"])
            user._linked_customer_id = udata.get("linked_customer_id")
            auth._users[uname] = user

        return bank, auth, tx_manager

    # ================================================================== #
    #  FRESH STATE
    # ================================================================== #

    def _create_fresh_state(self) -> tuple:
        """
        Bootstrap a brand-new bank state when no save file exists.

        Creates a Bank, AuthService, and TransactionManager with default
        values and registers a built-in ``admin`` / ``admin123`` account
        so the app is immediately usable on first launch.  The fresh state
        is saved to disk before being returned.

        Returns:
            (bank, auth_service, transaction_manager) tuple with default state.
        """
        bank = Bank("Python National Bank", "BR-001")
        auth = AuthService()
        tx_manager = TransactionManager()

        # Default admin so someone can log in on first run
        auth.register("admin", "admin123", Role.ADMIN)

        self.save(bank, auth, tx_manager)
        return bank, auth, tx_manager

    # ================================================================== #
    #  SERIALIZERS
    # ================================================================== #

    def _serialize_customer(self, c: Customer) -> dict:
        """Return a JSON-safe dict representation of a Customer."""
        return {
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone": c.phone,
            "account_numbers": c.account_numbers,
        }

    def _serialize_account(self, a) -> dict:
        """Return a JSON-safe dict for a SavingsAccount or CurrentAccount, including type-specific fields."""
        base = {
            "customer_id": a.customer_id,
            "balance": str(a.balance),
            "transaction_ids": a.transaction_ids,
            "is_active": a.is_active,
        }
        if isinstance(a, SavingsAccount):
            base["type"] = "savings"
            base["interest_rate"] = str(a.interest_rate)
            base["minimum_balance"] = str(a.minimum_balance)
        elif isinstance(a, CurrentAccount):
            base["type"] = "checking"
            base["overdraft_limit"] = str(a.overdraft_limit)
        return base

    def _serialize_transaction(self, t: Transaction) -> dict:
        """Return a JSON-safe dict for a Transaction by delegating to its own serialize() method."""
        return t.serialize()

    def _serialize_loan(self, loan: Loan) -> dict:
        """Return a JSON-safe dict representation of a Loan, including all lifecycle fields."""
        return {
            "customer_id": loan.customer_id,
            "principal": str(loan.principal),
            "interest_rate": str(loan.interest_rate),
            "duration_months": loan.duration_months,
            "emi": str(loan.emi),
            "remaining_balance": str(loan.remaining_balance),
            "status": loan.status.value,
            "rejection_reason": loan.rejection_reason,
        }

    def _serialize_card(self, card) -> dict:
        """Return a JSON-safe dict for a DebitCard or CreditCard, including type-specific fields."""
        base = {
            "customer_id": card.issued_to_customer_id,
            "pin_hash": card._pin_hash,
            "expiry": card.expiry.isoformat(),
            "is_blocked": card.is_blocked,
        }
        if isinstance(card, DebitCard):
            base["type"] = "debit"
            base["linked_account_number"] = card.linked_account_number
        elif isinstance(card, CreditCard):
            base["type"] = "credit"
            base["credit_limit"] = str(card.credit_limit)
            base["outstanding_balance"] = str(card.outstanding_balance)
        return base

    def _serialize_user(self, u: User) -> dict:
        """Return a JSON-safe dict for a User, storing the hashed password (never plaintext)."""
        return {
            "password_hash": u._password_hash,
            "role": u.role.value,
            "linked_customer_id": u.linked_customer_id,
        }