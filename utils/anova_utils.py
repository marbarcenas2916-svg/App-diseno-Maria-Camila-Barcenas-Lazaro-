"""Funciones estadísticas para el análisis de un diseño completamente al azar."""

import json
import warnings
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from scipy.stats import studentized_range
from statsmodels.formula.api import ols
from statsmodels.regression.linear_model import RegressionResultsWrapper
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd


def cargar_datos(archivo: str | Path | BinaryIO) -> pd.DataFrame:
    """Carga datos desde un archivo CSV o un libro de Excel.

    Args:
        archivo: Ruta o archivo abierto con nombre terminado en `.csv` o `.xlsx`.

    Returns:
        Datos leídos en un DataFrame.

    Raises:
        ValueError: Si el archivo no tiene una extensión admitida.
    """
    # Se obtiene la extensión desde el nombre para admitir rutas y archivos cargados.
    nombre_archivo = getattr(archivo, "name", archivo)
    extension = Path(str(nombre_archivo)).suffix.lower()

    # No aplica una fórmula estadística: se detecta el formato de almacenamiento.
    if extension == ".csv":
        # El motor de Python detecta si las columnas están separadas por coma o punto y coma.
        return pd.read_csv(archivo, sep=None, engine="python")
    if extension == ".xlsx":
        # Excel conserva los tipos de celda, por lo que pandas puede leerlo directamente.
        return pd.read_excel(archivo)

    raise ValueError("El archivo debe ser CSV o Excel con extensión .xlsx.")


def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Revisa que los datos cumplan las condiciones básicas de un DCA.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta cuantitativa.

    Returns:
        Lista de errores en español; queda vacía si los datos son válidos.
    """
    errores: list[str] = []

    # Se comprueba primero la estructura para evitar accesos a columnas inexistentes.
    columnas_faltantes = [
        columna for columna in (col_trat, col_resp) if columna not in df.columns
    ]
    if columnas_faltantes:
        return [f"Faltan las columnas requeridas: {', '.join(columnas_faltantes)}."]

    # Los espacios vacíos también representan mediciones o tratamientos faltantes.
    datos_requeridos = df[[col_trat, col_resp]].replace(r"^\s*$", pd.NA, regex=True)
    if datos_requeridos.isna().any().any():
        errores.append("Hay datos faltantes en las columnas de tratamiento o respuesta.")

    # La respuesta debe ser cuantitativa para que tenga sentido calcular medias y ANOVA.
    if not is_numeric_dtype(df[col_resp]):
        errores.append(f"La columna de respuesta '{col_resp}' no es numérica.")

    # Se cuentan los niveles para verificar que exista una comparación entre tratamientos.
    numero_tratamientos = df[col_trat].nunique(dropna=True)
    if numero_tratamientos < 2:
        errores.append("El DCA debe tener al menos 2 tratamientos.")

    # Para cada tratamiento j se exige n_j >= 2 réplicas independientes.
    replicas_por_tratamiento = df[col_trat].value_counts(dropna=True)
    if (replicas_por_tratamiento < 2).any():
        errores.append("Cada tratamiento debe tener al menos 2 réplicas.")

    return errores


def ajustar_dca(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> RegressionResultsWrapper:
    """Ajusta el modelo lineal de un diseño completamente al azar.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta cuantitativa.

    Returns:
        Modelo lineal ajustado por mínimos cuadrados ordinarios.

    Raises:
        ValueError: Si los datos no cumplen las condiciones básicas de un DCA.
    """
    # Se detiene el ajuste si la estructura, la respuesta o las réplicas no son válidas.
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede ajustar el DCA: " + " ".join(errores))

    # El modelo usa Y_ij = μ + τ_i + ε_ij para separar el efecto del tratamiento del error.
    # Q() protege nombres de columna con espacios, tildes, signos u otros caracteres.
    formula = (
        f"Q({json.dumps(col_resp)}) ~ "
        f"C(Q({json.dumps(col_trat)}))"
    )
    modelo = ols(formula, data=df).fit()
    return modelo


def tabla_anova(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Construye la tabla ANOVA tipo II y agrega la suma de cuadrados total.

    Args:
        modelo: Modelo lineal ajustado para el DCA.

    Returns:
        Tabla con las fuentes, grados de libertad, cuadrados medios y prueba F.
    """
    # ANOVA tipo II compara el efecto de tratamientos considerando el modelo ajustado.
    tabla_base = anova_lm(modelo, typ=2)

    # Se expresan las fuentes con términos comprensibles para el análisis del ensayo.
    fuentes = [
        "Error" if str(fuente) == "Residual" else "Tratamientos"
        for fuente in tabla_base.index
    ]
    tabla = pd.DataFrame(
        {
            "Fuente": fuentes,
            "gl": tabla_base["df"].to_numpy(dtype=float),
            "SC": tabla_base["sum_sq"].to_numpy(dtype=float),
            "F": tabla_base["F"].to_numpy(dtype=float),
            "p-valor": tabla_base["PR(>F)"].to_numpy(dtype=float),
        }
    )

    # Cada cuadrado medio es CM = SC / gl; la prueba usa F = CM_Tratamientos / CM_Error.
    tabla["CM"] = tabla["SC"] / tabla["gl"]
    tabla = tabla[["Fuente", "gl", "SC", "CM", "F", "p-valor"]]

    # La variación total suma tratamientos y error: SC_Total = SC_Tratamientos + SC_Error.
    # Los grados de libertad totales también se suman: gl_Total = gl_Tratamientos + gl_Error.
    grados_libertad_total = float(tabla["gl"].sum())
    suma_cuadrados_total = float(tabla["SC"].sum())
    fila_total = pd.DataFrame(
        [
            {
                "Fuente": "Total",
                "gl": grados_libertad_total,
                "SC": suma_cuadrados_total,
                "CM": suma_cuadrados_total / grados_libertad_total,
                "F": np.nan,
                "p-valor": np.nan,
            }
        ]
    )
    return pd.concat([tabla, fila_total], ignore_index=True)


def resumen_tratamientos(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> pd.DataFrame:
    """Resume el número de réplicas y la respuesta por tratamiento.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta cuantitativa.

    Returns:
        Tabla por tratamiento con n, total, media y desviación estándar.

    Raises:
        ValueError: Si los datos no cumplen las condiciones básicas de un DCA.
    """
    # Se evitan resúmenes engañosos si faltan mediciones o réplicas por tratamiento.
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede resumir el DCA: " + " ".join(errores))

    # Para el tratamiento i se calculan n_i, total_i = ΣY_ij y media_i = total_i / n_i.
    # La desviación estándar muestral es s_i = sqrt(Σ(Y_ij - media_i)^2 / (n_i - 1)).
    resumen = df.groupby(col_trat)[col_resp].agg(
        n="count",
        total="sum",
        media="mean",
        **{"desviación estándar": "std"},
    )
    return resumen.reset_index()


def coeficiente_variacion(
    modelo: RegressionResultsWrapper, df: pd.DataFrame, col_resp: str
) -> float:
    """Calcula el coeficiente de variación del experimento.

    Args:
        modelo: Modelo lineal ajustado para el DCA.
        df: Datos del experimento.
        col_resp: Nombre de la columna con la respuesta cuantitativa.

    Returns:
        Coeficiente de variación expresado como porcentaje.

    Raises:
        ValueError: Si la media general es cero o la columna no existe.
    """
    # Se usa la media general de las observaciones para expresar el error en escala relativa.
    if col_resp not in df.columns:
        raise ValueError(f"No se encontró la columna de respuesta '{col_resp}'.")
    media_general = float(df[col_resp].mean())
    if media_general == 0:
        raise ValueError("El CV no está definido cuando la media general es cero.")

    # El cuadrado medio del error estima la varianza residual: CME = SSE / gl_error.
    cuadrado_medio_error = float(modelo.mse_resid)

    # Se calcula CV = sqrt(CME) / media_general * 100 para comparar la precisión del ensayo.
    return float(np.sqrt(cuadrado_medio_error) / media_general * 100)


def tukey(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[pd.DataFrame, float]:
    """Compara medias con Tukey y calcula una diferencia mínima significativa.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta cuantitativa.
        alfa: Probabilidad de error tipo I, entre 0 y 1.

    Returns:
        Una tabla de comparaciones de Tukey y la DMS calculada para el diseño.

    Raises:
        ValueError: Si alfa o los datos no son válidos para la comparación.
    """
    # Se valida el nivel de significancia antes de solicitar cuantiles de la distribución.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1, sin incluir esos extremos.")

    # Tukey requiere al menos dos tratamientos y dos réplicas con respuesta numérica por grupo.
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede aplicar Tukey: " + " ".join(errores))

    # Tukey contrasta todas las diferencias |media_i - media_j| controlando el error familiar.
    resultado = pairwise_tukeyhsd(
        endog=df[col_resp], groups=df[col_trat], alpha=alfa
    )
    tabla_bruta = pd.DataFrame(
        resultado.summary().data[1:], columns=resultado.summary().data[0]
    )
    tabla_tukey = tabla_bruta.rename(
        columns={
            "group1": "Tratamiento 1",
            "group2": "Tratamiento 2",
            "meandiff": "Diferencia de medias",
            "p-adj": "p-valor ajustado",
            "lower": "Límite inferior",
            "upper": "Límite superior",
            "reject": "Diferencia significativa",
        }
    )

    # Se ajusta el DCA para obtener glE y CME del mismo modelo usado en las comparaciones.
    modelo = ajustar_dca(df, col_trat, col_resp)

    # Se obtienen t tratamientos y glE grados de libertad residuales para el cuantil q.
    replicas = df.groupby(col_trat).size()
    numero_tratamientos = len(replicas)
    grados_libertad_error = float(modelo.df_resid)
    cuantil_tukey = float(
        studentized_range.ppf(1 - alfa, numero_tratamientos, grados_libertad_error)
    )

    # El diseño balanceado usa r común; el desbalanceado aproxima r con la media armónica.
    balanceado = replicas.nunique() == 1
    if balanceado:
        replicas_equivalentes = float(replicas.iloc[0])
    else:
        replicas_equivalentes = float(len(replicas) / (1 / replicas).sum())
        warnings.warn(
            "La DMS es aproximada porque el diseño no está balanceado.",
            UserWarning,
            stacklevel=2,
        )

    # CME = SSE / glE y DMS = q(alfa; t; glE) * sqrt(CME / r).
    cuadrado_medio_error = float(modelo.mse_resid)
    dms = cuantil_tukey * float(np.sqrt(cuadrado_medio_error / replicas_equivalentes))

    return tabla_tukey, dms


def interpretar_dca(tabla: pd.DataFrame, alfa: float = 0.05) -> str:
    """Interpreta la prueba F de tratamientos en lenguaje sencillo.

    Args:
        tabla: Tabla ANOVA con las columnas `Fuente` y `p-valor`.
        alfa: Probabilidad de error tipo I, entre 0 y 1.

    Returns:
        Conclusión sobre H0 y su significado para comparar tratamientos.

    Raises:
        ValueError: Si alfa o la tabla no contienen la prueba de tratamientos.
    """
    # Se comprueba el nivel de decisión antes de comparar el p-valor.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1, sin incluir esos extremos.")
    if not {"Fuente", "p-valor"}.issubset(tabla.columns):
        raise ValueError("La tabla debe incluir las columnas 'Fuente' y 'p-valor'.")

    # H0 establece μ1 = μ2 = ... = μt; se busca la fila que contrasta esa igualdad.
    fila_tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos", "p-valor"]
    if len(fila_tratamientos) != 1 or pd.isna(fila_tratamientos.iloc[0]):
        raise ValueError("La tabla no contiene un p-valor válido para Tratamientos.")
    p_valor = float(fila_tratamientos.iloc[0])

    # La regla de decisión es rechazar H0 si p-valor <= alfa.
    if p_valor <= alfa:
        return (
            "Se rechaza H0: hay evidencia de que al menos dos medias de tratamiento "
            "son diferentes. Para decidir entre tratamientos, revise las comparaciones "
            "de Tukey y los supuestos del modelo."
        )
    return (
        "No se rechaza H0: no hay evidencia suficiente de diferencias entre las medias "
        "de los tratamientos. Esto no demuestra que sean iguales; considere la precisión "
        "del ensayo y los supuestos del modelo antes de decidir."
    )