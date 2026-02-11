import datetime
import dotenv
import email.header
import email.parser
import email.utils
import imaplib2
import io
import itertools
import logging
import os
import re
import pandas as pd
from grist_budget_agriculture.grist import api, uploadAttachment, downloadAttachment

import grist_budget_agriculture.send_email as send_email

dotenv.load_dotenv()
logger = logging.getLogger(__name__)
xlsx_re = re.compile(".*INFBUD53.*\.xlsx")


def get_xlsx(msg):
    for part in msg.walk():
        name = part.get_filename()
        if name and xlsx_re.match(name):
            return (name, part.get_payload(decode=True))
    return None


def process_email(msg):
    result = get_xlsx(msg)
    if result is None:
        logger.info("Pas de ficher xlsx en pièce jointe de l'email")
        return
    dt = datetime.datetime.strptime(msg.get("Date"), "%d %b %Y %H:%M:%S %z")

    a_id = uploadAttachment(result)
    create = {
        "Document": a_id,
        "Annee": 2025,
        "Cree_a": dt,
        "Type": "Automatique",
    }

    api.add_records(
        "INF_BUD_53",
        [create],
    )
    return result


def report_analysis(msg):
    logger = logging.getLogger()
    output = io.StringIO()
    ch = logging.StreamHandler(output)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    doc = process_email(msg)

    html = None
    if doc:
        bcs = api.fetch_table("Bons_de_commande")
        nbcs = [bc.NoBDC for bc in bcs if bc.NoBDC]

        infbuds = api.fetch_table("INF_BUD_53", {"Annee": 2025, "Type": "Automatique"})
        infbud = sorted(infbuds, key=lambda x: x.Cree_a, reverse=True)[0]

        last_doc = downloadAttachment(infbud.Document[1])
        last_df = pd.read_excel(last_doc)
        last = extract_bcs(nbcs, last_df)

        _, doc_content = doc
        df = pd.read_excel(doc_content)
        current = extract_bcs(nbcs, df)

        diff_df = get_diff(last, current)

        if len(diff_df):
            html = io.StringIO()
            html.write("<h1>RECAP</h1>")
            html.write(diff_df.transpose().to_html())
            html.write("\n")

    ch.flush()
    send_email.send(
        "Traitement automatique de l'email",
        output.getvalue(),
        html,
        InReplyTo=msg.get("Message-Id"),
    )
    logger.removeHandler(ch)
    output.close()


def main():
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
        report_analysis(msg)

    M.close()
    M.logout()
    logger.info("Finished")


def extract_bcs(nbcs, df):
    c = "N°EJ (Bon de commande / Marché / Convention / Subvention...)"
    df[c] = df[c].fillna(0).astype(int).astype(str)
    return df[df[c].isin(nbcs)]


def get_diff(df_l, df_c):
    df_l["Ancienne ligne"] = True
    df_c["Nouvelle ligne"] = True
    df = df_c.merge(df_l, how="outer")
    result = df[df["Ancienne ligne"].fillna(False) ^ df["Nouvelle ligne"].fillna(False)]

    del df_l["Ancienne ligne"]
    del df_c["Nouvelle ligne"]
    return result


def test():
    bcs = api.fetch_table("Bons_de_commande")
    nbcs = [bc.NoBDC for bc in bcs if bc.NoBDC]

    infbuds = api.fetch_table("INF_BUD_53", {"Annee": 2025, "Type": "Automatique"})
    sorted_infbuds = sorted(infbuds, key=lambda x: x.Cree_a)

    items = [(i, i.Document[1]) for i in sorted_infbuds][-6:-1]

    def get_extract(a_id):
        doc = downloadAttachment(a_id)
        df = pd.read_excel(doc)
        return extract_bcs(nbcs, df)

    html = io.StringIO()
    html.write("<h1>RECAP</h1>")
    for (item_m_1, last_m_1), (item, last) in itertools.pairwise(items):
        print(datetime.datetime.fromtimestamp(item.Cree_a))
        last_m_1doc = get_extract(last_m_1)
        last_doc = get_extract(last)
        diff_df = get_diff(last_m_1doc, last_doc)

        if len(diff_df):
            url = f"https://grist.numerique.gouv.fr/o/masaf/9mbWaZNUvym2/Budget/p/100?aclAsUser_=thomas.guillet%2Bruche%40beta.gouv.fr#a1.s485.r{item.id}.c2649"
            html.write(
                f'<div><a href="{url}">INF_BUD du {datetime.datetime.fromtimestamp(item.Cree_a)}</a></div>\n'
            )
            html.write(diff_df.to_html())
            html.write("\n")

    send_email.send("test", "GO", html.getvalue())


if __name__ == "__main__":
    test()
