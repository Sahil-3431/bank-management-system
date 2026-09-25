import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from database import SessionLocal
from config import OTP_HASH_SECRET
from email_service import (
    send_email,
    send_invalid_otp_email,
    send_expired_otp_email,
    send_max_attempts_email,
)
from models import (
    Customer,
    Account,
    OTPVerification,
    PasswordResetOTP,
)

# ============================================================
# OTP CONFIGURATION
# ============================================================

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


# ============================================================
# GENERATE OTP
# ============================================================

def generate_otp() -> str:
    """
    Generates a secure 6-digit OTP.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


# ============================================================
# HASH OTP
# ============================================================

def hash_otp(otp: str) -> str:
    """
    Creates a secure HMAC-SHA256 hash of the OTP.
    """

    if not OTP_HASH_SECRET:
        raise ValueError(
            "OTP_HASH_SECRET is not configured."
        )

    return hmac.new(
        OTP_HASH_SECRET.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


# ============================================================
# VERIFY OTP HASH
# ============================================================

def verify_otp_hash(
    otp: str,
    stored_hash: str,
) -> bool:
    """
    Safely compares entered OTP with stored OTP hash.
    """

    calculated_hash = hash_otp(otp)

    return hmac.compare_digest(
        calculated_hash,
        stored_hash,
    )


# ============================================================
# SEND TRANSACTION OTP
# ============================================================

def send_transaction_otp(
    customer_id: int,
    account_id: int,
    amount,
    purpose: str,
    reference_account_id: int = None,
) -> dict:
    """
    Generates and sends OTP for a transaction.

    The OTP is linked to the exact transaction details.
    """

    db = SessionLocal()

    # ----------------------------------------------------
    # Validate account ownership
    # ----------------------------------------------------

    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.customer_id == customer_id,
        )
        .first()
        )

    if not account:
        return {
            "success": False,
            "message": (
                "You are not authorized to initiate "
                "a transaction for this account."
            ),
        }

    # ----------------------------------------------------
    # Validate reference account
    # ----------------------------------------------------
    # Reference account is used for transfers.
    # It can belong to another customer, so we only
    # verify that the account exists.

    if reference_account_id is not None:
        if reference_account_id == account_id:
            return {
                "success": False,
                "message": (
                    "Source and destination accounts "
                    "cannot be the same."
                ),
            }

        reference_account = (
            db.query(Account)
            .filter(
                Account.id == reference_account_id
            )
            .first()
        )

        if not reference_account:
            return {
                "success": False,
                "message": (
                    "Destination account was not found."
                ),
            }

        if reference_account.status != "Active":
            return {
                "success": False,
                "message": (
                    "Destination account is not active."
                ),
            }

    try:

        # ----------------------------------------------------
        # Validate customer
        # ----------------------------------------------------

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": "Customer not found.",
            }

        if not customer.email:
            return {
                "success": False,
                "message": (
                    "Customer does not have a registered email."
                ),
            }

        # ----------------------------------------------------
        # Validate amount
        # ----------------------------------------------------

        try:
            amount = Decimal(str(amount))
        except Exception:
            return {
                "success": False,
                "message": "Invalid transaction amount.",
            }

        if amount <= Decimal("0.00"):
            return {
                "success": False,
                "message": (
                    "Transaction amount must be greater than zero."
                ),
            }

        # ----------------------------------------------------
        # Invalidate previous unverified OTPs
        # ----------------------------------------------------

        previous_otps = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.customer_id == customer_id,
                OTPVerification.is_verified.is_(False),
            )
            .all()
        )

        for old_otp in previous_otps:
            old_otp.is_verified = True

        # ----------------------------------------------------
        # Generate OTP
        # ----------------------------------------------------

        otp = generate_otp()

        otp_hash_value = hash_otp(otp)

        expires_at = (
            datetime.utcnow()
            + timedelta(minutes=OTP_EXPIRY_MINUTES)
        )

        # ----------------------------------------------------
        # Save OTP challenge
        # ----------------------------------------------------

        otp_record = OTPVerification(
            customer_id=customer_id,
            email=customer.email,
            otp_hash=otp_hash_value,
            purpose=purpose,
            account_id=account_id,
            reference_account_id=reference_account_id,
            amount=amount,
            expires_at=expires_at,
            attempts=0,
            max_attempts=MAX_OTP_ATTEMPTS,
            is_verified=False,
        )
        db.add(otp_record)
        db.commit()

        # ----------------------------------------------------
        # Send email
        # ----------------------------------------------------

        subject = ("Bank Management System - Transaction Verification OTP")
        body = f"""
        Hello {customer.full_name},

        Your OTP for transaction verification is:

        {otp}

        Transaction Type: {purpose}
        Amount: ₹{amount:,.2f}

        This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.

        You have a maximum of {MAX_OTP_ATTEMPTS} verification attempts.

        If you did not initiate this transaction, please contact the bank administrator immediately.

        Do not share this OTP with anyone.

        Regards,
        Bank Management System
        """
        email_result = send_email(
            recipient_email=customer.email,
            subject=subject,
            body=body.strip(),
        )
        if not email_result["success"]:

            # Remove OTP record if email could not be sent
            db.delete(otp_record)
            db.commit()
            return {
                "success": False,
                "message": email_result["message"],
            }
        return {
            "success": True,
            "message": (
                f"OTP sent successfully to "
                f"{mask_email(customer.email)}."
            ),
            "otp_id": otp_record.id,
            "expires_at": expires_at,
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Unable to send OTP: {str(e)}",
        }
    finally:
        db.close()


# ============================================================
# VERIFY TRANSACTION OTP
# ============================================================

def verify_transaction_otp(
    otp_id: int,
    entered_otp: str,
) -> dict:
    """
    Verifies transaction OTP.

    Returns the transaction details only when verification
    is successful.

    Sends security notification emails when:
    - OTP is incorrect
    - OTP has expired
    - Maximum OTP attempts are exceeded
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Find OTP
        # ----------------------------------------------------

        otp_record = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.id == otp_id
            )
            .first()
        )

        if not otp_record:
            return {
                "success": False,
                "message": "OTP verification request not found.",
            }

        # ----------------------------------------------------
        # Prepare email information
        # ----------------------------------------------------

        transaction_datetime = datetime.utcnow().strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )

        transaction_type = otp_record.purpose
        transaction_amount = otp_record.amount
        recipient_email = otp_record.email

        # ----------------------------------------------------
        # Already verified / invalidated OTP
        # ----------------------------------------------------

        if otp_record.is_verified:
            return {
                "success": False,
                "message": "This OTP has already been used.",
            }

        # ----------------------------------------------------
        # Maximum attempts
        # ----------------------------------------------------

        if otp_record.attempts >= otp_record.max_attempts:

            otp_record.is_verified = True
            db.commit()

            send_max_attempts_email(
                recipient_email=recipient_email,
                transaction_type=transaction_type,
                amount=transaction_amount,
                transaction_datetime=transaction_datetime,
            )

            return {
                "success": False,
                "message": (
                    "Maximum OTP verification attempts exceeded."
                ),
            }

        # ----------------------------------------------------
        # Expiry check
        # ----------------------------------------------------

        if datetime.utcnow() > otp_record.expires_at:

            otp_record.is_verified = True
            db.commit()

            send_expired_otp_email(
                recipient_email=recipient_email,
                transaction_type=transaction_type,
                amount=transaction_amount,
                transaction_datetime=transaction_datetime,
            )

            return {
                "success": False,
                "message": (
                    "OTP has expired. Please request a new OTP."
                ),
            }

        # ----------------------------------------------------
        # Validate OTP format
        # ----------------------------------------------------

        entered_otp = str(entered_otp).strip()

        if (
            len(entered_otp) != OTP_LENGTH
            or not entered_otp.isdigit()
        ):

            otp_record.attempts += 1

            # If this attempt reaches maximum attempts,
            # block the OTP and send maximum-attempts email.
            if otp_record.attempts >= otp_record.max_attempts:

                otp_record.is_verified = True
                db.commit()

                send_max_attempts_email(
                    recipient_email=recipient_email,
                    transaction_type=transaction_type,
                    amount=transaction_amount,
                    transaction_datetime=transaction_datetime,
                )

                return {
                    "success": False,
                    "message": (
                        "Maximum OTP verification attempts exceeded."
                    ),
                }

            db.commit()

            remaining = (
                otp_record.max_attempts
                - otp_record.attempts
            )

            send_invalid_otp_email(
                recipient_email=recipient_email,
                transaction_type=transaction_type,
                amount=transaction_amount,
                transaction_datetime=transaction_datetime,
            )

            return {
                "success": False,
                "message": (
                    f"Invalid OTP format. "
                    f"Attempts remaining: {max(remaining, 0)}"
                ),
            }

        # ----------------------------------------------------
        # Verify OTP
        # ----------------------------------------------------

        if not verify_otp_hash(
            entered_otp,
            otp_record.otp_hash,
        ):

            otp_record.attempts += 1

            # ------------------------------------------------
            # Maximum attempts reached
            # ------------------------------------------------

            if otp_record.attempts >= otp_record.max_attempts:

                otp_record.is_verified = True
                db.commit()

                send_max_attempts_email(
                    recipient_email=recipient_email,
                    transaction_type=transaction_type,
                    amount=transaction_amount,
                    transaction_datetime=transaction_datetime,
                )

                return {
                    "success": False,
                    "message": (
                        "Maximum OTP attempts exceeded."
                    ),
                }

            # ------------------------------------------------
            # Normal incorrect OTP
            # ------------------------------------------------

            db.commit()

            remaining = (
                otp_record.max_attempts
                - otp_record.attempts
            )

            send_invalid_otp_email(
                recipient_email=recipient_email,
                transaction_type=transaction_type,
                amount=transaction_amount,
                transaction_datetime=transaction_datetime,
            )

            return {
                "success": False,
                "message": (
                    f"Incorrect OTP. "
                    f"Attempts remaining: {remaining}"
                ),
            }

        # ----------------------------------------------------
        # Successful verification
        # ----------------------------------------------------

        otp_record.is_verified = True
        otp_record.verified_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "message": "OTP verified successfully.",

            # Return the exact transaction details
            # that were authorized by the OTP.
            "customer_id": otp_record.customer_id,
            "account_id": otp_record.account_id,
            "reference_account_id": (
                otp_record.reference_account_id
            ),
            "amount": Decimal(
                str(otp_record.amount)
            ),
            "purpose": otp_record.purpose,
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"OTP verification failed: {str(e)}"
            ),
        }

    finally:
        db.close()


# ============================================================
# MASK EMAIL
# ============================================================

def mask_email(email: str) -> str:
    """
    Masks email address before displaying it in UI.
    """

    if not email or "@" not in email:
        return "registered email"

    username, domain = email.split("@", 1)

    if len(username) <= 2:
        masked_username = username[0] + "*"
    else:
        masked_username = (
            username[0]
            + "*" * (len(username) - 2)
            + username[-1]
        )

    return f"{masked_username}@{domain}"

# ============================================================
# SEND PASSWORD RESET OTP
# ============================================================

def send_password_reset_otp(
    customer_id: int,
) -> dict:
    """
    Generate and send a password-reset OTP
    to the customer's registered email.
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Find customer
        # ----------------------------------------------------

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
            .first()
        )

        if not customer:

            return {
                "success": False,
                "message": "Customer not found.",
            }

        # ----------------------------------------------------
        # Check customer status
        # ----------------------------------------------------

        if not customer.is_active:

            return {
                "success": False,
                "message": (
                    "This customer account is currently blocked."
                ),
            }

        # ----------------------------------------------------
        # Check registered email
        # ----------------------------------------------------

        if not customer.email:

            return {
                "success": False,
                "message": (
                    "Customer does not have a registered email."
                ),
            }

        # ----------------------------------------------------
        # Invalidate previous reset OTPs
        # ----------------------------------------------------

        previous_otps = (
            db.query(PasswordResetOTP)
            .filter(
                PasswordResetOTP.customer_id
                == customer.id,
                PasswordResetOTP.is_verified.is_(False),
            )
            .all()
        )

        for old_otp in previous_otps:
            old_otp.is_verified = True

        # ----------------------------------------------------
        # Generate OTP
        # ----------------------------------------------------

        otp = generate_otp()

        otp_hash_value = hash_otp(otp)

        expires_at = (
            datetime.utcnow()
            + timedelta(
                minutes=OTP_EXPIRY_MINUTES
            )
        )

        # ----------------------------------------------------
        # Create OTP record
        # ----------------------------------------------------

        otp_record = PasswordResetOTP(
            customer_id=customer.id,
            email=customer.email,
            otp_hash=otp_hash_value,
            expires_at=expires_at,
            attempts=0,
            max_attempts=MAX_OTP_ATTEMPTS,
            is_verified=False,
        )

        db.add(otp_record)
        db.commit()

        # ----------------------------------------------------
        # Send OTP email
        # ----------------------------------------------------

        subject = (
            "Bank Management System - "
            "Password Reset OTP"
        )

        body = f"""
Hello {customer.full_name},

We received a request to reset your
Bank Management System password.

Your password reset OTP is:

{otp}

This OTP is valid for
{OTP_EXPIRY_MINUTES} minutes.

You have a maximum of
{MAX_OTP_ATTEMPTS} verification attempts.

If you did not request a password reset,
please ignore this email and contact the
bank administrator if necessary.

Do not share this OTP with anyone.

Regards,
Bank Management System
"""

        email_result = send_email(
            recipient_email=customer.email,
            subject=subject,
            body=body.strip(),
        )

        # ----------------------------------------------------
        # Remove OTP if email failed
        # ----------------------------------------------------

        if not email_result["success"]:

            db.delete(otp_record)
            db.commit()

            return {
                "success": False,
                "message": email_result["message"],
            }

        return {
            "success": True,
            "message": (
                "Password reset OTP sent successfully "
                f"to {mask_email(customer.email)}."
            ),
            "otp_id": otp_record.id,
            "expires_at": expires_at,
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Unable to send password reset OTP: {str(e)}"
            ),
        }

    finally:

        db.close()

def verify_password_reset_otp(
    otp_id: int,
    customer_id: int,
    entered_otp: str,
):
    """
    Verify OTP for password reset.

    Security checks:
    - OTP must belong to the current customer
    - OTP must not already be used
    - OTP must not be expired
    - Maximum 5 attempts
    - OTP must be exactly 6 digits
    """

    db = SessionLocal()

    try:
        # --------------------------------------------------------
        # FIND OTP
        # --------------------------------------------------------

        otp_record = (
            db.query(PasswordResetOTP)
            .filter(
                PasswordResetOTP.id == otp_id,
                PasswordResetOTP.customer_id == customer_id,
            )
            .first()
        )

        if not otp_record:
            return {
                "success": False,
                "message": "Invalid password reset OTP request.",
            }

        # --------------------------------------------------------
        # ALREADY VERIFIED
        # --------------------------------------------------------

        if otp_record.is_verified:
            return {
                "success": False,
                "message": "This OTP has already been used.",
            }

        # --------------------------------------------------------
        # MAX ATTEMPTS
        # --------------------------------------------------------

        if otp_record.attempts >= otp_record.max_attempts:
            return {
                "success": False,
                "message": (
                    "Maximum OTP verification attempts exceeded. "
                    "Please request a new OTP."
                ),
            }

        # --------------------------------------------------------
        # EXPIRY CHECK
        # --------------------------------------------------------

        now = datetime.utcnow()

        if now > otp_record.expires_at:

            otp_record.is_verified = True

            db.commit()

            return {
                "success": False,
                "message": (
                    "This OTP has expired. "
                    "Please request a new OTP."
                ),
            }

        # --------------------------------------------------------
        # OTP FORMAT
        # --------------------------------------------------------

        entered_otp = str(entered_otp).strip()

        if (
            len(entered_otp) != OTP_LENGTH
            or not entered_otp.isdigit()
        ):

            otp_record.attempts += 1

            db.commit()

            remaining = (
                otp_record.max_attempts
                - otp_record.attempts
            )

            return {
                "success": False,
                "message": (
                    f"Invalid OTP format. "
                    f"{remaining} attempt(s) remaining."
                ),
            }

        # --------------------------------------------------------
        # VERIFY HASH
        # --------------------------------------------------------

        if not verify_otp_hash(
            entered_otp,
            otp_record.otp_hash,
        ):

            otp_record.attempts += 1

            db.commit()

            remaining = (
                otp_record.max_attempts
                - otp_record.attempts
            )

            if remaining <= 0:
                return {
                    "success": False,
                    "message": (
                        "Maximum OTP verification attempts "
                        "exceeded. Please request a new OTP."
                    ),
                }

            return {
                "success": False,
                "message": (
                    "Incorrect OTP. "
                    f"{remaining} attempt(s) remaining."
                ),
            }

        # --------------------------------------------------------
        # OTP SUCCESSFULLY VERIFIED
        # --------------------------------------------------------

        otp_record.is_verified = True
        otp_record.verified_at = now

        db.commit()

        return {
            "success": True,
            "message": "OTP verified successfully.",
            "customer_id": otp_record.customer_id,
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Unable to verify OTP: {str(e)}"
            ),
        }

    finally:

        db.close()