"""
customer.py — Customer entity for the Banking Management System.
"""

import re
from datetime import date
from typing import List, Optional

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

EMPLOYMENT_STATUSES = ("Employed", "Self-Employed", "Unemployed", "Student", "Retired")
INCOME_RANGES = ("Under $25,000", "$25,000–$50,000", "$50,000–$100,000", "$100,000–$250,000", "Over $250,000")
ID_TYPES = ("Passport", "National ID", "Driver's License")


class Customer:
    """
    A bank customer with personal, contact, identity, and financial details.

    Attributes:
        _customer_id (str): Unique identifier (e.g. "CUST-0001").
        _first_name (str): Given name.
        _last_name (str): Family name.
        _email (str): Contact email.
        _phone (str): Contact phone number.
        _date_of_birth (str): ISO date string (YYYY-MM-DD).
        _nationality (str): Country of citizenship.
        _address (str): Street address.
        _city (str): City.
        _state (str): State or province.
        _zip_code (str): Postal / ZIP code.
        _country (str): Country of residence.
        _id_type (str): Government ID type.
        _id_number (str): Government ID number.
        _employment_status (str): Employment category.
        _annual_income (str): Annual income range.
        _account_numbers (List[str]): Account numbers owned by this customer.
    """

    def __init__(
        self,
        customer_id: str,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        date_of_birth: str,
        nationality: str,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        country: str,
        id_type: str,
        id_number: str,
        employment_status: str,
        annual_income: str,
    ) -> None:
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
        if not date_of_birth:
            raise ValueError("Date of birth cannot be blank.")
        try:
            dob = date.fromisoformat(date_of_birth)
        except ValueError:
            raise ValueError("Date of birth must be in YYYY-MM-DD format.")
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise ValueError("Customer must be at least 18 years old.")
        if dob >= today:
            raise ValueError("Date of birth must be in the past.")
        if not nationality or not nationality.strip():
            raise ValueError("Nationality cannot be blank.")
        if not address or not address.strip():
            raise ValueError("Address cannot be blank.")
        if not city or not city.strip():
            raise ValueError("City cannot be blank.")
        if not state or not state.strip():
            raise ValueError("State cannot be blank.")
        if not zip_code or not zip_code.strip():
            raise ValueError("ZIP code cannot be blank.")
        if not country or not country.strip():
            raise ValueError("Country cannot be blank.")
        if id_type not in ID_TYPES:
            raise ValueError(f"ID type must be one of: {', '.join(ID_TYPES)}.")
        if not id_number or not id_number.strip():
            raise ValueError("ID number cannot be blank.")
        if employment_status not in EMPLOYMENT_STATUSES:
            raise ValueError(f"Employment status must be one of: {', '.join(EMPLOYMENT_STATUSES)}.")
        if annual_income not in INCOME_RANGES:
            raise ValueError(f"Annual income must be one of: {', '.join(INCOME_RANGES)}.")

        self._customer_id: str = customer_id
        self._first_name: str = first_name.strip()
        self._last_name: str = last_name.strip()
        self._email: str = email.strip()
        self._phone: str = phone.strip()
        self._date_of_birth: str = date_of_birth
        self._nationality: str = nationality.strip()
        self._address: str = address.strip()
        self._city: str = city.strip()
        self._state: str = state.strip()
        self._zip_code: str = zip_code.strip()
        self._country: str = country.strip()
        self._id_type: str = id_type
        self._id_number: str = id_number.strip()
        self._employment_status: str = employment_status
        self._annual_income: str = annual_income
        self._account_numbers: List[str] = []

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def first_name(self) -> str:
        return self._first_name

    @property
    def last_name(self) -> str:
        return self._last_name

    @property
    def full_name(self) -> str:
        return f"{self._first_name} {self._last_name}"

    @property
    def email(self) -> str:
        return self._email

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def date_of_birth(self) -> str:
        return self._date_of_birth

    @property
    def nationality(self) -> str:
        return self._nationality

    @property
    def address(self) -> str:
        return self._address

    @property
    def city(self) -> str:
        return self._city

    @property
    def state(self) -> str:
        return self._state

    @property
    def zip_code(self) -> str:
        return self._zip_code

    @property
    def country(self) -> str:
        return self._country

    @property
    def id_type(self) -> str:
        return self._id_type

    @property
    def id_number(self) -> str:
        return self._id_number

    @property
    def employment_status(self) -> str:
        return self._employment_status

    @property
    def annual_income(self) -> str:
        return self._annual_income

    @property
    def account_numbers(self) -> List[str]:
        return list(self._account_numbers)

    # ------------------------------------------------------------------ #
    #  Account linking
    # ------------------------------------------------------------------ #

    def add_account(self, account_number: str) -> None:
        if account_number in self._account_numbers:
            raise ValueError(
                f"Account {account_number} is already linked to customer {self._customer_id}."
            )
        self._account_numbers.append(account_number)

    def remove_account(self, account_number: str) -> None:
        if account_number not in self._account_numbers:
            raise ValueError(
                f"Account {account_number} is not linked to customer {self._customer_id}."
            )
        self._account_numbers.remove(account_number)

    # ------------------------------------------------------------------ #
    #  Profile updates
    # ------------------------------------------------------------------ #

    def update_details(self, **kwargs: str) -> None:
        """Update one or more personal details."""
        allowed = {
            "first_name", "last_name", "email", "phone",
            "address", "city", "state", "zip_code", "country",
            "employment_status", "annual_income", "nationality",
        }
        for key, value in kwargs.items():
            if key in allowed:
                if not value or not str(value).strip():
                    raise ValueError(f"{key} cannot be blank.")
                if key == "email" and not _EMAIL_RE.match(value.strip()):
                    raise ValueError("Invalid email address. Must be in the format user@example.com.")
                if key == "employment_status" and value not in EMPLOYMENT_STATUSES:
                    raise ValueError(f"Employment status must be one of: {', '.join(EMPLOYMENT_STATUSES)}.")
                if key == "annual_income" and value not in INCOME_RANGES:
                    raise ValueError(f"Annual income must be one of: {', '.join(INCOME_RANGES)}.")
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
