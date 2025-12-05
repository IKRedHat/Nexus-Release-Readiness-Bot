# Nexus Admin Dashboard
## Technical Overview & Architecture Summary

---

### Executive Summary

The **Nexus Admin Dashboard** is an enterprise-grade web application for managing release readiness, feature requests, and system health monitoring. Built with modern technologies and following industry best practices, it provides a unified control center for DevOps, Release Management, and Engineering teams.

**Production Readiness: 95%** | **Version: 3.0.0**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 14)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  Dashboard  │  │  Releases   │  │   Health    │  │  Settings  │ │
│  │  (Widgets)  │  │  (Timeline) │  │  (Monitor)  │  │  (Config)  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │
│         └────────────────┴────────────────┴───────────────┘        │
│                              │                                      │
│              ┌───────────────┴───────────────┐                      │
│              │    API Client (Axios + SWR)   │                      │
│              │  • Token Management           │                      │
│              │  • WebSocket Connection       │                      │
│              └───────────────┬───────────────┘                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ HTTPS + WebSocket
┌──────────────────────────────┼──────────────────────────────────────┐
│                         BACKEND (FastAPI)                           │
│              ┌───────────────┴───────────────┐                      │
│              │      REST API Endpoints       │                      │
│              │  /auth  /releases  /users     │                      │
│              │  /health  /config  /audit     │                      │
│              └───────────────┬───────────────┘                      │
│         ┌────────────────────┼────────────────────┐                 │
│    ┌────┴────┐         ┌─────┴─────┐        ┌─────┴─────┐          │
│    │  RBAC   │         │  WebSocket │        │   Redis   │          │
│    │ Service │         │  Manager   │        │   Cache   │          │
│    └────┬────┘         └───────────┘        └───────────┘          │
│         │                                                           │
│    ┌────┴──────────────────────────────────────────────────┐       │
│    │              PostgreSQL / In-Memory Storage            │       │
│    │    Users │ Roles │ Audit Logs │ Refresh Tokens        │       │
│    └───────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Application

### Technology Stack
| Technology | Purpose |
|------------|---------|
| **Next.js 14** | React framework with App Router |
| **TypeScript** | Type-safe development |
| **Tailwind CSS** | Utility-first styling |
| **Shadcn/ui** | Accessible component library |
| **SWR** | Data fetching with caching |
| **Recharts** | Data visualization |

### Key Features

**📊 Dashboard**
- Customizable widget grid with drag-and-drop
- Real-time statistics (releases, users, health)
- Recent activity feed with live updates

**📅 Release Management**
- Interactive timeline/Gantt view
- CRUD operations with form dialogs
- Status tracking (Planning → In Progress → Completed)
- CSV/Excel export functionality

**💡 Feature Requests**
- Submission and voting system
- Priority and status management
- Inline commenting with @mentions
- Jira integration ready

**🏥 Health Monitoring**
- Service status dashboard
- Uptime tracking and alerts
- Response time metrics
- WebSocket real-time updates

**👥 User Management (RBAC)**
- Role-based access control
- User CRUD with role assignment
- Permission management
- Complete audit logging

**⚙️ Configuration**
- Mode toggle (Mock/Live/Hybrid)
- Dynamic credential management
- System settings panel

### Enterprise Features
- ✅ WebSocket real-time updates
- ✅ Keyboard navigation (Vim-like J/K)
- ✅ URL-persisted filters with presets
- ✅ Advanced charting with period comparison
- ✅ PWA support with offline capability
- ✅ Dark/Light theme support
- ✅ Accessibility (WCAG compliant)

---

## Backend API

### Technology Stack
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async API |
| **SQLAlchemy 2.0** | ORM with async support |
| **PostgreSQL** | Production database |
| **Redis** | Caching and session storage |
| **Alembic** | Database migrations |
| **Prometheus** | Metrics collection |

### API Endpoints

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/health` | GET | System health overview |
| `/stats` | GET | Dashboard statistics |
| `/auth/*` | POST, GET | Authentication (JWT + SSO) |
| `/releases/*` | CRUD | Release management |
| `/users/*` | CRUD | User management |
| `/roles/*` | CRUD | Role management |
| `/feature-requests/*` | CRUD | Feature request handling |
| `/audit-logs` | GET | Audit trail access |
| `/config/*` | GET, PUT | Configuration management |
| `/ws/*` | WebSocket | Real-time channels |

### Authentication & Security
- **JWT Tokens** with refresh token rotation
- **SSO Support**: Okta, Azure AD, Google, GitHub
- **RBAC**: 30+ granular permissions
- **Audit Logging**: All actions tracked
- **Rate Limiting**: Configurable per endpoint

### WebSocket Channels
| Channel | Update Frequency | Data |
|---------|-----------------|------|
| `/ws/health` | 10 seconds | Service status |
| `/ws/activity` | Real-time | User actions |
| `/ws/metrics` | 15 seconds | System metrics |

---

## Database Schema

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│    Users    │────▶│ User_Roles  │◀────│      Roles      │
├─────────────┤     ├─────────────┤     ├─────────────────┤
│ id          │     │ user_id     │     │ id              │
│ email       │     │ role_id     │     │ name            │
│ name        │     │ assigned_at │     │ permissions[]   │
│ status      │     └─────────────┘     │ is_system_role  │
│ sso_provider│                         └─────────────────┘
│ last_login  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐     ┌─────────────────┐
│   Audit_Logs    │     │ Refresh_Tokens  │
├─────────────────┤     ├─────────────────┤
│ id              │     │ id              │
│ user_id         │     │ token_hash      │
│ action          │     │ user_id         │
│ resource_type   │     │ expires_at      │
│ details (JSON)  │     │ revoked_at      │
│ timestamp       │     └─────────────────┘
└─────────────────┘
```

---

## Deployment

### Frontend (Vercel)
```bash
cd services/admin_dashboard/frontend-next
vercel deploy --prod
```

### Backend (Render/Docker)
```bash
cd services/admin_dashboard/backend
docker build -f Dockerfile.render -t nexus-admin-backend .
```

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL |
| `POSTGRES_HOST` | Yes* | Database host |
| `NEXUS_JWT_SECRET` | Yes | JWT signing key |
| `USE_DATABASE` | No | Enable PostgreSQL |

*Required when `USE_DATABASE=true`

---

## Quick Start

```bash
# 1. Backend
cd services/admin_dashboard/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8088

# 2. Frontend
cd services/admin_dashboard/frontend-next
npm install
npm run dev

# 3. Access
# Frontend: http://localhost:3000
# Backend:  http://localhost:8088
# API Docs: http://localhost:8088/docs
```

---

## File Structure

```
services/admin_dashboard/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── auth.py              # SSO & RBAC authentication
│   ├── db/                  # Database layer
│   ├── models/              # SQLAlchemy models
│   ├── crud/                # CRUD operations
│   ├── alembic/             # Database migrations
│   └── tests/               # API & WebSocket tests
│
└── frontend-next/
    ├── src/
    │   ├── app/             # Next.js App Router pages
    │   ├── components/      # React components
    │   ├── hooks/           # Custom React hooks
    │   ├── providers/       # Context providers
    │   ├── lib/             # Utilities & API client
    │   └── types/           # TypeScript definitions
    └── public/              # Static assets
```

---

## Summary

The Nexus Admin Dashboard delivers a **production-ready**, **enterprise-grade** solution for release management and system monitoring. Key achievements:

| Metric | Value |
|--------|-------|
| **Frontend Components** | 50+ reusable components |
| **API Endpoints** | 40+ REST + 4 WebSocket |
| **Test Coverage** | API, WebSocket, E2E |
| **Authentication** | JWT + 4 SSO providers |
| **Database Support** | PostgreSQL + Redis |
| **Real-time Updates** | WebSocket with auto-reconnect |

**Ready for:** Development ✅ | Staging ✅ | Production ✅

---

*Document Version: 1.0 | Last Updated: December 2024*

