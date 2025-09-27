# Tetarus's Arch Linux Repository

A custom Arch Linux package repository hosted on GitHub with automated builds for multiple packages.

## 🚀 Quick Setup

Add this repository to your system:

```bash
# Add to /etc/pacman.conf
echo '
[tetarus-repo]
SigLevel = Optional TrustAll
Server = https://tetarus.github.io/arch-repo/$arch' | sudo tee -a /etc/pacman.conf

# Sync package databases
sudo pacman -Sy

# Install packages
paru -S openai-codex-bin
```

## 📦 Available Packages

- **openai-codex-bin** - OpenAI Codex binary release (automatically tracks latest GitHub releases)

## ✨ Features

- **Automated Builds**: GitHub Actions builds packages weekly and on changes
- **Dynamic Versioning**: Git packages automatically track upstream releases
- **Multi-Architecture**: Support for x86_64 and aarch64 (when available)
- **Auto-Updates**: Paru/pacman automatically detects new versions
- **Clean Builds**: All packages built in isolated containers

## 🛠 Development

### Local Building

Build all packages locally:

```bash
./scripts/build-all.sh
```

### Adding New Packages

Use the helper script:

```bash
# Create new package from template
./scripts/add-package.sh my-new-package

# Copy from existing PKGBUILD
./scripts/add-package.sh my-package /path/to/existing/PKGBUILD

# Copy from directory
./scripts/add-package.sh my-package /path/to/package/dir
```

### Manual Package Addition

1. Create directory: `pkgbuilds/package-name/`
2. Add `PKGBUILD` file
3. Update `.github/workflows/build.yml` matrix to include the package name
4. Commit and push changes

## 📁 Repository Structure

```
arch-repo/
├── .github/workflows/
│   └── build.yml                # GitHub Actions CI/CD
├── pkgbuilds/
│   └── openai-codex-bin/        # Package source directories
│       └── PKGBUILD
├── scripts/
│   ├── build-all.sh             # Local build script
│   └── add-package.sh           # Package addition helper
├── x86_64/                      # Built packages (auto-generated)
│   ├── *.pkg.tar.zst
│   ├── tetarus-repo.db            # Repository database
│   └── tetarus-repo.files         # File list database
└── README.md
```

## 🔄 How It Works

1. **Package Changes**: When a PKGBUILD is modified or added, GitHub Actions triggers
2. **Matrix Builds**: Each package builds in parallel for faster CI times
3. **Weekly Rebuilds**: Scheduled builds ensure `-git` packages get latest versions
4. **Repository Update**: `repo-add` creates pacman-compatible database
5. **GitHub Pages**: Repository files served via GitHub Pages
6. **Auto-Updates**: Users get updates through normal `pacman -Syu` or `paru -Syu`

## 🏗 GitHub Actions Workflow

The CI workflow:

- Builds packages in Arch Linux containers
- Uses matrix strategy for parallel builds
- Handles dynamic versioning for `-git` packages
- Creates repository database with `repo-add`
- Deploys to GitHub Pages automatically
- Runs weekly to catch upstream updates

## 🔧 Configuration

### Local Repository

For local development, you can build and serve packages locally:

```bash
# Build packages
./scripts/build-all.sh

# Serve locally (example with Python)
cd x86_64
python -m http.server 8000

# Add to pacman.conf
[tetarus-local]
SigLevel = Optional TrustAll
Server = http://localhost:8000
```

### Custom Package Sources

Packages can pull from various sources:

- GitHub releases (like openai-codex-bin)
- AUR packages (for custom builds)
- Custom build scripts
- Binary redistributions

## 📋 Requirements

### For Building Locally

- Arch Linux or Arch-based distribution
- `base-devel` package group
- `git` for version control

### For CI/CD

- Public GitHub repository
- GitHub Pages enabled
- Repository secrets configured (if needed)

## 🤝 Contributing

1. Fork this repository
2. Add your package to `pkgbuilds/your-package/`
3. Update the package matrix in `.github/workflows/build.yml`
4. Test locally with `./scripts/build-all.sh`
5. Submit a pull request

### Package Guidelines

- Follow Arch packaging standards
- Use dynamic versioning for VCS packages
- Include proper dependencies
- Test builds locally before committing
- Document any special build requirements

## 📄 License

This repository structure is released under the MIT License. Individual packages may have their own licenses - check each package's PKGBUILD for details.

## 🔗 Related Links

- [Arch User Repository](https://aur.archlinux.org/)
- [Arch Linux Packaging Standards](https://wiki.archlinux.org/title/Arch_package_guidelines)
- [PKGBUILD Manual](https://man.archlinux.org/man/PKGBUILD.5)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
