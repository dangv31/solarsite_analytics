"""
energy_calculator.py
Módulo de cálculo de energía fotovoltaica estimada.
Fórmula estándar: E = A × r × H × PR

Parámetros por defecto para un sistema residencial típico colombiano:
  - Panel monocristalino 400W estándar del mercado
  - Sistema de 4 kWp (10 paneles)
  - Instalación en techo inclinado, sin sombras significativas
"""

import pandas as pd
import numpy as np
from typing import Optional

# ---------------------------------------------------------------------------
# Constantes por defecto — sistema residencial estándar
# ---------------------------------------------------------------------------

# Días por mes (sin año bisiesto)
DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

DEFAULT_PARAMS = {
    # --- Panel ---
    "panel_potencia_wp":   400,      # Potencia pico por panel (Wp)
    "panel_eficiencia":    0.20,     # Eficiencia del panel (20% → monocristalino estándar)
    "panel_area_m2":       2.0,      # Área por panel (m²) — aprox 1m × 2m

    # --- Sistema ---
    "num_paneles":         10,       # Número de paneles → 4 kWp instalados
    "performance_ratio":   0.75,     # PR = 75% (pérdidas típicas: inversor, cableado,
                                     #           temperatura, suciedad, tolerancias)

    # --- Económicos ---
    "tarifa_kwh_cop":      850,      # Tarifa eléctrica media Colombia (COP/kWh)
    "precio_sistema_cop":  18_000_000,  # Costo instalación ~4kWp en Colombia (COP)
    "vida_util_anios":     25,       # Vida útil garantizada del sistema
    "degradacion_anual":   0.005,    # Degradación de paneles: 0.5% por año
}


def calcular_energia_mensual(
    df_solar: pd.DataFrame,
    num_paneles:       int   = DEFAULT_PARAMS["num_paneles"],
    panel_eficiencia:  float = DEFAULT_PARAMS["panel_eficiencia"],
    panel_area_m2:     float = DEFAULT_PARAMS["panel_area_m2"],
    performance_ratio: float = DEFAULT_PARAMS["performance_ratio"],
) -> pd.DataFrame:
    """
    Aplica E = A × r × H × PR para cada mes y retorna el DataFrame
    enriquecido con columnas de energía estimada.

    Parámetros
    ----------
    df_solar          : DataFrame de fetch_solar_data() con columna 'radiacion_kwh'
    num_paneles       : Cantidad de paneles instalados
    panel_eficiencia  : Eficiencia de conversión del panel (0-1)
    panel_area_m2     : Área física de cada panel en m²
    performance_ratio : Factor de rendimiento global del sistema (0-1)

    Retorna
    -------
    df con columnas adicionales:
        - area_total_m2      : Área total del arreglo
        - energia_dia_kwh    : Energía generada por día (kWh/día)
        - energia_mes_kwh    : Energía generada en el mes completo (kWh)
        - energia_mes_kwh    : Energía mensual total
        - ahorro_mes_cop     : Ahorro económico mensual estimado (COP)
    """
    df = df_solar.copy()

    area_total = num_paneles * panel_area_m2

    # E_dia = A × r × H × PR  (kWh por día)
    df["area_total_m2"]   = area_total
    df["energia_dia_kwh"] = (
        area_total * panel_eficiencia * df["radiacion_kwh"] * performance_ratio
    ).round(3)

    # Energía mensual = energía diaria × días del mes
    df["dias_mes"]        = DAYS_PER_MONTH
    df["energia_mes_kwh"] = (df["energia_dia_kwh"] * df["dias_mes"]).round(1)

    return df


def calcular_kpis(
    df_energia: pd.DataFrame,
    tarifa_kwh_cop:    float = DEFAULT_PARAMS["tarifa_kwh_cop"],
    precio_sistema_cop: float = DEFAULT_PARAMS["precio_sistema_cop"],
    vida_util_anios:   int   = DEFAULT_PARAMS["vida_util_anios"],
    degradacion_anual: float = DEFAULT_PARAMS["degradacion_anual"],
    num_paneles:       int   = DEFAULT_PARAMS["num_paneles"],
    panel_potencia_wp: int   = DEFAULT_PARAMS["panel_potencia_wp"],
) -> dict:
    """
    Calcula los KPIs financieros y técnicos del sistema fotovoltaico.

    Retorna
    -------
    dict con:
        Técnicos:
          - potencia_pico_kwp       : Potencia instalada (kWp)
          - energia_anual_kwh       : Generación anual estimada (kWh)
          - energia_diaria_media    : Promedio diario anual (kWh/día)
          - mejor_mes / peor_mes    : Mes más/menos productivo
        Financieros:
          - ahorro_anual_cop        : Ahorro anual en factura (COP)
          - ahorro_mensual_medio    : Ahorro mensual promedio (COP)
          - payback_anios           : Período de retorno de inversión (años)
          - ahorro_vida_util_cop    : Ahorro total en vida útil (COP)
          - roi_pct                 : Retorno sobre inversión (%)
          - co2_evitado_kg_anual    : CO₂ evitado por año (kg)
    """
    energia_anual   = df_energia["energia_mes_kwh"].sum()
    ahorro_anual    = energia_anual * tarifa_kwh_cop
    potencia_kwp    = (num_paneles * panel_potencia_wp) / 1000

    # Ahorro acumulado con degradación año a año
    ahorro_acumulado = sum(
        ahorro_anual * ((1 - degradacion_anual) ** anio)
        for anio in range(vida_util_anios)
    )

    payback = precio_sistema_cop / ahorro_anual if ahorro_anual > 0 else 0
    roi     = ((ahorro_acumulado - precio_sistema_cop) / precio_sistema_cop) * 100

    # Factor de emisión Colombia: ~0.126 kg CO₂/kWh (red eléctrica nacional)
    co2_evitado = energia_anual * 0.126

    mejor_idx = df_energia["energia_mes_kwh"].idxmax()
    peor_idx  = df_energia["energia_mes_kwh"].idxmin()

    return {
        # Técnicos
        "potencia_pico_kwp":     round(potencia_kwp, 2),
        "energia_anual_kwh":     round(energia_anual, 1),
        "energia_diaria_media":  round(df_energia["energia_dia_kwh"].mean(), 2),
        "mejor_mes":             df_energia.loc[mejor_idx, "mes"],
        "mejor_mes_kwh":         round(df_energia.loc[mejor_idx, "energia_mes_kwh"], 1),
        "peor_mes":              df_energia.loc[peor_idx, "mes"],
        "peor_mes_kwh":          round(df_energia.loc[peor_idx, "energia_mes_kwh"], 1),
        # Financieros
        "ahorro_anual_cop":      round(ahorro_anual),
        "ahorro_mensual_medio":  round(ahorro_anual / 12),
        "payback_anios":         round(payback, 1),
        "ahorro_vida_util_cop":  round(ahorro_acumulado),
        "roi_pct":               round(roi, 1),
        # Ambiental
        "co2_evitado_kg_anual":  round(co2_evitado, 1),
    }
