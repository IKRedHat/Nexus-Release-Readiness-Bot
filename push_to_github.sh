#!/bin/bash

# Configuration
BRANCH_NAME="main"
COMMIT_MSG="feat: Implement MVP code for E0, E1, E2 deliverables"

echo "📦 Preparing to push to GitHub..."

# 1. Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Error: Not a git repository. Run 'git init' first."
    exit 1
fi

# 2. Add all files
echo "➕ Adding files..."
git add .

# 3. Commit
echo "Pm Committing changes..."
git commit -m "$COMMIT_MSG"

# 4. Push
echo "🚀 Pushing to origin/$BRANCH_NAME..."
# Note: Ensure you have set up your PAT (Personal Access Token) as discussed
git push origin $BRANCH_NAME

echo "✅ Done! Code is live on GitHub."
