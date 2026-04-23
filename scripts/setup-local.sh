#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Verificando entorno LaTeX local..."

if [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(pwd -W)\\scripts\\setup-local-windows.ps1"
  exit $?
fi

if ! command -v git >/dev/null 2>&1; then
  echo "[setup][error] Git no esta instalado. Instala Git y vuelve a ejecutar este script."
  exit 1
fi

install_with_apt() {
  sudo apt-get update
  sudo apt-get install -y \
    latexmk \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-lang-spanish \
    texlive-bibtex-extra
}

install_with_dnf() {
  sudo dnf install -y \
    latexmk \
    texlive-scheme-medium \
    texlive-collection-latexextra \
    texlive-collection-langspanish \
    texlive-apacite
}

install_with_pacman() {
  sudo pacman -Sy --needed \
    texlive-bin \
    texlive-core \
    texlive-latexextra \
    texlive-bibtexextra \
    texlive-langspanish
}

install_with_brew() {
  brew install --cask mactex-no-gui
}

if ! command -v latexmk >/dev/null 2>&1 || ! command -v pdflatex >/dev/null 2>&1 || ! command -v bibtex >/dev/null 2>&1; then
  echo "[setup] LaTeX local no esta instalado completo. Instalando dependencias..."

  if command -v apt-get >/dev/null 2>&1; then
    install_with_apt
  elif command -v dnf >/dev/null 2>&1; then
    install_with_dnf
  elif command -v pacman >/dev/null 2>&1; then
    install_with_pacman
  elif command -v brew >/dev/null 2>&1; then
    install_with_brew
    export PATH="/Library/TeX/texbin:$PATH"
  else
    echo "[setup][error] No se encontro un gestor compatible (apt, dnf, pacman o brew)."
    echo "[setup] Instala una distribucion TeX con latexmk, pdflatex y bibtex, y vuelve a ejecutar este script."
    exit 1
  fi
fi

mkdir -p PDF

echo "[setup] Compilando prueba inicial..."
latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF plantilla.tex >/dev/null

if [[ ! -f PDF/plantilla.pdf ]]; then
  echo "[setup][error] No se genero PDF/plantilla.pdf"
  exit 1
fi

echo "[setup] Todo listo. Puedes compilar desde VS Code con:"
echo "        Terminal -> Run Task -> Compile thesis PDF"
