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
PY_FILE="app.py"
ICON_PATH="assets/vaso.icns"
VENV_BUILD_DIR=".venv-build"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--version)
      VERSION="${2:-}"
      shift 2
      ;;
    --keep)
      KEEP="1"
      shift
      ;;
    --zip)
      MAKE_ZIP="1"
      shift
      ;;
    --arch)
      ARCH="${2:-}"
      shift 2
      ;;
    -h|--help)
      sed -n '1,260p' "$0"
      exit 0
      ;;
    *)
      echo "❌ Argument inconnu : $1"
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

need_file() {
  [[ -f "$1" ]] || { echo "❌ Fichier manquant : $1"; exit 1; }
}

need_dir() {
  [[ -d "$1" ]] || { echo "❌ Dossier manquant : $1"; exit 1; }
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "❌ Commande manquante : $1"; exit 1; }
}

say() {
  printf "%s\n" "$*"
}

# --- Detect arch if not provided ---
if [[ -z "$ARCH" ]]; then
  MACHINE="$(uname -m || true)"
  if [[ "$MACHINE" == "arm64" ]]; then
    ARCH="arm64"
  else
    ARCH="x86_64"
  fi
fi

if [[ "$ARCH" != "x86_64" && "$ARCH" != "arm64" ]]; then
  echo "❌ Valeur invalide pour --arch. Utilisez x86_64 ou arm64."
  exit 1
fi

# --- Checks ---
need_file "$PY_FILE"
need_file "$ICON_PATH"
need_dir "assets"
need_file "requirements.txt"
need_cmd python3
need_cmd grep
need_cmd sed
need_cmd hdiutil
need_cmd ditto
need_cmd shasum
need_cmd xattr

# --- Detect APP_NAME from code ---
APP_NAME_FROM_CODE="$(grep -E '^APP_NAME[[:space:]]*=[[:space:]]*"' "$PY_FILE" | sed -E 's/^[^"]*"([^"]+)".*$/\1/' || true)"
if [[ -n "$APP_NAME_FROM_CODE" ]]; then
  APP_NAME="$APP_NAME_FROM_CODE"
fi

# --- Version (default from code if not provided via -v/--version) ---
if [[ -z "$VERSION" ]]; then
  VERSION="$(grep -E '^APP_VERSION[[:space:]]*=[[:space:]]*"' "$PY_FILE" | sed -E 's/^[^"]*"([^"]+)".*$/\1/' || true)"
  if [[ -z "$VERSION" ]]; then
    echo "❌ Impossible d'extraire APP_VERSION depuis ${PY_FILE}"
    exit 1
  fi
  say "ℹ️ Version extraite du code : ${VERSION}"
fi

say "== ${APP_NAME} macOS build =="
say " - Version : ${VERSION}"
say " - Arch    : ${ARCH}"
say " - Entry   : ${PY_FILE}"
say " - Icon    : ${ICON_PATH}"

# --- Clean (start) ---
if [[ "$KEEP" != "1" ]]; then
  say "== Clean (start) =="
  rm -rf build dist "${APP_NAME}.spec" dist_dmg_staging releases "$VENV_BUILD_DIR"
  rm -rf "$HOME/Library/Application Support/pyinstaller" 2>/dev/null || true
else
  say "ℹ️ Keep activé : nettoyage initial ignoré"
fi

mkdir -p releases

# --- Create build venv ---
say "🐍 Préparation du venv de build…"
python3 -m venv "$VENV_BUILD_DIR"

# shellcheck disable=SC1091
source "$VENV_BUILD_DIR/bin/activate"

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

# --- Build .app ---
say "🏗️ Build PyInstaller…"
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
  echo "❌ Build failed : ${APP_PATH} introuvable"
  exit 1
fi

# --- Release artifacts ---
BASE_NAME="${APP_NAME}-v${VERSION}-macOS-${ARCH}"
DMG_PATH="releases/${BASE_NAME}.dmg"
ZIP_PATH="releases/${BASE_NAME}.zip"

# --- Optional ZIP of .app ---
if [[ "$MAKE_ZIP" == "1" ]]; then
  say "📦 Création ZIP…"
  rm -f "$ZIP_PATH"
  ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"
  (
    cd releases
    shasum -a 256 "$(basename "$ZIP_PATH")" > "$(basename "$ZIP_PATH").sha256"
  )
  say "✅ ZIP : ${ZIP_PATH}"
  say "✅ SHA : ${ZIP_PATH}.sha256"
fi

# --- Prepare DMG staging ---
say "📦 Préparation du staging DMG…"
STAGING_DIR="dist_dmg_staging"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp -R "$APP_PATH" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

# Best effort: remove quarantine attrs from built app inside staging
find "$STAGING_DIR/${APP_NAME}.app" -exec xattr -d com.apple.quarantine {} \; 2>/dev/null || true

# --- Create DMG ---
say "📦 Création DMG…"
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

say ""
say "✅ Build terminé :"
say " - App : dist/${APP_NAME}.app"
say " - DMG : ${DMG_PATH}"
say " - SHA : ${DMG_PATH}.sha256"
if [[ "$MAKE_ZIP" == "1" ]]; then
  say " - ZIP : ${ZIP_PATH}"
  say " - SHA : ${ZIP_PATH}.sha256"
fi

deactivate || true

if [[ "$KEEP" != "1" ]]; then
  say ""
  say "== Clean (end) =="
  say " - Suppression de staging/, build/, dist/, *.spec, .venv-build/, __pycache__/ et cache PyInstaller"

  rm -rf "$STAGING_DIR" 2>/dev/null || true
  rm -rf build dist "${APP_NAME}.spec" 2>/dev/null || true
  rm -rf "$VENV_BUILD_DIR" 2>/dev/null || true

  find "$ROOT_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
  find "$ROOT_DIR" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

  rm -rf "$HOME/Library/Application Support/pyinstaller" 2>/dev/null || true
else
  say "ℹ️ Keep activé : build/dist/spec/staging/venv-build conservés"
fi