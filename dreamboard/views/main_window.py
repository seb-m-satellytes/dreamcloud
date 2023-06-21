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
        self.view = DreambGraphicsView(app, self)
        self.info_dock_widget = QtWidgets.QDockWidget('Info', self)

        # Create a widget for the dock widget to hold the layout and fields
        info_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        # Create the fields for displaying item information
        self.info_text = QtWidgets.QTextEdit()
        self.source_link = QtWidgets.QLineEdit()
        self.source_is_local = QtWidgets.QCheckBox("Source is local")

        # Add the fields to the layout
        layout.addWidget(self.info_text)
        layout.addWidget(self.source_link)
        layout.addWidget(self.source_is_local)

        # Set the layout on the widget and the widget on the dock widget
        info_widget.setLayout(layout)
        self.info_dock_widget.setWidget(info_widget)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.info_dock_widget)

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

    def __del__(self):
        del self.view
