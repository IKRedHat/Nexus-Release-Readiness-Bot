# User Guide

Welcome to the Nexus Release Automation System! This guide will help you understand how to use Nexus to streamline your release readiness assessments.

## Overview

Nexus is your AI-powered release automation assistant. It connects to your existing tools (Jira, GitHub, Jenkins, Confluence) and provides intelligent insights about your release readiness through natural language interactions.

## Getting Started

### Slack Setup

1. **Install the Nexus Bot** to your Slack workspace
2. **Invite the bot** to your desired channels: `/invite @nexus`
3. **Start using commands** - see below for available options

---

## Slack Commands

### `/nexus` - General Queries

The primary command for interacting with Nexus. Ask anything in natural language!

```
/nexus What is the status of PROJ-123?
/nexus Is the v2.0 release ready to go?
/nexus Show me all blocked tickets in the current sprint
/nexus What are the security vulnerabilities in our codebase?
```

**Examples:**

| Query | What Nexus Does |
|-------|-----------------|
| `/nexus status v2.0` | Checks overall release readiness for version 2.0 |
| `/nexus ticket PROJ-456` | Fetches details of a specific Jira ticket |
| `/nexus blockers` | Lists all blocking issues for the current release |
| `/nexus security check` | Runs security scan analysis |

### `/nexus help`

Display available commands and usage examples.

```
/nexus help
```

### `/jira-update` - Update Jira Tickets

Opens a modal dialog to update Jira ticket status.

![Jira Update Modal](assets/jira-modal.png)

**Fields:**
- **Ticket Key**: Enter the Jira ticket key (e.g., PROJ-123)
- **New Status**: Select from available transitions
- **Comment**: Optional comment to add to the ticket

### `/nexus release` - Release Readiness Check

Opens a modal to configure and run a comprehensive release readiness check.

**Parameters:**
- **Release Version**: The version being assessed (e.g., v2.0.0)
- **Epic/Project Key**: The Jira epic or project to analyze
- **Repository**: GitHub repository name
- **Environment**: Target environment (dev, staging, prod)

### `/nexus report` - Generate Reports

Generate and optionally publish release readiness reports.

**Report Types:**
- **Release Readiness**: Comprehensive Go/No-Go assessment
- **Sprint Summary**: Current sprint progress and metrics
- **Security Scan**: Vulnerability assessment report

---

## Understanding Reports

### Release Readiness Report

The release readiness report provides a comprehensive assessment:

#### 1. Decision Banner

<div style="background: #28a745; color: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
  <strong style="font-size: 1.5em;">✓ GO</strong>
  <p>All critical criteria met. Release is approved.</p>
</div>

Possible decisions:
- 🟢 **GO**: All required criteria passed
- 🔴 **NO-GO**: Critical blockers present
- 🟡 **CONDITIONAL**: Approved with conditions
- ⚪ **PENDING**: Assessment in progress

#### 2. Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Ticket Completion** | Percentage of stories done | ≥ 90% |
| **Test Coverage** | Code coverage percentage | ≥ 80% |
| **Security Risk Score** | 0-100 risk assessment | ≤ 30 |
| **Build Success Rate** | CI pipeline reliability | ≥ 95% |

#### 3. Checklist Items

Each release criterion is evaluated:

- ✅ All critical tickets completed
- ✅ Test coverage ≥ 80%
- ✅ No critical vulnerabilities
- ✅ CI pipeline green
- ⚠️ Documentation updated (optional)

#### 4. Blockers & Risks

**Blockers** - Issues that must be resolved:
- PROJ-105: API timeout issue (Critical)

**Risks** - Items requiring attention:
- 2 high-severity vulnerabilities require patching within 7 days

---

## Natural Language Examples

Nexus understands natural language queries. Here are some examples:

### Status Checks

```
"What's the status of our release?"
"Are we ready to deploy to production?"
"How's Sprint 42 looking?"
"Any blockers I should know about?"
```

### Jira Queries

```
"Show me all in-progress tickets for PROJ"
"What tickets are assigned to John?"
"List all bugs in the current sprint"
"What's the story points completion rate?"
```

### CI/CD Queries

```
"Is the main branch healthy?"
"What was the last build status?"
"Any failing tests?"
"Show me open pull requests"
```

### Security

```
"Run a security check on our repo"
"Any critical vulnerabilities?"
"What's our security risk score?"
```

---

## Tips & Best Practices

### 1. Be Specific

While Nexus understands natural language, specific queries yield better results:

❌ "Status?"  
✅ "What is the release readiness status for v2.0?"

### 2. Use Ticket Keys

When asking about specific tickets, include the full key:

✅ "What's the status of PROJ-123?"

### 3. Include Context

For release checks, include the version and project:

✅ "Is version 2.0 of the backend service ready for release?"

### 4. Review the Trace

When Nexus provides an answer, it also shows its reasoning steps. Review these to understand how conclusions were reached.

---

## Troubleshooting

### "Command not found"

Make sure the Nexus bot is installed in your workspace and invited to the channel.

### Slow Response

Complex queries involving multiple agents may take 10-30 seconds. Nexus will show a "thinking" indicator.

### Missing Data

If Nexus can't find data:
1. Verify the ticket/project key is correct
2. Check that Nexus has access to the required systems
3. Ensure the integrations are configured correctly

### Error Messages

If you receive an error:
1. Try rephrasing your query
2. Check the Nexus status page for system issues
3. Contact your administrator

---

## Getting Help

- **In Slack**: `/nexus help`
- **Documentation**: You're reading it!
- **Issues**: [GitHub Issues](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues)
