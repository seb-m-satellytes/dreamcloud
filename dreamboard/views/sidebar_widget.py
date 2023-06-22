from PyQt6 import QtWidgets


class SidebarWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        # Create the fields for displaying item information
        self.current_item = None
        self.info_text = QtWidgets.QTextEdit()
        self.source_link = QtWidgets.QLineEdit()
        self.source_is_local = QtWidgets.QCheckBox("Source is local")

        self.info_text.textChanged.connect(self.updateItemMetadata)
        self.source_link.textChanged.connect(self.updateItemMetadata)
        self.source_is_local.stateChanged.connect(self.updateItemMetadata)
        # Add the fields to the layout
        layout.addWidget(self.info_text)
        layout.addWidget(self.source_link)
        layout.addWidget(self.source_is_local)

        self.setLayout(layout)

    def updateItemMetadata(self):
        if self.current_item is not None:
            metadata = self.current_item.data(1)["meta"]
            metadata["info_text"] = self.info_text.toPlainText()
            metadata["source_link"] = self.source_link.text()
            metadata["source_is_local"] = self.source_is_local.isChecked()
            self.current_item.setData(1, {"meta": metadata})

    def set_current_item(self, item):
        self.current_item = item
        metadata = item.data(1)['meta']
        self.info_text.setText(metadata['info_text'])
        self.source_link.setText(metadata['source_link'])
        self.source_is_local.setChecked(metadata['source_is_local'])
