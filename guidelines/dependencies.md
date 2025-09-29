# 📦 Dependency Management Guidelines

This document outlines our approach to managing dependencies in the Tessera project, ensuring security, stability, and maintainability.

## 🎯 Dependency Philosophy

We follow these core principles:

1. **Minimal Dependencies**: Only add dependencies when necessary
2. **Security First**: Prioritize security in dependency selection
3. **Stability**: Prefer mature, well-maintained libraries
4. **Explicit Versioning**: Pin dependencies to specific versions
5. **Regular Updates**: Keep dependencies updated and audited

## 📋 Dependency Types

### Primary Dependencies

- **Runtime Dependencies**: Required for production operation
- **Development Dependencies**: Tools for testing, linting, etc.
- **Optional Dependencies**: Additional features not required core functionality

## 🛠️ Adding Dependencies

### Evaluation Process

Before adding a new dependency, evaluate:

1. **Necessity**: Can we implement this ourselves? Is the functionality worth the dependency?
2. **Maintenance**: Is the project actively maintained?
3. **Community Support**: Size of community, responsiveness to issues
4. **Security History**: Past vulnerabilities and response time
5. **License Compatibility**: Must be compatible with our license
6. **Performance Impact**: Minimal overhead for critical components
7. **Size**: Minimizing bloat, especially for user-facing components

### Proposal Process

1. **Research**: Document the need and alternatives
2. **Discussion**: Create a GitHub Discussion with:
   - Purpose of the dependency
   - Alternatives considered
   - Security/maintenance evaluation
   - Integration plan

3. **Approval**: Get sign-off from at least one technical lead
4. **Implementation**: Follow the implementation process

### Implementation

```bash
# Adding runtime dependency
uv add package-name==1.2.3

# Adding development dependency
uv add package-name==1.2.3 --dev

# Adding dependency with extras
uv add "package-name[extra1,extra2]==1.2.3"

# Adding to optional dependency groups (edit pyproject.toml directly)
# Then run: uv sync
```

After adding:

1. Update `README.md` or documentation if needed
2. Run security scan: `uv run safety check`
3. Run all tests: `uv run pytest`
4. Document usage examples

## 🔍 Dependency Auditing

### Regular Audits

We conduct dependency audits:

- **Weekly**: Automated security scanning
- **Monthly**: Review for updates and deprecations
- **Quarterly**: Full dependency review, including removal candidates

### Security Scanning

```bash
# Using safety
uv run safety check

# Using pip-audit  
uv run pip-audit

# Check for known vulnerabilities with specific output
poetry export -f requirements.txt | safety check --full-report
```

### Version Updates

```bash
# List outdated packages
poetry show -o

# Update all dependencies (with care)
poetry update

# Update specific package
poetry update package-name
```

## 📤 Removing Dependencies

When a dependency is no longer needed:

1. **Document**: Create a proposal explaining:
   - Why it's no longer needed
   - Migration plan for existing usages
   - Backward compatibility impact

2. **Refactor**: Remove all usage of the dependency
3. **Remove**: 
   ```bash
   poetry remove package-name
   ```
4. **Test**: Verify all functionality still works
5. **Document**: Update relevant documentation

## 🔒 Dependency Security

### Handling Vulnerabilities

When a vulnerability is discovered:

1. **Assess Impact**: Determine severity and exposure
2. **Develop Plan**: Update or replace dependency
3. **Implement**: Apply fix with minimal disruption
4. **Document**: Record incident and resolution

### Response Timeframes

- **Critical**: Immediate action, fix within 24 hours
- **High**: Fix within 1 week
- **Medium**: Fix within 2 weeks
- **Low**: Address in next release cycle

## 📊 Dependency Pinning Strategy

### Version Specification

We use explicit pinning for stability:

```toml
# In pyproject.toml
[tool.poetry.dependencies]
python = ">=3.11,<3.12"
important-package = "==1.2.3"
less-critical-package = ">=1.0.0,<2.0.0"
```

### Handling Transitive Dependencies

- Use `poetry export --with-credentials` to lock all dependencies
- Review full dependency tree with `poetry show --tree`
- Use `poetry.lock` to ensure consistency across environments

## 📚 Using Python Built-in Libraries

Before adding external dependencies, consider Python's standard library:

- **HTTP Requests**: `urllib` or `http.client` (vs. `requests`)
- **Data Processing**: `csv`, `json` (vs. third-party parsers)
- **Date/Time**: `datetime` (vs. specialized libraries)
- **Concurrency**: `asyncio`, `threading` (vs. external async frameworks)
- **Testing**: `unittest` (vs. pytest for simple cases)

## 🧩 Common Dependencies and Alternatives

| Need | Recommended | Alternatives | Notes |
|------|-------------|--------------|-------|
| HTTP | `aiohttp` | `httpx`, `requests` | Prefer async for network I/O |
| Serialization | `msgpack` | `json`, `protobuf` | Balance between speed and size |
| Cryptography | `cryptography` | `pynacl` | Never implement crypto yourself |
| CLI | `click` | `argparse` | Standard library for simpler cases |
| Testing | `pytest` | `unittest` | Standard library for simpler cases |

## 🔄 Managing Multiple Python Versions

### Development Strategy

- Use `pyenv` to manage Python versions
- Test with all supported Python versions:
  ```bash
  tox -e py38,py39,py310,py311
  ```

### CI Testing

Our CI pipeline tests with:
- Python 3.11 (primary)
- Python 3.12 (compatibility testing)

## 📚 Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [PyPI](https://pypi.org/) - Python Package Index
- [Safety Documentation](https://safety.pypa.io/)
- [OWASP Dependency Management](https://owasp.org/www-project-dependency-check/)

## ❓ FAQ

**Q: When should I use poetry add vs. manually editing pyproject.toml?**
A: Always use `poetry add` to ensure consistency in poetry.lock.

**Q: How do I handle conflicting dependencies?**
A: First try `poetry update` to resolve. If that fails, you may need to find alternative packages or versions that are compatible.

**Q: How strict should version pinning be?**
A: Runtime dependencies should be pinned to exact versions (==1.2.3) while dev dependencies can use more flexible ranges (>=1.2.0,<2.0.0).

**Q: What if I need a dependency not available on PyPI?**
A: For GitHub dependencies:
```bash
poetry add git+https://github.com/org/repo.git#branch
```