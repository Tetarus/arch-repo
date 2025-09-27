#!/usr/bin/env python3
"""
Generate PKGBUILDs from templates and package metadata.
This script reads packages.yaml and generates static PKGBUILD files.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List

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


def format_array(items: List[str], indent: int = 0) -> str:
    """Format a list of items as a bash array."""
    if not items:
        return "()"

    if len(items) == 1:
        return f"('{items[0]}')"

    indent_str = " " * indent
    lines = [f"("]
    for item in items:
        lines.append(f"  '{item}'")
    lines.append(")")

    return "\n".join(f"{indent_str}{line}" for line in lines)


def generate_github_pkgbuild(package_name: str, data: Dict[str, Any]) -> str:
    """Generate PKGBUILD for GitHub-based package."""
    upstream = data['upstream']
    repo = upstream['repo']
    tag_prefix = upstream.get('tag_prefix', '')
    asset_pattern = upstream.get('asset_pattern', '')

    # Format dependencies
    depends = format_array(data.get('depends', []))
    optdepends = format_array(data.get('optdepends', []))
    makedepends = format_array(data.get('makedepends', []))
    provides = format_array(data.get('provides', []))
    conflicts = format_array(data.get('conflicts', []))

    return f"""# Maintainer: Tetarus
pkgname={package_name}
pkgver={data['version']}
pkgrel={data['pkgrel']}
pkgdesc="{data['description']}"
arch=({format_array(data['architectures'])[1:-1]})
url="{data['url']}"
license=('{data['license']}')
provides={provides}
conflicts={conflicts}
depends={depends}
optdepends={optdepends}
makedepends={makedepends}
options=(!debug)

prepare() {{
  cd "${{srcdir}}"

  local ver="${{pkgver}}"
  local tag="{tag_prefix}${{ver}}"

  local url="$(curl -fsSL "https://api.github.com/repos/{repo}/releases/tags/${{tag}}" \\
    | jq -r '.assets[] | select(.name | contains("{asset_pattern}")) | .browser_download_url' \\
    | head -n1)"

  if [[ -z "$url" ]]; then
    error "Failed to find download URL for version ${{ver}}"
    return 1
  fi

  curl -fL "$url" -o "codex.tar.gz"
  tar -xzf "codex.tar.gz"
}}

package() {{
  cd "${{srcdir}}"

  install -Dm755 "codex-{asset_pattern}" "$pkgdir/usr/bin/codex"
}}
"""


def generate_gcs_pkgbuild(package_name: str, data: Dict[str, Any]) -> str:
    """Generate PKGBUILD for GCS-based package."""
    upstream = data['upstream']
    bucket_url = upstream['bucket_url']
    platform_name = upstream['platform_name']
    checksum_verification = upstream.get('checksum_verification', False)

    # Format dependencies
    depends = format_array(data.get('depends', []))
    optdepends = format_array(data.get('optdepends', []))
    makedepends = format_array(data.get('makedepends', []))
    provides = format_array(data.get('provides', []))
    conflicts = format_array(data.get('conflicts', []))

    checksum_code = ""
    if checksum_verification:
        checksum_code = f'''
  # Download manifest to get checksum
  curl -fsSL -o manifest.json "${{_gcs_bucket}}/${{version}}/manifest.json"

  # Extract checksum for {platform_name} platform
  local expected_checksum
  if command -v jq >/dev/null 2>&1; then
    expected_checksum=$(jq -r '.platforms["{platform_name}"].checksum // empty' manifest.json)
  else
    # Fallback: extract checksum using bash regex
    local json=$(cat manifest.json | tr -d '\\n\\r\\t' | sed 's/ \\+/ /g')
    if [[ $json =~ \\"{platform_name}\\"[^}}]*\\"checksum\\"[[:space:]]*:[[:space:]]*\\"([a-f0-9]{{64}})\\" ]]; then
      expected_checksum="${{BASH_REMATCH[1]}}"
    fi
  fi

  if [ -z "$expected_checksum" ] || [[ ! "$expected_checksum" =~ ^[a-f0-9]{{64}}$ ]]; then
    error "Failed to extract valid checksum for {platform_name} platform"
    return 1
  fi

  msg "Expected checksum: $expected_checksum"

  # Download the binary
  curl -fsSL -o "claude" "${{_gcs_bucket}}/${{version}}/{platform_name}/claude"

  # Verify checksum
  local actual_checksum=$(sha256sum claude | cut -d' ' -f1)
  if [ "$actual_checksum" != "$expected_checksum" ]; then
    error "Checksum verification failed"
    error "Expected: $expected_checksum"
    error "Actual:   $actual_checksum"
    return 1
  fi

  msg "Checksum verification successful"'''
    else:
        checksum_code = f'''
  # Download the binary
  curl -fsSL -o "claude" "${{_gcs_bucket}}/${{version}}/{platform_name}/claude"'''

    license_section = ""
    if data['license'] == 'custom':
        license_section = f'''
  # Create a simple license file since it's proprietary
  install -Dm644 /dev/stdin "$pkgdir/usr/share/licenses/$pkgname/LICENSE" << 'EOF'
{package_name.replace('-bin', '').title()} is proprietary software.
For terms of service, visit: {data['url']}
EOF'''

    return f"""# Maintainer: Tetarus
pkgname={package_name}
pkgver={data['version']}
pkgrel={data['pkgrel']}
pkgdesc="{data['description']}"
arch=({format_array(data['architectures'])[1:-1]})
url="{data['url']}"
license=('{data['license']}')
depends={depends}
provides={provides}
conflicts={conflicts}
source=()
sha256sums=()
options=(!strip !debug)

_gcs_bucket="{bucket_url}"

prepare() {{
  cd "$srcdir"

  # Get current version
  local version="${{pkgver}}"
  msg "Downloading {package_name.title()} version $version"
{checksum_code}

  chmod +x "claude"
}}

package() {{
  cd "$srcdir"

  # Install the binary
  install -Dm755 "claude" "$pkgdir/usr/bin/claude"
{license_section}
}}
"""


def generate_pkgbuild(package_name: str, data: Dict[str, Any]) -> str:
    """Generate PKGBUILD content based on package type."""
    upstream = data['upstream']

    if upstream['type'] == 'github':
        return generate_github_pkgbuild(package_name, data)
    elif upstream['type'] == 'gcs':
        return generate_gcs_pkgbuild(package_name, data)
    else:
        raise ValueError(f"Unsupported upstream type: {upstream['type']}")


def main():
    """Main function to generate all PKGBUILDs."""
    repo_root = Path(__file__).parent.parent
    packages_file = repo_root / 'packages.yaml'
    pkgbuilds_dir = repo_root / 'pkgbuilds'

    if not packages_file.exists():
        error(f"packages.yaml not found at {packages_file}")
        sys.exit(1)

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
            pkgbuild_content = generate_pkgbuild(package_name, package_data)
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