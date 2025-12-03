# 🚀 Nexus Admin Dashboard - Frontend Deployment Guide

<div align="center">
  <img src="assets/nexus-logo.png" alt="Nexus Logo" width="120" />
  <br />
  <strong>Complete Guide to Deploying the Nexus Admin Dashboard</strong>
  <br />
  <em>Version 2.3.0 | Last Updated: December 2025</em>
</div>

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Deployment Options](#deployment-options)
5. [Manual Deployment to Vercel](#manual-deployment-to-vercel)
6. [Automated Deployment](#automated-deployment)
7. [Environment Configuration](#environment-configuration)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

---

## 🎯 Overview

The **Nexus Admin Dashboard** is a React-based single-page application (SPA) that serves as the central management interface for the Nexus Release Readiness platform. It provides:

- **Real-time Health Monitoring** - Track all agent statuses at a glance
- **Configuration Management** - Switch between mock and live modes
- **Observability Dashboard** - Integrated metrics, charts, and external tool links
- **Release Management** - Track releases, milestones, and readiness metrics

<div align="center">
  <img src="assets/mockups/admin-dashboard.svg" alt="Admin Dashboard Overview" width="800" />
  <br />
  <em>Figure 1: Nexus Admin Dashboard - Main Interface</em>
</div>

---

## 🔧 Prerequisites

Before deploying, ensure you have:

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 18.x or 20.x | JavaScript runtime |
| npm | 9.x+ | Package manager |
| Git | 2.x+ | Version control |
| Vercel CLI | 32.x+ | Deployment tool |

### Required Accounts

- **GitHub Account** - For repository access
- **Vercel Account** - For hosting (free tier available)
- **Backend API** - Running Nexus backend services

### Verify Prerequisites

```bash
# Check Node.js version
node --version  # Should be v18.x or v20.x

# Check npm version
npm --version   # Should be 9.x+

# Check Git version
git --version   # Should be 2.x+

# Install Vercel CLI globally
npm install -g vercel

# Verify Vercel CLI
vercel --version
```

---

## 🏗️ Architecture

### Frontend Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Nexus Admin Dashboard                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   React 18  │  │ TypeScript  │  │    Tailwind CSS     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Vite     │  │  Recharts   │  │   React Router      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Build Output (dist/)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │index.html│  │ CSS/JS   │  │  Assets  │  │ Manifest │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Vercel Edge                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │ CDN (Global) │  │  SSL/HTTPS   │  │ API Rewrites   │    │
│  └──────────────┘  └──────────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Nexus Backend API                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Admin Dashboard API (Port 8088) → All Agent Services  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Pages

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="assets/mockups/admin-dashboard-config.svg" alt="Configuration" width="350" />
        <br /><strong>Configuration Page</strong>
      </td>
      <td align="center">
        <img src="assets/mockups/admin-observability.svg" alt="Observability" width="350" />
        <br /><strong>Observability Dashboard</strong>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img src="assets/mockups/admin-releases.svg" alt="Releases" width="350" />
        <br /><strong>Release Management</strong>
      </td>
      <td align="center">
        <img src="assets/mockups/grafana-dashboard.svg" alt="Grafana" width="350" />
        <br /><strong>Grafana Integration</strong>
      </td>
    </tr>
  </table>
</div>

---

## 🚀 Deployment Options

| Method | Best For | Complexity | Time |
|--------|----------|------------|------|
| **Vercel CLI** | Quick deployments | ⭐ Easy | 5 min |
| **Vercel Dashboard** | Visual management | ⭐ Easy | 10 min |
| **GitHub Integration** | CI/CD pipelines | ⭐⭐ Medium | 15 min |
| **Python Script** | Automated workflows | ⭐⭐ Medium | 5 min |

---

## 📦 Manual Deployment to Vercel

### Step 1: Clone and Navigate

```bash
# Clone the repository (if not already done)
git clone https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git

# Navigate to the frontend directory
cd Nexus-Release-Readiness-Bot/services/admin_dashboard/frontend
```

### Step 2: Install Dependencies

```bash
# Install all dependencies
npm install --legacy-peer-deps

# Verify installation
npm list --depth=0
```

**Expected Output:**

```
nexus-admin-dashboard@2.3.0
├── axios@1.6.0
├── clsx@2.0.0
├── date-fns@2.30.0
├── lucide-react@0.294.0
├── react@18.2.0
├── react-dom@18.2.0
├── react-router-dom@6.20.0
└── recharts@2.10.0
```

### Step 3: Configure Environment

Create a `.env.local` file for local development:

```bash
# Create environment file
cat > .env.local << 'EOF'
# Backend API URL
VITE_API_URL=http://localhost:8088

# Application Settings
VITE_APP_NAME=Nexus Admin Dashboard
VITE_APP_VERSION=2.3.0

# Observability URLs
VITE_GRAFANA_URL=http://localhost:3000
VITE_PROMETHEUS_URL=http://localhost:9090
VITE_JAEGER_URL=http://localhost:16686
EOF
```

### Step 4: Build for Production

```bash
# Run production build
npm run build:prod

# Verify build output
ls -la dist/
```

**Expected Build Structure:**

```
dist/
├── assets/
│   ├── css/
│   │   └── index-[hash].css
│   ├── images/
│   │   └── [images]
│   └── js/
│       ├── index-[hash].js
│       ├── react-vendor-[hash].js
│       ├── chart-vendor-[hash].js
│       └── utils-vendor-[hash].js
├── index.html
└── vite.svg
```

### Step 5: Login to Vercel

```bash
# Login to Vercel (opens browser for authentication)
vercel login

# Verify login
vercel whoami
```

### Step 6: Deploy to Vercel

#### Option A: Interactive Deployment

```bash
# Start deployment wizard
vercel

# Answer prompts:
# ? Set up and deploy? [Y/n] Y
# ? Which scope? Your username or team
# ? Link to existing project? [y/N] N
# ? What's your project name? nexus-admin-dashboard
# ? In which directory is your code located? ./
# ? Want to modify settings? [y/N] N
```

#### Option B: Direct Production Deployment

```bash
# Deploy directly to production
vercel deploy --prod

# Or use npm script
npm run vercel:deploy:prod
```

### Step 7: Configure Environment Variables

After initial deployment, set environment variables:

```bash
# Set production API URL
vercel env add VITE_API_URL production
# Enter: https://your-backend-api.example.com

# Set app name
vercel env add VITE_APP_NAME production
# Enter: Nexus Admin Dashboard

# Set version
vercel env add VITE_APP_VERSION production
# Enter: 2.3.0

# Redeploy with new environment variables
vercel deploy --prod
```

### Step 8: Configure Custom Domain (Optional)

```bash
# Add custom domain
vercel domains add nexus-dashboard.yourdomain.com

# Verify DNS configuration
vercel domains inspect nexus-dashboard.yourdomain.com
```

---

## ⚙️ Automated Deployment

### Using the Python Deployment Script

We provide a comprehensive Python script for automated deployments:

```bash
# Navigate to scripts directory
cd /path/to/Nexus-Release-Readiness-Bot

# Run deployment script
python scripts/deploy_frontend.py --help

# Deploy to preview
python scripts/deploy_frontend.py --env preview

# Deploy to production
python scripts/deploy_frontend.py --env production

# Deploy with custom API URL
python scripts/deploy_frontend.py --env production --api-url https://api.example.com
```

### GitHub Actions CI/CD

Add automatic deployments on push:

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend to Vercel

on:
  push:
    branches: [main]
    paths:
      - 'services/admin_dashboard/frontend/**'

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
          cache-dependency-path: services/admin_dashboard/frontend/package-lock.json
      
      - name: Install Dependencies
        working-directory: services/admin_dashboard/frontend
        run: npm ci --legacy-peer-deps
      
      - name: Build
        working-directory: services/admin_dashboard/frontend
        run: npm run build:prod
        env:
          VITE_API_URL: ${{ secrets.VITE_API_URL }}
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: services/admin_dashboard/frontend
          vercel-args: '--prod'
```

---

## 🔐 Environment Configuration

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_URL` | ✅ Yes | Backend API endpoint | `https://api.nexus.io` |
| `VITE_APP_NAME` | No | Application display name | `Nexus Dashboard` |
| `VITE_APP_VERSION` | No | Current version | `2.3.0` |
| `VITE_GRAFANA_URL` | No | Grafana dashboard URL | `https://grafana.nexus.io` |
| `VITE_PROMETHEUS_URL` | No | Prometheus URL | `https://prometheus.nexus.io` |
| `VITE_JAEGER_URL` | No | Jaeger tracing URL | `https://jaeger.nexus.io` |
| `VITE_ENABLE_MOCK_MODE` | No | Enable mock data | `false` |
| `VITE_ENABLE_DEBUG` | No | Enable debug mode | `false` |

### Setting Variables in Vercel

**Via CLI:**

```bash
# Add single variable
vercel env add VITE_API_URL production

# Add from file
cat .env.production | while read line; do
  [[ $line =~ ^#.*$ ]] && continue
  [[ -z $line ]] && continue
  key=$(echo $line | cut -d= -f1)
  value=$(echo $line | cut -d= -f2-)
  vercel env add $key production <<< "$value"
done
```

**Via Dashboard:**

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Select your project
3. Navigate to **Settings** → **Environment Variables**
4. Add each variable with appropriate scope

<div align="center">
  <img src="assets/mockups/admin-dashboard-config.svg" alt="Environment Config" width="600" />
  <br />
  <em>Figure 2: Configuration Management Interface</em>
</div>

---

## ✅ Post-Deployment Verification

### 1. Verify Deployment Status

```bash
# List recent deployments
vercel ls

# Get deployment details
vercel inspect <deployment-url>
```

### 2. Health Check Endpoints

Test your deployed dashboard:

```bash
# Check if frontend loads
curl -I https://your-deployment-url.vercel.app

# Expected: HTTP/2 200

# Check API connectivity (via proxy)
curl https://your-deployment-url.vercel.app/api/health
```

### 3. Functional Verification Checklist

| Check | Expected Result | Status |
|-------|-----------------|--------|
| Homepage loads | Dashboard displays | ☐ |
| Health page shows agents | All 10 agents listed | ☐ |
| Configuration loads | Settings form visible | ☐ |
| Observability charts | Metrics displayed | ☐ |
| Releases page | Calendar visible | ☐ |
| API calls succeed | No CORS errors | ☐ |

### 4. Performance Verification

```bash
# Run Lighthouse audit
npx lighthouse https://your-deployment-url.vercel.app \
  --output=json \
  --output-path=./lighthouse-report.json

# View scores
cat lighthouse-report.json | jq '.categories | to_entries[] | "\(.key): \(.value.score * 100)%"'
```

**Target Scores:**

| Metric | Target | Minimum |
|--------|--------|---------|
| Performance | 90+ | 80 |
| Accessibility | 95+ | 90 |
| Best Practices | 95+ | 90 |
| SEO | 90+ | 80 |

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue: Build Fails with TypeScript Errors

```bash
# Error: TS2307: Cannot find module '@/components/...'
```

**Solution:** Ensure path aliases are configured in `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"]
    }
  }
}
```

#### Issue: API Calls Return CORS Errors

```bash
# Error: Access to fetch blocked by CORS policy
```

**Solution:** Verify `vercel.json` rewrites are correct and backend allows the Vercel domain:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.com/:path*"
    }
  ]
}
```

#### Issue: Environment Variables Not Available

**Solution:** Ensure variables are prefixed with `VITE_` and redeploy:

```bash
# Variables must start with VITE_
VITE_API_URL=https://api.example.com  # ✅ Correct
API_URL=https://api.example.com       # ❌ Won't be exposed
```

#### Issue: Deployment Stuck or Failed

```bash
# Check deployment logs
vercel logs <deployment-url>

# Force new deployment
vercel deploy --force
```

#### Issue: CSS/Styles Not Loading

**Solution:** Check build output and verify asset paths:

```bash
# Rebuild with verbose output
npm run build -- --debug

# Check if CSS file exists in dist
ls -la dist/assets/css/
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
vercel env add VITE_ENABLE_DEBUG production <<< "true"

# Redeploy
vercel deploy --prod
```

---

## 🔒 Security Best Practices

### 1. Environment Variables

- ✅ Never commit `.env` files to Git
- ✅ Use Vercel's encrypted environment variables
- ✅ Rotate API keys regularly
- ✅ Use different keys for preview/production

### 2. Content Security Policy

The `vercel.json` includes security headers:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" }
      ]
    }
  ]
}
```

### 3. API Security

- ✅ Backend should validate all requests
- ✅ Use HTTPS for all API communications
- ✅ Implement rate limiting on backend
- ✅ Validate CORS origins on backend

### 4. Dependency Security

```bash
# Audit dependencies regularly
npm audit

# Fix vulnerabilities
npm audit fix

# Check for updates
npm outdated
```

---

## 📚 Additional Resources

### Documentation Links

- [Vercel Documentation](https://vercel.com/docs)
- [Vite Configuration](https://vitejs.dev/config/)
- [React Router](https://reactrouter.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Related Nexus Documentation

- [Architecture Overview](architecture.md)
- [Admin Dashboard Guide](admin-dashboard.md)
- [Admin Dashboard Tutorial](admin-dashboard-tutorial.md)
- [API Testing Guide](api-testing-guide.md)

### Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review [GitHub Issues](https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/issues)
3. Join our Slack community

---

<div align="center">
  <strong>🎉 Congratulations!</strong>
  <br />
  Your Nexus Admin Dashboard is now deployed and ready to use.
  <br /><br />
  <img src="assets/mockups/admin-dashboard.svg" alt="Success" width="600" />
</div>

---

*Last updated: December 2025 | Nexus v2.3.0*

