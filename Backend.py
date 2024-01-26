import dash
from dash import dcc
from dash import html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.express as px


#crea el servidor web
app = dash.Dash()

fecha = [] #cremos una lista vacia
latitudes = [] #creamos una lista vacia
longitudes = [] #creamos una lista vacia
m = [] #creamos una lista vacia

#creamos una fucnion que calcula la calidad del aire 
def calculadora(m):
    polucion = 0
    #for valores in m:
    if m >= 0 and m <= 12:
        polucion = 0
    elif m >= 13 and m <= 35:
        polucion = 1
    elif m >= 36 and m <= 55:
        polucion = 2
    elif m >= 56:
        polucion = 3
    return polucion

#la direccion de donde se sacan los datos
url = "http://siata.gov.co:8089/estacionesAirePM25/cf7bb09b4d7d859a2840e22c3f3a9a8039917cc3/"
captura_web = pd.read_json(url,convert_dates='True') #captura los datos de la pg del siata
captura_datos_puros = captura_web.datos.values.tolist()
#captura_web.to_csv("datos-siata-json.txt")

#con el ciclo for guardamos los datos capturamos en las listas
for i in range(0,18):
  fecha.append(captura_web.datos[i]['ultimaActualizacion'])
  latitudes.append(captura_web.datos[i]['coordenadas'][0]['latitud'])
  longitudes.append(captura_web.datos[i]['coordenadas'][0]['longitud'])
  m.append(captura_web.datos[i]['valorICA'])
print(m)

m=np.array(m) #creamos un array con m
ysuperior=max(latitudes) #calculamos el valor maxino de latitud
yinferior=min(latitudes) #calculamos el valor minimo de latitud
xinferior=min(longitudes) #calculamos el valor maximo de longitudes
xsuperior=max(longitudes) #calculamos el valor minimo de longituf

#creamos una grilla o malla 
grid_x, grid_y = np.meshgrid(np.linspace(xinferior,xsuperior,100), np.linspace(yinferior,ysuperior,100))

#construyo la interpolacion
from scipy.interpolate import griddata

#predecimos los valores de m segun con los algoritmos de nearest, linear y cubic
grid_z0 = griddata((latitudes, longitudes), m, (grid_y, grid_x), method='nearest') 
grid_z1 = griddata((latitudes, longitudes), m, (grid_y, grid_x), method='linear')
grid_z2 = griddata((latitudes, longitudes), m, (grid_y, grid_x), method='cubic')

#llenar los datos NaN con el valor de nearest para completar los datos en z1 y z2
rows = grid_z0.shape[0]
cols = grid_z0.shape[1]

for x in range(0, cols):
    for y in range(0, rows):
        if np.isnan(grid_z1[x,y]):
            grid_z1[x,y]=grid_z0[x,y]
        if np.isnan(grid_z2[x,y]):
            grid_z2[x,y]=grid_z0[x,y]

#crea una lista
l_z = []
l_lat = []
l_lon = []
for x in range(0, cols - 1):
    for y in range(0, rows -1):
        l_z.append((calculadora(grid_z2[x,y]))) #calculamos la calidad del aire con la funcion calcular
        l_lat.append(grid_y[x,y])
        l_lon.append(grid_x[x,y])

data = pd.DataFrame() # creao un data frame para manejar facilmente los datos
data["dato"] = l_z
data["lat"] = l_lat
data["lon"] = l_lon
fig2 = px.scatter_mapbox(data, lat='lat', lon='lon', 
                       mapbox_style="open-street-map")

#creammos un mapa con los valores del dataset
fig = go.Figure(go.Densitymapbox(lat=l_lat, lon=l_lon, z=l_z, radius=10))
fig.update_layout(mapbox_style="stamen-terrain", mapbox_center_lon=180)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})


app.layout = html.Div([
    html.H1('MAPA DE CONTAMINACION INTERPOLADA SOBRE LA CIUDAD',style={
        'padding': '10px 5px' #titulo pagina
    }),
    html.Div('Mapa de calor generalizado',id='text-content',style={
        'padding': '10px 5px' #subtitulo
    }),
    #html.Label({}),

    html.Div([dcc.Graph(id='map', figure=fig)], style={'width': '90%', 'float': 'left', 'display': 'inline-block'})
])

#funcion principal
if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0',port=80)
