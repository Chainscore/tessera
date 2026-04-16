
![Tessera Logo](guidelines/cover.svg)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/Chainscore/tessera/build-binaries.yml?branch=main)](https://github.com/Chainscore/tessera/actions)
[![Test Status](https://img.shields.io/github/actions/workflow/status/Chainscore/tessera/pytest.yml?branch=main&label=tests)](https://github.com/Chainscore/tessera/actions)
[![Code Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)](https://github.com/Chainscore/tessera)


---

## About

Tessera is a Python implementation of the JAM (Join-Accumulate Machine) blockchain protocol as specified in the [JAM Graypaper](https://graypaper.com). It implements the core state transition functions, block production (Safrole), work package execution (PVM), and P2P networking required to participate in a JAM-based network.

## Installation

### Requirements

- Python 3.12
- uv package manager
- RocksDB system library

### Setup

```bash
# Clone repository (test-suites submodule is optional)
git clone --recursive https://github.com/Chainscore/tessera.git
cd tessera

# Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12

export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
uv sync --all-extras

# Initialize database directory
mkdir -p data/

# Initialize pre-commit hooks
uv run pre-commit install
```

## Usage

### Running a Node

```bash
# Start node with environment configuration
uv run jam --env envs/40000.env

# Enable validator mode
uv run jam --env envs/40000.env --validator

# Enable builder mode
uv run jam --env envs/40000.env --builder

# Disable RPC server
uv run jam --env envs/40000.env --no-rpc

# Enable telemetry
uv run jam --env envs/40000.env --telemetry host:port

# Specify database path
uv run jam --env envs/40000.env --db /path/to/db
```

### Building Binary

```bash
# Build standalone executable with PyInstaller
./build-binary.sh

# Binary output location
./dist/tessera-node-<OS>-<ARCH>.tar.gz
```

### Testing

```bash
# Run all tests
uv run pytest tests/

# Run specific test suite
uv run pytest tests/unit/safrole/
uv run pytest tests/unit/execution/
uv run pytest tests/integration/

# Run with coverage report
uv run pytest --cov=jam --cov-report=html tests/
```

## Architecture

### Core Components

- **State Management** (`jam/state/`): JAM state structure and transitions
  - Safrole: Block production and validator rotation (VRF-based)
  - Accumulation: Work report processing and service account updates
  - Disputes: Guarantor judgement system

- **Execution Engine** (`jam/execution/`): Polkavm (PVM) execution
  - Host calls: Import, export, gas, read, write, etc.
  - Invocations: Refine, accumulate, on-transfer handlers

- **Block Processing** (`jam/block/`): Header and extrinsic validation
  - Tickets: VRF ticket generation and verification
  - Guarantees: Work report guarantees
  - Assurances: Availability assurances

- **Operations** (`jam/operations/`): Node operation handlers
  - Block Producer: Ticket-based block authoring
  - Conductor: State transition orchestration
  - Assurer: Work package availability

- **Networking** (`jam/networking/`): QUIC-based P2P protocol

- **Storage** (`jam/db/`): RocksDB-backed state persistence

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure `uv run pytest` passes
5. Submit pull request

Follow the code style guidelines in `guidelines/code.md`.

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE)

Copyright (c) 2025 [Chainscore Labs](https://chainscorelabs.com/)
