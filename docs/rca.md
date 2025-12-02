# Smart Root Cause Analysis (RCA)

The Nexus RCA Agent provides intelligent analysis of failed CI/CD builds by correlating error logs with code changes to automatically identify root causes and suggest fixes.

## Key Features

- **Auto-Trigger on Failures**: Jenkins webhook integration for automatic RCA
- **Slack Notifications**: Sends analysis to release channel with PR owner tagging
- **Multi-Provider LLM Support**: Choose from OpenAI, Gemini, Anthropic, Ollama, or Groq
- **MCP Tool Exposure**: Tools available via Model Context Protocol over SSE
- **Git Correlation**: Maps errors to specific code changes
- **Confidence Scoring**: Rates analysis reliability

## What's New in v3.0

### 🧠 LangGraph Integration

The RCA Agent now integrates with the LangGraph orchestrator:

- **Stateful Analysis**: RCA results are persisted in the graph state
- **Human-in-the-Loop**: Optional approval workflow for fix suggestions
- **Tool Binding**: RCA tools are bound to the LangGraph agent via MCP

### 🤖 Multi-Provider LLM Support

RCA now supports multiple LLM providers via the LLM Factory:

| Provider | Model | Best For |
|----------|-------|----------|
| **Google Gemini** | gemini-1.5-pro | Large logs (1M context) |
| **OpenAI** | gpt-4o | High-quality analysis |
| **Anthropic** | claude-3.5-sonnet | Code-focused analysis |
| **Ollama** | codellama | Self-hosted, privacy |
| **Groq** | llama-3.1-70b | Fast inference |

Configure the provider in Admin Dashboard → Configuration → LLM.

### 🔌 MCP Tool Exposure

The RCA Agent exposes tools via MCP over SSE:

| Tool | Description |
|------|-------------|
| `analyze_build_failure` | Analyze a failed build and generate RCA |
| `get_build_logs` | Fetch build logs from Jenkins |
| `get_commit_changes` | Get git diff for a commit or PR |
| `get_rca_history` | Get historical RCA analyses |

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RCA ANALYSIS WORKFLOW (v3.0)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   Jenkins    │     │   GitHub     │     │  LLM Factory │                │
│  │  Build Logs  │     │   Git Diff   │     │  (Dynamic)   │                │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘                │
│         │                    │                    │                         │
│         └────────────────────┼────────────────────┘                         │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────────┐                                  │
│                    │     RCA Agent       │                                  │
│                    │  MCP Server :8006   │                                  │
│                    │  ┌───────────────┐  │                                  │
│                    │  │ 1. Fetch Logs │  │                                  │
│                    │  │ 2. Parse Errors│  │                                  │
│                    │  │ 3. Get Git Diff│  │                                  │
│                    │  │ 4. LLM Analysis│  │                                  │
│                    │  │ 5. Generate Fix│  │                                  │
│                    │  └───────────────┘  │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│                    ┌──────────┼──────────┐                                  │
│                    │          │          │                                  │
│                    ▼          ▼          ▼                                  │
│            ┌───────────┐ ┌─────────┐ ┌─────────────┐                       │
│            │ LangGraph │ │  Slack  │ │  PostgreSQL │                       │
│            │ StateGraph│ │Notifier │ │   State     │                       │
│            └───────────┘ └─────────┘ └─────────────┘                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

### 🔍 Intelligent Log Analysis

The RCA Agent intelligently processes build logs:

1. **Log Truncation**: Large logs are smartly truncated to fit LLM context windows while preserving:
   - Build initialization (first N lines)
   - Final status (last M lines)
   - All error blocks with surrounding context

2. **Error Pattern Detection**: Automatically detects error patterns for:
   - Python (Traceback, Exception, AssertionError)
   - Java (Exception, BUILD FAILURE, stack traces)
   - JavaScript/Node (TypeError, ReferenceError, npm ERR)
   - Generic CI (FAILURE, ERROR, Exit code)

### 🔗 Git Diff Correlation

Maps errors to specific code changes:

- Fetches commit diffs from GitHub
- Supports PR analysis
- Identifies which file/line likely caused the failure
- Shows relevant code snippets

### 🤖 LLM-Powered Analysis

Uses your configured LLM provider (via LLM Factory) for intelligent analysis:

- Correlates error logs with code changes
- Identifies root cause with confidence score
- Suggests specific code fixes
- Provides additional recommendations

**Recommended Providers for RCA:**

| Provider | Pros | Cons |
|----------|------|------|
| **Gemini 1.5 Pro** | 1M context window, handles huge logs | Slightly slower |
| **GPT-4o** | Best quality analysis | Smaller context, higher cost |
| **Claude 3.5 Sonnet** | Excellent code understanding | Limited availability |
| **Groq (Llama 3.1)** | Ultra-fast analysis | May miss nuances |

## Auto-Trigger on Build Failures

The RCA Agent can automatically analyze failed builds and notify your team via Slack.

### How It Works

```
┌─────────────┐      Webhook       ┌─────────────┐
│   Jenkins   │ ─────────────────▶ │  RCA Agent  │
│ Build Fails │                    │  /webhook/  │
└─────────────┘                    │   jenkins   │
                                   └──────┬──────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │  Analyze &  │
                                   │  Generate   │
                                   │  RCA Report │
                                   └──────┬──────┘
                                          │
                                          ▼
                                   ┌─────────────────────────────────────┐
                                   │         Slack Notification          │
                                   │  #release-notifications             │
                                   │  @pr-owner tagged                   │
                                   │  • Root cause summary               │
                                   │  • Suspected files                  │
                                   │  • Fix suggestion                   │
                                   │  • LLM provider used                │
                                   └─────────────────────────────────────┘
```

### Configuring Jenkins Webhook

1. Install the **Generic Webhook Trigger** plugin in Jenkins
2. Configure your pipeline:

```groovy
pipeline {
    agent any
    
    stages {
        stage('Build') { ... }
        stage('Test') { ... }
    }
    
    post {
        failure {
            script {
                def payload = [
                    name: env.JOB_NAME,
                    number: env.BUILD_NUMBER,
                    url: env.BUILD_URL,
                    result: currentBuild.result,
                    git_url: env.GIT_URL,
                    git_branch: env.GIT_BRANCH,
                    git_commit: env.GIT_COMMIT,
                    pr_number: env.CHANGE_ID?.toInteger(),
                    pr_author_email: env.CHANGE_AUTHOR_EMAIL,
                    release_channel: '#release-notifications'
                ]
                
                httpRequest(
                    url: 'http://rca-agent:8006/webhook/jenkins',
                    httpMode: 'POST',
                    contentType: 'APPLICATION_JSON',
                    requestBody: groovy.json.JsonOutput.toJson(payload)
                )
            }
        }
    }
}
```

### Slack Notification Example

When a build fails, the team receives a notification like this:

![RCA Slack Notification](assets/mockups/slack-rca-notification.svg)

The notification includes:
- **Error Type**: Color-coded badge (🧪 Test, 🔧 Compilation, 📦 Dependency)
- **Root Cause**: AI-generated summary of the failure
- **Confidence Score**: How sure the analysis is (🟢 high / 🟡 medium / 🔴 low)
- **@PR Owner**: Tagged so they get notified immediately
- **Suspected Files**: With specific line numbers
- **Fix Suggestion**: Actionable recommendation
- **LLM Used**: Shows which provider generated the analysis
- **Action Buttons**: View full analysis or re-run

### Environment Variables for Auto-Trigger

| Variable | Default | Description |
|----------|---------|-------------|
| `RCA_AUTO_ANALYZE` | `true` | Enable auto-analysis on webhooks |
| `SLACK_AGENT_URL` | `http://slack-agent:8084` | Slack agent URL |
| `SLACK_RELEASE_CHANNEL` | `#release-notifications` | Default notification channel |
| `SLACK_NOTIFY_ON_FAILURE` | `true` | Send Slack notifications |
| `SLACK_MOCK_MODE` | `true` | Use mock Slack (for testing) |

## Quick Start

### Via Natural Language (Slack)

```
User: Why did the last build fail?

Nexus: 🔍 Analyzing build nexus-main #142...

Root Cause Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Summary: Test failure in TestUserService.test_validate_email 
   due to validate_user_email() returning None instead of 
   ValidationResult when email format check fails.

🎯 Confidence: 92% (HIGH)

📁 Suspected File: src/api/users.py
   Lines: 87-89

🔧 Suggested Fix:
   def validate_user_email(self, email: str) -> ValidationResult:
       if not email:
           return ValidationResult(is_valid=False, error="Empty email")
       # ... rest of method

💡 Additional Recommendations:
   • Add type hints to ensure consistent return types
   • Consider adding more edge case tests

🤖 Analyzed by: OpenAI gpt-4o
```

### Via API

```bash
curl -X POST http://localhost:8006/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "nexus-main",
    "build_number": 142,
    "repo_name": "nexus-backend",
    "include_git_diff": true
  }'
```

### Via MCP Tool Call (LangGraph)

```python
# The LangGraph orchestrator calls RCA tools via MCP
tools = await mcp_client.get_tools()
rca_tool = tools["analyze_build_failure"]

result = await rca_tool.invoke({
    "job_name": "nexus-main",
    "build_number": 142,
    "include_git_diff": True
})
```

### Response

```json
{
  "analysis_id": "rca-nexus-main-142-1732976400",
  "root_cause_summary": "Test failure in test_validate_email due to validate_user_email() returning None instead of ValidationResult",
  "error_type": "test_failure",
  "error_message": "AttributeError: 'NoneType' object has no attribute 'is_valid'",
  "confidence_score": 0.92,
  "confidence_level": "high",
  "suspected_commit": "a1b2c3d4e5f6789",
  "suspected_author": "developer@example.com",
  "suspected_files": [
    {
      "file_path": "src/api/users.py",
      "change_type": "modified",
      "lines_added": 6,
      "lines_deleted": 1,
      "relevant_lines": [87, 88, 89]
    }
  ],
  "fix_suggestion": "The validate_user_email method returns None when the email is invalid or empty, but the test expects a ValidationResult object. Modify the method to always return a ValidationResult object.",
  "fix_code_snippet": "def validate_user_email(self, email: str) -> ValidationResult:\n    if not email:\n        return ValidationResult(is_valid=False, error=\"Email cannot be empty\")\n    ...",
  "additional_recommendations": [
    "Add type hints to ensure consistent return types",
    "Consider adding more edge case tests for email validation",
    "The error logging should not replace proper return values"
  ],
  "analyzed_at": "2025-11-30T14:30:00Z",
  "analysis_duration_seconds": 3.45,
  "llm_provider": "openai",
  "model_used": "gpt-4o",
  "tokens_used": 1250
}
```

## MCP Server Interface

The RCA Agent runs as an MCP server on port 8006, exposing tools via SSE:

### Available Tools

| Tool | Description | Required Params |
|------|-------------|-----------------|
| `analyze_build_failure` | Perform full RCA analysis | `job_name`, `build_number` |
| `get_build_logs` | Fetch raw build logs | `job_name`, `build_number` |
| `get_commit_changes` | Get git diff | `repo`, `commit_sha` or `pr_id` |
| `get_rca_history` | Get past analyses | `job_name` (optional) |

### Connecting to RCA MCP Server

```python
from nexus_lib.mcp import MCPClientConnection

# Connect to RCA agent
rca_client = MCPClientConnection("rca", "http://rca-agent:8006/sse")
await rca_client.connect()

# List available tools
tools = await rca_client.list_tools()
print(tools)  # ['analyze_build_failure', 'get_build_logs', ...]

# Call a tool
result = await rca_client.call_tool("analyze_build_failure", {
    "job_name": "nexus-main",
    "build_number": 142
})
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Analyze a failed build (with optional notification) |
| `POST` | `/webhook/jenkins` | Jenkins webhook for auto-trigger |
| `GET` | `/sse` | MCP SSE endpoint for tool exposure |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |

### Webhook Endpoint

```http
POST /webhook/jenkins
Content-Type: application/json

{
  "name": "nexus-main",
  "number": 142,
  "url": "http://jenkins:8080/job/nexus-main/142/",
  "result": "FAILURE",
  "git_url": "https://github.com/org/repo.git",
  "git_branch": "feature/new-api",
  "git_commit": "a1b2c3d4e5f6",
  "pr_number": 123,
  "pr_author_email": "developer@example.com",
  "release_channel": "#release-notifications"
}
```

**Response:**
```json
{
  "status": "queued",
  "message": "RCA analysis queued, Slack notification will be sent",
  "job": "nexus-main",
  "build": 142,
  "channel": "#release-notifications"
}
```

### Request Schema

```json
{
  "job_name": "string (required)",
  "build_number": "integer (required)",
  "build_url": "string (optional)",
  "repo_name": "string (optional)",
  "branch": "string (optional)",
  "pr_id": "integer (optional)",
  "commit_sha": "string (optional)",
  "include_git_diff": "boolean (default: true)",
  "include_test_output": "boolean (default: true)",
  "max_log_lines": "integer (default: 5000)",
  
  "notify": "boolean (default: false)",
  "channel": "string (optional, uses SLACK_RELEASE_CHANNEL if not set)",
  "pr_owner_email": "string (optional, for Slack user tagging)"
}
```

### Response Schema

```json
{
  "analysis_id": "string",
  "root_cause_summary": "string",
  "error_type": "compilation_error | test_failure | dependency_error | configuration_error | infrastructure_error | timeout_error | unknown",
  "error_message": "string",
  "confidence_score": "float (0.0-1.0)",
  "confidence_level": "high | medium | low | uncertain",
  "suspected_commit": "string (optional)",
  "suspected_author": "string (optional)",
  "suspected_files": [
    {
      "file_path": "string",
      "change_type": "added | modified | deleted",
      "lines_added": "integer",
      "lines_deleted": "integer",
      "relevant_lines": "[integer]",
      "code_snippet": "string (optional)"
    }
  ],
  "test_failures": [
    {
      "test_name": "string",
      "test_class": "string (optional)",
      "error_message": "string",
      "stack_trace": "string (optional)"
    }
  ],
  "error_log_excerpt": "string",
  "fix_suggestion": "string",
  "fix_code_snippet": "string (optional)",
  "additional_recommendations": "[string]",
  "analyzed_at": "datetime",
  "analysis_duration_seconds": "float",
  "llm_provider": "string",
  "model_used": "string",
  "tokens_used": "integer"
}
```

## Error Types

| Type | Description | Example |
|------|-------------|---------|
| `compilation_error` | Code failed to compile | Missing imports, syntax errors |
| `test_failure` | Unit/integration test failed | Assertion failures, exceptions in tests |
| `dependency_error` | Package installation issues | Missing modules, version conflicts |
| `configuration_error` | Config file issues | Invalid YAML, missing env vars |
| `infrastructure_error` | CI/CD infrastructure problems | Docker issues, network errors |
| `timeout_error` | Build or test timeout | Long-running tests |
| `unknown` | Unable to categorize | Unusual failures |

## Confidence Levels

| Level | Score Range | Meaning |
|-------|-------------|---------|
| `high` | 0.8 - 1.0 | Very confident, clear correlation |
| `medium` | 0.5 - 0.8 | Likely cause, some uncertainty |
| `low` | 0.3 - 0.5 | Possible cause, limited evidence |
| `uncertain` | 0.0 - 0.3 | Unclear, manual review needed |

## Prometheus Metrics

```prometheus
# RCA request counts (with trigger type and provider)
nexus_rca_requests_total{status="success",error_type="test_failure",trigger="webhook",llm_provider="openai"} 150
nexus_rca_requests_total{status="success",error_type="test_failure",trigger="manual",llm_provider="gemini"} 50
nexus_rca_requests_total{status="error",error_type="exception",trigger="webhook"} 5

# Jenkins webhook counts
nexus_rca_webhooks_total{job_name="nexus-main",status="queued"} 200
nexus_rca_webhooks_total{job_name="nexus-main",status="skipped"} 50

# Slack notification counts
nexus_rca_notifications_total{channel="#release-notifications",status="success"} 180
nexus_rca_notifications_total{channel="#release-notifications",status="error"} 5

# Analysis duration
nexus_rca_duration_seconds_bucket{job_name="nexus-main",le="5.0"} 120
nexus_rca_duration_seconds_bucket{job_name="nexus-main",le="10.0"} 145

# Confidence score distribution
nexus_rca_confidence_score_bucket{le="0.5"} 20
nexus_rca_confidence_score_bucket{le="0.8"} 100
nexus_rca_confidence_score_bucket{le="1.0"} 150

# LLM token usage (labeled by provider and task)
nexus_llm_tokens_total{provider="openai",model="gpt-4o",task_type="rca"} 125000
nexus_llm_tokens_total{provider="google",model="gemini-1.5-pro",task_type="rca"} 80000

# MCP tool calls
nexus_mcp_tool_calls_total{server="rca",tool="analyze_build_failure",status="success"} 200

# Active analyses
nexus_rca_active_analyses 2
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JENKINS_URL` | `http://jenkins:8080` | Jenkins server URL |
| `JENKINS_USERNAME` | - | Jenkins username |
| `JENKINS_API_TOKEN` | - | Jenkins API token |
| `JENKINS_MOCK_MODE` | `true` | Use mock data |
| `GITHUB_TOKEN` | - | GitHub personal access token |
| `GITHUB_ORG` | - | GitHub organization |
| `GITHUB_MOCK_MODE` | `true` | Use mock data |
| `RCA_MAX_LOG_CHARS` | `100000` | Max log characters |
| `RCA_MAX_DIFF_CHARS` | `50000` | Max diff characters |

### LLM Configuration (via Admin Dashboard)

Configure in Admin Dashboard → Configuration → LLM:

| Setting | Description |
|---------|-------------|
| `nexus:config:llm_provider` | LLM provider (openai, google, anthropic, etc.) |
| `nexus:config:llm_model` | Model name |
| `nexus:config:openai_api_key` | OpenAI API key |
| `nexus:config:gemini_api_key` | Google Gemini API key |
| `nexus:config:anthropic_api_key` | Anthropic API key |

### Recommended LLM Settings for RCA

For best RCA results, we recommend:

**Large Logs (> 50K chars):**
- Provider: `google`
- Model: `gemini-1.5-pro`
- Reason: 1M token context window

**Highest Quality:**
- Provider: `openai`
- Model: `gpt-4o`
- Reason: Best reasoning for complex failures

**Fast Turnaround:**
- Provider: `groq`
- Model: `llama-3.1-70b-versatile`
- Reason: Sub-second inference

## Orchestrator Integration

The RCA agent is automatically available to the LangGraph orchestrator via MCP:

### Trigger Phrases

The orchestrator will route these queries to the RCA agent:

- "Why did the build fail?"
- "What caused the failure in job X?"
- "Diagnose the error in build #142"
- "Debug the last build"
- "Analyze build failure"

### LangGraph Tool Binding

```python
# In graph.py - tools are automatically discovered via MCP
mcp_client = MCPClientManager()
await mcp_client.connect_all()

tools = mcp_client.get_langchain_tools()
# Includes: analyze_build_failure, get_build_logs, etc.

llm_with_tools = llm.bind_tools(tools)
```

## Log Truncation Strategy

Large build logs are truncated intelligently:

```
┌─────────────────────────────────────────────────────────────┐
│ === BUILD LOG START (first 100 lines) ===                   │
│ [Build initialization, environment info, dependency info]   │
├─────────────────────────────────────────────────────────────┤
│ === EXTRACTED ERROR BLOCKS ===                              │
│ --- Error Block 1 ---                                       │
│ [10 lines context before error]                             │
│ ERROR: Actual error message here                            │
│ Stack trace...                                              │
│ [10 lines context after error]                              │
├─────────────────────────────────────────────────────────────┤
│ [... 5000 lines truncated ...]                              │
├─────────────────────────────────────────────────────────────┤
│ === BUILD LOG END (last 200 lines) ===                      │
│ [Final status, summary, exit code]                          │
└─────────────────────────────────────────────────────────────┘
```

## Best Practices

### 1. Include Git Context

Always provide `repo_name` and `commit_sha` when available:

```json
{
  "job_name": "nexus-main",
  "build_number": 142,
  "repo_name": "nexus-backend",
  "commit_sha": "a1b2c3d4e5f6"
}
```

### 2. Use PRs When Possible

If the build is for a PR, include `pr_id` for better diff context:

```json
{
  "job_name": "nexus-pr-check",
  "build_number": 456,
  "repo_name": "nexus-backend",
  "pr_id": 123
}
```

### 3. Review Low Confidence Results

When confidence is `low` or `uncertain`:
- Review the full build log manually
- Check if the error is in infrastructure vs code
- Consider if this is a flaky test

### 4. Choose Right LLM Provider

- Use **Gemini 1.5 Pro** for very large logs
- Use **GPT-4o** for complex analysis
- Use **Groq** for quick turnaround

### 5. Track Costs

Monitor `nexus_llm_tokens_total{task_type="rca"}` to track analysis costs by provider.

## Troubleshooting

### Analysis Returns "Unknown" Error Type

- Check if the error patterns match supported languages
- Review the raw `error_log_excerpt` in the response
- Consider if it's an infrastructure issue

### Low Confidence Scores

- Ensure git diff is available (check `include_git_diff`)
- The error might be in code not changed in this build
- Could be a flaky test or environment issue

### Timeout During Analysis

- Reduce `max_log_lines` for faster processing
- Check if LLM service is responding
- Switch to a faster provider (Groq)
- Consider using mock mode for testing

### Missing Suspected Files

- Ensure GitHub token has repo access
- Check if `commit_sha` or `pr_id` is correct
- Verify the build actually contains code changes

### LLM Provider Errors

- Verify API key in Admin Dashboard → Configuration → LLM
- Check provider rate limits
- Try switching to a different provider
- Test connection in Admin Dashboard

### MCP Connection Issues

- Verify RCA agent is running: `docker ps | grep rca`
- Check SSE endpoint: `curl http://localhost:8006/health`
- Review agent logs: `docker logs rca-agent`
