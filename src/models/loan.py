"""
loan.py — Loan entity for the Banking Management System.

Represents a loan application that moves through a lifecycle:
PENDING → APPROVED → CLOSED   (or PENDING → REJECTED).

The EMI (Equated Monthly Instalment) is computed using the standard
reducing-balance formula once a loan is approved.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from src.utils.enums import LoanStatus, TransactionType


class Loan:
    """
    A customer loan with application, approval, and repayment logic.

    Attributes:
        _loan_id (str):
            Unique identifier (e.g. "LOAN-0001").
        _customer_id (str):
            ID of the customer who applied.
        _principal (Decimal):
            Requested / approved loan amount.
        _interest_rate (Decimal):
            Annual interest rate as a decimal (e.g. 0.08 = 8 %).
        _duration_months (int):
            Repayment period in months.
        _emi (Decimal):
            Calculated monthly instalment (set on approval).
        _remaining_balance (Decimal):
            Outstanding amount still owed.
        _status (LoanStatus):
            Current lifecycle state.
        _rejection_reason (Optional[str]):
            Reason text if the loan was rejected.
    """

    def __init__(
        self,
        loan_id: str,
        customer_id: str,
        principal: Decimal,
        interest_rate: Decimal,
        duration_months: int,
    ) -> None:
        """
        Create a new Loan application in PENDING status.

        Args:
            loan_id: Unique ID from IdGenerator.
            customer_id: Applying customer's ID.
            principal: Loan amount requested.
            interest_rate: Annual rate as a decimal.
            duration_months: Repayment term in months.

        Raises:
            ValueError: If principal ≤ 0, rate < 0, or duration ≤ 0.
        """
        if principal <= 0:
            raise ValueError("Loan principal must be positive.")
        if interest_rate < 0:
            raise ValueError("Interest rate cannot be negative.")
        if duration_months <= 0:
            raise ValueError("Duration must be at least 1 month.")

        self._loan_id: str = loan_id
        self._customer_id: str = customer_id
        self._principal: Decimal = principal
        self._interest_rate: Decimal = interest_rate
        self._duration_months: int = duration_months
        self._emi: Decimal = Decimal("0.00")
        self._remaining_balance: Decimal = Decimal("0.00")
        self._status: LoanStatus = LoanStatus.PENDING
        self._rejection_reason: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def loan_id(self) -> str:
        return self._loan_id

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def principal(self) -> Decimal:
        return self._principal

    @property
    def interest_rate(self) -> Decimal:
        return self._interest_rate

    @property
    def duration_months(self) -> int:
        return self._duration_months

    @property
    def emi(self) -> Decimal:
        return self._emi

    @property
    def remaining_balance(self) -> Decimal:
        return self._remaining_balance

    @property
    def status(self) -> LoanStatus:
        return self._status

    @property
    def rejection_reason(self) -> Optional[str]:
        return self._rejection_reason

    # ------------------------------------------------------------------ #
    #  EMI calculation
    # ------------------------------------------------------------------ #

    def calculate_emi(self) -> Decimal:
        """
        Compute the Equated Monthly Instalment using the standard formula:

            EMI = P × r × (1 + r)^n / ((1 + r)^n − 1)

        where P = principal, r = monthly rate, n = duration in months.
        If the interest rate is 0, EMI = P / n.

        Returns:
            The monthly instalment amount.
        """
        p = self._principal
        n = self._duration_months

        if self._interest_rate == 0:
            return (p / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        r = self._interest_rate / 12  # monthly rate
        factor = (1 + r) ** n
        emi = p * r * factor / (factor - 1)
        return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # ------------------------------------------------------------------ #
    #  Lifecycle transitions
    # ------------------------------------------------------------------ #

    def approve(self) -> None:
        """
        Approve the loan, calculate the EMI, and set the remaining balance.

        Raises:
            RuntimeError: If the loan is not in PENDING status.
        """
        if self._status != LoanStatus.PENDING:
            raise RuntimeError(
                f"Cannot approve loan {self._loan_id}: "
                f"current status is {self._status.value}."
            )
        self._emi = self.calculate_emi()
        self._remaining_balance = self._principal
        self._status = LoanStatus.APPROVED

    def reject(self, reason: str = "Does not meet eligibility criteria") -> None:
        """
        Reject the loan application.

        Args:
            reason: Explanation for the rejection.

        Raises:
            RuntimeError: If the loan is not in PENDING status.
        """
        if self._status != LoanStatus.PENDING:
            raise RuntimeError(
                f"Cannot reject loan {self._loan_id}: "
                f"current status is {self._status.value}."
            )
        self._rejection_reason = reason
        self._status = LoanStatus.REJECTED

    # ------------------------------------------------------------------ #
    #  Repayment
    # ------------------------------------------------------------------ #

    def make_payment(self, amount: Decimal) -> dict:
        """
        Apply a repayment toward the outstanding balance.

        Args:
            amount: Positive payment amount.

        Returns:
            Dict with transaction metadata for the payment.

        Raises:
            RuntimeError: If the loan is not APPROVED.
            ValueError: If amount ≤ 0 or exceeds the remaining balance.
        """
        if self._status != LoanStatus.APPROVED:
            raise RuntimeError(
                f"Cannot make payment on loan {self._loan_id}: "
                f"status is {self._status.value}."
            )
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        if amount > self._remaining_balance:
            raise ValueError(
                f"Payment (${amount:,.2f}) exceeds remaining balance "
                f"(${self._remaining_balance:,.2f})."
            )

        self._remaining_balance -= amount

        if self._remaining_balance == 0:
            self._status = LoanStatus.CLOSED

        return {
            "amount": amount,
            "transaction_type": TransactionType.LOAN_PAYMENT,
            "description": (
                f"Loan payment for {self._loan_id}. "
                f"Remaining: ${self._remaining_balance:,.2f}"
            ),
        }

    # ------------------------------------------------------------------ #
    #  Dunder methods
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"Loan(id={self._loan_id!r}, principal={self._principal}, "
            f"status={self._status.value})"
        )

    def __str__(self) -> str:
        return (
            f"[{self._loan_id}] ${self._principal:,.2f} over "
            f"{self._duration_months} mo — {self._status.value.upper()}"
        )