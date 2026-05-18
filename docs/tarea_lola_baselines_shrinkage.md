# Tarea tecnica - Lola: baselines robustos con shrinkage

## Objetivo

Reforzar la comparacion financiera del TFM incorporando baselines clasicos mas solidos basados en estimacion robusta de la matriz de covarianzas. La finalidad no es hacer que los modelos generativos ganen, sino que la comparacion sea academicamente defendible.

## Contexto

Actualmente el pipeline ya calcula tres baselines en `src/tfm_pipeline/run_baselines.py`:

- `equal_weight`
- `minimum_variance`
- `markowitz`

La optimizacion se implementa en `src/tfm_pipeline/optimization.py` con restricciones long-only, pesos entre 0 y 1 y suma de pesos igual a 1.

El problema es que Markowitz y minima varianza dependen de la covarianza historica muestral, que puede ser inestable. Una extension natural y rigurosa es incorporar Ledoit-Wolf covariance shrinkage.

## Archivos principales

- `src/tfm_pipeline/optimization.py`
- `src/tfm_pipeline/run_baselines.py`
- `tests/unit/test_optimization.py`
- Opcional: `src/tfm_pipeline/config.py`
- Opcional: `docs/flujo_codigo.md`

## Tareas

### 1. Implementar estimacion Ledoit-Wolf

Anadir una funcion en `optimization.py`, por ejemplo:

```python
def ledoit_wolf_covariance(returns: pd.DataFrame, periods_per_year: int = 252) -> np.ndarray:
    ...
```

Requisitos:

- Usar `sklearn.covariance.LedoitWolf`.
- Devolver una matriz `n_assets x n_assets` anualizada.
- Mantener el orden de columnas de `returns`.
- No modificar los datos de entrada.

### 2. Implementar carteras con covarianza shrinkage

Anadir funciones similares a las existentes:

```python
def minimum_variance_weights_from_covariance(cov: np.ndarray) -> np.ndarray:
    ...

def ledoit_wolf_minimum_variance_weights(returns: pd.DataFrame, periods_per_year: int = 252) -> np.ndarray:
    ...

def ledoit_wolf_mean_variance_weights(
    returns: pd.DataFrame,
    risk_aversion: float = 1.0,
    periods_per_year: int = 252,
) -> np.ndarray:
    ...
```

Requisitos:

- Mantener restricciones long-only.
- Pesos entre 0 y 1.
- Suma de pesos igual a 1.
- Si la optimizacion falla, lanzar `RuntimeError` con mensaje claro.

### 3. Integrar nuevos baselines en `run_baselines.py`

Anadir al diccionario `weights` nuevas filas:

- `ledoit_wolf_minimum_variance`
- `ledoit_wolf_markowitz`

El archivo `results/baselines/portfolio_metrics.csv` debe incluir estos modelos cuando se ejecute:

```bash
PYTHONPATH=src python3 -m tfm_pipeline.run_baselines
```

Tambien se deben guardar pesos JSON:

- `results/baselines/ledoit_wolf_minimum_variance_weights.json`
- `results/baselines/ledoit_wolf_markowitz_weights.json`

### 4. Anadir diagnosticos de covarianza

Anadir, si encaja de forma limpia, una salida adicional:

```text
results/baselines/covariance_diagnostics.csv
```

Columnas sugeridas:

- `estimator`
- `condition_number`
- `average_variance`
- `average_absolute_correlation`

Estimadores:

- `sample_covariance`
- `ledoit_wolf_covariance`

Esto ayudara a explicar por que shrinkage puede ser mas estable.

## Tests obligatorios

Anadir tests en `tests/unit/test_optimization.py`.

Casos minimos:

- `ledoit_wolf_covariance` devuelve forma correcta.
- La matriz de covarianza no contiene `NaN`.
- Los pesos de `ledoit_wolf_minimum_variance_weights` suman 1.
- Los pesos estan entre 0 y 1.
- `ledoit_wolf_mean_variance_weights` funciona con datos sinteticos pequenos.
- La optimizacion no cambia el orden ni el numero de activos.

Comando de verificacion:

```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_optimization.py tests/unit/test_evaluation.py
```

Si es posible, ejecutar toda la suite:

```bash
PYTHONPATH=src python3 -m pytest tests/unit
```

## Criterios de aceptacion

- El pipeline de baselines sigue funcionando.
- Aparecen los nuevos modelos en `portfolio_metrics.csv`.
- Los pesos se guardan en JSON.
- Los nuevos tests pasan.
- No se modifica la particion temporal de datos.
- No se usa informacion de validacion ni test para calcular los pesos.
- No se editan manualmente resultados generados.

## Riesgos y decisiones

- Es posible que Ledoit-Wolf supere a TimeGAN o VAE. Esto no es un problema: mejora la rigurosidad de la comparacion.
- Si el baseline nuevo hace que los modelos generativos parezcan peores, la conclusion debe reformularse hacia evaluacion de escenarios sinteticos, no hacia superioridad financiera.
- Si la dependencia `scikit-learn` no esta disponible, revisar `requirements.txt` antes de anadir una nueva dependencia.

## Entregable final

Una rama o commit con:

- funciones nuevas en `optimization.py`
- integracion en `run_baselines.py`
- tests unitarios
- breve nota en `docs/flujo_codigo.md` si se anaden nuevos outputs

Mensaje de commit sugerido:

```text
Add shrinkage covariance baselines

- Add Ledoit-Wolf covariance estimation.
- Add minimum-variance and mean-variance portfolios using shrinkage covariance.
- Include shrinkage baselines in the baseline runner.
- Add unit tests for covariance shape and long-only portfolio constraints.
```
