# Admin Dashboard Tutorial

A step-by-step guide for using the Nexus Admin Dashboard. This tutorial is designed for users who prefer a visual, no-code approach to managing the Nexus system.

## Table of Contents

1. [Accessing the Dashboard](#1-accessing-the-dashboard)
2. [Understanding the Interface](#2-understanding-the-interface)
3. [Checking System Health](#3-checking-system-health)
4. [Switching Between Modes](#4-switching-between-modes)
5. [Configuring Integrations](#5-configuring-integrations)
6. [Monitoring Agents](#6-monitoring-agents)
7. [Common Tasks](#7-common-tasks)
8. [Troubleshooting](#8-troubleshooting)

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

The dashboard has a **sidebar** on the left with three main sections:

| Icon | Section | Purpose |
|------|---------|---------|
| 📊 | **Dashboard** | System overview and quick actions |
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

## 5. Configuring Integrations

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

## 6. Monitoring Agents

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

