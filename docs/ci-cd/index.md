# CI/CD Documentation

Welcome to the Nexus CI/CD documentation. This section covers all aspects of the continuous integration and deployment pipelines.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Overview](./overview.md) | High-level architecture and workflow summary |
| [CI Workflow](./ci-workflow.md) | Detailed guide to the CI pipeline |
| [Release Workflow](./release-workflow.md) | How releases are automated |
| [Dependabot](./dependabot.md) | Automated dependency updates |
| [Troubleshooting](./troubleshooting.md) | Common issues and solutions |

---

## Pipeline Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    Nexus CI/CD Pipelines                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📥 Code Changes                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    CI Workflow                           │   │
│  │  ┌─────┐ ┌─────────┐ ┌──────┐ ┌─────┐ ┌────────┐       │   │
│  │  │Lint │ │Security │ │Tests │ │E2E  │ │Docker  │       │   │
│  │  └─────┘ └─────────┘ └──────┘ └─────┘ └────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Release Workflow                         │   │
│  │  ┌──────────┐ ┌─────────────┐ ┌───────────────┐        │   │
│  │  │Build &   │ │Push to      │ │Create GitHub  │        │   │
│  │  │Test      │ │Registry     │ │Release        │        │   │
│  │  └──────────┘ └─────────────┘ └───────────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│       │                                                          │
│       ▼                                                          │
│  🚀 Production Ready                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Workflow Files

All workflow files are located in `.github/workflows/`:

| File | Trigger | Purpose |
|------|---------|---------|
| `ci.yml` | Push, PR | Main CI pipeline |
| `release.yml` | Tags (v*) | Release automation |
| `dependency-review.yml` | PR | Security scanning |
| `labeler.yml` | PR | Auto-labeling |
| `stale.yml` | Schedule | Clean up inactive issues |

---

## Getting Started

### For Contributors

1. **Fork the repository**
2. **Make your changes**
3. **Push to your fork** - CI runs automatically
4. **Create a PR** - Additional checks run
5. **Address feedback** - CI re-runs on updates
6. **Merge** - When all checks pass

### For Maintainers

1. **Review PRs** - Check CI status
2. **Merge to main** - CI runs again
3. **Create a tag** - Release workflow triggers
4. **Monitor release** - Images pushed, release created

---

## Key Concepts

### Continuous Integration (CI)

Every code change is automatically:
- ✅ Linted and formatted
- ✅ Security scanned
- ✅ Unit tested
- ✅ E2E tested
- ✅ Docker build verified

### Continuous Delivery (CD)

When a version tag is created:
- ✅ Full test suite runs
- ✅ Docker images built
- ✅ Images pushed to GHCR
- ✅ GitHub release created
- ✅ Changelog generated

### Automated Maintenance

The repository is automatically maintained:
- ✅ Dependencies updated weekly
- ✅ Stale issues/PRs cleaned up
- ✅ PRs auto-labeled
- ✅ Security vulnerabilities flagged

---

## Status Badges

Add these to your README:

```markdown
![CI](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/actions/workflows/release.yml/badge.svg)
```

---

## Environment Requirements

### Required

| Requirement | Purpose |
|-------------|---------|
| GitHub Actions | CI/CD runtime |
| `GITHUB_TOKEN` | Auto-provided, repository access |

### Optional

| Secret | Purpose |
|--------|---------|
| `CODECOV_TOKEN` | Coverage reporting |
| `SLACK_WEBHOOK_URL` | Release notifications |

---

## Support

Having issues with CI/CD?

1. Check the [Troubleshooting Guide](./troubleshooting.md)
2. Search [existing issues](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues)
3. Create a new issue with workflow logs

---

## Related Documentation

- [GitHub Setup Guide](../GITHUB_SETUP.md) - Branch protection, discussions
- [Contributing Guide](../../CONTRIBUTING.md) - How to contribute
- [Architecture](../architecture.md) - System design

