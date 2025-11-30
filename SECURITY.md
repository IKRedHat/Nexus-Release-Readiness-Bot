# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Nexus seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please Do NOT

- ❌ Open a public GitHub issue for security vulnerabilities
- ❌ Disclose the vulnerability publicly before it's fixed
- ❌ Exploit the vulnerability for malicious purposes

### Please DO

- ✅ Email us at **security@example.com**
- ✅ Provide detailed information about the vulnerability
- ✅ Allow reasonable time for us to respond and fix the issue

## What to Include in Your Report

To help us triage and prioritize your report, please include:

1. **Type of vulnerability** (e.g., SQL injection, XSS, authentication bypass)
2. **Affected component** (e.g., orchestrator, jira-agent, slack-agent)
3. **Steps to reproduce** the vulnerability
4. **Potential impact** of the vulnerability
5. **Suggested fix** (if you have one)
6. **Your contact information** for follow-up

### Example Report

```
Subject: [SECURITY] SQL Injection in Jira Agent Search Endpoint

Type: SQL Injection
Component: services/agents/jira_agent/main.py
Affected Endpoint: GET /search

Description:
The JQL parameter in the search endpoint is not properly sanitized,
allowing an attacker to inject malicious SQL queries.

Steps to Reproduce:
1. Send GET request to /search?jql=project=PROJ' OR '1'='1
2. Observe that all tickets are returned regardless of permissions

Impact:
- Unauthorized access to ticket data
- Potential data exfiltration
- Privilege escalation

Suggested Fix:
Use parameterized queries or the Jira API's built-in JQL sanitization.

Contact: researcher@example.com
```

## Response Timeline

| Phase | Timeline |
|-------|----------|
| Initial Response | Within 48 hours |
| Vulnerability Confirmation | Within 5 business days |
| Fix Development | Depends on severity |
| Security Advisory | Upon fix release |

## Severity Levels

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical** | Remote code execution, data breach, complete auth bypass | 24-48 hours |
| **High** | Significant data exposure, privilege escalation | 3-5 days |
| **Medium** | Limited data exposure, XSS, CSRF | 1-2 weeks |
| **Low** | Information disclosure, best practice violation | Next release |

## Security Best Practices for Contributors

When contributing to Nexus, please follow these security guidelines:

### Authentication & Authorization

- Never hardcode API keys, tokens, or passwords
- Use environment variables for all secrets
- Implement proper auth checks on all endpoints
- Follow the principle of least privilege

### Data Handling

- Sanitize all user inputs
- Use parameterized queries for database access
- Encrypt sensitive data at rest and in transit
- Never log sensitive information (tokens, passwords, PII)

### Dependencies

- Keep dependencies up to date
- Review security advisories for all dependencies
- Use `pip audit` or `safety` to check for vulnerabilities
- Pin dependency versions in requirements.txt

### Code Review

- All code changes require security-focused review
- Use static analysis tools (bandit, semgrep)
- Test for common vulnerabilities (OWASP Top 10)

## Security Features

Nexus includes the following security features:

| Feature | Description |
|---------|-------------|
| JWT Authentication | Service-to-service authentication |
| Slack Request Verification | Validates Slack request signatures |
| Rate Limiting | Prevents abuse of API endpoints |
| Input Validation | Pydantic models for request validation |
| Audit Logging | Logs security-relevant events |
| HTTPS Only | All production traffic encrypted |

## Security Updates

Security updates are released as:

1. **Patch releases** for the current version
2. **Security advisories** on GitHub
3. **Announcements** in release notes

To receive security notifications:

- Watch the repository for releases
- Enable GitHub security alerts
- Subscribe to our security mailing list

## Acknowledgments

We thank the following security researchers who have helped improve Nexus:

<!-- This section will be updated as researchers are credited -->

- Your name could be here! 🏆

## Contact

- **Security Team**: security@example.com
- **PGP Key**: [Available upon request]
- **Response Time**: Within 48 hours

---

Thank you for helping keep Nexus and its users safe! 🔒

