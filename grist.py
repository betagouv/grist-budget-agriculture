from dotenv import load_dotenv
from grist_api import GristDocAPI
import os
import requests
import time

load_dotenv()

api = GristDocAPI(
    os.environ["GRIST_DOC_ID"],
    server=os.environ["GRIST_SERVER"],
    api_key=os.environ["GRIST_API_KEY"],
)


def updateAttachmentField(context):
    token = context["tokenInfo"]["token"]
    check_responses = []
    for id_to_check in context["attachmentIds"]:
        url = (
            f"{context['tokenInfo']['baseUrl']}/attachments/{id_to_check}?auth={token}"
        )
        check_responses.append(requests.get(url))
        time.sleep(0.1)

    if all([c.status_code == 200 for c in check_responses]):
        payload = {"records": context["payload"]}
        response = api.call(f"tables/{context['tableId']}/records", payload, "PATCH")
    else:
        response = None

    return check_responses, response


def uploadAttachment(file):
    files = {"upload": file}
    full_url = "%s/api/docs/%s/attachments" % (api._server, api._doc_id)
    resp = requests.post(
        full_url,
        files=files,
        headers={
            "Authorization": "Bearer %s" % api._api_key,
            "Accept": "application/json",
        },
    )
    return resp.json()[0]
