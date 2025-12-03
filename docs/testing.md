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

| Layer | Purpose | Speed | Scope |
|-------|---------|-------|-------|
| **Unit Tests** | Test individual functions/classes | ⚡ Fast | Isolated |
| **E2E Tests** | Test complete service endpoints | 🚀 Medium | Single service |
| **Integration Tests** | Test inter-service communication | 🔗 Medium | Multiple services |
| **Smoke Tests** | Quick health verification | 💨 Fast | All services |

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

| Test File | Coverage |
|-----------|----------|
| `test_schemas.py` | Pydantic models (JiraTicket, BuildStatus, etc.) |
| `test_react_engine.py` | Orchestrator ReAct engine, LLM client, memory |
| `test_hygiene_logic.py` | Jira hygiene validation, scoring, notifications |
| `test_rca_logic.py` | RCA log parsing, error extraction, stack traces |
| `test_config_manager.py` | Dynamic configuration, Redis fallback, mock mode |
| `test_analytics.py` | DORA metrics, KPIs, trend analysis, predictions |
| `test_webhooks.py` | Webhook subscriptions, HMAC security, delivery |
| `test_instrumentation.py` | Prometheus metrics, OpenTelemetry tracing |
| `test_llm_client.py` | LLM factory, Gemini, OpenAI clients |

**What's Tested:**
- ✅ Pydantic model validation and serialization
- ✅ Business logic correctness
- ✅ Error handling and edge cases
- ✅ Configuration management
- ✅ Metrics and instrumentation

---

### 🔄 E2E Tests (`tests/e2e/`)

End-to-end tests verify complete service functionality.

| Test File | Service | Coverage |
|-----------|---------|----------|
| `test_release_flow.py` | Orchestrator | Query execution, memory, metrics |
| `test_slack_flow.py` | Slack Agent | Commands, interactions, modals |
| `test_reporting_flow.py` | Reporting Agent | Report generation, previews |
| `test_jira_agent.py` | Jira Agent | Ticket CRUD, hierarchy, sprints |
| `test_git_ci_agent.py` | Git/CI Agent | GitHub, Jenkins, security |
| `test_hygiene_agent.py` | Hygiene Agent | Checks, scheduler, notifications |
| `test_rca_agent.py` | RCA Agent | Analysis, webhooks, Slack alerts |

**What's Tested:**
- ✅ All API endpoints
- ✅ Request/response validation
- ✅ AgentTaskRequest handling
- ✅ Webhook processing
- ✅ Mock mode behavior

---

### 🔗 Integration Tests (`tests/integration/`)

Integration tests verify inter-service communication.

| Test File | Coverage |
|-----------|----------|
| `test_agent_communication.py` | Orchestrator ↔ Agent calls, workflow chains |

**What's Tested:**
- ✅ Orchestrator → Agent tool execution
- ✅ Agent → Agent communication (e.g., Hygiene → Slack)
- ✅ Complete release readiness workflow
- ✅ Build failure → RCA → notification workflow
- ✅ Error handling and recovery
- ✅ Partial workflow failures

---

### 💨 Smoke Tests (`tests/smoke/`)

Smoke tests provide quick health verification after deployments.

| Test File | Coverage |
|-----------|----------|
| `test_all_services.py` | Health checks for all 10 services |

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
- ✅ Basic functionality
- ✅ Metrics endpoints
- ✅ Inter-service connectivity
- ✅ Database connectivity

---

## Running Tests

### Quick Commands

```bash
# Run all tests
pytest

# Run by category (using markers)
pytest -m unit           # Unit tests only
pytest -m e2e            # E2E tests only
pytest -m integration    # Integration tests only
pytest -m smoke          # Smoke tests only

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

| Component | Target | Current |
|-----------|--------|---------|
| `shared/nexus_lib` | 80% | 75%+ |
| `services/orchestrator` | 70% | 70%+ |
| `services/agents/*` | 70% | 65%+ |

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
| `pytest` | Run all tests |
| `pytest -m unit` | Unit tests only |
| `pytest -m e2e` | E2E tests only |
| `pytest -m smoke` | Smoke tests only |
| `pytest -m "not slow"` | Exclude slow tests |
| `pytest -v` | Verbose output |
| `pytest -x` | Stop on first failure |
| `pytest --cov=shared` | With coverage |
| `pytest -n auto` | Parallel execution |
| `pytest --pdb` | Debug on failure |

### Test Count Summary

| Category | Files | Tests |
|----------|-------|-------|
| Unit | 9 | ~180 |
| E2E | 7 | ~90 |
| Integration | 1 | ~20 |
| Smoke | 1 | ~34 |
| **Total** | **18** | **~324** |

> **Note:** As of v2.4.0, we have **324 passing tests** after comprehensive test suite fixes.

---

## Next Steps

- [CI Workflow Details](./ci-cd/ci-workflow.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Architecture Overview](./architecture.md)

