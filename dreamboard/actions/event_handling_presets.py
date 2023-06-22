from PyQt6 import QtWidgets


class EventHandlingPresets:
    def on_action_save_preset(self):
        print('save preset')
        new_preset_images = {}  # This dictionary will store the images
        for item in self.scene.items():
            item_uuid = item.data(0).replace('-', '_')
            new_preset_images[item_uuid] = {
                'x': item.x(),
                'y': item.y(),
                'rotation': item.rotation(),
                'scale': item.scale(),
            }

        # show a dialog to enter a name for the preset
        preset_name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok:
            new_preset = {"name": preset_name, "images": new_preset_images}
            # add the preset to the presets dict
            self.parent.presets[preset_name] = new_preset
            QtWidgets.QMessageBox.information(
                self,
                'SUCCESS',
                ('<p>Saved preset with the name %s</p>' % preset_name))

        else:
            print('no preset name entered')

    def on_action_delete_preset(self):
        print('delete preset')
