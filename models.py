from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from database import Base

# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(20),
        nullable=False,
        default="user",
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    customer = relationship(
        "Customer",
        back_populates="user",
    )

# ============================================================
# CUSTOMER MODEL
# ============================================================

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer,primary_key=True,index=True,)
    customer_code = Column(String(20),unique=True,nullable=False,index=True,)
    full_name = Column(String(120),nullable=False,)
    email = Column(String(120),unique=True,nullable=False,index=True,)
    phone = Column(String(20),nullable=False,)
    address = Column(Text,nullable=True,)
    created_at = Column(DateTime,nullable=False,default=datetime.utcnow,)
    is_active = Column(Boolean,nullable=False,default=True)
    accounts = relationship("Account",back_populates="customer",cascade="all, delete-orphan")
    user = relationship("User",back_populates="customer",uselist=False)

# ============================================================
# ACCOUNT MODEL
# ============================================================

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer,primary_key=True,index=True,)
    account_number = Column(String(20),unique=True,nullable=False,index=True,)
    account_type = Column(String(20),nullable=False,default="Savings",)
    balance = Column(Numeric(15, 2),nullable=False,default=Decimal("0.00"),)
    status = Column(String(20),nullable=False,default="Active",)
    customer_id = Column(Integer,ForeignKey("customers.id"),nullable=False,index=True,)
    created_at = Column(DateTime,nullable=False,default=datetime.utcnow,)
    customer = relationship("Customer",back_populates="accounts",)
    transactions = relationship("Transaction",back_populates="account",foreign_keys="Transaction.account_id",cascade="all, delete-orphan")

# ============================================================
# TRANSACTION MODEL
# ============================================================

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    transaction_ref = Column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    transaction_type = Column(
        String(30),
        nullable=False,
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    balance_after = Column(
        Numeric(15, 2),
        nullable=False,
    )

    reference_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=True,
        index=True,
    )

    description = Column(
        String(255),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    account = relationship(
        "Account",
        back_populates="transactions",
        foreign_keys=[account_id],
    )

    reference_account = relationship(
        "Account",
        foreign_keys=[reference_account_id],
    )

# ============================================================
# OTP VERIFICATION
# ============================================================

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    email = Column(
        String(120),
        nullable=False,
        index=True,
    )

    otp_hash = Column(
        String(255),
        nullable=False,
    )

    purpose = Column(
        String(30),
        nullable=False,
    )

    # Transaction details bound to this OTP
    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    reference_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=True,
        index=True,
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False,
    )

    expires_at = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    attempts = Column(
        Integer,
        nullable=False,
        default=0,
    )

    max_attempts = Column(
        Integer,
        nullable=False,
        default=5,
    )

    is_verified = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    verified_at = Column(
        DateTime,
        nullable=True,
    )

# ============================================================
# PASSWORD RESET OTP
# ============================================================

class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    email = Column(
        String(120),
        nullable=False,
        index=True,
    )

    otp_hash = Column(
        String(255),
        nullable=False,
    )

    expires_at = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    attempts = Column(
        Integer,
        nullable=False,
        default=0,
    )

    max_attempts = Column(
        Integer,
        nullable=False,
        default=5,
    )

    is_verified = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    verified_at = Column(
        DateTime,
        nullable=True,
    )