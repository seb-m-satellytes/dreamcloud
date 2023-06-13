# beeref/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore, storage

cred = credentials.Certificate('secrets/beeref-cloud-firebase-adminsdk-516n3-b042c30828.json')

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
        print(f'{doc.id} => {doc.to_dict()}')
        # Assume that each document has a 'name' field and print it
        name = doc.to_dict().get('name')
        if name:
            print(f'Name: {name}')


def upload_to_firebase(file_data, file_name):
    bucket = storage.bucket()
    # Create a new blob and upload the file's content.
    blob = bucket.blob(file_name)

    blob.upload_from_string(
        file_data, content_type='image/png'
    )

    # Make the blob public. This is not necessary if the
    # entire bucket is public.
    # See https://cloud.google.com/storage/docs/access-control/making-data-public.
    blob.make_public()

    # The public URL can be used to directly access the uploaded file via HTTP.
    print(blob.public_url)
    return blob.public_url
