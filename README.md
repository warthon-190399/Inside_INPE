# Inside INPE
## Descripción del Proyecto
Inside INPE es una aplicación de análisis y visualización de datos geográficos que permite explorar la distribución espacial de crímenes reportados por la población carcelaria en la ciudad de Lima y el Callao durante el año 2021. La aplicación utiliza diversas técnicas y visualizaciones para proporcionar una comprensión más profunda de la dinámica delictiva en la región.

## Contenido del repositorio

**crimenes_2021.csv**: Archivo CSV que contiene datos sobre crímenes reportados en el año 2021, con detalles sobre delitos, ubicaciones y otros atributos.
**lima_callao_distritos.geojson**: Archivo GeoJSON que representa la división geográfica de Lima y el Callao en distritos.
**INSIDE_INPE.ipynb**: Notebook del código
**inside.py**: Código fuente de la aplicación Streamlit que carga, limpia y visualiza los datos geográfico
**logo.png**: Imagen del logo utilizado en la aplicación.
**requirements.txt**: librerías utilizadas

## Contenido de la aplicación

La aplicación utiliza las siguientes visualizaciones y técnicas:

**Mapa Choropleth**: Representa la distribución de crímenes mediante un mapa de colores en los diferentes distritos de Lima y el Callao.

**Mapa de Burbujas**: Muestra la ubicación de crímenes mediante burbujas, donde el color representa el tipo de delito y el tamaño indica el número de ingresos a prisión.

**Mapa de Calor**: Visualiza la densidad de crímenes en función del número de ingresos, utilizando colores cálidos para áreas con mayor concentración y colores más fríos para áreas menos densas.

**Mapa de Hexágonos**: Utiliza hexágonos regulares para discretizar el espacio geográfico, proporcionando una visión estructurada de la incidencia delictiva.

**DBSCAN Clustering**: Implementa el algoritmo de agrupamiento espacial DBSCAN para identificar zonas con mayor incidencia de crímenes, resaltando clusters en el mapa.





