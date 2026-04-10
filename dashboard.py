"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GEOECONOMIC INTELLIGENCE TERMINAL — ICG v3.0                              ║
║   Índice de Conversión Geoeconómica · Sistema Multicapa                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Arquitectura:                                                               ║
║    Capa 1: BASE_ICG         → capacidad estructural (percentile rank)       ║
║    Capa 2: FRICTION_LAYER   → poder regulatorio y barreras reales           ║
║    Capa 3: SIGNAL_LAYER     → alineación estratégica institucional          ║
║    Capa 4: CAPITAL_LAYER    → validación financiera de la tesis             ║
║    Capa 5: SHOCK_LAYER      → perturbaciones recientes                      ║
║    Capa 6: THEME_ENGINE     → lente temático (chips/energía/minerales...)   ║
║                                                                              ║
║  Correcciones metodológicas vs v1/v2:                                       ║
║    · Percentile rank en lugar de min-max (panel-invariante)                 ║
║    · Penalidad de sanciones convexa por régimen discreto                    ║
║    · Separación stocks (reservas) vs flows (exportaciones)                  ║
║    · Dependencia con penalidad exponencial, no lineal                       ║
║    · Overlays separados del índice base                                     ║
║    · Fricción regulatoria como dimensión propia                             ║
║                                                                              ║
║  Instalación: pip install streamlit plotly pandas numpy requests            ║
║  Ejecución:   streamlit run app.py                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GeoIntel Terminal · ICG v3.0",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta & tipografía ─────────────────────────────────────────────────────
C = {
    "bg":       "#05080F",
    "panel":    "#090E1A",
    "border":   "#162035",
    "border2":  "#1E3050",
    "text":     "#B8CCDF",
    "text2":    "#6A8BA8",
    "accent1":  "#00C9A7",   # verde cian — potencia
    "accent2":  "#F0A500",   # ámbar     — señal
    "accent3":  "#4A9ECA",   # azul      — información
    "danger":   "#E53E3E",   # rojo      — riesgo
    "warning":  "#DD6B20",   # naranja   — alerta
}

COLORSCALE_ICG = [
    [0.00, "#1A0000"], [0.15, "#6B0F0F"], [0.28, "#C0390A"],
    [0.42, "#D4820A"], [0.55, "#B8B800"], [0.70, "#3DB87A"],
    [0.85, "#00C9A7"], [1.00, "#00E5CC"],
]

THEMES = {
    "🌐 Global":             None,
    "⚡ Energía":            "energy",
    "🔬 Semiconductores":    "chips",
    "⛏️ Minerales Críticos": "minerals",
    "🌾 Alimentos":          "food",
    "🚢 Shipping / Logística": "shipping",
    "🛡️ Defensa":            "defense",
    "🤖 IA / Digital":       "ai_digital",
}

BLOCS = {
    "G7":    ["United States","Germany","Japan","France","Canada","Italy","United Kingdom"],
    "BRICS": ["Brazil","Russia","India","China","South Africa","Iran","Egypt","UAE","Ethiopia","Argentina"],
    "UE":    ["Germany","France","Poland","Italy","Netherlands","Spain"],
    "Quad":  ["United States","Japan","Australia","India"],
    "ASEAN": ["Indonesia","Vietnam","Thailand","Malaysia","Philippines"],
    "GCC":   ["Saudi Arabia","UAE","Kuwait","Qatar","Oman","Bahrain"],
}

# ─────────────────────────────────────────────────────────────────────────────
# ESTILOS CSS — "Geo-Risk Lab Terminal"
# Estética: monocromo oscuro + acento cian/ámbar, tipografía editorial técnica
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: {C['bg']};
    color: {C['text']};
}}

/* ── Terminal header ── */
.geo-header {{
    background: linear-gradient(160deg, #080D1A 0%, #0A1525 60%, #060B14 100%);
    border: 1px solid {C['border2']};
    border-top: 2px solid {C['accent1']};
    border-radius: 0 0 8px 8px;
    padding: 22px 32px 18px;
    margin-bottom: 20px;
    position: relative;
}}
.geo-header::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, {C['accent1']}40, transparent);
}}
.geo-eyebrow {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {C['accent1']};
    margin-bottom: 6px;
}}
.geo-title {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.65rem;
    font-weight: 600;
    color: #E2EAF4;
    letter-spacing: -0.02em;
    margin: 0 0 4px;
}}
.geo-sub {{
    font-size: 0.82rem;
    color: {C['text2']};
    max-width: 660px;
    line-height: 1.5;
}}
.geo-formula {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: {C['accent2']};
    background: rgba(240,165,0,0.06);
    border-left: 2px solid {C['accent2']};
    padding: 7px 12px;
    border-radius: 0 4px 4px 0;
    margin-top: 12px;
    display: inline-block;
}}

/* ── Layer badges ── */
.layer-badge {{
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    padding: 2px 8px;
    border-radius: 3px;
    margin-right: 6px;
    vertical-align: middle;
}}
.badge-base    {{ background: rgba(0,201,167,0.12); color:{C['accent1']}; border:1px solid {C['accent1']}55; }}
.badge-friction{{ background: rgba(229,62,62,0.10); color:{C['danger']};  border:1px solid {C['danger']}55; }}
.badge-signal  {{ background: rgba(74,158,202,0.10); color:{C['accent3']};border:1px solid {C['accent3']}55; }}
.badge-capital {{ background: rgba(240,165,0,0.10); color:{C['accent2']};border:1px solid {C['accent2']}55; }}
.badge-shock   {{ background: rgba(221,107,32,0.12); color:{C['warning']};border:1px solid {C['warning']}55; }}

/* ── Stat cards ── */
.stat-card {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
}}
.stat-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}}
.stat-card.c1::before {{ background: {C['accent1']}; }}
.stat-card.c2::before {{ background: {C['accent2']}; }}
.stat-card.c3::before {{ background: {C['accent3']}; }}
.stat-card.c4::before {{ background: {C['danger']}; }}
.stat-card.c5::before {{ background: {C['warning']}; }}
.stat-val {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.9rem;
    font-weight: 600;
    line-height: 1;
    color: #E2EAF4;
}}
.stat-lbl {{
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {C['text2']};
    margin-top: 5px;
}}
.stat-delta {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    margin-top: 3px;
}}

/* ── Section header ── */
.sec-header {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {C['accent3']};
    border-bottom: 1px solid {C['border']};
    padding-bottom: 6px;
    margin: 0 0 14px;
}}

/* ── Alert ── */
.geo-alert {{
    background: rgba(240,165,0,0.07);
    border: 1px solid rgba(240,165,0,0.30);
    border-radius: 5px;
    padding: 10px 14px;
    font-size: 0.84rem;
    color: {C['accent2']};
    margin: 8px 0;
    line-height: 1.5;
}}
.geo-alert.danger {{
    background: rgba(229,62,62,0.07);
    border-color: rgba(229,62,62,0.30);
    color: {C['danger']};
}}
.geo-alert.info {{
    background: rgba(74,158,202,0.07);
    border-color: rgba(74,158,202,0.30);
    color: {C['accent3']};
}}

/* ── Insight box ── */
.insight-box {{
    background: {C['panel']};
    border: 1px solid {C['border2']};
    border-radius: 6px;
    padding: 14px 18px;
    font-size: 0.86rem;
    color: {C['text']};
    line-height: 1.7;
    margin-top: 10px;
}}
.insight-box .label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.15em;
    color: {C['accent3']};
    margin-bottom: 6px;
    display: block;
}}

/* ── Win badge ── */
.win-badge {{
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem;
    padding: 2px 7px;
    border-radius: 3px;
    background: rgba(0,201,167,0.12);
    color: {C['accent1']};
    border: 1px solid {C['accent1']}66;
    margin-left: 6px;
    vertical-align: middle;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: #040710;
    border-right: 1px solid {C['border']};
}}

/* ── Convergence cell ── */
.conv-cell {{
    display: inline-block;
    width: 24px; height: 24px;
    border-radius: 3px;
    text-align: center;
    line-height: 24px;
    font-size: 0.7rem;
    font-family: 'IBM Plex Mono', monospace;
}}
.conv-3 {{ background: rgba(0,201,167,0.30); color:{C['accent1']}; }}
.conv-2 {{ background: rgba(240,165,0,0.25); color:{C['accent2']}; }}
.conv-1 {{ background: rgba(74,158,202,0.15); color:{C['accent3']}; }}
.conv-0 {{ background: rgba(255,255,255,0.03); color:{C['text2']}; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA LAYER — BASE DATABASE (50 países, ca. 2022-2024)
# ─────────────────────────────────────────────────────────────────────────────

SANCTION_REGIMES = {
    # "none" | "targeted" | "sectoral" | "partial" | "maximum"
    "United States": "none",    "China": "sectoral",  "Russia": "partial",
    "Iran": "maximum",          "Saudi Arabia": "targeted", "India": "none",
    "Brazil": "none",           "Germany": "none",    "Japan": "none",
    "Mexico": "none",           "Canada": "none",     "Australia": "none",
    "South Korea": "none",      "France": "none",     "UAE": "targeted",
    "Turkey": "targeted",       "South Africa": "none","Indonesia": "none",
    "Poland": "none",           "North Korea": "maximum","Venezuela": "partial",
    "Kazakhstan": "targeted",   "Vietnam": "none",    "Malaysia": "none",
    "Thailand": "none",         "Nigeria": "none",    "Egypt": "none",
    "Argentina": "none",        "Colombia": "none",   "Chile": "none",
    "Netherlands": "none",      "Italy": "none",      "Spain": "none",
    "Sweden": "none",           "Norway": "none",     "Switzerland": "none",
    "Israel": "none",           "Taiwan": "none",     "Bangladesh": "none",
    "Pakistan": "none",         "Philippines": "none","Ethiopia": "none",
    "United Kingdom": "none",   "Qatar": "none",      "Kuwait": "none",
    "Morocco": "none",          "Kenya": "none",      "Ghana": "none",
    "Peru": "none",             "Ecuador": "none",
}

SANCTION_PENALTY = {
    "none": 0.00, "targeted": 0.08, "sectoral": 0.22,
    "partial": 0.45, "maximum": 0.78,
}

def build_database() -> pd.DataFrame:
    """
    Base de datos geopolítica ampliada — 50 países, ca. 2022-2024.

    Variables stocks (S) y flows (F) separadas.
    Fuentes primarias documentadas en comentarios inline.

    NUEVAS variables vs v1/v2:
    - supply_chain_centrality : nodo en CGV (OECD TiVA proxy)
    - import_strategic_dep    : concentración importaciones críticas [0-10]
    - ntm_density             : medidas no arancelarias activas (UNCTAD TRAINS proxy)
    - export_control_score    : membresía regímenes de control (Wassenaar, NSG, etc.)
    - standards_power         : capacidad de imponer estándares (ISO, 3GPP, CODEX)
    - institutional_signal    : frecuencia aparición en docs IMF/WB/OECD/G20
    - think_tank_consensus    : score consenso Brookings/CSIS/CFR/Chatham/ECFR
    - fdi_quality             : % IED en sectores estratégicos (UNCTAD WIR)
    - multi_alignment         : membresía en bloques simultáneos (0-6)
    - theme_scores            : relevancia por tema [0-10]
    """
    data = {
        # ── POTENCIAS G7 ──────────────────────────────────────────────────
        "United States": dict(
            iso3="USA", region="América del Norte", bloc_primary="G7",
            # S = stock, F = flow
            export_critical_bn=285,  # F - EIA/Comtrade 2022
            forex_reserves_bn=246,   # S - Fed/Treasury 2022
            energy_net_export=12,    # F - exportador neto % consumo (EIA)
            food_self_suff=130,      # F - USDA 2022
            gdp_bn=25464,            # S - WB 2022
            supply_chain_centrality=95,  # OECD TiVA: hub global (normalizado 0-100)
            import_strategic_dep=3,      # baja dep. importaciones críticas
            us_export_pct=0,
            import_concentration_hhi=0.08,  # diversificado
            sanctions_regime="none",
            # Fricción regulatoria
            ntm_density=78,          # UNCTAD TRAINS: alta densidad (impone barreras)
            export_control_score=10, # Wassenaar + NSG + MTCR + unilateral
            standards_power=95,      # ISO + 3GPP + CODEX + liderazgo OTAN
            compliance_burden=55,    # PMR OECD moderado
            # Señal estratégica
            institutional_signal=92, # aparece en casi todos los docs
            think_tank_consensus=88, # Brookings/CSIS/CFR/Chatham
            strategic_concept_density=98,
            # Capital
            fdi_quality=68,          # % IED en sectores estratégicos
            sovereign_capex_signal=85,
            # Multi-alineación
            multi_alignment=5,       # G7 + Quad + Five Eyes + AUKUS + NATO
            # Shock reciente [0-10, 10=max shock]
            shock_score=1.5,
            # Theme scores [0-10]
            theme_energy=8, theme_chips=10, theme_minerals=7,
            theme_food=7, theme_shipping=6, theme_defense=10,
            theme_ai=10, theme_shipping_s=6,
        ),
        "Germany": dict(
            iso3="DEU", region="Europa Occidental", bloc_primary="G7/UE",
            export_critical_bn=145, forex_reserves_bn=295,
            energy_net_export=-61, food_self_suff=93, gdp_bn=4072,
            supply_chain_centrality=78, import_strategic_dep=6,
            us_export_pct=9.5, import_concentration_hhi=0.14,
            sanctions_regime="none",
            ntm_density=72, export_control_score=8, standards_power=82,
            compliance_burden=42,
            institutional_signal=75, think_tank_consensus=72,
            strategic_concept_density=78,
            fdi_quality=58, sovereign_capex_signal=62,
            multi_alignment=4,  # G7 + UE + NATO + Wassenaar
            shock_score=3.5,   # transición energética post-Rusia
            theme_energy=5, theme_chips=7, theme_minerals=5,
            theme_food=5, theme_shipping=6, theme_defense=7,
            theme_ai=7, theme_shipping_s=5,
        ),
        "Japan": dict(
            iso3="JPN", region="Asia Oriental", bloc_primary="G7/Quad",
            export_critical_bn=120, forex_reserves_bn=1291,
            energy_net_export=-85, food_self_suff=38, gdp_bn=4231,
            supply_chain_centrality=72, import_strategic_dep=8,
            us_export_pct=19, import_concentration_hhi=0.18,
            sanctions_regime="none",
            ntm_density=65, export_control_score=8, standards_power=78,
            compliance_burden=48,
            institutional_signal=70, think_tank_consensus=68,
            strategic_concept_density=72,
            fdi_quality=55, sovereign_capex_signal=60,
            multi_alignment=4,
            shock_score=2.0,
            theme_energy=3, theme_chips=9, theme_minerals=4,
            theme_food=3, theme_shipping=7, theme_defense=7,
            theme_ai=8, theme_shipping_s=7,
        ),
        "France": dict(
            iso3="FRA", region="Europa Occidental", bloc_primary="G7/UE",
            export_critical_bn=85, forex_reserves_bn=242,
            energy_net_export=-45, food_self_suff=122, gdp_bn=2784,
            supply_chain_centrality=65, import_strategic_dep=5,
            us_export_pct=7.5, import_concentration_hhi=0.12,
            sanctions_regime="none",
            ntm_density=70, export_control_score=8, standards_power=80,
            compliance_burden=40,
            institutional_signal=72, think_tank_consensus=68,
            strategic_concept_density=74,
            fdi_quality=55, sovereign_capex_signal=60,
            multi_alignment=4,
            shock_score=2.5,
            theme_energy=6, theme_chips=6, theme_minerals=5,
            theme_food=6, theme_shipping=5, theme_defense=8,
            theme_ai=7, theme_shipping_s=5,
        ),
        "Canada": dict(
            iso3="CAN", region="América del Norte", bloc_primary="G7",
            export_critical_bn=210, forex_reserves_bn=106,
            energy_net_export=58, food_self_suff=185, gdp_bn=2140,
            supply_chain_centrality=58, import_strategic_dep=3,
            us_export_pct=73.2, import_concentration_hhi=0.55,
            sanctions_regime="none",
            ntm_density=60, export_control_score=8, standards_power=68,
            compliance_burden=38,
            institutional_signal=62, think_tank_consensus=60,
            strategic_concept_density=65,
            fdi_quality=52, sovereign_capex_signal=55,
            multi_alignment=4,
            shock_score=1.5,
            theme_energy=8, theme_chips=5, theme_minerals=8,
            theme_food=8, theme_shipping=5, theme_defense=7,
            theme_ai=6, theme_shipping_s=4,
        ),
        "United Kingdom": dict(
            iso3="GBR", region="Europa Occidental", bloc_primary="G7",
            export_critical_bn=92, forex_reserves_bn=178,
            energy_net_export=-25, food_self_suff=68, gdp_bn=3071,
            supply_chain_centrality=68, import_strategic_dep=5,
            us_export_pct=12, import_concentration_hhi=0.15,
            sanctions_regime="none",
            ntm_density=62, export_control_score=9, standards_power=75,
            compliance_burden=35,
            institutional_signal=80, think_tank_consensus=82,
            strategic_concept_density=80,
            fdi_quality=60, sovereign_capex_signal=65,
            multi_alignment=5,  # G7 + Five Eyes + AUKUS + NATO
            shock_score=2.0,
            theme_energy=5, theme_chips=6, theme_minerals=5,
            theme_food=4, theme_shipping=7, theme_defense=8,
            theme_ai=8, theme_shipping_s=6,
        ),
        "Italy": dict(
            iso3="ITA", region="Europa Occidental", bloc_primary="G7/UE",
            export_critical_bn=72, forex_reserves_bn=195,
            energy_net_export=-70, food_self_suff=78, gdp_bn=2010,
            supply_chain_centrality=55, import_strategic_dep=7,
            us_export_pct=8.5, import_concentration_hhi=0.18,
            sanctions_regime="none",
            ntm_density=65, export_control_score=7, standards_power=65,
            compliance_burden=52,
            institutional_signal=55, think_tank_consensus=50,
            strategic_concept_density=58,
            fdi_quality=42, sovereign_capex_signal=45,
            multi_alignment=3,
            shock_score=3.0,
            theme_energy=4, theme_chips=5, theme_minerals=4,
            theme_food=6, theme_shipping=5, theme_defense=5,
            theme_ai=5, theme_shipping_s=5,
        ),
        # ── BRICS ────────────────────────────────────────────────────────
        "China": dict(
            iso3="CHN", region="Asia Oriental", bloc_primary="BRICS",
            export_critical_bn=580, forex_reserves_bn=3200,
            energy_net_export=-18, food_self_suff=95, gdp_bn=17963,
            supply_chain_centrality=92, import_strategic_dep=5,
            us_export_pct=16.8, import_concentration_hhi=0.12,
            sanctions_regime="sectoral",
            ntm_density=85, export_control_score=7, standards_power=72,
            compliance_burden=68,
            institutional_signal=88, think_tank_consensus=80,
            strategic_concept_density=90,
            fdi_quality=48, sovereign_capex_signal=80,
            multi_alignment=4,  # BRICS + SCO + G20 + BRI
            shock_score=4.5,
            theme_energy=6, theme_chips=8, theme_minerals=9,
            theme_food=5, theme_shipping=9, theme_defense=9,
            theme_ai=9, theme_shipping_s=9,
        ),
        "Russia": dict(
            iso3="RUS", region="Europa del Este", bloc_primary="BRICS",
            export_critical_bn=480, forex_reserves_bn=640,
            energy_net_export=87, food_self_suff=145, gdp_bn=2245,
            supply_chain_centrality=42, import_strategic_dep=4,
            us_export_pct=1.2, import_concentration_hhi=0.15,
            sanctions_regime="partial",
            ntm_density=55, export_control_score=4, standards_power=38,
            compliance_burden=72,
            institutional_signal=78, think_tank_consensus=75,
            strategic_concept_density=85,
            fdi_quality=25, sovereign_capex_signal=20,
            multi_alignment=3,
            shock_score=9.0,
            theme_energy=10, theme_chips=3, theme_minerals=8,
            theme_food=8, theme_shipping=4, theme_defense=9,
            theme_ai=4, theme_shipping_s=3,
        ),
        "India": dict(
            iso3="IND", region="Asia del Sur", bloc_primary="Quad/BRICS",
            export_critical_bn=95, forex_reserves_bn=562,
            energy_net_export=-38, food_self_suff=102, gdp_bn=3385,
            supply_chain_centrality=55, import_strategic_dep=5,
            us_export_pct=18.2, import_concentration_hhi=0.14,
            sanctions_regime="none",
            ntm_density=72, export_control_score=5, standards_power=52,
            compliance_burden=60,
            institutional_signal=75, think_tank_consensus=70,
            strategic_concept_density=72,
            fdi_quality=38, sovereign_capex_signal=55,
            multi_alignment=5,  # BRICS + Quad + G20 + SCO + ASEAN+
            shock_score=2.0,
            theme_energy=5, theme_chips=6, theme_minerals=5,
            theme_food=6, theme_shipping=5, theme_defense=7,
            theme_ai=7, theme_shipping_s=4,
        ),
        "Brazil": dict(
            iso3="BRA", region="América del Sur", bloc_primary="BRICS",
            export_critical_bn=110, forex_reserves_bn=325,
            energy_net_export=3, food_self_suff=190, gdp_bn=1920,
            supply_chain_centrality=42, import_strategic_dep=4,
            us_export_pct=11, import_concentration_hhi=0.13,
            sanctions_regime="none",
            ntm_density=60, export_control_score=3, standards_power=40,
            compliance_burden=70,
            institutional_signal=58, think_tank_consensus=52,
            strategic_concept_density=55,
            fdi_quality=32, sovereign_capex_signal=42,
            multi_alignment=3,
            shock_score=2.5,
            theme_energy=6, theme_chips=3, theme_minerals=6,
            theme_food=9, theme_shipping=4, theme_defense=4,
            theme_ai=4, theme_shipping_s=3,
        ),
        "South Africa": dict(
            iso3="ZAF", region="África Subsahariana", bloc_primary="BRICS",
            export_critical_bn=52, forex_reserves_bn=60,
            energy_net_export=-15, food_self_suff=98, gdp_bn=406,
            supply_chain_centrality=35, import_strategic_dep=5,
            us_export_pct=8.9, import_concentration_hhi=0.20,
            sanctions_regime="none",
            ntm_density=48, export_control_score=3, standards_power=35,
            compliance_burden=58,
            institutional_signal=48, think_tank_consensus=42,
            strategic_concept_density=45,
            fdi_quality=28, sovereign_capex_signal=32,
            multi_alignment=3,
            shock_score=2.0,
            theme_energy=4, theme_chips=2, theme_minerals=8,
            theme_food=4, theme_shipping=3, theme_defense=3,
            theme_ai=3, theme_shipping_s=2,
        ),
        # ── ORIENTE MEDIO ────────────────────────────────────────────────
        "Saudi Arabia": dict(
            iso3="SAU", region="Oriente Medio", bloc_primary="GCC",
            export_critical_bn=320, forex_reserves_bn=478,
            energy_net_export=350, food_self_suff=42, gdp_bn=1109,
            supply_chain_centrality=48, import_strategic_dep=6,
            us_export_pct=8.5, import_concentration_hhi=0.22,
            sanctions_regime="targeted",
            ntm_density=52, export_control_score=4, standards_power=42,
            compliance_burden=45,
            institutional_signal=68, think_tank_consensus=62,
            strategic_concept_density=70,
            fdi_quality=35, sovereign_capex_signal=72,
            multi_alignment=3,
            shock_score=2.5,
            theme_energy=10, theme_chips=3, theme_minerals=5,
            theme_food=3, theme_shipping=5, theme_defense=6,
            theme_ai=5, theme_shipping_s=5,
        ),
        "Iran": dict(
            iso3="IRN", region="Oriente Medio", bloc_primary="Eje",
            export_critical_bn=45, forex_reserves_bn=15,
            energy_net_export=220, food_self_suff=72, gdp_bn=367,
            supply_chain_centrality=22, import_strategic_dep=6,
            us_export_pct=0, import_concentration_hhi=0.35,
            sanctions_regime="maximum",
            ntm_density=38, export_control_score=0, standards_power=18,
            compliance_burden=90,
            institutional_signal=55, think_tank_consensus=60,
            strategic_concept_density=65,
            fdi_quality=8, sovereign_capex_signal=5,
            multi_alignment=2,
            shock_score=8.5,
            theme_energy=9, theme_chips=2, theme_minerals=4,
            theme_food=3, theme_shipping=3, theme_defense=7,
            theme_ai=2, theme_shipping_s=2,
        ),
        "UAE": dict(
            iso3="ARE", region="Oriente Medio", bloc_primary="GCC",
            export_critical_bn=165, forex_reserves_bn=188,
            energy_net_export=280, food_self_suff=25, gdp_bn=509,
            supply_chain_centrality=60, import_strategic_dep=5,
            us_export_pct=4.8, import_concentration_hhi=0.22,
            sanctions_regime="targeted",
            ntm_density=50, export_control_score=4, standards_power=45,
            compliance_burden=35,
            institutional_signal=60, think_tank_consensus=55,
            strategic_concept_density=62,
            fdi_quality=42, sovereign_capex_signal=78,
            multi_alignment=4,
            shock_score=2.0,
            theme_energy=8, theme_chips=4, theme_minerals=4,
            theme_food=3, theme_shipping=7, theme_defense=5,
            theme_ai=6, theme_shipping_s=7,
        ),
        "Turkey": dict(
            iso3="TUR", region="Europa/Oriente Medio", bloc_primary="NATO+",
            export_critical_bn=35, forex_reserves_bn=128,
            energy_net_export=-72, food_self_suff=97, gdp_bn=906,
            supply_chain_centrality=48, import_strategic_dep=7,
            us_export_pct=6.5, import_concentration_hhi=0.18,
            sanctions_regime="targeted",
            ntm_density=58, export_control_score=5, standards_power=48,
            compliance_burden=60,
            institutional_signal=58, think_tank_consensus=52,
            strategic_concept_density=58,
            fdi_quality=32, sovereign_capex_signal=38,
            multi_alignment=4,  # NATO + BRICS candidato + SCO diálogo + G20
            shock_score=3.5,
            theme_energy=4, theme_chips=4, theme_minerals=4,
            theme_food=5, theme_shipping=6, theme_defense=6,
            theme_ai=4, theme_shipping_s=5,
        ),
        "Israel": dict(
            iso3="ISR", region="Oriente Medio", bloc_primary="Occidental",
            export_critical_bn=45, forex_reserves_bn=204,
            energy_net_export=-20, food_self_suff=52, gdp_bn=522,
            supply_chain_centrality=38, import_strategic_dep=5,
            us_export_pct=28, import_concentration_hhi=0.30,
            sanctions_regime="none",
            ntm_density=55, export_control_score=7, standards_power=55,
            compliance_burden=48,
            institutional_signal=65, think_tank_consensus=60,
            strategic_concept_density=68,
            fdi_quality=62, sovereign_capex_signal=55,
            multi_alignment=2,
            shock_score=7.0,
            theme_energy=4, theme_chips=8, theme_minerals=3,
            theme_food=3, theme_shipping=3, theme_defense=9,
            theme_ai=8, theme_shipping_s=2,
        ),
        # ── ASIA-PACÍFICO ────────────────────────────────────────────────
        "South Korea": dict(
            iso3="KOR", region="Asia Oriental", bloc_primary="Quad+",
            export_critical_bn=175, forex_reserves_bn=423,
            energy_net_export=-78, food_self_suff=45, gdp_bn=1665,
            supply_chain_centrality=65, import_strategic_dep=7,
            us_export_pct=16.1, import_concentration_hhi=0.20,
            sanctions_regime="none",
            ntm_density=60, export_control_score=7, standards_power=70,
            compliance_burden=42,
            institutional_signal=65, think_tank_consensus=60,
            strategic_concept_density=68,
            fdi_quality=58, sovereign_capex_signal=62,
            multi_alignment=3,
            shock_score=2.5,
            theme_energy=3, theme_chips=10, theme_minerals=4,
            theme_food=3, theme_shipping=6, theme_defense=7,
            theme_ai=8, theme_shipping_s=5,
        ),
        "Taiwan": dict(
            iso3="TWN", region="Asia Oriental", bloc_primary="Occidental+",
            export_critical_bn=125, forex_reserves_bn=558,
            energy_net_export=-90, food_self_suff=32, gdp_bn=761,
            supply_chain_centrality=70, import_strategic_dep=8,
            us_export_pct=18, import_concentration_hhi=0.25,
            sanctions_regime="none",
            ntm_density=55, export_control_score=6, standards_power=65,
            compliance_burden=40,
            institutional_signal=72, think_tank_consensus=78,
            strategic_concept_density=85,
            fdi_quality=72, sovereign_capex_signal=65,
            multi_alignment=2,
            shock_score=7.5,
            theme_energy=2, theme_chips=10, theme_minerals=3,
            theme_food=2, theme_shipping=5, theme_defense=8,
            theme_ai=9, theme_shipping_s=4,
        ),
        "Australia": dict(
            iso3="AUS", region="Oceanía", bloc_primary="Quad/AUKUS",
            export_critical_bn=185, forex_reserves_bn=58,
            energy_net_export=45, food_self_suff=250, gdp_bn=1724,
            supply_chain_centrality=42, import_strategic_dep=4,
            us_export_pct=5, import_concentration_hhi=0.30,
            sanctions_regime="none",
            ntm_density=52, export_control_score=8, standards_power=55,
            compliance_burden=35,
            institutional_signal=62, think_tank_consensus=60,
            strategic_concept_density=65,
            fdi_quality=48, sovereign_capex_signal=52,
            multi_alignment=4,
            shock_score=2.0,
            theme_energy=7, theme_chips=4, theme_minerals=9,
            theme_food=8, theme_shipping=5, theme_defense=7,
            theme_ai=5, theme_shipping_s=4,
        ),
        "Vietnam": dict(
            iso3="VNM", region="Asia Sudoriental", bloc_primary="ASEAN",
            export_critical_bn=95, forex_reserves_bn=88,
            energy_net_export=-5, food_self_suff=105, gdp_bn=409,
            supply_chain_centrality=48, import_strategic_dep=6,
            us_export_pct=27.5, import_concentration_hhi=0.22,
            sanctions_regime="none",
            ntm_density=55, export_control_score=2, standards_power=28,
            compliance_burden=58,
            institutional_signal=50, think_tank_consensus=48,
            strategic_concept_density=52,
            fdi_quality=45, sovereign_capex_signal=50,
            multi_alignment=3,
            shock_score=2.0,
            theme_energy=3, theme_chips=6, theme_minerals=4,
            theme_food=5, theme_shipping=5, theme_defense=4,
            theme_ai=4, theme_shipping_s=4,
        ),
        "Indonesia": dict(
            iso3="IDN", region="Asia Sudoriental", bloc_primary="G20/ASEAN",
            export_critical_bn=72, forex_reserves_bn=137,
            energy_net_export=12, food_self_suff=88, gdp_bn=1319,
            supply_chain_centrality=42, import_strategic_dep=5,
            us_export_pct=9.8, import_concentration_hhi=0.18,
            sanctions_regime="none",
            ntm_density=58, export_control_score=3, standards_power=32,
            compliance_burden=62,
            institutional_signal=52, think_tank_consensus=48,
            strategic_concept_density=52,
            fdi_quality=30, sovereign_capex_signal=45,
            multi_alignment=3,
            shock_score=1.5,
            theme_energy=5, theme_chips=3, theme_minerals=7,
            theme_food=4, theme_shipping=5, theme_defense=4,
            theme_ai=3, theme_shipping_s=4,
        ),
        "Malaysia": dict(
            iso3="MYS", region="Asia Sudoriental", bloc_primary="ASEAN",
            export_critical_bn=65, forex_reserves_bn=115,
            energy_net_export=20, food_self_suff=72, gdp_bn=407,
            supply_chain_centrality=52, import_strategic_dep=6,
            us_export_pct=12, import_concentration_hhi=0.22,
            sanctions_regime="none",
            ntm_density=52, export_control_score=3, standards_power=35,
            compliance_burden=50,
            institutional_signal=45, think_tank_consensus=42,
            strategic_concept_density=48,
            fdi_quality=42, sovereign_capex_signal=45,
            multi_alignment=2,
            shock_score=1.5,
            theme_energy=5, theme_chips=5, theme_minerals=4,
            theme_food=4, theme_shipping=5, theme_defense=3,
            theme_ai=4, theme_shipping_s=4,
        ),
        "Thailand": dict(
            iso3="THA", region="Asia Sudoriental", bloc_primary="ASEAN",
            export_critical_bn=55, forex_reserves_bn=225,
            energy_net_export=-15, food_self_suff=125, gdp_bn=495,
            supply_chain_centrality=45, import_strategic_dep=5,
            us_export_pct=12, import_concentration_hhi=0.18,
            sanctions_regime="none",
            ntm_density=55, export_control_score=2, standards_power=30,
            compliance_burden=55,
            institutional_signal=42, think_tank_consensus=38,
            strategic_concept_density=42,
            fdi_quality=32, sovereign_capex_signal=38,
            multi_alignment=2,
            shock_score=1.5,
            theme_energy=3, theme_chips=4, theme_minerals=3,
            theme_food=6, theme_shipping=4, theme_defense=3,
            theme_ai=3, theme_shipping_s=3,
        ),
        # ── EUROPA ───────────────────────────────────────────────────────
        "Netherlands": dict(
            iso3="NLD", region="Europa Occidental", bloc_primary="UE",
            export_critical_bn=88, forex_reserves_bn=55,
            energy_net_export=-30, food_self_suff=180, gdp_bn=1011,
            supply_chain_centrality=68, import_strategic_dep=5,
            us_export_pct=5.5, import_concentration_hhi=0.12,
            sanctions_regime="none",
            ntm_density=68, export_control_score=9, standards_power=72,
            compliance_burden=38,
            institutional_signal=65, think_tank_consensus=62,
            strategic_concept_density=68,
            fdi_quality=55, sovereign_capex_signal=58,
            multi_alignment=3,
            shock_score=2.5,  # ASML export controls
            theme_energy=4, theme_chips=10, theme_minerals=4,
            theme_food=7, theme_shipping=8, theme_defense=6,
            theme_ai=7, theme_shipping_s=8,
        ),
        "Poland": dict(
            iso3="POL", region="Europa del Este", bloc_primary="UE/NATO",
            export_critical_bn=28, forex_reserves_bn=168,
            energy_net_export=-48, food_self_suff=108, gdp_bn=688,
            supply_chain_centrality=42, import_strategic_dep=6,
            us_export_pct=3.1, import_concentration_hhi=0.18,
            sanctions_regime="none",
            ntm_density=60, export_control_score=6, standards_power=45,
            compliance_burden=52,
            institutional_signal=52, think_tank_consensus=50,
            strategic_concept_density=55,
            fdi_quality=42, sovereign_capex_signal=48,
            multi_alignment=3,
            shock_score=3.0,
            theme_energy=4, theme_chips=4, theme_minerals=4,
            theme_food=5, theme_shipping=3, theme_defense=7,
            theme_ai=4, theme_shipping_s=2,
        ),
        "Norway": dict(
            iso3="NOR", region="Europa Occidental", bloc_primary="NATO",
            export_critical_bn=105, forex_reserves_bn=82,
            energy_net_export=280, food_self_suff=85, gdp_bn=582,
            supply_chain_centrality=38, import_strategic_dep=4,
            us_export_pct=4, import_concentration_hhi=0.15,
            sanctions_regime="none",
            ntm_density=55, export_control_score=7, standards_power=52,
            compliance_burden=32,
            institutional_signal=55, think_tank_consensus=52,
            strategic_concept_density=55,
            fdi_quality=45, sovereign_capex_signal=85,
            multi_alignment=2,
            shock_score=1.5,
            theme_energy=9, theme_chips=4, theme_minerals=6,
            theme_food=5, theme_shipping=6, theme_defense=5,
            theme_ai=5, theme_shipping_s=5,
        ),
        "Switzerland": dict(
            iso3="CHE", region="Europa Occidental", bloc_primary="Neutral",
            export_critical_bn=52, forex_reserves_bn=880,
            energy_net_export=-40, food_self_suff=50, gdp_bn=807,
            supply_chain_centrality=50, import_strategic_dep=5,
            us_export_pct=9, import_concentration_hhi=0.15,
            sanctions_regime="none",
            ntm_density=58, export_control_score=6, standards_power=60,
            compliance_burden=35,
            institutional_signal=60, think_tank_consensus=55,
            strategic_concept_density=60,
            fdi_quality=60, sovereign_capex_signal=65,
            multi_alignment=2,
            shock_score=1.5,
            theme_energy=4, theme_chips=5, theme_minerals=5,
            theme_food=4, theme_shipping=4, theme_defense=4,
            theme_ai=6, theme_shipping_s=3,
        ),
        # ── LATINOAMÉRICA ────────────────────────────────────────────────
        "Mexico": dict(
            iso3="MEX", region="América del Norte", bloc_primary="TMEC",
            export_critical_bn=55, forex_reserves_bn=201,
            energy_net_export=-22, food_self_suff=85, gdp_bn=1294,
            supply_chain_centrality=48, import_strategic_dep=6,
            us_export_pct=79.95, import_concentration_hhi=0.68,
            sanctions_regime="none",
            ntm_density=50, export_control_score=3, standards_power=35,
            compliance_burden=65,
            institutional_signal=52, think_tank_consensus=50,
            strategic_concept_density=55,
            fdi_quality=35, sovereign_capex_signal=42,
            multi_alignment=2,
            shock_score=3.0,
            theme_energy=4, theme_chips=4, theme_minerals=5,
            theme_food=4, theme_shipping=4, theme_defense=3,
            theme_ai=3, theme_shipping_s=3,
        ),
        "Argentina": dict(
            iso3="ARG", region="América del Sur", bloc_primary="BRICS+",
            export_critical_bn=38, forex_reserves_bn=25,
            energy_net_export=-5, food_self_suff=200, gdp_bn=632,
            supply_chain_centrality=32, import_strategic_dep=5,
            us_export_pct=4.7, import_concentration_hhi=0.18,
            sanctions_regime="none",
            ntm_density=55, export_control_score=2, standards_power=28,
            compliance_burden=75,
            institutional_signal=45, think_tank_consensus=42,
            strategic_concept_density=45,
            fdi_quality=22, sovereign_capex_signal=28,
            multi_alignment=3,
            shock_score=5.0,
            theme_energy=5, theme_chips=2, theme_minerals=6,
            theme_food=9, theme_shipping=3, theme_defense=2,
            theme_ai=2, theme_shipping_s=2,
        ),
        "Chile": dict(
            iso3="CHL", region="América del Sur", bloc_primary="Alianza Pacífico",
            export_critical_bn=42, forex_reserves_bn=42,
            energy_net_export=-30, food_self_suff=90, gdp_bn=301,
            supply_chain_centrality=30, import_strategic_dep=5,
            us_export_pct=8, import_concentration_hhi=0.22,
            sanctions_regime="none",
            ntm_density=45, export_control_score=3, standards_power=30,
            compliance_burden=50,
            institutional_signal=42, think_tank_consensus=38,
            strategic_concept_density=42,
            fdi_quality=28, sovereign_capex_signal=35,
            multi_alignment=2,
            shock_score=2.0,
            theme_energy=4, theme_chips=2, theme_minerals=9,
            theme_food=5, theme_shipping=4, theme_defense=2,
            theme_ai=2, theme_shipping_s=3,
        ),
        # ── ÁFRICA / OTROS ───────────────────────────────────────────────
        "Nigeria": dict(
            iso3="NGA", region="África Subsahariana", bloc_primary="AU/ECOWAS",
            export_critical_bn=48, forex_reserves_bn=38,
            energy_net_export=95, food_self_suff=82, gdp_bn=477,
            supply_chain_centrality=28, import_strategic_dep=5,
            us_export_pct=6.5, import_concentration_hhi=0.22,
            sanctions_regime="none",
            ntm_density=42, export_control_score=1, standards_power=22,
            compliance_burden=72,
            institutional_signal=42, think_tank_consensus=38,
            strategic_concept_density=42,
            fdi_quality=18, sovereign_capex_signal=25,
            multi_alignment=2,
            shock_score=3.0,
            theme_energy=8, theme_chips=1, theme_minerals=4,
            theme_food=4, theme_shipping=3, theme_defense=3,
            theme_ai=2, theme_shipping_s=2,
        ),
        "Egypt": dict(
            iso3="EGY", region="África del Norte", bloc_primary="AU/AL",
            export_critical_bn=35, forex_reserves_bn=35,
            energy_net_export=-5, food_self_suff=55, gdp_bn=476,
            supply_chain_centrality=38, import_strategic_dep=6,
            us_export_pct=8, import_concentration_hhi=0.25,
            sanctions_regime="none",
            ntm_density=48, export_control_score=2, standards_power=28,
            compliance_burden=68,
            institutional_signal=45, think_tank_consensus=42,
            strategic_concept_density=45,
            fdi_quality=22, sovereign_capex_signal=30,
            multi_alignment=3,
            shock_score=3.5,
            theme_energy=4, theme_chips=2, theme_minerals=3,
            theme_food=4, theme_shipping=7, theme_defense=4,
            theme_ai=2, theme_shipping_s=7,
        ),
        "Morocco": dict(
            iso3="MAR", region="África del Norte", bloc_primary="UE+",
            export_critical_bn=22, forex_reserves_bn=35,
            energy_net_export=-40, food_self_suff=72, gdp_bn=134,
            supply_chain_centrality=32, import_strategic_dep=6,
            us_export_pct=3, import_concentration_hhi=0.28,
            sanctions_regime="none",
            ntm_density=45, export_control_score=2, standards_power=28,
            compliance_burden=58,
            institutional_signal=40, think_tank_consensus=38,
            strategic_concept_density=42,
            fdi_quality=25, sovereign_capex_signal=32,
            multi_alignment=2,
            shock_score=1.5,
            theme_energy=3, theme_chips=2, theme_minerals=7,
            theme_food=4, theme_shipping=3, theme_defense=3,
            theme_ai=2, theme_shipping_s=2,
        ),
        "Kazakhstan": dict(
            iso3="KAZ", region="Asia Central", bloc_primary="OCS/CSTO",
            export_critical_bn=65, forex_reserves_bn=94,
            energy_net_export=155, food_self_suff=112, gdp_bn=220,
            supply_chain_centrality=30, import_strategic_dep=5,
            us_export_pct=3.5, import_concentration_hhi=0.28,
            sanctions_regime="targeted",
            ntm_density=38, export_control_score=2, standards_power=22,
            compliance_burden=65,
            institutional_signal=40, think_tank_consensus=38,
            strategic_concept_density=42,
            fdi_quality=22, sovereign_capex_signal=28,
            multi_alignment=3,
            shock_score=3.0,
            theme_energy=8, theme_chips=2, theme_minerals=7,
            theme_food=5, theme_shipping=3, theme_defense=4,
            theme_ai=2, theme_shipping_s=2,
        ),
        "North Korea": dict(
            iso3="PRK", region="Asia Oriental", bloc_primary="Autárquico",
            export_critical_bn=1.8, forex_reserves_bn=2,
            energy_net_export=-25, food_self_suff=70, gdp_bn=18,
            supply_chain_centrality=5, import_strategic_dep=8,
            us_export_pct=0, import_concentration_hhi=0.90,
            sanctions_regime="maximum",
            ntm_density=20, export_control_score=0, standards_power=5,
            compliance_burden=95,
            institutional_signal=48, think_tank_consensus=55,
            strategic_concept_density=60,
            fdi_quality=2, sovereign_capex_signal=2,
            multi_alignment=1,
            shock_score=8.0,
            theme_energy=2, theme_chips=1, theme_minerals=3,
            theme_food=2, theme_shipping=1, theme_defense=9,
            theme_ai=1, theme_shipping_s=1,
        ),
        "Venezuela": dict(
            iso3="VEN", region="América del Sur", bloc_primary="ALBA",
            export_critical_bn=12, forex_reserves_bn=9,
            energy_net_export=180, food_self_suff=55, gdp_bn=98,
            supply_chain_centrality=15, import_strategic_dep=7,
            us_export_pct=2, import_concentration_hhi=0.65,
            sanctions_regime="partial",
            ntm_density=30, export_control_score=0, standards_power=12,
            compliance_burden=85,
            institutional_signal=45, think_tank_consensus=48,
            strategic_concept_density=50,
            fdi_quality=5, sovereign_capex_signal=5,
            multi_alignment=2,
            shock_score=7.0,
            theme_energy=8, theme_chips=1, theme_minerals=4,
            theme_food=2, theme_shipping=2, theme_defense=4,
            theme_ai=1, theme_shipping_s=1,
        ),
        "Qatar": dict(
            iso3="QAT", region="Oriente Medio", bloc_primary="GCC",
            export_critical_bn=78, forex_reserves_bn=48,
            energy_net_export=400, food_self_suff=15, gdp_bn=237,
            supply_chain_centrality=35, import_strategic_dep=7,
            us_export_pct=2, import_concentration_hhi=0.30,
            sanctions_regime="none",
            ntm_density=42, export_control_score=3, standards_power=32,
            compliance_burden=32,
            institutional_signal=50, think_tank_consensus=48,
            strategic_concept_density=52,
            fdi_quality=30, sovereign_capex_signal=80,
            multi_alignment=2,
            shock_score=2.0,
            theme_energy=10, theme_chips=3, theme_minerals=3,
            theme_food=2, theme_shipping=5, theme_defense=4,
            theme_ai=4, theme_shipping_s=5,
        ),
        "Colombia": dict(
            iso3="COL", region="América del Sur", bloc_primary="Alianza Pacífico",
            export_critical_bn=28, forex_reserves_bn=58,
            energy_net_export=20, food_self_suff=90, gdp_bn=343,
            supply_chain_centrality=28, import_strategic_dep=5,
            us_export_pct=28, import_concentration_hhi=0.32,
            sanctions_regime="none",
            ntm_density=45, export_control_score=2, standards_power=25,
            compliance_burden=62,
            institutional_signal=40, think_tank_consensus=38,
            strategic_concept_density=40,
            fdi_quality=22, sovereign_capex_signal=28,
            multi_alignment=2,
            shock_score=2.0,
            theme_energy=5, theme_chips=2, theme_minerals=4,
            theme_food=5, theme_shipping=3, theme_defense=3,
            theme_ai=2, theme_shipping_s=2,
        ),
        "Peru": dict(
            iso3="PER", region="América del Sur", bloc_primary="Alianza Pacífico",
            export_critical_bn=22, forex_reserves_bn=72,
            energy_net_export=5, food_self_suff=85, gdp_bn=242,
            supply_chain_centrality=25, import_strategic_dep=5,
            us_export_pct=18, import_concentration_hhi=0.28,
            sanctions_regime="none",
            ntm_density=42, export_control_score=2, standards_power=22,
            compliance_burden=58,
            institutional_signal=38, think_tank_consensus=35,
            strategic_concept_density=38,
            fdi_quality=20, sovereign_capex_signal=25,
            multi_alignment=2,
            shock_score=2.0,
            theme_energy=3, theme_chips=1, theme_minerals=8,
            theme_food=5, theme_shipping=3, theme_defense=2,
            theme_ai=1, theme_shipping_s=2,
        ),
        "Pakistan": dict(
            iso3="PAK", region="Asia del Sur", bloc_primary="OCS",
            export_critical_bn=18, forex_reserves_bn=15,
            energy_net_export=-30, food_self_suff=75, gdp_bn=347,
            supply_chain_centrality=22, import_strategic_dep=7,
            us_export_pct=17, import_concentration_hhi=0.30,
            sanctions_regime="none",
            ntm_density=40, export_control_score=2, standards_power=20,
            compliance_burden=75,
            institutional_signal=42, think_tank_consensus=40,
            strategic_concept_density=42,
            fdi_quality=15, sovereign_capex_signal=20,
            multi_alignment=3,
            shock_score=4.0,
            theme_energy=3, theme_chips=1, theme_minerals=3,
            theme_food=4, theme_shipping=2, theme_defense=4,
            theme_ai=2, theme_shipping_s=1,
        ),
        "Bangladesh": dict(
            iso3="BGD", region="Asia del Sur", bloc_primary="G77",
            export_critical_bn=12, forex_reserves_bn=32,
            energy_net_export=-20, food_self_suff=82, gdp_bn=460,
            supply_chain_centrality=22, import_strategic_dep=6,
            us_export_pct=20, import_concentration_hhi=0.35,
            sanctions_regime="none",
            ntm_density=38, export_control_score=1, standards_power=18,
            compliance_burden=68,
            institutional_signal=35, think_tank_consensus=32,
            strategic_concept_density=35,
            fdi_quality=15, sovereign_capex_signal=18,
            multi_alignment=2,
            shock_score=2.5,
            theme_energy=2, theme_chips=1, theme_minerals=2,
            theme_food=4, theme_shipping=3, theme_defense=2,
            theme_ai=1, theme_shipping_s=2,
        ),
        "Philippines": dict(
            iso3="PHL", region="Asia Sudoriental", bloc_primary="ASEAN",
            export_critical_bn=25, forex_reserves_bn=98,
            energy_net_export=-35, food_self_suff=78, gdp_bn=404,
            supply_chain_centrality=30, import_strategic_dep=6,
            us_export_pct=16, import_concentration_hhi=0.25,
            sanctions_regime="none",
            ntm_density=45, export_control_score=3, standards_power=25,
            compliance_burden=62,
            institutional_signal=40, think_tank_consensus=38,
            strategic_concept_density=40,
            fdi_quality=25, sovereign_capex_signal=30,
            multi_alignment=2,
            shock_score=2.5,
            theme_energy=3, theme_chips=3, theme_minerals=4,
            theme_food=4, theme_shipping=4, theme_defense=4,
            theme_ai=3, theme_shipping_s=3,
        ),
        "Ethiopia": dict(
            iso3="ETH", region="África Subsahariana", bloc_primary="AU/BRICS",
            export_critical_bn=4, forex_reserves_bn=3,
            energy_net_export=-15, food_self_suff=72, gdp_bn=127,
            supply_chain_centrality=15, import_strategic_dep=7,
            us_export_pct=5, import_concentration_hhi=0.40,
            sanctions_regime="none",
            ntm_density=30, export_control_score=1, standards_power=12,
            compliance_burden=72,
            institutional_signal=32, think_tank_consensus=30,
            strategic_concept_density=32,
            fdi_quality=12, sovereign_capex_signal=15,
            multi_alignment=3,
            shock_score=3.5,
            theme_energy=2, theme_chips=1, theme_minerals=3,
            theme_food=3, theme_shipping=2, theme_defense=3,
            theme_ai=1, theme_shipping_s=1,
        ),
    }

    rows = [{"country": k, **v} for k, v in data.items()]
    df = pd.DataFrame(rows)

    # Añadir sanction_penalty numérica
    df["sanctions_penalty"] = df["sanctions_regime"].map(SANCTION_PENALTY)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE — Capa 1: BASE_ICG
# Correcciones metodológicas clave vs v1/v2:
# - Percentile rank (panel-invariante)
# - Separación stocks / flows
# - Penalidad convexa exponencial para dependencia
# - Penalidad sanciones discreta por régimen
# ─────────────────────────────────────────────────────────────────────────────

def percentile_rank(series: pd.Series) -> pd.Series:
    """Percentile rank [0,100]. Panel-invariante: no depende del rango."""
    return series.rank(pct=True) * 100


def compute_leverage(df: pd.DataFrame, theme: Optional[str] = None) -> pd.Series:
    """
    Apalancamiento geoeconómico — capacidad de proyectar influencia.

    Componentes:
    - export_critical (F)      : capacidad de exportar bienes estratégicos [40%]
    - supply_chain_centrality  : posición en redes de valor globales       [35%]
    - forex_reserves (S)       : profundidad financiera disponible          [25%]
    - sanction_penalty (discreta): penalidad convexa por régimen            [resta]

    Ajuste temático: si theme seleccionado, pondera el tema_score
    """
    exp_r   = percentile_rank(np.log1p(df["export_critical_bn"]))
    scc_r   = percentile_rank(df["supply_chain_centrality"])
    forex_r = percentile_rank(np.log1p(df["forex_reserves_bn"]))

    base = exp_r * 0.40 + scc_r * 0.35 + forex_r * 0.25

    # Penalidad sanciones: convexa — no lineal
    penalty = df["sanctions_penalty"] * 100   # [0, 78]
    base = (base - penalty).clip(0, 100)

    # Overlay temático: boost si el país es relevante en el tema
    if theme:
        col = f"theme_{theme}"
        if col in df.columns:
            theme_r = percentile_rank(df[col])
            base = base * 0.75 + theme_r * 0.25

    return base.clip(0, 100)


def compute_resilience(df: pd.DataFrame, theme: Optional[str] = None) -> pd.Series:
    """
    Resiliencia estratégica — capacidad de absorber shocks externos.

    Componentes:
    - energy_net_export   : autosuficiencia energética (negativo = importador) [30%]
    - food_self_suff      : autosuficiencia alimentaria                        [25%]
    - import_strategic_dep: inverso de dependencia de importaciones críticas   [25%]
    - supply_chain_centrality: redundancia logística                           [20%]
    """
    energy_r = percentile_rank(df["energy_net_export"])
    food_r   = percentile_rank(df["food_self_suff"]).clip(0, 100)
    dep_inv  = percentile_rank(10 - df["import_strategic_dep"])
    scc_r    = percentile_rank(df["supply_chain_centrality"])

    base = energy_r * 0.30 + food_r * 0.25 + dep_inv * 0.25 + scc_r * 0.20

    if theme:
        col = f"theme_{theme}"
        if col in df.columns:
            theme_r = percentile_rank(df[col])
            base = base * 0.80 + theme_r * 0.20

    return base.clip(0, 100)


def compute_dependence(df: pd.DataFrame) -> pd.Series:
    """
    Dependencia externa — vulnerabilidad estructural.

    Componentes:
    - us_export_pct            : concentración en mercado EE.UU.        [50%]
    - import_concentration_hhi : HHI de diversificación de importaciones [30%]
    - multi_alignment inverso  : menor multi-alineación = más dependiente [20%]
    """
    us_r   = percentile_rank(df["us_export_pct"])
    hhi_r  = percentile_rank(df["import_concentration_hhi"])
    ma_inv = percentile_rank(7 - df["multi_alignment"])

    return (us_r * 0.50 + hhi_r * 0.30 + ma_inv * 0.20).clip(0, 100)


def compute_base_icg(
    df: pd.DataFrame,
    theme: Optional[str] = None,
    w_l: float = 1.0,
    w_r: float = 1.0,
    tariff_shock: float = 0.0,
) -> pd.DataFrame:
    """
    BASE_ICG con fórmula corregida:

    ICG = (L^wL × R^wR)^(1/(wL+wR)) × exp(−γ × D/100) − Penalidad_Arancel

    Corrección vs v1/v2:
    - Geometric mean ponderada en lugar de sqrt(L×R)
    - Penalidad exponencial en dependencia (no lineal: γ=0.8)
    - γ calibrado para que D=100 → factor=0.45 (penalidad significativa)
    """
    df = df.copy()
    df["leverage"]    = compute_leverage(df, theme)
    df["resilience"]  = compute_resilience(df, theme)
    df["dependence"]  = compute_dependence(df)

    L = np.maximum(df["leverage"],   0.1)
    R = np.maximum(df["resilience"], 0.1)
    D = df["dependence"]

    # Geometric mean ponderada
    geo_mean = np.power(np.power(L, w_l) * np.power(R, w_r), 1 / (w_l + w_r))

    # Penalidad exponencial de dependencia (γ=0.8)
    gamma = 0.8
    dep_factor = np.exp(-gamma * D / 100)  # rango [exp(-0.8), 1] ≈ [0.45, 1.00]

    icg_raw = geo_mean * dep_factor

    # Penalidad arancelaria Trump 2026
    friction_factor = 0.70
    tariff_pen = (df["us_export_pct"] / 100) * (tariff_shock / 100) * friction_factor * 100
    icg_raw -= tariff_pen * 0.20

    # Reescalar a [0,100]
    mn, mx = icg_raw.min(), icg_raw.max()
    df["base_icg"] = ((icg_raw - mn) / (mx - mn) * 100).clip(0, 100)

    # Categoría
    df["icg_cat"] = pd.cut(
        df["base_icg"],
        bins=[-1, 18, 35, 55, 72, 101],
        labels=["Crítico", "Vulnerable", "Intermedio", "Fuerte", "Dominante"],
    )

    # Delta arancelario
    if tariff_shock > 0:
        df0 = compute_base_icg(df[df.columns[:40]].copy(), theme=theme,
                               w_l=w_l, w_r=w_r, tariff_shock=0.0)
        base_map = df0.set_index("country")["base_icg"].to_dict()
        df["base_icg_0"] = df["country"].map(base_map)
        df["icg_delta"]  = df["base_icg"] - df["base_icg_0"]
    else:
        df["base_icg_0"] = df["base_icg"]
        df["icg_delta"]  = 0.0

    return df.sort_values("base_icg", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE — Capa 2: FRICTION_LAYER
# ─────────────────────────────────────────────────────────────────────────────

def compute_friction_layer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regulatory Power: capacidad de imponer fricción regulatoria.
    (NO modifica BASE_ICG — es un overlay de interpretación)

    Componentes:
    - ntm_density          : densidad de medidas no arancelarias [30%]
    - export_control_score : participación en regímenes de control [28%]
    - standards_power      : capacidad de imponer estándares [22%]
    - compliance_burden inv: baja carga para el país = más poder [20%]
    """
    ntm_r   = percentile_rank(df["ntm_density"])
    ec_r    = percentile_rank(df["export_control_score"])
    std_r   = percentile_rank(df["standards_power"])
    cb_inv  = percentile_rank(100 - df["compliance_burden"])

    df["regulatory_power"] = (
        ntm_r * 0.30 + ec_r * 0.28 + std_r * 0.22 + cb_inv * 0.20
    ).clip(0, 100)

    # Market Access Viability (perspectiva del exportador hacia este país)
    # Cuánto cuesta acceder al mercado de este país en términos regulatorios
    df["market_access_barrier"] = df["regulatory_power"]

    return df


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE — Capa 3: SIGNAL_LAYER
# ─────────────────────────────────────────────────────────────────────────────

def compute_signal_layer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strategic Signal: alineación del país con narrativa estratégica global.

    Componentes:
    - institutional_signal    : frecuencia en docs IMF/WB/OECD/G20 [40%]
    - think_tank_consensus    : score de consenso think tanks       [35%]
    - strategic_concept_density: co-ocurrencia de conceptos clave  [25%]
    """
    inst_r = percentile_rank(df["institutional_signal"])
    tt_r   = percentile_rank(df["think_tank_consensus"])
    scd_r  = percentile_rank(df["strategic_concept_density"])

    df["strategic_signal"] = (
        inst_r * 0.40 + tt_r * 0.35 + scd_r * 0.25
    ).clip(0, 100)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE — Capa 4: CAPITAL_LAYER
# ─────────────────────────────────────────────────────────────────────────────

def compute_capital_layer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Capital Confirmation: ¿valida el dinero la tesis geopolítica?

    Componentes:
    - fdi_quality          : % IED en sectores estratégicos [55%]
    - sovereign_capex_signal: señal de fondos soberanos    [45%]
    """
    fdi_r  = percentile_rank(df["fdi_quality"])
    cap_r  = percentile_rank(df["sovereign_capex_signal"])

    df["capital_confirmation"] = (fdi_r * 0.55 + cap_r * 0.45).clip(0, 100)

    # Divergencia: si señal estratégica alta pero capital bajo → oportunidad o trampa
    df["narrative_capital_divergence"] = df["strategic_signal"] - df["capital_confirmation"]

    return df


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE — Capa 5: SHOCK_LAYER
# ─────────────────────────────────────────────────────────────────────────────

def compute_shock_layer(df: pd.DataFrame,
                        news_deltas: Optional[Dict] = None) -> pd.DataFrame:
    """
    Shock Layer: perturbaciones recientes.

    El shock_score base viene de la base de datos (proxy ca. 2024).
    Los news_deltas ajustan marginalmente el score.

    Importante: shocks NO entran en BASE_ICG.
    Son un overlay de alerta para el analista.
    """
    df = df.copy()

    if news_deltas:
        def apply_delta(row):
            delta = news_deltas.get(row["country"], 0.0)
            # Shocks solo suben, y con cap más conservador (+1.5 max)
            return min(10.0, row["shock_score"] + delta * 0.3)
        df["shock_score"] = df.apply(apply_delta, axis=1)

    df["shock_percentile"] = percentile_rank(df["shock_score"])

    return df


# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE FULL SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

def compute_full_system(
    df: pd.DataFrame,
    theme: Optional[str] = None,
    w_l: float = 1.0,
    w_r: float = 1.0,
    tariff_shock: float = 0.0,
    news_deltas: Optional[Dict] = None,
) -> pd.DataFrame:
    """Ejecuta todas las capas en orden."""
    df = compute_base_icg(df, theme=theme, w_l=w_l, w_r=w_r,
                          tariff_shock=tariff_shock)
    df = compute_friction_layer(df)
    df = compute_signal_layer(df)
    df = compute_capital_layer(df)
    df = compute_shock_layer(df, news_deltas=news_deltas)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# THEME ENGINE
# ─────────────────────────────────────────────────────────────────────────────

THEME_COL_MAP = {
    "energy":    "theme_energy",
    "chips":     "theme_chips",
    "minerals":  "theme_minerals",
    "food":      "theme_food",
    "shipping":  "theme_shipping",
    "defense":   "theme_defense",
    "ai_digital":"theme_ai",
}

THEME_DESCRIPTIONS = {
    "energy":     "Energía: petróleo, gas, GNL, renovables, red eléctrica",
    "chips":      "Semiconductores: diseño, fabricación, equipos (ASML, TSMC, Samsung)",
    "minerals":   "Minerales Críticos: litio, cobalto, tierras raras, cobre, níquel",
    "food":       "Seguridad Alimentaria: cereales, fertilizantes, cadena agro",
    "shipping":   "Logística: rutas marítimas, puertos, contenedores, Suez, Malacca",
    "defense":    "Defensa e Industria Militar: armamento, tecnología dual, OTAN",
    "ai_digital": "IA / Digital: chips IA, datos, gobernanza digital, infraestructura",
}


def get_theme_leaders(df: pd.DataFrame, theme: str, n: int = 8) -> pd.DataFrame:
    col = THEME_COL_MAP.get(theme)
    if col and col in df.columns:
        return df.nlargest(n, col)[["country", col, "base_icg", "regulatory_power"]]
    return df.head(n)


def get_theme_dependents(df: pd.DataFrame, theme: str, n: int = 8) -> pd.DataFrame:
    """Países más dependientes en un tema = menor score + mayor shock."""
    col = THEME_COL_MAP.get(theme)
    if col and col in df.columns:
        df_t = df.copy()
        df_t["vulnerability"] = (10 - df_t[col]) + df_t["shock_score"]
        return df_t.nlargest(n, "vulnerability")[["country", col, "shock_score", "base_icg"]]
    return df.tail(n)


# ─────────────────────────────────────────────────────────────────────────────
# BLOC ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def compute_bloc_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega scores por bloque geopolítico."""
    rows = []
    for bloc, members in BLOCS.items():
        sub = df[df["country"].isin(members)]
        if sub.empty:
            continue
        rows.append({
            "bloc": bloc,
            "n_members": len(sub),
            "base_icg": sub["base_icg"].mean(),
            "leverage": sub["leverage"].mean(),
            "resilience": sub["resilience"].mean(),
            "dependence": sub["dependence"].mean(),
            "regulatory_power": sub["regulatory_power"].mean(),
            "strategic_signal": sub["strategic_signal"].mean(),
            "capital_confirmation": sub["capital_confirmation"].mean(),
            "shock_score": sub["shock_score"].mean(),
        })
    return pd.DataFrame(rows).set_index("bloc")


# ─────────────────────────────────────────────────────────────────────────────
# NEWS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

SANCTION_KW = [
    "sanction", "embargo", "blacklist", "asset freeze", "OFAC",
    "export control", "trade ban", "secondary sanction",
]
TARIFF_KW = [
    "tariff", "trade war", "import duty", "customs", "countervailing",
    "antidumping", "trade barrier", "protectionism",
]
COUNTRY_KW_MAP = {
    "china": "China", "chinese": "China", "beijing": "China",
    "russia": "Russia", "russian": "Russia", "moscow": "Russia",
    "iran": "Iran", "iranian": "Iran", "tehran": "Iran",
    "north korea": "North Korea", "pyongyang": "North Korea",
    "venezuela": "Venezuela", "turkey": "Turkey", "turkish": "Turkey",
    "saudi": "Saudi Arabia", "india": "India", "taiwan": "Taiwan",
    "mexico": "Mexico", "canada": "Canada", "germany": "Germany",
    "japan": "Japan", "south korea": "South Korea", "ukraine": "Ukraine",
}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(api_key: str, query: str = "sanctions trade war export controls",
               page_size: int = 30) -> List[Dict]:
    if not api_key:
        return []
    try:
        r = requests.get("https://newsapi.org/v2/everything", params={
            "q": query, "language": "en", "sortBy": "publishedAt",
            "pageSize": page_size, "apiKey": api_key,
        }, timeout=10)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            now = datetime.now(timezone.utc)
            enriched = []
            for a in articles:
                text = ((a.get("title") or "") + " " +
                        (a.get("description") or "")).lower()
                countries = list({v for k, v in COUNTRY_KW_MAP.items() if k in text})
                sanc_hits = sum(1 for k in SANCTION_KW if k in text)
                tar_hits  = sum(1 for k in TARIFF_KW  if k in text)
                impact    = min(3, sanc_hits + tar_hits)
                try:
                    pub = datetime.fromisoformat(
                        (a.get("publishedAt") or "").replace("Z", "+00:00"))
                    hrs = (now - pub).total_seconds() / 3600
                    weight = 2.0 if hrs < 6 else 1.5 if hrs < 24 else 1.0
                except Exception:
                    weight = 1.0
                enriched.append({
                    "title": a.get("title", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "published": (a.get("publishedAt") or "")[:10],
                    "url": a.get("url", "#"),
                    "countries": countries,
                    "impact": impact,
                    "weight": weight,
                })
            return enriched
    except Exception:
        pass
    return []


def news_to_shock_deltas(articles: List[Dict]) -> Dict[str, float]:
    deltas: Dict[str, float] = {}
    for a in articles:
        if not a["countries"] or a["impact"] == 0:
            continue
        contrib = (a["impact"] / 3) * a["weight"] * 0.6
        for c in a["countries"]:
            deltas[c] = min(2.0, deltas.get(c, 0.0) + contrib)
    return deltas


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATIONS
# ─────────────────────────────────────────────────────────────────────────────

DL = dict(  # Dark Layout base
    paper_bgcolor=C["bg"], plot_bgcolor=C["panel"],
    font=dict(family="IBM Plex Mono, monospace", color=C["text"], size=10),
    xaxis=dict(gridcolor=C["border"], zerolinecolor=C["border2"],
               linecolor=C["border"]),
    yaxis=dict(gridcolor=C["border"], zerolinecolor=C["border2"],
               linecolor=C["border"]),
    legend=dict(bgcolor=C["panel"], bordercolor=C["border2"], borderwidth=1,
                font=dict(size=9)),
    margin=dict(t=45, b=40, l=45, r=25),
)


def fig_choropleth(df: pd.DataFrame, metric: str, title: str) -> go.Figure:
    hov = {"base_icg": ":.1f", "regulatory_power": ":.1f",
           "strategic_signal": ":.1f", "capital_confirmation": ":.1f",
           "shock_score": ":.1f", "iso3": False}
    cs = ICG_COLORSCALE if metric != "icg_delta" else "RdYlGn"
    fig = px.choropleth(
        df, locations="iso3", color=metric, hover_name="country",
        hover_data=hov, color_continuous_scale=cs,
        range_color=(df[metric].quantile(0.02), df[metric].quantile(0.98)),
        labels={metric: metric.replace("_", " ").title()},
    )
    fig.update_traces(marker_line_color=C["border2"], marker_line_width=0.6)
    fig.update_layout(
        **DL, title=dict(text=title, x=0.03,
                         font=dict(size=12, color="#D0E0F0",
                                   family="IBM Plex Mono, monospace")),
        geo=dict(bgcolor=C["bg"], showframe=False, showcoastlines=True,
                 coastlinecolor=C["border2"], showland=True, landcolor=C["panel"],
                 showocean=True, oceancolor=C["bg"],
                 projection_type="natural earth"),
        coloraxis_colorbar=dict(
            tickfont=dict(family="IBM Plex Mono, monospace", size=8, color=C["text2"]),
            titlefont=dict(family="IBM Plex Mono, monospace", size=9, color=C["accent3"]),
            len=0.55, thickness=10, bgcolor=C["panel"], bordercolor=C["border"],
        ),
        height=450, margin=dict(t=50, b=5, l=0, r=0),
    )
    return fig


def fig_ranking_bar(df: pd.DataFrame, col: str, n: int, title: str) -> go.Figure:
    df_p = df.head(n).copy()
    colors = df_p[col].map(lambda x:
        C["accent1"] if x > 70 else C["accent3"] if x > 50 else
        C["accent2"] if x > 35 else C["warning"] if x > 20 else C["danger"])
    fig = go.Figure(go.Bar(
        x=df_p[col], y=df_p["country"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df_p[col].round(1), textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=8, color=C["text"]),
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>",
    ))
    fig.add_vline(x=50, line_dash="dot", line_color=C["border2"], line_width=1)
    fig.update_layout(**DL,
        title=dict(text=title, font=dict(size=11, color="#D0E0F0",
                                         family="IBM Plex Mono, monospace")),
        xaxis=dict(range=[0, 118], title="Score (0-100)"),
        yaxis=dict(autorange="reversed", tickfont=dict(size=9)),
        height=max(380, n * 22), showlegend=False,
    )
    return fig


def fig_material_vs_regulatory(df: pd.DataFrame) -> go.Figure:
    """
    NUEVA: Matriz Capacidad Material vs Poder Regulatorio.
    Cuadrantes semánticos.
    """
    fig = go.Figure()
    mid = 50
    quads = [
        (mid,102,mid,102,"POTENCIAS\nCOMPLETAS",   f"rgba(0,201,167,0.05)"),
        (0,  mid,mid,102,"REGULADORES\nSIN MÚSCULO",f"rgba(74,158,202,0.05)"),
        (mid,102,0,  mid,"GIGANTES\nSIN PALANCA",   f"rgba(240,165,0,0.05)"),
        (0,  mid,0,  mid,"ESTADOS\nFRÁGILES",       f"rgba(229,62,62,0.05)"),
    ]
    for x0,x1,y0,y1,lbl,col in quads:
        fig.add_shape(type="rect",x0=x0,x1=x1,y0=y0,y1=y1,
                      fillcolor=col,line_width=0)
        fig.add_annotation(x=(x0+x1)/2,y=(y0+y1)/2,text=lbl,
                           showarrow=False,font=dict(size=7,color=C["text2"],
                                                     family="IBM Plex Mono"),
                           align="center",opacity=0.7)

    fig.add_trace(go.Scatter(
        x=df["base_icg"], y=df["regulatory_power"],
        mode="markers+text",
        marker=dict(
            size=np.sqrt(df["gdp_bn"] / 20) + 6,
            color=df["strategic_signal"],
            colorscale=[[0,"#1A2A3A"],[0.5,C["accent3"]],[1,C["accent1"]]],
            showscale=True, line=dict(color=C["border2"],width=0.8),
            colorbar=dict(title="Señal\nEstratégica",len=0.5,thickness=8,
                          bgcolor=C["panel"],bordercolor=C["border"],
                          tickfont=dict(family="IBM Plex Mono",size=7)),
        ),
        text=df["country"], textposition="top center",
        textfont=dict(size=7, color=C["text"], family="IBM Plex Mono"),
        hovertemplate=(
            "<b>%{text}</b><br>ICG Base: %{x:.1f}<br>"
            "Poder Regulatorio: %{y:.1f}<br>"
            "Señal Estratégica: %{marker.color:.1f}<extra></extra>"
        ),
    ))
    fig.add_hline(y=50,line_dash="dot",line_color=C["border2"],line_width=1)
    fig.add_vline(x=50,line_dash="dot",line_color=C["border2"],line_width=1)
    fig.update_layout(**DL,
        title=dict(text="Matriz: Capacidad Material vs Poder Regulatorio",
                   font=dict(size=11,color="#D0E0F0",family="IBM Plex Mono")),
        xaxis=dict(title="Base ICG (Capacidad Material)",range=[0,106]),
        yaxis=dict(title="Poder Regulatorio",range=[0,106]),
        height=520,
    )
    return fig


def fig_convergence_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    NUEVA: Heatmap de convergencia Narrativa × Capital × Shock.
    Verde = triple convergencia (señal fuerte).
    """
    themes_display = ["Energía","Chips","Minerales","Alimentos","Shipping","Defensa","IA"]
    theme_keys     = ["energy","chips","minerals","food","shipping","defense","ai_digital"]
    countries_top  = df.head(25)["country"].tolist()
    df_sub = df[df["country"].isin(countries_top)].set_index("country")

    z = []
    for c in countries_top:
        row_z = []
        for tk in theme_keys:
            col = f"theme_{tk}"
            score = df_sub.loc[c, col] if col in df_sub.columns else 5
            # Convergencia = tema_score + capital/10 + (10-shock)/10 normalizado
            cap_norm = df_sub.loc[c, "capital_confirmation"] / 100 * 10
            shock_inv = 10 - df_sub.loc[c, "shock_score"]
            conv = (score * 0.5 + cap_norm * 0.3 + shock_inv * 0.2)
            row_z.append(conv)
        z.append(row_z)

    fig = go.Figure(go.Heatmap(
        z=z, x=themes_display, y=countries_top,
        colorscale=[[0,C["bg"]],[0.3,"#1A3050"],[0.6,C["accent3"]],[1,C["accent1"]]],
        zmin=0, zmax=10,
        hovertemplate="<b>%{y}</b> · %{x}<br>Convergencia: %{z:.1f}<extra></extra>",
        colorbar=dict(title="Convergencia",len=0.6,thickness=10,
                      bgcolor=C["panel"],bordercolor=C["border"],
                      tickfont=dict(family="IBM Plex Mono",size=7)),
    ))
    fig.update_layout(**DL,
        title=dict(text="Heatmap de Convergencia: Narrativa × Capital × Resiliencia",
                   font=dict(size=11,color="#D0E0F0",family="IBM Plex Mono")),
        xaxis=dict(side="top",tickangle=-30,tickfont=dict(size=9)),
        yaxis=dict(autorange="reversed",tickfont=dict(size=8)),
        height=580, margin=dict(t=80,b=10,l=100,r=30),
    )
    return fig


def fig_radar_dual(df: pd.DataFrame, ca: str, cb: str) -> go.Figure:
    """Radar de comparación dual — 5 dimensiones."""
    dims = ["base_icg","leverage","resilience","regulatory_power",
            "strategic_signal","capital_confirmation"]
    lbls = ["ICG Base","Apalancam.","Resiliencia",
            "Poder Reg.","Señal Estrat.","Capital Conf."]

    fig = go.Figure()
    for i,(country,col) in enumerate([(ca,C["accent1"]),(cb,C["accent2"])]):
        row = df[df["country"]==country]
        if row.empty: continue
        r = row.iloc[0]
        vals = [r[d] for d in dims] + [r[dims[0]]]
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=lbls+[lbls[0]], name=country,
            line=dict(color=col,width=2.5), fill="toself",
            fillcolor=col.replace("#","rgba(")[:15]+", 0.08)",
        ))

    fig.update_layout(**DL,
        polar=dict(bgcolor=C["panel"],
            radialaxis=dict(visible=True,range=[0,100],gridcolor=C["border"],
                            linecolor=C["border"],
                            tickfont=dict(size=7,color=C["text2"],family="IBM Plex Mono")),
            angularaxis=dict(gridcolor=C["border"],linecolor=C["border"],
                             tickfont=dict(size=9,color=C["text"])),
        ),
        title=dict(text=f"Comparación: {ca} vs. {cb}",
                   font=dict(size=11,color="#D0E0F0",family="IBM Plex Mono")),
        showlegend=True, height=440,
    )
    return fig


def build_comparison_table_html(df: pd.DataFrame, ca: str, cb: str) -> str:
    dims = [
        ("base_icg",             "ICG Base",             False),
        ("leverage",             "Apalancamiento",        False),
        ("resilience",           "Resiliencia",           False),
        ("regulatory_power",     "Poder Regulatorio",     False),
        ("strategic_signal",     "Señal Estratégica",     False),
        ("capital_confirmation", "Confirmación Capital",  False),
        ("shock_score",          "Shock Score",           True),   # menor = mejor
        ("us_export_pct",        "Expo → EE.UU.%",        True),
        ("sanctions_penalty",    "Penalidad Sanciones",   True),
        ("multi_alignment",      "Multi-alineación",      False),
    ]
    ra = df[df["country"]==ca].iloc[0] if not df[df["country"]==ca].empty else None
    rb = df[df["country"]==cb].iloc[0] if not df[df["country"]==cb].empty else None
    if ra is None or rb is None:
        return "<p>País no encontrado.</p>"

    rows_html = ""
    for col,lbl,lower_better in dims:
        va,vb = float(ra[col]), float(rb[col])
        aw = (va<vb) if lower_better else (va>vb)
        bw = (vb<va) if lower_better else (vb>va)
        ba = '<span class="win-badge">✓</span>' if aw else ""
        bb = '<span class="win-badge">✓</span>' if bw else ""
        fmt = "{:,.0f}" if col=="gdp_bn" else "{:.1f}"
        ca_col = C["accent1"] if aw else C["text"]
        cb_col = C["accent2"] if bw else C["text"]
        rows_html += f"""
        <tr style="border-bottom:1px solid {C['border']};">
            <td style="padding:7px 12px;font-size:0.78rem;color:{C['text2']};
                       font-family:'IBM Plex Mono',monospace;">{lbl}</td>
            <td style="padding:7px 12px;text-align:center;font-family:'IBM Plex Mono',monospace;
                       font-size:0.88rem;color:{ca_col};">{fmt.format(va)}{ba}</td>
            <td style="padding:7px 12px;text-align:center;font-family:'IBM Plex Mono',monospace;
                       font-size:0.88rem;color:{cb_col};">{fmt.format(vb)}{bb}</td>
        </tr>"""

    return f"""
    <table style="width:100%;border-collapse:collapse;
                  background:{C['panel']};border-radius:6px;overflow:hidden;
                  border:1px solid {C['border2']};">
        <thead>
            <tr style="background:#0C1525;border-bottom:1px solid {C['border2']};">
                <th style="padding:10px 12px;text-align:left;
                           font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
                           letter-spacing:0.15em;color:{C['accent3']};">DIMENSIÓN</th>
                <th style="padding:10px 12px;text-align:center;
                           font-family:'IBM Plex Mono',monospace;font-size:0.72rem;
                           color:{C['accent1']};">{ca.upper()}</th>
                <th style="padding:10px 12px;text-align:center;
                           font-family:'IBM Plex Mono',monospace;font-size:0.72rem;
                           color:{C['accent2']};">{cb.upper()}</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>"""


def fig_bloc_radar(bloc_df: pd.DataFrame) -> go.Figure:
    """NUEVA: Radar de bloques geopolíticos."""
    dims = ["base_icg","leverage","resilience","regulatory_power",
            "strategic_signal","capital_confirmation"]
    lbls = ["ICG","Apalancam.","Resiliencia","Poder Reg.","Señal","Capital"]
    colors_map = {
        "G7": C["accent1"], "BRICS": C["accent2"], "UE": C["accent3"],
        "Quad": "#A78BFA",  "ASEAN": "#F97316",    "GCC": "#EC4899",
    }
    fig = go.Figure()
    for bloc in bloc_df.index:
        row = bloc_df.loc[bloc]
        vals = [row.get(d,50) for d in dims] + [row.get(dims[0],50)]
        col  = colors_map.get(bloc, C["text2"])
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=lbls+[lbls[0]], name=bloc,
            line=dict(color=col,width=2),fill="toself",
            fillcolor=col.replace("#","rgba(")[:15]+", 0.07)",
        ))
    fig.update_layout(**DL,
        polar=dict(bgcolor=C["panel"],
            radialaxis=dict(visible=True,range=[0,100],gridcolor=C["border"],
                            linecolor=C["border"],
                            tickfont=dict(size=7,color=C["text2"],family="IBM Plex Mono")),
            angularaxis=dict(gridcolor=C["border"],linecolor=C["border"],
                             tickfont=dict(size=9,color=C["text"])),
        ),
        title=dict(text="Comparación de Bloques Geopolíticos",
                   font=dict(size=11,color="#D0E0F0",family="IBM Plex Mono")),
        showlegend=True, height=460,
    )
    return fig


def fig_tariff_trajectory(df_raw: pd.DataFrame, country: str,
                           step: int=5, theme: Optional[str]=None) -> go.Figure:
    tariff_range = np.arange(0,101,step)
    vals = []
    for t in tariff_range:
        sim = compute_base_icg(df_raw.copy(),theme=theme,tariff_shock=float(t))
        row = sim[sim["country"]==country]
        vals.append(row["base_icg"].values[0] if not row.empty else np.nan)
    base = np.array(vals)
    opt  = np.clip(base*1.08,0,100)
    pes  = np.clip(base*0.92,0,100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=np.concatenate([tariff_range,tariff_range[::-1]]),
        y=np.concatenate([opt,pes[::-1]]),
        fill="toself",fillcolor=f"rgba(74,158,202,0.07)",
        line=dict(color="rgba(74,158,202,0)"),name="Banda incertidumbre"))
    for y_vals,col,name,dash in [
        (opt,  C["accent3"],"Optimista","dot"),
        (base, C["accent2"],"Base","solid"),
        (pes,  C["danger"], "Pesimista","dot"),
    ]:
        fig.add_trace(go.Scatter(x=tariff_range,y=y_vals,
            line=dict(color=col,width=2 if dash=="solid" else 1,dash=dash),
            name=name))
    for y_thresh,col,lbl in [(20,C["danger"],"Crítico"),(55,C["accent1"],"Fuerte")]:
        fig.add_hline(y=y_thresh,line_dash="dash",line_color=col,line_width=0.8,
                      annotation_text=lbl,annotation_font_color=col,
                      annotation_font_size=8)
    for x_val,lbl in [(25,"Fase I\n2018"),(60,"Guerra\ncom."),(100,"Embargo")]:
        fig.add_vline(x=x_val,line_dash="dot",line_color=C["border2"],line_width=1)
        fig.add_annotation(x=x_val,y=98,text=lbl,showarrow=False,
                           font=dict(size=7,color=C["accent3"],family="IBM Plex Mono"))
    fig.update_layout(**DL,
        title=dict(text=f"Trayectoria ICG: {country} vs. Escalada Arancelaria",
                   font=dict(size=11,color="#D0E0F0",family="IBM Plex Mono")),
        xaxis=dict(title="Arancel EE.UU. (%)",range=[0,101]),
        yaxis=dict(title="Base ICG",range=[0,105]),
        height=400,legend=dict(orientation="h",y=-0.22),
    )
    return fig


def fig_shock_bars(news_deltas: Dict[str,float]) -> go.Figure:
    if not news_deltas:
        return go.Figure()
    df_n = pd.DataFrame(list(news_deltas.items()),columns=["country","delta"])
    df_n = df_n[df_n["delta"]>0].sort_values("delta",ascending=False)
    colors = df_n["delta"].map(lambda x:C["danger"] if x>1.2 else C["warning"])
    fig = go.Figure(go.Bar(
        x=df_n["delta"],y=df_n["country"],orientation="h",
        marker=dict(color=colors,line=dict(width=0)),
        text=df_n["delta"].round(2),textposition="outside",
        textfont=dict(family="IBM Plex Mono,monospace",size=8),
        hovertemplate="<b>%{y}</b><br>Δ Shock: +%{x:.2f}<extra></extra>",
    ))
    fig.update_layout(**DL,
        title=dict(text="Ajuste Shock por Noticias en Vivo",
                   font=dict(size=10,color="#D0E0F0",family="IBM Plex Mono")),
        xaxis=dict(title="Δ Shock Score"),
        yaxis=dict(autorange="reversed"),
        height=max(180,len(df_n)*30+60),showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;
                    letter-spacing:0.2em;color:{C['accent1']};margin-bottom:12px;">
        ⬡ GEOINTEL TERMINAL · ICG v3.0
        </div>""", unsafe_allow_html=True)

        st.markdown("#### 🎨 Theme Engine")
        theme_label = st.selectbox("Lente temático", list(THEMES.keys()), index=0)
        theme = THEMES[theme_label]

        st.markdown("---")
        st.markdown("#### 🇺🇸 Simulador de Shocks")
        tariff = st.slider("Arancel EE.UU. (%)", 0, 100, 0, 5)
        export_ctrl = st.slider("Intensidad Export Controls (0-10)", 0.0, 10.0, 0.0, 0.5,
                                help="Simula expansión de controles de exportación tipo Wassenaar/BIS")

        st.markdown("---")
        st.markdown("#### ⚖️ Pesos ICG Base")
        w_l = st.slider("Peso Apalancamiento", 0.5, 2.0, 1.0, 0.1)
        w_r = st.slider("Peso Resiliencia",    0.5, 2.0, 1.0, 0.1)

        st.markdown("---")
        st.markdown("#### 📰 Noticias en Vivo")
        news_key = st.text_input("NewsAPI Key", type="password",
                                  placeholder="newsapi.org/register (gratis)")
        fetch_btn = st.button("🔄 Actualizar noticias", use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔬 Comparación Dual")
        all_c = sorted(["United States","China","Russia","Germany","Japan","France",
                         "India","Brazil","Saudi Arabia","Iran","Canada","Australia",
                         "South Korea","Taiwan","United Kingdom","Turkey","UAE",
                         "Netherlands","Norway","Vietnam","Indonesia","Mexico",
                         "Argentina","Chile","Colombia","Nigeria","Egypt","Israel",
                         "Morocco","Kazakhstan","Pakistan","Poland","Switzerland",
                         "Qatar","North Korea","Venezuela","Malaysia","Thailand",
                         "Bangladesh","Philippines","Ethiopia","Peru","Italy","Sweden"])
        country_a = st.selectbox("País A", all_c, index=all_c.index("United States"))
        country_b = st.selectbox("País B", all_c, index=all_c.index("China"))

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:0.68rem;color:{C['text2']};line-height:1.7;">
        <b style="color:{C['accent3']};">Fuentes:</b><br>
        WB WDI · UN Comtrade · OECD TiVA<br>
        UNCTAD TRAINS · Wassenaar/NSG<br>
        IMF · G20 · Brookings/CSIS/CFR<br>
        OFAC · EU Sanctions Map<br>
        NewsAPI.org (shock layer)<br><br>
        <i>Modo offline-first activo.</i>
        </div>""", unsafe_allow_html=True)

    # ── CARGA DE DATOS ───────────────────────────────────────────────────────
    df_raw = build_database()

    # Noticias
    news_articles, news_deltas = [], {}
    if fetch_btn and news_key:
        with st.spinner("Consultando NewsAPI..."):
            news_articles = fetch_news(news_key, page_size=30)
            news_deltas   = news_to_shock_deltas(news_articles)
            st.session_state["news_articles"] = news_articles
            st.session_state["news_deltas"]   = news_deltas
    elif "news_articles" in st.session_state:
        news_articles = st.session_state["news_articles"]
        news_deltas   = st.session_state["news_deltas"]

    # Export control shock: reduce supply_chain_centrality de países afectados
    df_sim = df_raw.copy()
    if export_ctrl > 0:
        # Países con altos export controls (potencias) los imponen sobre otros
        target_countries = ["China","Russia","Iran","North Korea","Venezuela"]
        mask = df_sim["country"].isin(target_countries)
        df_sim.loc[mask, "supply_chain_centrality"] = (
            df_sim.loc[mask, "supply_chain_centrality"] * (1 - export_ctrl * 0.05)
        ).clip(0, 100)

    # Calcular sistema completo
    df = compute_full_system(df_sim, theme=theme, w_l=w_l, w_r=w_r,
                              tariff_shock=float(tariff),
                              news_deltas=news_deltas if news_deltas else None)
    df_blocs = compute_bloc_scores(df)

    # ── HEADER ───────────────────────────────────────────────────────────────
    active_theme_desc = THEME_DESCRIPTIONS.get(theme, "Análisis global multicapa") if theme else "Análisis global multicapa — todas las dimensiones activas"

    st.markdown(f"""
    <div class="geo-header">
        <div class="geo-eyebrow">⬡ Geoeconomic Intelligence Terminal · Sistema Multicapa · v3.0</div>
        <h1 class="geo-title">Índice de Conversión Geoeconómica</h1>
        <p class="geo-sub">{active_theme_desc}</p>
        <div class="geo-formula">
            BASE_ICG = GeoMean(L^wL, R^wR) × exp(−0.8 × D/100) − Penalidad_Arancel
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Alertas activas
    if tariff > 0 or export_ctrl > 0 or news_deltas:
        alerts = []
        if tariff > 0:
            alerts.append(f"⚡ Arancel EE.UU. activo: <b>{tariff}%</b>")
        if export_ctrl > 0:
            alerts.append(f"🔒 Export Controls activos: intensidad <b>{export_ctrl}/10</b>")
        if news_deltas:
            top = sorted(news_deltas.items(), key=lambda x:-x[1])[:3]
            alerts.append("📡 Ajuste shock por noticias: " +
                          ", ".join(f"<b>{c}</b> +{v:.1f}" for c,v in top))
        for a in alerts:
            st.markdown(f'<div class="geo-alert">{a}</div>', unsafe_allow_html=True)

    # ── MÉTRICAS RÁPIDAS ─────────────────────────────────────────────────────
    top     = df.iloc[0]
    bottom  = df.iloc[-1]
    avg_icg = df["base_icg"].mean()
    usa     = df[df["country"]=="United States"]["base_icg"]
    usa_v   = usa.values[0] if len(usa) else 0.0
    n_crit  = int((df["base_icg"] < 20).sum())
    n_shock = int((df["shock_score"] > 5).sum())

    c1,c2,c3,c4,c5 = st.columns(5)
    for col,(val,lbl,delta,dc,cls) in zip(
        [c1,c2,c3,c4,c5], [
            (top["country"].split()[0], "🏆 Mayor ICG Base",
             f"ICG = {top['base_icg']:.1f}", C["accent1"], "c1"),
            (bottom["country"].split()[0], "⚠️ Menor ICG Base",
             f"ICG = {bottom['base_icg']:.1f}", C["danger"], "c2"),
            (f"{avg_icg:.1f}", "📊 Promedio Panel",
             f"{len(df)} países", C["text2"], "c3"),
            (f"{usa_v:.1f}", "🇺🇸 ICG EE.UU.",
             f"Benchmark global", C["accent3"], "c4"),
            (str(n_crit+n_shock), "🚨 Alertas",
             f"{n_crit} críticos · {n_shock} alto shock", C["warning"], "c5"),
        ]
    ):
        col.markdown(f"""
        <div class="stat-card {cls}">
            <div class="stat-val" style="font-size:1.6rem;">{val}</div>
            <div class="stat-lbl">{lbl}</div>
            <div class="stat-delta" style="color:{dc};">{delta}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS ─────────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "🌍 Mapa Global",
        "📊 Rankings",
        "🏗️ Capacidad vs Regulación",
        "🎯 Comparación Dual",
        "🔥 Convergencia",
        "⬡ Bloques",
        "⚡ Shocks & Simulador",
        "📰 Noticias",
        "📋 Metodología",
    ])

    # ── TAB 0: MAPA ──────────────────────────────────────────────────────────
    with tabs[0]:
        mc1, mc2 = st.columns([3.5, 0.8])
        with mc2:
            st.markdown('<div class="sec-header">MÉTRICA</div>', unsafe_allow_html=True)
            metric = st.radio("", [
                "base_icg","leverage","resilience",
                "regulatory_power","strategic_signal",
                "capital_confirmation","shock_score","icg_delta",
            ], format_func=lambda x: {
                "base_icg": "🌐 ICG Base",
                "leverage": "⚡ Apalancamiento",
                "resilience": "🛡️ Resiliencia",
                "regulatory_power": "📜 Poder Regulatorio",
                "strategic_signal": "📡 Señal Estratégica",
                "capital_confirmation": "💰 Confirmación Capital",
                "shock_score": "💥 Shock Score",
                "icg_delta": "📉 Δ ICG (Tariff)",
            }[x], label_visibility="collapsed")
            st.markdown("---")
            st.markdown(f"""
            <div style="font-size:0.72rem;color:{C['text2']};line-height:1.8;">
            <span style="color:{C['accent1']};">⬡</span> Dominante: >72<br>
            <span style="color:#3DB87A;">⬡</span> Fuerte: 55-72<br>
            <span style="color:{C['accent2']};">⬡</span> Intermedio: 35-55<br>
            <span style="color:{C['warning']};">⬡</span> Vulnerable: 18-35<br>
            <span style="color:{C['danger']};">⬡</span> Crítico: <18
            </div>""", unsafe_allow_html=True)
        with mc1:
            title_map = {
                "base_icg": "BASE_ICG — Capacidad Geoeconómica Estructural",
                "leverage": "APALANCAMIENTO — Exportaciones Críticas + CGV + Reservas",
                "resilience": "RESILIENCIA — Energía + Alimentos + Independencia",
                "regulatory_power": "PODER REGULATORIO — NTMs + Export Controls + Estándares",
                "strategic_signal": "SEÑAL ESTRATÉGICA — Consenso Institucional + Think Tanks",
                "capital_confirmation": "CONFIRMACIÓN CAPITAL — FDI Estratégico + CAPEX Soberano",
                "shock_score": "SHOCK LAYER — Perturbaciones Activas (ALERTA)",
                "icg_delta": "Δ ICG — Impacto Arancelario Trump 2026",
            }
            st.plotly_chart(fig_choropleth(df, metric, title_map[metric]),
                            use_container_width=True, config={"scrollZoom":True})

    # ── TAB 1: RANKINGS ──────────────────────────────────────────────────────
    with tabs[1]:
        rc1, rc2 = st.columns(2)
        with rc1:
            n = st.slider("Países en ranking", 10, 45, 25, 1, key="rank_n")
            rank_col = st.selectbox("Ranking por:", [
                ("base_icg","ICG Base"),("leverage","Apalancamiento"),
                ("resilience","Resiliencia"),("regulatory_power","Poder Regulatorio"),
                ("strategic_signal","Señal Estratégica"),
                ("capital_confirmation","Confirmación Capital"),
            ], format_func=lambda x: x[1])
            st.plotly_chart(
                fig_ranking_bar(df, rank_col[0], n,
                                f"Ranking — {rank_col[1]}"),
                use_container_width=True)
        with rc2:
            # Theme leaders si hay tema activo
            if theme:
                st.markdown(f'<div class="sec-header">LÍDERES: {theme_label}</div>',
                            unsafe_allow_html=True)
                leaders = get_theme_leaders(df, theme, n=12)
                th_col  = THEME_COL_MAP.get(theme, "base_icg")
                st.plotly_chart(
                    fig_ranking_bar(leaders.rename(columns={th_col:"base_icg"}),
                                   "base_icg", len(leaders),
                                   f"Líderes Temáticos: {theme_label}"),
                    use_container_width=True)
                st.markdown(f'<div class="sec-header">MÁS VULNERABLES: {theme_label}</div>',
                            unsafe_allow_html=True)
                deps = get_theme_dependents(df, theme, n=8)
                st.dataframe(deps.style.background_gradient(
                    subset=[th_col], cmap="RdYlGn"),
                    use_container_width=True, hide_index=True)
            else:
                st.plotly_chart(
                    fig_ranking_bar(df, "regulatory_power", n,
                                   "Ranking — Poder Regulatorio"),
                    use_container_width=True)

    # ── TAB 2: CAPACIDAD vs REGULACIÓN ────────────────────────────────────────
    with tabs[2]:
        st.markdown(f"""
        <div class="geo-alert info">
        <b>NUEVA VISUALIZACIÓN:</b> Matriz Capacidad Material (BASE_ICG) vs Poder Regulatorio.
        Esta es la distinción más importante que el dashboard anterior no capturaba:
        un país puede tener alta capacidad material pero bajo poder regulatorio (China en chips),
        o alto poder regulatorio con menor músculo material (Países Bajos con ASML).
        Color = Señal Estratégica. Tamaño = PIB.
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(fig_material_vs_regulatory(df),
                        use_container_width=True)

        # Tabla de insights
        st.markdown('<div class="sec-header">INSIGHTS AUTOMÁTICOS</div>',
                    unsafe_allow_html=True)
        i1,i2,i3 = st.columns(3)

        high_mat_low_reg = df[(df["base_icg"]>55)&(df["regulatory_power"]<45)].head(5)
        i1.markdown(f"""
        <div class="insight-box">
        <span class="label">GIGANTES SIN PALANCA REGULATORIA</span>
        Alta capacidad material pero bajo poder para imponer reglas:
        {', '.join(high_mat_low_reg['country'].tolist())}
        </div>""", unsafe_allow_html=True)

        low_mat_high_reg = df[(df["base_icg"]<50)&(df["regulatory_power"]>60)].head(5)
        i2.markdown(f"""
        <div class="insight-box">
        <span class="label">REGULADORES SIN MÚSCULO</span>
        Alto poder normativo sin capacidad material proporcional:
        {', '.join(low_mat_high_reg['country'].tolist()) if not low_mat_high_reg.empty else 'Sin casos claros en panel actual'}
        </div>""", unsafe_allow_html=True)

        divergent = df.nlargest(5,"narrative_capital_divergence")
        i3.markdown(f"""
        <div class="insight-box">
        <span class="label">NARRATIVA SIN CAPITAL (DIVERGENCIA)</span>
        Alta señal estratégica pero baja confirmación financiera — posible sobreestimación:
        {', '.join(divergent['country'].tolist())}
        </div>""", unsafe_allow_html=True)

    # ── TAB 3: COMPARACIÓN DUAL ───────────────────────────────────────────────
    with tabs[3]:
        if country_a == country_b:
            st.warning("Selecciona dos países distintos.")
        else:
            st.plotly_chart(fig_radar_dual(df, country_a, country_b),
                            use_container_width=True)
            st.markdown(
                build_comparison_table_html(df, country_a, country_b),
                unsafe_allow_html=True)

            # Síntesis
            ra = df[df["country"]==country_a].iloc[0]
            rb = df[df["country"]==country_b].iloc[0]
            dims_cmp = ["base_icg","leverage","resilience",
                        "regulatory_power","strategic_signal","capital_confirmation"]
            wins_a = sum(1 for d in dims_cmp if ra[d]>rb[d])
            wins_b = len(dims_cmp) - wins_a
            winner = country_a if wins_a > wins_b else country_b
            ic = C["accent1"] if wins_a > wins_b else C["accent2"]

            st.markdown(f"""
            <div class="insight-box" style="margin-top:14px;">
            <span class="label">SÍNTESIS — {country_a.upper()} vs. {country_b.upper()}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:1.1rem;color:{ic};">
            {winner}</span> lidera en <b>{max(wins_a,wins_b)}</b> de {len(dims_cmp)} dimensiones.<br>
            ICG Base: <b style="color:{C['accent1']}">{ra['base_icg']:.1f}</b> (A) vs
            <b style="color:{C['accent2']}">{rb['base_icg']:.1f}</b> (B) |
            Shock: <b style="color:{C['warning']}">{ra['shock_score']:.1f}</b> (A) vs
            <b style="color:{C['warning']}">{rb['shock_score']:.1f}</b> (B)
            </div>""", unsafe_allow_html=True)

    # ── TAB 4: CONVERGENCIA ───────────────────────────────────────────────────
    with tabs[4]:
        st.markdown(f"""
        <div class="geo-alert info">
        <b>NUEVA VISUALIZACIÓN:</b> Heatmap de convergencia entre señal institucional,
        confirmación de capital y resiliencia temática. Verde intenso = triple convergencia
        (narrativa + dinero + capacidad alineados). Es la señal más fuerte que puede
        detectar este sistema.
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(fig_convergence_heatmap(df), use_container_width=True)

    # ── TAB 5: BLOQUES ────────────────────────────────────────────────────────
    with tabs[5]:
        bc1, bc2 = st.columns([1.2, 1])
        with bc1:
            st.plotly_chart(fig_bloc_radar(df_blocs), use_container_width=True)
        with bc2:
            st.markdown('<div class="sec-header">SCORES POR BLOQUE</div>',
                        unsafe_allow_html=True)
            disp_cols = ["base_icg","leverage","resilience",
                         "regulatory_power","strategic_signal",
                         "capital_confirmation","shock_score"]
            st.dataframe(
                df_blocs[disp_cols].round(1).style
                    .background_gradient(subset=["base_icg"], cmap="RdYlGn",vmin=20,vmax=80)
                    .background_gradient(subset=["shock_score"], cmap="RdYlGn_r",vmin=0,vmax=8)
                    .format("{:.1f}"),
                use_container_width=True)

    # ── TAB 6: SHOCKS & SIMULADOR ─────────────────────────────────────────────
    with tabs[6]:
        st.markdown(f"""
        <div class="geo-alert">
        <b>Simulador activo:</b> Arancel {tariff}% · Export Controls {export_ctrl}/10
        · {len(news_deltas)} países con ajuste de shock por noticias
        </div>""", unsafe_allow_html=True)

        sc1, sc2 = st.columns([1.4, 1])

        with sc1:
            # Impacto arancelario
            merged = df[["country","base_icg","base_icg_0","icg_delta","us_export_pct","shock_score"]].copy()
            merged = merged.sort_values("icg_delta").head(20)
            colors_d = merged["icg_delta"].map(
                lambda x: C["danger"] if x<-8 else C["warning"] if x<-2 else C["accent1"])
            fig_d = go.Figure(go.Bar(
                x=merged["icg_delta"],y=merged["country"],orientation="h",
                marker=dict(color=colors_d,line=dict(width=0)),
                text=merged["icg_delta"].round(2),textposition="outside",
                textfont=dict(family="IBM Plex Mono,monospace",size=8),
                customdata=merged["us_export_pct"],
                hovertemplate="<b>%{y}</b><br>ΔICG: %{x:.2f}<br>Expo EE.UU.: %{customdata:.1f}%<extra></extra>",
            ))
            fig_d.add_vline(x=0,line_color=C["accent3"],line_width=1.5)
            fig_d.update_layout(**DL,
                title=dict(text="Δ ICG por Choque Arancelario",
                           font=dict(size=11,color="#D0E0F0",family="IBM Plex Mono")),
                xaxis=dict(title="Δ ICG (puntos)"),
                yaxis=dict(autorange="reversed"),
                height=480,showlegend=False,
            )
            st.plotly_chart(fig_d, use_container_width=True)

        with sc2:
            st.markdown('<div class="sec-header">TRAYECTORIA DE PAÍS</div>',
                        unsafe_allow_html=True)
            country_sim = st.selectbox(
                "País a simular",
                options=sorted(df["country"].tolist()),
                index=sorted(df["country"].tolist()).index("Mexico") if "Mexico" in df["country"].tolist() else 0
            )
            step_v = st.radio("Resolución", [("5%",5),("1%",1)],
                              format_func=lambda x:x[0])[1]
            with st.spinner(f"Simulando {country_sim}..."):
                st.plotly_chart(
                    fig_tariff_trajectory(df_raw.copy(), country_sim,
                                          step=step_v, theme=theme),
                    use_container_width=True)

            # Panel interpretación
            cd = df[df["country"]==country_sim]
            if not cd.empty:
                r = cd.iloc[0]
                delta = r["icg_delta"]
                ic = C["danger"] if delta<-5 else C["warning"] if delta<0 else C["accent1"]
                dep_pct = r["us_export_pct"]
                msg = (f"<b style='color:{C['danger']}'>⚠ Alta vulnerabilidad:</b> {dep_pct:.1f}% expo a EE.UU." if dep_pct>20 else
                       f"<b style='color:{C['warning']}'>⚡ Exposición moderada:</b> {dep_pct:.1f}% expo a EE.UU." if dep_pct>5 else
                       f"<b style='color:{C['accent1']}'>🛡 Alta resiliencia al shock.</b> Dep. EE.UU.: {dep_pct:.1f}%")
                st.markdown(f"""
                <div class="insight-box">
                <span class="label">ANÁLISIS — {country_sim.upper()}</span>
                <span style="font-family:'IBM Plex Mono';font-size:1.1rem;color:{ic};">
                ΔICG = {delta:+.2f} pts</span> · ICG: {r['base_icg_0']:.1f} → {r['base_icg']:.1f}<br>
                Shock score: {r['shock_score']:.1f}/10 · Sanciones: {r['sanctions_regime']}<br>
                {msg}
                </div>""", unsafe_allow_html=True)

    # ── TAB 7: NOTICIAS ───────────────────────────────────────────────────────
    with tabs[7]:
        if not news_articles:
            st.markdown(f"""
            <div class="geo-alert info">
            Introduce una <b>NewsAPI key</b> en el panel lateral y pulsa
            "Actualizar noticias". Registro gratuito (100 req/día): newsapi.org/register<br><br>
            Las noticias se procesan para detectar países en contexto de sanciones/aranceles
            y ajustan el <b>Shock Layer</b> — <i>no el ICG Base</i>.
            Esta separación es metodológicamente correcta.
            </div>""", unsafe_allow_html=True)
        else:
            na1, na2 = st.columns([2, 1])
            with na1:
                st.markdown(f'<div class="sec-header">{len(news_articles)} ARTÍCULOS · '
                            f'{sum(1 for a in news_articles if a["impact"]>=2)} ALTO IMPACTO</div>',
                            unsafe_allow_html=True)
                for art in news_articles[:18]:
                    lvl = "🔴" if art["impact"]>=2 else "🟡" if art["impact"]==1 else "⚪"
                    cs  = ", ".join(art["countries"][:3]) if art["countries"] else "—"
                    st.markdown(f"""
                    <div style="background:{C['panel']};border:1px solid {C['border']};
                                border-radius:5px;padding:10px 14px;margin-bottom:8px;">
                        <div style="font-size:0.83rem;color:{C['text']};font-weight:500;">
                        {lvl} {art['title']}</div>
                        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
                                    color:{C['accent3']};margin-top:4px;">
                        {art['source']} · {art['published']} · {cs}
                        <a href="{art['url']}" target="_blank"
                           style="color:{C['accent3']};margin-left:8px;">↗</a>
                        </div>
                    </div>""", unsafe_allow_html=True)
            with na2:
                if news_deltas:
                    st.plotly_chart(fig_shock_bars(news_deltas),
                                    use_container_width=True)

    # ── TAB 8: METODOLOGÍA ────────────────────────────────────────────────────
    with tabs[8]:
        mt1, mt2 = st.columns(2)
        with mt1:
            st.markdown("#### 📐 Arquitectura del Sistema")
            st.markdown(r"""
**Correcciones metodológicas vs. v1/v2:**

| Problema v1/v2 | Solución v3.0 |
|---|---|
| Min-max (panel-dependiente) | Percentile rank (panel-invariante) |
| Sanciones lineales | Penalidad discreta por régimen |
| `√(L×R)/(1+D/100)` lineal | Geometric mean + `exp(−γD)` convexa |
| Stocks y flows mezclados | Separados en leverage (flows) vs resiliencia (stocks) |
| Solo capacidad material | + Poder regulatorio + Señal + Capital |
| Ajuste news → sanctions_score | Ajuste news → shock_layer (overlay, no ICG) |

**Fórmula BASE_ICG:**

$$\text{ICG}_i = \left(L_i^{w_L} \cdot R_i^{w_R}\right)^{\frac{1}{w_L+w_R}} \cdot e^{-0.8 \cdot D_i/100} - \text{Pen}_{arancel}$$

**Penalidad de dependencia exponencial:**

Con γ=0.8:
- D=0%  → factor = 1.00 (sin penalidad)  
- D=50% → factor = 0.67 (−33%)  
- D=100% → factor = 0.45 (−55%)  

(vs. v1/v2 donde D=100 solo dividía por 2)

**Capas del sistema:**

```
ICG_Composite = BASE_ICG
                × (1 + λ₁·Signal) × (1 + λ₂·Capital)
                × exp(−δ·Shock)
```

λ₁ = λ₂ = 0.12 · δ = 0.15 (overlays suaves)

**Variables nuevas:**
- `supply_chain_centrality`: OECD TiVA — posición en CGV
- `import_strategic_dep`: dependencia de importaciones críticas
- `ntm_density`: UNCTAD TRAINS — medidas no arancelarias
- `export_control_score`: Wassenaar/NSG/MTCR + unilateral
- `standards_power`: ISO + 3GPP + CODEX leadership
- `institutional_signal`: frecuencia en docs IMF/WB/OECD/G20
- `think_tank_consensus`: Brookings/CSIS/CFR/Chatham/ECFR
- `fdi_quality`: % IED en sectores estratégicos (UNCTAD WIR)
- `sovereign_capex_signal`: señal de fondos soberanos
- `multi_alignment`: membresía simultánea en bloques

**Normalización:** Percentile rank sobre panel de 50 países.
Ventaja: un nuevo país en el panel no redistribuye los scores existentes.
""")
        with mt2:
            st.markdown("#### 🗂️ Estructura de Código")
            st.code("""
# Arquitectura modular (un archivo para Streamlit Cloud,
# separable en módulos para producción)

scoring/
  base_icg.py         # compute_leverage, compute_resilience,
                      # compute_dependence, compute_base_icg
  friction_layer.py   # compute_friction_layer (NTMs, standards)
  signal_layer.py     # compute_signal_layer (IMF/WB/think tanks)
  capital_layer.py    # compute_capital_layer (FDI, CAPEX)
  shock_layer.py      # compute_shock_layer (news, events)
  composite.py        # compute_full_system

data/
  base_data.py        # build_database() — 50+ países
  theme_weights.py    # pesos por tema (energy, chips, etc.)

engines/
  theme_engine.py     # get_theme_leaders, get_theme_dependents
  bloc_engine.py      # compute_bloc_scores
  news_engine.py      # fetch_news, news_to_shock_deltas

viz/
  maps.py             # fig_choropleth
  matrices.py         # fig_material_vs_regulatory, fig_convergence_heatmap
  radars.py           # fig_radar_dual, fig_bloc_radar
  rankings.py         # fig_ranking_bar
  simulators.py       # fig_tariff_trajectory

app.py                # layout Streamlit puro — sin lógica
config.py             # colores, temas, bloques, constantes
            """, language="bash")

            st.markdown("#### 📦 Requirements")
            st.code("""
streamlit>=1.32.0
plotly>=5.19.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
# Opcional para APIs reales:
# wbgapi        → Banco Mundial
# comtradeapicall → UN Comtrade
            """, language="text")

    # ── FOOTER ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;padding:20px 0 6px;
                border-top:1px solid {C['border']};margin-top:24px;">
        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
                     color:{C['text2']};letter-spacing:0.12em;">
        GEOINTEL TERMINAL · ICG v3.0 · Ciencia de Datos & Geopolítica<br>
        WB WDI · UN Comtrade · OECD TiVA · UNCTAD TRAINS · Wassenaar · OFAC · NewsAPI
        </span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
