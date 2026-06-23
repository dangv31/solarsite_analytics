"""
data_fetcher.py
Módulo de conexión a la API NASA POWER.
Retorna datos históricos mensuales de radiación, nubosidad y temperatura.
"""

import requests
import pandas as pd
from typing import Optional

NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
NASA_PARAMETERS     = "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,T2M,CLOUD_AMT"

MONTH_NAMES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
]

NASA_MONTH_KEYS = [
    "JAN","FEB","MAR","APR","MAY","JUN",
    "JUL","AUG","SEP","OCT","NOV","DEC"
]

PRESET_CITIES = {
    "Medellín, Colombia":      (6.2442,  -75.5812),
    "Bogotá, Colombia":        (4.7110,  -74.0721),
    "Cali, Colombia":          (3.4516,  -76.5320),
    "Barranquilla, Colombia":  (10.9685, -74.7813),
    "Ciudad de México":        (19.4326, -99.1332),
    "Madrid, España":          (40.4168,  -3.7038),
    "Buenos Aires, Argentina": (-34.6037,-58.3816),
    "Miami, EE.UU.":           (25.7617, -80.1918),
    "Santiago, Chile":         (-33.4489,-70.6693),
}


def fetch_solar_data(
    lat: float,
    lon: float,
    community: str = "RE",
    timeout: int = 30,
) -> Optional[pd.DataFrame]:
    """
    Consulta la API NASA POWER y retorna un DataFrame con datos
    históricos mensuales (climatología) para las coordenadas dadas.
    """
    params = {
        "parameters": NASA_PARAMETERS,
        "community":  community,
        "longitude":  lon,
        "latitude":   lat,
        "format":     "JSON",
    }

    try:
        print(f"[NASA POWER] Consultando datos para lat={lat}, lon={lon}...")
        response = requests.get(NASA_POWER_BASE_URL, params=params, timeout=timeout)
        response.raise_for_status()

    except requests.exceptions.Timeout:
        print("[ERROR] Tiempo de espera agotado. Verifica tu conexión a internet.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP {response.status_code}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error de conexión: {e}")
        return None

    try:
        data       = response.json()
        properties = data["properties"]["parameter"]

        # DEBUG: muestra las claves reales de la API
        print("[DEBUG] Claves del primer parámetro:", list(list(properties.values())[0].keys()))

        radiacion   = properties["ALLSKY_SFC_SW_DWN"]
        radiacion_c = properties["CLRSKY_SFC_SW_DWN"]
        temperatura = properties["T2M"]
        nubosidad   = properties["CLOUD_AMT"]

        records = []
        for i, (nasa_key, month_name) in enumerate(zip(NASA_MONTH_KEYS, MONTH_NAMES), start=1):
            records.append({
                "mes":             month_name,
                "mes_num":         i,
                "radiacion_kwh":   round(radiacion.get(nasa_key, 0), 3),
                "radiacion_clear": round(radiacion_c.get(nasa_key, 0), 3),
                "temperatura_c":   round(temperatura.get(nasa_key, 0), 2),
                "nubosidad_pct":   round(nubosidad.get(nasa_key, 0), 1),
            })

        df = pd.DataFrame(records)
        print(f"[OK] Datos obtenidos: {len(df)} meses.")
        return df

    except (KeyError, TypeError) as e:
        print(f"[ERROR] No se pudo parsear la respuesta de NASA POWER: {e}")
        return None


def get_annual_summary(df: pd.DataFrame) -> dict:
    """Calcula un resumen anual a partir del DataFrame mensual."""
    return {
        "radiacion_anual_kwh": round(df["radiacion_kwh"].sum() * 30.44, 1),
        "radiacion_media_dia": round(df["radiacion_kwh"].mean(), 3),
        "temperatura_media":   round(df["temperatura_c"].mean(), 1),
        "nubosidad_media":     round(df["nubosidad_pct"].mean(), 1),
        "mejor_mes":           df.loc[df["radiacion_kwh"].idxmax(), "mes"],
        "peor_mes":            df.loc[df["radiacion_kwh"].idxmin(), "mes"],
    }


if __name__ == "__main__":
    LAT, LON = 6.2442, -75.5812

    df = fetch_solar_data(LAT, LON)

    if df is not None:
        print("\n=== DataFrame de radiación solar ===")
        print(df.to_string(index=False))

        print("\n=== Resumen Anual ===")
        summary = get_annual_summary(df)
        for k, v in summary.items():
            print(f"  {k:25s}: {v}")
    else:
        print("\n[FALLO] No se obtuvieron datos.")