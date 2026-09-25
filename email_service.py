import smtplib
from email.message import EmailMessage
from decimal import Decimal

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_FROM_EMAIL,
    SMTP_USE_TLS,
)


# ============================================================
# BASIC EMAIL SENDER
# ============================================================

def send_email(recipient_email: str, subject: str, body: str) -> dict:
    """
    Send a plain-text email using configured SMTP settings.
    """
    if not SMTP_USERNAME:
        return {
            "success": False,
            "message": "SMTP_USERNAME is not configured.",
        }
    if not SMTP_PASSWORD:
        return {
            "success": False,
            "message": "SMTP_PASSWORD is not configured.",
        }
    if not recipient_email:
        return {
            "success": False,
            "message": "Recipient email address is missing.",
        }
    try:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = SMTP_FROM_EMAIL or SMTP_USERNAME
        message["To"] = recipient_email
        message.set_content(body)
        with smtplib.SMTP(
            SMTP_HOST,
            int(SMTP_PORT),
            timeout=20,
        ) as server:
            server.ehlo()
            if SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD,
            )
            server.send_message(message)
        return {
            "success": True,
            "message": "Email sent successfully.",
        }
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": (
                "SMTP authentication failed. "
                "Check SMTP username and Gmail App Password."
            ),
        }
    except smtplib.SMTPException as e:
        return {
            "success": False,
            "message": f"SMTP error: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Email sending failed: {str(e)}",
        }


# ============================================================
# TRANSACTION SUCCESS EMAIL
# ============================================================

def send_transaction_success_email(
    recipient_email: str,
    transaction_type: str,
    amount,
    transaction_ref: str,
    balance_after,
    transaction_datetime: str,
    description: str = ""
):
    """
    Send transaction-success notification email.
    """

    amount = Decimal(str(amount))
    balance_after = Decimal(str(balance_after))

    subject = f"Transaction Successful - {transaction_ref}"

    body = f"""
Transaction Successful

Dear Customer,

Your banking transaction has been completed successfully.

Transaction Details
------------------------------
Transaction Type: {transaction_type}
Amount: ₹{amount:,.2f}
Transaction ID: {transaction_ref}
Balance After Transaction: ₹{balance_after:,.2f}
Date & Time: {transaction_datetime}
"""

    if description:
        body += f"Description: {description}\n"

    body += """
------------------------------

The transaction has been successfully processed.

If you did not authorize this transaction, please contact your bank immediately.

Thank you for banking with us.

Bank Management System
"""

    return send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body.strip(),
    )


# ============================================================
# INCORRECT OTP EMAIL
# ============================================================

def send_invalid_otp_email(
    recipient_email: str,
    transaction_type: str,
    amount,
    transaction_datetime: str
):
    """
    Send notification when an incorrect OTP is entered.
    """

    amount = Decimal(str(amount))

    subject = "Transaction Verification Failed - Incorrect OTP"

    body = f"""
Transaction Verification Failed

Dear Customer,

An incorrect OTP was entered while verifying a banking transaction.

Transaction Details
------------------------------
Transaction Type: {transaction_type}
Amount: ₹{amount:,.2f}
Date & Time: {transaction_datetime}

The transaction was NOT completed because the OTP verification failed.

For your security, no amount has been deducted or transferred.

If you did not initiate this transaction, please contact your bank immediately.

Bank Management System
"""

    return send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body.strip(),
    )


# ============================================================
# EXPIRED OTP EMAIL
# ============================================================

def send_expired_otp_email(
    recipient_email: str,
    transaction_type: str,
    amount,
    transaction_datetime: str
):
    """
    Send notification when OTP has expired.
    """

    amount = Decimal(str(amount))

    subject = "Transaction Verification Failed - OTP Expired"

    body = f"""
Transaction Verification Failed

Dear Customer,

The OTP generated for your banking transaction has expired.

Transaction Details
------------------------------
Transaction Type: {transaction_type}
Amount: ₹{amount:,.2f}
Date & Time: {transaction_datetime}

The transaction was NOT completed.

Please request a new OTP if you still want to proceed with the transaction.

If you did not initiate this transaction, please contact your bank immediately.

Bank Management System
"""

    return send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body.strip(),
    )


# ============================================================
# MAXIMUM OTP ATTEMPTS EMAIL
# ============================================================

def send_max_attempts_email(
    recipient_email: str,
    transaction_type: str,
    amount,
    transaction_datetime: str
):
    """
    Send notification when maximum OTP attempts are exceeded.
    """

    amount = Decimal(str(amount))

    subject = "Transaction Blocked - Maximum OTP Attempts"

    body = f"""
Transaction Blocked

Dear Customer,

Multiple incorrect OTP attempts were detected for a banking transaction.

Transaction Details
------------------------------
Transaction Type: {transaction_type}
Amount: ₹{amount:,.2f}
Date & Time: {transaction_datetime}

For security reasons, this transaction has been blocked.

No amount has been deducted or transferred.

If you did not initiate this transaction, please contact your bank immediately.

Bank Management System
"""

    return send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body.strip(),
    )


# ============================================================
# TRANSACTION FAILED EMAIL
# ============================================================

def send_transaction_failed_email(
    recipient_email: str,
    transaction_type: str,
    amount,
    reason: str,
    transaction_datetime: str
):
    """
    Send transaction-failure notification email.
    """

    amount = Decimal(str(amount))

    subject = f"Transaction Failed - {transaction_type}"

    body = f"""
Transaction Failed

Dear Customer,

Your banking transaction could not be completed.

Transaction Details
------------------------------
Transaction Type: {transaction_type}
Amount: ₹{amount:,.2f}
Date & Time: {transaction_datetime}
Reason: {reason}

No amount has been deducted or transferred.

If you need assistance, please contact your bank.

Bank Management System
"""

    return send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body.strip(),
    )


def send_transfer_success_email(
    recipient_email: str,
    transfer_direction: str,
    amount,
    transaction_ref: str,
    transaction_datetime: str,
    balance_after,
    sender_name: str,
    sender_account_number: str,
    sender_email: str,
    receiver_name: str,
    receiver_account_number: str,
    receiver_email: str,
    description: str = "",
):
    amount = Decimal(str(amount))
    balance_after = Decimal(str(balance_after))

    if transfer_direction == "TRANSFER OUT":
        subject = f"Transfer Successful - {transaction_ref}"

        heading = "Money Transfer Successful"

        balance_label = "Balance After Transfer"

        intro = (
            "Your account transfer has been completed successfully."
        )

    else:
        subject = f"Money Received - {transaction_ref}"

        heading = "Money Received Successfully"

        balance_label = "Balance After Receiving Money"

        intro = (
            "Money has been successfully received in your account."
        )

    body = f"""
        {heading}

        Dear Customer,

        {intro}

        ==================================================
        TRANSFER DETAILS
        ==================================================

        From Account
        --------------------------------------------------
        Customer Name: {sender_name}
        Account Number: {sender_account_number}
        Email: {sender_email}

        To Account
        --------------------------------------------------
        Customer Name: {receiver_name}
        Account Number: {receiver_account_number}
        Email: {receiver_email}

        ==================================================
        TRANSACTION DETAILS
        ==================================================

        Transaction Type: {transfer_direction}
        Amount: ₹{amount:,.2f}
        Transaction ID: {transaction_ref}
        Date & Time: {transaction_datetime}
        {balance_label}: ₹{balance_after:,.2f}
        """

    if description:
        body += f"Description: {description}\n"

    body += """
        ==================================================

        This transaction has been successfully processed.

        If you did not authorize this transaction, please contact your bank immediately.

        Thank you for banking with us.

        Bank Management System
    """

    return send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body.strip(),
    )