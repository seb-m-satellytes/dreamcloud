# -*- mode: python ; coding: utf-8 -*-

import os
from os.path import join
import platform

block_cipher = None

a = Analysis(
    [join('dreamboard', '__main__.py')],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        (join('dreamboard', 'documentation'), join('dreamboard', 'documentation')),
        (join('dreamboard', 'assets', '*.png'), join('dreamboard', 'assets'))],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

from dreamboard import constants

operating_system = platform.system()
architecture = platform.processor()

if operating_system.startswith('Win'):
    icon = 'logo.ico'
else:
    icon = 'logo.icns'  # For OSX; param gets ignored on Linux

executable_name = f'{constants.APPNAME}'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=executable_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None ,
    icon=join('dreamboard', 'assets', icon))

if operating_system == 'Darwin':
    app = BUNDLE(
        exe,
        name=f'{executable_name}.app',
        icon=join('dreamboard', 'assets', icon),
        bundle_identifier='org.dreamboard.app',
        version=f'{constants.VERSION}',
        info_plist={
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeExtensions': [ 'dreamb' ],
                    'CFBundleTypeRole': 'Viewer'
                }
            ]
        })
    