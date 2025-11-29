#!/bin/bash

BRANCH_NAME="main"
COMMIT_MSG="feat: Upgrade Nexus to Production (ReAct Engine, Agents, Observability)"

echo "📦 Staging Production Updates..."

# 1. Add all new files (including new folders like tests/unit, demo, etc)
git add .

# 2. Check status
git status

# 3. Commit
echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG"

# 4. Push
echo "🚀 Pushing to origin/$BRANCH_NAME..."
git push origin $BRANCH_NAME

echo "✅ Deployment Code is live on GitHub!"

