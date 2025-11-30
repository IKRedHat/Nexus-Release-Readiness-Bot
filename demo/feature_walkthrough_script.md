# Demo Script: Nexus Release Automation Walkthrough

**Goal:** Showcase the Nexus Multi-Agent System automating release readiness checks, proactive Jira hygiene management, and interactive reporting.

**Duration:** ~3 minutes

---

## Scene 1: Initiating a Release Readiness Check via Slack (0:00 - 0:30)

**Visual:** Slack interface. User types `/nexus status release-1.2.0` in a channel.

**Voiceover:**
> "Release managers often need quick, comprehensive updates on release readiness. With Nexus, they simply use a Slack command. Here, we're asking for the status of `release-1.2.0`."

**Action:** Show the "Thinking..." indicator appearing.

**Visual:** Nexus responds with a rich Block Kit message showing:
- 🟢 **GO Decision** banner
- Ticket completion: 95% (38/40)
- Test coverage: 87%
- Security risk score: 15/100
- Build status: ✅ Passing

**Voiceover:**
> "Within seconds, Nexus coordinates multiple agents - querying Jira for ticket status, GitHub for code health, Jenkins for build results - and synthesizes a Go/No-Go decision."

---

## Scene 2: Orchestrator ReAct Loop Visualization (0:30 - 1:00)

**Visual:** Terminal or log view showing the ReAct loop trace.

```
User: "Is the v1.2.0 release ready?"

🤔 Thought: I need to check Jira ticket completion first.
🔧 Action: get_sprint_stats
📊 Observation: {"completed": 38, "total": 40, "rate": 95%}

🤔 Thought: Good progress. Let me check security vulnerabilities.
🔧 Action: get_security_scan  
📊 Observation: {"risk_score": 15, "critical": 0, "high": 1}

🤔 Thought: No critical issues. Checking CI pipeline.
🔧 Action: get_build_status
📊 Observation: {"status": "SUCCESS", "tests": {"passed": 245}}

✅ Final Answer: The release is READY (GO).
```

**Voiceover:**
> "Behind the scenes, the ReAct engine reasons through each step. It thinks about what data it needs, calls specialized agents to gather information, observes the results, and continues until it has enough context to make a decision. This reasoning is fully transparent and auditable."

---

## Scene 3: Jira Hygiene Agent - Proactive Quality (1:00 - 1:45)

**Visual:** Clock showing 9:00 AM. Animation of the Hygiene Agent activating.

**Voiceover:**
> "But Nexus doesn't just wait for requests. The Jira Hygiene Agent runs proactively every weekday morning, scanning for data quality issues that could affect release assessments."

**Visual:** Slack DM notification appears for a developer:

```
📋 Jira Ticket Hygiene Report

Hi Alice! 👋

Our automated hygiene check found 3 tickets assigned 
to you that are missing required fields.

Project Hygiene Score: 70.0%

─────────────────────────────

Tickets needing attention:
• PROJ-123: Missing Labels, Story Points
• PROJ-124: Missing Fix Version
• PROJ-125: Missing Team/Contributors

─────────────────────────────

[🔧 Fix Tickets Now]  [📊 View Full Report]  [⏰ Remind Me Later]
```

**Voiceover:**
> "Developers receive friendly DMs listing exactly which tickets need attention, with actionable buttons to resolve issues immediately."

---

## Scene 4: Interactive Fix Modal (1:45 - 2:15)

**Visual:** User clicks "🔧 Fix Tickets Now" button. Modal opens.

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
│  │ backend, security, api              │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  📊 Story Points                            │
│  ┌─────────────────────────────────────┐   │
│  │ 8                            ▼      │   │
│  └─────────────────────────────────────┘   │
│                                             │
├─────────────────────────────────────────────┤
│           [Cancel]  [Update Tickets]        │
└─────────────────────────────────────────────┘
```

**Voiceover:**
> "Without leaving Slack, developers can fill in missing fields right in the modal. Labels, Fix Versions, Story Points, Team assignments - all updated with a single click."

**Visual:** User fills in fields and clicks "Update Tickets". Modal updates to show success.

**Voiceover:**
> "The updates flow through to Jira automatically, improving the hygiene score and ensuring accurate release assessments."

---

## Scene 5: Confluence Report Publishing (2:15 - 2:45)

**Visual:** User types `/nexus report v1.2.0`

**Voiceover:**
> "When it's time to document the release decision, Nexus generates beautiful, comprehensive reports."

**Visual:** Confluence page opens showing the Release Readiness Report:
- Executive summary with GO decision
- Ticket statistics chart
- Security scan results
- Test coverage metrics
- Blockers and risks section
- Timestamp and audit trail

**Voiceover:**
> "The report is automatically published to Confluence, providing a permanent record for compliance and stakeholder communication."

---

## Scene 6: Observability Dashboard (2:45 - 3:00)

**Visual:** Grafana dashboard showing:
- Hygiene score trend (70% → 95% over 2 weeks)
- LLM token usage graph
- Agent response times
- Release decisions pie chart (GO: 80%, CONDITIONAL: 15%, NO-GO: 5%)

**Voiceover:**
> "Finally, everything is observable. Track hygiene improvements over time, monitor LLM costs, analyze agent performance, and review release decision trends - all in real-time dashboards."

---

## Closing (3:00)

**Visual:** Nexus logo with tagline.

**Voiceover:**
> "Nexus: Intelligent release automation that thinks, acts, and keeps your data clean. Try it today."

---

## Key Talking Points for Live Demo

1. **Natural Language Understanding**: Emphasize that users don't need to learn complex syntax
2. **Multi-Agent Coordination**: Show how one query triggers multiple specialized agents
3. **Proactive Quality**: Highlight the shift-left approach of the Hygiene Agent
4. **Zero Context Switching**: Fixing Jira issues without leaving Slack
5. **Transparency**: The ReAct loop shows exactly how decisions are made
6. **Observability**: Everything is measured and visualized

## Demo Environment Setup

```bash
# Start all services
docker-compose up -d

# Verify health
curl http://localhost:8080/health
curl http://localhost:8005/health

# Trigger a hygiene check for demo
curl -X POST http://localhost:8005/run-check \
  -H "Content-Type: application/json" \
  -d '{"project_key": "PROJ", "notify": true}'

# Access Grafana (admin/nexus_admin)
open http://localhost:3000
```

## Fallback Mock Data

If live integrations aren't available, Nexus runs in mock mode providing realistic sample data for demonstrations.
