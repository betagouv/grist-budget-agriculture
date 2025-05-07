from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_file
from flask_cors import CORS
import jwt
import json
import os
import shutil
import tempfile

import access
import generate_pdf
import grist
import notifications
import send_email


load_dotenv()
application = Flask(__name__)
CORS(application)
webhook_route = os.environ["SECRET_ROUTE"]


@application.route("/")
def index():
    return jsonify({"result": "Home OK"})


@application.route("/redirect-service-fait")
def redirect_service_fait():
    response = grist.api.call("tables/Services_Faits/records?sort=-id&limit=1")
    data = response.json()
    object_id = data["records"][0]["id"]
    return redirect(
        f"https://grist.numerique.gouv.fr/o/masaf/9mbWaZNUvym2/Budget/p/97#a1.s472.r{object_id}.c143"
    )


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


@application.route("/grist-proxy/attachment", methods=["POST"])
def grist_proxy_attachment():
    input_data = request.get_json()
    jwt_details = jwt.decode(
        input_data["tokenInfo"]["token"], options={"verify_signature": False}
    )

    check_responses, response = grist.updateAttachmentField(input_data)
    result = {
        "jwt details": jwt_details,
        "table id": input_data["tableId"],
        "payload": input_data["payload"],
        "check status": [c.status_code for c in check_responses],
        "response status": response.status_code if response else None,
    }

    send_email.send(
        "[Notif GRIST] fix grist attachment",
        json.dumps(result, indent=2),
    )

    return jsonify(result)
