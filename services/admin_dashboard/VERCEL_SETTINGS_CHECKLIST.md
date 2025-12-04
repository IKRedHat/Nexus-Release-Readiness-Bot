# ✅ VERCEL CONFIGURATION CHECKLIST

## 🔧 Complete Settings for Nexus Admin Dashboard

---

## 1️⃣ ENVIRONMENT VARIABLES

**Go to:** Vercel Dashboard → Your Project → Settings → Environment Variables

### Required Variables:

| Variable Name | Value | Environments |
|--------------|-------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://nexus-admin-api-63b4.onrender.com` | Production, Preview, Development |

### How to Add:

1. Click **"Add New"** button
2. **Key:** `NEXT_PUBLIC_API_URL`
3. **Value:** `https://nexus-admin-api-63b4.onrender.com`
4. **Environments:** Check ALL three boxes:
   - ✅ Production
   - ✅ Preview
   - ✅ Development
5. Click **"Save"**

### ⚠️ Important Notes:

- Variable name MUST start with `NEXT_PUBLIC_` to be accessible in browser
- No trailing slash in URL
- Available in all deployments (production, preview branches, development)

---

## 2️⃣ BUILD & DEVELOPMENT SETTINGS

**Go to:** Vercel Dashboard → Your Project → Settings → General

### Build Settings:

| Setting | Value | Notes |
|---------|-------|-------|
| **Framework Preset** | `Next.js` | Auto-detected, keep as-is |
| **Root Directory** | `services/admin_dashboard/frontend-next` | CRITICAL - must be set! |
| **Build Command** | `next build` | Default, don't change |
| **Output Directory** | `.next` | Default, don't change |
| **Install Command** | `npm install --legacy-peer-deps` | IMPORTANT - must include flag |
| **Development Command** | `next dev` | Default, optional |

### How to Configure:

1. Scroll to **"Build & Development Settings"** section
2. Click **"Edit"** (if locked, click "Override")
3. Set each value as shown above
4. **CRITICAL:** Make sure Root Directory is `services/admin_dashboard/frontend-next`
5. **CRITICAL:** Make sure Install Command includes `--legacy-peer-deps`
6. Click **"Save"**

---

## 3️⃣ NODE.JS VERSION

**Go to:** Vercel Dashboard → Your Project → Settings → General

### Node.js Settings:

| Setting | Value | Notes |
|---------|-------|-------|
| **Node.js Version** | `20.x` | Matches .nvmrc file |

### How to Configure:

1. Find **"Node.js Version"** section
2. Select **`20.x`** from dropdown
3. Click **"Save"**

---

## 4️⃣ GIT SETTINGS

**Go to:** Vercel Dashboard → Your Project → Settings → Git

### Git Configuration:

| Setting | Value | Notes |
|---------|-------|-------|
| **Connected Repository** | `github.com/IKRedHat/Nexus-Release-Readiness-Bot` | Should already be connected |
| **Production Branch** | `main` | CRITICAL for auto-deploy |
| **Ignored Build Step** | (empty/default) | Don't skip builds |

### How to Verify:

1. Check **"Connected Git Repository"** shows your repo
2. Check **"Production Branch"** is set to `main`
3. Make sure no custom "Ignored Build Step" command is set
4. If anything wrong, click **"Disconnect"** and reconnect

---

## 5️⃣ DEPLOYMENT SETTINGS (Optional but Recommended)

**Go to:** Vercel Dashboard → Your Project → Settings → Deployment Protection

### Recommended Settings:

| Setting | Value | Why |
|---------|-------|-----|
| **Vercel Authentication** | `Disabled` | Allow public access |
| **Deployment Protection** | `Disabled` or `Standard` | Avoid blocking users |
| **Password Protection** | `Disabled` | Unless you need it |

---

## 6️⃣ DOMAINS (Optional)

**Go to:** Vercel Dashboard → Your Project → Settings → Domains

### Default Domain:

Your project gets a free Vercel domain:
```
nexus-admin-dashboard.vercel.app
```

### Custom Domain (Optional):

If you have a custom domain:
1. Click **"Add"**
2. Enter your domain (e.g., `admin.yourdomain.com`)
3. Follow DNS configuration instructions
4. Verify

---

## 📋 COMPLETE SETTINGS SUMMARY

Copy this and verify each one in Vercel:

### ✅ Environment Variables:
```
NEXT_PUBLIC_API_URL = https://nexus-admin-api-63b4.onrender.com
  ↳ Applied to: Production ✓, Preview ✓, Development ✓
```

### ✅ Build & Development Settings:
```
Framework: Next.js
Root Directory: services/admin_dashboard/frontend-next
Build Command: next build
Install Command: npm install --legacy-peer-deps
Output Directory: .next
Node.js Version: 20.x
```

### ✅ Git Settings:
```
Repository: IKRedHat/Nexus-Release-Readiness-Bot
Production Branch: main
Auto-Deploy: Enabled
```

### ✅ Deployment Protection:
```
Vercel Authentication: Disabled
Password Protection: Disabled
```

---

## 🎬 HOW TO APPLY SETTINGS & REDEPLOY

### Option 1: Automatic Redeploy (If Settings Changed)

If you change **environment variables**, Vercel may ask to redeploy:
1. A banner appears: "Redeploy to apply changes"
2. Click **"Redeploy"**
3. Select **"Use existing Build Cache"** (faster)
4. Click **"Redeploy"**

### Option 2: Manual Redeploy

To manually trigger a redeploy:
1. Go to **"Deployments"** tab
2. Click **"..."** (three dots) on latest deployment
3. Click **"Redeploy"**
4. Select **"Use existing Build Cache"**
5. Click **"Redeploy"**

### Option 3: Push a Commit (Tests Auto-Deploy)

Or just push any small change:
```bash
cd /Users/imran/Desktop/Nexus-Release-Readiness-Bot
echo "# Vercel configured - $(date)" >> services/admin_dashboard/frontend-next/README.md
git add -A
git commit -m "test: Verify Vercel settings applied"
git push origin main
```

---

## 🔍 VERIFICATION CHECKLIST

After redeploying, verify:

### ✅ Build Phase:
- [ ] Install completes with `--legacy-peer-deps` flag
- [ ] No dependency conflicts
- [ ] Next.js 14.2.33 detected
- [ ] No PostCSS/Tailwind errors

### ✅ Deployment:
- [ ] Build succeeds (green checkmark)
- [ ] Deployment URL is live
- [ ] No 500 errors

### ✅ Application:
- [ ] Login page loads correctly
- [ ] CSS/Tailwind styles applied properly
- [ ] Console shows correct API URL when inspecting
- [ ] Can login successfully
- [ ] All pages load without errors

### ✅ Environment Variables:
Open browser console on your deployed site and run:
```javascript
console.log(process.env.NEXT_PUBLIC_API_URL)
```
Should show: `https://nexus-admin-api-63b4.onrender.com`

---

## 🐛 TROUBLESHOOTING

### Issue: Build fails with dependency errors

**Solution:** Make sure Install Command is:
```
npm install --legacy-peer-deps
```

### Issue: API calls go to wrong URL

**Solution:** Verify environment variable:
- Name is `NEXT_PUBLIC_API_URL` (not `VITE_API_URL`)
- Applied to all environments
- No trailing slash
- Redeploy after adding

### Issue: Pages show 404

**Solution:** Make sure Root Directory is:
```
services/admin_dashboard/frontend-next
```

### Issue: Auto-deploy doesn't work

**Solution:** Check Git settings:
- Production Branch is `main`
- Repository is connected
- No "Ignored Build Step" command

---

## 🎯 QUICK SETTINGS VERIFICATION

Go through these in order:

1. **Environment Variables** → Add `NEXT_PUBLIC_API_URL`
2. **General → Build Settings** → Set Root Directory and Install Command
3. **General → Node.js Version** → Set to 20.x
4. **Git → Production Branch** → Verify it's `main`
5. **Redeploy** → Trigger a redeploy
6. **Test** → Open deployed URL and test login

---

## 📊 EXPECTED RESULT

After applying all settings:

**Build Logs Should Show:**
```
✓ Running install command: npm install --legacy-peer-deps
✓ Added 438 packages in 20s
✓ Detected Next.js version: 14.2.33
✓ Creating an optimized production build...
✓ Compiled successfully
✓ Build completed
```

**Deployed App Should:**
- Load login page with Nexus branding
- Accept valid credentials
- Connect to Render backend API
- Show all pages (Dashboard, Releases, Health, etc.)
- Have proper styling (dark theme, Tailwind CSS)

---

## ✅ FINAL CHECKLIST

Before you click "Redeploy", verify you've set:

- [ ] `NEXT_PUBLIC_API_URL` environment variable
- [ ] Root Directory: `services/admin_dashboard/frontend-next`
- [ ] Install Command: `npm install --legacy-peer-deps`
- [ ] Node.js Version: 20.x
- [ ] Production Branch: `main`

**Then redeploy and watch it succeed!** 🚀

