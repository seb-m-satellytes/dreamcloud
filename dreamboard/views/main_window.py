from dreamboard.assets import DreambAssets
from dreamboard.views.board_view import DreambGraphicsView
from PyQt6 import QtCore, QtWidgets
from dreamboard import constants
from dreamboard.views.sidebar_widget import SidebarWidget


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

        self.sidebar = SidebarWidget(self)
        self.info_dock_widget.setWidget(self.sidebar)

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
        current_item_uuid = self.sidebar.current_item.data(0) if self.sidebar.current_item is not None else None
        uuid = item.data(0)

        if (self.info_dock_widget.isVisible() and current_item_uuid == uuid):
            self.info_dock_widget.hide()
        else:
            self.info_dock_widget.show()
            self.sidebar.set_current_item(item)

    def mousePressEvent(self, event):
        self.info_dock_widget.hide()
        return super().mousePressEvent(event)

    def __del__(self):
        del self.view
