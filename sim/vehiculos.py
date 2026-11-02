"""Vehículos por día — motos, autos, colectivos y camiones — con Monte Carlo (pedido de Nico, 2/11/2026).

¿Hay un dato publicado de cuántos vehículos de cada tipo cargan por día o por mes en esta estación? **No** (ver
`research_notes/…/14_vehiculos_por_tipo.md`): ni la estación, ni la Secretaría de Energía, ni Vialidad publican conteos
por tipo de vehículo en una estación de San Rafael. Lo que sí hay son **proporciones** (Vialidad: 86,7 % autos y
camionetas en los accesos de Mendoza; AFAC: 3 % de pesados en el parque). Por eso se **sortea**:

  1. La probabilidad de cada tipo sale del propio modelo: mezcla de productos (DEM-04, DEM-05) × tipo de vehículo por
     producto (VEH-00). El pesado del motor ("camión / ómnibus", VEH-04) se parte en camiones y colectivos (VEH-08).
  2. Probabilidad acumulada.
  3. Intervalo de números aleatorios de 4 cifras (0000 a 9999).
  4. Para cada cliente del día (los clientes por día salen de la simulación) se genera un número aleatorio.
  5. El número cae en un intervalo ⇒ ese es su tipo de vehículo. Contando, salen los de cada tipo en el día.

Los números aleatorios salen de un generador con semilla propia: no tocan los streams del motor (STREAMS).
Este módulo no importa Streamlit.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from sim.datos import valor

#: Las cuatro categorías que se muestran, en orden.
CATEGORIAS: tuple[str, ...] = ("moto", "auto", "colectivo", "camion")
NOMBRES: dict[str, str] = {
    "moto": "Motos",
    "auto": "Autos y camionetas",
    "colectivo": "Colectivos",
    "camion": "Camiones",
}
#: Tipo del motor (VEH-00 / tipos_vehiculo) → categoría de la pestaña. El pesado se reparte aparte (VEH-08).
_CATEGORIA_DEL_TIPO = {"moto": "moto", "auto": "auto", "pick_up": "auto", "auto_gnc": "auto"}
#: Orden de los tipos en la matriz VEH-00.
_TIPOS_MATRIZ = ("moto", "auto", "pick_up", "camion")
#: Los números aleatorios van de 0000 a 9999.
ESCALA = 10_000


@dataclass(frozen=True)
class Intervalo:
    """Una fila de la tabla de Monte Carlo (pasos 1 a 3)."""

    categoria: str
    probabilidad: float
    acumulada: float
    desde: int          # primer número aleatorio del intervalo (0000–9999)
    hasta: int          # último número aleatorio del intervalo

    @property
    def texto(self) -> str:
        return f"{self.desde:04d} a {self.hasta:04d}" if self.hasta >= self.desde else "—"


@dataclass(frozen=True)
class DiaVehiculos:
    """Un día del sorteo: cuántos clientes hubo y cuántos de cada tipo salieron."""

    dia: int
    clientes: int
    cantidades: tuple[int, ...]                       # en el orden de CATEGORIAS
    detalle: tuple[tuple[int, str], ...] = ()         # (número aleatorio, categoría) de los primeros clientes


@dataclass(frozen=True)
class Resumen:
    """Una categoría en todo el período: lo sorteado contra lo esperado."""

    categoria: str
    total: int
    promedio_dia: float
    esperado_dia: float          # clientes por día promedio × probabilidad
    minimo: int
    maximo: int


def composicion(p, frac_colectivos: float | None = None) -> tuple[tuple[str, float], ...]:
    """Probabilidad de cada categoría para un cliente cualquiera (paso 1).

    Σ sobre los productos de (probabilidad de llegada del producto × % del tipo de vehículo en ese producto, VEH-00).
    El GNC es todo auto. El pesado se parte: `frac_colectivos` (VEH-08) son colectivos y el resto camiones.
    """
    frac = float(valor("VEH-08")) if frac_colectivos is None else float(frac_colectivos)
    if not 0.0 <= frac <= 1.0:
        raise ValueError("La fracción de colectivos tiene que estar entre 0 y 1.")
    matriz = dict(p.matriz_tipos)
    prob = dict.fromkeys(CATEGORIAS, 0.0)
    for producto, peso in zip(p.productos, p.pesos_llegada()):
        if producto.es_gnc:
            prob["auto"] += peso
            continue
        for tipo, fraccion in zip(_TIPOS_MATRIZ, matriz[producto.id]):
            if tipo == "camion":
                prob["colectivo"] += peso * fraccion * frac
                prob["camion"] += peso * fraccion * (1.0 - frac)
            else:
                prob[_CATEGORIA_DEL_TIPO[tipo]] += peso * fraccion
    total = sum(prob.values())
    return tuple((c, prob[c] / total) for c in CATEGORIAS)


def tabla(comp: Sequence[tuple[str, float]]) -> tuple[Intervalo, ...]:
    """Pasos 1 a 3: probabilidad, acumulada e intervalo de números aleatorios (0000–9999)."""
    filas, acumulada, desde = [], 0.0, 0
    for i, (categoria, prob) in enumerate(comp):
        acumulada += prob
        hasta = ESCALA - 1 if i == len(comp) - 1 else int(round(acumulada * ESCALA)) - 1
        filas.append(Intervalo(categoria, prob, min(acumulada, 1.0), desde, hasta))
        desde = hasta + 1
    return tuple(filas)


def asignar(numero: int, intervalos: Sequence[Intervalo]) -> str:
    """Paso 5: el número aleatorio (0000–9999) cae en un intervalo ⇒ la categoría."""
    for fila in intervalos:
        if fila.desde <= numero <= fila.hasta:
            return fila.categoria
    raise ValueError(f"Número aleatorio fuera de rango: {numero}.")


def sortear(clientes_por_dia: Sequence[int], comp: Sequence[tuple[str, float]], semilla: int = 1,
            detalle: int = 20) -> tuple[DiaVehiculos, ...]:
    """Pasos 4 y 5 para cada día: un número aleatorio por cliente y su tipo de vehículo; se cuentan por día.

    `detalle` = cuántos de los primeros clientes de cada día se guardan con su número (para mostrar el sorteo).
    """
    intervalos = tabla(comp)
    generador = random.Random(semilla)
    dias = []
    for d, n in enumerate(clientes_por_dia, start=1):
        cuenta = dict.fromkeys(CATEGORIAS, 0)
        primeros = []
        for k in range(int(n)):
            numero = int(generador.random() * ESCALA)
            categoria = asignar(numero, intervalos)
            cuenta[categoria] += 1
            if k < detalle:
                primeros.append((numero, categoria))
        dias.append(DiaVehiculos(d, int(n), tuple(cuenta[c] for c in CATEGORIAS), tuple(primeros)))
    return tuple(dias)


def resumir(dias: Sequence[DiaVehiculos], comp: Sequence[tuple[str, float]]) -> tuple[Resumen, ...]:
    """Por categoría: total del período, promedio por día, lo esperado (clientes × probabilidad), mínimo y máximo."""
    if not dias:
        return ()
    n = len(dias)
    clientes_medios = sum(d.clientes for d in dias) / n
    salida = []
    for i, (categoria, prob) in enumerate(comp):
        valores = [d.cantidades[i] for d in dias]
        salida.append(Resumen(categoria, sum(valores), sum(valores) / n, clientes_medios * prob,
                              min(valores), max(valores)))
    return tuple(salida)
