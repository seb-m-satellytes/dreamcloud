from PyQt6 import QtWidgets
from dreamboard import constants
import os
import logging

logger = logging.getLogger(__name__)


class EventHandlingFile:
    def on_action_open(self):
        self.scene.cancel_crop_mode()
        filename, f = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open file',
            filter=f'{constants.APPNAME} File (*.dreamb)')
        if filename:
            filename = os.path.normpath(filename)
            self.open_from_file(filename)
            self.filename = filename

    def on_action_save_as(self):
        self.scene.cancel_crop_mode()
        filename, f = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save file',
            filter=f'{constants.APPNAME} File (*.dreamb)')
        if filename:
            self.do_save(filename, create_new=True)

    def on_action_save(self):
        self.scene.cancel_crop_mode()
        if not self.filename:
            self.on_action_save_as()
        else:
            self.do_save(self.filename, create_new=False)

    def on_action_save_cloud(self):
        self.scene.cancel_crop_mode()
        self.do_save_cloud()

    def on_action_quit(self):
        self.timer.stop()
        logger.info('User quit. Exiting...')
        self.app.quit()
