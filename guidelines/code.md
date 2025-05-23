# 💻 Code Quality Guidelines for Tessera

This document outlines our coding standards and best practices for the Tessera project.

## 📐 Code Style

We follow a consistent code style based on established Python conventions:

### 🐍 Python Style Guide

- We follow [PEP 8](https://peps.python.org/pep-0008/) with a few customizations
- Line length: 88 characters (Black default)
- Use tabs for indentation (no spaces)

### 📝 Formatting Tools

All code is automatically formatted with:

- **Black**: Code formatting
  ```bash
  black .
  ```
  
- **isort**: Import sorting
  ```bash
  isort .
  ```

### 🔍 Linting

Code quality is enforced with:

- **Flake8**: Style guide enforcement
  ```bash
  flake8
  ```

- **Mypy**: Static type checking (strict mode)
  ```bash
  mypy --strict jam/
  ```

## 🧩 Code Organization

### 📂 Project Structure

```
jam/
├── common/           # Common utilities, shared code
├── consensus/        # Consensus mechanisms (Safrole, GRANDPA)
├── network/          # P2P networking, discovery
├── state/            # State management, transitions
├── crypto/           # Cryptographic primitives
├── codec/            # Serialization/deserialization
├── runtime/          # PVM execution environment
└── cli/              # Command-line interface
```

### 📄 File Organization

Each module should follow a consistent structure:

```python
"""Module docstring describing purpose and usage."""

# Standard library imports
import os
import sys

# Third-party imports
import numpy as np

# Local imports
from jam.common import utils

# Constants
MAX_BLOCK_SIZE = 1024 * 1024

# Classes and functions
class BlockHeader:
    """Class docstring."""
    ...
```

## 🧠 Code Design Principles

### 🎯 General Principles

1. **Explicit is better than implicit** (follow [The Zen of Python](https://peps.python.org/pep-0020/))
2. **Favor composition over inheritance**
3. **Single Responsibility Principle** - Each class/module has one job
4. **Open/Closed Principle** - Open for extension, closed for modification
5. **DRY (Don't Repeat Yourself)** - Avoid code duplication

### 🧪 Type Safety

- **Use type hints everywhere**
  ```python
  def verify_block(block: Block, previous_state: State) -> Result:
      """Verify block validity."""
  ```

- **Enable strict mypy checking**

### 🧩 Function Design

- **Small, focused functions** (under 50 lines ideally)
- **Clear argument names**
- **Use keyword arguments** for clarity
- **Document parameters** with docstrings
- **Return explicit values** (avoid side effects)

### 📊 Error Handling

- **Use exceptions for exceptional cases**
- **Create custom exception classes** for domain-specific errors
- **Fail early, fail loudly**
- **Ensure cleanup** with context managers or try/finally

```python
class InvalidBlockError(Exception):
    """Raised when a block fails validation."""
    pass

def validate_block(block: Block) -> None:
    if not block.is_valid():
        raise InvalidBlockError(f"Block {block.hash} failed validation")
```

## 📝 Documentation

### 📚 Docstrings

We use Google-style docstrings:

```python
def hash_block(block: Block) -> bytes:
    """Compute cryptographic hash of a block.
    
    Args:
        block: The block to hash
        
    Returns:
        32-byte hash digest
        
    Raises:
        TypeError: If block is not a valid Block instance
    """
```

### 📝 Comments

- Use comments to explain **why**, not what
- Comment complex algorithms or non-obvious solutions
- Keep comments up-to-date with code changes

## 🔄 Asynchronous Programming

- Use `asyncio` for concurrency
- Prefer `async`/`await` over callbacks
- Always document thread safety concerns
- Use proper async patterns, avoid mixing sync and async code

```python
async def fetch_peers(network: str) -> List[Peer]:
    """Fetch peers from the network asynchronously."""
    async with aiohttp.ClientSession() as session:
        # ...
```

## 🔒 Security Practices

- **Never hardcode secrets**
- **Validate all inputs**
- **Use safe crypto libraries** (don't implement your own)
- **Check for security vulnerabilities** in dependencies
- **Use constant-time comparisons** for cryptographic operations

```python
# Bad (timing attack vulnerable)
if user_provided_hmac == calculated_hmac:
    # ...

# Good (constant time comparison)
if hmac.compare_digest(user_provided_hmac, calculated_hmac):
    # ...
```

## 🔄 Performance Considerations

- **Profile before optimizing**
- **Document performance assumptions**
- **Use appropriate data structures**
- **Consider memory usage** for blockchain data
- **Add benchmarks** for critical paths

## 📚 Resources

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Effective Python](https://effectivepython.com/)
- [Python Type Checking Guide](https://realpython.com/python-type-checking/)
