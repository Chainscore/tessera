import os, sys, pathlib, glob, importlib, platform
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

# ------------------------------------------------------------------ #
# Robust repo-root detection
if '__file__' in globals():                       # normal exec
    project_root = pathlib.Path(__file__).resolve().parent
else:                                             # PyInstaller exec
    project_root = pathlib.Path(sys.argv[0]).resolve().parent
# ------------------------------------------------------------------ #

print(">> Starting Tessera PyInstaller build...")

# ------------------------------------------------------------------ #
# Dep-paths relative to repo root
rust_dep_paths = [
    project_root / 'deps' / 'py-ark-vrf',
    project_root / 'deps' / 'tsrkit-asm' / 'python',
    project_root / 'deps' / 'tsrkit-pvm',
    project_root / 'deps' / 'tsrkit-types',
    project_root / 'deps' / 'rockstore' / 'src',
    project_root,
]

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

# Collect from build directory (standard build output)
pvm_build_glob = project_root.glob('deps/tsrkit-pvm/build/**/*.so')
for so_file in pvm_build_glob:
    rel_dest = str(so_file.relative_to(project_root / 'deps/tsrkit-pvm/build')).replace(so_file.name, '')
    binaries.append((str(so_file), rel_dest.rstrip('/')))

# Collect from in-place builds (build_ext --inplace output)
pvm_inplace_glob = project_root.glob('deps/tsrkit-pvm/tsrkit_pvm/**/*.so')
for so_file in pvm_inplace_glob:
    rel_dest = str(so_file.relative_to(project_root / 'deps/tsrkit-pvm')).replace(so_file.name, '')
    binaries.append((str(so_file), rel_dest.rstrip('/')))

# Also check for .pyd files on Windows and .dylib on macOS
for ext in ['*.pyd', '*.dylib']:
    for so_file in project_root.glob(f'deps/tsrkit-pvm/tsrkit_pvm/**/{ext}'):
        rel_dest = str(so_file.relative_to(project_root / 'deps/tsrkit-pvm')).replace(so_file.name, '')
        binaries.append((str(so_file), rel_dest.rstrip('/')))

# ------------------------------------------------------------------ #
# SRS file (needed by py-ark-vrf) - use relative path
srs_path = project_root / 'deps' / 'py-ark-vrf' / 'bandersnatch_ring.srs'
if srs_path.exists():
    essential_files.extend([
        (str(srs_path), '.'),
        (str(srs_path), 'py_ark_vrf')
    ])

# ------------------------------------------------------------------ #
hidden = (
    ['jam']
    + collect_submodules('tsrkit_pvm')
    + collect_submodules('tsrkit_asm')
    + collect_submodules('tsrkit_types')
    + collect_submodules('rockstore')
    + collect_submodules('py_ark_vrf')
    + collect_submodules('bitarray')
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
    pathex=[str(p) for p in rust_dep_paths],
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
