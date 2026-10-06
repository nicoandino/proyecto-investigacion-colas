"""Gráficos de las estaciones del año y de la comparación de escenarios (Fase 7).

Todos los colores salen de `ui/tema.py` (control N15). Cada barra lleva su valor escrito y las
barras de error son el IC 95 % de las réplicas (o, en las diferencias, de las diferencias
réplica a réplica con números aleatorios comunes).
"""

from __future__ import annotations

import plotly.graph_objects as go

from sim.escenarios import diferencia_pareada, es_significativa
from sim.runner import ResultadoEscenario
from ui.tema import (
    AMARILLO,
    AZUL,
    GRIS,
    LIBRE,
    NARANJA,
    ROJO,
    TINTA_TENUE,
    plantilla_plotly,
)

_LAYOUT = dict(
    template=plantilla_plotly(),
    margin=dict(l=60, r=20, t=60, b=50),
    height=380,
    font=dict(size=13),
    separators=",.",
)

#: Motivos de pérdida de la taxonomía fija (§7.6) con su campo de `ResultadoReplica`.
MOTIVOS = (
    ("perdidos_cola_dia", "Abandonó la espera", GRIS),
    ("perdidos_cola_llena_dia", "Cola llena", AZUL),
    ("perdidos_sin_combustible_dia", "Sin combustible", ROJO),
    ("perdidos_corte_gnc_dia", "Corte de GNC", NARANJA),
)


def grafico_barras_ic(
    resultados: list[ResultadoEscenario],
    clave: str,
    titulo: str,
    unidad: str,
    decimales: int = 1,
    escala: float = 1.0,
) -> go.Figure:
    """Una barra por escenario (o estación) con su promedio y el IC 95 % como barra de error."""
    etiquetas = [r.escenario.nombre for r in resultados]
    valores = [r.resumen[clave].promedio * escala for r in resultados]
    errores = [r.resumen[clave].semiamplitud * escala for r in resultados]
    fig = go.Figure(
        go.Bar(
            x=etiquetas,
            y=valores,
            error_y=dict(type="data", array=errores, color=TINTA_TENUE, thickness=1.5),
            marker_color=AMARILLO,
            marker_line=dict(color=TINTA_TENUE, width=1),
            text=[f"{v:,.{decimales}f}" for v in valores],
            textposition="outside",
            hovertemplate="%{x}: %{y:,." + str(decimales) + "f} " + unidad + "<extra></extra>",
        )
    )
    fig.update_layout(title=titulo, yaxis_title=unidad, **_LAYOUT)
    fig.update_yaxes(rangemode="tozero")
    return fig


def grafico_perdidos_por_motivo(
    resultados: list[ResultadoEscenario], titulo: str | None = None, horizontal: bool = False
) -> go.Figure:
    """Clientes que se van por día, apilados por motivo (la taxonomía fija de §7.6)."""
    etiquetas = [r.escenario.nombre for r in resultados]
    fig = go.Figure()
    for campo, nombre, color in MOTIVOS:
        valores = [r.resumen[campo].promedio for r in resultados]
        eje = dict(y=etiquetas, x=valores, orientation="h") if horizontal else dict(x=etiquetas, y=valores)
        fig.add_bar(
            **eje,
            name=nombre,
            marker_color=color,
            text=[f"{v:,.1f}" if v >= 0.5 else "" for v in valores],
            textposition="inside",
            hovertemplate=nombre + ": %{" + ("x" if horizontal else "y") + ":,.2f} clientes por día<extra></extra>",
        )
    fig.update_layout(
        title=titulo or "Clientes que se van sin cargar, por día y por motivo",
        barmode="stack",
        **{**_LAYOUT, "legend": dict(orientation="h", y=-0.25 if not horizontal else -0.12),
           **({"height": max(380, 70 + 32 * len(etiquetas))} if horizontal else {})},
    )
    if horizontal:
        fig.update_xaxes(title="Clientes por día")
        fig.update_yaxes(autorange="reversed")
    else:
        fig.update_yaxes(title="Clientes por día")
    return fig


def grafico_diferencias(
    base: ResultadoEscenario,
    resultados: list[ResultadoEscenario],
    clave: str,
    etiqueta: str,
    unidad: str,
    mejor_bajo: bool,
    decimales: int = 2,
    escala: float = 1.0,
) -> go.Figure:
    """Diferencia contra S0 de cada escenario, con el IC 95 % de la diferencia pareada.

    Verde = mejora significativa, rojo = empeora significativamente, gris = no se distingue
    del azar (el IC contiene el 0). Cada barra lleva su valor escrito.
    """
    nombres: list[str] = []
    valores: list[float] = []
    errores: list[float] = []
    colores: list[str] = []
    rotulos: list[str] = []
    for r in resultados:
        if r is base:
            continue
        d = diferencia_pareada(base, r, clave)
        prom, err = d.promedio * escala, d.semiamplitud * escala
        nombres.append(r.escenario.nombre)
        valores.append(prom)
        errores.append(err)
        if not es_significativa(d):
            colores.append(GRIS)
            rotulos.append(f"{prom:+,.{decimales}f} (azar)")
        else:
            mejora = (prom < 0) == mejor_bajo
            colores.append(LIBRE if mejora else ROJO)
            rotulos.append(f"{prom:+,.{decimales}f} ({'mejora' if mejora else 'empeora'})")
    fig = go.Figure(
        go.Bar(
            y=[f"{n}<br><sub>{r}</sub>" for n, r in zip(nombres, rotulos)],
            x=valores,
            orientation="h",
            error_x=dict(type="data", array=errores, color=TINTA_TENUE, thickness=1.5),
            marker_color=colores,

            hovertemplate="%{y}: %{x:+,." + str(decimales) + "f} " + unidad + "<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"{etiqueta}: diferencia contra S0 (promedio ± IC 95 % de la diferencia)",
        xaxis_title=f"{unidad} respecto de S0",
        **{**_LAYOUT, "height": max(360, 80 + 44 * len(nombres)), "margin": dict(l=60, r=30, t=60, b=50)},
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def grafico_litros_por_mes(
    litros_por_dia: list[float], meses: tuple[str, ...], destacados: set[int], titulo: str
) -> go.Figure:
    """Litros por día esperados de cada mes (con la estacionalidad elegida y el calendario real).

    Los meses representativos de las 4 estaciones van en amarillo; los demás, en gris.
    """
    colores = [AMARILLO if m + 1 in destacados else GRIS for m in range(12)]
    fig = go.Figure(
        go.Bar(
            x=[m[:3].capitalize() for m in meses],
            y=litros_por_dia,
            marker_color=colores,
            marker_line=dict(color=TINTA_TENUE, width=1),
            text=[f"{v:,.0f}" for v in litros_por_dia],
            textposition="outside",
            hovertemplate="%{x}: %{y:,.0f} L por día<extra></extra>",
        )
    )
    fig.update_layout(title=titulo, yaxis_title="Litros por día", **_LAYOUT)
    fig.update_yaxes(rangemode="tozero")
    return fig


def _millones(valor: float) -> str:
    """Pesos en millones con coma decimal y el signo antes del $: -$1,50 M."""
    signo = "-" if valor < 0 else ""
    return f"{signo}${abs(valor) / 1e6:,.2f} M".replace(",", "X").replace(".", ",").replace("X", ".")


def grafico_cascada_economica(
    ingresos: list[tuple[str, float]], costos: list[tuple[str, float]], titulo: str
) -> go.Figure:
    """Cascada del mes: ingresos (suben) → costos (bajan) → margen operativo."""
    nombres = [n for n, _ in ingresos] + ["Ingresos"] + [n for n, _ in costos] + ["Margen operativo"]
    valores = [v for _, v in ingresos] + [0.0] + [-v for _, v in costos] + [0.0]
    medidas = (
        ["relative"] * len(ingresos) + ["total"] + ["relative"] * len(costos) + ["total"]
    )
    fig = go.Figure(
        go.Waterfall(
            x=nombres,
            y=valores,
            measure=medidas,
            text=[
                _millones(v) if m == "relative" else ""
                for v, m in zip(valores, medidas)
            ],
            textposition="outside",
            increasing=dict(marker=dict(color=LIBRE)),
            decreasing=dict(marker=dict(color=NARANJA)),
            totals=dict(marker=dict(color=AMARILLO, line=dict(color=TINTA_TENUE, width=1))),
            connector=dict(line=dict(color=TINTA_TENUE, width=1)),
            hovertemplate="%{x}: %{y:,.0f} $<extra></extra>",
        )
    )
    fig.update_layout(title=titulo, yaxis_title="Pesos por mes", showlegend=False, **_LAYOUT)
    fig.add_hline(y=0, line_color=TINTA_TENUE, line_width=1)
    return fig


def grafico_delta_margen(conclusiones, titulo: str) -> go.Figure:
    """Δ del margen operativo mensual de cada escenario contra S0, con el IC 95 % de la diferencia.

    Verde = suma margen significativamente, rojo = resta, gris = no se distingue del azar.
    """
    nombres, valores, errores, colores, rotulos = [], [], [], [], []
    for c in conclusiones:
        d = c.d_margen
        nombres.append(c.nombre)
        valores.append(d.promedio / 1e6)
        errores.append(d.semiamplitud / 1e6)
        if not c.significativa:
            colores.append(GRIS)
            rotulos.append(f"{d.promedio / 1e6:+,.2f} M (azar)")
        elif d.promedio > 0:
            colores.append(LIBRE)
            rotulos.append(f"{d.promedio / 1e6:+,.2f} M (suma)")
        else:
            colores.append(ROJO)
            rotulos.append(f"{d.promedio / 1e6:+,.2f} M (resta)")
    fig = go.Figure(
        go.Bar(
            y=[f"{n}<br><sub>{r}</sub>" for n, r in zip(nombres, rotulos)],
            x=valores,
            orientation="h",
            error_x=dict(type="data", array=errores, color=TINTA_TENUE, thickness=1.5),
            marker_color=colores,
            hovertemplate="%{x:+,.2f} millones de $ por mes<extra></extra>",
        )
    )
    fig.update_layout(
        title=titulo,
        xaxis_title="Millones de $ por mes respecto de S0",
        **{**_LAYOUT, "height": max(360, 80 + 44 * len(nombres)), "margin": dict(l=60, r=30, t=60, b=50)},
    )
    fig.update_yaxes(autorange="reversed")
    return fig
