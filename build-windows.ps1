[CmdletBinding()]
param(
  [string]$Version = "",
  [string]$Arch = "windows-x86_64",
  [switch]$Keep
)

$ErrorActionPreference = "Stop"

function Die([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

Set-Location -Path $PSScriptRoot
Write-Host "Repo: $PSScriptRoot"

# ---------- Constantes ----------
$EntryPy      = Join-Path $PSScriptRoot "app.py"
$AssetsDir    = Join-Path $PSScriptRoot "assets"
$DistDir      = Join-Path $PSScriptRoot "dist"
$BuildDir     = Join-Path $PSScriptRoot "build"
$ReleasesDir  = Join-Path $PSScriptRoot "releases"
$VenvDir      = Join-Path $PSScriptRoot ".venv-build"
$VenvPython   = Join-Path $VenvDir "Scripts\python.exe"
$ReqFile      = Join-Path $PSScriptRoot "requirements.txt"

# ---------- Sanity checks ----------
if (-not (Test-Path $EntryPy))   { Die "Missing file: $EntryPy" }
if (-not (Test-Path $AssetsDir)) { Die "Missing folder: $AssetsDir" }

# ---------- Detect APP_NAME ----------
$AppName = ""
$AppNameLine = Get-Content $EntryPy | Where-Object { $_ -match '^\s*APP_NAME\s*=' } | Select-Object -First 1
if ($AppNameLine) {
  $m = [regex]::Match($AppNameLine, 'APP_NAME\s*=\s*"([^"]+)"')
  if ($m.Success) {
    $AppName = $m.Groups[1].Value.Trim()
  }
}
if ([string]::IsNullOrWhiteSpace($AppName)) {
  $AppName = "Vaso"
  Write-Host "APP_NAME not detected in app.py, fallback: $AppName"
} else {
  Write-Host "Detected app name: $AppName"
}

# ---------- Detect Version ----------
if ([string]::IsNullOrWhiteSpace($Version)) {
  $VersionLine = Get-Content $EntryPy | Where-Object { $_ -match '^\s*APP_VERSION\s*=' } | Select-Object -First 1
  if ($VersionLine) {
    $m = [regex]::Match($VersionLine, 'APP_VERSION\s*=\s*"([^"]+)"')
    if ($m.Success) {
      $Version = $m.Groups[1].Value.Trim()
      Write-Host "Detected version: $Version"
    }
  }
}
if ([string]::IsNullOrWhiteSpace($Version)) {
  Die "Version not provided and APP_VERSION not found in app.py."
}

# ---------- Icon ----------
$IconPath = Join-Path $AssetsDir "vaso.ico"
if (-not (Test-Path $IconPath)) {
  Die "Missing icon: $IconPath"
}

# ---------- TRUE CLEAN (before build) ----------
if (-not $Keep) {
  Write-Host "Full clean: build/, dist/, releases/, *.spec, .venv-build/"
  Remove-Item -Recurse -Force $BuildDir, $DistDir, $ReleasesDir -ErrorAction SilentlyContinue
  Remove-Item -Force (Join-Path $PSScriptRoot "*.spec") -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
} else {
  Write-Host "Keep enabled: no pre-clean (build/dist/releases/spec/venv preserved)"
}

# ---------- Create build venv ----------
Write-Host "Creating build venv: $VenvDir"
python -m venv $VenvDir
if (-not (Test-Path $VenvPython)) { Die "Failed to create venv at $VenvDir" }

# ---------- Install build tools ----------
Write-Host "Preparing build venv..."
& $VenvPython -m pip install --upgrade pip setuptools wheel | Out-Host
& $VenvPython -m pip install --upgrade pyinstaller | Out-Host

if (Test-Path $ReqFile) {
  Write-Host "Installing requirements.txt..."
  & $VenvPython -m pip install -r $ReqFile | Out-Host
}

# ---------- Prepare releases ----------
New-Item -ItemType Directory -Force -Path $ReleasesDir | Out-Null

# ---------- PyInstaller args ----------
$pyiArgs = @()
$pyiArgs += "--noconfirm"
$pyiArgs += "--clean"
$pyiArgs += "--windowed"
$pyiArgs += "--name"
$pyiArgs += $AppName
$pyiArgs += "--icon"
$pyiArgs += $IconPath
$pyiArgs += "--add-data"
$pyiArgs += "assets;assets"

# Imports parfois capricieux selon environnement
$pyiArgs += "--hidden-import"
$pyiArgs += "matplotlib.backends.backend_tkagg"
$pyiArgs += "--hidden-import"
$pyiArgs += "mpl_toolkits.mplot3d"
$pyiArgs += "--hidden-import"
$pyiArgs += "numpy"

Write-Host "Running PyInstaller..."
& $VenvPython -m PyInstaller @pyiArgs $EntryPy
if ($LASTEXITCODE -ne 0) { Die "PyInstaller failed." }

# ---------- Check output ----------
$OutDir = Join-Path $DistDir $AppName
if (-not (Test-Path $OutDir)) { Die "Output folder missing: $OutDir" }

# ---------- ZIP ----------
$ZipName = "$AppName-v$Version-$Arch.zip"
$ZipPath = Join-Path $ReleasesDir $ZipName
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }

Write-Host "Creating ZIP..."
Compress-Archive -Path (Join-Path $OutDir "*") -DestinationPath $ZipPath -Force

# ---------- SHA256 ----------
$ShaFile = "SHA256SUMS-$AppName-v$Version.txt"
$ShaPath = Join-Path $ReleasesDir $ShaFile
$hash = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLower()
"$hash  $ZipName" | Out-File -FilePath $ShaPath -Encoding ascii

# ---------- Final clean after success ----------
if (-not $Keep) {
  Write-Host "Final clean: .venv-build/, build/, dist/, *.spec, __pycache__/ and PyInstaller cache"

  # Repo artifacts
  Remove-Item -Recurse -Force $VenvDir, $BuildDir, $DistDir -ErrorAction SilentlyContinue
  Remove-Item -Force (Join-Path $PSScriptRoot "*.spec") -ErrorAction SilentlyContinue

  # Python caches in repo
  Get-ChildItem -Path $PSScriptRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item -Recurse -Force $_.FullName -ErrorAction SilentlyContinue }

  Get-ChildItem -Path $PSScriptRoot -Recurse -File -Include "*.pyc","*.pyo" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item -Force $_.FullName -ErrorAction SilentlyContinue }

  # PyInstaller caches (user profile)
  $PyInstallerCache1 = Join-Path $env:LOCALAPPDATA "pyinstaller"
  $PyInstallerCache2 = Join-Path $env:APPDATA "pyinstaller"
  if (Test-Path $PyInstallerCache1) { Remove-Item -Recurse -Force $PyInstallerCache1 -ErrorAction SilentlyContinue }
  if (Test-Path $PyInstallerCache2) { Remove-Item -Recurse -Force $PyInstallerCache2 -ErrorAction SilentlyContinue }
} else {
  Write-Host "Keep enabled: no final cleaning (venv/build/dist/spec/caches preserved)"
}

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "ZIP: $ZipPath"
Write-Host "SHA: $ShaPath"