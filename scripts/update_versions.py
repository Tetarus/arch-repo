#!/usr/bin/env python3
"""
Update package versions by checking upstream sources.
This script reads packages.yaml and updates versions from upstream sources.
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import yaml


def log(message: str) -> None:
    """Log a message with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def warn(message: str) -> None:
    """Log a warning message."""
    log(f"⚠ WARNING: {message}")


def error(message: str) -> None:
    """Log an error message."""
    log(f"✗ ERROR: {message}")


def success(message: str) -> None:
    """Log a success message."""
    log(f"✓ {message}")


def make_request(url: str, timeout: int = 30) -> str:
    """Make an HTTP request with proper headers and error handling."""
    headers = {
        'User-Agent': 'Arch-Repo-Bot/1.0 (https://github.com/tetarus/arch-repo)',
        'Accept': 'application/json',
    }

    try:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode('utf-8')
    except (URLError, HTTPError) as e:
        error(f"Failed to fetch {url}: {e}")
        raise


def normalize_version(version: str, tag_prefix: str = "") -> str:
    """Normalize version string by removing prefixes and converting format."""
    # Remove tag prefix if specified
    if tag_prefix and version.startswith(tag_prefix):
        version = version[len(tag_prefix):]

    # Remove common version prefixes
    version = re.sub(r'^v?', '', version)

    # Convert hyphens to dots for consistency
    version = version.replace('-', '.')

    return version


def check_github_release(repo: str, tag_prefix: str = "", only_stable: bool = True) -> Optional[str]:
    """Check latest release from GitHub API."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        response = make_request(url)
        data = json.loads(response)

        # Skip prereleases if only_stable is True
        if only_stable and data.get('prerelease', False):
            log(f"Skipping prerelease {data['tag_name']} for {repo}")
            return None

        tag_name = data['tag_name']
        return normalize_version(tag_name, tag_prefix)

    except Exception as e:
        error(f"Failed to check GitHub release for {repo}: {e}")
        return None


def check_gcs_version(bucket_url: str, version_endpoint: str) -> Optional[str]:
    """Check version from Google Cloud Storage endpoint."""
    url = f"{bucket_url}/{version_endpoint}"

    try:
        response = make_request(url)
        version = response.strip()
        return normalize_version(version)

    except Exception as e:
        error(f"Failed to check GCS version at {url}: {e}")
        return None


def update_package_version(package_name: str, package_data: Dict[str, Any]) -> Tuple[str, bool]:
    """Update version for a single package. Returns (new_version, was_updated)."""
    current_version = package_data['version']
    upstream = package_data['upstream']

    log(f"Checking version for {package_name} (current: {current_version})")

    new_version = None

    if upstream['type'] == 'github':
        new_version = check_github_release(
            upstream['repo'],
            upstream.get('tag_prefix', ''),
            upstream.get('only_stable', True)
        )
    elif upstream['type'] == 'gcs':
        new_version = check_gcs_version(
            upstream['bucket_url'],
            upstream['version_endpoint']
        )
    else:
        error(f"Unknown upstream type: {upstream['type']}")
        return current_version, False

    if new_version is None:
        warn(f"Failed to get new version for {package_name}")
        return current_version, False

    if new_version != current_version:
        success(f"{package_name}: {current_version} → {new_version}")
        return new_version, True
    else:
        log(f"{package_name}: No version change")
        return current_version, False


def main():
    """Main function to update all package versions."""
    repo_root = Path(__file__).parent.parent
    packages_file = repo_root / 'packages.yaml'

    if not packages_file.exists():
        error(f"packages.yaml not found at {packages_file}")
        sys.exit(1)

    log("Starting package version update process")

    # Load packages configuration
    try:
        with open(packages_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        error(f"Failed to load packages.yaml: {e}")
        sys.exit(1)

    packages = config.get('packages', {})
    if not packages:
        warn("No packages found in packages.yaml")
        return

    log(f"Found {len(packages)} packages to check")

    updated_packages = []

    # Update versions for all packages
    for package_name, package_data in packages.items():
        new_version, was_updated = update_package_version(package_name, package_data)

        if was_updated:
            # Update version in the config
            config['packages'][package_name]['version'] = new_version
            # Reset pkgrel to 1 when version changes
            config['packages'][package_name]['pkgrel'] = 1
            updated_packages.append(package_name)

    # Write updated configuration back to file
    if updated_packages:
        log(f"Updating packages.yaml with {len(updated_packages)} changes")
        try:
            with open(packages_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            success(f"Updated packages: {', '.join(updated_packages)}")
        except Exception as e:
            error(f"Failed to write packages.yaml: {e}")
            sys.exit(1)
    else:
        log("No version updates found")

    log("Version update process completed")


if __name__ == '__main__':
    main()