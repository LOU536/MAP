# 🌐 ICG — Índice de Conversión Geoeconómica v2.0

**Dashboard interactivo de análisis geopolítico** construido con Streamlit y Plotly. Mide la capacidad de un Estado para convertir sus recursos económicos en poder político internacional, con simulador de escenarios arancelarios Trump 2026, radar de comparación dual y monitor de sanciones en tiempo real vía noticias.

---

## ¿Qué es el ICG?

El Índice de Conversión Geoeconómica responde a una pregunta central en la ciencia política internacional: dado que dos países tienen recursos similares, ¿por qué uno ejerce más influencia que el otro? La respuesta no está solo en el tamaño de la economía, sino en la capacidad de *convertir* esos recursos en palancas de poder —y en el grado en que la dependencia externa limita esa conversión.

### Fórmula central (calibrada v3)

$$ICG = \frac{\sqrt{Apalancamiento^{w_L} \times Resiliencia^{w_R}}}{1 + \frac{Dependencia}{100}} - Penalidad_{Arancelaria}$$

Los pesos $w_L$ y $w_R$ son ajustables desde el panel lateral. La penalidad arancelaria activa el **Simulador Trump 2026**.

### Componentes

| Dimensión | Variables | Fuente recomendada |
|---|---|---|
| **Apalancamiento** | Exportaciones críticas (HS27+HS26+HS84), reservas de divisas y oro, penalidad por sanciones activas | UN Comtrade, IMF IFS |
| **Resiliencia** | Autosuficiencia energética (exportaciones netas), autosuficiencia alimentaria, bono por tamaño de economía | World Bank WDI, FAO |
| **Dependencia Externa** | % exportaciones hacia EE.UU., score de sanciones internacionales | WITS/World Bank, OFAC |

### Escala de interpretación

| Rango ICG | Categoría | Perfil geopolítico |
|---|---|---|
| 80 – 100 | **Dominante** | Alta capacidad de coacción económica y proyección de poder |
| 60 – 80 | **Fuerte** | Vectores de influencia regional, margen de maniobra amplio |
| 40 – 60 | **Intermedio** | Posición negociadora, vulnerable a presiones externas selectivas |
| 20 – 40 | **Vulnerable** | Dependencia estructural, opciones limitadas ante shocks |
| 0 – 20 | **Crítico** | Estado geoeconómicamente frágil, sin capacidad de conversión |

---

## Características del dashboard (v2.0)

### 🌍 Mapa coroplético global
Colorea cada país según su ICG o cualquiera de sus componentes. Cambia entre ICG compuesto, Apalancamiento, Resiliencia, Dependencia y Δ ICG con arancel activo. Proyección Natural Earth con zoom interactivo.

### 🎯 Radar de comparación dual *(nuevo en v2.0)*
Selecciona dos países y compara sus perfiles en cuatro dimensiones simultáneamente: Apalancamiento, Resiliencia, Autonomía Estratégica e ICG Global. Una tabla muestra con badge **✓ Gana** la dimensión en que cada país supera al otro, y un párrafo interpretativo resume quién lidera en cada vector.

### ⚡ Simulador Trump 2026
Slider de 0 % a 100 % que modela el impacto de aranceles estadounidenses en tiempo real:

```
Penalidad_i = (expo_EE.UU._i / 100) × (T / 100) × 0.70 × 100 × 0.25
```

El factor 0.70 refleja que los países redirigen parte de sus exportaciones a otros mercados. Resultados validados:

| País | ICG base | Arancel 100 % | Δ |
|---|---|---|---|
| México | 39.1 | 16.8 | −22.3 pts |
| Canadá | 68.2 | 47.8 | −20.4 pts |
| China | 76.0 | 71.3 | −4.7 pts |
| Irán | 49.3 | 49.3 | 0.0 pts (ya embargado) |
| Rusia | 83.5 | 83.1 | −0.3 pts |

### 📰 Noticias en vivo con ajuste automático de sanciones *(nuevo en v2.0)*
Con una API key de NewsAPI.org (gratuita, 100 req/día), el dashboard consulta titulares en tiempo real, detecta países mencionados en noticias de sanciones o aranceles, y ajusta automáticamente su `sanctions_score`. Los artículos de menos de 6 horas pesan el doble. El ajuste se propaga inmediatamente al ICG de todos los países.

### 📊 Matriz geopolítica de cuadrantes
Scatter plot Apalancamiento vs. Resiliencia con burbujas proporcionales al PIB. Divide el espacio en: Potencias Globales, Autarquías Resilientes, Potencias Vulnerables y Estados Frágiles.

### 🔮 Trayectoria de país específico
Simulación continua del ICG de un país a lo largo de toda la escala arancelaria (0–100 %), con tres escenarios (optimista, base, pesimista) y bandas de incertidumbre.

---

## Instalación

```bash
pip install streamlit plotly pandas numpy requests
streamlit run icg_dashboard.py
```

El dashboard abre en `http://localhost:8501` y funciona sin ninguna API key gracias al modo **offline-first**.

---

## requirements.txt

Tu archivo actual es suficiente:

```
streamlit
pandas
plotly
numpy
requests
```

Si quieres activar la conexión directa al Banco Mundial, añade:

```
wbgapi
```

No hay ninguna otra dependencia requerida.

---

## Configuración de API keys

Crea `.streamlit/secrets.toml`. Ambas son completamente opcionales:

```toml
# NewsAPI — noticias en vivo para ajuste automático de sanciones
# Gratuita (100 req/día): https://newsapi.org/register
NEWS_API_KEY = "tu-key-newsapi"

# UN Comtrade — para superar el límite de 100 req/hora
# Registro: https://comtradeapi.un.org/
COMTRADE_KEY = "tu-key-comtrade"

# Banco Mundial e IMF no requieren key
```

> En Streamlit Cloud, introduce las keys en **Settings → Secrets** de tu app, no en el repositorio.

---

## Estructura del proyecto

```
icg-dashboard/
├── icg_dashboard.py     # Aplicación principal
├── requirements.txt     # Dependencias
├── README.md
└── .streamlit/
    └── secrets.toml     # API keys (NO commitear)
```

Añade al `.gitignore`:
```
.streamlit/secrets.toml
```

---

## Fuentes de datos primarias

| Variable | Fuente | Referencia |
|---|---|---|
| Exportaciones críticas | UN Comtrade | HS 27 + HS 26 + HS 84 · `comtrade.un.org` |
| Reservas de divisas | World Bank IDS | `FI.RES.TOTL.CD` |
| Importaciones de energía | World Bank WDI | `EG.IMP.CONS.ZS` |
| Autosuficiencia alimentaria | FAO / USDA | Food Balance Sheets · `fao.org/faostat` |
| PIB | World Bank WDI | `NY.GDP.MKTP.CD` |
| % exportaciones hacia EE.UU. | WITS / World Bank | Partner share · `wits.worldbank.org` |
| Score de sanciones | OFAC + EU Sanctions Map | `sanctionsmap.eu` · `ofac.treasury.gov` |
| Noticias en vivo | NewsAPI.org | `newsapi.org/v2/everything` |

---

## Limitaciones

**Fórmula.** El ICG es un índice comparativo, no una medida de poder absoluto. La raíz cuadrada suaviza la dominancia extrema de actores con ventaja en una sola dimensión. El divisor `(1 + D/100)` evita el colapso matemático en dependencia máxima.

**Base offline.** Valores proxy ca. 2022–2023. Para análisis académico se recomienda reemplazarlos con datos extraídos directamente de las APIs.

**Simulador arancelario.** Transmisión lineal con factor de fricción fijo (0.70). Es una herramienta de escenarios, no un modelo de equilibrio general.

**Ajuste por noticias.** El sistema detecta países por coincidencia de palabras clave, no por NLP semántico. El delta máximo de +2.5 pts por país limita el impacto de falsos positivos.

---

## Licencia

MIT License. Datos de la base offline son proxies documentados de fuentes públicas — ver atribuciones en la pestaña *Metodología* del dashboard y en los comentarios del código.
