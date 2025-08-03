import requests
import logging
import time
from .config import load_config
from pathlib import Path
import smtplib
from email.message import EmailMessage

def notify(message: str, subject: str = "Prediction Logger Notification"):
    """
    Send a notification to all configured channels (Slack, webhook, email).
    Retries Slack/webhook, falls back to secondary, and supports email if configured.
    """
    cfg = load_config()
    slack_url = cfg.get('slack_webhook_url')
    secondary_url = cfg.get('secondary_webhook_url')
    email_to = cfg.get('notify_email_to')
    email_from = cfg.get('notify_email_from')
    smtp_server = cfg.get('smtp_server')
    smtp_port = int(cfg.get('smtp_port', 587)) if cfg.get('smtp_port') else 587
    smtp_user = cfg.get('smtp_user')
    smtp_pass = cfg.get('smtp_pass')
    payload = {'text': message}
    # Slack/webhook with retry
    sent = False
    if slack_url:
        for attempt in range(3):
            try:
                resp = requests.post(slack_url, json=payload, timeout=5)
                resp.raise_for_status()
                logging.info("Slack notification sent")
                sent = True
                break
            except Exception as e:
                logging.error(f"Slack notify attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)
    # Fallback to secondary webhook
    if not sent and secondary_url:
        try:
            resp = requests.post(secondary_url, json=payload, timeout=5)
            resp.raise_for_status()
            logging.info("Secondary webhook notification sent")
            sent = True
        except Exception as e:
            logging.error(f"Secondary webhook notify failed: {e}")
    # Email notification (optional)
    if not sent and email_to and email_from and smtp_server:
        try:
            msg = EmailMessage()
            msg.set_content(message)
            msg['Subject'] = subject
            msg['From'] = email_from
            msg['To'] = email_to
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logging.info("Email notification sent")
            sent = True
        except Exception as e:
            logging.error(f"Email notify failed: {e}")
    if not sent:
        logging.error("All notification channels failed.")