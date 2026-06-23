# SolarSite Analytics

**SolarSite Analytics** es una plataforma web interactiva diseñada para la evaluación rápida del potencial solar en diferentes ubicaciones geográficas. El objetivo del proyecto es mitigar la incertidumbre técnica y económica antes de realizar inversiones en infraestructura fotovoltaica (paneles solares), permitiendo a empresas y usuarios residenciales visualizar la viabilidad energética de sus proyectos.

## Características principales
* **Consulta en Tiempo Real:** Integración directa con la API de **NASA POWER** para obtener datos climáticos históricos.
* **Métricas Clave:** Análisis de radiación solar (GHI), nubosidad y temperatura ambiente de la región seleccionada.
* **Estimador Fotovoltaico:** Cálculo automatizado de la producción energética estimada mensual y anual basado en parámetros estándar del sistema ($E = A \times r \times H \times PR$).
* **Mapas e Interfaz Interactiva:** Visualización geográfica mediante mapas dinámicos y gráficos analíticos interactivos.

## Stack Tecnológico
* **Lenguaje:** Python 3.x
* **Frontend/Dashboard:** Streamlit
* **Análisis de Datos:** Pandas / NumPy
* **Visualización:** Plotly / Folium
* **Fuentes de Datos:** NASA POWER API

## Instalación y Configuración

1. **Clonar el repositorio:**
```bash
   git clone [https://github.com/tu-usuario/solarsite-analytics.git](https://github.com/tu-usuario/solarsite-analytics.git)
   cd solarsite-analytics