"""Unit tests for AuthService."""

import pytest

from src.services.auth_service import AuthService
from src.utils.enums import Role


@pytest.fixture
def auth():
    return AuthService()


@pytest.fixture
def registered_auth():
    a = AuthService()
    a.register("alice", "pass123", Role.CUSTOMER, "C-001")
    a.register("admin", "admin123", Role.ADMIN)
    return a


class TestRegister:
    def test_register_returns_user(self, auth):
        user = auth.register("bob", "secret", Role.CUSTOMER)
        assert user.username == "bob"

    def test_register_duplicate_raises(self, auth):
        auth.register("bob", "secret", Role.CUSTOMER)
        with pytest.raises(ValueError, match="already taken"):
            auth.register("bob", "other", Role.CUSTOMER)

    def test_registered_user_has_correct_role(self, auth):
        user = auth.register("alice", "pw", Role.ADMIN)
        assert user.role == Role.ADMIN

    def test_registered_user_links_customer_id(self, auth):
        user = auth.register("alice", "pw", Role.CUSTOMER, "C-999")
        assert user.linked_customer_id == "C-999"


class TestLogin:
    def test_valid_login_returns_token(self, registered_auth):
        token = registered_auth.login("alice", "pass123")
        assert isinstance(token, str) and len(token) > 0

    def test_wrong_password_raises(self, registered_auth):
        with pytest.raises(ValueError, match="Invalid"):
            registered_auth.login("alice", "wrong")

    def test_unknown_user_raises(self, registered_auth):
        with pytest.raises(ValueError):
            registered_auth.login("nobody", "pw")

    def test_each_login_produces_unique_token(self, registered_auth):
        t1 = registered_auth.login("alice", "pass123")
        t2 = registered_auth.login("alice", "pass123")
        assert t1 != t2


class TestLogout:
    def test_logout_invalidates_token(self, registered_auth):
        token = registered_auth.login("alice", "pass123")
        registered_auth.logout(token)
        assert registered_auth.get_current_user(token) is None

    def test_logout_invalid_token_raises(self, registered_auth):
        with pytest.raises(KeyError):
            registered_auth.logout("bad-token")


class TestAuthorize:
    def test_customer_can_access_customer_route(self, registered_auth):
        token = registered_auth.login("alice", "pass123")
        user = registered_auth.authorize(token, Role.CUSTOMER)
        assert user.username == "alice"

    def test_admin_can_access_customer_route(self, registered_auth):
        token = registered_auth.login("admin", "admin123")
        user = registered_auth.authorize(token, Role.CUSTOMER)
        assert user.username == "admin"

    def test_customer_cannot_access_admin_route(self, registered_auth):
        token = registered_auth.login("alice", "pass123")
        with pytest.raises(PermissionError):
            registered_auth.authorize(token, Role.ADMIN)

    def test_invalid_token_raises(self, registered_auth):
        with pytest.raises(PermissionError, match="Invalid"):
            registered_auth.authorize("fake-token", Role.CUSTOMER)


class TestGetCurrentUser:
    def test_returns_user_for_valid_token(self, registered_auth):
        token = registered_auth.login("alice", "pass123")
        user = registered_auth.get_current_user(token)
        assert user.username == "alice"

    def test_returns_none_for_invalid_token(self, registered_auth):
        assert registered_auth.get_current_user("no-such-token") is None
