# SolarSite Analytics

Plataforma de evaluación del potencial solar para instalaciones fotovoltaicas residenciales y comerciales. Consume datos históricos de la API pública NASA POWER y estima la generación de energía, el retorno de inversión y el impacto ambiental de un sistema fotovoltaico para cualquier ubicación en Colombia.

---

## Requisitos previos

- Python 3.10 o superior
- Conexión a internet (para consultar la API de NASA POWER)
- Sistema operativo Windows

No se requiere ninguna cuenta ni token de API.

---

## Instalación y uso

Doble clic sobre `iniciar.bat`.

El script detecta automáticamente si es la primera ejecución. Si lo es, crea el entorno virtual e instala todas las dependencias antes de lanzar la aplicación. En ejecuciones posteriores arranca directamente.

La aplicación queda disponible en `http://localhost:8501` y se abre sola en el navegador por defecto.

Para cerrar la aplicación presiona `Ctrl + C` en la ventana de terminal.

---

## Estructura del proyecto

```
solarsite-analytics/
├── iniciar.bat            Lanzador con instalación automática
├── app.py                 Interfaz principal (Streamlit)
├── data_fetcher.py        Conexión a NASA POWER y parseo de datos
├── energy_calculator.py   Cálculos fotovoltaicos y KPIs
├── config.json            Parámetros configurables del sistema
└── requirements.txt       Dependencias de Python
```

---

## Configuración

Todos los parámetros del sistema se controlan desde `config.json`. No es necesario modificar ningún archivo `.py` para ajustar el comportamiento de la aplicación.

### Sistema fotovoltaico

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `panel_potencia_wp` | Potencia pico por panel (Wp) | 400 |
| `panel_eficiencia` | Eficiencia de conversión del panel | 0.20 |
| `panel_area_m2` | Area fisica de cada panel (m2) | 2.0 |
| `num_paneles` | Cantidad de paneles instalados | 10 |
| `performance_ratio` | Factor de rendimiento global del sistema | 0.75 |
| `vida_util_anios` | Vida util garantizada del sistema | 25 |
| `degradacion_anual` | Degradacion anual de los paneles | 0.005 |

### Parametros economicos

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `tarifa_kwh_cop` | Tarifa electrica (COP/kWh) | 850 |
| `precio_sistema_cop` | Costo total de instalacion (COP) | 18.000.000 |

### Parametros ambientales

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `factor_emision_co2_kg_kwh` | Factor de emision de la red electrica colombiana | 0.126 |
| `co2_absorbido_arbol_kg_anio` | CO2 absorbido por arbol al año (kg) | 21 |

### Interfaz

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `mapa_zoom` | Nivel de zoom inicial del mapa | 11 |
| `proyeccion_anios` | Años mostrados en la tabla de proyeccion financiera | 10 |
| `umbral_potencial_muy_alto` | Umbral de radiacion para clasificar potencial muy alto (kWh/m2/dia) | 5.5 |
| `umbral_potencial_alto` | Umbral para potencial alto | 4.5 |
| `umbral_potencial_moderado` | Umbral para potencial moderado | 3.5 |

---

## Fuente de datos

NASA POWER (Prediction of Worldwide Energy Resources) es un proyecto de la NASA que provee datos meteorologicos y de radiacion solar derivados de modelos satelitales. Los datos corresponden a climatologia mensual promedio historica y estan disponibles para cualquier coordenada del planeta sin registro ni autenticacion.

Endpoint utilizado: `https://power.larc.nasa.gov/api/temporal/climatology/point`

Variables consumidas:

- `ALLSKY_SFC_SW_DWN` — Irradiacion global horizontal real (kWh/m2/dia)
- `CLRSKY_SFC_SW_DWN` — Irradiacion en condiciones de cielo despejado (kWh/m2/dia)
- `T2M` — Temperatura media a 2 metros de altura (°C)
- `CLOUD_AMT` — Porcentaje de nubosidad (%)

---

## Metodologia de calculo

La estimacion de energia generada sigue la formula estandar de la industria fotovoltaica:

```
E = A x r x H x PR
```

| Variable | Descripcion |
|---|---|
| A | Area total del arreglo de paneles (m2) |
| r | Eficiencia de conversion del panel |
| H | Irradiacion solar mensual (kWh/m2/dia) |
| PR | Performance Ratio: factor de perdidas reales del sistema |

El Performance Ratio del 75% por defecto contempla perdidas tipicas por temperatura, suciedad, tolerancias de fabricacion, cableado e inversor.

El calculo de retorno de inversion incorpora una degradacion anual del 0.5% en la generacion, consistente con las garantias de los fabricantes de paneles monocristalinos actuales.

El factor de emision de CO2 (0.126 kg/kWh) corresponde al factor de emision de la red electrica colombiana publicado por el IDEAM.

---

## Ciudades disponibles

La aplicacion incluye 25 ciudades colombianas distribuidas en todos los departamentos del pais. La lista se administra desde la seccion `ciudades` del archivo `config.json` en formato:

```json
"Nombre ciudad (Departamento)": [latitud, longitud]
```

Para agregar una ciudad nueva basta con añadir una entrada en ese bloque y reiniciar la aplicacion.

---

## Dependencias

| Libreria | Version | Uso |
|---|---|---|
| streamlit | 1.35.0 | Interfaz de usuario |
| pandas | 2.2.2 | Manipulacion de datos |
| plotly | 5.22.0 | Graficos interactivos |
| folium | 0.17.0 | Mapas interactivos |
| streamlit-folium | 0.21.0 | Integracion Folium en Streamlit |
| requests | 2.32.3 | Consultas HTTP a la API |
| numpy | 1.26.4 | Operaciones numericas |

---

## Limitaciones conocidas

- Los datos de NASA POWER son promedios historicos climatologicos, no mediciones en tiempo real. Los valores reales de generacion pueden variar segun condiciones locales especificas como sombras, orientacion exacta del techo o contaminacion atmosferica local.
- La formula de calculo asume paneles orientados horizontalmente. Para instalaciones con inclinacion y azimut optimizados los valores reales seran superiores a los estimados.
- La tarifa electrica y el costo de instalacion son parametros que el usuario debe ajustar segun su situacion particular.