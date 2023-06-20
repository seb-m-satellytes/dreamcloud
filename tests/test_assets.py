from PyQt6 import QtGui

from dreamboard.assets import DreambAssets


def test_singleton(view):
    assert DreambAssets() is DreambAssets()
    assert DreambAssets().logo is DreambAssets().logo


def test_has_logo(view):
    assert isinstance(DreambAssets().logo, QtGui.QIcon)
