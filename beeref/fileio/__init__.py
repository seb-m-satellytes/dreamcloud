# This file is part of BeeRef.
#
# BeeRef is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BeeRef is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BeeRef.  If not, see <https://www.gnu.org/licenses/>.

import logging

from PyQt6 import QtCore, QtGui

from beeref import commands
from beeref.fileio.errors import BeeFileIOError
from beeref.fileio.image import load_image
from beeref.fileio.sql import SQLiteIO, is_bee_file
from beeref.items import BeePixmapItem
from beeref import firebase
from datetime import datetime
from firebase_admin import storage
from urllib.parse import quote
import uuid
import os

__all__ = [
    'is_bee_file',
    'load_bee',
    'save_bee',
    'load_images',
    'ThreadedLoader',
    'BeeFileIOError',
]

logger = logging.getLogger(__name__)


def load_bee(filename, scene, worker=None):
    """Load BeeRef native file."""
    logger.info(f'Loading from file {filename}...')
    io = SQLiteIO(filename, scene, readonly=True, worker=worker)
    return io.read()


def save_bee(filename, scene, create_new=False, worker=None):
    """Save BeeRef native file."""
    logger.info(f'Saving to file {filename}...')
    logger.debug(f'Create new: {create_new}')
    io = SQLiteIO(filename, scene, create_new, worker=worker)
    io.write()
    logger.info('Saved!')


def fetch_boards():
    """Fetch all board documents from Firestore."""
    db = firebase.get_firestore()
    boards_ref = db.collection("boards")
    docs = boards_ref.stream()
    boards = []
    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')
        board = doc.to_dict()
        board["id"] = doc.id
        boards.append(board)
    return boards

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

def save_bee_cloud(scene, worker=None):
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
    
    board_ref = db.collection("boards").document(doc_ref.id).collection("images")

    # Iterate over each item in the scene
    for i, item in enumerate(scene.items()):
        # Get image data and upload to Cloud Storage
        data = item.pixmap_to_bytes()
        print(item)
        filepath = os.path.basename(item.filename)
        filename = filepath.replace(" ", "-").lower()

        image_url = upload_to_firebase(data, filename)
        image_uuid = str(uuid.uuid4())
        
        # Create a new image document in Firestore under the board document
        image_data = {
            "filename": filename,
            "storage_url": image_url,
            "uuid": image_uuid,
            "x": item.x(),
            "y": item.y(),
            "z": item.zValue(),
            "scale": item.scale(),
            "rotation": item.rotation(),
            "flip": item.flip(),
        }

        board_ref.document(image_uuid).set(image_data)

        # Update the progress if a worker was provided
        if worker:
            worker.progress.emit(i)

    logger.info('Saved!')

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
            # TODO: Adjust the following code to match your actual image data
            blob = bucket.blob(image_data["storage_url"])
            image_data_bytes = blob.download_as_bytes()

            img = QtGui.QImage.fromData(image_data_bytes)
            
            item = BeePixmapItem(img, image_data["filename"])
            item.set_pos_center(QtCore.QPointF(image_data["x"], image_data["y"]))
            print('==>', item)
        
            scene.addItem(item)
            items.append(item)
            # scene.addItem(pixmap)


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

        item = BeePixmapItem(img, filename)
        item.set_pos_center(pos)
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
