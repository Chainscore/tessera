# 📋 Git Guidelines

This doc outlines our git workflow and conventions for the Tessera project. Following these guidelines ensures consistent development practices across our team.

## 🌿 Branch Structure

```
main (stable) → develop (integration) → feature branches
```

- **`main`**: Production-ready code, always deployable
- **`develop`**: Integration branch for features, pre-release testing
- **Feature branches**: All development work happens here

![GitFlow](https://wac-cdn.atlassian.com/dam/jcr:cc0b526e-adb7-4d45-874e-9bcea9898b4a/04%20Hotfix%20branches.svg?cdnVersion=2612)

## 🔄 Workflow

### 1. Creating a New Feature

```bash
# Always start from an updated develop branch
git checkout develop
git pull origin develop

# Create a new feature branch
git checkout -b feature/descriptive-name
```

### 2. Branch Naming Conventions

- **Features**: `feature/short-description`
- **Bugfixes**: `fix/issue-description`
- **Documentation**: `docs/what-changed`
- **Performance**: `perf/what-improved`
- **Tests**: `test/what-tested`
- **Refactoring**: `refactor/what-changed`

Examples:
- ✅ `feature/safrole-consensus`
- ✅ `fix/state-sync-error`
- ✅ `docs/consensus-algorithm`
- ❌ `my-branch` (too vague)
- ❌ `feature` (too vague)

## 📝 Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) standard:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

### Types:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Formatting, missing semicolons, etc; no code change
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

### Examples:
- ✅ `feat(consensus): implement Safrole protocol`
- ✅ `fix(network): resolve peer discovery timeout`
- ✅ `docs: update installation instructions`
- ❌ `updated code` (too vague)
- ❌ `fixed bug` (too vague)

## 🔍 Pull Request Process

1. **Create PR**: From your feature branch to `develop`
2. **Title**: Follow commit convention `type: description`
3. **Description**:
   - What changes does this PR introduce?
   - Why are these changes necessary?
   - Any relevant issue numbers?
   - How was this tested?
   - Screenshots (if UI changes)

### PR Template:
```markdown
## Description
[Description of the changes]

## Related Issues
Fixes #[issue number]

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have updated the documentation accordingly
```

### Review Requirements:
- At least 2 approvals required
- All CI checks must pass
- All review comments must be resolved

## 🔄 Merging Strategy

We use **Squash and Merge** for all PRs:
- Combines all feature branch commits into one commit on `develop`
- Maintains clean, readable history
- The squashed commit message should follow our commit conventions

## 🛠️ Handling Conflicts

```bash
# If conflicts arise between your branch and develop
git checkout develop
git pull origin develop
git checkout your-branch-name
git merge develop
# Resolve conflicts in your editor
git add .
git commit -m "merge: resolve conflicts with develop"
```

## 🏷️ Tagging and Releases

```bash
# Create a new tag
git tag -a v0.1.0 -m "First beta release"
git push origin v0.1.0
```

- We use [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH)
- Release tags are created from the `main` branch after PR from `develop`

## ⚙️ Git Hooks

We use pre-commit hooks for quality checks:
- Code formatting (black, isort)
- Linting (flake8)
- Type checking (mypy)
- Test coverage verification

First-time setup:
```bash
uv run pre-commit install
```

## 🧰 Useful Git Commands

```bash
# Stashing changes temporarily
git stash
git stash pop

# Viewing commit history with graph
git log --graph --oneline --all

# Amending your last commit (before pushing)
git commit --amend

# Interactive rebase to clean up commits (before PR)
git rebase -i HEAD~3  # Rebase last 3 commits
```

## 📚 Resources

- [Pro Git Book](https://git-scm.com/book/en/v2)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

## ❓ FAQ

**Q: I accidentally committed to develop, what should I do?**
A: If not pushed yet, use `git reset HEAD~1` to undo the commit, then create proper branch. If already pushed, consult with team lead.

**Q: How do I update my PR after review feedback?**
A: Make changes on your branch and push. The PR updates automatically.

**Q: How often should I commit?**
A: Commit logical chunks of work, usually when a specific task is complete. Avoid huge commits that mix many changes.

---

