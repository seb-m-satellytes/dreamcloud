from unittest.mock import patch

from PyQt6 import QtCore

from dreamboard.__main__ import DreamBoardMainWindow
from dreamboard.assets import DreambAssets
from dreamboard.views.board_view import DreambGraphicsView


@patch('PyQt6.QtWidgets.QWidget.show')
def test_dreamboard_mainwindow_init(show_mock, qapp):
    window = DreamBoardMainWindow(qapp)
    assert window.windowTitle() == 'DreamBoard'
    assert DreambAssets().logo == DreambAssets().logo
    assert window.windowIcon()
    assert window.contentsMargins() == QtCore.QMargins(0, 0, 0, 0)
    assert isinstance(window.view, DreambGraphicsView)
    show_mock.assert_called()


# @patch('dreamboard.views.DreambGraphicsView.open_from_file')
# def test_dreamboardapplication_fileopenevent(open_mock, qapp, main_window):
#    event = MagicMock()
#    event.type.return_value = QtCore.QEvent.Type.FileOpen
#    event.file.return_value = 'test.dreamb'
#    assert qapp.event(event) is True
#    open_mock.assert_called_once_with('test.dreamb')


# @patch('dreamboard.__main__.DreamBoardApplication')
# @patch('dreamboard.__main__.CommandlineArgs')
# def test_main(args_mock, app_mock, qapp):
#    app_mock.return_value = qapp
#    args_mock.return_value.filename = None
#    args_mock.return_value.loglevel = 'WARN'
#    with patch.object(qapp, 'exec') as exec_mock:
#        main()
#        args_mock.assert_called_once_with(with_check=True)
#        exec_mock.assert_called_once_with()
