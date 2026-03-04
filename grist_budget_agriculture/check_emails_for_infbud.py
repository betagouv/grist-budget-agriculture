import dotenv
import email.header
import email.parser
import email.utils
from imap_tools import MailBox
import imaplib2
import io
import logging
import os
import re
import sys
import pandas as pd

from grist_budget_agriculture.grist import api
import grist_budget_agriculture.send_email as send_email

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("grist_budget_agriculture"), autoescape=select_autoescape()
)


dotenv.load_dotenv()
logger = logging.getLogger(__name__)
xlsx_re = re.compile(".*INFBUD53.*\.xlsx")


def get_xlsx(msg):
    for part in msg.walk():
        name = part.get_filename()
        if name and xlsx_re.match(name):
            return part.get_payload(decode=True)
    return None


def process_email(msg):
    result = get_xlsx(msg)
    if result is None:
        logger.info("Pas de ficher xlsx en pièce jointe de l'email")
        return None
    return result


def process_file(infbud_df):
    infbud_df["NoEJ"] = (
        infbud_df["N°EJ (Bon de commande / Marché / Convention / Subvention...)"]
        .fillna(0)
        .astype(int)
        .astype(str)
    )
    infbud_df["NoDP"] = infbud_df["N° DP"].str[13:]
    # Correspondance numéro de la ligne sur Excel
    infbud_df["ligne_excel"] = infbud_df.index + 2

    bcs = api.fetch_table("Bons_de_commande")
    grist_bc_df = pd.DataFrame(bcs)
    grist_bc_df["annee_bc"] = pd.to_datetime(grist_bc_df["Date_BDC"], unit="s").dt.year
    col_total = "Montant TOTAL engagé (b)"
    ej_rows = [
        "ligne_excel",
        "Bascule des EJ non soldés (EJ années antérieures) (a)",
        "Montant EJ engagés Année en cours (= b - a)",
        col_total,
    ]
    # Somme les lignes relatives à un même EJ
    ae_df = (
        infbud_df[~infbud_df[col_total].isna()][["NoEJ", *ej_rows]]
        .groupby("NoEJ")
        .sum()
    )

    check_ae_df = ae_df.merge(
        grist_bc_df, left_index=True, right_on="NoBDC", how="right"
    )
    should_be_empty_bc_df = check_ae_df[
        (~check_ae_df[col_total].isna())
        * (check_ae_df[col_total] != check_ae_df["Montant_engage"])
    ]
    clean_should_be_empty_bc_df = should_be_empty_bc_df.rename(
        columns={col_total: "Montant Chorus", "Montant_engage": "Montant Grist"}
    )[["ligne_excel", "NoBDC", "annee_bc", "Montant Chorus", "Montant Grist"]]

    sfs = api.fetch_table("Services_Faits")
    grist_sf_df = pd.DataFrame(sfs)
    sf_df = infbud_df[infbud_df["N° SF"] != "#"]
    interesting_sf_df = sf_df.merge(
        grist_bc_df[["NoBDC"]], left_on="NoEJ", right_on="NoBDC"
    )
    check_sf_df = interesting_sf_df.merge(
        grist_sf_df, left_on="N° SF", right_on="No_SF", how="left"
    )
    missing_sf = check_sf_df[check_sf_df.id.isna()][
        ["NoEJ", "N° SF", "Montant réceptionné"]
    ]

    template = env.get_template("check_emails_for_infbud.html")
    return template.render(
        ej_count=ae_df.shape[0],
        match_count=sum(~check_ae_df[col_total].isna()),
        bogus_bc_count=clean_should_be_empty_bc_df.shape[0],
        bogus_bc=clean_should_be_empty_bc_df.to_html(index=False),
        sf_count=sf_df.shape[0],
        interesting_sf_count=interesting_sf_df.shape[0],
        missing_sf_count=missing_sf.shape[0],
        missing_sf=missing_sf.to_html(index=False),
    )


def report_analysis(num, msg):
    logger = logging.getLogger()
    output = io.StringIO()
    ch = logging.StreamHandler(output)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    logger.info(f"Traitement de l'email {num}")

    doc_bytes = process_email(msg)

    html_result = "<p>Bug. empty. check. code. Humans are disappointing.</p>"
    if doc_bytes:
        doc = io.BytesIO(doc_bytes)
        df = pd.read_excel(doc)

        html_result = process_file(df)

    ch.flush()
    send_email.send(
        "Traitement automatique de l'email",
        output.getvalue(),
        html_result,
        InReplyTo=msg.get("Message-Id"),
    )
    logger.removeHandler(ch)
    output.close()


def main():
    with MailBox(os.environ["IMAP_SERVER"]).login(
        os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"], initial_folder="Spam"
    ) as mailbox:
        mailbox.move(mailbox.uids(), "INBOX", chunks=100)

    M = imaplib2.IMAP4_SSL(host=os.environ["IMAP_SERVER"], port=993)
    M.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
    M.SELECT(readonly=False)

    subject = "[liste-compta-ruche] [BOWEBI] INFBUD53"
    search = '(UNSEEN SUBJECT "{}")'.format(subject)
    typ, data = M.SEARCH(None, search)
    ll = data[0].decode().split()

    bp = email.parser.BytesParser()
    for num in ll:
        typ2, data2 = M.FETCH(num, "RFC822")
        v = data2[0][1]
        msg = bp.parsebytes(v)
        report_analysis(num, msg)

    M.close()
    M.logout()
    logger.info("Finished")


def test():
    file = sys.argv[-1]
    if not file.endswith(".xlsx"):
        print("Il faut fournir un fichier Excel (.xlsx) d'une INFBUD53")
        return
    df = pd.read_excel(file)
    html = process_file(df)
    print(html)


if __name__ == "__main__":
    test()
