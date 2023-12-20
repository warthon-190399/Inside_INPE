# 1.- Importamos las librerias

import pandas as pd
import numpy as np
import plotly.express as px
import pydeck as pdk
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from shapely.geometry import MultiPoint
import streamlit as st
import json
import h3
import warnings
warnings.filterwarnings("ignore")

#2.- Importamos el dataset

crimpob = pd.read_csv('crimenes_2021.csv',
                index_col='ID'
                )

#3.- Limpiamos datos

crimpob_lc = crimpob[(crimpob['DEPARTAMENTO'].isin(['LIMA', 'CALLAO'])) &
                     ((crimpob['PROVINCIA'] == 'LIMA') |
                      (crimpob['DEPARTAMENTO'] == 'CALLAO'))]

crimpob_lc.dropna()

#4.- EDA

#5.- Geo Analisis

#5.1.- Trabajamos el geojson

data = open('lima_callao_distritos.geojson',
           encoding='utf8'
           )
distritos = json.load(data)

id = []
distrito = []

for idx in range(len(distritos['features'])):
    id.append(distritos['features'][idx]['properties']['id'])
    distrito.append(distritos['features'][idx]['properties']['distrito'])

geojson_df = pd.DataFrame({
    'id':id,
    'distrito':distrito
})

#5.2.- Choropleth

fig_choro = px.choropleth_mapbox(geojson_df,
                           geojson=distritos,
                           locations='id',
                           featureidkey='properties.id',
                           mapbox_style='carto-positron',
                           zoom=8,
                           center={'lat':-12.041377,
                                   'lon': -77.039402},
                           opacity=0.5,
                           hover_data=['distrito']
)

crim_choro = px.scatter_mapbox(crimpob_lc,
                            lat='LATITUD',
                            lon='LONGITUD',
                            hover_name='DISTRITO',
                            color_discrete_sequence=["red"]
)

fig_choro.add_trace(crim_choro.data[0])

#5.3.- Mapbox
fig_map = px.scatter_mapbox(crimpob_lc,
                        lat='LATITUD',
                        lon='LONGITUD',
                        mapbox_style='carto-positron',
                        zoom=8, #ciudad
                        hover_name='DISTRITO',
                        color='DELITO_GENERICO',
                        size='NUMERO_DE_INGRESOS',
                        center={'lat':-12.041377,
                                   'lon': -77.039402},
                        size_max=20 #limita el tamaño del punto
                        )
fig_map.update_layout(margin={'r':0,'t':0,'l':0,'b':0}) #elimina el marco
fig_map.update_layout(legend=dict(orientation='h',
                                  x= 0.5,
                                  y=-0.6,
                                  yanchor="bottom",
                                  xanchor="center",
                                  traceorder="normal",
                                  title="TIPO DE DELITO",
                                  title_font=dict(size=14),
                                  itemclick='toggleothers'
                                  )
                      )

#5.4.- Heatmap

fig = px.density_mapbox(crimpob_lc,
                        lat='LATITUD',
                        lon='LONGITUD',
                        mapbox_style='carto-positron',
                        color_continuous_scale='inferno',
                        zoom=8,
                        z='NUMERO_DE_INGRESOS',  # Utiliza GRUPOS_DE_INGRESOS como la variable de intensidad
                        radius=10,
                        opacity=0.9,
                        center={
                            'lat': -12.055710,
                            'lon': -77.032658
                        })
fig.update_layout(
    margin={'r': 0, 't': 0, 'b': 0, 'l': 0}
)

#5.5.- Hexagon

crimpob_h3 = crimpob_lc.copy()
RES = 8
crimpob_h3['h3'] = crimpob_h3.apply(lambda x: h3.geo_to_h3(x.LATITUD, x.LONGITUD, RES), axis=1)

layer = pdk.Layer(
    "H3HexagonLayer",  # Design
    crimpob_h3,
    pickable=True,  # Selectable
    stroked=True,  # Show hexagon area boundaries
    filled=True,  # Fill hexagons with color
    extruded=False,
    get_hexagon="h3",
    get_fill_color="[255, 255, 100, 50]",
    get_line_color=[255, 255, 255],
    line_width_min_pixels=2,
)

view_state = pdk.ViewState(
    latitude=-12.041377,
    longitude=-77.039402,
    zoom=10,
    bearing=0,
    pitch=30  # Pitch or tilt of the map
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "html": "<b>District:</b> {DISTRITO}<br/><b>Crime Count:</b> {NUMERO_DE_INGRESOS}<br/><b>Crime Type:</b> {DELITO_GENERICO}",
        "style": {"color": "white"}
    }
)  

# Render the visualization and save as an HTML file
deck.to_html("h3_hexagon_layer.html")

#6.- Preprocessing

drop_columns = ['PULMONAR_KPI', 'LOCALIZACION_TB', 'CONDICION_INGRESO', 'ABANDONO_RECUPERADO_KPI','ALCOHOLISMO', 'TABAQUISMO', 'DROGADICCION', 'SEXO', 'SEXO_MUJER_KPI', 'TRES_INGRESOS_KPI', 'RECIBE_TARGA', 'TIPO_DE_SEGURO_DE_SALUD', 'ALCOHOLISMO_KPI', 'TABAQUISMO_KPI', 'DROGADICCION_KPI', 'DELITO_GENERICO', 'SITUACION_JURIDICA', 'GRADO_DE_INSTRUCCION', 'OCUPACION_GENERICA', 'OCUPACION_ESPECIFICA', 'ESTADO_CIVIL', 'RANGO_DE_EDAD']
for column in drop_columns:
    crimpob_lc.drop(column, axis=1, inplace=True)

#7.- DBSCAN

KM_EPSILON = 0.5
MIN_SAMPLES = 6

def get_centermostpoint(cluster):
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    centermost_point = min(cluster, key=lambda point: great_circle(point,centroid).m)
    return tuple(centermost_point)

crimpob_lc_clean = crimpob_h3[~crimpob_h3['LATITUD'].isna()]
coords_cluster = crimpob_lc_clean[['LATITUD', 'LONGITUD']].to_numpy()

kms_per_radian = 6371.0088
epsilon = KM_EPSILON / kms_per_radian

db = DBSCAN(eps=epsilon,
           min_samples=MIN_SAMPLES,
            algorithm='ball_tree',
            metric='haversine'
           ).fit(np.radians(coords_cluster))

cluster_labels = db.labels_

num_clusters = len(set(cluster_labels))
clusters = pd.Series([coords_cluster[cluster_labels == n] for n in range(num_clusters)]).iloc[:-1]

centermost_points = clusters.map(get_centermostpoint)

lats, lons = zip(*centermost_points)
rep_points = pd.DataFrame({'lat':lats, 'lon':lons})
rep_points['size'] = 6

fig_DBSCAN = px.choropleth_mapbox(geojson_df,
                           geojson=distritos,
                           locations='id',
                           featureidkey='properties.id',
                           #color='color',
                           mapbox_style='carto-positron',
                           zoom=8,
                           center={'lat':-12.041377,
                                   'lon': -77.039402},
                           opacity=0.4,
                           hover_data=['distrito']
                          )

incidentes_cluster = px.scatter_mapbox(rep_points,
                                      lat="lat",
                                       lon="lon",
                                       hover_name="size",
                                       hover_data=["size"],
                                       mapbox_style="carto-positron",
                                       zoom=10,
                                       center={
                                           'lat':-12.036891,
                                           'lon':-77.026508
                                       },
                                       opacity=0.6,
                                       color_discrete_sequence=['red']
                                      )

fig_DBSCAN.add_trace(incidentes_cluster.data[0])


#8.- Layout

st.title("Inside INPE")
st.write("**Inside INPE** es una aplicación de streamlit que **permite observar datos georeferenciados del lugar de procedencia de delitos reportados por la población carcelaria de la ciudad de Lima y el Callao del año 2021**. En esta aplicación usted podrá observar el lugar de procedencia aprovechando las ventajas que brinda cada estilo de mapa disponible, siendo estos, **mapa choropleth**, **mapa de burbujas**, **mapa de calor** y **mapa de hexágonos**. Además, **se implementó** un algoritmo de clusterización espacial muy popular llamado **DBSCAN**. Las opciones están habilitadas en la barra lateral.")
st.divider()

logo = st.sidebar.image("logo.png")

st.sidebar.title("Opciones de visualización")

mapas = ["Mapa Choropleth", "Mapa de Burbujas", "Mapa de Calor", "Mapa de Hexágonos"]
selec_mapas = st.sidebar.selectbox("Escoja el mapa de su interés:", mapas)

dbscan_1 = ["Modelo de Clustering DBSCAN"]

selec_model = st.sidebar.multiselect("Visualizar modelo DBSCAN:", dbscan_1)

if "Modelo de Clustering DBSCAN" in selec_model:
    st.subheader("Modelo de Clustering Espacial DBSCAN")
    st.write("DBSCAN (Density-Based Spatial Clustering of Applications with Noise) es un **algoritmo de agrupamiento espacial basado en la densidad**. Su principal ventaja radica en su **capacidad para identificar agrupaciones de puntos en conjuntos de datos con formas y tamaños arbitrarios.**")
    st.write("Al aplicar DBSCAN a los datos de crímenes en Lima y Callao, se puede **obtener información valiosa** sobre la **agrupación de eventos delictivos**, identificando **áreas de interés para la aplicación de medidas preventivas y estrategias de seguridad**. Además, el algoritmo puede **revelar patrones geográficos específicos que podrían ser útiles para comprender mejor la dinámica del crimen en la región**.")
    st.plotly_chart(fig_DBSCAN)
    st.write("El algoritmo **DBSCAN** resalta las **zonas con mayor incidencia de crímenes en el mapa**. **Cada punto representa un cluster identificado por la proximidad entre los crímenes**. En otras palabras, los puntos en el mapa muestran **áreas específicas donde se concentran delitos**, y cada punto es el centro de un cluster de crímenes cercanos. Aquellas **ubicaciones con mayor densidad de puntos indican áreas con mayor actividad delictiva.**")
    st.divider()

if "Mapa Choropleth" in selec_mapas:
    st.subheader("Mapa Choropleth")
    st.write("Un choropleth es un tipo de mapa que **utiliza colores para mostrar la variación de una variable en diferentes áreas geográficas**, como distritos. Los puntos en el gráfico de dispersión **representan crímenes en ubicaciones específicas**, y al pasar el ratón, se revela el distrito asociado a cada crimen. Este mapa **ofrece una visión instantánea de la distribución de crímenes en relación con los distritos de Lima y el Callao**.")
    st.plotly_chart(fig_choro)
    st.divider()

if "Mapa de Burbujas" in selec_mapas:
    st.subheader("Mapa de Burbujas")
    st.write("El presente mapa de burbujas permite **visualizar la distribución geográfica de crímenes diferenciándolos por tipo de delito cometido**. Además, el tamaño de las burbujas refleja el número de ingresos a prisión por parte del delincuente. Este mapa **facilita la identificación y comprensión de patrones de crímenes en la ciudad**. Al pasar el mouse sobre las burbujas, se muestra información detallada, como el nombre del distrito y el tipo de delito cometido. La leyenda proporciona información adicional sobre el tipo de delito representado por cada color, si usted hace click en algún delito en la leyenda el mapa solo mostrará la distribución geográfica del delito seleccionado.")
    st.plotly_chart(fig_map)
    st.divider()

if "Mapa de Calor" in selec_mapas:
    st.subheader("Mapa de Calor")
    st.write("El mapa de calor **visualiza la densidad de crímenes en función del número de ingresos de los involucrados**. Utiliza **colores cálidos** para representar áreas con **mayor concentración de crímenes**, mientras que **colores más fríos** indican áreas con **menor densidad**. La **intensidad del color** en cada ubicación refleja el **número de ingresos promedio (reincidencia) de las personas relacionadas con los crímenes en esa área**. Al ajustar el zoom y la ubicación central del mapa, se puede explorar la distribución espacial de la edad de los involucrados en crímenes en la ciudad.")
    st.plotly_chart(fig)
    st.divider()

if "Mapa de Hexágonos" in selec_mapas:
    st.subheader("Mapa de Hexágonos")
    st.write("Un mapa de hexágonos es una herramienta efectiva para **analizar la distribución de crímenes en Lima y Callao**, ya que proporciona una representación visual clara y **comparativa de áreas específicas**. Al dividir el territorio en hexágonos regulares, se logra una **discretización (convierte los crímenes, que son variables continuas, en variables discretas)** que **simplifica la complejidad del espacio geográfico**, permitiendo identificar patrones y concentraciones de crímenes de manera más accesible. Esta metodología no solo mejora la legibilidad de la información, sino que también resalta las variaciones locales y proporciona una visión estructurada de la incidencia delictiva.")
    st.pydeck_chart(deck)
    st.divider()
 
