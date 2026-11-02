AUTOR = "Maria Camila Barcenas Lazaro"

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="App de Diseño Experimental",
    page_icon="🌱",
    layout="wide",
)

st.title("App de Diseño Experimental")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")
st.write(
    "El diseño experimental permite planear ensayos de campo para comparar "
    "tratamientos de manera ordenada, reducir el efecto de la variabilidad "
    "natural y obtener evidencia útil para tomar decisiones agrícolas."
)

modulos = pd.DataFrame(
    [
        {
            "Módulo": "DCA – Diseño completamente al azar",
            "Cuándo se usa": "Cuando las unidades experimentales son homogéneas.",
            "Ejemplo agrícola": "Comparar fertilizantes en parcelas uniformes de maíz.",
            "Estado": "Disponible",
        },
        {
            "Módulo": "DBCA – Diseño de bloques completos al azar",
            "Cuándo se usa": "Cuando se puede agrupar la variación en bloques.",
            "Ejemplo agrícola": "Comparar variedades de yuca en bloques según pendiente.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DCL – Diseño de cuadrado latino",
            "Cuándo se usa": "Cuando se deben controlar dos fuentes de variación.",
            "Ejemplo agrícola": "Evaluar tratamientos con gradientes de suelo y humedad.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DPD – Diseño de parcelas divididas",
            "Cuándo se usa": "Cuando un factor requiere parcelas principales y otro subparcelas.",
            "Ejemplo agrícola": "Probar riego en parcelas y variedades en subparcelas.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "Diseños factoriales",
            "Cuándo se usa": "Cuando se estudian varios factores y sus interacciones.",
            "Ejemplo agrícola": "Evaluar dosis de nitrógeno y densidades de siembra.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "RSM – Metodología de superficie de respuesta",
            "Cuándo se usa": "Cuando se busca modelar y optimizar una respuesta cuantitativa.",
            "Ejemplo agrícola": "Optimizar temperatura y tiempo de secado de granos.",
            "Estado": "En construcción",
        },
    ]
)

st.subheader("Módulos")
st.dataframe(modulos, hide_index=True, width="stretch")

st.subheader("Cómo usar la aplicación")
st.markdown(
    "1. Elige un módulo en el menú lateral.\n"
    "2. Carga o prepara los datos del ensayo.\n"
    "3. Revisa los resultados y su interpretación.\n"
    "4. Verifica los cálculos a mano y contrasta tus conclusiones."
)

st.warning(
    "Esta app apoya el aprendizaje. El estudiante interpreta los resultados, "
    "verifica supuestos y compara con su cálculo manual."
)

st.sidebar.header("Información del curso")
st.sidebar.write(f"**Autor:** {AUTOR}")
st.sidebar.write("**Curso:** Diseño Experimental")
st.sidebar.write("**Semestre:** 2026-2")