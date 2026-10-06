"""Tema Shell — única fuente de la paleta y del estilo (ORQUESTADOR §8.1).

Reglas obligatorias:
  1. Amarillo = fondo/relleno/acento, NUNCA texto sobre blanco (contraste ≈ 1,6:1).
     El texto sobre amarillo va en `TINTA`.
  2. El rojo de marca también es el rojo de "pérdida": toda pérdida lleva rótulo.
  3. Un solo tema claro.
  4. `plantilla_plotly()` reemplaza a `plotly_white` y a los hex sueltos de los gráficos.
  5. `[theme]` en `.streamlit/config.toml` (conservar `fileWatcherType = "poll"`).
  6. `css_global()` inyecta el CSS mínimo; `paleta_json()` alimenta el SVG de la animación.

PROHIBIDO repetir un hex fuera de este archivo (control N15).
"""

from __future__ import annotations

import plotly.graph_objects as go

# --- Marca (los hex difieren entre fuentes: default #FBCE07 / #DD1D21, N4) ---
AMARILLO = "#FBCE07"
ROJO = "#DD1D21"
AMARILLO_SUAVE = "#FFF6C2"

# --- Superficies y texto ------------------------------------------------------
TINTA = "#1A1A1A"
TINTA_TENUE = "#5B5B5B"
FONDO = "#FFFFFF"
FONDO_PANEL = "#F6F4EC"
BORDE = "#E2DED0"
ASFALTO = "#2B2F36"          # sólo dentro de la animación

# --- Estados (SIEMPRE con texto, no sólo color) -------------------------------
LIBRE = "#1E9E5A"
OCUPADO = AMARILLO
PERDIDO = ROJO

# --- Productos (5 colores distinguibles, N15) ---------------------------------
PRODUCTO = {
    "super": AMARILLO,
    "vpower": ROJO,
    "diesel": "#4B5563",
    "vpower_diesel": "#0F766E",
    "gnc": "#1D6FB8",
}

# --- Categorías de los gráficos (un color por significado) ---------------------
ESCENARIO = {"Base": "#64748B", "A": "#1D6FB8", "B": "#A855F7", "C": "#0F766E"}
AZUL = "#3B82F6"              # caja del minimarket y barras de demanda
CELESTE = "#0EA5E9"           # nivel del tanque
VERDE_OK = "#16A34A"
VERDE_INGRESO = "#22C55E"
NARANJA = "#FB923C"
GRIS = "#94A3B8"
INDIGO = "#6366F1"            # flete en los costos por política
TINTA_AZULADA = "#334155"     # ejes y líneas de referencia

# --- Detalles del dibujo de la animación (autos, surtidores, personas) ----------
FARO = "#FDE68A"
NEUMATICO = "#111827"
VIDRIO = "#0F172A"
PLATA = "#CBD5E1"

#: Color de cada producto (id del motor → color de `PRODUCTO`). El mismo color pinta
#: el auto en la animación, el surtidor y el tanque.
COLOR_PRODUCTO = {
    "super": PRODUCTO["super"],
    "vpower": PRODUCTO["vpower"],
    "diesel_g2": PRODUCTO["diesel"],
    "diesel_g3": PRODUCTO["vpower_diesel"],
    "gnc": PRODUCTO["gnc"],
}

# --- Tablero oscuro de la animación (rediseño v3) ------------------------------------------
OSC_FONDO = "#0A1220"
OSC_PANEL = "#111D33"
OSC_PANEL_2 = "#17263F"
OSC_BORDE = "#2A3F63"
OSC_TEXTO = "#EAF0F8"
OSC_TENUE = "#9DB0CC"
OSC_ASFALTO = "#2C313C"
OSC_ASFALTO_2 = "#383E4B"
OSC_ARBOL = "#1E5B34"
OSC_ARBOL_2 = "#2A7345"
OSC_VERDE = "#34D399"
OSC_TURQUESA = "#2DD4BF"

#: Color de cada producto sobre fondo oscuro (el diésel gris y el turquesa oscuro no se ven).
COLOR_PRODUCTO_OSCURO = {
    "super": AMARILLO,
    "vpower": ROJO,
    "diesel_g2": GRIS,
    "diesel_g3": OSC_TURQUESA,
    "gnc": AZUL,
}

#: Pares declarados para el control de contraste (WCAG ≥ 4,5:1, §10.3/N15).
PARES_CONTRASTE = (
    ("TINTA/AMARILLO", TINTA, AMARILLO),
    ("TINTA/FONDO", TINTA, FONDO),
    ("TINTA/FONDO_PANEL", TINTA, FONDO_PANEL),
    ("AMARILLO/ASFALTO", AMARILLO, ASFALTO),
    ("FONDO/ROJO", FONDO, ROJO),
    ("OSC_TEXTO/OSC_PANEL", OSC_TEXTO, OSC_PANEL),
    ("OSC_TENUE/OSC_PANEL", OSC_TENUE, OSC_PANEL),
    ("OSC_TEXTO/OSC_FONDO", OSC_TEXTO, OSC_FONDO),
    ("AMARILLO/OSC_PANEL", AMARILLO, OSC_PANEL),
    ("OSC_VERDE/OSC_PANEL", OSC_VERDE, OSC_PANEL),
)


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
# Plotly: una plantilla propia en lugar de `plotly_white`
# =============================================================================
def plantilla_plotly() -> go.layout.Template:
    """Template de Plotly con la paleta del tema (reemplaza a `plotly_white`)."""
    ejes = dict(
        gridcolor=BORDE,
        zerolinecolor=BORDE,
        linecolor=BORDE,
        title_font=dict(color=TINTA_TENUE, size=13),
        tickfont=dict(color=TINTA),
    )
    return go.layout.Template(
        layout=dict(
            colorway=[AMARILLO, ROJO, PRODUCTO["diesel"], PRODUCTO["vpower_diesel"],
                      PRODUCTO["gnc"], TINTA_TENUE],
            font=dict(color=TINTA, size=13),
            paper_bgcolor=FONDO,
            plot_bgcolor=FONDO,
            title=dict(font=dict(color=TINTA, size=16)),
            legend=dict(font=dict(color=TINTA)),
            xaxis=dict(ejes),
            yaxis=dict(ejes),
            hoverlabel=dict(bgcolor=FONDO_PANEL, font=dict(color=TINTA)),
        )
    )


# =============================================================================
# CSS global mínimo (franja amarilla con filete rojo, insignias)
# =============================================================================
def css_global() -> str:
    """CSS inyectado con `st.markdown(..., unsafe_allow_html=True)`."""
    return (
        "<style>"
        # Franja Shell superior: amarillo con filete rojo (sin logo).
        f"[data-testid='stAppViewContainer'] {{ border-top: 6px solid {AMARILLO}; }}"
        f"[data-testid='stAppViewContainer'] {{ box-shadow: inset 0 -2px 0 {ROJO}; }}"
        f"[data-testid='stHeader'] {{ background: {FONDO}; }}"
        f"[data-testid='stSidebar'] {{ background: {FONDO_PANEL}; }}"
        # Insignias de los datos (§8.4)
        ".insignia { display: inline-block; border-radius: 8px; padding: 1px 8px; "
        "font-size: 0.78rem; font-weight: 600; margin-left: 6px; vertical-align: middle; }"
        f".insignia-dato {{ background: {rgba(LIBRE, 0.15)}; color: {LIBRE}; }}"
        f".insignia-estimacion {{ background: {rgba(AMARILLO, 0.25)}; color: {TINTA}; }}"
        f".insignia-observacion {{ background: {rgba(PRODUCTO['gnc'], 0.15)}; "
        f"color: {PRODUCTO['gnc']}; }}"
        f".insignia-supuesto {{ background: {rgba(NARANJA, 0.2)}; color: #9A3412; }}"
        f".insignia-heredado {{ background: {rgba(GRIS, 0.25)}; color: {TINTA_TENUE}; }}"
        "</style>"
    )


# =============================================================================
# Paleta para el SVG de la animación (§8.1-6)
# =============================================================================
def paleta_json() -> dict:
    """Colores que la animación recibe por JSON (ningún hex en `ui/animacion.py`)."""
    return {
        "fondo": FONDO,
        "panel": FONDO_PANEL,
        "borde": BORDE,
        "tinta": TINTA,
        "tenue": TINTA_TENUE,
        "asfalto": ASFALTO,
        "linea": FONDO,                 # marcas viales sobre el asfalto
        "amarillo": AMARILLO,
        "amarilloSuave": AMARILLO_SUAVE,
        "rojo": ROJO,
        "libre": LIBRE,
        "naranja": NARANJA,
        "producto": COLOR_PRODUCTO,
        "faros": FARO,
        "neumatico": NEUMATICO,
        "vidrio": VIDRIO,
        "plata": PLATA,
    }


def paleta_oscura_json() -> dict:
    """Colores del tablero oscuro de la animación (ningún hex en `ui/animacion.py`)."""
    return {
        "fondo": OSC_FONDO,
        "panel": OSC_PANEL,
        "panel2": OSC_PANEL_2,
        "borde": OSC_BORDE,
        "tinta": OSC_TEXTO,
        "tenue": OSC_TENUE,
        "asfalto": OSC_ASFALTO,
        "asfalto2": OSC_ASFALTO_2,
        "linea": AMARILLO,
        "amarillo": AMARILLO,
        "rojo": ROJO,
        "azul": AZUL,
        "libre": OSC_VERDE,
        "naranja": NARANJA,
        "arbol": OSC_ARBOL,
        "arbol2": OSC_ARBOL_2,
        "faros": FARO,
        "neumatico": NEUMATICO,
        "vidrio": VIDRIO,
        "plata": PLATA,
        "negro": OSC_FONDO,
        "blanco": FONDO,
        "producto": COLOR_PRODUCTO_OSCURO,
    }
