#!/usr/bin/env python3
"""
Generate index.html from template and package metadata.
This script creates a web page listing all packages in the repository.
"""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple

import yaml


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


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size // 1024}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f}MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f}GB"


def format_time_ago(timestamp: float) -> str:
    """Format timestamp as relative time."""
    now = time.time()
    diff = int(now - timestamp)

    if diff < 60:
        return "just now"
    elif diff < 3600:
        return f"{diff // 60} minutes ago"
    elif diff < 86400:
        return f"{diff // 3600} hours ago"
    else:
        return f"{diff // 86400} days ago"


def get_package_files(output_dir: Path, package_name: str) -> List[Tuple[str, int, float]]:
    """Get list of package files for a given package name."""
    package_files = []

    if not output_dir.exists():
        return package_files

    for file_path in output_dir.glob(f"{package_name}-*.pkg.tar.zst"):
        if file_path.is_file():
            stat = file_path.stat()
            package_files.append((file_path.name, stat.st_size, stat.st_mtime))

    return sorted(package_files)


def generate_package_table(packages: Dict[str, Any], output_dir: Path) -> str:
    """Generate HTML table rows for packages."""
    table_rows = []

    for pkg_name, pkg_data in packages.items():
        version = pkg_data.get('version', 'unknown')
        description = pkg_data.get('description', 'No description')

        package_files = get_package_files(output_dir, pkg_name)

        if package_files:
            for filename, size, mtime in package_files:
                size_str = format_size(size)
                time_str = format_time_ago(mtime)

                table_rows.append(f'''
                <tr>
                    <td><a href="{filename}">{pkg_name}</a></td>
                    <td>{version}</td>
                    <td>{description}</td>
                    <td>{size_str}</td>
                    <td>{time_str}</td>
                </tr>''')
        else:
            # Package not built yet
            table_rows.append(f'''
                <tr>
                    <td>{pkg_name}</td>
                    <td>{version}</td>
                    <td>{description}</td>
                    <td>-</td>
                    <td>not built</td>
                </tr>''')

    return ''.join(table_rows)


def main():
    """Main function to generate the index page."""
    repo_root = Path(__file__).parent.parent
    packages_file = repo_root / 'packages.yaml'
    template_file = repo_root / 'static' / 'index-template.html'
    output_dir = repo_root / 'x86_64'
    index_file = output_dir / 'index.html'

    log("Generating index.html from template and package metadata")

    # Check if required files exist
    if not packages_file.exists():
        error(f"packages.yaml not found at {packages_file}")
        sys.exit(1)

    if not template_file.exists():
        error(f"Template file not found: {template_file}")
        sys.exit(1)

    if not output_dir.exists():
        error(f"Output directory not found: {output_dir}")
        sys.exit(1)

    # Load packages configuration
    try:
        with open(packages_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        error(f"Failed to load packages.yaml: {e}")
        sys.exit(1)

    packages = config.get('packages', {})
    package_count = len(packages)

    # Generate package table
    package_table = generate_package_table(packages, output_dir)

    # Read template
    try:
        with open(template_file, 'r') as f:
            template_content = f.read()
    except Exception as e:
        error(f"Failed to read template file: {e}")
        sys.exit(1)

    # Replace placeholders
    generation_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    index_content = template_content.replace('{{GENERATION_TIME}}', generation_time)
    index_content = index_content.replace('{{PACKAGE_COUNT}}', str(package_count))
    index_content = index_content.replace('{{PACKAGE_TABLE}}', package_table)

    # Write index file
    try:
        with open(index_file, 'w') as f:
            f.write(index_content)
    except Exception as e:
        error(f"Failed to write index file: {e}")
        sys.exit(1)

    success(f"Generated index.html with {package_count} packages")
    log(f"Output: {index_file}")


if __name__ == '__main__':
    main()