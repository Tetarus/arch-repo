#!/bin/bash
# build-all.sh - Build all packages using the new metadata-driven system

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$REPO_DIR/x86_64"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

# Check if we're running as root
if [[ $EUID -eq 0 ]]; then
    error "This script should not be run as root!"
    error "makepkg cannot be run as root. Please run as a regular user."
    exit 1
fi

# Check if makepkg is available
if ! command -v makepkg &> /dev/null; then
    error "makepkg is not installed. Please install base-devel package."
    exit 1
fi

# Check if Python dependencies are installed
if ! python3 -c "import yaml" &> /dev/null; then
    error "Python dependencies not installed. Please run: pip install -r requirements.txt"
    exit 1
fi

cd "$REPO_DIR"

log "Generating PKGBUILDs from metadata..."
if ! python3 scripts/generate_pkgbuilds.py; then
    error "Failed to generate PKGBUILDs"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get list of packages from metadata
PACKAGES=$(python3 -c "
import yaml
with open('packages.yaml', 'r') as f:
    config = yaml.safe_load(f)
for pkg in config['packages']:
    print(pkg)
")

if [[ -z "$PACKAGES" ]]; then
    warn "No packages found in packages.yaml"
    exit 0
fi

log "Found packages: $(echo $PACKAGES | tr '\n' ' ')"

# Build each package
BUILT_PACKAGES=()
FAILED_PACKAGES=()

for pkg in $PACKAGES; do
    log "Building package: $pkg"

    pkg_dir="pkgbuilds/$pkg"

    if [[ ! -f "$pkg_dir/PKGBUILD" ]]; then
        error "No PKGBUILD found in $pkg_dir"
        FAILED_PACKAGES+=("$pkg")
        continue
    fi

    cd "$pkg_dir"

    # Clean previous builds
    if ls *.pkg.tar.* 1> /dev/null 2>&1; then
        log "Cleaning previous build artifacts for $pkg"
        rm -f *.pkg.tar.*
    fi

    # Build package
    if makepkg -sf --noconfirm --needed; then
        # Copy built packages to output directory
        if ls *.pkg.tar.* 1> /dev/null 2>&1; then
            cp *.pkg.tar.* "$OUTPUT_DIR/"
            success "Successfully built $pkg"
            BUILT_PACKAGES+=("$pkg")
        else
            error "Package $pkg built but no package file found"
            FAILED_PACKAGES+=("$pkg")
        fi
    else
        error "Failed to build package: $pkg"
        FAILED_PACKAGES+=("$pkg")
    fi

    cd "$REPO_DIR"
done

# Print summary
echo
log "Build Summary:"
log "=============="

if [[ ${#BUILT_PACKAGES[@]} -gt 0 ]]; then
    success "Successfully built ${#BUILT_PACKAGES[@]} package(s):"
    for pkg in "${BUILT_PACKAGES[@]}"; do
        echo "  ✓ $pkg"
    done
fi

if [[ ${#FAILED_PACKAGES[@]} -gt 0 ]]; then
    error "Failed to build ${#FAILED_PACKAGES[@]} package(s):"
    for pkg in "${FAILED_PACKAGES[@]}"; do
        echo "  ✗ $pkg"
    done
fi

# Update repository database if we have packages
if [[ ${#BUILT_PACKAGES[@]} -gt 0 ]]; then
    log "Updating repository database..."
    cd "$OUTPUT_DIR"

    if repo-add tetarus-repo.db.tar.xz *.pkg.tar.*; then
        success "Repository database updated successfully"

        # Create symlinks for easier access
        ln -sf tetarus-repo.db.tar.xz tetarus-repo.db
        ln -sf tetarus-repo.files.tar.xz tetarus-repo.files

        log "Repository contents:"
        ls -la
    else
        error "Failed to update repository database"
        exit 1
    fi
fi

# Exit with error if any packages failed
if [[ ${#FAILED_PACKAGES[@]} -gt 0 ]]; then
    exit 1
fi

success "All packages built successfully!"