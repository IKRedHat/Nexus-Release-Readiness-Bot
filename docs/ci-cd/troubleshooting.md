# CI/CD Troubleshooting Guide

This comprehensive guide helps you diagnose and fix common issues with the Nexus CI/CD pipelines.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [CI Workflow Issues](#ci-workflow-issues)
- [Release Workflow Issues](#release-workflow-issues)
- [Dependabot Issues](#dependabot-issues)
- [Docker Build Issues](#docker-build-issues)
- [Test Failures](#test-failures)
- [Permission Issues](#permission-issues)
- [Performance Issues](#performance-issues)
- [Common Error Messages](#common-error-messages)

---

## Quick Diagnostics

### Workflow Status Check

```bash
# Check recent workflow runs
gh run list --limit 10

# View specific run details
gh run view <run-id>

# Download logs
gh run download <run-id>
```

### Common First Steps

1. ✅ Check if the issue is intermittent (rerun the job)
2. ✅ Check GitHub Status page for outages
3. ✅ Verify branch protection settings
4. ✅ Check secrets are configured correctly
5. ✅ Review recent changes to workflow files

---

## CI Workflow Issues

### 1. Lint Job Failing

#### Black Formatting Error

**Error:**
```
would reformat shared/nexus_lib/utils.py
Oh no! 💥 💔 💥
2 files would be reformatted
```

**Solution:**
```bash
# Fix formatting locally
black shared/ services/ tests/

# Commit and push
git add -A
git commit -m "style: format code with black"
git push
```

#### isort Import Error

**Error:**
```
ERROR: shared/nexus_lib/middleware.py Imports are incorrectly sorted
```

**Solution:**
```bash
# Fix imports locally
isort shared/ services/ tests/

# Or use dev script
./scripts/dev.sh format
```

#### flake8 Errors

**Error:**
```
shared/nexus_lib/utils.py:45:80: E501 line too long (125 > 120 characters)
```

**Solution:**
```bash
# Check errors
flake8 shared/ services/ --max-line-length=120

# Fix by:
# 1. Breaking long lines
# 2. Using variables for long expressions
# 3. Adding # noqa: E501 for unavoidable cases
```

#### mypy Type Errors

**Error:**
```
shared/nexus_lib/llm/gemini.py:42: error: Incompatible return type
```

**Solution:**
```python
# Add proper type hints
def get_client() -> Optional[GeminiClient]:  # Not just -> GeminiClient
    ...

# Or ignore if it's a false positive
result = some_function()  # type: ignore
```

---

### 2. Security Scan Failing

#### Bandit Findings

**Error:**
```
>> Issue: [B105:hardcoded_password_string] Possible hardcoded password
   Severity: Low   Confidence: Medium
   Location: services/agents/jira_agent/main.py:25
```

**Solutions:**

| Issue | Solution |
|-------|----------|
| Hardcoded password | Use environment variables |
| SQL injection | Use parameterized queries |
| Insecure random | Use `secrets` module |
| Shell injection | Use `subprocess` with list args |

**Example Fix:**
```python
# ❌ Bad
password = "secret123"

# ✅ Good
password = os.environ.get("JIRA_API_TOKEN")
```

**To Skip False Positives:**
```python
# nosec B105 - This is a test fixture, not a real password
test_password = "test123"  # nosec
```

#### pip-audit Vulnerabilities

**Error:**
```
Found 2 known vulnerabilities in 1 package
Name    Version  ID             Fix Versions
------  -------  -------------  ------------
jinja2  2.11.3   PYSEC-2021-66  2.11.3
```

**Solution:**
```bash
# Update the vulnerable package
pip install --upgrade jinja2

# Update requirements.txt
pip freeze | grep -i jinja2 > requirements.txt
```

---

### 3. Unit Tests Failing

#### Test Discovery Issues

**Error:**
```
collected 0 items
```

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Missing `__init__.py` | Add empty `__init__.py` to test directories |
| Wrong file naming | Rename to `test_*.py` or `*_test.py` |
| Import errors | Check PYTHONPATH includes project root |

#### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'nexus_lib'
```

**Solution:**
Add to `conftest.py`:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/orchestrator')))
```

#### Async Test Issues

**Error:**
```
RuntimeWarning: coroutine 'test_something' was never awaited
```

**Solution:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

#### Flaky Tests

**Symptoms:**
- Tests pass locally but fail in CI
- Tests fail intermittently

**Solutions:**

1. **Add timeouts:**
```python
@pytest.mark.timeout(10)
async def test_with_timeout():
    ...
```

2. **Mock external services:**
```python
from unittest.mock import patch, AsyncMock

@patch('nexus_lib.utils.AsyncHttpClient.get', new_callable=AsyncMock)
async def test_with_mock(mock_get):
    mock_get.return_value = {"status": "success"}
    ...
```

3. **Add retry logic:**
```python
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_flaky_external_call():
    ...
```

---

### 4. Docker Build Failing

#### Build Context Errors

**Error:**
```
COPY failed: file not found in build context
```

**Solution:**
- Check file paths are relative to repository root
- Verify `.dockerignore` isn't excluding needed files
- Ensure the file exists and is committed

#### Dependency Installation Errors

**Error:**
```
ERROR: Could not find a version that satisfies the requirement
```

**Solutions:**

1. **Pin versions:**
```
# requirements.txt
fastapi==0.104.1
pydantic>=2.0,<3.0
```

2. **Use compatible versions:**
```bash
pip install package1 package2  # Let pip resolve
pip freeze > requirements.txt
```

#### Out of Memory

**Error:**
```
The runner has received a shutdown signal.
```

**Solution:**
- Reduce parallel builds
- Use smaller base images
- Add `.dockerignore` to exclude unnecessary files

---

## Release Workflow Issues

### 1. Tag Validation Failing

**Error:**
```
❌ Invalid version format: release-2.0
Expected format: v1.2.3 or v1.2.3-beta.1
```

**Solution:**
```bash
# Use correct format
git tag v2.0.0  # Not "release-2.0"
git push origin v2.0.0
```

### 2. Docker Push Failing

**Error:**
```
denied: permission_denied: write_package
```

**Solutions:**

1. **Check workflow permissions:**
```yaml
permissions:
  packages: write
```

2. **Verify token has write access:**
   - Go to Settings → Actions → General
   - Under "Workflow permissions"
   - Select "Read and write permissions"

3. **For forks:** Create `GHCR_TOKEN` secret with `write:packages` scope

### 3. Release Creation Failing

**Error:**
```
Resource not accessible by integration
```

**Solution:**
```yaml
permissions:
  contents: write  # Required for creating releases
```

### 4. Changelog Generation Issues

**Error:**
```
fatal: No names found, cannot describe anything.
```

**Solution:**
Ensure tags are pushed:
```bash
git push origin --tags
```

---

## Dependabot Issues

### 1. Dependabot PRs Not Created

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| Invalid `dependabot.yml` | Validate YAML syntax |
| Wrong directory path | Check paths match actual structure |
| Package ecosystem wrong | Verify `pip` for Python |

**Validation:**
```bash
# Check syntax
cat .github/dependabot.yml | python -c "import yaml,sys; yaml.safe_load(sys.stdin)"
```

### 2. Too Many PRs

**Solution:**
Configure grouping in `dependabot.yml`:
```yaml
groups:
  python-minor:
    patterns:
      - "*"
    update-types:
      - "minor"
      - "patch"
```

### 3. Security Updates Not Working

**Check:**
1. Go to Settings → Security → Dependabot
2. Ensure "Dependabot security updates" is enabled

---

## Permission Issues

### 1. "Resource not accessible by integration"

**Cause:** Insufficient permissions in workflow.

**Solution:**
```yaml
permissions:
  contents: read
  packages: write
  pull-requests: write
  issues: write
```

### 2. "refusing to allow a GitHub App to create or update workflow"

**Cause:** Trying to modify workflow files.

**Solution:**
- Workflow changes must be made manually
- Cannot modify `.github/workflows/` via automated processes

### 3. Protected Branch Errors

**Error:**
```
refusing to allow an OAuth App to create or update workflow
```

**Solutions:**
1. Create PR instead of direct push
2. Use a PAT with `workflow` scope
3. Temporarily disable branch protection (not recommended)

---

## Performance Issues

### 1. Slow CI Runs

**Optimizations:**

| Issue | Solution |
|-------|----------|
| No caching | Add pip/Docker caching |
| Sequential jobs | Run independent jobs in parallel |
| Large Docker context | Add `.dockerignore` |
| Full git clone | Use `fetch-depth: 1` |

**Example - Shallow Clone:**
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 1  # Only latest commit
```

### 2. Cache Not Working

**Debugging:**
```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

**Check:**
- Key hash changes when files change
- `restore-keys` provides fallback

### 3. Timeout Errors

**Solution:**
Add explicit timeouts:
```yaml
jobs:
  test:
    timeout-minutes: 30
    steps:
      - name: Run tests
        timeout-minutes: 15
        run: pytest tests/
```

---

## Common Error Messages

### Reference Guide

| Error | Cause | Solution |
|-------|-------|----------|
| `ENOSPC: no space left on device` | Runner out of disk | Clean up, reduce artifacts |
| `Process completed with exit code 1` | Command failed | Check logs for details |
| `Context access might be invalid` | Undefined variable | Check variable names/context |
| `The process '/usr/bin/git' failed with exit code 128` | Git error | Check clone depth, permissions |
| `Container action is only supported on Linux` | Wrong runner | Use `ubuntu-latest` |
| `Error: Timeout after 360000ms` | Operation too slow | Increase timeout or optimize |

---

## Debug Mode

### Enable Debug Logging

1. Go to repository Settings
2. Navigate to Secrets → Actions
3. Add secret: `ACTIONS_STEP_DEBUG` = `true`
4. Rerun the workflow

### View Raw Logs

1. Go to the workflow run
2. Click on the job
3. Click "..." menu → "View raw logs"

### Local Debugging with `act`

```bash
# Install act (https://github.com/nektos/act)
brew install act

# Run workflow locally
act push -j lint

# With secrets
act push -s GITHUB_TOKEN="$(gh auth token)"
```

---

## Getting Help

If you can't resolve the issue:

1. **Search existing issues:** [GitHub Issues](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues)
2. **Check GitHub Status:** [githubstatus.com](https://www.githubstatus.com/)
3. **Create an issue** with:
   - Workflow run link
   - Error message
   - Steps to reproduce
   - What you've tried

---

## Related Documentation

- [CI Workflow Details](./ci-workflow.md)
- [Release Workflow Details](./release-workflow.md)
- [GitHub Setup Guide](../GITHUB_SETUP.md)
- [Contributing Guide](../../CONTRIBUTING.md)

