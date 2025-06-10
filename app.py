from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_file
from flask_cors import CORS
import jwt
import json
import os
import requests
import shutil
import tempfile

import access
import chorus
import generate_pdf
import grist
import inf_bud_53
import notifications
import send_email


load_dotenv()
application = Flask(__name__, static_folder="out", static_url_path="")
CORS(application)
webhook_route = os.environ["SECRET_ROUTE"]
subdomain = os.getenv("SUBDOMAIN", "/api")

for root, dirs, files in os.walk(application.static_folder):
    html_files = [f for f in files if f.endswith(".html")]
    if html_files:
        clean_root = root[len(application.static_folder) + 1 :]
        for html_subpath in html_files:
            html_file_path = os.path.join(clean_root, html_subpath)
            public_subpath = os.path.splitext(html_file_path)[0]

            public_directory, file_name = os.path.split(html_file_path)
            if file_name == "index.html":
                application.add_url_rule(
                    f"{application.static_url_path}/{public_directory}",
                    endpoint="static",
                    defaults={"filename": html_file_path},
                )
            application.add_url_rule(
                f"{application.static_url_path}/{public_subpath}",
                endpoint="static",
                defaults={"filename": html_file_path},
            )


@application.route(f"{subdomain}/")
def index():
    return jsonify({"result": f"Home OK at {subdomain}"})


@application.route(f"{subdomain}/redirect-service-fait")
def redirect_service_fait():
    response = grist.api.call("tables/Services_Faits/records?sort=-id&limit=1")
    data = response.json()
    object_id = data["records"][0]["id"]
    return redirect(
        f"https://grist.numerique.gouv.fr/o/masaf/9mbWaZNUvym2/Budget/p/97#a1.s472.r{object_id}.c143"
    )


@application.route(f"{subdomain}/pdf")
def pdf():
    with tempfile.NamedTemporaryFile(suffix=".ott") as a:
        shutil.copy("files/CACSF.odt", a.name)
        generate_pdf.run_cmd(a.name, os.path.dirname(a.name))
        root, _ = os.path.splitext(a.name)
        return send_file(f"{root}.pdf", download_name="CACSF.pdf", as_attachment=True)


@application.route(
    f"{subdomain}{webhook_route}",
    defaults={"type": "none", "action": "none"},
    methods=["GET", "POST"],
)
@application.route(
    f"{subdomain}{webhook_route}/<type>",
    defaults={"action": "none"},
    methods=["GET", "POST"],
)
@application.route(
    f"{subdomain}{webhook_route}/<type>/<action>",
    methods=["GET", "POST"],
)
def webhook(type, action):
    if request.method == "GET":
        return jsonify({"result": f"GET {webhook_route}/{type}/{action} OK"})

    input_data = request.get_json()

    if type == "notifications":
        for n in input_data:
            msg = notifications.build_message(n)
            send_email.send_message(msg)
    elif type == "scalingo":
        data = {
            "text": "Notification Scalingo",
            "props": {"card": f"```json\n{json.dumps(input_data, indent=2)}\n```"},
        }
        requests.post(
            os.environ["MATTERMOST_WEBHOOK"],
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
    else:
        send_email.send(
            "Notif GRIST",
            json.dumps(
                {"type": type, "action": action, "input_data": input_data}, indent=2
            ),
        )
    return jsonify({"result": f"POST {type}/{action} OK"})


@application.route(f"{subdomain}{webhook_route}/personnes", methods=["POST"])
def personne_webhook():
    access.update()
    return jsonify({"result": "OK"})


@application.route(f"{subdomain}/grist-proxy/attachment", methods=["POST"])
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


@application.route(f"{subdomain}/chorus/inf-bud-53", methods=["POST"])
def chorus_inf_bud_53():
    input_data = request.get_json()
    with tempfile.NamedTemporaryFile() as dest:
        result = chorus.inf_bud_53_filter(input_data)

        file_ext = input_data["format"]
        chorus.to(file_ext, result, dest)
        return send_file(dest.name, download_name=f"INF_BUD_53.{file_ext}")


@application.route(f"{subdomain}/chorus/inf-bud-53/aggregate", methods=["POST"])
def chorus_inf_bud_53_aggregate():
    input_data = request.get_json()
    with tempfile.NamedTemporaryFile() as dest:
        df = chorus.inf_bud_53_aggregate(input_data)

        old = chorus.inf_bud_53_aggregate(input_data, True)
        old["Nouvelle ligne"] = False
        result = df.merge(old, how="left")
        result["Nouvelle ligne"].fillna(True, inplace=True)

        inf_bud_53.add_check_column(result)

        file_ext = input_data["format"]
        chorus.to(file_ext, result, dest)
        return send_file(dest.name, download_name=f"INF_BUD_53_a.{file_ext}")
