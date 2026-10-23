"""Tema "tótem de precios nocturno" — única fuente de la paleta y del estilo (DESIGN.md).

La app se lee como el cartel de precios de la estación de noche: pocas cifras grandes, iluminadas,
sobre asfalto casi negro, y todo lo demás callado.

Reglas obligatorias:
  1. El amarillo Shell es la luz: la franja de la marquesina, la acción principal, la pestaña activa y
     las cifras clave. El texto SOBRE amarillo va en `SOBRE_AMARILLO`.
  2. El rojo Shell sólo alerta (quiebres, pérdidas, cortes) y la línea bajo la franja. Como texto sobre
     la noche no llega a 4,5:1: el texto de alerta va en `ROJO_TEXTO`.
  3. Un solo tema, oscuro. Una sola familia tipográfica: Archivo (variable de peso y ancho), guardada en
     `static/fonts/`; condensada y pesada para las cifras, normal para el texto; cifras tabulares.
  4. `plantilla_plotly()` pinta todos los gráficos; `paleta_json()` alimenta los tableros en JavaScript.
  5. `[theme]` de `.streamlit/config.toml` repite estos valores (conservar `fileWatcherType = "poll"`).
  6. Los colores de las series pasaron el validador de paletas (banda de luminosidad, croma y daltonismo)
     sobre `NOCHE`; el amarillo y el rojo de marca quedan fuera de la banda a propósito (son identidad).

PROHIBIDO repetir un hex fuera de este archivo (control N15).
"""

from __future__ import annotations

import plotly.graph_objects as go

# --- Marca (los hex difieren entre fuentes: default #FBCE07 / #DD1D21, N4) ---
AMARILLO = "#FBCE07"
ROJO = "#DD1D21"

# --- La noche: superficies ----------------------------------------------------
NOCHE = "#0E0D0B"            # fondo de la página: asfalto casi negro, cálido
PANEL = "#171613"            # paneles, desplegables, encabezado de las tablas
PANEL_2 = "#211F1B"          # controles y paneles dentro de un panel
FILETE = "#2E2B26"           # filetes de 1 px: la única estructura
FILETE_FUERTE = "#47423A"    # filete de un control al pasar el mouse
AMARILLO_SUAVE = "#2A2410"   # panel apenas encendido de amarillo (avisos del tablero)

# --- Texto ---------------------------------------------------------------------
TEXTO = "#EEEAE0"            # blanco cálido, como el acrílico del tótem
TEXTO_2 = "#B5AFA2"          # secundario
TEXTO_3 = "#958F82"          # terciario (ejes, notas al pie)
SOBRE_AMARILLO = "#16130C"   # texto sobre la luz amarilla
ROJO_TEXTO = "#FF7A6E"       # el rojo de alerta cuando es texto

# --- Nombres de siempre (los usan los gráficos y los tableros) -------------------
TINTA = TEXTO
TINTA_TENUE = TEXTO_2
FONDO = NOCHE
FONDO_PANEL = PANEL
BORDE = FILETE
ASFALTO = "#1B1A17"          # el playón de la animación
REFERENCIA = "#CFC9BB"       # ejes y líneas de referencia de los gráficos

# --- Series de los gráficos (validadas sobre NOCHE: banda L 0,48–0,67, croma ≥ 0,10) ---
AZUL = "#4F8FE0"             # GNC, caja del minimarket, barras de demanda
TURQUESA = "#1FA894"
NARANJA = "#D9772E"
VIOLETA = "#A47BE8"
GRIS = "#8E897E"             # lo neutro: la base, lo que no es ninguna categoría
CELESTE = "#45B0D6"          # nivel del tanque
INDIGO = "#7F86E8"           # flete en los costos por política
VERDE_OK = "#3FAE6A"
VERDE_INGRESO = "#5BC285"

# --- Estados (SIEMPRE con texto, no sólo color) -------------------------------
LIBRE = VERDE_OK
OCUPADO = AMARILLO
PERDIDO = ROJO

# --- Productos (5 colores distinguibles, N15) ---------------------------------
PRODUCTO = {
    "super": AMARILLO,
    "vpower": ROJO,
    "diesel": VIOLETA,
    "vpower_diesel": TURQUESA,
    "gnc": AZUL,
}

# --- Categorías de los gráficos (un color por significado) ---------------------
ESCENARIO = {"Base": GRIS, "A": AZUL, "B": VIOLETA, "C": TURQUESA}

# --- Detalles del dibujo de la animación (autos, surtidores, personas) ----------
FARO = "#F6E3A1"
NEUMATICO = "#0A0908"
VIDRIO = "#1B2230"
PLATA = "#C9C4B8"
ARBOL = "#1F3A2A"
ARBOL_2 = "#2A4E37"
ASFALTO_2 = "#24221E"        # el panel de cada zona sobre el playón

#: Color de cada producto (id del motor → color de `PRODUCTO`). El mismo color pinta
#: el auto en la animación, el surtidor, el tanque y su serie en los gráficos.
COLOR_PRODUCTO = {
    "super": PRODUCTO["super"],
    "vpower": PRODUCTO["vpower"],
    "diesel_g2": PRODUCTO["diesel"],
    "diesel_g3": PRODUCTO["vpower_diesel"],
    "gnc": PRODUCTO["gnc"],
}
#: Antes el tablero tenía su propia paleta oscura; ahora toda la app es oscura y es la misma.
COLOR_PRODUCTO_OSCURO = COLOR_PRODUCTO

#: Pares declarados para el control de contraste (WCAG ≥ 4,5:1, §10.3/N15).
PARES_CONTRASTE = (
    ("TEXTO/NOCHE", TEXTO, NOCHE),
    ("TEXTO/PANEL", TEXTO, PANEL),
    ("TEXTO/PANEL_2", TEXTO, PANEL_2),
    ("TEXTO_2/NOCHE", TEXTO_2, NOCHE),
    ("TEXTO_2/PANEL_2", TEXTO_2, PANEL_2),
    ("TEXTO_3/PANEL_2", TEXTO_3, PANEL_2),
    ("SOBRE_AMARILLO/AMARILLO", SOBRE_AMARILLO, AMARILLO),
    ("AMARILLO/NOCHE", AMARILLO, NOCHE),
    ("AMARILLO/PANEL_2", AMARILLO, PANEL_2),
    ("ROJO_TEXTO/PANEL", ROJO_TEXTO, PANEL),
    ("VERDE_OK/PANEL", VERDE_OK, PANEL),
    ("TEXTO/AMARILLO_SUAVE", TEXTO, AMARILLO_SUAVE),
    ("TEXTO_2/ASFALTO_2", TEXTO_2, ASFALTO_2),
)

#: Familia tipográfica (los archivos están en static/fonts/ y se declaran también en config.toml).
FAMILIA = "Archivo, 'Segoe UI', system-ui, sans-serif"
#: Ancho de Archivo para las cifras del tótem y los títulos (eje "wdth" de la variable, en %).
ANCHO_TOTEM = 72


# =============================================================================
# Utilidades de color
# =============================================================================
def _luminancia(hex_: str) -> float:
    """Luminancia relativa WCAG de un color #RRGGBB."""
    def canal(v: int) -> float:
        c = v / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    h = hex_.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(fondo: str, frente: str) -> float:
    """Razón de contraste WCAG (1 a 21; ≥ 4,5 para texto normal)."""
    l1, l2 = _luminancia(fondo), _luminancia(frente)
    clara, oscura = (l1, l2) if l1 > l2 else (l2, l1)
    return (clara + 0.05) / (oscura + 0.05)


def rgba(hex_: str, alfa: float) -> str:
    """`rgba(r, g, b, alfa)` a partir de un hex, para rellenos de Plotly."""
    h = hex_.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alfa})"


# =============================================================================
# Plotly: los gráficos sobre la noche
# =============================================================================
def plantilla_plotly() -> go.layout.Template:
    """Template de Plotly: fondo transparente (se ve la noche), grilla de filetes, Archivo y cifras tabulares."""
    ejes = dict(
        gridcolor=FILETE,
        zerolinecolor=FILETE_FUERTE,
        linecolor=FILETE_FUERTE,
        title_font=dict(color=TEXTO_2, size=13),
        tickfont=dict(color=TEXTO_2, size=12),
    )
    return go.layout.Template(
        layout=dict(
            colorway=[AMARILLO, AZUL, TURQUESA, NARANJA, VIOLETA, GRIS],
            font=dict(color=TEXTO, size=13, family=FAMILIA),
            paper_bgcolor=rgba(NOCHE, 0),
            plot_bgcolor=rgba(NOCHE, 0),
            title=dict(font=dict(color=TEXTO, size=16, family=FAMILIA)),
            legend=dict(font=dict(color=TEXTO_2), bgcolor=rgba(NOCHE, 0)),
            xaxis=dict(ejes),
            yaxis=dict(ejes),
            hoverlabel=dict(bgcolor=PANEL_2, bordercolor=FILETE_FUERTE,
                            font=dict(color=TEXTO, family=FAMILIA)),
            annotationdefaults=dict(font=dict(color=TEXTO_2)),
        )
    )


# =============================================================================
# CSS global: la marquesina, el encabezado, las pestañas, las cifras del tótem
# =============================================================================
def css_global() -> str:
    """CSS inyectado con `st.markdown(..., unsafe_allow_html=True)`."""
    a, n = AMARILLO, NOCHE
    return f"""<style>
/* Archivo con su eje de ancho (Streamlit declara el peso; acá también el ancho, para las cifras condensadas). */
@font-face {{ font-family: "Archivo"; src: url("app/static/fonts/Archivo-latin.woff2") format("woff2");
  font-weight: 100 900; font-stretch: 62% 125%; font-display: swap;
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329,
                 U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }}
@font-face {{ font-family: "Archivo"; src: url("app/static/fonts/Archivo-latin-ext.woff2") format("woff2");
  font-weight: 100 900; font-stretch: 62% 125%; font-display: swap;
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F,
                 U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF; }}

:root {{ color-scheme: dark; accent-color: {a}; }}
::selection {{ background: {a}; color: {SOBRE_AMARILLO}; }}
html {{ scrollbar-color: {FILETE_FUERTE} {n}; }}
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {n}; }}
::-webkit-scrollbar-thumb {{ background: {FILETE_FUERTE}; border-radius: 5px; border: 2px solid {n}; }}
::-webkit-scrollbar-thumb:hover {{ background: {TEXTO_3}; }}
body, .stApp {{ font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }}
a {{ text-underline-offset: 3px; }}
:focus-visible {{ outline: 2px solid {a} !important; outline-offset: 2px !important; }}

/* La marquesina: franja amarilla con la línea roja debajo, fija arriba (sin logo). */
.stApp::before {{ content: ""; position: fixed; inset: 0 0 auto 0; height: 14px; z-index: 1000002;
  background: linear-gradient({a} 0 11px, {ROJO} 11px 14px); pointer-events: none; }}
[data-testid="stHeader"] {{ background: transparent; top: 14px; height: 2.25rem;
  backdrop-filter: none; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 2.75rem; max-width: 1440px; }}

/* La portada: una foto apenas visible (30 %) detrás del encabezado, que se funde con la noche hacia abajo.
   La marquesina va arriba del simulador; la foto de la playa, sólo en el menú (static/img/). */
.st-key-portada, .st-key-portada_menu {{ position: relative; padding: 1.4rem 0 0.6rem; }}
.st-key-portada::before, .st-key-portada_menu::before {{ content: ""; position: absolute; z-index: 0;
  inset: -5.5rem -5rem -0.5rem; background-size: cover; opacity: 0.3; pointer-events: none;
  -webkit-mask-image: linear-gradient(to bottom, black 45%, transparent);
  mask-image: linear-gradient(to bottom, black 45%, transparent); }}
.st-key-portada::before {{ background-image: url("app/static/img/marquesina.webp"); background-position: center 38%; }}
.st-key-portada_menu::before {{ background-image: url("app/static/img/playa-gnc.webp"); background-position: center 30%; }}
.st-key-portada > *, .st-key-portada_menu > * {{ position: relative; z-index: 1; }}

/* Títulos: Archivo condensada y pesada, en mayúsculas, como los carteles de la estación. */
h1, h2, h3, h4 {{ font-variation-settings: "wdth" {ANCHO_TOTEM}; text-wrap: balance; }}
h1 {{ text-transform: uppercase; letter-spacing: 0.005em; line-height: 1.02 !important;
  font-size: clamp(1.8rem, 2.6vw, 2.4rem) !important; font-weight: 800 !important; }}
h2, h3 {{ letter-spacing: 0; }}
h4 {{ text-transform: uppercase; letter-spacing: 0.04em; font-size: 1.05rem !important; color: {TEXTO}; }}
h5 {{ font-size: 0.98rem !important; font-weight: 650 !important; color: {TEXTO}; }}
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a, [data-testid="stHeaderActionElements"] {{ display: none !important; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ max-width: 72ch; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: {TEXTO_2}; }}
[data-testid="stCaptionContainer"] p {{ max-width: 75ch; }}
hr {{ border-color: {FILETE} !important; }}
.tot-periodo {{ text-align: right; font-variation-settings: "wdth" {ANCHO_TOTEM}; font-weight: 750;
  text-transform: uppercase; letter-spacing: 0.04em; font-size: 1.05rem; color: {a}; line-height: 1.15;
  margin: 0.55rem 0 0.45rem; }}
.tot-periodo span {{ display: block; font-weight: 450; text-transform: none; letter-spacing: 0;
  font-variation-settings: "wdth" 100; font-size: 0.8rem; color: {TEXTO_2}; }}

/* Pestañas: una barra de filetes; la activa se enciende como un precio (texto e indicador amarillos). */
/* Todas las pestañas a la vista (en una notebook no entran en una fila: pasan a la segunda, sin flechas). */
[data-testid="stTabs"] [role="tablist"] {{ gap: 0; border-bottom: 1px solid {FILETE}; flex-wrap: wrap;
  overflow: visible !important; }}
[data-testid="stTabsScrollLeft"], [data-testid="stTabsScrollRight"] {{ display: none !important; }}
[data-testid="stTab"] {{ padding: 0.5rem 0.42rem 0.55rem !important; border-radius: 3px 3px 0 0; color: {TEXTO_2};
  transition: color 160ms cubic-bezier(.16,1,.3,1), background-color 160ms cubic-bezier(.16,1,.3,1); }}
[data-testid="stTab"] p {{ font-size: 0.9rem; font-weight: 600; letter-spacing: 0.01em;
  font-variation-settings: "wdth" 74; }}
/* En el celular, una sola fila que se desliza de costado. */
@media (max-width: 760px) {{
  [data-testid="stTabs"] [role="tablist"] {{ flex-wrap: nowrap; overflow-x: auto !important; scrollbar-width: none; }}
  [data-testid="stTab"] {{ flex: none; }}
}}
[data-testid="stTab"] p span[role="img"] {{ font-variation-settings: "FILL" 0, "wght" 300; font-size: 1.1rem;
  margin-right: 0.15rem; }}
[data-testid="stTab"]:hover {{ color: {TEXTO}; background: {PANEL}; }}
/* La pestaña activa se enciende como un precio: una ranura amarilla con la letra oscura. */
[data-testid="stTab"][aria-selected="true"] {{ color: {SOBRE_AMARILLO} !important; background: {a}; }}
[data-testid="stTab"][aria-selected="true"] p {{ font-weight: 800; color: {SOBRE_AMARILLO}; }}
[data-testid="stTab"] .react-aria-SelectionIndicator {{ background: {a}; }}

/* Íconos de línea finos (Material Symbols de Streamlit, contorno). */
[data-testid="stIconMaterial"] {{ font-variation-settings: "FILL" 0, "wght" 300, "GRAD" 0, "opsz" 24; }}

/* Las cifras del tótem: condensadas, pesadas, tabulares, con su filete amarillo; sin tarjeta. */
[data-testid="stMetric"] {{ background: transparent !important; border: 0 !important; border-radius: 0 !important;
  box-shadow: none !important; border-top: 1px solid {rgba(AMARILLO, 0.55)} !important;
  padding: 0.7rem 0 0.2rem !important; }}
[data-testid="stMetricLabel"] p {{ font-size: 0.74rem !important; font-weight: 600; letter-spacing: 0.07em;
  text-transform: uppercase; color: {TEXTO_2}; }}
[data-testid="stMetricValue"] {{ font-variation-settings: "wdth" {ANCHO_TOTEM}; font-weight: 750;
  font-size: clamp(2.2rem, 3.4vw, 3.2rem) !important; line-height: 1.02; letter-spacing: -0.005em; color: {TEXTO}; }}
.tot-cifra {{ border-top: 1px solid {rgba(AMARILLO, 0.55)}; padding: 0.7rem 0 0.15rem; }}
.tot-cifra-rotulo {{ font-size: 0.74rem; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase;
  color: {TEXTO_2}; margin-bottom: 0.35rem; }}
.tot-cifra-valor {{ font-variation-settings: "wdth" {ANCHO_TOTEM}; font-weight: 750; color: {TEXTO};
  font-size: clamp(2.6rem, 4.2vw, 4rem); line-height: 0.98; letter-spacing: -0.01em; white-space: nowrap;
  animation: tot-enciende 520ms cubic-bezier(.16,1,.3,1) both; }}
.tot-cifra-valor.tot-texto {{ font-size: clamp(1.9rem, 2.8vw, 2.7rem); white-space: normal; }}
.tot-cifra-rotulo {{ position: relative; }}
.tot-cifra-rotulo abbr {{ text-decoration: underline dotted {TEXTO_3}; text-underline-offset: 3px; cursor: help; }}
.tot-cifra-rotulo abbr:hover::after, .tot-cifra-rotulo abbr:focus::after {{ content: attr(data-ayuda);
  position: absolute; left: 0; top: calc(100% + 6px); z-index: 20; width: max-content; max-width: 32ch;
  background: {PANEL_2}; color: {TEXTO}; border: 1px solid {FILETE_FUERTE}; border-radius: 4px; padding: 0.5rem 0.65rem;
  font-size: 0.82rem; font-weight: 450; letter-spacing: 0; text-transform: none; line-height: 1.4;
  box-shadow: 0 8px 24px {rgba(NOCHE, 0.6)}; }}
.tot-cifra-debajo {{ font-size: 0.85rem; color: {TEXTO_2}; margin-top: 0.3rem; }}
.tot-cifra-valor span {{ font-size: 0.42em; font-weight: 600; color: {TEXTO_2}; margin-left: 0.18em;
  letter-spacing: 0.02em; }}
@keyframes tot-enciende {{ from {{ color: {TEXTO_2}; }} to {{ color: {TEXTO}; }} }}
[data-testid="stMetricDelta"] {{ font-size: 0.85rem; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stMetric"]) {{ border: 0 !important; }}

/* Botones: la acción principal es la luz amarilla; las otras, un filete. */
[data-testid="stBaseButton-primary"] {{ background: {a} !important; color: {SOBRE_AMARILLO} !important;
  border: 1px solid {a} !important; font-weight: 700; }}
[data-testid="stBaseButton-primary"] p {{ font-weight: 700; }}
[data-testid="stBaseButton-primary"]:hover {{ filter: brightness(1.06); }}
[data-testid="stBaseButton-primary"]:disabled {{ background: {PANEL_2} !important; color: {TEXTO_3} !important;
  border-color: {FILETE} !important; filter: none; }}
[data-testid="stBaseButton-secondary"] {{ background: {PANEL} !important; border: 1px solid {FILETE_FUERTE} !important;
  color: {TEXTO} !important; }}
[data-testid="stBaseButton-secondary"]:hover {{ border-color: {a} !important; color: {a} !important; }}
[data-testid="stBaseButton-secondary"]:disabled {{ color: {TEXTO_3} !important; border-color: {FILETE} !important; }}
[data-testid="stDownloadButton"] button {{ background: {PANEL} !important; border: 1px solid {FILETE_FUERTE} !important; }}

/* Avisos: un panel callado con filete de 1 px; el ícono lleva el color del estado. */
[data-testid="stAlertContainer"] {{ background: {PANEL} !important; border: 1px solid {FILETE} !important;
  border-radius: 4px; color: {TEXTO} !important; }}
[data-testid="stAlertContainer"] p, [data-testid="stAlertContainer"] li {{ color: {TEXTO} !important; }}
[data-testid="stAlertContentInfo"] [data-testid="stIconMaterial"] {{ color: {AZUL}; }}
[data-testid="stAlertContentSuccess"] [data-testid="stIconMaterial"] {{ color: {VERDE_OK}; }}
[data-testid="stAlertContentWarning"] [data-testid="stIconMaterial"] {{ color: {TEXTO_2}; }}
[data-testid="stAlertContentError"] [data-testid="stIconMaterial"] {{ color: {ROJO_TEXTO}; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{ border-color: {FILETE_FUERTE} !important; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{ border-color: {rgba(ROJO, 0.6)} !important; }}

/* Desplegables, tablas y controles: paneles apenas más claros que la noche. */
[data-testid="stExpander"] details {{ background: {PANEL}; border: 1px solid {FILETE}; border-radius: 4px; }}
[data-testid="stExpander"] summary {{ color: {TEXTO}; }}
[data-testid="stExpander"] summary:hover {{ color: {a}; }}
[data-testid="stExpander"] summary p {{ font-weight: 600; }}
[data-testid="stDataFrame"], [data-testid="stTable"] {{ border: 1px solid {FILETE}; border-radius: 4px; }}
[data-testid="stTable"] th {{ color: {TEXTO_2}; font-weight: 600; }}
[data-baseweb="select"] > div, [data-baseweb="input"], [data-testid="stNumberInputContainer"] {{ background: {PANEL_2}; }}
[data-baseweb="popover"] ul {{ background: {PANEL_2}; }}
[data-testid="stSlider"] [role="slider"] {{ box-shadow: none; }}

/* Ayuda "?": el cartel no atrapa el mouse (si no, al cruzarlo quedaba abierto). */
[data-testid="stTooltipContent"] {{ pointer-events: none !important; }}
/* El iframe invisible que instala el arreglo de la ayuda no ocupa lugar. */
[data-testid="stElementContainer"]:has(iframe[srcdoc*='__ayudasInstaladas']) {{ display: none; }}

/* Insignias de los datos (§8.4): texto con un punto del color del tipo. */
.insignia {{ display: inline-flex; align-items: center; gap: 6px; border: 1px solid {FILETE_FUERTE};
  border-radius: 999px; padding: 1px 9px; font-size: 0.78rem; font-weight: 600; margin-left: 6px;
  vertical-align: middle; color: {TEXTO}; }}
.insignia::before {{ content: ""; width: 7px; height: 7px; border-radius: 50%; background: {GRIS}; }}
.insignia-dato::before {{ background: {VERDE_OK}; }}
.insignia-estimacion::before {{ background: {a}; }}
.insignia-observacion::before {{ background: {AZUL}; }}
.insignia-supuesto::before {{ background: {NARANJA}; }}

@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
</style>"""


# =============================================================================
# Paleta para los tableros en JavaScript (animación y seguimiento del camión)
# =============================================================================
def paleta_json() -> dict:
    """Colores que reciben por JSON los tableros dibujados en el navegador (ningún hex en `ui/animacion.py`)."""
    return {
        "fondo": NOCHE,
        "panel": PANEL,
        "panel2": PANEL_2,
        "borde": FILETE,
        "bordeFuerte": FILETE_FUERTE,
        "tinta": TEXTO,
        "tenue": TEXTO_2,
        "tenue3": TEXTO_3,
        "asfalto": ASFALTO,
        "asfalto2": ASFALTO_2,
        "linea": AMARILLO,
        "amarillo": AMARILLO,
        "amarilloSuave": AMARILLO_SUAVE,
        "sobreAmarillo": SOBRE_AMARILLO,
        "rojo": ROJO,
        "rojoTexto": ROJO_TEXTO,
        "azul": AZUL,
        "libre": VERDE_OK,
        "naranja": NARANJA,
        "arbol": ARBOL,
        "arbol2": ARBOL_2,
        "faros": FARO,
        "neumatico": NEUMATICO,
        "vidrio": VIDRIO,
        "plata": PLATA,
        "negro": NOCHE,
        "blanco": TEXTO,
        "producto": COLOR_PRODUCTO,
    }


#: El tablero de la animación usaba una paleta oscura aparte; ahora es la misma de toda la app.
paleta_oscura_json = paleta_json
