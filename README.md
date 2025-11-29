<div align="center">

Nexus: Multi-Agent Release Automation System

<p>
<b>Nexus</b> is a cutting-edge, multi-agent automation system designed to revolutionize software Release Management.
Built on a <b>Managed Compute Platform (MCP)</b> architecture, Nexus uses a Central Orchestrator powered by the
<b>ReAct (Reasoning and Acting)</b> framework to coordinate specialized agents, automating everything from weekly status nudges to complex Go/No-Go decision reports.
</p>

</div>

📑 Table of Contents

System Architecture

Key Features

Repository Structure

Quick Start

Roadmap

Contributing

License

🧠 System Architecture

<p>Nexus operates on a <b>hub-and-spoke model</b>. The Central Orchestrator acts as the "brain," delegating tasks to specialized agents that interface with external tools.</p>

<table>
<thead>
<tr>
<th align="left">Component</th>
<th align="left">Responsibility</th>
<th align="left">Tech Stack</th>
</tr>
</thead>
<tbody>
<tr>
<td><b>Central Orchestrator</b></td>
<td>ReAct planning engine, context management, and routing.</td>
<td>Python (FastAPI), Gemini API</td>
</tr>
<tr>
<td><b>Slack Agent</b></td>
<td>Conversational interface, slash commands, and interactive modals.</td>
<td>Slack Bolt SDK</td>
</tr>
<tr>
<td><b>Jira Agent</b></td>
<td>Ticket management, hierarchical summaries (Task → Epic).</td>
<td>Jira Cloud API</td>
</tr>
<tr>
<td><b>Git/CI Agent</b></td>
<td>Build triggers, branch management, and security scanning.</td>
<td>GitHub/Jenkins APIs</td>
</tr>
<tr>
<td><b>Reporting Agent</b></td>
<td>Generates Confluence Go/No-Go reports and aggregates evidence.</td>
<td>Confluence API</td>
</tr>
<tr>
<td><b>Data Layer</b></td>
<td>RAG Memory (Vector DB) and State Management.</td>
<td>PostgreSQL, Vector DB</td>
</tr>
</tbody>
</table>

✨ Key Features

1. 💬 Conversational Core

<ul>
<li><b>Slack-First Workflow:</b> Developers interact entirely via Slack using commands like <code>/jira update</code> or <code>/jenkins build</code>.</li>
<li><b>Interactive Modals:</b> Update ticket status and add comments seamlessly without context switching.</li>
</ul>

2. 🤖 Intelligent Automation

<ul>
<li><b>ReAct Planning:</b> The Orchestrator dynamically determines the correct sequence of agents to call based on natural language queries.




<i>Example: "Check the status of the payment service release and look for any blockers"</i>
</li>
<li><b>RAG-Powered Search:</b> Provides answers grounded in historical data from Jira and Confluence.




<i>Example: "Why did the Q3 release fail?"</i>
</li>
</ul>

3. 📊 Automated Reporting

<ul>
<li><b>Hierarchical Summaries:</b> Uses LLMs to summarize child tasks into Epic descriptions and Epics into Strategic updates.</li>
<li><b>One-Click Go/No-Go:</b> Automatically compiles security scores, test results, and outstanding blockers into a Confluence decision document.</li>
</ul>

📂 Repository Structure

<p>This project follows a <b>Monorepo</b> pattern for easier dependency management and synchronized deployments.</p>

<pre>
nexus-automation/
├── .github/workflows/          <span style="color: #888;"># CI/CD Pipelines</span>
├── infrastructure/             <span style="color: #888;"># Terraform & Docker configuration</span>
│   ├── terraform/              <span style="color: #888;"># Cloud provisioning (Cloud Run, SQL)</span>
│   └── docker/                 <span style="color: #888;"># Dockerfiles for Orchestrator & Agents</span>
├── services/                   <span style="color: #888;"># Microservices Source Code</span>
│   ├── orchestrator/           <span style="color: #888;"># Central Intelligence (FastAPI + ReAct)</span>
│   └── agents/                 <span style="color: #888;"># Specialized Tool Agents (Jira, Git, Slack, etc.)</span>
├── shared/nexus_lib/           <span style="color: #888;"># Shared Schemas & API Contracts</span>
├── tests/e2e/                  <span style="color: #888;"># Integration Tests</span>
└── scripts/                    <span style="color: #888;"># Setup and Utility Scripts</span>
</pre>

🚀 Quick Start

Follow these steps to get the system running locally.

Prerequisites

Python 3.11+

Docker & Docker Compose

Git

1. Installation

Clone the repository and enter the directory:

git clone [https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git)
cd Nexus-Release-Readiness-Bot


2. Setup & Code Injection

Initialize the project structure and inject the MVP functional code:

# 1. Create folder structure
chmod +x setup_repo.sh
./setup_repo.sh

# 2. Inject MVP functional code (Orchestrator, Shared Libs, Terraform)
chmod +x install_nexus_code.sh
./install_nexus_code.sh


3. Run Local Demo

Test the ReAct Engine logic locally without deploying to the cloud:

chmod +x run_mvp_demo.sh
./run_mvp_demo.sh


What this does:

Sets up a local virtual environment.

Starts the Central Orchestrator service in the background.

Simulates user commands (e.g., /jira status, /search-rm) via CURL.

Displays the ReAct plan generated by the Orchestrator.

🗺️ Roadmap

[x] Phase 0: Foundation (Current) - Infrastructure setup, Auth, and API Contracts.

[ ] Phase 1: Conversational Core - Full Slack integration and basic Jira updates.

[ ] Phase 2: Intelligence - Vector DB implementation and ReAct grounded search.

[ ] Phase 3: Automation - Scheduling agent and automated Confluence reporting.

🤝 Contributing

We welcome contributions! Please follow these steps:

Fork the repository.

Create a feature branch (git checkout -b feature/amazing-feature).

Commit your changes (git commit -m 'Add some amazing feature').

Push to the branch (git push origin feature/amazing-feature).

Open a Pull Request.

📄 License

Distributed under the MIT License. See LICENSE for more information.

