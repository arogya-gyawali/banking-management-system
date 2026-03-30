"""
app.py — Premium Streamlit interface for the Banking Management System.

Run with:
    python3 -m streamlit run app.py
"""

import streamlit as st
from decimal import Decimal, InvalidOperation

from src.models.customer import Customer
from src.models.loan import Loan
from src.models.card import DebitCard, CreditCard
from src.models.account import SavingsAccount, CurrentAccount
from src.services.account_manager import AccountManager
from src.services.transaction_manager import TransactionManager
from src.services.auth_service import AuthService
from src.models.bank import Bank
from src.utils.enums import AccountType, Role, LoanStatus
from src.utils.data_store import DataStore

# ====================================================================== #
#  PAGE CONFIG
# ====================================================================== #
st.set_page_config(
    page_title="Python National Bank",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ====================================================================== #
#  PREMIUM CSS
# ====================================================================== #
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --navy-900: #0a0e1a;
        --navy-800: #0f1629;
        --navy-700: #151d35;
        --navy-600: #1b2544;
        --navy-500: #243055;
        --gold-400: #d4a853;
        --gold-300: #e8c175;
        --gold-200: #f0d49b;
        --emerald: #34d399;
        --rose: #fb7185;
        --sky: #38bdf8;
        --glass: rgba(255, 255, 255, 0.04);
        --glass-border: rgba(255, 255, 255, 0.08);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
    }

    .stApp {
        background: var(--navy-900) !important;
        color: var(--text-primary) !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stApp > header { background: transparent !important; }
    .block-container { padding-top: 2rem !important; max-width: 1200px !important; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--navy-800) 0%, var(--navy-900) 100%) !important;
        border-right: 1px solid var(--glass-border) !important;
    }
    section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: var(--text-primary) !important; }
    p, span, label, li, div { color: var(--text-secondary) !important; }

    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: var(--navy-700) !important;
        border: 1px solid var(--glass-border) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--gold-400) !important;
        box-shadow: 0 0 0 2px rgba(212, 168, 83, 0.15) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--gold-400) 0%, #c4963f 100%) !important;
        color: var(--navy-900) !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 25px rgba(212, 168, 83, 0.3) !important;
    }

    [data-testid="stMetric"] {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-family: 'Playfair Display', serif !important; }
    [data-testid="stMetricLabel"] { color: var(--text-muted) !important; text-transform: uppercase !important; font-size: 0.7rem !important; letter-spacing: 1.5px !important; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important; background: var(--navy-800) !important;
        border-radius: 12px !important; padding: 4px !important; border: 1px solid var(--glass-border) !important;
    }
    .stTabs [data-baseweb="tab"] { border-radius: 10px !important; color: var(--text-muted) !important; font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important; }
    .stTabs [aria-selected="true"] { background: var(--navy-600) !important; color: var(--gold-300) !important; }

    hr { border-color: var(--glass-border) !important; opacity: 0.5; }

    .hero-title {
        font-family: 'Playfair Display', serif; font-size: 3.2rem; font-weight: 800;
        background: linear-gradient(135deg, var(--gold-200) 0%, var(--gold-400) 50%, var(--gold-200) 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1;
    }
    .hero-sub { font-family: 'DM Sans', sans-serif; font-size: 1rem; color: var(--text-muted); letter-spacing: 3px; text-transform: uppercase; margin-top: 0.5rem; }

    .glass-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid var(--glass-border); border-radius: 16px; padding: 1.8rem; margin-bottom: 1rem;
        backdrop-filter: blur(10px); transition: all 0.3s ease;
    }
    .glass-card:hover { border-color: rgba(212, 168, 83, 0.2); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }

    .account-card {
        background: linear-gradient(135deg, var(--navy-700) 0%, var(--navy-800) 100%);
        border: 1px solid var(--glass-border); border-radius: 20px; padding: 2rem;
        position: relative; overflow: hidden;
    }
    .account-card::before {
        content: ''; position: absolute; top: -50%; right: -50%; width: 100%; height: 100%;
        background: radial-gradient(circle, rgba(212,168,83,0.06) 0%, transparent 70%);
    }
    .account-card .acc-type { font-size: 0.7rem; color: var(--gold-400); text-transform: uppercase; letter-spacing: 2.5px; font-weight: 600; margin-bottom: 0.8rem; }
    .account-card .acc-balance { font-family: 'Playfair Display', serif; font-size: 2.6rem; font-weight: 700; color: var(--text-primary); line-height: 1; }
    .account-card .acc-detail { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.4rem; }
    .account-card .acc-status { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.8rem; }
    .status-active { background: rgba(52,211,153,0.15); color: var(--emerald); border: 1px solid rgba(52,211,153,0.3); }
    .status-closed { background: rgba(251,113,133,0.15); color: var(--rose); border: 1px solid rgba(251,113,133,0.3); }

    .success-toast { background: linear-gradient(135deg, rgba(52,211,153,0.1) 0%, rgba(52,211,153,0.05) 100%); border: 1px solid rgba(52,211,153,0.3); border-left: 4px solid var(--emerald); color: var(--emerald); padding: 1.2rem 1.5rem; border-radius: 12px; margin: 1rem 0; }
    .success-toast strong { color: var(--emerald); }
    .info-toast { background: linear-gradient(135deg, rgba(56,189,248,0.1) 0%, rgba(56,189,248,0.05) 100%); border: 1px solid rgba(56,189,248,0.2); border-left: 4px solid var(--sky); color: var(--sky); padding: 1.2rem 1.5rem; border-radius: 12px; margin: 1rem 0; }
    .warning-toast { background: linear-gradient(135deg, rgba(212,168,83,0.1) 0%, rgba(212,168,83,0.05) 100%); border: 1px solid rgba(212,168,83,0.2); border-left: 4px solid var(--gold-400); color: var(--gold-300); padding: 1.2rem 1.5rem; border-radius: 12px; margin: 1rem 0; }

    .tx-row { display: flex; align-items: center; justify-content: space-between; padding: 1rem 1.2rem; border-radius: 12px; margin-bottom: 0.5rem; background: var(--glass); border: 1px solid var(--glass-border); transition: all 0.2s ease; }
    .tx-row:hover { background: rgba(255,255,255,0.06); }
    .tx-icon { font-size: 1.5rem; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 12px; margin-right: 1rem; flex-shrink: 0; }
    .tx-icon-deposit { background: rgba(52,211,153,0.12); }
    .tx-icon-withdrawal { background: rgba(251,113,133,0.12); }
    .tx-icon-transfer { background: rgba(56,189,248,0.12); }
    .tx-icon-other { background: rgba(212,168,83,0.12); }
    .tx-info { flex-grow: 1; }
    .tx-type { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
    .tx-meta { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--text-muted); margin-top: 2px; }
    .tx-amount { font-weight: 700; font-size: 1.05rem; text-align: right; flex-shrink: 0; }
    .tx-positive { color: var(--emerald); }
    .tx-negative { color: var(--rose); }

    .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 1rem 0; }
    .stat-card { background: var(--glass); border: 1px solid var(--glass-border); border-radius: 14px; padding: 1.2rem 1.5rem; text-align: center; }
    .stat-value { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; color: var(--text-primary); }
    .stat-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1.5px; margin-top: 0.3rem; }

    .login-container { max-width: 420px; margin: 4rem auto; }
    .login-brand { text-align: center; margin-bottom: 2.5rem; }
    .login-brand .icon { font-size: 3rem; margin-bottom: 1rem; }
    .login-box { background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%); border: 1px solid var(--glass-border); border-radius: 20px; padding: 2.5rem; backdrop-filter: blur(20px); }

    .section-title { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.3rem; }
    .section-sub { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.5rem; }
    .sidebar-brand { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: var(--gold-300) !important; font-weight: 700; }
    .sidebar-user { font-size: 0.8rem; color: var(--text-muted) !important; }
    .sidebar-role { display: inline-block; font-size: 0.65rem; padding: 3px 10px; border-radius: 20px; background: rgba(212,168,83,0.15); color: var(--gold-400) !important; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-top: 0.3rem; }
    .form-section { background: var(--glass); border: 1px solid var(--glass-border); border-radius: 16px; padding: 2rem; margin: 1rem 0; }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--navy-900); }
    ::-webkit-scrollbar-thumb { background: var(--navy-600); border-radius: 3px; }

    @keyframes fadeUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    .animate-in { animation: fadeUp 0.5s ease-out forwards; }
    .delay-1 { animation-delay: 0.1s; opacity: 0; }
    .delay-2 { animation-delay: 0.2s; opacity: 0; }
    .delay-3 { animation-delay: 0.3s; opacity: 0; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


# ====================================================================== #
#  STATE
# ====================================================================== #
def init_state():
    if "initialized" not in st.session_state:
        store = DataStore()
        bank, auth, tx_manager = store.load()
        acct_manager = AccountManager(bank, tx_manager)
        st.session_state.bank = bank
        st.session_state.auth = auth
        st.session_state.tx_manager = tx_manager
        st.session_state.acct_manager = acct_manager
        st.session_state.store = store
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.customer_id = None
        st.session_state.initialized = True

def save():
    st.session_state.store.save(st.session_state.bank, st.session_state.auth, st.session_state.tx_manager)


# ====================================================================== #
#  HELPERS
# ====================================================================== #
def _acct_options(bank, customer):
    opts = {}
    for acc_num in customer.account_numbers:
        a = bank.find_account(acc_num)
        if a and a.is_active:
            t = "Savings" if isinstance(a, SavingsAccount) else "Checking"
            opts[f"{t}  \u2022  {acc_num}  \u2022  ${a.balance:,.2f}"] = acc_num
    return opts

def _parse_amount(s):
    if not s:
        st.error("Please enter an amount.")
        return None
    try:
        a = Decimal(s)
        if a <= 0:
            st.error("Amount must be positive.")
            return None
        return a
    except InvalidOperation:
        st.error("Invalid amount format.")
        return None

def _section(title, sub=""):
    st.markdown(f'<div class="section-title animate-in">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub animate-in delay-1">{sub}</div>', unsafe_allow_html=True)

def _success(msg):
    st.markdown(f'<div class="success-toast animate-in">{msg}</div>', unsafe_allow_html=True)

def _info(msg):
    st.markdown(f'<div class="info-toast animate-in">{msg}</div>', unsafe_allow_html=True)

def _warn(msg):
    st.markdown(f'<div class="warning-toast animate-in">{msg}</div>', unsafe_allow_html=True)


# ====================================================================== #
#  LOGIN
# ====================================================================== #
def login_page():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("""
        <div class="login-brand animate-in">
            <div class="icon">\U0001F3E6</div>
            <div class="hero-title">Python National Bank</div>
            <div class="hero-sub">Secure \u2022 Reliable \u2022 Modern</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box animate-in delay-2">', unsafe_allow_html=True)
    username = st.text_input("Username", placeholder="Enter your username", label_visibility="collapsed")
    password = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="collapsed")

    if st.button("Sign In", use_container_width=True):
        if not username or not password:
            st.error("Please enter both fields.")
            return
        user = st.session_state.auth._users.get(username)
        if user is None or not user.verify_password(password):
            st.error("Invalid credentials.")
            return
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = user.role
        st.session_state.customer_id = user.linked_customer_id
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="info-toast animate-in delay-3" style="margin-top: 1.5rem; text-align: center;">
            <strong>First time?</strong>&ensp;Login:&ensp;
            <code style="color: var(--sky);">admin</code> /
            <code style="color: var(--sky);">admin123</code>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ====================================================================== #
#  SIDEBAR
# ====================================================================== #
def sidebar():
    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 0.5rem 0 1rem 0;">
                <div class="sidebar-brand">\U0001F3E6 Python National Bank</div>
                <div class="sidebar-user" style="margin-top:0.8rem;">{st.session_state.username}</div>
                <div class="sidebar-role">{st.session_state.role.value}</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.role == Role.CUSTOMER:
            page = st.radio("", [
                "\U0001F3E0  Dashboard",
                "\U0001F4B0  Deposit",
                "\U0001F4B8  Withdraw",
                "\U0001F504  Transfer",
                "\U0001F4DC  Transactions",
                "\U0001F4CB  Loans",
                "\U0001F4B3  Cards",
            ], label_visibility="collapsed")
        else:
            page = st.radio("", [
                "\U0001F3E0  Dashboard",
                "\U0001F464  Register Customer",
                "\U0001F3E6  Create Account",
                "\U0001F4CB  Manage Loans",
                "\U0001F4B3  Issue Card",
                "\U0001F465  All Customers",
            ], label_visibility="collapsed")

        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            for k in ["logged_in", "username", "role", "customer_id"]:
                st.session_state[k] = None
            st.session_state.logged_in = False
            st.rerun()
    return page


# ====================================================================== #
#  CUSTOMER PAGES
# ====================================================================== #
def customer_dashboard():
    bank = st.session_state.bank
    cid = st.session_state.customer_id
    customer = bank.find_customer(cid)
    _section("Welcome back", f"Here's your financial overview, {customer.first_name}.")

    if not customer.account_numbers:
        _info("You don't have any accounts yet. Contact an administrator to get started.")
        return

    cols = st.columns(len(customer.account_numbers))
    for i, acc_num in enumerate(customer.account_numbers):
        account = bank.find_account(acc_num)
        if not account: continue
        t = "Savings Account" if isinstance(account, SavingsAccount) else "Checking Account"
        scls = "status-active" if account.is_active else "status-closed"
        stxt = "Active" if account.is_active else "Closed"
        with cols[i]:
            st.markdown(f"""
                <div class="account-card animate-in delay-{i+1}">
                    <div class="acc-type">{t}</div>
                    <div class="acc-balance">${account.balance:,.2f}</div>
                    <div class="acc-detail">{acc_num}</div>
                    <div class="acc-status {scls}">{stxt}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    total = sum(bank.find_account(a).balance for a in customer.account_numbers if bank.find_account(a))
    st.markdown(f"""
        <div class="glass-card animate-in delay-3" style="text-align: center;">
            <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 2px; font-weight: 600;">Total Portfolio Balance</div>
            <div style="font-family: 'Playfair Display', serif; font-size: 2.5rem; font-weight: 700; color: var(--gold-300); margin-top: 0.3rem;">${total:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)


def deposit_page():
    _section("Deposit Funds", "Add money to your account.")
    bank, am = st.session_state.bank, st.session_state.acct_manager
    customer = bank.find_customer(st.session_state.customer_id)
    if not customer or not customer.account_numbers: _info("No accounts available."); return
    opts = _acct_options(bank, customer)
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    sel = st.selectbox("Account", list(opts.keys()))
    amt = st.text_input("Amount ($)", placeholder="500.00")
    desc = st.text_input("Description", placeholder="Paycheck, savings, etc.")
    if st.button("Deposit", use_container_width=True):
        amount = _parse_amount(amt)
        if amount:
            try:
                tx = am.deposit(opts[sel], amount, desc); save()
                _success(f"\u2705 <strong>${amount:,.2f}</strong> deposited successfully.<br><small>Transaction: {tx.transaction_id}</small>")
            except (ValueError, RuntimeError) as e: st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)


def withdraw_page():
    _section("Withdraw Funds", "Take money from your account.")
    bank, am = st.session_state.bank, st.session_state.acct_manager
    customer = bank.find_customer(st.session_state.customer_id)
    if not customer or not customer.account_numbers: _info("No accounts available."); return
    opts = _acct_options(bank, customer)
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    sel = st.selectbox("Account", list(opts.keys()))
    amt = st.text_input("Amount ($)", placeholder="200.00")
    desc = st.text_input("Description", placeholder="ATM, rent, etc.")
    if st.button("Withdraw", use_container_width=True):
        amount = _parse_amount(amt)
        if amount:
            try:
                tx = am.withdraw(opts[sel], amount, desc); save()
                _success(f"\u2705 <strong>${amount:,.2f}</strong> withdrawn successfully.<br><small>Transaction: {tx.transaction_id}</small>")
            except (ValueError, RuntimeError) as e: st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)


def transfer_page():
    _section("Transfer Funds", "Move money between your accounts.")
    bank, am = st.session_state.bank, st.session_state.acct_manager
    customer = bank.find_customer(st.session_state.customer_id)
    if not customer or len(customer.account_numbers) < 2: _info("You need at least two accounts to transfer."); return
    opts = _acct_options(bank, customer)
    keys = list(opts.keys())
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: fr = st.selectbox("From", keys, index=0)
    with c2: to = st.selectbox("To", keys, index=min(1, len(keys)-1))
    amt = st.text_input("Amount ($)", placeholder="100.00")
    if st.button("Transfer", use_container_width=True):
        if fr == to: st.error("Cannot transfer to the same account.")
        else:
            amount = _parse_amount(amt)
            if amount:
                try:
                    am.transfer(opts[fr], opts[to], amount); save()
                    _success(f"\u2705 <strong>${amount:,.2f}</strong> transferred successfully.")
                except (ValueError, RuntimeError) as e: st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)


def transaction_history_page():
    _section("Transaction History", "A complete record of your activity.")
    bank, am = st.session_state.bank, st.session_state.acct_manager
    customer = bank.find_customer(st.session_state.customer_id)
    if not customer or not customer.account_numbers: _info("No accounts available."); return
    opts = _acct_options(bank, customer)
    sel = st.selectbox("Account", list(opts.keys()))
    history = am.get_transaction_history(opts[sel])
    if not history: _info("No transactions yet."); return
    st.markdown("<br>", unsafe_allow_html=True)
    for tx in reversed(history):
        tv = tx.transaction_type.value
        icon_map = {"deposit": ("\u2193", "tx-icon-deposit"), "withdrawal": ("\u2191", "tx-icon-withdrawal"), "transfer": ("\u21C4", "tx-icon-transfer")}
        icon, icls = icon_map.get(tv, ("\u2022", "tx-icon-other"))
        is_credit = tv in ("deposit", "interest")
        sign = "+" if is_credit else "\u2212"
        acls = "tx-positive" if is_credit else "tx-negative"
        desc = tx.description or tv.replace("_", " ").title()
        ts = tx.timestamp.strftime("%b %d, %Y  \u2022  %I:%M %p")
        st.markdown(f"""
            <div class="tx-row">
                <div class="tx-icon {icls}">{icon}</div>
                <div class="tx-info">
                    <div class="tx-type">{desc}</div>
                    <div class="tx-meta">{tx.transaction_id}  \u2022  {ts}</div>
                </div>
                <div class="tx-amount {acls}">{sign}${tx.amount:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)


def loans_page():
    _section("Loans", "View your loans or apply for a new one.")
    bank = st.session_state.bank
    cid = st.session_state.customer_id
    loans = bank.get_loans_for_customer(cid)
    tab1, tab2 = st.tabs(["My Loans", "Apply for Loan"])
    with tab1:
        if not loans: _info("You have no loans.")
        for loan in loans:
            sc = {"pending": "\U0001F7E1", "approved": "\U0001F7E2", "rejected": "\U0001F534", "closed": "\u26AA"}.get(loan.status.value, "\u26AA")
            with st.expander(f"{sc}  {loan.loan_id}  \u2014  ${loan.principal:,.2f}  ({loan.status.value.upper()})"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Principal", f"${loan.principal:,.2f}")
                c2.metric("EMI", f"${loan.emi:,.2f}/mo")
                c3.metric("Remaining", f"${loan.remaining_balance:,.2f}")
                st.caption(f"Rate: {loan.interest_rate*100:.1f}%  \u2022  Term: {loan.duration_months} months")
                if loan.rejection_reason: st.error(f"Reason: {loan.rejection_reason}")
                if loan.status == LoanStatus.APPROVED:
                    pay = st.text_input("Payment ($)", value=str(loan.emi), key=f"p_{loan.loan_id}")
                    if st.button("Make Payment", key=f"pb_{loan.loan_id}"):
                        try:
                            loan.make_payment(Decimal(pay)); save()
                            _success(f"Payment applied. Remaining: ${loan.remaining_balance:,.2f}")
                        except (ValueError, RuntimeError) as e: st.error(str(e))
    with tab2:
        has_pending = any(l.status == LoanStatus.PENDING for l in loans)
        if has_pending: _warn("You already have a pending application.")
        else:
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: principal = st.text_input("Loan Amount ($)", placeholder="10000"); rate = st.text_input("Annual Rate (%)", value="8.0")
            with c2: term = st.selectbox("Term (months)", [12, 24, 36, 48, 60], index=1); purpose = st.text_input("Purpose", placeholder="Home renovation")
            if st.button("Submit Application", use_container_width=True):
                try:
                    p = Decimal(principal); r = Decimal(rate) / 100
                    lid = bank.id_generator.generate_loan_id()
                    loan = Loan(lid, cid, p, r, term); bank.add_loan(loan); save()
                    emi = loan.calculate_emi()
                    _success(f"\u2705 Application <strong>{lid}</strong> submitted!<br>Estimated EMI: <strong>${emi:,.2f}/month</strong>")
                except (ValueError, InvalidOperation) as e: st.error(str(e))
            st.markdown('</div>', unsafe_allow_html=True)


def cards_page():
    _section("My Cards", "View your debit and credit cards.")
    bank = st.session_state.bank
    cards = [c for c in bank._cards.values() if c.issued_to_customer_id == st.session_state.customer_id]
    if not cards: _info("No cards issued yet. Contact an admin."); return
    for card in cards:
        ct = "Debit" if isinstance(card, DebitCard) else "Credit"
        status = "\U0001F534 Blocked" if card.is_blocked else "\U0001F7E2 Active"
        with st.expander(f"\U0001F4B3  {ct} Card  \u2022  {card.card_number}"):
            c1, c2 = st.columns(2)
            c1.write(f"**Card:** `{card.card_number}`"); c1.write(f"**Expires:** {card.expiry}"); c1.write(f"**Status:** {status}")
            if isinstance(card, DebitCard): c2.write(f"**Linked Account:** `{card.linked_account_number}`")
            else: c2.metric("Limit", f"${card.credit_limit:,.2f}"); c2.metric("Outstanding", f"${card.outstanding_balance:,.2f}"); c2.metric("Available", f"${card.available_credit:,.2f}")


# ====================================================================== #
#  ADMIN PAGES
# ====================================================================== #
def admin_dashboard():
    bank = st.session_state.bank
    _section("Admin Dashboard", "System overview and management.")
    custs = len(bank._customers); accts = len(bank._accounts)
    active_loans = sum(1 for l in bank._loans.values() if l.status == LoanStatus.APPROVED)
    ncards = len(bank._cards); pending = sum(1 for l in bank._loans.values() if l.status == LoanStatus.PENDING)
    st.markdown(f"""
        <div class="stat-grid animate-in">
            <div class="stat-card"><div class="stat-value">{custs}</div><div class="stat-label">Customers</div></div>
            <div class="stat-card"><div class="stat-value">{accts}</div><div class="stat-label">Accounts</div></div>
            <div class="stat-card"><div class="stat-value">{active_loans}</div><div class="stat-label">Active Loans</div></div>
            <div class="stat-card"><div class="stat-value">{ncards}</div><div class="stat-label">Cards Issued</div></div>
        </div>
    """, unsafe_allow_html=True)
    if pending > 0: _warn(f"\u26A0\uFE0F <strong>{pending}</strong> loan application(s) awaiting your review.")


def register_customer_page():
    _section("Register Customer", "Create a new customer profile and login.")
    bank, auth = st.session_state.bank, st.session_state.auth
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: fn = st.text_input("First Name"); ln = st.text_input("Last Name"); email = st.text_input("Email")
    with c2: phone = st.text_input("Phone"); uname = st.text_input("Login Username"); pw = st.text_input("Login Password", type="password")
    if st.button("Register", use_container_width=True):
        if not all([fn, ln, email, phone, uname, pw]): st.error("All fields are required.")
        else:
            try:
                cid = bank.id_generator.generate_customer_id()
                c = Customer(cid, fn, ln, email, phone); bank.add_customer(c)
                auth.register(uname, pw, Role.CUSTOMER, cid); save()
                _success(f"\u2705 <strong>{fn} {ln}</strong> registered as <code>{cid}</code><br>Login: <code>{uname}</code>")
            except ValueError as e: st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)


def create_account_page():
    _section("Create Account", "Open a new savings or checking account.")
    bank, am = st.session_state.bank, st.session_state.acct_manager
    customers = bank.get_all_customers()
    if not customers: _info("No customers registered yet."); return
    copts = {f"{c.full_name}  ({c.customer_id})": c.customer_id for c in customers}
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    sel = st.selectbox("Customer", list(copts.keys()))
    atype = st.selectbox("Account Type", ["Savings", "Checking"])
    dep = st.text_input("Initial Deposit ($)", value="100.00")
    if st.button("Create Account", use_container_width=True):
        try:
            d = Decimal(dep); at = AccountType.SAVINGS if atype == "Savings" else AccountType.CHECKING
            a = am.create_account(copts[sel], at, d); save()
            _success(f"\u2705 {atype} account <strong>{a.account_number}</strong> created with ${d:,.2f}")
        except (ValueError, KeyError) as e: st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)


def manage_loans_page():
    _section("Manage Loans", "Review and process loan applications.")
    bank = st.session_state.bank
    pending = [l for l in bank._loans.values() if l.status == LoanStatus.PENDING]
    processed = [l for l in bank._loans.values() if l.status != LoanStatus.PENDING]
    tab1, tab2 = st.tabs(["Pending", "Processed"])
    with tab1:
        if not pending: _info("No pending applications.")
        for loan in pending:
            cust = bank.find_customer(loan.customer_id)
            name = cust.full_name if cust else loan.customer_id
            emi = loan.calculate_emi()
            st.markdown(f"""
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="color:var(--text-primary); font-weight:600; font-size:1rem;">{name}</div>
                            <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:var(--text-muted);">{loan.loan_id}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="color:var(--text-primary); font-weight:600;">${loan.principal:,.2f}</div>
                            <div style="font-size:0.75rem; color:var(--text-muted);">EMI: ${emi:,.2f}/mo \u2022 {loan.duration_months}mo</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            c1, c2, _ = st.columns([1, 1, 3])
            with c1:
                if st.button("\u2705 Approve", key=f"a_{loan.loan_id}", use_container_width=True): loan.approve(); save(); st.rerun()
            with c2:
                if st.button("\u274C Reject", key=f"r_{loan.loan_id}", use_container_width=True): loan.reject(); save(); st.rerun()
            st.markdown("---")
    with tab2:
        if not processed: _info("No processed loans yet.")
        for loan in processed:
            icon = "\U0001F7E2" if loan.status == LoanStatus.APPROVED else "\U0001F534" if loan.status == LoanStatus.REJECTED else "\u26AA"
            st.write(f"{icon}  `{loan.loan_id}`  \u2014  ${loan.principal:,.2f}  \u2014  **{loan.status.value.upper()}**")


def issue_card_page():
    _section("Issue Card", "Issue a debit or credit card to a customer.")
    bank = st.session_state.bank
    customers = bank.get_all_customers()
    if not customers: _info("No customers registered yet."); return
    copts = {f"{c.full_name}  ({c.customer_id})": c.customer_id for c in customers}
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    sel = st.selectbox("Customer", list(copts.keys())); cid = copts[sel]
    ctype = st.selectbox("Card Type", ["Debit", "Credit"])
    if ctype == "Debit":
        cust = bank.find_customer(cid)
        if not cust or not cust.account_numbers: _warn("This customer has no accounts to link."); st.markdown('</div>', unsafe_allow_html=True); return
        aopts = _acct_options(bank, cust); sacc = st.selectbox("Link to Account", list(aopts.keys()))
    pin = st.text_input("Set PIN (4 digits)", type="password", max_chars=4)
    if ctype == "Credit": limit = st.text_input("Credit Limit ($)", value="5000.00")
    if st.button("Issue Card", use_container_width=True):
        if not pin or not pin.isdigit() or len(pin) != 4: st.error("PIN must be exactly 4 digits.")
        else:
            try:
                cn = bank.id_generator.generate_card_number()
                if ctype == "Debit": card = DebitCard(cn, cid, pin, aopts[sacc])
                else: card = CreditCard(cn, cid, pin, Decimal(limit))
                bank.add_card(card); save()
                _success(f"\u2705 {ctype} card <strong>{cn}</strong> issued. Expires {card.expiry}")
            except (ValueError, InvalidOperation) as e: st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)


def all_customers_page():
    _section("All Customers", "View registered customer profiles.")
    bank = st.session_state.bank
    customers = bank.get_all_customers()
    if not customers: _info("No customers registered yet."); return
    for c in customers:
        with st.expander(f"\U0001F464  {c.full_name}  \u2022  {c.customer_id}"):
            c1, c2 = st.columns(2)
            c1.write(f"**Email:** {c.email}"); c1.write(f"**Phone:** {c.phone}")
            accs = [bank.find_account(a) for a in c.account_numbers if bank.find_account(a)]
            c2.write(f"**Accounts:** {len(accs)}")
            for a in accs:
                t = "Savings" if isinstance(a, SavingsAccount) else "Checking"
                c2.write(f"` {a.account_number} `  {t}  \u2014  ${a.balance:,.2f}")


# ====================================================================== #
#  ROUTER
# ====================================================================== #
def main():
    init_state()
    inject_css()
    if not st.session_state.logged_in: login_page(); return
    page = sidebar()
    if st.session_state.role == Role.CUSTOMER:
        routes = {"\U0001F3E0  Dashboard": customer_dashboard, "\U0001F4B0  Deposit": deposit_page, "\U0001F4B8  Withdraw": withdraw_page, "\U0001F504  Transfer": transfer_page, "\U0001F4DC  Transactions": transaction_history_page, "\U0001F4CB  Loans": loans_page, "\U0001F4B3  Cards": cards_page}
    else:
        routes = {"\U0001F3E0  Dashboard": admin_dashboard, "\U0001F464  Register Customer": register_customer_page, "\U0001F3E6  Create Account": create_account_page, "\U0001F4CB  Manage Loans": manage_loans_page, "\U0001F4B3  Issue Card": issue_card_page, "\U0001F465  All Customers": all_customers_page}
    fn = routes.get(page)
    if fn: fn()

if __name__ == "__main__":
    main()