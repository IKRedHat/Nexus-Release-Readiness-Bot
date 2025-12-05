# 🧭 Nexus Engineering Onboarding Guide

> The comprehensive map to the Nexus Multi-Agent Release Automation Platform.

![Status](https://img.shields.io/badge/Status-Active_Development-blue?style=for-the-badge)
![Tech](https://img.shields.io/badge/Tech-Python_|_FastAPI_|_LangGraph-green?style=for-the-badge)
![Docs](https://img.shields.io/badge/Docs-Up_to_Date-orange?style=for-the-badge)

---

## 1. 🚀 What is Nexus? (The 30-Second Pitch)

> **Think of Nexus as a super-smart Release Manager that lives in Slack.**

Instead of you manually checking 5 different tools, Nexus orchestrates the work:

1. **🧠 Thinks:** "User asked for status → I need to check Jira and Jenkins."
2. **⚡ Acts:** Securely connects to tools via API.
3. **📝 Summarizes:** Returns a "Go/No-Go" decision report.

**It's not just a chatbot.** It is a **Stateful Multi-Agent System** capable of reasoning, planning, and executing complex workflows.

---

## 2. 🏗️ The Architecture: Hub-and-Spoke

We use a **Monorepo** structure organized like a wheel.

| Component | Role | Description |
|-----------|------|-------------|
| **The Hub** | 🧠 **Orchestrator** | The central brain. Receives Slack messages, plans the workflow using AI, and delegates tasks. |
| **The Spokes** | 🤖 **Agents** | Small, focused services. Each agent handles ONE tool (Jira, Git, etc.) and reports back to the Hub. |

---

## 3. 📂 Navigating the Code (`/services`)

This is where 90% of your work will happen. Each folder acts as an independent microservice.

### 🧠 The Brain

- **`services/orchestrator/`**
  - **Role:** The decision maker. Maintains memory and runs the reasoning loop.
  - **Key File:** `app/core/react_engine.py` (The AI Logic).
  - **Tech:** Python, FastAPI, Gemini AI, LangGraph.

### 🤖 The Hands (Agents)

These services wrap external APIs into a standard interface.

| Agent | Purpose |
|-------|---------|
| `jira_agent/` | Translates "Get Ticket" into Atlassian API calls. Handles hierarchy fetching. |
| `git_ci_agent/` | Triggers Jenkins builds, checks GitHub PR status, and runs RCA. |
| `slack_agent/` | The "Ears". Listens to Slack events/commands and forwards them to the Hub. |
| `reporting_agent/` | Generates beautiful HTML dashboards and publishes them to Confluence. |

### ⚙️ The Control Panel

- **`services/admin_dashboard/`**
  - **Role:** A web UI to manage API keys and configurations without restarting servers.
  - **Tech:** React (Frontend) + FastAPI (Backend).

---

## 4. 🔗 The Glue (`/shared`)

We hate repeating code. Common logic lives here to keep agents lightweight.

| Path | Purpose |
|------|---------|
| 📦 `shared/nexus_lib/schemas/` | **The Contracts:** Defines data models like `JiraTicket`. Ensures the Orchestrator and Agents speak the same language. |
| 🛡️ `shared/nexus_lib/middleware.py` | **Security & Metrics:** Automatically handles token validation and request counting for every service. |

---

## 5. 🛠️ How It Runs (`/infrastructure`)

We use **Docker** to containerize everything. No "it works on my machine" issues.

### docker-compose.yml

This magic file spins up the entire world with one command:

1. 🗄️ **Postgres:** For saving state (Memory).
2. ⚡ **Redis:** For fast configuration caching.
3. 🚀 **Orchestrator + 5 Agents:** All connected on a private network.

---

## 6. 💻 Your First Contribution

Ready to ship code? Follow this flow:

1. **Pick a Card:** Find a Jira ticket (e.g., *"Add support for Trello"*).

2. **Create the Agent:**
   - Copy the `jira_agent` folder.
   - Rename it to `trello_agent`.

3. **Define the Contract:** Go to `shared/nexus_lib/schemas` and define what a `TrelloCard` looks like.

4. **Implement Logic:** Write the code to talk to Trello API using our `AsyncHttpClient` wrapper.

5. **Register:** Add the agent to `docker-compose.yml` and tell the Orchestrator about the new tool.

6. **Test:**
   ```bash
   ./setup_local_env.sh
   docker-compose up
   ```

> 💡 **Pro Tip:** Stuck? Check `tests/e2e/`. We have end-to-end tests that trace a request from start to finish!

---

*Made with ❤️ for Nexus Engineers*

