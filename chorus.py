import os
import pandas as pd
import requests
import tempfile
import inf_bud_53


def get_chorus_data(filepath):
    df = pd.read_csv(filepath, sep=";", header=4, thousands=" ", decimal=",", dtype=str)
    idx_cols = df.columns
    year_field = idx_cols[-1]
    value_field = "Montant Chorus"
    df.columns = pd.Index(
        [*idx_cols.values[:7], "Type montant", "Exercice comptable", value_field]
    )
    df["Exercice comptable"] = int(year_field)
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
    df["Date de base de la DP - date"] = pd.to_datetime(
        df["Date de base de la DP"], errors="coerce", format="%d.%m.%Y"
    )

    res = df[(~agg_rows) * (~df[value_field].isna())]

    return res


def merge_grist(df, gristBC, gristSF):
    bccol = "NoBDC"
    sfcol = "No_SF"
    df_join = df.merge(
        gristBC[gristBC[bccol] != ""],
        left_on="N° EJ",
        right_on=bccol,
        how="right",
        suffixes=("_CHORUS", "_BC"),
    ).merge(
        gristSF,
        left_on="N° SF",
        right_on=sfcol,
        how="outer",
        suffixes=("_CHORUS", "_SF"),
    )
    return df_join


def download_infbud_csv(token_info, attachment_id):
    url = f"{token_info['baseUrl']}/attachments/{attachment_id}/download?auth={token_info['token']}"
    response = requests.get(url)
    with tempfile.NamedTemporaryFile(suffix=".csv") as fd:
        for chunk in response.iter_content(chunk_size=128):
            fd.write(chunk)
        fd.seek(os.SEEK_SET, 0)
        return get_chorus_data(fd.name)


def build_url(token_info, table_name):
    return f"{token_info['baseUrl']}/tables/{table_name}/records?auth={token_info['token']}"


def fetch_grist(token_info, table):
    url = build_url(token_info, table)
    response = requests.get(url)
    grist_data = response.json()
    records = grist_data["records"]
    return pd.DataFrame([{"id": r["id"], **r["fields"]} for r in records])


def build_df(initial_df, token_info):
    bcs = fetch_grist(token_info, "Bons_de_commande")
    sfs = fetch_grist(token_info, "Services_Faits")
    df = merge_grist(initial_df, bcs, sfs)

    columns = (
        df.columns
    )  # [*initial_df.columns.values, "NoBDC", "Montant_AE", "Numero_BC", "Montant_CP"]
    return df[columns].sort_values(
        ["N° EJ", "Exercice comptable", "Type montant", "NoBDC"]
    )


def to(ext, result, dest):
    if ext == "pickle":
        result.to_pickle(dest)
        dest.seek(os.SEEK_SET, 0)
    else:
        with pd.ExcelWriter(dest, engine="xlsxwriter") as writer:
            result.to_excel(writer, sheet_name="summary")
            writer.sheets["summary"].autofit()


def inf_bud_53_filter(context, dest):
    token_info = context["tokenInfo"]
    attachments = context["record"][context["mapping"]["Piece_jointe"]]
    attachment_id = attachments[0]
    initial_df = download_infbud_csv(token_info, attachment_id)

    result = build_df(initial_df, token_info)

    to(context["format"], result, dest)


def inf_bud_53_aggregate(context, dest):
    token_info = context["tokenInfo"]
    field_name = context["mapping"]["Piece_jointe"]

    url = build_url(token_info, "INF_BUD_53")
    response = requests.get(url)
    grist_data = response.json()
    records = grist_data["records"]
    restits = pd.DataFrame([r["fields"] for r in records])
    restits.sort_values(["Cree_a"], inplace=True)
    vals = restits.groupby("Annee").last()

    attachment_ids = [attachment_ids[1] for attachment_ids in vals[field_name]]

    dfs = [
        download_infbud_csv(token_info, attachment_id)
        for attachment_id in attachment_ids
    ]
    initial_df = pd.concat(dfs)
    result = build_df(initial_df, token_info)
    inf_bud_53.add_check_column(result)

    to(context["format"], result, dest)


# « Montants engagé » : somme des montants consommés par l’EJ au statut « commande » au niveau du poste de l’EJ. L’indicateur se base sur la date d’impact budgétaire de l’EJ ;
# « Montant réceptionné » : somme des services faits TTC au niveau des postes de l’EJ. L’indicateur se base sur la date d’impact budgétaire de l’EJ auquel se réfère le service fait ;
# « Montant facturé » : somme des montants facturés des DP directes et des montants facturés des DP sur EJ ;
# « Montant payé » : somme des montants payés DP directes + montants payés DP sur EJ + montants PSOP/hors PSOP + écritures correctives + opérations de régularisation


# « Montant engagé » : montant des postes d’EJ engagés dans l’exercice en cours + bascule des EJ non soldés. Le montant inclut les montants basculés et les montants cumulés depuis le 1er janvier de l’exercice sélectionné ;
# « Montant certifié non soldé » : montant des postes de SF certifiés (codes 101 ou 105) non soldés par une DP au statut « facturé » ou « payé » ou non annulés par un SF avec code mouvement 102 ou 106. Cette colonne n’est pertinente que pour l’année en cours ;
# « Montant préenregistré » : montant des DP au statut « préenregistré complet ». Il s’agit du montant cumulé depuis le 1er janvier de l’année sélectionnée. Cette colonne n’est valable que pour l’année en cours ;
# « Montant facturé » : montant des DP au statut « facturé ». Cet indicateur n’est pas pertinent sur les années antérieures ;
# « Montant payé » : montant des postes dont le statut est payé.
