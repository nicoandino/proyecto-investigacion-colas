"""Gráficos de la red de abastecimiento (Fase 5): el mapa de rutas y el plazo con cortes.

Todos los colores salen de `ui/tema.py` (control N15).
"""

from __future__ import annotations

import plotly.graph_objects as go

from sim.config import ParametrosRed
from sim.red import NOMBRE_NODO, arcos_de_la_ruta, camino_mas_corto
from ui.tema import (
    AMARILLO,
    AZUL,
    FONDO,
    GRIS,
    ROJO,
    TINTA_AZULADA,
    plantilla_plotly,
    rgba,
)

#: Posiciones (longitud, latitud) APROXIMADAS de los nodos: sólo sirven para dibujar.
#: Dock Sud está a ≈ 900 km al este (fuera de escala), así que se lo dibuja al borde.
_POSICION_NODO = {
    "LUJAN": (-68.88, -33.03),
    "PAREDITAS": (-69.10, -33.85),
    "SOSNEADO": (-69.60, -35.10),
    "SANRAFAEL": (-68.33, -34.62),
    "ALVEAR": (-67.69, -34.98),
    "MONTECOMAN": (-67.90, -34.60),
    "LAPAZ": (-67.55, -33.46),
    "DOCK": (-65.9, -35.45),
    "ARROYO": (-65.9, -33.6),
}

#: Dónde va el rótulo de cada nodo (San Rafael y Monte Comán están pegados).
_POSICION_TEXTO = {
    "LUJAN": "top center",
    "PAREDITAS": "top left",
    "SOSNEADO": "bottom center",
    "SANRAFAEL": "bottom left",
    "ALVEAR": "bottom center",
    "MONTECOMAN": "top right",
    "LAPAZ": "top center",
    "DOCK": "bottom center",
    "ARROYO": "top center",
}

_LAYOUT = dict(
    template=plantilla_plotly(),
    margin=dict(l=60, r=20, t=50, b=50),
    height=380,
    font=dict(size=13),
    separators=",.",
)


def _km(valor: float) -> str:
    """Kilómetros con coma decimal y punto de miles: 1.056,5."""
    return f"{valor:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def grafico_red(
    red: ParametrosRed, cerrados: tuple[tuple[str, str], ...] = ()
) -> go.Figure:
    """La red de rutas: la ruta óptima (gruesa, amarilla), los arcos cortados (rojo,
    tachados) y, si el corte está en la ruta, el desvío (azul)."""
    cierres = frozenset(frozenset(par) for par in cerrados)
    optimo = camino_mas_corto(red)
    en_ruta = arcos_de_la_ruta(optimo.ruta)
    afecta = bool(cierres & en_ruta)
    desvio = camino_mas_corto(red, cerrados=cerrados) if afecta else None
    en_desvio = arcos_de_la_ruta(desvio.ruta) if desvio and desvio.ruta else frozenset()

    fig = go.Figure()
    for arco in red.arcos:
        clave = frozenset((arco.a, arco.b))
        x = [_POSICION_NODO[arco.a][0], _POSICION_NODO[arco.b][0]]
        y = [_POSICION_NODO[arco.a][1], _POSICION_NODO[arco.b][1]]
        cortado = clave in cierres
        if cortado:
            color, ancho, trazo = ROJO, 4, "dash"
        elif clave in en_desvio:
            color, ancho, trazo = AZUL, 6, "solid"
        elif clave in en_ruta and not afecta:
            color, ancho, trazo = AMARILLO, 8, "solid"
        else:
            color, ancho, trazo = GRIS, 2, "solid"
        if color == AMARILLO:
            # Contorno oscuro bajo el amarillo: solo no se ve sobre fondo blanco.
            fig.add_trace(
                go.Scatter(x=x, y=y, mode="lines", hoverinfo="skip", showlegend=False,
                           line=dict(color=TINTA_AZULADA, width=ancho + 4))
            )
        fig.add_trace(
            go.Scatter(
                x=x, y=y, mode="lines", showlegend=False, hoverinfo="text",
                text=f"{NOMBRE_NODO[arco.a]} – {NOMBRE_NODO[arco.b]}<br>{arco.ruta} · "
                     f"{_km(arco.km)} km{' · CORTADO' if cortado else ''}",
                line=dict(color=color, width=ancho, dash=trazo),
            )
        )
        fig.add_annotation(
            x=sum(x) / 2, y=sum(y) / 2,
            text=("✕ CORTADO<br>" if cortado else "") + f"{arco.ruta} · {_km(arco.km)} km",
            showarrow=False, font=dict(size=11, color=ROJO if cortado else TINTA_AZULADA),
            bgcolor=rgba(FONDO, 0.85),
        )
    for nodo, (x, y) in _POSICION_NODO.items():
        es_origen, es_destino = nodo == red.origen, nodo == red.destino
        fig.add_trace(
            go.Scatter(
                x=[x], y=[y], mode="markers+text", showlegend=False, hoverinfo="skip",
                text=[NOMBRE_NODO[nodo]], textposition=_POSICION_TEXTO[nodo],
                textfont=dict(size=12, color=TINTA_AZULADA),
                marker=dict(
                    size=17 if (es_origen or es_destino) else 11,
                    color=ROJO if es_destino else (TINTA_AZULADA if es_origen else GRIS),
                    line=dict(width=2, color=TINTA_AZULADA),
                ),
            )
        )
    fig.update_layout(
        title="Red de abastecimiento (posiciones aproximadas; Dock Sud y Arroyo Seco están a ≈ 800–900 km, fuera de escala)",
        xaxis=dict(visible=False, range=[-70.4, -65.4]),
        yaxis=dict(visible=False, range=[-35.8, -32.6]),
        **{**_LAYOUT, "hovermode": "closest", "height": 600,
           "margin": dict(l=10, r=10, t=50, b=10)},
    )
    return fig


def grafico_plazos(sin_corte: list[float], con_corte: list[float], etiqueta: str) -> go.Figure:
    """Histograma del plazo de entrega con y sin el corte (mismos plazos base)."""
    fig = go.Figure()
    fig.add_histogram(x=sin_corte, name="Sin cortes", marker_color=GRIS, opacity=0.75,
                      xbins=dict(size=2))
    fig.add_histogram(x=con_corte, name=etiqueta, marker_color=ROJO, opacity=0.6,
                      xbins=dict(size=2))
    fig.update_layout(
        title="Plazo de entrega del camión, con y sin cortes",
        xaxis_title="Horas desde el pedido hasta la descarga",
        yaxis_title="Viajes",
        barmode="overlay",
        **{**_LAYOUT, "hovermode": "x"},
    )
    return fig
