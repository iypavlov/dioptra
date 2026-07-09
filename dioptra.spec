# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

datas = []
assets_src = Path("assets").resolve()
if assets_src.exists():
    for f in assets_src.rglob("*"):
        if f.is_file():
            rel = f.relative_to(assets_src.parent)
            datas.append((str(f), str(rel.parent)))

a = Analysis(
    ["src/dioptra/__main__.py"],
    pathex=[str(Path("src").resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtSvg",
        "paddleocr",
        "paddle",
        "mss",
        "keyboard",
        "mouse",
        "deep_translator",
        "PIL",
        "PIL.ImageEnhance",
        "PIL.ImageFilter",
        "numpy",
        "dioptra",
        "dioptra.cache",
        "dioptra.settings",
        "dioptra.ocr_service",
        "dioptra.app_paths",
        "dioptra.translation",
        "dioptra.translation.base",
        "dioptra.translation.google_translate",
        "dioptra.translation.ollama_translate",
        "dioptra.translation_worker",
        "dioptra.ui",
        "dioptra.ui.modal_window",
        "dioptra.ui.settings_window",
        "dioptra.ui.region_selector",
        "dioptra.log",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "Cython",
        "matplotlib",
        "tkinter",
        "test",
        "unittest",
        "pydoc",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Dioptra",
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
    icon="assets/icon.png" if Path("assets/icon.png").exists() else None,
)
