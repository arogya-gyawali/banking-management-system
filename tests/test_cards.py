"""Unit tests for DebitCard and CreditCard."""

import pytest
from decimal import Decimal

from src.models.card import DebitCard, CreditCard
from src.utils.enums import TransactionType


class TestCardCreation:
    def test_debit_card_created(self):
        card = DebitCard("CARD-001", "C-001", "1234", "ACCT-001")
        assert card.card_number == "CARD-001"
        assert not card.is_blocked

    def test_credit_card_created(self):
        card = CreditCard("CARD-002", "C-001", "5678", Decimal("5000.00"))
        assert card.credit_limit == Decimal("5000.00")
        assert card.outstanding_balance == Decimal("0.00")

    def test_pin_must_be_4_digits(self):
        with pytest.raises(ValueError, match="4 digits"):
            DebitCard("CARD-001", "C-001", "12", "ACCT-001")

    def test_pin_cannot_contain_letters(self):
        with pytest.raises(ValueError):
            DebitCard("CARD-001", "C-001", "12ab", "ACCT-001")


class TestPinValidation:
    def test_correct_pin_validates(self):
        card = DebitCard("CARD-001", "C-001", "1234", "ACCT-001")
        assert card.validate_pin("1234") is True

    def test_wrong_pin_fails(self):
        card = DebitCard("CARD-001", "C-001", "1234", "ACCT-001")
        assert card.validate_pin("0000") is False


class TestDebitCardCharge:
    def setup_method(self):
        self.card = DebitCard("CARD-001", "C-001", "1234", "ACCT-001")

    def test_valid_charge_returns_metadata(self):
        meta = self.card.charge(Decimal("50.00"), "1234")
        assert meta["transaction_type"] == TransactionType.CARD_CHARGE
        assert meta["amount"] == Decimal("50.00")
        assert meta["source_account"] == "ACCT-001"

    def test_wrong_pin_raises(self):
        with pytest.raises(ValueError, match="PIN"):
            self.card.charge(Decimal("50.00"), "9999")

    def test_zero_amount_raises(self):
        with pytest.raises(ValueError):
            self.card.charge(Decimal("0.00"), "1234")

    def test_blocked_card_raises(self):
        self.card.block()
        with pytest.raises(RuntimeError, match="blocked"):
            self.card.charge(Decimal("10.00"), "1234")


class TestCardBlock:
    def test_blocking_sets_flag(self):
        card = DebitCard("CARD-001", "C-001", "1234", "ACCT-001")
        card.block()
        assert card.is_blocked

    def test_blocking_twice_raises(self):
        card = DebitCard("CARD-001", "C-001", "1234", "ACCT-001")
        card.block()
        with pytest.raises(RuntimeError, match="already blocked"):
            card.block()


class TestCreditCardCharge:
    def setup_method(self):
        self.card = CreditCard("CARD-002", "C-001", "5678", Decimal("1000.00"))

    def test_charge_increases_outstanding(self):
        self.card.charge(Decimal("200.00"), "5678")
        assert self.card.outstanding_balance == Decimal("200.00")

    def test_charge_reduces_available_credit(self):
        self.card.charge(Decimal("300.00"), "5678")
        assert self.card.available_credit == Decimal("700.00")

    def test_charge_exceeding_limit_raises(self):
        with pytest.raises(ValueError, match="exceeds available credit"):
            self.card.charge(Decimal("1500.00"), "5678")

    def test_charge_exactly_at_limit(self):
        self.card.charge(Decimal("1000.00"), "5678")
        assert self.card.available_credit == Decimal("0.00")


class TestCreditCardPayment:
    def setup_method(self):
        self.card = CreditCard("CARD-002", "C-001", "5678", Decimal("1000.00"))
        self.card.charge(Decimal("500.00"), "5678")

    def test_payment_reduces_outstanding(self):
        self.card.make_payment(Decimal("200.00"))
        assert self.card.outstanding_balance == Decimal("300.00")

    def test_full_payment_clears_balance(self):
        self.card.make_payment(Decimal("500.00"))
        assert self.card.outstanding_balance == Decimal("0.00")

    def test_overpayment_raises(self):
        with pytest.raises(ValueError, match="exceeds outstanding"):
            self.card.make_payment(Decimal("600.00"))

    def test_zero_payment_raises(self):
        with pytest.raises(ValueError, match="positive"):
            self.card.make_payment(Decimal("0.00"))
