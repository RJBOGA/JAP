# src/backend/services/email_service.py
import os
import resend
from typing import List

# Initialize the Resend client with the API key from .env
resend.api_key = os.getenv("RESEND_API_KEY")

# Replace this with your own verified sending domain email
# For the free tier, you can only send from the email you signed up with.
SENDER_EMAIL = "onboarding@resend.dev"  # Default provided by Resend

def send_interview_invitation(to_email: str, candidate_name: str, job_title: str, company: str):
    """Sends an interview invitation email."""
    if not resend.api_key:
        print("WARNING: RESEND_API_KEY not set. Skipping email.")
        return

    subject = f"Interview Invitation for the {job_title} position at {company}"
    html_body = f"""
    <p>Hi {candidate_name},</p>
    <p>Congratulations! We would like to invite you for an interview for the <strong>{job_title}</strong> role at <strong>{company}</strong>.</p>
    <p>Our hiring team will be in touch shortly to coordinate a time that works for you.</p>
    <p>Best regards,<br/>The Hiring Team at {company}</p>
    """
    try:
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        print(f"Interview invitation sent to {to_email}")
    except Exception as e:
        print(f"ERROR: Failed to send interview invitation to {to_email}. Error: {e}")

def send_rejection_notification(to_email: str, candidate_name: str, job_title: str, company: str):
    """Sends a rejection email to unsuccessful applicants."""
    if not resend.api_key:
        print("WARNING: RESEND_API_KEY not set. Skipping email.")
        return
        
    subject = f"Update on your application for {job_title} at {company}"
    html_body = f"""
    <p>Hi {candidate_name},</p>
    <p>Thank you for your interest in the <strong>{job_title}</strong> role at <strong>{company}</strong>.</p>
    <p>We received a large number of qualified applications, and after careful consideration, we have decided to move forward with other candidates whose experience more closely matches our current needs.</p>
    <p>We appreciate you taking the time to apply and wish you the best of luck in your job search.</p>
    <p>Best regards,<br/>The Hiring Team at {company}</p>
    """
    try:
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        print(f"Rejection notification sent to {to_email}")
    except Exception as e:
        print(f"ERROR: Failed to send rejection email to {to_email}. Error: {e}")
