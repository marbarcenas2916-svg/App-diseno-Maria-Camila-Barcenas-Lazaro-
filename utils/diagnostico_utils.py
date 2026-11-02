"""Pruebas y gráficos para revisar supuestos del diseño completamente al azar."""

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from scipy.stats import levene, probplot, shapiro
from statsmodels.regression.linear_model import RegressionResultsWrapper


def residuos_y_ajustados(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Extrae residuos y valores ajustados del modelo del DCA.

    Args:
        modelo: Modelo lineal ajustado para el diseño completamente al azar.

    Returns:
        DataFrame con las columnas `Valores ajustados` y `Residuos`.
    """
    # Cada residuo mide la diferencia entre lo observado y lo estimado: e_ij = Y_ij - Y_estimado_ij.
    valores_ajustados = np.asarray(modelo.fittedvalues, dtype=float)
    residuos = np.asarray(modelo.resid, dtype=float)

    # Se conservan ambas cantidades por observación para revisar patrones del error.
    return pd.DataFrame(
        {"Valores ajustados": valores_ajustados, "Residuos": residuos}
    )


def prueba_shapiro(
    residuos: pd.Series | np.ndarray | list[float], alfa: float = 0.05
) -> tuple[float, float, str]:
    """Evalúa la normalidad de los residuos con Shapiro-Wilk.

    Args:
        residuos: Residuos del modelo del DCA.
        alfa: Nivel de significancia para la conclusión, entre 0 y 1.

    Returns:
        Estadístico W, p-valor y conclusión en español.

    Raises:
        ValueError: Si alfa no es válido o hay menos de tres residuos utilizables.
    """
    # Se comprueba alfa para aplicar una regla de decisión estadística válida.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1, sin incluir esos extremos.")

    # Se omiten residuos no disponibles; Shapiro-Wilk requiere al menos tres observaciones.
    valores = pd.Series(residuos, dtype=float).dropna().to_numpy()
    if len(valores) < 3:
        raise ValueError("Shapiro-Wilk requiere al menos 3 residuos disponibles.")

    # H0 plantea normalidad de los residuos; se evalúa con el estadístico W de Shapiro-Wilk.
    estadistico, p_valor = shapiro(valores)
    if not np.isfinite(estadistico) or not np.isfinite(p_valor):
        raise ValueError("No fue posible calcular la prueba de Shapiro-Wilk.")

    # Se rechaza H0 cuando p-valor < alfa; un valor mayor no demuestra normalidad.
    if p_valor < alfa:
        conclusion = (
            "Se rechaza la normalidad de los residuos: hay evidencia de que se apartan "
            f"de una distribución normal (p-valor < alfa = {alfa:.2f})."
        )
    else:
        conclusion = (
            "No se rechaza la normalidad de los residuos: no hay evidencia suficiente "
            f"para afirmar que se apartan de una distribución normal (alfa = {alfa:.2f})."
        )

    return float(estadistico), float(p_valor), conclusion


def prueba_levene(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[float, float, str]:
    """Evalúa la igualdad de varianzas entre tratamientos con Levene mediana.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta cuantitativa.
        alfa: Nivel de significancia para la conclusión, entre 0 y 1.

    Returns:
        Estadístico de Levene, p-valor y conclusión en español.

    Raises:
        ValueError: Si faltan columnas, hay datos no numéricos o grupos insuficientes.
    """
    # Se comprueban entradas y alfa antes de comparar la variabilidad entre grupos.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1, sin incluir esos extremos.")
    columnas_faltantes = [
        columna for columna in (col_trat, col_resp) if columna not in df.columns
    ]
    if columnas_faltantes:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(columnas_faltantes)}.")
    if df[[col_trat, col_resp]].isna().any().any():
        raise ValueError("Levene no puede calcularse si hay datos faltantes.")

    # Se separan las respuestas por tratamiento para estimar la dispersión de cada grupo.
    try:
        grupos = [
            grupo.to_numpy(dtype=float)
            for _, grupo in df.groupby(col_trat, sort=False)[col_resp]
        ]
    except (TypeError, ValueError) as error:
        raise ValueError("La respuesta debe ser numérica para aplicar Levene.") from error
    if len(grupos) < 2 or any(len(grupo) < 2 for grupo in grupos):
        raise ValueError("Levene requiere al menos 2 tratamientos con 2 réplicas cada uno.")

    # Levene usa la mediana de cada tratamiento como centro, reduciendo sensibilidad a valores extremos.
    estadistico, p_valor = levene(*grupos, center="median")
    if not np.isfinite(estadistico) or not np.isfinite(p_valor):
        raise ValueError("No fue posible calcular la prueba de Levene.")

    # H0 plantea varianzas iguales; se rechaza cuando p-valor < alfa.
    if p_valor < alfa:
        conclusion = (
            "Se rechaza la igualdad de varianzas: hay evidencia de variabilidad distinta "
            f"entre tratamientos (p-valor < alfa = {alfa:.2f})."
        )
    else:
        conclusion = (
            "No se rechaza la igualdad de varianzas: no hay evidencia suficiente de "
            f"variabilidad distinta entre tratamientos (alfa = {alfa:.2f})."
        )

    return float(estadistico), float(p_valor), conclusion


def grafico_residuos_vs_ajustados(modelo: RegressionResultsWrapper) -> Figure:
    """Crea un gráfico de residuos frente a valores ajustados.

    Args:
        modelo: Modelo lineal ajustado para el diseño completamente al azar.

    Returns:
        Figura Plotly para inspeccionar dispersión y patrones de los residuos.
    """
    # Se grafican e_ij = Y_ij - Y_estimado_ij para buscar forma de embudo o patrones sistemáticos.
    datos_grafico = residuos_y_ajustados(modelo)
    figura = px.scatter(
        datos_grafico,
        x="Valores ajustados",
        y="Residuos",
        labels={
            "Valores ajustados": "Valores ajustados",
            "Residuos": "Residuos",
        },
        title="Residuos frente a valores ajustados",
    )

    # La línea en cero ayuda a identificar si los errores se distribuyen alrededor del valor esperado.
    figura.add_hline(y=0, line_dash="dash", line_color="gray")
    return figura


def grafico_qq(residuos: pd.Series | np.ndarray | list[float]) -> Figure:
    """Crea el gráfico Q-Q de los residuos frente a cuantiles normales teóricos.

    Args:
        residuos: Residuos del modelo del DCA.

    Returns:
        Figura Plotly con puntos observados y línea de referencia normal.

    Raises:
        ValueError: Si hay menos de dos residuos utilizables.
    """
    # Se ordenan los residuos y se obtienen cuantiles de una distribución normal de referencia.
    valores = pd.Series(residuos, dtype=float).dropna().to_numpy()
    if len(valores) < 2:
        raise ValueError("El gráfico Q-Q requiere al menos 2 residuos disponibles.")
    (cuantiles_teoricos, residuos_ordenados), (pendiente, intercepto, _) = probplot(
        valores, dist="norm"
    )
    datos_grafico = pd.DataFrame(
        {
            "Cuantiles normales teóricos": cuantiles_teoricos,
            "Residuos ordenados": residuos_ordenados,
        }
    )

    # La referencia es la recta y = pendiente * x + intercepto del ajuste normal de probplot.
    figura = px.scatter(
        datos_grafico,
        x="Cuantiles normales teóricos",
        y="Residuos ordenados",
        title="Gráfico Q-Q de los residuos",
    )
    figura.add_scatter(
        x=cuantiles_teoricos,
        y=pendiente * np.asarray(cuantiles_teoricos) + intercepto,
        mode="lines",
        name="Referencia normal",
    )
    return figura