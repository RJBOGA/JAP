# src/backend/services/email_service.py
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from dotenv import load_dotenv

# --- Load Env Vars (Ensure visibility) ---
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# --- Configuration ---
SMTP_HOST = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT", 587))
SMTP_USERNAME = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
SENDER_EMAIL = SMTP_USERNAME # The sender must be the authenticated account

def _send_email(to_email: str, subject: str, html_body: str):
    """Internal helper to connect to SMTP and send the email."""
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD]):
        print("WARNING: SMTP credentials not fully configured. Skipping email.")
        return

    message = MIMEText(html_body, 'html')
    message['Subject'] = subject
    message['From'] = SENDER_EMAIL
    message['To'] = to_email

    context = ssl.create_default_context()
    
    try:
        # Use starttls for port 587
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string())
        
        print(f"SMTP Success: Email sent to {to_email}")
        
    except Exception as e:
        print(f"SMTP ERROR: Failed to send email to {to_email}. Error: {type(e).__name__}: {e}")

def send_interview_invitation(to_email: str, candidate_name: str, job_title: str, company: str):
    """Sends an interview invitation email."""
    subject = f"Interview Invitation for the {job_title} position at {company}"
    html_body = f"""
    <p>Hi {candidate_name},</p>
    <p>Congratulations! We would like to invite you for an interview for the <strong>{job_title}</strong> role at <strong>{company}</strong>.</p>
    <p>Our hiring team will be in touch shortly to coordinate a time that works for you.</p>
    <p>Best regards,<br/>The Hiring Team at {company}</p>
    """
    _send_email(to_email, subject, html_body)

def send_rejection_notification(to_email: str, candidate_name: str, job_title: str, company: str):
    """Sends a rejection email to unsuccessful applicants."""
    subject = f"Update on your application for {job_title} at {company}"
    html_body = f"""
    <p>Hi {candidate_name},</p>
    <p>Thank you for your interest in the <strong>{job_title}</strong> role at <strong>{company}</strong>.</p>
    <p>We received a large number of qualified applications, and after careful consideration, we have decided to move forward with other candidates whose experience more closely matches our current needs.</p>
    <p>We appreciate you taking the time to apply and wish you the best of luck in your job search.</p>
    <p>Best regards,<br/>The Hiring Team at {company}</p>
    """
    _send_email(to_email, subject, html_body)