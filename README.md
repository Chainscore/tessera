# Tessera

JAM blockchain client implementation in Python

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
  ./scripts/test.sh --all
  
  # Just unit tests
  ./scripts/test.sh --unit
  
  # Test vectors for specific module
  ./scripts/test.sh --vectors --module safrole
  
  # Test vectors with full spec
  ./scripts/test.sh --vectors --module accumulate --spec full
  ```

- **Update submodules:**
  ```bash
  ./scripts/update-submodules.sh
  ```

- **Update dependencies:**
  ```bash
  poetry update
  ```

## 📦 Dependencies

This project uses several external dependencies that are managed as Git submodules:

- `py-ark-vrf` - VRF implementation (uses published ark-vrf crate from crates.io)
- `tsrkit-pvm` - PVM toolkit
- `tsrkit-asm` - Assembly toolkit

## 🧪 Test Suites

The repository includes comprehensive test suites as a submodule:

- **W3F Test Vectors** - Official JAM protocol test vectors
- **Jamduna Test Vectors** - Additional implementation test vectors  
- **PVM Tests** - Polkavm execution tests
- **Codec Tests** - Serialization/deserialization tests
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

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Poetry:**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

4. **Configure Poetry:**
   ```bash
   poetry config virtualenvs.create false
   poetry config virtualenvs.in-project false
   ```

5. **Install dependencies:**
   ```bash
   poetry install
   ```

6. **Setup pre-commit:**
   ```bash
   poetry run pre-commit install
   ```

## 🔧 Troubleshooting

### Python Version Issues
- Ensure you have Python 3.12 or higher installed
- Check your Python version: `python3 --version`

### Submodule Issues
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
./dist/Tessera --validator_index 0
```
