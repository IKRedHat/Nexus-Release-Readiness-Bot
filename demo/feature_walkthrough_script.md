# Demo Script: Nexus Release Automation Walkthrough

**Goal:** Showcase the Nexus Multi-Agent System automating release readiness checks, proactive Jira hygiene management, AI-powered recommendations, and interactive reporting.

**Duration:** ~4 minutes

**What's New in v2.0:**
- 🤖 Google Gemini LLM integration
- 🏠 Slack App Home dashboard
- 💡 AI-powered recommendations
- 🏢 Multi-tenant support

---

## Scene 1: App Home Dashboard (0:00 - 0:30)

**Visual:** User clicks on the Nexus app in Slack sidebar. App Home opens.

**Visual:** Rich dashboard appears:

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Nexus Release Automation                                 │
│  Good morning, Alice! Here's your release management dashboard│
│  📅 Monday, December 2, 2024 | Last updated: 9:30 AM        │
├─────────────────────────────────────────────────────────────┤
│  ⚡ Quick Actions                                            │
│  [📊 Release Status] [🔧 Hygiene Check] [📝 Report] [❓ Help] │
├─────────────────────────────────────────────────────────────┤
│  📈 Release Status Overview                                  │
│  Current Version: v2.0.0                                     │
│  Decision: 🟡 CONDITIONAL | Completion: 87%                  │
│  Build: ✅ Passing | Security: 75/100 | Blockers: 2         │
├─────────────────────────────────────────────────────────────┤
│  🔧 Jira Hygiene: 🟡 78% - Good                [Fix Now]     │
├─────────────────────────────────────────────────────────────┤
│  💡 AI Recommendations                       [View All]      │
│  🔴 Address 2 blocking issues before release                 │
│  🟠 Improve hygiene score from 78% to 90%+                   │
└─────────────────────────────────────────────────────────────┘
```

**Voiceover:**
> "Welcome to Nexus 2.0! When you open the app in Slack, you're greeted with a personalized dashboard. At a glance, you see your release status, hygiene score, and AI-powered recommendations - all without typing a single command."

---

## Scene 2: Initiating a Release Readiness Check via Slack (0:30 - 1:00)

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

## Scene 3: Orchestrator ReAct Loop with Gemini (1:00 - 1:30)

**Visual:** Terminal or log view showing the ReAct loop trace with Gemini LLM.

```
User: "Is the v1.2.0 release ready?"
LLM: Google Gemini 2.0 Flash

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

📊 LLM Usage: 1,245 tokens | Cost: $0.0012 | Latency: 1.2s
```

**Voiceover:**
> "Behind the scenes, Google Gemini 2.0 Flash powers the reasoning. It thinks about what data it needs, calls specialized agents, and synthesizes a decision. Token usage and costs are tracked for every request."

---

## Scene 4: AI-Powered Recommendations (1:30 - 2:00)

**Visual:** User clicks "View All" in the AI Recommendations widget. Full recommendations panel opens.

```
┌─────────────────────────────────────────────────────────────┐
│  💡 AI Recommendations for PROJ                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔴 CRITICAL: Address Blocking Issues                        │
│  2 blocking issues are preventing release readiness.         │
│  → Resolve PROJ-145: API timeout issue                       │
│  → Resolve PROJ-147: Database connection failure             │
│                                                              │
│  🟠 HIGH: Improve Hygiene Score                              │
│  Current: 78% | Target: 90%+                                 │
│  → Add Story Points to 3 tickets                             │
│  → Add Labels to 2 tickets                                   │
│                                                              │
│  🟡 MEDIUM: Optimize Release Timing                          │
│  Historical analysis suggests Tuesday releases have          │
│  25% higher success rate than Friday releases.               │
│  → Consider scheduling for Tuesday afternoon                 │
│                                                              │
│  🟢 LOW: Process Improvement                                 │
│  → Add automated release checks to CI pipeline               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Voiceover:**
> "The AI Recommendations engine analyzes historical patterns - release timing, hygiene trends, velocity data - to provide actionable suggestions. Critical blockers are flagged first, followed by hygiene improvements and process optimizations."

---

## Scene 5: Jira Hygiene Agent - Proactive Quality (2:00 - 2:30)

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

## Scene 6: Interactive Fix Modal (2:30 - 3:00)

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

## Scene 7: Confluence Report Publishing (3:00 - 3:30)

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

## Scene 8: Observability Dashboard (3:30 - 3:50)

**Visual:** Grafana dashboard showing:
- Hygiene score trend (70% → 95% over 2 weeks)
- LLM token usage and cost tracking (Gemini vs OpenAI)
- Agent response times
- AI recommendation effectiveness
- Release decisions pie chart (GO: 80%, CONDITIONAL: 15%, NO-GO: 5%)

**Voiceover:**
> "Finally, everything is observable. Track hygiene improvements over time, monitor LLM costs across providers, analyze agent performance, measure recommendation impact, and review release decision trends - all in real-time dashboards."

---

## Closing (3:50 - 4:00)

**Visual:** Nexus logo with tagline.

**Voiceover:**
> "Nexus 2.0: Intelligent release automation powered by Google Gemini, with proactive AI recommendations and a beautiful dashboard experience. Try it today."

---

## Key Talking Points for Live Demo

1. **App Home Dashboard**: First-class Slack experience with at-a-glance status
2. **Google Gemini Integration**: Production-ready LLM with cost tracking
3. **AI Recommendations**: Pattern-based intelligent suggestions
4. **Multi-Agent Coordination**: Show how one query triggers multiple specialized agents
5. **Proactive Quality**: Highlight the shift-left approach of the Hygiene Agent
6. **Zero Context Switching**: Fixing Jira issues without leaving Slack
7. **Transparency**: The ReAct loop shows exactly how decisions are made
8. **Multi-Tenancy**: Enterprise-ready organization isolation (optional demo)
9. **Observability**: Everything is measured and visualized

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
