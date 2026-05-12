# Flujo inicial de codigo

Este documento resume como ejecutar el primer flujo reproducible del proyecto antes de incorporar VAE y TimeGAN.

## Instalacion

Desde la raiz del repositorio:

```bash
python -m pip install -e .
```

Esto instala el paquete `tfm_pipeline` en modo editable, de forma que los cambios en `src/` se reflejan sin reinstalar.

## Baselines clasicos

Para ejecutar el flujo inicial:

```bash
python -m tfm_pipeline.run_baselines
```

El script realiza estas etapas:

1. Descarga precios ajustados desde Yahoo Finance.
2. Calcula retornos logaritmicos diarios.
3. Divide los datos en entrenamiento, validacion y prueba con corte temporal.
4. Calcula tres carteras base: equiponderada, minima varianza y Markowitz.
5. Evalua las carteras sobre retornos reales del conjunto de prueba.
6. Guarda metricas y pesos en `results/baselines/`.

## Salidas generadas

| Archivo | Contenido |
|---|---|
| `results/baselines/portfolio_metrics.csv` | Metricas financieras fuera de muestra |
| `results/baselines/equal_weight_weights.json` | Pesos de la cartera equiponderada |
| `results/baselines/minimum_variance_weights.json` | Pesos de la cartera de minima varianza |
| `results/baselines/markowitz_weights.json` | Pesos de la cartera Markowitz |
| `results/baselines/log_returns.csv` | Retornos logaritmicos descargados y alineados |

`results/` esta ignorado por Git porque son artefactos reproducibles.

## Siguiente paso

## VAE baseline

Para ejecutar el primer modelo generativo:

```bash
python -m tfm_pipeline.run_vae
```

El script realiza estas etapas:

1. Reutiliza la misma descarga, calculo de retornos y particion temporal.
2. Normaliza los retornos con media y desviacion calculadas solo en entrenamiento.
3. Construye ventanas temporales de 30 dias.
4. Entrena un VAE sobre las ventanas de entrenamiento con early stopping segun perdida de validacion.
5. Repite el entrenamiento para una pequena rejilla de valores beta.
6. Genera escenarios sinteticos de retornos para cada beta.
7. Evalua dos variantes: escenarios VAE sin calibrar y escenarios VAE calibrados a la volatilidad historica de entrenamiento.
8. Evalua la similitud distribucional entre retornos reales y sinteticos.
9. Construye carteras basadas en escenarios VAE y las evalua sobre datos reales de prueba.

Salidas principales:

| Archivo | Contenido |
|---|---|
| `results/vae/distribution_metrics.csv` | Metricas de similitud real-sintetico |
| `results/vae/distribution_summary.csv` | Resumen de media, volatilidad, cuantiles, asimetria y curtosis |
| `results/vae/beta_grid_summary.csv` | Comparacion agregada entre valores beta y variantes calibradas |
| `results/vae/portfolio_metrics.csv` | Metricas financieras de carteras VAE fuera de muestra |
| `results/vae/training_history_<beta>.csv` | Perdida total, reconstruccion y KL para cada beta |
| `results/vae/synthetic_returns_<beta>.csv` | Retornos sinteticos sin calibrar |
| `results/vae/synthetic_returns_<beta>_vol_calibrated.csv` | Retornos sinteticos calibrados a volatilidad historica |
| `results/vae/*_weights.json` | Pesos de cada cartera basada en escenarios VAE |

Las variantes de cartera VAE son:

| Variante | Descripcion |
|---|---|
| `minimum_variance` | Usa solo la covarianza estimada con escenarios sinteticos |
| `markowitz` | Usa media y covarianza estimadas con escenarios sinteticos |
| `historical_mean_synthetic_covariance` | Usa media historica y covarianza sintetica |
| `shrunk_mean_synthetic_covariance` | Usa media historica contraida hacia la media transversal y covarianza sintetica |

## TimeGAN baseline

Para ejecutar el primer baseline generativo temporal:

```bash
python -m tfm_pipeline.run_timegan
```

El script realiza estas etapas:

1. Reutiliza la misma descarga, calculo de retornos y particion temporal.
2. Normaliza los retornos con estadisticos calculados solo en entrenamiento.
3. Construye ventanas temporales de 30 dias manteniendo la estructura secuencial.
4. Entrena un TimeGAN compacto con fases de autoencoder, supervisor y entrenamiento adversarial conjunto.
5. Genera escenarios sinteticos secuenciales de retornos.
6. Evalua dos variantes: TimeGAN sin calibrar y TimeGAN calibrado a la volatilidad historica de entrenamiento.
7. Aplica el mismo protocolo de metricas distribucionales y evaluacion financiera fuera de muestra usado para VAE.

Salidas principales:

| Archivo | Contenido |
|---|---|
| `results/timegan/distribution_metrics.csv` | Metricas de similitud real-sintetico |
| `results/timegan/distribution_summary.csv` | Resumen estadistico por activo y variante |
| `results/timegan/portfolio_metrics.csv` | Metricas financieras de carteras TimeGAN fuera de muestra |
| `results/timegan/training_history.csv` | Perdidas de autoencoder, supervisor, generador y discriminador |
| `results/timegan/synthetic_returns.csv` | Retornos sinteticos sin calibrar |
| `results/timegan/synthetic_returns_vol_calibrated.csv` | Retornos sinteticos calibrados a volatilidad historica |
| `results/timegan/*_weights.json` | Pesos de cada cartera basada en escenarios TimeGAN |

La configuracion inicial de TimeGAN prioriza ejecucion rapida y reproducibilidad. Si los resultados iniciales son estables, se puede aumentar el numero de epocas o la dimension oculta para la ejecucion final.

## Comparacion de resultados

Tras ejecutar baselines, VAE y TimeGAN, se puede generar una tabla combinada con:

```bash
python -m tfm_pipeline.compare_results
```

La salida se guarda en `results/combined_portfolio_metrics.csv`.
