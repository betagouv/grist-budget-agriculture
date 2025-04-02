from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
import json
import os
import shutil
import tempfile

import access
import generate_pdf
import notifications
import send_email


load_dotenv()
application = Flask(__name__)
webhook_route = os.environ["SECRET_ROUTE"]


@application.route("/")
def index():
    return jsonify({"result": "Home OK"})


@application.route("/pdf")
def pdf():
    with tempfile.NamedTemporaryFile(suffix=".ott") as a:
        shutil.copy("files/CACSF.odt", a.name)
        generate_pdf.run_cmd(a.name, os.path.dirname(a.name))
        root, _ = os.path.splitext(a.name)
        return send_file(f"{root}.pdf", download_name="CACSF.pdf", as_attachment=True)


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

    if type == "notifications":
        for n in input_data:
            msg = notifications.build_message(n)
            send_email.send_message(msg)
    else:
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
