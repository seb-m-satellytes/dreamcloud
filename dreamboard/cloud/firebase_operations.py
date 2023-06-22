import logging
import dreamboard.user_instance as user_instance
from dreamboard import firebase
from firebase_admin import storage, firestore
from datetime import datetime
from dreamboard.items import DreambPixmapItem
from PyQt6 import QtCore, QtGui
import os
import uuid

logger = logging.getLogger(__name__)


def fetch_boards():
    """Fetch all board documents from Firestore."""
    db = firebase.get_firestore()
    boards = []

    try:
        # Get reference to the users collection
        users_col = db.collection("users")
        boards_col = db.collection("boards")

        # Fetch the user document
        user_doc = users_col.document(user_instance.user.id).get()
        if user_doc.exists:
            # Get the list of board ids associated with the user
            board_ids = user_doc.to_dict().get("boards", [])

            print('Board IDs', board_ids)

            for board_id in board_ids:
                board_doc = boards_col.document(board_id).get()
                if board_doc.exists:
                    board = board_doc.to_dict()
                    board["id"] = board_doc.id
                    boards.append(board)
                    logger.info('Fetched boards from cloud.')

            boards = sorted(boards, key=lambda x: x['updated_at'], reverse=True)

    except Exception as e:
        logger.error('Error fetching boards from cloud with error: ' + str(e))

    print('Fetched boards from cloud.', boards)
    return boards


def upload_to_firebase(file_data, file_name):
    bucket = storage.bucket()
    # Create a new blob and upload the file's content.
    blob = bucket.blob(file_name)

    try:
        blob.upload_from_string(
            file_data, content_type='image/png'
        )
        logger.info('Uploaded image to cloud.')
    except Exception as e:
        logger.error('Error uploading image to cloud with error: ' + str(e))


def save_new_image_to_cloud(doc_ref, item):
    # Get image data and upload to Cloud Storage
    data = item.pixmap_to_bytes()
    filepath = os.path.basename(item.filename)
    filename = filepath.replace(" ", "-").lower()

    upload_to_firebase(data, filename)
    image_uuid = str(uuid.uuid4())

    # Create a new image document in Firestore under the board document
    image_data = {
        "filename": filename,
        "storage_url": filename,
        "uuid": image_uuid,
        "x": item.x(),
        "y": item.y(),
        "z": item.zValue(),
        "scale": item.scale(),
        "rotation": item.rotation(),
        "flip": item.flip(),
        "info_text": item.data(1)['meta']['info_text'],
        "source_link": item.data(1)['meta']['source_link'],
        "source_is_local": item.data(1)['meta']['source_is_local'],
        "created_at": firestore.SERVER_TIMESTAMP
    }

    try:
        doc_ref.document(image_uuid).set(image_data)
        logger.info('Saved new image to cloud.')
    except Exception as e:
        logger.error('Error saving new image to cloud with error: ' + str(e))


def update_image_in_cloud(board_images_col, item):
    item_uuid = item.data(0).strip()

    updated_image_data = {
            "x": item.x(),
            "y": item.y(),
            "z": item.zValue(),
            "scale": item.scale(),
            "rotation": item.rotation(),
            "flip": item.flip(),
            "info_text": item.data(1)['meta']['info_text'],
            "source_link": item.data(1)['meta']['source_link'],
            "source_is_local": item.data(1)['meta']['source_is_local'],
            "updated_at": firestore.SERVER_TIMESTAMP
        }
    try:
        board_images_col.document(item_uuid).update(updated_image_data)
        logger.info('Updated image in cloud.')
    except Exception as e:
        logger.error('Error updating image to cloud with error: ' + str(e))


def fetch_presets_from_cloud(board_ref, mainWindow):
    try:
        # Fetch all presets for this board
        board_presets_col = board_ref.collection("presets")
        presets_docs = board_presets_col.stream()

        mainWindow.presets = {}

        for doc in presets_docs:
            mainWindow.presets[doc.id] = doc.to_dict()

        logger.info('Fetched presets from cloud.')
    except Exception as e:
        logger.error('Error fetching presets from cloud with error: ' + str(e))


def create_image_from_cloud(image_data, mainWindow, bucket):
    try:
        # Download the image from Cloud Storage
        blob = bucket.blob(image_data["storage_url"])
        image_data_bytes = blob.download_as_bytes()

        img = QtGui.QImage.fromData(image_data_bytes)

        # Create a new item and add it to the scene
        item = DreambPixmapItem(img, image_data["filename"], mainWindow.toggleSidebar)

        item.set_pos_center(QtCore.QPointF(image_data["x"], image_data["y"]))
        item.setRotation(image_data["rotation"])
        item.setScale(image_data["scale"])

        item.setData(0, image_data["uuid"])

        item.setData(1, {
            "meta": {
                "info_text": image_data["info_text"],
                "source_link": image_data["source_link"],
                "source_is_local": image_data["source_is_local"]
            }
        })

        return item
    except Exception as e:
        logger.error('Error creating image from cloud with error: ' + str(e))


def update_presets_in_cloud(db, doc_ref, local_presets):
    board_presets_col = db.collection("boards").document(doc_ref.id).collection("presets")
    presets_docs = board_presets_col.stream()

    preset_doc_ids = [p.id for p in presets_docs]

    for preset_id, preset in list(local_presets.items()):  # We convert to list for safe iteration while removing items
        # Find presets that are in local_presets but not in the cloud
        if preset_id not in preset_doc_ids:
            logger.info(f'Preset {preset_id} added to cloud')
            try:
                _, new_preset_ref = board_presets_col.add(preset)
                # replace preset_id with firestore id
                local_presets.pop(preset_id)
                local_presets[new_preset_ref.id] = preset
            except Exception as e:
                logger.error('Error adding preset to cloud with error: ' + str(e))
                continue

        else:
            logger.info(f'Preset {preset_id} updated in cloud')
            try:
                board_presets_col.document(preset_id).update(preset)
            except Exception as e:
                logger.error('Error updating preset to cloud with error: ' + str(e))
                continue


def create_board_in_cloud(db, user_doc, board_name) -> str:
    users_col = db.collection("users")

    user_doc = users_col.document(user_instance.user.id).get()
    if user_doc.exists:
        # Create a new board document in Firestore
        board_data = {
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "name": board_name  # use actual board name here
        }

        try:
            _, board_ref = db.collection("boards").add(board_data)
            print('save to doc', user_doc)
            user_doc.update({"boards": firestore.ArrayUnion([board_ref.id])})
            return str(board_ref)
        except Exception as e:
            logger.error('Error creating board in cloud with error: ' + str(e))
            return ''


def save_dreamb_cloud(scene, local_presets, boards_local=None, current_board_id=None, worker=None):
    logger.info('Saving...')
    # Get Firestore client and Cloud Storage bucket
    db = firebase.get_firestore()

    # boards_local = list of boards with name and id
    # current_board = id of current board

    boards_cloud = fetch_boards()
    print('Saving...', boards_local, current_board_id, boards_cloud, [b["id"] for b in boards_cloud])

    # if current_board is not in boards_cloud, create it

    if current_board_id and current_board_id not in [b["id"] for b in boards_cloud]:
        board_name = [b["name"] for b in boards_local if b["id"] == current_board_id][0]
        board_ref = create_board_in_cloud(db, user_instance.user, board_name)
    elif (len(boards_cloud)):
        board_ref = db.collection("boards").document(current_board_id)

        try:
            board_ref.update({"updated_at": datetime.now()})
        except Exception as e:
            logger.error('Error updating board in cloud with error: ' + str(e))
            return

    board_images_col = db.collection("boards").document(board_ref.id).collection("images")

    update_presets_in_cloud(db, board_ref, local_presets)

    # Iterate over each item in the scene
    for i, item in enumerate(scene.items()):
        if (item.isNew):
            save_new_image_to_cloud(board_ref, item)
        else:
            update_image_in_cloud(board_images_col, item)

        # Update the progress if a worker was provided
        if worker:
            worker.progress.emit(i)

    logger.info('Saved!')


def load_dreamb_cloud(scene, mainWindow, board_id=None):
    logger.info('Loading...')
    # Get Firestore client and Cloud Storage bucket
    db = firebase.get_firestore()
    bucket = firebase.get_storage()

    # Fetch all boards, sorted by latest updated_at
    boards = fetch_boards()

    # Make the boards available to the mainWindow
    mainWindow.boards = boards

    if len(boards) > 0:
        if not board_id:
            # Open the first board
            board_id = boards[0]["id"]

        mainWindow.current_board = board_id
        board_ref = db.collection("boards").document(board_id)

        fetch_presets_from_cloud(board_ref, mainWindow)

        try:
            # Fetch all images for this board
            images_col = board_ref.collection("images")
            images_docs = images_col.stream()

            items = []
            # Iterate over each image
            for image_doc in images_docs:
                image_data = image_doc.to_dict()
                logger.info(f'Loading image from file {image_data["storage_url"]}')

                item = create_image_from_cloud(image_data, mainWindow, bucket)

                scene.addItem(item)
                items.append(item)
        except Exception as e:
            logger.error('Error loading images from cloud with error: ' + str(e))
    else:
        logger.info('No boards found.')

    logger.info('Loaded!')
