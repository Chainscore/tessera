# Tessera

Clean-room JAM client implementation in Python

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- Git

### Setup

1. **Clone the repository with submodules:**
   ```bash
   git clone --recursive https://github.com/chainscore/tessera.git
   cd tessera
   ```

2. **Run the automated setup script:**
   ```bash
   ./scripts/setup.sh
   ```

   This script will:
   - ✅ Check Python version compatibility
   - 📦 Create a local virtual environment
   - 📚 Install Poetry (if not already installed)
   - 📥 Initialize and update Git submodules
   - 📦 Install all project dependencies
   - 🔗 Set up pre-commit hooks
   - 💾 Create necessary data directories

3. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

### Development Workflow

- **Run the application:**
  ```bash
  poetry run jam
  ```

- **Run tests:**
  ```bash
  # All tests (unit + integration + vectors)
  poetry run poe tests
  
  # Just unit tests
  poetry run poe tests unit
  
  # Test vectors for specific module
  poetry run poe tests vectors --module safrole
  
  # Test vectors with tiny spec
  poetry run poe tests vectors --module accumulate --spec tiny
  ```

- **Update internal dependencies:**
  ```bash
  poetry run poe update-deps
  ```

- **Update dependencies:**
  ```bash
  poetry update
  ```

- **Build binary:**
  ```bash
  poetry run poe build
  ```

## 📦 Dependencies

This project uses several external dependencies that are managed as Git submodules:

- `py-ark-vrf` - VRF implementation (uses published ark-vrf crate from crates.io)
- `tsrkit-pvm` - PVM toolkit
- `tsrkit-asm` - Assembly toolkit
- `tsrkit-types` - Serialization & scrit typing

## 🧪 Test Suites

The repository includes comprehensive test suites as a submodule:

- **W3F Test Vectors** - Official JAM protocol test vectors
- **PVM Tests** - Polkavm execution tests
- **Trace Tests** - State transition trace validation
- **Performance Tests** - Benchmarking and profiling tools

All submodules are automatically handled by the setup script.

## 🛠️ Manual Setup (Alternative)

If you prefer to set up manually:

1. **Clone with submodules:**
   ```bash
   git clone --recursive https://github.com/chainscore/tessera.git
   cd tessera
   ```

2. **Install Poetry:**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Setup:**
   ```bash
   poetry run poe setup
   source venv/bin/activate
   ```

4. **Start Dev Node**
   ```bash
   poetry run jam --env envs/40000.env
   ```

## 🔧 Troubleshooting

### Python Version Issues
- Ensure you have Python 3.12 or higher installed
- Check your Python version: `python3 --version`

### Submodule Issues
- Run update-deps: `poetry run poe update-deps`

#### Alternate option:
- Update submodules: `git submodule update --init --recursive`
- Force update: `git submodule update --remote --merge`

### Virtual Environment Issues
- Recreate venv: `rm -rf venv && python3 -m venv venv`
- Reactivate: `source venv/bin/activate`

### Dependency Issues
- Clear Poetry cache: `poetry cache clear --all .`
- Reinstall: `poetry install --no-cache`

## 📋 Development Guidelines

See [guidelines/](guidelines/) for detailed development guidelines:

- [Architecture](guidelines/architecture.md)
- [Code Style](guidelines/code.md)
- [Dependencies](guidelines/dependencies.md)
- [Testing](guidelines/testing.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `poetry run pytest`
5. Submit a pull request

## 📄 License

GPL-3.0-only

## How to Create an Executable Binary from PyArmor-protected Code

```bash
poetry run poe build
```

## How to run the Binary

```bash
./dist/tessera-node --env envs/40000.env
```
