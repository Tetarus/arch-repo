# Tetarus's Arch Linux Repository

A custom Arch Linux package repository hosted on GitHub with automated builds for multiple packages.

## 🚀 Quick Setup

Add this repository to your system:

```bash
# Add to /etc/pacman.conf
sudo tee -a /etc/pacman.conf << 'EOF'

[tetarus-repo]
SigLevel = Optional TrustAll
Server = https://tetarus.github.io/arch-repo
EOF

# Sync package databases
sudo pacman -Sy

# Install packages
paru -S claude-code-bin
paru -S openai-codex-bin
```

## 📦 Available Packages

- **claude-code-bin** - Claude Code CLI for Anthropic's Claude AI assistant
- **openai-codex-bin** - OpenAI Codex binary release (automatically tracks latest GitHub releases)

All packages are defined in `packages.yaml` and automatically track upstream releases.

## ✨ Features

- **Metadata-Driven**: Single `packages.yaml` file defines all package information
- **Auto-Generated PKGBUILDs**: Static PKGBUILDs generated from metadata, no runtime API calls
- **Automated Builds**: GitHub Actions builds packages on changes and version updates
- **Dynamic Versioning**: Automatically tracks upstream releases
- **Multi-Architecture**: Support for x86_64 and aarch64 (when available)
- **Clean Builds**: All packages built in isolated Arch Linux containers

## 🛠 Development

### Local Building

Install Python dependencies and build all packages:

```bash
# Install dependencies
pip install -r requirements.txt

# Generate PKGBUILDs from metadata
python scripts/generate_pkgbuilds.py

# Build all packages
./scripts/build-all.sh
```

### Adding New Packages

1. Add package metadata to `packages.yaml`
2. Generate PKGBUILDs: `python scripts/generate_pkgbuilds.py`
3. Update package matrix in `.github/workflows/build.yml`
4. Test locally: `./scripts/build-all.sh`

### Version Management

```bash
# Check for upstream version updates
python scripts/update_versions.py

# Generate PKGBUILDs after version changes
python scripts/generate_pkgbuilds.py
```

## 📁 Repository Structure

```
arch-repo/
├── .github/workflows/
│   └── build.yml                # GitHub Actions CI/CD
├── pkgbuilds/                   # Generated PKGBUILDs (auto-generated)
│   ├── claude-code-bin/PKGBUILD
│   └── openai-codex-bin/PKGBUILD
├── scripts/
│   ├── build-all.sh             # Local build script
│   ├── update_versions.py       # Check upstream versions
│   ├── generate_pkgbuilds.py    # Generate PKGBUILDs from metadata
│   └── generate_index.py        # Generate repository index
├── x86_64/                      # Built packages (auto-generated)
│   ├── *.pkg.tar.zst
│   ├── tetarus-repo.db          # Repository database
│   └── tetarus-repo.files       # File list database
├── packages.yaml                # Package metadata (source of truth)
├── requirements.txt             # Python dependencies
└── README.md
```

## 🔄 How It Works

1. **Metadata Updates**: When `packages.yaml` or scripts change, GitHub Actions triggers
2. **PKGBUILD Generation**: Python scripts generate static PKGBUILDs from metadata
3. **Matrix Builds**: Each package builds in parallel in Arch containers
4. **Repository Creation**: `repo-add` creates pacman-compatible database
5. **GitHub Pages**: Repository served at `https://tetarus.github.io/arch-repo`
6. **Auto-Updates**: Users get updates through normal `pacman -Syu`

## 🏗 GitHub Actions Workflow

Three-job pipeline:

1. **Build**: Matrix builds each package in parallel
2. **Repository**: Collects packages and creates repository database
3. **Deploy**: Publishes repository to GitHub Pages

## 🔧 Local Development

Serve packages locally for testing:

```bash
# Build packages
./scripts/build-all.sh

# Serve locally
cd x86_64 && python -m http.server 8000

# Add to /etc/pacman.conf
[tetarus-local]
SigLevel = Optional TrustAll
Server = http://localhost:8000
```

## 📋 Requirements

- **Local**: Arch Linux, `base-devel`, Python, `git`
- **CI/CD**: GitHub repository with Pages enabled

## 🤝 Contributing

1. Fork this repository
2. Add package metadata to `packages.yaml`
3. Update workflow matrix in `.github/workflows/build.yml`
4. Test locally and submit a pull request

### Package Guidelines

- Add package metadata to `packages.yaml` following existing examples
- Follow Arch packaging standards
- Test locally with `python scripts/generate_pkgbuilds.py && ./scripts/build-all.sh`
- Update workflow matrix in `.github/workflows/build.yml`

## 📄 License

This repository structure is released under the MIT License. Individual packages may have their own licenses - check each package's PKGBUILD for details.

## 🔗 Related Links

- [Arch User Repository](https://aur.archlinux.org/)
- [Arch Linux Packaging Standards](https://wiki.archlinux.org/title/Arch_package_guidelines)
- [PKGBUILD Manual](https://man.archlinux.org/man/PKGBUILD.5)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
