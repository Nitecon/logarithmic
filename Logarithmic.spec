# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

# Include font files - bundle entire fonts directory
font_dir = project_root / 'fonts'
font_datas = []
if font_dir.exists():
    # Add all font files with their subdirectory structure
    for font_file in font_dir.glob('**/*.ttf'):
        # Preserve directory structure: fonts/Michroma/file.ttf -> fonts/Michroma/
        relative_path = font_file.relative_to(project_root)
        dest_dir = str(relative_path.parent)
        font_datas.append((str(font_file), dest_dir))

a = Analysis(
    ['src/logarithmic/__main__.py'],
    pathex=[],
    binaries=[],
    datas=font_datas,
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'watchdog.observers', 'watchdog.events'],
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
    name='Logarithmic',
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
    icon='logo.ico',
)

# Create macOS app bundle
app = BUNDLE(
    exe,
    name='Logarithmic.app',
    icon='logo.icns',
    bundle_identifier='com.logarithmic.app',
    version='1.0.0',
    info_plist='Info.plist',
)
