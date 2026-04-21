"""Unit tests for SavingsAccount and CurrentAccount."""

import pytest
from decimal import Decimal

from src.models.account import SavingsAccount, CurrentAccount
from src.utils.enums import TransactionType


# ── SavingsAccount ──────────────────────────────────────────────────────────

class TestSavingsAccountCreation:
    def test_creates_with_valid_deposit(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("200.00"))
        assert acc.balance == Decimal("200.00")
        assert acc.is_active

    def test_raises_if_deposit_below_minimum(self):
        with pytest.raises(ValueError, match="minimum balance"):
            SavingsAccount("ACCT-001", "C-001", Decimal("50.00"))

    def test_raises_on_negative_deposit(self):
        with pytest.raises(ValueError):
            SavingsAccount("ACCT-001", "C-001", Decimal("-1.00"))

    def test_default_interest_rate(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("100.00"))
        assert acc.interest_rate == Decimal("0.025")


class TestSavingsAccountDeposit:
    def setup_method(self):
        self.acc = SavingsAccount("ACCT-001", "C-001", Decimal("100.00"))

    def test_deposit_increases_balance(self):
        self.acc.deposit(Decimal("50.00"))
        assert self.acc.balance == Decimal("150.00")

    def test_deposit_returns_correct_metadata(self):
        meta = self.acc.deposit(Decimal("50.00"), "Paycheck")
        assert meta["transaction_type"] == TransactionType.DEPOSIT
        assert meta["amount"] == Decimal("50.00")
        assert meta["description"] == "Paycheck"

    def test_deposit_zero_raises(self):
        with pytest.raises(ValueError):
            self.acc.deposit(Decimal("0.00"))

    def test_deposit_negative_raises(self):
        with pytest.raises(ValueError):
            self.acc.deposit(Decimal("-10.00"))

    def test_deposit_on_closed_account_raises(self):
        self.acc.close()
        with pytest.raises(RuntimeError, match="closed"):
            self.acc.deposit(Decimal("10.00"))


class TestSavingsAccountWithdrawal:
    def setup_method(self):
        self.acc = SavingsAccount("ACCT-001", "C-001", Decimal("500.00"))

    def test_withdraw_decreases_balance(self):
        self.acc.withdraw(Decimal("200.00"))
        assert self.acc.balance == Decimal("300.00")

    def test_withdraw_returns_correct_metadata(self):
        meta = self.acc.withdraw(Decimal("100.00"), "Rent")
        assert meta["transaction_type"] == TransactionType.WITHDRAWAL
        assert meta["amount"] == Decimal("100.00")

    def test_withdraw_below_minimum_raises(self):
        with pytest.raises(ValueError, match="minimum balance"):
            self.acc.withdraw(Decimal("450.00"))  # leaves $50, below $100 min

    def test_withdraw_zero_raises(self):
        with pytest.raises(ValueError):
            self.acc.withdraw(Decimal("0.00"))

    def test_withdraw_on_closed_account_raises(self):
        self.acc.close()
        with pytest.raises(RuntimeError, match="closed"):
            self.acc.withdraw(Decimal("10.00"))


class TestSavingsAccountInterest:
    def test_apply_interest_increases_balance(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("1000.00"))
        acc.apply_interest()
        assert acc.balance == Decimal("1025.00")

    def test_apply_interest_metadata(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("1000.00"))
        meta = acc.apply_interest()
        assert meta["transaction_type"] == TransactionType.INTEREST
        assert meta["amount"] == Decimal("25.00")

    def test_apply_interest_on_closed_raises(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("100.00"))
        acc.close()
        with pytest.raises(RuntimeError):
            acc.apply_interest()


class TestSavingsAccountClose:
    def test_close_deactivates_account(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("100.00"))
        acc.close()
        assert not acc.is_active

    def test_close_twice_raises(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("100.00"))
        acc.close()
        with pytest.raises(RuntimeError, match="already closed"):
            acc.close()


# ── CurrentAccount ───────────────────────────────────────────────────────────

class TestCurrentAccountDeposit:
    def setup_method(self):
        self.acc = CurrentAccount("ACCT-002", "C-001", Decimal("0.00"))

    def test_deposit_from_zero(self):
        self.acc.deposit(Decimal("300.00"))
        assert self.acc.balance == Decimal("300.00")

    def test_deposit_zero_raises(self):
        with pytest.raises(ValueError):
            self.acc.deposit(Decimal("0.00"))


class TestCurrentAccountWithdrawal:
    def setup_method(self):
        self.acc = CurrentAccount("ACCT-002", "C-001", Decimal("200.00"))

    def test_withdraw_within_balance(self):
        self.acc.withdraw(Decimal("100.00"))
        assert self.acc.balance == Decimal("100.00")

    def test_withdraw_full_balance(self):
        self.acc.withdraw(Decimal("200.00"))
        assert self.acc.balance == Decimal("0.00")

    def test_withdraw_more_than_balance_raises(self):
        with pytest.raises(ValueError, match="Overdraft limit exceeded"):
            self.acc.withdraw(Decimal("201.00"))

    def test_overdraft_flag_false_when_balance_zero(self):
        meta = self.acc.withdraw(Decimal("200.00"))
        assert meta["overdraft_used"] is False

    def test_overdraft_allowed_when_explicit_limit_set(self):
        acc = CurrentAccount("ACCT-003", "C-001", Decimal("200.00"), overdraft_limit=Decimal("500.00"))
        acc.withdraw(Decimal("500.00"))  # balance → -$300, within $500 limit
        assert acc.balance == Decimal("-300.00")

    def test_withdraw_on_closed_account_raises(self):
        self.acc.close()
        with pytest.raises(RuntimeError):
            self.acc.withdraw(Decimal("10.00"))


class TestAccountTransactionIds:
    def test_add_transaction_id(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("100.00"))
        acc.add_transaction_id("TX-001")
        assert "TX-001" in acc.transaction_ids

    def test_transaction_ids_returns_copy(self):
        acc = SavingsAccount("ACCT-001", "C-001", Decimal("100.00"))
        acc.add_transaction_id("TX-001")
        ids = acc.transaction_ids
        ids.append("FAKE")
        assert "FAKE" not in acc.transaction_ids
