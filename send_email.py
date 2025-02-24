from dotenv import load_dotenv
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


load_dotenv()
port = 587  # For starttls
smtp_server = os.environ["SMTP_SERVER"]
sender_email = os.environ["SMTP_USER"]
receiver_email = os.environ["APP_EMAIL"]
password = os.environ["SMTP_PASSWORD"]


def send(subjet, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subjet
    msg["From"] = sender_email
    msg["To"] = receiver_email
    part1 = MIMEText(body, "plain", "utf-8")
    msg.attach(part1)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.send_message(msg)
