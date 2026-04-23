# TFM - Entorno colaborativo estilo Overleaf con WebLaTex

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/carlosorch/tfm)

Este repositorio esta preparado para trabajar la tesis con un flujo similar a Overleaf (edicion web, colaboracion en tiempo real y compilacion continua), pero con GitHub como base de control de versiones.

## Que queda configurado

- WebLaTex mediante `sanjibsen/weblatex:latest` en `.devcontainer/devcontainer.json`.
- Compilacion automatica al guardar (`latex-workshop`) y salida en `PDF/`.
- Extensions para colaboracion y redaccion: LaTeX Workshop, Live Share, Copilot y Grammarly.
- Configuracion local equivalente en `.vscode/settings.json` para quien trabaje sin Codespaces.
- Ignorado de artefactos de compilacion en `.gitignore`.
- CI de GitHub Actions para generar el PDF en cada push/PR.

## Flujo recomendado (tipo Overleaf)

1. Abrir el repo en GitHub.
2. Ir a `Code` -> `Codespaces` -> `Create codespace on main`.
3. Esperar a que arranque el contenedor (primera vez tarda mas).
4. Editar `plantilla.tex` y guardar (`Ctrl+S`).
5. Revisar `PDF/plantilla.pdf` (se regenera automaticamente).
6. Para coedicion en vivo, usar Live Share desde la barra lateral de VS Code web.

## Compilacion local con Docker

```bash
docker run --rm -v "$PWD":/work -w /work sanjibsen/weblatex:latest \
  latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex
```

El PDF queda en `PDF/plantilla.pdf`.

## Colaboracion entre miembros del TFM

- Cambios pequenos: commit directo a `main` (si el equipo lo acuerda).
- Cambios grandes: rama + pull request + revision/comentarios.
- Historial completo y reversible con Git (equivalente al historial de Overleaf, pero mas potente).

## Notas actuales del proyecto

- La compilacion funciona correctamente en este entorno.
- Existen varias citas sin entrada en `bibliografia.bib` (no bloquea el PDF, pero deja warnings).
