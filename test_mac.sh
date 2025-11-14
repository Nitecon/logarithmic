#!/bin/bash
# Test script for local development
set -e  # Exit on error

echo "Building app..."
pyinstaller Logarithmic.spec --noconfirm

echo ""
echo "Signing app with ad-hoc signature for testing..."
# Ad-hoc signing is sufficient for local sandbox testing
codesign --force --deep --sign - \
    --entitlements entitlements.plist \
    dist/Logarithmic.app

echo ""
echo "Verifying signature..."
codesign --verify --deep --verbose dist/Logarithmic.app

echo ""
echo "Testing app launch (non-sandboxed)..."
echo "Opening app for 5 seconds to verify fonts and basic functionality..."
open dist/Logarithmic.app
sleep 5

echo ""
echo "⚠️  Note: Full sandbox testing requires proper App Store signing."
echo "The bsd.sb profile is too restrictive for GUI apps."
echo "To test sandbox behavior, use the signed build from build_mac.sh"
echo ""
echo "✅ Build and basic launch test complete!"
echo "Check if the app opened and fonts loaded correctly."