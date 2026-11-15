"""Email dispatch utility for scheduled medication reminders and urgent caregiver alerts."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Dict
from backend.core.config import get_settings
from backend.core.logging import logger


def send_reminder_email(to_email: str, medication_name: str, scheduled_time: str) -> Dict[str, str]:
    """Sends a polite, clear medication reminder email to an elderly patient or caregiver.

    Args:
        to_email: Recipient's email address.
        medication_name: Name and dosage of the prescribed medicine.
        scheduled_time: Scheduled time or interval.

    Returns:
        A dictionary with operation status and message.
    """
    settings = get_settings()
    sender_email = settings.email_sender
    sender_password = settings.email_password
    smtp_server = settings.smtp_server
    smtp_port = settings.smtp_port

    if not sender_email or not sender_password:
        logger.warning("[EmailService] EMAIL_SENDER or EMAIL_PASSWORD not set. Simulating email dispatch.")
        return {
            "status": "success",
            "message": f"Simulated reminder email dispatched to {to_email} (Credentials not configured)",
        }

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"💊 CareSync AI Reminder: {medication_name} at {scheduled_time}"
    msg["From"] = f"CareSync AI <{sender_email}>"
    msg["To"] = to_email

    plain_text = (
        f"Hello,\n\n"
        f"This is a gentle reminder from CareSync AI to take your medication:\n\n"
        f"• Medication: {medication_name}\n"
        f"• Scheduled Time: {scheduled_time}\n\n"
        f"Please take it with a glass of water according to your prescription instructions.\n"
        f"Wishing you health and wellness,\n"
        f"CareSync AI Team"
    )

    msg.attach(MIMEText(plain_text, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        logger.info(f"[EmailService] Reminder email dispatched to {to_email}")
        return {"status": "success", "message": f"Reminder email successfully sent to {to_email}"}
    except Exception as e:
        logger.error(f"[EmailService] Failed to send reminder email: {e}")
        return {"status": "error", "message": f"Failed to send reminder email: {str(e)}"}


def send_caregiver_alert_email(
    to_email: str, patient_name: str, alert_type: str, details: str
) -> Dict[str, str]:
    """Dispatches an urgent caregiver notification email regarding a senior patient.

    Args:
        to_email: Caregiver's destination email address.
        patient_name: Full name of the elderly patient.
        alert_type: 'missed_dose' or 'sos'.
        details: Specific details or situation description.

    Returns:
        Status dictionary confirming delivery.
    """
    settings = get_settings()
    sender_email = settings.email_sender
    sender_password = settings.email_password
    smtp_server = settings.smtp_server
    smtp_port = settings.smtp_port

    if not sender_email or not sender_password:
        logger.warning("[EmailService] Email credentials not configured. Simulating caregiver alert dispatch.")
        return {
            "status": "success",
            "message": f"Caregiver alert for {patient_name} simulated to {to_email}",
        }

    subject_prefix = "🚨 URGENT SOS ALERT" if alert_type == "sos" else "⚠️ MISSED DOSE NOTICE"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{subject_prefix}: {patient_name} requires attention"
    msg["From"] = f"CareSync AI Alert <{sender_email}>"
    msg["To"] = to_email

    body_text = (
        f"ATTENTION CAREGIVER:\n\n"
        f"Patient: {patient_name}\n"
        f"Alert Type: {alert_type.upper()}\n"
        f"Details: {details}\n\n"
        f"Please check in with {patient_name} immediately or review their CareSync AI schedule.\n\n"
        f"CareSync AI Emergency Dispatch Service"
    )

    msg.attach(MIMEText(body_text, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        logger.info(f"[EmailService] Caregiver alert successfully sent to {to_email}")
        return {
            "status": "success",
            "message": f"Caregiver alert successfully delivered to {to_email}",
        }
    except Exception as e:
        logger.error(f"[EmailService] Failed to send caregiver alert: {e}")
        return {"status": "error", "message": f"Failed to send caregiver alert: {str(e)}"}
