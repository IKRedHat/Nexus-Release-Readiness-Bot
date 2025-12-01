# Smart Root Cause Analysis (RCA)

The Nexus RCA Agent provides intelligent analysis of failed CI/CD builds by correlating error logs with code changes to automatically identify root causes and suggest fixes.

## Key Features

- **Auto-Trigger on Failures**: Jenkins webhook integration for automatic RCA
- **Slack Notifications**: Sends analysis to release channel with PR owner tagging
- **LLM-Powered Analysis**: Uses Google Gemini 1.5 Pro for deep log analysis
- **Git Correlation**: Maps errors to specific code changes
- **Confidence Scoring**: Rates analysis reliability

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RCA ANALYSIS WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   Jenkins    │     │   GitHub     │     │    Gemini    │                │
│  │  Build Logs  │     │   Git Diff   │     │     LLM      │                │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘                │
│         │                    │                    │                         │
│         └────────────────────┼────────────────────┘                         │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────────┐                                  │
│                    │     RCA Agent       │                                  │
│                    │  ┌───────────────┐  │                                  │
│                    │  │ 1. Fetch Logs │  │                                  │
│                    │  │ 2. Parse Errors│  │                                  │
│                    │  │ 3. Get Git Diff│  │                                  │
│                    │  │ 4. LLM Analysis│  │                                  │
│                    │  │ 5. Generate Fix│  │                                  │
│                    │  └───────────────┘  │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │   RCA Analysis      │                                  │
│                    │  • Root Cause       │                                  │
│                    │  • Suspected File   │                                  │
│                    │  • Fix Suggestion   │                                  │
│                    │  • Confidence Score │                                  │
│                    └─────────────────────┘                                  │
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

Uses Google Gemini (1.5 Pro) for intelligent analysis:

- Correlates error logs with code changes
- Identifies root cause with confidence score
- Suggests specific code fixes
- Provides additional recommendations

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

```
┌────────────────────────────────────────────────────────────────┐
│  🔍 Build Failure Analysis                                      │
│                                                                  │
│  Analysis ID: rca-nexus-main-142-1732976400                     │
│  Build: http://jenkins:8080/job/nexus-main/142/                 │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  🧪 Error Type: Test Failure                                    │
│                                                                  │
│  Root Cause:                                                     │
│  Test failure in TestUserService.test_validate_email due to     │
│  validate_user_email() returning None instead of ValidationResult│
│                                                                  │
│  🟢 Confidence: 92% (high)    Suspected Author: @john.doe       │
│                                                                  │
│  📁 Suspected Files:                                            │
│  • src/api/users.py (lines: 87, 88, 89)                        │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  💡 Suggested Fix:                                              │
│  Add null check before accessing is_valid attribute...          │
│                                                                  │
│  ```python                                                       │
│  if result is not None:                                          │
│      return result.is_valid                                      │
│  ```                                                             │
│                                                                  │
│  [📋 View Full Analysis]  [🔄 Re-run Analysis]                  │
│                                                                  │
│  💡 Additional: Add type hints | Add edge case tests            │
└────────────────────────────────────────────────────────────────┘
```

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
  "model_used": "gemini-1.5-pro",
  "tokens_used": 1250
}
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Analyze a failed build (with optional notification) |
| `POST` | `/webhook/jenkins` | Jenkins webhook for auto-trigger |
| `POST` | `/execute` | Generic execution (orchestrator) |
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
  
  // Notification options
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
  "model_used": "string (optional)",
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
# RCA request counts (with trigger type)
nexus_rca_requests_total{status="success",error_type="test_failure",trigger="webhook"} 150
nexus_rca_requests_total{status="success",error_type="test_failure",trigger="manual"} 50
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

# LLM token usage (labeled for cost tracking)
nexus_llm_tokens_total{model="gemini-1.5-pro",task_type="rca"} 125000

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
| `GEMINI_API_KEY` | - | Google Gemini API key |
| `RCA_LLM_MODEL` | `gemini-1.5-pro` | LLM model for analysis |
| `LLM_MOCK_MODE` | `true` | Use mock responses |
| `RCA_MAX_LOG_CHARS` | `100000` | Max log characters |
| `RCA_MAX_DIFF_CHARS` | `50000` | Max diff characters |

### Why Gemini 1.5 Pro?

We recommend Gemini 1.5 Pro for RCA because:

- **1M Token Context**: Can handle very large build logs
- **Strong Code Understanding**: Excellent at correlating errors with code
- **Cost Effective**: Competitive pricing for large inputs
- **Fast Response**: Good latency for interactive use

## Orchestrator Integration

The RCA agent is automatically available to the Nexus orchestrator:

### Trigger Phrases

The orchestrator will route these queries to the RCA agent:

- "Why did the build fail?"
- "What caused the failure in job X?"
- "Diagnose the error in build #142"
- "Debug the last build"
- "Analyze build failure"

### Tool Registration

```python
# In react_engine.py
"analyze_build_failure": Tool(
    name="analyze_build_failure",
    description="Analyze a failed Jenkins build to determine root cause...",
    agent_type="rca",
    endpoint="/analyze",
    method="POST",
    required_params=["job_name", "build_number"]
)
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

### 4. Track Costs

Monitor `nexus_llm_tokens_total{task_type="rca"}` to track analysis costs.

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
- Consider using mock mode for testing

### Missing Suspected Files

- Ensure GitHub token has repo access
- Check if `commit_sha` or `pr_id` is correct
- Verify the build actually contains code changes

