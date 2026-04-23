$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$miktexBins = @(
  "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64",
  "$env:ProgramFiles\MiKTeX\miktex\bin\x64",
  "${env:ProgramFiles(x86)}\MiKTeX\miktex\bin"
) | Where-Object { $_ -and (Test-Path $_) }

$perlBins = @(
  "C:\Strawberry\perl\bin",
  "$env:ProgramFiles\Strawberry\perl\bin",
  "${env:ProgramFiles(x86)}\Strawberry\perl\bin"
) | Where-Object { $_ -and (Test-Path $_) }

foreach ($bin in $miktexBins) {
  if ($env:Path -notlike "*$bin*") {
    $env:Path = "$bin;$env:Path"
  }
}

foreach ($bin in $perlBins) {
  if ($env:Path -notlike "*$bin*") {
    $env:Path = "$bin;$env:Path"
  }
}

if (-not (Get-Command latexmk -ErrorAction SilentlyContinue)) {
  Write-Error "[compile][error] No se encontro latexmk. Ejecuta primero la task 'Setup local thesis environment'."
}

if (-not (Get-Command perl -ErrorAction SilentlyContinue)) {
  Write-Error "[compile][error] latexmk necesita Perl. Ejecuta primero la task 'Setup local thesis environment'."
}

New-Item -ItemType Directory -Force -Path "PDF" | Out-Null

& latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex
exit $LASTEXITCODE
