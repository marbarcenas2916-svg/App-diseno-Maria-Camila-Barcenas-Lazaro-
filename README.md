# Aplicación de Diseño Experimental

Aplicación educativa desarrollada en Python y Streamlit para apoyar el curso de Diseño Experimental del programa de Ingeniería Agrícola de la Universidad de Sucre. Permite organizar datos de ensayos agrícolas, revisar análisis estadísticos y estudiar la interpretación de distintos diseños experimentales.

## Módulos

| Módulo | Diseño | Estado |
| --- | --- | --- |
| DCA | Diseño completamente al azar | Disponible |
| DBCA | Diseño de bloques completos al azar | En construcción |
| DCL | Diseño de cuadrado latino | En construcción |
| DPD | Diseño de parcelas divididas | En construcción |
| Factoriales | Diseños factoriales | En construcción |
| RSM | Metodología de superficie de respuesta | En construcción |

El módulo DCA incluye carga de datos CSV o Excel, ANOVA, comparaciones de Tukey, gráficos y diagnóstico de supuestos. `data/dca_secadores.csv` es el conjunto de datos de ejemplo.

## Estructura del proyecto

```text
.
├── .github/
│   └── copilot-instructions.md
├── app.py
├── data/
│   └── dca_secadores.csv
├── pages/
│   ├── 01_DCA.py
│   ├── 02_DBCA.py
│   ├── 03_DCL.py
│   ├── 04_DPD.py
│   ├── 05_Factoriales.py
│   └── 06_RSM.py
├── utils/
│   ├── __init__.py
│   ├── anova_utils.py
│   └── diagnostico_utils.py
├── verificacion/
│   └── verificacion_dca.R
└── requirements.txt
```

- `app.py`: portada y presentación de los módulos.
- `pages/`: páginas de Streamlit para cada diseño experimental.
- `utils/`: funciones reutilizables para análisis y diagnóstico.
- `data/`: conjuntos de datos de ejemplo.
- `verificacion/`: scripts en R para contrastar resultados.

## Instalación y ejecución local

En Windows, desde PowerShell y la carpeta del proyecto:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

En macOS o Linux, ejecuta desde la raíz del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Codespaces

Abre el repositorio en Codespaces y ejecuta desde la raíz:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará la dirección de la aplicación en el terminal; en Codespaces puedes abrir el puerto que indique el entorno.

## Verificación en R

El script `verificacion/verificacion_dca.R` lee `../data/dca_mi_variante.csv`. Ese archivo debe estar disponible en `data/`. Para que la ruta relativa sea válida, ejecuta el script desde la carpeta `verificacion/`:

```bash
cd verificacion
Rscript verificacion_dca.R
```

## Autor

Maria Camila Barcenas Lazaro, estudiante del curso de Diseño Experimental, Ingeniería Agrícola, Universidad de Sucre. Semestre 2026-2.

## Uso de inteligencia artificial

Se utilizó GitHub Copilot como apoyo para estructurar y documentar código y para preparar esta documentación. Los resultados estadísticos de la aplicación se calculan a partir de los datos ingresados; no se presentan resultados inventados como si fueran análisis reales. El estudiante debe revisar los supuestos, interpretar los resultados y contrastarlos con sus cálculos.
