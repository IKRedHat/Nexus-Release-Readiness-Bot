# Nexus Admin Dashboard - Vercel Deployment Guide

> **📋 Consolidated Documentation**  
> This guide combines all Vercel deployment information into a single reference.

---

## Table of Contents

1. [Quick Start (5 Minutes)](#quick-start)
2. [Detailed Configuration](#detailed-configuration)
3. [Environment Variables](#environment-variables)
4. [Auto-Deployment Setup](#auto-deployment-setup)
5. [Troubleshooting](#troubleshooting)
6. [Fresh Deployment (Nuclear Option)](#fresh-deployment)
7. [Verification Checklist](#verification-checklist)

---

## Quick Start

### Deploy in 3 Steps

#### Step 1: Import Repository

1. Go to **https://vercel.com/new**
2. Click **"Import Git Repository"**
3. Select **GitHub** → `IKRedHat/Nexus-Release-Readiness-Bot`

#### Step 2: Configure Project

| Setting | Value |
|---------|-------|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | `services/admin_dashboard/frontend-next` |
| **Build Command** | `next build` (default) |
| **Install Command** | `npm install --legacy-peer-deps` |
| **Node.js Version** | 20.x |

#### Step 3: Add Environment Variables

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_API_URL` | `https://nexus-admin-api.onrender.com` |

Click **"Deploy"** → Wait 2-3 minutes → Done! 🎉

---

## Detailed Configuration

### Build & Development Settings

**Location:** Vercel Dashboard → Project → Settings → General

```
Framework Preset:    Next.js
Root Directory:      services/admin_dashboard/frontend-next
Build Command:       next build
Output Directory:    .next
Install Command:     npm install --legacy-peer-deps
Node.js Version:     20.x
```

### Git Settings

**Location:** Vercel Dashboard → Project → Settings → Git

```
Connected Repository:  IKRedHat/Nexus-Release-Readiness-Bot
Production Branch:     main
Auto-Deploy:           Enabled
Preview Deployments:   Enabled (for PRs)
```

### Deployment Protection (Optional)

**Location:** Vercel Dashboard → Project → Settings → Deployment Protection

```
Vercel Authentication:  Disabled (for public access)
Password Protection:    Disabled
```

---

## Environment Variables

### Required Variables

| Variable | Value | Environments |
|----------|-------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://nexus-admin-api.onrender.com` | Production, Preview, Development |

### How to Add

1. Go to **Settings** → **Environment Variables**
2. Click **"Add New"**
3. Enter key: `NEXT_PUBLIC_API_URL`
4. Enter value: `https://nexus-admin-api.onrender.com`
5. Check ALL environments: ✅ Production, ✅ Preview, ✅ Development
6. Click **"Save"**
7. **Redeploy** to apply changes

### Verify Variables Are Working

Open browser console on deployed site:
```javascript
console.log(process.env.NEXT_PUBLIC_API_URL)
// Should show: https://nexus-admin-api.onrender.com
```

---

## Auto-Deployment Setup

### How It Works

```
Git Push → GitHub Webhook → Vercel API → Build → Deploy
(~30 seconds from push to build start)
```

### Enable Auto-Deploy

1. **Vercel Dashboard** → Your Project → **Settings** → **Git**
2. Verify **"Connected Git Repository"** shows your repo
3. Set **"Production Branch"** to `main`
4. Enable **"Automatically deploy"** (should be ON by default)

### Verify GitHub Webhook

1. Go to: `https://github.com/YOUR_ORG/YOUR_REPO/settings/hooks`
2. Look for Vercel webhook: `https://api.vercel.com/...`
3. Check **Recent Deliveries** → Should show `200 OK` responses

### Test Auto-Deploy

```bash
# Make a small change
echo "# Test $(date)" >> README.md
git add -A && git commit -m "test: Verify auto-deploy"
git push origin main

# Check Vercel Dashboard - should see new deployment within 30 seconds
```

---

## Troubleshooting

### Build Fails with "Module not found"

**Cause:** Root directory not set correctly

**Solution:**
1. Settings → General → Root Directory
2. Set to: `services/admin_dashboard/frontend-next`
3. Redeploy

### Build Fails with Dependency Errors

**Cause:** Missing `--legacy-peer-deps` flag

**Solution:**
1. Settings → General → Install Command
2. Set to: `npm install --legacy-peer-deps`
3. Redeploy

### API Calls Go to Wrong URL

**Cause:** Environment variable not set or wrong name

**Solution:**
1. Variable name MUST be `NEXT_PUBLIC_API_URL` (not `VITE_API_URL`)
2. No trailing slash in URL
3. Applied to all environments
4. Redeploy after adding

### Auto-Deploy Not Working

**Cause:** Git integration broken or webhook missing

**Solution:**
1. Settings → Git → Verify repository is connected
2. Check production branch is `main`
3. Check GitHub webhook exists and shows 200 OK responses
4. If still broken, disconnect and reconnect Git integration

### Vercel Deploys Old Commit

**Cause:** Stale Git connection or cached reference

**Solution:**
1. Go to Settings → Git
2. Click **"Disconnect"**
3. Click **"Connect Git Repository"** again
4. Select your repository
5. Redeploy

### "Commit Author Required" Error

**Cause:** Git email not verified on GitHub

**Solution:**
1. Go to: `https://github.com/settings/emails`
2. Add your email if not listed
3. Verify the email (click link in verification email)
4. Push a new commit

---

## Fresh Deployment

### When to Use

Use this when:
- Auto-deploy is completely broken
- Vercel keeps using old commits
- All troubleshooting steps failed

### Step 1: Save Environment Variables

Before deleting, copy your environment variables from:
**Settings → Environment Variables**

### Step 2: Delete Old Project

1. Settings → scroll to bottom
2. Click **"Delete Project"**
3. Type project name to confirm
4. Click **"Delete"**

### Step 3: Create New Project

1. Go to: `https://vercel.com/new`
2. Import from GitHub
3. Select your repository
4. Configure:
   ```
   Root Directory:    services/admin_dashboard/frontend-next
   Install Command:   npm install --legacy-peer-deps
   ```
5. Add environment variables
6. Deploy

### Step 4: Verify

- First deploy uses latest commit
- Auto-deploy works (test with a push)
- All pages load correctly

---

## Verification Checklist

### After Deployment

- [ ] Production URL is accessible
- [ ] Login page displays correctly
- [ ] Dashboard loads with stats
- [ ] No console errors
- [ ] Mobile view works
- [ ] API calls succeed
- [ ] All navigation works
- [ ] SSL certificate active

### Settings Verification

- [ ] Root Directory: `services/admin_dashboard/frontend-next`
- [ ] Install Command includes `--legacy-peer-deps`
- [ ] Node.js Version: 20.x
- [ ] Production Branch: `main`
- [ ] Environment variables set for all environments
- [ ] Git integration connected

### Auto-Deploy Verification

- [ ] Push a test commit
- [ ] Deployment starts within 30 seconds
- [ ] Uses the latest commit
- [ ] Build succeeds

---

## Quick Reference

### URLs

| Resource | URL |
|----------|-----|
| Vercel Dashboard | https://vercel.com/dashboard |
| New Project | https://vercel.com/new |
| Vercel Status | https://www.vercel-status.com |

### Settings Summary

```yaml
Project:
  Framework: Next.js
  Root: services/admin_dashboard/frontend-next
  Node: 20.x
  
Build:
  Install: npm install --legacy-peer-deps
  Build: next build
  Output: .next

Git:
  Branch: main
  Auto-Deploy: Enabled
  
Environment:
  NEXT_PUBLIC_API_URL: https://nexus-admin-api.onrender.com
```

### Common Commands

```bash
# Test locally
cd services/admin_dashboard/frontend-next
npm install --legacy-peer-deps
npm run dev

# Build locally
npm run build

# Deploy via CLI
npx vercel --prod
```

---

## Performance Expectations

| Metric | Target |
|--------|--------|
| Build Time | < 3 minutes |
| First Load | < 2 seconds |
| Lighthouse Score | 90+ |
| Uptime | 99.9% |

---

**Last Updated:** December 2024  
**Replaces:** DEPLOYMENT_INSTRUCTIONS.md, VERCEL_SETTINGS_CHECKLIST.md, VERCEL_AUTO_DEPLOY.md, VERCEL_FIX_AUTO_DEPLOY.md, VERCEL_FRESH_DEPLOY.md

