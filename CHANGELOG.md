# Changelog

All notable changes to the Nexus Release Automation System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

---

## [2.5.0] - 2025-12-04

### Added

#### 🐳 Enterprise Docker Architecture
- **Multi-stage Dockerfiles** - Optimized builds with 3-stage pattern (builder → deps → runtime)
- **UV Package Manager** - 10x faster dependency installation using Rust-based UV
- **Dockerfile.base** - Shared base image with non-root user and Python health checks
- **Dockerfile.agent** - Unified agent template replacing per-agent Dockerfiles
- **.dockerignore** - Build context optimization (~500MB → ~50MB)
- **OCI-Compliant Labels** - Standard metadata for all images
- **Python-Native Health Checks** - No curl dependency, smaller images
- **Non-Root Containers** - All services run as UID 1000 for security
- **Resource Limits** - Memory limits in docker-compose.yml
- **Named Containers** - Clear container naming (nexus-orchestrator, etc.)
- **Custom Network** - Isolated nexus-network for service communication

#### ⎈ Enterprise Helm Charts (v2.4.0)
- **Complete Chart Re-architecture** - Production-grade Kubernetes deployment
- **30+ Helper Functions** - DRY templates in `_helpers.tpl`
- **Reusable Agent Template** - `_agent.tpl` for consistent agent deployments
- **Pod Disruption Budgets** - Safe rolling updates with PDBs
- **Network Policies** - Zero-trust security with explicit allow rules
- **ServiceMonitors** - Prometheus Operator integration for all 10 services
- **External Secrets Support** - AWS Secrets Manager, HashiCorp Vault
- **Pod Anti-Affinity** - High availability with cross-node/zone distribution
- **Topology Spread Constraints** - Even distribution across failure domains
- **Init Containers** - Dependency health checks before startup
- **Lifecycle Hooks** - 10s graceful shutdown with preStop hooks
- **Security Contexts** - Non-root, read-only filesystem, seccomp profiles
- **Environment-Specific Values** - values-dev.yaml, values-prod.yaml
- **Comprehensive README** - Full deployment guide with architecture diagrams

#### 📖 Documentation
- **Docker for Beginners Guide** (`docs/docker-for-beginners.md`) - 700-line tutorial
  - Visual diagrams and real-world analogies
  - Multi-stage build explanation
  - Docker Compose walkthrough
  - Commands cheat sheet
  - Troubleshooting guide
- **Helm Chart README** (`infrastructure/k8s/nexus-stack/README.md`) - Production guide
  - Architecture overview with diagrams
  - Quick start commands
  - Security and observability configuration
  - Environment-specific deployment

### Changed
- Replaced `Dockerfile.generic-agent` with unified `Dockerfile.agent`
- Replaced `Dockerfile.rca-agent` with build args in `Dockerfile.agent`
- Updated docker-compose.yml with new Dockerfile references
- **Fixed Hygiene Agent Port**: 8005 → 8085 in all Helm templates

### Removed
- `Dockerfile.generic-agent` - Replaced by `Dockerfile.agent`
- `Dockerfile.rca-agent` - Consolidated into `Dockerfile.agent`

### Security
- All containers run as non-root user (UID 1000)
- Read-only root filesystem
- Dropped all Linux capabilities
- Seccomp profiles enabled (RuntimeDefault)
- Network policies enforce zero-trust

---

## [2.4.0] - 2025-12-04

### Added

#### 🚀 Frontend Deployment with Vercel
- **Vercel Configuration** (`vercel.json`) - Optimized settings for Vite/React SPA
- **Python Deployment Script** (`scripts/deploy_frontend.py`) - 700+ line comprehensive automation
  - Multi-environment support (preview, staging, production)
  - Prerequisite validation (Node.js, npm, Vercel CLI, Git)
  - Automated build with verification
  - Environment variable management
  - Deployment health checks with retries
  - Rollback support
  - Detailed logging with colored output
  - Deployment reports saved to `reports/`
- **GitHub Actions Workflow** (`.github/workflows/deploy-frontend.yml`)
  - Automatic preview deployments on PRs
  - Production deployment on main branch push
  - Manual deployment trigger with environment selection
  - Build artifact caching
  - Health check verification
- **Frontend Deployment Guide** (`docs/frontend-deployment-guide.md`)
  - Step-by-step manual deployment instructions
  - Architecture diagrams and visual references
  - Environment variable configuration guide
  - Post-deployment verification checklist
  - Troubleshooting section
  - Security best practices

#### 🧪 Comprehensive Test Suite Enhancements
- **1,449 total tests** (from 324 - 347% improvement!)
- 100% coverage on all 6 critical components:
  - Orchestrator (72 tests)
  - Jira Agent (126 tests: 100 unit + 26 e2e)
  - Git/CI Agent (118 tests: 94 unit + 24 e2e)
  - Slack Agent (156 tests: 106 unit + 50 e2e)
  - Admin Dashboard (110 tests)
  - Shared Library (94 tests)
- New test files:
  - `tests/unit/test_jira_agent.py` - JiraClient, parsing, operations
  - `tests/unit/test_git_ci_agent.py` - GitHub, Jenkins, Security clients
  - `tests/unit/test_slack_agent.py` - SlackClient, BlockKitBuilder, modals
  - `tests/unit/test_shared_lib.py` - Schemas, LLM, Config, utilities
  - `tests/unit/test_error_handling.py` - Error scenarios, edge cases
  - `tests/e2e/test_slack_agent.py` - Commands, events, interactions
  - `tests/integration/test_full_workflows.py` - Complete workflow tests
  - `tests/smoke/test_comprehensive_smoke.py` - Full system verification
  - `tests/performance/test_load.py` - Load testing, latency distribution
- Added code coverage reporting to CI/CD with Codecov integration

### Changed
- Updated `vite.config.ts` with production optimizations
  - Path aliases (@components, @pages, @assets)
  - Code splitting (react-vendor, chart-vendor, utils-vendor)
  - Terser minification for production
- Updated `package.json` with Vercel scripts
- Added `terser` as dev dependency for minification
- Updated mkdocs.yml with new Deployment section

### Fixed
- Fixed E2E tests to use correct `AgentTaskRequest` schema (action/payload)
- Fixed smoke tests to use correct health endpoints
- Fixed unit test imports and assertions

---

## [2.3.1] - 2025-12-01

### Changed
- Refactored all agents to use ConfigManager for dynamic configuration
- All agents now support live mode switching without restart
- Version bumped to 2.3.1 across all services

### Added
- GitHub labels configuration file (`.github/labels.yml`)
- Admin Dashboard configuration mockup visual
- Enhanced Admin Dashboard tutorial with detailed configuration steps

---

## [2.3.0] - 2025-12-01

### Added

#### 🎛️ Admin Dashboard
- New web-based Admin Dashboard (`services/admin_dashboard/`)
- React + Vite frontend with Tailwind CSS and cyber/tech dark theme
- FastAPI backend for configuration management
- Real-time agent health monitoring with auto-refresh
- Mode switching (Mock/Live) with instant propagation
- Secure credential management with masked sensitive values
- Configuration templates for all integrations (Jira, GitHub, Jenkins, LLM, Slack, Confluence)

#### 🔧 Dynamic Configuration System
- New `ConfigManager` class in `shared/nexus_lib/config.py`
- Redis-backed dynamic configuration with environment variable fallback
- Configuration caching with TTL for performance
- `is_mock_mode()` helper for conditional logic
- `with_mock_fallback()` decorator for easy mock/live switching
- `ConfigContext` context manager for configuration-aware operations
- `AgentRegistry` for centralized agent URL management

#### 📊 New Dashboard Components
- `ModeSwitch` - Animated toggle for Mock/Live modes
- `StatusCard` - Health status visualization with glow effects
- `ConfigForm` - Secure credential input with show/hide toggle
- Health Monitor page with real-time agent status
- Settings page with categorized configuration forms

#### 📚 Documentation
- `docs/admin-dashboard.md` - Comprehensive dashboard documentation
- `docs/admin-dashboard-tutorial.md` - Step-by-step no-code user guide
- Admin Dashboard mockup visual (`docs/assets/mockups/admin-dashboard.svg`)

### Changed
- Updated Docker Compose to include admin-dashboard service (port 8088)
- Updated Prometheus config to scrape admin-dashboard metrics
- Updated Kubernetes Helm values with adminDashboard configuration
- Updated mkdocs.yml navigation with Admin Dashboard section

### Metrics
- `nexus_admin_config_changes_total{key, source}` - Configuration changes
- `nexus_admin_health_checks_total{agent, status}` - Health check counts
- `nexus_admin_mode_switches_total{from_mode, to_mode}` - Mode switches
- `nexus_admin_active_mode` - Current mode gauge (0=mock, 1=live)

---

## [2.2.1] - 2025-12-01

### Added

#### 🔔 RCA Auto-Trigger & Slack Notifications
- Jenkins webhook endpoint (`/webhook/jenkins`) for automatic RCA on build failures
- Background analysis task for async processing
- SlackNotificationClient for sending RCA results to release channels
- PR owner lookup by email and @mention in Slack notifications
- Rich Block Kit notification formatting with:
  - Root cause summary with color-coded confidence
  - Suspected files with line numbers
  - Fix suggestions with code snippets
  - Action buttons (View Full Analysis, Re-run)

#### New Environment Variables
- `RCA_AUTO_ANALYZE` - Enable/disable auto-trigger (default: true)
- `SLACK_AGENT_URL` - Slack agent endpoint
- `SLACK_RELEASE_CHANNEL` - Default notification channel
- `SLACK_NOTIFY_ON_FAILURE` - Enable/disable notifications
- `SLACK_MOCK_MODE` - Mock mode for testing

#### New Prometheus Metrics
- `nexus_rca_webhooks_total{job_name, status}` - Webhook tracking
- `nexus_rca_notifications_total{channel, status}` - Notification tracking
- Updated `nexus_rca_requests_total` with `trigger` label (manual/webhook/orchestrator)

### Changed
- Updated `/analyze` endpoint to accept `notify`, `channel`, `pr_owner_email` params
- RCA analysis now returns `notification_sent`, `notification_channel`, `pr_owner_tagged` fields
- Docker Compose RCA agent now depends on slack-agent

---

## [2.2.0] - 2025-12-01

### Added

#### 🔍 Smart Root Cause Analysis (RCA)
- New RCA Agent service for analyzing failed CI/CD builds
- Intelligent log truncation utility preserving error blocks for LLM context windows
- Error pattern detection for Python, Java, JavaScript/Node, and generic CI failures
- Stack trace parsing for Python and Java exceptions
- Failing test identification for pytest and JUnit
- LLM-powered analysis using Google Gemini 1.5 Pro (1M token context)
- Git diff correlation to map errors to specific code changes
- Confidence scoring (high/medium/low/uncertain)
- Automated fix suggestions with code snippets
- Support for Jenkins build logs and GitHub diffs/PRs

#### New Pydantic Models
- `RcaRequest` - Analysis request with build and git context
- `RcaAnalysis` - Comprehensive analysis result with fix suggestions
- `RcaFileChange` - File changes that may have caused issues
- `RcaTestFailure` - Detailed test failure information
- `RcaConfidenceLevel` and `RcaErrorType` enums

#### Orchestrator Integration
- New `analyze_build_failure` tool registered in ReAct engine
- Natural language routing for RCA queries ("Why did build fail?", "Diagnose error")
- RCA query classification for metrics

### Changed
- Updated agent registry to include RCA agent URL
- Enhanced LLM mock responses for RCA-related queries

### Infrastructure
- New `Dockerfile.rca-agent` for RCA service (port 8006)
- Updated docker-compose.yml with RCA agent service
- Extended Prometheus scrape config for RCA metrics
- Updated Kubernetes Helm values with RCA agent configuration

### Documentation
- New `docs/rca.md` with comprehensive RCA documentation
- Updated mkdocs.yml navigation
- Updated README with RCA feature highlight

### Testing
- New `tests/unit/test_rca_logic.py` with comprehensive test coverage
- Tests for log truncation, error extraction, stack trace parsing
- Tests for RCA Pydantic models and LLM input formatting

---

## [2.1.0] - 2025-11-30

### Added

#### 📊 Advanced Analytics Dashboard
- Comprehensive KPI dashboard with DORA metrics
- Real-time metrics aggregation from all agents
- Time series analysis with flexible granularity
- Trend detection and historical comparisons
- Predictive analytics for release dates and quality scores
- Resource planning predictions
- Anomaly detection with severity levels
- Team performance tracking and comparison
- AI-powered insights and recommendations
- Industry benchmarking (DORA metrics)
- Prometheus metrics export for Grafana integration

#### 🔔 Webhook Integration Service
- Enterprise-grade webhook system for external integrations
- 25+ event types across releases, builds, deployments, security
- HMAC-SHA256 signature verification for security
- Automatic retry with exponential backoff (up to 5 attempts)
- Per-subscriber rate limiting
- Event filtering by project, team, and severity
- Delivery tracking and history
- Manual retry capability for failed deliveries
- Test endpoint for webhook validation
- Comprehensive statistics and monitoring

### Changed
- Updated architecture to include Analytics and Webhook services
- Enhanced Docker Compose with new services (ports 8086, 8087)
- Extended Prometheus configuration for new service metrics
- Updated Kubernetes Helm chart with analytics and webhook deployments
- Updated documentation navigation with Advanced Features section

### Infrastructure
- New Dockerfiles for Analytics and Webhook services
- Updated docker-compose.yml with all services
- Extended prometheus.yml scrape configurations
- New Kubernetes values for analytics and webhooks
- Ingress routes for /analytics and /webhooks

---

## [2.0.0] - 2025-11-30

### Added

#### 🤖 Google Gemini Integration
- Production-ready LLM client with Gemini 2.0 Flash support
- Async generation with streaming capabilities
- Native function calling support
- Token usage and cost tracking
- Automatic fallback to mock mode for development

#### 🏢 Multi-Tenant Support
- Enterprise-ready organization isolation
- Tenant plans: Free, Starter, Professional, Enterprise
- Per-tenant resource limits and configuration
- Feature flags per organization
- Tenant resolution via headers, subdomain, or API key

#### 💡 AI Recommendations Engine
- Pattern-based intelligent suggestions
- Release timing optimization
- Hygiene improvement recommendations
- Velocity and risk analysis
- Blocker resolution prioritization

#### 🏠 Slack App Home Dashboard
- Rich interactive dashboard when opening the app
- Quick action buttons for common tasks
- Real-time release status widget
- Hygiene score with fix button
- AI recommendations preview

#### 🔧 Jira Hygiene Agent Enhancements
- Interactive Slack modals for fixing violations
- Multi-ticket batch updates
- "Fix Now" button in notifications
- Snooze/remind later functionality

#### 📊 Visual Mockups
- Grafana dashboard mockup (SVG)
- Slack App Home mockup
- Hygiene fix modal mockup
- Confluence report mockup
- AI recommendations mockup

#### 🛠️ Development Scripts
- `scripts/setup.sh` - One-click development setup
- `scripts/dev.sh` - Development helper commands
- `scripts/verify.sh` - Health verification
- `scripts/uninstall.sh` - Clean uninstall

### Changed
- Upgraded documentation to reflect all new features
- Updated architecture diagrams
- Enhanced demo walkthrough script (4 minutes)

### Security
- Added SECURITY.md with vulnerability reporting process
- Improved input validation across all agents

---

## [1.1.0] - 2025-11-15

### Added

#### 🔧 Jira Hygiene Agent
- New specialized agent for Jira data quality
- Scheduled checks (weekdays at 9:00 AM)
- Field validation: Labels, Fix Version, Story Points, Team
- Hygiene scoring (0-100%)
- Slack DM notifications to assignees
- Prometheus metrics for hygiene tracking

#### 📊 Enhanced Observability
- Grafana dashboard for Nexus metrics
- LLM token usage and cost tracking
- Agent response time monitoring
- ReAct loop analytics

### Changed
- Updated shared library with hygiene-related schemas
- Enhanced Slack agent with `/send-dm` endpoint
- Improved Jira agent with bulk update capabilities

---

## [1.0.0] - 2025-10-01

### Added

#### 🧠 Core Platform
- Central Orchestrator with ReAct engine
- LangChain integration for agent coordination
- Vector memory for context retention (ChromaDB/pgvector)
- JWT-based service authentication

#### 🤖 Specialized Agents
- **Jira Agent**: Ticket operations, hierarchy fetching, search
- **Git/CI Agent**: GitHub integration, Jenkins builds, security scans
- **Reporting Agent**: HTML report generation, Confluence publishing
- **Slack Agent**: Command handling, Block Kit messages, modals

#### 🔗 Integrations
- Jira Cloud/Server via `atlassian-python-api`
- GitHub via `PyGithub`
- Jenkins via `python-jenkins`
- Confluence for report publishing
- Slack with Block Kit support

#### 🏗️ Infrastructure
- Docker multi-stage builds
- Docker Compose for local development
- Kubernetes Helm charts
- Prometheus metrics endpoints
- OpenTelemetry tracing

#### 📖 Documentation
- MkDocs-based documentation
- User guide
- Architecture documentation
- API reference
- Deployment runbook

### Security
- Request signing for Slack webhooks
- Environment-based secrets management
- Network policies for Kubernetes

---

## [0.1.0] - 2025-08-15

### Added
- Initial MVP release
- Basic project structure
- Proof of concept for multi-agent architecture

---

[Unreleased]: https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/releases/tag/v0.1.0

