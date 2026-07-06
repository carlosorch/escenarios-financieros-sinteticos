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
    texlive-fonts-extra \
    texlive-lang-spanish \
    texlive-bibtex-extra
}

install_with_dnf() {
  sudo dnf install -y \
    latexmk \
    texlive-scheme-medium \
    texlive-collection-latexextra \
    texlive-collection-fontsextra \
    texlive-collection-langspanish \
    texlive-apacite
}

install_with_pacman() {
  sudo pacman -Sy --needed \
    texlive-bin \
    texlive-core \
    texlive-latexextra \
    texlive-fontsextra \
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

for command in latexmk pdflatex bibtex; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "[setup][error] No se encontro $command tras instalar dependencias."
    echo "[setup] Cierra y abre la terminal o VS Code, y vuelve a ejecutar este script."
    exit 1
  fi
done

echo "[setup] Herramientas LaTeX detectadas:"
latexmk -version | head -n 1
pdflatex --version | head -n 1
bibtex --version | head -n 1

mkdir -p PDF

echo "[setup] Compilando prueba inicial..."
latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=PDF memoria.tex >/dev/null

if [[ ! -f PDF/memoria.pdf ]]; then
  echo "[setup][error] No se genero PDF/memoria.pdf"
  exit 1
fi

echo "[setup] Todo listo. Puedes compilar desde VS Code con:"
echo "        Terminal -> Run Task -> Compile thesis PDF"
