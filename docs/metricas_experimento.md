# Protocolo de métricas del experimento

Este documento fija el protocolo operativo de evaluación para que las métricas usadas en el código puedan trasladarse después de forma coherente al documento LaTeX.

## Configuración experimental

| Elemento | Decisión |
|---|---|
| Activos | AAPL, MSFT, GOOGL, AMZN, META, NVDA, JPM, XOM, JNJ, PG |
| Fuente | Yahoo Finance mediante `yfinance` |
| Frecuencia | Diaria |
| Campo de precio | Precio ajustado de cierre |
| Variable modelada | Retornos logarítmicos diarios |
| Periodo completo | 2015-01-01 a 2026-05-12 |
| Entrenamiento | 2015-01-01 a 2022-12-31 |
| Validación | 2023-01-01 a 2024-06-30 |
| Prueba | 2024-07-01 a 2026-05-12 |
| Ventana inicial | 30 días x 10 activos |
| Restricciones de cartera | Long-only, pesos entre 0 y 1, suma de pesos igual a 1 |

## Modelos y baselines

| Modelo | Papel | Uso en evaluación |
|---|---|---|
| Equiponderada | Baseline simple | Referencia mínima de diversificación |
| Mínima varianza | Baseline clásico de riesgo | Optimización con covarianza histórica |
| Markowitz media-varianza | Baseline clásico | Optimización con media y covarianza histórica |
| VAE | Baseline generativo probabilístico | Escenarios sintéticos no adversariales |
| TimeGAN | Modelo generativo temporal principal | Escenarios sintéticos secuenciales multiactivo |

Los modelos de difusión se mantienen como contexto del estado del arte y posible extensión, pero no forman parte del protocolo mínimo obligatorio.

## Variantes de calibración generativa

| Variante | Propósito |
|---|---|
| Escenarios sin calibrar | Evaluar directamente la salida del modelo generativo |
| Escenarios calibrados a media y volatilidad | Diagnosticar si el error principal del modelo está en la localización y escala de los retornos |

La calibración de media y volatilidad se tratará como una variante diagnóstica, no como sustituto del modelo generativo principal. Sus métricas de media y volatilidad no deben interpretarse como aprendizaje directo del modelo, ya que se imponen mediante post-procesado con estadísticos de entrenamiento.

## Métricas distribucionales

Estas métricas comparan retornos reales y retornos sintéticos por activo y, cuando proceda, de forma agregada.

| Métrica | Qué evalúa | Uso previsto |
|---|---|---|
| Media | Nivel medio de los retornos | Detectar sesgos sistemáticos |
| Volatilidad | Dispersión de los retornos | Comprobar si el riesgo marginal se conserva |
| Asimetría | Forma no simétrica de la distribución | Evaluar sesgos de cola |
| Curtosis | Peso de las colas | Evaluar eventos extremos y colas pesadas |
| Percentiles | Forma empírica de la distribución | Comparar cuantiles centrales y extremos |
| VaR | Pérdida extrema a un nivel de confianza | Métrica opcional de riesgo de cola |
| CVaR | Pérdida esperada condicionada a superar VaR | Métrica opcional de severidad de cola |

## Métricas temporales y de dependencia

Estas métricas evalúan si los escenarios preservan relaciones temporales y multiactivo relevantes para la construcción de carteras.

| Métrica | Qué evalúa | Uso previsto |
|---|---|---|
| Matriz de correlación | Dependencia lineal entre activos | Comparar estructura de diversificación |
| Error de correlación | Distancia entre matrices real y sintética | Resumir pérdida de dependencia multiactivo |
| Autocorrelación de retornos | Dependencia temporal directa | Comprobar persistencia temporal |
| Autocorrelación de retornos absolutos | Agrupación de volatilidad | Evaluar si se preservan patrones de volatilidad |
| Información mutua | Dependencia no lineal entre activos | Métrica opcional si el alcance lo permite |

## Métricas informacionales

Estas métricas comparan distribuciones empíricas reales y sintéticas. Se calcularán sobre histogramas con bins comunes o estimaciones equivalentes, aplicando suavizado cuando sea necesario para evitar probabilidades nulas.

| Métrica | Qué evalúa | Nota de implementación |
|---|---|---|
| Divergencia KL | Pérdida de información al aproximar la distribución real con la sintética | Puede ser inestable con probabilidades cero; requiere suavizado |
| Jensen-Shannon | Distancia simétrica y acotada entre distribuciones | Métrica principal complementaria a KL |
| Entropía | Incertidumbre o dispersión de una distribución | Compara si el modelo reduce o amplifica variabilidad |
| Wasserstein | Distancia geométrica entre distribuciones | Complementa diferencias de forma y desplazamiento |

## Métricas financieras

La evaluación financiera se realizará siempre sobre retornos reales del conjunto de prueba. Los retornos sintéticos se usan para estimar parámetros o distribuciones de optimización, no para medir el rendimiento final.

Como la variable modelada son retornos logarítmicos, la rentabilidad acumulada se calcula como `exp(sum(r_t)) - 1` y la rentabilidad anualizada como `exp(mean(r_t) * 252) - 1`. La volatilidad anualizada se calcula como la desviación típica de retornos logarítmicos multiplicada por `sqrt(252)`.

| Métrica | Qué evalúa | Uso previsto |
|---|---|---|
| Rentabilidad acumulada | Resultado total del periodo de prueba | Comparar comportamiento final |
| Rentabilidad anualizada | Retorno ajustado a frecuencia anual | Comparación homogénea entre carteras |
| Volatilidad anualizada | Riesgo realizado anualizado | Medir riesgo fuera de muestra |
| Ratio de Sharpe | Retorno ajustado por riesgo | Comparar eficiencia riesgo-rentabilidad |
| Máximo drawdown | Mayor caída acumulada | Evaluar riesgo de pérdidas severas |
| Entropía de pesos | Diversificación de asignaciones | Penalizar carteras excesivamente concentradas |
| Concentración de pesos | Suma de pesos al cuadrado o Herfindahl | Medir dependencia de pocos activos |
| Estabilidad de pesos | Cambio de pesos entre rebalanceos o experimentos | Evaluar robustez de asignaciones |
| Turnover | Rotación de cartera | Métrica opcional si hay rebalanceo temporal |

## Criterio de comparación

Un modelo generativo no se considerará mejor únicamente por producir mayor rentabilidad en el periodo de prueba. La comparación se realizará en dos niveles:

1. Fidelidad de escenarios: capacidad para preservar propiedades estadísticas, temporales e informacionales de los retornos reales.
2. Utilidad financiera: comportamiento de las carteras construidas con esos escenarios cuando se evalúan sobre datos reales fuera de muestra.

Esta separación evita confundir la calidad de generación de datos con el resultado financiero puntual de un periodo concreto.

## Validación y robustez

La fidelidad distribucional se revisa tanto frente al conjunto de entrenamiento como frente al conjunto de validación. El conjunto de prueba queda reservado para medir el rendimiento financiero de carteras ya definidas.

Para TimeGAN, además de la ejecución de una semilla individual, se calcula una evaluación multi-semilla. Las tablas agregadas reportan media y desviación típica de las métricas para reducir la dependencia de una inicialización concreta, especialmente cuando se entrena con CUDA.

La selección de la semilla o variante final de TimeGAN se hará con un ranking basado solo en diagnósticos de validación distribucionales, temporales e informacionales. Las métricas financieras de prueba quedan reservadas para la evaluación final del modelo ya seleccionado.
