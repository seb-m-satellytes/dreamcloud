# dreamboard/firebase.py
import os
import firebase_admin
import base64
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, storage

load_dotenv()

firebase_config = {
    "type": os.getenv('TYPE'),
    "project_id": os.getenv('PROJECT_ID'),
    "private_key_id": os.getenv('PRIVATE_KEY_ID'),
    "private_key": base64.b64decode(os.getenv('PRIVATE_KEY')).decode().replace('\\n', '\n'),  # Private keys often have newlines in them
    "client_email": os.getenv('CLIENT_EMAIL'),
    "client_id": os.getenv('CLIENT_ID'),
    "auth_uri": os.getenv('AUTH_URI'),
    "token_uri": os.getenv('TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('CLIENT_X509_CERT_URL')
}

cred = credentials.Certificate(firebase_config)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "storageBucket": "beeref-cloud.appspot.com"
    })

db = firestore.client()
bucket = storage.bucket()


def get_firestore():
    return db


def get_storage():
    return bucket


def fetch_default_user_name():
    # Get a reference to the 'default-user' collection
    users_ref = db.collection('default-user')

    # Fetch all documents from the collection
    docs = users_ref.stream()

    # Loop over the documents
    for doc in docs:
        # Assume that each document has a 'name' field and print it
        name = doc.to_dict().get('name')
        if name:
            print(f'Name: {name}')
