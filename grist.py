from dotenv import load_dotenv
from grist_api import GristDocAPI
import os
import requests

load_dotenv()

api = GristDocAPI(
    os.environ["GRIST_DOC_ID"],
    server=os.environ["GRIST_SERVER"],
    api_key=os.environ["GRIST_API_KEY"],
)


def updateAttachmentField(context):
    token = context["tokenInfo"]["token"]
    id_to_check = context["attachmentIds"][-1]
    url = f"{context['tokenInfo']['baseUrl']}/attachments/{id_to_check}?auth={token}"
    check_response = requests.get(url)

    if check_response.status_code == 200:
        payload = {"records": context["payload"]}
        response = api.call(f"tables/{context['tableId']}/records", payload, "PATCH")
    else:
        response = None

    return check_response, response
