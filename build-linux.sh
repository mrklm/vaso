#!/usr/bin/env bash
set -euo pipefail

############################################
# Vaso build-linux.sh
############################################

APP_NAME="Vaso"
MAIN_PY="app.py"
ICON_PATH="assets/vaso.png"
KEEP_BUILD_DIRS="0"

############################################
# Options
############################################

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep)
      KEEP_BUILD_DIRS="1"
      shift
      ;;
    -h|--help)
      echo "Usage: ./build-linux.sh [--keep]"
      exit 0
      ;;
    *)
      echo "Option inconnue: $1"
      exit 1
      ;;
  esac
done

############################################
# Helpers
############################################

need_file() {
  [[ -f "$1" ]] || { echo "❌ Fichier manquant: $1"; exit 1; }
}

need_dir() {
  [[ -d "$1" ]] || { echo "❌ Dossier manquant: $1"; exit 1; }
}

say() {
  printf "%s\n" "$*"
}

detect_arch() {
  local m
  m="$(uname -m || true)"
  case "$m" in
    x86_64|amd64) echo "x86_64" ;;
    aarch64|arm64) echo "arm64" ;;
    *) echo "$m" ;;
  esac
}

############################################
# Préflight
############################################

say "🧪 Préflight…"

need_file "$MAIN_PY"
need_file "requirements.txt"
need_dir  "assets"
need_file "$ICON_PATH"

ARCH="$(detect_arch)"

say "🏗️  Architecture détectée : linux-${ARCH}"

############################################
# Lecture version automatique
############################################

VERSION="$(grep -Po '(?<=APP_VERSION = ")[^"]+' "$MAIN_PY" || true)"

if [[ -z "$VERSION" ]]; then
  echo "❌ Impossible de lire APP_VERSION dans $MAIN_PY"
  exit 1
fi

APP_NAME_FROM_CODE="$(grep -Po '(?<=APP_NAME = ")[^"]+' "$MAIN_PY" || true)"
if [[ -n "$APP_NAME_FROM_CODE" ]]; then
  APP_NAME="$APP_NAME_FROM_CODE"
fi

say "📦 Nom appli : $APP_NAME"
say "📦 Version détectée : $VERSION"

############################################
# Nettoyage précédent
############################################

if [[ "$KEEP_BUILD_DIRS" == "1" ]]; then
  say "🧾 --keep activé : build/dist/spec/AppDir conservés"
else
  say "🧹 Nettoyage ancien build…"
  rm -rf build dist *.spec "${APP_NAME}.AppDir" releases .venv-build
fi

mkdir -p releases

############################################
# Venv de build
############################################

say "🐍 Préparation venv de build…"

python3 -m venv .venv-build

# shellcheck disable=SC1091
source .venv-build/bin/activate

python -m pip install -U pip setuptools wheel
pip install -U pyinstaller

if [[ -f requirements.txt ]]; then
  pip install -r requirements.txt
fi

############################################
# Build PyInstaller
############################################

say "🏗️  Build PyInstaller…"

python -m PyInstaller \
  --name "$APP_NAME" \
  --noconfirm \
  --clean \
  --windowed \
  --icon "$ICON_PATH" \
  --add-data "assets:assets" \
  --hidden-import "matplotlib.backends.backend_tkagg" \
  --hidden-import "mpl_toolkits.mplot3d" \
  --hidden-import "numpy" \
  --hidden-import "trimesh" \
  "$MAIN_PY"

BIN_PATH="dist/$APP_NAME/$APP_NAME"
if [[ ! -f "$BIN_PATH" ]]; then
  echo "❌ PyInstaller a échoué : binaire introuvable ($BIN_PATH)"
  exit 1
fi

############################################
# Génération tar.gz
############################################

TAR_NAME="${APP_NAME}-v${VERSION}-linux-${ARCH}.tar.gz"

say "📦 Création tar.gz…"
tar -czf "releases/${TAR_NAME}" -C dist "$APP_NAME"

(
  cd releases
  sha256sum "${TAR_NAME}" > "${TAR_NAME}.sha256"
)

############################################
# Génération AppImage (optionnelle)
############################################

if command -v appimagetool >/dev/null 2>&1; then
  say "📦 appimagetool détecté : création AppImage…"

  rm -rf "${APP_NAME}.AppDir"
  mkdir -p "${APP_NAME}.AppDir/usr/bin"
  cp -a "dist/$APP_NAME/." "${APP_NAME}.AppDir/usr/bin/"

  cat > "${APP_NAME}.AppDir/AppRun" <<EOF
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\$0")")"
exec "\$HERE/usr/bin/$APP_NAME" "\$@"
EOF

  chmod +x "${APP_NAME}.AppDir/AppRun"

  cat > "${APP_NAME}.AppDir/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Exec=$APP_NAME
Icon=$APP_NAME
Categories=Graphics;
Terminal=false
EOF

  cp -a "$ICON_PATH" "${APP_NAME}.AppDir/${APP_NAME}.png"

  APPIMAGE_NAME="${APP_NAME}-v${VERSION}-linux-${ARCH}.AppImage"

  appimagetool "${APP_NAME}.AppDir" "releases/${APPIMAGE_NAME}"
  chmod +x "releases/${APPIMAGE_NAME}"

  (
    cd releases
    sha256sum "${APPIMAGE_NAME}" > "${APPIMAGE_NAME}.sha256"
  )
else
  say "⚠️  appimagetool non trouvé : AppImage ignorée"
  say "   Le tar.gz a bien été généré."
fi

############################################
# Clean final
############################################

if [[ "$KEEP_BUILD_DIRS" == "1" ]]; then
  say "🧾 --keep activé : .venv-build, build, dist, spec et AppDir conservés"
else
  say "🧹 Clean final…"
  rm -rf build dist *.spec "${APP_NAME}.AppDir" .venv-build
  find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true
fi

say ""
say "🎉 Build terminé : ${APP_NAME} ${VERSION} (linux-${ARCH})"
say "📦 Artefacts disponibles dans releases/"
ls -lh releases