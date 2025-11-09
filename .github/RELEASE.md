# Release Process

This document describes how to create a new release of Logarithmic.

## Automated Releases

Releases are automatically built and published via GitHub Actions when you push a version tag.

### Creating a Release

1. **Update version** in `pyproject.toml` if needed
2. **Commit all changes** to main branch
3. **Create and push a version tag:**

```bash
git tag v1.0.0
git push origin v1.0.0
```

4. **GitHub Actions will automatically:**
   - Build executables for Linux, macOS, and Windows
   - Create a GitHub Release
   - Attach the built binaries to the release

### Release Artifacts

The following artifacts are created:

- **Linux**: `Logarithmic-Linux.tar.gz` - Single executable binary
- **macOS**: `Logarithmic-macOS.zip` - Application bundle (.app)
- **Windows**: `Logarithmic-Windows.zip` - Executable (.exe)

## Manual Build (Local Testing)

To test the build process locally:

### Windows
```bash
python -m pip install pyinstaller
pyinstaller Logarithmic.spec
# Output: dist/Logarithmic.exe
```

### macOS
```bash
python -m pip install pyinstaller
pyinstaller Logarithmic.spec
# Output: dist/Logarithmic.app or dist/Logarithmic
```

### Linux
```bash
python -m pip install pyinstaller
pyinstaller Logarithmic.spec
# Output: dist/Logarithmic
```

## Build Configuration

The build is configured in `Logarithmic.spec`:

- **Entry point**: `src/logarithmic/__main__.py`
- **Fonts**: All `.ttf` files from `fonts/` directory are bundled
- **Hidden imports**: PySide6 modules and watchdog
- **Console**: Disabled (windowed application)
- **Optimization**: UPX compression enabled

## Troubleshooting

### Fonts not loading
Ensure all font files are in the `fonts/` directory and have `.ttf` extension.

### Import errors
Add missing modules to `hiddenimports` in `Logarithmic.spec`.

### Size optimization
The executable includes:
- Python runtime
- PySide6 Qt libraries
- All dependencies
- Font files

Typical sizes:
- Windows: ~80-100 MB
- macOS: ~90-110 MB
- Linux: ~80-100 MB

## CI/CD Workflows

### CI Workflow (`.github/workflows/ci.yml`)
- Runs on every push to main and pull requests
- Tests on Linux, macOS, and Windows
- Validates imports and basic functionality

### Release Workflow (`.github/workflows/release.yml`)
- Triggered by version tags (v*)
- Builds executables for all platforms
- Creates GitHub Release with binaries
- Can be manually triggered via workflow_dispatch
