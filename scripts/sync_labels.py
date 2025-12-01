#!/usr/bin/env python3
"""
GitHub Labels Sync Script
=========================

Syncs labels from .github/labels.yml to your GitHub repository.

Usage:
    export GITHUB_TOKEN=your_token_here
    python scripts/sync_labels.py

Or:
    python scripts/sync_labels.py --token YOUR_TOKEN

Requirements:
    pip install requests pyyaml
"""

import os
import sys
import argparse
import requests
import yaml
from typing import List, Dict, Any

# Configuration
REPO_OWNER = "IKRedHat"
REPO_NAME = "Nexus-Release-Readiness-Bot"
LABELS_FILE = ".github/labels.yml"
GITHUB_API_BASE = "https://api.github.com"


def load_labels_from_file(filepath: str) -> List[Dict[str, str]]:
    """Load labels from YAML file."""
    with open(filepath, 'r') as f:
        labels = yaml.safe_load(f)
    return labels


def get_existing_labels(token: str) -> Dict[str, Dict[str, str]]:
    """Get all existing labels from the repository."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    labels = {}
    page = 1
    
    while True:
        response = requests.get(
            f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels",
            headers=headers,
            params={"page": page, "per_page": 100}
        )
        response.raise_for_status()
        
        page_labels = response.json()
        if not page_labels:
            break
            
        for label in page_labels:
            labels[label["name"]] = {
                "color": label["color"],
                "description": label.get("description", "")
            }
        
        page += 1
    
    return labels


def create_label(token: str, name: str, color: str, description: str) -> bool:
    """Create a new label."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": name,
        "color": color.lstrip('#'),
        "description": description or ""
    }
    
    response = requests.post(
        f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        print(f"  ✅ Created: {name}")
        return True
    else:
        print(f"  ❌ Failed to create {name}: {response.json().get('message', 'Unknown error')}")
        return False


def update_label(token: str, name: str, color: str, description: str) -> bool:
    """Update an existing label."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "new_name": name,
        "color": color.lstrip('#'),
        "description": description or ""
    }
    
    response = requests.patch(
        f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels/{requests.utils.quote(name, safe='')}",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        print(f"  🔄 Updated: {name}")
        return True
    else:
        print(f"  ❌ Failed to update {name}: {response.json().get('message', 'Unknown error')}")
        return False


def delete_label(token: str, name: str) -> bool:
    """Delete a label."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.delete(
        f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels/{requests.utils.quote(name, safe='')}",
        headers=headers
    )
    
    if response.status_code == 204:
        print(f"  🗑️  Deleted: {name}")
        return True
    else:
        print(f"  ❌ Failed to delete {name}")
        return False


def sync_labels(token: str, dry_run: bool = False, delete_extra: bool = False):
    """Sync labels from file to GitHub."""
    print(f"\n🏷️  GitHub Labels Sync")
    print(f"{'=' * 50}")
    print(f"Repository: {REPO_OWNER}/{REPO_NAME}")
    print(f"Labels file: {LABELS_FILE}")
    print(f"Dry run: {dry_run}")
    print(f"Delete extra: {delete_extra}")
    print(f"{'=' * 50}\n")
    
    # Load desired labels
    print("📂 Loading labels from file...")
    desired_labels = load_labels_from_file(LABELS_FILE)
    print(f"   Found {len(desired_labels)} labels in file\n")
    
    # Get existing labels
    print("🌐 Fetching existing labels from GitHub...")
    existing_labels = get_existing_labels(token)
    print(f"   Found {len(existing_labels)} labels on GitHub\n")
    
    # Convert desired labels to dict for easier lookup
    desired_dict = {
        label["name"]: {
            "color": label["color"].lstrip('#'),
            "description": label.get("description", "")
        }
        for label in desired_labels
    }
    
    # Statistics
    created = 0
    updated = 0
    deleted = 0
    unchanged = 0
    
    # Create or update labels
    print("🔄 Processing labels...\n")
    
    for name, props in desired_dict.items():
        if name in existing_labels:
            # Check if update needed
            existing = existing_labels[name]
            if (existing["color"].lower() != props["color"].lower() or 
                existing["description"] != props["description"]):
                if dry_run:
                    print(f"  [DRY RUN] Would update: {name}")
                    updated += 1
                else:
                    if update_label(token, name, props["color"], props["description"]):
                        updated += 1
            else:
                unchanged += 1
        else:
            # Create new label
            if dry_run:
                print(f"  [DRY RUN] Would create: {name}")
                created += 1
            else:
                if create_label(token, name, props["color"], props["description"]):
                    created += 1
    
    # Delete extra labels (if enabled)
    if delete_extra:
        print("\n🗑️  Checking for labels to delete...\n")
        for name in existing_labels:
            if name not in desired_dict:
                if dry_run:
                    print(f"  [DRY RUN] Would delete: {name}")
                    deleted += 1
                else:
                    if delete_label(token, name):
                        deleted += 1
    
    # Summary
    print(f"\n{'=' * 50}")
    print("📊 Summary:")
    print(f"   ✅ Created: {created}")
    print(f"   🔄 Updated: {updated}")
    print(f"   ⏭️  Unchanged: {unchanged}")
    if delete_extra:
        print(f"   🗑️  Deleted: {deleted}")
    print(f"{'=' * 50}\n")
    
    if dry_run:
        print("ℹ️  This was a dry run. Run without --dry-run to apply changes.\n")


def main():
    parser = argparse.ArgumentParser(description="Sync GitHub labels from YAML file")
    parser.add_argument("--token", "-t", help="GitHub personal access token")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Preview changes without applying")
    parser.add_argument("--delete-extra", action="store_true", help="Delete labels not in the YAML file")
    
    args = parser.parse_args()
    
    # Get token
    token = args.token or os.environ.get("GITHUB_TOKEN")
    
    if not token:
        print("❌ Error: GitHub token required.")
        print("   Set GITHUB_TOKEN environment variable or use --token flag")
        sys.exit(1)
    
    # Change to repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)
    
    # Check if labels file exists
    if not os.path.exists(LABELS_FILE):
        print(f"❌ Error: Labels file not found: {LABELS_FILE}")
        sys.exit(1)
    
    try:
        sync_labels(token, dry_run=args.dry_run, delete_extra=args.delete_extra)
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

