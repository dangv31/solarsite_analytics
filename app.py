"""
app.py
SolarSite Analytics — Interfaz principal Streamlit.
Fase 3.1: Maquetación y Sidebar con parámetros del sistema.
"""
import folium
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
from data_fetcher import fetch_solar_data, PRESET_CITIES, get_annual_summary
from energy_calculator import (
    calcular_energia_mensual,
    calcular_kpis,
    DEFAULT_PARAMS,
)

# ---------------------------------------------------------------------------
# Configuración global de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SolarSite Analytics",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS personalizado — paleta solar
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Fondo sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; }

    /* Título principal */
    .solar-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FFD700, #FF6B35);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .solar-subtitle {
        color: #888;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }

    /* Tarjetas de sección */
    .section-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #2a2a4a;
        margin-bottom: 1rem;
    }

    /* Separador sidebar */
    .sidebar-section {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #FFD700 !important;
        text-transform: uppercase;
        margin: 1.2rem 0 0.4rem 0;
    }

    /* Ocultar menú hamburguesa */
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — Panel de control
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ☀️ SolarSite Analytics")
    st.markdown("---")

    # ── 1. Selección de ubicación ──────────────────────────────────────────
    st.markdown('<p class="sidebar-section">📍 Ubicación</p>', unsafe_allow_html=True)

    modo_ubicacion = st.radio(
        "Selecciona el modo",
        ["Ciudad predefinida", "Coordenadas manuales"],
        horizontal=True,
    )

    if modo_ubicacion == "Ciudad predefinida":
        ciudad = st.selectbox("Ciudad", list(PRESET_CITIES.keys()))
        lat, lon = PRESET_CITIES[ciudad]
        st.caption(f"Lat: {lat:.4f} | Lon: {lon:.4f}")
    else:
        lat = st.number_input("Latitud",  min_value=-90.0,  max_value=90.0,  value=6.2442,  step=0.0001, format="%.4f")
        lon = st.number_input("Longitud", min_value=-180.0, max_value=180.0, value=-75.5812, step=0.0001, format="%.4f")
        ciudad = f"Coordenadas ({lat:.3f}, {lon:.3f})"

    # ── 2. Parámetros del sistema fotovoltaico ─────────────────────────────
    st.markdown('<p class="sidebar-section">⚡ Sistema fotovoltaico</p>', unsafe_allow_html=True)

    num_paneles = st.slider(
        "Número de paneles",
        min_value=2, max_value=50,
        value=DEFAULT_PARAMS["num_paneles"],
        step=1,
        help="Cada panel es de 400 Wp (monocristalino estándar)",
    )

    panel_eficiencia = st.slider(
        "Eficiencia del panel (%)",
        min_value=14, max_value=23,
        value=int(DEFAULT_PARAMS["panel_eficiencia"] * 100),
        step=1,
        help="Rango típico: 17-22% para paneles comerciales actuales",
    ) / 100

    performance_ratio = st.slider(
        "Performance Ratio — PR (%)",
        min_value=60, max_value=90,
        value=int(DEFAULT_PARAMS["performance_ratio"] * 100),
        step=1,
        help="Pérdidas reales: inversor, temperatura, suciedad, cableado",
    ) / 100

    # ── 3. Parámetros económicos ───────────────────────────────────────────
    st.markdown('<p class="sidebar-section">💰 Parámetros económicos</p>', unsafe_allow_html=True)

    tarifa_kwh = st.number_input(
        "Tarifa eléctrica (COP/kWh)",
        min_value=100, max_value=2000,
        value=DEFAULT_PARAMS["tarifa_kwh_cop"],
        step=50,
        help="Consulta tu factura de energía. Media Colombia ≈ 850 COP/kWh",
    )

    precio_sistema = st.number_input(
        "Costo del sistema (COP)",
        min_value=1_000_000, max_value=100_000_000,
        value=DEFAULT_PARAMS["precio_sistema_cop"],
        step=500_000,
        format="%d",
        help="Costo total de instalación incluyendo paneles, inversor y mano de obra",
    )

    st.markdown("---")

    # ── Botón de análisis ──────────────────────────────────────────────────
    analizar = st.button("🔍 Analizar potencial solar", use_container_width=True, type="primary")


# ---------------------------------------------------------------------------
# Área principal
# ---------------------------------------------------------------------------
st.markdown('<h1 class="solar-title">☀️ SolarSite Analytics</h1>', unsafe_allow_html=True)
st.markdown('<p class="solar-subtitle">Plataforma de evaluación del potencial fotovoltaico · Datos NASA POWER</p>', unsafe_allow_html=True)

# Estado de sesión para persistir resultados entre interacciones
if "df_energia" not in st.session_state:
    st.session_state.df_energia = None
    st.session_state.kpis       = None
    st.session_state.ciudad_act = None

# ---------------------------------------------------------------------------
# Lógica de carga de datos
# ---------------------------------------------------------------------------
if analizar:
    with st.spinner(f"Consultando NASA POWER para **{ciudad}**..."):
        df_solar = fetch_solar_data(lat, lon)

    if df_solar is not None:
        df_energia = calcular_energia_mensual(
            df_solar,
            num_paneles=num_paneles,
            panel_eficiencia=panel_eficiencia,
            performance_ratio=performance_ratio,
        )
        kpis = calcular_kpis(
            df_energia,
            tarifa_kwh_cop=tarifa_kwh,
            precio_sistema_cop=precio_sistema,
            num_paneles=num_paneles,
        )
        st.session_state.df_energia = df_energia
        st.session_state.kpis       = kpis
        st.session_state.ciudad_act = ciudad
        st.success(f"✅ Datos cargados para **{ciudad}**")
    else:
        st.error("❌ No se pudieron obtener datos. Verifica tu conexión a internet.")

# ---------------------------------------------------------------------------
# Render principal (si hay datos cargados)
# ---------------------------------------------------------------------------
if st.session_state.df_energia is not None:
    df  = st.session_state.df_energia
    kpis = st.session_state.kpis

    st.markdown(f"### 📍 Analizando: `{st.session_state.ciudad_act}`")
    st.markdown("---")

    # Placeholder para los próximos pasos
    tab_mapa, tab_graficos, tab_kpis, tab_datos = st.tabs([
        "🗺️ Mapa",
        "📈 Radiación & Temperatura",
        "⚡ KPIs del Sistema",
        "📋 Datos Crudos",
    ])

    with tab_mapa:
        st.subheader(f"📍 Ubicación seleccionada — {st.session_state.ciudad_act}")

        # ── Datos para el mapa ─────────────────────────────────────────────
        resumen = get_annual_summary(df)
        rad_media = resumen["radiacion_media_dia"]

        # Color del marcador según potencial solar
        if rad_media >= 5.5:
            color_marcador = "red"
            potencial_label = "🔴 Muy Alto"
        elif rad_media >= 4.5:
            color_marcador = "orange"
            potencial_label = "🟠 Alto"
        elif rad_media >= 3.5:
            color_marcador = "green"
            potencial_label = "🟢 Moderado"
        else:
            color_marcador = "blue"
            potencial_label = "🔵 Bajo"

        # ── Construcción del mapa ──────────────────────────────────────────
        mapa = folium.Map(
            location=[lat, lon],
            zoom_start=11,
            tiles="CartoDB dark_matter",  # Estilo oscuro acorde a la UI
        )

        # Círculo de área de influencia
        folium.Circle(
            location=[lat, lon],
            radius=3000,
            color="#FFD700",
            fill=True,
            fill_color="#FFD700",
            fill_opacity=0.08,
            weight=1.5,
        ).add_to(mapa)

        # Marcador principal con popup detallado
        popup_html = f"""
        <div style="font-family:sans-serif; min-width:220px; padding:4px">
            <h4 style="color:#FF6B35; margin:0 0 8px 0">☀️ {st.session_state.ciudad_act}</h4>
            <table style="width:100%; font-size:13px; border-collapse:collapse">
                <tr><td style="padding:3px 0; color:#666">Potencial solar</td>
                    <td style="text-align:right; font-weight:bold">{potencial_label}</td></tr>
                <tr><td style="padding:3px 0; color:#666">Radiación media</td>
                    <td style="text-align:right"><b>{rad_media:.3f}</b> kWh/m²/día</td></tr>
                <tr><td style="padding:3px 0; color:#666">Mejor mes</td>
                    <td style="text-align:right"><b>{resumen['mejor_mes']}</b></td></tr>
                <tr><td style="padding:3px 0; color:#666">Peor mes</td>
                    <td style="text-align:right"><b>{resumen['peor_mes']}</b></td></tr>
                <tr><td style="padding:3px 0; color:#666">Temperatura media</td>
                    <td style="text-align:right"><b>{resumen['temperatura_media']:.1f}</b> °C</td></tr>
                <tr><td style="padding:3px 0; color:#666">Nubosidad media</td>
                    <td style="text-align:right"><b>{resumen['nubosidad_media']:.1f}</b> %</td></tr>
                <tr><td style="padding:3px 0; color:#666">Latitud / Longitud</td>
                    <td style="text-align:right">{lat:.4f} / {lon:.4f}</td></tr>
            </table>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"☀️ {st.session_state.ciudad_act} — clic para detalles",
            icon=folium.Icon(color=color_marcador, icon="sun-o", prefix="fa"),
        ).add_to(mapa)

        # ── Render del mapa ────────────────────────────────────────────────
        col_mapa, col_info = st.columns([3, 1])

        with col_mapa:
            st_folium(mapa, width=None, height=420, returned_objects=[])

        with col_info:
            st.markdown("#### Resumen de ubicación")
            st.metric("Potencial", potencial_label)
            st.metric("Radiación media diaria", f"{rad_media:.2f} kWh/m²/día")
            st.metric("Mejor mes", resumen["mejor_mes"])
            st.metric("Peor mes", resumen["peor_mes"])
            st.metric("Temperatura media", f"{resumen['temperatura_media']:.1f} °C")
            st.metric("Nubosidad media", f"{resumen['nubosidad_media']:.1f} %")

    with tab_graficos:
        st.info("📈 Gráficos Plotly — se implementarán en el Paso 3.3")

    with tab_kpis:
        st.info("⚡ Dashboard de KPIs — se implementará en el Paso 3.4")

    with tab_datos:
        st.subheader("DataFrame completo")
        st.dataframe(
            df[[
                "mes", "radiacion_kwh", "radiacion_clear",
                "temperatura_c", "nubosidad_pct",
                "energia_dia_kwh", "energia_mes_kwh"
            ]].style.format({
                "radiacion_kwh":   "{:.3f}",
                "radiacion_clear": "{:.3f}",
                "temperatura_c":   "{:.1f}",
                "nubosidad_pct":   "{:.1f}",
                "energia_dia_kwh": "{:.2f}",
                "energia_mes_kwh": "{:.1f}",
            }),
            use_container_width=True,
            height=460,
        )

else:
    # Pantalla de bienvenida
    st.markdown("""
    <div class="section-card">
        <h3 style="color:#FFD700">¿Cómo usar SolarSite Analytics?</h3>
        <ol style="color:#ccc; line-height:2">
            <li>Selecciona una <b>ciudad</b> o ingresa <b>coordenadas</b> en el panel izquierdo</li>
            <li>Ajusta los <b>parámetros de tu sistema</b> fotovoltaico</li>
            <li>Configura tu <b>tarifa eléctrica</b> y costo estimado de instalación</li>
            <li>Pulsa <b>🔍 Analizar potencial solar</b></li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("APIs integradas", "NASA POWER", "Datos históricos reales")
    with col2:
        st.metric("Ciudades preconfiguradas", len(PRESET_CITIES), "América y Europa")
    with col3:
        st.metric("Horizonte de análisis", "25 años", "Vida útil del sistema")