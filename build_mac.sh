#!/bin/bash
# Personal build script - not committed to repo

if [ -z "$APP_CERT" ]; then
  echo "Error: APP_CERT environment variable not set"
  echo "Example: export APP_CERT='3rd Party Mac Developer Application: Your Name (YOUR_TEAM_ID)'"
  exit 1
fi
if [ -z "$INSTALLER_CERT" ]; then
  echo "Error: INSTALLER_CERT environment variable not set"
  echo "Example: export INSTALLER_CERT='3rd Party Mac Developer Installer: Your Name (YOUR_TEAM_ID)'"
  exit 2
fi

# Clean and build
rm -rf build dist
pyinstaller Logarithmic.spec

# Sign
codesign --deep --force --verify --verbose \
    --sign "$APP_CERT" \
    --options runtime \
    --entitlements entitlements.plist \
    "dist/Logarithmic.app"

# Create package
productbuild --component dist/Logarithmic.app /Applications \
    --sign "$INSTALLER_CERT" \
    dist/Logarithmic.pkg

# Verify signatures
echo "Verifying app signature..."
codesign --verify --deep --strict --verbose=2 dist/Logarithmic.app

echo "Verifying package signature..."
pkgutil --check-signature dist/Logarithmic.pkg

echo ""
echo "✅ Build complete!"
echo "App bundle: dist/Logarithmic.app"
echo "Installer package: dist/Logarithmic.pkg"
