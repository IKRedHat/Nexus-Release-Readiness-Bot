# Contributing to Nexus Release Automation

First off, thank you for considering contributing to Nexus! 🚀 It's people like you that make Nexus such a great tool for release automation.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Review Process](#review-process)
- [Community](#community)

---

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [nexus-maintainers@example.com](mailto:nexus-maintainers@example.com).

---

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**
- **Docker & Docker Compose**
- **Git**

### Quick Setup

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/Nexus-Release-Readiness-Bot.git
cd Nexus-Release-Readiness-Bot

# 3. Add upstream remote
git remote add upstream https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git

# 4. Run the one-click setup
./scripts/setup.sh --dev

# 5. Verify everything works
./scripts/verify.sh
```

### Project Structure

```
Nexus-Release-Readiness-Bot/
├── services/                  # Microservices
│   ├── orchestrator/          # Central brain (ReAct engine)
│   └── agents/                # Specialized agents
│       ├── jira_agent/
│       ├── git_ci_agent/
│       ├── reporting_agent/
│       ├── slack_agent/
│       └── jira_hygiene_agent/
├── shared/nexus_lib/          # Shared library
├── infrastructure/            # Docker, K8s, Terraform
├── tests/                     # Unit and E2E tests
├── docs/                      # Documentation
└── scripts/                   # Development scripts
```

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**When reporting a bug, include:**

- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Environment details (OS, Python version, Docker version)
- Relevant logs or screenshots
- Possible fix (if you have one in mind)

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) when creating an issue.

### 💡 Suggesting Features

We love feature suggestions! Before suggesting:

- Check if the feature already exists
- Check if there's an open issue for it
- Consider if it aligns with Nexus's goals

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) when creating an issue.

### 📝 Improving Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples or use cases
- Improve code comments
- Add missing API documentation

### 🔧 Contributing Code

Ready to contribute code? Here's how:

1. **Find an issue** - Look for issues labeled `good first issue` or `help wanted`
2. **Claim the issue** - Comment that you're working on it
3. **Create a branch** - Follow our [branching strategy](#branching-strategy)
4. **Write code** - Follow our [style guidelines](#style-guidelines)
5. **Write tests** - Ensure your code is tested
6. **Submit a PR** - Follow the [PR process](#pull-request-process)

---

## Development Workflow

### Branching Strategy

We use a simplified Git Flow:

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code |
| `develop` | Integration branch for features |
| `feature/*` | New features |
| `bugfix/*` | Bug fixes |
| `hotfix/*` | Urgent production fixes |
| `docs/*` | Documentation updates |

**Branch naming convention:**

```
feature/add-slack-app-home
bugfix/fix-hygiene-score-calculation
hotfix/critical-auth-bypass
docs/update-api-reference
```

### Creating a Feature Branch

```bash
# Ensure you're up to date
git checkout main
git pull upstream main

# Create your feature branch
git checkout -b feature/your-feature-name

# Make your changes...

# Keep your branch updated
git fetch upstream
git rebase upstream/main
```

### Running Tests

```bash
# Run all tests
./scripts/dev.sh test

# Run specific test categories
./scripts/dev.sh test-unit      # Unit tests only
./scripts/dev.sh test-e2e       # E2E tests only

# Run with coverage
pytest tests/ --cov=shared --cov=services --cov-report=html

# Run linters
./scripts/dev.sh lint
```

### Local Development

```bash
# Start all services
./scripts/dev.sh start

# View logs
./scripts/dev.sh logs

# Check health
./scripts/dev.sh health

# Send a test query
./scripts/dev.sh query "Is the v2.0 release ready?"

# Run a hygiene check
./scripts/dev.sh hygiene PROJ
```

---

## Style Guidelines

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 120 characters max
- **Imports**: Use `isort` for sorting
- **Formatting**: Use `black` for auto-formatting
- **Type hints**: Required for all public functions
- **Docstrings**: Google style

```python
from typing import Dict, List, Optional

def calculate_hygiene_score(
    tickets: List[Dict],
    required_fields: Optional[List[str]] = None
) -> float:
    """
    Calculate the hygiene score for a list of tickets.

    Args:
        tickets: List of Jira ticket dictionaries.
        required_fields: Fields to check. Defaults to standard fields.

    Returns:
        Hygiene score as a percentage (0-100).

    Raises:
        ValueError: If tickets list is empty.

    Example:
        >>> score = calculate_hygiene_score(tickets)
        >>> print(f"Score: {score}%")
    """
    if not tickets:
        raise ValueError("Tickets list cannot be empty")
    
    # Implementation...
```

### Formatting Your Code

```bash
# Format with black
black shared/ services/ tests/

# Sort imports
isort shared/ services/ tests/

# Check linting
flake8 shared/ services/ --max-line-length=120

# Type checking
mypy shared/ --ignore-missing-imports
```

### Testing Standards

Nexus uses a comprehensive testing strategy with ~370 tests across 4 categories:

| Category | Location | Purpose | Required For |
|----------|----------|---------|--------------|
| **Unit** | `tests/unit/` | Isolated component testing | All new functions |
| **E2E** | `tests/e2e/` | Service endpoint testing | New endpoints |
| **Integration** | `tests/integration/` | Inter-service workflows | Cross-service features |
| **Smoke** | `tests/smoke/` | Quick health checks | Major deployments |

**Requirements:**
- **Unit tests**: Required for all new functions/classes
- **E2E tests**: Required for new endpoints/features
- **Coverage**: Aim for 80%+ coverage on new code
- **Naming**: `test_<action>_<scenario>` (e.g., `test_validate_ticket_missing_labels`)

**Running Tests:**
```bash
# Run all tests
pytest

# Run by category
pytest -m unit           # Unit tests
pytest -m e2e            # E2E tests
pytest -m integration    # Integration tests
pytest -m smoke          # Smoke tests

# Run with coverage
pytest --cov=shared --cov-report=html
```

**Example Test:**
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestHygieneChecker:
    """Tests for the HygieneChecker class."""

    @pytest.fixture
    def checker(self):
        """Create checker with mocked dependencies."""
        return HygieneChecker(mock_client, mock_config)

    def test_validate_ticket_missing_labels(self, checker):
        """Should detect missing labels as a violation."""
        ticket = {"key": "PROJ-123", "fields": {"labels": []}}
        violations = checker._validate_ticket(ticket)
        assert "Labels" in violations

    @pytest.mark.asyncio
    async def test_check_hygiene_sends_notifications(self, checker):
        """Should send DM notifications when violations are found."""
        with patch.object(checker.slack_client, "post") as mock_dm:
            mock_dm.return_value = {"status": "success"}
            await checker.check_hygiene(project_key="PROJ")
            mock_dm.assert_called()
```

📖 **[Full Testing Documentation](docs/testing.md)**

---

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `chore` | Build process, dependencies |
| `ci` | CI/CD changes |

### Examples

```bash
# Feature
feat(hygiene): add interactive Slack modal for fixing violations

# Bug fix
fix(orchestrator): resolve memory leak in ReAct loop

# Documentation
docs(api): add OpenAPI specs for hygiene agent endpoints

# With breaking change
feat(auth)!: switch to OAuth 2.0 authentication

BREAKING CHANGE: API tokens are no longer supported.
Use OAuth 2.0 tokens instead.
```

### Commit Best Practices

- ✅ Use present tense: "Add feature" not "Added feature"
- ✅ Use imperative mood: "Fix bug" not "Fixes bug"
- ✅ Keep subject line under 72 characters
- ✅ Reference issues: "Fixes #123"
- ❌ Don't end subject with a period

---

## Pull Request Process

### Before Submitting

- [ ] Code follows our style guidelines
- [ ] All tests pass locally
- [ ] New code has appropriate tests
- [ ] Documentation is updated (if applicable)
- [ ] Commit messages follow conventions
- [ ] Branch is rebased on latest `main`

### Creating a Pull Request

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a PR** on GitHub against `main` (or `develop` for features)

3. **Fill out the PR template** completely

4. **Request reviewers** - Tag relevant maintainers

5. **Respond to feedback** - Address review comments promptly

### PR Title Format

Follow the same format as commit messages:

```
feat(hygiene): add interactive Slack modal for fixing violations
fix(orchestrator): resolve memory leak in ReAct loop
docs(readme): update quick start instructions
```

### PR Size Guidelines

| Size | Lines Changed | Review Time |
|------|---------------|-------------|
| XS | < 50 | < 30 min |
| S | 50-200 | 1-2 hours |
| M | 200-500 | Half day |
| L | 500-1000 | Full day |
| XL | > 1000 | Consider splitting |

**Prefer smaller PRs** - They're easier to review and less likely to introduce bugs.

---

## Review Process

### For Contributors

After submitting your PR:

1. **Wait for CI** - All checks must pass
2. **Address feedback** - Respond to all comments
3. **Request re-review** - After making changes
4. **Be patient** - Reviews may take 1-3 business days

### For Reviewers

When reviewing PRs, check:

#### Code Quality
- [ ] Code is readable and well-organized
- [ ] Functions have clear, single responsibilities
- [ ] No unnecessary complexity
- [ ] Proper error handling
- [ ] No hardcoded values (use config/env vars)

#### Testing
- [ ] Tests cover the changes
- [ ] Tests are meaningful (not just for coverage)
- [ ] Edge cases are considered
- [ ] Tests pass in CI

#### Security
- [ ] No sensitive data in code
- [ ] Input validation is present
- [ ] Auth/authz is properly implemented
- [ ] No SQL injection, XSS, etc.

#### Documentation
- [ ] Public APIs are documented
- [ ] Complex logic has comments
- [ ] README/docs updated if needed

#### Performance
- [ ] No obvious performance issues
- [ ] Database queries are optimized
- [ ] No unnecessary API calls

### Review Comments

Use these prefixes for clarity:

| Prefix | Meaning |
|--------|---------|
| `blocking:` | Must be fixed before merge |
| `suggestion:` | Nice to have, not required |
| `question:` | Seeking clarification |
| `nitpick:` | Minor style preference |
| `praise:` | Highlighting good work! |

**Example:**
```
blocking: This could cause a null pointer exception if `user` is None.

suggestion: Consider extracting this into a helper function for reusability.

nitpick: Prefer `is not None` over `!= None` per PEP 8.

praise: Great test coverage here! 🎉
```

### Approving PRs

To approve a PR:

1. **Review all files** - Don't skim
2. **Run locally** (for complex changes)
3. **Leave approval** with summary comment
4. **Merge** (if you have permission) or request merge

### Merge Strategy

We use **Squash and Merge** for most PRs:

- Keeps history clean
- Single commit per feature
- PR title becomes commit message

For large features with meaningful commits, we may use **Merge Commit**.

---

## Additional Guidelines

### Security Vulnerabilities

**Do NOT open public issues for security vulnerabilities.**

Instead, email [security@example.com](mailto:security@example.com) with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

See [SECURITY.md](SECURITY.md) for our security policy.

### Dependency Updates

When updating dependencies:

1. Update one dependency at a time
2. Run full test suite
3. Note any breaking changes in PR
4. Update requirements.txt with pinned versions

### Breaking Changes

For breaking changes:

1. Discuss in an issue first
2. Add `BREAKING CHANGE:` in commit footer
3. Update migration guide
4. Bump major version

---

## Recognition

Contributors are recognized in several ways:

- 📋 Listed in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- 🏆 Highlighted in release notes
- 💎 Special badges for significant contributions

---

## Getting Help

- 💬 **Discussions**: [GitHub Discussions](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/discussions)
- 📧 **Email**: nexus-maintainers@example.com
- 📖 **Docs**: [Documentation](docs/index.md)

---

## Thank You!

Your contributions make Nexus better for everyone. Whether it's a bug fix, feature, or documentation improvement - every contribution matters! 🙏

Happy coding! 🚀

