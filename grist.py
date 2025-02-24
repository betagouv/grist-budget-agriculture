from dotenv import load_dotenv
from grist_api import GristDocAPI
import os

load_dotenv()

api = GristDocAPI(
    os.environ["GRIST_DOC_ID"],
    server=os.environ["GRIST_SERVER"],
    api_key=os.environ["GRIST_API_KEY"],
)
