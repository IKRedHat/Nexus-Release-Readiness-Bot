# Vercel Auto-Deployment Configuration Guide

## 🎯 Quick Setup - Enable Auto-Deploy from GitHub

### Step 1: Verify Git Integration

1. **Go to Vercel Dashboard:**
   ```
   https://vercel.com/dashboard
   ```

2. **Click on your project** (Nexus Admin Dashboard)

3. **Go to "Settings" tab** (top navigation)

4. **Click "Git" in the sidebar**

### Step 2: Configure Auto-Deployment

#### Option A: If Git is Connected

You should see:
```
✓ Connected to GitHub: IKRedHat/Nexus-Release-Readiness-Bot
```

**Configure these settings:**

1. **Production Branch:** `main`
   - ✅ Deploy every push to `main` branch

2. **Auto Deploy:** ✅ Enabled
   - This should be toggled ON

3. **Ignored Build Step:** Leave empty (or default)

#### Option B: If Git is NOT Connected

1. Click **"Connect Git Repository"**
2. Select **GitHub**
3. Authorize Vercel to access your repos
4. Select: `IKRedHat/Nexus-Release-Readiness-Bot`
5. Click **"Import"**

---

## 🔧 DETAILED CONFIGURATION

### 1. Production Branch Settings

**Location:** Settings → Git → Production Branch

```
Production Branch: main
```

- [x] Deploy every push to `main`
- [x] Create automatic preview deployments for pull requests

### 2. Deploy Hooks (Alternative Method)

If you want manual control over when to deploy:

**Location:** Settings → Git → Deploy Hooks

1. Click **"Create Hook"**
2. Name it: "Manual Deploy"
3. Copy the webhook URL
4. Use this URL to trigger deployments via API/GitHub Actions

---

## 🎬 GITHUB WEBHOOK VERIFICATION

Vercel uses GitHub webhooks for auto-deployment. Verify this:

### In GitHub:

1. **Go to your GitHub repository:**
   ```
   https://github.com/IKRedHat/Nexus-Release-Readiness-Bot
   ```

2. **Click "Settings" tab**

3. **Click "Webhooks" in sidebar**

4. **You should see a Vercel webhook:**
   ```
   Payload URL: https://api.vercel.com/v1/integrations/...
   Content type: application/json
   Events: Just the push event
   Active: ✓ (green checkmark)
   ```

### If NO Webhook Exists:

**You need to reconnect Vercel to GitHub:**

1. In Vercel → Settings → Git
2. Click **"Disconnect"** (if connected)
3. Click **"Connect Git Repository"** again
4. Re-authorize and select your repo
5. This will create the webhook

---

## 🔍 TROUBLESHOOTING AUTO-DEPLOY

### Issue 1: Webhook Not Firing

**Check:**
```
GitHub Repo → Settings → Webhooks → Click Vercel webhook → Recent Deliveries
```

**You should see:**
- ✅ Recent push events
- ✅ Response: 200 OK

**If showing errors:**
- Reconnect Git integration in Vercel
- Check GitHub permissions

### Issue 2: Builds Not Triggering

**Verify in Vercel:**
```
Project → Settings → Git
```

**Must have:**
- [x] Production Branch: `main`
- [x] Automatically deploy: ON
- [x] Git Integration: Connected

### Issue 3: Root Directory Not Set

**If builds fail or wrong code deploys:**

```
Project → Settings → General → Root Directory
```

**Should be:**
```
services/admin_dashboard/frontend-next
```

**NOT:**
- `frontend` (old directory)
- `.` (project root)
- Empty

---

## 🧪 TEST AUTO-DEPLOYMENT

After configuration, test it:

### 1. Make a Small Change

```bash
cd /Users/imran/Desktop/Nexus-Release-Readiness-Bot
echo "# Test auto-deploy" >> services/admin_dashboard/frontend-next/README.md
git add -A
git commit -m "test: Verify Vercel auto-deployment"
git push origin main
```

### 2. Check Vercel Dashboard

Within **~30 seconds**, you should see:
- New deployment starting
- Status: "Building..."
- Then: "Ready" (after ~2 min)

---

## ⚙️ RECOMMENDED CONFIGURATION

### Complete Settings Checklist:

#### General Settings:
```
Root Directory: services/admin_dashboard/frontend-next
Framework Preset: Next.js
Build Command: npm run build (auto-detected)
Output Directory: .next (auto-detected)
Install Command: npm install
Node.js Version: 20.x (recommended)
```

#### Git Settings:
```
Production Branch: main
✓ Automatically deploy: ON
✓ Deploy Preview: ON (for PRs)
✓ Comments on PR: ON (optional)
```

#### Environment Variables:
```
NEXT_PUBLIC_API_URL = https://nexus-admin-api-63b4.onrender.com
```

---

## 🚨 COMMON MISTAKES TO AVOID

### ❌ Wrong Root Directory
```
Root Directory: frontend (WRONG - old directory)
Root Directory: . (WRONG - project root)
```
✅ **Correct:**
```
Root Directory: services/admin_dashboard/frontend-next
```

### ❌ Git Integration Not Connected
```
Status: Not connected
```
✅ **Correct:**
```
Status: ✓ Connected to IKRedHat/Nexus-Release-Readiness-Bot
```

### ❌ Auto-Deploy Disabled
```
Automatically deploy: OFF
```
✅ **Correct:**
```
Automatically deploy: ON
```

---

## 📊 VERIFICATION CHECKLIST

After setup, verify:

- [ ] Git integration shows "Connected"
- [ ] Production branch is set to `main`
- [ ] "Automatically deploy" is enabled
- [ ] Root directory is `services/admin_dashboard/frontend-next`
- [ ] GitHub webhook exists and is active
- [ ] Test commit triggers automatic deployment
- [ ] Environment variables are set

---

## 🎯 QUICK FIX (Most Common Issue)

**If auto-deploy isn't working, do this:**

1. **Vercel Dashboard** → Your Project → **Settings**
2. **Git** (sidebar) → **Disconnect**
3. **Connect Git Repository** → Select GitHub
4. Choose: `IKRedHat/Nexus-Release-Readiness-Bot`
5. **Import** → Configure settings:
   ```
   Root Directory: services/admin_dashboard/frontend-next
   ```
6. **Deploy**

This recreates the GitHub webhook and fixes 90% of issues.

---

## 📞 STILL NOT WORKING?

### Check Vercel Status:
```
https://www.vercel-status.com/
```

### Check GitHub Permissions:
```
GitHub → Settings → Applications → Vercel
- Should have access to your repos
- Should have webhook permissions
```

### Contact Vercel Support:
```
https://vercel.com/support
```

---

## ✅ SUCCESS INDICATORS

When properly configured, you'll see:

**On Git Push:**
```
✓ Pushed to GitHub
→ Vercel webhook fires (~5 sec)
→ Deployment starts automatically
→ Build runs
→ Deploy completes
→ Notification (if enabled)
```

**In Vercel Dashboard:**
```
Deployments tab shows:
- New deployment from latest commit
- Status: Building → Ready
- No manual trigger needed
```

---

**Once configured, every `git push origin main` will automatically deploy! 🚀**

