import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict
from dotenv import load_dotenv

load_dotenv()


def send_reminder_email(to_email: str, medication_name: str, scheduled_time: str) -> Dict[str, str]:
    """
    Sends a polite, clear medication reminder email to an elderly patient or caregiver
    using Python's built-in smtplib.

    Args:
        to_email: Recipient's email address.
        medication_name: Name and dosage of the prescribed medicine.
        scheduled_time: Scheduled time or interval (e.g., '08:00 AM' or 'After breakfast').

    Returns:
        A dictionary with operation status and message.
    """
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if not sender_email or not sender_password:
        raise ValueError(
            "EMAIL_SENDER or EMAIL_PASSWORD environment variable is missing. "
            "Please configure them in your .env file."
        )

    # Compose email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"💊 Medication Reminder: {medication_name} at {scheduled_time}"
    msg["From"] = f"CareSync AI <{sender_email}>"
    msg["To"] = to_email

    # Plaintext fallback
    plain_text = (
        f"Hello,\n\n"
        f"This is a gentle reminder from CareSync AI to take your medication:\n\n"
        f"• Medication: {medication_name}\n"
        f"• Scheduled Time: {scheduled_time}\n\n"
        f"Please take it with a glass of water according to your prescription instructions.\n"
        f"If you have already taken it or have questions, please check with your doctor or caregiver.\n\n"
        f"Wishing you health and wellness,\n"
        f"The CareSync AI Team"
    )

    # HTML Body with high readability and contrast for elderly users & caregivers
    html_text = f"""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          font-family: Arial, sans-serif;
          background-color: #f8fafc;
          margin: 0;
          padding: 24px;
          color: #1e293b;
        }}
        .card {{
          background-color: #ffffff;
          max-width: 580px;
          margin: 0 auto;
          border-radius: 12px;
          border: 1px solid #e2e8f0;
          padding: 32px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .header {{
          text-align: center;
          border-bottom: 2px solid #e2e8f0;
          padding-bottom: 16px;
          margin-bottom: 24px;
        }}
        .header h1 {{
          color: #0284c7;
          font-size: 26px;
          margin: 0;
        }}
        .med-box {{
          background-color: #f0fdf4;
          border-left: 6px solid #16a34a;
          padding: 20px;
          border-radius: 8px;
          margin: 20px 0;
        }}
        .med-name {{
          font-size: 22px;
          font-weight: bold;
          color: #15803d;
          margin-bottom: 8px;
        }}
        .med-time {{
          font-size: 18px;
          color: #334155;
        }}
        .footer {{
          margin-top: 32px;
          font-size: 14px;
          color: #64748b;
          text-align: center;
          border-top: 1px solid #e2e8f0;
          padding-top: 16px;
        }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>CareSync AI</h1>
          <p style="font-size: 16px; color: #64748b; margin: 4px 0 0 0;">Medication Schedule Reminder</p>
        </div>
        <p style="font-size: 18px; line-height: 1.6;">Hello,</p>
        <p style="font-size: 18px; line-height: 1.6;">This is a friendly reminder to take your scheduled dose:</p>
        
        <div class="med-box">
          <div class="med-name">💊 {medication_name}</div>
          <div class="med-time">⏰ <strong>Time:</strong> {scheduled_time}</div>
        </div>

        <p style="font-size: 16px; line-height: 1.6; color: #475569;">
          Please remember to take your dose with water, following the prescribed instructions on your bottle or strip.
        </p>

        <div class="footer">
          <p>CareSync AI • Dedicated to Compassionate Elderly Care & Wellness</p>
        </div>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_text, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())

        return {
            "status": "success",
            "message": f"Reminder email successfully sent to {to_email}",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send reminder email: {str(e)}",
        }
