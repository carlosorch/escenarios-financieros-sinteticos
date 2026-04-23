# TFM - Flujo local con VS Code y WebLaTex

Este repositorio esta preparado para trabajar la tesis en local con VS Code, Docker y GitHub como base de control de versiones.

## Que queda configurado

- WebLaTex mediante `sanjibsen/weblatex:latest` en `.devcontainer/devcontainer.json`.
- Compilacion automatica al guardar (`latex-workshop`) y salida en `PDF/`.
- Tarea de VS Code para compilar con Docker sin instalar LaTeX localmente.
- Extensions para colaboracion y redaccion: LaTeX Workshop, Live Share, Copilot y Grammarly.
- Configuracion local equivalente en `.vscode/settings.json` para quien trabaje sin Codespaces.
- Ignorado de artefactos de compilacion en `.gitignore`.
- Workflow manual de GitHub Actions para generar el PDF solo cuando se necesite.

## Guia paso a paso para trabajar en local

### 1. Instalar lo minimo necesario

Cada persona del equipo debe tener instalado:

- `Git`
- `VS Code`
- `Docker Desktop` o `Docker Engine`
- Cuenta de GitHub con acceso al repo `carlosorch/tfm`

### Instalacion en Linux, macOS y Windows

#### Linux (Ubuntu/Debian)

Git:

```bash
sudo apt update
sudo apt install -y git
```

VS Code:

```bash
sudo snap install code --classic
```

Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

#### macOS

Si tienes `Homebrew` instalado:

Git:

```bash
brew install git
```

VS Code:

```bash
brew install --cask visual-studio-code
```

Docker Desktop:

```bash
brew install --cask docker
```

Despues de instalar Docker Desktop en macOS:

1. Abrir la app `Docker`
2. Esperar a que termine de arrancar
3. Comprobarlo con:

```bash
docker --version
docker ps
```

Si no tienes `Homebrew`, puedes instalarlo con:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Windows

Opcion recomendada: usar `winget` en PowerShell.

Git:

```powershell
winget install --id Git.Git -e
```

VS Code:

```powershell
winget install --id Microsoft.VisualStudioCode -e
```

Docker Desktop:

```powershell
winget install --id Docker.DockerDesktop -e
```

Despues de instalar Docker Desktop en Windows:

1. Abrir `Docker Desktop`
2. Esperar a que termine de arrancar
3. Comprobarlo en PowerShell:

```powershell
docker --version
docker ps
```

Si `winget` no esta disponible, usar los instaladores oficiales:

- Git: `https://git-scm.com/downloads`
- VS Code: `https://code.visualstudio.com/Download`
- Docker Desktop: `https://www.docker.com/products/docker-desktop/`

Comprobacion rapida en terminal:

```bash
git --version
docker --version
code --version
```

### 2. Clonar el repositorio

En una terminal, ejecutar:

```bash
git clone git@github.com:carlosorch/tfm.git
cd tfm
```

Si alguien no tiene SSH configurado en GitHub, puede usar HTTPS:

```bash
git clone https://github.com/carlosorch/tfm.git
cd tfm
```

### 3. Abrir el proyecto en VS Code

Desde la carpeta del repo:

```bash
code .
```

Al abrirlo, VS Code deberia sugerir instalar extensiones recomendadas.
Instalar como minimo:

- `LaTeX Workshop`
- `Live Share` si vais a compartir una sesion
- `Grammarly` solo si a esa persona le resulta util

### 4. Arrancar Docker

Antes de compilar con el flujo recomendado, Docker tiene que estar encendido.

Comprobarlo con:

```bash
docker ps
```

Si ese comando responde sin error, Docker esta listo.

### 5. Editar la tesis

El archivo principal es:

```text
plantilla.tex
```

La bibliografia esta en:

```text
bibliografia.bib
```

Las imagenes estan en:

```text
media/
```

### 6. Compilar el PDF en local con Docker

Opcion recomendada si no quereis instalar LaTeX completo en cada ordenador.

En VS Code:

1. Ir a `Terminal` -> `Run Task`
2. Elegir `Compile thesis PDF (Docker)`

O por terminal manual:

```bash
docker run --rm -v "$PWD":/work -w /work sanjibsen/weblatex:latest \
  latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex
```

Salida esperada:

- El PDF se genera en `PDF/plantilla.pdf`

### 7. Compilar al guardar con LaTeX Workshop

Esto solo aplica si esa persona tiene LaTeX instalado localmente, por ejemplo `latexmk`.

Comprobacion:

```bash
latexmk -v
```

Si existe `latexmk`, entonces:

- abrir `plantilla.tex`
- guardar con `Ctrl+S`
- `LaTeX Workshop` recompilara automaticamente

Si `latexmk` no esta instalado, usar Docker como en el paso anterior.

### 8. Ver el PDF

Las dos opciones mas comodas son:

- abrir `PDF/plantilla.pdf` con el visor de VS Code
- abrir `PDF/plantilla.pdf` con el visor PDF del sistema operativo

Si el visor integrado va lento, usar el visor local del sistema suele ir mejor.

### 9. Flujo diario recomendado

Cada vez que alguien vaya a trabajar:

```bash
cd tfm
git pull
```

Editar los archivos necesarios y compilar.

Cuando termine sus cambios:

```bash
git status
git add .
git commit -m "Describe brevemente el cambio"
git push
```

### 10. Si dos personas editan a la vez

Flujo simple recomendado:

- antes de empezar: `git pull`
- al terminar: `git add`, `git commit`, `git push`
- si Git avisa de conflicto: hacer otro `git pull` y resolverlo antes de seguir

### 11. Compilacion remota manual en GitHub

Usar esto solo si quereis generar un PDF desde GitHub sin depender del ordenador local.

Pasos:

1. Entrar en el repo en GitHub
2. Abrir la pestaña `Actions`
3. Entrar en `Build Thesis PDF`
4. Pulsar `Run workflow`
5. Esperar a que termine
6. Descargar el artefacto `tesis-pdf`

### 12. Problemas tipicos

Si falla Docker:

```bash
docker ps
```

Si falla Git porque faltan cambios remotos:

```bash
git pull
```

Si quereis recompilar limpio:

```bash
rm -rf PDF
mkdir PDF
docker run --rm -v "$PWD":/work -w /work sanjibsen/weblatex:latest \
  latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex
```

## Compilacion local con VS Code

- Si tienes TeX Live/MiKTeX + `latexmk` en tu equipo, `LaTeX Workshop` recompila al guardar.
- Si no quieres instalar LaTeX, usa Docker con la tarea incluida de VS Code.

Este workflow no se ejecuta automaticamente en cada `push` o `pull request`.

## Compilacion local con Docker

```bash
docker run --rm -v "$PWD":/work -w /work sanjibsen/weblatex:latest \
  latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex
```

El PDF queda en `PDF/plantilla.pdf`.

## Codespaces

Codespaces queda disponible como opcion secundaria, pero el flujo recomendado para este proyecto es trabajar en local por rendimiento y mejor compatibilidad con el visor PDF y las extensiones.

## Colaboracion entre miembros del TFM

- Cambios pequenos: commit directo a `main` (si el equipo lo acuerda).
- Cambios grandes: rama + pull request + revision/comentarios.
- Historial completo y reversible con Git (equivalente al historial de Overleaf, pero mas potente).
- GitHub Actions consume cuota de la cuenta propietaria del repositorio (`carlosorch/tfm`).

## Notas actuales del proyecto

- La compilacion funciona correctamente en este entorno.
- La bibliografia actual ya resuelve las referencias que faltaban en el documento.
