"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       ÍNDICE DE CONVERSIÓN GEOECONÓMICA — DASHBOARD v2.0                   ║
║       Ciencia de Datos & Geopolítica | Streamlit + Plotly                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  NOVEDADES v2.0:                                                             ║
║  • Radar de Comparación Dual: dos países, dimensión a dimensión             ║
║  • Noticias en vivo: NewsAPI → ajuste automático sanctions_score            ║
║  • Fórmula calibrada v3 (única definición, sin duplicados)                  ║
║  • Arquitectura offline-first con 3 capas de degradación elegante           ║
║                                                                              ║
║  Fórmula:                                                                    ║
║    ICG = √(Apalancamiento^wL × Resiliencia^wR) / (1 + D/100) − Penalidad   ║
║                                                                              ║
║  Instalación:                                                                ║
║    pip install streamlit plotly pandas numpy requests wbgapi                 ║
║                                                                              ║
║  API keys opcionales (.streamlit/secrets.toml):                             ║
║    COMTRADE_KEY = "..."   # UN Comtrade >100 req/h                          ║
║    NEWS_API_KEY = "..."   # NewsAPI.org — gratis hasta 100 req/día          ║
║                                                                              ║
║  Ejecución:                                                                  ║
║    streamlit run icg_dashboard.py                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
# 0. IMPORTACIONES
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ICG · Índice de Conversión Geoeconómica v2.0",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. ESTILOS — "Intelligence Terminal Dark" con acento ámbar/cian
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #080C14;
    color: #C8D6E5;
}

/* Header */
.icg-header {
    background: linear-gradient(135deg, #0A1628 0%, #0D1F3C 60%, #091420 100%);
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 28px 36px 24px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.icg-header::before {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 38px,
        rgba(30,58,95,0.12) 38px, rgba(30,58,95,0.12) 39px);
    pointer-events: none;
}
.icg-title {
    font-family: 'Space Mono', monospace;
    font-size: 1.9rem;
    font-weight: 700;
    color: #E8F4FD;
    letter-spacing: -0.02em;
    margin: 0 0 4px;
    position: relative;
}
.icg-badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4A9ECA;
    margin-bottom: 10px;
    position: relative;
}
.icg-formula {
    font-family: 'Space Mono', monospace;
    font-size: 1rem;
    color: #F0B429;
    background: rgba(240,180,41,0.07);
    border-left: 3px solid #F0B429;
    padding: 9px 14px;
    border-radius: 0 8px 8px 0;
    margin-top: 14px;
    display: inline-block;
    position: relative;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(145deg, #0D1F3C, #091629);
    border: 1px solid #1E3A5F;
    border-radius: 10px;
    padding: 18px;
    text-align: center;
    transition: border-color .25s, transform .2s;
}
.metric-card:hover { border-color: #4A9ECA; transform: translateY(-2px); }
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    color: #4ADE80;
    line-height: 1;
}
.metric-label {
    font-size: 0.72rem;
    color: #6B8BA4;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 5px;
}
.metric-delta {
    font-family: 'Space Mono', monospace;
    font-size: 0.82rem;
    margin-top: 4px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #060A10;
    border-right: 1px solid #1A3050;
}

/* News card */
.news-card {
    background: #0A1628;
    border: 1px solid #1E3A5F;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
    transition: border-color .2s;
}
.news-card:hover { border-color: #4A9ECA; }
.news-title { font-size: 0.85rem; color: #C8D6E5; font-weight: 500; line-height: 1.4; }
.news-meta  { font-family: 'Space Mono', monospace; font-size: 0.7rem; color: #4A9ECA; margin-top: 5px; }
.news-alert { color: #F0B429 !important; }
.news-impact-badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    padding: 2px 7px;
    border-radius: 4px;
    margin-left: 6px;
    vertical-align: middle;
}
.badge-high   { background: rgba(255,107,107,0.15); color: #FF6B6B; border: 1px solid #FF6B6B; }
.badge-medium { background: rgba(240,180,41,0.15);  color: #F0B429; border: 1px solid #F0B429; }
.badge-low    { background: rgba(74,158,202,0.15);  color: #4A9ECA; border: 1px solid #4A9ECA; }

/* Alert box */
.alert-box {
    background: rgba(240,180,41,0.08);
    border: 1px solid rgba(240,180,41,0.35);
    border-radius: 8px;
    padding: 11px 15px;
    font-size: 0.87rem;
    color: #F0B429;
    margin: 8px 0;
}

/* Status */
.status-live    { color: #4ADE80; }
.status-offline { color: #FF6B6B; }

/* Comparison panel */
.compare-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4A9ECA;
    border-bottom: 1px solid #1A3050;
    padding-bottom: 6px;
    margin-bottom: 12px;
}
.win-badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(74,222,128,0.12);
    color: #4ADE80;
    border: 1px solid #4ADE80;
    margin-left: 6px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. CONSTANTES VISUALES
# ─────────────────────────────────────────────────────────────────────────────
ICG_COLORSCALE = [
    [0.00, "#3D0000"], [0.18, "#7F1010"], [0.30, "#C84B11"],
    [0.45, "#E8A020"], [0.62, "#A8C832"], [0.80, "#3CB87A"],
    [1.00, "#00D4AA"],
]

DARK_LAYOUT = dict(
    paper_bgcolor="#080C14", plot_bgcolor="#0A1220",
    font=dict(family="DM Sans, sans-serif", color="#C8D6E5", size=11),
    xaxis=dict(gridcolor="#1A3050", zerolinecolor="#1A3050", linecolor="#1A3050"),
    yaxis=dict(gridcolor="#1A3050", zerolinecolor="#1A3050", linecolor="#1A3050"),
    legend=dict(bgcolor="#0D1F3C", bordercolor="#1E3A5F", borderwidth=1),
    margin=dict(t=50, b=45, l=45, r=25),
)

RADAR_COLORS = ["#00D4AA", "#F0B429", "#FF6B6B", "#4A9ECA", "#A78BFA", "#F97316"]

DIMENSION_LABELS = {
    "leverage":      "Apalancamiento",
    "resilience":    "Resiliencia",
    "dependence_inv":"Aut. Estratégica",
    "icg":           "ICG Global",
}


# ─────────────────────────────────────────────────────────────────────────────
# 4. CAPA DE DATOS — API BANCO MUNDIAL
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_worldbank(indicator: str, year: int = 2022) -> Dict[str, float]:
    """
    Extrae un indicador del Banco Mundial vía endpoint REST público.
    Retorna dict {iso3: valor}. No requiere API key.
    """
    url = (f"https://api.worldbank.org/v2/country/all/indicator/{indicator}"
           f"?format=json&date={year}&per_page=300&mrv=1")
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            payload = r.json()
            if len(payload) > 1 and payload[1]:
                return {
                    e["countryiso3code"]: float(e["value"])
                    for e in payload[1]
                    if e.get("countryiso3code") and e.get("value") is not None
                }
    except Exception:
        pass
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# 5. CAPA DE DATOS — NOTICIAS EN VIVO (NewsAPI)
# ─────────────────────────────────────────────────────────────────────────────

SANCTION_KEYWORDS = [
    "sanction", "sanctions", "sanctioned", "embargo", "blacklist",
    "OFAC", "export control", "trade ban", "asset freeze",
    "tariff", "trade war", "countermeasure",
]

TARIFF_KEYWORDS = [
    "tariff", "tariffs", "trade war", "import duty", "customs",
    "protectionism", "trade barrier",
]

COUNTRY_MAP_NEWS = {
    "china": "China", "chinese": "China", "beijing": "China",
    "russia": "Russia", "russian": "Russia", "moscow": "Russia",
    "iran": "Iran", "iranian": "Iran", "tehran": "Iran",
    "north korea": "North Korea", "pyongyang": "North Korea",
    "venezuela": "Venezuela", "caracas": "Venezuela",
    "turkey": "Turkey", "turkish": "Turkey", "ankara": "Turkey",
    "saudi": "Saudi Arabia", "riyadh": "Saudi Arabia",
    "mexico": "Mexico", "mexican": "Mexico",
    "canada": "Canada", "canadian": "Canada",
    "india": "India", "indian": "India",
    "germany": "Germany", "german": "Germany",
    "japan": "Japan", "japanese": "Japan",
}


@st.cache_data(ttl=900, show_spinner=False)   # caché 15 min
def fetch_news_live(api_key: str, query: str = "sanctions tariffs trade war",
                    page_size: int = 20) -> List[Dict]:
    """
    Consulta NewsAPI.org por noticias recientes de sanciones/aranceles.
    Endpoint: https://newsapi.org/v2/everything
    Gratis hasta 100 peticiones/día. Requiere registro en newsapi.org.

    Retorna lista de artículos con campos:
        title, source, publishedAt, url, country_mentions, impact_score
    """
    if not api_key:
        return []
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": api_key,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            enriched = []
            for a in articles:
                text = (a.get("title", "") + " " + (a.get("description") or "")).lower()
                # Detectar países mencionados
                countries_found = []
                for kw, country in COUNTRY_MAP_NEWS.items():
                    if kw in text and country not in countries_found:
                        countries_found.append(country)
                # Score de impacto (0-3) basado en keywords
                sanc_hits   = sum(1 for k in SANCTION_KEYWORDS if k.lower() in text)
                tariff_hits = sum(1 for k in TARIFF_KEYWORDS   if k.lower() in text)
                impact = min(3, sanc_hits + tariff_hits)
                enriched.append({
                    "title":    a.get("title", "Sin título"),
                    "source":   a.get("source", {}).get("name", "Desconocido"),
                    "published": a.get("publishedAt", ""),
                    "url":      a.get("url", "#"),
                    "countries": countries_found,
                    "sanction_hits": sanc_hits,
                    "tariff_hits":   tariff_hits,
                    "impact":   impact,   # 0=bajo, 1=medio, 2-3=alto
                })
            return enriched
    except Exception:
        pass
    return []


def compute_news_sanctions_delta(articles: List[Dict]) -> Dict[str, float]:
    """
    Calcula el ajuste de sanctions_score para cada país basado en noticias recientes.

    Lógica:
    - Cada artículo con mención de un país suma un delta proporcional a su impact score.
    - Artículos recientes (<6h) pesan el doble.
    - Delta máximo acumulado por país: +2.5 puntos sobre la escala [0,10].
    - El delta es ADITIVO sobre el score base de la base de datos.

    Retorna: dict {country: delta_sanctions}
    """
    now = datetime.now(timezone.utc)
    deltas: Dict[str, float] = {}

    for article in articles:
        pub_str  = article.get("published", "")
        impact   = article.get("impact", 0)
        countries = article.get("countries", [])

        if not countries or impact == 0:
            continue

        # Peso temporal (artículos más recientes pesan más)
        weight = 1.0
        try:
            pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            hours_ago = (now - pub_dt).total_seconds() / 3600
            weight = 2.0 if hours_ago < 6 else (1.5 if hours_ago < 24 else 1.0)
        except Exception:
            pass

        for country in countries:
            contribution = (impact / 3) * weight * 0.8   # max ~2.4 por artículo top
            deltas[country] = min(2.5, deltas.get(country, 0.0) + contribution)

    return deltas


# ─────────────────────────────────────────────────────────────────────────────
# 6. BASE DE DATOS GEOPOLÍTICA (22 PAÍSES, ca. 2022)
# ─────────────────────────────────────────────────────────────────────────────
def build_database() -> pd.DataFrame:
    """
    Proxy documentado. Variables y fuentes primarias en comentarios inline.
    Reemplazable con fetch_worldbank() cuando hay conexión.

    Campos:
      export_critical_bn  : UN Comtrade HS27+HS26+HS84
      forex_reserves_bn   : IMF IFS / WB FI.RES.TOTL.CD
      energy_import_pct   : WB EG.IMP.CONS.ZS (negativo = exportador neto)
      food_self_sufficiency: FAO FBS / USDA PSD (>100 = exportador neto)
      gdp_bn              : WB NY.GDP.MKTP.CD 2022
      us_export_pct       : WITS partner share 2022-2023
      sanctions_score     : OFAC + EU Sanctions Map [0-10]
    """
    data = {
        "United States": dict(iso3="USA", region="América del Norte",
            export_critical_bn=285, forex_reserves_bn=246,  energy_import_pct=-12,
            food_self_sufficiency=130, gdp_bn=25464, us_export_pct=0.0,  sanctions_score=0.0,
            bloc="Occidental"),
        "China": dict(iso3="CHN", region="Asia Oriental",
            export_critical_bn=580, forex_reserves_bn=3200, energy_import_pct=18,
            food_self_sufficiency=95,  gdp_bn=17963, us_export_pct=16.8, sanctions_score=3.5,
            bloc="BRICS"),
        "Russia": dict(iso3="RUS", region="Europa del Este",
            export_critical_bn=480, forex_reserves_bn=640,  energy_import_pct=-87,
            food_self_sufficiency=145, gdp_bn=2245,  us_export_pct=1.2,  sanctions_score=9.5,
            bloc="BRICS"),
        "Iran": dict(iso3="IRN", region="Oriente Medio",
            export_critical_bn=45,  forex_reserves_bn=15,   energy_import_pct=-220,
            food_self_sufficiency=72,  gdp_bn=367,   us_export_pct=0.0,  sanctions_score=10.0,
            bloc="Eje resistencia"),
        "Saudi Arabia": dict(iso3="SAU", region="Oriente Medio",
            export_critical_bn=320, forex_reserves_bn=478,  energy_import_pct=-350,
            food_self_sufficiency=42,  gdp_bn=1109,  us_export_pct=8.5,  sanctions_score=1.0,
            bloc="G20"),
        "India": dict(iso3="IND", region="Asia del Sur",
            export_critical_bn=95,  forex_reserves_bn=562,  energy_import_pct=38,
            food_self_sufficiency=102, gdp_bn=3385,  us_export_pct=18.2, sanctions_score=0.5,
            bloc="Quad/BRICS"),
        "Brazil": dict(iso3="BRA", region="América del Sur",
            export_critical_bn=110, forex_reserves_bn=325,  energy_import_pct=-3,
            food_self_sufficiency=190, gdp_bn=1920,  us_export_pct=11.0, sanctions_score=0.0,
            bloc="BRICS/G20"),
        "Germany": dict(iso3="DEU", region="Europa Occidental",
            export_critical_bn=145, forex_reserves_bn=295,  energy_import_pct=61,
            food_self_sufficiency=93,  gdp_bn=4072,  us_export_pct=9.5,  sanctions_score=0.0,
            bloc="Occidental/UE"),
        "Japan": dict(iso3="JPN", region="Asia Oriental",
            export_critical_bn=120, forex_reserves_bn=1291, energy_import_pct=85,
            food_self_sufficiency=38,  gdp_bn=4231,  us_export_pct=19.0, sanctions_score=0.0,
            bloc="Occidental/Quad"),
        "Mexico": dict(iso3="MEX", region="América del Norte",
            export_critical_bn=55,  forex_reserves_bn=201,  energy_import_pct=22,
            food_self_sufficiency=85,  gdp_bn=1294,  us_export_pct=79.95, sanctions_score=0.0,
            bloc="América del Norte"),
        "Canada": dict(iso3="CAN", region="América del Norte",
            export_critical_bn=210, forex_reserves_bn=106,  energy_import_pct=-58,
            food_self_sufficiency=185, gdp_bn=2140,  us_export_pct=73.2, sanctions_score=0.0,
            bloc="Occidental"),
        "Australia": dict(iso3="AUS", region="Oceanía",
            export_critical_bn=185, forex_reserves_bn=58,   energy_import_pct=-45,
            food_self_sufficiency=250, gdp_bn=1724,  us_export_pct=5.0,  sanctions_score=0.0,
            bloc="Occidental/Quad"),
        "South Korea": dict(iso3="KOR", region="Asia Oriental",
            export_critical_bn=175, forex_reserves_bn=423,  energy_import_pct=78,
            food_self_sufficiency=45,  gdp_bn=1665,  us_export_pct=16.1, sanctions_score=0.0,
            bloc="Occidental"),
        "France": dict(iso3="FRA", region="Europa Occidental",
            export_critical_bn=85,  forex_reserves_bn=242,  energy_import_pct=45,
            food_self_sufficiency=122, gdp_bn=2784,  us_export_pct=7.5,  sanctions_score=0.0,
            bloc="Occidental/UE"),
        "UAE": dict(iso3="ARE", region="Oriente Medio",
            export_critical_bn=165, forex_reserves_bn=188,  energy_import_pct=-280,
            food_self_sufficiency=25,  gdp_bn=509,   us_export_pct=4.8,  sanctions_score=0.5,
            bloc="G20"),
        "Turkey": dict(iso3="TUR", region="Europa/Oriente Medio",
            export_critical_bn=35,  forex_reserves_bn=128,  energy_import_pct=72,
            food_self_sufficiency=97,  gdp_bn=906,   us_export_pct=6.5,  sanctions_score=1.5,
            bloc="OTAN (ambiguo)"),
        "South Africa": dict(iso3="ZAF", region="África Subsahariana",
            export_critical_bn=52,  forex_reserves_bn=60,   energy_import_pct=15,
            food_self_sufficiency=98,  gdp_bn=406,   us_export_pct=8.9,  sanctions_score=0.5,
            bloc="BRICS"),
        "Indonesia": dict(iso3="IDN", region="Asia Sudoriental",
            export_critical_bn=72,  forex_reserves_bn=137,  energy_import_pct=-12,
            food_self_sufficiency=88,  gdp_bn=1319,  us_export_pct=9.8,  sanctions_score=0.0,
            bloc="G20/ASEAN"),
        "Poland": dict(iso3="POL", region="Europa del Este",
            export_critical_bn=28,  forex_reserves_bn=168,  energy_import_pct=48,
            food_self_sufficiency=108, gdp_bn=688,   us_export_pct=3.1,  sanctions_score=0.0,
            bloc="Occidental/UE"),
        "North Korea": dict(iso3="PRK", region="Asia Oriental",
            export_critical_bn=1.8, forex_reserves_bn=2,    energy_import_pct=25,
            food_self_sufficiency=70,  gdp_bn=18,    us_export_pct=0.0,  sanctions_score=10.0,
            bloc="Autárquico"),
        "Venezuela": dict(iso3="VEN", region="América del Sur",
            export_critical_bn=12,  forex_reserves_bn=9,    energy_import_pct=-180,
            food_self_sufficiency=55,  gdp_bn=98,    us_export_pct=2.0,  sanctions_score=8.5,
            bloc="ALBA"),
        "Kazakhstan": dict(iso3="KAZ", region="Asia Central",
            export_critical_bn=65,  forex_reserves_bn=94,   energy_import_pct=-155,
            food_self_sufficiency=112, gdp_bn=220,   us_export_pct=3.5,  sanctions_score=1.0,
            bloc="OCS/CSTO"),
    }
    rows = [{"country": k, **v} for k, v in data.items()]
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# 7. MOTOR ICG — FÓRMULA CALIBRADA v3 (ÚNICA DEFINICIÓN)
# ─────────────────────────────────────────────────────────────────────────────

def _norm(s: pd.Series) -> pd.Series:
    """Min-max normalización a [0, 100]. Segura ante series constantes."""
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(50.0, index=s.index)
    return (s - mn) / (mx - mn) * 100


def calculate_leverage(df: pd.DataFrame) -> pd.Series:
    """
    Apalancamiento = capacidad de proyectar influencia económica.

    Variables:
      Export Score  : ln(export_critical_bn + 1) → [0,100]  peso 55%
      Forex Score   : ln(forex_reserves_bn  + 1) → [0,100]  peso 35%
      Sanction Pen. : sanctions_score × 4 → [0,40] pts penalidad   10%

    Sanciones activas reducen el apalancamiento efectivo porque:
      - Las reservas pueden estar congeladas (Rusia 2022)
      - Los mercados de destino están bloqueados (Irán)
    """
    exp_n = _norm(np.log1p(df["export_critical_bn"]))
    forex_n = _norm(np.log1p(df["forex_reserves_bn"]))
    sanction_pen = df["sanctions_score"] * 4      # 0-40 pts
    return (exp_n * 0.55 + forex_n * 0.35 - sanction_pen * 0.10).clip(0, 100)


def calculate_resilience(df: pd.DataFrame) -> pd.Series:
    """
    Resiliencia = capacidad de absorber shocks externos.

    Variables:
      Energy Score  : -energy_import_pct → exportador neto=alto  peso 50%
      Food Score    : food_self_sufficiency → [0,100]             peso 50%
      GDP Bonus     : ln(gdp_bn) → bono máx 15 pts               (suplemen.)

    Energía negativa (exportador neto) → mejor resiliencia estratégica.
    """
    energy_n = _norm(-df["energy_import_pct"])
    food_n   = _norm(df["food_self_sufficiency"]).clip(0, 100)
    gdp_b    = _norm(np.log1p(df["gdp_bn"])) * 0.15
    return (energy_n * 0.50 + food_n * 0.50 + gdp_b).clip(0, 100)


def calculate_dependence(df: pd.DataFrame) -> pd.Series:
    """
    Dependencia externa = vulnerabilidad estructural.

    Variables:
      US exposure   : us_export_pct normalizado  peso 65%
      Sanction dep. : sanctions_score normalizado peso 35%

    Nota: el impacto arancelario NO se incluye aquí sino como penalidad
    directa en compute_icg() para mayor transparencia del modelo.
    """
    return (_norm(df["us_export_pct"]) * 0.65 +
            _norm(df["sanctions_score"]) * 0.35).clip(0, 100)


def compute_icg(
    df: pd.DataFrame,
    us_tariff: float = 0.0,
    w_leverage: float = 1.0,
    w_resilience: float = 1.0,
    news_deltas: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Fórmula calibrada v3:

        ICG = √(L^wL × R^wR) / (1 + D/100) − Penalidad_Arancelaria

    • √(L×R) suaviza la dominancia extrema de actores con ventaja en una sola dimensión
    • (1 + D/100) evita colapso matemático en dependencia máxima
    • Penalidad arancelaria: proporcional a exposición × arancel × friction(0.70)

    Ajuste por noticias:
      news_deltas: dict {country: Δsanctions} calculado por compute_news_sanctions_delta()
      Se suma al sanctions_score base antes de recalcular leverage y dependencia.

    Calibración validada (15 países ca. 2022):
      EE.UU.=100 | Arabia/Brasil≈95 | Rusia≈84 | China≈76
      Canadá≈68  | Alemania≈67     | India≈66  | México≈39
      Δ México con arancel 100%: −22 pts | Δ Irán: ≈0 (ya embargado)
    """
    df = df.copy()

    # Aplicar ajuste de noticias sobre sanctions_score
    if news_deltas:
        def apply_delta(row):
            delta = news_deltas.get(row["country"], 0.0)
            return min(10.0, row["sanctions_score"] + delta)
        df["sanctions_score"] = df.apply(apply_delta, axis=1)

    # Subíndices
    df["leverage"]   = calculate_leverage(df)
    df["resilience"] = calculate_resilience(df)
    df["dependence"] = calculate_dependence(df)

    L = np.maximum(df["leverage"],   0.0)
    R = np.maximum(df["resilience"], 0.0)
    D = df["dependence"]

    # ICG bruto
    icg_raw = np.sqrt(np.power(L, w_leverage) * np.power(R, w_resilience)) / (1 + D / 100)

    # Penalidad arancelaria Trump 2026
    # friction = 0.70: solo el 70% del efecto se transmite (redireccionamiento parcial)
    tariff_penalty = (df["us_export_pct"] / 100) * (us_tariff / 100) * 0.70 * 100
    icg_penalized  = icg_raw - tariff_penalty * 0.25

    # Reescalar a [0, 100]
    mn, mx = icg_penalized.min(), icg_penalized.max()
    df["icg"] = ((icg_penalized - mn) / (mx - mn) * 100).clip(0, 100)

    # Categoría semántica
    df["icg_category"] = pd.cut(
        df["icg"],
        bins=[-1, 20, 40, 60, 80, 101],
        labels=["Crítico", "Vulnerable", "Intermedio", "Fuerte", "Dominante"],
    )

    # Delta arancelario (para visualizaciones)
    if us_tariff > 0:
        df_base_ref = compute_icg(
            df[["country", "iso3", "region", "export_critical_bn", "forex_reserves_bn",
                "energy_import_pct", "food_self_sufficiency", "gdp_bn",
                "us_export_pct", "sanctions_score", "bloc"]].copy(),
            us_tariff=0.0, w_leverage=w_leverage, w_resilience=w_resilience,
        )
        base_map = df_base_ref.set_index("country")["icg"].to_dict()
        df["icg_base"]  = df["country"].map(base_map)
        df["icg_delta"] = df["icg"] - df["icg_base"]
    else:
        df["icg_base"]  = df["icg"]
        df["icg_delta"] = 0.0

    return df.sort_values("icg", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# 8. VISUALIZACIONES
# ─────────────────────────────────────────────────────────────────────────────

def fig_choropleth(df: pd.DataFrame, metric: str = "icg") -> go.Figure:
    labels = {"icg": "ICG (0-100)", "leverage": "Apalancamiento",
              "resilience": "Resiliencia", "dependence": "Dependencia",
              "icg_delta": "Δ ICG"}
    titles = {"icg": "Índice de Conversión Geoeconómica — Global",
              "leverage": "Apalancamiento Geoeconómico",
              "resilience": "Resiliencia Estratégica",
              "dependence": "Dependencia Externa",
              "icg_delta": "Impacto Arancelario Trump 2026: Δ ICG"}

    fig = px.choropleth(
        df, locations="iso3", color=metric, hover_name="country",
        hover_data={"icg": ":.1f", "leverage": ":.1f", "resilience": ":.1f",
                    "dependence": ":.1f", "sanctions_score": ":.1f", "iso3": False},
        color_continuous_scale="RdYlGn" if metric == "icg_delta" else ICG_COLORSCALE,
        range_color=(df[metric].min(), df[metric].max()),
        title=titles.get(metric, metric), labels={metric: labels.get(metric, metric)},
    )
    fig.update_traces(marker_line_color="#1E3A5F", marker_line_width=0.7)
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(x=0.04, font=dict(size=13, color="#E8F4FD", family="Space Mono, monospace")),
        geo=dict(bgcolor="#080C14", showframe=False, showcoastlines=True,
                 coastlinecolor="#1E3A5F", showland=True, landcolor="#0A1220",
                 showocean=True, oceancolor="#060A10", projection_type="natural earth"),
        coloraxis_colorbar=dict(
            title=labels.get(metric, metric),
            tickfont=dict(family="Space Mono, monospace", size=8, color="#6B8BA4"),
            titlefont=dict(family="Space Mono, monospace", size=9, color="#4A9ECA"),
            len=0.55, thickness=11, bgcolor="#0D1F3C", bordercolor="#1E3A5F",
        ),
        height=460, margin=dict(t=55, b=5, l=0, r=0),
    )
    return fig


def fig_ranking_bar(df: pd.DataFrame, n: int = 22) -> go.Figure:
    df_p = df.head(n).copy()
    colors = df_p["icg"].map(lambda x:
        "#00D4AA" if x > 75 else "#3CB87A" if x > 55 else
        "#E8A020" if x > 38 else "#C84B11" if x > 20 else "#7F1010")

    fig = go.Figure(go.Bar(
        x=df_p["icg"], y=df_p["country"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df_p["icg"].round(1), textposition="outside",
        textfont=dict(family="Space Mono, monospace", size=8.5, color="#C8D6E5"),
        customdata=np.stack([df_p["leverage"], df_p["resilience"],
                             df_p["dependence"], df_p["icg_category"].astype(str)], axis=1),
        hovertemplate="<b>%{y}</b><br>ICG: %{x:.1f}<br>"
                      "Apalancamiento: %{customdata[0]:.1f}<br>"
                      "Resiliencia: %{customdata[1]:.1f}<br>"
                      "Dependencia: %{customdata[2]:.1f}<br>"
                      "Categoría: %{customdata[3]}<extra></extra>",
    ))
    fig.add_vline(x=50, line_dash="dash", line_color="#2A4A6A", line_width=1)
    fig.add_annotation(x=50, y=1, text="50", showarrow=False,
                       font=dict(color="#4A9ECA", size=8, family="Space Mono"),
                       yref="paper", xanchor="left", xshift=4)
    fig.update_layout(**DARK_LAYOUT,
        title=dict(text=f"Ranking ICG — {n} Países",
                   font=dict(family="Space Mono, monospace", size=12, color="#E8F4FD")),
        xaxis=dict(title="ICG (0-100)", range=[0, 118]),
        yaxis=dict(autorange="reversed", tickfont=dict(size=9)),
        height=max(480, n * 24), showlegend=False,
    )
    return fig


def fig_radar_dual(df: pd.DataFrame, country_a: str, country_b: str) -> go.Figure:
    """
    Radar de comparación dual: muestra 4 dimensiones para dos países.
    Dimensiones: Apalancamiento, Resiliencia, Autonomía Estratégica (1-dep), ICG.
    """
    dims = ["leverage", "resilience", "dependence_inv", "icg"]
    labels = ["Apalancamiento", "Resiliencia", "Aut. Estratégica", "ICG Global"]

    df_r = df.copy()
    df_r["dependence_inv"] = 100 - df_r["dependence"]   # invertir: menor dep = mejor

    rows = {c: df_r[df_r["country"] == c] for c in [country_a, country_b]}

    fig = go.Figure()
    colors = [RADAR_COLORS[0], RADAR_COLORS[1]]

    for i, (country, color) in enumerate(zip([country_a, country_b], colors)):
        row = rows[country]
        if row.empty:
            continue
        r = row.iloc[0]
        vals = [r[d] for d in dims] + [r[dims[0]]]     # cerrar polígono
        lbls = labels + [labels[0]]

        fig.add_trace(go.Scatterpolar(
            r=vals, theta=lbls, name=country,
            line=dict(color=color, width=2.5),
            fill="toself",
            fillcolor=color.replace("#", "rgba(") + ", 0.10)",
        ))

        # Puntos individuales para hover
        fig.add_trace(go.Scatterpolar(
            r=[r[d] for d in dims], theta=labels, name=f"{country} pts",
            mode="markers",
            marker=dict(color=color, size=8),
            showlegend=False,
            hovertemplate="<b>%{theta}</b>: %{r:.1f}<extra>" + country + "</extra>",
        ))

    fig.update_layout(
        **DARK_LAYOUT,
        polar=dict(
            bgcolor="#0A1220",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1A3050",
                            linecolor="#1A3050",
                            tickfont=dict(size=7, color="#6B8BA4", family="Space Mono")),
            angularaxis=dict(gridcolor="#1A3050", linecolor="#1A3050",
                             tickfont=dict(size=10, color="#C8D6E5")),
        ),
        title=dict(text=f"Comparación Dimensional: {country_a} vs. {country_b}",
                   font=dict(family="Space Mono, monospace", size=12, color="#E8F4FD")),
        showlegend=True,
        legend=dict(bgcolor="#0D1F3C", bordercolor="#1E3A5F", borderwidth=1,
                    font=dict(size=10)),
        height=440,
    )
    return fig


def build_comparison_table(df: pd.DataFrame, country_a: str, country_b: str) -> str:
    """Genera HTML de tabla comparativa dimensión a dimensión con badges de ganador."""
    df_r = df.copy()
    df_r["dependence_inv"] = 100 - df_r["dependence"]

    dims = [
        ("icg",            "ICG Global"),
        ("leverage",       "Apalancamiento"),
        ("resilience",     "Resiliencia"),
        ("dependence_inv", "Aut. Estratégica"),
        ("sanctions_score","Sanciones (0=mejor)"),
        ("us_export_pct",  "Expo. → EE.UU. (0=mejor)"),
        ("gdp_bn",         "PIB (bn USD)"),
    ]

    ra = df_r[df_r["country"] == country_a].iloc[0] if not df_r[df_r["country"] == country_a].empty else None
    rb = df_r[df_r["country"] == country_b].iloc[0] if not df_r[df_r["country"] == country_b].empty else None

    if ra is None or rb is None:
        return "<p>País no encontrado.</p>"

    rows_html = ""
    for col, label in dims:
        va, vb = float(ra[col]), float(rb[col])
        # Para sanciones y expo EEUU, menor es mejor
        lower_better = col in ("sanctions_score", "us_export_pct", "dependence")
        a_wins = (va > vb) if not lower_better else (va < vb)
        b_wins = (vb > va) if not lower_better else (vb < va)

        badge_a = '<span class="win-badge">✓ Gana</span>' if a_wins else ""
        badge_b = '<span class="win-badge">✓ Gana</span>' if b_wins else ""

        fmt = "{:,.0f}" if col == "gdp_bn" else "{:.1f}"
        rows_html += f"""
        <tr>
            <td style="color:#6B8BA4; font-size:0.82rem; padding:7px 10px;">{label}</td>
            <td style="font-family:'Space Mono',monospace; font-size:0.88rem;
                       color:{'#00D4AA' if a_wins else '#C8D6E5'}; text-align:center;">
                {fmt.format(va)} {badge_a}
            </td>
            <td style="font-family:'Space Mono',monospace; font-size:0.88rem;
                       color:{'#F0B429' if b_wins else '#C8D6E5'}; text-align:center;">
                {fmt.format(vb)} {badge_b}
            </td>
        </tr>"""

    return f"""
    <table style="width:100%; border-collapse:collapse;
                  background:#0A1628; border-radius:8px; overflow:hidden;">
        <thead>
            <tr style="background:#0D1F3C; border-bottom:1px solid #1E3A5F;">
                <th style="padding:10px; text-align:left; font-family:'Space Mono',monospace;
                           font-size:0.75rem; color:#4A9ECA; letter-spacing:0.1em;">DIMENSIÓN</th>
                <th style="padding:10px; text-align:center; font-family:'Space Mono',monospace;
                           font-size:0.75rem; color:#00D4AA;">{country_a.upper()}</th>
                <th style="padding:10px; text-align:center; font-family:'Space Mono',monospace;
                           font-size:0.75rem; color:#F0B429;">{country_b.upper()}</th>
            </tr>
        </thead>
        <tbody style="border: 1px solid #1E3A5F;">
            {rows_html}
        </tbody>
    </table>"""


def fig_scatter_matrix(df: pd.DataFrame) -> go.Figure:
    """Matriz geopolítica: Apalancamiento vs Resiliencia, burbujas = PIB, color = ICG."""
    fig = go.Figure()
    mid = 50
    for x0, x1, y0, y1, lbl, col in [
        (mid,105, mid,105, "POTENCIAS GLOBALES",      "rgba(0,212,170,0.04)"),
        (0,  mid, mid,105, "AUTARQUÍAS RESILIENTES",  "rgba(240,180,41,0.04)"),
        (mid,105, 0,  mid, "POTENCIAS VULNERABLES",   "rgba(74,158,202,0.04)"),
        (0,  mid, 0,  mid, "ESTADOS FRÁGILES",        "rgba(255,107,107,0.04)"),
    ]:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=col, line_width=0)
        fig.add_annotation(x=(x0+x1)/2, y=(y0+y1)/2, text=lbl, showarrow=False,
                           font=dict(size=7.5, color="#3A5A7A", family="Space Mono"),
                           opacity=0.8, align="center")

    fig.add_trace(go.Scatter(
        x=df["leverage"], y=df["resilience"], mode="markers+text",
        marker=dict(size=np.sqrt(df["gdp_bn"] / 22) + 7, color=df["icg"],
                    colorscale=ICG_COLORSCALE, showscale=True,
                    line=dict(color="#1E3A5F", width=1),
                    colorbar=dict(title="ICG", len=0.55, thickness=9,
                                  bgcolor="#0D1F3C", bordercolor="#1E3A5F",
                                  tickfont=dict(family="Space Mono", size=7))),
        text=df["country"], textposition="top center",
        textfont=dict(size=7.5, color="#C8D6E5", family="DM Sans"),
        hovertemplate="<b>%{text}</b><br>Apalancamiento: %{x:.1f}<br>"
                      "Resiliencia: %{y:.1f}<br>ICG: %{marker.color:.1f}<extra></extra>",
    ))
    fig.add_hline(y=50, line_dash="dot", line_color="#1E3A5F", line_width=1)
    fig.add_vline(x=50, line_dash="dot", line_color="#1E3A5F", line_width=1)
    fig.update_layout(**DARK_LAYOUT,
        title=dict(text="Matriz Geopolítica: Apalancamiento vs. Resiliencia",
                   font=dict(family="Space Mono, monospace", size=12, color="#E8F4FD")),
        xaxis=dict(title="Apalancamiento", range=[0, 105]),
        yaxis=dict(title="Resiliencia", range=[0, 105]),
        height=500,
    )
    return fig


def fig_tariff_impact(df_base: pd.DataFrame, df_shock: pd.DataFrame,
                       highlights: List[str]) -> go.Figure:
    """Barras horizontales mostrando Δ ICG por país con el arancel activo."""
    merged = df_base[["country", "icg", "us_export_pct"]].copy()
    merged["icg_shock"] = df_shock.set_index("country")["icg"].reindex(merged["country"]).values
    merged["delta"] = merged["icg_shock"] - merged["icg"]
    merged = merged.sort_values("delta").head(20)

    colors = merged["delta"].map(
        lambda x: "#FF6B6B" if x < -8 else "#F0B429" if x < -2 else "#4ADE80")

    fig = go.Figure(go.Bar(
        x=merged["delta"], y=merged["country"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=merged["delta"].round(2), textposition="outside",
        textfont=dict(family="Space Mono, monospace", size=8.5),
        hovertemplate="<b>%{y}</b><br>Δ ICG: %{x:.2f}<br>"
                      "Expo → EE.UU.: %{customdata:.1f}%<extra></extra>",
        customdata=merged["us_export_pct"],
    ))
    fig.add_vline(x=0, line_color="#4A9ECA", line_width=1.5)
    for c in highlights:
        row = merged[merged["country"] == c]
        if not row.empty:
            fig.add_annotation(x=row["delta"].values[0], y=c, text=f"◄ {c}",
                               showarrow=False, font=dict(color="#F0B429", size=9),
                               xanchor="right" if row["delta"].values[0] < 0 else "left")
    fig.update_layout(**DARK_LAYOUT,
        title=dict(text="Simulador Trump 2026: Impacto Arancelario por País",
                   font=dict(family="Space Mono, monospace", size=12, color="#E8F4FD")),
        xaxis=dict(title="Δ ICG (puntos)"),
        yaxis=dict(autorange="reversed"),
        height=480, showlegend=False,
    )
    return fig


def fig_tariff_trajectory(df_raw: pd.DataFrame, country: str,
                           step: int = 5) -> go.Figure:
    """Trayectoria ICG de un país a lo largo de 0-100% de arancel."""
    tariff_range = np.arange(0, 101, step)
    vals = []
    for t in tariff_range:
        sim = compute_icg(df_raw.copy(), us_tariff=float(t))
        row = sim[sim["country"] == country]
        vals.append(row["icg"].values[0] if not row.empty else np.nan)

    base = np.array(vals)
    opt  = np.clip(base * 1.10, 0, 100)
    pes  = np.clip(base * 0.90, 0, 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=np.concatenate([tariff_range, tariff_range[::-1]]),
        y=np.concatenate([opt, pes[::-1]]),
        fill="toself", fillcolor="rgba(74,158,202,0.09)",
        line=dict(color="rgba(74,158,202,0)"), name="Banda incertidumbre"))
    fig.add_trace(go.Scatter(x=tariff_range, y=opt, line=dict(color="#4A9ECA", width=1, dash="dot"), name="Optimista"))
    fig.add_trace(go.Scatter(x=tariff_range, y=base, line=dict(color="#F0B429", width=2.5), name=f"Base — {country}"))
    fig.add_trace(go.Scatter(x=tariff_range, y=pes, line=dict(color="#FF6B6B", width=1, dash="dot"), name="Pesimista"))

    for y_val, col, lbl in [(30, "#FF6B6B", "Crítico"), (60, "#4ADE80", "Fuerte")]:
        fig.add_hline(y=y_val, line_dash="dash", line_color=col, line_width=0.8,
                      annotation_text=lbl, annotation_font_color=col, annotation_font_size=8)
    for x_val, lbl in [(25, "Fase I\n2018"), (60, "Guerra\ncomercial"), (100, "Embargo")]:
        fig.add_vline(x=x_val, line_dash="dot", line_color="#1E3A5F", line_width=1)
        fig.add_annotation(x=x_val, y=97, text=lbl, showarrow=False,
                           font=dict(size=7.5, color="#4A9ECA", family="Space Mono"))

    fig.update_layout(**DARK_LAYOUT,
        title=dict(text=f"Trayectoria ICG: {country} vs. Escalada Arancelaria",
                   font=dict(family="Space Mono, monospace", size=12, color="#E8F4FD")),
        xaxis=dict(title="Arancel EE.UU. (%)", range=[0, 101]),
        yaxis=dict(title="ICG (0-100)", range=[0, 105]),
        height=400, legend=dict(orientation="h", y=-0.22),
    )
    return fig


def fig_news_sanction_bars(news_deltas: Dict[str, float]) -> go.Figure:
    """Muestra el ajuste de sanctions_score inducido por noticias recientes."""
    if not news_deltas:
        return go.Figure()
    df_n = pd.DataFrame(list(news_deltas.items()), columns=["country", "delta"])
    df_n = df_n[df_n["delta"] > 0].sort_values("delta", ascending=False)
    if df_n.empty:
        return go.Figure()

    colors = df_n["delta"].map(lambda x: "#FF6B6B" if x > 1.5 else "#F0B429")
    fig = go.Figure(go.Bar(
        x=df_n["delta"], y=df_n["country"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df_n["delta"].round(2), textposition="outside",
        textfont=dict(family="Space Mono, monospace", size=9),
        hovertemplate="<b>%{y}</b><br>Δ Sanciones: +%{x:.2f}<extra></extra>",
    ))
    fig.update_layout(**DARK_LAYOUT,
        title=dict(text="Ajuste Automático de Sanciones por Noticias",
                   font=dict(family="Space Mono, monospace", size=12, color="#E8F4FD")),
        xaxis=dict(title="Δ Sanctions Score"),
        yaxis=dict(autorange="reversed"),
        height=max(200, len(df_n) * 35 + 80), showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 9. LAYOUT PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def main():

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🎛️ Controles ICG")

        st.markdown("---")
        st.markdown("#### 🇺🇸 Simulador Trump 2026")
        st.markdown(
            '<div class="alert-box">Ajusta el arancel de EE.UU. y observa '
            'el impacto en tiempo real sobre el ICG global.</div>',
            unsafe_allow_html=True,
        )
        tariff = st.slider("Arancel EE.UU. (%)", 0, 100, 0, 5,
                           help="0%=sin choque | 25%=Guerra comercial Fase I | 100%=Embargo")

        st.markdown("---")
        st.markdown("#### ⚖️ Pesos del Índice")
        w_lev = st.slider("Peso Apalancamiento", 0.5, 2.0, 1.0, 0.1)
        w_res = st.slider("Peso Resiliencia",    0.5, 2.0, 1.0, 0.1)

        st.markdown("---")
        st.markdown("#### 📰 Noticias en Vivo")
        news_api_key = st.text_input(
            "NewsAPI Key", type="password",
            placeholder="Obtener gratis en newsapi.org",
            help="Gratis hasta 100 peticiones/día. newsapi.org/register",
        )
        news_query = st.text_input(
            "Búsqueda de noticias",
            value="sanctions tariffs trade war embargo",
            help="Palabras clave para detectar eventos que afectan las sanciones",
        )
        fetch_news = st.button("🔄 Actualizar noticias", use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔬 Países para Análisis")
        all_countries = sorted([
            "Australia", "Brazil", "Canada", "China", "France", "Germany",
            "India", "Indonesia", "Iran", "Japan", "Kazakhstan", "Mexico",
            "North Korea", "Poland", "Russia", "Saudi Arabia", "South Africa",
            "South Korea", "Turkey", "UAE", "United States", "Venezuela",
        ])
        highlight_countries = st.multiselect(
            "Destacar en Simulador", options=all_countries,
            default=["Iran", "China", "Mexico"],
        )

        st.markdown("---")
        st.markdown("""
        <div style="font-size:0.72rem; color:#3A5A7A; line-height:1.7;">
        <b>Fuentes de datos:</b><br>
        • World Bank WDI (GDP, energía, reservas)<br>
        • UN Comtrade HS27/26/84<br>
        • IMF IFS (reservas divisas)<br>
        • OFAC / EU Sanctions Map<br>
        • NewsAPI.org (noticias en vivo)<br><br>
        <i>Modo offline-first activo.</i>
        </div>
        """, unsafe_allow_html=True)

    # ── CARGA DE DATOS ───────────────────────────────────────────────────────
    with st.spinner("Cargando base de datos geopolítica..."):
        df_raw = build_database()

    # Noticias en vivo
    news_articles: List[Dict] = []
    news_deltas: Dict[str, float] = {}

    if fetch_news or (news_api_key and "news_articles" not in st.session_state):
        with st.spinner("Consultando NewsAPI..."):
            news_articles = fetch_news_live(news_api_key, news_query, page_size=25)
            news_deltas   = compute_news_sanctions_delta(news_articles)
            st.session_state["news_articles"] = news_articles
            st.session_state["news_deltas"]   = news_deltas
    elif "news_articles" in st.session_state:
        news_articles = st.session_state["news_articles"]
        news_deltas   = st.session_state["news_deltas"]

    # Calcular ICG
    df_base  = compute_icg(df_raw.copy(), us_tariff=0.0,
                           w_leverage=w_lev, w_resilience=w_res,
                           news_deltas=news_deltas if news_deltas else None)
    df_shock = compute_icg(df_raw.copy(), us_tariff=float(tariff),
                           w_leverage=w_lev, w_resilience=w_res,
                           news_deltas=news_deltas if news_deltas else None)

    # ── HEADER ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="icg-header">
        <div style="position:relative; z-index:1;">
            <div class="icg-badge">⬡ Sistema de Análisis Geopolítico · v2.0 · {datetime.now().year}</div>
            <h1 class="icg-title">Índice de Conversión Geoeconómica</h1>
            <p style="color:#6B8BA4; font-size:0.92rem; margin:6px 0 0; max-width:680px;">
                Mide la capacidad de un Estado para convertir sus recursos económicos en
                poder político internacional. Integra datos del Banco Mundial, UN Comtrade,
                IMF y noticias en tiempo real.
            </p>
            <div class="icg-formula">
                ICG = √( Apalancamiento × Resiliencia ) ÷ ( 1 + Dependencia/100 ) − Penalidad
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── MÉTRICAS ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    top    = df_shock.iloc[0]
    bottom = df_shock.iloc[-1]
    avg    = df_shock["icg"].mean()
    usa    = df_shock[df_shock["country"] == "United States"]["icg"]
    usa_v  = usa.values[0] if len(usa) else 0.0
    n_crit = int((df_shock["icg"] < 20).sum())

    usa_base = df_base[df_base["country"] == "United States"]["icg"]
    delta_usa = (usa_v - usa_base.values[0]) if len(usa_base) else 0.0

    for col, val, label, delta_str, dcolor in [
        (c1, top["country"].split()[0], "🏆 Mayor ICG",
         f'ICG = {top["icg"]:.1f}', "#4ADE80"),
        (c2, bottom["country"].split()[0], "⚠️ Menor ICG",
         f'ICG = {bottom["icg"]:.1f}', "#FF6B6B"),
        (c3, f"{avg:.1f}", "📊 Promedio Global",
         f'{len(df_shock)} países', "#6B8BA4"),
        (c4, f"{usa_v:.1f}", "🇺🇸 ICG EE.UU.",
         f'Δ {delta_usa:+.1f} con arancel', "#4ADE80" if delta_usa >= 0 else "#FF6B6B"),
        (c5, str(n_crit), "🚨 Estados Críticos",
         "ICG < 20 pts", "#6B8BA4"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1.55rem;">{val}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-delta" style="color:{dcolor};">{delta_str}</div>
        </div>""", unsafe_allow_html=True)

    # Alerta si hay ajuste por noticias
    if news_deltas:
        affected = ", ".join(f"**{c}** (+{v:.1f})" for c, v in
                             sorted(news_deltas.items(), key=lambda x: -x[1])[:5])
        st.markdown(
            f'<div class="alert-box">📡 <b>Ajuste de sanciones por noticias en vivo:</b> '
            f'{affected}</div>', unsafe_allow_html=True)

    if tariff > 0:
        st.markdown(
            f'<div class="alert-box">⚡ <b>Arancel Trump activo: {tariff}%</b> — '
            f'Los países con mayor dependencia de exportaciones a EE.UU. son los más afectados.</div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🌍 Mapa Global",
        "📊 Rankings",
        "🎯 Comparación Dual",
        "⚡ Simulador Trump",
        "📰 Noticias en Vivo",
        "📋 Metodología",
    ])

    # ── TAB 1: MAPA ──────────────────────────────────────────────────────────
    with tab1:
        col_map, col_ctrl = st.columns([3.2, 0.8])
        with col_ctrl:
            st.markdown("**Métrica**")
            metric = st.radio("", ["icg", "leverage", "resilience", "dependence", "icg_delta"],
                format_func=lambda x: {
                    "icg": "🌐 ICG", "leverage": "⚡ Apalancamiento",
                    "resilience": "🛡️ Resiliencia", "dependence": "🔗 Dependencia",
                    "icg_delta": "📉 Δ ICG",
                }[x], label_visibility="collapsed")
            st.markdown("---")
            for cat, clr, rng in [
                ("Dominante", "#00D4AA", "80-100"), ("Fuerte",    "#3CB87A", "60-80"),
                ("Intermedio","#E8A020", "40-60"),  ("Vulnerable","#C84B11", "20-40"),
                ("Crítico",   "#7F1010", "0-20"),
            ]:
                st.markdown(
                    f'<span style="color:{clr}; font-family:Space Mono; font-size:0.78rem;">■ {cat}</span> '
                    f'<span style="color:#6B8BA4; font-size:0.73rem;">({rng})</span>',
                    unsafe_allow_html=True)
        with col_map:
            st.plotly_chart(fig_choropleth(df_shock, metric),
                            use_container_width=True, config={"scrollZoom": True})

    # ── TAB 2: RANKINGS ──────────────────────────────────────────────────────
    with tab2:
        r1, r2 = st.columns([1.3, 1])
        with r1:
            n = st.slider("Número de países", 10, 22, 22, 1)
            st.plotly_chart(fig_ranking_bar(df_shock, n), use_container_width=True)
        with r2:
            st.plotly_chart(fig_scatter_matrix(df_shock), use_container_width=True)

    # ── TAB 3: COMPARACIÓN DUAL ───────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="compare-header">⬡ RADAR DE COMPARACIÓN DIMENSIONAL</div>',
                    unsafe_allow_html=True)
        st.markdown("Selecciona dos países para analizar en qué dimensión gana cada uno.")

        cc1, cc2 = st.columns(2)
        with cc1:
            country_a = st.selectbox("🟢 País A", all_countries,
                                     index=all_countries.index("United States"))
        with cc2:
            country_b = st.selectbox("🟡 País B", all_countries,
                                     index=all_countries.index("China"))

        if country_a == country_b:
            st.warning("Selecciona dos países distintos para la comparación.")
        else:
            # Radar
            st.plotly_chart(fig_radar_dual(df_shock, country_a, country_b),
                            use_container_width=True)

            # Tabla comparativa
            st.markdown("#### Tabla Dimensión a Dimensión")
            st.markdown(
                build_comparison_table(df_shock, country_a, country_b),
                unsafe_allow_html=True,
            )

            # Resumen interpretativo
            ra = df_shock[df_shock["country"] == country_a].iloc[0]
            rb = df_shock[df_shock["country"] == country_b].iloc[0]
            winner_icg    = country_a if ra["icg"] > rb["icg"] else country_b
            winner_lev    = country_a if ra["leverage"] > rb["leverage"] else country_b
            winner_res    = country_a if ra["resilience"] > rb["resilience"] else country_b
            winner_indep  = country_a if ra["dependence"] < rb["dependence"] else country_b

            st.markdown(f"""
            <div style="background:#0A1628; border:1px solid #1E3A5F; border-radius:10px;
                        padding:16px 20px; margin-top:14px;">
                <span style="font-family:Space Mono; font-size:0.75rem; color:#4A9ECA;
                             letter-spacing:0.1em;">SÍNTESIS COMPARATIVA</span><br><br>
                <span style="font-size:0.87rem; color:#C8D6E5; line-height:2;">
                🏆 <b>Mayor ICG global:</b> {winner_icg}<br>
                ⚡ <b>Mayor apalancamiento</b> (exportaciones + reservas): {winner_lev}<br>
                🛡️ <b>Mayor resiliencia</b> (energía + alimentos): {winner_res}<br>
                🔓 <b>Mayor autonomía estratégica</b> (menor dependencia): {winner_indep}
                </span>
            </div>""", unsafe_allow_html=True)

    # ── TAB 4: SIMULADOR TRUMP ────────────────────────────────────────────────
    with tab4:
        st.markdown("""
        <div class="alert-box" style="border-color:rgba(240,180,41,0.5); font-size:0.9rem;">
        <b>🎯 Caso de Estudio: Aranceles Trump 2026</b><br>
        El simulador transmite el choque arancelario a través de la fórmula:<br>
        <code>Penalidad_i = (exp_EE.UU._i / 100) × (T / 100) × 0.70 × 100</code><br>
        Factor de fricción 0.70: no toda la producción afectada se redirige perfectamente.
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.plotly_chart(fig_tariff_impact(df_base, df_shock, highlight_countries),
                        use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔮 Trayectoria de País Específico")
        sc1, sc2 = st.columns([1, 3])
        with sc1:
            country_sim = st.selectbox(
                "País a simular", sorted(df_base["country"].tolist()),
                index=sorted(df_base["country"].tolist()).index("Iran")
                      if "Iran" in df_base["country"].tolist() else 0)
            reso = st.radio("Resolución", ["Baja (5%)", "Alta (1%)"])
        with sc2:
            step_val = 5 if "Baja" in reso else 1
            with st.spinner(f"Simulando para {country_sim}..."):
                st.plotly_chart(fig_tariff_trajectory(df_raw.copy(), country_sim, step_val),
                                use_container_width=True)

        # Panel interpretación
        cd  = df_shock[df_shock["country"] == country_sim]
        if not cd.empty:
            row = cd.iloc[0]
            icg_now  = row["icg"]
            icg_base = df_base[df_base["country"] == country_sim]["icg"].values[0]
            delta    = icg_now - icg_base
            dep_pct  = row["us_export_pct"]
            ic       = "#FF6B6B" if delta < -5 else "#F0B429" if delta < 0 else "#4ADE80"
            msg = (f"⚠️ <b>Alta vulnerabilidad:</b> {country_sim} exporta {dep_pct:.1f}% a EE.UU. "
                   f"Un arancel de {tariff}% erosiona significativamente su ICG."
                   if dep_pct > 20 else
                   f"⚡ <b>Exposición moderada:</b> {dep_pct:.1f}% hacia EE.UU. Impacto contenido."
                   if dep_pct > 5 else
                   f"🛡️ <b>Alta resiliencia al choque:</b> Solo {dep_pct:.1f}% expo a EE.UU. "
                   f"El ICG de {country_sim} depende de otros vectores.")
            st.markdown(f"""
            <div style="background:#0A1628; border:1px solid #1E3A5F; border-radius:10px;
                        padding:16px 20px; margin-top:12px;">
                <span style="font-family:Space Mono; font-size:0.78rem; color:#4A9ECA;">
                    ANÁLISIS — {country_sim.upper()} · ARANCEL {tariff}%
                </span><br><br>
                <span style="font-family:Space Mono; font-size:1.25rem; color:{ic};">
                    ΔICG = {delta:+.2f} pts
                </span>
                &nbsp;|&nbsp;
                <span style="color:#6B8BA4; font-size:0.88rem;">
                    {icg_base:.1f} → {icg_now:.1f}
                </span><br><br>
                <span style="font-size:0.86rem; color:#C8D6E5;">{msg}</span>
            </div>""", unsafe_allow_html=True)

    # ── TAB 5: NOTICIAS EN VIVO ───────────────────────────────────────────────
    with tab5:
        st.markdown("#### 📡 Monitor de Sanciones y Aranceles en Tiempo Real")
        st.markdown(
            "Las noticias detectadas como relevantes ajustan automáticamente el "
            "`sanctions_score` de los países mencionados, lo que modifica su ICG en "
            "tiempo real. Introduce tu **NewsAPI key** en el panel lateral para activar esta función."
        )

        if not news_articles:
            st.info(
                "No hay noticias cargadas. Introduce una NewsAPI key en el panel lateral "
                "y pulsa **Actualizar noticias**. Registro gratuito en [newsapi.org](https://newsapi.org/register)."
            )
        else:
            n1, n2 = st.columns([2, 1])
            with n1:
                st.markdown(f"**{len(news_articles)} artículos analizados** — "
                            f"{sum(1 for a in news_articles if a['impact'] >= 2)} de alto impacto")
                for art in news_articles[:15]:
                    impact_lvl = "high" if art["impact"] >= 2 else "medium" if art["impact"] == 1 else "low"
                    impact_lbl = {
                        "high": '<span class="news-impact-badge badge-high">ALTO</span>',
                        "medium": '<span class="news-impact-badge badge-medium">MEDIO</span>',
                        "low": '<span class="news-impact-badge badge-low">BAJO</span>',
                    }[impact_lvl]
                    countries_str = (", ".join(art["countries"][:3]) if art["countries"]
                                     else "<span style='color:#3A5A7A'>Sin país detectado</span>")
                    pub_short = art["published"][:10] if art["published"] else "—"
                    st.markdown(f"""
                    <div class="news-card">
                        <div class="news-title">{art['title']} {impact_lbl}</div>
                        <div class="news-meta">
                            {art['source']} · {pub_short} · Países: {countries_str}
                            · <a href="{art['url']}" target="_blank"
                               style="color:#4A9ECA; text-decoration:none;">Leer →</a>
                        </div>
                    </div>""", unsafe_allow_html=True)

            with n2:
                if news_deltas:
                    st.markdown("**Ajuste automático de sanciones**")
                    st.plotly_chart(fig_news_sanction_bars(news_deltas),
                                    use_container_width=True)
                    st.markdown("**Países más afectados por noticias:**")
                    for c, delta in sorted(news_deltas.items(), key=lambda x: -x[1])[:8]:
                        bar_w = int(delta / 2.5 * 100)
                        st.markdown(f"""
                        <div style="margin:4px 0;">
                            <span style="font-family:Space Mono; font-size:0.8rem; color:#C8D6E5;">
                                {c}
                            </span>
                            <div style="background:#1A3050; border-radius:3px; height:6px; margin-top:3px;">
                                <div style="background:#F0B429; width:{bar_w}%;
                                            height:6px; border-radius:3px;"></div>
                            </div>
                            <span style="font-family:Space Mono; font-size:0.72rem; color:#F0B429;">
                                +{delta:.2f} pts sanciones
                            </span>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("Carga noticias para ver el ajuste por país.")

    # ── TAB 6: METODOLOGÍA ────────────────────────────────────────────────────
    with tab6:
        m1, m2 = st.columns(2)
        with m1:
            st.markdown("#### 📐 Fórmula y Calibración")
            st.markdown(r"""
**Fórmula central (v3):**

$$ICG = \frac{\sqrt{L^{w_L} \times R^{w_R}}}{1 + D/100} - Penalidad_{Arancelaria}$$

**Subíndices:**

| | Variables | Pesos |
|---|---|---|
| **L** Apalancamiento | ln(Exp. críticas) + ln(Reservas) − Sanciones | 55%+35%−10% |
| **R** Resiliencia | −Energía importada + Autosuf. alimentaria + Bono PIB | 50%+50%+bono |
| **D** Dependencia | Expo→EE.UU. + Sanciones (normaliz.) | 65%+35% |

**Penalidad arancelaria:**

$$Pen_i = \frac{exp_{EE.UU.,i}}{100} \times \frac{T}{100} \times 0.70 \times 100 \times 0.25$$

(0.70 = friction factor; 0.25 = escala al ICG)

**Ajuste por noticias:**

$$\Delta S_i = \sum_j \frac{impact_j}{3} \times w_{temporal} \times 0.8$$

donde $w_{temporal}$ = 2.0 si < 6h, 1.5 si < 24h, 1.0 en otro caso.

**Calibración validada:**

| País | ICG base | Δ arancel 100% |
|---|---|---|
| EE.UU. | 100.0 | 0.0 |
| Arabia Saudí | 96.0 | −2.4 |
| Rusia | 83.5 | −0.3 |
| China | 76.0 | −4.7 |
| Canadá | 68.2 | −20.4 |
| México | 39.1 | **−22.3** |
| Irán | 49.3 | 0.0 |
""")

        with m2:
            st.markdown("#### 🔌 Arquitectura de APIs")
            st.code("""
# ── Banco Mundial ────────────────────────
import wbgapi as wb

# PIB (NY.GDP.MKTP.CD)
gdp = wb.data.DataFrame("NY.GDP.MKTP.CD",
    economy="all", mrv=1)

# Energía (EG.IMP.CONS.ZS)
energy = wb.data.DataFrame("EG.IMP.CONS.ZS",
    economy="all", mrv=1)

# Reservas (FI.RES.TOTL.CD)
res = wb.data.DataFrame("FI.RES.TOTL.CD",
    economy="all", mrv=1)

# ── UN Comtrade ──────────────────────────
# HS 27 = Combustibles minerales
url = ("https://comtradeapi.un.org/public/v1"
       "/preview/C/A/HS?reporterCode=156"
       "&period=2022&cmdCode=27&flowCode=X")
data = requests.get(url, headers={
    "Ocp-Apim-Subscription-Key": KEY
}).json()["data"]

# ── IMF IFS ──────────────────────────────
# Reservas de divisas por país
imf = requests.get(
    "http://dataservices.imf.org/REST"
    "/SDMX_JSON.svc/CompactData"
    "/IFS/Q.CN.RESERVES.FX"
    "?startPeriod=2022&endPeriod=2022"
).json()

# ── NewsAPI ───────────────────────────────
news = requests.get(
    "https://newsapi.org/v2/everything",
    params={"q": "sanctions tariffs",
            "sortBy": "publishedAt",
            "pageSize": 25,
            "apiKey": NEWS_KEY}
).json()["articles"]
            """, language="python")

            st.markdown("#### 📦 Instalación y ejecución")
            st.code("""
# Instalar dependencias
pip install streamlit plotly pandas numpy requests wbgapi

# Configurar API keys (.streamlit/secrets.toml)
[secrets]
COMTRADE_KEY = "tu-key-comtrade"
NEWS_API_KEY = "tu-key-newsapi"
# Banco Mundial e IMF: sin key requerida

# Ejecutar
streamlit run icg_dashboard.py
            """, language="bash")

        # Tabla completa de datos
        st.markdown("---")
        st.markdown("#### 🗃️ Base de Datos Completa")

        fcol, scol = st.columns(2)
        with fcol:
            cat_f = st.multiselect("Filtrar categoría",
                ["Dominante", "Fuerte", "Intermedio", "Vulnerable", "Crítico"],
                default=["Dominante", "Fuerte", "Intermedio", "Vulnerable", "Crítico"])
        with scol:
            sort_f = st.selectbox("Ordenar por",
                ["icg", "leverage", "resilience", "dependence",
                 "gdp_bn", "us_export_pct", "sanctions_score"],
                format_func=lambda x: {
                    "icg": "ICG", "leverage": "Apalancamiento",
                    "resilience": "Resiliencia", "dependence": "Dependencia",
                    "gdp_bn": "PIB (bn USD)", "us_export_pct": "% Expo → EE.UU.",
                    "sanctions_score": "Sanciones",
                }[x])

        disp = df_shock[df_shock["icg_category"].astype(str).isin(cat_f)]\
            .sort_values(sort_f, ascending=False)[[
                "country", "icg", "icg_category", "leverage", "resilience",
                "dependence", "gdp_bn", "export_critical_bn", "forex_reserves_bn",
                "energy_import_pct", "food_self_sufficiency",
                "us_export_pct", "sanctions_score", "icg_delta",
            ]].rename(columns={
                "country": "País", "icg": "ICG", "icg_category": "Categoría",
                "leverage": "Apalancam.", "resilience": "Resiliencia",
                "dependence": "Dependencia", "gdp_bn": "PIB (bn$)",
                "export_critical_bn": "Exp.Crít.", "forex_reserves_bn": "Reservas",
                "energy_import_pct": "Energía imp.%", "food_self_sufficiency": "Alim.%",
                "us_export_pct": "Exp.→EE.UU.%", "sanctions_score": "Sanciones",
                "icg_delta": "ΔICG",
            })

        st.dataframe(
            disp.style.format({
                "ICG": "{:.1f}", "Apalancam.": "{:.1f}", "Resiliencia": "{:.1f}",
                "Dependencia": "{:.1f}", "PIB (bn$)": "{:,.0f}",
                "Exp.Crít.": "{:.0f}", "Reservas": "{:.0f}",
                "Energía imp.%": "{:.0f}", "Alim.%": "{:.0f}",
                "Exp.→EE.UU.%": "{:.1f}", "Sanciones": "{:.1f}", "ΔICG": "{:+.2f}",
            }).background_gradient(subset=["ICG"], cmap="RdYlGn", vmin=0, vmax=100)
             .background_gradient(subset=["ΔICG"], cmap="RdYlGn", vmin=-25, vmax=5),
            use_container_width=True, hide_index=True, height=460,
        )

    # ── FOOTER ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:24px 0 8px;
                border-top:1px solid #1A3050; margin-top:28px;">
        <span style="font-family:Space Mono,monospace; font-size:0.72rem;
                     color:#2A4A6A; letter-spacing:0.12em;">
        ICG DASHBOARD v2.0 · CIENCIA DE DATOS & GEOPOLÍTICA<br>
        World Bank WDI · UN Comtrade · IMF IFS · NewsAPI.org · OFAC
        </span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
