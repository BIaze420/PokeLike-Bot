# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


block_cipher = None

datas = [
    ("assets/lunaticlabs_banner.png", "assets"),
    ("assets/lunaticlabs_logo_transp.png", "assets"),
    ("assets/favicon.ico", "assets"),
]
datas += collect_data_files("customtkinter")

hiddenimports = [
    "PIL._tkinter_finder",
]
hiddenimports += collect_submodules("selenium")
hiddenimports += collect_submodules("webdriver_manager")


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
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
    name="PokeLike Bot",
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
    icon="assets/favicon.ico",
    version="version_info.txt",
)
