# 👋 Onboarding Guide

Welcome to the Tessera team! This guide will help you get set up and productive as quickly as possible.

## 🚀 Getting Started

### 📋 First Day Checklist

- [ ] Set up your development environment
- [ ] Clone the Tessera repository
- [ ] Run the test suite successfully
- [ ] Build the documentation
- [ ] Run a local Tessera node
- [ ] Join team communication channels

### 🔑 Access Requirements

Contact your team lead to get access to:

- GitHub repository access
- Google Chat for team communication
- Azure resources for deployments (optional)
- Team calendar for meetings
- Any other project-specific tools

## 💻 Development Environment Setup

### 🐍 Python Environment

Tessera requires **Python 3.11+**. We recommend using pyenv to manage Python versions:

#### macOS

```bash
# Install pyenv
brew install pyenv

# Install Python 3.11
pyenv install 3.11.4

# Set as global default
pyenv global 3.11.4
```

#### Ubuntu/Debian

```bash
# Dependencies
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl git

# Install pyenv
curl https://pyenv.run | bash

# Add to path (add to your .bashrc or .zshrc)
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Install Python 3.11
pyenv install 3.11.4
pyenv global 3.11.4
```

### 📦 UV Setup

We use UV for fast, modern Python package management:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to your PATH (restart shell or run)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify installation
uv --version
```

### 📥 Project Setup

```bash
# Clone repository
git clone https://github.com/chainscore/tessera.git
cd tessera

# Install dependencies
uv sync

# Set up pre-commit hooks
uv run pre-commit install
```

### 🔧 IDE Setup

#### VS Code (Recommended)

1. Install VS Code from [code.visualstudio.com](https://code.visualstudio.com/)

2. Install essential extensions:
   - Python
   - Pylance
   - Black Formatter
   - isort
   - Ruff
   - Test Explorer UI
   - Python Test Explorer

3. Configure settings (`settings.json`):
   ```json
   {
     "python.formatting.provider": "black",
     "editor.formatOnSave": true,
     "python.linting.enabled": true,
     "python.linting.flake8Enabled": true,
     "python.linting.mypyEnabled": true,
     "python.testing.pytestEnabled": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     }
   }
   ```

#### PyCharm

1. Install PyCharm from [jetbrains.com](https://www.jetbrains.com/pycharm/)

2. Install plugins:
   - Black
   - isort

3. Configure Python interpreter:
   - Go to Settings → Project → Python Interpreter
   - Add Interpreter → System Interpreter
   - Select the Python interpreter in your UV environment

## 🧪 Verifying Your Setup

Run these commands to verify your setup:

```bash
# Run tests
pytest

# Format code
black .
isort .

# Lint code
flake8

# Type check
mypy jam/

# Build documentation
cd docs
make html
cd ..

# Run Tessera
jam
```

## 🛠️ Common Development Tasks

### 📦 Managing Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a development dependency  
uv add package-name --dev

# Update dependencies
uv lock --upgrade

# View installed packages
uv tree

# Run commands in the project environment
uv run command-name
```

### 🔄 Git Workflow

See [git.md](./git.md) for detailed git guidelines.

Basic workflow:
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add my feature"

# Push to GitHub
git push -u origin feature/my-feature

# Create PR via GitHub UI
```

### 🧪 Testing

See [testing.md](./testing.md) for detailed testing guidelines.

Basic testing commands:
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=jam

# Run specific test
pytest tests/unit/test_file.py::test_function
```

### 📚 Documentation

See [docs.md](./docs.md) for detailed documentation guidelines.

```bash
# Build documentation
cd docs
make html

# View in browser
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
```

## 🎓 Learning Resources

### 📘 Python Resources

- [Official Python Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python Tutorials](https://realpython.com/)
- [Python Type Hints Guide](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### 📗 Blockchain Resources

- [JAM Protocol Specification](https://example.com/jam-spec)  <!-- Update with actual link -->
- [Substrate Documentation](https://docs.substrate.io/)
- [Blockchain Fundamentals Course](https://www.coursera.org/learn/blockchain-basics)
- [Polkadot Wiki](https://wiki.polkadot.network/)

### 📙 Project-Specific Resources

- [Tessera Documentation](https://github.com/chainscore/tessera/docs)
- [Team Architecture Documents](https://github.com/chainscore/tessera/wiki)
- [Project Roadmap](https://github.com/chainscore/tessera/projects)

## 👥 Team Communication

- **Daily Standups**: 10:00 AM, in-person or via Google Meet
- **Sprint Planning**: Every two weeks, Monday at 2:00 PM
- **Code Reviews**: Required for all PRs, aim to review within 24 hours
- **Technical Discussions**: Use GitHub Discussions for technical topics
- **Urgent Issues**: Google Chat for immediate attention

## 🗓️ Development Process

- We use 2-week sprints for planning
- GitHub Projects for task tracking
- Pull requests for all changes
- Code reviews by at least 2 team members
- CI/CD for automated testing and deployment

## ❓ FAQ

**Q: What should I work on first?**
A: Start with issues tagged "good first issue" in GitHub.

**Q: Who do I ask for help?**
A: Your team lead is your first point of contact. For technical questions, the team chat is a good place to ask.

**Q: How do I run a local test network?**
A: See the [Local Development Network](./docs/modules/network.rst) guide.

**Q: How do I debug issues?**
A: Use Python's built-in debugger or VS Code's debugging tools. See debugging section in our development guide.

## 🎉 Next Steps

1. Set up your development environment
2. Complete the [Tessera Tutorial](./docs/tutorials/getting_started.rst)
3. Explore the codebase, starting with the module structure
4. Take on your first issue!

Welcome to the team! 🚀