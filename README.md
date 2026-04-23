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

## Flujo recomendado en local

1. Clonar el repo y abrirlo en VS Code.
2. Tener Docker arrancado.
3. Editar `plantilla.tex` y guardar (`Ctrl+S`) si tienes `latexmk` instalado localmente.
4. Si no tienes LaTeX instalado, ejecutar la tarea `Compile thesis PDF (Docker)` desde `Terminal` -> `Run Task`.
5. Revisar `PDF/plantilla.pdf` con un visor PDF local o en la pestaña de LaTeX Workshop.

## Compilacion local con VS Code

- Si tienes TeX Live/MiKTeX + `latexmk` en tu equipo, `LaTeX Workshop` recompila al guardar.
- Si no quieres instalar LaTeX, usa Docker con la tarea incluida de VS Code.

## Compilacion manual en GitHub

1. Ir a `Actions` en el repositorio.
2. Abrir `Build Thesis PDF`.
3. Pulsar `Run workflow`.
4. Descargar el artefacto `tesis-pdf` cuando termine.

Este workflow ya no se ejecuta automaticamente en cada `push` o `pull request`.

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
