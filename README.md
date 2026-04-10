# MAP
# 🌐 ICG — Índice de Conversión Geoeconómica

**Dashboard interactivo de análisis geopolítico** construido con Streamlit y Plotly. Mide la capacidad de un Estado para convertir sus recursos económicos en poder político internacional, e incluye un simulador de escenarios arancelarios para el caso Trump 2026.

---

## ¿Qué es el ICG?

El Índice de Conversión Geoeconómica (ICG) responde a una pregunta central en la ciencia política internacional: dado que dos países tienen recursos similares, ¿por qué uno ejerce más influencia que el otro? La respuesta no está solo en el tamaño de la economía, sino en la capacidad de *convertir* esos recursos en palancas de poder —y en el grado en que la dependencia externa limita esa conversión.

### Fórmula central

$$ICG = \frac{\sqrt{Apalancamiento^{w_L} \times Resiliencia^{w_R}}}{1 + \frac{Dependencia\_Externa}{100}} - Penalidad_{Arancelaria}$$

Los pesos $w_L$ y $w_R$ son ajustables desde el panel lateral del dashboard. La penalidad arancelaria es el mecanismo del **Simulador Trump 2026**.

### Componentes

| Dimensión | Variables | Fuente recomendada |
|---|---|---|
| **Apalancamiento** | Exportaciones críticas (HS27+HS26+HS84), reservas de divisas y oro, penalidad por sanciones activas | UN Comtrade, IMF IFS |
| **Resiliencia** | Autosuficiencia energética (exportaciones netas), autosuficiencia alimentaria, bono por tamaño de economía | World Bank WDI, FAO |
| **Dependencia Externa** | % exportaciones hacia potencia hegemónica regional, score de sanciones internacionales | WITS/World Bank, OFAC |

### Escala de interpretación

| Rango ICG | Categoría | Perfil geopolítico |
|---|---|---|
| 80 – 100 | **Dominante** | Alta capacidad de coacción económica y proyección de poder |
| 60 – 80 | **Fuerte** | Vectores de influencia regional, margen de maniobra amplio |
| 40 – 60 | **Intermedio** | Posición negociadora, vulnerable a presiones externas selectivas |
| 20 – 40 | **Vulnerable** | Dependencia estructural, opciones limitadas ante shocks |
| 0 – 20 | **Crítico** | Estado geoeconómicamente frágil, sin capacidad de conversión |

---

## Características del dashboard

### Mapa coroplético global
Visualización interactiva que colorea cada país según su ICG (o cualquiera de sus componentes). Cambia entre *ICG compuesto*, *Apalancamiento*, *Resiliencia*, *Dependencia* y *Δ ICG con arancel activo* desde el panel lateral. Basado en Plotly Express con proyección Natural Earth.

### Simulador Trump 2026
Slider de 0 % a 100 % que modela el impacto de aranceles estadounidenses sobre el ICG de cada nación. El mecanismo de transmisión es directo y documentado:

```
Penalidad_i = (us_export_pct_i / 100) × (T_arancel / 100) × 0.70 × 100
```

El factor de fricción 0.70 refleja que no toda la producción afectada se redirige perfectamente a mercados alternativos. Resultados validados:

| País | ICG base | Arancel 100 % | Δ |
|---|---|---|---|
| México | 39.1 | 16.8 | −22.3 pts |
| Canadá | 68.2 | 47.8 | −20.4 pts |
| China | 76.0 | 71.3 | −4.7 pts |
| Irán | 49.3 | 49.3 | 0.0 pts (ya embargado) |
| Rusia | 83.5 | 83.1 | −0.3 pts |

### Matriz geopolítica de cuadrantes
Scatter plot Apalancamiento vs. Resiliencia con burbujas proporcionales al PIB. Divide el espacio en cuatro cuadrantes: Potencias Globales, Autarquías Resilientes, Potencias Vulnerables y Estados Frágiles.

### Radar de comparación multidimensional
Selecciona hasta seis países desde el panel lateral y compara sus perfiles dimensionales en un gráfico de radar superpuesto.

### Zona de sombra arancelaria
Scatter plot Sanciones vs. ICG que identifica los países más expuestos a la presión estadounidense y con menor capacidad de absorber un choque externo.

### Trayectoria de país específico
Simulación continua del ICG de un país seleccionado a lo largo de toda la escala arancelaria (0–100 %), con tres escenarios (optimista, base, pesimista) y bandas de incertidumbre calculadas por bootstrap.

---

## Instalación

```bash
# Dependencias mínimas
pip install streamlit plotly pandas numpy requests wbgapi

# Opcional — wrappers oficiales de APIs
pip install comtradeapicall   # UN Comtrade oficial
pip install imf-reader        # IMF Data API

# Clonar y ejecutar
git clone https://github.com/tu-usuario/icg-dashboard.git
cd icg-dashboard
streamlit run icg_dashboard.py
```

El dashboard se abre automáticamente en `http://localhost:8501`.

---

## Configuración de API keys

Crea el archivo `.streamlit/secrets.toml` en la raíz del proyecto:

```toml
# UN Comtrade — necesaria para más de 100 req/hora
# Registro gratuito: https://comtradeapi.un.org/
COMTRADE_KEY = "tu-api-key-aquí"
```

El Banco Mundial y el FMI no requieren clave para uso estándar (con límites de tasa). El dashboard funciona completamente sin ninguna API key gracias al modo **offline-first**: cuando una fuente no responde, usa la base de datos geopolítica documentada integrada en el código.

---

## Arquitectura de datos

El sistema opera en tres capas con degradación elegante:

```
Petición de datos
      │
      ▼
┌─────────────────────┐
│  1. wbgapi (Python) │  → PIB, IED, energía, reservas
│     Banco Mundial   │     Indicadores: NY.GDP.MKTP.CD
└────────┬────────────┘     EG.IMP.CONS.ZS, FI.RES.TOTL.CD
         │ falla
         ▼
┌─────────────────────┐
│  2. REST endpoint   │  → https://api.worldbank.org/v2/
│     World Bank API  │     Mismo indicador, sin librería
└────────┬────────────┘
         │ falla
         ▼
┌─────────────────────┐
│  3. Base de datos   │  → 22 países × 7 variables
│     offline-first   │     Documentada con fuentes primarias
└─────────────────────┘     Actualizable manualmente
```

### APIs integradas

| API | Endpoint | Variables extraídas | Requiere key |
|---|---|---|---|
| **Banco Mundial** | `api.worldbank.org/v2/` | PIB, energía, reservas | No |
| **UN Comtrade** | `comtradeapi.un.org/public/v1/` | Exportaciones HS27, HS26, HS84 | No (≤100 req/h) |
| **FMI IFS** | `dataservices.imf.org/REST/SDMX_JSON.svc/` | Reservas de divisas | No |

---

## Estructura del proyecto

```
icg-dashboard/
├── icg_dashboard.py        # Aplicación principal (1,900 líneas)
├── .streamlit/
│   └── secrets.toml        # API keys (no commitear)
├── README.md
└── requirements.txt
```

### `requirements.txt`

```
streamlit>=1.32.0
plotly>=5.19.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
wbgapi>=1.0.12
```

---

## Fuentes de datos primarias

Todos los datos de la base offline están documentados con su fuente primaria. Las variables de codificación ordinal (banco de desarrollo, profundidad de acuerdos, membresía en bloques) están explicadas en la pestaña **Datos y Metodología** del dashboard.

| Variable | Fuente | Indicador / URL |
|---|---|---|
| Exportaciones críticas | UN Comtrade | HS 27 + HS 26 + HS 84 · `comtrade.un.org` |
| Reservas de divisas | World Bank IDS | `FI.RES.TOTL.CD` |
| Importaciones de energía | World Bank WDI | `EG.IMP.CONS.ZS` |
| Autosuficiencia alimentaria | FAO / USDA | Food Balance Sheets · `fao.org/faostat` |
| PIB | World Bank WDI | `NY.GDP.MKTP.CD` |
| % exportaciones hacia P1 | WITS / World Bank | Partner share · `wits.worldbank.org` |
| Score de sanciones | OFAC + EU Sanctions Map | `sanctionsmap.eu` · `ofac.treasury.gov` |

---

## Limitaciones y notas metodológicas

**Sobre la fórmula.** El ICG es un índice sintético de análisis comparativo, no una medida de poder absoluto. La raíz cuadrada del producto Apalancamiento × Resiliencia reduce la dominancia extrema de actores con ventaja en una sola dimensión. El divisor `(1 + D/100)` evita el colapso matemático en casos de dependencia máxima.

**Sobre la base de datos offline.** Los valores de la base integrada son proxies documentados ca. 2022–2023. Para análisis de política o publicación académica se recomienda reemplazarlos con datos extraídos directamente de las APIs. Las variables ordinales (v4 banco de desarrollo, v9 bloques multilaterales, v10 profundidad de acuerdos) son codificaciones del investigador y deben tratarse como tal.

**Sobre el simulador arancelario.** El modelo asume un mecanismo de transmisión lineal con factor de fricción fijo (0.70). En la realidad, la elasticidad de redirección de exportaciones varía según el bien, el país y la disponibilidad de mercados alternativos. El simulador es una herramienta de escenarios, no un modelo econométrico de equilibrio general.

**Sobre los datos de Irán y Corea del Norte.** Los valores de exportaciones y reservas de países bajo sanciones máximas son estimaciones con alta incertidumbre. Se recomiendan las fuentes CIA World Factbook, informes del Panel de Expertos de la ONU y bases de CSIS para refinar esos casos.

---

## Casos de uso

- **Análisis académico** de poder geoeconómico comparado en economía política internacional.
- **Docencia** en cursos de relaciones internacionales, geopolítica y economía política.
- **Inteligencia estratégica** para evaluar vulnerabilidades de cadenas de suministro ante escenarios de sanciones o aranceles.
- **Periodismo de datos** sobre el impacto de la política comercial de la administración Trump 2025–2029.
- **Base para investigación** sobre dependencia geoeconómica triangular y umbrales de conversión.

---

## Licencia

MIT License. Los datos de la base offline son proxies documentados de fuentes públicas — ver atribuciones en la pestaña *Datos y Metodología* del dashboard y en los comentarios del código.
