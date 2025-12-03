# CI Workflow Deep Dive

This document provides detailed documentation for the Continuous Integration (CI) workflow.

## Overview

The CI workflow (`ci.yml`) is the main quality gate for all code changes. It runs on every push and pull request to ensure code quality, security, and functionality.

---

## Workflow File

**Location:** `.github/workflows/ci.yml`

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop`

---

## Jobs

### 1. Lint & Format (`lint`)

**Purpose:** Ensure code follows project style guidelines.

**Tools Used:**
| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Black** | Code formatting | `--check --diff` |
| **isort** | Import sorting | `--check-only --diff` |
| **flake8** | Linting | `--max-line-length=120` |
| **mypy** | Type checking | `--ignore-missing-imports` |

**What It Checks:**
- Code is formatted with Black
- Imports are sorted correctly
- No linting errors (PEP 8 compliance)
- Type hints are valid

**How to Fix Locally:**
```bash
# Format code
black shared/ services/ tests/

# Sort imports
isort shared/ services/ tests/

# Check linting
flake8 shared/ services/ --max-line-length=120

# Type check
mypy shared/ --ignore-missing-imports
```

---

### 2. Security Scan (`security`)

**Purpose:** Identify security vulnerabilities in code and dependencies.

**Tools Used:**
| Tool | Purpose |
|------|---------|
| **Bandit** | Python security linter |
| **pip-audit** | Dependency vulnerability scanner |

**What It Checks:**
- Common security issues in Python code
- Known vulnerabilities in dependencies
- Insecure coding patterns

**Bandit Rules Skipped:**
- `B101`: Assert statements (used in tests)
- `B104`: Binding to all interfaces (intentional for containers)

**Output:**
- `bandit-report.json` artifact with detailed findings

**How to Fix Locally:**
```bash
# Run Bandit
bandit -r shared/ services/ -ll

# Check dependencies
pip-audit

# Fix vulnerabilities
pip install --upgrade <vulnerable-package>
```

---

### 3. Unit Tests (`test-unit`)

**Purpose:** Verify individual components work correctly.

**Matrix:**
| Python Version | Status |
|----------------|--------|
| 3.10 | ✅ Tested |
| 3.11 | ✅ Tested (primary) |
| 3.12 | ✅ Tested |

**Coverage:**
- Minimum coverage is tracked but not enforced
- Coverage reports uploaded to Codecov
- XML and terminal reports generated

**Test Files (9 files, ~200 tests):**

| File | Coverage |
|------|----------|
| `test_schemas.py` | Pydantic models (JiraTicket, BuildStatus, etc.) |
| `test_react_engine.py` | ReAct engine, LLM client, vector memory |
| `test_hygiene_logic.py` | Hygiene validation, scoring, notifications |
| `test_rca_logic.py` | Log parsing, error extraction, stack traces |
| `test_config_manager.py` | Dynamic configuration, Redis fallback |
| `test_analytics.py` | DORA metrics, KPIs, trend analysis |
| `test_webhooks.py` | Webhook subscriptions, HMAC, delivery |
| `test_instrumentation.py` | Prometheus metrics, OpenTelemetry |
| `test_llm_client.py` | LLM factory, Gemini, OpenAI clients |

**What It Tests:**
- ✅ Pydantic model validation and serialization
- ✅ Business logic correctness
- ✅ Error handling and edge cases
- ✅ Configuration management
- ✅ Metrics and instrumentation
- ✅ LLM client abstraction

**How to Run Locally:**
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=shared --cov-report=html

# Run specific test file
pytest tests/unit/test_hygiene_logic.py -v

# Run by marker
pytest -m unit -v
```

**Artifacts:**
- `test-results-unit-{python-version}.xml` - JUnit test results
- Coverage uploaded to Codecov (Python 3.11 only)

---

### 4. E2E Tests (`test-e2e`)

**Purpose:** Verify end-to-end functionality across services.

**Dependencies:** Runs after `lint` and `test-unit` pass.

**Test Files (7 files, ~100 tests):**

| File | Service | Coverage |
|------|---------|----------|
| `test_release_flow.py` | Orchestrator | Query execution, memory, metrics |
| `test_slack_flow.py` | Slack Agent | Commands, interactions, modals |
| `test_reporting_flow.py` | Reporting Agent | Report generation, previews |
| `test_jira_agent.py` | Jira Agent | Ticket CRUD, hierarchy, sprints |
| `test_git_ci_agent.py` | Git/CI Agent | GitHub, Jenkins, security |
| `test_hygiene_agent.py` | Hygiene Agent | Checks, scheduler, notifications |
| `test_rca_agent.py` | RCA Agent | Analysis, webhooks, Slack alerts |

**What It Tests:**
- ✅ All API endpoints per service
- ✅ Request/response validation
- ✅ AgentTaskRequest handling
- ✅ Webhook processing
- ✅ Mock mode behavior

**How to Run Locally:**
```bash
# Start services first
./scripts/dev.sh start

# Run E2E tests
pytest tests/e2e/ -v

# Run by marker
pytest -m e2e -v

# Or use dev script
./scripts/dev.sh test-e2e
```

---

### 4.1 Integration Tests (`test-integration`)

**Purpose:** Verify inter-service communication workflows.

**Test Files (1 file, ~30 tests):**

| File | Coverage |
|------|----------|
| `test_agent_communication.py` | Orchestrator ↔ Agent calls, workflow chains |

**What It Tests:**
- ✅ Orchestrator → Agent tool execution
- ✅ Agent → Agent communication (Hygiene → Slack)
- ✅ Complete release readiness workflow
- ✅ Build failure → RCA → notification workflow
- ✅ Error handling and recovery

**How to Run Locally:**
```bash
pytest tests/integration/ -v

# Run by marker
pytest -m integration -v
```

---

### 4.2 Smoke Tests (`test-smoke`)

**Purpose:** Quick health verification after deployments.

**Test Files (1 file, ~40 tests):**

| File | Coverage |
|------|----------|
| `test_all_services.py` | Health checks for all 10 services |

**What It Tests:**
- ✅ Service health endpoints
- ✅ Basic functionality
- ✅ Metrics endpoints
- ✅ Inter-service connectivity
- ✅ Database connectivity

**How to Run Locally:**
```bash
# Ensure services are running
./scripts/dev.sh start

# Run smoke tests
pytest tests/smoke/ -v

# Run by marker
pytest -m smoke -v
```

---

### 5. Docker Build (`docker-build`)

**Purpose:** Verify Docker images build successfully.

**Services Built:**
| Service | Dockerfile |
|---------|------------|
| orchestrator | `Dockerfile.orchestrator` |
| jira-agent | `Dockerfile.generic-agent` |
| jira-hygiene-agent | `Dockerfile.generic-agent` |
| slack-agent | `Dockerfile.generic-agent` |

**Features:**
- Uses Docker Buildx for multi-platform support
- Caches layers with GitHub Actions cache
- Does NOT push images (CI only validates build)

**How to Build Locally:**
```bash
# Build specific service
docker build -f infrastructure/docker/Dockerfile.orchestrator -t nexus/orchestrator .

# Build with docker-compose
docker-compose build
```

---

### 6. Documentation (`docs`)

**Purpose:** Ensure documentation builds without errors.

**Tools:**
- MkDocs with Material theme
- Link checking (when enabled)

**What It Checks:**
- MkDocs configuration is valid
- All pages render correctly
- No broken internal links

**How to Build Locally:**
```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Build documentation
mkdocs build --strict

# Serve locally
mkdocs serve
```

---

### 7. CI Success (`ci-success`)

**Purpose:** Final check to confirm all required jobs passed.

**Behavior:**
- Runs after all other jobs complete
- Checks `lint` and `test-unit` are successful
- Required for branch protection status checks

---

## Job Dependencies

```mermaid
flowchart TD
    A[lint] --> D[test-e2e]
    B[security] --> E[ci-success]
    C[test-unit] --> D
    C --> E
    A --> E
    D --> E
    F[docker-build] --> E
    G[docs] --> E
    A --> F
```

---

## Caching

The workflow uses GitHub Actions cache for:

| Cache | Key Pattern | Purpose |
|-------|-------------|---------|
| pip dependencies | `{os}-pip-{hash}` | Speed up installs |
| Docker layers | `gha` type cache | Speed up builds |

**Cache Invalidation:**
- Changes to `requirements.txt` files
- Weekly rotation for security

---

## Timeouts

| Job | Timeout |
|-----|---------|
| lint | 10 minutes |
| security | 10 minutes |
| test-unit | 15 minutes |
| test-e2e | 20 minutes |
| docker-build | 30 minutes |

---

## Artifacts

| Artifact | Retention | Contents |
|----------|-----------|----------|
| `security-report` | 30 days | Bandit JSON report |
| `test-results-unit-{version}` | 30 days | JUnit XML results |
| `test-results-e2e` | 30 days | JUnit XML results |

---

## Common Patterns

### Skip CI

To skip CI for trivial changes (docs typos, etc.):

```bash
git commit -m "docs: fix typo [skip ci]"
```

### Rerun Failed Jobs

1. Go to Actions tab
2. Find the failed workflow run
3. Click "Re-run failed jobs"

### View Detailed Logs

1. Click on the workflow run
2. Click on the failed job
3. Expand the failed step
4. Click "View raw logs" for full output

---

## Status Badges

Add to README:

```markdown
![CI](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/actions/workflows/ci.yml/badge.svg)
```

---

---

### 8. Frontend Deployment (`deploy-frontend`)

**Purpose:** Deploy Admin Dashboard frontend to Vercel.

**Location:** `.github/workflows/deploy-frontend.yml`

**Triggers:**
- Push to `main` with changes in `services/admin_dashboard/frontend/**`
- Pull requests with frontend changes (preview deployment)
- Manual trigger via `workflow_dispatch`

**Jobs:**

| Job | Purpose |
|-----|---------|
| `build` | Build frontend with Vite |
| `deploy-preview` | Deploy to Vercel preview (PRs) |
| `deploy-production` | Deploy to Vercel production (main) |
| `deploy-manual` | Manual deployment with environment selection |

**Features:**
- Automatic preview deployments on PRs with PR comment
- Production deployment on main branch push
- Health check verification after deployment
- Build artifact caching

**How to Trigger Manually:**
1. Go to Actions → Deploy Frontend to Vercel
2. Click "Run workflow"
3. Select environment (preview/production)

---

## Next Steps

- [Release Workflow](./release-workflow.md)
- [Frontend Deployment Guide](../frontend-deployment-guide.md)
- [Troubleshooting](./troubleshooting.md)

