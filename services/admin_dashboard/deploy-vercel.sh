#!/bin/bash

# Vercel Manual Deployment Script
# Use this when auto-deploy is blocked by git author issues

echo "🚀 Deploying to Vercel via CLI..."
echo ""

cd services/admin_dashboard/frontend-next

echo "📦 Installing Vercel CLI..."
npm install -g vercel

echo ""
echo "🔐 Please login to Vercel when prompted..."
vercel login

echo ""
echo "🏗️  Deploying to production..."
vercel --prod --yes

echo ""
echo "✅ Deployment complete!"
echo "🌐 Check your Vercel dashboard for the deployment URL"

