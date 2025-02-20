from dotenv import load_dotenv
from flask import Flask, jsonify, request
import json
import os
import smtplib
import ssl

load_dotenv()
application = Flask(__name__)
webhook_route = os.environ["SECRET_ROUTE"]


port = 587  # For starttls
smtp_server = os.environ["SMTP_SERVER"]
sender_email = os.environ["SMTP_USER"]
receiver_email = os.environ["APP_EMAIL"]
password = os.environ["SMTP_PASSWORD"]


@application.route("/")
def index():
    return jsonify({"result": "Home OK"})


@application.route(webhook_route, methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return jsonify({"result": f"GET {webhook_route} OK"})

    input_data = request.get_json()
    message = f"""\
Subject: Notif GRIST
To: {receiver_email}
{json.dumps(input_data, indent=2)}"""

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

    return jsonify({"result": "POST OK"})
