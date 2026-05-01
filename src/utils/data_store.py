"""
data_store.py — SQLite-based persistence for the Banking Management System.

Saves and loads the entire bank state (customers, accounts, transactions,
loans, cards, users, and ID counters) to a SQLite database file so data
survives between Streamlit sessions.

On first run, if a legacy JSON file exists at ``data/bank_state.json`` it
is automatically migrated into the new database and then left in place as
a backup.
"""

import json
import os
import sqlite3
from datetime import date, datetime
from decimal import Decimal

from src.models.account import CurrentAccount, SavingsAccount
from src.models.bank import Bank
from src.models.card import CreditCard, DebitCard
from src.models.customer import Customer
from src.models.loan import Loan
from src.models.transaction import Transaction
from src.models.user import User
from src.services.auth_service import AuthService
from src.services.transaction_manager import TransactionManager
from src.utils.enums import LoanStatus, Role, TransactionStatus, TransactionType

DEFAULT_PATH = "data/bank.db"
LEGACY_JSON_PATH = "data/bank_state.json"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bank (
    id          INTEGER PRIMARY KEY,
    bank_name   TEXT NOT NULL,
    branch_code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS id_counters (
    prefix TEXT PRIMARY KEY,
    value  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id       TEXT PRIMARY KEY,
    first_name        TEXT NOT NULL,
    last_name         TEXT NOT NULL,
    email             TEXT NOT NULL,
    phone             TEXT NOT NULL,
    account_numbers   TEXT NOT NULL DEFAULT '[]',
    date_of_birth     TEXT NOT NULL DEFAULT '',
    nationality       TEXT NOT NULL DEFAULT '',
    address           TEXT NOT NULL DEFAULT '',
    city              TEXT NOT NULL DEFAULT '',
    state             TEXT NOT NULL DEFAULT '',
    zip_code          TEXT NOT NULL DEFAULT '',
    country           TEXT NOT NULL DEFAULT '',
    id_type           TEXT NOT NULL DEFAULT '',
    id_number         TEXT NOT NULL DEFAULT '',
    employment_status TEXT NOT NULL DEFAULT '',
    annual_income     TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS accounts (
    account_number  TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL,
    balance         TEXT NOT NULL,
    transaction_ids TEXT NOT NULL DEFAULT '[]',
    is_active       INTEGER NOT NULL,
    type            TEXT NOT NULL,
    interest_rate   TEXT,
    minimum_balance TEXT,
    overdraft_limit TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   TEXT PRIMARY KEY,
    timestamp        TEXT NOT NULL,
    amount           TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    source_account   TEXT,
    target_account   TEXT,
    description      TEXT,
    status           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id           TEXT PRIMARY KEY,
    customer_id       TEXT NOT NULL,
    principal         TEXT NOT NULL,
    interest_rate     TEXT NOT NULL,
    duration_months   INTEGER NOT NULL,
    emi               TEXT NOT NULL,
    remaining_balance TEXT NOT NULL,
    status            TEXT NOT NULL,
    rejection_reason  TEXT
);

CREATE TABLE IF NOT EXISTS cards (
    card_number           TEXT PRIMARY KEY,
    customer_id           TEXT NOT NULL,
    pin_hash              TEXT NOT NULL,
    expiry                TEXT NOT NULL,
    is_blocked            INTEGER NOT NULL,
    type                  TEXT NOT NULL,
    linked_account_number TEXT,
    credit_limit          TEXT,
    outstanding_balance   TEXT
);

CREATE TABLE IF NOT EXISTS users (
    username           TEXT PRIMARY KEY,
    password_hash      TEXT NOT NULL,
    role               TEXT NOT NULL,
    linked_customer_id TEXT
);
"""


class DataStore:
    """
    Handles persistence of the entire bank state using a SQLite database.

    The public interface (save / load) is identical to the previous JSON
    implementation so no other part of the application needs to change.

    Attributes:
        _filepath (str): Path to the SQLite ``.db`` file.
    """

    def __init__(self, filepath: str = DEFAULT_PATH) -> None:
        """
        Create a DataStore pointing at the given SQLite database file.

        Args:
            filepath: Path to the ``.db`` file used for persistence.
                      Defaults to ``data/bank.db``.
        """
        self._filepath = filepath

    # ================================================================== #
    #  Internal helpers
    # ================================================================== #

    def _connect(self) -> sqlite3.Connection:
        """
        Open and return a connection to the SQLite database.

        Creates the ``data/`` directory if it does not exist.
        Rows are returned as sqlite3.Row objects (accessible by column name).
        """
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
        conn = sqlite3.connect(self._filepath)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all tables and add any missing columns for existing databases."""
        conn.executescript(_SCHEMA)
        # Add new customer columns to existing databases that predate the KYC update
        new_columns = [
            ("date_of_birth", "TEXT NOT NULL DEFAULT ''"),
            ("nationality",   "TEXT NOT NULL DEFAULT ''"),
            ("address",       "TEXT NOT NULL DEFAULT ''"),
            ("city",          "TEXT NOT NULL DEFAULT ''"),
            ("state",         "TEXT NOT NULL DEFAULT ''"),
            ("zip_code",      "TEXT NOT NULL DEFAULT ''"),
            ("country",       "TEXT NOT NULL DEFAULT ''"),
            ("id_type",       "TEXT NOT NULL DEFAULT ''"),
            ("id_number",     "TEXT NOT NULL DEFAULT ''"),
            ("employment_status", "TEXT NOT NULL DEFAULT ''"),
            ("annual_income", "TEXT NOT NULL DEFAULT ''"),
        ]
        existing = {row[1] for row in conn.execute("PRAGMA table_info(customers)")}
        for col, definition in new_columns:
            if col not in existing:
                conn.execute(f"ALTER TABLE customers ADD COLUMN {col} {definition}")
        conn.commit()

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
        Serialize the entire bank state and write it to the SQLite database.

        All rows are deleted and reinserted on each save to guarantee
        consistency.  The database file and its parent directory are created
        automatically if they do not already exist.

        Args:
            bank: The Bank aggregate containing all domain entities.
            auth: The AuthService holding registered users and sessions.
            tx_manager: The TransactionManager holding all transactions.
        """
        conn = self._connect()
        self._create_tables(conn)

        conn.executescript("""
            DELETE FROM bank;
            DELETE FROM id_counters;
            DELETE FROM customers;
            DELETE FROM accounts;
            DELETE FROM transactions;
            DELETE FROM loans;
            DELETE FROM cards;
            DELETE FROM users;
        """)

        # Bank meta
        conn.execute(
            "INSERT INTO bank (id, bank_name, branch_code) VALUES (1, ?, ?)",
            (bank.bank_name, bank.branch_code),
        )

        # ID counters
        conn.executemany(
            "INSERT INTO id_counters (prefix, value) VALUES (?, ?)",
            list(bank.id_generator._counters.items()),
        )

        # Customers
        conn.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    cid, c.first_name, c.last_name, c.email, c.phone,
                    json.dumps(c.account_numbers),
                    getattr(c, "_date_of_birth", ""),
                    getattr(c, "_nationality", ""),
                    getattr(c, "_address", ""),
                    getattr(c, "_city", ""),
                    getattr(c, "_state", ""),
                    getattr(c, "_zip_code", ""),
                    getattr(c, "_country", ""),
                    getattr(c, "_id_type", ""),
                    getattr(c, "_id_number", ""),
                    getattr(c, "_employment_status", ""),
                    getattr(c, "_annual_income", ""),
                )
                for cid, c in bank._customers.items()
            ],
        )

        # Accounts
        account_rows = []
        for anum, a in bank._accounts.items():
            if isinstance(a, SavingsAccount):
                account_rows.append((
                    anum, a.customer_id, str(a.balance),
                    json.dumps(a.transaction_ids), int(a.is_active),
                    "savings", str(a.interest_rate), str(a.minimum_balance), None,
                ))
            else:
                account_rows.append((
                    anum, a.customer_id, str(a.balance),
                    json.dumps(a.transaction_ids), int(a.is_active),
                    "checking", None, None, str(a.overdraft_limit),
                ))
        conn.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", account_rows)

        # Transactions
        tx_rows = []
        for tid, t in tx_manager._transactions.items():
            d = t.serialize()
            tx_rows.append((
                tid, d["timestamp"], str(d["amount"]), d["transaction_type"],
                d.get("source_account"), d.get("target_account"),
                d.get("description", ""), d["status"],
            ))
        conn.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tx_rows)

        # Loans
        conn.executemany(
            "INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (lid, loan.customer_id, str(loan.principal),
                 str(loan.interest_rate), loan.duration_months,
                 str(loan.emi), str(loan.remaining_balance),
                 loan.status.value, loan.rejection_reason)
                for lid, loan in bank._loans.items()
            ],
        )

        # Cards
        card_rows = []
        for cnum, card in bank._cards.items():
            if isinstance(card, DebitCard):
                card_rows.append((
                    cnum, card.issued_to_customer_id, card._pin_hash,
                    card.expiry.isoformat(), int(card.is_blocked),
                    "debit", card.linked_account_number, None, None,
                ))
            else:
                card_rows.append((
                    cnum, card.issued_to_customer_id, card._pin_hash,
                    card.expiry.isoformat(), int(card.is_blocked),
                    "credit", None, str(card.credit_limit), str(card.outstanding_balance),
                ))
        conn.executemany("INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", card_rows)

        # Users
        conn.executemany(
            "INSERT INTO users VALUES (?, ?, ?, ?)",
            [
                (uname, u._password_hash, u.role.value, u.linked_customer_id)
                for uname, u in auth._users.items()
            ],
        )

        conn.commit()
        conn.close()

    # ================================================================== #
    #  LOAD
    # ================================================================== #

    def load(self) -> tuple:
        """
        Read state from the SQLite database and reconstruct all domain objects.

        If the database file does not exist, checks for a legacy JSON file and
        migrates it automatically.  If neither exists, bootstraps a fresh state
        with a default admin account.

        Returns:
            (bank, auth_service, transaction_manager) tuple ready for use.
        """
        if not os.path.exists(self._filepath):
            if os.path.exists(LEGACY_JSON_PATH):
                return self._migrate_from_json()
            return self._create_fresh_state()

        conn = self._connect()
        self._create_tables(conn)

        row = conn.execute("SELECT * FROM bank WHERE id = 1").fetchone()
        if row is None:
            conn.close()
            return self._create_fresh_state()

        bank = Bank(row["bank_name"], row["branch_code"])

        for r in conn.execute("SELECT * FROM id_counters"):
            bank._id_generator._counters[r["prefix"]] = r["value"]

        for r in conn.execute("SELECT * FROM customers"):
            customer = Customer.__new__(Customer)
            customer._customer_id = r["customer_id"]
            customer._first_name = r["first_name"]
            customer._last_name = r["last_name"]
            customer._email = r["email"]
            customer._phone = r["phone"]
            customer._account_numbers = json.loads(r["account_numbers"])
            customer._date_of_birth = r["date_of_birth"] if "date_of_birth" in r.keys() else ""
            customer._nationality = r["nationality"] if "nationality" in r.keys() else ""
            customer._address = r["address"] if "address" in r.keys() else ""
            customer._city = r["city"] if "city" in r.keys() else ""
            customer._state = r["state"] if "state" in r.keys() else ""
            customer._zip_code = r["zip_code"] if "zip_code" in r.keys() else ""
            customer._country = r["country"] if "country" in r.keys() else ""
            customer._id_type = r["id_type"] if "id_type" in r.keys() else ""
            customer._id_number = r["id_number"] if "id_number" in r.keys() else ""
            customer._employment_status = r["employment_status"] if "employment_status" in r.keys() else ""
            customer._annual_income = r["annual_income"] if "annual_income" in r.keys() else ""
            bank._customers[r["customer_id"]] = customer

        for r in conn.execute("SELECT * FROM accounts"):
            if r["type"] == "savings":
                account = SavingsAccount.__new__(SavingsAccount)
                account._account_number = r["account_number"]
                account._customer_id = r["customer_id"]
                account._balance = Decimal(r["balance"])
                account._transaction_ids = json.loads(r["transaction_ids"])
                account._is_active = bool(r["is_active"])
                account._interest_rate = Decimal(r["interest_rate"])
                account._minimum_balance = Decimal(r["minimum_balance"])
            else:
                account = CurrentAccount.__new__(CurrentAccount)
                account._account_number = r["account_number"]
                account._customer_id = r["customer_id"]
                account._balance = Decimal(r["balance"])
                account._transaction_ids = json.loads(r["transaction_ids"])
                account._is_active = bool(r["is_active"])
                account._overdraft_limit = Decimal(r["overdraft_limit"])
                account._minimum_balance = Decimal("0.00")
            bank._accounts[r["account_number"]] = account

        tx_manager = TransactionManager()
        for r in conn.execute("SELECT * FROM transactions"):
            tx = Transaction.__new__(Transaction)
            tx._transaction_id = r["transaction_id"]
            tx._timestamp = datetime.fromisoformat(r["timestamp"])
            tx._amount = Decimal(r["amount"])
            tx._transaction_type = TransactionType(r["transaction_type"])
            tx._source_account = r["source_account"]
            tx._target_account = r["target_account"]
            tx._description = r["description"] or ""
            tx._status = TransactionStatus(r["status"])
            tx_manager._transactions[r["transaction_id"]] = tx

        for r in conn.execute("SELECT * FROM loans"):
            loan = Loan.__new__(Loan)
            loan._loan_id = r["loan_id"]
            loan._customer_id = r["customer_id"]
            loan._principal = Decimal(r["principal"])
            loan._interest_rate = Decimal(r["interest_rate"])
            loan._duration_months = r["duration_months"]
            loan._emi = Decimal(r["emi"])
            loan._remaining_balance = Decimal(r["remaining_balance"])
            loan._status = LoanStatus(r["status"])
            loan._rejection_reason = r["rejection_reason"]
            bank._loans[r["loan_id"]] = loan

        for r in conn.execute("SELECT * FROM cards"):
            if r["type"] == "debit":
                card = DebitCard.__new__(DebitCard)
                card._card_number = r["card_number"]
                card._issued_to_customer_id = r["customer_id"]
                card._pin_hash = r["pin_hash"]
                card._expiry = date.fromisoformat(r["expiry"])
                card._is_blocked = bool(r["is_blocked"])
                card._linked_account_number = r["linked_account_number"]
            else:
                card = CreditCard.__new__(CreditCard)
                card._card_number = r["card_number"]
                card._issued_to_customer_id = r["customer_id"]
                card._pin_hash = r["pin_hash"]
                card._expiry = date.fromisoformat(r["expiry"])
                card._is_blocked = bool(r["is_blocked"])
                card._credit_limit = Decimal(r["credit_limit"])
                card._outstanding_balance = Decimal(r["outstanding_balance"])
            bank._cards[r["card_number"]] = card

        auth = AuthService()
        for r in conn.execute("SELECT * FROM users"):
            user = User.__new__(User)
            user._username = r["username"]
            user._password_hash = r["password_hash"]
            user._role = Role(r["role"])
            user._linked_customer_id = r["linked_customer_id"]
            auth._users[r["username"]] = user

        conn.close()
        return bank, auth, tx_manager

    # ================================================================== #
    #  FRESH STATE
    # ================================================================== #

    def _create_fresh_state(self) -> tuple:
        """
        Bootstrap a brand-new bank state when no database or JSON file exists.

        Registers a built-in ``admin`` / ``admin123`` account so the app is
        immediately usable on first launch, then saves the state to the DB.

        Returns:
            (bank, auth_service, transaction_manager) tuple with default state.
        """
        bank = Bank("NovaBank", "BR-001")
        auth = AuthService()
        tx_manager = TransactionManager()
        auth.register("admin", "admin123", Role.ADMIN)
        self.save(bank, auth, tx_manager)
        return bank, auth, tx_manager

    # ================================================================== #
    #  MIGRATION
    # ================================================================== #

    def _migrate_from_json(self) -> tuple:
        """
        Read the legacy JSON file and import it into the new SQLite database.

        Called automatically on first run when ``data/bank_state.json`` exists
        but ``data/bank.db`` does not.  After migration the JSON file is kept
        as a backup and the app continues using SQLite from that point on.

        Returns:
            (bank, auth_service, transaction_manager) reconstructed from JSON.
        """
        with open(LEGACY_JSON_PATH, "r") as f:
            state = json.load(f)

        if not state or "bank" not in state:
            return self._create_fresh_state()

        bank_data = state["bank"]
        bank = Bank(bank_data["bank_name"], bank_data["branch_code"])
        bank._id_generator._counters = {
            k: int(v) for k, v in bank_data["id_counters"].items()
        }

        for cid, cdata in state.get("customers", {}).items():
            customer = Customer.__new__(Customer)
            customer._customer_id = cid
            customer._first_name = cdata["first_name"]
            customer._last_name = cdata["last_name"]
            customer._email = cdata["email"]
            customer._phone = cdata["phone"]
            customer._account_numbers = cdata.get("account_numbers", [])
            bank._customers[cid] = customer

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
                account._overdraft_limit = Decimal(adata.get("overdraft_limit", "0.00"))
                account._minimum_balance = Decimal("0.00")
            bank._accounts[anum] = account

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

        auth = AuthService()
        for uname, udata in state.get("users", {}).items():
            user = User.__new__(User)
            user._username = uname
            user._password_hash = udata["password_hash"]
            user._role = Role(udata["role"])
            user._linked_customer_id = udata.get("linked_customer_id")
            auth._users[uname] = user

        self.save(bank, auth, tx_manager)
        return bank, auth, tx_manager
