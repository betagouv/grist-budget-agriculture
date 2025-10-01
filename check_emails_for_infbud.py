import datetime
import dotenv
import email.header
import email.parser
import email.utils
import imaplib2
import io
import logging
import os
import re
from grist import api, uploadAttachment

import send_email

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


def report_analysis(msg):
    logger = logging.getLogger()
    output = io.StringIO()
    ch = logging.StreamHandler(output)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    process_email(msg)

    ch.flush()
    send_email.send(
        "Traitement automatique de l'email",
        output.getvalue(),
        InReplyTo=msg.get("Message-Id"),
    )
    logger.removeHandler(ch)
    output.close()


def main():
    bcs = api.fetch_table("Bons_de_commande")
    infbuds = api.fetch_table("INF_BUD_53", {"Annee": 2025})
    infbud = sorted(infbuds, key=lambda x: x.Cree_a, reverse=True)[0]

    M = imaplib2.IMAP4_SSL(host=os.environ["IMAP_SERVER"], port=993)
    M.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
    M.SELECT(readonly=False)

    subject = "[liste-compta-ruche] [BOWEBI] INFBUD53"
    search = '(UNSEEN SUBJECT "{}")'.format(subject)
    typ, data = M.SEARCH(None, search)
    ll = data[0].decode().split()

    infbud = api.fetch_table("INF_BUD_53", {"Annee": 2025, "Type": "Automatique"})
    logger.info(bcs)
    logger.info(infbud)

    bp = email.parser.BytesParser()
    for num in ll:
        print(num)
        typ2, data2 = M.FETCH(num, "RFC822")
        v = data2[0][1]
        msg = bp.parsebytes(v)
        report_analysis(msg)

    M.close()
    M.logout()
    logger.info("Finished")
