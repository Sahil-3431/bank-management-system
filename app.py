import streamlit as st

from auth import (
    create_initial_admin,
    login_page,
    logout,
    is_admin,
    validate_current_session,
)

from database import init_db

from ui import (
    dashboard_page,
    customer_page,
    account_page,
    transaction_page,
    user_banking_page,
    user_management_page,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Bank Management System",
    page_icon="🏦",
    layout="wide",
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_db()


# ============================================================
# INITIAL ADMIN
# ============================================================

create_initial_admin()


# ============================================================
# SESSION STATE
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "customer_id" not in st.session_state:
    st.session_state.customer_id = None


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.authenticated:

    login_page()

    st.stop()


# ============================================================
# SESSION SECURITY VALIDATION
# ============================================================

if not validate_current_session():

    logout()

    st.error(
        "Your session is no longer valid. "
        "Please login again."
    )
    st.stop()


# ============================================================
# GET CURRENT ROLE
# ============================================================

current_role = st.session_state.get(
    "role",
    "user",
)

# ============================================================
# PREMIUM SIDEBAR CSS
# ============================================================

st.markdown(
    """
    <style>
    /* ======================================================
       SIDEBAR
       ====================================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #171923 0%,
                #11131a 55%,
                #0d0f14 100%
            );
        border-right:
            1px solid rgba(255,255,255,0.08);

    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;

    }

    /* ======================================================
       BRAND
       ====================================================== */

    .premium-brand {
        padding:
            8px 5px 22px 5px;
    }
    .brand-icon {
        font-size: 2.5rem;
        line-height: 1;
        margin-bottom: 8px;
    }
    .brand-title {
        font-size: 1.42rem;
        font-weight: 850;
        letter-spacing: 1px;
        color: #ffffff;
        line-height: 1.15;
    }
    .brand-subtitle {
        font-size: 0.68rem;
        color: #858c9d;
        letter-spacing: 1.8px;
        margin-top: 7px;
        text-transform: uppercase;
    }

    /* ======================================================
       PROFILE CARD
       ====================================================== */

    .sidebar-profile {
        background:
            linear-gradient(
                145deg,
                rgba(255,255,255,0.075),
                rgba(255,255,255,0.025)
            );
        border:
            1px solid rgba(255,255,255,0.09);
        border-radius: 16px;
        padding: 14px;
        margin:
            4px 0 26px 0;
        box-shadow:
            0 8px 25px rgba(0,0,0,0.18);
    }
    .profile-top {
        display: flex;
        align-items: center;
        gap: 11px;
    }
    .profile-avatar {
        width: 40px;
        height: 40px;
        min-width: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        background:
            linear-gradient(
                135deg,
                #6366f1,
                #8b5cf6
            );
        font-size: 1.15rem;
        box-shadow:
            0 5px 15px
            rgba(99,102,241,0.28);
    }
    .profile-name {
        color: #ffffff;
        font-size: 0.96rem;
        font-weight: 750;
        line-height: 1.2;
    }
    .profile-role {
        color: #9299aa;
        font-size: 0.72rem;
        margin-top: 4px;
    }
    .role-badge {
        display: inline-block;
        margin-top: 12px;
        padding:
            4px 10px;
        border-radius: 999px;
        background:
            rgba(99,102,241,0.13);
        border:
            1px solid
            rgba(99,102,241,0.28);
        color: #a5b4fc;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
    }

    /* ======================================================
       MENU TITLE
       ====================================================== */

    .sidebar-section-title {
        color: #777f92;
        font-size: 0.68rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin:
            0 0 9px 4px;
    }

    /* ======================================================
       RADIO NAVIGATION
       ====================================================== */

    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] > label {
        display: none;

    }
    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] > div {
        gap: 5px;
    }
    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] label {
        border-radius: 12px;
        padding:
            9px 11px;
        transition:
            all 0.2s ease;
        color: #c5cad5;
    }
    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] label:hover {
        background:
            rgba(255,255,255,0.055);
        color: #ffffff;
    }
    section[data-testid="stSidebar"]
    div[data-testid="stRadio"]
    label:has(input:checked) {
        background:
            linear-gradient(
                90deg,
                rgba(99,102,241,0.20),
                rgba(139,92,246,0.08)
            );
        border:
            1px solid
            rgba(99,102,241,0.25);
        color: #ffffff;
        box-shadow:
            0 5px 18px
            rgba(0,0,0,0.12);
    }

    /* ======================================================
       DIVIDER
       ====================================================== */

    .sidebar-divider {
        height: 1px;
        background:
            rgba(255,255,255,0.08);
        margin:
            24px 0 18px 0;
    }

    /* ======================================================
       LOGOUT BUTTON
       ====================================================== */

    section[data-testid="stSidebar"]
    button {
        border-radius: 12px;
        border:
            1px solid
            rgba(255,255,255,0.10);
        background:
            rgba(255,255,255,0.035);
        color: #d7dbe4;
        font-weight: 650;
        min-height: 43px;
        transition:
            all 0.2s ease;
    }
    section[data-testid="stSidebar"]
    button:hover {
        background:
            rgba(239,68,68,0.10);
        border-color:
            rgba(239,68,68,0.30);

        color: #fca5a5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PREMIUM SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="premium-brand">
            <div class="brand-icon">
                🏦
            </div>
            <div class="brand-title">
                BANK MANAGEMENT
            </div>
            <div class="brand-subtitle">
                Secure Banking System
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    if is_admin():
        profile_icon = "👑"
        profile_role = "Administrator"

    else:
        profile_icon = "👤"
        profile_role = "Bank Customer"

    st.markdown(
        f"""
        <div class="sidebar-profile">
            <div class="profile-top">
                <div class="profile-avatar">
                    {profile_icon}
                </div>
                <div>
                    <div class="profile-name">
                        {st.session_state.username}
                    </div>
                    <div class="profile-role">
                        {profile_role}
                    </div>
                </div>
            </div>
            <div class="role-badge">
                {current_role}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # MENU TITLE
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="sidebar-section-title">
            Main Menu
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # ADMIN NAVIGATION
    # ========================================================

    if is_admin():
        page = st.radio(
            "Navigation",
            [
                "📊 Dashboard",
                "👤 Customers",
                "🏦 Accounts",
                "💰 Transactions",
                "🛡️ User Management",
            ],
            label_visibility="collapsed",
        )

    # ========================================================
    # USER NAVIGATION
    # ========================================================

    else:
        page = st.radio(
            "Navigation",
            [
                "💰 My Banking",
            ],
            label_visibility="collapsed",
        )

    # --------------------------------------------------------
    # DIVIDER
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-divider"></div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

    if st.button(
        "🚪  Logout",
        use_container_width=True,
    ):
        logout()


# ============================================================
# ADMIN PAGES
# ============================================================

if is_admin():
    if page == "📊 Dashboard":
        dashboard_page()

    elif page == "👤 Customers":
        customer_page()

    elif page == "🏦 Accounts":
        account_page()

    elif page == "💰 Transactions":
        transaction_page()
    elif page == "🛡️ User Management":
        user_management_page()


# ============================================================
# USER PAGES
# ============================================================

else:
    if page == "💰 My Banking":
        user_banking_page()