# 🚀 Nexus Admin Dashboard - Frontend Deployment Guide

<div align="center">

**Complete Guide to Deploying the Nexus Admin Dashboard**

*Built with Next.js 14 | Optimized for Vercel*

**Version 3.0.0** | **Last Updated:** December 2025

</div>

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Deployment Options](#deployment-options)
5. [Vercel Deployment](#vercel-deployment)
6. [Environment Configuration](#environment-configuration)
7. [GitHub Integration](#github-integration)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

---

## 🎯 Overview

The **Nexus Admin Dashboard** is an enterprise-grade Next.js 14 application providing:

- **Real-time Health Monitoring** - WebSocket-powered live updates
- **Release Management** - Timeline/Gantt views, CRUD operations
- **User & Role Management** - Full RBAC with 30+ permissions
- **Feature Requests** - Voting, comments, Jira integration
- **Dynamic Configuration** - Mode switching, credential management

<div align="center">

```
┌─────────────────────────────────────────────────────────────┐
│                  Next.js 14 Frontend                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ App Router  │  │ Server/     │  │    Tailwind CSS     │  │
│  │   Pages     │  │ Client Comp │  │    + Shadcn/ui      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Vercel Edge Network                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │ Global CDN   │  │  SSL/HTTPS   │  │ Edge Functions │    │
│  └──────────────┘  └──────────────┘  └────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                   Backend API (FastAPI)                      │
│              https://your-api.onrender.com                   │
└─────────────────────────────────────────────────────────────┘
```

</div>

---

## 🔧 Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 18.x or 20.x | JavaScript runtime |
| npm | 9.x+ | Package manager |
| Git | 2.x+ | Version control |
| Vercel CLI | Latest | Deployment tool (optional) |

### Required Accounts

- **GitHub Account** - Repository access
- **Vercel Account** - Hosting (free tier available)
- **Backend API** - Running Nexus backend on Render or similar

### Verify Prerequisites

```bash
# Check versions
node --version   # v18.x or v20.x
npm --version    # 9.x+
git --version    # 2.x+

# Install Vercel CLI (optional)
npm install -g vercel
vercel --version
```

---

## 🏗️ Architecture

### Frontend Stack

| Technology | Purpose |
|------------|---------|
| **Next.js 14** | React framework with App Router |
| **TypeScript** | Type-safe development |
| **Tailwind CSS** | Utility-first styling |
| **Shadcn/ui** | Accessible component library |
| **SWR** | Data fetching with caching |
| **Recharts** | Data visualization |
| **@dnd-kit** | Drag-and-drop functionality |

### Project Structure

```
services/admin_dashboard/frontend-next/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── page.tsx         # Dashboard (home)
│   │   ├── releases/        # Release management
│   │   ├── health/          # Health monitoring
│   │   ├── settings/        # Configuration
│   │   ├── admin/           # User/Role management
│   │   ├── audit-log/       # Audit trail
│   │   └── feature-requests/ # Feature requests
│   ├── components/          # React components
│   │   ├── ui/              # Shadcn/ui components
│   │   ├── layout/          # Layout components
│   │   ├── charts/          # Chart components
│   │   └── ...
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utilities, API client
│   ├── providers/           # Context providers
│   └── types/               # TypeScript definitions
├── public/                  # Static assets
├── next.config.js           # Next.js configuration
├── tailwind.config.js       # Tailwind configuration
├── vercel.json              # Vercel configuration
└── package.json             # Dependencies
```

---

## 🚀 Deployment Options

| Method | Best For | Complexity | Time |
|--------|----------|------------|------|
| **Vercel Dashboard** | Visual management | ⭐ Easy | 5 min |
| **Vercel CLI** | Command-line workflow | ⭐ Easy | 5 min |
| **GitHub Integration** | CI/CD pipelines | ⭐⭐ Medium | 10 min |
| **Docker** | Self-hosted | ⭐⭐ Medium | 15 min |

---

## ☁️ Vercel Deployment

### Option 1: Vercel Dashboard (Recommended)

1. **Push to GitHub**
   ```bash
   git add -A
   git commit -m "deploy: Admin Dashboard v3.0.0"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Click "Import Git Repository"
   - Select your repository
   - Configure project:
     - **Root Directory:** `services/admin_dashboard/frontend-next`
     - **Framework Preset:** Next.js (auto-detected)
     - **Build Command:** `npm run build`
     - **Output Directory:** `.next`

3. **Set Environment Variables**
   - Go to Project Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `https://your-api.onrender.com`

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (~2-3 minutes)

### Option 2: Vercel CLI

```bash
# Navigate to frontend
cd services/admin_dashboard/frontend-next

# Login to Vercel
vercel login

# Deploy preview
vercel

# Deploy to production
vercel --prod

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://your-api.onrender.com
```

### Option 3: One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/IKRedHat/Nexus-Release-Readiness-Bot&root-directory=services/admin_dashboard/frontend-next)

---

## ⚙️ Environment Configuration

### Required Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | Backend API URL | `https://api.nexus.io` |
| `NEXT_PUBLIC_APP_VERSION` | No | Version display | `3.0.0` |

### Setting Variables in Vercel

**Via Dashboard:**
1. Go to Project → Settings → Environment Variables
2. Add variable name and value
3. Select environments: Production, Preview, Development
4. Click Save

**Via CLI:**
```bash
# Add variable
vercel env add NEXT_PUBLIC_API_URL production

# List variables
vercel env ls

# Remove variable
vercel env rm NEXT_PUBLIC_API_URL production
```

### Local Development

Create `.env.local`:

```env
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8088

# App Settings
NEXT_PUBLIC_APP_VERSION=3.0.0
```

---

## 🔗 GitHub Integration

### Automatic Deployments

Vercel automatically deploys:
- **Production:** On push to `main` branch
- **Preview:** On pull requests

### Configure Auto-Deploy

1. Go to Vercel Dashboard → Project → Settings → Git
2. Enable "Auto-deploy" for:
   - Production Branch: `main`
   - Preview Branches: All

### GitHub Actions (Optional)

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - 'services/admin_dashboard/frontend-next/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: services/admin_dashboard/frontend-next/package-lock.json
      
      - name: Install Dependencies
        working-directory: services/admin_dashboard/frontend-next
        run: npm ci
      
      - name: Build
        working-directory: services/admin_dashboard/frontend-next
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: services/admin_dashboard/frontend-next
          vercel-args: '--prod'
```

---

## ✅ Post-Deployment Verification

### 1. Check Deployment Status

```bash
# List deployments
vercel ls

# Get deployment info
vercel inspect <deployment-url>
```

### 2. Verification Checklist

| Check | Expected Result | Status |
|-------|-----------------|--------|
| Homepage loads | Dashboard displays | ☐ |
| Login works | Can authenticate | ☐ |
| API connected | Data fetches | ☐ |
| WebSocket works | Real-time updates | ☐ |
| Theme toggle | Light/Dark works | ☐ |
| Mobile responsive | Displays correctly | ☐ |

### 3. Test API Connectivity

```bash
# Frontend loads
curl -I https://your-app.vercel.app

# API health (via proxy or direct)
curl https://your-app.vercel.app/api/health
```

### 4. Performance Check

Run Lighthouse audit:
```bash
npx lighthouse https://your-app.vercel.app \
  --output=json \
  --output-path=./lighthouse.json
```

**Target Scores:**
| Metric | Target |
|--------|--------|
| Performance | 90+ |
| Accessibility | 95+ |
| Best Practices | 95+ |
| SEO | 90+ |

---

## 🐛 Troubleshooting

### Build Fails

**TypeScript Errors:**
```bash
# Run type check locally first
npm run type-check

# Fix issues, then redeploy
```

**Missing Dependencies:**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

### API Connection Issues

**CORS Errors:**
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend CORS configuration allows your Vercel domain

**Environment Variables Not Loading:**
- Variables must start with `NEXT_PUBLIC_` to be exposed to browser
- Redeploy after adding/changing variables

### Deployment Stuck

```bash
# Force new deployment
vercel --force

# Check deployment logs
vercel logs <deployment-url>
```

### WebSocket Not Connecting

- Ensure backend WebSocket endpoints are available
- Check browser console for connection errors
- Verify no proxy blocking WebSocket upgrade

---

## 🔒 Security Best Practices

### 1. Environment Security

- ✅ Never commit `.env` files
- ✅ Use Vercel's encrypted environment variables
- ✅ Rotate secrets regularly
- ✅ Use different values for preview/production

### 2. Headers Configuration

The `vercel.json` includes security headers:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

### 3. Dependency Security

```bash
# Audit dependencies
npm audit

# Fix vulnerabilities
npm audit fix

# Check for updates
npm outdated
```

---

## 📚 Additional Resources

### Nexus Documentation

- [Admin Dashboard Guide](admin-dashboard.md)
- [Admin Dashboard Tutorial](admin-dashboard-tutorial.md)
- [Architecture Overview](architecture.md)
- [Backend Deployment](runbooks/deployment.md)

### External Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

## 🎉 Quick Deploy Summary

```bash
# 1. Navigate to frontend
cd services/admin_dashboard/frontend-next

# 2. Install dependencies
npm install

# 3. Build (verify locally)
npm run build

# 4. Deploy to Vercel
vercel --prod

# 5. Set API URL in Vercel Dashboard
# NEXT_PUBLIC_API_URL = https://your-api.onrender.com

# 6. Done! 🚀
```

**Your dashboard will be live at:** `https://your-project.vercel.app`

---

*Documentation Version 3.0.0 | Last Updated: December 2025*
