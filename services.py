import re
import secrets
from decimal import (
    Decimal,
    InvalidOperation,
)
from sqlalchemy import or_
from auth import require_admin
from database import SessionLocal
from models import (
    User,
    Customer,
    Account,
    Transaction,
)
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from email_service import (
    send_transaction_success_email,
    send_transaction_failed_email,
    send_transfer_success_email,
)


# ============================================================
# ADMIN AUTHORIZATION
# ============================================================

def ensure_admin_access():
    """
    Ensure that the currently authenticated user
    has administrator privileges.
    """
    if not require_admin():
        raise PermissionError("Administrator access is required for this operation.")
    return True

# ============================================================
# CUSTOMER CODE GENERATOR
# ============================================================

def generate_customer_code() -> str:
    """
    Generate a unique customer code.

    Example:
        CUSTA8F39D21
    """
    random_part = secrets.token_hex(5).upper()
    return f"CUST{random_part}"

# ============================================================
# EMAIL VALIDATION
# ============================================================

def is_valid_email(email: str) -> bool:
    """
    Basic email validation.
    """
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern,email,) is not None


# ============================================================
# PHONE VALIDATION
# ============================================================

def is_valid_phone(phone: str) -> bool:
    """
    Validate Indian-style 10 digit mobile number.

    Accepted example:
        9876543210
    """

    return (
        phone.isdigit()
        and len(phone) == 10
        and phone[0] in "6789"
    )

# ============================================================
# CREATE CUSTOMER
# ============================================================

def create_customer(
    full_name: str,
    email: str,
    phone: str,
    address: str = "",
):
    ensure_admin_access()
    """
    Create a new customer.

    Returns:
        {
            "success": True,
            "customer": Customer object,
        }
    or
        {
            "success": False,
            "message": "Error message",
        }
    """

    full_name = full_name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    address = address.strip()

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if not full_name:
        return {"success": False,"message": "Full name is required.",}
    if len(full_name) < 3:
        return {"success": False,"message": "Full name must contain at least 3 characters.",}
    if not is_valid_email(email):
        return {"success": False,"message": "Please enter a valid email address.",}
    if not is_valid_phone(phone):
        return {
            "success": False,
            "message": (
                "Phone number must be a valid "
                "10-digit Indian mobile number."
            ),
        }
    if address and len(address) > 500:
        return {"success": False,"message": "Address is too long.",}
    db = SessionLocal()
    try:

        # ----------------------------------------------------
        # Check duplicate email
        # ----------------------------------------------------

        existing_email = (
            db.query(Customer)
            .filter(Customer.email == email)
            .first()
        )
        if existing_email:
            return {
                "success": False,
                "message": (
                    "A customer with this email "
                    "already exists."
                ),
            }

        # ----------------------------------------------------
        # Generate unique customer code
        # ----------------------------------------------------

        customer_code = generate_customer_code()
        while (
            db.query(Customer)
            .filter(Customer.customer_code == customer_code)
            .first()
        ):

            customer_code = generate_customer_code()

        # ----------------------------------------------------
        # Create customer
        # ----------------------------------------------------

        customer = Customer(
            customer_code=customer_code,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address or None,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return {"success": True,"customer": customer,}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ============================================================
# UPDATE CUSTOMER
# ============================================================

def update_customer(
    customer_id: int,
    full_name: str,
    email: str,
    phone: str,
    address: str = ""
):
    ensure_admin_access()
    """
    Update an existing customer's details.

    Customer code is not changed.
    """

    full_name = full_name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    address = address.strip()

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if not full_name:
        return {
            "success": False,
            "message": "Full name is required.",
        }

    if len(full_name) < 3:
        return {
            "success": False,
            "message": (
                "Full name must contain at least 3 characters."
            ),
        }

    if not is_valid_email(email):
        return {
            "success": False,
            "message": "Please enter a valid email address.",
        }

    if not is_valid_phone(phone):
        return {
            "success": False,
            "message": (
                "Phone number must be a valid "
                "10-digit Indian mobile number."
            ),
        }

    if address and len(address) > 500:
        return {
            "success": False,
            "message": "Address is too long.",
        }

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Find customer
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

        # ----------------------------------------------------
        # Check duplicate email
        #
        # Same customer's existing email is allowed.
        # Another customer's email is not allowed.
        # ----------------------------------------------------

        existing_email = (
            db.query(Customer)
            .filter(
                Customer.email == email,
                Customer.id != customer_id,
            )
            .first()
        )

        if existing_email:
            return {
                "success": False,
                "message": (
                    "Another customer with this "
                    "email already exists."
                ),
            }

        # ----------------------------------------------------
        # Update details
        # ----------------------------------------------------

        customer.full_name = full_name
        customer.email = email
        customer.phone = phone
        customer.address = address or None

        db.commit()
        db.refresh(customer)

        return {
            "success": True,
            "message": "Customer details updated successfully.",
            "customer": customer,
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Unable to update customer: {str(e)}"
            ),
        }

    finally:
        db.close()

# ============================================================
# GET ALL CUSTOMERS
# ============================================================

def get_all_customers():
    ensure_admin_access()
    db = SessionLocal()
    try:
        customers = (
            db.query(Customer)
            .order_by(Customer.created_at.desc())
            .all()
        )
        return customers
    finally:
        db.close()

# ============================================================
# SEARCH CUSTOMERS
# ============================================================

def search_customers(search_term: str):
    ensure_admin_access()
    search_term = search_term.strip()
    if not search_term:
        return get_all_customers()
    db = SessionLocal()
    try:
        search_pattern = (f"%{search_term}%")
        customers = (
            db.query(Customer)
            .filter(
                or_(
                    Customer.customer_code.ilike(search_pattern),
                    Customer.full_name.ilike(search_pattern),
                    Customer.email.ilike(search_pattern),
                    Customer.phone.ilike(search_pattern),
                )
            )
            .order_by(
                Customer.created_at.desc())
            .all()
            )
        return customers

    finally:
        db.close()

# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

from decimal import Decimal, InvalidOperation
from models import Account

# ============================================================
# ACCOUNT NUMBER GENERATOR
# ============================================================

def generate_account_number() -> str:
    """
    Generate a 12-digit unique bank account number.
    Example:
        100123456789
    """
    import secrets
    number = secrets.randbelow(900000000000) + 100000000000
    return str(number)

# ============================================================
# ACCOUNT NUMBER UNIQUE CHECK
# ============================================================

def get_unique_account_number(db):
    account_number = generate_account_number()
    while (
        db.query(Account)
        .filter(Account.account_number == account_number)
        .first()
    ):
        account_number = generate_account_number()
    return account_number


# ============================================================
# CREATE ACCOUNT
# ============================================================

def create_account(customer_id: int,account_type: str,opening_balance,):
    """
    Create a new bank account for a customer.
    """

    # --------------------------------------------------------
    # Validate account type
    # --------------------------------------------------------

    allowed_account_types = {
        "Savings",
        "Current",
        "Salary",
    }
    if account_type not in allowed_account_types:
        return {
            "success": False,
            "message": "Invalid account type.",
        }

    # --------------------------------------------------------
    # Convert opening balance
    # --------------------------------------------------------

    try:
        balance = Decimal(str(opening_balance))
    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return {
            "success": False,
            "message": "Invalid opening balance.",
        }

    # --------------------------------------------------------
    # Validate balance
    # --------------------------------------------------------

    if balance < Decimal("0.00"):
        return {
            "success": False,
            "message": ("Opening balance cannot be negative."),
        }
    # Maximum supported amount
    if balance > Decimal("9999999999999.99"):
        return {
            "success": False,
            "message": ("Opening balance is too large."),
        }
    db = SessionLocal()
    try:

        # ----------------------------------------------------
        # Verify customer exists
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

        # ----------------------------------------------------
        # Generate unique account number
        # ----------------------------------------------------

        account_number = (get_unique_account_number(db))

        # ----------------------------------------------------
        # Create account
        # ----------------------------------------------------

        account = Account(
            account_number=account_number,
            account_type=account_type,
            balance=balance,
            status="Active",
            customer_id=customer_id,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return {
            "success": True,
            "account": account,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ============================================================
# GET ALL ACCOUNTS
# ============================================================

def get_all_accounts():
    ensure_admin_access()
    db = SessionLocal()
    try:
        accounts = (
            db.query(Account)
            .options(joinedload(Account.customer))
            .order_by(Account.created_at.desc())
            .all()
        )
        return accounts
    finally:
        db.close()

# ============================================================
# GET ACCOUNTS BY CUSTOMER
# ============================================================

def get_customer_accounts(customer_id: int,):
    db = SessionLocal()
    try:
        accounts = (
            db.query(Account)
            .filter(Account.customer_id == customer_id)
            .order_by(Account.created_at.desc())
            .all()
        )
        return accounts
    finally:
        db.close()

# ============================================================
# SEARCH ACCOUNTS
# ============================================================

def search_accounts(search_term: str,):
    ensure_admin_access()
    search_term = search_term.strip()
    db = SessionLocal()
    try:
        query = (
            db.query(Account)
            .options(joinedload(Account.customer))
            .join(Customer)
        )
        if search_term:
            search_pattern = (f"%{search_term}%")
            query = query.filter(
                or_(
                    Account.account_number.ilike(search_pattern),
                    Customer.customer_code.ilike(search_pattern),
                    Customer.full_name.ilike(search_pattern),
                )
            )
        return (
            query
            .order_by(Account.created_at.desc())
            .all()
        )
    finally:
        db.close()
        
# ============================================================
# ACCOUNT STATUS UPDATE
# ============================================================

def update_account_status(account_id: int,new_status: str,):
    allowed_statuses = {
        "Active",
        "Inactive",
        "Blocked",
    }
    if new_status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid account status.",
        }
    db = SessionLocal()
    try:
        account = (
            db.query(Account)
            .filter(Account.id == account_id)
            .first()
        )
        if not account:
            return {
                "success": False,
                "message": "Account not found.",
            }
        account.status = new_status
        db.commit()
        return {
            "success": True,
            "message": (f"Account status changed to " f"{new_status}."),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ============================================================
# TRANSACTION ID GENERATOR
# ============================================================

def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID.

    Example:
        TXN8F29A73C1D
    """
    random_part = secrets.token_hex(6).upper()
    return f"TXN{random_part}"

# ============================================================
# UNIQUE TRANSACTION ID
# ============================================================

def get_unique_transaction_ref(db):
    transaction_ref = generate_transaction_id()
    while (
        db.query(Transaction)
        .filter(Transaction.transaction_ref == transaction_ref)
        .first()
    ):
        transaction_ref = generate_transaction_id()
    return transaction_ref

# ============================================================
# AMOUNT VALIDATION
# ============================================================

def validate_transaction_amount(amount):
    try:
        amount = Decimal(str(amount))
    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return (False,None,"Invalid transaction amount.")
    if amount <= Decimal("0.00"):
        return (False,None,"Transaction amount must be greater than ₹0.")
    if amount > Decimal("9999999999999.99"):
        return (False,None,"Transaction amount is too large.")
    return (True,amount,None)

# ============================================================
# DEPOSIT
# ============================================================

def deposit_money(
    account_id: int,
    amount,
    description: str = "",
    customer_id: int = None,
):
    valid, amount, error = validate_transaction_amount(amount)

    if not valid:
        return {
            "success": False,
            "message": error,
        }

    # ========================================================
    # CUSTOMER OWNERSHIP CHECK
    # ========================================================

    if customer_id is not None:
        ownership = verify_customer_account_ownership(
            customer_id=customer_id,
            account_id=account_id,
        )
        if not ownership["success"]:
            return {
                "success": False,
                "message": ownership["message"],
            }

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Lock account row
        # ----------------------------------------------------

        account = (
            db.query(Account)
            .filter(Account.id == account_id)
            .with_for_update()
            .first()
        )

        if not account:
            return {
                "success": False,
                "message": "Account not found.",
            }

        # ----------------------------------------------------
        # Account status check
        # ----------------------------------------------------

        if account.status != "Active":
            return {
                "success": False,
                "message": (
                    f"Account is {account.status.lower()}. "
                    "Transaction cannot be completed."
                ),
            }

        # ----------------------------------------------------
        # Calculate new balance
        # ----------------------------------------------------

        old_balance = Decimal(str(account.balance))
        new_balance = old_balance + amount

        # ----------------------------------------------------
        # Update account balance
        # ----------------------------------------------------

        account.balance = new_balance

        # ----------------------------------------------------
        # Create transaction
        # ----------------------------------------------------

        transaction = Transaction(
            transaction_ref=get_unique_transaction_ref(db),
            account_id=account.id,
            transaction_type="DEPOSIT",
            amount=amount,
            balance_after=new_balance,
            description=(
                description.strip()
                if description
                else "Cash deposit"
            ),
        )

        db.add(transaction)

        # ----------------------------------------------------
        # Commit transaction
        # ----------------------------------------------------

        db.commit()
        db.refresh(transaction)

        # ----------------------------------------------------
        # Get customer email
        # ----------------------------------------------------

        customer = (
            db.query(Customer)
            .filter(Customer.id == account.customer_id)
            .first()
        )

        # ----------------------------------------------------
        # Prepare Indian date & time
        # ----------------------------------------------------

        transaction_datetime = (
            transaction.created_at + timedelta(hours=5, minutes=30)
        ).strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )

        # ----------------------------------------------------
        # Send success email
        # ----------------------------------------------------

        email_result = None

        if customer and customer.email:

            email_result = send_transaction_success_email(
                recipient_email=customer.email,
                transaction_type="DEPOSIT",
                amount=amount,
                transaction_ref=transaction.transaction_ref,
                balance_after=new_balance,
                transaction_datetime=transaction_datetime,
                description=(
                    description.strip()
                    if description
                    else "Cash deposit"
                ),
            )

        # ----------------------------------------------------
        # Return success response
        # ----------------------------------------------------

        return {
            "success": True,
            "message": "Deposit successful.",
            "transaction_id": transaction.transaction_ref,
            "new_balance": new_balance,
            "email_sent": (
                email_result["success"]
                if email_result
                else False
            ),
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# WITHDRAWAL
# ============================================================

def withdraw_money(
    account_id: int,
    amount,
    description: str = "",
    customer_id: int = None,
):
    valid, amount, error = validate_transaction_amount(amount)

    if not valid:
        return {
            "success": False,
            "message": error,
        }

    # ========================================================
    # CUSTOMER OWNERSHIP CHECK
    # ========================================================

    if customer_id is not None:
        ownership = verify_customer_account_ownership(
            customer_id=customer_id,
            account_id=account_id,
        )
        if not ownership["success"]:
            return {
                "success": False,
                "message": ownership["message"],
            }

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Lock account
        # ----------------------------------------------------

        account = (
            db.query(Account)
            .filter(Account.id == account_id)
            .with_for_update()
            .first()
        )

        if not account:
            return {
                "success": False,
                "message": "Account not found.",
            }

        # ----------------------------------------------------
        # Get customer
        # ----------------------------------------------------

        customer = (
            db.query(Customer)
            .filter(Customer.id == account.customer_id)
            .first()
        )

        # ----------------------------------------------------
        # Status check
        # ----------------------------------------------------

        if account.status != "Active":
            failure_message = (
                f"Account is {account.status.lower()}. "
                "Transaction cannot be completed."
            )

            return {
                "success": False,
                "message": failure_message,
            }

        # ----------------------------------------------------
        # Current balance
        # ----------------------------------------------------

        current_balance = Decimal(str(account.balance))

        # ----------------------------------------------------
        # Sufficient balance check
        # ----------------------------------------------------

        if amount > current_balance:
            failure_message = "Insufficient account balance."
            email_result = None

            # --------------------------------------------------------
            # Send failed transaction email
            # --------------------------------------------------------

            if customer and customer.email:
                transaction_datetime = (
                    datetime.utcnow() + timedelta(hours=5, minutes=30)
                ).strftime(
                    "%d-%m-%Y %I:%M:%S %p"
                )

                email_result = send_transaction_failed_email(
                    recipient_email=customer.email,
                    transaction_type="WITHDRAWAL",
                    amount=amount,
                    transaction_datetime=transaction_datetime,
                    reason=failure_message,
                )

            return {
                "success": False,
                "message": failure_message,
                "email_sent": (
                    email_result["success"]
                    if email_result
                    else False
                ),
            }
        
        # ----------------------------------------------------
        # Calculate new balance
        # ----------------------------------------------------

        new_balance = current_balance - amount

        # ----------------------------------------------------
        # Update balance
        # ----------------------------------------------------

        account.balance = new_balance

        # ----------------------------------------------------
        # Create transaction
        # ----------------------------------------------------

        transaction = Transaction(
            transaction_ref=get_unique_transaction_ref(db),
            account_id=account.id,
            transaction_type="WITHDRAWAL",
            amount=amount,
            balance_after=new_balance,
            description=(
                description.strip()
                if description
                else "Cash withdrawal"
            ),
        )

        db.add(transaction)

        # ----------------------------------------------------
        # Commit transaction
        # ----------------------------------------------------

        db.commit()
        db.refresh(transaction)

        # ----------------------------------------------------
        # Prepare Indian date & time
        # ----------------------------------------------------

        transaction_datetime = (
            transaction.created_at + timedelta(hours=5, minutes=30)
        ).strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )

        # ----------------------------------------------------
        # Send success email
        # ----------------------------------------------------

        email_result = None

        if customer and customer.email:
            email_result = send_transaction_success_email(
                recipient_email=customer.email,
                transaction_type="WITHDRAWAL",
                amount=amount,
                transaction_ref=transaction.transaction_ref,
                balance_after=new_balance,
                transaction_datetime=transaction_datetime,
                description=(
                    description.strip()
                    if description
                    else "Cash withdrawal"
                ),
            )

        # ----------------------------------------------------
        # Return success response
        # ----------------------------------------------------

        return {
            "success": True,
            "message": "Withdrawal successful.",
            "transaction_id": transaction.transaction_ref,
            "new_balance": new_balance,
            "email_sent": (
                email_result["success"]
                if email_result
                else False
            ),
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

# ============================================================
# TRANSFER MONEY
# ============================================================

def transfer_money(
    source_account_id: int,
    destination_account_id: int,
    amount,
    description: str = "",
    customer_id: int = None,
):

    # --------------------------------------------------------
    # Amount validation
    # --------------------------------------------------------

    valid, amount, error = validate_transaction_amount(amount)

    if not valid:
        return {
            "success": False,
            "message": error,
        }

    # --------------------------------------------------------
    # Same account check
    # --------------------------------------------------------

    if source_account_id == destination_account_id:
        return {
            "success": False,
            "message": (
                "Source and destination accounts "
                "cannot be the same."
            ),
        }

    # ========================================================
    # SOURCE ACCOUNT OWNERSHIP CHECK
    # ========================================================

    if customer_id is not None:
        ownership = verify_customer_account_ownership(
            customer_id=customer_id,
            account_id=source_account_id,
        )
        if not ownership["success"]:
            return {
                "success": False,
                "message": ownership["message"],
            }

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Lock accounts in predictable order
        # ----------------------------------------------------

        first_id = min(
            source_account_id,
            destination_account_id,
        )

        second_id = max(
            source_account_id,
            destination_account_id,
        )

        first_account = (
            db.query(Account)
            .filter(Account.id == first_id)
            .with_for_update()
            .first()
        )

        second_account = (
            db.query(Account)
            .filter(Account.id == second_id)
            .with_for_update()
            .first()
        )

        if not first_account or not second_account:
            return {
                "success": False,
                "message": (
                    "One or both accounts "
                    "were not found."
                ),
            }

        # ----------------------------------------------------
        # Re-identify source and destination
        # ----------------------------------------------------

        if first_account.id == source_account_id:
            source_account = first_account
            destination_account = second_account
        else:
            source_account = second_account
            destination_account = first_account

        # ----------------------------------------------------
        # Get source customer
        # ----------------------------------------------------

        source_customer = (
            db.query(Customer)
            .filter(
                Customer.id == source_account.customer_id
            )
            .first()
        )

        # ----------------------------------------------------
        # Get destination customer
        # ----------------------------------------------------

        destination_customer = (
            db.query(Customer)
            .filter(
                Customer.id == destination_account.customer_id
            )
            .first()
        )

        if not source_customer:
            return {
                "success": False,
                "message": (
                    "Source account customer "
                    "was not found."
                ),
            }

        if not destination_customer:
            return {
                "success": False,
                "message": (
                    "Destination account customer "
                    "was not found."
                ),
            }

        # ----------------------------------------------------
        # Source account status
        # ----------------------------------------------------

        if source_account.status != "Active":
            return {
                "success": False,
                "message": (
                    "Source account is not active."
                ),
            }

        # ----------------------------------------------------
        # Destination account status
        # ----------------------------------------------------

        if destination_account.status != "Active":
            return {
                "success": False,
                "message": (
                    "Destination account is not active."
                ),
            }

        # ----------------------------------------------------
        # Current balances
        # ----------------------------------------------------

        source_balance = Decimal(
            str(source_account.balance)
        )

        destination_balance = Decimal(
            str(destination_account.balance)
        )

        # ----------------------------------------------------
        # Sufficient balance
        # ----------------------------------------------------

        if amount > source_balance:

            failure_message = (
                "Insufficient balance in source account."
            )

            email_result = None

            if source_customer.email:

                transaction_datetime = (
                    datetime.utcnow()
                    + timedelta(hours=5, minutes=30)
                ).strftime(
                    "%d-%m-%Y %I:%M:%S %p"
                )

                email_result = (
                    send_transaction_failed_email(
                        recipient_email=(
                            source_customer.email
                        ),
                        transaction_type="TRANSFER",
                        amount=amount,
                        transaction_datetime=(
                            transaction_datetime
                        ),
                        reason=failure_message,
                    )
                )

            return {
                "success": False,
                "message": failure_message,
                "email_sent": (
                    email_result["success"]
                    if email_result
                    else False
                ),
            }

        # ----------------------------------------------------
        # Calculate new balances
        # ----------------------------------------------------

        source_new_balance = (
            source_balance - amount
        )

        destination_new_balance = (
            destination_balance + amount
        )

        # ----------------------------------------------------
        # Update balances
        # ----------------------------------------------------

        source_account.balance = (
            source_new_balance
        )

        destination_account.balance = (
            destination_new_balance
        )

        # ----------------------------------------------------
        # Generate transaction references
        # ----------------------------------------------------

        transfer_out_id = (
            get_unique_transaction_ref(db)
        )

        transfer_in_id = (
            get_unique_transaction_ref(db)
        )

        # Make sure both transaction references
        # are different.

        while transfer_in_id == transfer_out_id:
            transfer_in_id = (
                get_unique_transaction_ref(db)
            )

        # ----------------------------------------------------
        # Transfer description
        # ----------------------------------------------------

        transfer_description = (
            description.strip()
            if description
            else "Account transfer"
        )

        # ----------------------------------------------------
        # Source transaction
        # ----------------------------------------------------

        transfer_out = Transaction(
            transaction_ref=transfer_out_id,
            account_id=source_account.id,
            transaction_type="TRANSFER_OUT",
            amount=amount,
            balance_after=source_new_balance,
            reference_account_id=(
                destination_account.id
            ),
            description=transfer_description,
        )

        # ----------------------------------------------------
        # Destination transaction
        # ----------------------------------------------------

        transfer_in = Transaction(
            transaction_ref=transfer_in_id,
            account_id=destination_account.id,
            transaction_type="TRANSFER_IN",
            amount=amount,
            balance_after=destination_new_balance,
            reference_account_id=(
                source_account.id
            ),
            description=transfer_description,
        )

        # ----------------------------------------------------
        # Add transactions
        # ----------------------------------------------------

        db.add(transfer_out)
        db.add(transfer_in)

        # ----------------------------------------------------
        # Atomic commit
        # ----------------------------------------------------

        db.commit()

        # ----------------------------------------------------
        # Refresh transactions
        # ----------------------------------------------------

        db.refresh(transfer_out)
        db.refresh(transfer_in)

        # ----------------------------------------------------
        # Indian date & time
        # ----------------------------------------------------

        transaction_datetime = (
            transfer_out.created_at
            + timedelta(hours=5, minutes=30)
        ).strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )

        # ====================================================
        # SOURCE CUSTOMER EMAIL
        # ====================================================

        source_email_result = None

        if source_customer.email:

            source_email_result = (
                send_transfer_success_email(
                    recipient_email=(
                        source_customer.email
                    ),

                    transfer_direction=(
                        "TRANSFER OUT"
                    ),

                    amount=amount,

                    transaction_ref=(
                        transfer_out.transaction_ref
                    ),

                    transaction_datetime=(
                        transaction_datetime
                    ),

                    balance_after=(
                        source_new_balance
                    ),

                    # ----------------------------------------
                    # SENDER DETAILS
                    # ----------------------------------------

                    sender_name=(
                        source_customer.full_name
                    ),

                    sender_account_number=(
                        source_account.account_number
                    ),

                    sender_email=(
                        source_customer.email
                    ),

                    # ----------------------------------------
                    # RECEIVER DETAILS
                    # ----------------------------------------

                    receiver_name=(
                        destination_customer.full_name
                    ),

                    receiver_account_number=(
                        destination_account.account_number
                    ),

                    receiver_email=(
                        destination_customer.email
                    ),

                    description=(
                        transfer_description
                    ),
                )
            )

        # ====================================================
        # DESTINATION CUSTOMER EMAIL
        # ====================================================

        destination_email_result = None

        if destination_customer.email:

            destination_email_result = (
                send_transfer_success_email(
                    recipient_email=(
                        destination_customer.email
                    ),

                    transfer_direction=(
                        "TRANSFER IN"
                    ),

                    amount=amount,

                    transaction_ref=(
                        transfer_in.transaction_ref
                    ),

                    transaction_datetime=(
                        transaction_datetime
                    ),

                    balance_after=(
                        destination_new_balance
                    ),

                    # ----------------------------------------
                    # SENDER DETAILS
                    # ----------------------------------------

                    sender_name=(
                        source_customer.full_name
                    ),

                    sender_account_number=(
                        source_account.account_number
                    ),

                    sender_email=(
                        source_customer.email
                    ),

                    # ----------------------------------------
                    # RECEIVER DETAILS
                    # ----------------------------------------

                    receiver_name=(
                        destination_customer.full_name
                    ),

                    receiver_account_number=(
                        destination_account.account_number
                    ),

                    receiver_email=(
                        destination_customer.email
                    ),

                    description=(
                        transfer_description
                    ),
                )
            )

        # ====================================================
        # RETURN SUCCESS
        # ====================================================

        return {
            "success": True,
            "message": (
                "Transfer completed successfully."
            ),

            "transfer_out_id": (
                transfer_out.transaction_ref
            ),

            "transfer_in_id": (
                transfer_in.transaction_ref
            ),

            "source_balance": (
                source_new_balance
            ),

            "destination_balance": (
                destination_new_balance
            ),

            "source_email_sent": (
                source_email_result["success"]
                if source_email_result
                else False
            ),

            "destination_email_sent": (
                destination_email_result["success"]
                if destination_email_result
                else False
            ),
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

# ============================================================
# TRANSACTION HISTORY
# ============================================================

def get_account_transactions(
    account_id: int,
):
    ensure_admin_access()
    db = SessionLocal()

    try:

        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.account_id
                == account_id
            )
            .order_by(
                Transaction.created_at.desc()
            )
            .all()
        )

        return transactions

    finally:

        db.close()

# ============================================================
# GET ACTIVE ACCOUNTS
# ============================================================

def get_active_accounts():

    db = SessionLocal()

    try:

        accounts = (
            db.query(Account)
            .options(
                joinedload(Account.customer)
            )
            .filter(
                Account.status == "Active"
            )
            .order_by(
                Account.account_number
            )
            .all()
        )

        return accounts

    finally:

        db.close()

# ============================================================
# DASHBOARD SERVICES
# ============================================================

def get_dashboard_statistics():
    ensure_admin_access()
    """
    Returns overall banking statistics for the dashboard.
    """

    db = SessionLocal()

    try:
        customers_count = db.query(Customer).count()

        accounts = db.query(Account).all()

        total_accounts = len(accounts)

        active_accounts = sum(
            1 for account in accounts
            if account.status == "Active"
        )

        inactive_accounts = sum(
            1 for account in accounts
            if account.status == "Inactive"
        )

        blocked_accounts = sum(
            1 for account in accounts
            if account.status == "Blocked"
        )

        total_balance = sum(
            (
                Decimal(str(account.balance))
                for account in accounts
            ),
            Decimal("0.00")
        )

        transactions_count = db.query(Transaction).count()

        deposits = sum(
            (
                Decimal(str(row[0]))
                for row in (
                    db.query(Transaction.amount)
                    .filter(
                        Transaction.transaction_type == "DEPOSIT"
                    )
                    .all()
                )
            ),
            Decimal("0.00")
        )

        withdrawals = sum(
            (
                Decimal(str(row[0]))
                for row in (
                    db.query(Transaction.amount)
                    .filter(
                        Transaction.transaction_type == "WITHDRAWAL"
                    )
                    .all()
                )
            ),
            Decimal("0.00")
        )

        transfer_in = sum(
            (
                Decimal(str(row[0]))
                for row in (
                    db.query(Transaction.amount)
                    .filter(
                        Transaction.transaction_type == "TRANSFER_IN"
                    )
                    .all()
                )
            ),
            Decimal("0.00")
        )

        transfer_out = sum(
            (
                Decimal(str(row[0]))
                for row in (
                    db.query(Transaction.amount)
                    .filter(
                        Transaction.transaction_type == "TRANSFER_OUT"
                    )
                    .all()
                )
            ),
            Decimal("0.00")
        )

        savings_accounts = (
            db.query(Account)
            .filter(Account.account_type == "Savings")
            .count()
        )

        current_accounts = (
            db.query(Account)
            .filter(Account.account_type == "Current")
            .count()
        )

        salary_accounts = (
            db.query(Account)
            .filter(Account.account_type == "Salary")
            .count()
        )

        return {
            "customers": customers_count,
            "accounts": total_accounts,
            "balance": total_balance,
            "transactions": transactions_count,
            "active_accounts": active_accounts,
            "inactive_accounts": inactive_accounts,
            "blocked_accounts": blocked_accounts,
            "deposits": deposits,
            "withdrawals": withdrawals,
            "transfer_in": transfer_in,
            "transfer_out": transfer_out,
            "savings_accounts": savings_accounts,
            "current_accounts": current_accounts,
            "salary_accounts": salary_accounts,
        }

    except Exception:
        raise

    finally:
        db.close()


def get_recent_transactions(limit=10):
    ensure_admin_access()
    """
    Returns the most recent transactions.
    """

    db = SessionLocal()

    try:
        transactions = (
            db.query(Transaction)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .all()
        )

        return transactions

    finally:
        db.close()

# ============================================================
# USER ACCOUNT SECURITY
# ============================================================

def verify_customer_account_ownership(
    customer_id: int,
    account_id: int,
):
    """
    Verify that an account belongs to the logged-in customer.
    """

    if not customer_id or not account_id:
        return {
            "success": False,
            "message": "Invalid customer or account.",
        }

    db = SessionLocal()

    try:

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
                    "You are not authorized to access "
                    "this account."
                ),
            }

        return {
            "success": True,
            "account": account,
        }

    finally:

        db.close()


# ============================================================
# GET USER ACTIVE ACCOUNTS
# ============================================================

def get_customer_active_accounts(customer_id: int):
    if not customer_id:
        return []

    db = SessionLocal()
    try:
        accounts = (
            db.query(Account)
            .options(
                joinedload(Account.customer)
            )
            .filter(
                Account.customer_id == customer_id,
                Account.status == "Active",
            )
            .order_by(Account.account_number)
            .all()
        )
        return accounts
    finally:
        db.close()


# ============================================================
# GET USER TRANSACTIONS
# ============================================================

def get_customer_account_transactions(
    customer_id: int,
    account_id: int,
):

    if not customer_id or not account_id:
        return []

    db = SessionLocal()

    try:

        account = (
            db.query(Account)
            .filter(
                Account.id == account_id,
                Account.customer_id == customer_id,
            )
            .first()
        )

        if not account:
            return []

        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.account_id == account_id
            )
            .order_by(
                Transaction.created_at.desc()
            )
            .all()
        )

        return transactions

    finally:

        db.close()

# ============================================================
# USER PROFILE / CUSTOMER SECURITY
# ============================================================

def get_customer_profile(customer_id: int):
    """
    Return only the customer profile linked to the
    authenticated user's customer_id.
    """

    if not customer_id:
        return None

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
            .first()
        )

        return customer

    finally:

        db.close()

def block_customer(customer_id):
    """
    Block a customer.

    Only administrators are allowed to perform this operation.
    """

    ensure_admin_access()

    session = SessionLocal()

    try:
        customer = (
            session.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return False, "Customer not found."

        if not customer.is_active:
            return False, "Customer is already blocked."

        customer.is_active = False

        # Disable linked login account
        user = (
            session.query(User)
            .filter(User.customer_id == customer.id)
            .first()
        )

        if user:
            user.is_active = False

        session.commit()

        return True, "Customer blocked successfully."

    except Exception as e:
        session.rollback()
        return False, f"Failed to block customer: {str(e)}"

    finally:
        session.close()


def unblock_customer(customer_id):
    """
    Unblock a customer.

    Only administrators are allowed to perform this operation.
    """

    ensure_admin_access()

    session = SessionLocal()

    try:
        customer = (
            session.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return False, "Customer not found."

        if customer.is_active:
            return False, "Customer is already active."

        customer.is_active = True

        # Re-enable linked login account
        user = (
            session.query(User)
            .filter(User.customer_id == customer.id)
            .first()
        )

        if user:
            user.is_active = True

        session.commit()

        return True, "Customer unblocked successfully."

    except Exception as e:
        session.rollback()
        return False, f"Failed to unblock customer: {str(e)}"

    finally:
        session.close()

def delete_customer(customer_id):
    """
    Permanently delete a customer and all related banking data.

    Only administrators are allowed to perform this operation.

    A customer cannot be deleted if any linked account
    has a non-zero balance.
    """

    ensure_admin_access()

    session = SessionLocal()

    try:
        customer = (
            session.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return False, "Customer not found."

        # ----------------------------------------------------
        # Get all accounts belonging to the customer
        # ----------------------------------------------------

        accounts = (
            session.query(Account)
            .filter(
                Account.customer_id == customer.id
            )
            .all()
        )

        # ----------------------------------------------------
        # Prevent deletion when any account has balance
        # ----------------------------------------------------

        non_zero_accounts = [
            account
            for account in accounts
            if Decimal(str(account.balance)) != Decimal("0.00")
        ]

        if non_zero_accounts:

            account_numbers = ", ".join(
                account.account_number
                for account in non_zero_accounts
            )

            return (
                False,
                "Customer cannot be deleted because "
                f"the following account(s) have a non-zero "
                f"balance: {account_numbers}. "
                "Please make the balance zero first.",
            )

        account_ids = [
            account.id
            for account in accounts
        ]

        # ----------------------------------------------------
        # Remove references to these accounts from
        # other transaction records first
        # ----------------------------------------------------

        if account_ids:

            (
                session.query(Transaction)
                .filter(
                    Transaction.reference_account_id.in_(
                        account_ids
                    )
                )
                .update(
                    {
                        Transaction.reference_account_id: None
                    },
                    synchronize_session=False,
                )
            )

            # ------------------------------------------------
            # Delete transactions belonging to these accounts
            # ------------------------------------------------

            (
                session.query(Transaction)
                .filter(
                    Transaction.account_id.in_(
                        account_ids
                    )
                )
                .delete(
                    synchronize_session=False
                )
            )

            # ------------------------------------------------
            # Delete customer accounts
            # ------------------------------------------------

            (
                session.query(Account)
                .filter(
                    Account.id.in_(account_ids)
                )
                .delete(
                    synchronize_session=False
                )
            )

        # ----------------------------------------------------
        # Delete linked user login
        # ----------------------------------------------------

        user = (
            session.query(User)
            .filter(
                User.customer_id == customer.id
            )
            .first()
        )

        if user:
            session.delete(user)

        # ----------------------------------------------------
        # Delete customer
        # ----------------------------------------------------

        session.delete(customer)

        session.commit()

        return True, "Customer deleted successfully."

    except Exception as e:

        session.rollback()

        return (
            False,
            f"Failed to delete customer: {str(e)}",
        )

    finally:
        session.close()

def verify_customer_for_password_reset(
    full_name,
    email,
    phone,
):
    """
    Verify customer identity using registered
    full name, email and mobile number.

    This function does not reset the password
    and does not send an OTP.
    """

    session = SessionLocal()

    try:
        full_name = full_name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not full_name:
            return False, None, "Full name is required."

        if not email:
            return False, None, "Email is required."

        if not phone:
            return False, None, "Mobile number is required."

        customer = (
            session.query(Customer)
            .filter(
                Customer.email == email,
            )
            .first()
        )

        if not customer:
            return (
                False,
                None,
                "The provided customer details could not be verified.",
            )

        if customer.full_name.strip().lower() != full_name.lower():
            return (
                False,
                None,
                "The provided customer details could not be verified.",
            )

        if customer.phone.strip() != phone:
            return (
                False,
                None,
                "The provided customer details could not be verified.",
            )

        if not customer.is_active:
            return (
                False,
                None,
                "This customer account is currently blocked.",
            )

        return (
            True,
            customer.id,
            "Customer details verified successfully.",
        )

    except Exception as e:

        return (
            False,
            None,
            f"Unable to verify customer details: {str(e)}",
        )

    finally:
        session.close()