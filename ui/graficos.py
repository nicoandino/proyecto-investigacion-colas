"""Gráficos de la interfaz, armados con Plotly.

Todos reciben resultados del motor y devuelven una figura; no tocan Streamlit.
"""

from __future__ import annotations

import plotly.graph_objects as go

from sim.config import DemandaDiaria, ParametrosSimulacion
from sim.economia import CostoPolitica, ResultadoEconomico
from sim.runner import ResultadoEscenario
from sim.traza import Traza
from ui.textos import Metrica

# Un color por escenario, usado en todos los gráficos para que se lean juntos.
COLOR_ESCENARIO = {
    "Base": "#64748b",
    "A": "#3b82f6",
    "B": "#a855f7",
    "C": "#10b981",
}
COLOR_SURTIDOR = "#f59e0b"
COLOR_CAJA = "#3b82f6"
COLOR_TANQUE = "#0ea5e9"
VERDE = "#16a34a"
ROJO = "#dc2626"
NARANJA = "#fb923c"
GRIS = "#94a3b8"

_LAYOUT = dict(
    template="plotly_white",
    margin=dict(l=60, r=20, t=50, b=50),
    height=380,
    hovermode="x unified",
    font=dict(size=13),
)


def _layout(**cambios) -> dict:
    return {**_LAYOUT, **cambios}


# =============================================================================
# El día animado: colas y ocupación
# =============================================================================
def grafico_evolucion_colas(traza: Traza, dia: int) -> go.Figure:
    """Longitud de las dos colas a lo largo del día animado."""
    minutos, cola_s = traza.serie("cola_surtidor")
    _, cola_c = traza.serie("cola_caja")
    horas = [m / 60 for m in minutos]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=horas, y=cola_s, name="Cola de surtidores", mode="lines",
            line=dict(color=COLOR_SURTIDOR, width=2, shape="hv"),
            fill="tozeroy", fillcolor="rgba(245,158,11,0.15)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=horas, y=cola_c, name="Cola de la caja", mode="lines",
            line=dict(color=COLOR_CAJA, width=2, shape="hv"),
        )
    )
    fig.update_layout(
        title=f"Colas a lo largo del día {dia}",
        xaxis_title="Hora del día",
        yaxis_title="Clientes en cola",
        xaxis=dict(dtick=2, range=[0, 24]),
        **_layout(),
    )
    return fig


def grafico_ocupacion(traza: Traza, surtidores: int, dia: int) -> go.Figure:
    """Surtidores ocupados a lo largo del día, contra la capacidad instalada."""
    minutos, ocupados = traza.serie("surtidores_ocupados")
    horas = [m / 60 for m in minutos]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=horas, y=ocupados, name="Surtidores ocupados", mode="lines",
            line=dict(color=COLOR_SURTIDOR, width=2, shape="hv"),
            fill="tozeroy", fillcolor="rgba(245,158,11,0.2)",
        )
    )
    fig.add_hline(
        y=surtidores, line_dash="dash", line_color=ROJO,
        annotation_text=f"capacidad instalada ({surtidores})",
        annotation_position="bottom right",
    )
    fig.update_layout(
        title=f"Ocupación de los surtidores — día {dia}",
        xaxis_title="Hora del día",
        yaxis_title="Surtidores en uso",
        xaxis=dict(dtick=2, range=[0, 24]),
        yaxis=dict(dtick=1),
        **_layout(),
    )
    return fig


# =============================================================================
# Monte Carlo y demanda
# =============================================================================
def grafico_perfil_horario(traza: Traza, dias_medidos: int) -> go.Figure:
    """Dónde está realmente el pico: llegadas por hora contra espera por hora.

    Es el gráfico que justifica por qué no alcanza con mirar el promedio de 24 horas.
    """
    horas = list(range(24))
    llegadas = [traza.llegadas_por_hora[h] / max(dias_medidos, 1) for h in horas]
    esperas = traza.espera_por_hora

    fig = go.Figure()
    fig.add_bar(
        x=horas, y=llegadas, name="Autos que llegan",
        marker_color="rgba(59,130,246,0.55)",
        hovertemplate="%{x}:00 — %{y:.1f} autos<extra></extra>",
    )
    fig.add_trace(
        go.Scatter(
            x=horas, y=esperas, name="Espera promedio", mode="lines+markers",
            line=dict(color=ROJO, width=3), yaxis="y2",
            hovertemplate="%{x}:00 — %{y:.2f} min<extra></extra>",
        )
    )
    fig.update_layout(
        title="Perfil del día: cuándo llegan y cuánto esperan",
        xaxis=dict(title="Hora del día", dtick=2),
        yaxis=dict(title="Autos por hora"),
        yaxis2=dict(
            title="Espera promedio (min)", overlaying="y", side="right",
            showgrid=False, rangemode="tozero",
        ),
        legend=dict(orientation="h", y=1.12, x=0),
        **_layout(hovermode="x"),
    )
    return fig


def grafico_distribucion_demanda(demanda: DemandaDiaria, traza: Traza) -> go.Figure:
    """Compara la tabla empírica con la frecuencia que efectivamente salió al simular."""
    sorteos = [d.autos_sorteados for d in traza.dias]
    total = max(len(sorteos), 1)
    observadas = [100 * sorteos.count(v) / total for v in demanda.valores]
    teoricas = [100 * p for p in demanda.probabilidades]
    etiquetas = [str(v) for v in demanda.valores]

    fig = go.Figure()
    fig.add_bar(x=etiquetas, y=teoricas, name="Tabla observada (histórica)", marker_color=GRIS)
    fig.add_bar(x=etiquetas, y=observadas, name="Frecuencia simulada", marker_color=COLOR_CAJA)
    fig.update_layout(
        title="La simulación reproduce la tabla de frecuencias",
        xaxis_title="Autos por día",
        yaxis_title="Frecuencia (%)",
        barmode="group",
        **_layout(hovermode="x"),
    )
    return fig


def grafico_demanda_diaria(traza: Traza) -> go.Figure:
    """Día por día del mes: cuántos autos llegaron, cuántos se atendieron y qué se perdió."""
    dias = traza.dias
    numeros = [d.dia for d in dias]

    fig = go.Figure()
    fig.add_bar(
        x=numeros, y=[d.atendidos for d in dias], name="Atendidos", marker_color=VERDE
    )
    fig.add_bar(
        x=numeros, y=[d.perdidos_cola for d in dias], name="Perdidos por cola",
        marker_color=NARANJA,
    )
    fig.add_bar(
        x=numeros, y=[d.perdidos_sin_combustible for d in dias],
        name="Perdidos sin combustible", marker_color=ROJO,
    )
    fig.add_trace(
        go.Scatter(
            x=numeros, y=[d.autos_sorteados for d in dias], name="Demanda sorteada",
            mode="lines", line=dict(color="#1e293b", width=2, dash="dot"),
        )
    )
    fig.update_layout(
        title="Cada día del mes: demanda sorteada y qué pasó con ella",
        xaxis_title="Día",
        yaxis_title="Autos",
        barmode="stack",
        **_layout(hovermode="x"),
    )
    return fig


# =============================================================================
# Inventario
# =============================================================================
def grafico_tanque(traza: Traza, p: ParametrosSimulacion) -> go.Figure:
    """El clásico gráfico de dientes de sierra del nivel de inventario."""
    dias, litros = traza.serie_inventario()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dias, y=litros, name="Nivel del tanque", mode="lines",
            line=dict(color=COLOR_TANQUE, width=2),
            fill="tozeroy", fillcolor="rgba(14,165,233,0.18)",
            hovertemplate="día %{x:.1f} — %{y:,.0f} L<extra></extra>",
        )
    )
    fig.add_hline(
        y=p.tanque.punto_pedido, line_dash="dash", line_color=NARANJA,
        annotation_text=f"punto de pedido ({p.tanque.punto_pedido:,.0f} L)",
        annotation_position="top left",
    )
    fig.add_hline(
        y=p.tanque.capacidad, line_dash="dot", line_color=GRIS,
        annotation_text=f"capacidad ({p.tanque.capacidad:,.0f} L)",
        annotation_position="bottom left",
    )
    fig.add_hline(y=0, line_color=ROJO, line_width=1)
    fig.add_vrect(
        x0=0, x1=p.dias_calentamiento, fillcolor="rgba(100,116,139,0.18)", line_width=0,
        annotation_text="calentamiento", annotation_position="top left",
        annotation_font_size=11,
    )
    fig.update_layout(
        title="Nivel del tanque durante el mes",
        xaxis_title="Día",
        yaxis_title="Litros en el tanque",
        **_layout(hovermode="x", height=420),
    )
    return fig


def grafico_costos_politicas(costos: list[CostoPolitica]) -> go.Figure:
    """Costo mensual de cada política, abierto en sus tres componentes."""
    ordenados = sorted(costos, key=lambda c: c.costo_total)
    etiquetas = [c.etiqueta for c in ordenados]

    fig = go.Figure()
    fig.add_bar(
        x=etiquetas, y=[c.costo_pedidos for c in ordenados],
        name="Costo de pedido (flete)", marker_color="#6366f1",
    )
    fig.add_bar(
        x=etiquetas, y=[c.costo_almacenamiento for c in ordenados],
        name="Costo de almacenamiento", marker_color="#0ea5e9",
    )
    fig.add_bar(
        x=etiquetas, y=[c.costo_faltante for c in ordenados],
        name="Costo de faltante (venta perdida)", marker_color=ROJO,
    )
    fig.update_layout(
        title="Costo mensual por política de reposición (ordenado de menor a mayor)",
        xaxis_title="Política: punto de pedido (s) y cantidad a pedir (Q)",
        yaxis_title="Pesos por mes",
        barmode="stack",
        **_layout(hovermode="x", height=440),
    )
    fig.update_xaxes(tickangle=-35)
    return fig


def grafico_frontera_politicas(costos: list[CostoPolitica]) -> go.Figure:
    """Nivel de servicio contra costo: el compromiso que hay que elegir."""
    mejor = min(costos, key=lambda c: c.costo_total) if costos else None

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[c.nivel_servicio * 100 for c in costos],
            y=[c.costo_total for c in costos],
            mode="markers+text",
            marker=dict(
                size=13,
                color=[VERDE if c is mejor else COLOR_CAJA for c in costos],
                line=dict(width=1, color="#1e293b"),
            ),
            text=[c.etiqueta if c is mejor else "" for c in costos],
            textposition="top center",
            hovertext=[
                f"{c.etiqueta}<br>servicio {c.nivel_servicio * 100:.1f} %"
                f"<br>costo ${c.costo_total:,.0f}/mes"
                for c in costos
            ],
            hoverinfo="text",
            name="Políticas probadas",
        )
    )
    fig.update_layout(
        title="Nivel de servicio contra costo total (en verde, la mejor)",
        xaxis_title="Nivel de servicio (%)",
        yaxis_title="Costo total mensual ($)",
        showlegend=False,
        **_layout(hovermode="closest"),
    )
    return fig


# =============================================================================
# Escenarios de capacidad
# =============================================================================
def grafico_comparativo(
    resultados: list[ResultadoEscenario],
    metrica: Metrica,
) -> go.Figure:
    """Barras por escenario con la barra de error del intervalo de confianza del 95 %."""
    nombres = [r.escenario.nombre for r in resultados]
    valores = [metrica.valor_mostrado(r.resumen[metrica.clave].promedio) for r in resultados]
    errores = [
        metrica.valor_mostrado(r.resumen[metrica.clave].semiamplitud) for r in resultados
    ]

    fig = go.Figure(
        go.Bar(
            x=nombres,
            y=valores,
            marker_color=[COLOR_ESCENARIO.get(n, GRIS) for n in nombres],
            error_y=dict(type="data", array=errores, color="#334155", thickness=1.5, width=8),
            text=[f"{v:,.{metrica.decimales}f}" for v in valores],
            textposition="outside",
            hovertemplate="%{x}: %{y:,.2f}<extra></extra>",
        )
    )
    unidad = metrica.unidad_mostrada
    fig.update_layout(
        title=f"{metrica.etiqueta} por escenario (promedio ± IC 95 %)",
        xaxis_title="Escenario",
        yaxis_title=f"{metrica.etiqueta} [{unidad}]" if unidad else metrica.etiqueta,
        showlegend=False,
        **_layout(hovermode="closest"),
    )
    return fig


def grafico_atendidos_vs_perdidos(resultados: list[ResultadoEscenario]) -> go.Figure:
    """Clientes atendidos contra clientes perdidos, separando los dos motivos."""
    nombres = [r.escenario.nombre for r in resultados]

    fig = go.Figure()
    fig.add_bar(
        x=nombres, y=[r.prom("atendidos_dia") for r in resultados],
        name="Atendidos", marker_color=VERDE,
    )
    fig.add_bar(
        x=nombres, y=[r.prom("perdidos_cola_dia") for r in resultados],
        name="Perdidos por cola", marker_color=NARANJA,
    )
    fig.add_bar(
        x=nombres, y=[r.prom("perdidos_sin_combustible_dia") for r in resultados],
        name="Perdidos sin combustible", marker_color=ROJO,
    )
    fig.update_layout(
        title="Clientes por día: atendidos y perdidos, según el motivo",
        xaxis_title="Escenario",
        yaxis_title="Autos por día",
        barmode="group",
        **_layout(hovermode="x"),
    )
    return fig


def grafico_dispersion_replicas(
    resultados: list[ResultadoEscenario],
    metrica: Metrica,
) -> go.Figure:
    """Dispersión entre réplicas: el resultado es una distribución, no un número."""
    fig = go.Figure()
    for r in resultados:
        valores = [
            metrica.valor_mostrado(getattr(rep, metrica.clave)) for rep in r.replicas
        ]
        fig.add_trace(
            go.Box(
                y=valores,
                name=r.escenario.nombre,
                marker_color=COLOR_ESCENARIO.get(r.escenario.nombre, GRIS),
                boxpoints="all",
                jitter=0.5,
                pointpos=0,
            )
        )
    fig.update_layout(
        title=f"Dispersión de {metrica.etiqueta.lower()} entre réplicas",
        xaxis_title="Escenario",
        yaxis_title=metrica.etiqueta,
        showlegend=False,
        **_layout(hovermode="closest"),
    )
    return fig


# =============================================================================
# Economía
# =============================================================================
def grafico_beneficio(economia: list[ResultadoEconomico]) -> go.Figure:
    """Beneficio neto mensual de cada escenario frente al Base."""
    alternativos = [e for e in economia if not e.es_base]
    nombres = [e.nombre for e in alternativos]
    valores = [e.beneficio_neto for e in alternativos]

    fig = go.Figure(
        go.Bar(
            x=nombres,
            y=valores,
            marker_color=[VERDE if v > 0 else ROJO for v in valores],
            text=[f"${v:,.0f}" for v in valores],
            textposition="outside",
            hovertemplate="%{x}: $%{y:,.0f} por mes<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_color="#334155", line_width=1)
    fig.update_layout(
        title="Beneficio neto mensual respecto del escenario Base",
        xaxis_title="Escenario",
        yaxis_title="Pesos por mes",
        showlegend=False,
        **_layout(hovermode="closest"),
    )
    return fig


def grafico_ingresos_costos(economia: list[ResultadoEconomico]) -> go.Figure:
    """Ingreso extra contra costo incremental: por qué conviene o no conviene."""
    alternativos = [e for e in economia if not e.es_base]
    nombres = [e.nombre for e in alternativos]

    fig = go.Figure()
    fig.add_bar(
        x=nombres, y=[e.ingreso_extra for e in alternativos],
        name="Ingreso extra mensual", marker_color="#22c55e",
    )
    fig.add_bar(
        x=nombres, y=[-e.costo_capacidad for e in alternativos],
        name="Costo operativo incremental", marker_color=ROJO,
    )
    fig.add_trace(
        go.Scatter(
            x=nombres, y=[e.beneficio_neto for e in alternativos],
            name="Beneficio neto", mode="markers+text",
            marker=dict(size=13, color="#1e293b", symbol="diamond"),
            text=[f"${e.beneficio_neto:,.0f}" for e in alternativos],
            textposition="top center",
        )
    )
    fig.add_hline(y=0, line_color="#334155", line_width=1)
    fig.update_layout(
        title="De dónde sale el beneficio: ingreso extra menos costo incremental",
        xaxis_title="Escenario",
        yaxis_title="Pesos por mes",
        barmode="relative",
        **_layout(hovermode="x"),
    )
    return fig


def grafico_venta_perdida(economia: list[ResultadoEconomico]) -> go.Figure:
    """Cuánta plata se deja sobre la mesa en cada escenario."""
    nombres = [e.nombre for e in economia]

    fig = go.Figure(
        go.Bar(
            x=nombres,
            y=[e.venta_perdida for e in economia],
            marker_color=ROJO,
            text=[f"${e.venta_perdida:,.0f}" for e in economia],
            textposition="outside",
            hovertemplate="%{x}: $%{y:,.0f} por mes<extra></extra>",
        )
    )
    fig.update_layout(
        title="Venta perdida mensual (costo de oportunidad)",
        xaxis_title="Escenario",
        yaxis_title="Pesos por mes",
        showlegend=False,
        **_layout(hovermode="closest"),
    )
    return fig
