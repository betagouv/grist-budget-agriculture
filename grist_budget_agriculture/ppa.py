from grist_api import GristDocAPI
import json
import pandas as pd
import tempfile

SERVER = "https://grist.numerique.gouv.fr"
DOC_ID = "3y9TdQbW2Uqa"


def find_personal(org, user_id):
    if "owner" not in org or org["owner"] is None:
        return False
    if "id" not in org["owner"]:
        return False
    return org["owner"]["id"] == user_id


def generate_choices(column):
    options = json.loads(column["fields"]["widgetOptions"])
    fields = column["fields"]
    field_type = fields["type"]
    if field_type == "Choice":
        return options["choices"]
    elif field_type == "Bool":
        return [True, False]
    else:
        return []


def main(output):
    api = GristDocAPI(DOC_ID, server=SERVER)
    user_info = api.call("/api/profile/user", prefix="").json()
    org_list = api.call("/api/orgs", prefix="").json()

    personal_org = [o for o in org_list if find_personal(o, user_info["id"])]
    org_info = personal_org[0]

    org_id = org_info["id"]
    tmp_name = "tmp_worspace"
    ws_id = api.call(
        f"/api/orgs/{org_id}/workspaces",
        json_data={"name": tmp_name},
        method="POST",
        prefix="",
    ).json()

    doc_info = api.call("").json()
    doc_id = doc_info["id"]
    copy_response = api.call(
        f"/api/docs/{doc_id}/copy",
        json_data={
            "documentName": doc_info["name"],
            "workspaceId": ws_id,
            "asTemplate": True,
        },
        prefix="",
    )
    new_doc_id = copy_response.json()

    new_api = api = GristDocAPI(new_doc_id, server=SERVER)
    tables = new_api.call("tables").json()["tables"]

    for table in tables:
        table_name = table["id"]
        columns = new_api.columns(table_name).json()["columns"]
        index_columns = [c for c in columns if c["fields"]["formula"] == ""]
        names = [c["id"] for c in index_columns]

        levels = [generate_choices(c) for c in index_columns]
        mi = pd.MultiIndex.from_product(levels, names=names)

        records = [{n: v for (n, v) in zip(mi.names, values)} for values in mi.values]
        new_api.add_records(table_name, records, chunk_size=1000)

    xslx_response = new_api.call("download/xlsx")
    output.write(xslx_response.content)

    api.call(f"/api/workspaces/{ws_id}", method="DELETE", prefix="")


if __name__ == "__main__":
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as a:
        main(a)
        print(a.name)
