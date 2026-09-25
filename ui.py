import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from services import (
    create_customer,
    update_customer,
    get_all_customers,
    search_customers,
    create_account,
    get_all_accounts,
    search_accounts,
    deposit_money,
    withdraw_money,
    transfer_money,
    get_active_accounts,
    get_account_transactions,
    get_dashboard_statistics,
    get_recent_transactions,
    block_customer,
    unblock_customer,
    delete_customer,
)
from otp_service import (
    send_transaction_otp,
    verify_transaction_otp,
)
from auth import (
    get_all_users_for_admin,
    update_user_role,
    delete_user_account,
)

# ============================================================
# CUSTOMER PAGE
# ============================================================

def customer_page():

    st.title("👤 Customer Management")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "➕ Add Customer",
            "🔎 View / Search Customers",
            "✏️ Update Customer",
            "🔒 Block / Unblock / Delete",
        ]
    )

    # ========================================================
    # ADD CUSTOMER
    # ========================================================

    with tab1:

        st.subheader("Create New Customer")

        with st.form(
            "add_customer_form",
            clear_on_submit=True,
        ):

            col1, col2 = st.columns(2)

            with col1:

                full_name = st.text_input(
                    "Full Name *",
                    placeholder="Enter customer name",
                )

                email = st.text_input(
                    "Email *",
                    placeholder="example@gmail.com",
                )

            with col2:

                phone = st.text_input(
                    "Phone Number *",
                    placeholder="XXXXXXXXXX",
                    max_chars=10,
                )

                address = st.text_area(
                    "Address",
                    placeholder=(
                        "Enter complete customer address"
                    ),
                )

            submitted = st.form_submit_button(
                "Create Customer",
                use_container_width=True,
            )

        if submitted:

            result = create_customer(
                full_name=full_name,
                email=email,
                phone=phone,
                address=address,
            )

            if result["success"]:

                customer = result["customer"]

                st.success(
                    "Customer created successfully!"
                )

                st.info(
                    "Customer Code: "
                    f"**{customer.customer_code}**"
                )

            else:

                st.error(
                    result["message"]
                )

    # ========================================================
    # VIEW / SEARCH
    # ========================================================

    with tab2:

        st.subheader("Customers")

        search_term = st.text_input(
            "Search",
            placeholder=(
                "Search by customer code, "
                "name, email or phone"
            ),
            key="customer_search",
        )

        if search_term:

            customers = search_customers(
                search_term
            )

        else:

            customers = get_all_customers()

        if not customers:

            st.info(
                "No customers found."
            )

        else:

            data = []

            for customer in customers:

                data.append(
                    {
                        "Customer Code": (
                            customer.customer_code
                        ),
                        "Full Name": (
                            customer.full_name
                        ),
                        "Email": (
                            customer.email
                        ),
                        "Phone": (
                            customer.phone
                        ),
                        "Address": (
                            customer.address or "-"
                        ),
                        "Created At": (
                            customer.created_at.strftime(
                                "%d-%m-%Y %H:%M"
                            )
                        ),
                    }
                )

            dataframe = pd.DataFrame(
                data
            )

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )

    # ========================================================
    # UPDATE CUSTOMER
    # ========================================================

    with tab3:

        st.subheader(
            "✏️ Update Customer Details"
        )

        customers = get_all_customers()

        if not customers:

            st.info(
                "No customers available to update."
            )

        else:

            customer_options = {
                (
                    f"{customer.customer_code} | "
                    f"{customer.full_name} | "
                    f"{customer.email}"
                ): customer.id
                for customer in customers
            }

            selected_customer = st.selectbox(
                "Select Customer",
                options=list(
                    customer_options.keys()
                ),
                key="update_customer_select",
            )

            selected_customer_id = (
                customer_options[
                    selected_customer
                ]
            )

            selected_customer_obj = next(
                (
                    customer
                    for customer in customers
                    if customer.id
                    == selected_customer_id
                ),
                None,
            )

            if selected_customer_obj:

                st.markdown(
                    """
                    <div style="
                        padding: 12px 16px;
                        border-radius: 10px;
                        background: rgba(99, 102, 241, 0.08);
                        border: 1px solid rgba(99, 102, 241, 0.20);
                        margin-bottom: 18px;
                    ">
                        <b>Customer Code:</b>
                        &nbsp;
                        Current customer code will remain unchanged.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col1, col2 = st.columns(2)

                with col1:

                    updated_full_name = st.text_input(
                        "Full Name *",
                        value=(
                            selected_customer_obj.full_name
                        ),
                        key=(
                            f"update_name_"
                            f"{selected_customer_id}"
                        ),
                    )

                    updated_email = st.text_input(
                        "Email *",
                        value=(
                            selected_customer_obj.email
                        ),
                        key=(
                            f"update_email_"
                            f"{selected_customer_id}"
                        ),
                    )

                with col2:

                    updated_phone = st.text_input(
                        "Phone Number *",
                        value=(
                            selected_customer_obj.phone
                        ),
                        max_chars=10,
                        key=(
                            f"update_phone_"
                            f"{selected_customer_id}"
                        ),
                    )
                    updated_address = st.text_area(
                        "Address",
                        value=(
                            selected_customer_obj.address
                            or ""
                        ),
                        key=(
                            f"update_address_"
                            f"{selected_customer_id}"
                        ),
                    )
                st.warning(
                    "⚠️ If you change the customer's email, "
                    "future transaction OTPs will be sent "
                    "to the new email address."
                )
                if st.button(
                    "💾 Update Customer",
                    use_container_width=True,
                    key="update_customer_button",
                ):
                    result = update_customer(
                        customer_id=selected_customer_id,
                        full_name=updated_full_name,
                        email=updated_email,
                        phone=updated_phone,
                        address=updated_address,
                    )
                    if result["success"]:
                        st.success(result["message"])
                        st.info(
                            "Customer Code: "
                            f"**{result['customer'].customer_code}**"
                        )
                    else:
                        st.error(result["message"])


    # ========================================================
    # BLOCK / UNBLOCK CUSTOMER
    # ========================================================

    with tab4:
        st.subheader("🔒 Customer Block / Unblock")
        customers = get_all_customers()
        if not customers:
            st.info("No customers available.")
        else:
            customer_options = {
                (
                    f"{customer.customer_code} | "
                    f"{customer.full_name} | "
                    f"{customer.email}"
                ): customer.id
                for customer in customers
            }
            selected_customer = st.selectbox(
                "Select Customer",
                options=list(
                    customer_options.keys()
                ),
                key="status_customer_select",
            )

            selected_customer_id = (
                customer_options[
                    selected_customer
                ]
            )

            selected_customer_obj = next(
                (
                    customer
                    for customer in customers
                    if customer.id
                    == selected_customer_id
                ),
                None,
            )

            if selected_customer_obj:

                st.divider()

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        "**Customer Code**"
                    )

                    st.write(
                        selected_customer_obj.customer_code
                    )

                    st.write(
                        "**Full Name**"
                    )

                    st.write(
                        selected_customer_obj.full_name
                    )

                with col2:

                    st.write(
                        "**Email**"
                    )

                    st.write(
                        selected_customer_obj.email
                    )

                    st.write(
                        "**Current Status**"
                    )

                    if selected_customer_obj.is_active:

                        st.success(
                            "🟢 Active"
                        )

                    else:

                        st.error(
                            "🔴 Blocked"
                        )

                st.divider()

                if selected_customer_obj.is_active:

                    st.warning(
                        "Blocking this customer will "
                        "also disable the linked user login."
                    )

                    if st.button(
                        "🔒 Block Customer",
                        type="primary",
                        use_container_width=True,
                        key=(
                            f"block_customer_"
                            f"{selected_customer_id}"
                        ),
                    ):

                        success, message = block_customer(
                            selected_customer_id
                        )

                        if success:

                            st.success(message)

                            st.rerun()

                        else:

                            st.error(message)

                else:

                    st.info(
                        "This customer is currently blocked."
                    )

                    st.warning(
                        "Unblocking this customer will "
                        "also enable the linked user login."
                    )

                    if st.button(
                        "🔓 Unblock Customer",
                        type="primary",
                        use_container_width=True,
                        key=(
                            f"unblock_customer_"
                            f"{selected_customer_id}"
                        ),
                    ):

                        success, message = unblock_customer(
                            selected_customer_id
                        )

                        if success:

                            st.success(message)

                            st.rerun()

                        else:

                            st.error(message)

        # ====================================================
        # DELETE CUSTOMER
        # ====================================================

        st.divider()
        st.subheader("🗑️ Delete Customer")
        st.warning(
            "⚠️ Customer deletion is permanent. "
            "The linked user login, accounts, and "
            "transaction records will also be deleted."
        )
        delete_confirmation = st.checkbox(
            "I understand that this action cannot be undone.",
            key=(
                f"delete_confirmation_"
                f"{selected_customer_id}"
            ),
        )
        if st.button(
            "🗑️ Delete Customer Permanently",
            type="primary",
            use_container_width=True,
            key=(
                f"delete_customer_"
                f"{selected_customer_id}"
            ),
            disabled=not delete_confirmation,
        ):

            success, message = delete_customer(
                selected_customer_id
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

# ============================================================
# ACCOUNT PAGE
# ============================================================

def account_page():
    st.title("🏦 Account Management")
    tab1, tab2 = st.tabs(["➕ Create Account","🔎 View / Search Accounts",])

    # ========================================================
    # CREATE ACCOUNT
    # ========================================================

    with tab1:
        st.subheader("Create New Bank Account")
        customers = get_all_customers()
        if not customers:
            st.warning(
                "No customers available. "
                "Please create a customer first."
            )
            return

        customer_options = {
            (
                f"{customer.customer_code} | "
                f"{customer.full_name} | "
                f"{customer.phone}"
            ): customer.id
            for customer in customers
        }
        selected_customer = st.selectbox(
            "Select Customer *",
            options=list(customer_options.keys()),
        )
        account_type = st.selectbox(
            "Account Type *",
            options=["Savings","Current","Salary",],
        )
        opening_balance = st.number_input(
            "Opening Balance (₹)",
            min_value=0.00,
            max_value=9999999999999.99,
            value=0.00,
            step=100.00,
            format="%.2f",
        )
        st.info(
            "Opening balance will be added to "
            "the account. The transaction record "
            "will be handled by the transaction "
            "module in Step 7."
        )
        create_button = st.button(
            "Create Bank Account",
            use_container_width=True,
        )
        if create_button:
            customer_id = customer_options[selected_customer]
            result = create_account(
                customer_id=customer_id,
                account_type=account_type,
                opening_balance=opening_balance,
            )
            if result["success"]:
                account = result["account"]
                st.success("Bank account created successfully!")
                st.metric("Account Number",account.account_number,)
                st.write(f"Account Type: " f"**{account.account_type}**")
                st.write(f"Opening Balance: " f"**₹ {account.balance:,.2f}**")
            else:
                st.error(result["message"])

    # ========================================================
    # VIEW / SEARCH ACCOUNTS
    # ========================================================

    with tab2:
        st.subheader("Bank Accounts")
        search_term = st.text_input(
            "Search Account",
            placeholder=(
                "Search by account number, "
                "customer code or customer name"
            ),
        )
        accounts = search_accounts(search_term)
        if not accounts:
            st.info("No accounts found.")
            return
        data = []
        for account in accounts:
            customer = account.customer
            data.append(
                {
                    "Account Number": (account.account_number),
                    "Customer Code": (customer.customer_code),
                    "Customer Name": (customer.full_name),
                    "Account Type": (account.account_type),
                    "Balance": (f"₹ {account.balance:,.2f}"),
                    "Status": (account.status),
                    "Created At": (
                        account.created_at
                        .strftime("%d-%m-%Y %H:%M")
                    ),
                }
            )
        dataframe = pd.DataFrame(data)
        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# DASHBOARD PAGE
# ============================================================

def dashboard_page():
    st.markdown(
        """
        <div style="padding: 10px 0 20px 0;">
            <h1 style="
                margin-bottom: 4px;
                font-size: 2.2rem;
            ">
                📊 Banking Dashboard
            </h1>
            <p style="
                color: #6b7280;
                font-size: 1rem;
                margin-top: 0;
            ">
                Overview of customers, accounts, balances and transactions
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # GET DASHBOARD DATA
    # --------------------------------------------------------

    stats = get_dashboard_statistics()

    # --------------------------------------------------------
    # PROFESSIONAL KPI CARDS
    # --------------------------------------------------------

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    def dashboard_kpi_card(title, value, icon):
        st.markdown(
            f"""
            <div style="
                background: var(--background-color);
                border: 1px solid rgba(128, 128, 128, 0.20);
                border-radius: 16px;
                padding: 20px;
                min-height: 125px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            ">
                <div style="
                    font-size: 0.95rem;
                    opacity: 0.75;
                    margin-bottom: 10px;
                ">
                    {icon}&nbsp; {title}
                </div>
                <div style="
                    font-size: 1.75rem;
                    font-weight: 700;
                    line-height: 1.2;
                ">
                    {value}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi1:
        dashboard_kpi_card(
            "Total Customers",
            stats["customers"],
            "👤",
        )
    with kpi2:
        dashboard_kpi_card(
            "Total Accounts",
            stats["accounts"],
            "🏦",
        )
    with kpi3:
        dashboard_kpi_card(
            "Total Bank Balance",
            f"₹ {stats['balance']:,.2f}",
            "💰",
        )
    with kpi4:
        dashboard_kpi_card(
            "Total Transactions",
            stats["transactions"],
            "💳",
        )

    st.markdown("-----")

    # --------------------------------------------------------
    # ACCOUNT STATUS CARDS
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            margin-top: 10px;
            margin-bottom: 14px;
        ">
            <div style="
                font-size: 1.35rem;
                font-weight: 650;
            ">
                🏦 Account Status
            </div>
            <div style="
                font-size: 0.90rem;
                opacity: 0.65;
                margin-top: 3px;
            ">
                Current status of all customer accounts
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    status_col1, status_col2, status_col3 = st.columns(3)

    def account_status_card(title, value, icon):
        st.markdown(
            f"""
            <div style="
                background: var(--background-color);
                border: 1px solid rgba(128, 128, 128, 0.20);
                border-radius: 14px;
                padding: 18px 20px;
                min-height: 105px;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
            ">
                <div style="
                    font-size: 0.92rem;
                    opacity: 0.70;
                    margin-bottom: 8px;
                ">
                    {icon}&nbsp; {title}
                </div>
                <div style="
                    font-size: 1.65rem;
                    font-weight: 700;
                ">
                    {value}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with status_col1:
        account_status_card(
            "Active Accounts",
            stats["active_accounts"],
            "🟢",
        )
    with status_col2:
        account_status_card(
            "Inactive Accounts",
            stats["inactive_accounts"],
            "🟡",
        )
    with status_col3:
        account_status_card(
            "Blocked Accounts",
            stats["blocked_accounts"],
            "🔴",
        )

    st.markdown("-----")

    # --------------------------------------------------------
    # FINANCIAL SUMMARY CARDS
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            margin-top: 10px;
            margin-bottom: 14px;
        ">
            <div style="
                font-size: 1.35rem;
                font-weight: 650;
            ">
                💰 Financial Summary
            </div>
            <div style="
                font-size: 0.90rem;
                opacity: 0.65;
                margin-top: 3px;
            ">
                Overview of banking transaction activity
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    finance_col1, finance_col2, finance_col3, finance_col4 = st.columns(4)

    def financial_card(title, value, icon):
        st.markdown(
            f"""
            <div style="
                background: var(--background-color);
                border: 1px solid rgba(128, 128, 128, 0.20);
                border-radius: 14px;
                padding: 18px 20px;
                min-height: 110px;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
            ">
                <div style="
                    font-size: 0.92rem;
                    opacity: 0.70;
                    margin-bottom: 8px;
                ">
                    {icon}&nbsp; {title}
                </div>
                <div style="
                    font-size: 1.45rem;
                    font-weight: 700;
                    line-height: 1.25;
                ">
                    ₹ {value:,.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with finance_col1:
        financial_card(
            "Deposits",
            float(stats["deposits"]),
            "📥",
        )
    with finance_col2:
        financial_card(
            "Withdrawals",
            float(stats["withdrawals"]),
            "📤",
        )
    with finance_col3:
        financial_card(
            "Transfer In",
            float(stats["transfer_in"]),
            "↗️",
        )
    with finance_col4:
        financial_card(
            "Transfer Out",
            float(stats["transfer_out"]),
            "↘️",
        )

    st.markdown("-----")

    # --------------------------------------------------------
    # PROFESSIONAL CHARTS
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            margin-top: 18px;
            margin-bottom: 14px;
        ">
            <div style="
                font-size: 1.35rem;
                font-weight: 650;
            ">
                📊 Banking Analytics
            </div>
            <div style="
                font-size: 0.90rem;
                opacity: 0.65;
                margin-top: 3px;
            ">
                Visual overview of account distribution and transaction activity
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_col1, chart_col2 = st.columns(2)

    # ========================================================
    # ACCOUNT TYPE CHART
    # ========================================================

    with chart_col1:
        st.markdown(
            """
            <div style="
                font-size: 1.05rem;
                font-weight: 600;
                margin-bottom: 8px;
            ">
                🏦 Account Type Distribution
            </div>
            """,
            unsafe_allow_html=True,
        )
        account_type_data = pd.DataFrame(
            {
                "Account Type": [
                    "Savings",
                    "Current",
                    "Salary",
                ],
                "Accounts": [
                    stats["savings_accounts"],
                    stats["current_accounts"],
                    stats["salary_accounts"],
                ],
            }
        )
        st.bar_chart(
            account_type_data.set_index("Account Type"),
            use_container_width=True,
        )
        st.markdown("-----")


    # ========================================================
    # TRANSACTION SUMMARY CHART
    # ========================================================

    with chart_col2:
        st.markdown(
            """
            <div style="
                font-size: 1.05rem;
                font-weight: 600;
                margin-bottom: 8px;
            ">
                💵 Transaction Summary
            </div>
            """,
            unsafe_allow_html=True,
        )
        transaction_data = pd.DataFrame(
            {
                "Transaction Type": [
                    "Deposits",
                    "Withdrawals",
                    "Transfer In",
                    "Transfer Out",
                ],
                "Amount": [
                    float(stats["deposits"]),
                    float(stats["withdrawals"]),
                    float(stats["transfer_in"]),
                    float(stats["transfer_out"]),
                ],
            }
        )
        st.bar_chart(
            transaction_data.set_index("Transaction Type"),
            use_container_width=True,
        )
        st.markdown("-----")

    # --------------------------------------------------------
    # RECENT TRANSACTIONS
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            margin-top: 22px;
            margin-bottom: 14px;
        ">
            <div style="
                font-size: 1.35rem;
                font-weight: 650;
            ">
                🧾 Recent Transactions
            </div>
            <div style="
                font-size: 0.90rem;
                opacity: 0.65;
                margin-top: 3px;
            ">
                Latest banking activity across customer accounts
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    recent_transactions = get_recent_transactions(10)

    if recent_transactions:
        transaction_data = []
        for transaction in recent_transactions:
            transaction_data.append(
                {
                    "Transaction ID": transaction.transaction_ref,
                    "Type": transaction.transaction_type,
                    "Amount": f"₹ {float(transaction.amount):,.2f}",
                    "Balance After": (
                        f"₹ {float(transaction.balance_after):,.2f}"
                        if transaction.balance_after is not None
                        else "-"
                    ),
                    "Description": (
                        transaction.description
                        if transaction.description
                        else "-"
                    ),
                    "Date": (
                        (transaction.created_at + timedelta(hours=5, minutes=30))
                        .strftime("%d-%m-%Y %I:%M:%S %p")
                    ),
                }
            )
        recent_df = pd.DataFrame(transaction_data)
        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True,
            height=390,
        )
    else:
        st.info("No transactions available yet.")

    st.markdown("------")

    # --------------------------------------------------------
    # QUICK BANKING SUMMARY
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            margin-top: 22px;
            margin-bottom: 14px;
        ">
            <div style="
                font-size: 1.35rem;
                font-weight: 650;
            ">
                📌 Quick Banking Summary
            </div>
            <div style="
                font-size: 0.90rem;
                opacity: 0.65;
                margin-top: 3px;
            ">
                Key highlights from the current banking system
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    summary_col1, summary_col2 = st.columns(2)

    # ========================================================
    # CUSTOMER OVERVIEW CARD
    # ========================================================

    with summary_col1:
        st.markdown(
            f"""
            <div style="
                background: var(--background-color);
                border: 1px solid rgba(128, 128, 128, 0.20);
                border-radius: 16px;
                padding: 20px 22px;
                min-height: 155px;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
            ">
                <div style="
                    font-size: 1.05rem;
                    font-weight: 650;
                    margin-bottom: 14px;
                ">
                    👤 Customer Overview
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    padding: 7px 0;
                    border-bottom: 1px solid rgba(128, 128, 128, 0.12);
                ">
                    <span>Total Customers</span>
                    <strong>{stats["customers"]}</strong>
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    padding: 7px 0;
                    border-bottom: 1px solid rgba(128, 128, 128, 0.12);
                ">
                    <span>Total Accounts</span>
                    <strong>{stats["accounts"]}</strong>
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    padding: 7px 0;
                ">
                    <span>Active Accounts</span>
                    <strong>{stats["active_accounts"]}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # BANKING ACTIVITY CARD
    # ========================================================

    with summary_col2:
        st.markdown(
            f"""
            <div style="
                background: var(--background-color);
                border: 1px solid rgba(128, 128, 128, 0.20);
                border-radius: 16px;
                padding: 20px 22px;
                min-height: 155px;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
            ">
                <div style="
                    font-size: 1.05rem;
                    font-weight: 650;
                    margin-bottom: 14px;
                ">
                    💳 Banking Activity
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    padding: 7px 0;
                    border-bottom: 1px solid rgba(128, 128, 128, 0.12);
                ">
                    <span>Total Transactions</span>
                    <strong>{stats["transactions"]}</strong>
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    padding: 7px 0;
                    border-bottom: 1px solid rgba(128, 128, 128, 0.12);
                ">
                    <span>Total Deposits</span>
                    <strong>₹ {stats["deposits"]:,.2f}</strong>
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    padding: 7px 0;
                ">
                    <span>Total Withdrawals</span>
                    <strong>₹ {stats["withdrawals"]:,.2f}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================
# ACCOUNT STATEMENT PDF
# ============================================================

def generate_account_statement_pdf(
    account,
    transactions,
    start_date,
    end_date,
):
    """
    Generate professional PDF account statement.
    """

    buffer = BytesIO()

    # --------------------------------------------------------
    # PDF DOCUMENT
    # --------------------------------------------------------

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "StatementTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "StatementSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=15,
    )

    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        spaceBefore=8,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )

    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
    )

    # --------------------------------------------------------
    # STORY
    # --------------------------------------------------------

    story = []

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "BANK MANAGEMENT SYSTEM",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Account Statement",
            subtitle_style,
        )
    )

    # --------------------------------------------------------
    # CUSTOMER / ACCOUNT DETAILS
    # --------------------------------------------------------

    customer = account.customer

    customer_name = (
        customer.full_name
        if customer
        else "-"
    )

    customer_code = (
        customer.customer_code
        if customer
        else "-"
    )

    customer_email = (
        customer.email
        if customer
        else "-"
    )

    account_details = [
        [
            Paragraph(
                "<b>Customer Name</b>",
                normal_style,
            ),
            Paragraph(
                customer_name,
                normal_style,
            ),
            Paragraph(
                "<b>Customer Code</b>",
                normal_style,
            ),
            Paragraph(
                customer_code,
                normal_style,
            ),
        ],
        [
            Paragraph(
                "<b>Account Number</b>",
                normal_style,
            ),
            Paragraph(
                account.account_number,
                normal_style,
            ),
            Paragraph(
                "<b>Account Type</b>",
                normal_style,
            ),
            Paragraph(
                account.account_type,
                normal_style,
            ),
        ],
        [
            Paragraph(
                "<b>Account Status</b>",
                normal_style,
            ),
            Paragraph(
                account.status,
                normal_style,
            ),
            Paragraph(
                "<b>Email</b>",
                normal_style,
            ),
            Paragraph(
                customer_email,
                normal_style,
            ),
        ],
        [
            Paragraph(
                "<b>Statement Period</b>",
                normal_style,
            ),
            Paragraph(
                (
                    f"{start_date.strftime('%d-%m-%Y')}"
                    f" to "
                    f"{end_date.strftime('%d-%m-%Y')}"
                ),
                normal_style,
            ),
            Paragraph(
                "<b>Generated On</b>",
                normal_style,
            ),
            Paragraph(
                datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                ),
                normal_style,
            ),
        ],
    ]

    details_table = Table(
        account_details,
        colWidths=[
            32 * mm,
            58 * mm,
            32 * mm,
            58 * mm,
        ],
    )

    details_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.whitesmoke,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(details_table)

    story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # TRANSACTION CALCULATIONS
    # --------------------------------------------------------

    total_credit = 0.0
    total_debit = 0.0

    statement_transactions = []

    for transaction in transactions:

        transaction_date = (
            transaction.created_at
            + timedelta(hours=5, minutes=30)
        )

        # Only include requested period
        if (
            transaction_date.date()
            < start_date
        ):
            continue

        if (
            transaction_date.date()
            > end_date
        ):
            continue

        amount = float(
            transaction.amount
        )

        transaction_type = (
            transaction.transaction_type.upper()
        )

        if transaction_type in [
            "DEPOSIT",
            "TRANSFER_IN",
        ]:

            credit = amount
            debit = 0.0

            total_credit += amount

        elif transaction_type in [
            "WITHDRAWAL",
            "TRANSFER_OUT",
        ]:

            credit = 0.0
            debit = amount

            total_debit += amount

        else:

            credit = 0.0
            debit = 0.0

        statement_transactions.append(
            {
                "transaction": transaction,
                "date": transaction_date,
                "credit": credit,
                "debit": debit,
            }
        )

    # --------------------------------------------------------
    # OPENING BALANCE
    # --------------------------------------------------------

    opening_balance = 0.0

    previous_transactions = []

    for transaction in transactions:

        transaction_date = (
            transaction.created_at
            + timedelta(hours=5, minutes=30)
        )

        if transaction_date.date() < start_date:
            previous_transactions.append(
                transaction
            )

    if previous_transactions:

        previous_transactions.sort(
            key=lambda x: x.created_at
        )

        last_previous_transaction = (
            previous_transactions[-1]
        )

        if (
            last_previous_transaction.balance_after
            is not None
        ):
            opening_balance = float(
                last_previous_transaction.balance_after
            )

    else:

        # If there are no previous transactions,
        # calculate opening balance from current balance.

        current_balance = float(
            account.balance
        )

        opening_balance = (
            current_balance
            - total_credit
            + total_debit
        )

    # --------------------------------------------------------
    # CLOSING BALANCE
    # --------------------------------------------------------

    closing_balance = (
        opening_balance
        + total_credit
        - total_debit
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Statement Summary",
            section_style,
        )
    )

    summary_data = [
        [
            Paragraph(
                "<b>Opening Balance</b>",
                normal_style,
            ),
            Paragraph(
                f"₹ {opening_balance:,.2f}",
                normal_style,
            ),
            Paragraph(
                "<b>Total Credits</b>",
                normal_style,
            ),
            Paragraph(
                f"₹ {total_credit:,.2f}",
                normal_style,
            ),
        ],
        [
            Paragraph(
                "<b>Total Debits</b>",
                normal_style,
            ),
            Paragraph(
                f"₹ {total_debit:,.2f}",
                normal_style,
            ),
            Paragraph(
                "<b>Closing Balance</b>",
                normal_style,
            ),
            Paragraph(
                f"₹ {closing_balance:,.2f}",
                normal_style,
            ),
        ],
        [
            Paragraph(
                "<b>Total Transactions</b>",
                normal_style,
            ),
            Paragraph(
                str(
                    len(statement_transactions)
                ),
                normal_style,
            ),
            Paragraph(
                "<b>Statement Period</b>",
                normal_style,
            ),
            Paragraph(
                (
                    f"{start_date.strftime('%d-%m-%Y')}"
                    f" - "
                    f"{end_date.strftime('%d-%m-%Y')}"
                ),
                normal_style,
            ),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            37 * mm,
            55 * mm,
            37 * mm,
            51 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F5F7FA"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(summary_table)

    story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # TRANSACTION TABLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Transaction Details",
            section_style,
        )
    )

    transaction_data = [
        [
            Paragraph(
                "<b>Date & Time</b>",
                small_style,
            ),
            Paragraph(
                "<b>Transaction ID</b>",
                small_style,
            ),
            Paragraph(
                "<b>Type</b>",
                small_style,
            ),
            Paragraph(
                "<b>Description</b>",
                small_style,
            ),
            Paragraph(
                "<b>Debit</b>",
                small_style,
            ),
            Paragraph(
                "<b>Credit</b>",
                small_style,
            ),
            Paragraph(
                "<b>Balance</b>",
                small_style,
            ),
        ]
    ]

    for item in statement_transactions:

        transaction = item["transaction"]

        transaction_data.append(
            [
                Paragraph(
                    item["date"].strftime(
                        "%d-%m-%Y<br/>%I:%M %p"
                    ),
                    small_style,
                ),
                Paragraph(
                    str(
                        transaction.transaction_ref
                    ),
                    small_style,
                ),
                Paragraph(
                    transaction.transaction_type,
                    small_style,
                ),
                Paragraph(
                    transaction.description
                    or "-",
                    small_style,
                ),
                Paragraph(
                    (
                        f"₹ {item['debit']:,.2f}"
                        if item["debit"] > 0
                        else "-"
                    ),
                    small_style,
                ),
                Paragraph(
                    (
                        f"₹ {item['credit']:,.2f}"
                        if item["credit"] > 0
                        else "-"
                    ),
                    small_style,
                ),
                Paragraph(
                    (
                        f"₹ "
                        f"{float(transaction.balance_after):,.2f}"
                        if transaction.balance_after
                        is not None
                        else "-"
                    ),
                    small_style,
                ),
            ]
        )

    if len(transaction_data) == 1:

        transaction_data.append(
            [
                Paragraph(
                    "-",
                    small_style,
                ),
                Paragraph(
                    "-",
                    small_style,
                ),
                Paragraph(
                    "No transactions",
                    small_style,
                ),
                Paragraph(
                    "-",
                    small_style,
                ),
                Paragraph(
                    "-",
                    small_style,
                ),
                Paragraph(
                    "-",
                    small_style,
                ),
                Paragraph(
                    "-",
                    small_style,
                ),
            ]
        )

    transaction_table = Table(
        transaction_data,
        colWidths=[
            25 * mm,
            31 * mm,
            25 * mm,
            39 * mm,
            23 * mm,
            23 * mm,
            27 * mm,
        ],
        repeatRows=1,
    )

    transaction_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#E9EEF5"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(transaction_table)

    story.append(Spacer(1, 18))

    # --------------------------------------------------------
    # FOOTER NOTE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            (
                "<b>Note:</b> This is a system-generated "
                "account statement. Please verify the "
                "transaction details and contact the bank "
                "administrator in case of any discrepancy."
            ),
            small_style,
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "Bank Management System",
            subtitle_style,
        )
    )

    # --------------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------------

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# TRANSACTION PAGE
# ============================================================

def transaction_page():

    st.title("💰 Transaction Management")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "💵 Deposit",
            "💸 Withdrawal",
            "🔄 Transfer",
            "📜 Transaction History",
            "📄 Account Statement",
        ]
    )

    # ========================================================
    # GET ACTIVE ACCOUNTS
    # ========================================================

    accounts = get_active_accounts()

    if not accounts:
        st.warning(
            "No active accounts available."
        )
        return

    account_options = {
        (
            f"{account.account_number} | "
            f"{account.customer.full_name}"
        ): account.id
        for account in accounts
    }

    # ========================================================
    # DEPOSIT
    # ========================================================

    with tab1:

        st.subheader("Deposit Money")

        selected_account = st.selectbox(
            "Select Account",
            options=list(account_options.keys()),
            key="deposit_account",
        )

        selected_account_obj = next(
            (
                account
                for account in accounts
                if account.id
                == account_options[selected_account]
            ),
            None,
        )

        amount = st.number_input(
            "Deposit Amount (₹)",
            min_value=0.00,
            value=0.00,
            step=100.00,
            format="%.2f",
            key="deposit_amount",
        )

        description = st.text_input(
            "Description",
            value="Cash deposit",
            key="deposit_description",
        )

        # ----------------------------------------------------
        # SEND OTP
        # ----------------------------------------------------

        if st.button(
            "📧 Send OTP",
            use_container_width=True,
            key="deposit_send_otp",
        ):

            if amount <= 0:

                st.error(
                    "Please enter a valid deposit amount."
                )

            elif selected_account_obj is None:

                st.error(
                    "Unable to identify selected account."
                )

            else:

                result = send_transaction_otp(
                    customer_id=(
                        selected_account_obj.customer.id
                    ),
                    account_id=(
                        selected_account_obj.id
                    ),
                    amount=amount,
                    purpose="DEPOSIT",
                )

                if result["success"]:

                    st.session_state[
                        "deposit_otp_id"
                    ] = result["otp_id"]

                    st.session_state[
                        "deposit_otp_active"
                    ] = True

                    st.success(
                        result["message"]
                    )

                else:

                    st.error(
                        result["message"]
                    )

        # ----------------------------------------------------
        # OTP VERIFICATION
        # ----------------------------------------------------

        if st.session_state.get(
            "deposit_otp_active",
            False,
        ):

            st.info(
                "🔐 OTP has been sent to the "
                "customer's registered email. "
                "Enter the OTP to continue."
            )

            otp = st.text_input(
                "Enter 6-Digit OTP",
                max_chars=6,
                type="password",
                key="deposit_otp_input",
            )

            if st.button(
                "✅ Verify OTP & Deposit",
                use_container_width=True,
                key="deposit_verify_otp",
            ):

                otp_result = verify_transaction_otp(
                    otp_id=st.session_state[
                        "deposit_otp_id"
                    ],
                    entered_otp=otp,
                )

                if otp_result["success"]:

                    # ------------------------------------------------
                    # IMPORTANT:
                    # Use transaction details returned by the
                    # verified OTP, not fresh UI values.
                    # ------------------------------------------------

                    transaction_result = deposit_money(
                        account_id=otp_result[
                            "account_id"
                        ],
                        amount=otp_result[
                            "amount"
                        ],
                        description=description,
                    )

                    if transaction_result["success"]:

                        st.session_state[
                            "deposit_otp_active"
                        ] = False

                        st.session_state.pop(
                            "deposit_otp_id",
                            None,
                        )

                        st.success(
                            transaction_result["message"]
                        )

                        st.info(
                            "Transaction ID: "
                            f"**{transaction_result['transaction_id']}**"
                        )

                        st.metric(
                            "New Balance",
                            (
                                f"₹ "
                                f"{transaction_result['new_balance']:,.2f}"
                            ),
                        )

                    else:

                        st.error(
                            transaction_result["message"]
                        )

                else:

                    st.error(
                        otp_result["message"]
                    )

    # ========================================================
    # WITHDRAWAL
    # ========================================================

    with tab2:

        st.subheader("Withdraw Money")

        selected_account = st.selectbox(
            "Select Account",
            options=list(account_options.keys()),
            key="withdraw_account",
        )

        selected_account_obj = next(
            (
                account
                for account in accounts
                if account.id
                == account_options[selected_account]
            ),
            None,
        )

        amount = st.number_input(
            "Withdrawal Amount (₹)",
            min_value=0.00,
            value=0.00,
            step=100.00,
            format="%.2f",
            key="withdraw_amount",
        )

        description = st.text_input(
            "Description",
            value="Cash withdrawal",
            key="withdraw_description",
        )

        # ----------------------------------------------------
        # SEND OTP
        # ----------------------------------------------------

        if st.button(
            "📧 Send OTP",
            use_container_width=True,
            key="withdraw_send_otp",
        ):

            if amount <= 0:

                st.error(
                    "Please enter a valid withdrawal amount."
                )

            elif selected_account_obj is None:

                st.error(
                    "Unable to identify selected account."
                )

            else:

                result = send_transaction_otp(
                    customer_id=(
                        selected_account_obj.customer.id
                    ),
                    account_id=(
                        selected_account_obj.id
                    ),
                    amount=amount,
                    purpose="WITHDRAWAL",
                )

                if result["success"]:

                    st.session_state[
                        "withdraw_otp_id"
                    ] = result["otp_id"]

                    st.session_state[
                        "withdraw_otp_active"
                    ] = True

                    st.success(
                        result["message"]
                    )

                else:

                    st.error(
                        result["message"]
                    )

        # ----------------------------------------------------
        # OTP VERIFICATION
        # ----------------------------------------------------

        if st.session_state.get(
            "withdraw_otp_active",
            False,
        ):

            st.info(
                "🔐 OTP has been sent to the "
                "customer's registered email. "
                "Enter the OTP to continue."
            )

            otp = st.text_input(
                "Enter 6-Digit OTP",
                max_chars=6,
                type="password",
                key="withdraw_otp_input",
            )

            if st.button(
                "✅ Verify OTP & Withdraw",
                use_container_width=True,
                key="withdraw_verify_otp",
            ):

                otp_result = verify_transaction_otp(
                    otp_id=st.session_state[
                        "withdraw_otp_id"
                    ],
                    entered_otp=otp,
                )

                if otp_result["success"]:

                    transaction_result = withdraw_money(
                        account_id=otp_result[
                            "account_id"
                        ],
                        amount=otp_result[
                            "amount"
                        ],
                        description=description,
                    )

                    if transaction_result["success"]:

                        st.session_state[
                            "withdraw_otp_active"
                        ] = False

                        st.session_state.pop(
                            "withdraw_otp_id",
                            None,
                        )

                        st.success(
                            transaction_result["message"]
                        )

                        st.info(
                            "Transaction ID: "
                            f"**{transaction_result['transaction_id']}**"
                        )

                        st.metric(
                            "New Balance",
                            (
                                f"₹ "
                                f"{transaction_result['new_balance']:,.2f}"
                            ),
                        )

                    else:

                        st.error(
                            transaction_result["message"]
                        )

                else:

                    st.error(
                        otp_result["message"]
                    )

    # ========================================================
    # TRANSFER
    # ========================================================

    with tab3:

        st.subheader("Transfer Money")

        source_account = st.selectbox(
            "From Account",
            options=list(account_options.keys()),
            key="source_account",
        )

        destination_account = st.selectbox(
            "To Account",
            options=list(account_options.keys()),
            key="destination_account",
        )

        amount = st.number_input(
            "Transfer Amount (₹)",
            min_value=0.00,
            value=0.00,
            step=100.00,
            format="%.2f",
            key="transfer_amount",
        )

        description = st.text_input(
            "Transfer Description",
            value="Account transfer",
            key="transfer_description",
        )

        source_account_obj = next(
            (
                account
                for account in accounts
                if account.id
                == account_options[source_account]
            ),
            None,
        )

        destination_account_obj = next(
            (
                account
                for account in accounts
                if account.id
                == account_options[destination_account]
            ),
            None,
        )

        # ----------------------------------------------------
        # SEND OTP
        # ----------------------------------------------------

        if st.button(
            "📧 Send OTP",
            use_container_width=True,
            key="transfer_send_otp",
        ):

            source_id = account_options[
                source_account
            ]

            destination_id = account_options[
                destination_account
            ]

            if source_id == destination_id:

                st.error(
                    "Source and destination accounts "
                    "cannot be the same."
                )

            elif amount <= 0:

                st.error(
                    "Please enter a valid transfer amount."
                )

            elif source_account_obj is None:

                st.error(
                    "Unable to identify source account."
                )

            else:

                result = send_transaction_otp(
                    customer_id=(
                        source_account_obj.customer.id
                    ),
                    account_id=source_id,
                    reference_account_id=destination_id,
                    amount=amount,
                    purpose="TRANSFER",
                )

                if result["success"]:

                    st.session_state[
                        "transfer_otp_id"
                    ] = result["otp_id"]

                    st.session_state[
                        "transfer_otp_active"
                    ] = True

                    st.success(
                        result["message"]
                    )

                else:

                    st.error(
                        result["message"]
                    )

        # ----------------------------------------------------
        # OTP VERIFICATION
        # ----------------------------------------------------

        if st.session_state.get(
            "transfer_otp_active",
            False,
        ):

            st.info(
                "🔐 OTP has been sent to the "
                "source account holder's registered email. "
                "Enter the OTP to continue."
            )

            otp = st.text_input(
                "Enter 6-Digit OTP",
                max_chars=6,
                type="password",
                key="transfer_otp_input",
            )

            if st.button(
                "✅ Verify OTP & Transfer",
                use_container_width=True,
                key="transfer_verify_otp",
            ):

                otp_result = verify_transaction_otp(
                    otp_id=st.session_state[
                        "transfer_otp_id"
                    ],
                    entered_otp=otp,
                )

                if otp_result["success"]:

                    transaction_result = transfer_money(
                        source_account_id=otp_result[
                            "account_id"
                        ],
                        destination_account_id=otp_result[
                            "reference_account_id"
                        ],
                        amount=otp_result[
                            "amount"
                        ],
                        description=description,
                    )

                    if transaction_result["success"]:

                        st.session_state[
                            "transfer_otp_active"
                        ] = False

                        st.session_state.pop(
                            "transfer_otp_id",
                            None,
                        )

                        st.success(
                            transaction_result["message"]
                        )

                        st.info(
                            "Transfer Out ID: "
                            f"**{transaction_result['transfer_out_id']}**"
                        )

                        st.info(
                            "Transfer In ID: "
                            f"**{transaction_result['transfer_in_id']}**"
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            st.metric(
                                "Source Balance",
                                (
                                    f"₹ "
                                    f"{transaction_result['source_balance']:,.2f}"
                                ),
                            )

                        with col2:

                            st.metric(
                                "Destination Balance",
                                (
                                    f"₹ "
                                    f"{transaction_result['destination_balance']:,.2f}"
                                ),
                            )

                    else:

                        st.error(
                            transaction_result["message"]
                        )

                else:

                    st.error(
                        otp_result["message"]
                    )

    # ========================================================
    # TRANSACTION HISTORY
    # ========================================================

    with tab4:

        st.subheader(
            "Transaction History"
        )

        selected_account = st.selectbox(
            "Select Account",
            options=list(account_options.keys()),
            key="history_account",
        )

        account_id = account_options[
            selected_account
        ]

        transactions = (
            get_account_transactions(
                account_id
            )
        )

        if not transactions:

            st.info(
                "No transactions found."
            )

        else:

            data = []

            for transaction in transactions:

                data.append(
                    {
                        "Transaction ID": (
                            transaction.transaction_ref
                        ),
                        "Type": (
                            transaction.transaction_type
                        ),
                        "Amount": (
                            f"₹ {transaction.amount:,.2f}"
                        ),
                        "Balance After": (
                            f"₹ "
                            f"{transaction.balance_after:,.2f}"
                        ),
                        "Description": (
                            transaction.description
                            or "-"
                        ),
                        "Date": (
                            (transaction.created_at + timedelta(hours=5, minutes=30))
                            .strftime("%d-%m-%Y %I:%M:%S %p")
                        ),
                    }
                )

            dataframe = pd.DataFrame(
                data
            )

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )

        # ========================================================
    # ACCOUNT STATEMENT
    # ========================================================

    with tab5:

        st.subheader(
            "📄 Account Statement"
        )

        st.info(
            "Generate and download a PDF statement "
            "for the selected account and date range."
        )

        # ----------------------------------------------------
        # ACCOUNT SELECTION
        # ----------------------------------------------------

        statement_account = st.selectbox(
            "Select Account",
            options=list(account_options.keys()),
            key="statement_account",
        )

        statement_account_id = (
            account_options[
                statement_account
            ]
        )

        statement_account_obj = next(
            (
                account
                for account in accounts
                if account.id
                == statement_account_id
            ),
            None,
        )

        # ----------------------------------------------------
        # DATE RANGE
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            start_date = st.date_input(
                "Start Date",
                value=(
                    datetime.now().date()
                    - timedelta(days=30)
                ),
                key="statement_start_date",
            )

        with col2:

            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                key="statement_end_date",
            )

        # ----------------------------------------------------
        # DATE VALIDATION
        # ----------------------------------------------------

        if start_date > end_date:

            st.error(
                "Start date cannot be later than end date."
            )

        elif statement_account_obj is None:

            st.error(
                "Unable to identify selected account."
            )

        else:

            # ------------------------------------------------
            # GET TRANSACTIONS
            # ------------------------------------------------

            statement_transactions = (
                get_account_transactions(
                    statement_account_id
                )
            )

            # ------------------------------------------------
            # FILTER TRANSACTIONS FOR DISPLAY
            # ------------------------------------------------

            filtered_transactions = []

            for transaction in (
                statement_transactions
            ):

                transaction_date = (
                    transaction.created_at
                    + timedelta(
                        hours=5,
                        minutes=30,
                    )
                ).date()

                if (
                    start_date
                    <= transaction_date
                    <= end_date
                ):

                    filtered_transactions.append(
                        transaction
                    )

            # ------------------------------------------------
            # PREVIEW
            # ------------------------------------------------

            st.markdown(
                "### 📊 Statement Preview"
            )

            preview_data = []

            for transaction in (
                filtered_transactions
            ):

                transaction_type = (
                    transaction.transaction_type.upper()
                )

                amount = float(
                    transaction.amount
                )

                if transaction_type in [
                    "DEPOSIT",
                    "TRANSFER_IN",
                ]:

                    credit = (
                        f"₹ {amount:,.2f}"
                    )

                    debit = "-"

                elif transaction_type in [
                    "WITHDRAWAL",
                    "TRANSFER_OUT",
                ]:

                    debit = (
                        f"₹ {amount:,.2f}"
                    )

                    credit = "-"

                else:

                    debit = "-"
                    credit = "-"

                preview_data.append(
                    {
                        "Date": (
                            (
                                transaction.created_at
                                + timedelta(
                                    hours=5,
                                    minutes=30,
                                )
                            ).strftime(
                                "%d-%m-%Y %I:%M %p"
                            )
                        ),
                        "Transaction ID": (
                            transaction.transaction_ref
                        ),
                        "Type": (
                            transaction.transaction_type
                        ),
                        "Description": (
                            transaction.description
                            or "-"
                        ),
                        "Debit": debit,
                        "Credit": credit,
                        "Balance": (
                            f"₹ "
                            f"{float(transaction.balance_after):,.2f}"
                            if transaction.balance_after
                            is not None
                            else "-"
                        ),
                    }
                )

            if preview_data:

                preview_df = pd.DataFrame(
                    preview_data
                )

                st.dataframe(
                    preview_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No transactions found for "
                    "the selected date range."
                )

            # ------------------------------------------------
            # GENERATE PDF
            # ------------------------------------------------

            pdf_data = (
                generate_account_statement_pdf(
                    account=statement_account_obj,
                    transactions=statement_transactions,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            # ------------------------------------------------
            # DOWNLOAD BUTTON
            # ------------------------------------------------

            account_number = (
                statement_account_obj.account_number
            )

            filename = (
                f"Account_Statement_"
                f"{account_number}_"
                f"{start_date.strftime('%d-%m-%Y')}_"
                f"{end_date.strftime('%d-%m-%Y')}.pdf"
            )

            st.download_button(
                label="📥 Download Account Statement PDF",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )

# ============================================================
# USER BANKING PAGE
# ============================================================

def user_banking_page():

    customer_id = st.session_state.get("customer_id")
    # ========================================================
    # MY PROFILE
    # ========================================================

    from services import get_customer_profile
    customer = get_customer_profile(customer_id)
    if not customer:
        st.error("Customer profile could not be found.")
        return
    if not customer_id:
        st.error("Customer profile could not be identified.")
        return

    # --------------------------------------------------------
    # IMPORT USER-SPECIFIC SERVICES
    # --------------------------------------------------------

    from services import (
        get_customer_active_accounts,
        get_customer_account_transactions,
    )

    # --------------------------------------------------------
    # GET ONLY LOGGED-IN USER ACCOUNTS
    # --------------------------------------------------------

    accounts = get_customer_active_accounts(
        customer_id
    )

    if not accounts:

        st.title("💰 My Banking")

        st.info(
            "No active bank accounts are linked "
            "to your profile yet."
        )

        return

    # --------------------------------------------------------
    # ACCOUNT OPTIONS
    # --------------------------------------------------------

    account_options = {
        (
            f"{account.account_number} | "
            f"{account.account_type} | "
            f"₹ {float(account.balance):,.2f}"
        ): account.id
        for account in accounts
    }

    # --------------------------------------------------------
    # PAGE HEADER
    # --------------------------------------------------------

    st.title("💰 My Banking")
    st.caption("Manage your own bank accounts and transactions.")

    # --------------------------------------------------------
    # MY ACCOUNTS
    # --------------------------------------------------------

    st.subheader("🏦 My Accounts")

    # ========================================================
    # ACCOUNT CARD STYLING
    # ========================================================

    st.markdown(
        """
        <style>
        .account-card {
            background: linear-gradient(
                145deg,
                #171922,
                #101116
            );
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 18px;
            padding: 24px 26px;
            margin: 12px 0 20px 0;
            box-shadow:
                0 8px 25px rgba(0,0,0,0.20);
        }
        .account-name {
            font-size: 1.75rem;
            font-weight: 800;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            color: #ffffff;
            margin-bottom: 22px;
        }
        .account-label {
            font-size: 0.82rem;
            color: #9ca3af;
            margin-bottom: 4px;
            font-weight: 500;
        }
        .account-value {
            font-size: 1.15rem;
            font-weight: 650;
            color: #f3f4f6;
            margin-bottom: 15px;
        }
        .account-type {
            font-size: 1.35rem;
            font-weight: 750;
            color: #ffffff;
            margin-bottom: 15px;
        }
        .account-balance {
            font-size: 1.45rem;
            font-weight: 750;
            color: #ffffff;
            margin-bottom: 15px;
        }
        .account-status {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 700;
            background: rgba(34,197,94,0.14);
            color: #4ade80;
            border: 1px solid rgba(34,197,94,0.30);
            margin-bottom: 15px;
        }
        .account-date {
            font-size: 1rem;
            font-weight: 600;
            color: #e5e7eb;
            margin-bottom: 3px;
        }
        .account-time {
            font-size: 0.88rem;
            color: #9ca3af;
        }
        .account-divider {
            height: 1px;
            background: rgba(255,255,255,0.08);
            margin: 5px 0 20px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


    # ========================================================
    # DISPLAY EACH ACCOUNT
    # ========================================================

    for account in accounts:

        # ----------------------------------------------------
        # ACCOUNT NUMBER VISIBILITY
        # ----------------------------------------------------

        visibility_key = (f"show_account_number_{account.id}")
        if visibility_key not in st.session_state:
            st.session_state[visibility_key] = False

        # ----------------------------------------------------
        # ACCOUNT NUMBER
        # ----------------------------------------------------

        account_number = str(account.account_number)
        if st.session_state[visibility_key]:
            displayed_account_number = (account_number)

        else:

            # Show only last 4 digits
            if len(account_number) > 4:

                displayed_account_number = (
                    "•••• •••• •••• "
                    + account_number[-4:]
                )
            else:
                displayed_account_number = ("••••")

        # ----------------------------------------------------
        # DATE & TIME
        # ----------------------------------------------------

        created_date = account.created_at.strftime("%d %B %Y")
        created_time = account.created_at.strftime("%I:%M %p")

        # ----------------------------------------------------
        # ACCOUNT CARD
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div class="account-card">
                <div class="account-name">
                    {customer.full_name.upper()}
                </div>
                <div class="account-divider"></div>
                <div class="account-label">
                    ACCOUNT NUMBER
                </div>
                <div class="account-value">
                    {displayed_account_number}
                </div>
                <div class="account-label">
                    ACCOUNT TYPE
                </div>
                <div class="account-type">
                    {account.account_type}
                </div>
                <div class="account-label">
                    BALANCE
                </div>
                <div class="account-balance">
                    ₹ {float(account.balance):,.2f}
                </div>
                <div class="account-label">
                    STATUS
                </div>
                <div class="account-status">
                    ● {account.status}
                </div>
                <div class="account-label">
                    CREATED AT
                </div>
                <div class="account-date">
                    📅 {created_date}
                </div>
                <div class="account-time">
                    🕒 {created_time}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


        # ----------------------------------------------------
        # EYE BUTTON
        # ----------------------------------------------------

        button_col1, button_col2 = st.columns(
            [5.2, 1]
        )

        with button_col1:
            pass

        with button_col2:

            if st.button(
                (
                    "🙈 Hide"
                    if st.session_state[
                        visibility_key
                    ]
                    else "👁 View"
                ),
                key=(
                    f"toggle_account_"
                    f"{account.id}"
                ),
                use_container_width=True,
            ):

                st.session_state[
                    visibility_key
                ] = not st.session_state[
                    visibility_key
                ]

                st.rerun()

    # --------------------------------------------------------
    # DIVIDER
    # --------------------------------------------------------

    st.markdown("---")

    # --------------------------------------------------------
    # TABS
    # --------------------------------------------------------

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "👤 My Profile",
            "💵 Deposit",
            "💸 Withdrawal",
            "🔄 Transfer",
            "📜 Transaction History",
            "📄 Account Statement",
        ]
    )

    with tab1:
        st.subheader("👤 My Profile")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Customer Code**")
            st.info(customer.customer_code)

            st.write("**Full Name**")
            st.info(customer.full_name)

            st.write("**Email**")
            st.info(customer.email)

        with col2:
            st.write("**Phone**")
            st.info(customer.phone)

            st.write("**Address**")
            st.info(customer.address)

            st.write("**Customer ID**")
            st.info(str(customer.id))

        st.divider()
        st.subheader("🔐 Change Password")
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password",type="password")
            new_password = st.text_input("New Password",type="password")
            confirm_password = st.text_input("Confirm New Password",type="password")
            change_password_button = st.form_submit_button("🔑 Change Password",use_container_width=True)
            if change_password_button:
                if not current_password:
                    st.warning("Please enter your current password.")
                elif not new_password:
                    st.warning("Please enter a new password.")
                elif not confirm_password:
                    st.warning("Please confirm your new password.")
                elif new_password != confirm_password:
                    st.error("New password and confirm password do not match.")
                else:
                    from auth import change_user_password
                    result = change_user_password(
                        user_id=st.session_state.get("user_id"),
                        current_password=current_password,
                        new_password=new_password,
                    )
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])

    # ========================================================
    # DEPOSIT
    # ========================================================

    with tab2:

        st.subheader("💵 Deposit Money")

        selected_account = st.selectbox(
            "Select Your Account",
            options=list(account_options.keys()),
            key="user_deposit_account",
        )

        selected_account_id = account_options[
            selected_account
        ]

        selected_account_obj = next(
            (
                account
                for account in accounts
                if account.id == selected_account_id
            ),
            None,
        )

        amount = st.number_input(
            "Deposit Amount (₹)",
            min_value=0.00,
            value=0.00,
            step=100.00,
            format="%.2f",
            key="user_deposit_amount",
        )

        description = st.text_input(
            "Description",
            value="Cash deposit",
            key="user_deposit_description",
        )

        if st.button(
            "📧 Send OTP",
            use_container_width=True,
            key="user_deposit_send_otp",
        ):

            if amount <= 0:

                st.error(
                    "Please enter a valid deposit amount."
                )

            elif selected_account_obj is None:

                st.error(
                    "Unable to identify your account."
                )

            else:

                result = send_transaction_otp(
                    customer_id=customer_id,
                    account_id=selected_account_id,
                    amount=amount,
                    purpose="DEPOSIT",
                )

                if result["success"]:

                    st.session_state[
                        "user_deposit_otp_id"
                    ] = result["otp_id"]

                    st.session_state[
                        "user_deposit_otp_active"
                    ] = True

                    st.success(
                        result["message"]
                    )

                else:

                    st.error(
                        result["message"]
                    )

        if st.session_state.get(
            "user_deposit_otp_active",
            False,
        ):

            st.info(
                "🔐 OTP has been sent to your "
                "registered email address."
            )

            otp = st.text_input(
                "Enter 6-Digit OTP",
                max_chars=6,
                type="password",
                key="user_deposit_otp_input",
            )

            if st.button(
                "✅ Verify OTP & Deposit",
                use_container_width=True,
                key="user_deposit_verify_otp",
            ):

                otp_result = verify_transaction_otp(
                    otp_id=st.session_state[
                        "user_deposit_otp_id"
                    ],
                    entered_otp=otp,
                )

                if otp_result["success"]:

                    transaction_result = deposit_money(
                        account_id=otp_result[
                            "account_id"
                        ],
                        amount=otp_result[
                            "amount"
                        ],
                        description=description,
                        customer_id=customer_id,
                    )

                    if transaction_result["success"]:

                        st.session_state[
                            "user_deposit_otp_active"
                        ] = False

                        st.session_state.pop(
                            "user_deposit_otp_id",
                            None,
                        )

                        st.success(
                            transaction_result["message"]
                        )

                        st.info(
                            "Transaction ID: "
                            f"**{transaction_result['transaction_id']}**"
                        )

                        st.metric(
                            "New Balance",
                            (
                                f"₹ "
                                f"{transaction_result['new_balance']:,.2f}"
                            ),
                        )

                    else:

                        st.error(
                            transaction_result["message"]
                        )

                else:

                    st.error(
                        otp_result["message"]
                    )

    # ========================================================
    # WITHDRAWAL
    # ========================================================

    with tab3:

        st.subheader("💸 Withdraw Money")

        selected_account = st.selectbox(
            "Select Your Account",
            options=list(account_options.keys()),
            key="user_withdraw_account",
        )

        selected_account_id = account_options[
            selected_account
        ]

        selected_account_obj = next(
            (
                account
                for account in accounts
                if account.id == selected_account_id
            ),
            None,
        )

        amount = st.number_input(
            "Withdrawal Amount (₹)",
            min_value=0.00,
            value=0.00,
            step=100.00,
            format="%.2f",
            key="user_withdraw_amount",
        )

        description = st.text_input(
            "Description",
            value="Cash withdrawal",
            key="user_withdraw_description",
        )

        if st.button(
            "📧 Send OTP",
            use_container_width=True,
            key="user_withdraw_send_otp",
        ):

            if amount <= 0:

                st.error(
                    "Please enter a valid withdrawal amount."
                )

            elif selected_account_obj is None:

                st.error(
                    "Unable to identify your account."
                )

            else:

                result = send_transaction_otp(
                    customer_id=customer_id,
                    account_id=selected_account_id,
                    amount=amount,
                    purpose="WITHDRAWAL",
                )

                if result["success"]:

                    st.session_state[
                        "user_withdraw_otp_id"
                    ] = result["otp_id"]

                    st.session_state[
                        "user_withdraw_otp_active"
                    ] = True

                    st.success(
                        result["message"]
                    )

                else:

                    st.error(
                        result["message"]
                    )

        if st.session_state.get(
            "user_withdraw_otp_active",
            False,
        ):

            st.info(
                "🔐 OTP has been sent to your "
                "registered email address."
            )

            otp = st.text_input(
                "Enter 6-Digit OTP",
                max_chars=6,
                type="password",
                key="user_withdraw_otp_input",
            )

            if st.button(
                "✅ Verify OTP & Withdraw",
                use_container_width=True,
                key="user_withdraw_verify_otp",
            ):

                otp_result = verify_transaction_otp(
                    otp_id=st.session_state[
                        "user_withdraw_otp_id"
                    ],
                    entered_otp=otp,
                )

                if otp_result["success"]:

                    transaction_result = withdraw_money(
                        account_id=otp_result[
                            "account_id"
                        ],
                        amount=otp_result[
                            "amount"
                        ],
                        description=description,
                        customer_id=customer_id,
                    )

                    if transaction_result["success"]:

                        st.session_state[
                            "user_withdraw_otp_active"
                        ] = False

                        st.session_state.pop(
                            "user_withdraw_otp_id",
                            None,
                        )

                        st.success(
                            transaction_result["message"]
                        )

                        st.info(
                            "Transaction ID: "
                            f"**{transaction_result['transaction_id']}**"
                        )

                        st.metric(
                            "New Balance",
                            (
                                f"₹ "
                                f"{transaction_result['new_balance']:,.2f}"
                            ),
                        )

                    else:

                        st.error(
                            transaction_result["message"]
                        )

                else:

                    st.error(
                        otp_result["message"]
                    )

    # ========================================================
    # TRANSFER
    # ========================================================

    with tab4:

        st.subheader("🔄 Transfer Money")

        source_account = st.selectbox(
            "From Your Account",
            options=list(account_options.keys()),
            key="user_source_account",
        )

        source_id = account_options[
            source_account
        ]

        # ----------------------------------------------------
        # DESTINATION ACCOUNT
        # ----------------------------------------------------

        all_active_accounts = get_active_accounts()

        destination_options = {
            (
                f"{account.account_number} | "
                f"{account.customer.full_name}"
            ): account.id
            for account in all_active_accounts
            if account.id != source_id
        }

        if not destination_options:

            st.warning(
                "No other active bank accounts are "
                "available for transfer."
            )

        else:

            destination_account = st.selectbox(
                "To Account",
                options=list(
                    destination_options.keys()
                ),
                key="user_destination_account",
            )

            destination_id = destination_options[
                destination_account
            ]

            amount = st.number_input(
                "Transfer Amount (₹)",
                min_value=0.00,
                value=0.00,
                step=100.00,
                format="%.2f",
                key="user_transfer_amount",
            )

            description = st.text_input(
                "Transfer Description",
                value="Account transfer",
                key="user_transfer_description",
            )

            if st.button(
                "📧 Send OTP",
                use_container_width=True,
                key="user_transfer_send_otp",
            ):

                if amount <= 0:

                    st.error(
                        "Please enter a valid transfer amount."
                    )

                else:

                    result = send_transaction_otp(
                        customer_id=customer_id,
                        account_id=source_id,
                        reference_account_id=destination_id,
                        amount=amount,
                        purpose="TRANSFER",
                    )

                    if result["success"]:

                        st.session_state[
                            "user_transfer_otp_id"
                        ] = result["otp_id"]

                        st.session_state[
                            "user_transfer_otp_active"
                        ] = True

                        st.success(
                            result["message"]
                        )

                    else:

                        st.error(
                            result["message"]
                        )

            if st.session_state.get(
                "user_transfer_otp_active",
                False,
            ):

                st.info(
                    "🔐 OTP has been sent to your "
                    "registered email address."
                )

                otp = st.text_input(
                    "Enter 6-Digit OTP",
                    max_chars=6,
                    type="password",
                    key="user_transfer_otp_input",
                )

                if st.button(
                    "✅ Verify OTP & Transfer",
                    use_container_width=True,
                    key="user_transfer_verify_otp",
                ):

                    otp_result = verify_transaction_otp(
                        otp_id=st.session_state[
                            "user_transfer_otp_id"
                        ],
                        entered_otp=otp,
                    )

                    if otp_result["success"]:

                        transaction_result = transfer_money(
                            source_account_id=otp_result[
                                "account_id"
                            ],
                            destination_account_id=otp_result[
                                "reference_account_id"
                            ],
                            amount=otp_result[
                                "amount"
                            ],
                            description=description,
                            customer_id=customer_id,
                        )

                        if transaction_result["success"]:

                            st.session_state[
                                "user_transfer_otp_active"
                            ] = False

                            st.session_state.pop(
                                "user_transfer_otp_id",
                                None,
                            )

                            st.success(
                                transaction_result["message"]
                            )

                            st.info(
                                "Transfer Out ID: "
                                f"**{transaction_result['transfer_out_id']}**"
                            )

                            st.info(
                                "Transfer In ID: "
                                f"**{transaction_result['transfer_in_id']}**"
                            )

                            col1, col2 = st.columns(2)

                            with col1:

                                st.metric(
                                    "Source Balance",
                                    (
                                        f"₹ "
                                        f"{transaction_result['source_balance']:,.2f}"
                                    ),
                                )

                            with col2:

                                st.metric(
                                    "Destination Balance",
                                    (
                                        f"₹ "
                                        f"{transaction_result['destination_balance']:,.2f}"
                                    ),
                                )

                        else:

                            st.error(
                                transaction_result["message"]
                            )

                    else:

                        st.error(
                            otp_result["message"]
                        )

    # ========================================================
    # TRANSACTION HISTORY
    # ========================================================

    with tab5:

        st.subheader("📜 My Transaction History")

        selected_account = st.selectbox(
            "Select Your Account",
            options=list(account_options.keys()),
            key="user_history_account",
        )

        account_id = account_options[
            selected_account
        ]

        transactions = (
            get_customer_account_transactions(
                customer_id=customer_id,
                account_id=account_id,
            )
        )

        if not transactions:

            st.info(
                "No transactions found."
            )

        else:

            data = []

            for transaction in transactions:

                data.append(
                    {
                        "Transaction ID": (
                            transaction.transaction_ref
                        ),
                        "Type": (
                            transaction.transaction_type
                        ),
                        "Amount": (
                            f"₹ {float(transaction.amount):,.2f}"
                        ),
                        "Balance After": (
                            f"₹ "
                            f"{float(transaction.balance_after):,.2f}"
                            if transaction.balance_after
                            is not None
                            else "-"
                        ),
                        "Description": (
                            transaction.description
                            or "-"
                        ),
                        "Date": (
                            (
                                transaction.created_at
                                + timedelta(
                                    hours=5,
                                    minutes=30,
                                )
                            ).strftime(
                                "%d-%m-%Y %I:%M:%S %p"
                            )
                        ),
                    }
                )

            dataframe = pd.DataFrame(data)

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )

    # ========================================================
    # ACCOUNT STATEMENT
    # ========================================================

    with tab6:

        st.subheader("📄 My Account Statement")

        st.info(
            "Generate and download a PDF statement "
            "for your account and selected date range."
        )

        statement_account = st.selectbox(
            "Select Your Account",
            options=list(account_options.keys()),
            key="user_statement_account",
        )

        statement_account_id = account_options[
            statement_account
        ]

        statement_account_obj = next(
            (
                account
                for account in accounts
                if account.id == statement_account_id
            ),
            None,
        )

        col1, col2 = st.columns(2)

        with col1:

            start_date = st.date_input(
                "Start Date",
                value=(
                    datetime.now().date()
                    - timedelta(days=30)
                ),
                key="user_statement_start_date",
            )

        with col2:

            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                key="user_statement_end_date",
            )

        if start_date > end_date:

            st.error(
                "Start date cannot be later than end date."
            )

        elif statement_account_obj is None:

            st.error(
                "Unable to identify your account."
            )

        else:

            statement_transactions = (
                get_customer_account_transactions(
                    customer_id=customer_id,
                    account_id=statement_account_id,
                )
            )

            filtered_transactions = []

            for transaction in statement_transactions:

                transaction_date = (
                    transaction.created_at
                    + timedelta(
                        hours=5,
                        minutes=30,
                    )
                ).date()

                if (
                    start_date
                    <= transaction_date
                    <= end_date
                ):

                    filtered_transactions.append(
                        transaction
                    )

            st.markdown(
                "### 📊 Statement Preview"
            )

            preview_data = []

            for transaction in filtered_transactions:

                transaction_type = (
                    transaction.transaction_type.upper()
                )

                amount = float(
                    transaction.amount
                )

                if transaction_type in [
                    "DEPOSIT",
                    "TRANSFER_IN",
                ]:

                    credit = (
                        f"₹ {amount:,.2f}"
                    )
                    debit = "-"

                elif transaction_type in [
                    "WITHDRAWAL",
                    "TRANSFER_OUT",
                ]:

                    debit = (
                        f"₹ {amount:,.2f}"
                    )
                    credit = "-"

                else:

                    debit = "-"
                    credit = "-"

                preview_data.append(
                    {
                        "Date": (
                            (
                                transaction.created_at
                                + timedelta(
                                    hours=5,
                                    minutes=30,
                                )
                            ).strftime(
                                "%d-%m-%Y %I:%M %p"
                            )
                        ),
                        "Transaction ID": (
                            transaction.transaction_ref
                        ),
                        "Type": (
                            transaction.transaction_type
                        ),
                        "Description": (
                            transaction.description
                            or "-"
                        ),
                        "Debit": debit,
                        "Credit": credit,
                        "Balance": (
                            f"₹ "
                            f"{float(transaction.balance_after):,.2f}"
                            if transaction.balance_after
                            is not None
                            else "-"
                        ),
                    }
                )

            if preview_data:

                preview_df = pd.DataFrame(
                    preview_data
                )

                st.dataframe(
                    preview_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No transactions found for "
                    "the selected date range."
                )

            pdf_data = (
                generate_account_statement_pdf(
                    account=statement_account_obj,
                    transactions=statement_transactions,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            account_number = (
                statement_account_obj.account_number
            )

            filename = (
                f"Account_Statement_"
                f"{account_number}_"
                f"{start_date.strftime('%d-%m-%Y')}_"
                f"{end_date.strftime('%d-%m-%Y')}.pdf"
            )

            st.download_button(
                label="📥 Download Account Statement PDF",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )

# ============================================================
# USER MANAGEMENT PAGE
# ============================================================

def user_management_page():
    # ========================================================
    # PAGE CSS
    # ========================================================

    st.markdown(
        """
        <style>
        .user-management-header {
            padding:
                8px 0 20px 0;
        }
        .user-management-title {
            font-size: 2.2rem;
            font-weight: 850;
            color: #f8fafc;
            margin-bottom: 5px;
        }
        .user-management-subtitle {
            color: #9299aa;
            font-size: 0.92rem;
        }
        .role-stat-card {
            background:
                linear-gradient(
                    145deg,
                    rgba(255,255,255,0.055),
                    rgba(255,255,255,0.018)
                );
            border:
                1px solid
                rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 18px;
            min-height: 105px;
            box-shadow:
                0 8px 25px
                rgba(0,0,0,0.15);
        }
        .role-stat-icon {
            font-size: 1.35rem;
            margin-bottom: 5px;
        }
        .role-stat-label {
            color: #8f96a8;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .role-stat-value {
            color: #ffffff;
            font-size: 1.65rem;
            font-weight: 800;
            margin-top: 3px;
        }
        .user-role-card {
            background:
                rgba(255,255,255,0.025);
            border:
                1px solid
                rgba(255,255,255,0.07);
            border-radius: 15px;
            padding: 14px 16px;
            margin:
                8px 0;
        }
        .user-name {
            color: #f8fafc;
            font-size: 1rem;
            font-weight: 750;
        }
        .user-meta {
            color: #777f91;
            font-size: 0.74rem;
            margin-top: 4px;
        }
        .current-role {
            color: #a5b4fc;
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # HEADER
    # ========================================================

    st.markdown(
        """
        <div class="user-management-header">
            <div class="user-management-title">
                🛡️ User Management
            </div>
            <div class="user-management-subtitle">
                Manage user accounts and administrator
                privileges securely.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # LOAD USERS
    # ========================================================

    try:
        users = get_all_users_for_admin()
    except PermissionError:
        st.error("Administrator access is required.")
        return
    except Exception as e:
        st.error(f"Unable to load users: {e}")
        return

    # ========================================================
    # STATISTICS
    # ========================================================

    total_users = len(users)
    total_admins = sum(
        1
        for user in users
        if user["role"] == "admin"
    )
    total_customers = sum(
        1
        for user in users
        if user["role"] == "user"
    )

    stat1, stat2, stat3 = st.columns(3)

    with stat1:
        st.markdown(
            f"""
            <div class="role-stat-card">
                <div class="role-stat-icon">
                    👥
                </div>
                <div class="role-stat-label">
                    Total Users
                </div>
                <div class="role-stat-value">
                    {total_users}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with stat2:
        st.markdown(
            f"""
            <div class="role-stat-card">
                <div class="role-stat-icon">
                    👑
                </div>
                <div class="role-stat-label">
                    Administrators
                </div>
                <div class="role-stat-value">
                    {total_admins}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with stat3:
        st.markdown(
            f"""
            <div class="role-stat-card">
                <div class="role-stat-icon">
                    👤
                </div>
                <div class="role-stat-label">
                    Customers
                </div>
                <div class="role-stat-value">
                    {total_customers}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>",unsafe_allow_html=True,)

    # ========================================================
    # INFORMATION
    # ========================================================

    st.info(
        "🔐 Only administrators can change user roles. "
        "At least one administrator must always remain active."
    )

    # ========================================================
    # USER LIST
    # ========================================================

    st.markdown("### 👥 User Accounts")

    if not users:
        st.warning("No user accounts found.")
        return

    for user in users:
        user_id = user["id"]
        username = user["username"]
        current_role = user["role"]
        is_active = user["is_active"]
        created_at = user["created_at"]

        # ----------------------------------------------------
        # CARD
        # ----------------------------------------------------

        st.markdown(
            '<div class="user-role-card">',
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4, col5 = st.columns(
            [2.3, 1.1, 1.5, 1.1, 1.1]
        )

        # ----------------------------------------------------
        # USERNAME
        # ----------------------------------------------------

        with col1:
            status_text = (
                "Active"
                if is_active
                else "Inactive"
            )
            st.markdown(
                f"""
                <div class="user-name">
                    👤 {username}
                </div>
                <div class="user-meta">
                    User ID: {user_id}
                    &nbsp; • &nbsp;
                    {status_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # CURRENT ROLE
        # ----------------------------------------------------

        with col2:
            st.markdown(
                f"""
                <div class="current-role">
                    {current_role}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # ROLE SELECT
        # ----------------------------------------------------

        with col3:
            role_options = ["User","Admin",]
            current_role_display = (
                "Admin"
                if current_role == "admin"
                else "User"
            )

            selected_role = st.selectbox(
                "Change Role",
                role_options,
                index=role_options.index(
                    current_role_display
                ),
                key=f"role_select_{user_id}",
                label_visibility="collapsed",
            )

        # ----------------------------------------------------
        # UPDATE BUTTON
        # ----------------------------------------------------

        with col4:
            update_clicked = st.button(
                "💾 Update",
                key=f"update_role_{user_id}",
                use_container_width=True,
            )
            if update_clicked:
                new_role = (
                    "admin"
                    if selected_role == "Admin"
                    else "user"
                )
                result = update_user_role(
                    user_id=user_id,
                    new_role=new_role,
                )

                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])

        # ----------------------------------------------------
        # DELETE BUTTON
        # ----------------------------------------------------

        with col5:
            delete_clicked = st.button(
                "🗑️ Delete",
                key=f"delete_user_{user_id}",
                use_container_width=True,
            )
            if delete_clicked:
                st.session_state[f"confirm_delete_{user_id}"] = True
            if st.session_state.get(
                f"confirm_delete_{user_id}",
                False
            ):
                st.warning(
                    f"Are you sure you want to delete "
                    f"'{username}'?"
                )
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    confirm_delete = st.button(
                        "✅ Confirm",
                        key=f"confirm_delete_btn_{user_id}",
                        use_container_width=True,
                    )
                with confirm_col2:
                    cancel_delete = st.button(
                        "❌ Cancel",
                        key=f"cancel_delete_btn_{user_id}",
                        use_container_width=True,
                    )
                if confirm_delete:
                    result = delete_user_account(user_id=user_id)
                    if result["success"]:
                        st.session_state[f"confirm_delete_{user_id}"] = False
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
                if cancel_delete:
                    st.session_state[f"confirm_delete_{user_id}"] = False
                    st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )