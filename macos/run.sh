#!/bin/bash
set -e

cd "$(dirname "$0")/.."

# --- Backend ---
pkill -f "uvicorn app.main:app" 2>/dev/null || true
echo "Starting backend..."
python3 -m uvicorn app.main:app --reload &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# --- Swift app ---
cd macos
echo "Building..."
swift build

APP=".build/PersonalAssistant.app"
mkdir -p "$APP/Contents/MacOS"

cp .build/debug/PersonalAssistant "$APP/Contents/MacOS/"

cat > "$APP/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>PersonalAssistant</string>
    <key>CFBundleIdentifier</key>
    <string>com.personal.assistant</string>
    <key>CFBundleName</key>
    <string>Personal Assistant</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsLocalNetworking</key>
        <true/>
    </dict>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

pkill -x PersonalAssistant 2>/dev/null || true

echo "Launching..."
open "$APP"
