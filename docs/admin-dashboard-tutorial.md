# Admin Dashboard Tutorial

> **Version:** 3.0.0 | **Last Updated:** December 2024

A step-by-step guide for using the Nexus Admin Dashboard. This tutorial is designed for users who prefer a visual, no-code approach to managing the Nexus system.

## Table of Contents

1. [Accessing the Dashboard](#1-accessing-the-dashboard)
2. [Understanding the Interface](#2-understanding-the-interface)
3. [Checking System Health](#3-checking-system-health)
4. [Switching Between Modes](#4-switching-between-modes)
5. [Viewing Observability Metrics](#5-viewing-observability-metrics)
6. [Managing Releases](#6-managing-releases)
7. [Using the Release Timeline](#7-using-the-release-timeline)
8. [Configuring Integrations](#8-configuring-integrations)
9. [Configuration Tab - Going from Mock to Live](#9-configuration-tab---going-from-mock-to-live)
10. [Monitoring Agents](#10-monitoring-agents)
11. [Authentication & SSO](#11-authentication--sso)
12. [User Management](#12-user-management)
13. [Role Management](#13-role-management)
14. [Feature Requests](#14-feature-requests)
15. [Viewing Audit Logs](#15-viewing-audit-logs)
16. [Customizing Your Dashboard](#16-customizing-your-dashboard)
17. [Keyboard Shortcuts](#17-keyboard-shortcuts)
18. [Using Filter Presets](#18-using-filter-presets)
19. [Common Tasks](#19-common-tasks)
20. [Troubleshooting](#20-troubleshooting)

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

The dashboard has a **sidebar** on the left with five main sections:

| Icon | Section | Purpose |
|------|---------|---------|
| 📊 | **Dashboard** | System overview and quick actions |
| 📅 | **Releases** | Manage releases and target dates |
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

## 6. Managing Releases

The **Releases** page allows you to track release versions, target dates, and readiness metrics. You can create releases manually or import from external sources like Smartsheet, CSV, or webhooks.

![Releases Page](assets/mockups/admin-releases.svg)

### Step 1: Navigate to Releases

Click **"📅 Releases"** in the sidebar (second item).

### Step 2: Review Summary Cards

At the top, you'll see four summary cards:

| Card | What It Shows | Color |
|------|---------------|-------|
| **Total Releases** | All tracked releases | Blue |
| **Upcoming** | Releases on schedule | Green |
| **At Risk** | Releases within 14 days of target | Amber |
| **Overdue** | Releases past target date | Red |

### Step 3: Create a New Release

1. Click the **"+ New Release"** button (top right)
2. Fill in the required fields:
   - **Version**: e.g., `v2.1.0`
   - **Target Date**: Select from calendar
3. Optional fields:
   - **Release Name**: e.g., "Phoenix"
   - **Description**: Brief description
   - **Release Type**: Major, Minor, Patch, Hotfix, Feature
   - **Jira Project Key**: e.g., `PROJ`
   - **Repository**: e.g., `nexus-backend`
   - **Release Manager**: Email address
4. Click **"Create Release"**

### Step 4: Import from Smartsheet

To sync releases from Smartsheet:

1. Click the **"Import"** button
2. Select the **"Smartsheet"** tab
3. Enter your Smartsheet API token
4. Enter the Sheet ID
5. Click **"Sync from Smartsheet"**

The system will automatically map these columns:
- Release Version
- Target Date
- Status
- Release Name (optional)

### Step 5: Import from CSV

To import from a CSV file:

1. Click the **"Import"** button
2. Select the **"CSV"** tab
3. Paste CSV data in this format:

```csv
version,target_date,name,status
v2.1.0,2025-02-15,Phoenix,planning
v2.2.0,2025-03-01,Ember,in_progress
```

4. Click **"Import CSV"**

### Step 6: Configure Webhook Integration

For automated syncing from external systems:

1. Click the **"Import"** button
2. Select the **"Webhook"** tab
3. Copy the webhook URL shown
4. Configure your external system to POST to this URL

**Webhook Payload Format:**
```json
{
  "action": "create",
  "source": "your-system",
  "release": {
    "version": "v2.1.0",
    "target_date": "2025-02-15T00:00:00Z",
    "name": "Phoenix"
  }
}
```

### Step 7: View Release Details

Each release card shows:

| Element | Description |
|---------|-------------|
| **Status Badge** | Planning, In Progress, Testing, Ready, Deployed |
| **Type Badge** | Major, Minor, Patch, Hotfix |
| **Source Badge** | Where the release came from |
| **Version** | Release version number |
| **Description** | Brief description |
| **Meta Info** | Target date, project, repo, manager |
| **Days Counter** | Days until release (red if overdue) |
| **Metrics** | Readiness score, ticket %, critical issues |

### Step 8: Track Milestones

For each release, you can track milestones:

1. Click on a release to expand
2. View milestone progress bar
3. Milestones show:
   - ✅ Green: Completed
   - 🔴 Red: Overdue
   - ⚪ Gray: Upcoming

### Step 9: Refresh Release Metrics

To update metrics from Jira, Jenkins, etc.:

1. Find the release card
2. Click the **🔄 Refresh** button
3. Wait for metrics to update

Metrics include:
- Ticket completion rate
- Build success rate
- Test coverage
- Critical vulnerabilities
- Readiness score

### Step 10: Delete a Release

1. Find the release card
2. Click the **🗑️ Delete** button
3. Confirm deletion in the popup

> ⚠️ **Warning**: Deletion is permanent. Make sure you want to remove this release.

---

## 7. Using the Release Timeline

The **Timeline View** provides a visual Gantt-style representation of your releases.

### Step 1: Switch to Timeline View

On the Releases page, click the **"📅 Timeline"** tab (next to "List" view).

### Step 2: Understanding the Timeline

The timeline shows:
- **Horizontal Axis**: Time (dates)
- **Vertical Axis**: Releases stacked
- **Bars**: Release duration (start to target date)
- **Today Marker**: Red vertical line showing current date

### Step 3: Change Zoom Level

Use the zoom controls at the top:

| Zoom | Best For |
|------|----------|
| **Day** | Detailed daily view (1-2 weeks visible) |
| **Week** | Standard planning view (1-2 months visible) |
| **Month** | High-level roadmap (3-6 months visible) |

### Step 4: Navigate the Timeline

- **Scroll Horizontally**: Drag the timeline left/right
- **Click "Today"**: Jump to current date
- **Click Release Bar**: View release details

### Step 5: Status Color Coding

| Color | Status |
|-------|--------|
| 🔵 Blue | Planned |
| 🟡 Yellow | In Progress |
| 🟢 Green | Completed |
| 🔴 Red | Cancelled |

### Step 6: View Release Details

Hover over any release bar to see a tooltip with:
- Version and name
- Target date
- Current status
- Days remaining

### Step 7: Quick Actions

Click on a release bar to open the detail panel where you can:
- Edit the release
- Change status
- View linked items

---

## 8. Configuring Integrations

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

## 9. Configuration Tab - Going from Mock to Live

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

## 10. Monitoring Agents

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

## 11. Authentication & SSO

The Admin Dashboard supports enterprise Single Sign-On (SSO) for secure authentication.

![Login Page](assets/mockups/admin-login.svg)

### Step 1: Access the Login Page

When you first access the dashboard, you'll see the login page with SSO options.

### Step 2: Choose Your SSO Provider

Click on your organization's SSO provider:

| Provider | Button | Configuration |
|----------|--------|---------------|
| **Okta** | Blue "Okta" button | Requires Okta app setup |
| **Azure AD** | Blue "Azure AD" button | Requires Azure app registration |
| **Google** | White "Google" button | Requires Google OAuth setup |
| **GitHub** | Black "GitHub" button | Requires GitHub OAuth app |

### Step 3: Authenticate

1. Click your SSO provider button
2. You'll be redirected to your identity provider
3. Enter your corporate credentials
4. Complete any MFA requirements
5. You'll be redirected back to the dashboard

### Step 4: Local Authentication (Fallback)

If SSO is not configured, you can use local authentication:

1. Enter your email address
2. Click **"Sign In"**
3. Check your email for a magic link (if enabled)

> **Tip**: Contact your administrator if you don't see your SSO provider listed.

---

## 12. User Management

Administrators can manage users, assign roles, and control access from the User Management page.

![User Management](assets/mockups/admin-user-management.svg)

### Step 1: Navigate to User Management

Click **"👥 User Management"** in the sidebar under the "ADMINISTRATION" section.

### Step 2: View Users

You'll see a table with all users showing:

- **User**: Name and avatar
- **Email**: User's email address
- **Role**: Assigned role (Admin, Developer, etc.)
- **Status**: Active, Pending, or Suspended
- **Auth**: SSO provider (Okta, Azure, Google, GitHub)
- **Actions**: Edit and delete buttons

### Step 3: Add a New User

1. Click the **"+ Add User"** button (top right)
2. Fill in user details:
   - Name
   - Email
   - Role (select from dropdown)
3. Click **"Create User"**

The user will receive an invitation email with setup instructions.

### Step 4: Edit a User

1. Find the user in the table
2. Click the **✏️** (edit) icon
3. Modify user details or role
4. Click **"Save Changes"**

### Step 5: Sync SSO Users

Click **"🔄 Sync SSO"** to import users from your identity provider.

---

## 13. Role Management

Define and customize roles to control access permissions.

![Role Management](assets/mockups/admin-role-management.svg)

### Step 1: Navigate to Role Management

Click **"🔐 Role Management"** in the sidebar under the "ADMINISTRATION" section.

### Step 2: View Existing Roles

The left panel shows all available roles:

| Role | Icon | Type |
|------|------|------|
| Admin | 🛡️ | System |
| Engineering Manager | 👔 | System |
| Developer | 💻 | System |
| Product Manager | 📦 | System |
| Custom roles | ⭐ | Custom |

### Step 3: View Role Permissions

1. Click on a role in the left panel
2. The right panel shows all permissions
3. Green toggles indicate enabled permissions

### Step 4: Edit Role Permissions

1. Click the **✏️** (edit) icon on the role
2. Toggle permissions on/off:
   - **Dashboard**: View, Edit Config
   - **Users**: View, Manage, Delete
   - **Feature Requests**: Submit, View, Manage
   - **System**: Admin Config, Audit Logs
3. Click **"💾 Save Permissions"**

### Step 5: Create a Custom Role

1. Click **"+ Create Role"** (top right)
2. Enter role name and description
3. Select permissions
4. Click **"Create Role"**

---

## 14. Feature Requests

Submit feature requests and bug reports that automatically create Jira tickets.

![Feature Requests](assets/mockups/admin-feature-requests.svg)

### Step 1: Navigate to Feature Requests

Click **"💡 Feature Requests"** in the sidebar under the "ADMINISTRATION" section.

### Step 2: View Existing Requests

The page shows:

- **Summary Cards**: Total, Pending, In Progress, Completed
- **Filter Tabs**: All, Features, Bugs, My Requests
- **Request Cards**: Detailed view of each request

### Step 3: Submit a New Request

1. Click **"+ New Request"** (top right)
2. Fill in the form:
   - **Type**: Feature Request, Bug Report, Improvement
   - **Title**: Brief description
   - **Description**: Detailed explanation
   - **Priority**: Critical, High, Medium, Low
   - **Component**: Which part of Nexus
   - **Labels**: Optional tags
3. Click **"Submit"**

### Step 4: Automatic Jira Integration

When you submit a request:

1. ✅ Stored in the Admin Dashboard
2. ✅ Jira ticket created automatically
3. ✅ Assigned to component owner
4. ✅ Notifications sent to Slack

The Jira ticket link appears on the request card.

### Step 5: Track Request Status

Request statuses:

| Status | Description | Jira Equivalent |
|--------|-------------|-----------------|
| **Submitted** | Just created | Open |
| **Triaged** | Under review | To Do |
| **In Progress** | Being worked on | In Progress |
| **Completed** | Done | Done |
| **Rejected** | Won't implement | Won't Do |

### Step 6: Export Requests

Click **"📤 Export"** to download requests as JSON or CSV.

---

## 15. Viewing Audit Logs

The **Audit Log** page provides a complete activity history for compliance and troubleshooting.

### Step 1: Navigate to Audit Log

Click **"📋 Audit Log"** in the sidebar.

### Step 2: View Activity History

You'll see a table with all system activities:

| Column | Description |
|--------|-------------|
| **Timestamp** | When the action occurred |
| **User** | Who performed the action |
| **Action** | What action was taken (create, update, delete, login) |
| **Resource** | What was affected (user, release, config) |
| **Details** | Additional context |

### Step 3: Filter Activities

Use the filter controls at the top:

1. **Date Range**: Select start and end dates
2. **User**: Filter by specific user
3. **Action Type**: Select action types (create, update, delete, login, logout)
4. **Resource Type**: Filter by resource (users, releases, roles, etc.)

### Step 4: Search

Use the search bar to find specific entries by keyword.

### Step 5: View Stats Dashboard

The stats panel shows:
- Total actions in period
- Actions by type (pie chart)
- Most active users
- Peak activity times

### Step 6: Export Audit Data

Click **"Export"** to download:
- **JSON**: Full data for programmatic use
- **CSV**: Spreadsheet-compatible format

---

## 16. Customizing Your Dashboard

The Dashboard features a **drag-and-drop widget system** for personalization.

### Step 1: Enter Edit Mode

Click the **"⚙️ Customize"** button in the dashboard header.

### Step 2: Rearrange Widgets

- **Drag**: Click and hold any widget card, drag to new position
- **Drop**: Release to place in new location
- Other widgets will automatically reflow

### Step 3: Resize Widgets

Click the resize icon on any widget to choose:

| Size | Description |
|------|-------------|
| **Small** | 1/4 width (fits 4 per row) |
| **Medium** | 1/2 width (fits 2 per row) |
| **Large** | 3/4 width |
| **Full** | Full width |

### Step 4: Show/Hide Widgets

- Click the **eye icon** to hide a widget
- Access hidden widgets from the **"+ Add Widget"** panel
- Click to restore hidden widgets

### Step 5: Save Layout

Click **"💾 Save Layout"** - your preferences persist in browser storage.

### Step 6: Reset to Default

Click **"🔄 Reset Layout"** to restore the default widget arrangement.

---

## 17. Keyboard Shortcuts

The dashboard supports **Vim-like keyboard navigation** for power users.

### Navigation Shortcuts

| Key | Action |
|-----|--------|
| `J` | Move down to next item |
| `K` | Move up to previous item |
| `G` | Go to first item |
| `Shift+G` | Go to last item |
| `Enter` | Select/Open current item |
| `Escape` | Close modal or cancel |

### Global Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus search input |
| `?` | Show keyboard shortcuts help |
| `D` | Go to Dashboard |
| `R` | Go to Releases |
| `H` | Go to Health Monitor |
| `S` | Go to Settings |

### List-Specific Shortcuts

| Key | Action |
|-----|--------|
| `E` | Edit selected item |
| `Delete` | Delete selected item |
| `N` | Create new item |

### Enabling Keyboard Navigation

Keyboard shortcuts are enabled by default. Click into a list view to activate navigation.

> 💡 **Tip**: Press `?` at any time to see all available shortcuts.

---

## 18. Using Filter Presets

Save and reuse filter combinations across sessions.

### Step 1: Apply Filters

Set up your desired filters (status, priority, date range, etc.).

### Step 2: Save as Preset

1. Click **"💾 Save Preset"** button
2. Enter a name (e.g., "My Active Releases")
3. Click **"Save"**

### Step 3: Load a Preset

1. Click the **"Presets"** dropdown
2. Select your saved preset
3. Filters apply automatically

### Step 4: Manage Presets

- **Edit**: Click the pencil icon to rename
- **Delete**: Click the trash icon to remove
- **Set Default**: Star a preset to load on page open

### URL Synchronization

Filters automatically sync to the URL:
```
/releases?status=in_progress&priority=high
```

This means you can:
- Share filtered views via URL
- Bookmark specific filter combinations
- Use browser back/forward to navigate filter history

---

## 19. Common Tasks

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

## 20. Troubleshooting

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

