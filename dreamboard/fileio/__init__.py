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

from PyQt6 import QtCore

from dreamboard import commands
from dreamboard.fileio.errors import DreambFileIOError
from dreamboard.fileio.image import load_image
from dreamboard.fileio.sql import SQLiteIO, is_dreamb_file
from dreamboard.items import DreambPixmapItem

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


def load_images(filenames, pos, scene, mainWindow, worker):
    """Add images to existing scene."""
    print('load_images')

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

        item = DreambPixmapItem(img, filename, mainWindow.toggleSidebar)
        item.set_pos_center(pos)
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
