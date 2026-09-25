import bcrypt
import streamlit as st
from database import SessionLocal
from models import User, Customer

# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Convert plain password into a secure bcrypt hash.
    """

    password_bytes = password.encode("utf-8")

    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(
        password_bytes,
        salt,
    )

    return hashed_password.decode("utf-8")


# ============================================================
# PASSWORD VERIFICATION
# ============================================================

def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """
    Verify a plain password against stored bcrypt hash.
    """

    password_bytes = password.encode("utf-8")

    hash_bytes = password_hash.encode("utf-8")

    return bcrypt.checkpw(
        password_bytes,
        hash_bytes,
    )


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    username: str,
    password: str,
    role: str = "user",
) -> bool:
    """
    Create a basic user.

    Used mainly for admin/system-level user creation.
    """

    username = username.strip()

    db = SessionLocal()

    try:

        existing_user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

        if existing_user:
            return False

        new_user = User(
            username=username,
            password_hash=hash_password(
                password
            ),
            role=role,
            is_active=True,
        )

        db.add(new_user)

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# CREATE CUSTOMER USER
# ============================================================

def create_customer_user(
    full_name: str,
    email: str,
    phone: str,
    address: str,
    username: str,
    password: str,
):
    """
    Create a new customer and connect that customer
    with a normal application user.

    Signup creates:

        Customer
            +
        User
            +
        User.customer_id
    """

    full_name = full_name.strip()

    email = email.strip().lower()

    phone = phone.strip()

    address = address.strip()

    username = username.strip()

    # --------------------------------------------------------
    # BASIC VALIDATION
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
                "Full name must contain at least "
                "3 characters."
            ),
        }

    if not email:

        return {
            "success": False,
            "message": "Email is required.",
        }

    if "@" not in email or "." not in email:

        return {
            "success": False,
            "message": (
                "Please enter a valid email address."
            ),
        }

    if (
        not phone.isdigit()
        or len(phone) != 10
        or phone[0] not in "6789"
    ):

        return {
            "success": False,
            "message": (
                "Phone number must be a valid "
                "10-digit Indian mobile number."
            ),
        }

    if not username:

        return {
            "success": False,
            "message": "Username is required.",
        }

    if len(username) < 4:

        return {
            "success": False,
            "message": (
                "Username must contain at least "
                "4 characters."
            ),
        }

    if not password:

        return {
            "success": False,
            "message": "Password is required.",
        }

    if len(password) < 6:

        return {
            "success": False,
            "message": (
                "Password must contain at least "
                "6 characters."
            ),
        }

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # CHECK USERNAME
        # ----------------------------------------------------

        existing_user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

        if existing_user:

            return {
                "success": False,
                "message": (
                    "Username already exists. "
                    "Please choose another username."
                ),
            }

        # ----------------------------------------------------
        # CHECK CUSTOMER EMAIL
        # ----------------------------------------------------

        existing_customer = (
            db.query(Customer)
            .filter(
                Customer.email == email
            )
            .first()
        )

        if existing_customer:

            return {
                "success": False,
                "message": (
                    "A customer with this email "
                    "already exists."
                ),
            }

        # ----------------------------------------------------
        # GENERATE CUSTOMER CODE
        # ----------------------------------------------------

        import secrets

        customer_code = (
            "CUST"
            + secrets.token_hex(5).upper()
        )

        while (
            db.query(Customer)
            .filter(
                Customer.customer_code
                == customer_code
            )
            .first()
        ):

            customer_code = (
                "CUST"
                + secrets.token_hex(5).upper()
            )

        # ----------------------------------------------------
        # CREATE CUSTOMER
        # ----------------------------------------------------

        customer = Customer(
            customer_code=customer_code,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address or None,
        )

        db.add(customer)

        db.flush()

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        new_user = User(
            username=username,
            password_hash=hash_password(
                password
            ),
            role="user",
            customer_id=customer.id,
            is_active=True,
        )

        db.add(new_user)

        # ----------------------------------------------------
        # COMMIT BOTH TOGETHER
        # ----------------------------------------------------

        db.commit()

        db.refresh(customer)

        db.refresh(new_user)

        return {
            "success": True,
            "message": (
                "User account created successfully."
            ),
            "customer": customer,
            "user": new_user,
        }

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# AUTHENTICATE USER
# ============================================================

def authenticate_user(
    username: str,
    password: str,
):
    """
    Authenticate user using username and password.

    Returns:
        User object if successful.
        None if authentication fails.
    """

    username = username.strip()

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

        if not user:

            return None

        if not user.is_active:

            return None

        if not verify_password(
            password,
            user.password_hash,
        ):

            return None

        return user

    finally:

        db.close()

# ============================================================
# CHANGE USER PASSWORD
# ============================================================

def change_user_password(
    user_id: int,
    current_password: str,
    new_password: str,
):
    """
    Change password only for the authenticated user
    after verifying the current password.
    """

    if not user_id:
        return {
            "success": False,
            "message": "User account could not be identified.",
        }

    if not current_password or not new_password:
        return {
            "success": False,
            "message": "All password fields are required.",
        }

    if len(new_password) < 6:
        return {
            "success": False,
            "message": "New password must be at least 6 characters long.",
        }

    if current_password == new_password:
        return {
            "success": False,
            "message": "New password must be different from the current password.",
        }

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return {
                "success": False,
                "message": "User account not found.",
            }

        # ----------------------------------------------------
        # Verify current password
        # ----------------------------------------------------

        if not verify_password(
            current_password,
            user.password_hash,
        ):
            return {
                "success": False,
                "message": "Current password is incorrect.",
            }

        # ----------------------------------------------------
        # Update password
        # ----------------------------------------------------

        user.password_hash = hash_password(new_password)

        db.commit()

        return {
            "success": True,
            "message": "Password changed successfully.",
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": f"Unable to change password: {str(e)}",
        }

    finally:

        db.close()

# ========================================================
# RESET USER PASSWORD
# ========================================================

def reset_user_password(
    customer_id: int,
    new_password: str,
):
    """
    Reset password for a customer after OTP verification.

    Security checks:
    - Customer must exist
    - Customer must be active
    - User account must exist
    - User account must be active
    - Password must contain at least 6 characters
    """

    db = SessionLocal()

    try:

        # ------------------------------------------------
        # VALIDATE PASSWORD
        # ------------------------------------------------

        if not new_password or len(new_password) < 6:

            return {
                "success": False,
                "message": (
                    "Password must contain at least "
                    "6 characters."
                ),
            }

        # ------------------------------------------------
        # FIND CUSTOMER
        # ------------------------------------------------

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id,
                Customer.is_active == True,
            )
            .first()
        )

        if not customer:

            return {
                "success": False,
                "message": (
                    "Customer account not found "
                    "or is inactive."
                ),
            }

        # ------------------------------------------------
        # FIND USER ACCOUNT
        # ------------------------------------------------

        user = (
            db.query(User)
            .filter(
                User.customer_id == customer_id,
                User.is_active == True,
            )
            .first()
        )

        if not user:

            return {
                "success": False,
                "message": (
                    "Login account was not found "
                    "or is inactive."
                ),
            }

        # ------------------------------------------------
        # HASH NEW PASSWORD
        # ------------------------------------------------

        new_password_hash = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        # ------------------------------------------------
        # UPDATE PASSWORD
        # ------------------------------------------------

        user.password_hash = new_password_hash

        db.commit()

        return {
            "success": True,
            "message": (
                "Password reset successfully."
            ),
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Unable to reset password: {str(e)}"
            ),
        }

    finally:

        db.close()

# ============================================================
# PREMIUM LOGIN / SIGNUP / RESET PASSWORD PAGE
# ============================================================

def login_page():

    # ========================================================
    # PREMIUM AUTH PAGE CSS
    # ========================================================

    st.markdown(
        """
        <style>

        /* ==================================================
           REMOVE DEFAULT TOP SPACE
           ================================================== */

        .block-container {
            padding-top: 2.2rem !important;
            padding-bottom: 2rem !important;
        }

        /* ==================================================
           MAIN AUTH BRAND
           ================================================== */

        .auth-brand {
            text-align: center;
            margin-bottom: 12px;
        }
        .auth-brand-icon {
            font-size: 3.4rem;
            line-height: 1;
            margin-bottom: 10px;
            filter:
                drop-shadow(
                    0 8px 15px
                    rgba(99,102,241,0.25)
                );
        }
        .auth-brand-title {
            font-size: 2.35rem;
            font-weight: 850;
            letter-spacing: 0.8px;
            color: #f8fafc;
            line-height: 1.1;
        }
        .auth-brand-subtitle {
            margin-top: 8px;
            font-size: 0.92rem;
            color: #8f96a8;
            letter-spacing: 0.3px;
        }

        /* ==================================================
           AUTH HEADING
           ================================================== */

        .auth-heading {
            font-size: 1.55rem;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 5px;
        }
        .auth-description {
            color: #9299aa;
            font-size: 0.86rem;
            line-height: 1.55;
            margin-bottom: 18px;
        }

        /* ==================================================
           SECTION HEADING
           ================================================== */

        .auth-section {
            font-size: 0.76rem;
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: 1.1px;
            color: #8f96a8;
            margin:
                18px 0 10px 0;
        }

        /* ==================================================
           INPUT LABELS
           ================================================== */

        div[data-testid="stTextInput"]
        label,
        div[data-testid="stTextArea"]
        label {
            color: #cbd1dc !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
        }

        /* ==================================================
           INPUT BOXES
           ================================================== */

        div[data-testid="stTextInput"]
        input,
        div[data-testid="stTextArea"]
        textarea {
            background:
                rgba(255,255,255,0.035)
                !important;
            border:
                1px solid
                rgba(255,255,255,0.10)
                !important;
            border-radius:
                11px
                !important;
            color:
                #f8fafc
                !important;
            min-height:
                43px
                !important;
        }
        div[data-testid="stTextInput"]
        input:focus,
        div[data-testid="stTextArea"]
        textarea:focus {
            border-color:
                #6366f1
                !important;
            box-shadow:
                0 0 0 1px
                rgba(99,102,241,0.30)
                !important;
        }
        div[data-testid="stTextInput"]
        input::placeholder,
        div[data-testid="stTextArea"]
        textarea::placeholder {
            color:
                #686f80
                !important;
        }

        /* ==================================================
           TABS
           ================================================== */

        button[data-baseweb="tab"] {
            color:
                #8f96a8
                !important;
            font-weight:
                650
                !important;
            font-size:
                0.88rem
                !important;
            padding:
                11px 14px
                !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color:
                #ffffff
                !important;
        }
        div[data-baseweb="tab-highlight"] {
            background:
                linear-gradient(
                    90deg,
                    #6366f1,
                    #8b5cf6
                )
                !important;
            height:
                3px
                !important;
            border-radius:
                10px
                !important;
        }

        /* ==================================================
           BUTTONS
           ================================================== */

        div.stButton > button,
        div[data-testid="stFormSubmitButton"]
        button {
            border:
                1px solid
                rgba(99,102,241,0.30)
                !important;
            border-radius:
                11px
                !important;
            background:
                linear-gradient(
                    135deg,
                    #6366f1,
                    #7c3aed
                )
                !important;
            color:
                #ffffff
                !important;
            font-weight:
                700
                !important;
            min-height:
                44px
                !important;
            transition:
                all 0.20s ease
                !important;
            box-shadow:
                0 7px 18px
                rgba(99,102,241,0.18)
                !important;
        }
        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"]
        button:hover {
            transform:
                translateY(-1px);
            box-shadow:
                0 10px 24px
                rgba(99,102,241,0.28)
                !important;
            border-color:
                rgba(139,92,246,0.55)
                !important;
        }

        /* ==================================================
           FORM BORDER
           ================================================== */

        div[data-testid="stForm"] {
            border:
                none
                !important;
            padding:
                0
                !important;
            background:
                transparent
                !important;
        }

        /* ==================================================
           INFO / SUCCESS / ERROR
           ================================================== */

        div[data-testid="stAlert"] {
            border-radius:
                11px
                !important;
            border:
                1px solid
                rgba(255,255,255,0.08)
                !important;
        }

        /* ==================================================
           SECURITY FOOTER
           ================================================== */

        .auth-security {
            text-align: center;
            margin-top: 20px;
            color: #697183;
            font-size: 0.72rem;
        }
        .auth-security strong {
            color: #8f96a8;
        }

        /* ==================================================
           MOBILE
           ================================================== */

        @media (max-width: 768px) {
            .auth-brand-title {
                font-size:
                    1.85rem;
            }
            .auth-card {
                padding:
                    20px 17px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # BRAND
    # ========================================================

    st.markdown(
        """
        <div class="auth-brand">
            <div class="auth-brand-icon">
                🏦
            </div>
            <div class="auth-brand-title">
                BANK MANAGEMENT
            </div>
            <div class="auth-brand-subtitle">
                Secure Banking Portal
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # CENTER AUTH CARD
    # ========================================================

    left_space, center, right_space = st.columns(
        [1, 2.15, 1]
    )

    with center:

        # ====================================================
        # TABS
        # ====================================================

        login_tab, signup_tab, reset_tab = st.tabs(
            [
                "🔐 Login",
                "📝 Signup",
                "🔑 Reset Password",
            ]
        )

        # ====================================================
        # LOGIN
        # ====================================================

        with login_tab:
            st.markdown(
                """
                <div class="auth-heading">
                    Welcome Back
                </div>
                <div class="auth-description">
                    Sign in to securely access your
                    banking account and manage your
                    banking activities.
                </div>
                """,
                unsafe_allow_html=True,
            )


            with st.form(
                "login_form",
                clear_on_submit=False,
            ):

                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                )

                login_button = (
                    st.form_submit_button(
                        "🔐  Login Securely",
                        use_container_width=True,
                    )
                )

            if login_button:
                username = username.strip()

                if not username or not password:
                    st.error(
                        "Please enter username "
                        "and password."
                    )
                    return

                user = authenticate_user(
                    username,
                    password,
                )

                if user:

                    # ----------------------------------------
                    # SESSION DATA
                    # ----------------------------------------

                    st.session_state.authenticated = True
                    st.session_state.user_id = (
                        user.id
                    )
                    st.session_state.username = (
                        user.username
                    )
                    st.session_state.role = (
                        user.role
                    )
                    st.session_state.customer_id = (
                        user.customer_id
                    )
                    st.success(
                        "Login successful!"
                    )
                    st.rerun()

                else:
                    st.error(
                        "Invalid username or password."
                    )


        # ====================================================
        # SIGNUP
        # ====================================================

        with signup_tab:
            st.markdown(
                """
                <div class="auth-heading">
                    Create Your Account
                </div>
                <div class="auth-description">
                    Register as a new banking customer.
                    Your customer profile will be created
                    automatically.
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form(
                "signup_form",
                clear_on_submit=True,
            ):

                # --------------------------------------------
                # CUSTOMER DETAILS
                # --------------------------------------------

                st.markdown(
                    """
                    <div class="auth-section">
                        👤 Customer Information
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col1, col2 = st.columns(
                    2
                )

                with col1:
                    full_name = st.text_input(
                        "Full Name *",
                        placeholder="Enter your full name",
                    )

                    email = st.text_input(
                        "Email *",
                        placeholder="example@gmail.com",
                    )

                    phone = st.text_input(
                        "Phone Number *",
                        placeholder="9876543210",
                        max_chars=10,
                    )

                with col2:
                    address = st.text_area(
                        "Address",
                        placeholder=(
                            "Enter your complete address"
                        ),
                    )

                # --------------------------------------------
                # LOGIN CREDENTIALS
                # --------------------------------------------

                st.markdown(
                    """
                    <div class="auth-section">
                        🔐 Login Credentials
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                username = st.text_input(
                    "Username *",
                    placeholder="Choose a username",
                )

                password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Minimum 6 characters",
                )

                confirm_password = st.text_input(
                    "Confirm Password *",
                    type="password",
                    placeholder="Re-enter your password",
                )

                signup_button = (
                    st.form_submit_button(
                        "📝  Create Account",
                        use_container_width=True,
                    )
                )

            if signup_button:

                # --------------------------------------------
                # CONFIRM PASSWORD
                # --------------------------------------------

                if password != confirm_password:
                    st.error(
                        "Password and confirm password "
                        "do not match."
                    )

                else:
                    result = (
                        create_customer_user(
                            full_name=full_name,
                            email=email,
                            phone=phone,
                            address=address,
                            username=username,
                            password=password,
                        )
                    )

                    if result["success"]:
                        customer = (
                            result["customer"]
                        )

                        st.success(
                            "🎉 User account created "
                            "successfully!"
                        )

                        st.info(
                            "Your Customer Code: "
                            f"**{customer.customer_code}**"
                        )

                        st.info(
                            "You can now login using "
                            "your username and password."
                        )

                    else:
                        st.error(
                            result["message"]
                        )

        # ====================================================
        # RESET PASSWORD
        # ====================================================

        with reset_tab:
            st.markdown(
                """
                <div class="auth-heading">
                    Reset Your Password
                </div>
                <div class="auth-description">
                    Verify your registered details,
                    receive an OTP, and securely create
                    a new password.
                </div>
                """,
                unsafe_allow_html=True,
            )


            # ------------------------------------------------
            # RESET INFORMATION
            # ------------------------------------------------

            st.markdown(
                """
                <div class="auth-section">
                    👤 Verify Your Identity
                </div>
                """,
                unsafe_allow_html=True,
            )


            reset_name = st.text_input(
                "Full Name",
                placeholder=(
                    "Enter your registered full name"
                ),
                key="reset_full_name",
            )


            reset_email = st.text_input(
                "Registered Email",
                placeholder=(
                    "Enter your registered email"
                ),
                key="reset_email",
            )


            reset_phone = st.text_input(
                "Registered Mobile Number",
                placeholder=(
                    "Enter your registered mobile number"
                ),
                key="reset_phone",
            )


            # ------------------------------------------------
            # IMPORT RESET FUNCTIONS
            # ------------------------------------------------

            from services import (
                verify_customer_for_password_reset,
            )

            from otp_service import (
                send_password_reset_otp,
                verify_password_reset_otp,
            )

            # ------------------------------------------------
            # VERIFY DETAILS
            # ------------------------------------------------

            verify_details = st.button(
                "🔍  Verify Details",
                use_container_width=True,
                type="primary",
                key="verify_reset_details",
            )

            if verify_details:
                if not reset_name.strip():
                    st.error(
                        "Please enter your full name."
                    )

                elif not reset_email.strip():
                    st.error(
                        "Please enter your registered email."
                    )

                elif not reset_phone.strip():
                    st.error(
                        "Please enter your registered mobile number."
                    )

                else:
                    (
                        verified,
                        customer_id,
                        message,
                    ) = verify_customer_for_password_reset(
                        reset_name,
                        reset_email,
                        reset_phone,
                    )

                    if verified:
                        st.success(message)

                        # ------------------------------------
                        # SAVE CUSTOMER
                        # ------------------------------------

                        st.session_state.reset_customer_id = (
                            customer_id
                        )
                        st.session_state.reset_identity_verified = (
                            True
                        )

                        # ------------------------------------
                        # SEND OTP
                        # ------------------------------------

                        otp_result = (
                            send_password_reset_otp(
                                customer_id=customer_id
                            )
                        )

                        if otp_result["success"]:
                            st.session_state.reset_otp_id = (
                                otp_result["otp_id"]
                            )
                            st.session_state.reset_otp_sent = (
                                True
                            )
                            st.session_state.reset_otp_verified = (
                                False
                            )
                            st.success(
                                "📧 OTP has been sent successfully "
                                "to your registered email."
                            )
                            st.info(
                                "Please check your email inbox "
                                "and spam folder. The OTP is valid "
                                "for 5 minutes."
                            )

                        else:
                            st.session_state.reset_otp_sent = (
                                False
                            )
                            st.error(
                                "❌ Unable to send OTP: "
                                f"{otp_result['message']}"
                            )

                    else:
                        st.error(message)


            # =================================================
            # OTP VERIFICATION
            # =================================================

            if st.session_state.get(
                "reset_otp_sent",
                False,
            ):

                st.markdown(
                    '<div class="auth-section">'
                    '🔐 OTP Verification'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.info(
                    "Enter the 6-digit OTP sent to your "
                    "registered email address."
                )
                entered_reset_otp = st.text_input(
                    "Enter OTP",
                    max_chars=6,
                    placeholder="Enter 6-digit OTP",
                    key="reset_otp_input",
                )
                verify_otp_button = st.button(
                    "✅  Verify OTP",
                    use_container_width=True,
                    type="primary",
                    key="verify_reset_otp",
                )
                if verify_otp_button:
                    if not entered_reset_otp.strip():
                        st.error(
                            "Please enter the OTP."
                        )
                    else:
                        otp_verification = (
                            verify_password_reset_otp(
                                otp_id=st.session_state.get(
                                    "reset_otp_id"
                                ),
                                customer_id=st.session_state.get(
                                    "reset_customer_id"
                                ),
                                entered_otp=entered_reset_otp,
                            )
                        )
                        if otp_verification["success"]:
                            st.session_state.reset_otp_verified = (
                                True
                            )
                            st.success(
                                "✅ OTP verified successfully!"
                            )
                            st.info(
                                "You can now create your "
                                "new password."
                            )
                        else:
                            st.error(
                                f"❌ {otp_verification['message']}"
                            )

            # =================================================
            # NEW PASSWORD
            # =================================================

            if st.session_state.get(
                "reset_otp_verified",
                False,
            ):
                st.markdown(
                    '<div class="auth-section">'
                    '🔑 Create New Password'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.info(
                    "Your OTP has been verified successfully. "
                    "Create a new password for your account."
                )
                new_reset_password = st.text_input(
                    "New Password",
                    type="password",
                    placeholder=(
                        "Enter your new password"
                    ),
                    key="new_reset_password",
                )
                confirm_reset_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                    placeholder=(
                        "Re-enter your new password"
                    ),
                    key="confirm_reset_password",
                )
                reset_password_button = st.button(
                    "🔄  Reset Password",
                    use_container_width=True,
                    type="primary",
                    key="reset_password_button",
                )
                if reset_password_button:

                    # ----------------------------------------
                    # EMPTY PASSWORD
                    # ----------------------------------------

                    if not new_reset_password.strip():
                        st.error(
                            "Please enter your new password."
                        )

                    # ----------------------------------------
                    # CONFIRM PASSWORD
                    # ----------------------------------------

                    elif not confirm_reset_password.strip():
                        st.error(
                            "Please confirm your new password."
                        )

                    # ----------------------------------------
                    # PASSWORD LENGTH
                    # ----------------------------------------

                    elif len(new_reset_password) < 6:
                        st.error(
                            "Password must contain at least "
                            "6 characters."
                        )

                    # ----------------------------------------
                    # PASSWORD MATCH
                    # ----------------------------------------

                    elif (
                        new_reset_password
                        != confirm_reset_password
                    ):
                        st.error(
                            "New password and confirm password "
                            "do not match."
                        )

                    else:

                        # ------------------------------------
                        # RESET PASSWORD
                        # ------------------------------------

                        reset_result = (
                            reset_user_password(
                                customer_id=st.session_state.get(
                                    "reset_customer_id"
                                ),
                                new_password=(
                                    new_reset_password
                                ),
                            )
                        )

                        if reset_result["success"]:
                            st.success(
                                "🎉 Password reset successfully!"
                            )
                            st.info(
                                "You can now login using your "
                                "new password."
                            )

                            # --------------------------------
                            # CLEAR RESET STATE
                            # --------------------------------

                            st.session_state.reset_identity_verified = (
                                False
                            )
                            st.session_state.reset_otp_sent = (
                                False
                            )
                            st.session_state.reset_otp_verified = (
                                False
                            )
                            st.session_state.reset_customer_id = (
                                None
                            )
                            st.session_state.reset_otp_id = (
                                None
                            )

                        else:
                            st.error(
                                f"❌ {reset_result['message']}"
                            )


        # ====================================================
        # SECURITY FOOTER
        # ====================================================

        st.markdown(
            """
            <div class="auth-security">
                🔒 <strong>Secure Banking Portal</strong>
                &nbsp;•&nbsp;
                Your account information is protected
            </div>
            """,
            unsafe_allow_html=True,
        )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

# ============================================================
# CREATE INITIAL ADMIN
# ============================================================

def create_initial_admin():

    from config import (
        INITIAL_ADMIN_USERNAME,
        INITIAL_ADMIN_PASSWORD,
    )

    if not INITIAL_ADMIN_PASSWORD:

        raise RuntimeError(
            "INITIAL_ADMIN_PASSWORD "
            "is not configured."
        )

    db = SessionLocal()

    try:

        existing_admin = (
            db.query(User)
            .filter(
                User.username
                == INITIAL_ADMIN_USERNAME
            )
            .first()
        )

        if existing_admin:

            # ------------------------------------------------
            # IMPORTANT
            # Ensure configured initial admin
            # always remains an admin.
            # ------------------------------------------------

            if existing_admin.role != "admin":

                existing_admin.role = "admin"

                db.commit()

            return

        admin = User(
            username=INITIAL_ADMIN_USERNAME,
            password_hash=hash_password(
                INITIAL_ADMIN_PASSWORD
            ),
            role="admin",
            customer_id=None,
            is_active=True,
        )

        db.add(admin)

        db.commit()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# ADMIN ACCESS CONTROL
# ============================================================

def is_admin():
    """
    Check whether the currently authenticated user
    has admin role.
    """

    return (
        st.session_state.get("authenticated", False)
        and st.session_state.get("role") == "admin"
    )

def require_admin():
    """
    Verify that the currently authenticated user
    has admin privileges.

    Returns:
        True  -> Admin user
        False -> Not authorized
    """

    if not st.session_state.get("authenticated", False):
        return False

    if not validate_current_session():
        return False

    return st.session_state.get("role") == "admin"

# ============================================================
# ADMIN USER MANAGEMENT
# ============================================================

def get_all_users_for_admin():
    """
    Return all user accounts for the Admin User Management page.

    Only authenticated administrators are allowed to access
    this function.
    """

    if not require_admin():

        raise PermissionError(
            "Administrator access is required."
        )

    db = SessionLocal()

    try:

        users = (
            db.query(User)
            .order_by(User.created_at.desc())
            .all()
        )

        return [
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "customer_id": user.customer_id,
                "created_at": user.created_at,
            }
            for user in users
        ]

    finally:

        db.close()


def update_user_role(
    user_id: int,
    new_role: str,
):
    """
    Change a user's role between user and admin.

    Only administrators can perform this operation.
    """

    # --------------------------------------------------------
    # ADMIN AUTHORIZATION
    # --------------------------------------------------------

    if not require_admin():

        return {
            "success": False,
            "message": (
                "Administrator access is required."
            ),
        }


    # --------------------------------------------------------
    # VALID ROLE
    # --------------------------------------------------------

    new_role = new_role.strip().lower()

    if new_role not in ["user", "admin"]:

        return {
            "success": False,
            "message": (
                "Invalid role. Choose User or Admin."
            ),
        }


    # --------------------------------------------------------
    # TARGET USER ID
    # --------------------------------------------------------

    if not user_id:

        return {
            "success": False,
            "message": "Invalid user account.",
        }


    # --------------------------------------------------------
    # CURRENT LOGGED-IN USER
    # --------------------------------------------------------

    current_user_id = (
        st.session_state.get("user_id")
    )


    # --------------------------------------------------------
    # PREVENT SELF ROLE CHANGE
    # --------------------------------------------------------

    if user_id == current_user_id:

        return {
            "success": False,
            "message": (
                "You cannot change your own role."
            ),
        }


    db = SessionLocal()

    try:

        target_user = (
            db.query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )


        # ----------------------------------------------------
        # USER NOT FOUND
        # ----------------------------------------------------

        if not target_user:

            return {
                "success": False,
                "message": "User account not found.",
            }


        old_role = target_user.role


        # ----------------------------------------------------
        # NO CHANGE
        # ----------------------------------------------------

        if old_role == new_role:

            return {
                "success": False,
                "message": (
                    "The user already has this role."
                ),
            }

        # ----------------------------------------------------
        # PREVENT LAST ADMIN FROM BEING REMOVED
        # ----------------------------------------------------

        if (
            old_role == "admin"
            and new_role == "user"
        ):
            admin_count = (
                db.query(User)
                .filter(
                    User.role == "admin"
                )
                .count()
            )

            if admin_count <= 1:
                return {
                    "success": False,
                    "message": (
                        "The last administrator cannot "
                        "be changed to User. "
                        "At least one Admin account "
                        "must remain."
                    ),
                }

        # ----------------------------------------------------
        # UPDATE ROLE
        # ----------------------------------------------------

        target_user.role = new_role
        db.commit()

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return {
            "success": True,
            "message": (
                f"User '{target_user.username}' "
                f"role changed from "
                f"'{old_role.title()}' to "
                f"'{new_role.title()}'."
            ),
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": (
                f"Unable to update user role: {str(e)}"
            ),
        }

    finally:
        db.close()

# ============================================================
# DELETE USER / ADMIN ACCOUNT
# ============================================================

def delete_user_account(user_id: int):
    """
    Delete a user/admin login account.

    Only administrators can perform this operation.
    The currently logged-in administrator cannot delete
    their own account.

    The last administrator cannot be deleted.
    """

    # --------------------------------------------------------
    # ADMIN AUTHORIZATION
    # --------------------------------------------------------

    if not require_admin():
        return {
            "success": False,
            "message": "Administrator access is required.",
        }

    # --------------------------------------------------------
    # VALID USER ID
    # --------------------------------------------------------

    if not user_id:
        return {
            "success": False,
            "message": "Invalid user account.",
        }

    # --------------------------------------------------------
    # CURRENT LOGGED-IN USER
    # --------------------------------------------------------

    current_user_id = st.session_state.get("user_id")

    if user_id == current_user_id:
        return {
            "success": False,
            "message": "You cannot delete your own account.",
        }

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # FIND TARGET USER
        # ----------------------------------------------------

        target_user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not target_user:
            return {
                "success": False,
                "message": "User account not found.",
            }

        # ----------------------------------------------------
        # PREVENT DELETING LAST ADMIN
        # ----------------------------------------------------

        if target_user.role == "admin":

            admin_count = (
                db.query(User)
                .filter(User.role == "admin")
                .count()
            )

            if admin_count <= 1:
                return {
                    "success": False,
                    "message": (
                        "The last administrator cannot be deleted. "
                        "At least one Admin account must remain."
                    ),
                }

        username = target_user.username
        role = target_user.role

        # ----------------------------------------------------
        # DELETE USER ACCOUNT
        # ----------------------------------------------------

        db.delete(target_user)
        db.commit()

        return {
            "success": True,
            "message": (
                f"{role.title()} account "
                f"'{username}' deleted successfully."
            ),
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": f"Unable to delete account: {str(e)}",
        }

    finally:
        db.close()

# ============================================================
# SESSION SECURITY VALIDATION
# ============================================================

def validate_current_session():
    """
    Validate the currently authenticated user's session
    against the database.
    """

    if not st.session_state.get("authenticated", False):
        return False

    user_id = st.session_state.get("user_id")

    if not user_id:
        return False

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return False

        # ----------------------------------------------------
        # Account status check
        # ----------------------------------------------------

        if not user.is_active:
            return False

        # ----------------------------------------------------
        # Validate session role
        # ----------------------------------------------------

        session_role = st.session_state.get("role")

        if session_role != user.role:
            return False

        # ----------------------------------------------------
        # Validate session username
        # ----------------------------------------------------

        session_username = st.session_state.get("username")

        if session_username != user.username:
            return False

        # ----------------------------------------------------
        # Validate customer mapping
        # ----------------------------------------------------

        session_customer_id = st.session_state.get(
            "customer_id"
        )

        if session_customer_id != user.customer_id:
            return False

        return True

    finally:

        db.close()

# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.clear()

    st.rerun()