import os.path
import pytest
import uuid

from unittest.mock import MagicMock, patch

from PyQt6 import QtGui, QtWidgets


def pytest_configure(config):
    # Ignore logging configuration for DreamBoard during test runs. This
    # avoids logging to the regular log file and spamming test output
    # with debug messages.
    #
    # This needs to be done before the application code is even loaded since
    # logging configuration happens on module level
    import logging.config
    logging.config.dictConfig = MagicMock

    # Disable creation of KeyboardSettings.ini to speed tests up
    from dreamboard.config import KeyboardSettings
    KeyboardSettings.save_unknown_shortcuts = False


@pytest.fixture(autouse=True)
def commandline_args():
    config_patcher = patch('dreamboard.views.board_view.commandline_args')
    config_mock = config_patcher.start()
    config_mock.filename = None
    yield config_mock
    config_patcher.stop()


@pytest.fixture(autouse=True)
def settings(tmpdir):
    from dreamboard.config import DreambSettings
    dir_patcher = patch('dreamboard.config.DreambSettings.get_settings_dir',
                        return_value=tmpdir.dirname)
    dir_patcher.start()
    settings = DreambSettings()
    yield settings
    settings.clear()
    dir_patcher.stop()


@pytest.fixture(autouse=True)
def kbsettings(tmpdir):
    from dreamboard.config import KeyboardSettings
    dir_patcher = patch('dreamboard.config.DreambSettings.get_settings_dir',
                        return_value=tmpdir.dirname)
    dir_patcher.start()
    kbsettings = KeyboardSettings()
    yield kbsettings
    kbsettings.clear()
    dir_patcher.stop()


@pytest.fixture
def main_window(qtbot):
    from dreamboard.__main__ import DreamBoardMainWindow
    app = QtWidgets.QApplication.instance()
    main = DreamBoardMainWindow(app)
    qtbot.addWidget(main)
    yield main


@pytest.fixture
def view(main_window):
    yield main_window.view


@pytest.fixture
def imgfilename3x3():
    root = os.path.dirname(__file__)
    yield os.path.join(root, 'assets', 'test3x3.png')


@pytest.fixture
def imgdata3x3(imgfilename3x3):
    with open(imgfilename3x3, 'rb') as f:
        imgdata3x3 = f.read()
    yield imgdata3x3


@pytest.fixture
def tmpfile(tmpdir):
    yield os.path.join(tmpdir, str(uuid.uuid4()))


@pytest.fixture
def item():
    from dreamboard.items import DreambPixmapItem
    yield DreambPixmapItem(QtGui.QImage())


@pytest.fixture(scope="session")
def qapp():
    from dreamboard.__main__ import DreamBoardApplication
    yield DreamBoardApplication([])
