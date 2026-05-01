"""
app.py — Premium Streamlit interface for the Banking Management System.

Run with:
    python3 -m streamlit run app.py
"""

import streamlit as st
from datetime import date
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
    page_title="NovaBank",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ====================================================================== #
#  PREMIUM CSS
# ====================================================================== #
def inject_css():
    """
    Inject the professional light theme CSS into the Streamlit page.

    Inspired by Chase Online Banking and Stripe Dashboard: light gray
    background, white content cards with subtle shadows, deep navy sidebar,
    and professional blue accents.
    """
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg:        #0d1117;
        --surface:   #161b22;
        --surface-2: #1c2330;
        --border:    #30363d;
        --blue:      #4493f8;
        --blue-dim:  #1f3a5f;
        --green:     #3fb950;
        --green-dim: #1a3a21;
        --red:       #f85149;
        --red-dim:   #3a1f1f;
        --amber:     #d29922;
        --amber-dim: #3a2e10;
        --text-1:    #e6edf3;
        --text-2:    #8b949e;
        --text-3:    #484f58;
        --mono:      'JetBrains Mono', monospace;
    }

    /* ── Base ── */
    .stApp { background: var(--bg) !important; font-family: 'Inter', sans-serif !important; color: var(--text-1) !important; }
    .stApp > header { background: transparent !important; }
    .block-container { padding-top: 2.5rem !important; max-width: 1100px !important; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #010409 !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] * { color: #8b949e !important; }
    section[data-testid="stSidebar"] .stRadio label { padding: 0.45rem 0.6rem; border-radius: 6px; transition: background 0.15s; }
    section[data-testid="stSidebar"] .stRadio label:hover { background: rgba(177,186,196,0.08) !important; }

    /* ── Typography ── */
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; color: var(--text-1) !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    p, span, label, li, div { color: var(--text-1) !important; }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-1) !important;
        border-radius: 6px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--blue) !important;
        box-shadow: 0 0 0 3px rgba(68,147,248,0.15) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: #238636 !important;
        color: #ffffff !important;
        border: 1px solid rgba(240,246,252,0.1) !important;
        border-radius: 6px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.5rem 1.2rem !important;
        transition: background 0.2s !important;
        text-transform: none !important;
    }
    .stButton > button:hover {
        background: #2ea043 !important;
        transform: none !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 1.2rem !important;
    }
    [data-testid="stMetricValue"] { color: var(--text-1) !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: var(--text-2) !important; text-transform: uppercase !important; font-size: 0.68rem !important; letter-spacing: 1px !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 0 !important; background: var(--surface) !important; border-radius: 8px !important; padding: 3px !important; border: 1px solid var(--border) !important; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px !important; color: var(--text-2) !important; font-family: 'Inter', sans-serif !important; font-weight: 500 !important; font-size: 0.875rem !important; }
    .stTabs [aria-selected="true"] { background: var(--surface-2) !important; color: var(--text-1) !important; }

    hr { border-color: var(--border) !important; }

    /* ── Login ── */
    .login-container { max-width: 400px; margin: 5rem auto; }
    .login-brand { text-align: center; margin-bottom: 2rem; }
    .login-brand .icon { font-size: 2.8rem; margin-bottom: 0.8rem; }
    .hero-title { font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 800; color: var(--text-1) !important; letter-spacing: -0.03em; }
    .hero-sub { font-size: 0.85rem; color: var(--text-2) !important; letter-spacing: 0.05em; text-transform: uppercase; margin-top: 0.4rem; }
    .login-box { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 2.5rem; }

    /* ── Section headings ── */
    .section-title { font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 700; color: var(--text-1) !important; margin-bottom: 0.25rem; letter-spacing: -0.02em; }
    .section-sub { font-size: 0.85rem; color: var(--text-2) !important; margin-bottom: 1.5rem; }

    /* ── Sidebar brand ── */
    .sidebar-brand { font-family: 'Inter', sans-serif; font-size: 1.05rem; color: var(--text-1) !important; font-weight: 700; letter-spacing: -0.01em; }
    .sidebar-user { font-size: 0.8rem; color: var(--text-2) !important; margin-top: 0.2rem; }
    .sidebar-role { display: inline-block; font-size: 0.65rem; padding: 2px 8px; border-radius: 20px; background: var(--blue-dim); color: var(--blue) !important; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-top: 0.3rem; border: 1px solid rgba(68,147,248,0.3); }

    /* ── Form section ── */
    .form-section { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 2rem; margin: 1rem 0; }

    /* ── Account cards ── */
    .account-card { background: var(--surface-2); border: 1px solid var(--border); border-radius: 12px; padding: 1.8rem; position: relative; overflow: hidden; }
    .account-card::before { content: ''; position: absolute; top: -40%; right: -20%; width: 70%; height: 140%; background: radial-gradient(circle, rgba(68,147,248,0.1) 0%, transparent 65%); }
    .account-card .acc-type { font-size: 0.68rem; color: var(--blue) !important; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; margin-bottom: 0.8rem; }
    .account-card .acc-balance { font-family: 'Inter', sans-serif; font-size: 2.4rem; font-weight: 800; color: var(--text-1) !important; line-height: 1; letter-spacing: -0.03em; }
    .account-card .acc-detail { font-family: var(--mono); font-size: 0.72rem; color: var(--text-2) !important; margin-top: 0.5rem; }
    .account-card .acc-status { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.62rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.8rem; }
    .status-active { background: var(--green-dim); color: var(--green) !important; border: 1px solid rgba(63,185,80,0.3); }
    .status-closed { background: var(--red-dim); color: var(--red) !important; border: 1px solid rgba(248,81,73,0.3); }

    /* ── Toasts ── */
    .success-toast { background: var(--green-dim); border: 1px solid rgba(63,185,80,0.4); border-left: 3px solid var(--green); color: var(--green) !important; padding: 1rem 1.4rem; border-radius: 8px; margin: 1rem 0; font-size: 0.9rem; }
    .success-toast strong { color: #7ee787 !important; }
    .info-toast { background: var(--blue-dim); border: 1px solid rgba(68,147,248,0.4); border-left: 3px solid var(--blue); color: var(--blue) !important; padding: 1rem 1.4rem; border-radius: 8px; margin: 1rem 0; font-size: 0.9rem; }
    .warning-toast { background: var(--amber-dim); border: 1px solid rgba(210,153,34,0.4); border-left: 3px solid var(--amber); color: var(--amber) !important; padding: 1rem 1.4rem; border-radius: 8px; margin: 1rem 0; font-size: 0.9rem; }

    /* ── Transactions ── */
    .tx-row { display: flex; align-items: center; justify-content: space-between; padding: 0.9rem 1.1rem; border-radius: 8px; margin-bottom: 0.4rem; background: var(--surface); border: 1px solid var(--border); transition: border-color 0.15s; }
    .tx-row:hover { border-color: #8b949e; }
    .tx-icon { font-size: 1.2rem; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 8px; margin-right: 0.9rem; flex-shrink: 0; }
    .tx-icon-deposit { background: var(--green-dim); }
    .tx-icon-withdrawal { background: var(--red-dim); }
    .tx-icon-transfer { background: var(--blue-dim); }
    .tx-icon-other { background: var(--amber-dim); }
    .tx-info { flex-grow: 1; }
    .tx-type { font-weight: 600; font-size: 0.875rem; color: var(--text-1) !important; }
    .tx-meta { font-family: var(--mono); font-size: 0.68rem; color: var(--text-2) !important; margin-top: 2px; }
    .tx-amount { font-weight: 700; font-size: 1rem; text-align: right; flex-shrink: 0; }
    .tx-positive { color: var(--green) !important; }
    .tx-negative { color: var(--red) !important; }

    /* ── Stat cards ── */
    .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 1rem 0; }
    .stat-card { background: var(--surface); border: 1px solid var(--border); border-top: 2px solid var(--blue); border-radius: 8px; padding: 1.2rem 1.5rem; }
    .stat-value { font-family: 'Inter', sans-serif; font-size: 1.9rem; font-weight: 800; color: var(--text-1) !important; letter-spacing: -0.03em; }
    .stat-label { font-size: 0.68rem; color: var(--text-2) !important; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.3rem; }

    /* ── Glass card ── */
    .glass-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.6rem; margin-bottom: 1rem; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

    /* ── Animations ── */
    @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .animate-in { animation: fadeUp 0.35s ease-out forwards; }
    .delay-1 { animation-delay: 0.08s; opacity: 0; }
    .delay-2 { animation-delay: 0.16s; opacity: 0; }
    .delay-3 { animation-delay: 0.24s; opacity: 0; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


# ====================================================================== #
#  STATE
# ====================================================================== #
def init_state():
    """
    Bootstrap Streamlit session state on the very first page load.

    Loads the bank, AuthService, and TransactionManager from disk via
    DataStore, constructs an AccountManager, and stores all services in
    ``st.session_state`` so every page function can access them without
    re-loading.  Also initialises login-related flags to their logged-out
    defaults.  Safe to call on every rerun — the ``initialized`` guard
    prevents duplicate work.
    """
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
    """
    Persist the current bank state to disk via the DataStore.

    Convenience wrapper that reads the bank, auth, and transaction manager
    from ``st.session_state`` and delegates to ``DataStore.save()``.  Call
    this after any mutation (deposit, new customer, loan approval, etc.) so
    changes survive a page refresh.
    """
    st.session_state.store.save(st.session_state.bank, st.session_state.auth, st.session_state.tx_manager)


# ====================================================================== #
#  HELPERS
# ====================================================================== #
def _acct_options(bank, customer):
    """
    Build a display-label → account-number mapping for a customer's active accounts.

    Args:
        bank: The Bank instance used to look up account objects.
        customer: The Customer whose accounts should be listed.

    Returns:
        Dict mapping human-readable labels (e.g. ``"Savings  •  ACCT-0001  •  $500.00"``)
        to raw account number strings.  Only active accounts are included.
    """
    opts = {}
    for acc_num in customer.account_numbers:
        a = bank.find_account(acc_num)
        if a and a.is_active:
            t = "Savings" if isinstance(a, SavingsAccount) else "Checking"
            opts[f"{t}  \u2022  {acc_num}  \u2022  ${a.balance:,.2f}"] = acc_num
    return opts

def _parse_amount(s):
    """
    Parse and validate a user-supplied amount string.

    Args:
        s: Raw string from a Streamlit text input (e.g. ``"250.00"``).

    Returns:
        A positive ``Decimal`` if the input is valid, or ``None`` if it
        is empty, non-numeric, or not greater than zero.  Displays an
        ``st.error`` message before returning ``None``.
    """
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
    """
    Render a styled page-section heading with an optional subtitle.

    Args:
        title: Main heading text.
        sub: Optional secondary line displayed below the heading.
    """
    st.markdown(f'<div class="section-title animate-in">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub animate-in delay-1">{sub}</div>', unsafe_allow_html=True)

def _success(msg):
    """Render a green success toast banner with the given HTML message."""
    st.markdown(f'<div class="success-toast animate-in">{msg}</div>', unsafe_allow_html=True)

def _info(msg):
    """Render a blue informational toast banner with the given HTML message."""
    st.markdown(f'<div class="info-toast animate-in">{msg}</div>', unsafe_allow_html=True)

def _warn(msg):
    """Render a gold warning toast banner with the given HTML message."""
    st.markdown(f'<div class="warning-toast animate-in">{msg}</div>', unsafe_allow_html=True)

def _error(msg):
    """Render a Streamlit error, escaping $ signs so they are not interpreted as LaTeX."""
    st.error(str(msg).replace("$", "\\$"))


# ====================================================================== #
#  LOGIN
# ====================================================================== #
def login_page():
    """
    Render the full-page login form shown to unauthenticated visitors.

    Displays the bank branding, a username/password form, and a hint
    showing the default admin credentials.  On successful authentication
    the session state is updated (``logged_in``, ``username``, ``role``,
    ``customer_id``) and the app reruns to show the main dashboard.
    """
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("""
        <div class="login-brand animate-in">
            <div class="icon">\U0001F3E6</div>
            <div class="hero-title">NovaBank</div>
            <div class="hero-sub">Secure &bull; Reliable &bull; Modern</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box animate-in delay-2">', unsafe_allow_html=True)
    st.markdown('<p style="font-weight:600;color:#e6edf3;margin-bottom:0.3rem;">Username</p>', unsafe_allow_html=True)
    username = st.text_input("Username", placeholder="Enter your username", label_visibility="collapsed")
    st.markdown('<p style="font-weight:600;color:#e6edf3;margin-bottom:0.3rem;margin-top:0.8rem;">Password</p>', unsafe_allow_html=True)
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
            <strong>Demo credentials:</strong>&ensp;
            <code style="background:#1f3a5f;padding:2px 6px;border-radius:4px;color:#4493f8;">admin</code> /
            <code style="background:#1f3a5f;padding:2px 6px;border-radius:4px;color:#4493f8;">admin123</code>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ====================================================================== #
#  SIDEBAR
# ====================================================================== #
def sidebar():
    """
    Render the navigation sidebar and return the currently selected page name.

    Displays the logged-in user's name and role, then shows a role-appropriate
    set of navigation options (customers see account/transaction pages; admins
    see management pages).  Also renders a Sign Out button that clears session
    state and reruns the app.

    Returns:
        The label string of the currently selected radio option.
    """
    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 0.5rem 0 1rem 0;">
                <div class="sidebar-brand">\U0001F3E6 NovaBank</div>
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
                "\U0001F4B0  Review Deposits",
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
    """
    Render the customer dashboard showing all account cards and total portfolio balance.

    Looks up the logged-in customer's accounts and renders each one as a
    styled card (account type, balance, account number, active/closed status).
    A summary card at the bottom shows the combined balance across all accounts.
    """
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
    """
    Render the deposit form allowing a customer to add funds to one of their accounts.

    The customer selects an active account, enters an amount and optional
    description, then submits.  On success the transaction ID is shown and
    the state is saved to disk.
    """
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
                from src.utils.enums import TransactionStatus
                if tx.status == TransactionStatus.PENDING:
                    _warn(f"\u23F3 <strong>${amount:,.2f}</strong> deposit is <strong>pending admin review</strong> and will be credited once approved.<br><small>Transaction: {tx.transaction_id}</small>")
                else:
                    _success(f"\u2705 <strong>${amount:,.2f}</strong> deposited successfully.<br><small>Transaction: {tx.transaction_id}</small>")
            except (ValueError, RuntimeError) as e: _error(e)
    st.markdown('</div>', unsafe_allow_html=True)


def withdraw_page():
    """
    Render the withdrawal form allowing a customer to take funds from one of their accounts.

    The customer selects an active account, enters an amount and optional
    description, then submits.  Balance and minimum-balance rules are enforced
    by the underlying Account model; errors are surfaced via ``st.error``.
    """
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
            except (ValueError, RuntimeError) as e: _error(e)
    st.markdown('</div>', unsafe_allow_html=True)


def transfer_page():
    """
    Render the transfer form allowing a customer to move funds between their own accounts.

    Requires the customer to have at least two accounts.  The customer
    selects a source and destination account and enters an amount.
    Transferring to the same account is blocked client-side before hitting
    the service layer.
    """
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
                except (ValueError, RuntimeError) as e: _error(e)
    st.markdown('</div>', unsafe_allow_html=True)


def transaction_history_page():
    """
    Render the transaction history page showing all activity for a selected account.

    Transactions are displayed in reverse-chronological order (newest first),
    each rendered as a styled row with an icon, description, timestamp, and
    a colour-coded amount (green for credits, red for debits).
    """
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
    """
    Render the customer loans page with two tabs: existing loans and a new application form.

    The "My Loans" tab lists all loans with their status, EMI, and remaining
    balance.  Approved loans show an inline payment form where the customer
    selects which account to pay from; the amount is validated against the
    account balance and deducted before the loan balance is reduced.  The
    "Apply for Loan" tab is hidden if a pending application already exists,
    preventing duplicates.
    """
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
                    customer = bank.find_customer(cid)
                    opts = _acct_options(bank, customer)
                    if not opts:
                        _warn("You need an active account to make a loan payment.")
                    else:
                        am = st.session_state.acct_manager
                        pay_acct = st.selectbox("Pay from account", list(opts.keys()), key=f"pa_{loan.loan_id}")
                        pay = st.text_input("Payment ($)", value=str(loan.emi), key=f"p_{loan.loan_id}")
                        if st.button("Make Payment", key=f"pb_{loan.loan_id}"):
                            try:
                                amount = Decimal(pay)
                                acct_num = opts[pay_acct]
                                acct = bank.find_account(acct_num)
                                if acct.balance < amount:
                                    _error(f"Insufficient funds. Account balance is ${acct.balance:,.2f} but payment is ${amount:,.2f}.")
                                else:
                                    am.withdraw(acct_num, amount, f"Loan payment for {loan.loan_id}")
                                    loan.make_payment(amount)
                                    save()
                                    _success(f"Payment of ${amount:,.2f} deducted from account {acct_num}. Loan remaining: ${loan.remaining_balance:,.2f}")
                            except (ValueError, RuntimeError, InvalidOperation) as e:
                                _error(e)
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
                except (ValueError, InvalidOperation) as e: _error(e)
            st.markdown('</div>', unsafe_allow_html=True)


def cards_page():
    """
    Render the customer cards page listing all debit and credit cards issued to them.

    Each card is shown in a collapsible expander with its number, expiry, and
    status.  Debit cards show their linked account; credit cards show credit
    limit, outstanding balance, and available credit.
    """
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
    """
    Render the admin dashboard with a high-level system overview.

    Displays stat cards for total customers, accounts, active loans, and
    cards issued.  A warning banner is shown when there are pending loan
    applications awaiting review.
    """
    bank = st.session_state.bank
    tm = st.session_state.tx_manager
    _section("Admin Dashboard", "System overview and management.")
    custs = len(bank._customers); accts = len(bank._accounts)
    active_loans = sum(1 for l in bank._loans.values() if l.status == LoanStatus.APPROVED)
    ncards = len(bank._cards)
    pending_loans = sum(1 for l in bank._loans.values() if l.status == LoanStatus.PENDING)
    from src.utils.enums import TransactionStatus
    pending_deposits = sum(
        1 for tx in tm.get_all_transactions()
        if tx.transaction_type.value == "deposit" and tx.status == TransactionStatus.PENDING
    )
    st.markdown(f"""
        <div class="stat-grid animate-in">
            <div class="stat-card"><div class="stat-value">{custs}</div><div class="stat-label">Customers</div></div>
            <div class="stat-card"><div class="stat-value">{accts}</div><div class="stat-label">Accounts</div></div>
            <div class="stat-card"><div class="stat-value">{active_loans}</div><div class="stat-label">Active Loans</div></div>
            <div class="stat-card"><div class="stat-value">{ncards}</div><div class="stat-label">Cards Issued</div></div>
        </div>
    """, unsafe_allow_html=True)
    if pending_loans > 0: _warn(f"\u26A0\uFE0F <strong>{pending_loans}</strong> loan application(s) awaiting your review.")
    if pending_deposits > 0: _warn(f"\u26A0\uFE0F <strong>{pending_deposits}</strong> deposit(s) flagged and awaiting your review.")


def register_customer_page():
    """
    Render the admin form for registering a new customer with full KYC details.

    Collects personal info, address, government ID, employment details,
    and login credentials.  Creates a Customer entity, registers it with
    the Bank, and creates a CUSTOMER-role login via AuthService.
    """
    from src.models.customer import EMPLOYMENT_STATUSES, INCOME_RANGES, ID_TYPES
    _section("Register Customer", "Create a new customer profile with full KYC details.")
    bank, auth = st.session_state.bank, st.session_state.auth

    st.markdown('<div class="form-section">', unsafe_allow_html=True)

    st.markdown("**Personal Information**")
    c1, c2 = st.columns(2)
    with c1:
        fn = st.text_input("First Name")
        ln = st.text_input("Last Name")
        dob = st.date_input("Date of Birth", min_value=date(1900, 1, 1), max_value=date.today(), value=date(1990, 1, 1))
    with c2:
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")
        nationality = st.text_input("Nationality")

    st.markdown("---")
    st.markdown("**Residential Address**")
    address = st.text_input("Street Address")
    c3, c4, c5 = st.columns(3)
    with c3: city = st.text_input("City")
    with c4: state = st.text_input("State / Province")
    with c5: zip_code = st.text_input("ZIP / Postal Code")
    country = st.text_input("Country")

    st.markdown("---")
    st.markdown("**Government Identification**")
    c6, c7 = st.columns(2)
    with c6: id_type = st.selectbox("ID Type", ID_TYPES)
    with c7: id_number = st.text_input("ID Number")

    st.markdown("---")
    st.markdown("**Financial Profile**")
    c8, c9 = st.columns(2)
    with c8: employment_status = st.selectbox("Employment Status", EMPLOYMENT_STATUSES)
    with c9: annual_income = st.selectbox("Annual Income", INCOME_RANGES)

    st.markdown("---")
    st.markdown("**Login Credentials**")
    c10, c11 = st.columns(2)
    with c10: uname = st.text_input("Username")
    with c11: pw = st.text_input("Password", type="password")

    if st.button("Register Customer", use_container_width=True):
        if not all([fn, ln, email, phone, nationality, address, city, state, zip_code, country, id_number, uname, pw]):
            st.error("All fields are required.")
        else:
            try:
                cid = bank.id_generator.generate_customer_id()
                c = Customer(
                    cid, fn, ln, email, phone,
                    dob.isoformat(), nationality,
                    address, city, state, zip_code, country,
                    id_type, id_number,
                    employment_status, annual_income,
                )
                bank.add_customer(c)
                auth.register(uname, pw, Role.CUSTOMER, cid)
                save()
                _success(f"\u2705 <strong>{fn} {ln}</strong> registered as <code>{cid}</code> &mdash; Login: <code>{uname}</code>")
            except ValueError as e:
                _error(e)

    st.markdown('</div>', unsafe_allow_html=True)


def create_account_page():
    """
    Render the admin form for opening a new savings or checking account for a customer.

    The admin selects an existing customer, chooses the account type, and
    enters an initial deposit.  The AccountManager handles creation and
    logs the opening deposit transaction automatically.
    """
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
        except (ValueError, KeyError) as e: _error(e)
    st.markdown('</div>', unsafe_allow_html=True)


def manage_loans_page():
    """
    Render the admin loan management page with tabs for pending and processed loans.

    The "Pending" tab shows each unreviewed application with Approve/Reject
    buttons.  Approving calls ``loan.approve()``; rejecting calls ``loan.reject()``.
    Both actions save state and rerun the app to refresh the list.  The
    "Processed" tab shows all approved, rejected, or closed loans read-only.
    """
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
    """
    Render the admin form for issuing a debit or credit card to a customer.

    Debit card issuance requires the customer to have at least one active
    account to link.  Credit card issuance requires a credit limit.  Both
    card types require a 4-digit PIN which is hashed before storage.
    """
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
            except (ValueError, InvalidOperation) as e: _error(e)
    st.markdown('</div>', unsafe_allow_html=True)


def all_customers_page():
    """
    Render the admin view of all registered customers with removal support.

    Each customer is shown in a collapsible expander with their contact
    details, linked accounts, and a Remove Customer button.  Removal is
    blocked if the customer has any remaining balance or outstanding loans.
    """
    _section("All Customers", "View and manage registered customer profiles.")
    bank = st.session_state.bank
    auth = st.session_state.auth
    customers = bank.get_all_customers()
    if not customers: _info("No customers registered yet."); return
    for c in customers:
        with st.expander(f"\U0001F464  {c.full_name}  \u2022  {c.customer_id}"):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Email:** {c.email}")
            c1.write(f"**Phone:** {c.phone}")
            c1.write(f"**Date of Birth:** {getattr(c, '_date_of_birth', '') or '—'}")
            c1.write(f"**Nationality:** {getattr(c, '_nationality', '') or '—'}")
            c2.write(f"**Address:** {getattr(c, '_address', '') or '—'}")
            c2.write(f"**City:** {getattr(c, '_city', '') or '—'}, {getattr(c, '_state', '') or '—'}")
            c2.write(f"**ZIP:** {getattr(c, '_zip_code', '') or '—'}")
            c2.write(f"**Country:** {getattr(c, '_country', '') or '—'}")
            c3.write(f"**ID:** {getattr(c, '_id_type', '') or '—'} — {getattr(c, '_id_number', '') or '—'}")
            c3.write(f"**Employment:** {getattr(c, '_employment_status', '') or '—'}")
            c3.write(f"**Income:** {getattr(c, '_annual_income', '') or '—'}")
            accs = [bank.find_account(a) for a in c.account_numbers if bank.find_account(a)]
            c3.write(f"**Accounts:** {len(accs)}")
            for a in accs:
                t = "Savings" if isinstance(a, SavingsAccount) else "Checking"
                c3.write(f"` {a.account_number} `  {t}  \u2014  ${a.balance:,.2f}")

            st.markdown("---")
            confirm_key = f"confirm_remove_{c.customer_id}"
            if st.session_state.get(confirm_key):
                st.warning(f"Are you sure you want to permanently remove **{c.full_name}**? This cannot be undone.")
                col1, col2 = st.columns(2)
                if col1.button("Yes, remove", key=f"yes_{c.customer_id}", use_container_width=True):
                    try:
                        bank.offboard_customer(c.customer_id)
                        auth.remove_user_by_customer_id(c.customer_id)
                        save()
                        st.success(f"{c.full_name} has been removed.")
                        st.session_state[confirm_key] = False
                        st.rerun()
                    except (ValueError, KeyError) as e:
                        _error(e)
                        st.session_state[confirm_key] = False
                if col2.button("Cancel", key=f"cancel_{c.customer_id}", use_container_width=True):
                    st.session_state[confirm_key] = False
                    st.rerun()
            else:
                if st.button(f"\U0001F5D1\uFE0F  Remove Customer", key=f"rm_{c.customer_id}", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()


def review_deposits_page():
    """
    Render the admin page for reviewing flagged deposit transactions.

    Deposits >= $5,000 or that pushed a customer's daily total over $10,000
    are held as PENDING.  The admin can approve (credit the account) or
    reject (discard without crediting) each one.
    """
    _section("Review Deposits", "Approve or reject flagged deposit transactions.")
    from src.utils.enums import TransactionStatus
    bank = st.session_state.bank
    am = st.session_state.acct_manager
    tm = st.session_state.tx_manager

    pending = [
        tx for tx in tm.get_all_transactions()
        if tx.transaction_type.value == "deposit" and tx.status == TransactionStatus.PENDING
    ]
    processed = [
        tx for tx in tm.get_all_transactions()
        if tx.transaction_type.value == "deposit" and tx.status != TransactionStatus.PENDING
        and tx.status != TransactionStatus.COMPLETED or (
            tx.transaction_type.value == "deposit"
            and tx.status == TransactionStatus.FAILED
        )
    ]

    if not pending:
        _info("No deposits are currently pending review.")
    else:
        st.markdown(f"**{len(pending)} deposit(s) awaiting review:**")
        for tx in pending:
            acct = bank.find_account(tx.target_account)
            customer = bank.find_customer(acct.customer_id) if acct else None
            name = customer.full_name if customer else "Unknown"
            with st.expander(f"💰  {tx.transaction_id}  —  ${tx.amount:,.2f}  —  {name}  ({tx.target_account})"):
                st.write(f"**Amount:** ${tx.amount:,.2f}")
                st.write(f"**Account:** {tx.target_account}")
                st.write(f"**Customer:** {name}")
                st.write(f"**Description:** {tx.description}")
                st.write(f"**Submitted:** {tx.timestamp:%Y-%m-%d %H:%M:%S}")
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"appr_{tx.transaction_id}", use_container_width=True):
                    try:
                        am.approve_pending_deposit(tx.transaction_id); save()
                        st.success(f"Deposit {tx.transaction_id} approved. ${tx.amount:,.2f} credited.")
                        st.rerun()
                    except Exception as e: _error(e)
                if c2.button("❌ Reject", key=f"rej_{tx.transaction_id}", use_container_width=True):
                    try:
                        am.reject_pending_deposit(tx.transaction_id); save()
                        st.warning(f"Deposit {tx.transaction_id} rejected.")
                        st.rerun()
                    except Exception as e: _error(e)

    rejected = [
        tx for tx in tm.get_all_transactions()
        if tx.transaction_type.value == "deposit" and tx.status == TransactionStatus.FAILED
    ]
    if rejected:
        st.markdown("---")
        st.markdown(f"**{len(rejected)} rejected deposit(s):**")
        for tx in rejected:
            acct = bank.find_account(tx.target_account)
            customer = bank.find_customer(acct.customer_id) if acct else None
            name = customer.full_name if customer else "Unknown"
            st.markdown(f"- `{tx.transaction_id}` &nbsp; ${tx.amount:,.2f} &nbsp; {name} &nbsp; <span style='color:#e74c3c'>Rejected</span>", unsafe_allow_html=True)


# ====================================================================== #
#  ROUTER
# ====================================================================== #
def main():
    """
    Application entry point and page router.

    Initialises session state and injects CSS on every rerun, then routes
    to either the login page (unauthenticated) or the appropriate page
    function based on the sidebar selection and the logged-in user's role.
    """
    init_state()
    inject_css()
    if not st.session_state.logged_in: login_page(); return
    page = sidebar()
    if st.session_state.role == Role.CUSTOMER:
        routes = {"\U0001F3E0  Dashboard": customer_dashboard, "\U0001F4B0  Deposit": deposit_page, "\U0001F4B8  Withdraw": withdraw_page, "\U0001F504  Transfer": transfer_page, "\U0001F4DC  Transactions": transaction_history_page, "\U0001F4CB  Loans": loans_page, "\U0001F4B3  Cards": cards_page}
    else:
        routes = {"\U0001F3E0  Dashboard": admin_dashboard, "\U0001F464  Register Customer": register_customer_page, "\U0001F3E6  Create Account": create_account_page, "\U0001F4CB  Manage Loans": manage_loans_page, "\U0001F4B0  Review Deposits": review_deposits_page, "\U0001F4B3  Issue Card": issue_card_page, "\U0001F465  All Customers": all_customers_page}
    fn = routes.get(page)
    if fn: fn()

if __name__ == "__main__":
    main()