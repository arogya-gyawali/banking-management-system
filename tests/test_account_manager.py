"""Unit tests for AccountManager (deposit, withdraw, transfer)."""

import pytest
from decimal import Decimal

from src.models.bank import Bank
from src.models.customer import Customer
from src.services.account_manager import AccountManager
from src.services.transaction_manager import TransactionManager
from src.utils.enums import AccountType, TransactionType


@pytest.fixture
def setup():
    bank = Bank("Test Bank", "TST")
    tx_manager = TransactionManager()
    am = AccountManager(bank, tx_manager)

    cust = Customer("C-001", "Jane", "Doe", "jane@test.com", "555-0001")
    bank.add_customer(cust)

    cust2 = Customer("C-002", "John", "Smith", "john@test.com", "555-0002")
    bank.add_customer(cust2)

    return bank, tx_manager, am


class TestCreateAccount:
    def test_creates_savings_account(self, setup):
        bank, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("200.00"))
        assert acc.balance == Decimal("200.00")
        assert bank.find_account(acc.account_number) is acc

    def test_creates_checking_account(self, setup):
        bank, _, am = setup
        acc = am.create_account("C-001", AccountType.CHECKING, Decimal("50.00"))
        assert acc.balance == Decimal("50.00")

    def test_initial_deposit_logged_as_transaction(self, setup):
        _, tx_manager, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("200.00"))
        history = tx_manager.get_transactions_for_account(acc.account_number)
        assert len(history) == 1
        assert history[0].transaction_type == TransactionType.DEPOSIT

    def test_zero_deposit_no_transaction_logged(self, setup):
        _, tx_manager, am = setup
        acc = am.create_account("C-001", AccountType.CHECKING, Decimal("0.00"))
        history = tx_manager.get_transactions_for_account(acc.account_number)
        assert len(history) == 0

    def test_unknown_customer_raises(self, setup):
        _, _, am = setup
        with pytest.raises(KeyError):
            am.create_account("NO-SUCH", AccountType.SAVINGS, Decimal("100.00"))


class TestDeposit:
    def test_deposit_increases_balance(self, setup):
        bank, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("200.00"))
        am.deposit(acc.account_number, Decimal("300.00"))
        assert acc.balance == Decimal("500.00")

    def test_deposit_returns_transaction(self, setup):
        _, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("200.00"))
        tx = am.deposit(acc.account_number, Decimal("100.00"), "Test deposit")
        assert tx.transaction_type == TransactionType.DEPOSIT
        assert tx.amount == Decimal("100.00")

    def test_deposit_logged_in_transaction_manager(self, setup):
        _, tx_manager, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("200.00"))
        am.deposit(acc.account_number, Decimal("50.00"))
        history = tx_manager.get_transactions_for_account(acc.account_number)
        types = [t.transaction_type for t in history]
        assert TransactionType.DEPOSIT in types

    def test_deposit_to_unknown_account_raises(self, setup):
        _, _, am = setup
        with pytest.raises(KeyError):
            am.deposit("ACCT-FAKE", Decimal("100.00"))


class TestWithdraw:
    def test_withdraw_decreases_balance(self, setup):
        _, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("500.00"))
        am.withdraw(acc.account_number, Decimal("200.00"))
        assert acc.balance == Decimal("300.00")

    def test_withdraw_returns_transaction(self, setup):
        _, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("500.00"))
        tx = am.withdraw(acc.account_number, Decimal("100.00"))
        assert tx.transaction_type == TransactionType.WITHDRAWAL

    def test_withdraw_insufficient_funds_raises(self, setup):
        _, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("100.00"))
        with pytest.raises(ValueError):
            am.withdraw(acc.account_number, Decimal("50.00"))  # would go below $100 min


class TestTransfer:
    def test_transfer_moves_funds(self, setup):
        bank, _, am = setup
        src = am.create_account("C-001", AccountType.SAVINGS, Decimal("500.00"))
        dst = am.create_account("C-002", AccountType.SAVINGS, Decimal("200.00"))
        am.transfer(src.account_number, dst.account_number, Decimal("100.00"))
        assert src.balance == Decimal("400.00")
        assert dst.balance == Decimal("300.00")

    def test_transfer_returns_two_transactions(self, setup):
        _, _, am = setup
        src = am.create_account("C-001", AccountType.SAVINGS, Decimal("500.00"))
        dst = am.create_account("C-002", AccountType.SAVINGS, Decimal("200.00"))
        debit_tx, credit_tx = am.transfer(src.account_number, dst.account_number, Decimal("50.00"))
        assert debit_tx.transaction_type == TransactionType.TRANSFER
        assert credit_tx.transaction_type == TransactionType.TRANSFER

    def test_transfer_same_account_raises(self, setup):
        _, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("200.00"))
        with pytest.raises(ValueError, match="same account"):
            am.transfer(acc.account_number, acc.account_number, Decimal("50.00"))

    def test_transfer_insufficient_funds_rolls_back(self, setup):
        _, _, am = setup
        src = am.create_account("C-001", AccountType.SAVINGS, Decimal("100.00"))
        dst = am.create_account("C-002", AccountType.SAVINGS, Decimal("200.00"))
        with pytest.raises(ValueError):
            am.transfer(src.account_number, dst.account_number, Decimal("50.00"))
        # src balance should be unchanged
        assert src.balance == Decimal("100.00")


class TestGetBalance:
    def test_returns_current_balance(self, setup):
        _, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("250.00"))
        assert am.get_balance(acc.account_number) == Decimal("250.00")


class TestGetTransactionHistory:
    def test_returns_transactions_in_order(self, setup):
        _, _, am = setup
        acc = am.create_account("C-001", AccountType.SAVINGS, Decimal("200.00"))
        am.deposit(acc.account_number, Decimal("50.00"))
        am.deposit(acc.account_number, Decimal("75.00"))
        history = am.get_transaction_history(acc.account_number)
        assert len(history) == 3  # initial + 2 deposits
