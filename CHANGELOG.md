# Changelog

All notable changes to the Nexus Release Automation System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflows
- Dependabot configuration for automated dependency updates
- Comprehensive contribution guidelines
- Issue and PR templates
- Code of Conduct
- Security policy

### Changed
- Updated README with better quick start instructions

### Removed
- Legacy MVP scaffold scripts

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

