from PyQt6 import QtWidgets, QtGui, QtCore
import os
from dreamboard import constants
from dreamboard import widgets
from dreamboard.actions.event_handling_file import EventHandlingFile
from dreamboard.actions.event_handling_edit import EventHandlingEdit
from dreamboard.actions.event_handling_view import EventHandlingView
from dreamboard.actions.event_handling_insert import EventHandlingInsert
from dreamboard.actions.event_handling_transform import EventHandlingTransform
from dreamboard.actions.event_handling_normalize import EventHandlingNormalize
from dreamboard.actions.event_handling_arrange import EventHandlingArrange
from dreamboard.actions.event_handling_presets import EventHandlingPresets
import logging

logger = logging.getLogger(__name__)


class EventHandlingMixin(EventHandlingFile, EventHandlingEdit, EventHandlingView, EventHandlingInsert,
                         EventHandlingTransform, EventHandlingNormalize, EventHandlingArrange, EventHandlingPresets):
    """This mixin class contains all the event handling methods for the DreambGraphicsView class."""

    def on_action_help(self):
        widgets.HelpDialog(self)

    def on_action_about(self):
        QtWidgets.QMessageBox.about(
            self,
            f'About {constants.APPNAME}',
            (f'<h2>{constants.APPNAME} {constants.VERSION}</h2>'
             f'<p>{constants.APPNAME_FULL}</p>'
             f'<p>{constants.COPYRIGHT}</p>'
             f'<p><a href="{constants.WEBSITE}">'
             f'Visit the {constants.APPNAME} website</a></p>'))

    def on_action_debuglog(self):
        widgets.DebugLogDialog(self)

    def on_action_open_settings_dir(self):
        dirname = os.path.dirname(self.settings.fileName())
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(dirname))
