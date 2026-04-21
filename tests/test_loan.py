"""Unit tests for the Loan model."""

import pytest
from decimal import Decimal

from src.models.loan import Loan
from src.utils.enums import LoanStatus, TransactionType


def make_loan(**overrides):
    defaults = dict(
        loan_id="LOAN-001",
        customer_id="C-001",
        principal=Decimal("12000.00"),
        interest_rate=Decimal("0.08"),
        duration_months=12,
    )
    defaults.update(overrides)
    return Loan(**defaults)


class TestLoanCreation:
    def test_creates_in_pending_status(self):
        loan = make_loan()
        assert loan.status == LoanStatus.PENDING

    def test_raises_on_zero_principal(self):
        with pytest.raises(ValueError, match="principal"):
            make_loan(principal=Decimal("0"))

    def test_raises_on_negative_principal(self):
        with pytest.raises(ValueError):
            make_loan(principal=Decimal("-100"))

    def test_raises_on_negative_rate(self):
        with pytest.raises(ValueError, match="rate"):
            make_loan(interest_rate=Decimal("-0.01"))

    def test_raises_on_zero_duration(self):
        with pytest.raises(ValueError, match="Duration"):
            make_loan(duration_months=0)

    def test_emi_starts_at_zero(self):
        loan = make_loan()
        assert loan.emi == Decimal("0.00")

    def test_remaining_balance_starts_at_zero(self):
        loan = make_loan()
        assert loan.remaining_balance == Decimal("0.00")


class TestLoanEMI:
    def test_emi_calculated_correctly(self):
        # $12,000 @ 8% annual / 12 months → $1,043.86/mo
        loan = make_loan()
        emi = loan.calculate_emi()
        assert emi == Decimal("1043.86")

    def test_zero_interest_emi(self):
        loan = make_loan(principal=Decimal("1200.00"), interest_rate=Decimal("0"), duration_months=12)
        emi = loan.calculate_emi()
        assert emi == Decimal("100.00")


class TestLoanApproval:
    def test_approve_sets_status(self):
        loan = make_loan()
        loan.approve()
        assert loan.status == LoanStatus.APPROVED

    def test_approve_sets_emi(self):
        loan = make_loan()
        loan.approve()
        assert loan.emi > Decimal("0")

    def test_approve_sets_remaining_balance_to_principal(self):
        loan = make_loan()
        loan.approve()
        assert loan.remaining_balance == loan.principal

    def test_cannot_approve_twice(self):
        loan = make_loan()
        loan.approve()
        with pytest.raises(RuntimeError, match="approved"):
            loan.approve()

    def test_cannot_approve_rejected_loan(self):
        loan = make_loan()
        loan.reject()
        with pytest.raises(RuntimeError):
            loan.approve()


class TestLoanRejection:
    def test_reject_sets_status(self):
        loan = make_loan()
        loan.reject()
        assert loan.status == LoanStatus.REJECTED

    def test_reject_stores_reason(self):
        loan = make_loan()
        loan.reject("Poor credit score")
        assert loan.rejection_reason == "Poor credit score"

    def test_default_rejection_reason(self):
        loan = make_loan()
        loan.reject()
        assert loan.rejection_reason is not None

    def test_cannot_reject_twice(self):
        loan = make_loan()
        loan.reject()
        with pytest.raises(RuntimeError):
            loan.reject()


class TestLoanPayment:
    def setup_method(self):
        self.loan = make_loan()
        self.loan.approve()

    def test_payment_reduces_balance(self):
        self.loan.make_payment(Decimal("1000.00"))
        assert self.loan.remaining_balance == Decimal("11000.00")

    def test_payment_returns_metadata(self):
        result = self.loan.make_payment(Decimal("500.00"))
        assert result["transaction_type"] == TransactionType.LOAN_PAYMENT
        assert result["amount"] == Decimal("500.00")

    def test_full_payment_closes_loan(self):
        self.loan.make_payment(self.loan.remaining_balance)
        assert self.loan.status == LoanStatus.CLOSED

    def test_overpayment_raises(self):
        with pytest.raises(ValueError, match="exceeds remaining"):
            self.loan.make_payment(Decimal("99999.00"))

    def test_zero_payment_raises(self):
        with pytest.raises(ValueError, match="positive"):
            self.loan.make_payment(Decimal("0"))

    def test_payment_on_pending_loan_raises(self):
        pending = make_loan()
        with pytest.raises(RuntimeError, match="pending"):
            pending.make_payment(Decimal("100.00"))

    def test_payment_on_rejected_loan_raises(self):
        loan = make_loan()
        loan.reject()
        with pytest.raises(RuntimeError):
            loan.make_payment(Decimal("100.00"))
