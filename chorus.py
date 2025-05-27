import os
import pandas as pd
import requests
import tempfile


def get_chorus_data(filepath):
    df = pd.read_csv(filepath, sep=";", header=4, thousands=" ", decimal=",", dtype=str)
    idx_cols = df.columns
    year_field = idx_cols[-1]
    value_field = "Montant Chorus"
    df.columns = pd.Index(
        [*idx_cols.values[:7], "Type montant", "Exercice comptable", value_field]
    )
    df["Exercice comptable"] = year_field
    new_vals = df[value_field].apply(
        lambda v: v if pd.isna(v) else float(v.replace(" ", "").replace(",", "."))
    )
    df[value_field] = new_vals
    agg_columns = df.columns.values[:7]
    agg_rows = df[agg_columns].apply(
        lambda row: row.apply(lambda v: "Résultat" in v).any(), axis=1
    )
    res = df[(~agg_rows) * (~df[value_field].isna())]
    return res


def merge_grist(df, gristDf):
    col = "NoBDC"
    df_join = df.merge(
        gristDf[gristDf[col] != ""], left_on="N° EJ", right_on=col, how="right"
    )
    return df_join


def download_infbud_csv(context):
    token_info = context["tokenInfo"]
    attachments = context["record"][context["mapping"]["Piece_jointe"]]
    attachment_id = attachments[0]
    url = f"{token_info['baseUrl']}/attachments/{attachment_id}/download?auth={token_info['token']}"
    response = requests.get(url)
    with tempfile.NamedTemporaryFile(suffix=".csv") as fd:
        for chunk in response.iter_content(chunk_size=128):
            fd.write(chunk)
        fd.seek(os.SEEK_SET, 0)
        return get_chorus_data(fd.name)


def fetch_bcs(token_info):
    url = f"{token_info['baseUrl']}/tables/Bons_de_commande/records?auth={token_info['token']}"
    response = requests.get(url)
    grist_data = response.json()
    records = grist_data["records"]
    return pd.DataFrame([r["fields"] for r in records])


def inf_bud_53(context, dest):
    df = download_infbud_csv(context)
    bcs = fetch_bcs(context["tokenInfo"])
    res = merge_grist(df, bcs)

    columns = [*df.columns.values, "NoBDC", "Montant_AE"]

    with pd.ExcelWriter(dest, engine="xlsxwriter") as writer:
        res[columns].to_excel(writer, sheet_name="summary")
        writer.sheets["summary"].autofit()
