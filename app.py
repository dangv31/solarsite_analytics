"""
app.py
SolarSite Analytics — Interfaz principal Streamlit.
MVP completo consolidado.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import json
from pathlib import Path

from data_fetcher import fetch_solar_data, PRESET_CITIES, get_annual_summary
from energy_calculator import (
    calcular_energia_mensual,
    calcular_kpis
)

def load_config():
    with open(Path(__file__).parent / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)

CFG = load_config()

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
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; }

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
    .section-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #2a2a4a;
        margin-bottom: 1rem;
    }
    .sidebar-section {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #FFD700 !important;
        text-transform: uppercase;
        margin: 1.2rem 0 0.4rem 0;
    }
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

    # ── 1. Ubicación ──────────────────────────────────────────────────────
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
        lat = st.number_input("Latitud",  min_value=-90.0,  max_value=90.0,  value=6.2442,   step=0.0001, format="%.4f")
        lon = st.number_input("Longitud", min_value=-180.0, max_value=180.0, value=-75.5812, step=0.0001, format="%.4f")
        ciudad = f"Coordenadas ({lat:.3f}, {lon:.3f})"

    # ── 2. Sistema fotovoltaico ───────────────────────────────────────────
    st.markdown('<p class="sidebar-section">⚡ Sistema fotovoltaico</p>', unsafe_allow_html=True)

    num_paneles = st.slider(
        "Número de paneles",
        min_value=2, max_value=50,
        value=CFG["sistema"]["num_paneles"],
        step=1,
        help=f"Cada panel es de {CFG['sistema']['panel_potencia_wp']} Wp (monocristalino estándar)",
    )
    panel_eficiencia = st.slider(
        "Eficiencia del panel (%)",
        min_value=14, max_value=23,
        value=int(CFG["sistema"]["panel_eficiencia"] * 100),
        step=1,
        help="Rango típico: 17-22% para paneles comerciales actuales",
    ) / 100

    performance_ratio = st.slider(
        "Performance Ratio — PR (%)",
        min_value=60, max_value=90,
        value=int(CFG["sistema"]["performance_ratio"] * 100),
        step=1,
        help="Pérdidas reales: inversor, temperatura, suciedad, cableado",
    ) / 100

    # ── 3. Parámetros económicos ──────────────────────────────────────────
    st.markdown('<p class="sidebar-section">💰 Parámetros económicos</p>', unsafe_allow_html=True)

    tarifa_kwh = st.number_input(
        "Tarifa eléctrica (COP/kWh)",
        min_value=100, max_value=2000,
        value=CFG["economico"]["tarifa_kwh_cop"],
        step=50,
    )
    precio_sistema = st.number_input(
        "Costo del sistema (COP)",
        min_value=1_000_000, max_value=100_000_000,
        value=CFG["economico"]["precio_sistema_cop"],
        step=500_000,
        format="%d",
    )

    st.markdown("---")
    analizar = st.button("🔍 Analizar potencial solar", use_container_width=True, type="primary")


# ---------------------------------------------------------------------------
# Área principal — Header
# ---------------------------------------------------------------------------
st.markdown('<h1 class="solar-title">☀️ SolarSite Analytics</h1>', unsafe_allow_html=True)
st.markdown('<p class="solar-subtitle">Plataforma de evaluación del potencial fotovoltaico · Datos NASA POWER</p>', unsafe_allow_html=True)

# Estado de sesión
if "df_energia" not in st.session_state:
    st.session_state.df_energia = None
    st.session_state.kpis       = None
    st.session_state.ciudad_act = None
    st.session_state.lat        = None
    st.session_state.lon        = None

# ---------------------------------------------------------------------------
# Carga de datos
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
        st.session_state.lat        = lat
        st.session_state.lon        = lon
        st.success(f"Datos cargados para **{ciudad}**")
    else:
        st.error("No se pudieron obtener datos. Verifica tu conexión a internet.")

# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------
if st.session_state.df_energia is not None:
    df   = st.session_state.df_energia
    kpis = st.session_state.kpis
    lat  = st.session_state.lat
    lon  = st.session_state.lon

    st.markdown(f"### 📍 Analizando: `{st.session_state.ciudad_act}`")
    st.markdown("---")

    tab_mapa, tab_graficos, tab_kpis, tab_datos = st.tabs([
        "🗺️ Mapa",
        "📈 Radiación & Temperatura",
        "⚡ KPIs del Sistema",
        "📋 Datos Crudos",
    ])

    # ── Tab 1: Mapa ────────────────────────────────────────────────────────
    with tab_mapa:
        st.subheader(f"📍 Ubicación seleccionada — {st.session_state.ciudad_act}")

        resumen   = get_annual_summary(df)
        rad_media = resumen["radiacion_media_dia"]

        umbral_muy_alto = CFG["ui"]["umbral_potencial_muy_alto"]
        umbral_alto     = CFG["ui"]["umbral_potencial_alto"]
        umbral_moderado = CFG["ui"]["umbral_potencial_moderado"]

        if rad_media >= umbral_muy_alto:
            color_marcador = "red";    potencial_label = "🔴 Muy Alto"
        elif rad_media >= umbral_alto:
            color_marcador = "orange"; potencial_label = "🟠 Alto"
        elif rad_media >= umbral_moderado:
            color_marcador = "green";  potencial_label = "🟢 Moderado"
        else:
            color_marcador = "blue";   potencial_label = "🔵 Bajo"

        mapa = folium.Map(location=[lat, lon], zoom_start=11, tiles="CartoDB dark_matter")

        folium.Circle(
            location=[lat, lon], radius=3000,
            color="#FFD700", fill=True, fill_color="#FFD700",
            fill_opacity=0.08, weight=1.5,
        ).add_to(mapa)

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

        col_mapa, col_info = st.columns([3, 1])
        with col_mapa:
            st_folium(mapa, width=None, height=420, returned_objects=[])
        with col_info:
            st.markdown("#### Resumen de ubicación")
            st.metric("Potencial",             potencial_label)
            st.metric("Radiación media diaria", f"{rad_media:.2f} kWh/m²/día")
            st.metric("Mejor mes",             resumen["mejor_mes"])
            st.metric("Peor mes",              resumen["peor_mes"])
            st.metric("Temperatura media",     f"{resumen['temperatura_media']:.1f} °C")
            st.metric("Nubosidad media",       f"{resumen['nubosidad_media']:.1f} %")

    # ── Tab 2: Gráficos ────────────────────────────────────────────────────
    with tab_graficos:
        st.subheader("📈 Radiación Solar y Temperatura a lo largo del año")

        meses     = df["mes"].tolist()
        rad_real  = df["radiacion_kwh"].tolist()
        rad_clear = df["radiacion_clear"].tolist()
        temp      = df["temperatura_c"].tolist()
        nubosidad = df["nubosidad_pct"].tolist()
        energia   = df["energia_mes_kwh"].tolist()

        # Gráfico 1: Radiación real vs cielo despejado
        fig_rad = go.Figure()
        fig_rad.add_trace(go.Scatter(
            x=meses, y=rad_clear, name="Cielo despejado",
            mode="lines", line=dict(color="#FFD700", width=2, dash="dot"),
        ))
        fig_rad.add_trace(go.Scatter(
            x=meses, y=rad_real, name="Radiación real (con nubes)",
            mode="lines+markers",
            line=dict(color="#FF6B35", width=3),
            marker=dict(size=8, color="#FF6B35", line=dict(color="white", width=1.5)),
            fill="tonexty", fillcolor="rgba(255,107,53,0.12)",
        ))
        fig_rad.update_layout(
            title=dict(text="☀️ Irradiación Global Horizontal (kWh/m²/día)", font=dict(size=16)),
            xaxis_title="Mes", yaxis_title="kWh/m²/día",
            legend=dict(orientation="h", y=-0.2), height=380,
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="#e0e0e0"),
            xaxis=dict(gridcolor="#2a2a4a"), yaxis=dict(gridcolor="#2a2a4a"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_rad, use_container_width=True)

        # Gráfico 2: Temperatura y Nubosidad
        fig_temp = make_subplots(specs=[[{"secondary_y": True}]])
        fig_temp.add_trace(go.Bar(
            x=meses, y=nubosidad, name="Nubosidad (%)",
            marker_color="rgba(100,149,237,0.5)",
            marker_line_color="rgba(100,149,237,0.8)", marker_line_width=1,
        ), secondary_y=True)
        fig_temp.add_trace(go.Scatter(
            x=meses, y=temp, name="Temperatura (°C)",
            mode="lines+markers", line=dict(color="#00CED1", width=3),
            marker=dict(size=8, color="#00CED1", line=dict(color="white", width=1.5)),
        ), secondary_y=False)
        fig_temp.update_layout(
            title=dict(text="🌡️ Temperatura Media y Nubosidad Mensual", font=dict(size=16)),
            height=380, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="#e0e0e0"), xaxis=dict(gridcolor="#2a2a4a"),
            legend=dict(orientation="h", y=-0.2), hovermode="x unified",
        )
        fig_temp.update_yaxes(title_text="Temperatura (°C)", gridcolor="#2a2a4a", secondary_y=False)
        fig_temp.update_yaxes(title_text="Nubosidad (%)", range=[0, 100], secondary_y=True, showgrid=False)
        st.plotly_chart(fig_temp, use_container_width=True)

        # Gráfico 3: Energía mensual
        colores_barras = [
            "#FF6B35" if e == max(energia) else
            "#4a90d9" if e == min(energia) else
            "#FFD700"
            for e in energia
        ]
        fig_energia = go.Figure()
        fig_energia.add_trace(go.Bar(
            x=meses, y=energia, name="Energía generada",
            marker_color=colores_barras,
            marker_line_color="rgba(255,255,255,0.2)", marker_line_width=1,
            text=[f"{e:.0f}" for e in energia],
            textposition="outside", textfont=dict(color="#e0e0e0", size=11),
        ))
        fig_energia.add_hline(
            y=sum(energia) / 12, line_dash="dash",
            line_color="#ffffff", line_width=1.5,
            annotation_text=f"Media: {sum(energia)/12:.0f} kWh",
            annotation_position="top right",
            annotation_font_color="#ffffff",
        )
        fig_energia.update_layout(
            title=dict(text="⚡ Energía Estimada Generada por Mes (kWh)", font=dict(size=16)),
            xaxis_title="Mes", yaxis_title="kWh", height=380,
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="#e0e0e0"),
            xaxis=dict(gridcolor="#2a2a4a"), yaxis=dict(gridcolor="#2a2a4a"),
            showlegend=False,
        )
        st.plotly_chart(fig_energia, use_container_width=True)
        st.caption("🟠 Mejor mes · 🔵 Peor mes · 🟡 Resto del año  |  Línea blanca = media anual")

    # ── Tab 3: KPIs ────────────────────────────────────────────────────────
    with tab_kpis:
        st.subheader("⚡ KPIs del Sistema Fotovoltaico")

        potencia_kwp = kpis["potencia_pico_kwp"]

        # Fila 1: Técnicos
        st.markdown("#### 🔧 Rendimiento Técnico")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Potencia instalada",      f"{potencia_kwp:.1f} kWp",              f"{int(potencia_kwp*1000/400)} paneles × 400 Wp")
        col2.metric("Energía anual estimada",  f"{kpis['energia_anual_kwh']:,.0f} kWh", f"{kpis['energia_diaria_media']:.1f} kWh/día promedio")
        col3.metric("Mejor mes ☀️",             kpis["mejor_mes"],                       f"{kpis['mejor_mes_kwh']:,.0f} kWh generados")
        col4.metric("Peor mes 🌧️",              kpis["peor_mes"],                        f"{kpis['peor_mes_kwh']:,.0f} kWh generados", delta_color="inverse")

        st.markdown("---")

        # Fila 2: Financieros
        st.markdown("#### 💰 Retorno Financiero")
        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Ahorro mensual medio",   f"${kpis['ahorro_mensual_medio']:,.0f} COP",  "en factura eléctrica")
        col6.metric("Ahorro anual estimado",  f"${kpis['ahorro_anual_cop']:,.0f} COP",       f"a {int(CFG['economico']['tarifa_kwh_cop'])} COP/kWh")
        col7.metric("Período de retorno",     f"{kpis['payback_anios']:.1f} años",           f"sobre {CFG['sistema']['vida_util_anios']} años de vida útil")
        col8.metric("ROI a 25 años",          f"{kpis['roi_pct']:.1f}%",                     f"${kpis['ahorro_vida_util_cop']:,.0f} COP total")

        st.markdown("---")

        # Fila 3: Ambiental + Gauge
        st.markdown("#### 🌱 Impacto Ambiental & Potencial Solar")
        col9, col10 = st.columns([1, 2])

        with col9:
            st.metric("CO₂ evitado por año",   f"{kpis['co2_evitado_kg_anual']:,.0f} kg",   f"≈ {kpis['co2_evitado_kg_anual']*25/1000:.1f} ton en 25 años")
            st.metric("Árboles equivalentes",  f"{int(kpis['co2_evitado_kg_anual']/21)} árboles/año", "1 árbol absorbe ~21 kg CO₂/año")

        with col10:
            rad_media       = get_annual_summary(df)["radiacion_media_dia"]
            umbral_muy_alto = CFG["ui"]["umbral_potencial_muy_alto"]
            umbral_alto     = CFG["ui"]["umbral_potencial_alto"]
            umbral_moderado = CFG["ui"]["umbral_potencial_moderado"]

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=rad_media,
                title={"text": "Radiación Media Diaria (kWh/m²/día)", "font": {"size": 15}},
                delta={"reference": umbral_alto, "suffix": f" vs ref. {umbral_alto}"},
                number={"suffix": " kWh/m²/día", "font": {"size": 22}},
                gauge={
                    "axis": {"range": [0, 8], "tickcolor": "#e0e0e0"},
                    "bar":  {"color": "#FF6B35", "thickness": 0.25},
                    "bgcolor": "#1e1e2e", "bordercolor": "#2a2a4a",
                    "steps": [
                        {"range": [0,              umbral_moderado], "color": "#1a3a5c"},
                        {"range": [umbral_moderado, umbral_alto],    "color": "#1a5c3a"},
                        {"range": [umbral_alto,     umbral_muy_alto],"color": "#5c4a1a"},
                        {"range": [umbral_muy_alto, 8],              "color": "#5c1a1a"},
                    ],
                    "threshold": {"line": {"color": "#FFD700", "width": 3}, "thickness": 0.8, "value": rad_media},
                },
            ))
            fig_gauge.update_layout(
                height=280, paper_bgcolor="#0e1117",
                font=dict(color="#e0e0e0"), margin=dict(t=60, b=20, l=30, r=30),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("---")

        # Proyección 10 años
        st.markdown("#### 📊 Proyección financiera (primeros 10 años)")
        filas = []
        ahorro_base = kpis["ahorro_anual_cop"]
        for anio in range(1, CFG["ui"]["proyeccion_anios"] + 1):
            ahorro_anio = ahorro_base * ((1 - CFG["sistema"]["degradacion_anual"]) ** (anio - 1))
            acumulado   = sum(
                ahorro_base * ((1 - CFG["sistema"]["degradacion_anual"]) ** a)
                for a in range(anio)
            )
            recuperado = min(acumulado / CFG["economico"]["precio_sistema_cop"] * 100, 100)
            filas.append({
                "Año":                       anio,
                "Ahorro anual (COP)":        int(ahorro_anio),
                "Ahorro acumulado (COP)":    int(acumulado),
                "Inversión recuperada (%)":  round(recuperado, 1),
                "¿Payback alcanzado?":       "✅ Sí" if acumulado >= CFG["economico"]["precio_sistema_cop"] else "⏳ No",
            })
        df_proyeccion = pd.DataFrame(filas)
        st.dataframe(
            df_proyeccion.style.format({
                "Ahorro anual (COP)":       "{:,.0f}",
                "Ahorro acumulado (COP)":   "{:,.0f}",
                "Inversión recuperada (%)": "{:.1f}%",
            }).applymap(
                lambda v: "background-color: #1a3a1a" if v == "✅ Sí" else "",
                subset=["¿Payback alcanzado?"],
            ),
            use_container_width=True,
            hide_index=True,
        )

    # ── Tab 4: Datos crudos ────────────────────────────────────────────────
    with tab_datos:
        st.subheader("DataFrame completo")
        st.dataframe(
            df[[
                "mes", "radiacion_kwh", "radiacion_clear",
                "temperatura_c", "nubosidad_pct",
                "energia_dia_kwh", "energia_mes_kwh",
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

# ---------------------------------------------------------------------------
# Pantalla de bienvenida (sin datos aún)
# ---------------------------------------------------------------------------
else:
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
        st.metric("APIs integradas",            "NASA POWER",        "Datos históricos reales")
    with col2:
        st.metric("Ciudades preconfiguradas",   len(PRESET_CITIES),  "América y Europa")
    with col3:
        st.metric("Horizonte de análisis",      "25 años",           "Vida útil del sistema")