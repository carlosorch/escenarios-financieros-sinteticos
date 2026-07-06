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

function Add-MiKTeXToPath {
  foreach ($bin in $miktexBins) {
    if ($env:Path -notlike "*$bin*") {
      $env:Path = "$bin;$env:Path"
    }
  }
}

function Add-PerlToPath {
  foreach ($bin in $perlBins) {
    if ($env:Path -notlike "*$bin*") {
      $env:Path = "$bin;$env:Path"
    }
  }
}

function Test-LaTeXCommand {
  param([string] $Name)
  return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-PerlCommand {
  return $null -ne (Get-Command perl -ErrorAction SilentlyContinue)
}

function Invoke-WindowsPdfBuild {
  param(
    [string] $TexFile = "plantilla.tex",
    [string] $OutputDir = "PDF"
  )

  $baseName = [System.IO.Path]::GetFileNameWithoutExtension($TexFile)
  $pdfTarget = Join-Path $OutputDir "$baseName.pdf"

  New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

  if (Test-Path $pdfTarget) {
    Remove-Item $pdfTarget -Force
  }

  Write-Host "[setup] Ejecutando pdflatex (pasada 1)..."
  & pdflatex -interaction=nonstopmode -file-line-error $TexFile | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Error "[setup][error] Fallo pdflatex en la primera pasada."
  }

  Write-Host "[setup] Ejecutando bibtex..."
  & bibtex $baseName | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Error "[setup][error] Fallo bibtex durante la compilacion de prueba."
  }

  Write-Host "[setup] Ejecutando pdflatex (pasada 2)..."
  & pdflatex -interaction=nonstopmode -file-line-error $TexFile | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Error "[setup][error] Fallo pdflatex en la segunda pasada."
  }

  Write-Host "[setup] Ejecutando pdflatex (pasada 3)..."
  & pdflatex -interaction=nonstopmode -file-line-error $TexFile | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Error "[setup][error] Fallo pdflatex en la tercera pasada."
  }

  if (-not (Test-Path "$baseName.pdf")) {
    Write-Error "[setup][error] No se genero $baseName.pdf en la raiz del proyecto."
  }

  Copy-Item "$baseName.pdf" $pdfTarget -Force
}

function Install-MiKTeX {
  $winget = Get-Command winget.exe -ErrorAction SilentlyContinue

  if (-not $winget) {
    Write-Error "[setup][error] winget no esta disponible. Instala MiKTeX manualmente: https://miktex.org/download"
  }

  Write-Host "[setup] MiKTeX no esta instalado. Instalando MiKTeX con winget..."
  Write-Host "[setup] Windows puede pedir permisos de administrador para continuar."

  $wingetArgs = @(
    "install",
    "--id",
    "MiKTeX.MiKTeX",
    "--exact",
    "--source",
    "winget",
    "--accept-package-agreements",
    "--accept-source-agreements"
  )

  $process = Start-Process -FilePath $winget.Source -ArgumentList $wingetArgs -Verb RunAs -Wait -PassThru

  if ($process.ExitCode -ne 0) {
    Add-MiKTeXToPath

    if (Test-LaTeXCommand "pdflatex") {
      Write-Host "[setup] winget devolvio codigo $($process.ExitCode), pero MiKTeX ya esta disponible. Continuando..."
      return
    }

    Write-Error "[setup][error] La instalacion de MiKTeX fallo con codigo $($process.ExitCode)."
  }
}

function Install-StrawberryPerl {
  $winget = Get-Command winget.exe -ErrorAction SilentlyContinue

  if (-not $winget) {
    Write-Error "[setup][error] winget no esta disponible. Instala Strawberry Perl manualmente: https://strawberryperl.com/"
  }

  Write-Host "[setup] Perl no esta instalado. Instalando Strawberry Perl con winget..."
  Write-Host "[setup] Windows puede pedir permisos de administrador para continuar."

  $wingetArgs = @(
    "install",
    "--id",
    "StrawberryPerl.StrawberryPerl",
    "--exact",
    "--source",
    "winget",
    "--accept-package-agreements",
    "--accept-source-agreements"
  )

  $process = Start-Process -FilePath $winget.Source -ArgumentList $wingetArgs -Verb RunAs -Wait -PassThru

  if ($process.ExitCode -ne 0) {
    Refresh-PerlPaths

    if (Test-PerlCommand) {
      Write-Host "[setup] winget devolvio codigo $($process.ExitCode), pero Perl ya esta disponible. Continuando..."
      return
    }

    Write-Error "[setup][error] La instalacion de Strawberry Perl fallo con codigo $($process.ExitCode)."
  }
}

function Refresh-MiKTeXPaths {
  $script:miktexBins = @(
    "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64",
    "$env:ProgramFiles\MiKTeX\miktex\bin\x64",
    "${env:ProgramFiles(x86)}\MiKTeX\miktex\bin"
  ) | Where-Object { $_ -and (Test-Path $_) }

  Add-MiKTeXToPath
}

function Refresh-PerlPaths {
  $script:perlBins = @(
    "C:\Strawberry\perl\bin",
    "$env:ProgramFiles\Strawberry\perl\bin",
    "${env:ProgramFiles(x86)}\Strawberry\perl\bin"
  ) | Where-Object { $_ -and (Test-Path $_) }

  Add-PerlToPath
}

function Invoke-IfAvailable {
  param(
    [string] $Command,
    [string[]] $Arguments
  )

  $resolved = Get-Command $Command -ErrorAction SilentlyContinue

  if ($resolved) {
    & $resolved.Source @Arguments
  }
}

function Configure-MiKTeX {
  Write-Host "[setup] Configurando MiKTeX para instalar paquetes faltantes automaticamente..."

  Invoke-IfAvailable "initexmf" @("--set-config-value=[MPM]AutoInstall=1")
  Invoke-IfAvailable "initexmf" @("--update-fndb")

  if (-not (Test-LaTeXCommand "latexmk")) {
    if (Test-LaTeXCommand "miktex") {
      Invoke-IfAvailable "miktex" @("packages", "require", "latexmk")
    }
    else {
      Invoke-IfAvailable "mpm" @("--install=latexmk")
    }
  }
}

Refresh-MiKTeXPaths
Refresh-PerlPaths

if (-not (Test-LaTeXCommand "pdflatex")) {
  Install-MiKTeX
  Refresh-MiKTeXPaths
}

if (-not (Test-LaTeXCommand "pdflatex")) {
  Write-Error "[setup][error] MiKTeX parece instalado, pero pdflatex no esta disponible. Cierra y abre VS Code, y vuelve a ejecutar la task."
}

if (-not (Test-PerlCommand)) {
  Install-StrawberryPerl
  Refresh-PerlPaths
}

Configure-MiKTeX
Refresh-MiKTeXPaths
Refresh-PerlPaths

Write-Host "[setup] Herramientas LaTeX detectadas:"
& pdflatex --version | Select-Object -First 1 | Out-Host
& bibtex --version | Select-Object -First 1 | Out-Host
if (Test-LaTeXCommand "latexmk") {
  & latexmk -version | Select-Object -First 1 | Out-Host
}
else {
  Write-Host "[setup] latexmk no esta disponible; la compilacion local de Windows usara pdflatex + bibtex."
}
if (Test-PerlCommand) {
  & perl --version | Select-Object -First 2 | Out-Host
}
else {
  Write-Host "[setup] Perl no esta disponible; no es necesario para la task de compilacion de Windows."
}

Write-Host "[setup] Compilando prueba inicial..."
Invoke-WindowsPdfBuild

if (-not (Test-Path "PDF\memoria.pdf")) {
  Write-Error "[setup][error] No se genero PDF\memoria.pdf"
}

Write-Host "[setup] Todo listo. Puedes compilar desde VS Code con:"
Write-Host "        Terminal -> Run Task -> Compile thesis PDF"
