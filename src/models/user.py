"""
user.py — User entity for the Banking Management System.

A User holds login credentials and a role (CUSTOMER or ADMIN).
Customer-type users are linked to a Customer record by customer_id.
Passwords are stored as SHA-256 hashes — the plaintext is never kept.
"""

import hashlib
from typing import Optional

from src.utils.enums import Role


class User:
    """
    A system user with credentials and role-based access.

    Attributes:
        _username (str):
            Unique login name.
        _password_hash (str):
            SHA-256 hash of the user's password.
        _role (Role):
            CUSTOMER or ADMIN.
        _linked_customer_id (Optional[str]):
            Associated Customer ID (None for admin-only users).
    """

    def __init__(
        self,
        username: str,
        password: str,
        role: Role,
        linked_customer_id: Optional[str] = None,
    ) -> None:
        """
        Create a new User.

        Args:
            username: Unique login name.
            password: Plaintext password (will be hashed immediately).
            role: CUSTOMER or ADMIN.
            linked_customer_id: Customer ID to link, if applicable.

        Raises:
            ValueError: If username or password is blank.
        """
        if not username or not username.strip():
            raise ValueError("Username cannot be blank.")
        if not password:
            raise ValueError("Password cannot be blank.")

        self._username: str = username.strip()
        self._password_hash: str = self._hash(password)
        self._role: Role = role
        self._linked_customer_id: Optional[str] = linked_customer_id

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def username(self) -> str:
        return self._username

    @property
    def role(self) -> Role:
        return self._role

    @property
    def linked_customer_id(self) -> Optional[str]:
        return self._linked_customer_id

    # ------------------------------------------------------------------ #
    #  Password helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hash(value: str) -> str:
        """Return the SHA-256 hex digest of *value*."""
        return hashlib.sha256(value.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """
        Check whether *password* matches the stored hash.

        Args:
            password: Plaintext password to verify.

        Returns:
            True if correct, False otherwise.
        """
        return self._hash(password) == self._password_hash

    def set_password(self, password: str) -> None:
        """
        Replace the stored password hash.

        Args:
            password: New plaintext password.

        Raises:
            ValueError: If the new password is blank.
        """
        if not password:
            raise ValueError("Password cannot be blank.")
        self._password_hash = self._hash(password)

    # ------------------------------------------------------------------ #
    #  Dunder methods
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"User(username={self._username!r}, "
            f"role={self._role.value})"
        )

    def __str__(self) -> str:
        return f"[{self._username}] {self._role.value.upper()}"