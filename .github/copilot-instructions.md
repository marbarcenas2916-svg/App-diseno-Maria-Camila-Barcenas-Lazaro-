# Instrucciones para GitHub Copilot

## Contexto del proyecto

- Este repositorio contiene una aplicación de Diseño Experimental desarrollada en Python y Streamlit para el curso de Diseño Experimental del programa de Ingeniería Agrícola de la Universidad de Sucre.
- La estructura prevista es:
  - `app.py`: portada de la aplicación.
  - `pages/`: una página por cada diseño experimental.
  - `utils/`: funciones reutilizables; debe incluir `__init__.py`.
  - `data/`: archivos CSV de ejemplo.
  - `verificacion/`: scripts en R para verificar los análisis.

## Idioma y documentación

- Escribe todo el código, comentarios, docstrings y mensajes de la interfaz en español.
- Añade un comentario en cada paso estadístico que explique qué se calcula y por qué, con una explicación comprensible para estudiantes de Ingeniería Agrícola.
- Declara las funciones con anotaciones de tipos (`type hints`) y docstrings en estilo Google, redactados en español.

## Dependencias

- Usa únicamente estas librerías: `streamlit`, `pandas`, `numpy`, `scipy`, `statsmodels`, `plotly` y `openpyxl`.
- No agregues otras dependencias sin pedir permiso.

## Análisis estadístico

- Ajusta los modelos ANOVA con `statsmodels.formula.api.ols` y calcula la tabla con `statsmodels.stats.anova.anova_lm`, usando `typ=2`.
- Realiza las comparaciones de Tukey con `statsmodels.stats.multicomp.pairwise_tukeyhsd`.
- No inventes ni codifiques resultados estadísticos de ejemplo como si fueran resultados reales: todos los números presentados deben provenir del cálculo correspondiente.

## Verificación

- Antes de terminar una tarea, ejecuta el código afectado y corrige los errores que aparezcan.
- Si no hay código ejecutable afectado por la tarea, indica esta limitación en el resumen en lugar de afirmar que se ejecutó.