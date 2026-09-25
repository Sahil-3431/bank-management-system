# 🏦 Bank Management System

> A secure, role-based banking management application built with **Python, Streamlit, SQLAlchemy, and PostgreSQL/compatible relational databases**. The system provides separate workflows for administrators and bank customers, covering customer management, account management, transactions, OTP-protected financial operations, account statements, authentication, and administrative user management.

---

## 📌 Project Overview

The **Bank Management System** is a full-stack style banking application implemented with Python and Streamlit. It combines a responsive web interface, relational database layer, authentication services, OTP verification, and banking business logic into a single application.

The project is designed around two primary roles:

- **Administrator** — manages customers, accounts, transactions, and application users.
- **Bank Customer** — securely accesses personal banking information, accounts, transactions, profile settings, and statements.

The application follows a modular architecture so that authentication, database models, business services, UI pages, email/OTP functionality, and configuration remain separated.

---

## ✨ Key Features

### 🔐 Authentication & Security

- Secure username/password authentication
- Password hashing using **bcrypt**
- Role-based access control
- Admin and customer access separation
- Active-session validation
- Logout/session handling
- Password change functionality
- Password reset workflow using OTP
- Environment-based configuration for sensitive credentials

### 👑 Administrator Features

Administrators can access:

- 📊 Banking Dashboard
- 👤 Customer Management
- 🏦 Account Management
- 💰 Transaction Management
- 🛡️ User Management
- Customer block/unblock controls
- Customer deletion workflow
- User role management
- Admin/User account deletion
- Account statement generation
- Transaction monitoring

### 👤 Customer Features

Customers can:

- View personal profile
- View linked bank accounts
- Check account balances
- Deposit money
- Withdraw money
- Transfer money
- View transaction history
- Generate/download account statements
- Change password
- Complete OTP verification for protected transactions

### 💳 Banking Operations

The system supports:

- Account creation
- Savings/current-style account handling
- Deposit
- Withdrawal
- Account-to-account transfer
- Transaction references
- Balance tracking
- Balance-after-transaction records
- Account status management
- Transaction history

### 📧 OTP & Email Security

OTP verification is integrated into sensitive workflows such as:

- Deposit
- Withdrawal
- Transfer
- Password reset

The project uses hashed OTP storage and configurable expiry/attempt controls.

### 📄 PDF Account Statements

Users can generate professional PDF account statements containing:

- Account information
- Statement period
- Transaction details
- Transaction references
- Debit/credit information
- Balance information

---

# 🧩 User Management

The **User Management** module is designed for administrator-level account control.

Administrators can:

- View registered users
- View current roles
- Change a user's role
- Delete a user account
- Delete another administrator account
- Protect their own account from deletion
- Prevent deletion of the final remaining administrator

### Delete Account Safety Rules

The delete functionality includes safeguards:

```text
Admin
  │
  ├── Delete User ───────────────► Allowed
  │
  ├── Delete Another Admin ──────► Allowed
  │
  ├── Delete Own Account ────────► Blocked
  │
  └── Delete Last Admin ─────────► Blocked
```

Deleting a **login/user account** is intentionally separate from deleting a customer's banking data. Customer, account, and transaction deletion should be handled through their respective administrative workflows.

---

# 🏗️ System Architecture

```text
                    ┌─────────────────────────┐
                    │       Streamlit UI      │
                    │  app.py + ui.py         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Authentication Layer    │
                    │ auth.py                 │
                    │                         │
                    │ Login / Roles / bcrypt  │
                    │ Session / Password      │
                    └────────────┬────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  ▼                             ▼
       ┌─────────────────────┐       ┌─────────────────────┐
       │ Business Services   │       │ OTP / Email Layer   │
       │ services.py         │       │ otp_service.py      │
       │                     │       │ email_service.py    │
       │ Banking Operations  │       │                     │
       └──────────┬──────────┘       └─────────────────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │ SQLAlchemy ORM      │
       │ database.py         │
       │ models.py           │
       └──────────┬──────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │ Relational Database │
       │ PostgreSQL / SQL DB │
       └─────────────────────┘
```

---

# 🗃️ Database Design

The core data model contains the following entities:

### `users`

Stores authentication and authorization information.

Important fields:

- `id`
- `username`
- `password_hash`
- `role`
- `customer_id`
- `is_active`
- `created_at`

### `customers`

Stores customer profile information.

Important fields:

- `id`
- `customer_code`
- `full_name`
- `email`
- `phone`
- `address`
- `is_active`
- `created_at`

### `accounts`

Stores customer bank accounts.

Important fields:

- `id`
- `account_number`
- `account_type`
- `balance`
- `status`
- `customer_id`
- `created_at`

### `transactions`

Stores financial transaction history.

Important fields include:

- `id`
- `transaction_ref`
- `account_id`
- `transaction_type`
- `amount`
- `balance_after`
- `reference_account_id`
- `description`
- `created_at`

### OTP Tables

The project also includes dedicated models for:

- Transaction OTP verification
- Password reset OTP verification

---

# 🔗 Entity Relationship Overview

```text
             ┌─────────────────┐
             │     Customer    │
             └────────┬────────┘
                      │
             1        │        N
                      ▼
             ┌─────────────────┐
             │     Account     │
             └────────┬────────┘
                      │
             1        │        N
                      ▼
             ┌─────────────────┐
             │   Transaction   │
             └─────────────────┘

             ┌─────────────────┐
             │      User       │
             └────────┬────────┘
                      │
                      │ 0..1
                      ▼
             ┌─────────────────┐
             │     Customer    │
             └─────────────────┘
```

---

# 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Programming Language | Python |
| Web Framework / UI | Streamlit |
| ORM | SQLAlchemy |
| Database | PostgreSQL / SQLAlchemy-compatible DB |
| Authentication | bcrypt |
| Password Utilities | Passlib |
| Data Processing | Pandas |
| Environment Management | python-dotenv |
| Email | SMTP |
| OTP Security | Hashed OTP workflow |
| PDF Generation | ReportLab |
| Database Migration Support | Alembic |
| Testing | Pytest |

---

# 📁 Project Structure

```text
bank_management_system/
│
├── app.py
│   └── Main Streamlit application and navigation
│
├── ui.py
│   └── Application pages and user interface
│
├── auth.py
│   └── Authentication, authorization, passwords,
│       roles, sessions and user administration
│
├── services.py
│   └── Banking business logic and service operations
│
├── models.py
│   └── SQLAlchemy database models
│
├── database.py
│   └── Database engine, sessions and initialization
│
├── config.py
│   └── Environment and application configuration
│
├── otp_service.py
│   └── OTP generation/verification logic
│
├── email_service.py
│   └── SMTP/email functionality
│
├── test_email.py
│   └── Email configuration test utility
│
├── tests/
│   └── Application/service tests
│
├── requirements.txt
│   └── Python dependencies
│
├── .env.example
│   └── Environment variable template
│
├── .gitignore
│   └── Git ignore configuration
│
└── .streamlit/
    └── Streamlit configuration
```

---

# ⚙️ Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/bank-management-system.git
cd bank-management-system
```

Replace `YOUR-USERNAME` with your GitHub username.

---

## 2. Create a Virtual Environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Configuration

Create a `.env` file in the project root.

You can use `.env.example` as the template.

Example:

```env
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/bank_management

INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=your_secure_admin_password

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_USE_TLS=true

OTP_HASH_SECRET=your_long_random_secret
```

### ⚠️ Security Notice

Never commit the real `.env` file to GitHub.

Keep secrets such as:

- Database passwords
- SMTP passwords
- OTP secrets
- Admin passwords
- API credentials

outside source control.

The repository should contain `.env.example`, not production secrets.

---

# 🗄️ Database Setup

The application reads the database connection from:

```env
DATABASE_URL
```

Example PostgreSQL configuration:

```env
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/bank_management
```

Make sure the database exists before starting the application.

The application initializes the SQLAlchemy database schema when it starts.

---

# ▶️ Run the Application

Start Streamlit:

```bash
streamlit run app.py
```

The application will open in your browser.

Typical local address:

```text
http://localhost:8501
```

---

# 🔐 Authentication Flow

```text
User
 │
 ▼
Login Page
 │
 ├── Invalid Credentials ──► Error
 │
 └── Valid Credentials
          │
          ▼
    Session Created
          │
          ▼
   Role Verification
       /        \
      /          \
   Admin        User
     │            │
     ▼            ▼
Admin Pages   My Banking
```

The application validates the current session and role before exposing protected functionality.

---

# 👑 Admin Workflow

```text
Admin Login
    │
    ▼
Dashboard
    │
    ├── Customer Management
    │      ├── Create
    │      ├── View
    │      ├── Block / Unblock
    │      └── Delete
    │
    ├── Account Management
    │      ├── Create
    │      └── Manage
    │
    ├── Transaction Management
    │      ├── Deposit
    │      ├── Withdrawal
    │      ├── Transfer
    │      └── Statements
    │
    └── User Management
           ├── View Users
           ├── Change Role
           └── Delete User/Admin
```

---

# 👤 Customer Workflow

```text
Customer Login
      │
      ▼
   My Banking
      │
      ├── My Profile
      ├── My Accounts
      ├── Balance
      ├── Deposit
      ├── Withdraw
      ├── Transfer
      ├── Transaction History
      ├── Account Statement
      └── Change Password
```

---

# 💸 Transaction Security Flow

Sensitive transactions use OTP verification.

```text
Customer
   │
   ▼
Select Transaction
   │
   ▼
Enter Amount / Details
   │
   ▼
Send OTP
   │
   ▼
Email OTP
   │
   ▼
Enter OTP
   │
   ▼
Verify OTP
   │
   ├── Invalid ──► Reject Transaction
   │
   └── Valid
        │
        ▼
   Execute Transaction
        │
        ▼
   Update Balance
        │
        ▼
   Save Transaction Record
```

---

# 📊 Dashboard

The banking dashboard provides an administrative overview of the system, including banking and account-related statistics.

The interface uses a responsive wide-screen Streamlit layout with dedicated KPI-style sections and administrative navigation.

---

# 📄 Account Statement

The system can generate PDF account statements based on:

- Selected account
- Selected date range
- Transaction history

The generated document can be downloaded directly from the application.

---

# 🧪 Testing

The project includes a `tests/` directory.

Run the test suite using:

```bash
pytest
```

For more detailed output:

```bash
pytest -v
```

---

# 🚀 Deployment

The application can be deployed on platforms that support Python/Streamlit applications.

Before deployment:

### 1. Configure production environment variables

Set:

```text
DATABASE_URL
INITIAL_ADMIN_USERNAME
INITIAL_ADMIN_PASSWORD
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM_EMAIL
SMTP_USE_TLS
OTP_HASH_SECRET
```

### 2. Do not upload `.env`

Use the hosting provider's secret/environment-variable management.

### 3. Verify database connectivity

Ensure the production database accepts connections from the deployed application.

### 4. Test authentication

Verify:

- Admin login
- Customer login
- Password changes
- Password reset
- OTP delivery

### 5. Test financial workflows

Verify:

- Deposit
- Withdrawal
- Transfer
- Transaction history
- Statement generation

---

# 🛡️ Security Considerations

This project includes several security-oriented practices:

- Password hashing with bcrypt
- Role-based access control
- Session validation
- OTP verification for sensitive operations
- Hashed OTP storage
- OTP expiry and attempt controls
- Environment-based secret management
- Database transactions with rollback handling
- Protection against deleting the currently logged-in administrator
- Protection against deleting the final administrator

### Production Recommendations

For a real production banking environment, additionally consider:

- HTTPS/TLS everywhere
- Strong password policy
- Multi-factor authentication
- CSRF/session hardening where applicable
- Rate limiting
- Audit logs
- Database backups
- Encryption at rest
- Secrets manager
- Least-privilege database users
- Security monitoring
- Automated dependency scanning
- Formal penetration testing
- Strong transaction authorization and fraud controls

> This project is an educational/software portfolio implementation and should not be treated as a production banking platform without additional security, compliance, reliability, and audit controls.

---

# 📈 Future Enhancements

Potential future improvements include:

- 🔔 Real-time transaction notifications
- 📱 Mobile-responsive customer experience
- 📊 Advanced financial analytics
- 📈 Transaction trend dashboards
- 🔎 Advanced transaction search and filtering
- 🧾 Automated monthly statements
- 📧 Transaction email notifications
- 🔐 Two-factor authentication
- 📝 Comprehensive audit logging
- 🧑‍💼 Employee/Staff role hierarchy
- 🌐 Production-grade deployment pipeline
- 🧪 Expanded unit and integration testing
- 🐳 Docker containerization
- ⚙️ CI/CD with GitHub Actions

---

# 🧑‍💻 Development Guidelines

When extending the project:

1. Keep UI code inside `ui.py`.
2. Keep authentication/authorization logic inside `auth.py`.
3. Keep banking business logic inside `services.py`.
4. Keep database models inside `models.py`.
5. Keep database/session configuration inside `database.py`.
6. Keep secrets in environment variables.
7. Add tests for important business logic.
8. Avoid committing `.env` or credentials.
9. Use clear function names and meaningful error messages.
10. Validate all financial operations before committing database changes.

---

# 🐛 Troubleshooting

### `DATABASE_URL is not configured`

Create `.env` and add:

```env
DATABASE_URL=your_database_connection_string
```

---

### Database connection error

Check:

- Database server is running
- Database name is correct
- Username/password are correct
- Host and port are correct
- PostgreSQL driver is installed

Install the PostgreSQL driver if needed:

```bash
pip install psycopg2-binary
```

---

### Streamlit command not found

Activate the virtual environment and install dependencies:

```bash
pip install streamlit
```

Then:

```bash
streamlit run app.py
```

---

### Email/OTP not working

Verify:

- SMTP host
- SMTP port
- SMTP username
- SMTP password/app password
- TLS setting
- Sender email
- Network access

---

# 📜 License

This project can be distributed under the license selected by the repository owner.

If no license has been added yet, add an appropriate `LICENSE` file before presenting the repository as an open-source project.

---

# 👨‍💻 Author

**Sahil Khan**

**Data Analyst | Data Scientist**

Interested in:

- Data Analytics
- Python
- SQL
- Machine Learning
- Business Intelligence
- Software Development

---

# ⭐ Project Highlights

```text
✔ Role-Based Authentication
✔ Admin & Customer Workflows
✔ Secure Password Hashing
✔ OTP-Protected Transactions
✔ Customer Management
✔ Account Management
✔ Deposit / Withdrawal / Transfer
✔ Transaction History
✔ PDF Account Statements
✔ Admin User Management
✔ User/Admin Role Management
✔ Secure User Deletion Controls
✔ SQLAlchemy ORM
✔ PostgreSQL Support
✔ Streamlit Dashboard
✔ Modular Python Architecture
✔ Environment-Based Configuration
```

---

## 📌 Project Status

**Status:** Active Development

The project is structured as a portfolio-grade banking management application and can be extended with additional enterprise security, audit, deployment, testing, and analytics capabilities.
