# GitHub Repository Setup Guide

This guide covers the recommended GitHub configuration for the Nexus Release Automation repository, including branch protection, discussions, and other settings.

## Table of Contents

- [Branch Protection Rules](#branch-protection-rules)
- [GitHub Discussions](#github-discussions)
- [Repository Settings](#repository-settings)
- [Secrets Configuration](#secrets-configuration)
- [Webhooks](#webhooks)

---

## Branch Protection Rules

### Setting Up Branch Protection

Navigate to: **Settings → Branches → Add branch protection rule**

### Main Branch (`main`)

Create a rule for `main` with these settings:

#### Required Settings ✅

| Setting | Value | Reason |
|---------|-------|--------|
| **Require a pull request before merging** | ✅ Enabled | Prevent direct pushes |
| **Require approvals** | 1 (or 2 for teams) | Code review gate |
| **Dismiss stale pull request approvals** | ✅ Enabled | Re-review after changes |
| **Require review from Code Owners** | ✅ Enabled | Ensure right reviewers |
| **Require status checks to pass** | ✅ Enabled | CI must pass |
| **Require branches to be up to date** | ✅ Enabled | No merge conflicts |
| **Require conversation resolution** | ✅ Enabled | Address all feedback |
| **Require signed commits** | ✅ Enabled | Verify commit authors |
| **Include administrators** | ✅ Enabled | Rules apply to everyone |

#### Required Status Checks

Add these status checks (from CI workflow):

```
✅ Lint & Format
✅ Unit Tests (3.11)
✅ Security Scan
✅ Docker Build
```

#### Example Configuration

```yaml
# Branch protection for 'main'
protection:
  required_pull_request_reviews:
    required_approving_review_count: 1
    dismiss_stale_reviews: true
    require_code_owner_reviews: true
  required_status_checks:
    strict: true
    contexts:
      - "🔍 Lint & Format"
      - "🧪 Unit Tests (3.11)"
      - "🔒 Security Scan"
  enforce_admins: true
  required_signatures: true
  restrictions: null
```

### Develop Branch (`develop`)

For the `develop` branch (if using GitFlow):

| Setting | Value |
|---------|-------|
| Require pull request | ✅ Enabled |
| Require approvals | 1 |
| Require status checks | ✅ Enabled (lint, unit tests) |
| Allow force pushes | ❌ Disabled |

---

## GitHub Discussions

### Enabling Discussions

1. Go to **Settings → General**
2. Scroll to **Features**
3. Check ✅ **Discussions**
4. Click **Set up discussions**

### Recommended Categories

Create these discussion categories:

| Category | Icon | Description | Format |
|----------|------|-------------|--------|
| **📣 Announcements** | 📣 | Official project updates | Announcement |
| **💡 Ideas** | 💡 | Feature suggestions | Open-ended |
| **❓ Q&A** | ❓ | Questions and answers | Question |
| **🙌 Show and Tell** | 🙌 | Share what you've built | Open-ended |
| **💬 General** | 💬 | General conversations | Open-ended |

### Category Descriptions

#### 📣 Announcements
```
Official announcements from the Nexus team.
Subscribe to stay updated on releases, breaking changes, and important news.
```

#### 💡 Ideas
```
Share your ideas for new features or improvements.
Before posting, please search existing ideas to avoid duplicates.
Upvote ideas you'd like to see implemented!
```

#### ❓ Q&A
```
Ask questions about using Nexus.
- Search existing questions first
- Mark answers as "Answered" when resolved
- Include relevant details (version, config, logs)
```

#### 🙌 Show and Tell
```
Share your Nexus integrations, customizations, and success stories!
We love seeing how you use Nexus in your workflows.
```

#### 💬 General
```
General discussions about release automation, DevOps, and related topics.
A place to connect with the community.
```

### Discussions Welcome Message

Add this as a pinned discussion in General:

```markdown
# 👋 Welcome to Nexus Discussions!

We're excited to have you here! This is the place to:

- 💡 **Share ideas** for new features
- ❓ **Ask questions** about using Nexus
- 🙌 **Show off** what you've built
- 💬 **Connect** with the community

## Quick Links

- 📖 [Documentation](../docs/index.md)
- 🚀 [Getting Started](../README.md#-quick-start)
- 🐛 [Report a Bug](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues/new?template=feature_request.md)

## Community Guidelines

- Be respectful and inclusive
- Search before posting
- Provide context and details
- Help others when you can

See our [Code of Conduct](../CODE_OF_CONDUCT.md) for more details.

Happy automating! 🚀
```

---

## Repository Settings

### General Settings

Navigate to: **Settings → General**

| Setting | Recommended Value |
|---------|-------------------|
| **Default branch** | `main` |
| **Features: Wikis** | ❌ Disabled (use /docs instead) |
| **Features: Issues** | ✅ Enabled |
| **Features: Sponsorships** | Optional |
| **Features: Discussions** | ✅ Enabled |
| **Pull Requests: Allow merge commits** | ✅ Enabled |
| **Pull Requests: Allow squash merging** | ✅ Enabled (default) |
| **Pull Requests: Allow rebase merging** | ✅ Enabled |
| **Pull Requests: Default to squash** | ✅ Enabled |
| **Pull Requests: Auto-delete head branches** | ✅ Enabled |

### Merge Button Settings

Recommended default: **Squash and merge**

- Keeps history clean
- PR title becomes commit message
- All PR commits squashed into one

### Security Settings

Navigate to: **Settings → Security**

| Setting | Value |
|---------|-------|
| **Dependency graph** | ✅ Enabled |
| **Dependabot alerts** | ✅ Enabled |
| **Dependabot security updates** | ✅ Enabled |
| **Code scanning** | ✅ Enabled (if available) |
| **Secret scanning** | ✅ Enabled |
| **Push protection** | ✅ Enabled |

---

## Secrets Configuration

### Repository Secrets

Navigate to: **Settings → Secrets and variables → Actions**

#### Required Secrets

| Secret Name | Description | Required For |
|-------------|-------------|--------------|
| `GITHUB_TOKEN` | Auto-provided | CI/CD workflows |

#### Optional Secrets (for full functionality)

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `CODECOV_TOKEN` | Code coverage reporting | [codecov.io](https://codecov.io) |
| `SLACK_WEBHOOK_URL` | Release notifications | Slack App settings |
| `DOCKERHUB_USERNAME` | Docker Hub publishing | Docker Hub account |
| `DOCKERHUB_TOKEN` | Docker Hub publishing | Docker Hub → Security |

### Environment Secrets

For production deployments, create environments:

1. **Settings → Environments → New environment**
2. Create `production` environment
3. Add required reviewers
4. Configure environment secrets

---

## Webhooks

### Recommended Webhooks

| Service | Purpose | Events |
|---------|---------|--------|
| **Slack** | Team notifications | Releases, Issues, PRs |
| **Discord** | Community notifications | Releases |

### Slack Integration

1. Create a Slack App at [api.slack.com](https://api.slack.com/apps)
2. Add Incoming Webhooks
3. Add webhook URL to repository secrets
4. Use in release workflow

---

## Quick Setup Checklist

Use this checklist to configure your repository:

### Branch Protection
- [ ] Create rule for `main` branch
- [ ] Require pull request reviews (1+)
- [ ] Require status checks to pass
- [ ] Enable signed commits
- [ ] Include administrators

### Discussions
- [ ] Enable Discussions feature
- [ ] Create recommended categories
- [ ] Add welcome post

### Security
- [ ] Enable Dependabot alerts
- [ ] Enable Dependabot security updates
- [ ] Enable secret scanning
- [ ] Enable push protection

### Automation
- [ ] Verify CI workflow runs on PRs
- [ ] Verify Dependabot is creating PRs
- [ ] Test release workflow (manual trigger)

### Documentation
- [ ] Verify CONTRIBUTING.md is linked
- [ ] Verify CODE_OF_CONDUCT.md exists
- [ ] Verify SECURITY.md exists

---

## Troubleshooting

### Status Checks Not Appearing

If status checks aren't appearing in branch protection:

1. Ensure CI workflow has run at least once
2. Check workflow name matches exactly
3. Try running workflow manually

### Dependabot Not Working

If Dependabot isn't creating PRs:

1. Verify `.github/dependabot.yml` syntax
2. Check Dependabot is enabled in Security settings
3. Review Dependabot logs in Insights → Dependency graph

### Protected Branch Errors

If you can't push to protected branch:

1. Create a PR instead of direct push
2. Ensure CI checks pass
3. Get required approvals
4. If admin, check "Include administrators" setting

---

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [GitHub Discussions Documentation](https://docs.github.com/en/discussions)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

