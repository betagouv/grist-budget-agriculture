from dotenv import load_dotenv
import os
import re
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


def send(subjet, body, html_body=None, **kwargs):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subjet
    msg["To"] = receiver_email
    message = "Message automatique de github.com/betagouv/grist-budget-agriculture"
    for v in kwargs:
        key = re.sub("(?P<prev>[a-z])(?P<cap>[A-Z])", "\g<prev>-\g<cap>", v)
        msg[key] = kwargs[v]
    full_body = "\n\n".join([body, message])
    part1 = MIMEText(full_body, "plain", "utf-8")
    msg.attach(part1)

    if html_body:
        part2 = MIMEText(f"{html_body}<div>{message}</div>", "html", "utf-8")
        msg.attach(part2)

    send_message(msg)


def main():
    send("TEST", "TEST", "TEST")


if __name__ == "__main__":
    main()
