# Admin Dashboard Tutorial

A step-by-step guide for using the Nexus Admin Dashboard. This tutorial is designed for users who prefer a visual, no-code approach to managing the Nexus system.

## Table of Contents

1. [Accessing the Dashboard](#1-accessing-the-dashboard)
2. [Understanding the Interface](#2-understanding-the-interface)
3. [Checking System Health](#3-checking-system-health)
4. [Switching Between Modes](#4-switching-between-modes)
5. [Viewing Observability Metrics](#5-viewing-observability-metrics)
6. [Configuration Tab - Going from Mock to Live](#6-configuration-tab---going-from-mock-to-live)
7. [Monitoring Agents](#7-monitoring-agents)
8. [Common Tasks](#8-common-tasks)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Accessing the Dashboard

### Step 1: Open Your Browser

Open your preferred web browser (Chrome, Firefox, Safari, or Edge).

### Step 2: Navigate to the Dashboard

Type the dashboard URL in the address bar:

```
http://localhost:8088
```

> **Note**: If Nexus is deployed on a server, replace `localhost` with your server's address.

### Step 3: Wait for the Dashboard to Load

You should see the Nexus Admin Dashboard with a dark theme and green accent colors.

![Dashboard Loading](assets/mockups/admin-dashboard.svg)

---

## 2. Understanding the Interface

### Main Navigation

The dashboard has a **sidebar** on the left with four main sections:

| Icon | Section | Purpose |
|------|---------|---------|
| 📊 | **Dashboard** | System overview and quick actions |
| 📈 | **Observability** | Metrics, charts, and performance data |
| ❤️ | **Health Monitor** | Real-time agent status |
| ⚙️ | **Configuration** | Manage settings and credentials |

### Dashboard Overview

The main dashboard shows:

1. **Mode Switch** (top right) - Toggle between Mock and Live modes
2. **Status Cards** - System mode, agent health, Redis connection, uptime
3. **Agent Grid** - Health status of each agent
4. **Quick Actions** - Common tasks like refresh and mode switching

---

## 3. Checking System Health

### Step 1: Go to Health Monitor

Click on **"Health Monitor"** in the sidebar.

### Step 2: View Overall Status

At the top, you'll see a banner showing:
- **System Status**: Healthy (green), Degraded (yellow), or Unhealthy (red)
- **Active Agents**: How many agents are running (e.g., "7 of 9 operational")
- **Current Mode**: Mock or Live

### Step 3: Review Individual Agents

Each agent is shown in a card with:
- **Name**: e.g., "Jira Agent"
- **Status**: Green dot = healthy, Red dot = unhealthy
- **Response Time**: How fast the agent responds (in milliseconds)
- **URL**: The agent's internal address

### Step 4: Click for Details

Click on any agent card to see more information:
- Detailed status
- Last check time
- Error messages (if any)

### Step 5: Enable Auto-Refresh

Toggle **"Auto-refresh"** at the top right to automatically update health status every 10 seconds.

---

## 4. Switching Between Modes

### Understanding Modes

| Mode | What It Does | When to Use |
|------|--------------|-------------|
| **Mock** | Uses simulated data | Testing, demos, development |
| **Live** | Connects to real systems | Production use |

### Step 1: Locate the Mode Switch

Find the **mode toggle** in the top-right corner of the Dashboard page.

It shows:
- **Mock** on the left
- **Live** on the right
- A switch in between

### Step 2: Click the Switch

To change modes:
1. Click on the switch toggle
2. It will slide from one side to the other
3. Wait 1-2 seconds for the change to propagate

### Step 3: Confirm the Change

You'll see:
- A notification confirming the mode change
- All status cards update to reflect the new mode
- The mode indicator changes color (Yellow for Mock, Green for Live)

### Step 4: Verify Agents Updated

Go to **Health Monitor** to ensure all agents are operating in the new mode.

> ⚠️ **Warning**: Switching to Live mode will make real API calls to Jira, GitHub, etc. Make sure your credentials are configured first!

---

## 5. Viewing Observability Metrics

The **Observability** page provides a consolidated view of all system metrics, integrating data from Prometheus and Grafana.

![Observability Dashboard](assets/mockups/admin-observability.svg)

### Step 1: Navigate to Observability

Click **"📈 Observability"** in the sidebar (second item).

### Step 2: Review Summary Cards

At the top, you'll see four key metrics:

| Card | What It Shows | Good Value |
|------|---------------|------------|
| **Total Requests** | All API requests processed | Depends on usage |
| **Avg Latency** | Average response time | < 200ms |
| **Error Rate** | Percentage of failed requests | < 1% |
| **LLM Cost** | Total AI API costs | Budget-dependent |

Each card shows:
- Current value
- Change percentage (green = good, red = bad)

### Step 3: Select Time Range

Use the time selector at the top right:

| Option | Shows Data From |
|--------|-----------------|
| **1h** | Last 1 hour |
| **6h** | Last 6 hours |
| **24h** | Last 24 hours |
| **7d** | Last 7 days |

### Step 4: Analyze Traffic Chart

The **Request Traffic** chart shows:
- X-axis: Time
- Y-axis: Number of requests
- Area filled in green

Look for:
- 📈 **Spikes**: Sudden traffic increases
- 📉 **Drops**: Possible issues
- 📊 **Patterns**: Regular usage patterns

### Step 5: Check Latency Trends

The **Latency Over Time** chart shows response times:
- Blue line = Average latency
- Higher = Slower responses

Watch for:
- Sudden spikes (performance issues)
- Gradual increases (capacity problems)

### Step 6: Review Agent Performance Table

The table shows per-agent metrics:

| Column | Meaning |
|--------|---------|
| **Agent** | Service name |
| **Status** | healthy/degraded/unhealthy |
| **Requests** | Number of requests handled |
| **Errors** | Failed requests |
| **Latency** | Average response time |

> 💡 **Tip**: Click on column headers to sort

### Step 7: Analyze LLM Usage

The **LLM Token Usage** pie chart shows:
- Token distribution by model
- Cost per model
- Color-coded legend

This helps you:
- Understand AI costs
- Optimize model selection
- Track mock vs live usage

### Step 8: Check Hygiene Score

The circular **Hygiene Score** indicator shows:
- Percentage of compliant Jira tickets
- Color-coded: Green (>80%), Yellow (60-80%), Red (<60%)

### Step 9: Access External Dashboards

Click the quick links to open:
- **Grafana**: Full detailed dashboards
- **Prometheus**: Raw metrics queries
- **Jaeger**: Distributed tracing

### Step 10: View Embedded Grafana (Optional)

If Grafana is configured for embedding:
1. Scroll to the bottom
2. View embedded Grafana panels
3. Click "Open in Grafana" for full view

> **Note**: To enable embedding, set `allow_embedding = true` in Grafana configuration.

---

## 6. Configuring Integrations

### Step 1: Go to Configuration

Click on **"Configuration"** in the sidebar.

### Step 2: Select an Integration

At the top, you'll see tabs for different integrations:
- **Jira** - Issue tracking
- **GitHub** - Code repository
- **Jenkins** - CI/CD pipelines
- **LLM** - AI/Language models
- **Slack** - Messaging
- **Confluence** - Documentation

Click on the tab you want to configure.

### Step 3: Fill in the Fields

Each integration has specific fields:

#### Jira Configuration

| Field | What to Enter | Example |
|-------|---------------|---------|
| Jira URL | Your Atlassian URL | `https://mycompany.atlassian.net` |
| Username/Email | Your login email | `user@company.com` |
| API Token | Your Jira API token | `xxxxxxxxxx` |
| Default Project | Project key | `PROJ` |

#### GitHub Configuration

| Field | What to Enter | Example |
|-------|---------------|---------|
| Personal Access Token | GitHub PAT | `ghp_xxxxxx` |
| Organization | Your org name | `mycompany` |
| Default Repository | Main repo | `main-app` |

#### LLM Configuration

| Field | What to Enter | Example |
|-------|---------------|---------|
| Provider | Select from dropdown | `google` |
| Model | Model name | `gemini-1.5-pro` |
| Gemini API Key | Google AI key | `AIzaxxxxxxx` |
| OpenAI API Key | OpenAI key | `sk-xxxxxxx` |

### Step 4: Save Each Field

After entering a value:
1. Click the **"Save"** button next to the field
2. Wait for the success message
3. The button turns gray when saved

### Step 5: Verify Configuration

Scroll down to see the **"All Configuration Values"** table showing:
- All configured keys
- Their current values (masked for secrets)
- The source (Redis, Environment, or Default)

---

## 6. Configuration Tab - Going from Mock to Live

The Configuration tab is where you set up all your integrations to move from Mock mode to Live mode. This is the most important section for production deployment.

![Configuration Tab](assets/mockups/admin-dashboard-config.svg)

### Understanding Configuration Sources

Configuration values come from three sources (in priority order):

| Source | Color | Description |
|--------|-------|-------------|
| **Redis** | 🟢 Green | Dynamically set via Admin Dashboard |
| **Environment** | 🔵 Blue | Set via Docker/K8s environment variables |
| **Default** | ⚪ Gray | Built-in fallback values |

### Step 1: Navigate to Configuration

1. Click **"Configuration"** (⚙️) in the sidebar
2. You'll see tabs for each integration category

### Step 2: Configure Jira

1. Click the **"Jira"** tab
2. Fill in the following fields:

| Field | What to Enter | How to Get It |
|-------|---------------|---------------|
| **Jira URL** | `https://your-org.atlassian.net` | Your Jira Cloud URL |
| **Username/Email** | Your Atlassian email | e.g., `user@company.com` |
| **API Token** | Jira API token | Create at [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |
| **Default Project** | Project key | e.g., `PROJ`, `NEXUS` |

3. Click **"Save"** after each field
4. Wait for the green success message

### Step 3: Configure GitHub

1. Click the **"GitHub"** tab
2. Fill in:

| Field | What to Enter | How to Get It |
|-------|---------------|---------------|
| **Personal Access Token** | `ghp_xxxxxxxxxxxx` | Create at GitHub → Settings → Developer Settings → Personal access tokens |
| **Organization** | Your GitHub org name | e.g., `mycompany` |
| **Default Repository** | Main repo name | e.g., `nexus-app` |

**Required Token Scopes:**
- `repo` - Full repository access
- `read:org` - Read organization data
- `workflow` - Trigger GitHub Actions

### Step 4: Configure Jenkins

1. Click the **"Jenkins"** tab
2. Fill in:

| Field | What to Enter | How to Get It |
|-------|---------------|---------------|
| **Jenkins URL** | `http://jenkins.company.com:8080` | Your Jenkins server URL |
| **Username** | Jenkins username | Usually your login |
| **API Token** | Jenkins API token | Jenkins → User → Configure → API Token |

### Step 5: Configure LLM (AI Provider)

1. Click the **"LLM"** tab
2. Choose your provider and configure:

**For Google Gemini (Recommended):**

| Field | Value |
|-------|-------|
| **Provider** | `google` |
| **Model** | `gemini-1.5-pro` (or `gemini-2.0-flash`) |
| **Gemini API Key** | Get from [Google AI Studio](https://aistudio.google.com/app/apikey) |

**For OpenAI:**

| Field | Value |
|-------|-------|
| **Provider** | `openai` |
| **Model** | `gpt-4o` or `gpt-4-turbo` |
| **OpenAI API Key** | Get from [OpenAI Platform](https://platform.openai.com/api-keys) |

**For Mock Mode (Testing):**

| Field | Value |
|-------|-------|
| **Provider** | `mock` |

### Step 6: Configure Slack (Optional)

1. Click the **"Slack"** tab
2. Fill in:

| Field | What to Enter | How to Get It |
|-------|---------------|---------------|
| **Bot Token** | `xoxb-xxxx` | Slack App → OAuth & Permissions |
| **Signing Secret** | `xxxxxxxx` | Slack App → Basic Information |
| **App Token** | `xapp-xxxx` | Slack App → Basic Information → App-Level Tokens |

### Step 7: Configure Confluence (Optional)

1. Click the **"Confluence"** tab
2. Fill in:

| Field | What to Enter |
|-------|---------------|
| **Confluence URL** | `https://your-org.atlassian.net/wiki` |
| **Username/Email** | Same as Jira |
| **API Token** | Same as Jira API token |
| **Space Key** | Target space key (e.g., `DOCS`) |

### Step 8: Verify Configuration

After configuring all integrations:

1. Scroll down to **"All Configuration Values"** table
2. Verify each key shows:
   - ✅ Your entered value (or masked for secrets)
   - ✅ Source shows "redis" (green)
   - ✅ Correct category

### Step 9: Switch to Live Mode

Once all configurations are saved:

1. Go back to **Dashboard**
2. Click the **Mode Switch** to toggle from Mock → Live
3. The switch will turn green
4. Go to **Health Monitor** to verify all agents connect successfully

### Troubleshooting Configuration

| Problem | Solution |
|---------|----------|
| "Save" button stays gray | Enter a different value than current |
| Value not saving | Check Redis connection in health check |
| Source shows "env" not "redis" | Click Save again to override |
| Agent unhealthy after config | Verify credentials are correct, check agent logs |

### Quick Reference: Required vs Optional

| Integration | Required for Live? | Notes |
|-------------|-------------------|-------|
| Jira | ✅ Required | Core functionality |
| GitHub | ✅ Required | For PR and repo analysis |
| Jenkins | ⚠️ Recommended | For build status |
| LLM | ✅ Required | For AI reasoning |
| Slack | ⚠️ Recommended | For notifications |
| Confluence | ⚪ Optional | For report publishing |

---

## 7. Monitoring Agents

### Step 1: Go to Health Monitor

Click **"Health Monitor"** in the sidebar.

### Step 2: Check the Overview Banner

The top banner shows system-wide health:
- 🟢 **System Healthy**: All agents working
- 🟡 **System Degraded**: Some agents down
- 🔴 **System Unhealthy**: Critical failures

### Step 3: Review Agent Cards

Each card shows:
- **Agent Name**: What the agent does
- **Status Dot**: Green (healthy) or Red (unhealthy)
- **Connection**: "Connected" or "Disconnected"
- **Response Time**: Speed in milliseconds

### Step 4: Investigate Issues

If an agent shows red:
1. Click on the card
2. Review the error details
3. Note the error message
4. Check the agent logs for more information

### Step 5: Manual Refresh

Click **"Refresh Now"** to immediately check all agents.

---

## 7. Common Tasks

### Task 1: Preparing for a Demo

1. Go to **Dashboard**
2. Ensure the mode is set to **Mock**
3. Check **Health Monitor** - all agents should be green
4. Go to **Configuration** → **LLM**
5. Set Provider to `mock`
6. Save the setting

### Task 2: Going Live for Production

1. Go to **Configuration**
2. Configure all integrations:
   - Jira URL and credentials
   - GitHub token
   - Jenkins credentials
   - LLM API keys (Gemini or OpenAI)
   - Slack tokens
3. Go to **Dashboard**
4. Click the mode switch to **Live**
5. Monitor **Health Monitor** for any issues

### Task 3: Updating API Credentials

1. Go to **Configuration**
2. Select the integration (e.g., Jira)
3. Find the credential field (e.g., API Token)
4. Enter the new value
5. Click **Save**
6. Verify in the table below that the source shows "redis"

### Task 4: Troubleshooting an Agent

1. Go to **Health Monitor**
2. Find the unhealthy agent (red status)
3. Click on the agent card
4. Note the error message
5. Common fixes:
   - Check credentials in Configuration
   - Verify the external service is accessible
   - Restart the agent container

---

## 8. Troubleshooting

### Problem: Dashboard Won't Load

**Symptoms**: Blank page or "Connection Refused"

**Solutions**:
1. Check if Docker containers are running:
   ```bash
   docker ps
   ```
2. Ensure the admin-dashboard container is up
3. Try accessing http://localhost:8088/health

### Problem: "Redis Not Available" Warning

**Symptoms**: Yellow warning about Redis connection

**Solutions**:
1. Check if Redis is running:
   ```bash
   docker ps | grep redis
   ```
2. The dashboard will still work using environment variables

### Problem: Agent Shows Unhealthy

**Symptoms**: Red status dot on an agent

**Solutions**:
1. Click the agent card for details
2. Check the error message
3. Verify the agent container is running
4. Check agent-specific credentials in Configuration

### Problem: Configuration Not Saving

**Symptoms**: Save button doesn't work or no success message

**Solutions**:
1. Check Redis connectivity (see above)
2. Ensure the value is not empty
3. Try refreshing the page
4. Check browser console for errors

### Problem: Mode Switch Doesn't Work

**Symptoms**: Switch toggles but mode doesn't change

**Solutions**:
1. Wait a few seconds for propagation
2. Refresh the page
3. Check if Redis is connected
4. Verify no other errors are shown

### Problem: Health Checks Are Slow

**Symptoms**: Agent cards take a long time to update

**Solutions**:
1. Network latency may be high
2. Disable auto-refresh temporarily
3. Use manual refresh for specific checks
4. Check if agents are overloaded

---

## Quick Reference Card

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `R` | Refresh health status |
| `D` | Go to Dashboard |
| `H` | Go to Health Monitor |
| `S` | Go to Settings |

### Color Codes

| Color | Meaning |
|-------|---------|
| 🟢 Green | Healthy / Success / Live Mode |
| 🟡 Yellow/Amber | Warning / Mock Mode |
| 🔴 Red | Error / Unhealthy |
| ⚪ Gray | Disabled / Neutral |

### Status Icons

| Icon | Meaning |
|------|---------|
| ✓ | Success / Healthy |
| ✗ | Error / Unhealthy |
| ⟳ | Loading / Refreshing |
| ⚠ | Warning |
| 🔒 | Sensitive / Secure |

---

## Getting Help

If you encounter issues not covered in this tutorial:

1. **Check the logs**: Use `docker logs admin-dashboard`
2. **Review documentation**: See `/docs/admin-dashboard.md`
3. **Ask in Slack**: Post in #nexus-support
4. **File an issue**: GitHub Issues for bugs

---

*Last updated: December 2025*

