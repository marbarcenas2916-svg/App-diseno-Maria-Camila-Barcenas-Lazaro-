# Este script contrasta en R el análisis del diseño completamente al azar.
# Ejecútalo desde la carpeta verificacion para que ../data apunte a la carpeta de datos.
datos <- read.csv("../data/dca_mi_variante.csv", stringsAsFactors = FALSE) # Lee las observaciones registradas para cada secador.
datos$secador <- factor(datos$secador) # Trata cada secador como un nivel de tratamiento y no como una cantidad numérica.
modelo <- aov(humedad ~ factor(secador), data = datos) # Ajusta el ANOVA de un factor para comparar las medias de humedad.
print(summary(modelo)) # Muestra la tabla ANOVA y permite revisar si hay diferencias entre tratamientos.
medias_secador <- aggregate(humedad ~ secador, data = datos, FUN = mean) # Calcula la media de humedad de las réplicas de cada secador.
print(medias_secador) # Presenta las medias para identificar el nivel promedio de cada tratamiento.
tabla_anova <- summary(modelo)[[1]] # Guarda la tabla ANOVA para obtener el cuadrado medio del error.
cme <- tabla_anova["Residuals", "Mean Sq"] # Usa el cuadrado medio residual como estimación de la variabilidad experimental.
media_general <- mean(datos$humedad) # Calcula la media de todas las observaciones para expresar el error en escala relativa.
cv <- sqrt(cme) / media_general * 100 # Calcula el CV (%) = raíz del CME / media general * 100 para resumir la precisión del ensayo.
cat(sprintf("Coeficiente de variación: %.4f %%\n", cv)) # Imprime el CV en porcentaje para facilitar su lectura.
print(TukeyHSD(modelo)) # Compara pares de medias y ajusta por comparaciones múltiples.