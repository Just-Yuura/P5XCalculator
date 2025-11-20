# -*- mode: python ; coding: utf-8 -*-
import os
import sys

spec_root = os.path.abspath(SPECPATH)

if sys.platform == 'win32':
    app_icon = os.path.join(spec_root, 'src', 'assets', 'app_icon.ico')
else:
    app_icon = os.path.join(spec_root, 'src', 'assets', 'app_icon.png')

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('src/assets', 'assets')],
    hiddenimports=['src', 'src.gui', 'src.core', 'src.data', 'src.model'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='P5XCalculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon
)