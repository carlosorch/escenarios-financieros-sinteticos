# Resumen de la tarea baselines shrinkage

Documento de seguimiento con un resumen completo del trabajo realizado para incorporar baselines robustos con covarianza Ledoit-Wolf.

## 1. Objetivo inicial

La tarea consistía en reforzar el pipeline financiero del proyecto añadiendo baselines más robustos basados en Ledoit-Wolf shrinkage para estimar la matriz de covarianzas.

## 2. Punto de partida del proyecto

Antes de la tarea, `src/tfm_pipeline/run_baselines.py` ya generaba tres baselines:

- `equal_weight`
- `minimum_variance`
- `markowitz`

La optimización de estos modelos dependía de la covarianza muestral de retornos y mantenía restricciones long-only, pesos en `[0, 1]` y suma total 1.

## 3. Aspectos añadidos en la tarea

### 3.1 Estimación Ledoit-Wolf

En `src/tfm_pipeline/optimization.py` se añadió:

- `ledoit_wolf_covariance(returns, periods_per_year=252)`
  Esta función recibe los retornos de los activos y calcula una matriz de covarianzas utilizando sklearn.covariance.LedoitWolf,luego anualiza esa matriz según los periodos de mercado por año y conserva el mismo orden de activos que tienen las columnas del DataFrame.

### 3.2 Portafolios con covarianza shrinkage
A partir de esta nueva matriz de covarianzas, también se han incorporado nuevas funciones para calcular carteras optimizadas.

- `minimum_variance_weights_from_covariance(cov)`: función genérica para obtener pesos de mínima varianza a partir de una matriz de covarianzas ya calculada
- `ledoit_wolf_minimum_variance_weights(returns, periods_per_year=252)`: primero estima la covarianza con Ledoit-Wolf a partir de los retornos y uego utiliza esa covarianza para obtener la cartera de mínima varianza.
- `ledoit_wolf_mean_variance_weights(returns, risk_aversion=1.0, periods_per_year=252)`:estima la covarianza con Ledoit-Wolf, pero construye una cartera mean-variance (Markowitz) considerando retorno esperado y riesgo.

Estas heredan las restricciones existentes: long-only, pesos entre 0 y 1, y suma igual a 1. Si la optimización falla, lanzan un `RuntimeError` con mensaje claro.

### 3.3 Integración en el runner
 Se han añadido dos nuevos modelos al diccionario de pesos utilizado por el runner: ledoit_wolf_minimum_variance y ledoit_wolf_markowitz para que `python -m tfm_pipeline.run_baselines` los evalúe igual que los demás. El script calcula las métricas de test para todas las estrategias y guarda los pesos de cada cartera en JSON, de modo que la comparación es uniforme y no cambia la partición de datos.

## 4. Resultados de ejecución

Al ejecutar `python -m tfm_pipeline.run_baselines` se produce:

- `results/baselines/portfolio_metrics.csv` con 5 modelos:
  - `equal_weight`
  - `minimum_variance`
  - `markowitz`
  - `ledoit_wolf_minimum_variance`
  - `ledoit_wolf_markowitz`

- Pesos guardados en JSON:
  - `results/baselines/equal_weight_weights.json`
  - `results/baselines/minimum_variance_weights.json`
  - `results/baselines/markowitz_weights.json`
  - `results/baselines/ledoit_wolf_minimum_variance_weights.json`
  - `results/baselines/ledoit_wolf_markowitz_weights.json`

- Otros artefactos generados automáticamente:
  - `results/baselines/log_returns.csv`
  - `results/baselines/metadata.json`

## 5. Validación con tests

Se validó la implementación con tests en `tests/unit/test_optimization.py`.

Casos cubiertos:

- `ledoit_wolf_covariance` devuelve la forma correcta.
- La matriz de covarianza no contiene `NaN`.
- `ledoit_wolf_minimum_variance_weights` suma 1.
- Los pesos están en el rango `[0, 1]`.
- `ledoit_wolf_mean_variance_weights` funciona con datos sintéticos.
- La optimización no modifica el orden ni el número de activos.

## 6. Interpretación de los resultados

Los resultados muestran que la cartera ledoit_wolf_minimum_variance mejora ligeramente a la cartera minimum_variance clásica. La rentabilidad anualizada aumenta de forma leve, la volatilidad se reduce ligeramente y el Sharpe ratio mejora. Esto indica que el uso de Ledoit-Wolf aporta una estimación más estable de la matriz de covarianzas.

En el caso de ledoit_wolf_markowitz, el comportamiento es muy parecido al de markowitz. La rentabilidad aumenta ligeramente, pero la volatilidad y el drawdown siguen siendo elevados. Esto sugiere que la inestabilidad de Markowitz no depende solo de la matriz de covarianzas, sino también de la estimación de los retornos esperados.

También se observa que equal_weight obtiene el mejor Sharpe ratio, lo que refuerza la necesidad de comparar los modelos generativos con baselines clásicos sólidos y no únicamente con estrategias débiles.