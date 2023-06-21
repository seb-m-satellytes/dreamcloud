import os.path
import shutil
import sqlite3
from unittest.mock import MagicMock, patch, mock_open

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from dreamboard.config import logfile_name
from dreamboard.items import DreambPixmapItem, DreambTextItem
from dreamboard.views.board_view import DreambGraphicsView


def test_inits_menu(view, qapp):
    parent = QtWidgets.QMainWindow()
    view = DreambGraphicsView(qapp, parent)
    assert isinstance(view.context_menu, QtWidgets.QMenu)
    assert len(view.actions()) > 0
    assert view.dreamb_actions
    assert view.dreamb_actiongroups


@patch('dreamboard.view.DreambGraphicsView.open_from_file')
def test_init_without_filename(open_file_mock, qapp, commandline_args):
    commandline_args.filename = None
    parent = QtWidgets.QMainWindow()
    view = DreambGraphicsView(qapp, parent)
    open_file_mock.assert_not_called()
    assert view.parent.windowTitle() == 'DreamBoard'
    del view


@patch('dreamboard.view.DreambGraphicsView.open_from_file')
def test_init_with_filename(open_file_mock, view, qapp, commandline_args):
    commandline_args.filename = 'test.dreamb'
    parent = QtWidgets.QMainWindow()
    view = DreambGraphicsView(qapp, parent)
    open_file_mock.assert_called_once_with('test.dreamb')
    del view


@patch('dreamboard.widgets.WelcomeOverlay.hide')
def test_on_scene_changed_when_items(hide_mock, view):
    item = DreambPixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    view.scale(2, 2)
    with patch('dreamboard.view.DreambGraphicsView.recalc_scene_rect') as r:
        view.on_scene_changed(None)
        r.assert_called_once_with()
        hide_mock.assert_called_once_with()
        assert view.get_scale() == 2


@patch('dreamboard.widgets.WelcomeOverlay.show')
def test_on_scene_changed_when_no_items(show_mock, view):
    view.scale(2, 2)
    with patch('dreamboard.view.DreambGraphicsView.recalc_scene_rect') as r:
        view.on_scene_changed(None)
        r.assert_called()
        show_mock.assert_called_once_with()
        assert view.get_scale() == 1


def test_get_supported_image_formats_for_reading(view):
    formats = view.get_supported_image_formats(QtGui.QImageReader)
    assert '*.png' in formats
    assert '*.jpg' in formats


def test_clear_scene(view, item):
    view.scene.addItem(item)
    view.scale(2, 2)
    view.translate(123, 456)
    view.filename = 'test.dreamb'
    view.undo_stack = MagicMock()

    view.clear_scene()
    assert not view.scene.items()
    assert view.transform().isIdentity()
    assert view.filename is None
    view.undo_stack.clear.assert_called_once_with()
    assert view.parent.windowTitle() == 'DreamBoard'


def test_reset_previous_transform_when_other_item(view):
    item1 = MagicMock()
    item2 = MagicMock()
    view.previous_transform = {
        'transform': 'foo',
        'toggle_item': item1,
    }
    view.reset_previous_transform(toggle_item=item2)
    assert view.previous_transform is None


def test_reset_previous_transform_when_same_item(view):
    item = MagicMock()
    view.previous_transform = {
        'transform': 'foo',
        'toggle_item': item,
    }
    view.reset_previous_transform(toggle_item=item)
    assert view.previous_transform == {
        'transform': 'foo',
        'toggle_item': item,
    }


@patch('dreamboard.view.DreambGraphicsView.fitInView')
def test_fit_rect_no_toggle(fit_mock, view):
    rect = QtCore.QRectF(30, 40, 100, 80)
    view.previous_transform = {'toggle_item': MagicMock()}
    view.fit_rect(rect)
    fit_mock.assert_called_with(rect, Qt.AspectRatioMode.KeepAspectRatio)
    assert view.previous_transform is None


@patch('dreamboard.view.DreambGraphicsView.fitInView')
def test_fit_rect_toggle_when_no_previous(fit_mock, view):
    item = MagicMock()
    view.previous_transform = None
    view.setSceneRect(QtCore.QRectF(-2000, -2000, 4000, 4000))
    rect = QtCore.QRectF(30, 40, 100, 80)
    view.scale(2, 2)
    view.horizontalScrollBar().setValue(-40)
    view.verticalScrollBar().setValue(-50)
    view.fit_rect(rect, toggle_item=item)
    fit_mock.assert_called_with(rect, Qt.AspectRatioMode.KeepAspectRatio)
    assert view.previous_transform['toggle_item'] == item
    assert view.previous_transform['transform'].m11() == 2
    assert isinstance(view.previous_transform['center'], QtCore.QPointF)


@patch('dreamboard.view.DreambGraphicsView.fitInView')
@patch('dreamboard.view.DreambGraphicsView.centerOn')
def test_fit_rect_toggle_when_previous(center_mock, fit_mock, view):
    item = MagicMock()
    view.previous_transform = {
        'toggle_item': item,
        'transform': QtGui.QTransform.fromScale(2, 2),
        'center': QtCore.QPointF(30, 40)
    }
    view.setSceneRect(QtCore.QRectF(-2000, -2000, 4000, 4000))
    rect = QtCore.QRectF(30, 40, 100, 80)
    view.fit_rect(rect, toggle_item=item)
    fit_mock.assert_not_called()
    center_mock.assert_called_once_with(QtCore.QPointF(30, 40))
    assert view.get_scale() == 2


@patch('dreamboard.view.DreambGraphicsView.clear_scene')
def test_open_from_file(clear_mock, view, qtbot):
    root = os.path.dirname(__file__)
    filename = os.path.join(root, 'assets', 'test1item.dreamb')
    view.on_loading_finished = MagicMock()
    view.open_from_file(filename)
    view.worker.wait()
    qtbot.waitUntil(lambda: view.on_loading_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is False
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_loading_finished.assert_called_once_with(filename, [])


def test_open_from_file_when_error(view, qtbot):
    view.on_loading_finished = MagicMock()
    view.open_from_file('uieauiae')
    view.worker.wait()
    qtbot.waitUntil(lambda: view.on_loading_finished.called is True)
    assert list(view.scene.items()) == []
    view.on_loading_finished.assert_called_once_with(
        'uieauiae', ['unable to open database file'])


@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
def test_on_action_open(dialog_mock, view, qtbot):
    # FIXME: #1
    # Can't check signal handling currently
    root = os.path.dirname(__file__)
    filename = os.path.join(root, 'assets', 'test1item.dreamb')
    dialog_mock.return_value = (filename, None)
    view.on_loading_finished = MagicMock()
    view.scene.cancel_crop_mode = MagicMock()

    view.on_action_open()
    qtbot.waitUntil(lambda: view.on_loading_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is False
    assert item.pixmap()
    view.on_loading_finished.assert_called_once_with(filename, [])
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
@patch('dreamboard.view.DreambGraphicsView.open_from_file')
def test_on_action_open_when_no_filename(open_mock, dialog_mock, view):
    dialog_mock.return_value = (None, None)
    view.scene.cancel_crop_mode = MagicMock()
    view.on_action_open()
    open_mock.assert_not_called()
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_save_as(dialog_mock, view, imgfilename3x3, tmpdir):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    filename = os.path.join(tmpdir, 'test.dreamb')
    assert os.path.exists(filename) is False
    dialog_mock.return_value = (filename, None)
    view.on_action_save_as()
    view.worker.wait()
    assert os.path.exists(filename) is True
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
@patch('dreamboard.view.DreambGraphicsView.do_save')
def test_on_action_save_as_when_no_filename(
        save_mock, dialog_mock, view, imgfilename3x3):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    dialog_mock.return_value = (None, None)
    view.on_action_save_as()
    save_mock.assert_not_called()
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_save_as_filename_doesnt_end_with_dreamb(
        dialog_mock, view, qtbot, imgfilename3x3, tmpdir):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    view.on_saving_finished = MagicMock()
    filename = os.path.join(tmpdir, 'test')
    assert os.path.exists(filename) is False
    dialog_mock.return_value = (filename, None)
    view.on_action_save_as()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    assert os.path.exists(f'{filename}.dreamb') is True
    view.on_saving_finished.assert_called_once_with(f'{filename}.dreamb', [])
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
@patch('dreamboard.fileio.sql.SQLiteIO.write_data')
def test_on_action_save_as_when_error(
        save_mock, dialog_mock, view, qtbot, imgfilename3x3, tmpdir):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.on_saving_finished = MagicMock()
    view.scene.cancel_crop_mode = MagicMock()
    filename = os.path.join(tmpdir, 'test.dreamb')
    dialog_mock.return_value = (filename, None)
    save_mock.side_effect = sqlite3.Error('foo')
    view.on_action_save_as()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    view.on_saving_finished.assert_called_once_with(filename, ['foo'])
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_on_action_save(view, qtbot, imgfilename3x3, tmpdir):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    view.filename = os.path.join(tmpdir, 'test.dreamb')
    root = os.path.dirname(__file__)
    shutil.copyfile(os.path.join(root, 'assets', 'test1item.dreamb'),
                    view.filename)
    view.on_saving_finished = MagicMock()
    view.on_action_save()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    assert os.path.exists(view.filename) is True
    view.on_saving_finished.assert_called_once_with(view.filename, [])
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.view.DreambGraphicsView.on_action_save_as')
def test_on_action_save_when_no_filename(save_as_mock, view, imgfilename3x3):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    view.filename = None
    view.on_action_save()
    save_as_mock.assert_called_once_with()
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.widgets.HelpDialog.show')
def test_on_action_help(show_mock, view):
    view.on_action_help()
    show_mock.assert_called_once()


@patch('dreamboard.widgets.DebugLogDialog.show')
def test_on_action_debuglog(show_mock, view):
    with patch('builtins.open', mock_open(read_data='log')) as open_mock:
        view.on_action_debuglog()
        show_mock.assert_called_once()
        open_mock.assert_called_once_with(logfile_name())


@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
def test_on_action_insert_images_new_scene(
        dialog_mock, clear_mock, view, imgfilename3x3, qtbot):
    dialog_mock.return_value = ([imgfilename3x3], None)
    view.on_insert_images_finished = MagicMock()
    view.scene.cancel_crop_mode = MagicMock()
    view.on_action_insert_images()
    qtbot.waitUntil(lambda: view.on_insert_images_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_insert_images_finished.assert_called_once_with(True, '', [])
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
def test_on_action_insert_images_existing_scene(
        dialog_mock, clear_mock, view, imgfilename3x3, qtbot, item):
    view.scene.addItem(item)
    dialog_mock.return_value = ([imgfilename3x3], None)
    view.on_insert_images_finished = MagicMock()
    view.scene.cancel_crop_mode = MagicMock()
    view.on_action_insert_images()
    qtbot.waitUntil(lambda: view.on_insert_images_finished.called is True)
    assert len(view.scene.items()) == 2
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_insert_images_finished.assert_called_once_with(False, '', [])
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
def test_on_action_insert_images_when_error(
        dialog_mock, clear_mock, view, imgfilename3x3, qtbot):
    dialog_mock.return_value = ([imgfilename3x3, 'iaeiae', 'trntrn'], None)
    view.on_insert_images_finished = MagicMock()
    view.scene.cancel_crop_mode = MagicMock()
    view.on_action_insert_images()
    qtbot.waitUntil(lambda: view.on_insert_images_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_insert_images_finished.assert_called_once_with(
        True, '', ['iaeiae', 'trntrn'])
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
def test_on_action_insert_text(clear_mock, view):
    view.scene.cancel_crop_mode = MagicMock()
    view.on_action_insert_text()
    clear_mock.assert_called_once_with()
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.toPlainText() == 'Text'
    assert item.isSelected() is True
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('PyQt6.QtWidgets.QApplication.clipboard')
def test_on_action_copy_image(clipboard_mock, view, imgfilename3x3):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    item.setSelected(True)
    mimedata = QtCore.QMimeData()
    clipboard_mock.return_value.mimeData.return_value = mimedata
    view.on_action_copy()

    clipboard_mock.return_value.setPixmap.assert_called_once()
    view.scene.internal_clipboard == [item]
    assert mimedata.data('dreamboard/items') == b'1'
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('PyQt6.QtWidgets.QApplication.clipboard')
def test_on_action_copy_text(clipboard_mock, view, imgfilename3x3):
    item = DreambTextItem('foo bar')
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    item.setSelected(True)
    mimedata = QtCore.QMimeData()
    clipboard_mock.return_value.mimeData.return_value = mimedata
    view.on_action_copy()

    clipboard_mock.return_value.setText.assert_called_once_with('foo bar')
    view.scene.internal_clipboard == [item]
    assert mimedata.data('dreamboard/items') == b'1'
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.view.DreambGraphicsView.on_action_fit_scene')
@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_external_new_scene(
        clipboard_mock, clear_mock, fit_mock, view, imgfilename3x3):
    clipboard_mock.return_value = QtGui.QImage(imgfilename3x3)
    view.scene.cancel_crop_mode = MagicMock()
    view.on_action_paste()
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
    fit_mock.assert_called_once_with()
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.view.DreambGraphicsView.on_action_fit_scene')
@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_external_existing_scene(
        clipboard_mock, clear_mock, fit_mock, view, item, imgfilename3x3):
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    clipboard_mock.return_value = QtGui.QImage(imgfilename3x3)
    view.on_action_paste()
    assert len(view.scene.items()) == 2
    assert view.scene.items()[0].isSelected() is True
    assert view.scene.items()[1].isSelected() is False
    fit_mock.assert_not_called()
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.mimeData')
def test_on_action_paste_internal(mimedata_mock, clear_mock, view):
    mimedata = QtCore.QMimeData()
    mimedata.setData('dreamboard/items', QtCore.QByteArray.number(1))
    mimedata_mock.return_value = mimedata
    item = DreambPixmapItem(QtGui.QImage())
    view.scene.internal_clipboard = [item]
    view.scene.cancel_crop_mode = MagicMock()
    view.on_action_paste()
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
    clear_mock.assert_called_once_with()
    view.scene.cancel_crop_mode.assert_called()


@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.text')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_when_text(img_mock, text_mock, clear_mock, view):
    img_mock.return_value = QtGui.QImage()
    text_mock.return_value = 'foo bar'
    view.scene.cancel_crop_mode = MagicMock()
    view.on_action_paste()
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
    assert view.scene.items()[0].toPlainText() == 'foo bar'
    clear_mock.assert_called_once_with()
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.scene.DreambGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.text')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_when_empty(img_mock, text_mock, clear_mock, view):
    view.scene.cancel_crop_mode = MagicMock()
    img_mock.return_value = QtGui.QImage()
    text_mock.return_value = ''
    view.on_action_paste()
    assert len(view.scene.items()) == 0
    clear_mock.assert_not_called()
    view.scene.cancel_crop_mode.assert_called_once_with()


@patch('dreamboard.view.DreambGraphicsView.on_action_copy')
def test_on_action_cut(copy_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    view.on_action_cut()
    copy_mock.assert_called_once_with()
    assert view.scene.items() == []
    assert view.undo_stack.isClean() is False


@patch('PyQt6.QtWidgets.QWidget.create')
@patch('PyQt6.QtWidgets.QWidget.destroy')
@patch('PyQt6.QtWidgets.QWidget.show')
def test_on_action_always_on_top_checked(
        show_mock, destroy_mock, create_mock, view):
    view.on_action_always_on_top(True)
    assert view.parent.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    show_mock.assert_called_once()
    destroy_mock.assert_called_once()
    create_mock.assert_called_once()


@patch('PyQt6.QtWidgets.QWidget.create')
@patch('PyQt6.QtWidgets.QWidget.destroy')
@patch('PyQt6.QtWidgets.QWidget.show')
def test_on_action_always_on_top_unchecked(
        show_mock, destroy_mock, create_mock, view):
    view.on_action_always_on_top(False)
    assert not (view.parent.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
    show_mock.assert_called_once()
    destroy_mock.assert_called_once()
    create_mock.assert_called_once()


def test_on_action_show_menubar(view):
    view.toplevel_menus = [QtWidgets.QMenu('Foo')]
    view.on_action_show_menubar(True)
    assert len(view.parent.menuBar().actions()) == 1
    view.on_action_show_menubar(False)
    assert view.parent.menuBar().actions() == []


@patch('PyQt6.QtWidgets.QWidget.create')
@patch('PyQt6.QtWidgets.QWidget.destroy')
@patch('PyQt6.QtWidgets.QWidget.show')
def test_on_action_show_titlebar_checked(
        show_mock, destroy_mock, create_mock, view):
    view.on_action_show_titlebar(True)
    assert not (view.parent.windowFlags() & Qt.WindowType.FramelessWindowHint)
    show_mock.assert_called_once()
    destroy_mock.assert_called_once()
    create_mock.assert_called_once()


@patch('PyQt6.QtWidgets.QWidget.create')
@patch('PyQt6.QtWidgets.QWidget.destroy')
@patch('PyQt6.QtWidgets.QWidget.show')
def test_on_action_show_titlebar_unchecked(
        show_mock, destroy_mock, create_mock, view):
    view.on_action_show_titlebar(False)
    assert view.parent.windowFlags() & Qt.WindowType.FramelessWindowHint
    show_mock.assert_called_once()
    destroy_mock.assert_called_once()
    create_mock.assert_called_once()


def test_on_action_delete_items(view, item):
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.addItem(item)
    item.setSelected(True)
    view.on_action_delete_items()
    assert view.scene.items() == []
    assert view.undo_stack.isClean() is False
    view.scene.cancel_crop_mode.assert_called_once()


@patch('PyQt6.QtGui.QUndoStack.isClean', return_value=True)
def test_update_window_title_no_changes_no_filename(clear_mock, view):
    view.filename = None
    view.update_window_title()
    assert view.parent.windowTitle() == 'DreamBoard'


@patch('PyQt6.QtGui.QUndoStack.isClean', return_value=False)
def test_update_window_title_changes_no_filename(clear_mock, view):
    view.filename = None
    view.update_window_title()
    assert view.parent.windowTitle() == '[Untitled]* - DreamBoard'


@patch('PyQt6.QtGui.QUndoStack.isClean', return_value=True)
def test_update_window_title_no_changes_filename(clear_mock, view):
    view.filename = 'test.dreamb'
    view.update_window_title()
    assert view.parent.windowTitle() == 'test.dreamb - DreamBoard'


@patch('PyQt6.QtGui.QUndoStack.isClean', return_value=False)
def test_update_window_title_changes_filename(clear_mock, view):
    view.filename = 'test.dreamb'
    view.update_window_title()
    assert view.parent.windowTitle() == 'test.dreamb* - DreamBoard'


@patch('dreamboard.view.DreambGraphicsView.recalc_scene_rect')
@patch('dreamboard.scene.DreambGraphicsScene.on_view_scale_change')
def test_scale(view_scale_mock, recalc_mock, view):
    view.scale(3.3, 3.3)
    view_scale_mock.assert_called_once_with()
    recalc_mock.assert_called_once_with()
    assert view.get_scale() == 3.3


@patch('PyQt6.QtWidgets.QScrollBar.setValue')
def test_pan(scroll_value_mock, view, item):
    view.scene.addItem(item)
    view.pan(QtCore.QPointF(5, 10))
    assert scroll_value_mock.call_count == 2


@patch('PyQt6.QtWidgets.QScrollBar.setValue')
def test_pan_when_no_items(scroll_value_mock, view):
    view.pan(QtCore.QPointF(5, 10))
    scroll_value_mock.assert_not_called()


@patch('dreamboard.view.DreambGraphicsView.reset_previous_transform')
@patch('dreamboard.view.DreambGraphicsView.pan')
def test_zoom_in(pan_mock, reset_mock, view, imgfilename3x3):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.zoom(40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 1.04
    reset_mock.assert_called_once_with()
    pan_mock.assert_called_once()


@patch('dreamboard.view.DreambGraphicsView.reset_previous_transform')
@patch('dreamboard.view.DreambGraphicsView.pan')
def test_zoom_in_max_zoom_size(pan_mock, reset_mock, view, imgfilename3x3):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scale(10000000, 10000000)
    view.scene.addItem(item)
    view.zoom(40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 10000000
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('dreamboard.view.DreambGraphicsView.reset_previous_transform')
@patch('dreamboard.view.DreambGraphicsView.pan')
def test_zoom_out(pan_mock, reset_mock, view, imgfilename3x3):
    item = DreambPixmapItem(QtGui.QImage(imgfilename3x3))
    view.scale(100, 100)
    view.scene.addItem(item)
    view.zoom(-40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 100 / 1.04
    reset_mock.assert_called_once_with()
    pan_mock.assert_called_once()


@patch('dreamboard.view.DreambGraphicsView.reset_previous_transform')
@patch('dreamboard.view.DreambGraphicsView.pan')
def test_zoom_out_min_zoom_size(pan_mock, reset_mock, view, item):
    view.scene.addItem(item)
    view.zoom(-40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('dreamboard.view.DreambGraphicsView.reset_previous_transform')
@patch('dreamboard.view.DreambGraphicsView.pan')
def test_no_items(pan_mock, reset_mock, view, item):
    view.zoom(40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('dreamboard.view.DreambGraphicsView.reset_previous_transform')
@patch('dreamboard.view.DreambGraphicsView.pan')
def test_delta_zero(pan_mock, reset_mock, view, item):
    view.scene.addItem(item)
    view.zoom(0, QtCore.QPointF(10, 10))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('dreamboard.view.DreambGraphicsView.zoom')
def test_wheel_event(zoom_mock, view):
    event = MagicMock()
    event.angleDelta.return_value = QtCore.QPointF(0, 40)
    event.position.return_value = QtCore.QPointF(10, 20)
    view.wheelEvent(event)
    zoom_mock.assert_called_once_with(40, QtCore.QPointF(10, 20))
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_zoom(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    event.button.return_value = Qt.MouseButton.MiddleButton
    event.modifiers.return_value = Qt.KeyboardModifier.ControlModifier
    view.mousePressEvent(event)
    assert view.zoom_active is True
    assert view.pan_active is False
    assert view.movewin_active is False
    assert view.event_start == QtCore.QPointF(10, 20)
    assert view.event_anchor == QtCore.QPointF(10, 20)
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_pan_middle_drag(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    event.button.return_value = Qt.MouseButton.MiddleButton
    event.modifiers.return_value = None
    view.mousePressEvent(event)
    assert view.pan_active is True
    assert view.zoom_active is False
    assert view.movewin_active is False
    assert view.event_start == QtCore.QPointF(10, 20)
    mouse_event_mock.assert_not_called()
    view.cursor() == Qt.CursorShape.ClosedHandCursor
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_pan_alt_left_drag(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = Qt.KeyboardModifier.AltModifier
    view.mousePressEvent(event)
    assert view.pan_active is True
    assert view.zoom_active is False
    assert view.movewin_active is False
    assert view.event_start == QtCore.QPointF(10, 20)
    mouse_event_mock.assert_not_called()
    view.cursor() == Qt.CursorShape.ClosedHandCursor
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_move_window(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = (
        Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ControlModifier)
    view.mousePressEvent(event)
    assert view.pan_active is False
    assert view.zoom_active is False
    assert view.movewin_active is True
    assert view.event_start == view.mapToGlobal(QtCore.QPointF(10, 20))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_unhandled(mouse_event_mock, view):
    event = MagicMock()
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = None
    view.mousePressEvent(event)
    assert view.pan_active is False
    assert view.zoom_active is False
    assert view.movewin_active is False
    mouse_event_mock.assert_called_once_with(event)
    event.accept.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('dreamboard.view.DreambGraphicsView.pan')
def test_mouse_move_pan(pan_mock, mouse_event_mock, view):
    view.pan_active = True
    view.event_start = QtCore.QPointF(55, 66)
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    view.mouseMoveEvent(event)
    pan_mock.assert_called_once_with(QtCore.QPointF(45, 46))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('dreamboard.view.DreambGraphicsView.zoom')
def test_mouse_move_zoom(zoom_mock, mouse_event_mock, view):
    view.zoom_active = True
    view.event_anchor = QtCore.QPointF(55, 66)
    view.event_start = QtCore.QPointF(10, 20)
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 18)
    view.mouseMoveEvent(event)
    zoom_mock.assert_called_once_with(40, QtCore.QPointF(55, 66))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('PyQt6.QtWidgets.QWidget.move')
def test_mouse_move_movewin(move_mock, mouse_event_mock, view):
    view.movewin_active = True
    view.event_start = QtCore.QPointF(10, 20)
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(15, 18)
    view.mouseMoveEvent(event)
    move_mock.assert_called_once_with(5, -2)
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
def test_mouse_move_unhandled(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    view.mouseMoveEvent(event)
    mouse_event_mock.assert_called_once_with(event)
    event.accept.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_pan(mouse_event_mock, view):
    event = MagicMock()
    view.pan_active = True
    view.setCursor(Qt.CursorShape.ClosedHandCursor)
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_not_called()
    assert view.pan_active is False
    event.accept.assert_called_once_with()
    view.cursor() == Qt.CursorShape.ArrowCursor


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_zoom(mouse_event_mock, view):
    event = MagicMock()
    view.zoom_active = True
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_not_called()
    assert view.zoom_active is False
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_movewin(mouse_event_mock, view):
    event = MagicMock()
    view.movewin_active = True
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_not_called()
    assert view.movewin_active is False
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_unhandled(mouse_event_mock, view):
    event = MagicMock()
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_called_once_with(event)
    event.accept.assert_not_called()


def test_drag_enter_when_url(view, imgfilename3x3):
    url = QtCore.QUrl()
    url.fromLocalFile(imgfilename3x3)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata

    view.dragEnterEvent(event)
    event.acceptProposedAction.assert_called_once()


def test_drag_enter_when_img(view, imgfilename3x3):
    mimedata = QtCore.QMimeData()
    mimedata.setImageData(QtGui.QImage(imgfilename3x3))
    event = MagicMock()
    event.mimeData.return_value = mimedata

    view.dragEnterEvent(event)
    event.acceptProposedAction.assert_called_once()


def test_drag_enter_when_unsupported(view):
    mimedata = QtCore.QMimeData()
    event = MagicMock()
    event.mimeData.return_value = mimedata

    view.dragEnterEvent(event)
    event.acceptProposedAction.assert_not_called()


def test_drag_move(view):
    event = MagicMock()
    view.dragMoveEvent(event)
    event.acceptProposedAction.assert_called_once()


@patch('dreamboard.view.DreambGraphicsView.do_insert_images')
def test_drop_when_url(insert_mock, view, imgfilename3x3):
    url = QtCore.QUrl.fromLocalFile(imgfilename3x3)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10, 20)

    view.dropEvent(event)
    insert_mock.assert_called_once_with([url], QtCore.QPoint(10, 20))


@patch('dreamboard.view.DreambGraphicsView.open_from_file')
def test_drop_when_url_dreambfile_and_scene_empty(open_mock, view):
    root = os.path.dirname(__file__)
    filename = os.path.join(root, 'assets', 'test1item.dreamb')
    url = QtCore.QUrl.fromLocalFile(filename)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10, 20)

    view.dropEvent(event)
    open_mock.assert_called_once_with(filename)


@patch('dreamboard.view.DreambGraphicsView.do_insert_images')
@patch('dreamboard.view.DreambGraphicsView.open_from_file')
def test_drop_when_url_dreambfile_and_scene_not_empty(
        open_mock, insert_mock, view, item):
    view.scene.addItem(item)
    root = os.path.dirname(__file__)
    filename = os.path.join(root, 'assets', 'test1item.dreamb')
    url = QtCore.QUrl.fromLocalFile(filename)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10, 20)

    view.dropEvent(event)
    open_mock.assert_not_called()


def test_drop_when_img(view, imgfilename3x3):
    mimedata = QtCore.QMimeData()
    mimedata.setImageData(QtGui.QImage(imgfilename3x3))
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10, 20)

    view.dropEvent(event)
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
