from dreamboard.assets import DreambAssets
from dreamboard.views.board_view import DreambGraphicsView
from PyQt6 import QtCore, QtWidgets
from dreamboard import constants


class DreamBoardMainWindow(QtWidgets.QMainWindow):

    def __init__(self, app):
        super().__init__()
        app.setOrganizationName(constants.APPNAME)
        app.setApplicationName(constants.APPNAME)
        self.setWindowIcon(DreambAssets().logo)

        # save the presets
        self.presets = {}
        
        self.view = DreambGraphicsView(app, self)
        self.info_dock_widget = QtWidgets.QDockWidget('Info', self)

        # Create a widget for the dock widget to hold the layout and fields
        info_widget = QtWidgets.QWidget()
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

        # Set the layout on the widget and the widget on the dock widget
        info_widget.setLayout(layout)
        self.info_dock_widget.setWidget(info_widget)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.info_dock_widget)
        self.info_dock_widget.hide()

        default_window_size = QtCore.QSize(500, 300)
        geom = self.view.settings.value('MainWindow/geometry')
        if geom is None:
            self.resize(default_window_size)
        else:
            if not self.restoreGeometry(geom):
                self.resize(default_window_size)
        self.setCentralWidget(self.view)
        self.show()

    def closeEvent(self, event):
        geom = self.saveGeometry()
        self.view.settings.setValue('MainWindow/geometry', geom)
        event.accept()

    def toggleSidebar(self, item):
        metadata = item.data(1)['meta']
        uuid = item.data(0)
        current_item_uuid = self.current_item.data(0) if self.current_item is not None else None

        self.info_text.setText(metadata['info_text'])
        self.source_link.setText(metadata['source_link'])
        self.source_is_local.setChecked(metadata['source_is_local'])

        if (self.info_dock_widget.isVisible() and current_item_uuid == uuid):
            self.info_dock_widget.hide()
        else:
            self.info_dock_widget.show()
            self.current_item = item

    def mousePressEvent(self, event):
        self.info_dock_widget.hide()
        return super().mousePressEvent(event)

    def updateItemMetadata(self):
        if self.current_item is not None:
            metadata = self.current_item.data(1)["meta"]
            metadata["info_text"] = self.info_text.toPlainText()
            metadata["source_link"] = self.source_link.text()
            metadata["source_is_local"] = self.source_is_local.isChecked()
            self.current_item.setData(1, {"meta": metadata})

    def __del__(self):
        del self.view
