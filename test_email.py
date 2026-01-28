import smtplib
import os
from dotenv import load_dotenv

# Force reload of .env
load_dotenv(override=True)

def test_smtp():
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    print(f"Testing SMTP Connection to {smtp_server}:{smtp_port}")
    print(f"User: {smtp_user}")
    # Print first and last char of password for verification
    if smtp_password:
        print(f"Password: {smtp_password[0]}...{smtp_password[-1]} (Len: {len(smtp_password)})")
    else:
        print("Password: None")

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        print("✅ SMTP Authentication Successful!")
        server.quit()
    except Exception as e:
        print(f"❌ SMTP Failed: {e}")

if __name__ == "__main__":
    test_smtp()
