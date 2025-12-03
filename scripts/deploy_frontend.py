#!/usr/bin/env python3
"""
Nexus Admin Dashboard - Frontend Deployment Script
===================================================

A comprehensive Python script for deploying the Nexus Admin Dashboard
frontend to Vercel with full automation, validation, and rollback capabilities.

Features:
- Multi-environment deployment (preview, production, staging)
- Automatic dependency management
- Build optimization and validation
- Environment variable management
- Deployment health checks
- Rollback support
- Detailed logging and reporting

Usage:
    python scripts/deploy_frontend.py --help
    python scripts/deploy_frontend.py --env preview
    python scripts/deploy_frontend.py --env production --api-url https://api.example.com
    python scripts/deploy_frontend.py --rollback --deployment-id dpl_xxx

Author: Nexus Team
Version: 2.3.0
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# Configuration
# ============================================================================

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DeploymentEnvironment(Enum):
    """Supported deployment environments"""
    PREVIEW = "preview"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DeploymentConfig:
    """Configuration for deployment"""
    project_name: str = "nexus-admin-dashboard"
    frontend_path: str = "services/admin_dashboard/frontend"
    build_dir: str = "dist"
    node_version: str = "20"
    npm_version: str = "9"
    
    # Default environment variables
    default_env_vars: Dict[str, str] = field(default_factory=lambda: {
        "VITE_APP_NAME": "Nexus Admin Dashboard",
        "VITE_APP_VERSION": "2.3.0",
        "VITE_ENABLE_MOCK_MODE": "false",
        "VITE_ENABLE_DEBUG": "false"
    })
    
    # Vercel regions
    regions: List[str] = field(default_factory=lambda: ["iad1"])
    
    # Build commands
    install_cmd: str = "npm install --legacy-peer-deps"
    build_cmd: str = "npm run build:prod"
    typecheck_cmd: str = "npm run typecheck"
    lint_cmd: str = "npm run lint"


@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    success: bool
    deployment_url: Optional[str] = None
    deployment_id: Optional[str] = None
    build_time: float = 0.0
    deploy_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging with colored output"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create custom formatter with colors
    class ColoredFormatter(logging.Formatter):
        FORMATS = {
            logging.DEBUG: f"{Colors.CYAN}%(asctime)s [DEBUG] %(message)s{Colors.ENDC}",
            logging.INFO: f"%(asctime)s [INFO] %(message)s",
            logging.WARNING: f"{Colors.YELLOW}%(asctime)s [WARN] %(message)s{Colors.ENDC}",
            logging.ERROR: f"{Colors.RED}%(asctime)s [ERROR] %(message)s{Colors.ENDC}",
            logging.CRITICAL: f"{Colors.RED}{Colors.BOLD}%(asctime)s [CRITICAL] %(message)s{Colors.ENDC}"
        }
        
        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
            return formatter.format(record)
    
    # Setup handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())
    
    # Setup logger
    logger = logging.getLogger("deploy_frontend")
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    return logger


# ============================================================================
# Utility Functions
# ============================================================================

def print_banner():
    """Print deployment script banner"""
    banner = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🚀 NEXUS FRONTEND DEPLOYMENT SCRIPT                            ║
║                                                                   ║
║   Deploy the Admin Dashboard to Vercel with confidence            ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝{Colors.ENDC}
    """
    print(banner)


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
    print(f"  {Colors.BLUE}▶ {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")


def print_success(message: str):
    """Print success message"""
    print(f"  {Colors.GREEN}✓{Colors.ENDC}  {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"  {Colors.YELLOW}⚠{Colors.ENDC}  {message}")


def print_error(message: str):
    """Print error message"""
    print(f"  {Colors.RED}✗{Colors.ENDC}  {message}")


def print_info(message: str):
    """Print info message"""
    print(f"  {Colors.CYAN}→{Colors.ENDC}  {message}")


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    timeout: int = 300
) -> Tuple[bool, str, str]:
    """
    Run a shell command and return success status, stdout, and stderr.
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        env: Environment variables
        capture_output: Whether to capture output
        timeout: Command timeout in seconds
    
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        # Merge with current environment
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=run_env,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        
        return (
            result.returncode == 0,
            result.stdout if capture_output else "",
            result.stderr if capture_output else ""
        )
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH"""
    return shutil.which(command) is not None


def get_project_root() -> Path:
    """Get the project root directory"""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def get_frontend_path(config: DeploymentConfig) -> Path:
    """Get the frontend directory path"""
    return get_project_root() / config.frontend_path


# ============================================================================
# Prerequisite Checks
# ============================================================================

class PrerequisiteChecker:
    """Check all prerequisites for deployment"""
    
    def __init__(self, config: DeploymentConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def check_all(self) -> bool:
        """Run all prerequisite checks"""
        print_section("Checking Prerequisites")
        
        checks = [
            ("Node.js", self._check_node),
            ("npm", self._check_npm),
            ("Vercel CLI", self._check_vercel),
            ("Git", self._check_git),
            ("Frontend Directory", self._check_frontend_dir),
            ("Package.json", self._check_package_json),
            ("Vercel Config", self._check_vercel_config),
            ("Vercel Authentication", self._check_vercel_auth)
        ]
        
        all_passed = True
        for name, check_func in checks:
            try:
                passed, message = check_func()
                if passed:
                    print_success(f"{name}: {message}")
                else:
                    print_error(f"{name}: {message}")
                    all_passed = False
            except Exception as e:
                print_error(f"{name}: Check failed - {e}")
                all_passed = False
        
        if self.warnings:
            print()
            for warning in self.warnings:
                print_warning(warning)
        
        return all_passed
    
    def _check_node(self) -> Tuple[bool, str]:
        """Check Node.js installation and version"""
        if not check_command_exists("node"):
            return False, "Not installed"
        
        success, stdout, _ = run_command(["node", "--version"])
        if not success:
            return False, "Unable to get version"
        
        version = stdout.strip().lstrip('v')
        major_version = int(version.split('.')[0])
        
        if major_version < 18:
            return False, f"Version {version} is too old (need 18+)"
        
        return True, f"v{version}"
    
    def _check_npm(self) -> Tuple[bool, str]:
        """Check npm installation and version"""
        if not check_command_exists("npm"):
            return False, "Not installed"
        
        success, stdout, _ = run_command(["npm", "--version"])
        if not success:
            return False, "Unable to get version"
        
        version = stdout.strip()
        return True, f"v{version}"
    
    def _check_vercel(self) -> Tuple[bool, str]:
        """Check Vercel CLI installation"""
        if not check_command_exists("vercel"):
            return False, "Not installed. Run: npm install -g vercel"
        
        success, stdout, _ = run_command(["vercel", "--version"])
        if not success:
            return False, "Unable to get version"
        
        version = stdout.strip().split('\n')[0]
        return True, version
    
    def _check_git(self) -> Tuple[bool, str]:
        """Check Git installation"""
        if not check_command_exists("git"):
            return False, "Not installed"
        
        success, stdout, _ = run_command(["git", "--version"])
        if not success:
            return False, "Unable to get version"
        
        version = stdout.strip()
        return True, version
    
    def _check_frontend_dir(self) -> Tuple[bool, str]:
        """Check frontend directory exists"""
        frontend_path = get_frontend_path(self.config)
        
        if not frontend_path.exists():
            return False, f"Directory not found: {frontend_path}"
        
        return True, str(frontend_path)
    
    def _check_package_json(self) -> Tuple[bool, str]:
        """Check package.json exists and is valid"""
        frontend_path = get_frontend_path(self.config)
        package_json = frontend_path / "package.json"
        
        if not package_json.exists():
            return False, "package.json not found"
        
        try:
            with open(package_json) as f:
                data = json.load(f)
            
            name = data.get("name", "unknown")
            version = data.get("version", "unknown")
            return True, f"{name}@{version}"
        except json.JSONDecodeError:
            return False, "Invalid JSON"
    
    def _check_vercel_config(self) -> Tuple[bool, str]:
        """Check vercel.json exists"""
        frontend_path = get_frontend_path(self.config)
        vercel_json = frontend_path / "vercel.json"
        
        if not vercel_json.exists():
            self.warnings.append("vercel.json not found - using defaults")
            return True, "Not found (using defaults)"
        
        try:
            with open(vercel_json) as f:
                data = json.load(f)
            return True, f"Found ({data.get('name', 'unnamed')})"
        except json.JSONDecodeError:
            return False, "Invalid JSON"
    
    def _check_vercel_auth(self) -> Tuple[bool, str]:
        """Check Vercel authentication"""
        success, stdout, stderr = run_command(["vercel", "whoami"])
        
        if not success:
            return False, "Not logged in. Run: vercel login"
        
        username = stdout.strip()
        return True, f"Logged in as {username}"


# ============================================================================
# Builder
# ============================================================================

class FrontendBuilder:
    """Build the frontend application"""
    
    def __init__(self, config: DeploymentConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.frontend_path = get_frontend_path(config)
    
    def build(self, env_vars: Dict[str, str]) -> Tuple[bool, float, List[str]]:
        """
        Build the frontend application.
        
        Args:
            env_vars: Environment variables for the build
        
        Returns:
            Tuple of (success, build_time_seconds, errors)
        """
        print_section("Building Frontend")
        errors = []
        start_time = time.time()
        
        # Step 1: Clean previous build
        print_info("Cleaning previous build...")
        dist_path = self.frontend_path / self.config.build_dir
        if dist_path.exists():
            shutil.rmtree(dist_path)
            print_success("Previous build cleaned")
        
        # Step 2: Install dependencies
        print_info("Installing dependencies...")
        success, stdout, stderr = run_command(
            self.config.install_cmd.split(),
            cwd=self.frontend_path,
            timeout=300
        )
        
        if not success:
            errors.append(f"Dependency installation failed: {stderr}")
            print_error("Dependency installation failed")
            return False, time.time() - start_time, errors
        
        print_success("Dependencies installed")
        
        # Step 3: Type checking (optional but recommended)
        print_info("Running type check...")
        success, stdout, stderr = run_command(
            self.config.typecheck_cmd.split(),
            cwd=self.frontend_path,
            env=env_vars,
            timeout=120
        )
        
        if not success:
            print_warning(f"Type check warnings: {stderr[:200]}...")
        else:
            print_success("Type check passed")
        
        # Step 4: Production build
        print_info("Building for production...")
        success, stdout, stderr = run_command(
            self.config.build_cmd.split(),
            cwd=self.frontend_path,
            env=env_vars,
            timeout=300
        )
        
        if not success:
            errors.append(f"Build failed: {stderr}")
            print_error("Build failed")
            return False, time.time() - start_time, errors
        
        print_success("Production build completed")
        
        # Step 5: Verify build output
        print_info("Verifying build output...")
        if not self._verify_build():
            errors.append("Build verification failed")
            print_error("Build verification failed")
            return False, time.time() - start_time, errors
        
        print_success("Build verified successfully")
        
        build_time = time.time() - start_time
        print_info(f"Build completed in {build_time:.1f}s")
        
        return True, build_time, errors
    
    def _verify_build(self) -> bool:
        """Verify the build output is valid"""
        dist_path = self.frontend_path / self.config.build_dir
        
        # Check dist directory exists
        if not dist_path.exists():
            self.logger.error("Build output directory not found")
            return False
        
        # Check index.html exists
        index_html = dist_path / "index.html"
        if not index_html.exists():
            self.logger.error("index.html not found in build output")
            return False
        
        # Check assets directory
        assets_dir = dist_path / "assets"
        if not assets_dir.exists():
            self.logger.error("assets directory not found in build output")
            return False
        
        # Check for JS files
        js_files = list(assets_dir.glob("**/*.js"))
        if not js_files:
            self.logger.error("No JavaScript files found in build output")
            return False
        
        # Check for CSS files
        css_files = list(assets_dir.glob("**/*.css"))
        if not css_files:
            self.logger.warning("No CSS files found in build output")
        
        self.logger.info(f"Build output: {len(js_files)} JS files, {len(css_files)} CSS files")
        return True
    
    def get_build_stats(self) -> Dict[str, Any]:
        """Get statistics about the build output"""
        dist_path = self.frontend_path / self.config.build_dir
        
        if not dist_path.exists():
            return {}
        
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "js_files": 0,
            "js_size_bytes": 0,
            "css_files": 0,
            "css_size_bytes": 0,
            "other_files": 0
        }
        
        for file in dist_path.rglob("*"):
            if file.is_file():
                size = file.stat().st_size
                stats["total_files"] += 1
                stats["total_size_bytes"] += size
                
                if file.suffix == ".js":
                    stats["js_files"] += 1
                    stats["js_size_bytes"] += size
                elif file.suffix == ".css":
                    stats["css_files"] += 1
                    stats["css_size_bytes"] += size
                else:
                    stats["other_files"] += 1
        
        return stats


# ============================================================================
# Deployer
# ============================================================================

class VercelDeployer:
    """Deploy to Vercel"""
    
    def __init__(self, config: DeploymentConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.frontend_path = get_frontend_path(config)
    
    def deploy(
        self,
        environment: DeploymentEnvironment,
        env_vars: Dict[str, str]
    ) -> DeploymentResult:
        """
        Deploy to Vercel.
        
        Args:
            environment: Target deployment environment
            env_vars: Environment variables to set
        
        Returns:
            DeploymentResult with deployment details
        """
        print_section(f"Deploying to Vercel ({environment.value})")
        
        result = DeploymentResult(success=False)
        start_time = time.time()
        
        # Step 1: Set environment variables
        if env_vars:
            print_info("Setting environment variables...")
            self._set_env_vars(env_vars, environment)
            print_success(f"Set {len(env_vars)} environment variables")
        
        # Step 2: Deploy
        print_info(f"Deploying to {environment.value}...")
        
        cmd = ["vercel", "deploy"]
        
        if environment == DeploymentEnvironment.PRODUCTION:
            cmd.append("--prod")
        
        # Add yes flag to skip prompts
        cmd.append("--yes")
        
        success, stdout, stderr = run_command(
            cmd,
            cwd=self.frontend_path,
            timeout=600
        )
        
        if not success:
            result.errors.append(f"Deployment failed: {stderr}")
            print_error("Deployment failed")
            print_error(stderr[:500] if stderr else "No error details")
            return result
        
        # Parse deployment URL from output
        deployment_url = self._parse_deployment_url(stdout)
        deployment_id = self._parse_deployment_id(stdout)
        
        if deployment_url:
            result.deployment_url = deployment_url
            result.deployment_id = deployment_id
            print_success(f"Deployed to: {deployment_url}")
        else:
            # Try to get URL from vercel ls
            deployment_url = self._get_latest_deployment_url()
            if deployment_url:
                result.deployment_url = deployment_url
                print_success(f"Deployed to: {deployment_url}")
        
        result.success = True
        result.deploy_time = time.time() - start_time
        result.logs.append(stdout)
        
        print_info(f"Deployment completed in {result.deploy_time:.1f}s")
        
        return result
    
    def _set_env_vars(
        self,
        env_vars: Dict[str, str],
        environment: DeploymentEnvironment
    ):
        """Set environment variables in Vercel"""
        env_target = environment.value
        
        for key, value in env_vars.items():
            # Try to remove existing var first (ignore errors)
            run_command(
                ["vercel", "env", "rm", key, env_target, "--yes"],
                cwd=self.frontend_path,
                capture_output=True
            )
            
            # Add new var
            process = subprocess.Popen(
                ["vercel", "env", "add", key, env_target],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.frontend_path,
                text=True
            )
            process.communicate(input=value)
    
    def _parse_deployment_url(self, output: str) -> Optional[str]:
        """Parse deployment URL from Vercel output"""
        # Look for production URL or preview URL
        patterns = [
            r'https://[a-zA-Z0-9-]+\.vercel\.app',
            r'https://[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+\.vercel\.app'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(0)
        
        return None
    
    def _parse_deployment_id(self, output: str) -> Optional[str]:
        """Parse deployment ID from Vercel output"""
        match = re.search(r'(dpl_[a-zA-Z0-9]+)', output)
        return match.group(1) if match else None
    
    def _get_latest_deployment_url(self) -> Optional[str]:
        """Get the latest deployment URL from vercel ls"""
        success, stdout, _ = run_command(
            ["vercel", "ls", "--json"],
            cwd=self.frontend_path
        )
        
        if not success:
            return None
        
        try:
            # Parse JSON output - it might be multiple lines
            for line in stdout.strip().split('\n'):
                if line.startswith('['):
                    deployments = json.loads(line)
                    if deployments:
                        return deployments[0].get('url')
        except json.JSONDecodeError:
            pass
        
        return None
    
    def rollback(self, deployment_id: str) -> bool:
        """
        Rollback to a previous deployment.
        
        Args:
            deployment_id: The deployment ID to rollback to
        
        Returns:
            True if rollback succeeded
        """
        print_section(f"Rolling Back to {deployment_id}")
        
        success, stdout, stderr = run_command(
            ["vercel", "rollback", deployment_id, "--yes"],
            cwd=self.frontend_path,
            timeout=120
        )
        
        if success:
            print_success("Rollback completed successfully")
        else:
            print_error(f"Rollback failed: {stderr}")
        
        return success
    
    def list_deployments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent deployments"""
        success, stdout, _ = run_command(
            ["vercel", "ls", "--json"],
            cwd=self.frontend_path
        )
        
        if not success:
            return []
        
        try:
            for line in stdout.strip().split('\n'):
                if line.startswith('['):
                    deployments = json.loads(line)
                    return deployments[:limit]
        except json.JSONDecodeError:
            pass
        
        return []


# ============================================================================
# Health Checker
# ============================================================================

class DeploymentHealthChecker:
    """Verify deployment health"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def check_health(self, url: str, retries: int = 5, delay: int = 10) -> bool:
        """
        Check deployment health by hitting the URL.
        
        Args:
            url: Deployment URL to check
            retries: Number of retry attempts
            delay: Delay between retries in seconds
        
        Returns:
            True if deployment is healthy
        """
        print_section("Verifying Deployment Health")
        
        import urllib.request
        import urllib.error
        
        for attempt in range(1, retries + 1):
            print_info(f"Health check attempt {attempt}/{retries}...")
            
            try:
                req = urllib.request.Request(url, method='HEAD')
                req.add_header('User-Agent', 'Nexus-Deploy-Script/2.3.0')
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    status_code = response.status
                    
                    if status_code == 200:
                        print_success(f"Deployment is healthy (HTTP {status_code})")
                        return True
                    else:
                        print_warning(f"Unexpected status code: {status_code}")
                        
            except urllib.error.HTTPError as e:
                print_warning(f"HTTP error: {e.code}")
            except urllib.error.URLError as e:
                print_warning(f"URL error: {e.reason}")
            except Exception as e:
                print_warning(f"Error: {e}")
            
            if attempt < retries:
                print_info(f"Waiting {delay}s before retry...")
                time.sleep(delay)
        
        print_error("Health check failed after all retries")
        return False


# ============================================================================
# Report Generator
# ============================================================================

class DeploymentReportGenerator:
    """Generate deployment reports"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def generate_report(
        self,
        result: DeploymentResult,
        environment: DeploymentEnvironment,
        build_stats: Dict[str, Any]
    ) -> str:
        """Generate a deployment report"""
        
        report = f"""
{Colors.CYAN}═══════════════════════════════════════════════════════════════════{Colors.ENDC}
{Colors.BOLD}  DEPLOYMENT REPORT{Colors.ENDC}
{Colors.CYAN}═══════════════════════════════════════════════════════════════════{Colors.ENDC}

  {Colors.BOLD}Status:{Colors.ENDC}        {'✅ SUCCESS' if result.success else '❌ FAILED'}
  {Colors.BOLD}Environment:{Colors.ENDC}   {environment.value.upper()}
  {Colors.BOLD}Timestamp:{Colors.ENDC}     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  
  {Colors.BOLD}Deployment URL:{Colors.ENDC}
    {result.deployment_url or 'N/A'}
  
  {Colors.BOLD}Deployment ID:{Colors.ENDC}
    {result.deployment_id or 'N/A'}

  {Colors.BOLD}Timings:{Colors.ENDC}
    Build Time:  {result.build_time:.1f}s
    Deploy Time: {result.deploy_time:.1f}s
    Total Time:  {result.build_time + result.deploy_time:.1f}s

  {Colors.BOLD}Build Statistics:{Colors.ENDC}
    Total Files:    {build_stats.get('total_files', 0)}
    Total Size:     {self._format_size(build_stats.get('total_size_bytes', 0))}
    JS Files:       {build_stats.get('js_files', 0)} ({self._format_size(build_stats.get('js_size_bytes', 0))})
    CSS Files:      {build_stats.get('css_files', 0)} ({self._format_size(build_stats.get('css_size_bytes', 0))})
"""
        
        if result.errors:
            report += f"""
  {Colors.RED}{Colors.BOLD}Errors:{Colors.ENDC}
"""
            for error in result.errors:
                report += f"    • {error}\n"
        
        if result.warnings:
            report += f"""
  {Colors.YELLOW}{Colors.BOLD}Warnings:{Colors.ENDC}
"""
            for warning in result.warnings:
                report += f"    • {warning}\n"
        
        report += f"""
{Colors.CYAN}═══════════════════════════════════════════════════════════════════{Colors.ENDC}
"""
        
        return report
    
    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def save_report(self, report: str, filepath: Path):
        """Save report to file (without ANSI colors)"""
        # Strip ANSI codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_report = ansi_escape.sub('', report)
        
        with open(filepath, 'w') as f:
            f.write(clean_report)
        
        print_info(f"Report saved to: {filepath}")


# ============================================================================
# Main Deployment Orchestrator
# ============================================================================

class DeploymentOrchestrator:
    """Orchestrate the complete deployment process"""
    
    def __init__(self, config: DeploymentConfig, verbose: bool = False):
        self.config = config
        self.logger = setup_logging(verbose)
        self.checker = PrerequisiteChecker(config, self.logger)
        self.builder = FrontendBuilder(config, self.logger)
        self.deployer = VercelDeployer(config, self.logger)
        self.health_checker = DeploymentHealthChecker(self.logger)
        self.report_generator = DeploymentReportGenerator(self.logger)
    
    def deploy(
        self,
        environment: DeploymentEnvironment,
        api_url: Optional[str] = None,
        skip_build: bool = False,
        skip_health_check: bool = False
    ) -> DeploymentResult:
        """
        Execute full deployment pipeline.
        
        Args:
            environment: Target environment
            api_url: Backend API URL
            skip_build: Skip the build step
            skip_health_check: Skip health verification
        
        Returns:
            DeploymentResult with all details
        """
        print_banner()
        
        # Prepare environment variables
        env_vars = self.config.default_env_vars.copy()
        if api_url:
            env_vars["VITE_API_URL"] = api_url
        
        # Step 1: Check prerequisites
        if not self.checker.check_all():
            return DeploymentResult(
                success=False,
                errors=["Prerequisites check failed"]
            )
        
        result = DeploymentResult(success=True)
        
        # Step 2: Build (if not skipped)
        if not skip_build:
            build_success, build_time, build_errors = self.builder.build(env_vars)
            result.build_time = build_time
            
            if not build_success:
                result.success = False
                result.errors.extend(build_errors)
                return result
        else:
            print_section("Skipping Build (--skip-build)")
            print_info("Using existing build output")
        
        # Step 3: Deploy
        deploy_result = self.deployer.deploy(environment, env_vars)
        
        result.success = deploy_result.success
        result.deployment_url = deploy_result.deployment_url
        result.deployment_id = deploy_result.deployment_id
        result.deploy_time = deploy_result.deploy_time
        result.errors.extend(deploy_result.errors)
        result.logs.extend(deploy_result.logs)
        
        if not result.success:
            return result
        
        # Step 4: Health check (if not skipped)
        if not skip_health_check and result.deployment_url:
            health_ok = self.health_checker.check_health(result.deployment_url)
            if not health_ok:
                result.warnings.append("Deployment health check failed")
        
        # Step 5: Generate report
        build_stats = self.builder.get_build_stats()
        report = self.report_generator.generate_report(result, environment, build_stats)
        print(report)
        
        # Save report
        reports_dir = get_project_root() / "reports"
        reports_dir.mkdir(exist_ok=True)
        report_file = reports_dir / f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.report_generator.save_report(report, report_file)
        
        return result
    
    def rollback(self, deployment_id: str) -> bool:
        """Rollback to a previous deployment"""
        print_banner()
        return self.deployer.rollback(deployment_id)
    
    def list_deployments(self, limit: int = 10):
        """List recent deployments"""
        print_banner()
        print_section("Recent Deployments")
        
        deployments = self.deployer.list_deployments(limit)
        
        if not deployments:
            print_warning("No deployments found")
            return
        
        print(f"\n  {'URL':<50} {'State':<12} {'Created':<20}")
        print(f"  {'-'*50} {'-'*12} {'-'*20}")
        
        for dep in deployments:
            url = dep.get('url', 'N/A')[:48]
            state = dep.get('state', 'N/A')
            created = dep.get('created', 'N/A')
            
            if isinstance(created, int):
                created = datetime.fromtimestamp(created / 1000).strftime('%Y-%m-%d %H:%M')
            
            print(f"  {url:<50} {state:<12} {created:<20}")


# ============================================================================
# CLI Entry Point
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Deploy Nexus Admin Dashboard to Vercel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Deploy to preview:
    %(prog)s --env preview

  Deploy to production:
    %(prog)s --env production

  Deploy with custom API URL:
    %(prog)s --env production --api-url https://api.example.com

  Rollback to previous deployment:
    %(prog)s --rollback --deployment-id dpl_xxxxx

  List recent deployments:
    %(prog)s --list

For more information, see docs/frontend-deployment-guide.md
        """
    )
    
    # Deployment options
    parser.add_argument(
        "--env", "-e",
        type=str,
        choices=["preview", "staging", "production"],
        default="preview",
        help="Target deployment environment (default: preview)"
    )
    
    parser.add_argument(
        "--api-url",
        type=str,
        help="Backend API URL to use"
    )
    
    # Build options
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip the build step (use existing dist/)"
    )
    
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip deployment health verification"
    )
    
    # Rollback options
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback to a previous deployment"
    )
    
    parser.add_argument(
        "--deployment-id",
        type=str,
        help="Deployment ID for rollback (e.g., dpl_xxxxx)"
    )
    
    # List option
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List recent deployments"
    )
    
    # Verbosity
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    config = DeploymentConfig()
    orchestrator = DeploymentOrchestrator(config, verbose=args.verbose)
    
    try:
        # Handle list command
        if args.list:
            orchestrator.list_deployments()
            return 0
        
        # Handle rollback command
        if args.rollback:
            if not args.deployment_id:
                print_error("--deployment-id is required for rollback")
                return 1
            
            success = orchestrator.rollback(args.deployment_id)
            return 0 if success else 1
        
        # Handle deployment
        environment = DeploymentEnvironment(args.env)
        
        result = orchestrator.deploy(
            environment=environment,
            api_url=args.api_url,
            skip_build=args.skip_build,
            skip_health_check=args.skip_health_check
        )
        
        if result.success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Deployment successful!{Colors.ENDC}")
            if result.deployment_url:
                print(f"   {Colors.CYAN}→ {result.deployment_url}{Colors.ENDC}\n")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Deployment failed!{Colors.ENDC}")
            for error in result.errors:
                print(f"   {Colors.RED}→ {error}{Colors.ENDC}")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Deployment cancelled by user{Colors.ENDC}")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.ENDC}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

