# Nexus Release Automation - Demo Walkthrough Script

## 🎬 Video Overview

**Duration:** 2-3 minutes  
**Format:** Screen recording with voiceover  
**Resolution:** 1920x1080  

---

## Scene 1: Introduction (0:00 - 0:20)

### Visual
- Slack workspace with Nexus bot visible in sidebar
- Clean, professional Slack theme

### Voiceover

> "Meet Nexus, your AI-powered release automation assistant. Nexus connects to your existing tools - Jira, GitHub, Jenkins, and Confluence - to provide intelligent release readiness assessments through natural conversation."

### On-Screen Action
1. Show Slack workspace
2. Hover over Nexus bot in sidebar

---

## Scene 2: Triggering a Release Check (0:20 - 0:45)

### Visual
- Slack message input focused
- Type the command slowly

### Voiceover

> "Let's check if our v2.0 release is ready for production. I'll simply ask Nexus using natural language."

### On-Screen Action

1. Type: `/nexus Is the v2.0 release ready to go?`
2. Press Enter
3. Show the immediate acknowledgment: "🧠 Nexus is thinking..."

### Script Highlight
```
User types: /nexus Is the v2.0 release ready to go?
Bot responds: 🧠 Processing your request...
```

---

## Scene 3: The ReAct Reasoning Process (0:45 - 1:15)

### Visual
- Split screen: Slack on left, Orchestrator logs on right
- Terminal showing colored logs

### Voiceover

> "Behind the scenes, Nexus uses a ReAct reasoning engine. Watch as it thinks through what data to gather, takes actions to call specialized agents, and observes the results."

### On-Screen Action (Terminal/Logs)

Show logs appearing in real-time:

```
[ORCHESTRATOR] ReAct Loop Started
[THOUGHT] I need to check Jira sprint status for release readiness
[ACTION] get_sprint_stats → Jira Agent
[OBSERVE] Received: 93.3% completion, 2 blocked tickets

[THOUGHT] Good progress. Now checking security vulnerabilities
[ACTION] get_security_scan → Git/CI Agent  
[OBSERVE] Received: Risk score 25/100, 0 critical, 2 high

[THOUGHT] Need to verify build pipeline status
[ACTION] get_build_status → Git/CI Agent
[OBSERVE] Received: Build #142 SUCCESS, 245 tests passed

[FINAL] Synthesizing Go/No-Go decision...
```

### Script Notes
- Use syntax highlighting in logs
- Add subtle animations as each step appears
- Show the tool calls connecting to different agents

---

## Scene 4: Agent Execution (1:15 - 1:45)

### Visual
- Focus on one agent: Jira Agent updating a ticket
- Show the API call and response

### Voiceover

> "Each specialized agent handles its domain. Here, the Jira Agent is fetching the complete ticket hierarchy for our release epic - from stories down to subtasks."

### On-Screen Action

1. Show Jira Agent logs:
```
[JIRA-AGENT] Fetching hierarchy for PROJ-100
[JIRA-AGENT] Found 3 stories, 12 subtasks
[JIRA-AGENT] Calculating completion metrics...
```

2. Show a brief view of a Jira ticket being accessed

### Alternative: Show Block Kit Modal

If demonstrating the update flow:
1. User triggers `/jira-update`
2. Modal opens with fields
3. User fills in: "PROJ-105", Status: "Done", Comment: "Verified fix"
4. Submit and show success message

---

## Scene 5: The Final Report (1:45 - 2:15)

### Visual
- Full-screen: Release Readiness Report in Confluence
- Slowly scroll through the report

### Voiceover

> "And here's the result - a beautiful, comprehensive release readiness report. The GO decision is clear, with detailed metrics, a checklist of criteria, and any risks identified. This report is automatically published to Confluence for team visibility."

### On-Screen Action

1. Show the report header with GO decision badge (green)
2. Scroll past the stats grid:
   - 93.3% Ticket Completion ✓
   - 85.5% Test Coverage ✓
   - 25/100 Security Risk ✓
   - 95.5% Build Success ✓
3. Show the checklist with checkmarks
4. Show the risks section (2 high-severity vulns noted)
5. Show the Confluence URL in the browser

### Script Highlight
```
🟢 GO - Release Approved

All critical criteria met:
✅ Ticket completion >= 90%
✅ Test coverage >= 80%  
✅ No critical vulnerabilities
✅ CI pipeline green
```

---

## Scene 6: Response in Slack (2:15 - 2:30)

### Visual
- Back to Slack
- Rich Block Kit message with the summary

### Voiceover

> "The summary is delivered right back to Slack with rich formatting. Team members can see the decision at a glance, with links to the full report and any action items."

### On-Screen Action

Show the Slack message with:
- Header: "✅ Release Readiness: v2.0"
- Stats in organized sections
- "View Full Report" button
- Context footer with timestamp

---

## Scene 7: Closing (2:30 - 2:45)

### Visual
- Grafana dashboard showing metrics
- Zoom out to show all panels

### Voiceover

> "Nexus provides full observability into every operation - LLM usage, agent performance, and business metrics like release decisions. That's Nexus: intelligent release automation that gives you confidence to ship."

### On-Screen Action

1. Show Grafana dashboard
2. Highlight key panels:
   - LLM token usage
   - Agent latency
   - Go/No-Go decision count
3. Fade to logo/end screen

---

## End Card (2:45 - 3:00)

### Visual
- Nexus logo centered
- GitHub URL below
- "Get Started Today" CTA

### Text on Screen

```
NEXUS
Multi-Agent Release Automation

github.com/IKRedHat/Nexus-Release-Readiness-Bot

Get Started Today →
```

---

## Production Notes

### Recording Setup

1. **Screen Resolution:** 1920x1080
2. **Font Size:** Increase terminal/IDE fonts to 16pt for readability
3. **Theme:** Use dark theme for consistency
4. **Browser:** Chrome with clean profile, no extensions visible

### Audio

- Record voiceover separately
- Background music: Subtle, tech-forward (royalty-free)
- Sound effects: Subtle keyboard clicks, notification sounds

### Editing

- Use smooth transitions between scenes
- Add subtle zoom effects on important elements
- Include lower-thirds for scene titles
- Add progress indicator for video length

### Assets Needed

1. Nexus logo (SVG/PNG)
2. Slack workspace with demo data
3. Sample Jira tickets
4. Configured Grafana dashboard
5. Terminal with colored log output

---

## Demo Data Setup

Before recording, ensure:

1. **Jira**: Create demo project "PROJ" with sample tickets
2. **GitHub**: Have a repo with mock PR and passing CI
3. **Slack**: Bot installed in demo workspace
4. **Grafana**: Dashboard imported with sample data
5. **Mock Mode**: Agents running in mock mode with realistic data

---

## Key Messages to Convey

1. ✅ **Natural Language** - Just ask in plain English
2. ✅ **Intelligent Reasoning** - Shows its thinking process
3. ✅ **Multi-Source Integration** - Connects all your tools
4. ✅ **Beautiful Reports** - Professional, actionable output
5. ✅ **Full Observability** - Know what's happening at all times
