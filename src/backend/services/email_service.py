# src/backend/services/email_service.py
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from dotenv import load_dotenv
from ..repository import application_repo 
import logging

logger = logging.getLogger(__name__)
# --- IMPORTS FOR AUDIT ---
# Note: The application_repo relies on the MongoDB connection setup in db.py, 
# but this file only needs the import to use the update_one_application function.
from ..repository import application_repo 
# -----------------------------

# --- Load Env Vars (Ensure visibility) ---
# Explicitly load necessary env files relative to this script's location
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# --- Configuration ---
SMTP_HOST = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT", 587))
SMTP_USERNAME = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
SENDER_EMAIL = SMTP_USERNAME 

def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Internal helper to connect to SMTP and send the email."""
    # If this check fails, we still want to log it
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD]):
        logger.error("FATAL CONFIG ERROR: SMTP credentials missing in .env")
        return False

    # This print MUST show up if the function is executed.
    print(f"ULTIMATE_DEBUG: Attempting SMTP login with {SMTP_USERNAME} to {SMTP_HOST}:{SMTP_PORT}") 

    message = MIMEText(html_body, 'html', 'utf-8')
    message['Subject'] = subject
    message['From'] = SENDER_EMAIL
    message['To'] = to_email

    context = ssl.create_default_context()
    
    try:
        logger.debug(f"DEBUG_E: Attempting connection to {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string().encode('utf-8')) 
        
        print(f"ULTIMATE_DEBUG: SMTP SUCCESS to {to_email}")
        return True
        
    except Exception as e:
        # Re-raise the exception after printing for a full traceback
        print(f"ULTIMATE_DEBUG: SMTP FAILURE - {type(e).__name__}: {e}")
        raise # <-- CRITICAL: Re-raise the exception to force Flask to show the traceback
        return False

# def _send_email(to_email: str, subject: str, html_body: str) -> bool:
#     """Internal helper to connect to SMTP and send the email."""
#     if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD]):
#         logger.warning("SMTP credentials not fully configured. Skipping email.")
#         logger.debug(f"Host={SMTP_HOST}, User={SMTP_USERNAME}, Pass_Set={bool(SMTP_PASSWORD)}") # <-- Use logger.debug
#         print("WARNING: SMTP credentials not fully configured. Skipping email.")
#         return False
    
#     # MIME message construction
#     message = MIMEText(html_body, 'html')
#     message['Subject'] = subject
#     message['From'] = SENDER_EMAIL
#     message['To'] = to_email

#     context = ssl.create_default_context()
    
#     try:
#         # Use starttls for port 587
#         with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
#             server.starttls(context=context)
#             server.login(SMTP_USERNAME, SMTP_PASSWORD)
#             server.sendmail(SENDER_EMAIL, to_email, message.as_string())
        
#         print(f"SMTP Success: Email sent to {to_email}")
#         return True
        
#     except Exception as e:
#         print(f"SMTP ERROR: Failed to send email to {to_email}. Error: {type(e).__name__}: {e}")
#         logger.error(f"SMTP ERROR: Failed to send email to {to_email}. Error: {type(e).__name__}: {e}") # <-- Use logger.error
#         return False

def _audit_email_success(app_id: int, event_type: str):
    """Updates the application with the successful email event type."""
    try:
        application_repo.update_one_application(
            {"appId": app_id}, 
            {"emailSent": event_type}
        )
        logger.info(f"AUDIT Success: Application {app_id} marked as {event_type} email sent.") # <-- Use logger.info
        print(f"AUDIT Success: Application {app_id} marked as {event_type} email sent.")
        
    except Exception as e:
        logger.error(f"AUDIT ERROR: Failed to update application {app_id} emailSent field. Error: {e}") # <-- Use logger.error
        print(f"AUDIT ERROR: Failed to update application {app_id} emailSent field. Error: {e}")

def send_interview_invitation(to_email: str, candidate_name: str, job_title: str, company: str, app_id: int):
    """Sends an interview invitation email and audits success."""
    subject = f"Interview Invitation for the {job_title} position at {company}"
    html_body = f"""
    <p>Hi {candidate_name},</p>
    <p>Congratulations! We would like to invite you for an interview for the <strong>{job_title}</strong> role at <strong>{company}</strong>.</p>
    <p>Our hiring team will be in touch shortly to coordinate a time that works for you.</p>
    <p>Best regards,<br/>The Hiring Team at {company}</p>
    """
    if _send_email(to_email, subject, html_body):
        _audit_email_success(app_id, "Interview")

def send_rejection_notification(to_email: str, candidate_name: str, job_title: str, company: str, app_id: int):
    """Sends a rejection email to unsuccessful applicants and audits success."""
    subject = f"Update on your application for {job_title} at {company}"
    html_body = f"""
    <p>Hi {candidate_name},</p>
    <p>Thank you for your interest in the <strong>{job_title}</strong> role at <strong>{company}</strong>.</p>
    <p>We received a large number of qualified applications, and after careful consideration, we have decided to move forward with other candidates whose experience more closely matches our current needs.</p>
    <p>We appreciate you taking the time to apply and wish you the best of luck in your job search.</p>
    <p>Best regards,<br/>The Hiring Team at {company}</p>
    """
    if _send_email(to_email, subject, html_body):
        _audit_email_success(app_id, "Rejected")