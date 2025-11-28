#!/bin/bash

# 1. Create Directory Structure
echo "Creating directory structure..."

mkdir -p .github/workflows
mkdir -p docs/architecture docs/api-specs docs/runbooks
mkdir -p infrastructure/docker
mkdir -p infrastructure/terraform/modules/cloud-run
mkdir -p infrastructure/terraform/modules/postgres
mkdir -p infrastructure/terraform/modules/vector-db
mkdir -p infrastructure/terraform/environments/dev
mkdir -p infrastructure/terraform/environments/prod
mkdir -p infrastructure/k8s

# Services - Orchestrator
mkdir -p services/orchestrator/app/core
mkdir -p services/orchestrator/app/api
mkdir -p services/orchestrator/app/models
mkdir -p services/orchestrator/tests

# Services - Agents
mkdir -p services/agents/jira_agent/src
mkdir -p services/agents/git_ci_agent/src
mkdir -p services/agents/slack_agent/src
mkdir -p services/agents/reporting_agent/src
mkdir -p services/agents/scheduling_agent/src

# Shared Library
mkdir -p shared/nexus_lib/auth
mkdir -p shared/nexus_lib/logging
mkdir -p shared/nexus_lib/schemas

# Tests
mkdir -p tests/e2e

echo "Directories created."

# 2. Create Placeholder Files
echo "Creating placeholder files..."

# Root configuration
touch .gitignore
touch .pre-commit-config.yaml
touch docker-compose.yml
touch Makefile
# Note: README.md likely exists if you initialized the repo, but we touch it just in case
touch README.md 

# GitHub Workflows
touch .github/workflows/ci-test.yaml
touch .github/workflows/cd-deploy-orchestrator.yaml
touch .github/workflows/cd-deploy-agents.yaml
touch .github/PULL_REQUEST_TEMPLATE.md

# Infrastructure - Docker
touch infrastructure/docker/Dockerfile.orchestrator
touch infrastructure/docker/Dockerfile.generic-agent

# Infrastructure - Terraform
touch infrastructure/terraform/main.tf
touch infrastructure/terraform/environments/dev/main.tf
touch infrastructure/terraform/environments/prod/main.tf

# Services - Orchestrator
touch services/orchestrator/requirements.txt
touch services/orchestrator/main.py
touch services/orchestrator/app/__init__.py
touch services/orchestrator/app/core/__init__.py
touch services/orchestrator/app/api/__init__.py
touch services/orchestrator/app/models/__init__.py

# Services - Agents (Main entry points and src inits)
for agent in jira_agent git_ci_agent slack_agent reporting_agent scheduling_agent; do
    touch services/agents/$agent/main.py
    touch services/agents/$agent/src/__init__.py
    touch services/agents/$agent/requirements.txt
done

# Shared Library
touch shared/setup.py
touch shared/nexus_lib/__init__.py
touch shared/nexus_lib/auth/__init__.py
touch shared/nexus_lib/logging/__init__.py
touch shared/nexus_lib/schemas/__init__.py

# E2E Tests
touch tests/conftest.py
touch tests/e2e/test_slack_flow.py
touch tests/e2e/test_reporting_flow.py

# 3. Create a basic .gitignore
cat <<EOT >> .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Terraform
.terraform/
*.tfstate
*.tfstate.backup

# Environment Variables
.env

# IDEs
.vscode/
.idea/
EOT

echo "File structure setup complete!"
