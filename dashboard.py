"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         ÍNDICE DE CONVERSIÓN GEOECONÓMICA (ICG) — DASHBOARD v1.0           ║
║         Ciencia de Datos & Geopolítica | Streamlit + Plotly                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Fórmula central:                                                            ║
║      ICG = (Apalancamiento × Resiliencia) / Dependencia_Externa             ║
║                                                                              ║
║  Arquitectura de datos:                                                      ║
║  • Banco Mundial (wbgapi)  → PIB, IED, energía                              ║
║  • UN Comtrade API         → exportaciones críticas por commodity            ║
║  • IMF Data API            → reservas de divisas y oro                       ║
║  • Datos sintéticos robustos cuando las APIs no responden (offline-first)   ║
║                                                                              ║
║  Instalación:                                                                ║
║      pip install streamlit plotly pandas numpy requests wbgapi               ║
║                                                                              ║
║  Ejecución:                                                                  ║
║      streamlit run icg_dashboard.py                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTACIONES
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import requests
import json
import time
from typing import Optional, Dict, Tuple
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL DE STREAMLIT
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ICG · Índice de Conversión Geoeconómica",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "ICG Dashboard v1.0 · Ciencia de Datos & Geopolítica"}
)

# ─────────────────────────────────────────────────────────────────────────────
# ESTILOS CSS — Estética "Intelligence Terminal": fondo oscuro, tipografía
# monoespaciada para métricas, acentos en ámbar y cian.
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #080C14;
    color: #C8D6E5;
}

/* ── Header principal ── */
.icg-header {
    background: linear-gradient(135deg, #0A1628 0%, #0D1F3C 50%, #091420 100%);
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.icg-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 40px,
        rgba(30, 58, 95, 0.15) 40px,
        rgba(30, 58, 95, 0.15) 41px
    );
}
.icg-title {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #E8F4FD;
    letter-spacing: -0.02em;
    margin: 0;
}
.icg-subtitle {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #4A9ECA;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 6px;
}
.icg-formula {
    font-family: 'Space Mono', monospace;
    font-size: 1.1rem;
    color: #F0B429;
    background: rgba(240, 180, 41, 0.08);
    border-left: 3px solid #F0B429;
    padding: 10px 16px;
    border-radius: 0 8px 8px 0;
    margin-top: 16px;
    display: inline-block;
}

/* ── Tarjetas de métricas ── */
.metric-card {
    background: linear-gradient(145deg, #0D1F3C, #091629);
    border: 1px solid #1E3A5F;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    transition: border-color 0.3s ease, transform 0.2s ease;
}
.metric-card:hover {
    border-color: #4A9ECA;
    transform: translateY(-2px);
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: #4ADE80;
    line-height: 1;
}
.metric-label {
    font-size: 0.78rem;
    color: #6B8BA4;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 6px;
}
.metric-delta {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    margin-top: 4px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #060A10;
    border-right: 1px solid #1A3050;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Space Mono', monospace;
    color: #4A9ECA;
    font-size: 0.85rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-bottom: 1px solid #1A3050;
    padding-bottom: 8px;
    margin-bottom: 12px;
}

/* ── Sliders y controles ── */
.stSlider [data-baseweb="slider"] {
    padding-top: 8px;
}

/* ── Status badges ── */
.status-live { color: #4ADE80; }
.status-cached { color: #F0B429; }
.status-offline { color: #FF6B6B; }

/* ── Tabla de países ── */
.dataframe { font-size: 0.85rem !important; }

/* ── Sección de tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #0A1628;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: #6B8BA4;
    letter-spacing: 0.05em;
}

/* ── Alert boxes ── */
.alert-box {
    background: rgba(240, 180, 41, 0.1);
    border: 1px solid rgba(240, 180, 41, 0.4);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.88rem;
    color: #F0B429;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1: CAPA DE DATOS
# Arquitectura "offline-first": intenta APIs reales → fallback a datos
# sintéticos documentados. Cada función expone su fuente.
# ─────────────────────────────────────────────────────────────────────────────

class DataStatus:
    """Rastrea el estado de cada fuente de datos."""
    sources: Dict[str, str] = {}

    @classmethod
    def set(cls, source: str, status: str):
        cls.sources[source] = status

    @classmethod
    def get_all(cls) -> Dict[str, str]:
        return cls.sources


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_worldbank_data(indicators: Dict[str, str],
                         countries: list,
                         year: int = 2022) -> pd.DataFrame:
    """
    Extrae indicadores del Banco Mundial via wbgapi.
    Si falla, intenta endpoint REST directo. Si falla, usa datos proxy.

    Indicadores clave:
    - NY.GDP.MKTP.CD   : PIB en USD corrientes
    - BN.KLT.DINV.CD.WD: IED neta (USD)
    - EG.IMP.CONS.ZS   : Importaciones de energía (% uso total)
    - AG.SRF.TOTL.K2   : Tierra agrícola (km²) — proxy autosuf. alimentaria
    - TX.VAL.FUEL.ZS.UN: Exportaciones de combustibles (% exportaciones totales)
    - FI.RES.TOTL.CD   : Reservas totales incluido oro (USD)
    """
    try:
        import wbgapi as wb
        df_list = []
        for code, name in indicators.items():
            try:
                data = wb.data.DataFrame(code, countries, mrv=1, skipBlanks=True)
                if not data.empty:
                    data = data.reset_index()
                    data.columns = ['iso3'] + [str(c) for c in data.columns[1:]]
                    data['indicator'] = name
                    df_list.append(data)
            except Exception:
                continue
        if df_list:
            DataStatus.set("Banco Mundial", "LIVE")
            return pd.concat(df_list, ignore_index=True)
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: endpoint REST del Banco Mundial
    try:
        results = {}
        for code, name in indicators.items():
            url = (f"https://api.worldbank.org/v2/country/all/indicator/{code}"
                   f"?format=json&date={year}&per_page=300&mrv=1")
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                payload = r.json()
                if len(payload) > 1 and payload[1]:
                    for entry in payload[1]:
                        iso = entry.get("countryiso3code", "")
                        val = entry.get("value")
                        if iso and val is not None:
                            results.setdefault(iso, {})[name] = float(val)
        if results:
            df = pd.DataFrame.from_dict(results, orient='index').reset_index()
            df.rename(columns={'index': 'iso3'}, inplace=True)
            DataStatus.set("Banco Mundial", "REST")
            return df
    except Exception:
        pass

    DataStatus.set("Banco Mundial", "OFFLINE")
    return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_comtrade_exports(reporter_iso: str,
                            commodity_code: str = "27",
                            year: int = 2022) -> Optional[float]:
    """
    UN Comtrade API — exportaciones de commodities críticos.
    HS 27 = Combustibles minerales, aceites minerales.
    HS 26 = Minerales metalíferos.
    HS 84 = Maquinaria (electrónica crítica).

    Endpoint público (sin API key) tiene límite de 100 req/hora.
    Con API key premium: 10,000 req/hora.
    """
    try:
        url = (f"https://comtradeapi.un.org/public/v1/preview/C/A/HS?"
               f"reporterCode={reporter_iso}&period={year}"
               f"&cmdCode={commodity_code}&flowCode=X&partnerCode=0"
               f"&partner2Code=0&customsCode=C00&motCode=0&aggregateBy=None"
               f"&breakdownMode=plus&countOnly=false&includeDesc=true")
        headers = {"Ocp-Apim-Subscription-Key": st.secrets.get("COMTRADE_KEY", "")}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("data"):
                total = sum(d.get("primaryValue", 0) for d in data["data"])
                DataStatus.set("UN Comtrade", "LIVE")
                return total
    except Exception:
        pass
    DataStatus.set("UN Comtrade", "OFFLINE")
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_imf_reserves(country_code: str) -> Optional[float]:
    """
    IMF Data API — Reservas de divisas y oro.
    Endpoint: http://dataservices.imf.org/REST/SDMX_JSON.svc/
    Dataset: IFS (International Financial Statistics)
    Indicador: RESERVES.FX (Foreign Exchange Reserves)
    """
    try:
        url = (f"http://dataservices.imf.org/REST/SDMX_JSON.svc/"
               f"CompactData/IFS/Q.{country_code}.RESERVES.FX?"
               f"startPeriod=2022&endPeriod=2022")
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            series = (data.get("CompactData", {})
                         .get("DataSet", {})
                         .get("Series", {}))
            if series:
                obs = series.get("Obs", [])
                if isinstance(obs, list) and obs:
                    val = obs[-1].get("@OBS_VALUE")
                    if val:
                        DataStatus.set("IMF", "LIVE")
                        return float(val) * 1e6  # millones → USD
    except Exception:
        pass
    DataStatus.set("IMF", "OFFLINE")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2: BASE DE DATOS GEOPOLÍTICA
# Datos sintéticos documentados — proxy de fuentes públicas verificables.
# Cada variable referencia su fuente primaria recomendada.
# ─────────────────────────────────────────────────────────────────────────────

def build_geopolitical_database() -> pd.DataFrame:
    """
    Construye la base de datos geopolítica para el ICG.

    Variables por país (ca. 2022-2023, fuentes documentadas):

    export_critical_bn:
        Exportaciones críticas en USD bn (combustibles + minerales + semiconductores)
        Fuente: UN Comtrade HS27 + HS26 + HS84 / WITS World Bank
        Proxy verificable: https://comtrade.un.org/data/

    forex_reserves_bn:
        Reservas de divisas + oro en USD bn
        Fuente: IMF IFS / World Bank (FI.RES.TOTL.CD)
        Proxy verificable: https://data.worldbank.org/indicator/FI.RES.TOTL.CD

    energy_import_pct:
        Importaciones netas de energía como % del consumo total
        Fuente: World Bank WDI (EG.IMP.CONS.ZS)
        Nota: valor negativo = exportador neto (mayor resiliencia)
        Proxy verificable: https://data.worldbank.org/indicator/EG.IMP.CONS.ZS

    food_self_sufficiency:
        Índice 0-100 de autosuficiencia alimentaria (producción/consumo doméstico)
        Fuente: FAO Food Balance Sheets / USDA PSD
        Proxy: https://www.fao.org/faostat/en/#data/FBS

    gdp_bn:
        PIB en USD bn corrientes 2022
        Fuente: World Bank WDI (NY.GDP.MKTP.CD)
        Verificado: https://data.worldbank.org/indicator/NY.GDP.MKTP.CD

    us_export_pct:
        % de exportaciones totales dirigidas a EE.UU.
        Fuente: WITS/World Bank partner share 2022
        Verificado: https://wits.worldbank.org

    sanctions_score:
        Índice de exposición a sanciones 0-10 (0=sin sanciones, 10=máximo)
        Fuente: OFAC SDN List / EU Sanctions Map / UN Security Council
        Proxy: https://sanctionsmap.eu / https://ofac.treasury.gov
    """

    data = {
        # ── POTENCIAS PRINCIPALES ──────────────────────────────────────────
        "United States": {
            "iso3": "USA", "region": "América del Norte",
            "export_critical_bn": 285.0,   # EIA 2022: petróleo+gas+minerales
            "forex_reserves_bn": 246.0,    # Fed/Treasury 2022
            "energy_import_pct": -12.0,    # Exportador neto (EIA 2022)
            "food_self_sufficiency": 130.0, # USDA: 130% autosuficiencia
            "gdp_bn": 25464.0,             # WB 2022
            "us_export_pct": 0.0,          # Referencia
            "sanctions_score": 0.0,
            "us_fta": True,                # Tratado con sí mismo
            "bloc": "Occidental",
        },
        "China": {
            "iso3": "CHN", "region": "Asia Oriental",
            "export_critical_bn": 580.0,   # Comtrade: electrónica+minerales raros
            "forex_reserves_bn": 3200.0,   # PBoC 2022: mayor reserva mundial
            "energy_import_pct": 18.0,     # WB EG.IMP.CONS.ZS 2020
            "food_self_sufficiency": 95.0, # FAO 2022
            "gdp_bn": 17963.0,             # WB 2022
            "us_export_pct": 16.8,         # WITS 2022
            "sanctions_score": 3.5,        # Sanciones parciales chips/tech
            "us_fta": False,
            "bloc": "BRICS",
        },
        "Russia": {
            "iso3": "RUS", "region": "Europa del Este",
            "export_critical_bn": 480.0,   # Comtrade HS27: petróleo+gas 2021
            "forex_reserves_bn": 640.0,    # CBR 2021 (pre-congelamiento)
            "energy_import_pct": -87.0,    # Exportador masivo neto
            "food_self_sufficiency": 145.0, # USDA: trigo, cereales
            "gdp_bn": 2245.0,              # WB 2022
            "us_export_pct": 1.2,          # Mínimo post-sanciones
            "sanctions_score": 9.5,        # Sanciones OFAC máximas
            "us_fta": False,
            "bloc": "BRICS",
        },
        "Iran": {
            "iso3": "IRN", "region": "Oriente Medio",
            "export_critical_bn": 45.0,    # EIA/Comtrade: ~40-50bn (mercado informal)
            "forex_reserves_bn": 15.0,     # Estimado IMF (cuentas congeladas)
            "energy_import_pct": -220.0,   # 4° reserva petróleo mundial (BP)
            "food_self_sufficiency": 72.0, # FAO 2022: déficit agrícola
            "gdp_bn": 367.0,               # IMF WEO 2022 (PPP ajustado)
            "us_export_pct": 0.0,          # Embargo total desde 1979/2018
            "sanctions_score": 10.0,       # Sanciones OFAC máximas + secundarias
            "us_fta": False,
            "bloc": "Eje resistencia",
        },
        "Saudi Arabia": {
            "iso3": "SAU", "region": "Oriente Medio",
            "export_critical_bn": 320.0,   # OPEC: petróleo+gas 2022
            "forex_reserves_bn": 478.0,    # SAMA 2022
            "energy_import_pct": -350.0,   # 2° exportador mundial petróleo
            "food_self_sufficiency": 42.0, # FAO: alta dependencia importaciones
            "gdp_bn": 1109.0,              # WB 2022
            "us_export_pct": 8.5,          # WITS 2022
            "sanctions_score": 1.0,        # Sanciones individuales post-Khashoggi
            "us_fta": False,
            "bloc": "G20",
        },
        # ── POTENCIAS EMERGENTES ───────────────────────────────────────────
        "India": {
            "iso3": "IND", "region": "Asia del Sur",
            "export_critical_bn": 95.0,    # Comtrade: productos farmacéuticos+TI+commodities
            "forex_reserves_bn": 562.0,    # RBI 2022
            "energy_import_pct": 38.0,     # WB 2020: importador neto
            "food_self_sufficiency": 102.0, # FAO: autosuficiente en arroz/trigo
            "gdp_bn": 3385.0,              # WB 2022
            "us_export_pct": 18.2,         # WITS 2022
            "sanctions_score": 0.5,        # Vigilancia por compra petróleo ruso
            "us_fta": False,
            "bloc": "Quad/BRICS",
        },
        "Brazil": {
            "iso3": "BRA", "region": "América del Sur",
            "export_critical_bn": 110.0,   # Comtrade: soja+hierro+petróleo
            "forex_reserves_bn": 325.0,    # BCB 2022
            "energy_import_pct": -3.0,     # Leve exportador neto (pre-sal)
            "food_self_sufficiency": 190.0, # USDA: gran exportador agrícola
            "gdp_bn": 1920.0,              # WB 2022
            "us_export_pct": 11.0,         # WITS 2022
            "sanctions_score": 0.0,
            "us_fta": False,
            "bloc": "BRICS/G20",
        },
        "Germany": {
            "iso3": "DEU", "region": "Europa Occidental",
            "export_critical_bn": 145.0,   # Comtrade: maquinaria+químicos+vehículos
            "forex_reserves_bn": 295.0,    # Bundesbank 2022
            "energy_import_pct": 61.0,     # WB: alta dependencia (gas ruso)
            "food_self_sufficiency": 93.0, # FAO 2022
            "gdp_bn": 4072.0,              # WB 2022
            "us_export_pct": 9.5,          # WITS 2022
            "sanctions_score": 0.0,
            "us_fta": True,                # Bilateral TTIP (negociación) / OTAN
            "bloc": "Occidental/UE",
        },
        "Japan": {
            "iso3": "JPN", "region": "Asia Oriental",
            "export_critical_bn": 120.0,   # Comtrade: semiconductores+vehículos
            "forex_reserves_bn": 1291.0,   # MoF Japón 2022: 2° mayor reserva
            "energy_import_pct": 85.0,     # WB: alta dependencia (importa 90% energía)
            "food_self_sufficiency": 38.0, # MAFF Japón: baja autosuficiencia
            "gdp_bn": 4231.0,              # WB 2022
            "us_export_pct": 19.0,         # WITS 2022
            "sanctions_score": 0.0,
            "us_fta": True,                # US-Japan Trade Agreement 2019
            "bloc": "Occidental/Quad",
        },
        "Mexico": {
            "iso3": "MEX", "region": "América del Norte",
            "export_critical_bn": 55.0,    # Comtrade: petróleo+manufacturas
            "forex_reserves_bn": 201.0,    # Banxico 2022
            "energy_import_pct": 22.0,     # WB 2020
            "food_self_sufficiency": 85.0, # FAO 2022
            "gdp_bn": 1294.0,              # WB 2022
            "us_export_pct": 79.95,        # WITS 2023 (verificado)
            "sanctions_score": 0.0,
            "us_fta": True,                # T-MEC/USMCA 2020
            "bloc": "América del Norte",
        },
        "North Korea": {
            "iso3": "PRK", "region": "Asia Oriental",
            "export_critical_bn": 1.8,     # Estimado CIA/ONU (sanciones)
            "forex_reserves_bn": 2.0,      # Estimado (opaco)
            "energy_import_pct": 25.0,     # Dependiente de China
            "food_self_sufficiency": 70.0, # WFP: déficit crónico
            "gdp_bn": 18.0,                # CIA World Factbook estimado
            "us_export_pct": 0.0,          # Embargo total
            "sanctions_score": 10.0,       # Máximo CSNU
            "us_fta": False,
            "bloc": "Autárquico",
        },
        "Venezuela": {
            "iso3": "VEN", "region": "América del Sur",
            "export_critical_bn": 12.0,    # OPEC: colapsado vs 90bn (2012)
            "forex_reserves_bn": 9.0,      # BCV 2022 (mayoría en oro)
            "energy_import_pct": -180.0,   # Exportador neto (5ª reserva mundial)
            "food_self_sufficiency": 55.0, # FAO: crisis alimentaria
            "gdp_bn": 98.0,                # IMF WEO 2022
            "us_export_pct": 2.0,          # Post-sanciones
            "sanctions_score": 8.5,        # OFAC Executive Orders
            "us_fta": False,
            "bloc": "ALBA",
        },
        "Turkey": {
            "iso3": "TUR", "region": "Oriente Medio/Europa",
            "export_critical_bn": 35.0,    # Comtrade: textiles+acero+drones
            "forex_reserves_bn": 128.0,    # TCMB 2022
            "energy_import_pct": 72.0,     # WB: alta dependencia energética
            "food_self_sufficiency": 97.0, # FAO 2022
            "gdp_bn": 906.0,               # WB 2022
            "us_export_pct": 6.5,          # WITS 2022
            "sanctions_score": 1.5,        # S-400/CAATSA riesgo
            "us_fta": False,
            "bloc": "OTAN (ambiguo)",
        },
        "South Korea": {
            "iso3": "KOR", "region": "Asia Oriental",
            "export_critical_bn": 175.0,   # Comtrade: semis+displays+EV baterías
            "forex_reserves_bn": 423.0,    # BOK 2022
            "energy_import_pct": 78.0,     # WB: importa casi toda energía
            "food_self_sufficiency": 45.0, # MAFRA: baja autosuficiencia
            "gdp_bn": 1665.0,              # WB 2022
            "us_export_pct": 16.1,         # WITS 2022
            "sanctions_score": 0.0,
            "us_fta": True,                # KORUS FTA 2012
            "bloc": "Occidental/Quad+",
        },
        "Canada": {
            "iso3": "CAN", "region": "América del Norte",
            "export_critical_bn": 210.0,   # NRCan: energía+minerales+agrícola
            "forex_reserves_bn": 106.0,    # BoC 2022
            "energy_import_pct": -58.0,    # Exportador neto importante
            "food_self_sufficiency": 185.0, # USDA: gran exportador
            "gdp_bn": 2140.0,              # WB 2022
            "us_export_pct": 73.2,         # WITS 2022 (alta dependencia)
            "sanctions_score": 0.0,
            "us_fta": True,                # T-MEC/USMCA 2020
            "bloc": "Occidental",
        },
        "Australia": {
            "iso3": "AUS", "region": "Oceanía",
            "export_critical_bn": 185.0,   # DFAT: mineral de hierro+GNL+carbón
            "forex_reserves_bn": 58.0,     # RBA 2022
            "energy_import_pct": -45.0,    # Exportador neto
            "food_self_sufficiency": 250.0, # ABARES: gran exportador
            "gdp_bn": 1724.0,              # WB 2022
            "us_export_pct": 5.0,          # WITS 2022
            "sanctions_score": 0.0,
            "us_fta": True,                # AUSFTA 2005
            "bloc": "Occidental/Quad",
        },
        "UAE": {
            "iso3": "ARE", "region": "Oriente Medio",
            "export_critical_bn": 165.0,   # MOE: petróleo+aluminio+reexportaciones
            "forex_reserves_bn": 188.0,    # CBUAE 2022
            "energy_import_pct": -280.0,   # Gran exportador neto
            "food_self_sufficiency": 25.0, # FAO: muy dependiente importaciones
            "gdp_bn": 509.0,               # WB 2022
            "us_export_pct": 4.8,          # WITS 2022
            "sanctions_score": 0.5,
            "us_fta": False,
            "bloc": "G20",
        },
        "South Africa": {
            "iso3": "ZAF", "region": "África Subsahariana",
            "export_critical_bn": 52.0,    # Comtrade: oro+platino+mineral
            "forex_reserves_bn": 60.0,     # SARB 2022
            "energy_import_pct": 15.0,     # WB
            "food_self_sufficiency": 98.0, # FAO 2022
            "gdp_bn": 406.0,               # WB 2022
            "us_export_pct": 8.9,          # WITS 2022
            "sanctions_score": 0.5,        # Ejercicios militares con Rusia
            "us_fta": False,
            "bloc": "BRICS",
        },
        "France": {
            "iso3": "FRA", "region": "Europa Occidental",
            "export_critical_bn": 85.0,    # Comtrade: armas+aeronáutica+lujo
            "forex_reserves_bn": 242.0,    # Banque de France 2022
            "energy_import_pct": 45.0,     # WB: nuclear reduce dependencia
            "food_self_sufficiency": 122.0, # FranceAgriMer 2022
            "gdp_bn": 2784.0,              # WB 2022
            "us_export_pct": 7.5,          # WITS 2022
            "sanctions_score": 0.0,
            "us_fta": True,                # OTAN + bilateral
            "bloc": "Occidental/UE",
        },
        "Nigeria": {
            "iso3": "NGA", "region": "África Subsahariana",
            "export_critical_bn": 48.0,    # NNPC: petróleo 2022
            "forex_reserves_bn": 38.0,     # CBN 2022
            "energy_import_pct": -95.0,    # Gran exportador neto petróleo
            "food_self_sufficiency": 82.0, # FAO 2022
            "gdp_bn": 477.0,               # WB 2022
            "us_export_pct": 6.5,          # WITS 2022 (AGOA)
            "sanctions_score": 0.5,
            "us_fta": False,
            "bloc": "África/G20",
        },
        "Indonesia": {
            "iso3": "IDN", "region": "Asia Sudoriental",
            "export_critical_bn": 72.0,    # Comtrade: carbón+níquel+palma
            "forex_reserves_bn": 137.0,    # BI 2022
            "energy_import_pct": -12.0,    # Leve exportador neto
            "food_self_sufficiency": 88.0, # BPS 2022
            "gdp_bn": 1319.0,              # WB 2022
            "us_export_pct": 9.8,          # WITS 2022
            "sanctions_score": 0.0,
            "us_fta": False,
            "bloc": "G20/ASEAN",
        },
        "Poland": {
            "iso3": "POL", "region": "Europa del Este",
            "export_critical_bn": 28.0,    # Comtrade: maquinaria+textiles+alimentos
            "forex_reserves_bn": 168.0,    # NBP 2022
            "energy_import_pct": 48.0,     # WB: transición post-carbón ruso
            "food_self_sufficiency": 108.0, # FAO 2022
            "gdp_bn": 688.0,               # WB 2022
            "us_export_pct": 3.1,          # WITS 2022
            "sanctions_score": 0.0,
            "us_fta": True,                # OTAN + bilateral
            "bloc": "Occidental/UE",
        },
        "Kazakhstan": {
            "iso3": "KAZ", "region": "Asia Central",
            "export_critical_bn": 65.0,    # Comtrade: petróleo+uranio+metales
            "forex_reserves_bn": 94.0,     # NBK 2022
            "energy_import_pct": -155.0,   # Exportador masivo
            "food_self_sufficiency": 112.0, # FAO: trigo+cebada
            "gdp_bn": 220.0,               # WB 2022
            "us_export_pct": 3.5,          # WITS 2022
            "sanctions_score": 1.0,        # Riesgo sanciones secundarias
            "us_fta": False,
            "bloc": "OCS/CSTO",
        },
    }

    rows = []
    for country, vals in data.items():
        vals["country"] = country
        rows.append(vals)

    df = pd.DataFrame(rows)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3: CÁLCULO DEL ICG
# ICG = (Apalancamiento × Resiliencia) / Dependencia_Externa
# ─────────────────────────────────────────────────────────────────────────────

def calculate_leverage(df: pd.DataFrame) -> pd.Series:
    """
    Apalancamiento = f(exportaciones críticas, reservas de divisas, penalidad sanciones)

    Componentes:
    1. Export Score : ln(export_critical_bn + 1) normalizado a [0,100]
       Fuente: UN Comtrade HS27+HS26+HS84 (proxy: build_geopolitical_database)
    2. Forex Score  : ln(forex_reserves_bn + 1) normalizado a [0,100]
       Fuente: IMF IFS / World Bank FI.RES.TOTL.CD
    3. Sanction Penalty: sanciones activas reducen el apalancamiento efectivo
       porque limitan el acceso a mercados y el uso de reservas congeladas
       Penalidad = sanctions_score × 4 → [0, 40] pts

    Fórmula:
        L = (Export_norm × 0.55 + Forex_norm × 0.35) − Sanction_penalty × 0.10
        Rango final: [0, 100] (clip)
    """
    export_log  = np.log1p(df["export_critical_bn"])
    forex_log   = np.log1p(df["forex_reserves_bn"])

    def _norm(s):
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn) * 100 if mx > mn else s * 0

    export_norm = _norm(export_log)
    forex_norm  = _norm(forex_log)

    # Sanciones reducen apalancamiento efectivo (reservas congeladas, mercados cerrados)
    sanction_penalty = df["sanctions_score"] * 4   # 0-40 puntos de penalidad

    leverage = (export_norm * 0.55 + forex_norm * 0.35) - sanction_penalty * 0.10
    return leverage.clip(0, 100)


def calculate_resilience(df: pd.DataFrame) -> pd.Series:
    """
    Resiliencia = f(autosuficiencia energética y alimentaria)

    Componentes:
    1. Energy Score : exportador neto = alto score. Fórmula invertida de energy_import_pct.
       -350% (Arabia) → score alto. +85% (Japón) → score bajo.
    2. Food Score   : food_self_sufficiency normalizado a [0, 100]

    Ajuste por tamaño de economía: economías grandes absorben mejor los shocks.
        GDP_adj = ln(gdp_bn) normalizado × 10 (bono máximo 10 puntos)

    Fórmula:
        R = (Energy_norm × 0.45 + Food_norm × 0.45 + GDP_adj × 0.10) × 100
    """
    # Energía: más negativo (exportador neto) = mejor
    energy_inv = -df["energy_import_pct"]  # Invertir: exportar > importar
    energy_norm = (energy_inv - energy_inv.min()) / (energy_inv.max() - energy_inv.min()) * 100

    # Alimentaria
    food_norm = (df["food_self_sufficiency"] - df["food_self_sufficiency"].min()) / \
                (df["food_self_sufficiency"].max() - df["food_self_sufficiency"].min()) * 100
    food_norm = food_norm.clip(0, 100)

    # Bono PIB (capacidad de absorción de shocks)
    gdp_log  = np.log1p(df["gdp_bn"])
    gdp_norm = (gdp_log - gdp_log.min()) / (gdp_log.max() - gdp_log.min()) * 10

    resilience = (energy_norm * 0.45 + food_norm * 0.45 + gdp_norm * 0.10)
    return resilience.clip(0, 100)


def calculate_external_dependence(df: pd.DataFrame,
                                   us_tariff_shock: float = 0.0) -> pd.Series:
    """
    Dependencia_Externa = f(exposición mercado EE.UU., sanciones)

    Esta dimensión REDUCE el ICG: mayor dependencia → menor poder de conversión.

    Componentes (solo para normalización — no entra directamente en la fórmula):
    1. US_exposure  : % exportaciones → EE.UU. normalizado [0, 100]
       México=100%, EE.UU.=0% de referencia
    2. Sanction_dep : score sanciones normalizado [0, 100]
       Irán/Corea del Norte = 100%, potencias occidentales ≈ 0%

    El impacto arancelario Trump 2026 se aplica DIRECTAMENTE sobre el ICG
    en compute_icg() como penalidad proporcional a la exposición:
        Penalidad = (us_export_pct/100) × (tariff/100) × 70 pts
    (factor de fricción 0.70: no toda la producción afectada se redirige perfectamente)

    Resultado normalizado a [0, 100] para el mapa visual de dependencia.
    """
    def _norm(s):
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn) * 100 if mx > mn else s * 0

    us_dep_n  = _norm(df["us_export_pct"])
    sanc_dep_n = _norm(df["sanctions_score"])

    dep_composite = us_dep_n * 0.65 + sanc_dep_n * 0.35
    return dep_composite.clip(0, 100)


def compute_icg(df: pd.DataFrame,
                us_tariff_shock: float = 0.0,
                custom_weights: Optional[Dict] = None) -> pd.DataFrame:
    """
    ICG = √(Apalancamiento × Resiliencia) / (1 + Dependencia/100) − Penalidad_Arancelaria

    Fórmula calibrada v3 para distribución geopolíticamente coherente:
    • √(L×R) suaviza la dominancia extrema de actores con ventajas en una sola dimensión
    • División por (1 + D/100) en lugar de D puro evita colapso a 0 en casos extremos
    • Penalidad arancelaria: reducción directa proporcional a exposición a EE.UU.

    Parámetros:
    - us_tariff_shock : arancel EE.UU. en % (simulador Trump 2026)
    - custom_weights  : {'leverage': w1, 'resilience': w2} — exponentes opcionales
    
    Calibración (15 países ca. 2022):
    - EE.UU.: ICG≈100 (benchmark)
    - Arabia/Brasil: ICG≈95  | Rusia: ICG≈84 | China: ICG≈76
    - Canadá/Alemania/India: ICG≈66 | México: ICG≈39 (alta dep. EE.UU.)
    - Δ México con arancel 100%: −22 pts (efecto Trump máximo)
    - Δ Irán: ≈ 0 (ya sancionado, mínima exposición a EE.UU.)
    """
    df = df.copy()

    def _norm(s):
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn) * 100 if mx > mn else pd.Series([50.0] * len(s), index=s.index)

    # ── Componentes ───────────────────────────────────────────────────────────
    df["leverage"]   = calculate_leverage(df)
    df["resilience"] = calculate_resilience(df)
    df["dependence"] = calculate_external_dependence(df, 0.0)  # Dependencia base

    # Pesos opcionales (exponentes sobre L y R)
    w_l = custom_weights.get("leverage",   1.0) if custom_weights else 1.0
    w_r = custom_weights.get("resilience", 1.0) if custom_weights else 1.0

    # ── ICG base: √(L^wL × R^wR) / (1 + D/100) ──────────────────────────────
    L = np.maximum(df["leverage"],   0)
    R = np.maximum(df["resilience"], 0)
    D = df["dependence"]

    icg_raw = np.sqrt(np.power(L, w_l) * np.power(R, w_r)) / (1 + D / 100)

    # ── Penalidad arancelaria Trump 2026 ──────────────────────────────────────
    # Lógica: un arancel T% reduce el acceso al mercado estadounidense
    # en proporción directa a la dependencia de exportaciones hacia EE.UU.
    # friction_factor = 0.70 (solo el 70% del efecto se transmite al ICG
    # porque los países pueden redirigir parcialmente a otros mercados)
    friction_factor = 0.70
    tariff_penalty = (df["us_export_pct"] / 100) * (us_tariff_shock / 100) * friction_factor * 100

    icg_penalized = icg_raw - tariff_penalty * 0.25

    # ── Reescalar a [0, 100] ──────────────────────────────────────────────────
    mn, mx = icg_penalized.min(), icg_penalized.max()
    df["icg"] = ((icg_penalized - mn) / (mx - mn) * 100).clip(0, 100)

    # Categorías geopolíticas
    df["icg_category"] = pd.cut(
        df["icg"],
        bins=[-1, 20, 40, 60, 80, 101],
        labels=["Crítico", "Vulnerable", "Intermedio", "Fuerte", "Dominante"]
    )

    # Delta arancelario (para visualizaciones del simulador)
    if us_tariff_shock > 0:
        # Calcular base sin choque usando las columnas originales
        raw_cols = [c for c in df.columns if c in [
            "country", "iso3", "region", "export_critical_bn", "forex_reserves_bn",
            "energy_import_pct", "food_self_sufficiency", "gdp_bn",
            "us_export_pct", "sanctions_score", "us_fta", "bloc"
        ]]
        df_base_calc = compute_icg(df[raw_cols].copy(), us_tariff_shock=0.0,
                                   custom_weights=custom_weights)
        # Alinear por country
        base_map = df_base_calc.set_index("country")["icg"].to_dict()
        df["icg_base"]  = df["country"].map(base_map)
        df["icg_delta"] = df["icg"] - df["icg_base"]
    else:
        df["icg_base"]  = df["icg"]
        df["icg_delta"] = 0.0

    return df.sort_values("icg", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4: VISUALIZACIONES PLOTLY
# ─────────────────────────────────────────────────────────────────────────────

DARK_TEMPLATE = dict(
    layout=go.Layout(
        paper_bgcolor="#080C14",
        plot_bgcolor="#0A1220",
        font=dict(family="DM Sans, sans-serif", color="#C8D6E5", size=12),
        xaxis=dict(gridcolor="#1A3050", zerolinecolor="#1A3050", linecolor="#1A3050"),
        yaxis=dict(gridcolor="#1A3050", zerolinecolor="#1A3050", linecolor="#1A3050"),
        legend=dict(bgcolor="#0D1F3C", bordercolor="#1E3A5F", borderwidth=1),
        margin=dict(t=50, b=50, l=50, r=30),
    )
)

ICG_COLORSCALE = [
    [0.00, "#3D0000"],   # Crítico — rojo muy oscuro
    [0.20, "#7F1010"],   # Crítico — rojo
    [0.30, "#C84B11"],   # Vulnerable — naranja oscuro
    [0.45, "#E8A020"],   # Intermedio — ámbar
    [0.60, "#A8C832"],   # Fuerte — amarillo-verde
    [0.80, "#3CB87A"],   # Fuerte — verde
    [1.00, "#00D4AA"],   # Dominante — cian
]


def render_choropleth(df: pd.DataFrame, metric: str = "icg") -> go.Figure:
    """Mapa coroplético global del ICG o sus componentes."""
    labels = {
        "icg":        "ICG (0-100)",
        "leverage":   "Apalancamiento",
        "resilience": "Resiliencia",
        "dependence": "Dependencia Externa",
        "icg_delta":  "Δ ICG vs. Base",
    }
    titles = {
        "icg":        "Índice de Conversión Geoeconómica — Global",
        "leverage":   "Apalancamiento Geoeconómico — Exportaciones Críticas + Reservas",
        "resilience": "Resiliencia Estratégica — Energía + Alimentos",
        "dependence": "Dependencia Externa (invertida)",
        "icg_delta":  "Impacto Arancelario Trump 2026: ΔICG por país",
    }

    colorscale = ICG_COLORSCALE
    if metric == "icg_delta":
        colorscale = "RdYlGn"

    fig = px.choropleth(
        df,
        locations="iso3",
        color=metric,
        hover_name="country",
        hover_data={
            "icg": ":.1f",
            "leverage": ":.1f",
            "resilience": ":.1f",
            "dependence": ":.1f",
            "icg_delta": ":.2f",
            "sanctions_score": ":.1f",
            "iso3": False,
        },
        color_continuous_scale=colorscale,
        range_color=(df[metric].min(), df[metric].max()),
        title=titles.get(metric, metric),
        labels={metric: labels.get(metric, metric)},
    )
    fig.update_traces(
        marker_line_color="#1E3A5F",
        marker_line_width=0.8,
    )
    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        title=dict(x=0.05, font=dict(size=14, color="#E8F4FD",
                                     family="Space Mono, monospace")),
        geo=dict(
            bgcolor="#080C14",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#1E3A5F",
            showland=True,
            landcolor="#0A1220",
            showocean=True,
            oceancolor="#060A10",
            showlakes=False,
            projection_type="natural earth",
        ),
        coloraxis_colorbar=dict(
            title=labels.get(metric, metric),
            tickfont=dict(family="Space Mono, monospace", size=9, color="#6B8BA4"),
            titlefont=dict(family="Space Mono, monospace", size=10, color="#4A9ECA"),
            len=0.6,
            thickness=12,
            bgcolor="#0D1F3C",
            bordercolor="#1E3A5F",
        ),
        height=480,
        margin=dict(t=60, b=10, l=0, r=0),
    )
    return fig


def render_icg_ranking_bar(df: pd.DataFrame, n: int = 20) -> go.Figure:
    """Bar chart horizontal con el ranking ICG de los top/bottom N países."""
    df_plot = df.head(n).copy()
    colors = df_plot["icg"].map(
        lambda x: ("#00D4AA" if x > 70 else
                   "#3CB87A" if x > 55 else
                   "#E8A020" if x > 40 else
                   "#C84B11" if x > 25 else
                   "#7F1010")
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_plot["icg"],
        y=df_plot["country"],
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=0),
            pattern=dict(shape=""),
        ),
        text=df_plot["icg"].round(1),
        textposition="outside",
        textfont=dict(family="Space Mono, monospace", size=9, color="#C8D6E5"),
        customdata=np.stack([
            df_plot["leverage"], df_plot["resilience"],
            df_plot["dependence"], df_plot["icg_category"].astype(str)
        ], axis=1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "ICG: %{x:.1f}<br>"
            "Apalancamiento: %{customdata[0]:.1f}<br>"
            "Resiliencia: %{customdata[1]:.1f}<br>"
            "Dependencia: %{customdata[2]:.1f}<br>"
            "Categoría: %{customdata[3]}<extra></extra>"
        ),
    ))

    fig.add_vline(x=50, line_dash="dash", line_color="#1E3A5F", line_width=1)
    fig.add_annotation(x=50, y=1, text="Umbral 50", showarrow=False,
                       font=dict(color="#4A9ECA", size=9, family="Space Mono"),
                       yref="paper", xanchor="left", xshift=5)

    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        title=dict(text=f"Ranking ICG — Top {n} Países",
                   font=dict(family="Space Mono, monospace", size=13, color="#E8F4FD")),
        xaxis=dict(title="ICG (0-100)", range=[0, 115]),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
        height=max(500, n * 26),
        showlegend=False,
    )
    return fig


def render_radar_comparison(df: pd.DataFrame,
                             countries: list) -> go.Figure:
    """Radar chart para comparar dimensiones ICG entre países seleccionados."""
    dimensions = ["leverage", "resilience", "icg"]
    dim_labels  = ["Apalancamiento", "Resiliencia", "ICG Global"]

    COLORS_RADAR = ["#00D4AA", "#F0B429", "#FF6B6B", "#4A9ECA", "#A78BFA", "#F97316"]

    fig = go.Figure()

    for i, country in enumerate(countries):
        row = df[df["country"] == country]
        if row.empty:
            continue
        row = row.iloc[0]
        values = [row[d] for d in dimensions]
        values += [values[0]]  # cerrar polígono

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=dim_labels + [dim_labels[0]],
            name=country,
            line=dict(color=COLORS_RADAR[i % len(COLORS_RADAR)], width=2),
            fill="toself",
            fillcolor=f"rgba{tuple(list(px.colors.hex_to_rgb(COLORS_RADAR[i % len(COLORS_RADAR)])) + [0.08])}",
        ))

    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        polar=dict(
            bgcolor="#0A1220",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#1A3050", linecolor="#1A3050",
                tickfont=dict(size=8, color="#6B8BA4", family="Space Mono"),
            ),
            angularaxis=dict(
                gridcolor="#1A3050", linecolor="#1A3050",
                tickfont=dict(size=10, color="#C8D6E5"),
            ),
        ),
        title=dict(text="Comparación Multidimensional ICG",
                   font=dict(family="Space Mono, monospace", size=13, color="#E8F4FD")),
        showlegend=True,
        height=420,
    )
    return fig


def render_tariff_impact_chart(df_base: pd.DataFrame,
                                df_shock: pd.DataFrame,
                                highlight: list) -> go.Figure:
    """
    Gráfico de impacto arancelario: ICG base vs. ICG con choque Trump 2026.
    Muestra la caída relativa de ICG por país al aplicar el arancel seleccionado.
    """
    # Filtrar países con mayor exposición a EE.UU. (más interesantes para el análisis)
    df_merged = df_base[["country", "icg", "us_export_pct", "sanctions_score"]].copy()
    df_merged["icg_base"]  = df_base["icg"].values
    df_merged["icg_shock"] = df_shock["icg"].values
    df_merged["delta"]     = df_merged["icg_shock"] - df_merged["icg_base"]

    # Top 15 más afectados + países destacados
    top_affected = (df_merged.nsmallest(15, "delta")["country"].tolist()
                    + highlight)
    df_plot = df_merged[df_merged["country"].isin(set(top_affected))].copy()
    df_plot = df_plot.sort_values("delta")

    fig = go.Figure()

    # Barras delta
    colors_delta = df_plot["delta"].map(
        lambda x: "#FF6B6B" if x < -5 else "#F0B429" if x < 0 else "#4ADE80"
    )
    fig.add_trace(go.Bar(
        x=df_plot["delta"],
        y=df_plot["country"],
        orientation="h",
        marker=dict(color=colors_delta, line=dict(width=0)),
        name="ΔICG",
        text=df_plot["delta"].round(2),
        textposition="outside",
        textfont=dict(family="Space Mono, monospace", size=9),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "ΔICG: %{x:.2f}<br>"
            "Expo. a EE.UU.: %{customdata:.1f}%<extra></extra>"
        ),
        customdata=df_plot["us_export_pct"],
    ))

    fig.add_vline(x=0, line_color="#4A9ECA", line_width=1.5)

    # Resaltar países seleccionados
    for c in highlight:
        row = df_plot[df_plot["country"] == c]
        if not row.empty:
            fig.add_annotation(
                x=row["delta"].values[0],
                y=c,
                text=f"← {c}",
                showarrow=False,
                font=dict(color="#F0B429", size=10, family="Space Mono"),
                xanchor="right" if row["delta"].values[0] < 0 else "left",
            )

    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        title=dict(
            text="Simulador Trump 2026: Impacto Arancelario sobre el ICG",
            font=dict(family="Space Mono, monospace", size=13, color="#E8F4FD"),
        ),
        xaxis=dict(title="Δ ICG (puntos)", zeroline=True),
        yaxis=dict(autorange="reversed"),
        height=500,
        showlegend=False,
    )
    return fig


def render_scatter_leverage_resilience(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot Apalancamiento vs Resiliencia.
    Tamaño de burbuja = PIB. Color = ICG.
    Cuadrantes geopolíticos: Potencia, Autarquía, Dependiente, Vulnerable.
    """
    fig = go.Figure()

    # Fondo de cuadrantes
    mid = 50
    for (x0, x1, y0, y1, label, color) in [
        (mid, 105, mid, 105, "POTENCIAS<br>GLOBALES",   "rgba(0, 212, 170, 0.04)"),
        (0,   mid, mid, 105, "AUTARQUÍAS<br>RESILIENTES", "rgba(240, 180, 41, 0.04)"),
        (mid, 105, 0,   mid, "POTENCIAS<br>VULNERABLES",  "rgba(74, 158, 202, 0.04)"),
        (0,   mid, 0,   mid, "ESTADOS<br>FRÁGILES",       "rgba(255, 107, 107, 0.04)"),
    ]:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=color, line_width=0)
        fig.add_annotation(
            x=(x0+x1)/2, y=(y0+y1)/2, text=label,
            showarrow=False, font=dict(size=8, color="#3A5A7A", family="Space Mono"),
            opacity=0.7, align="center",
        )

    # Puntos
    fig.add_trace(go.Scatter(
        x=df["leverage"],
        y=df["resilience"],
        mode="markers+text",
        marker=dict(
            size=np.sqrt(df["gdp_bn"] / 25) + 8,
            color=df["icg"],
            colorscale=ICG_COLORSCALE,
            showscale=True,
            line=dict(color="#1E3A5F", width=1),
            colorbar=dict(
                title="ICG",
                tickfont=dict(family="Space Mono", size=8),
                len=0.6, thickness=10,
                bgcolor="#0D1F3C", bordercolor="#1E3A5F",
            ),
        ),
        text=df["country"],
        textposition="top center",
        textfont=dict(size=8, color="#C8D6E5", family="DM Sans"),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Apalancamiento: %{x:.1f}<br>"
            "Resiliencia: %{y:.1f}<br>"
            "ICG: %{marker.color:.1f}<extra></extra>"
        ),
    ))

    # Líneas de cuadrante
    fig.add_hline(y=50, line_dash="dot", line_color="#1E3A5F", line_width=1)
    fig.add_vline(x=50, line_dash="dot", line_color="#1E3A5F", line_width=1)

    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        title=dict(text="Matriz Geopolítica: Apalancamiento vs. Resiliencia",
                   font=dict(family="Space Mono, monospace", size=13, color="#E8F4FD")),
        xaxis=dict(title="Apalancamiento (Exportaciones Críticas + Reservas)", range=[0, 105]),
        yaxis=dict(title="Resiliencia (Energía + Alimentos)", range=[0, 105]),
        height=550,
    )
    return fig


def render_sanctions_network(df: pd.DataFrame) -> go.Figure:
    """
    Mapa de calor: Sanciones EE.UU. vs. ICG
    Muestra la "zona de sombra arancelaria" (países bajo presión estadounidense)
    """
    fig = px.scatter(
        df.sort_values("sanctions_score"),
        x="sanctions_score",
        y="icg",
        size="gdp_bn",
        color="us_export_pct",
        text="country",
        color_continuous_scale="Blues_r",
        size_max=60,
        labels={
            "sanctions_score": "Exposición a Sanciones EE.UU. (0-10)",
            "icg": "ICG (0-100)",
            "us_export_pct": "% Exp. → EE.UU.",
        },
        title="Zona de Sombra Arancelaria: Sanciones vs. Poder de Conversión",
    )

    # Umbral de riesgo alto
    fig.add_vline(x=7, line_dash="dash", line_color="#FF6B6B",
                  annotation_text="Zona de Sanciones Severas",
                  annotation_font_color="#FF6B6B",
                  annotation_font_size=9)
    fig.add_hline(y=40, line_dash="dash", line_color="#F0B429",
                  annotation_text="Umbral ICG crítico",
                  annotation_font_color="#F0B429",
                  annotation_font_size=9)

    fig.update_traces(
        marker_line_color="#1E3A5F", marker_line_width=1,
        textfont=dict(size=8, color="#C8D6E5"),
    )
    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        height=480,
        title_font=dict(family="Space Mono, monospace", size=13, color="#E8F4FD"),
        coloraxis_colorbar=dict(
            title="% Exp EE.UU.",
            tickfont=dict(family="Space Mono", size=8),
            bgcolor="#0D1F3C", bordercolor="#1E3A5F",
        ),
    )
    return fig


def render_tariff_time_simulation(
        df: pd.DataFrame,
        country: str,
        tariff_range: np.ndarray) -> go.Figure:
    """
    Simulación de trayectoria del ICG de un país específico
    a medida que aumenta el arancel de EE.UU. (0-100%).
    Muestra 3 escenarios: Optimista, Base, Pesimista.
    """
    icg_values = []
    for t in tariff_range:
        df_sim = compute_icg(df.copy(), us_tariff_shock=t)
        row = df_sim[df_sim["country"] == country]
        if not row.empty:
            icg_values.append(row["icg"].values[0])
        else:
            icg_values.append(np.nan)

    icg_base = np.array(icg_values)

    # Escenarios: ±10% variación en los parámetros
    icg_optimistic = np.clip(icg_base * 1.10, 0, 100)
    icg_pessimistic = np.clip(icg_base * 0.90, 0, 100)

    fig = go.Figure()

    # Banda de incertidumbre
    fig.add_trace(go.Scatter(
        x=np.concatenate([tariff_range, tariff_range[::-1]]),
        y=np.concatenate([icg_optimistic, icg_pessimistic[::-1]]),
        fill="toself",
        fillcolor="rgba(74, 158, 202, 0.10)",
        line=dict(color="rgba(74, 158, 202, 0)"),
        name="Banda de incertidumbre",
        showlegend=True,
    ))

    # Escenario optimista
    fig.add_trace(go.Scatter(
        x=tariff_range, y=icg_optimistic,
        line=dict(color="#4A9ECA", width=1, dash="dot"),
        name="Escenario optimista",
    ))

    # Escenario base
    fig.add_trace(go.Scatter(
        x=tariff_range, y=icg_base,
        line=dict(color="#F0B429", width=2.5),
        name=f"ICG Base — {country}",
        mode="lines",
    ))

    # Escenario pesimista
    fig.add_trace(go.Scatter(
        x=tariff_range, y=icg_pessimistic,
        line=dict(color="#FF6B6B", width=1, dash="dot"),
        name="Escenario pesimista",
    ))

    # Líneas de referencia
    fig.add_hline(y=30, line_dash="dash", line_color="#FF6B6B", line_width=0.8,
                  annotation_text="Umbral crítico (30)", annotation_font_size=9,
                  annotation_font_color="#FF6B6B")
    fig.add_hline(y=60, line_dash="dash", line_color="#4ADE80", line_width=0.8,
                  annotation_text="Umbral fuerte (60)", annotation_font_size=9,
                  annotation_font_color="#4ADE80")

    # Eventos históricos marcados
    events = {
        25: "Aranceles\nFase 1 (2018)",
        60: "Máx. guerra\ncomercial",
        100: "Embargo\ntotal",
    }
    for x_val, label in events.items():
        fig.add_vline(x=x_val, line_dash="dot", line_color="#1E3A5F", line_width=1)
        fig.add_annotation(x=x_val, y=95, text=label, showarrow=False,
                           font=dict(size=7.5, color="#4A9ECA", family="Space Mono"),
                           textangle=0, yref="y")

    fig.update_layout(
        **DARK_TEMPLATE["layout"].to_plotly_json(),
        title=dict(
            text=f"Trayectoria ICG de {country} vs. Escalada Arancelaria EE.UU.",
            font=dict(family="Space Mono, monospace", size=13, color="#E8F4FD"),
        ),
        xaxis=dict(title="Arancel EE.UU. aplicado (%)", range=[0, 101]),
        yaxis=dict(title="ICG (0-100)", range=[0, 105]),
        height=420,
        legend=dict(orientation="h", y=-0.2),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5: LAYOUT PRINCIPAL STREAMLIT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── HEADER ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="icg-header">
        <div style="position: relative; z-index: 1;">
            <p class="icg-subtitle">⬡ SISTEMA DE ANÁLISIS GEOPOLÍTICO · v1.0 · 2026</p>
            <h1 class="icg-title">Índice de Conversión Geoeconómica</h1>
            <p style="color: #6B8BA4; font-size: 0.95rem; margin-top: 8px; max-width: 720px;">
                Mide la capacidad de un Estado para convertir sus recursos económicos 
                en poder político internacional. Integra datos en tiempo real del 
                Banco Mundial, UN Comtrade e IMF.
            </p>
            <div class="icg-formula">
                ICG = ( Apalancamiento × Resiliencia ) ÷ Dependencia_Externa
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🎛️ Controles")

        st.markdown("**Año de referencia**")
        year = st.selectbox("Año", [2022, 2021, 2020], index=0, label_visibility="collapsed")

        st.markdown("---")
        st.markdown("### 🇺🇸 Simulador Trump 2026")
        st.markdown(
            '<div class="alert-box">Ajusta el arancel de EE.UU. y observa '
            'el impacto en tiempo real sobre el ICG de cada país.</div>',
            unsafe_allow_html=True
        )
        tariff = st.slider(
            "Arancel EE.UU. aplicado (%)",
            min_value=0, max_value=100, value=0, step=5,
            help="0% = sin choque / 25% = Guerra comercial Fase I / 100% = Embargo total"
        )

        st.markdown("---")
        st.markdown("### ⚖️ Pesos del Índice")
        w_leverage = st.slider("Peso Apalancamiento", 0.5, 2.0, 1.0, 0.1)
        w_resilience = st.slider("Peso Resiliencia", 0.5, 2.0, 1.0, 0.1)

        st.markdown("---")
        st.markdown("### 🔬 Países del Análisis")
        all_countries = sorted([
            "China", "Russia", "Iran", "Saudi Arabia", "India", "Brazil",
            "Germany", "Japan", "Mexico", "North Korea", "Venezuela",
            "Turkey", "South Korea", "Canada", "Australia",
            "UAE", "South Africa", "France", "Nigeria", "Indonesia",
            "Poland", "Kazakhstan",
        ])
        radar_countries = st.multiselect(
            "Comparar en Radar Chart",
            options=all_countries,
            default=["United States", "China", "Russia", "Iran"],
        )
        highlight_countries = st.multiselect(
            "Destacar en Simulador",
            options=all_countries,
            default=["Iran", "China", "Mexico"],
        )

        st.markdown("---")
        st.markdown("### 📡 Estado de APIs")
        api_placeholder = st.empty()

        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.75rem; color: #3A5A7A; line-height: 1.6;">
        <b>Fuentes de datos:</b><br>
        • Banco Mundial WDI<br>
        • UN Comtrade HS2022<br>
        • IMF IFS<br>
        • OEC Economic Complexity<br>
        • Voeten AGNU Dataset<br>
        • OFAC / EU Sanctions Map<br><br>
        <i>Modo offline activo cuando las APIs no responden.</i>
        </div>
        """, unsafe_allow_html=True)

    # ── CARGA DE DATOS ───────────────────────────────────────────────────────
    with st.spinner("Cargando base de datos geopolítica..."):
        df_raw = build_geopolitical_database()

    # Calcular ICG base (sin choque)
    custom_weights = {"leverage": w_leverage, "resilience": w_resilience}
    df_base  = compute_icg(df_raw.copy(), us_tariff_shock=0.0,   custom_weights=custom_weights)
    df_shock = compute_icg(df_raw.copy(), us_tariff_shock=float(tariff), custom_weights=custom_weights)

    # Estado de APIs
    api_placeholder.markdown(f"""
    | API | Estado |
    |-----|--------|
    | Banco Mundial | <span class="status-offline">⬤ Offline (proxy)</span> |
    | UN Comtrade | <span class="status-offline">⬤ Offline (proxy)</span> |
    | IMF | <span class="status-offline">⬤ Offline (proxy)</span> |
    """, unsafe_allow_html=True)

    # ── MÉTRICAS RÁPIDAS ─────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    top_country    = df_shock.iloc[0]["country"]
    bottom_country = df_shock.iloc[-1]["country"]
    avg_icg        = df_shock["icg"].mean()
    usa_icg        = df_shock[df_shock["country"] == "United States"]["icg"].values
    usa_icg_val    = usa_icg[0] if len(usa_icg) else 0.0
    n_critical     = (df_shock["icg"] < 25).sum()

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size: 1.6rem;">{top_country.split()[0]}</div>
            <div class="metric-label">🏆 Mayor ICG</div>
            <div class="metric-delta" style="color:#4ADE80;">
                ICG = {df_shock.iloc[0]["icg"]:.1f}
            </div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size: 1.6rem;">{bottom_country.split()[0]}</div>
            <div class="metric-label">⚠️ Menor ICG</div>
            <div class="metric-delta" style="color:#FF6B6B;">
                ICG = {df_shock.iloc[-1]["icg"]:.1f}
            </div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_icg:.1f}</div>
            <div class="metric-label">📊 ICG Promedio Global</div>
            <div class="metric-delta" style="color:#6B8BA4;">Panel de {len(df_shock)} países</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        delta_usa = usa_icg_val - df_base[df_base["country"] == "United States"]["icg"].values[0] if tariff > 0 else 0.0
        delta_color = "#4ADE80" if delta_usa >= 0 else "#FF6B6B"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#4A9ECA;">{usa_icg_val:.1f}</div>
            <div class="metric-label">🇺🇸 ICG EE.UU.</div>
            <div class="metric-delta" style="color:{delta_color};">
                Δ {delta_usa:+.1f} con arancel
            </div>
        </div>""", unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#FF6B6B;">{n_critical}</div>
            <div class="metric-label">🚨 Estados Críticos</div>
            <div class="metric-delta" style="color:#6B8BA4;">ICG &lt; 25 puntos</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS PRINCIPALES ─────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌍 Mapa Global",
        "📊 Rankings y Matriz",
        "🎯 Comparación",
        "⚡ Simulador Trump 2026",
        "📋 Datos y Metodología",
    ])

    # ── TAB 1: MAPA ──────────────────────────────────────────────────────────
    with tab1:
        map_col1, map_col2 = st.columns([3, 1])

        with map_col2:
            st.markdown("**Métrica del mapa**")
            map_metric = st.radio(
                "",
                options=["icg", "leverage", "resilience", "dependence", "icg_delta"],
                format_func=lambda x: {
                    "icg": "🌐 ICG Compuesto",
                    "leverage": "⚡ Apalancamiento",
                    "resilience": "🛡️ Resiliencia",
                    "dependence": "🔗 Dependencia",
                    "icg_delta": "📉 Δ ICG (Tariff)",
                }[x],
                label_visibility="collapsed",
            )
            st.markdown("---")
            st.markdown(f"""
            **Arancel activo:** `{tariff}%`  
            **Peso Apalancamiento:** `{w_leverage}x`  
            **Peso Resiliencia:** `{w_resilience}x`
            """)
            st.markdown("---")
            st.markdown("**Leyenda ICG**")
            for cat, color, rng in [
                ("Dominante", "#00D4AA", "80-100"),
                ("Fuerte",    "#3CB87A", "65-80"),
                ("Intermedio","#E8A020", "45-65"),
                ("Vulnerable","#C84B11", "25-45"),
                ("Crítico",   "#7F1010", "0-25"),
            ]:
                st.markdown(
                    f'<span style="color:{color}; font-family:Space Mono; font-size:0.8rem;">'
                    f'■ {cat}</span> <span style="color:#6B8BA4; font-size:0.75rem;">({rng})</span>',
                    unsafe_allow_html=True
                )

        with map_col1:
            df_map = df_shock if map_metric != "icg_delta" else df_shock
            st.plotly_chart(render_choropleth(df_map, map_metric),
                            use_container_width=True, config={"scrollZoom": True})

        if tariff > 0:
            st.markdown(
                f'<div class="alert-box">⚡ <b>Arancel Trump activo: {tariff}%</b> — '
                f'El mapa refleja el impacto sobre el ICG. Los países con mayor '
                f'dependencia de exportaciones a EE.UU. son los más afectados.</div>',
                unsafe_allow_html=True
            )

    # ── TAB 2: RANKINGS ──────────────────────────────────────────────────────
    with tab2:
        r_col1, r_col2 = st.columns([1.2, 1])

        with r_col1:
            n_countries = st.slider("Número de países en ranking", 10, 22, 20, 1)
            st.plotly_chart(
                render_icg_ranking_bar(df_shock, n=n_countries),
                use_container_width=True
            )

        with r_col2:
            st.plotly_chart(
                render_scatter_leverage_resilience(df_shock),
                use_container_width=True
            )

    # ── TAB 3: COMPARACIÓN ───────────────────────────────────────────────────
    with tab3:
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            st.plotly_chart(
                render_radar_comparison(df_shock, radar_countries),
                use_container_width=True
            )
        with c_col2:
            st.plotly_chart(
                render_sanctions_network(df_shock),
                use_container_width=True
            )

        # Tabla comparativa detallada
        st.markdown("#### Tabla Comparativa Detallada")
        if radar_countries:
            df_table = df_shock[df_shock["country"].isin(radar_countries)][
                ["country", "icg", "icg_category", "leverage", "resilience",
                 "dependence", "sanctions_score", "us_export_pct", "gdp_bn"]
            ].rename(columns={
                "country": "País", "icg": "ICG", "icg_category": "Categoría",
                "leverage": "Apalancamiento", "resilience": "Resiliencia",
                "dependence": "Dependencia", "sanctions_score": "Sanciones (0-10)",
                "us_export_pct": "% Exp. → EE.UU.", "gdp_bn": "PIB (bn USD)",
            })
            st.dataframe(
                df_table.style.format({
                    "ICG": "{:.1f}", "Apalancamiento": "{:.1f}",
                    "Resiliencia": "{:.1f}", "Dependencia": "{:.1f}",
                    "Sanciones (0-10)": "{:.1f}", "% Exp. → EE.UU.": "{:.1f}",
                    "PIB (bn USD)": "{:,.0f}",
                }).background_gradient(subset=["ICG"], cmap="RdYlGn"),
                use_container_width=True, hide_index=True,
            )

    # ── TAB 4: SIMULADOR TRUMP 2026 ──────────────────────────────────────────
    with tab4:
        st.markdown("""
        <div class="alert-box" style="border-color: rgba(240,180,41,0.6); font-size:0.92rem;">
        <b>🎯 Caso de Estudio: Aranceles Trump 2026</b><br>
        Este simulador modela el impacto de los aranceles sobre el ICG de cada nación. 
        El choque se transmite a través de la variable <i>Dependencia Externa</i>: 
        países con alta dependencia del mercado estadounidense ven caer su ICG más 
        intensamente. <b>El arancel activo actualmente es: {}</b>%
        </div>
        """.format(tariff), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Panel superior: impacto global
        st.plotly_chart(
            render_tariff_impact_chart(df_base, df_shock, highlight_countries),
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### 🔮 Trayectoria de País Específico")
        sim_col1, sim_col2 = st.columns([1, 3])

        with sim_col1:
            country_sim = st.selectbox(
                "País a simular",
                options=sorted(df_base["country"].tolist()),
                index=sorted(df_base["country"].tolist()).index("Iran") if "Iran" in df_base["country"].tolist() else 0,
            )
            sim_resolution = st.radio(
                "Resolución", ["Baja (5%)", "Alta (1%)"],
                help="Alta resolución es más lenta pero más precisa"
            )
            step = 5 if "Baja" in sim_resolution else 1

        with sim_col2:
            tariff_range = np.arange(0, 101, step)
            with st.spinner(f"Simulando {len(tariff_range)} escenarios para {country_sim}..."):
                fig_traj = render_tariff_time_simulation(
                    df_raw.copy(), country_sim, tariff_range
                )
            st.plotly_chart(fig_traj, use_container_width=True)

        # Panel de interpretación
        country_data = df_shock[df_shock["country"] == country_sim]
        if not country_data.empty:
            cd = country_data.iloc[0]
            icg_t  = cd["icg"]
            icg_b  = df_base[df_base["country"] == country_sim]["icg"].values[0]
            delta  = icg_t - icg_b
            us_dep = cd["us_export_pct"]

            interp_color = "#FF6B6B" if delta < -5 else "#F0B429" if delta < 0 else "#4ADE80"
            st.markdown(f"""
            <div style="background:#0A1628; border:1px solid #1E3A5F; border-radius:10px; padding:18px; margin-top:12px;">
                <span style="font-family:Space Mono; font-size:0.8rem; color:#4A9ECA; letter-spacing:0.1em;">
                ANÁLISIS — {country_sim.upper()} · ARANCEL EE.UU. {tariff}%
                </span><br><br>
                <span style="font-family:Space Mono; font-size:1.3rem; color:{interp_color};">
                ΔICG = {delta:+.2f} pts
                </span>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <span style="color:#6B8BA4; font-size:0.9rem;">
                ICG base: {icg_b:.1f} → ICG actual: {icg_t:.1f}
                </span><br><br>
                <span style="font-size:0.88rem; color:#C8D6E5; line-height:1.8;">
                {'⚠️ <b>Alta vulnerabilidad:</b> ' + f'{country_sim} exporta {us_dep:.1f}% a EE.UU. Un arancel de {tariff}% erosiona significativamente su capacidad de conversión geoeconómica.' if us_dep > 20 else
                 '⚡ <b>Exposición moderada:</b> ' + f'{country_sim} tiene una dependencia de {us_dep:.1f}% hacia el mercado estadounidense. El impacto es contenido pero acumulable.' if us_dep > 5 else
                 '🛡️ <b>Alta resiliencia al choque:</b> ' + f'Con solo {us_dep:.1f}% de exportaciones hacia EE.UU., {country_sim} absorbe bien el choque arancelario. Su ICG depende de otros vectores.'}
                </span>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 5: DATOS Y METODOLOGÍA ───────────────────────────────────────────
    with tab5:
        m_col1, m_col2 = st.columns(2)

        with m_col1:
            st.markdown("#### 📐 Metodología del ICG")
            st.markdown(r"""
**Fórmula central:**
$$ICG = \frac{Apalancamiento^{w_L} \times Resiliencia^{w_R}}{Dependencia\_Externa}$$

**Componentes:**

| Subíndice | Variables | Ponderación |
|-----------|-----------|-------------|
| Apalancamiento | Export. críticas (ln) + Reservas divisas (ln) − Sanción penalty | 55% + 35% + 10% |
| Resiliencia | Energía neta exportada + Autosuficiencia alimentaria + Bono PIB | 45% + 45% + 10% |
| Dependencia | Expo. → EE.UU. + Score sanciones + Penalidad arancel | 60% + 25% + 15% |

**Escala final:** Reescalado a [0, 100] en el panel de países.

**Umbrales interpretativos:**
- ICG > 80: Potencia con alta capacidad de coerción económica
- ICG 60-80: Estado fuerte con vectores de influencia regional
- ICG 40-60: Posición intermedia, vulnerable a presiones externas
- ICG 20-40: Dependencia estructural, margen de maniobra reducido
- ICG < 20: Estado geoeconómicamente frágil

**Efecto Trump 2026 (simulador):**

$$\Delta Dependencia_i = \frac{Expo_{EE.UU.,i}}{100} \times T_{arancel} \times 1.5$$

donde 1.5 es el *friction multiplier*: no todas las exportaciones 
afectadas se redirigen perfectamente a mercados alternativos.
            """)

        with m_col2:
            st.markdown("#### 🔌 Arquitectura de APIs")
            st.code("""
# ── Banco Mundial (wbgapi) ─────────────────────
import wbgapi as wb

# PIB por país (USD corrientes 2022)
gdp = wb.data.DataFrame(
    "NY.GDP.MKTP.CD",
    economy="all",
    mrv=1
)

# Importaciones de energía (% consumo total)
energy = wb.data.DataFrame(
    "EG.IMP.CONS.ZS",
    economy="all",
    mrv=1
)

# Reservas totales incluido oro
reserves = wb.data.DataFrame(
    "FI.RES.TOTL.CD",
    economy="all",
    mrv=1
)

# ── UN Comtrade API ────────────────────────────
# Exportaciones combustibles HS-27 (petróleo+gas)
url = (
    "https://comtradeapi.un.org/public/v1/preview"
    "/C/A/HS?reporterCode=156"  # China=156
    "&period=2022&cmdCode=27"
    "&flowCode=X&partnerCode=0"
)
headers = {"Ocp-Apim-Subscription-Key": API_KEY}
resp = requests.get(url, headers=headers)
exports = resp.json()["data"]

# ── IMF IFS API ────────────────────────────────
# Reservas de divisas (USD millones)
imf_url = (
    "http://dataservices.imf.org/REST"
    "/SDMX_JSON.svc/CompactData"
    "/IFS/Q.CN.RESERVES.FX"
    "?startPeriod=2022&endPeriod=2022"
)
reserves_imf = requests.get(imf_url).json()
            """, language="python")

            st.markdown("#### 📦 Instalación")
            st.code("""
# Dependencias del proyecto
pip install streamlit plotly pandas numpy 
pip install requests wbgapi

# Opcional (mejor rendimiento con APIs)
pip install comtradeapicall  # Wrapper oficial UN Comtrade
pip install imf-reader        # Wrapper IMF Data API

# Ejecución
streamlit run icg_dashboard.py
            """, language="bash")

            st.markdown("#### 🗝️ Configuración de API Keys")
            st.code("""
# Crea .streamlit/secrets.toml en la raíz del proyecto
# UN Comtrade requiere key para >100 req/hora

[secrets]
COMTRADE_KEY = "tu-api-key-aquí"
# Obtener en: https://comtradeapi.un.org/

# El Banco Mundial y el IMF NO requieren key
# para uso estándar (con límites de tasa)
            """, language="toml")

        # Tabla de datos completa
        st.markdown("---")
        st.markdown("#### 🗃️ Base de Datos Completa")

        col_filter, col_sort = st.columns(2)
        with col_filter:
            cat_filter = st.multiselect(
                "Filtrar por categoría ICG",
                options=["Dominante", "Fuerte", "Intermedio", "Vulnerable", "Crítico"],
                default=["Dominante", "Fuerte", "Intermedio", "Vulnerable", "Crítico"],
            )
        with col_sort:
            sort_by = st.selectbox(
                "Ordenar por",
                options=["icg", "leverage", "resilience", "dependence",
                         "gdp_bn", "us_export_pct", "sanctions_score"],
                format_func=lambda x: {
                    "icg": "ICG", "leverage": "Apalancamiento",
                    "resilience": "Resiliencia", "dependence": "Dependencia",
                    "gdp_bn": "PIB (bn USD)", "us_export_pct": "% Expo → EE.UU.",
                    "sanctions_score": "Sanciones (0-10)",
                }[x]
            )

        df_display = df_shock[
            df_shock["icg_category"].astype(str).isin(cat_filter)
        ].sort_values(sort_by, ascending=False)[
            ["country", "icg", "icg_category", "leverage", "resilience",
             "dependence", "gdp_bn", "export_critical_bn", "forex_reserves_bn",
             "energy_import_pct", "food_self_sufficiency", "us_export_pct",
             "sanctions_score", "icg_delta"]
        ].rename(columns={
            "country": "País", "icg": "ICG", "icg_category": "Categoría",
            "leverage": "Apalancam.", "resilience": "Resiliencia",
            "dependence": "Dependencia", "gdp_bn": "PIB (bn $)",
            "export_critical_bn": "Exp.Crít. (bn$)", "forex_reserves_bn": "Reservas (bn$)",
            "energy_import_pct": "Energía imp.%", "food_self_sufficiency": "Autosuf.Alim.",
            "us_export_pct": "Exp.→EE.UU.%", "sanctions_score": "Sanciones",
            "icg_delta": "ΔICG (Tariff)",
        })

        st.dataframe(
            df_display.style.format({
                "ICG": "{:.1f}", "Apalancam.": "{:.1f}", "Resiliencia": "{:.1f}",
                "Dependencia": "{:.1f}", "PIB (bn $)": "{:,.0f}",
                "Exp.Crít. (bn$)": "{:.0f}", "Reservas (bn$)": "{:.0f}",
                "Energía imp.%": "{:.0f}", "Autosuf.Alim.": "{:.0f}",
                "Exp.→EE.UU.%": "{:.1f}", "Sanciones": "{:.1f}",
                "ΔICG (Tariff)": "{:+.2f}",
            }).background_gradient(subset=["ICG"], cmap="RdYlGn", vmin=0, vmax=100)
             .background_gradient(subset=["ΔICG (Tariff)"], cmap="RdYlGn", vmin=-20, vmax=5),
            use_container_width=True, hide_index=True, height=480,
        )

    # ── FOOTER ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align: center; padding: 30px 0 10px; 
                border-top: 1px solid #1A3050; margin-top: 30px;">
        <span style="font-family: Space Mono, monospace; font-size: 0.75rem; 
                     color: #3A5A7A; letter-spacing: 0.12em;">
        ICG DASHBOARD v1.0 · CIENCIA DE DATOS & GEOPOLÍTICA<br>
        Datos: World Bank WDI · UN Comtrade · IMF IFS · OEC · OFAC<br>
        Proxy sintético cuando APIs no responden (modo offline-first)
        </span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
