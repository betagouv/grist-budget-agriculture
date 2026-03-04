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

import grist_budget_agriculture.send_email as send_email

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
    infbud_df["id"] = infbud_df.index

    col_total = "Montant TOTAL engagé (b)"
    ej_rows = [
        "Bascule des EJ non soldés (EJ années antérieures) (a)",
        "Montant EJ engagés Année en cours (= b - a)",
        col_total,
    ]
    ae_df = (
        infbud_df[~infbud_df[col_total].isna()][["NoEJ", *ej_rows]]
        .groupby("NoEJ")
        .sum()
    )
    return ae_df


def report_analysis(num, msg):
    logger = logging.getLogger()
    output = io.StringIO()
    ch = logging.StreamHandler(output)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    logger.info(f"Traitement de l'email {num}")

    doc_bytes = process_email(msg)

    html = None
    if doc_bytes:
        doc = io.BytesIO(doc_bytes)
        df = pd.read_excel(doc)

        result_df = process_file(df)

        html = io.StringIO()
        html.write("<h1>RECAP</h1>")
        html.write(result_df.to_html())
        html.write("\n")

    ch.flush()
    send_email.send(
        "Traitement automatique de l'email",
        output.getvalue(),
        html.getvalue(),
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
    result_df = process_file(df)
    print(result_df)


if __name__ == "__main__":
    test()
