from dotenv import load_dotenv
from flask import Flask, jsonify, request
import json
import os

import access
import send_email

load_dotenv()
application = Flask(__name__)
webhook_route = os.environ["SECRET_ROUTE"]


@application.route("/")
def index():
    return jsonify({"result": "Home OK"})


@application.route(
    f"{webhook_route}",
    defaults={"type": "none", "action": "none"},
    methods=["GET", "POST"],
)
@application.route(
    f"{webhook_route}/<type>", defaults={"action": "none"}, methods=["GET", "POST"]
)
@application.route(f"{webhook_route}/<type>/<action>", methods=["GET", "POST"])
def webhook(type, action):
    if request.method == "GET":
        return jsonify({"result": f"GET {webhook_route}/{type}/{action} OK"})

    input_data = request.get_json()
    send_email.send(
        "Notif GRIST",
        json.dumps(
            {"type": type, "action": action, "input_data": input_data}, indent=2
        ),
    )
    return jsonify({"result": "POST OK"})


@application.route(f"{webhook_route}/personnes", methods=["POST"])
def personne_webhook():
    access.update()
    return jsonify({"result": "OK"})
