import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# Paths
project_root = os.path.abspath('.')
rust_dep_paths = [
    os.path.join(project_root, 'deps', 'py-ark-vrf'),
    os.path.join(project_root, 'deps', 'tsrkit-asm', 'python'),
    os.path.join(project_root, 'deps', 'tsrkit-pvm'),
    project_root
]

# Configuration files and tests
config_files = [
    ('genesis.json', '.'),
    ('dev-spec.json', '.'),
    ('envs', 'envs'),
    ('tests', 'tests'),
]

a = Analysis(
    ['jam/cli.py'],
    pathex=rust_dep_paths,
    binaries=[],
    datas=config_files,
    hiddenimports=[
        'collections.abc', 'sympy', 'py_ecc', 'deepdiff', 
        'tsrkit_asm', 'jam.cli', 'jam.audit'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'test', 'tkinter', 'matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='tessera-node',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
