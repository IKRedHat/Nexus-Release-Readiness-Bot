# Dependabot Configuration

This document explains how Dependabot is configured to automatically keep Nexus dependencies up to date.

## Overview

Dependabot automatically creates pull requests to update dependencies, helping to:
- Keep packages up to date
- Fix security vulnerabilities quickly
- Reduce technical debt

---

## Configuration

**Location:** `.github/dependabot.yml`

### Package Ecosystems

| Ecosystem | Directory | Schedule | Purpose |
|-----------|-----------|----------|---------|
| `pip` | Multiple | Weekly (Monday) | Python packages |
| `github-actions` | `/` | Weekly (Monday) | Action versions |
| `docker` | `/infrastructure/docker` | Weekly (Monday) | Base images |
| `terraform` | `/infrastructure/terraform` | Monthly | Terraform providers |

---

## Python Dependencies

Dependabot monitors each service's requirements:

```yaml
# Example configuration
- package-ecosystem: "pip"
  directory: "/services/orchestrator"
  schedule:
    interval: "weekly"
    day: "monday"
    time: "09:00"
    timezone: "UTC"
  open-pull-requests-limit: 5
  labels:
    - "dependencies"
    - "python"
    - "orchestrator"
```

### Services Monitored

| Service | Directory | Label |
|---------|-----------|-------|
| Orchestrator | `/services/orchestrator` | `orchestrator` |
| Jira Agent | `/services/agents/jira_agent` | `jira-agent` |
| Jira Hygiene Agent | `/services/agents/jira_hygiene_agent` | `hygiene-agent` |
| Git/CI Agent | `/services/agents/git_ci_agent` | `git-ci-agent` |
| Reporting Agent | `/services/agents/reporting_agent` | `reporting-agent` |
| Slack Agent | `/services/agents/slack_agent` | `slack-agent` |
| Shared Library | `/shared` | `shared-lib` |

### Grouping Strategy

Minor and patch updates are grouped together to reduce PR noise:

```yaml
groups:
  python-minor:
    patterns:
      - "*"
    update-types:
      - "minor"
      - "patch"
```

This means:
- Major version updates get individual PRs (breaking changes)
- Minor/patch updates are grouped into single PRs

---

## GitHub Actions

Actions are updated weekly:

```yaml
- package-ecosystem: "github-actions"
  directory: "/"
  schedule:
    interval: "weekly"
  labels:
    - "dependencies"
    - "github-actions"
    - "ci"
```

### Why Update Actions?

| Reason | Example |
|--------|---------|
| Security fixes | `actions/checkout` vulnerabilities |
| New features | Better caching in `actions/cache` |
| Performance | Faster setup in `actions/setup-python` |
| Deprecations | Node 16 → Node 20 migration |

---

## Docker Base Images

Docker images are monitored for updates:

```yaml
- package-ecosystem: "docker"
  directory: "/infrastructure/docker"
  schedule:
    interval: "weekly"
  labels:
    - "dependencies"
    - "docker"
    - "infrastructure"
```

### What Gets Updated

| Base Image | Purpose |
|------------|---------|
| `python:3.11-slim` | Service runtime |
| `python:3.11-alpine` | Smaller images |

---

## Handling Dependabot PRs

### Reviewing PRs

1. **Check the changelog** in the PR description
2. **Review breaking changes** (especially major versions)
3. **Wait for CI checks** to pass
4. **Test locally** for critical packages

### Merging Strategy

| Update Type | Strategy |
|-------------|----------|
| Patch (x.x.1 → x.x.2) | Merge if CI passes |
| Minor (x.1.x → x.2.x) | Review changelog, merge if compatible |
| Major (1.x.x → 2.x.x) | Full review, test locally, update code if needed |

### Auto-Merge (Optional)

You can configure auto-merge for safe updates:

```yaml
# In workflow file
- name: Auto-merge Dependabot PRs
  if: github.actor == 'dependabot[bot]'
  run: gh pr merge --auto --squash "$PR_URL"
```

---

## Security Updates

Dependabot security updates are separate from version updates:

### Enabling

1. Go to **Settings → Security → Code security and analysis**
2. Enable **Dependabot alerts**
3. Enable **Dependabot security updates**

### Behavior

- Creates PRs immediately when vulnerabilities are detected
- Higher priority than regular updates
- Includes CVE information

### Example Security PR

```markdown
## Dependabot Security Update

Bumps [jinja2](https://github.com/pallets/jinja) from 2.11.3 to 3.0.1.

### Security Vulnerability
- **CVE-2024-1234**: Remote code execution via template injection
- **Severity**: High
- **CVSS Score**: 8.5

### Release Notes
[Link to changelog]
```

---

## Managing PR Volume

### If Too Many PRs

1. **Reduce open PR limit:**
```yaml
open-pull-requests-limit: 3  # Default is 5
```

2. **Use grouping:**
```yaml
groups:
  all-minor-patch:
    patterns: ["*"]
    update-types: ["minor", "patch"]
```

3. **Ignore specific packages:**
```yaml
ignore:
  - dependency-name: "some-package"
    versions: [">=2.0.0"]  # Ignore v2+
```

### If PRs Are Stale

Review and merge regularly, or configure auto-merge.

---

## Ignoring Updates

### Ignore Specific Versions

```yaml
ignore:
  - dependency-name: "django"
    versions: [">=4.0.0"]  # Stay on 3.x
```

### Ignore All Updates for a Package

```yaml
ignore:
  - dependency-name: "legacy-package"
```

### Ignore Update Types

```yaml
ignore:
  - dependency-name: "stable-package"
    update-types: ["version-update:semver-major"]
```

---

## Troubleshooting

### PRs Not Being Created

1. **Check configuration syntax:**
```bash
cat .github/dependabot.yml | python -c "import yaml,sys; yaml.safe_load(sys.stdin)"
```

2. **Verify directory exists:**
```bash
ls -la services/orchestrator/requirements.txt
```

3. **Check Dependabot logs:**
   - Settings → Security → Dependabot
   - Click on the ecosystem
   - View "Last checked" and any errors

### PRs Failing CI

Common causes:
- Incompatible package versions
- Breaking changes in dependencies
- Missing peer dependencies

Solution:
- Update multiple packages together
- Pin compatible versions
- Add necessary code changes

---

## Best Practices

### 1. Review Weekly

Set a recurring task to review Dependabot PRs each week.

### 2. Merge Security Updates Quickly

Security PRs should be merged within 24-48 hours.

### 3. Keep Dependencies Fresh

Don't let PRs pile up. Old PRs become harder to merge.

### 4. Test Locally for Major Updates

```bash
# Update locally first
pip install package-name==new.version

# Run tests
./scripts/dev.sh test

# If passing, merge the PR
```

### 5. Use Branch Protection

Require CI to pass before merging Dependabot PRs.

---

## Related Documentation

- [CI Workflow](./ci-workflow.md)
- [Troubleshooting](./troubleshooting.md)
- [GitHub Setup](../GITHUB_SETUP.md)

