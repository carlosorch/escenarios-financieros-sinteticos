$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

function Add-ExistingPath {
  param([string[]] $Paths)

  foreach ($path in $Paths) {
    if ($path -and (Test-Path $path) -and $env:Path -notlike "*$path*") {
      $env:Path = "$path;$env:Path"
    }
  }
}

function Refresh-ToolPaths {
  Add-ExistingPath @(
    "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64",
    "$env:ProgramFiles\MiKTeX\miktex\bin\x64",
    "${env:ProgramFiles(x86)}\MiKTeX\miktex\bin",
    "C:\Strawberry\perl\bin",
    "$env:ProgramFiles\Strawberry\perl\bin",
    "${env:ProgramFiles(x86)}\Strawberry\perl\bin"
  )
}

function Test-Command {
  param([string] $Name)
  return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WithChocolatey {
  param([string] $Package)

  if (-not (Test-Command "choco")) {
    Write-Error "[setup-ci][error] Chocolatey is not available on this Windows runner."
  }

  Write-Host "[setup-ci] Installing $Package with Chocolatey..."
  choco install $Package -y --no-progress
}

Refresh-ToolPaths

if (-not (Test-Command "pdflatex")) {
  Install-WithChocolatey "miktex"
  Refresh-ToolPaths
}

if (-not (Test-Command "perl")) {
  Install-WithChocolatey "strawberryperl"
  Refresh-ToolPaths
}

if (-not (Test-Command "pdflatex")) {
  Write-Error "[setup-ci][error] pdflatex is not available after installing MiKTeX."
}

if (-not (Test-Command "perl")) {
  Write-Error "[setup-ci][error] perl is not available after installing Strawberry Perl."
}

Write-Host "[setup-ci] Configuring MiKTeX automatic package installation..."
if (Test-Command "initexmf") {
  initexmf --set-config-value="[MPM]AutoInstall=1"
  initexmf --update-fndb
}

if (-not (Test-Command "latexmk")) {
  if (Test-Command "miktex") {
    miktex packages require latexmk
  }
  elseif (Test-Command "mpm") {
    mpm --install=latexmk
  }

  Refresh-ToolPaths
}

if (-not (Test-Command "latexmk")) {
  Write-Error "[setup-ci][error] latexmk is not available after MiKTeX setup."
}

New-Item -ItemType Directory -Force -Path "PDF" | Out-Null

Write-Host "[setup-ci] Compiling initial PDF..."
latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex

if ($LASTEXITCODE -ne 0 -or -not (Test-Path "PDF\plantilla.pdf")) {
  Write-Error "[setup-ci][error] PDF\plantilla.pdf was not generated."
}

Write-Host "[setup-ci] Windows CI LaTeX environment is ready."
