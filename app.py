import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()
application = Flask(__name__)
webhook_route = os.environ["SECRET_ROUTE"]


@application.route("/")
def index():
    return jsonify({"result": "Home OK"})


@application.route(webhook_route)
def webhook():
    return jsonify({"result": f"{webhook_route} OK"})
