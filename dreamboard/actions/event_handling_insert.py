from PyQt6 import QtWidgets, QtGui
from dreamboard.items import DreambTextItem
import logging
from dreamboard import commands

logger = logging.getLogger(__name__)


class EventHandlingInsert:
    def on_action_insert_images(self):
        self.scene.cancel_crop_mode()
        formats = self.get_supported_image_formats(QtGui.QImageReader)
        logger.debug(f'Supported image types for reading: {formats}')
        filenames, f = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption='Select one or more images to open',
            filter=f'Images ({formats})')
        self.do_insert_images(filenames)

    def on_action_insert_text(self):
        self.scene.cancel_crop_mode()
        item = DreambTextItem()
        pos = self.mapToScene(self.mapFromGlobal(self.cursor().pos()))
        item.setScale(1 / self.get_scale())
        self.undo_stack.push(commands.InsertItems(self.scene, [item], pos))
