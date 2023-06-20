# dreamboard/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore, storage

cred = credentials.Certificate('secrets/dreamboard-cloud-firebase-adminsdk-516n3-b042c30828.json')

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
