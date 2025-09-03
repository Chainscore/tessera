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

# Absolutely minimal hidden imports for core functionality
core_imports = [
    'jam.cli',
    'asyncio',
    'dotenv',
]

# Extremely aggressive exclusions to minimize binary size
excluded_modules = [
    # Development and testing
    'pytest', 'test', 'tests', 'testing', '_pytest',
    'coverage', 'pytest_cov', 'pytest_asyncio',
    
    # Code formatting and linting
    'black', 'flake8', 'isort', 'pre_commit', 'mypy', 'pylint',
    
    # Documentation
    'sphinx', 'docs', 'documentation', 'docutils',
    
    # Build tools (be careful with distutils)
    'setuptools', 'pip', 'wheel', 'pkg_resources',
    'poetry', 'pyproject', 'build',
    
    # GUI frameworks (not needed for CLI)
    'tkinter', 'turtle', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    
    # Scientific computing (not needed for blockchain)
    'matplotlib', 'numpy', 'scipy', 'pandas', 'jupyter', 
    'notebook', 'ipython', 'seaborn', 'plotly',
    
    # Web frameworks (we use minimal ones)
    'django', 'flask', 'fastapi', 'tornado',
    
    # Database drivers (we use RocksDB)
    'sqlite3', 'psycopg2', 'pymongo', 'sqlalchemy',
    
    # XML/HTML processing (not needed)
    'xml', 'html', 'html.parser', 'http.server',
    'requests', 'beautifulsoup4', 'lxml',
    
    # Image processing (not needed)
    'PIL', 'Pillow', 'imageio', 'opencv',
    
    # Compression (only need basic)
    'bz2', 'lzma', 'zipapp',
    
    # Multimedia (not needed)
    'wave', 'aifc', 'sunau', 'audioop',
    
    # Legacy modules
    'imp', 'pkgutil', 'pydoc', 'tabnanny',
    
    # Debugging
    'pdb', 'bdb', 'cProfile', 'profile', 'trace',
    
    # Networking we don't use
    'ftplib', 'smtplib', 'telnetlib',
    
    # Platform-specific modules
    'winsound', 'msilib', 'msvcrt',
    
    # Unused standard library - be careful with dependencies
    'cgi', 'cgitb', 'mailbox', 'mimetypes', 'quopri', 'uu',
    'xdrlib', 'shelve', 'dbm', 'nntplib', 'poplib',
    'imaplib', 'smtpd', 'socketserver', 'xmlrpc',
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
    optimize=2,  # Maximum optimization
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
