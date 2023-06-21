#!/usr/bin/env python3

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
import platform
import signal
import sys
import os
import json

from PyQt6 import QtCore, QtWidgets

from dreamboard import constants
from dreamboard.config import CommandlineArgs, DreambSettings, logfile_name
from dreamboard.utils import create_palette_from_dict
from dreamboard.user import LoginDialog
from dreamboard.views.main_window import DreamBoardMainWindow
import dreamboard.user_instance as user_instance
from dreamboard.user import User

logger = logging.getLogger(__name__)


class DreamBoardApplication(QtWidgets.QApplication):

    def event(self, event):
        if event.type() == QtCore.QEvent.Type.FileOpen:
            for widget in self.topLevelWidgets():
                if isinstance(widget, DreamBoardMainWindow):
                    widget.view.open_from_file(event.file())
                    return True
            return False
        else:
            return super().event(event)


def safe_timer(timeout, func, *args, **kwargs):
    """Create a timer that is safe against garbage collection and
    overlapping calls.
    See: http://ralsina.me/weblog/posts/BB974.html
    """
    def timer_event():
        try:
            func(*args, **kwargs)
        finally:
            QtCore.QTimer.singleShot(timeout, timer_event)
    QtCore.QTimer.singleShot(timeout, timer_event)


def handle_sigint(signum, frame):
    logger.info('Received interrupt. Exiting...')
    QtWidgets.QApplication.quit()


def handle_uncaught_exception(exc_type, exc, traceback):
    logger.critical('Unhandled exception',
                    exc_info=(exc_type, exc, traceback))
    QtWidgets.QApplication.quit()


sys.excepthook = handle_uncaught_exception


def main():
    logger.info(f'Starting {constants.APPNAME} version {constants.VERSION}')
    logger.debug('System: %s', ' '.join(platform.uname()))
    logger.debug('Python: %s', platform.python_version())
    settings = DreambSettings()
    logger.info(f'Using settings: {settings.fileName()}')
    logger.info(f'Logging to: {logfile_name()}')
    CommandlineArgs(with_check=True)  # Force checking
    palette = create_palette_from_dict(constants.COLORS)
    app = DreamBoardApplication(sys.argv)
    app.setPalette(palette)

    signal.signal(signal.SIGINT, handle_sigint)
    # Repeatedly run python-noop to give the interpreter time to
    # handle signals
    safe_timer(50, lambda: None)

    login_dialog = LoginDialog()

    if os.path.exists('user.json'):
        with open('user.json', 'r') as file:
            user_uid = json.load(file)
            user_instance.user = User(user_uid)

        dreamb = DreamBoardMainWindow(app)  # NOQA:F841
    elif login_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        dreamb = DreamBoardMainWindow(app)  # NOQA:F841
        print('Login accepted')
    else:
        sys.exit()

    app.exec()

    # app.exec()
    del dreamb
    del app
    logger.debug('DreamBoard closed')


if __name__ == '__main__':
    main()  # pragma: no cover
