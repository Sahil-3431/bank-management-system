from email_service import send_email


result = send_email(
    recipient_email="ssaifiji00000@gmail.com",
    subject="Bank Management System - Email Test",
    body=(
        "Hello,\n\n"
        "This is a test email from the Bank Management System.\n\n"
        "Email configuration is working successfully."
    ),
)


print(result)