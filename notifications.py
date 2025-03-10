from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from grist import api


def build_to_field(tos):
    toField = ", ".join(
        [f"{p['fields']['Nom_d_usage']} <{p['fields']['Email']}>" for p in tos]
    )

    return toField


def build_message(notif):
    msg = MIMEMultipart("alternative")

    def bcSubject(props):
        return f"[grist-ruche] BC à suivre {props['NoBDC'] or 'TBD'} d'un montant de {props['Montant_AE']}"

    configs = {
        "Bon_de_commande": {
            "table": "Bons_de_commande",
            "notifProp": "Bon_de_commande",
            "subject": bcSubject,
            "intro": lambda props: f"le bon de commande {props['NoBDC'] or 'TBD'} d'un montant de {props['Montant_AE']}",
        },
        "Service_fait": {
            "table": "Services_Faits",
            "notifProp": "Service_fait",
            "subject": lambda props: f"[grist-ruche] SF à suivre pour le BC {props['gristHelper_Display2']} en date du {props['Date_du_PV']}",
            "intro": lambda props: f"le service fait pour le BC {props['gristHelper_Display2']} en date du {props['Date_du_PV']}",
        },
    }

    ids = [notif["Personne_emettrice"], *notif["Destinataires"][1:]]
    idString = json.dumps(ids)

    peopleResponse = api.call(f'tables/Personnes/records?filter={{"id": {idString}}}')
    peopleData = peopleResponse.json()["records"]

    config = configs["Bon_de_commande" if notif["Bon_de_commande"] else "Service_fait"]

    objectTable = config["table"]
    objectId = notif[config["notifProp"]]

    objectResponse = api.call(
        f'tables/{objectTable}/records?filter={{"id": [{objectId}]}}&hidden=true'
    )
    objectData = objectResponse.json()["records"][0]
    link = objectData["fields"]["Lien"].split(" ", 1)[1]

    msg["Subject"] = config["subject"](objectData["fields"])

    sender = [p for p in peopleData if p["id"] == notif["Personne_emettrice"]][0]
    senderName = sender["fields"]["Nom_d_usage"]
    senderEmail = sender["fields"]["Email"]

    tos = [p for p in peopleData if p["id"] in notif["Destinataires"]]
    toField = build_to_field(tos)

    msg["To"] = toField
    msg["Cc"] = f"{senderName} <{senderEmail}>"

    intro = config["intro"](objectData["fields"])
    part1 = MIMEText(
        f"""
Bonjour,

{senderName} vous a attribué {intro}.

C'est accessible au lien suivant {link}.

Le commentaire suivant a été ajouté :
«
{notif["Commentaires"]}
»
""",
        "plain",
        "utf-8",
    )
    msg.attach(part1)
    return msg
