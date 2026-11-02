"""Vehículos por día (Montecarlo): motos, autos, camionetas, colectivos y camiones (2/11/2026).

¿Hay un dato publicado de cuántos vehículos de cada tipo cargan por día o por mes en una estación de San Rafael?
**No** (research_notes/demanda_310k_y_mix_vehicular.md). Sí hay **proporciones**: el censo de Vialidad en la RN 143 a
la entrada de San Rafael (VEH-08; la RN 143 es la propia Av. Balloffet) y el parque de motos (VEH-09). Por eso se
sortea, día por día:

  1. Total de vehículos del día: N ~ Normal(media del día, DEM-16 × media base), redondeado y ≥ 0. La media del día
     sale de los litros del día ÷ litros medios por vehículo (DEM-11): ≈ 257 con 310.000 L/mes; la media base es la
     del día promedio del año (sin fin de semana ni estacionalidad).
  2. Tipo de cada vehículo: U(0,1) contra la tabla de probabilidades acumuladas (el método de la cátedra).
  3. Litros de cada carga: Triangular del tipo (VEH-10).

Es la MISMA tabla que usa el simulador para sus llegadas (`ParametrosSimulacion.mezcla_vehiculos`, matriz VEH-00
derivada): la pestaña muestra el sorteo y el motor lo usa. Los números aleatorios salen de un generador con semilla
propia (no tocan los STREAMS del motor). Este módulo no importa Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from sim.config import dias_del_mes
from sim.datos import valor

#: Los cinco tipos, en el orden de la tabla.
CATEGORIAS: tuple[str, ...] = ("moto", "auto", "pick_up", "colectivo", "camion")
NOMBRES: dict[str, str] = {
    "moto": "Moto", "auto": "Auto", "pick_up": "Camioneta", "colectivo": "Colectivo", "camion": "Camión",
}


@dataclass(frozen=True)
class Intervalo:
    """Una fila de la tabla de Montecarlo: probabilidad, acumulada y rango de U(0,1)."""

    categoria: str
    probabilidad: float
    acumulada: float
    desde: float
    hasta: float

    @property
    def texto(self) -> str:
        return f"[{self.desde:.4f} – {self.hasta:.4f})".replace(".", ",")


@dataclass(frozen=True)
class DiaVehiculos:
    """Un día del sorteo."""

    dia: int                                        # 1 = primer día del período
    media: float                                    # vehículos esperados ese día
    n: int                                          # vehículos sorteados (paso 1)
    cantidades: tuple[int, ...]                     # por tipo, en el orden de CATEGORIAS
    litros: tuple[float, ...]                       # por tipo
    detalle: tuple[tuple[float, str, float], ...] = ()   # (U, tipo, litros) de los primeros vehículos

    @property
    def litros_total(self) -> float:
        return float(sum(self.litros))


@dataclass(frozen=True)
class ResumenMes:
    """Litros de un mes repetido muchas veces (Montecarlo): media y percentiles 5 y 95."""

    mes: int
    repeticiones: int
    esperado: float          # Σ litros del día del simulador en ese mes
    media: float
    p5: float
    p95: float
    vehiculos_dia: float     # vehículos por día, promedio


def tabla(p) -> tuple[Intervalo, ...]:
    """Pasos 1 a 3 del Montecarlo: probabilidad, acumulada y rango [desde, hasta) de U(0,1)."""
    filas, acumulada = [], 0.0
    for i, (categoria, prob) in enumerate(p.mezcla_vehiculos):
        desde = acumulada
        acumulada = 1.0 if i == len(p.mezcla_vehiculos) - 1 else acumulada + prob
        filas.append(Intervalo(categoria, prob, acumulada, desde, acumulada))
    return tuple(filas)


def tipo_de(u: float, intervalos: tuple[Intervalo, ...]) -> str:
    """Paso 5: el número U cae en un rango ⇒ el tipo de vehículo."""
    for fila in intervalos:
        if fila.desde <= u < fila.hasta:
            return fila.categoria
    return intervalos[-1].categoria


def media_base(p) -> float:
    """Vehículos de líquidos de un día promedio: litros del mes ÷ (365 / 12) días ÷ litros medios (≈ 257)."""
    return p.litros_mes / (365.0 / 12.0) / p.litros_medios_por_cliente


def media_del_dia(p, dia: int) -> float:
    """Vehículos de líquidos esperados ese día: litros del día (fin de semana y estacionalidad) ÷ litros medios."""
    return p.litros_del_dia(dia) / p.litros_medios_por_cliente


def _parametros(p):
    intervalos = tabla(p)
    acumuladas = np.array([f.acumulada for f in intervalos])
    tipos = {t.id: t for t in p.tipos_vehiculo}
    a = np.array([tipos[c].litros.minimo for c in CATEGORIAS])
    m = np.array([tipos[c].litros.moda for c in CATEGORIAS])
    b = np.array([tipos[c].litros.maximo for c in CATEGORIAS])
    return intervalos, acumuladas, a, m, b


def _un_dia(rng, media: float, desvio: float, acumuladas, a, m, b):
    n = max(0, int(round(rng.normal(media, desvio))))
    u = rng.random(n)
    idx = np.minimum(np.searchsorted(acumuladas, u, side="right"), len(CATEGORIAS) - 1)
    litros = rng.triangular(a[idx], m[idx], b[idx]) if n else np.zeros(0)
    return n, u, idx, litros


def sortear(p, semilla: int = 1, cv: float | None = None, detalle: int = 15) -> tuple[DiaVehiculos, ...]:
    """Los pasos 1 a 3 para cada día del período de `p`."""
    cv = float(valor("DEM-16")) if cv is None else float(cv)
    _, acumuladas, a, m, b = _parametros(p)
    rng = np.random.default_rng(semilla)
    desvio = cv * media_base(p)
    dias = []
    for d in range(1, p.dias + 1):
        media = media_del_dia(p, d)
        n, u, idx, litros = _un_dia(rng, media, desvio, acumuladas, a, m, b)
        cantidades = np.bincount(idx, minlength=len(CATEGORIAS))
        por_tipo = np.bincount(idx, weights=litros, minlength=len(CATEGORIAS))
        primeros = tuple((float(u[k]), CATEGORIAS[int(idx[k])], float(litros[k])) for k in range(min(detalle, n)))
        dias.append(DiaVehiculos(d, media, n, tuple(int(x) for x in cantidades),
                                 tuple(float(x) for x in por_tipo), primeros))
    return tuple(dias)


def resumen_mes(p, mes: int, semilla: int = 1, repeticiones: int = 1000, cv: float | None = None) -> ResumenMes:
    """El mes `mes` (del año de referencia) sorteado `repeticiones` veces: media, P5 y P95 de los litros."""
    cv = float(valor("DEM-16")) if cv is None else float(cv)
    p_mes = replace(p, fecha_inicio=(mes, 1), dias=dias_del_mes(mes), dias_calentamiento=0, dia_animado=1)
    _, acumuladas, a, m, b = _parametros(p_mes)
    rng = np.random.default_rng(10_000 + semilla)
    desvio = cv * media_base(p_mes)
    medias = [media_del_dia(p_mes, d) for d in range(1, p_mes.dias + 1)]
    totales, vehiculos = np.zeros(repeticiones), np.zeros(repeticiones)
    for r in range(repeticiones):
        for media in medias:
            n, _, _, litros = _un_dia(rng, media, desvio, acumuladas, a, m, b)
            totales[r] += litros.sum()
            vehiculos[r] += n
    esperado = sum(p_mes.litros_del_dia(d) for d in range(1, p_mes.dias + 1))
    return ResumenMes(mes, repeticiones, esperado, float(totales.mean()), float(np.percentile(totales, 5)),
                      float(np.percentile(totales, 95)), float(vehiculos.mean() / p_mes.dias))


__all__ = ["CATEGORIAS", "NOMBRES", "DiaVehiculos", "Intervalo", "ResumenMes", "media_base",
           "media_del_dia", "resumen_mes", "sortear", "tabla", "tipo_de"]
