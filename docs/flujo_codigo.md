# Flujo de ejecucion del codigo

Guia minima para instalar y ejecutar el pipeline Python del TFM desde la raiz del repositorio.

## Requisitos

- Python 3.10 o superior.
- Git.
- Conexion a internet para descargar precios desde Yahoo Finance.

Usamos `python3` porque en macOS y Linux suele ser el comando correcto. Si tu equipo usa `python`, puedes sustituirlo.

## Instalacion rapida

Opcion recomendada con `uv`:

```bash
uv sync --extra dev
```

Si no tienes `uv`, instala el paquete en modo editable con `pip`:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

Si aparece un error de permisos con `pip`:

```bash
python3 -m pip install --user -e ".[dev]"
```

## Mac

En Mac no uses `requirements-cuda.txt`: eso es solo para CUDA/NVIDIA.

En Mac con Apple Silicon (`M1`, `M2`, `M3` o `M4`), VAE y TimeGAN intentan usar `mps`, que es la alternativa de Apple a CUDA. Si `mps` no esta disponible, el codigo cae automaticamente a CPU.

No hay que instalar `mps` aparte: viene incluido con PyTorch en macOS cuando el equipo y la version de macOS lo soportan.

Para comprobar si PyTorch detecta `mps`:

```bash
python3 -c "import torch; print(torch.__version__); print(torch.backends.mps.is_available())"
```

## Linux / NVIDIA

Si tienes GPU NVIDIA y quieres usar CUDA:

```bash
python3 -m pip install -r requirements-cuda.txt
python3 -m pip install -e ".[dev]"
```

Para comprobar CUDA:

```bash
python3 -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

## Comprobacion inicial

Antes de lanzar experimentos largos:

Con `uv`:

```bash
uv run python -c "import tfm_pipeline; print('tfm_pipeline OK')"
uv run pytest
```

Con el entorno instalado por `pip`:

```bash
python3 -c "import tfm_pipeline; print('tfm_pipeline OK')"
python3 -m pytest
```

La configuracion de `pytest` ya apunta a `src/`, por lo que no hace falta exportar `PYTHONPATH` manualmente.

## Para la tarea de Lola

Lola solo necesita comprobar tests y ejecutar baselines. No hace falta ejecutar VAE ni TimeGAN.

```bash
uv sync --extra dev
uv run pytest
uv run python -m tfm_pipeline.run_baselines
```

Equivalente con `pip`:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m tfm_pipeline.run_baselines
```

Salidas principales:

| Archivo | Contenido |
|---|---|
| `results/baselines/portfolio_metrics.csv` | Metricas financieras fuera de muestra |
| `results/baselines/*_weights.json` | Pesos de las carteras base |
| `results/baselines/log_returns.csv` | Retornos descargados y alineados |

`results/` esta ignorado por Git porque contiene artefactos reproducibles.

## Flujo completo

Ejecutar en este orden:

```bash
uv run python -m tfm_pipeline.run_baselines
uv run python -m tfm_pipeline.run_vae
uv run python -m tfm_pipeline.run_timegan
uv run python -m tfm_pipeline.run_timegan_multiseed
uv run python -m tfm_pipeline.report_timegan_multiseed
uv run python -m tfm_pipeline.compare_results
uv run python scripts/generate-result-figures.py
```

Si usas un entorno instalado con `pip`, sustituye `uv run python` por `python3`.

Salidas principales:

| Carpeta | Contenido |
|---|---|
| `results/baselines/` | Baselines clasicos |
| `results/vae/` | Escenarios y metricas VAE |
| `results/timegan/` | Escenarios y metricas TimeGAN |
| `results/timegan_multiseed/` | Robustez TimeGAN por semilla, ranking de seleccion por validacion y reporte legible |
| `results/combined_portfolio_metrics.csv` | Comparacion agregada |
| `media/result_*.png` | Figuras actualizadas para el documento LaTeX |

En `results/timegan_multiseed/` se generan tambien `metadata.json`, `seed_ranking.csv`, `best_seed.json`, `best_seed_portfolio_metrics.csv`, `diagnostic_summary_by_seed.csv`, `validation_diagnostic_summary_by_seed.csv`, `portfolio_metrics_by_seed.csv`, `training_history_by_seed.csv` y `report.md`. La semilla seleccionada se escoge solo con diagnosticos de validacion; las metricas financieras de prueba se consultan despues para reportar el rendimiento final.

## Integracion continua Python

El workflow `.github/workflows/python-tests.yml` ejecuta los tests unitarios con `uv` cuando cambian `src/`, `tests/`, `pyproject.toml`, `requirements*.txt` o el propio workflow. Tambien se puede lanzar manualmente desde GitHub Actions.
