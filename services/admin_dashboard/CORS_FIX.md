# 🔧 CORS FIX FOR VERCEL DEPLOYMENT

## 🚨 PROBLEM: Frontend Can't Connect to Backend

**Error:** "Unable to Load Settings - Could not fetch configuration from the backend API"

**Root Cause:** CORS policy blocking frontend from accessing backend API

---

## ✅ SOLUTION: Update CORS in Render

### Option 1: Via Render Dashboard (Recommended - 2 minutes)

1. **Go to:** https://dashboard.render.com
2. **Click:** Your service `nexus-admin-api`
3. **Click:** "Environment" tab (left sidebar)
4. **Find:** `NEXUS_CORS_ORIGINS` variable
5. **Click:** "Edit" button
6. **Update value to:**
   ```
   https://*.vercel.app,http://localhost:5173,http://localhost:3000
   ```
   **This allows ALL Vercel domains** (wildcard)

7. **Click:** "Save Changes"
8. **Render will automatically redeploy** (takes 2-3 minutes)

### Option 2: Add Your Specific Domain

If you want to be more restrictive:

**Update `NEXUS_CORS_ORIGINS` to:**
```
https://your-actual-domain.vercel.app,https://*.vercel.app,http://localhost:5173
```

**Replace `your-actual-domain.vercel.app` with your actual Vercel URL!**

---

## 🔍 HOW TO FIND YOUR VERCEL DOMAIN

**Look at your browser address bar:**
```
https://nexus-admin-dashboard-[random].vercel.app
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         This is your domain
```

---

## 🧪 TEST AFTER FIX

1. **Wait 2-3 minutes** for Render to redeploy
2. **Go to Render logs** and verify it restarted
3. **Refresh your Vercel deployment**
4. **Settings page should load!**

---

## 📋 ALTERNATIVE: Update render.yaml (Permanent Fix)

If you want to make this change permanent in code:

**File:** `render.yaml`

**Find line 58-59:**
```yaml
- key: NEXUS_CORS_ORIGINS
  value: "https://nexus-admin-dashboard-gamma.vercel.app,https://*.vercel.app,http://localhost:5173"
```

**Change to:**
```yaml
- key: NEXUS_CORS_ORIGINS
  value: "https://*.vercel.app,http://localhost:5173,http://localhost:3000"
```

**This allows any Vercel deployment!**

---

## ✅ VERIFICATION

After Render redeploys:

1. **Open your Vercel deployment**
2. **Click on any page** (Dashboard, Releases, etc.)
3. **Should load data successfully!**

---

**Go to Render Dashboard NOW and update that CORS setting!** 🚀

