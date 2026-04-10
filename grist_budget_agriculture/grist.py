"""
Ces fonctions font le lien avec l'API de Grist
En particulier, le contournement du bug lié aux pièces jointes.
"""

from dotenv import load_dotenv
from grist_api import GristDocAPI
import os
import pandas as pd
import pickle
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


def downloadAttachment(a_id):
    attachment_id = int(a_id)
    rel_path = f"tmp/a_{int(a_id)}"
    if os.path.exists(rel_path):
        return rel_path

    response = api.call(f"attachments/{attachment_id}/download", method="GET")
    with open(rel_path, "wb") as f:
        f.write(response.content)
    return rel_path


def getDataframe(name):
    records = api.fetch_table(name)
    return pd.DataFrame(records)


def getCachedDataframe(name):
    with open(".grist-cache", "rb") as file:
        return pickle.load(file)[name]


def cacheDF():
    table_names = ["Bons_de_commande", "Services_Faits"]
    results = {table: pd.DataFrame(api.fetch_table(table)) for table in table_names}
    with open(".grist-cache", "wb") as file:
        pickle.dump(results, file)


if __name__ == "__main__":
    cacheDF()
