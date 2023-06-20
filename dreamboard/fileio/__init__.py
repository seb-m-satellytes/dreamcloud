# This file is part of DreamBoard.
#
# DreamBoard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DreamBoard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DreamBoard.  If not, see <https://www.gnu.org/licenses/>.

import logging

from PyQt6 import QtCore, QtGui

from dreamboard import commands
from dreamboard.fileio.errors import DreambFileIOError
from dreamboard.fileio.image import load_image
from dreamboard.fileio.sql import SQLiteIO, is_dreamb_file
from dreamboard.items import DreambPixmapItem
from dreamboard import firebase
from datetime import datetime
from firebase_admin import storage, firestore
from urllib.parse import quote
import uuid
import os
import dreamboard.user_instance as user_instance

__all__ = [
    'is_dreamb_file',
    'load_dreamb',
    'save_dreamb',
    'load_images',
    'ThreadedLoader',
    'DreambFileIOError',
]

logger = logging.getLogger(__name__)


def load_dreamb(filename, scene, worker=None):
    """Load DreamBoard native file."""
    logger.info(f'Loading from file {filename}...')
    io = SQLiteIO(filename, scene, readonly=True, worker=worker)
    return io.read()


def save_dreamb(filename, scene, create_new=False, worker=None):
    """Save DreamBoard native file."""
    logger.info(f'Saving to file {filename}...')
    logger.debug(f'Create new: {create_new}')
    io = SQLiteIO(filename, scene, create_new, worker=worker)
    io.write()
    logger.info('Saved!')


def fetch_boards():
    """Fetch all board documents from Firestore."""
    db = firebase.get_firestore()

    # Get reference to the users collection
    users_ref = db.collection("users")
    
    # Fetch the user document
    user_doc = users_ref.document(user_instance.user.id).get()
    if user_doc.exists:
        # Get the list of board ids associated with the user
        board_ids = user_doc.to_dict().get("boards", [])

        boards_ref = db.collection("boards")
        docs = boards_ref.stream()
        boards = []
        for board_id in board_ids:
            board_doc = boards_ref.document(board_id).get()
            if board_doc.exists:
                board = board_doc.to_dict()
                board["id"] = board_doc.id
                boards.append(board)
    else:
        boards = []

    return boards

def upload_to_firebase(file_data, file_name):
    bucket = storage.bucket()
    # Create a new blob and upload the file's content.
    blob = bucket.blob(file_name)

    blob.upload_from_string(
        file_data, content_type='image/png'
    )

def save_dreamb_cloud(scene, worker=None):
    logger.info('Saving...')
    # Get Firestore client and Cloud Storage bucket
    db = firebase.get_firestore()

    boards = fetch_boards()

    if (len(boards)):
        # Fetch the first board
        board_id = boards[0]["id"]
        doc_ref = db.collection("boards").document(board_id)
    else:
        # Create a new board document in Firestore
        board_data = {
            "created_at": datetime.now(),
            "name": "Board Name"  # use actual board name here
        }
        _, doc_ref = db.collection("boards").add(board_data)
    
    board_images_ref = db.collection("boards").document(doc_ref.id).collection("images")

    # Iterate over each item in the scene
    for i, item in enumerate(scene.items()):
        item_uuid = item.data(0).strip()
    
        
        if (item.isNew):
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
                "created_at": firestore.SERVER_TIMESTAMP
            }

            try:
                board_images_ref.document(image_uuid).set(image_data)
                logger.info('Saved new image to cloud.')
            except Exception as e:
                logger.error('Error saving new image to cloud with error: ' + str(e))
        else:
            updated_image_data = {
                "x": item.x(),
                "y": item.y(),
                "z": item.zValue(),
                "scale": item.scale(),
                "rotation": item.rotation(),
                "flip": item.flip(),
                "updated_at": firestore.SERVER_TIMESTAMP
            }

            try:
                board_images_ref.document(item_uuid).update(updated_image_data)
            except Exception as e:
                logger.error('Error updating image to cloud with error: ' + str(e))

        # Update the progress if a worker was provided
        if worker:
            worker.progress.emit(i)


def load_board(scene):
    # Get Firestore client and Cloud Storage bucket
    db = firebase.get_firestore()
    bucket = firebase.get_storage()

    # Fetch all boards
    boards = fetch_boards()
    
    # TODO: Add a way to select which board to load
    # For this example, let's just load the first board
    if len(boards) > 0:
        board_id = boards[0]["id"]
        board_ref = db.collection("boards").document(board_id)

        # Fetch all images for this board
        images_ref = board_ref.collection("images")
        images_docs = images_ref.stream()

        items = []
        # Iterate over each image
        for image_doc in images_docs:
            image_data = image_doc.to_dict()
            logger.info(f'Loading image from file {image_data["storage_url"]}')
            
            # Download the image from Cloud Storage
            blob = bucket.blob(image_data["storage_url"])
            image_data_bytes = blob.download_as_bytes()

            img = QtGui.QImage.fromData(image_data_bytes)
            
            item = DreambPixmapItem(img, image_data["filename"])
            item.set_pos_center(QtCore.QPointF(image_data["x"], image_data["y"]))
            item.setRotation(image_data["rotation"])
            item.setScale(image_data["scale"])
            
            item.setData(0, image_data["uuid"])
          
            scene.addItem(item)
            items.append(item)

def load_images(filenames, pos, scene, worker):
    """Add images to existing scene."""

    errors = []
    items = []
    worker.begin_processing.emit(len(filenames))
    for i, filename in enumerate(filenames):
        logger.info(f'Loading image from file {filename}')
        img, filename = load_image(filename)
        worker.progress.emit(i)
        if img.isNull():
            logger.info(f'Could not load file {filename}')
            errors.append(filename)
            continue

        item = DreambPixmapItem(img, filename)
        item.set_pos_center(pos)
        item.setHasChanged()
        item.setIsNew()
        scene.add_item_later({'item': item, 'type': 'pixmap'}, selected=True)
        items.append(item)
        if worker.canceled:
            break
        # Give main thread time to process items:
        worker.msleep(10)

    scene.undo_stack.push(
        commands.InsertItems(scene, items, ignore_first_redo=True))
    worker.finished.emit('', errors)


class ThreadedIO(QtCore.QThread):
    """Dedicated thread for loading and saving."""

    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(str, list)
    begin_processing = QtCore.pyqtSignal(int)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.kwargs['worker'] = self
        self.canceled = False

    def run(self):
        self.func(*self.args, **self.kwargs)

    def on_canceled(self):
        self.canceled = True
