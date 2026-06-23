"""
energy_calculator.py
Módulo de cálculo fotovoltaico.
Todos los parámetros se leen de config.json.
"""

import json
import pandas as pd
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# Días por mes (sin año bisiesto)
DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def calcular_energia_mensual(
    df_solar: pd.DataFrame,
    num_paneles:       int   = None,
    panel_eficiencia:  float = None,
    panel_area_m2:     float = None,
    performance_ratio: float = None,
) -> pd.DataFrame:
    """
    Aplica E = A × r × H × PR para cada mes.
    Los valores None se toman de config.json.
    """
    cfg = load_config()["sistema"]

    num_paneles       = num_paneles       if num_paneles       is not None else cfg["num_paneles"]
    panel_eficiencia  = panel_eficiencia  if panel_eficiencia  is not None else cfg["panel_eficiencia"]
    panel_area_m2     = panel_area_m2     if panel_area_m2     is not None else cfg["panel_area_m2"]
    performance_ratio = performance_ratio if performance_ratio is not None else cfg["performance_ratio"]

    df = df_solar.copy()
    area_total = num_paneles * panel_area_m2

    df["area_total_m2"]   = area_total
    df["energia_dia_kwh"] = (
        area_total * panel_eficiencia * df["radiacion_kwh"] * performance_ratio
    ).round(3)
    df["dias_mes"]        = DAYS_PER_MONTH
    df["energia_mes_kwh"] = (df["energia_dia_kwh"] * df["dias_mes"]).round(1)

    return df


def calcular_kpis(
    df_energia: pd.DataFrame,
    tarifa_kwh_cop:     float = None,
    precio_sistema_cop: float = None,
    num_paneles:        int   = None,
) -> dict:
    """
    Calcula KPIs técnicos, financieros y ambientales.
    Los valores None se toman de config.json.
    """
    cfg      = load_config()
    cfg_sys  = cfg["sistema"]
    cfg_eco  = cfg["economico"]
    cfg_amb  = cfg["ambiental"]

    tarifa_kwh_cop     = tarifa_kwh_cop     if tarifa_kwh_cop     is not None else cfg_eco["tarifa_kwh_cop"]
    precio_sistema_cop = precio_sistema_cop if precio_sistema_cop is not None else cfg_eco["precio_sistema_cop"]
    num_paneles        = num_paneles        if num_paneles        is not None else cfg_sys["num_paneles"]

    vida_util         = cfg_sys["vida_util_anios"]
    degradacion       = cfg_sys["degradacion_anual"]
    panel_potencia_wp = cfg_sys["panel_potencia_wp"]
    factor_co2        = cfg_amb["factor_emision_co2_kg_kwh"]

    energia_anual  = df_energia["energia_mes_kwh"].sum()
    ahorro_anual   = energia_anual * tarifa_kwh_cop
    potencia_kwp   = (num_paneles * panel_potencia_wp) / 1000

    ahorro_acumulado = sum(
        ahorro_anual * ((1 - degradacion) ** anio)
        for anio in range(vida_util)
    )

    payback = precio_sistema_cop / ahorro_anual if ahorro_anual > 0 else 0
    roi     = ((ahorro_acumulado - precio_sistema_cop) / precio_sistema_cop) * 100

    mejor_idx = df_energia["energia_mes_kwh"].idxmax()
    peor_idx  = df_energia["energia_mes_kwh"].idxmin()

    return {
        "potencia_pico_kwp":    round(potencia_kwp, 2),
        "energia_anual_kwh":    round(energia_anual, 1),
        "energia_diaria_media": round(df_energia["energia_dia_kwh"].mean(), 2),
        "mejor_mes":            df_energia.loc[mejor_idx, "mes"],
        "mejor_mes_kwh":        round(df_energia.loc[mejor_idx, "energia_mes_kwh"], 1),
        "peor_mes":             df_energia.loc[peor_idx, "mes"],
        "peor_mes_kwh":         round(df_energia.loc[peor_idx, "energia_mes_kwh"], 1),
        "ahorro_anual_cop":     round(ahorro_anual),
        "ahorro_mensual_medio": round(ahorro_anual / 12),
        "payback_anios":        round(payback, 1),
        "ahorro_vida_util_cop": round(ahorro_acumulado),
        "roi_pct":              round(roi, 1),
        "co2_evitado_kg_anual": round(energia_anual * factor_co2, 1),
    }