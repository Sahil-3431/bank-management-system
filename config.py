import os
from dotenv import load_dotenv

load_dotenv()


def get_setting(name, default=None):
    """
    First try environment variables.
    If not found, try Streamlit secrets.
    """
    value = os.getenv(name)

    if value:
        return value

    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = get_setting("DATABASE_URL")


# ============================================================
# INITIAL ADMIN CONFIGURATION
# ============================================================

INITIAL_ADMIN_USERNAME = get_setting(
    "INITIAL_ADMIN_USERNAME",
    "admin",
)

INITIAL_ADMIN_PASSWORD = get_setting(
    "INITIAL_ADMIN_PASSWORD"
)


# ============================================================
# EMAIL / SMTP CONFIGURATION
# ============================================================

SMTP_HOST = get_setting(
    "SMTP_HOST",
    "smtp.gmail.com",
)

SMTP_PORT = int(
    get_setting(
        "SMTP_PORT",
        "587",
    )
)

SMTP_USERNAME = get_setting(
    "SMTP_USERNAME",
)

SMTP_PASSWORD = get_setting(
    "SMTP_PASSWORD",
)

SMTP_FROM_EMAIL = get_setting(
    "SMTP_FROM_EMAIL",
    SMTP_USERNAME,
)

SMTP_USE_TLS = str(
    get_setting(
        "SMTP_USE_TLS",
        "true",
    )
).lower() == "true"

# ============================================================
# OTP SECURITY CONFIGURATION
# ============================================================

OTP_HASH_SECRET = get_setting(
    "OTP_HASH_SECRET"
)