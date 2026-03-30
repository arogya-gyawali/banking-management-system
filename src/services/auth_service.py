"""
auth_service.py — Authentication and authorisation service.

Provides user registration, login (returns a simple token), and
role-based authorisation checks.  Tokens are plain UUIDs mapped to
usernames — sufficient for a course project but not production-grade.
"""

import uuid
from typing import Dict, Optional

from src.models.user import User
from src.utils.enums import Role


class AuthService:
    """
    Manages user credentials, sessions, and access control.

    Attributes:
        _users (Dict[str, User]):
            Username → User mapping.
        _sessions (Dict[str, str]):
            Token → username mapping (active sessions).
    """

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, str] = {}

    # ------------------------------------------------------------------ #
    #  Registration
    # ------------------------------------------------------------------ #

    def register(
        self,
        username: str,
        password: str,
        role: Role,
        linked_customer_id: Optional[str] = None,
    ) -> User:
        """
        Create and store a new User.

        Args:
            username: Desired login name.
            password: Plaintext password (hashed inside User).
            role: CUSTOMER or ADMIN.
            linked_customer_id: Customer ID to associate (optional).

        Returns:
            The newly created User.

        Raises:
            ValueError: If the username is already taken.
        """
        if username in self._users:
            raise ValueError(f"Username '{username}' is already taken.")

        user = User(username, password, role, linked_customer_id)
        self._users[username] = user
        return user

    # ------------------------------------------------------------------ #
    #  Login / Logout
    # ------------------------------------------------------------------ #

    def login(self, username: str, password: str) -> str:
        """
        Authenticate a user and return a session token.

        Args:
            username: Login name.
            password: Plaintext password.

        Returns:
            A UUID session token string.

        Raises:
            ValueError: If the username does not exist or the
                        password is incorrect.
        """
        user = self._users.get(username)
        if user is None or not user.verify_password(password):
            raise ValueError("Invalid username or password.")

        token = str(uuid.uuid4())
        self._sessions[token] = username
        return token

    def logout(self, token: str) -> None:
        """
        Invalidate a session token.

        Args:
            token: The session token to revoke.

        Raises:
            KeyError: If the token is not active.
        """
        if token not in self._sessions:
            raise KeyError("Invalid or expired session token.")
        del self._sessions[token]

    # ------------------------------------------------------------------ #
    #  Authorisation
    # ------------------------------------------------------------------ #

    def authorize(self, token: str, required_role: Role) -> User:
        """
        Verify that a token belongs to a user with the required role.

        Args:
            token: Active session token.
            required_role: The minimum role needed.

        Returns:
            The authenticated User.

        Raises:
            PermissionError: If the token is invalid or the user
                             lacks the required role.
        """
        username = self._sessions.get(token)
        if username is None:
            raise PermissionError("Invalid or expired session token.")

        user = self._users[username]
        if user.role != required_role and user.role != Role.ADMIN:
            raise PermissionError(
                f"User '{username}' does not have "
                f"{required_role.value} access."
            )
        return user

    def get_current_user(self, token: str) -> Optional[User]:
        """
        Return the User associated with a token, or None.

        Args:
            token: Session token.

        Returns:
            The User if the token is valid, else None.
        """
        username = self._sessions.get(token)
        if username is None:
            return None
        return self._users.get(username)

    # ------------------------------------------------------------------ #
    #  Dunder
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"AuthService(users={len(self._users)}, "
            f"sessions={len(self._sessions)})"
        )