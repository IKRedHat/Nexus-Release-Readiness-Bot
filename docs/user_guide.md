# User Guide

Welcome to the Nexus Release Automation System! This guide will help you understand how to use Nexus to streamline your release readiness assessments and maintain high-quality Jira data.

## Overview

Nexus is your AI-powered release automation assistant. It connects to your existing tools (Jira, GitHub, Jenkins, Confluence) and provides intelligent insights about your release readiness through natural language interactions.

**Key Capabilities:**
- 🧠 **Intelligent Queries** - Ask questions in natural language
- 📊 **Release Assessments** - Automated Go/No-Go decisions
- 🔧 **Jira Hygiene** - Proactive data quality management
- 📝 **Rich Reports** - Beautiful Confluence reports

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

## 🔧 Jira Hygiene Notifications

Nexus proactively monitors your Jira data quality through the **Jira Hygiene Agent**. This ensures your tickets are properly filled out before release assessments.

### How It Works

1. **Scheduled Checks**: Every weekday at 9:00 AM, Nexus scans active sprint tickets
2. **Validation**: Checks for missing required fields
3. **Notifications**: Sends DM to assignees with violation details
4. **Interactive Fixes**: Fix issues directly from Slack without leaving the app

### What Gets Checked

| Field | Why It Matters |
|-------|----------------|
| 🏷️ **Labels** | Categorization and filtering |
| 📦 **Fix Version** | Release planning and tracking |
| 🔍 **Affected Version** | Impact and regression analysis |
| 📊 **Story Points** | Capacity planning and velocity |
| 👥 **Team/Contributors** | Ownership and accountability |

### Receiving a Hygiene Notification

When tickets assigned to you have missing fields, you'll receive a DM like this:

```
📋 Jira Ticket Hygiene Report

Hi Alice! 👋

Our automated hygiene check found 3 tickets assigned to 
you that are missing required fields.

Project Hygiene Score: 70.0%

────────────────────────────────────

Tickets needing attention:
• PROJ-123: Missing Labels, Story Points
• PROJ-124: Missing Fix Version
• PROJ-125: Missing Team/Contributors

────────────────────────────────────

[🔧 Fix Tickets Now]  [📊 View Full Report]  [⏰ Remind Me Later]
```

### Fixing Violations from Slack

Click **"🔧 Fix Tickets Now"** to open an interactive modal:

1. **Modal Opens**: Shows all tickets with their missing fields
2. **Fill In Values**: Enter the missing information for each ticket
   - Labels: `backend, api, security` (comma-separated)
   - Fix Version: `v2.0.0`
   - Story Points: Select from dropdown (1, 2, 3, 5, 8, 13, 21)
   - Team: `Platform Team`
3. **Submit**: Click "Update Tickets"
4. **Confirmation**: Receive a confirmation DM when updates complete

**Example Modal:**

```
┌─────────────────────────────────────────────┐
│  🔧 Fix Jira Ticket Hygiene                 │
├─────────────────────────────────────────────┤
│                                             │
│  PROJ-123: Implement user authentication    │
│  Missing: Labels, Story Points              │
│                                             │
│  🏷️ Labels                                  │
│  ┌─────────────────────────────────────┐   │
│  │ e.g., backend, api, security        │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  📊 Story Points                            │
│  ┌─────────────────────────────────────┐   │
│  │ Select story points          ▼      │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ─────────────────────────────────────────  │
│                                             │
│  PROJ-124: Fix login timeout issue          │
│  Missing: Fix Version                       │
│                                             │
│  📦 Fix Version                             │
│  ┌─────────────────────────────────────┐   │
│  │ e.g., v2.0.0, 2024-Q1               │   │
│  └─────────────────────────────────────┘   │
│                                             │
├─────────────────────────────────────────────┤
│           [Cancel]  [Update Tickets]        │
└─────────────────────────────────────────────┘
```

### Snoozing Reminders

Click **"⏰ Remind Me Later"** to snooze the notification. You'll be reminded again in 24 hours.

### Hygiene Score

The **Project Hygiene Score** is calculated as:

```
Hygiene Score = (Compliant Tickets / Total Tickets) × 100%
```

- **90-100%**: Excellent ✅
- **70-89%**: Good 🟡
- **50-69%**: Needs Improvement ⚠️
- **Below 50%**: Critical 🔴

---

## Understanding Reports

### Release Readiness Report

The release readiness report provides a comprehensive assessment:

#### 1. Decision Banner

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
| **Hygiene Score** | Data quality percentage | ≥ 80% |

#### 3. Checklist Items

Each release criterion is evaluated:

- ✅ All critical tickets completed
- ✅ Test coverage ≥ 80%
- ✅ No critical vulnerabilities
- ✅ CI pipeline green
- ✅ Jira hygiene score ≥ 80%
- ⚠️ Documentation updated (optional)

#### 4. Blockers & Risks

**Blockers** - Issues that must be resolved:
- PROJ-105: API timeout issue (Critical)

**Risks** - Items requiring attention:
- 2 high-severity vulnerabilities require patching within 7 days
- 5 tickets missing Story Points (affects velocity calculation)

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

### Hygiene

```
"What's our project hygiene score?"
"Which tickets are missing labels?"
"Run a hygiene check on PROJ"
```

---

## API Access

For programmatic access, Nexus exposes REST APIs:

### Orchestrator API

```bash
# Run a query
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Is v2.0 ready for release?"}'

# Check health
curl http://localhost:8080/health
```

### Hygiene Agent API

```bash
# Manual hygiene check
curl -X POST http://localhost:8005/run-check \
  -H "Content-Type: application/json" \
  -d '{"project_key": "PROJ", "notify": true}'

# Get violations for a project
curl http://localhost:8005/violations/PROJ

# Check scheduler status
curl http://localhost:8005/status
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

### 5. Maintain Hygiene

Regularly address hygiene notifications to:
- Improve release assessment accuracy
- Keep velocity metrics reliable
- Ensure proper release tracking

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

### No Hygiene Notifications

If you're not receiving hygiene notifications:
1. Check that your Slack email matches your Jira email
2. Verify the Hygiene Agent is running: `curl http://localhost:8005/health`
3. Check your Slack DM settings

### Modal Not Opening

If the "Fix Tickets Now" button doesn't open a modal:
1. Try again - there may be a temporary network issue
2. Check that you're using the Slack desktop or web app (not mobile)
3. Contact your administrator

### Error Messages

If you receive an error:
1. Try rephrasing your query
2. Check the Nexus status page for system issues
3. Contact your administrator

---

## Getting Help

- **In Slack**: `/nexus help`
- **Documentation**: You're reading it!
- **Architecture**: [Architecture Guide](architecture.md)
- **API Reference**: [API Specs](api-specs/overview.md)
- **Issues**: [GitHub Issues](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues)
