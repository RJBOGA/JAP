# scripts/test_smtp_config.py
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from dotenv import load_dotenv

# --- 1. Load Environment Variables (Critical for isolation) ---
# We load the .env files explicitly to ensure config visibility
load_dotenv(os.path.join(os.path.dirname(__file__), '../src/.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '../src/backend/.env'))

# --- 2. Configuration & Test Data ---
SMTP_HOST = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT", 587))
SMTP_USERNAME = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD") # This is the App Password
SENDER_EMAIL = SMTP_USERNAME 
TEST_RECIPIENT = SMTP_USERNAME # Sending test email to self

def run_smtp_test():
    """Reads environment and attempts a connection/login/send test."""
    print("="*60)
    print("EMAIL CONFIGURATION & SMTP DIAGNOSTIC TEST")
    print("="*60)
    
    # Check 1: Verify Configuration Read
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD]):
        print("❌ CONFIGURATION FAILURE: One or more critical variables are missing.")
        print(f"  HOST: {SMTP_HOST}")
        print(f"  USER: {SMTP_USERNAME}")
        print(f"  PASS: {'SET' if SMTP_PASSWORD else 'NOT SET'}")
        print("="*60)
        return

    print("✅ Configuration variables read successfully.")
    print(f"   HOST: {SMTP_HOST}:{SMTP_PORT}")
    print(f"   USER: {SMTP_USERNAME}")
    print(f"   RECIPIENT: {TEST_RECIPIENT}")
    print("-"*60)
    
    # Check 2: Attempt SMTP Connection and Authentication
    context = ssl.create_default_context()
    subject = "SMTP Diagnostic Test from JobChat.AI"
    html_body = "<p>If you received this email, your SMTP configuration is correct!</p>"
    
    message = MIMEText(html_body, 'html')
    message['Subject'] = subject
    message['From'] = SENDER_EMAIL
    message['To'] = TEST_RECIPIENT

    try:
        print("Attempting connection and login...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, TEST_RECIPIENT, message.as_string())
        
        print("\n🎉🎉🎉 TEST SUCCESS! 🎉🎉🎉")
        print("The test email should be in your inbox shortly.")
        print("Your SMTP configuration is CORRECT.")
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ AUTHENTICATION FAILURE!")
        print("  Reason: Incorrect App Password or Gmail settings are blocking the login.")
        print("  Action: GENERATE A NEW APP PASSWORD (see previous instructions).")
        
    except smtplib.SMTPServerDisconnected:
        print("\n❌ CONNECTION FAILURE: Server Disconnected.")
        print("  Reason: Host or Port might be incorrect, or a firewall is blocking port 587.")
        
    except Exception as e:
        print(f"\n❌ UNHANDLED SMTP ERROR: {type(e).__name__}: {e}")
        print("  Action: Check firewall or other network/server settings.")
        
    print("="*60)

if __name__ == "__main__":
    run_smtp_test()