import sys, pathlib, platform, site
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.utils.hooks import (
    collect_dynamic_libs,
    collect_submodules,
    collect_data_files,
    copy_metadata,
)

# ------------------------------------------------------------------ #
# Robust repo-root detection
if '__file__' in globals():                       # normal exec
    project_root = pathlib.Path(__file__).resolve().parent
else:                                             # PyInstaller exec
    project_root = pathlib.Path(sys.argv[0]).resolve().parent
# ------------------------------------------------------------------ #

print(">> Starting Tessera PyInstaller build...")

# ------------------------------------------------------------------ #
# Only the repo itself needs to be on the search path; third-party packages
# are resolved from the active environment.
analysis_paths = [project_root]

# ------------------------------------------------------------------ #
# Native binaries - detect platform-specific library extension
current_platform = platform.system()
if current_platform == 'Darwin':
    rocksdb_lib = 'librocksdb.dylib'
elif current_platform == 'Linux':
    rocksdb_lib = 'librocksdb.so'
else:
    raise RuntimeError(f"Unsupported platform: {current_platform}")

print(f">> Platform detected: {current_platform}")
print(f">> Looking for RocksDB library: {rocksdb_lib}")

# Verify the library file exists before adding to binaries
rocksdb_path = project_root / 'libs' / rocksdb_lib
if not rocksdb_path.exists():
    raise FileNotFoundError(f"RocksDB library not found: {rocksdb_path}")

binaries = [(str(rocksdb_path), 'lib')]
print(f">> RocksDB library found and added: {rocksdb_path}")

# bitarray - manual inclusion since PyInstaller has trouble finding it
bitarray_venv_path = project_root / '.venv/lib/python3.12/site-packages/bitarray'
essential_files = []

# ------------------------------------------------------------------ #
# Include distribution metadata for packages that query importlib.metadata
for package_name in ["py_ecc", "dot_ring", "rockstore", "tsrkit_pvm", "tsrkit_asm", "tsrkit_types"]:
    metadata_entries = copy_metadata(package_name)
    essential_files.extend(metadata_entries)
    print(f">> Added metadata for {package_name}: {metadata_entries}")

if bitarray_venv_path.exists():
    # Include the entire bitarray package
    essential_files.append((str(bitarray_venv_path), 'bitarray'))
    # Explicitly include the binary extensions
    bitarray_so_files = list(bitarray_venv_path.glob('*.so'))
    for so_file in bitarray_so_files:
        binaries.append((str(so_file), 'bitarray'))
    print(f"Found bitarray at: {bitarray_venv_path}")
    print(f"Found {len(bitarray_so_files)} bitarray binary extensions")
else:
    print("Warning: bitarray not found in venv")

# tsrkit-pvm compiled extensions - discover dynamically from multiple locations
binaries += collect_dynamic_libs('tsrkit_pvm')

# gmpy2 compiled extension + shared libs
binaries += collect_dynamic_libs('gmpy2')

# dot-ring files
dot_ring_datas = collect_data_files(
    "dot_ring",
    includes=[
        "ring_proof/columns/*.json",
        "vrf/data/*.bin"
    ]
)

if not dot_ring_datas:
    raise RuntimeError(
        "Failed to collect dot_ring SRS data files. "
        "Is 'dot-ring' installed in this environment?"
    )

essential_files.extend(dot_ring_datas)

print(f">> Added dot-ring data files: {dot_ring_datas}")

# Add dev-spec.json in project root to the bundle root (meipass)
dev_spec = project_root / "dev-spec.json"
if dev_spec.exists():
    essential_files.append((str(dev_spec), "."))

# ------------------------------------------------------------------ #
hidden = (
    ['jam', 'gmpy2']
    + collect_submodules('tsrkit_pvm')
    + collect_submodules('tsrkit_asm')
    + collect_submodules('tsrkit_types')
    + collect_submodules('rockstore')
    + collect_submodules('bitarray')
    + collect_submodules('py_ecc')
)

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
    pathex=[str(p) for p in analysis_paths],
    binaries=binaries,
    datas=essential_files,
    hiddenimports=hidden,
    excludes=excluded_modules,
    optimize=1
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
