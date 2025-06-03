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
    types = [
        "Montant engagé",
        "Montant réceptionné",
        "Montant certifié non soldé",
        "Montant pré-enregistré",
        "Montant facturé",
        "Montant payé",
    ]
    df["Type montant"] = (
        df["Type montant"]
        .astype("category")
        .cat.reorder_categories(types, ordered=True)
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
    initial_df = download_infbud_csv(context)
    bcs = fetch_bcs(context["tokenInfo"])
    df = merge_grist(initial_df, bcs)

    columns = [*initial_df.columns.values, "NoBDC", "Montant_AE"]
    res = df[columns].sort_values(["N° EJ", "Type montant", "NoBDC"])

    if context["format"] == "pickle":
        res.to_pickle(dest)
        dest.seek(os.SEEK_SET, 0)
    else:
        with pd.ExcelWriter(dest, engine="xlsxwriter") as writer:
            res.to_excel(writer, sheet_name="summary")
            writer.sheets["summary"].autofit()


# « Montants engagé » : somme des montants consommés par l’EJ au statut « commande » au niveau du poste de l’EJ. L’indicateur se base sur la date d’impact budgétaire de l’EJ ;
# « Montant réceptionné » : somme des services faits TTC au niveau des postes de l’EJ. L’indicateur se base sur la date d’impact budgétaire de l’EJ auquel se réfère le service fait ;
# « Montant facturé » : somme des montants facturés des DP directes et des montants facturés des DP sur EJ ;
# « Montant payé » : somme des montants payés DP directes + montants payés DP sur EJ + montants PSOP/hors PSOP + écritures correctives + opérations de régularisation


# « Montant engagé » : montant des postes d’EJ engagés dans l’exercice en cours + bascule des EJ non soldés. Le montant inclut les montants basculés et les montants cumulés depuis le 1er janvier de l’exercice sélectionné ;
# « Montant certifié non soldé » : montant des postes de SF certifiés (codes 101 ou 105) non soldés par une DP au statut « facturé » ou « payé » ou non annulés par un SF avec code mouvement 102 ou 106. Cette colonne n’est pertinente que pour l’année en cours ;
# « Montant préenregistré » : montant des DP au statut « préenregistré complet ». Il s’agit du montant cumulé depuis le 1er janvier de l’année sélectionnée. Cette colonne n’est valable que pour l’année en cours ;
# « Montant facturé » : montant des DP au statut « facturé ». Cet indicateur n’est pas pertinent sur les années antérieures ;
# « Montant payé » : montant des postes dont le statut est payé.
