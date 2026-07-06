# Synthetic Financial Scenarios

Repositorio asociado al Trabajo de Fin de Máster **"Generación de escenarios sintéticos de retornos financieros mediante VAE y TimeGAN para optimización de carteras"**.

El proyecto implementa un pipeline reproducible en Python para descargar precios financieros, preparar retornos logarítmicos, generar escenarios sintéticos con modelos generativos y evaluar su utilidad en optimización de carteras.

## Objetivo

Evaluar si escenarios sintéticos generados mediante **VAE** y **TimeGAN** pueden preservar propiedades estadísticas, temporales e informacionales de retornos financieros reales y servir como apoyo para construir carteras comparables con métodos clásicos.

El repositorio incluye:

- código del pipeline experimental;
- modelos VAE y TimeGAN en PyTorch;
- baselines financieros clásicos;
- métricas distribucionales, temporales, informacionales y financieras;
- pruebas unitarias;
- memoria LaTeX del TFM y scripts de compilación.

## Diseño experimental

| Elemento | Valor |
| --- | --- |
| Fuente de datos | Yahoo Finance mediante `yfinance` |
| Activos | AAPL, MSFT, GOOGL, AMZN, META, NVDA, JPM, XOM, JNJ y PG |
| Frecuencia | Diaria |
| Variable modelada | Retornos logarítmicos |
| Periodo completo | 2015-01-01 a 2026-05-12 |
| Entrenamiento | 2015-01-01 a 2022-12-31 |
| Validación | 2023-01-01 a 2024-06-30 |
| Prueba | 2024-07-01 a 2026-05-12 |
| Ventana temporal | 30 días |
| Modelos generativos | VAE y TimeGAN |
| Baselines | Equiponderada, mínima varianza, Markowitz y Ledoit-Wolf |

La evaluación separa dos preguntas:

1. **Fidelidad generativa**: si los escenarios sintéticos conservan propiedades de los retornos reales.
2. **Utilidad financiera**: si las carteras construidas con esos escenarios se comportan razonablemente sobre datos reales fuera de muestra.

## Estructura del repositorio

```text
.
├── plantilla.tex                 # Memoria principal en LaTeX
├── bibliografia.bib              # Bibliografía APA
├── src/tfm_pipeline/             # Pipeline experimental Python
│   ├── config.py                 # Configuración del experimento
│   ├── data.py                   # Descarga y preparación de retornos
│   ├── evaluation.py             # Métricas financieras
│   ├── synthetic_evaluation.py   # Métricas de escenarios sintéticos
│   ├── optimization.py           # Optimización de carteras
│   ├── model_selection.py        # Selección por validación
│   ├── models/                   # VAE y TimeGAN
│   └── run_*.py                  # Puntos de entrada del pipeline
├── tests/unit/                   # Pruebas unitarias
├── docs/                         # Guías de ejecución y métricas
├── scripts/                      # Compilación LaTeX y generación de figuras
├── media/                        # Figuras usadas en la memoria
└── results/                      # Resultados generados localmente
```

## Instalación

Requisitos:

- Python 3.10 o superior;
- Git;
- conexión a internet para descargar precios desde Yahoo Finance.

Clonar el repositorio:

```bash
git clone https://github.com/carlosorch/synthetic-financial-scenarios.git
cd synthetic-financial-scenarios
```

Instalación recomendada con `uv`:

```bash
uv sync --extra dev
```

Alternativa con `pip`:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

En equipos Linux con GPU NVIDIA puede usarse el fichero CUDA:

```bash
python3 -m pip install -r requirements-cuda.txt
python3 -m pip install -e ".[dev]"
```

## Comprobación rápida

```bash
uv run python -c "import tfm_pipeline; print('tfm_pipeline OK')"
uv run pytest
```

Con `pip`, sustituir `uv run` por `python3 -m` cuando proceda:

```bash
python3 -m pytest
```

## Ejecución del pipeline

Flujo completo:

```bash
uv run python -m tfm_pipeline.run_baselines
uv run python -m tfm_pipeline.run_vae
uv run python -m tfm_pipeline.run_timegan
uv run python -m tfm_pipeline.run_timegan_multiseed
uv run python -m tfm_pipeline.report_timegan_multiseed
uv run python -m tfm_pipeline.compare_results
uv run python scripts/generate-result-figures.py
```

Para una comprobación corta, ejecutar solo los tests y los baselines:

```bash
uv run pytest
uv run python -m tfm_pipeline.run_baselines
```

Las salidas se generan en `results/`. Esta carpeta no se versiona porque contiene artefactos reproducibles.

## Resultados generados

| Ruta | Contenido |
| --- | --- |
| `results/baselines/` | Métricas y pesos de carteras clásicas |
| `results/vae/` | Escenarios y métricas del VAE |
| `results/timegan/` | Escenarios y métricas de TimeGAN |
| `results/timegan_multiseed/` | Evaluación multi-semilla, ranking y selección por validación |
| `results/combined_portfolio_metrics.csv` | Comparación agregada de carteras |
| `media/result_*.png` | Figuras regeneradas para la memoria |

El criterio de selección de TimeGAN se basa en diagnósticos de validación. Las métricas financieras de test se reservan para la evaluación final fuera de muestra.

## Compilación de la memoria

La memoria principal está en `plantilla.tex`.

Compilación local:

```bash
./scripts/compile-local.sh
```

En Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\compile-local-windows.ps1
```

También puede compilarse desde VS Code con la tarea **Compile thesis PDF**. El PDF generado se guarda en `PDF/plantilla.pdf`.

## Documentación útil

- `docs/flujo_codigo.md`: guía de instalación y ejecución del pipeline.
- `docs/metricas_experimento.md`: protocolo de métricas usado en el experimento.
- `plantilla.tex`: memoria completa del TFM.

## Reproducibilidad

El pipeline registra metadatos de ejecución como revisión de Git, rama activa, versión de Python, plataforma, paquetes instalados y disponibilidad de CUDA/MPS. Esto facilita reconstruir el entorno experimental y explicar diferencias entre ejecuciones.

Los modelos generativos son estocásticos; por ello, TimeGAN incluye una evaluación multi-semilla y una selección basada exclusivamente en validación.

## Limitaciones

Este repositorio tiene finalidad académica. No constituye asesoramiento financiero ni un sistema de trading. Los resultados deben interpretarse como evidencia experimental dentro del protocolo definido, no como garantía de rendimiento futuro.

## Referencias principales

- Yoon, J., Jarrett, D., & van der Schaar, M. (2019). *Time-series Generative Adversarial Networks*. NeurIPS.
- Kingma, D. P., & Welling, M. (2014). *Auto-Encoding Variational Bayes*. ICLR.
- Markowitz, H. (1952). *Portfolio Selection*. The Journal of Finance.

La bibliografía completa está en `bibliografia.bib` y en la memoria LaTeX.

## Licencia

Este proyecto se distribuye bajo licencia MIT. Ver el archivo `LICENSE`.
