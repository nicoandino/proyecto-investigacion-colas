"""Análisis financiero de una decisión: flujo de fondos, VAN, TIR y período de recupero (payback).

El flujo de cada mes es la ganancia INCREMENTAL que da la simulación (la estación con la decisión menos la estación de
hoy, o el resultado entero si se evalúa el negocio completo). Se trabaja en pesos de hoy (moneda constante) con una
tasa de descuento real, así la inflación no se cuenta dos veces.

  VAN = −I + Σ F / (1 + i)^t          t = 1 … n meses, i = tasa mensual = (1 + tasa anual)^(1/12) − 1
  TIR = la tasa que hace VAN = 0 (se busca por bisección; se informa anual)
  Payback simple = I ÷ F meses · payback descontado = primer mes en que Σ F/(1+i)^t ≥ I

Este módulo no importa Streamlit.
"""

from __future__ import annotations

from typing import NamedTuple


class Financiero(NamedTuple):
    inversion: float                  # I, en $ al inicio
    flujo_mensual: float              # F, en $ por mes
    meses: int                        # n
    tasa_anual: float                 # tasa de descuento real anual
    tasa_mensual: float
    van: float
    tir_anual: float | None           # None si no hay inversión o el flujo nunca la recupera
    payback_meses: float | None       # simple
    payback_descontado_meses: int | None
    por_anio: tuple[tuple[int, float, float, float], ...]   # (año, flujo, flujo descontado, acumulado descontado)


def tasa_mensual(tasa_anual: float) -> float:
    return (1.0 + tasa_anual) ** (1.0 / 12.0) - 1.0


def van(inversion: float, flujo: float, meses: int, i_mensual: float) -> float:
    if i_mensual == 0:
        return -inversion + flujo * meses
    return -inversion + flujo * (1.0 - (1.0 + i_mensual) ** -meses) / i_mensual


def tir_mensual(inversion: float, flujo: float, meses: int) -> float | None:
    """La tasa mensual que hace VAN = 0, por bisección. None si no existe (sin inversión o flujo que no la recupera)."""
    if inversion <= 0 or flujo <= 0 or flujo * meses <= inversion:
        return None
    bajo, alto = 0.0, 1.0
    while van(inversion, flujo, meses, alto) > 0:
        alto *= 2.0
    for _ in range(200):
        medio = (bajo + alto) / 2.0
        if van(inversion, flujo, meses, medio) > 0:
            bajo = medio
        else:
            alto = medio
    return (bajo + alto) / 2.0


def analizar(inversion: float, flujo_mensual: float, meses: int, tasa_anual: float) -> Financiero:
    i = tasa_mensual(tasa_anual)
    r = tir_mensual(inversion, flujo_mensual, meses)
    payback = inversion / flujo_mensual if inversion > 0 and flujo_mensual > 0 else None
    acumulado, recupero = 0.0, None
    for t in range(1, meses + 1):
        acumulado += flujo_mensual / (1.0 + i) ** t
        if recupero is None and inversion > 0 and acumulado >= inversion:
            recupero = t
    por_anio, acumulado_anio = [(0, -inversion, -inversion, -inversion)], -inversion
    for anio in range(1, (meses + 11) // 12 + 1):
        meses_anio = range((anio - 1) * 12 + 1, min(anio * 12, meses) + 1)
        flujo = flujo_mensual * len(meses_anio)
        flujo_desc = sum(flujo_mensual / (1.0 + i) ** t for t in meses_anio)
        acumulado_anio += flujo_desc
        por_anio.append((anio, flujo, flujo_desc, acumulado_anio))
    return Financiero(
        inversion=inversion, flujo_mensual=flujo_mensual, meses=meses, tasa_anual=tasa_anual, tasa_mensual=i,
        van=van(inversion, flujo_mensual, meses, i), tir_anual=None if r is None else (1.0 + r) ** 12 - 1.0,
        payback_meses=payback, payback_descontado_meses=recupero, por_anio=tuple(por_anio),
    )


# =============================================================================
# Las decisiones que se evalúan: el flujo mensual sale de la simulación
# =============================================================================
#: Qué se puede evaluar en el desplegable de Economía.
OPCIONES = {
    "surtidor": "Un surtidor más de nafta (2 caras)",
    "playero": "Un playero más en las horas pico",
    "estacion": "La estación completa (el negocio)",
}


def con_decision(p, opcion: str):
    """Los parámetros de la estación con la decisión tomada (la estación completa no cambia nada)."""
    from dataclasses import replace

    from sim.config import turnos_con_refuerzo
    from sim.escenarios import PICOS

    if opcion == "surtidor":
        return replace(p, grupos=tuple(replace(g, caras=g.caras + 2) if g.id == "A" else g for g in p.grupos))
    if opcion == "playero":
        return replace(p, turnos=turnos_con_refuerzo(p.playeros_por_turno, tuple((d, h, 1) for d, h in PICOS)))
    return p


def inversion_de(opcion: str, eco) -> float:
    """La inversión inicial del Registro: el surtidor (ECO-05), nada para el playero, la estación (FIN-03)."""
    from sim.datos import valor

    return {"surtidor": eco.inversion_surtidor, "playero": 0.0, "estacion": float(valor("FIN-03"))}[opcion]


def flujo_mensual(opcion: str, base, con, eco) -> float:
    """Ganancia por mes que agrega la decisión: resultado con la decisión − resultado de hoy (promedio de réplicas).

    `base` y `con` son listas de EconomiaMensual. El surtidor suma además su costo operativo mensual (ECO-05); el
    playero ya está en los sueldos (más personas-turno). La estación completa es su resultado entero.
    """
    def promedio(lista):
        return sum(e.margen_operativo for e in lista) / len(lista)

    if opcion == "estacion":
        return promedio(base)
    extra = eco.operativo_surtidor_mensual if opcion == "surtidor" else 0.0
    return promedio(con) - promedio(base) - extra
