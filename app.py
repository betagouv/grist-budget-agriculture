from dotenv import load_dotenv
from flask import Flask, jsonify, request
import json
import os

import send_email

load_dotenv()
application = Flask(__name__)
webhook_route = os.environ["SECRET_ROUTE"]


@application.route("/")
def index():
    return jsonify({"result": "Home OK"})


@application.route(webhook_route, methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return jsonify({"result": f"GET {webhook_route} OK"})

    input_data = request.get_json()
    send_email.send("Notif GRIST", json.dumps(input_data, indent=2))
    return jsonify({"result": "POST OK"})
