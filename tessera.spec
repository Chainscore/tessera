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

# Essential configuration files only - minimal set
essential_files = [
    ('dev-spec.json', '.'),
    ('envs', 'envs'),
]

# Essential hidden imports for core functionality  
core_imports = [
    'jam'
]

# Extremely aggressive exclusions to minimize binary size  
excluded_modules = [
    # Development and testing
    'pytest', 'test', 'tests', 'testing', '_pytest',
    'coverage', 'pytest_cov', 'pytest_asyncio',

    # Test suites
    'tessera-test-suites',
    
    # Code formatting and linting  
    'black', 'flake8', 'isort', 'pre_commit', 'mypy', 'pylint',
    
    # Documentation
    'sphinx', 'docs', 'documentation', 'docutils'
]

a = Analysis(
    ['jam/cli.py'],
    pathex=rust_dep_paths,
    binaries=[],
    datas=essential_files,
    hiddenimports=core_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    optimize=1,  # Maximum optimization
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='tessera-node',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,  # UPX can slow startup and cause issues
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Additional optimization flags
    exclude_binaries=False,  # Include everything in single file
)
