#!/usr/bin/env bash
set -euo pipefail

# build-macos.sh — Vaso macOS (Intel / Apple Silicon)
# Build: PyInstaller -> .app -> (optional) ZIP -> DMG -> sha256
#
# Usage:
#   ./build-macos.sh
#   ./build-macos.sh -v 1.0.0
#   ./build-macos.sh -v 1.0.0 --zip
#   ./build-macos.sh -v 1.0.0 --keep
#   ./build-macos.sh -v 1.0.0 --arch x86_64
#   ./build-macos.sh -v 1.0.0 --arch arm64

APP_NAME="Vaso"
VERSION=""
KEEP="0"
MAKE_ZIP="0"
ARCH=""   # x86_64 | arm64 | auto

while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--version) VERSION="${2:-}"; shift 2 ;;
    --keep) KEEP="1"; shift ;;
    --zip) MAKE_ZIP="1"; shift ;;
    --arch) ARCH="${2:-}"; shift 2 ;;
    -h|--help)
      sed -n '1,220p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# --- Detect arch if not provided ---
if [[ -z "$ARCH" ]]; then
  MACHINE="$(uname -m)"
  if [[ "$MACHINE" == "arm64" ]]; then
    ARCH="arm64"
  else
    ARCH="x86_64"
  fi
fi

if [[ "$ARCH" != "x86_64" && "$ARCH" != "arm64" ]]; then
  echo "❌ Invalid --arch. Use x86_64 or arm64."
  exit 1
fi

PY_FILE="app.py"
ICON_PATH="assets/vaso.icns"

# --- Checks ---
[[ -d ".venv" ]] || { echo "❌ Missing .venv/ (create venv first)"; exit 1; }
[[ -f "$PY_FILE" ]] || { echo "❌ Missing ${PY_FILE} (run this script at repo root)"; exit 1; }
[[ -f "$ICON_PATH" ]] || { echo "❌ Missing ${ICON_PATH}"; exit 1; }
[[ -d "assets" ]] || { echo "❌ Missing assets/"; exit 1; }
[[ -f "requirements.txt" ]] || { echo "❌ Missing requirements.txt"; exit 1; }

# --- Detect APP_NAME from code ---
APP_NAME_FROM_CODE="$(grep -E '^APP_NAME[[:space:]]*=[[:space:]]*"' "${PY_FILE}" | sed -E 's/^[^"]*"([^"]+)".*$/\1/' || true)"
if [[ -n "$APP_NAME_FROM_CODE" ]]; then
  APP_NAME="$APP_NAME_FROM_CODE"
fi

# --- Version (default from code if not provided via -v/--version) ---
if [[ -z "${VERSION}" ]]; then
  VERSION="$(grep -E '^APP_VERSION[[:space:]]*=[[:space:]]*"' "${PY_FILE}" | sed -E 's/^[^"]*"([^"]+)".*$/\1/' || true)"
  if [[ -z "${VERSION}" ]]; then
    echo "❌ Unable to extract APP_VERSION from ${PY_FILE}"
    exit 1
  fi
  echo "ℹ️ Version extracted from code: ${VERSION}"
fi

echo "== ${APP_NAME} macOS build =="
echo " - Version: ${VERSION}"
echo " - Arch:    ${ARCH}"
echo " - Entry:   ${PY_FILE}"
echo " - Icon:    ${ICON_PATH}"

# --- Activate venv ---
# shellcheck disable=SC1091
source ".venv/bin/activate"

python -V
python -m pip install -U pip wheel setuptools >/dev/null
python -m pip install -U pyinstaller >/dev/null
python -m pip install -r requirements.txt >/dev/null

# Quick imports (fail fast)
python - <<'PY'
import tkinter
import numpy
import matplotlib
import trimesh
print("Imports OK")
PY

# --- Clean (start) ---
VENV_BUILD_DIR=".venv-build"

if [[ "$KEEP" != "1" ]]; then
  echo "== Clean (start) =="
  rm -rf build dist "${APP_NAME}.spec" dist_dmg_staging
  rm -rf releases
  rm -rf "$VENV_BUILD_DIR" 2>/dev/null || true
  rm -rf "$HOME/Library/Application Support/pyinstaller" 2>/dev/null || true
else
  echo "ℹ️ Keep enabled: skip clean at start"
fi

mkdir -p releases

# --- Build .app ---
pyinstaller \
  --name "${APP_NAME}" \
  --windowed \
  --noconfirm \
  --clean \
  --icon "${ICON_PATH}" \
  --add-data "assets:assets" \
  --hidden-import "matplotlib.backends.backend_tkagg" \
  --hidden-import "mpl_toolkits.mplot3d" \
  --hidden-import "numpy" \
  --hidden-import "trimesh" \
  "${PY_FILE}"

APP_PATH="dist/${APP_NAME}.app"
if [[ ! -d "$APP_PATH" ]]; then
  echo "❌ Build failed: ${APP_PATH} not found"
  exit 1
fi

# --- Release artifacts ---
BASE_NAME="${APP_NAME}-v${VERSION}-macOS-${ARCH}"
DMG_PATH="releases/${BASE_NAME}.dmg"
ZIP_PATH="releases/${BASE_NAME}.zip"

# --- Optional ZIP of .app ---
if [[ "$MAKE_ZIP" == "1" ]]; then
  rm -f "$ZIP_PATH"
  ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"
  (
    cd releases
    shasum -a 256 "$(basename "$ZIP_PATH")" > "$(basename "$ZIP_PATH").sha256"
  )
  echo "✅ ZIP: ${ZIP_PATH}"
  echo "✅ SHA: ${ZIP_PATH}.sha256"
fi

# --- Prepare DMG staging ---
STAGING_DIR="dist_dmg_staging"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp -R "$APP_PATH" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

# Best effort: remove quarantine attrs from built app inside staging
find "$STAGING_DIR/${APP_NAME}.app" -exec xattr -d com.apple.quarantine {} \; 2>/dev/null || true

# --- Create DMG ---
rm -f "$DMG_PATH"
hdiutil create \
  -volname "${APP_NAME}" \
  -srcfolder "$STAGING_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH" >/dev/null

# --- SHA-256 for DMG ---
rm -f "${DMG_PATH}.sha256"
(
  cd releases
  shasum -a 256 "$(basename "$DMG_PATH")" > "$(basename "$DMG_PATH").sha256"
)

echo
echo "✅ Done:"
echo " - App: dist/${APP_NAME}.app"
echo " - DMG: ${DMG_PATH}"
echo " - SHA: ${DMG_PATH}.sha256"
if [[ "$MAKE_ZIP" == "1" ]]; then
  echo " - ZIP: ${ZIP_PATH}"
  echo " - SHA: ${ZIP_PATH}.sha256"
fi

if [[ "$KEEP" != "1" ]]; then
  echo
  echo "== Clean (end) =="
  echo " - Removing staging/, build/, dist/, *.spec, .venv-build/, __pycache__/ and PyInstaller cache"

  rm -rf "$STAGING_DIR" 2>/dev/null || true
  rm -rf build dist "${APP_NAME}.spec" 2>/dev/null || true
  rm -rf "$VENV_BUILD_DIR" 2>/dev/null || true

  # Python caches in repo
  find "$ROOT_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
  find "$ROOT_DIR" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

  # PyInstaller cache (user profile)
  rm -rf "$HOME/Library/Application Support/pyinstaller" 2>/dev/null || true
else
  echo "ℹ️ Keep enabled: build artifacts preserved (staging/build/dist/spec/caches)"
fi