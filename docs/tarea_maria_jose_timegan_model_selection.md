# Tarea tecnica - Maria Jose: seleccion robusta de semillas TimeGAN

## Objetivo

Hacer que la evaluacion multi-semilla de TimeGAN sea mas rigurosa y defendible, evitando seleccionar resultados por rendimiento en test. La seleccion debe basarse exclusivamente en metricas de validacion distribucional, temporal e informacional.

## Contexto

Actualmente `src/tfm_pipeline/run_timegan_multiseed.py` ejecuta TimeGAN con varias semillas y genera:

- `results/timegan_multiseed/diagnostic_summary_by_seed.csv`
- `results/timegan_multiseed/validation_diagnostic_summary_by_seed.csv`
- `results/timegan_multiseed/portfolio_metrics_by_seed.csv`
- `results/timegan_multiseed/training_history_by_seed.csv`
- `results/timegan_multiseed/diagnostic_summary.csv`
- `results/timegan_multiseed/validation_diagnostic_summary.csv`
- `results/timegan_multiseed/portfolio_metrics.csv`

El siguiente paso es crear un ranking de semillas/modelos usando solo diagnosticos de validacion. Esto permite afirmar en la memoria que la seleccion de modelo no se hace mirando el rendimiento financiero de test.

## Archivos principales

- `src/tfm_pipeline/run_timegan_multiseed.py`
- `src/tfm_pipeline/synthetic_evaluation.py`
- Nuevo opcional: `src/tfm_pipeline/model_selection.py`
- Nuevo opcional: `tests/unit/test_model_selection.py`
- Opcional: `docs/flujo_codigo.md`
- Opcional: `docs/metricas_experimento.md`

## Tareas

### 1. Crear una funcion de scoring de validacion

Crear un modulo nuevo si ayuda a mantener limpio el runner:

```text
src/tfm_pipeline/model_selection.py
```

Funciones sugeridas:

```python
def score_validation_diagnostics(
    diagnostics: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    ...

def select_best_seed(scored_diagnostics: pd.DataFrame) -> dict[str, object]:
    ...
```

La entrada principal sera `validation_diagnostic_summary_by_seed.csv` o el `DataFrame` equivalente generado en memoria.

### 2. Definir metricas para el score

Usar solo columnas de validacion. Pesos iniciales sugeridos:

| Metrica | Peso | Motivo |
|---|---:|---|
| `mean_jensen_shannon` | 1.0 | similitud distribucional estable |
| `mean_wasserstein` | 1.0 | distancia global entre distribuciones |
| `correlation_matrix_error` | 1.5 | dependencia multiactivo relevante para carteras |
| `autocorrelation_error` | 1.0 | estructura temporal de retornos |
| `absolute_autocorrelation_error` | 1.0 | clustering de volatilidad |
| `mean_abs_kurtosis_error` | 1.0 | preservacion de colas |

Si alguna columna no existe, la funcion debe fallar con un mensaje claro o ignorarla solo si esta documentado. Preferencia: fallar claramente para no ocultar errores.

### 3. Normalizar metricas antes de combinarlas

Como las metricas tienen escalas distintas, normalizar cada columna antes de sumar.

Metodo recomendado:

```text
normalized_metric = metric / median(metric)
```

Alternativa aceptable:

```text
min-max scaling
```

Requisitos:

- Valores mas bajos deben significar mejor resultado.
- El score final mas bajo debe ganar.
- Manejar valores cero o constantes sin dividir por cero.
- Mantener columnas originales y anadir columnas normalizadas o un `validation_score` final.

### 4. Integrar ranking en `run_timegan_multiseed.py`

Despues de crear `validation_diagnostics`, generar:

```text
results/timegan_multiseed/seed_ranking.csv
results/timegan_multiseed/best_seed.json
results/timegan_multiseed/best_seed_portfolio_metrics.csv
```

`seed_ranking.csv` debe contener al menos:

- `rank`
- `seed`
- `variant`
- metricas originales usadas en el score
- `validation_score`

`best_seed.json` debe contener:

- `seed`
- `variant`
- `validation_score`
- `selection_basis`: texto indicando que se uso validacion, no test
- `metrics_used`

`best_seed_portfolio_metrics.csv` debe filtrar `portfolio_metrics_by_seed.csv` para la semilla y variante seleccionadas, pero sin usar estas metricas para seleccionar.

### 5. Evitar leakage de test

Regla critica:

- No usar `portfolio_metrics_by_seed.csv` para decidir el mejor seed.
- No usar `sharpe_ratio`, `annualized_return`, `max_drawdown`, `value_at_risk` o `conditional_value_at_risk` para ranking.
- Esas metricas solo se consultan despues para reportar el rendimiento final del seed seleccionado.

## Tests obligatorios

Crear tests con datos ficticios.

Casos minimos:

- El ranking ordena correctamente por menor `validation_score`.
- La funcion no usa columnas financieras de test aunque existan.
- Si una metrica requerida falta, se lanza `ValueError` claro.
- El score funciona si una metrica tiene valores constantes.
- `best_seed` devuelve semilla y variante correctas.

Comando de verificacion:

```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_model_selection.py tests/unit/test_evaluation.py
```

Si es posible, ejecutar toda la suite:

```bash
PYTHONPATH=src python3 -m pytest tests/unit
```

## Criterios de aceptacion

- `python -m tfm_pipeline.run_timegan_multiseed` genera ranking y best seed.
- La seleccion usa solo diagnosticos de validacion.
- Los tests pasan.
- El formato de outputs existentes no se rompe.
- La funcion de scoring es reutilizable y testeable fuera del runner.
- La metodologia queda defendible: validacion para seleccionar, test para evaluar.

## Riesgos y decisiones

- El seed con mejor validacion puede no tener mejor Sharpe en test. Esto es correcto y debe mantenerse.
- Si diferentes variantes tienen escalas de metricas muy distintas, revisar si conviene rankear por `variant` o ranking conjunto. Recomendacion inicial: ranking conjunto con `seed` y `variant`.
- Si el score parece arbitrario, documentar claramente pesos y justificacion.

## Entregable final

Una rama o commit con:

- modulo de seleccion o funciones equivalentes
- integracion en `run_timegan_multiseed.py`
- outputs `seed_ranking.csv`, `best_seed.json`, `best_seed_portfolio_metrics.csv`
- tests unitarios
- nota breve en docs si se anaden nuevos outputs

Mensaje de commit sugerido:

```text
Add validation-based TimeGAN seed selection

- Score TimeGAN seeds using validation diagnostics only.
- Generate seed ranking and best-seed metadata outputs.
- Export test portfolio metrics for the selected seed without using them for selection.
- Add unit tests for ranking and leakage prevention.
```
