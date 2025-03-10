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


def send_message(msg):
    msg["From"] = f"Equipe Budget Ruche Numerique <{sender_email}>"

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.send_message(msg)


def send(subjet, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subjet
    msg["To"] = receiver_email
    full_body = "\n\n".join(
        [body, "Message automatique de github.com/betagouv/notifs-grist-agriculture"]
    )
    part1 = MIMEText(full_body, "plain", "utf-8")
    msg.attach(part1)

    send_message(msg)
