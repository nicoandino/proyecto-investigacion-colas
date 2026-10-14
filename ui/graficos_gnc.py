"""Gráfico del GNC día por día, con los episodios de corte sombreados (Fase 6).

Todos los colores salen de `ui/tema.py` (control N15).
"""

from __future__ import annotations

from datetime import date, timedelta

import plotly.graph_objects as go

from sim.config import ANO_REFERENCIA, ParametrosSimulacion
from sim.traza import Traza
from ui.tema import COLOR_PRODUCTO, NARANJA, ROJO, plantilla_plotly, rgba

_LAYOUT = dict(
    template=plantilla_plotly(),
    margin=dict(l=60, r=20, t=50, b=50),
    height=420,
    font=dict(size=13),
    separators=",.",
)


def grafico_gnc_dias(traza: Traza, p: ParametrosSimulacion) -> go.Figure:
    """Clientes de GNC por día: atendidos, pasados a Súper y perdidos por el corte.

    Las franjas rojas son los días con corte (con su cantidad de horas en el rótulo).
    """
    inicio = date(ANO_REFERENCIA, *p.fecha_inicio)
    dias = [d for d in traza.dias]
    fechas = [(inicio + timedelta(days=d.dia - 1)).isoformat() for d in dias]

    fig = go.Figure()
    fig.add_bar(
        x=fechas, y=[d.gnc_atendidos for d in dias], name="Cargaron GNC",
        marker_color=COLOR_PRODUCTO["gnc"],
        hovertemplate="%{x}: %{y} clientes cargaron GNC<extra></extra>",
    )
    fig.add_bar(
        x=fechas, y=[d.gnc_migrados for d in dias], name="Pasaron a Súper",
        marker_color=NARANJA,
        hovertemplate="%{x}: %{y} pasaron a nafta<extra></extra>",
    )
    fig.add_bar(
        x=fechas, y=[d.gnc_perdidos for d in dias], name="Se perdieron por el corte",
        marker_color=ROJO,
        hovertemplate="%{x}: %{y} se fueron sin cargar<extra></extra>",
    )
    # Franjas de corte: tramos seguidos de días con minutos de corte
    tramo: list[int] = []
    for k, d in enumerate(dias + [None]):
        if d is not None and d.gnc_corte_min > 0:
            tramo.append(k)
            continue
        if tramo:
            horas = sum(dias[j].gnc_corte_min for j in tramo) / 60.0
            fig.add_vrect(
                x0=(inicio + timedelta(days=dias[tramo[0]].dia - 1.5)).isoformat(),
                x1=(inicio + timedelta(days=dias[tramo[-1]].dia - 0.5)).isoformat(),
                fillcolor=rgba(ROJO, 0.12), line_width=0,
                annotation_text=f"corte de GNC ({horas:.0f} h)",
                annotation_position="top left", annotation_font_size=12,
            )
            tramo = []
    fig.update_layout(
        title="Clientes de GNC por día (las franjas rojas son los episodios de corte)",
        xaxis_title="Fecha",
        yaxis_title="Clientes por día",
        barmode="stack",
        hovermode="x unified",
        **_LAYOUT,
    )
    return fig
