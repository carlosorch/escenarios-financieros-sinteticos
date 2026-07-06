#!/usr/bin/env bash
set -euo pipefail

if [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(pwd -W)\\scripts\\compile-local-windows.ps1"
  exit $?
fi

mkdir -p PDF
latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF memoria.tex
