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

if (-not (Get-Command pdflatex -ErrorAction SilentlyContinue)) {
  Write-Error "[compile][error] No se encontro pdflatex. Ejecuta primero la task 'Setup local thesis environment'."
}

if (-not (Get-Command bibtex -ErrorAction SilentlyContinue)) {
  Write-Error "[compile][error] No se encontro bibtex. Ejecuta primero la task 'Setup local thesis environment'."
}

New-Item -ItemType Directory -Force -Path "PDF" | Out-Null

$texFile = "memoria.tex"
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($texFile)
$pdfTarget = Join-Path "PDF" "$baseName.pdf"

if (Test-Path $pdfTarget) {
  Remove-Item $pdfTarget -Force
}

Write-Host "[compile] Ejecutando pdflatex (pasada 1)..."
& pdflatex -interaction=nonstopmode -file-line-error $texFile
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "[compile] Ejecutando bibtex..."
& bibtex $baseName
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "[compile] Ejecutando pdflatex (pasada 2)..."
& pdflatex -interaction=nonstopmode -file-line-error $texFile
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "[compile] Ejecutando pdflatex (pasada 3)..."
& pdflatex -interaction=nonstopmode -file-line-error $texFile
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

if (-not (Test-Path "$baseName.pdf")) {
  Write-Error "[compile][error] No se genero $baseName.pdf en la raiz del proyecto."
}

Copy-Item "$baseName.pdf" $pdfTarget -Force
Write-Host "[compile] PDF generado en $pdfTarget"
