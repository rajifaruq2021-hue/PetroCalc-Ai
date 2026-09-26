import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Sends a real One-Time Password (OTP) email via SMTP (e.g., Gmail SMTP).
    Reads SMTP_USER and SMTP_PASSWORD from environment variables if set.
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.environ.get("SMTP_USER", "petrocalc.ai.noreply@gmail.com")
    sender_password = os.environ.get("SMTP_PASSWORD", "")

    if not sender_password:
        # If SMTP password is not configured in environment, return False so the app
        # can guide the user or fall back gracefully.
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "PetroCalc AI — Secure Login Verification Code"

        body = (
            f"Hello,\n\n"
            f"Your One-Time Password (OTP) for authenticating into PetroCalc AI is:\n\n"
            f"    {otp_code}\n\n"
            f"Please enter this 6-digit code on the secure portal to complete your sign-in.\n\n"
            f"Best regards,\n"
            f"PetroCalc AI Engineering Team"
        )
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False
