import dotenv
import email.header
import email.parser
import email.utils
import imaplib2
import logging
import os
from pypdf import PdfReader
import re
import tempfile
import zipfile
from grist import api, uploadAttachment

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


def extract_BC(raw_subject):
    sections = email.header.decode_header(raw_subject)
    subject = "".join([p[0].decode(p[1]) if p[1] else p[0].decode() for p in sections])
    nbc = re.compile("(?:BDC_)(\d{10})(?:_)").findall(subject)
    assert len(nbc) == 1
    return nbc[0]


def extract_amounts(msg):
    for part in msg.walk():
        print(part.get_content_type(), part.is_multipart())


def write_zip(msg, tzf):
    for part in msg.walk():
        if part.get_content_type() == "application/x-zip-compressed":
            v = part.get_payload(decode=True)
            tzf.write(v)
            return tzf
    return None


def process_email(msg, bcs):
    res = email.utils.parseaddr(msg.get("From"))
    if res[1] != "bdc-rpa.aife@finances.gouv.fr":
        logging.debug("Message ne provenant pas de l'AIFE")
        return
    s = msg.get("Subject")
    nbc = extract_BC(s)
    bcm = [bc for bc in bcs if bc.NoBDC == nbc]
    if len(bcm) == 1:
        logger.info("Déjà inscrit")
        return
    elif len(bcm) > 1:
        logger.warn("Plusieurs correspondances en N°EJ")
        return
    with tempfile.TemporaryFile() as tzf:
        result = write_zip(msg, tzf)
        if result is None:
            logger.warn("Pas de ficher ZIP en pièce jointe de l'email")
            return
        tzf.seek(0)
        zf = zipfile.ZipFile(tzf)
        pdf = [f for f in zf.infolist() if f.orig_filename.startswith("BDC_")]
        bc = pdf[0]
        with tempfile.TemporaryFile() as tf:
            tf.write(zf.read(bc.orig_filename))
            tf.seek(0)
            reader = PdfReader(tf)
            page = reader.pages[0]
            text = page.extract_text()
            numberMatches = re.compile("\d{0,3} \d{3},\d{2}").findall(text)
            numbers = [
                float(n.replace(" ", "").replace(",", ".")) for n in numberMatches
            ]
            brbs = list(set(re.compile("BRB[^ ]+").findall(text)))

            if brbs:
                brb = brbs[0]
                bm = [bc for bc in bcs if bc.No_DA == brb and bc.Montant_AE in numbers]
                if len(bm) == 1:
                    record = bm[0]
            mm = [bc for bc in bcs if bc.Montant_AE in numbers]
            if len(mm) == 1:
                record = mm[0]
            else:
                logger.error("Pas de correspondances")
                return

            tf.seek(0)
            a_id = uploadAttachment((bc.orig_filename, tf.read()))
            bdc_file = [*record.bdc_file, a_id] if record.bdc_file else ["L", a_id]
            api.update_records(
                "Bons_de_commande",
                [{"id": record.id, "NoBDC": nbc, "bdc_file": bdc_file}],
            )
            logger.warning("Ajout du N° de BC et du PDF du BC pour %s" % nbc)


def for_BC():
    M = imaplib2.IMAP4_SSL(host=os.environ["IMAP_SERVER"], port=993)
    M.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
    M.SELECT()

    subject = "Envoi BDC_"
    search = '(UNSEEN SUBJECT "{}")'.format(subject)
    typ, data = M.SEARCH(None, search)
    ll = data[0].decode().split()

    bcs = api.fetch_table("Bons_de_commande")

    bp = email.parser.BytesParser()
    results = []
    for num in reversed(ll):
        typ2, data2 = M.FETCH(num, "RFC822")
        v = data2[0][1]
        msg = bp.parsebytes(v)
        results.append(process_email(msg, bcs))

    M.close()
    M.logout()
    logger.warning("Finished")
