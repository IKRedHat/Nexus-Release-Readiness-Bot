# 🐳 Docker for Beginners: Understanding Nexus Dockerfiles

> A friendly guide for developers new to Docker, explaining how Nexus uses containers.

---

## 📚 Table of Contents

1. [What is Docker?](#-what-is-docker)
2. [Why Do We Need Docker?](#-why-do-we-need-docker)
3. [Key Docker Concepts](#-key-docker-concepts)
4. [Understanding Dockerfiles](#-understanding-dockerfiles)
5. [Nexus Docker Architecture](#-nexus-docker-architecture)
6. [Step-by-Step Dockerfile Breakdown](#-step-by-step-dockerfile-breakdown)
7. [Docker Compose Explained](#-docker-compose-explained)
8. [Common Commands Cheat Sheet](#-common-commands-cheat-sheet)
9. [Troubleshooting Guide](#-troubleshooting-guide)

---

## 🤔 What is Docker?

Think of Docker like a **shipping container** for software:

```
┌─────────────────────────────────────────────────────────────────┐
│                        REAL WORLD                               │
│                                                                 │
│   🏠 Your House          🚢 Shipping Container    🏭 Warehouse │
│   (Your Computer)        (Docker Container)        (Any Server) │
│                                                                 │
│   You pack your          Container ships          Container     │
│   belongings            anywhere in the world     unpacks same  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       SOFTWARE WORLD                            │
│                                                                 │
│   💻 Developer's         📦 Docker Container      ☁️ Server     │
│   Machine                                                       │
│                                                                 │
│   You write code    →    Package with all      →  Runs exactly  │
│                          dependencies             the same!     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**In simple terms:** Docker packages your application along with everything it needs to run (Python, libraries, settings) into a single "container" that works the same everywhere.

---

## 🎯 Why Do We Need Docker?

### The "Works on My Machine" Problem

```
Developer A: "The app works fine on my laptop!"
Developer B: "It crashes on my machine..."
Server:      "It doesn't start at all!"

WHY? Different Python versions, missing libraries, different settings...
```

### Docker Solves This

```
┌─────────────────────────────────────────────────────────────────┐
│                    WITHOUT DOCKER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Developer A        Developer B         Production Server       │
│  ├─ Python 3.9      ├─ Python 3.11      ├─ Python 3.8          │
│  ├─ Redis 6.0       ├─ Redis 7.0        ├─ No Redis!           │
│  └─ macOS           └─ Windows          └─ Linux               │
│                                                                 │
│  Result: 😱 "Works on my machine" chaos!                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     WITH DOCKER                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Developer A        Developer B         Production Server       │
│  ├─ Docker          ├─ Docker           ├─ Docker              │
│  └─ Same Container  └─ Same Container   └─ Same Container      │
│                                                                 │
│  Result: 🎉 Identical environment everywhere!                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Docker Concepts

### 1. Image vs Container

Think of it like a **recipe** vs a **cake**:

| Concept | Real World Analogy | Description |
|---------|-------------------|-------------|
| **Image** | Recipe 📝 | A blueprint/template. Read-only. |
| **Container** | Cake 🎂 | A running instance of the image. |

```
Image (Recipe)              Container (Cake)
┌──────────────┐           ┌──────────────┐
│ Python 3.11  │           │ Running App  │
│ FastAPI      │  ──RUN──▶ │ Port 8080    │
│ Your Code    │           │ Memory: 256M │
└──────────────┘           └──────────────┘

One image can create MANY containers (like one recipe can make many cakes!)
```

### 2. Dockerfile

A **Dockerfile** is a text file with instructions to build an image.

```dockerfile
# It's like a recipe with steps:
FROM python:3.11        # Step 1: Start with Python base
COPY . /app             # Step 2: Copy your code
RUN pip install -r requirements.txt  # Step 3: Install dependencies
CMD ["python", "main.py"]  # Step 4: Run the app
```

### 3. Docker Compose

**Docker Compose** runs multiple containers together:

```
Without Compose:                    With Compose:
┌────────────────────────┐         ┌────────────────────────┐
│ docker run orchestrator│         │ docker compose up      │
│ docker run jira-agent  │    ▶    │                        │
│ docker run slack-agent │         │ (Starts ALL services!) │
│ docker run redis       │         │                        │
│ docker run postgres    │         └────────────────────────┘
│ ... (10 more commands) │
└────────────────────────┘
```

---

## 📖 Understanding Dockerfiles

### Basic Structure

Every Dockerfile instruction builds a **layer** (like layers of a cake):

```dockerfile
# ========================================
# Layer 1: Base Image (Foundation)
# ========================================
FROM python:3.11-slim
#     └── "Start with this existing image"
#         (Like: "Start with a chocolate cake base")

# ========================================
# Layer 2: Install System Dependencies
# ========================================
RUN apt-get update && apt-get install -y curl
#   └── "Run this command during build"

# ========================================
# Layer 3: Set Working Directory
# ========================================
WORKDIR /app
#        └── "All future commands happen in /app folder"

# ========================================
# Layer 4: Copy Files
# ========================================
COPY requirements.txt ./
#    └── Copy from your computer INTO the image

# ========================================
# Layer 5: Install Python Dependencies
# ========================================
RUN pip install -r requirements.txt

# ========================================
# Layer 6: Copy Application Code
# ========================================
COPY . .

# ========================================
# Configuration
# ========================================
ENV PORT=8080
#   └── Set environment variable

EXPOSE 8080
#      └── Document which port the app uses

# ========================================
# Startup Command
# ========================================
CMD ["python", "main.py"]
#   └── "Run this when container starts"
```

### Why Layers Matter

Docker **caches** each layer. If nothing changes, it reuses the cached layer:

```
Build #1 (First time - 5 minutes):
┌─────────────────┐
│ FROM python     │ → Downloads base image
│ RUN apt install │ → Installs tools
│ COPY req.txt    │ → Copies file
│ RUN pip install │ → Installs packages (SLOW!)
│ COPY . .        │ → Copies code
└─────────────────┘

Build #2 (Only code changed - 10 seconds!):
┌─────────────────┐
│ FROM python     │ → ✅ Cached!
│ RUN apt install │ → ✅ Cached!
│ COPY req.txt    │ → ✅ Cached! (file unchanged)
│ RUN pip install │ → ✅ Cached! (requirements unchanged)
│ COPY . .        │ → 🔄 Rebuilds (code changed)
└─────────────────┘
```

**Pro Tip:** Copy requirements.txt BEFORE copying code, so dependency installation is cached!

---

## 🏗️ Nexus Docker Architecture

### Overview

Nexus has **10 services** running in containers:

```
┌─────────────────────────────────────────────────────────────────┐
│                     NEXUS CONTAINER ECOSYSTEM                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   🧠 BRAIN                                                      │
│   ┌─────────────────┐                                          │
│   │  Orchestrator   │ Port 8080 - The "smart" coordinator      │
│   └────────┬────────┘                                          │
│            │                                                    │
│   🤖 SPECIALIST AGENTS (Talk to external tools)                │
│   ┌────────┴────────┬─────────────┬─────────────┐              │
│   │   Jira Agent    │  Git Agent  │ Slack Agent │              │
│   │   Port 8081     │  Port 8082  │ Port 8084   │              │
│   └─────────────────┴─────────────┴─────────────┘              │
│   ┌─────────────────┬─────────────┬─────────────┐              │
│   │ Reporting Agent │ RCA Agent   │Hygiene Agent│              │
│   │   Port 8083     │  Port 8006  │ Port 8085   │              │
│   └─────────────────┴─────────────┴─────────────┘              │
│                                                                 │
│   📊 ADVANCED SERVICES                                          │
│   ┌─────────────────┬─────────────┬─────────────┐              │
│   │    Analytics    │  Webhooks   │  Dashboard  │              │
│   │   Port 8086     │  Port 8087  │ Port 8088   │              │
│   └─────────────────┴─────────────┴─────────────┘              │
│                                                                 │
│   🗄️ DATA & MONITORING                                          │
│   ┌─────────────────┬─────────────┬─────────────┐              │
│   │   PostgreSQL    │    Redis    │ Prometheus  │              │
│   │   Port 5432     │  Port 6379  │ Port 9090   │              │
│   └─────────────────┴─────────────┴─────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Dockerfile Files Explained

| Dockerfile | What It Builds | Used By |
|------------|---------------|---------|
| `Dockerfile.orchestrator` | The main "brain" service | Orchestrator only |
| `Dockerfile.agent` | Universal agent template | All 6 specialist agents |
| `Dockerfile.admin-dashboard` | Web UI + Backend | Admin Dashboard |
| `Dockerfile.analytics` | Metrics & analytics | Analytics service |
| `Dockerfile.webhooks` | Event notifications | Webhooks service |
| `Dockerfile.base` | Shared foundation | Optional base image |

---

## 🔍 Step-by-Step Dockerfile Breakdown

Let's examine `Dockerfile.orchestrator` piece by piece:

### Part 1: The Header

```dockerfile
# syntax=docker/dockerfile:1.7
```

**What it does:** Enables advanced Docker features (BuildKit).

**Why:** Allows caching, faster builds, and modern syntax.

---

### Part 2: Build Arguments

```dockerfile
ARG PYTHON_VERSION=3.11
ARG UV_VERSION=0.4.18
```

**What it does:** Defines variables you can change at build time.

**Why:** Makes the Dockerfile flexible. Want Python 3.12? Just change the argument!

```bash
# Using default (Python 3.11)
docker build -t myapp .

# Using different version
docker build --build-arg PYTHON_VERSION=3.12 -t myapp .
```

---

### Part 3: Multi-Stage Builds

This is the **key optimization**! We use 3 stages:

```dockerfile
# ══════════════════════════════════════════════════════════════
# STAGE 1: Get the UV package manager
# ══════════════════════════════════════════════════════════════
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
#    └── Download a tiny image containing UV tool
#                                           └── Name this stage "uv"
```

**Why UV?** It's a Rust-based package manager that's 10x faster than pip!

```dockerfile
# ══════════════════════════════════════════════════════════════
# STAGE 2: Build all dependencies
# ══════════════════════════════════════════════════════════════
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder
#                                            └── Name this stage "builder"

COPY --from=uv /uv /usr/local/bin/uv
#    └── Copy the UV tool from Stage 1

RUN apt-get update && apt-get install -y gcc libpq-dev
#   └── Install build tools (needed to compile Python packages)

COPY requirements.txt .
RUN uv pip wheel --wheel-dir /wheels -r requirements.txt
#   └── Pre-compile all packages into "wheel" files
```

**Why Stage 2?** We install build tools (gcc, etc.) here, but we DON'T want them in our final image (they're huge and a security risk).

```dockerfile
# ══════════════════════════════════════════════════════════════
# STAGE 3: Create the final, tiny image
# ══════════════════════════════════════════════════════════════
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
#    └── Start fresh with a clean, small image

# Copy ONLY the pre-built packages (not the build tools!)
COPY --from=builder /wheels /wheels
#    └── Copy wheels from Stage 2

RUN pip install /wheels/*.whl && rm -rf /wheels
#   └── Install packages from wheels (no compilation needed!)

COPY . /app
#   └── Copy your actual application code
```

**Why Stage 3?** The final image only contains what we NEED to run:
- ✅ Python runtime
- ✅ Pre-built packages
- ✅ Your code
- ❌ No build tools (gcc, etc.)
- ❌ No source files for packages

### Visual: Multi-Stage Build

```
STAGE 1 (uv)          STAGE 2 (builder)         STAGE 3 (runtime)
┌──────────────┐      ┌──────────────────┐      ┌──────────────────┐
│     UV       │─────▶│ Python           │      │ Python           │
│   (5 MB)     │      │ + Build Tools    │      │ (NO build tools) │
└──────────────┘      │ + UV             │      │                  │
                      │ + Source Code    │      │ Pre-built        │
                      │                  │─────▶│ packages only    │
                      │ OUTPUT:          │      │                  │
                      │ /wheels/*.whl    │      │ Your app code    │
                      │ (pre-compiled)   │      │                  │
                      └──────────────────┘      └──────────────────┘
                           ~1.2 GB                   ~150 MB
                                               
                      ❌ DISCARDED              ✅ FINAL IMAGE
```

---

### Part 4: Security Features

```dockerfile
# Create a non-root user
RUN groupadd --gid 1000 nexus \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home nexus
#      └── Create user "nexus" with ID 1000

USER nexus
#    └── Switch to non-root user
```

**Why non-root?** If an attacker breaks into your container, they have limited permissions (not admin access).

```dockerfile
# Health check without curl
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD ["/usr/local/bin/healthcheck"]
```

**Why Python health check?** We don't need to install `curl` (saves space and reduces security surface).

---

### Part 5: The Startup Command

```dockerfile
CMD ["python", "-m", "uvicorn", \
     "services.orchestrator.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080"]
```

**What it does:** Starts the FastAPI web server when the container runs.

**Breakdown:**
- `python -m uvicorn` → Run Uvicorn (fast Python web server)
- `services.orchestrator.main:app` → Load the FastAPI app
- `--host 0.0.0.0` → Listen on all network interfaces
- `--port 8080` → Use port 8080

---

## 🎼 Docker Compose Explained

`docker-compose.yml` defines ALL services and how they connect:

### Basic Structure

```yaml
# Define the project name
name: nexus

# Define all services (containers)
services:
  
  # Service 1: Redis (Database cache)
  redis:
    image: redis:7-alpine        # Use pre-built Redis image
    ports:
      - "6379:6379"              # Map container:host ports
    volumes:
      - redis_data:/data         # Persist data

  # Service 2: Orchestrator (Our app)
  orchestrator:
    build:
      context: ../..             # Where to find source code
      dockerfile: infrastructure/docker/Dockerfile.orchestrator
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379  # Connect to Redis service
    depends_on:
      - redis                     # Start Redis first!

# Define persistent storage
volumes:
  redis_data:
```

### Service Dependencies

```yaml
orchestrator:
  depends_on:
    redis:
      condition: service_healthy  # Wait until Redis is healthy
    postgres:
      condition: service_healthy
```

**Why?** The Orchestrator needs Redis and Postgres to be ready before it starts!

```
Start Order:
┌────────────┐     ┌────────────┐     ┌──────────────┐
│   Redis    │────▶│  Postgres  │────▶│ Orchestrator │
│  (starts)  │     │  (starts)  │     │   (starts)   │
│            │     │            │     │              │
│  health ✓  │     │  health ✓  │     │  health ✓    │
└────────────┘     └────────────┘     └──────────────┘
```

### Network Magic

All services in docker-compose can talk to each other by name:

```yaml
orchestrator:
  environment:
    - REDIS_URL=redis://redis:6379
    #                   └── This is the SERVICE NAME, not IP!
    - JIRA_AGENT_URL=http://jira-agent:8081
    #                       └── Service name again!
```

Docker creates a network where:
- `redis` resolves to Redis container's IP
- `jira-agent` resolves to Jira Agent's IP
- No hardcoded IPs needed!

---

## 📋 Common Commands Cheat Sheet

### Building

```bash
# Build all services
docker compose build

# Build specific service
docker compose build orchestrator

# Build without cache (fresh build)
docker compose build --no-cache

# Build with different Python version
docker compose build --build-arg PYTHON_VERSION=3.12
```

### Running

```bash
# Start all services (in background)
docker compose up -d

# Start specific service
docker compose up -d orchestrator

# Start and rebuild if needed
docker compose up -d --build

# Stop all services
docker compose down

# Stop and remove all data (volumes)
docker compose down -v
```

### Viewing

```bash
# List running containers
docker compose ps

# View logs (all services)
docker compose logs

# View logs (specific service, follow mode)
docker compose logs -f orchestrator

# View last 100 log lines
docker compose logs --tail=100 orchestrator
```

### Debugging

```bash
# Open shell inside container
docker compose exec orchestrator /bin/bash

# Run one-off command
docker compose exec orchestrator python -c "print('Hello!')"

# Check container resource usage
docker stats

# Inspect container details
docker inspect nexus-orchestrator
```

### Cleanup

```bash
# Remove stopped containers
docker compose rm

# Remove unused images
docker image prune

# Remove everything unused
docker system prune -a

# Remove specific image
docker rmi nexus-orchestrator:latest
```

---

## 🔧 Troubleshooting Guide

### Problem: Container won't start

```bash
# Check the logs
docker compose logs orchestrator

# Common causes:
# 1. Port already in use
# 2. Missing environment variables
# 3. Dependency not ready
```

### Problem: "Port already in use"

```bash
# Find what's using the port
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use different port in docker-compose.yml
ports:
  - "8090:8080"  # Use 8090 on host
```

### Problem: Container is unhealthy

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' nexus-orchestrator

# View health check logs
docker inspect --format='{{json .State.Health}}' nexus-orchestrator | jq
```

### Problem: Out of disk space

```bash
# See what's using space
docker system df

# Clean up
docker system prune -a --volumes
```

### Problem: Slow builds

```bash
# Use BuildKit (faster)
DOCKER_BUILDKIT=1 docker compose build

# Check .dockerignore is excluding unnecessary files
cat infrastructure/docker/.dockerignore
```

---

## 🎓 Key Takeaways

1. **Docker = Consistent environments** - Same container runs everywhere
2. **Image = Recipe, Container = Running cake** - One image, many containers
3. **Dockerfile = Build instructions** - Step-by-step image creation
4. **Multi-stage builds = Smaller images** - Build tools in stage 1, app in stage 2
5. **Docker Compose = Orchestra conductor** - Manages multiple containers
6. **Layers = Caching** - Order matters for fast rebuilds!
7. **Non-root = Security** - Always run as unprivileged user

---

## 📚 Further Learning

- [Docker Getting Started](https://docs.docker.com/get-started/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Play with Docker (Free Lab)](https://labs.play-with-docker.com/)

---

*Happy containerizing! 🐳*

