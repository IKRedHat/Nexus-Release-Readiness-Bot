# 🔧 FIX: Vercel Not Auto-Deploying Latest Commits

## 🚨 CURRENT PROBLEM

**Symptom:** Vercel keeps deploying old commit `b785a81` instead of latest `219b14d`

**Error in Old Commit:**
```
Module not found: Can't resolve '@/lib/utils'
```

This was already fixed in later commits, but Vercel isn't picking them up!

---

## ✅ COMPLETE FIX (Step-by-Step)

### STEP 1: Verify GitHub Email (Check This First)

**Go to:**
```
https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/commits/main
```

**Look at the latest commit:** `test: Verify commit author email is recognized by Vercel`

**✓ Does it show:**
- Your profile picture? (Good!)
- Or just initials in a circle? (Email not verified!)

**If no profile picture:**
Your email verification didn't work. Go to:
```
https://github.com/settings/emails
```

Check if `ikhalidi@redhat.com` shows **"✓ Verified"**

If not verified, click "Resend verification email" and verify it.

---

### STEP 2: Reconnect Vercel to GitHub (CRITICAL)

#### A. Go to Vercel Project Settings

1. **Open Vercel Dashboard:**
   ```
   https://vercel.com/dashboard
   ```

2. **Click your project:** `nexus-admin-dashboard-nxt` (or whatever it's called)

3. **Click "Settings" tab** (top navigation)

4. **Click "Git" in sidebar**

#### B. Check Git Configuration

**You should see:**
```
Connected Git Repository
  github.com/IKRedHat/Nexus-Release-Readiness-Bot
```

**⚠️ If you see "Disconnected" or any warning:**
1. Click **"Disconnect"** (if shown)
2. Click **"Connect Git Repository"**
3. Select **GitHub**
4. Choose repository: `IKRedHat/Nexus-Release-Readiness-Bot`
5. Click **"Connect"**

#### C. Set Production Branch

**Still in Settings > Git:**

1. Find **"Production Branch"** section
2. Make sure it says: **`main`**
3. If not, change it to `main`
4. Click **"Save"**

#### D. Enable Auto-Deployments

**Still in Settings > Git:**

1. Find **"Deploy Hooks"** or **"Auto Deploy"** section
2. Make sure **"Automatically deploy branches"** is **enabled**
3. Check that `main` is set as production branch

---

### STEP 3: Disconnect and Reconnect GitHub Integration (Nuclear Option)

**If auto-deploy still doesn't work, do this:**

#### A. Disconnect GitHub from Vercel

1. Go to **Vercel Dashboard** → **Settings** → **Git**
2. Click **"Disconnect"** button
3. Confirm disconnection

#### B. Reconnect with Fresh Permissions

1. Click **"Connect Git Repository"**
2. Choose **"GitHub"**
3. **IMPORTANT:** When GitHub asks for permissions:
   - Make sure to grant **"Read and Write"** access
   - Grant access to **"IKRedHat/Nexus-Release-Readiness-Bot"**
4. Select the repository
5. Set **Root Directory:** `services/admin_dashboard/frontend-next`
6. Set **Production Branch:** `main`
7. Click **"Deploy"**

---

### STEP 4: Check GitHub Webhook (Advanced)

Vercel creates a webhook in GitHub to listen for new commits.

#### A. Check GitHub Webhook Exists

1. **Go to your GitHub repo:**
   ```
   https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/settings/hooks
   ```

2. **You should see a webhook to Vercel:**
   ```
   https://api.vercel.com/...
   ```

3. **Click on it**

4. **Check:**
   - **Recent Deliveries:** Should show recent push events
   - **Response:** Should be 200 OK (green checkmark)

#### B. If Webhook is Missing or Failing

**Option 1: Re-add via Vercel (Recommended)**
1. Go to Vercel Settings → Git
2. Disconnect and reconnect GitHub (as in Step 3)
3. This will recreate the webhook

**Option 2: Manually Add Webhook**
1. In GitHub repo → Settings → Webhooks
2. Click "Add webhook"
3. **Payload URL:** Get from Vercel Settings → Git → Deploy Hook URL
4. **Content type:** `application/json`
5. **Events:** "Just the push event"
6. Click "Add webhook"

---

### STEP 5: Force Deploy Latest Commit Manually

While we fix auto-deploy, let's get the latest commit deployed:

#### A. Via Vercel Dashboard

1. Go to your Vercel project
2. Click **"Deployments"** tab
3. Click **"Deploy"** button (top right)
4. **IMPORTANT:** Make sure you select:
   - **Branch:** `main`
   - **Commit:** `219b14d` (latest commit with the fix)
   - NOT the old `b785a81`!
5. Click **"Deploy"**

#### B. Via GitHub (Trigger Webhook)

Make a dummy commit to force trigger:

```bash
cd /Users/imran/Desktop/Nexus-Release-Readiness-Bot

# Make a trivial change
echo "" >> services/admin_dashboard/frontend-next/README.md
echo "<!-- Trigger Vercel auto-deploy -->" >> services/admin_dashboard/frontend-next/README.md

git add -A
git commit -m "chore: Trigger Vercel auto-deploy test"
git push origin main
```

**Then watch Vercel dashboard** - it should deploy within 30 seconds.

---

## 🔍 DIAGNOSTICS CHECKLIST

Run through this checklist:

### ✅ GitHub Side:

- [ ] Email `ikhalidi@redhat.com` added to GitHub
- [ ] Email shows "✓ Verified" at https://github.com/settings/emails
- [ ] Latest commit shows profile picture (not just initials)
- [ ] Webhook exists at repo Settings → Webhooks
- [ ] Webhook shows "Recent Deliveries" with 200 OK responses

### ✅ Vercel Side:

- [ ] Project exists: `nexus-admin-dashboard-nxt`
- [ ] Git is connected: Settings → Git shows repository
- [ ] Production branch is `main`
- [ ] Root directory is `services/admin_dashboard/frontend-next`
- [ ] Auto-deploy is enabled

### ✅ Test:

- [ ] Make a dummy commit
- [ ] Vercel starts building within 30 seconds
- [ ] Build uses the NEW commit (not old one)
- [ ] Build succeeds without `@/lib/utils` error

---

## 🎯 QUICK TEST SCRIPT

After following the steps above, test with this:

```bash
cd /Users/imran/Desktop/Nexus-Release-Readiness-Bot

# Create test file
echo "# Vercel Auto-Deploy Test $(date)" > services/admin_dashboard/frontend-next/DEPLOY_TEST.md

git add -A
git commit -m "test: Verify Vercel auto-deploys on push ($(date +%H:%M))"
git push origin main

echo "✅ Pushed! Now:"
echo "1. Go to Vercel dashboard"
echo "2. You should see a new deployment starting within 30 seconds"
echo "3. Check the commit hash - it should be the latest!"
```

---

## 🆘 IF STILL NOT WORKING

### Last Resort: Create New Vercel Project

If nothing works, the Vercel project might be corrupted:

1. **Delete the old Vercel project** (backup environment variables first!)

2. **Create new Vercel project:**
   ```bash
   cd /Users/imran/Desktop/Nexus-Release-Readiness-Bot/services/admin_dashboard/frontend-next
   npx vercel --prod
   ```

3. **Follow prompts:**
   - Link to GitHub? **Yes**
   - Production branch? **main**
   - Root directory? **.** (you're already in it)

4. **Set environment variables** in Vercel dashboard

5. **Test:** Make a commit and watch it auto-deploy

---

## 📊 WHAT YOU SHOULD SEE WHEN WORKING

### On Git Push:

```bash
$ git push origin main
To https://github.com/IKRedHat/Nexus-Release-Readiness-Bot.git
   219b14d..abc1234  main -> main
```

### On Vercel (Within 30 seconds):

```
🔨 Building...
   Branch: main
   Commit: abc1234 "test: Verify Vercel auto-deploys..."
   
✓ Build completed in 2m 15s
✓ Deployment ready
```

### On GitHub Webhook:

```
✓ Webhook delivery
  Request: POST to https://api.vercel.com/...
  Response: 200 OK
```

---

## 🎬 DO THIS NOW

### Immediate Actions (in order):

1. **Verify email at:** https://github.com/settings/emails
   - Confirm `ikhalidi@redhat.com` shows "✓ Verified"

2. **Check Vercel Git connection:** https://vercel.com/dashboard
   - Settings → Git → Make sure connected to right repo

3. **Check GitHub webhook:** https://github.com/IKRedHat/Nexus-Release-Readiness-Bot/settings/hooks
   - Confirm Vercel webhook exists and recent deliveries are 200 OK

4. **If webhook is failing, reconnect GitHub in Vercel**

5. **Test with dummy commit** (use script above)

---

## ✅ SUCCESS CRITERIA

You'll know it's fixed when:

1. **You push a commit** → Vercel deploys **within 30 seconds**
2. **Vercel uses the LATEST commit** (not an old one)
3. **Build succeeds** (no `@/lib/utils` errors)
4. **Every future push auto-deploys** without manual intervention

---

**Start with Step 1 (verify email), then Step 2 (check Vercel Git settings). Report back what you see!** 🚀

