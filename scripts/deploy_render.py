#!/usr/bin/env python3
"""
Render Deployment Script for Nexus Admin Dashboard Backend

This script helps deploy the Admin Dashboard backend to Render.
It can either:
1. Open the Render dashboard for manual deployment
2. Use the Render API to deploy (requires API key)

Usage:
    ./scripts/deploy_render.py              # Interactive deployment
    ./scripts/deploy_render.py --api-key    # API-based deployment
"""

import os
import sys
import json
import webbrowser
import subprocess
from pathlib import Path
from datetime import datetime

# ANSI colors
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    print(f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🚀 NEXUS BACKEND DEPLOYMENT TO RENDER                          ║
║                                                                   ║
║   Deploy the Admin Dashboard API to Render Cloud                  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝{Colors.END}
    """)

def check_prerequisites():
    """Check if all prerequisites are met"""
    print(f"{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    print(f"  ▶ Checking Prerequisites")
    print(f"{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    
    all_good = True
    
    # Check render.yaml exists
    render_yaml = Path(__file__).parent.parent / "render.yaml"
    if render_yaml.exists():
        print(f"  {Colors.GREEN}✓{Colors.END}  render.yaml: Found")
    else:
        print(f"  {Colors.RED}✗{Colors.END}  render.yaml: Not found")
        all_good = False
    
    # Check backend directory
    backend_dir = Path(__file__).parent.parent / "services/admin_dashboard/backend"
    if backend_dir.exists():
        print(f"  {Colors.GREEN}✓{Colors.END}  Backend Directory: Found")
    else:
        print(f"  {Colors.RED}✗{Colors.END}  Backend Directory: Not found")
        all_good = False
    
    # Check requirements.txt
    req_file = backend_dir / "requirements.txt"
    if req_file.exists():
        print(f"  {Colors.GREEN}✓{Colors.END}  requirements.txt: Found")
    else:
        print(f"  {Colors.RED}✗{Colors.END}  requirements.txt: Not found")
        all_good = False
    
    # Check git status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"  {Colors.YELLOW}⚠{Colors.END}  Git: Uncommitted changes detected")
            else:
                print(f"  {Colors.GREEN}✓{Colors.END}  Git: Clean working directory")
        
        # Check if pushed to remote
        result = subprocess.run(
            ["git", "log", "origin/main..HEAD", "--oneline"],
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        if result.stdout.strip():
            print(f"  {Colors.YELLOW}⚠{Colors.END}  Git: Unpushed commits - push before deploying")
        else:
            print(f"  {Colors.GREEN}✓{Colors.END}  Git: All commits pushed to origin/main")
    except Exception as e:
        print(f"  {Colors.YELLOW}⚠{Colors.END}  Git: Could not check status")
    
    return all_good

def get_github_repo_url():
    """Get the GitHub repository URL"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Convert SSH to HTTPS if needed
            if url.startswith("git@github.com:"):
                url = url.replace("git@github.com:", "https://github.com/").replace(".git", "")
            elif url.endswith(".git"):
                url = url[:-4]
            return url
    except:
        pass
    return "https://github.com/IKRedHat/Nexus-Release-Readiness-Bot"

def deploy_via_dashboard():
    """Open Render dashboard for deployment"""
    print(f"\n{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    print(f"  ▶ Deployment Instructions")
    print(f"{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    
    repo_url = get_github_repo_url()
    
    print(f"""
  {Colors.CYAN}Step 1:{Colors.END} Go to Render Dashboard
          https://dashboard.render.com/

  {Colors.CYAN}Step 2:{Colors.END} Click "New +" → "Blueprint"
  
  {Colors.CYAN}Step 3:{Colors.END} Connect your GitHub repository:
          {Colors.YELLOW}{repo_url}{Colors.END}
  
  {Colors.CYAN}Step 4:{Colors.END} Render will detect render.yaml automatically
  
  {Colors.CYAN}Step 5:{Colors.END} Review and click "Apply"
  
  {Colors.GREEN}Environment Variables (auto-configured):{Colors.END}
  ┌─────────────────────────────┬────────────────────────────────┐
  │ Variable                    │ Value                          │
  ├─────────────────────────────┼────────────────────────────────┤
  │ NEXUS_ENV                   │ production                     │
  │ NEXUS_RBAC_ENABLED          │ true                           │
  │ NEXUS_JWT_SECRET            │ (auto-generated)               │
  │ NEXUS_ADMIN_EMAIL           │ admin@nexus.local              │
  │ NEXUS_CORS_ORIGINS          │ *.vercel.app                   │
  └─────────────────────────────┴────────────────────────────────┘
    """)
    
    print(f"\n  {Colors.BOLD}Would you like to open Render dashboard?{Colors.END}")
    response = input(f"  Open browser? [Y/n]: ").strip().lower()
    
    if response != 'n':
        webbrowser.open("https://dashboard.render.com/select-repo?type=blueprint")
        print(f"\n  {Colors.GREEN}✓{Colors.END} Opened Render dashboard in browser")

def show_post_deployment_steps():
    """Show steps after deployment"""
    print(f"\n{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    print(f"  ▶ Post-Deployment Steps")
    print(f"{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    
    print(f"""
  {Colors.CYAN}1.{Colors.END} Wait for Render to finish deploying (2-5 minutes)
  
  {Colors.CYAN}2.{Colors.END} Copy your Render URL (e.g., https://nexus-admin-api.onrender.com)
  
  {Colors.CYAN}3.{Colors.END} Update Vercel frontend with backend URL:
  
     {Colors.YELLOW}$ cd services/admin_dashboard/frontend{Colors.END}
     {Colors.YELLOW}$ vercel env add VITE_API_URL{Colors.END}
     → Enter: https://nexus-admin-api.onrender.com
     
  {Colors.CYAN}4.{Colors.END} Redeploy Vercel frontend:
  
     {Colors.YELLOW}$ vercel --prod{Colors.END}
  
  {Colors.CYAN}5.{Colors.END} Test the deployment:
     
     • Backend health: https://nexus-admin-api.onrender.com/health
     • Frontend: https://frontend-xxx.vercel.app
     • Login: admin@nexus.local (any password in dev mode)
    """)

def create_env_template():
    """Create .env.render template"""
    env_template = """# Render Environment Variables Template
# Copy these to your Render dashboard

# Application
NEXUS_ENV=production
PYTHONPATH=/opt/render/project/src/shared

# Authentication (auto-generated by Render)
# NEXUS_JWT_SECRET=<auto-generated>
NEXUS_RBAC_ENABLED=true
NEXUS_TOKEN_EXPIRE_MINUTES=60
NEXUS_REFRESH_TOKEN_DAYS=7
NEXUS_ADMIN_EMAIL=admin@nexus.local
NEXUS_SSO_PROVIDER=local

# CORS (update with your Vercel URL)
NEXUS_CORS_ORIGINS=https://frontend-8chgad0im-imrans-projects-8eb4b7ab.vercel.app,https://*.vercel.app

# Frontend URL (for redirects)
NEXUS_FRONTEND_URL=https://frontend-8chgad0im-imrans-projects-8eb4b7ab.vercel.app

# Optional: Redis (if using Render Redis)
# REDIS_URL=<from-render-redis-service>

# Optional: SSO Providers (configure in Render dashboard)
# OKTA_DOMAIN=
# OKTA_CLIENT_ID=
# OKTA_CLIENT_SECRET=
# AZURE_TENANT_ID=
# AZURE_CLIENT_ID=
# AZURE_CLIENT_SECRET=
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_SECRET=
# GITHUB_CLIENT_ID=
# GITHUB_CLIENT_SECRET=
"""
    
    env_file = Path(__file__).parent.parent / "services/admin_dashboard/backend/.env.render"
    env_file.write_text(env_template)
    print(f"  {Colors.GREEN}✓{Colors.END} Created .env.render template")
    return env_file

def main():
    print_header()
    
    if not check_prerequisites():
        print(f"\n{Colors.RED}❌ Prerequisites check failed!{Colors.END}")
        print("   Please fix the issues above and try again.")
        sys.exit(1)
    
    print(f"\n{Colors.GREEN}✓ All prerequisites met!{Colors.END}")
    
    # Create env template
    create_env_template()
    
    # Deploy via dashboard
    deploy_via_dashboard()
    
    # Show post-deployment steps
    show_post_deployment_steps()
    
    print(f"""
{Colors.CYAN}═══════════════════════════════════════════════════════════════════{Colors.END}
  {Colors.GREEN}🎉 Deployment process initiated!{Colors.END}
  
  After deployment, your backend will be available at:
  {Colors.YELLOW}https://nexus-admin-api.onrender.com{Colors.END}
  
  Need help? Check the docs:
  • Render: https://render.com/docs
  • Nexus: docs/deployment.md
{Colors.CYAN}═══════════════════════════════════════════════════════════════════{Colors.END}
    """)

if __name__ == "__main__":
    main()

