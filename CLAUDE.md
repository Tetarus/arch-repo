# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a custom Arch Linux package repository that automatically builds and distributes packages via GitHub Actions and GitHub Pages. The repository focuses on packaging software not available in official Arch repositories, particularly tracking upstream releases dynamically.

## Core Architecture

### Package Build System

- **Metadata-Driven**: Central `packages.yaml` file contains all package information as single source of truth
- **Generated PKGBUILDs**: Static PKGBUILDs are generated from metadata and templates, no runtime API calls
- **Separated Concerns**: Version checking happens independently from building, improving reliability
- **Multi-Architecture**: Supports both x86_64 and aarch64 when upstream provides releases
- **Repository Database**: Uses `repo-add` to create pacman-compatible `.db` and `.files` databases

### Build Pipeline

1. **Version Checking**: Python script checks upstream sources and updates `packages.yaml`
2. **PKGBUILD Generation**: Python script generates static PKGBUILDs from metadata and templates
3. **Local Development**: `scripts/build-all.sh` generates PKGBUILDs and builds all packages locally using `makepkg`
4. **CI/CD**: GitHub Actions generates PKGBUILDs then builds packages in Arch Linux containers
5. **Matrix Strategy**: Each package builds in parallel for faster CI times
6. **Repository Generation**: Built packages are collected and `repo-add` creates the repository database
7. **Distribution**: GitHub Pages serves the repository at `https://tetarus.github.io/arch-repo/`

### Key Components

#### Core Files

- `packages.yaml`: Central metadata file containing all package information
- `requirements.txt`: Python dependencies for the new system

#### Scripts (`scripts/`)

- `update_versions.py`: Check upstream sources and update package versions in `packages.yaml`
- `generate_pkgbuilds.py`: Generate static PKGBUILDs from metadata and templates
- `build-all.sh`: Comprehensive local build script that generates PKGBUILDs and builds packages

#### Generated PKGBUILDs (`pkgbuilds/*/PKGBUILD`)

- Generated automatically from metadata, no manual editing required
- Static versions with no runtime API calls during builds
- Support for GitHub releases and Google Cloud Storage upstream sources
- Include proper error handling and checksum verification where applicable

## Common Development Commands

### Package Management

```bash
# Install Python dependencies
pip install -r requirements.txt

# Check for version updates
python3 scripts/update_versions.py

# Generate PKGBUILDs from metadata
python3 scripts/generate_pkgbuilds.py

# Build all packages locally
./scripts/build-all.sh
```

### Building Individual Packages

```bash
# Generate PKGBUILDs first
python3 scripts/generate_pkgbuilds.py

# Build single package
cd pkgbuilds/<package-name>
makepkg -sf --noconfirm --needed

# Test package installation
sudo pacman -U *.pkg.tar.zst
```

### Adding New Packages

```bash
# Edit packages.yaml to add new package metadata
# Then regenerate PKGBUILDs
python3 scripts/generate_pkgbuilds.py

# Update CI matrix in .github/workflows/build.yml to include new package
```

### Repository Management

```bash
# Update repository database after building
cd x86_64
repo-add tetarus-repo.db.tar.xz *.pkg.tar.zst

# Serve repository locally for testing
cd x86_64
python -m http.server 8000
```

## GitHub Actions Workflow

The CI system (`build.yml`) uses a two-job approach:

1. **Build Job**: Matrix strategy builds each package in parallel in Arch Linux containers
2. **Repository Job**: Collects all built packages and creates repository database for GitHub Pages deployment

### Package Matrix

When adding packages, update the matrix in `.github/workflows/build.yml`:

```yaml
strategy:
  matrix:
    package: [openai-codex-git, new-package-name]
```

## Package Development Patterns

### Dynamic Versioning for Git Packages

PKGBUILDs use `pkgver()` functions that query GitHub API to get latest release tags:

- Handles both stable and prerelease versions via `ONLY_STABLE` environment variable
- Normalizes version strings by removing prefixes and converting hyphens to dots
- Includes proper error handling for API failures

### Binary Package Pattern

The repository specializes in packaging upstream binary releases:

- Downloads from GitHub releases API based on architecture
- Extracts and installs pre-built binaries rather than building from source
- Uses robust binary detection logic in `prepare()` function

### Architecture Support

PKGBUILDs map Arch architecture names to Rust/upstream target triples:

- `x86_64` → `x86_64-unknown-linux-gnu`
- `aarch64` → `aarch64-unknown-linux-gnu`

## Repository Structure Context

The repository serves as both source code (PKGBUILDs) and distribution point (built packages), with `x86_64/` containing the actual pacman repository that users install from.
