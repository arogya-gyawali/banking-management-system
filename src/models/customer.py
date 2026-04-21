"""
customer.py — Customer entity for the Banking Management System.

A Customer represents an individual bank client.  Each customer has a
unique ID, personal details, and references (by account number) to the
accounts they own.  The Bank class is responsible for creating and
storing Customer instances.
"""

import re
from typing import List

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Customer:
    """
    A bank customer with personal information and linked account numbers.

    Attributes:
        _customer_id (str):
            Unique identifier (e.g. "CUST-0001").
        _first_name (str):
            Customer's first (given) name.
        _last_name (str):
            Customer's last (family) name.
        _email (str):
            Contact email address.
        _phone (str):
            Contact phone number.
        _account_numbers (List[str]):
            Account numbers owned by this customer.
    """

    def __init__(
        self,
        customer_id: str,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
    ) -> None:
        """
        Create a new Customer.

        Args:
            customer_id: Unique ID assigned by the IdGenerator.
            first_name: Given name.
            last_name: Family name.
            email: Contact email.
            phone: Contact phone number.

        Raises:
            ValueError: If any required field is blank.
        """
        if not first_name or not first_name.strip():
            raise ValueError("First name cannot be blank.")
        if not last_name or not last_name.strip():
            raise ValueError("Last name cannot be blank.")
        if not email or not email.strip():
            raise ValueError("Email cannot be blank.")
        if not _EMAIL_RE.match(email.strip()):
            raise ValueError("Invalid email address. Must be in the format user@example.com.")
        if not phone or not phone.strip():
            raise ValueError("Phone cannot be blank.")

        self._customer_id: str = customer_id
        self._first_name: str = first_name.strip()
        self._last_name: str = last_name.strip()
        self._email: str = email.strip()
        self._phone: str = phone.strip()
        self._account_numbers: List[str] = []

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def customer_id(self) -> str:
        """Return the unique customer identifier."""
        return self._customer_id

    @property
    def first_name(self) -> str:
        """Return the customer's first name."""
        return self._first_name

    @property
    def last_name(self) -> str:
        """Return the customer's last name."""
        return self._last_name

    @property
    def full_name(self) -> str:
        """Return the customer's full name."""
        return f"{self._first_name} {self._last_name}"

    @property
    def email(self) -> str:
        """Return the contact email."""
        return self._email

    @property
    def phone(self) -> str:
        """Return the contact phone number."""
        return self._phone

    @property
    def account_numbers(self) -> List[str]:
        """Return a copy of the linked account numbers list."""
        return list(self._account_numbers)

    # ------------------------------------------------------------------ #
    #  Account linking
    # ------------------------------------------------------------------ #

    def add_account(self, account_number: str) -> None:
        """
        Link an account to this customer.

        Args:
            account_number: The account number to link.

        Raises:
            ValueError: If the account is already linked.
        """
        if account_number in self._account_numbers:
            raise ValueError(
                f"Account {account_number} is already linked to "
                f"customer {self._customer_id}."
            )
        self._account_numbers.append(account_number)

    def remove_account(self, account_number: str) -> None:
        """
        Unlink an account from this customer.

        Args:
            account_number: The account number to remove.

        Raises:
            ValueError: If the account is not currently linked.
        """
        if account_number not in self._account_numbers:
            raise ValueError(
                f"Account {account_number} is not linked to "
                f"customer {self._customer_id}."
            )
        self._account_numbers.remove(account_number)

    # ------------------------------------------------------------------ #
    #  Profile updates
    # ------------------------------------------------------------------ #

    def update_details(self, **kwargs: str) -> None:
        """
        Update one or more personal details.

        Accepted keyword arguments: first_name, last_name, email, phone.
        Unknown keys are silently ignored.

        Args:
            **kwargs: Field names mapped to their new values.

        Raises:
            ValueError: If a provided value is blank.
        """
        allowed = {"first_name", "last_name", "email", "phone"}
        for key, value in kwargs.items():
            if key in allowed:
                if not value or not value.strip():
                    raise ValueError(f"{key} cannot be blank.")
                if key == "email" and not _EMAIL_RE.match(value.strip()):
                    raise ValueError("Invalid email address. Must be in the format user@example.com.")
                setattr(self, f"_{key}", value.strip())

    # ------------------------------------------------------------------ #
    #  Dunder methods
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"Customer(id={self._customer_id!r}, "
            f"name={self.full_name!r}, "
            f"accounts={len(self._account_numbers)})"
        )

    def __str__(self) -> str:
        return (
            f"[{self._customer_id}] {self.full_name} "
            f"({len(self._account_numbers)} account(s))"
        )