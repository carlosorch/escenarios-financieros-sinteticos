#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Verificando herramientas base..."

if ! command -v git >/dev/null 2>&1; then
  echo "[setup][error] Git no esta instalado. Instala Git y vuelve a ejecutar este script."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[setup][error] Docker no esta instalado. Instala Docker Desktop/Engine y vuelve a ejecutar este script."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[setup][error] Docker esta instalado pero no responde. Abre Docker Desktop o inicia el servicio Docker."
  exit 1
fi

echo "[setup] Docker OK. Descargando imagen WebLaTex (primera vez puede tardar)..."
docker pull sanjibsen/weblatex:latest

mkdir -p PDF

echo "[setup] Compilando prueba inicial..."
docker run --rm -v "$(pwd)":/work -w /work sanjibsen/weblatex:latest \
  latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex >/dev/null

if [[ ! -f PDF/plantilla.pdf ]]; then
  echo "[setup][error] No se genero PDF/plantilla.pdf"
  exit 1
fi

echo "[setup] Todo listo. Puedes compilar desde VS Code con:"
echo "        Terminal -> Run Task -> Compile thesis PDF (Docker)"
