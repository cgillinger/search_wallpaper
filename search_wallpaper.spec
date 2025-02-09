# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['.', 'src'],
    binaries=[],
    datas=[
        ('src/api/*', 'api'),
        ('src/config/*', 'config'),
        ('src/utils/*', 'utils'),
        ('resources/icon.ico', 'resources')
    ],
    hiddenimports=[
        'requests',
        'requests.adapters',
        'PIL',
        'PIL.Image',
        'selenium',
        'selenium.webdriver',
        'webdriver_manager',
        'configparser',
        'logging',
        'ctypes',
        'tkinter',
        'tkinter.ttk'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SearchWallpaper',
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
    icon='resources/icon.ico'
)