#!/usr/bin/env python3
"""
Generate PKGBUILDs from templates and package metadata.
This script reads packages.yaml and generates static PKGBUILD files using Jinja2 templates.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

import yaml
from jinja2 import Environment, FileSystemLoader


def log(message: str) -> None:
    """Log a message with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def error(message: str) -> None:
    """Log an error message."""
    log(f"✗ ERROR: {message}")


def success(message: str) -> None:
    """Log a success message."""
    log(f"✓ {message}")


def generate_pkgbuild(package_name: str, data: Dict[str, Any], env: Environment) -> str:
    """Generate PKGBUILD content using Jinja2 templates."""
    upstream = data['upstream']
    upstream_type = upstream['type']

    # Select template based on upstream type
    template_file = f"{upstream_type}.pkgbuild.j2"

    try:
        template = env.get_template(template_file)
    except Exception as e:
        raise ValueError(f"Template {template_file} not found: {e}")

    # Prepare template variables by flattening the data structure
    template_vars = {
        'package_name': package_name,
        'version': data['version'],
        'pkgrel': data['pkgrel'],
        'description': data['description'],
        'architectures': data['architectures'],
        'url': data['url'],
        'license': data['license'],
        'depends': data.get('depends', []),
        'optdepends': data.get('optdepends', []),
        'makedepends': data.get('makedepends', []),
        'provides': data.get('provides', []),
        'conflicts': data.get('conflicts', []),
        'upstream': upstream
    }

    return template.render(**template_vars)


def main():
    """Main function to generate all PKGBUILDs."""
    repo_root = Path(__file__).parent.parent
    packages_file = repo_root / 'packages.yaml'
    pkgbuilds_dir = repo_root / 'pkgbuilds'
    templates_dir = repo_root / 'templates'

    if not packages_file.exists():
        error(f"packages.yaml not found at {packages_file}")
        sys.exit(1)

    if not templates_dir.exists():
        error(f"Templates directory not found at {templates_dir}")
        sys.exit(1)

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )

    log("Starting PKGBUILD generation process")

    # Load packages configuration
    try:
        with open(packages_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        error(f"Failed to load packages.yaml: {e}")
        sys.exit(1)

    packages = config.get('packages', {})
    if not packages:
        error("No packages found in packages.yaml")
        sys.exit(1)

    log(f"Found {len(packages)} packages to generate")

    # Generate PKGBUILDs for all packages
    for package_name, package_data in packages.items():
        log(f"Generating PKGBUILD for {package_name}")

        # Create package directory
        package_dir = pkgbuilds_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        # Generate PKGBUILD content
        try:
            pkgbuild_content = generate_pkgbuild(package_name, package_data, env)
        except Exception as e:
            error(f"Failed to generate PKGBUILD for {package_name}: {e}")
            continue

        # Write PKGBUILD file
        pkgbuild_file = package_dir / 'PKGBUILD'
        try:
            with open(pkgbuild_file, 'w') as f:
                f.write(pkgbuild_content)
            success(f"Generated {pkgbuild_file}")
        except Exception as e:
            error(f"Failed to write PKGBUILD for {package_name}: {e}")

    log("PKGBUILD generation completed")


if __name__ == '__main__':
    main()