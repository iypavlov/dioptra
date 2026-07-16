# -*- mode: python ; coding: utf-8 -*-

import os
import site

from PyInstaller.building.datastruct import Tree

block_cipher = None

a = Analysis(
    ["src/dioptra/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("assets", "assets"),
    ],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "keyboard",
        "mouse",
        "mss",
        "PIL",
        "PIL.Image",
        "PIL.ImageEnhance",
        "PIL.ImageFilter",
        "numpy",
        "rapidocr",
        "onnxruntime",
        "deep_translator",
        "deep_translator.google",
        "deep_translator.exceptions",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch",
        "stanza",
        "tkinter",
        "matplotlib",
        "scipy",
        "PyQt5",
        "PySide2",
        "PySide6",
        "IPython",
        "jupyter",
        "notebook",
        "pandas",
        "lxml",
        "pydantic",
        "rich",
        "test",
        "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Collect rapidocr data files (yaml configs, onnx models, etc.)
_rapidocr_dir = None
for _d in site.getsitepackages():
    _p = os.path.join(_d, "rapidocr")
    if os.path.isdir(_p):
        _rapidocr_dir = _p
        break

if _rapidocr_dir:
    a.datas += Tree(
        _rapidocr_dir,
        prefix="rapidocr",
        excludes=["*.py", "*.pyc"],
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
    icon="assets\\icon.ico" if os.path.exists("assets\\icon.ico") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Dioptra",
)
