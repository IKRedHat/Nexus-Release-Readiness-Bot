# Testing Guide

This comprehensive guide covers the Nexus testing strategy, test categories, and how to run tests effectively.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Writing Tests](#writing-tests)
6. [Fixtures & Utilities](#fixtures--utilities)
7. [CI/CD Integration](#cicd-integration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Nexus uses a multi-layered testing strategy to ensure reliability across all services:

| Layer | Purpose | Speed | Scope | Tests |
|-------|---------|-------|-------|-------|
| **Unit Tests** | Test individual functions/classes | ⚡ Fast | Isolated | 875 |
| **E2E Tests** | Test complete service endpoints | 🚀 Medium | Single service | 410 |
| **Integration Tests** | Test inter-service communication | 🔗 Medium | Multiple services | 60 |
| **Smoke Tests** | Quick health verification | 💨 Fast | All services | 72 |
| **Performance Tests** | Load and latency testing | ⏱️ Slow | System-wide | 32 |

### Test Framework

- **Framework:** pytest 7.0+
- **Async Support:** pytest-asyncio
- **HTTP Testing:** HTTPX, TestClient (FastAPI)
- **Mocking:** unittest.mock, AsyncMock
- **Coverage:** pytest-cov

---

## Test Categories

### 🧪 Unit Tests (`tests/unit/`)

Unit tests verify individual components in isolation.

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_jira_agent.py` | 100 | JiraClient init, parsing, mock data, operations, API endpoints |
| `test_slack_agent.py` | 106 | SlackClient, BlockKitBuilder, modals, hygiene fix, API endpoints |
| `test_git_ci_agent.py` | 94 | GitHubClient, JenkinsClient, SecurityScannerClient, endpoints |
| `test_shared_lib.py` | 94 | Schemas, LLM, ConfigManager, instrumentation, utilities |
| `test_error_handling.py` | 40 | Input validation, boundary conditions, error scenarios |
| `test_schemas.py` | ~50 | Pydantic models (JiraTicket, BuildStatus, etc.) |
| `test_react_engine.py` | ~30 | Orchestrator ReAct engine, LLM client, memory |
| `test_hygiene_logic.py` | ~40 | Jira hygiene validation, scoring, notifications |
| `test_rca_logic.py` | ~30 | RCA log parsing, error extraction, stack traces |
| `test_config_manager.py` | ~30 | Dynamic configuration, Redis fallback, mock mode |
| `test_analytics.py` | 42 | DORA metrics, KPIs, trend analysis, predictions |
| `test_webhooks.py` | 34 | Webhook subscriptions, HMAC security, delivery |
| `test_instrumentation.py` | ~25 | Prometheus metrics, OpenTelemetry tracing |
| `test_llm_client.py` | ~25 | LLM factory, Gemini, OpenAI clients |

**What's Tested:**
- ✅ Pydantic model validation and serialization
- ✅ Business logic correctness
- ✅ Error handling and edge cases
- ✅ Configuration management
- ✅ Metrics and instrumentation

---

### 🔄 E2E Tests (`tests/e2e/`)

End-to-end tests verify complete service functionality.

| Test File | Service | Tests | Coverage |
|-----------|---------|-------|----------|
| `test_admin_dashboard.py` | Admin Dashboard | 110 | Health, config, releases, metrics, integrations |
| `test_orchestrator.py` | Orchestrator | 72 | Queries, specialists, memory, concurrent requests |
| `test_slack_agent.py` | Slack Agent | 50 | Commands, events, interactions, notifications |
| `test_release_flow.py` | Orchestrator | ~25 | Query execution, memory, metrics |
| `test_slack_flow.py` | Slack Agent | ~20 | Commands, interactions, modals |
| `test_reporting_flow.py` | Reporting Agent | ~15 | Report generation, previews |
| `test_jira_agent.py` | Jira Agent | 26 | Ticket CRUD, hierarchy, sprints |
| `test_git_ci_agent.py` | Git/CI Agent | 24 | GitHub, Jenkins, security |
| `test_hygiene_agent.py` | Hygiene Agent | ~20 | Checks, scheduler, notifications |
| `test_rca_agent.py` | RCA Agent | 24 | Analysis, webhooks, Slack alerts |

**What's Tested:**
- ✅ All API endpoints
- ✅ Request/response validation
- ✅ AgentTaskRequest handling
- ✅ Webhook processing
- ✅ Mock mode behavior

---

### 🔗 Integration Tests (`tests/integration/`)

Integration tests verify inter-service communication.

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_agent_communication.py` | ~25 | Orchestrator ↔ Agent calls, workflow chains |
| `test_full_workflows.py` | 36 | Release lifecycle, RCA→Slack, Hygiene chains |

**What's Tested:**
- ✅ Orchestrator → Agent tool execution
- ✅ Agent → Agent communication (e.g., Hygiene → Slack)
- ✅ Complete release readiness workflow
- ✅ Build failure → RCA → notification workflow
- ✅ Error handling and recovery
- ✅ Partial workflow failures
- ✅ Configuration propagation across services
- ✅ Analytics data collection workflows
- ✅ Webhook event delivery
- ✅ Cross-service data consistency

---

### 💨 Smoke Tests (`tests/smoke/`)

Smoke tests provide quick health verification after deployments.

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_all_services.py` | ~25 | Health checks for all 10 services |
| `test_comprehensive_smoke.py` | 47 | Full system verification, response times |

**Services Tested:**

| Service | Port | Health Path |
|---------|------|-------------|
| Orchestrator | 8080 | `/health` |
| Jira Agent | 8081 | `/health` |
| Git/CI Agent | 8082 | `/health` |
| Reporting Agent | 8083 | `/health` |
| Slack Agent | 8084 | `/health` |
| Hygiene Agent | 8085 | `/health` |
| RCA Agent | 8006 | `/health` |
| Analytics Agent | 8086 | `/health` |
| Webhooks Agent | 8087 | `/health` |
| Admin Dashboard | 8088 | `/health-check` |

**What's Tested:**
- ✅ Service availability
- ✅ Basic functionality per service
- ✅ Metrics endpoints (Prometheus)
- ✅ API documentation endpoints
- ✅ Inter-service connectivity
- ✅ Observability stack (Prometheus, Grafana, Jaeger)
- ✅ Kubernetes liveness/readiness probes
- ✅ Response time validation

---

### ⚡ Performance Tests (`tests/performance/`)

Performance tests verify system behavior under load.

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_load.py` | 32 | Response times, throughput, concurrent requests |

**What's Tested:**
- ✅ Response time baselines (health < 100ms)
- ✅ Concurrent request handling (20+ simultaneous)
- ✅ Throughput measurements (requests/second)
- ✅ Latency distribution (P95, P99)
- ✅ Sustained load testing (30s @ 10 RPS)
- ✅ Memory usage patterns
- ✅ Connection pooling efficiency
- ✅ Rate limiting behavior

---

## Running Tests

### Quick Commands

```bash
# Run all tests
pytest

# Run by category (using markers)
pytest -m unit           # Unit tests only (875 tests)
pytest -m e2e            # E2E tests only (410 tests)
pytest -m integration    # Integration tests only (60 tests)
pytest -m smoke          # Smoke tests only (72 tests)
pytest -m performance    # Performance tests only (32 tests)

# Exclude slow tests
pytest -m "not slow"

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_schemas.py

# Run specific test class
pytest tests/unit/test_schemas.py::TestJiraSchemas

# Run specific test method
pytest tests/unit/test_schemas.py::TestJiraSchemas::test_jira_ticket_minimal
```

### Using Dev Script

```bash
# Run all tests
./scripts/dev.sh test

# Run unit tests only
./scripts/dev.sh test-unit

# Run E2E tests
./scripts/dev.sh test-e2e
```

### With Coverage

```bash
# Generate coverage report
pytest --cov=shared --cov=services --cov-report=html

# Open coverage report
open htmlcov/index.html

# Coverage with specific directories
pytest --cov=shared/nexus_lib --cov-report=term-missing
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto           # Auto-detect CPU cores
pytest -n 4              # Use 4 workers
```

---

## Test Coverage

### Coverage Targets

| Component | Target | Current | Status |
|-----------|--------|---------|--------|
| `shared/nexus_lib` | 80% | **100%** | ✅ |
| `services/orchestrator` | 80% | **100%** | ✅ |
| `services/jira_agent` | 80% | **100%** | ✅ |
| `services/git_ci_agent` | 80% | **100%** | ✅ |
| `services/slack_agent` | 80% | **100%** | ✅ |
| `services/admin_dashboard` | 80% | **100%** | ✅ |
| `services/analytics` | 70% | 84% | ✅ |
| `services/webhooks` | 70% | 68% | ⚠️ |
| `services/rca_agent` | 70% | 72% | ✅ |

> **Note:** All critical components (marked with ⭐) are at 100% coverage as of v2.4.0.

### Generating Reports

```bash
# Terminal report
pytest --cov=shared --cov-report=term-missing

# HTML report
pytest --cov=shared --cov-report=html

# XML report (for CI)
pytest --cov=shared --cov-report=xml:coverage.xml

# Combined report
pytest --cov=shared --cov=services \
       --cov-report=term-missing \
       --cov-report=html:htmlcov \
       --cov-report=xml:coverage.xml
```

---

## Writing Tests

### Test Structure

```python
"""
Unit Tests for Feature X
========================

Brief description of what's being tested.
"""

import pytest
from unittest.mock import AsyncMock, patch

class TestFeatureX:
    """Tests for Feature X functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        return {"key": "value"}
    
    def test_basic_functionality(self, sample_data):
        """Test basic use case."""
        result = function_under_test(sample_data)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        result = await async_function()
        assert result["status"] == "success"
    
    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            function_with_validation(invalid_input)
```

### Naming Conventions

| Pattern | Example | Use For |
|---------|---------|---------|
| `test_<action>_<condition>` | `test_create_ticket_success` | Positive cases |
| `test_<action>_<failure>` | `test_create_ticket_invalid` | Negative cases |
| `test_<action>_<edge_case>` | `test_create_ticket_empty` | Edge cases |

### Using Markers

```python
import pytest

@pytest.mark.unit
def test_unit_example():
    """Unit test example."""
    pass

@pytest.mark.e2e
def test_e2e_example():
    """E2E test example."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Slow test - skip with -m 'not slow'."""
    pass

@pytest.mark.asyncio
async def test_async_example():
    """Async test example."""
    pass
```

---

## Fixtures & Utilities

### Available Fixtures

The following fixtures are available in `tests/conftest.py`:

| Fixture | Type | Description |
|---------|------|-------------|
| `event_loop` | Session | Async event loop |
| `mock_vector_memory` | Function | Mock VectorMemory |
| `mock_http_client` | Function | Mock AsyncHttpClient |
| `sample_jira_ticket` | Function | Sample Jira ticket data |
| `sample_build_status` | Function | Sample build status data |
| `sample_security_scan` | Function | Sample security scan data |
| `sample_release_stats` | Function | Sample release statistics |
| `sample_agent_request` | Function | Sample AgentTaskRequest |
| `mock_llm_response` | Function | Mock LLM response |
| `mock_final_answer_response` | Function | Mock LLM final answer |
| `sample_hygiene_result` | Function | Sample hygiene check result |
| `sample_rca_result` | Function | Sample RCA analysis result |
| `sample_analytics_kpis` | Function | Sample analytics KPIs |
| `sample_webhook_subscription` | Function | Sample webhook subscription |
| `sample_config` | Function | Sample system configuration |
| `mock_redis` | Function | Mock Redis client |
| `sample_jenkins_log` | Function | Sample Jenkins failure log |
| `sample_git_diff` | Function | Sample Git diff |

### Helper Functions

```python
from tests.conftest import (
    create_mock_agent_response,
    create_mock_health_response
)

# Create standardized agent response
response = create_mock_agent_response(
    status="success",
    data={"key": "value"}
)

# Create health check response
health = create_mock_health_response(
    service_name="jira-agent",
    healthy=True
)
```

---

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically in the CI pipeline:

```yaml
# .github/workflows/ci.yml
jobs:
  test-unit:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Run Unit Tests
        run: |
          pytest tests/unit/ -v --cov=shared --cov-report=xml
      - name: Upload Coverage
        uses: codecov/codecov-action@v3

  test-e2e:
    needs: [lint, test-unit]
    steps:
      - name: Run E2E Tests
        run: pytest tests/e2e/ -v
```

### Test Artifacts

| Artifact | Purpose | Retention |
|----------|---------|-----------|
| `test-results-unit-*.xml` | JUnit results | 30 days |
| `test-results-e2e.xml` | E2E results | 30 days |
| `coverage.xml` | Coverage data | 30 days |

---

## Troubleshooting

### Common Issues

#### Tests Not Found

```bash
# Ensure correct directory
pytest tests/unit/ -v

# Check test discovery
pytest --collect-only

# Verify file naming (must start with test_)
ls tests/unit/
```

#### Import Errors

```bash
# Install shared library
pip install -e shared/

# Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/shared:$(pwd)/services/orchestrator"
```

#### Async Test Failures

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check asyncio mode in pytest.ini
# asyncio_mode = auto
```

#### Mock Mode Issues

```bash
# Set environment variables
export JIRA_MOCK_MODE=true
export GITHUB_MOCK_MODE=true
export LLM_PROVIDER=mock

# Or use .env file
source .env
pytest
```

### Debugging Tests

```bash
# Run with print output
pytest -s

# Run with verbose debug
pytest -vv

# Stop on first failure
pytest -x

# Enter debugger on failure
pytest --pdb

# Show local variables
pytest -l
```

### Performance Issues

```bash
# Profile slow tests
pytest --durations=10

# Skip slow tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

---

## Quick Reference

### Commands Cheat Sheet

| Command | Description |
|---------|-------------|
| `pytest` | Run all 1,449 tests |
| `pytest -m unit` | Unit tests only (875) |
| `pytest -m e2e` | E2E tests only (410) |
| `pytest -m integration` | Integration tests (60) |
| `pytest -m smoke` | Smoke tests only (72) |
| `pytest -m performance` | Performance tests (32) |
| `pytest -m "not slow"` | Exclude slow tests |
| `pytest -v` | Verbose output |
| `pytest -x` | Stop on first failure |
| `pytest --cov=shared` | With coverage |
| `pytest -n auto` | Parallel execution |
| `pytest --pdb` | Debug on failure |

### Test Count Summary

| Category | Files | Tests |
|----------|-------|-------|
| Unit | 14 | 875 |
| E2E | 10 | 410 |
| Integration | 2 | 60 |
| Smoke | 2 | 72 |
| Performance | 1 | 32 |
| **Total** | **29** | **1,449** |

> **Note:** As of v2.4.0, we have **1,449 passing tests** with 100% coverage on all critical components.

---

## Next Steps

- [CI Workflow Details](./ci-cd/ci-workflow.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Architecture Overview](./architecture.md)

