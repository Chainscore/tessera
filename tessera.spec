import os
import platform
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

print("🚀 Starting Tessera PyInstaller build with MyPyC optimizations...")

# Paths
project_root = os.path.abspath('.')
rust_dep_paths = [
    os.path.join(project_root, 'deps', 'py-ark-vrf'),
    os.path.join(project_root, 'deps', 'tsrkit-asm', 'python'),
    os.path.join(project_root, 'deps', 'tsrkit-pvm'),
    os.path.join(project_root, 'deps', 'tsrkit-types'),
    os.path.join(project_root, 'deps', 'rockstore', 'src'),
    project_root
]

# Platform-specific RocksDB library bundling and MyPyC compiled modules
rocksdb_binaries = []
mypyc_binaries = []
system = platform.system()

if system == "Linux":
    rocksdb_lib_path = os.path.join(project_root, 'libs', 'librocksdb.so')
    if os.path.exists(rocksdb_lib_path):
        rocksdb_binaries = [(rocksdb_lib_path, 'lib')]
elif system == "Darwin":
    rocksdb_lib_path = os.path.join(project_root, 'libs', 'librocksdb.dylib')
    if os.path.exists(rocksdb_lib_path):
        rocksdb_binaries = [(rocksdb_lib_path, 'lib')]

# Find and bundle MyPyC compiled extensions from tsrkit-pvm
mypyc_build_dir = os.path.join(project_root, 'deps', 'tsrkit-pvm', 'build')
if os.path.exists(mypyc_build_dir):
    print(f"Looking for MyPyC compiled modules in: {mypyc_build_dir}")
    # Find all .so/.dylib/.pyd files in the build directory
    for root, dirs, files in os.walk(mypyc_build_dir):
        for file in files:
            if file.endswith(('.so', '.dylib', '.pyd')):
                src_path = os.path.join(root, file)
                # Calculate relative path for destination
                rel_path = os.path.relpath(root, mypyc_build_dir)
                if rel_path == '.':
                    dest_path = '.'
                else:
                    dest_path = rel_path
                mypyc_binaries.append((src_path, dest_path))
                print(f"Found MyPyC module: {src_path} -> {dest_path}")

# Also check in the package directory for in-place compiled modules
pvm_package_dir = os.path.join(project_root, 'deps', 'tsrkit-pvm', 'tsrkit_pvm')
if os.path.exists(pvm_package_dir):
    for root, dirs, files in os.walk(pvm_package_dir):
        for file in files:
            if file.endswith(('.so', '.dylib', '.pyd')):
                src_path = os.path.join(root, file)
                # Calculate relative path for destination within the package
                rel_path = os.path.relpath(root, pvm_package_dir)
                if rel_path == '.':
                    dest_path = 'tsrkit_pvm'
                else:
                    dest_path = os.path.join('tsrkit_pvm', rel_path)
                mypyc_binaries.append((src_path, dest_path))
                print(f"Found in-place MyPyC module: {src_path} -> {dest_path}")

# Combine all binaries
all_binaries = rocksdb_binaries + mypyc_binaries

# Essential configuration files only - minimal set
essential_files = [
    ('dev-spec.json', '.'),
    ('envs', 'envs'),
    # Include SRS file for VRF operations
    ('deps/py-ark-vrf/bandersnatch_ring.srs', '.'),
    ('deps/py-ark-vrf/py_ark_vrf/bandersnatch_ring.srs', 'py_ark_vrf'),
]

# Essential hidden imports for core functionality and MyPyC modules
core_imports = [
    'jam',
    # MyPyC compiled modules from tsrkit-pvm
    'tsrkit_pvm.common.utils',
    'tsrkit_pvm.common.status',
    'tsrkit_pvm.common.constants',
    'tsrkit_pvm.core.code',
    'tsrkit_pvm.core.mapper',
    'tsrkit_pvm.interpreter.pvm',
    'tsrkit_pvm.interpreter.program',
    'tsrkit_pvm.interpreter.memory',
    'tsrkit_pvm.interpreter.instructions.tables.wo_args',
    'tsrkit_pvm.interpreter.instructions.tables.i_imm',
    'tsrkit_pvm.interpreter.instructions.tables.i_offset',
    'tsrkit_pvm.interpreter.instructions.tables.i_reg_i_ewimm',
    'tsrkit_pvm.interpreter.instructions.tables.i_reg_i_imm',
    'tsrkit_pvm.interpreter.instructions.tables.i_reg_i_imm_i_offset',
    'tsrkit_pvm.interpreter.instructions.tables.ii_imm',
    'tsrkit_pvm.interpreter.instructions.tables.ii_reg',
    'tsrkit_pvm.interpreter.instructions.tables.ii_reg_i_imm',
    'tsrkit_pvm.interpreter.instructions.tables.ii_reg_i_offset',
    'tsrkit_pvm.interpreter.instructions.tables.ii_reg_ii_imm',
    'tsrkit_pvm.interpreter.instructions.tables.iii_reg',
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
    binaries=all_binaries,
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
