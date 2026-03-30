"""
main.py — Entry point for the Banking Management System.

Demonstrates the major use cases from the Use Case Model:
  1. Admin registration and login
  2. Customer registration and login
  3. Account creation (savings + checking)
  4. Deposits, withdrawals, and transfers
  5. Loan application, approval, EMI, and payment
  6. Card issuance and transactions
  7. Transaction history viewing

Run from the project root:
    python -m src.main
"""

from decimal import Decimal

from src.models.bank import Bank
from src.models.card import CreditCard, DebitCard
from src.models.customer import Customer
from src.models.loan import Loan
from src.services.account_manager import AccountManager
from src.services.auth_service import AuthService
from src.services.transaction_manager import TransactionManager
from src.utils.enums import AccountType, Role


def separator(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main() -> None:
    """Run the full banking system demonstration."""

    # ------------------------------------------------------------------ #
    #  Initialise core objects
    # ------------------------------------------------------------------ #
    bank = Bank("Python National Bank", "BR-001")
    tx_manager = TransactionManager()
    acct_manager = AccountManager(bank, tx_manager)
    auth = AuthService()

    separator("1. USER REGISTRATION & LOGIN")

    # Register an admin
    auth.register("admin1", "admin_pass", Role.ADMIN)
    admin_token = auth.login("admin1", "admin_pass")
    print(f"Admin logged in  → token: {admin_token[:8]}...")

    # Register a customer (admin would normally do this)
    cust_id = bank.id_generator.generate_customer_id()
    customer = Customer(cust_id, "Alice", "Johnson", "alice@email.com", "555-0101")
    bank.add_customer(customer)

    auth.register("alice", "alice_pass", Role.CUSTOMER, linked_customer_id=cust_id)
    cust_token = auth.login("alice", "alice_pass")
    print(f"Customer '{customer.full_name}' registered as {cust_id}")
    print(f"Customer logged in → token: {cust_token[:8]}...")

    # ------------------------------------------------------------------ #
    separator("2. ACCOUNT CREATION")

    savings = acct_manager.create_account(
        cust_id, AccountType.SAVINGS, Decimal("1000.00")
    )
    print(f"Savings account created: {savings}")

    checking = acct_manager.create_account(
        cust_id, AccountType.CHECKING, Decimal("500.00")
    )
    print(f"Checking account created: {checking}")

    # ------------------------------------------------------------------ #
    separator("3. DEPOSIT FUNDS")

    tx = acct_manager.deposit(savings.account_number, Decimal("250.00"), "Paycheck")
    print(f"Deposited $250 → {savings}")
    print(tx.generate_receipt())

    # ------------------------------------------------------------------ #
    separator("4. WITHDRAW FUNDS")

    tx = acct_manager.withdraw(savings.account_number, Decimal("100.00"), "ATM withdrawal")
    print(f"Withdrew $100 → {savings}")

    # Overdraft demo on checking
    tx = acct_manager.withdraw(checking.account_number, Decimal("600.00"), "Rent payment")
    print(f"Withdrew $600 (overdraft) → {checking}")

    # ------------------------------------------------------------------ #
    separator("5. TRANSFER FUNDS")

    debit_tx, credit_tx = acct_manager.transfer(
        savings.account_number, checking.account_number, Decimal("200.00")
    )
    print(f"Transferred $200: {savings.account_number} → {checking.account_number}")
    print(f"  Savings balance : ${acct_manager.get_balance(savings.account_number):,.2f}")
    print(f"  Checking balance: ${acct_manager.get_balance(checking.account_number):,.2f}")

    # ------------------------------------------------------------------ #
    separator("6. LOAN APPLICATION & APPROVAL")

    loan_id = bank.id_generator.generate_loan_id()
    loan = Loan(
        loan_id, cust_id,
        principal=Decimal("10000.00"),
        interest_rate=Decimal("0.08"),
        duration_months=24,
    )
    bank.add_loan(loan)
    print(f"Loan applied: {loan}")

    # Admin approves
    loan.approve()
    print(f"Loan approved — EMI: ${loan.emi:,.2f}/month")

    # Customer makes a payment
    payment_meta = loan.make_payment(loan.emi)
    print(
        f"Payment of ${loan.emi:,.2f} made — "
        f"remaining: ${loan.remaining_balance:,.2f}"
    )

    # ------------------------------------------------------------------ #
    separator("7. CARD ISSUANCE & TRANSACTIONS")

    # Debit card linked to checking
    debit_card_num = bank.id_generator.generate_card_number()
    debit_card = DebitCard(
        debit_card_num, cust_id, "1234", checking.account_number
    )
    bank.add_card(debit_card)
    print(f"Debit card issued: {debit_card}")

    charge_meta = debit_card.charge(Decimal("50.00"), "1234")
    # In a full flow, AccountManager would withdraw from the linked account
    print(f"Debit card charge authorised for $50.00")

    # Credit card
    credit_card_num = bank.id_generator.generate_card_number()
    credit_card = CreditCard(
        credit_card_num, cust_id, "5678", credit_limit=Decimal("3000.00")
    )
    bank.add_card(credit_card)
    print(f"Credit card issued: {credit_card}")

    credit_card.charge(Decimal("120.00"), "5678")
    print(
        f"Credit card charged $120.00 — "
        f"outstanding: ${credit_card.outstanding_balance:,.2f}, "
        f"available: ${credit_card.available_credit:,.2f}"
    )

    # ------------------------------------------------------------------ #
    separator("8. VIEW TRANSACTION HISTORY")

    history = acct_manager.get_transaction_history(savings.account_number)
    print(f"Savings account ({savings.account_number}) — {len(history)} transactions:")
    for t in history:
        print(f"  {t}")

    # ------------------------------------------------------------------ #
    separator("9. SYSTEM SUMMARY")

    print(bank)
    bank.save_state()
    print("\nDemonstration complete.")


if __name__ == "__main__":
    main()