# PyInstaller spec file for music-algorithm
# Build with: pyinstaller music_algorithm.spec --clean --noconfirm

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'spotipy',
        'spotipy.oauth2',
        'spotipy.cache_handler',
        'spotipy.exceptions',
        'spotipy.util',
        'requests',
        'requests.adapters',
        'urllib3',
        'certifi',
        'charset_normalizer',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['networkx'],  # imported in requirements but unused at runtime; reduces exe size
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
    name='music-algorithm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,   # CLI tool — keep the console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
