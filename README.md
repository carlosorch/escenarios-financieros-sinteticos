# TFM - Flujo local con VS Code y LaTeX

Este repositorio esta preparado para trabajar la tesis en local con VS Code, LaTeX instalado en el ordenador y GitHub como control de versiones.

## Que queda configurado

- Compilacion local con `latexmk`, `pdflatex` y `bibtex`.
- Setup automatico desde VS Code para instalar/verificar dependencias LaTeX.
- Tarea de compilacion local a PDF.
- LaTeX Workshop configurado para usar `latexmk_local` como receta recomendada.
- Docker queda solo como fallback opcional, no como flujo principal.
- Workflow manual de GitHub Actions para generar el PDF cuando se necesite.

## Inicio rapido

1. Abrir el repo en VS Code.
2. Ejecutar `Terminal` -> `Run Task` -> `Setup local thesis environment`.
3. Cuando termine, ejecutar `Terminal` -> `Run Task` -> `Compile thesis PDF`.
4. Abrir `PDF/plantilla.pdf`.

En Windows, el setup instala MiKTeX y Strawberry Perl con `winget` si no estan instalados. Puede pedir permisos de administrador.

## Requisitos base

Cada persona del equipo debe tener:

- `Git`
- `VS Code`
- Cuenta de GitHub con acceso al repo

El setup del proyecto se encarga de LaTeX:

- Windows: instala/verifica MiKTeX y Strawberry Perl, necesario para ejecutar `latexmk`.
- Linux: instala paquetes TeX Live usando `apt`, `dnf` o `pacman` si estan disponibles.
- macOS: instala `mactex-no-gui` usando Homebrew si esta disponible.

## Instalacion base por sistema

### Windows

Opcion recomendada: usar `winget` en PowerShell.

```powershell
winget install --id Git.Git -e
winget install --id Microsoft.VisualStudioCode -e
```

Si `winget` no esta disponible, usar los instaladores oficiales:

- Git: `https://git-scm.com/downloads`
- VS Code: `https://code.visualstudio.com/Download`

No hace falta instalar Docker para trabajar en local.

### Linux Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y git
sudo snap install code --classic
```

### macOS

Con Homebrew:

```bash
brew install git
brew install --cask visual-studio-code
```

Si no tienes Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Clonar y abrir el repositorio

```bash
git clone git@github.com:carlosorch/tfm.git
cd tfm
code .
```

Si alguien no tiene SSH configurado en GitHub:

```bash
git clone https://github.com/carlosorch/tfm.git
cd tfm
code .
```

Al abrir el repo, VS Code deberia sugerir instalar extensiones recomendadas. Instalar como minimo:

- `LaTeX Workshop`
- `Live Share` si vais a compartir una sesion
- `Grammarly` solo si a esa persona le resulta util

## Setup local de LaTeX

En VS Code:

1. Ir a `Terminal` -> `Run Task`.
2. Elegir `Setup local thesis environment`.
3. Esperar a que instale/verifique LaTeX.
4. Confirmar que se genera `PDF/plantilla.pdf`.

Por terminal:

```bash
./scripts/setup-local.sh
```

En Windows tambien se puede ejecutar:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-local-windows.ps1
```

## Compilar el PDF

En VS Code:

1. Ir a `Terminal` -> `Run Task`.
2. Elegir `Compile thesis PDF`.

Por terminal:

```bash
./scripts/compile-local.sh
```

En Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\compile-local-windows.ps1
```

Salida esperada:

- `PDF/plantilla.pdf`

## Compilar con LaTeX Workshop

La receta recomendada es:

```text
latexmk_local (recommended)
```

Para compilar desde LaTeX Workshop:

- abrir `plantilla.tex`
- ejecutar `LaTeX Workshop: Build LaTeX project`
- o usar el boton de build de la extension

La autocompilacion al guardar esta desactivada en `.vscode/settings.json` para evitar builds constantes. Si el equipo la quiere activar, cambiar:

```json
"latex-workshop.latex.autoBuild.run": "onSave"
```

## Archivos principales

- Documento principal: `plantilla.tex`
- Bibliografia: `bibliografia.bib`
- Imagenes: `media/`
- PDF generado: `PDF/plantilla.pdf`

## Flujo diario recomendado

Antes de empezar:

```bash
git pull
```

Despues de editar y compilar:

```bash
git status
git add .
git commit -m "Describe brevemente el cambio"
git push
```

Si dos personas editan a la vez:

- antes de empezar: `git pull`
- al terminar: `git add`, `git commit`, `git push`
- si Git avisa de conflicto: hacer otro `git pull` y resolverlo antes de seguir

## Compilacion remota manual en GitHub

Usar esto solo si quereis generar un PDF desde GitHub sin depender del ordenador local.

Pasos:

1. Entrar en el repo en GitHub.
2. Abrir la pestana `Actions`.
3. Entrar en `Build Thesis PDF`.
4. Pulsar `Run workflow`.
5. Esperar a que termine.
6. Descargar el artefacto `tesis-pdf`.

## Prueba de instalacion desde cero

El repositorio incluye una prueba aislada para comprobar si una persona con un equipo limpio podria instalar las dependencias y compilar el PDF.

La prueba se ejecuta en GitHub Actions sobre maquinas nuevas de:

- Linux: `ubuntu-latest`
- macOS: `macos-latest`
- Windows: `windows-latest`

Workflow:

```text
Fresh Install Test
```

Que valida:

- instalacion/verificacion de LaTeX en Linux y macOS usando `scripts/setup-local.sh`
- instalacion/verificacion de LaTeX en Windows usando `scripts/setup-ci-windows.ps1`
- disponibilidad de `latexmk`, `pdflatex` y `bibtex`
- disponibilidad de `perl` en Windows, necesario para `latexmk`
- generacion correcta de `PDF/plantilla.pdf`

En Windows, la prueba de GitHub Actions usa un script separado porque el setup normal para usuarios puede requerir permisos de administrador mediante `winget`. El flujo para usuarios sigue siendo:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-local-windows.ps1
```

Para ejecutar la prueba desde GitHub:

1. Entrar en el repo en GitHub.
2. Abrir la pestana `Actions`.
3. Entrar en `Fresh Install Test`.
4. Pulsar `Run workflow`.
5. Revisar los tres jobs: Linux, macOS y Windows.
6. Descargar el artefacto `thesis-pdf-*` si se quiere revisar el PDF generado por cada sistema.

## Docker como fallback

Docker ya no es el flujo principal. Si alguien lo tiene instalado y quiere usarlo, sigue disponible:

```bash
docker run --rm -v "$PWD":/work -w /work sanjibsen/weblatex:latest \
  latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex
```

En VS Code tambien existe la task:

```text
Compile thesis PDF (Docker fallback)
```

## Problemas tipicos

Si VS Code no encuentra `latexmk` justo despues de instalar MiKTeX:

- cerrar VS Code
- abrir VS Code otra vez
- ejecutar `Setup local thesis environment`

Si `latexmk` dice que falta `perl`:

- ejecutar `Setup local thesis environment`
- aceptar la instalacion de Strawberry Perl si Windows pide permisos
- cerrar y abrir VS Code si la terminal antigua no detecta el nuevo `PATH`

Si MiKTeX avisa `So far, you have not checked for MiKTeX updates`, el PDF puede estar compilando correctamente; para quitar el aviso, abrir `MiKTeX Console` y pulsar `Check for updates`.

Si quieres recompilar limpio:

```bash
rm -rf PDF
mkdir PDF
./scripts/compile-local.sh
```

En Windows:

```powershell
Remove-Item -Recurse -Force .\PDF
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\compile-local-windows.ps1
```

## Codespaces

Codespaces queda disponible como opcion secundaria. El flujo recomendado para este proyecto es trabajar en local con LaTeX instalado en el ordenador.

## Colaboracion entre miembros del TFM

- Cambios pequenos: commit directo a `main` si el equipo lo acuerda.
- Cambios grandes: rama + pull request + revision.
- Historial completo y reversible con Git.
- GitHub Actions consume cuota de la cuenta propietaria del repositorio.
