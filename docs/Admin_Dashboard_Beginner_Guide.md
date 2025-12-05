# 🎛️ Admin Dashboard Beginner's Guide

> Your friendly introduction to the Nexus Admin Dashboard codebase.

![Next.js](https://img.shields.io/badge/Frontend-Next.js_14-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?style=for-the-badge&logo=typescript)

---

## 1. 🤔 What is the Admin Dashboard?

> **Think of it as the "Control Room" for Nexus.**

The Admin Dashboard is a web application where you can:

- **📊 See Everything:** View releases, health status, and metrics in one place.
- **👥 Manage People:** Add users, assign roles, control who can do what.
- **⚙️ Configure System:** Change settings without touching code.
- **📝 Track Changes:** See who did what with complete audit logs.

**It has two parts:** A pretty *Frontend* (what you see) and a smart *Backend* (what does the work).

---

## 2. 🏗️ The Two Halves: Frontend & Backend

Like a restaurant: the **Frontend** is the dining room (pretty, customer-facing), and the **Backend** is the kitchen (where the magic happens).

| Part | Technology | What It Does |
|------|------------|--------------|
| **🎨 Frontend** | Next.js + React | Shows buttons, tables, charts. Lives in your browser. Makes things look nice. |
| **⚙️ Backend** | FastAPI + Python | Stores data, checks passwords, runs business logic. Lives on a server. |

> 💡 **Simple Rule:** If you want to change how something *looks*, edit Frontend. If you want to change how something *works*, edit Backend.

---

## 3. 🎨 Frontend: The User Interface

**Located at:** `services/admin_dashboard/frontend-next/`

### 📁 Key Folders You'll Work With:

```
src/
├── app/                  # Pages - each folder = one page
│   ├── page.tsx          # Homepage (Dashboard)
│   ├── releases/         # Release management page
│   ├── health/           # Health monitoring page
│   └── settings/         # Configuration page
│
├── components/           # Reusable UI pieces (buttons, cards, etc.)
│   ├── Layout.tsx        # The sidebar + header wrapper
│   └── ui/               # Small components (Button, Input, etc.)
│
├── hooks/                # Custom React hooks
│   ├── useAPI.ts         # Fetches data from backend
│   └── useAuth.ts        # Handles login/logout
│
└── types/                # TypeScript definitions
    └── index.ts          # "What does a User look like?"
```

### 🧩 How Pages Work:

Each page follows a simple pattern:

```tsx
// A typical page (simplified)
export default function ReleasesPage() {
  // 1️⃣ Fetch data from backend
  const { data: releases } = useReleases();
  
  // 2️⃣ Show loading state while waiting
  if (!releases) return <LoadingSpinner />;
  
  // 3️⃣ Display the data
  return (
    <div>
      <h1>Releases</h1>
      {releases.map(release => (
        <ReleaseCard key={release.id} data={release} />
      ))}
    </div>
  );
}
```

---

## 4. ⚙️ Backend: The Brain

**Located at:** `services/admin_dashboard/backend/`

### 📁 Key Files You'll Work With:

```
backend/
├── main.py               # 🚀 The main file - all API endpoints
├── auth.py               # 🔐 Login, logout, permissions
│
├── models/               # Database tables
│   ├── user.py           # What is a User?
│   └── role.py           # What is a Role?
│
├── crud/                 # Database operations
│   └── user.py           # Create, Read, Update, Delete users
│
└── db/                   # Database connection
    └── session.py        # Connect to PostgreSQL
```

### 📡 How API Endpoints Work:

An endpoint is like a phone number - you call it, it answers:

```python
# main.py - A simple endpoint
@app.get("/releases")
async def get_releases():
    """When someone visits /releases, send back the list."""
    releases = await ReleaseManager.list_releases()
    return releases

@app.post("/releases")
async def create_release(data: dict):
    """When someone sends data to /releases, create a new one."""
    new_release = await ReleaseManager.create_release(data)
    return new_release
```

| HTTP Method | What It Does | Example |
|-------------|--------------|---------|
| `GET` | 📖 Read data | Get list of users |
| `POST` | ➕ Create new | Add a new release |
| `PUT` | ✏️ Update existing | Edit a user's name |
| `DELETE` | 🗑️ Remove | Delete a role |

---

## 5. 🔄 How Frontend & Backend Talk

```
🎨 Frontend  →  HTTP Request  →  ⚙️ Backend  →  JSON Response  →  🎨 Frontend
```

1. **User clicks "Load Releases"** button on the page.
2. **Frontend sends request**: `GET /releases`
3. **Backend receives it**, queries database, prepares data.
4. **Backend sends back JSON**: `[{id: 1, name: "v2.0"}, ...]`
5. **Frontend displays** the releases as pretty cards.

> 🔌 **Real-Time Updates:** We also use **WebSockets** for instant updates. Instead of asking "any news?", the backend says "hey, something changed!" automatically.

---

## 6. 💻 Your First Contribution

Let's add a feature! Say we want to show "Last Login" on user cards.

### Step 1: Update the Type (Frontend)

Tell TypeScript what the new field looks like:

```typescript
// src/types/index.ts
interface User {
  id: string;
  name: string;
  email: string;
  last_login: string;  // ← Add this line
}
```

### Step 2: Display It (Frontend)

Show it in the component:

```tsx
// src/components/UserCard.tsx
<p>Last Login: {user.last_login}</p>
```

### Step 3: Send It (Backend)

Make sure the API returns this field:

```python
# backend/main.py
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = get_user_from_db(user_id)
    return {
        "id": user.id,
        "name": user.name,
        "last_login": user.last_login  # ← Add this
    }
```

### Step 4: Test It!

```bash
# Start backend
cd services/admin_dashboard/backend
uvicorn main:app --reload

# Start frontend (new terminal)
cd services/admin_dashboard/frontend-next
npm run dev

# Open http://localhost:3000 🎉
```

---

## 7. 📋 Common Tasks Cheat Sheet

| I want to... | Edit this file |
|--------------|----------------|
| Add a new page | `frontend-next/src/app/new-page/page.tsx` |
| Change sidebar links | `frontend-next/src/components/Layout.tsx` |
| Add a new button style | `frontend-next/src/components/ui/button.tsx` |
| Create new API endpoint | `backend/main.py` |
| Add a database table | `backend/models/` + run migration |
| Change login logic | `backend/auth.py` |
| Add user permissions | `shared/nexus_lib/schemas/rbac.py` |

---

## 8. ⌨️ Commands You'll Use Daily

### Frontend

```bash
npm run dev      # Start development
npm run build    # Build for production
npm run lint     # Check for errors
npm run test     # Run tests
```

### Backend

```bash
uvicorn main:app --reload  # Start server
pytest tests/              # Run tests
alembic upgrade head       # Run migrations
```

---

## 💡 Pro Tips for Beginners

| Tip | Details |
|-----|---------|
| 🔍 **Use the API Docs** | Visit `http://localhost:8088/docs` to see all available endpoints with a "Try it" button! |
| 🎯 **Start Small** | Fix a typo, add a tooltip, change a color. Get comfortable before big features. |
| 📚 **Read the Types** | `src/types/index.ts` tells you exactly what data looks like. |
| 🧪 **Check Tests** | The `__tests__` folder shows how things should work. |

---

*Made with ❤️ for new Nexus contributors*

*Last Updated: December 2024 | Questions? Ask in #nexus-help*

