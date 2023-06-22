import logging
from dreamboard import commands
from PyQt6 import QtWidgets, QtCore
from dreamboard.items import DreambTextItem, DreambPixmapItem


logger = logging.getLogger(__name__)


class EventHandlingEdit:
    def on_action_undo(self):
        logger.debug('Undo: %s' % self.undo_stack.undoText())
        self.scene.cancel_crop_mode()
        self.undo_stack.undo()

    def on_action_redo(self):
        logger.debug('Redo: %s' % self.undo_stack.redoText())
        self.scene.cancel_crop_mode()
        self.undo_stack.redo()

    def on_action_select_all(self):
        self.scene.set_selected_all_items(True)

    def on_action_deselect_all(self):
        self.scene.set_selected_all_items(False)

    def on_action_cut(self):
        logger.debug('Cutting items...')
        self.on_action_copy()
        self.undo_stack.push(
            commands.DeleteItems(
                self.scene, self.scene.selectedItems(user_only=True)))

    def on_action_paste(self):
        self.scene.cancel_crop_mode()
        logger.debug('Pasting from clipboard...')
        clipboard = QtWidgets.QApplication.clipboard()
        pos = self.mapToScene(self.mapFromGlobal(self.cursor().pos()))

        # See if we need to look up the internal clipboard:
        data = clipboard.mimeData().data('dreamboard/items')
        logger.debug(f'Custom data in clipboard: {data}')
        if data:
            self.scene.paste_from_internal_clipboard(pos)
            return

        img = clipboard.image()
        if not img.isNull():
            item = DreambPixmapItem(img)
            self.undo_stack.push(commands.InsertItems(self.scene, [item], pos))
            if len(self.scene.items()) == 1:
                # This is the first image in the scene
                self.on_action_fit_scene()
            return
        text = clipboard.text()
        if text:
            item = DreambTextItem(text)
            item.setScale(1 / self.get_scale())
            self.undo_stack.push(commands.InsertItems(self.scene, [item], pos))
            return
        logger.info('No image data or text in clipboard')

    def on_action_copy(self):
        logger.debug('Copying to clipboard...')
        self.scene.cancel_crop_mode()
        clipboard = QtWidgets.QApplication.clipboard()
        items = self.scene.selectedItems(user_only=True)

        # At the moment, we can only copy one image to the global
        # clipboard. (Later, we might create an image of the whole
        # selection for external copying.)
        items[0].copy_to_clipboard(clipboard)

        # However, we can copy all items to the internal clipboard:
        self.scene.copy_selection_to_internal_clipboard()

        # We set a marker for ourselves in the global clipboard so
        # that we know to look up the internal clipboard when pasting:
        clipboard.mimeData().setData(
            'dreamboard/items', QtCore.QByteArray.number(len(items)))

    def on_action_delete_items(self):
        logger.debug('Deleting items...')
        self.scene.cancel_crop_mode()
        self.undo_stack.push(
            commands.DeleteItems(
                self.scene, self.scene.selectedItems(user_only=True)))

    def on_action_raise_to_top(self):
        self.scene.raise_to_top()

    def on_action_lower_to_bottom(self):
        self.scene.lower_to_bottom()
