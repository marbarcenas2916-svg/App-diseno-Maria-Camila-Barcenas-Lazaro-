from io import BytesIO
from pathlib import Path
import warnings

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import f as distribucion_f

from utils.anova_utils import (
	ajustar_dca,
	cargar_datos,
	coeficiente_variacion,
	interpretar_dca,
	resumen_tratamientos,
	tabla_anova,
	tukey,
	validar_dca,
)
from utils.diagnostico_utils import (
	grafico_qq,
	grafico_residuos_vs_ajustados,
	prueba_levene,
	prueba_shapiro,
	residuos_y_ajustados,
)


RUTA_EJEMPLO = Path(__file__).resolve().parents[1] / "data" / "dca_secadores.csv"


@st.cache_data(show_spinner="Cargando datos del ensayo...")
def cargar_datos_en_cache(
	nombre_archivo: str | None, contenido: bytes | None
) -> pd.DataFrame:
	"""Carga el archivo seleccionado o los datos de ejemplo y guarda el resultado en caché.

	Args:
		nombre_archivo: Nombre del archivo cargado o None para usar el ejemplo.
		contenido: Contenido binario del archivo cargado o None para usar el ejemplo.

	Returns:
		Datos del ensayo en un DataFrame.

	Raises:
		ValueError: Si solo se recibe el nombre o el contenido del archivo.
	"""
	# Si no se selecciona archivo, se conserva un ejemplo reproducible para explorar el módulo.
	if nombre_archivo is None and contenido is None:
		return cargar_datos(RUTA_EJEMPLO)
	if nombre_archivo is None or contenido is None:
		raise ValueError("No se pudo leer el archivo seleccionado.")

	# BytesIO permite entregar el archivo en memoria a la función común de carga.
	archivo = BytesIO(contenido)
	archivo.name = nombre_archivo
	return cargar_datos(archivo)


st.title("Diseño completamente al azar (DCA)")
st.write(
	"El DCA compara tratamientos asignados al azar cuando las unidades experimentales "
	"son homogéneas. En este ejemplo se compara la humedad final de yuca obtenida con "
	"cuatro secadores solares, con cuatro réplicas por secador."
)

archivo_cargado = st.file_uploader(
	"Cargar datos del ensayo", type=["csv", "xlsx"]
)
if archivo_cargado is None:
	st.caption(
		"No se cargó un archivo; se utilizan los datos de ejemplo "
		"data/dca_secadores.csv."
	)

try:
	if archivo_cargado is None:
		datos = cargar_datos_en_cache(None, None)
	else:
		datos = cargar_datos_en_cache(
			archivo_cargado.name, archivo_cargado.getvalue()
		)
except Exception as error:
	st.error(f"No fue posible cargar los datos: {error}")
	st.stop()

# Los nombres de columnas se convierten en texto para que los selectores y Q() usen la misma etiqueta.
datos.columns = datos.columns.map(str)
columnas = datos.columns.tolist()
if len(columnas) < 2:
	st.error("El archivo debe tener al menos una columna de tratamiento y una de respuesta.")
	st.stop()

indice_tratamiento = columnas.index("secador") if "secador" in columnas else 0
columna_tratamiento = st.selectbox(
	"Columna de tratamiento",
	columnas,
	index=indice_tratamiento,
)

columnas_respuesta = [
	columna for columna in columnas if columna != columna_tratamiento
]
if not columnas_respuesta:
	st.error("Selecciona columnas distintas para tratamiento y respuesta.")
	st.stop()
indice_respuesta = (
	columnas_respuesta.index("humedad")
	if "humedad" in columnas_respuesta
	else 0
)
columna_respuesta = st.selectbox(
	"Columna de respuesta",
	columnas_respuesta,
	index=indice_respuesta,
)

alfa = st.slider(
	"Nivel de significancia (alfa)",
	min_value=0.01,
	max_value=0.10,
	value=0.05,
	step=0.01,
)

# Se validan columnas, tipo de respuesta, datos faltantes y réplicas antes de hacer inferencia.
errores_validacion = validar_dca(datos, columna_tratamiento, columna_respuesta)
if errores_validacion:
	for error in errores_validacion:
		st.error(error)
	st.stop()

# El ajuste y los resúmenes se delegan a las funciones comunes del módulo de análisis.
modelo = ajustar_dca(datos, columna_tratamiento, columna_respuesta)
tabla = tabla_anova(modelo)
resumen = resumen_tratamientos(datos, columna_tratamiento, columna_respuesta)
cv = coeficiente_variacion(modelo, datos, columna_respuesta)

fila_tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos"].iloc[0]
fila_error = tabla.loc[tabla["Fuente"] == "Error"].iloc[0]
p_valor = float(fila_tratamientos["p-valor"])
f_observada = float(fila_tratamientos["F"])
gl_tratamientos = float(fila_tratamientos["gl"])
gl_error = float(fila_error["gl"])

# F crítica delimita la región de rechazo: F crítica = F(1 - alfa; gl tratamientos; gl error).
f_critica = float(
	distribucion_f.ppf(1 - alfa, gl_tratamientos, gl_error)
)

# Los residuos e_ij = Y_ij - Y_estimado_ij permiten revisar el comportamiento del error.
datos_residuos = residuos_y_ajustados(modelo)

# Shapiro-Wilk evalúa normalidad y Levene con mediana evalúa igualdad de varianzas.
shapiro_estadistico, shapiro_p, shapiro_conclusion = prueba_shapiro(
	datos_residuos["Residuos"], alfa
)
levene_estadistico, levene_p, levene_conclusion = prueba_levene(
	datos, columna_tratamiento, columna_respuesta, alfa
)
tabla_supuestos = pd.DataFrame(
	[
		{
			"Prueba": "Shapiro-Wilk",
			"Estadístico": shapiro_estadistico,
			"p-valor": shapiro_p,
			"Conclusión": shapiro_conclusion,
		},
		{
			"Prueba": "Levene (centro: mediana)",
			"Estadístico": levene_estadistico,
			"p-valor": levene_p,
			"Conclusión": levene_conclusion,
		},
	]
)

pestanas = st.tabs(["Datos", "ANOVA", "Comparaciones", "Gráficos", "Supuestos"])

with pestanas[0]:
	st.subheader("Datos del ensayo")
	st.dataframe(datos, hide_index=True, width="stretch")
	st.subheader("Resumen por tratamiento")
	st.dataframe(resumen, hide_index=True, width="stretch")

with pestanas[1]:
	st.subheader("Tabla ANOVA")
	tabla_formateada = tabla.style.format(
		{
			"gl": "{:.0f}",
			"SC": "{:.4f}",
			"CM": "{:.4f}",
			"F": "{:.4f}",
			"p-valor": lambda valor: (
				""
				if pd.isna(valor)
				else "<0.0001"
				if 0 < valor < 0.0001
				else f"{valor:.4f}"
			),
		}
	)
	st.dataframe(tabla_formateada, hide_index=True, width="stretch")

	columnas_metricas = st.columns(3)
	columnas_metricas[0].metric("F observada", f"{f_observada:.4f}")
	columnas_metricas[1].metric("F crítica", f"{f_critica:.4f}")
	columnas_metricas[2].metric("Coeficiente de variación", f"{cv:.4f} %")

	interpretacion = interpretar_dca(tabla, alfa)
	if p_valor <= alfa:
		st.success(interpretacion)
	else:
		st.info(interpretacion)

with pestanas[2]:
	st.subheader("Comparaciones múltiples de Tukey")
	if p_valor < alfa:
		# La DMS usa el CME del modelo y el número de réplicas; avisamos si es aproximada.
		with warnings.catch_warnings(record=True) as avisos:
			warnings.simplefilter("always")
			comparaciones, dms = tukey(
				datos, columna_tratamiento, columna_respuesta, alfa
			)
		for aviso in avisos:
			st.warning(str(aviso.message))

		st.dataframe(
			comparaciones.style.format(
				{
					"Diferencia de medias": "{:.4f}",
					"p-valor ajustado": "{:.4f}",
					"Límite inferior": "{:.4f}",
					"Límite superior": "{:.4f}",
				}
			),
			hide_index=True,
			width="stretch",
		)
		st.metric("Diferencia mínima significativa (DMS)", f"{dms:.4f}")
	else:
		st.info(
			f"No se realiza Tukey porque el ANOVA no detectó diferencias "
			f"significativas entre tratamientos (p = {p_valor:.4f} ≥ alfa = {alfa:.2f})."
		)

with pestanas[3]:
	st.subheader("Respuesta por tratamiento")
	figura_cajas = px.box(
		datos,
		x=columna_tratamiento,
		y=columna_respuesta,
		color=columna_tratamiento,
		points="all",
		labels={
			columna_tratamiento: "Tratamiento",
			columna_respuesta: "Respuesta",
		},
	)
	figura_cajas.update_layout(showlegend=False)
	st.plotly_chart(figura_cajas, width="stretch")

	st.subheader("Media por tratamiento")
	figura_medias = px.bar(
		resumen,
		x=columna_tratamiento,
		y="media",
		color=columna_tratamiento,
		error_y="desviación estándar",
		text_auto=".4f",
		labels={
			columna_tratamiento: "Tratamiento",
			"media": "Media de la respuesta",
			"desviación estándar": "Desviación estándar",
		},
	)
	figura_medias.update_layout(showlegend=False)
	st.plotly_chart(figura_medias, width="stretch")

with pestanas[4]:
	st.subheader("Residuos frente a valores ajustados")
	st.plotly_chart(
		grafico_residuos_vs_ajustados(modelo),
		width="stretch",
	)
	st.subheader("Normalidad de los residuos")
	st.plotly_chart(
		grafico_qq(datos_residuos["Residuos"]),
		width="stretch",
	)

	st.subheader("Pruebas de supuestos")
	st.dataframe(
		tabla_supuestos.style.format(
			{
				"Estadístico": "{:.4f}",
				"p-valor": "{:.4f}",
			}
		),
		hide_index=True,
		width="stretch",
	)

	st.markdown(
		"**Normalidad:** Shapiro-Wilk comprueba si los residuos son compatibles "
		"con una distribución normal.\n\n"
		"**Homogeneidad de varianzas:** Levene, centrada en la mediana, revisa si "
		"la variabilidad de la respuesta es similar entre tratamientos.\n\n"
		"**Independencia:** no se determina con Shapiro-Wilk ni con Levene. En un DCA "
		"se sustenta en la asignación aleatoria de los tratamientos; también debe "
		"revisarse que la toma de datos no haya introducido dependencia entre réplicas."
	)