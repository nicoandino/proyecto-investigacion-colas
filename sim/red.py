"""Red de abastecimiento: camino más corto del camión y cortes de ruta (ORQUESTADOR §7.4).

La estación se abastece con un camión cisterna que sale de un origen (Dock Sud ≈ 991 km
por General Alvear, o la planta de Luján de Cuyo). La red es un grafo no dirigido de 10
arcos (nota 06 §1.2–1.3) y el camino del camión es el más corto en km, calculado con
DIJKSTRA (`heapq`, sin networkx): el apunte de redes de la materia (TP 5, camino más
corto), aplicado a un problema real.

Un corte cierra uno o más arcos. Si el arco cerrado NO está en el camino óptimo, el viaje
no se entera (con origen Dock Sud, el corte nevado de la RN 143 Pareditas–San Rafael no
está en la ruta). Si está, el camión toma el mejor camino alternativo o espera que se
reabra, lo que sea menor:

    demora = mín(tiempo del camino alternativo − tiempo del camino óptimo,
                 duración restante del corte)

y esa demora se SUMA al plazo de entrega base (INV-01, que ya incluye la espera
administrativa, la carga y el viaje normal).

Unidades: kilómetros, minutos (el motor trabaja en minutos), velocidad en km/h.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import replace
from functools import lru_cache
from typing import NamedTuple

from sim.config import ANO_REFERENCIA, Arco, CorteRuta, ParametrosRed, Triangular
from sim.distribuciones import Aleatorio


class Camino(NamedTuple):
    """Resultado de `camino_mas_corto`: (km, minutos, nodos de la ruta)."""

    km: float
    minutos: float
    ruta: tuple[str, ...]


SIN_CAMINO = Camino(math.inf, math.inf, ())

#: Nombres para mostrar de los nodos de la red.
NOMBRE_NODO = {
    "DOCK": "Dock Sud",
    "LUJAN": "Luján de Cuyo",
    "PAREDITAS": "Pareditas",
    "SOSNEADO": "El Sosneado",
    "SANRAFAEL": "San Rafael",
    "ALVEAR": "General Alvear",
    "MONTECOMAN": "Monte Comán",
    "LAPAZ": "La Paz",
    "ARROYO": "Arroyo Seco",
}

#: Etiquetas de los escenarios de corte para la interfaz.
ETIQUETA_ESCENARIO = {
    "ninguno": "Sin cortes",
    "aleatorio": "Cortes sorteados en jun–ago",
}


def descripcion_ruta(red: ParametrosRed) -> str:
    """'Dock Sud → General Alvear → San Rafael · 991 km · 14,2 h' (el camino óptimo)."""
    camino = _camino(red, frozenset())
    nodos = " → ".join(NOMBRE_NODO[n] for n in camino.ruta)
    return f"{nodos} · {camino.km:,.0f} km · {camino.minutos / 60:.1f} h".replace(".", ",")


def _clave(a: str, b: str) -> frozenset[str]:
    return frozenset((a, b))


@lru_cache(maxsize=512)
def _camino(red: ParametrosRed, cerrados: frozenset[frozenset[str]]) -> Camino:
    """Dijkstra sobre los km, sin los arcos `cerrados` (cacheado: la red es inmutable)."""
    vecinos: dict[str, list[tuple[str, float]]] = {}
    for arco in red.arcos:
        if _clave(arco.a, arco.b) in cerrados:
            continue
        vecinos.setdefault(arco.a, []).append((arco.b, arco.km))
        vecinos.setdefault(arco.b, []).append((arco.a, arco.km))

    mejor: dict[str, float] = {red.origen: 0.0}
    previo: dict[str, str] = {}
    cola = [(0.0, red.origen)]
    while cola:
        km, nodo = heapq.heappop(cola)
        if km > mejor.get(nodo, math.inf):
            continue                      # entrada vieja del heap
        if nodo == red.destino:
            break
        for siguiente, largo in vecinos.get(nodo, ()):
            candidato = km + largo
            if candidato < mejor.get(siguiente, math.inf):
                mejor[siguiente] = candidato
                previo[siguiente] = nodo
                heapq.heappush(cola, (candidato, siguiente))

    if red.destino not in mejor:
        return SIN_CAMINO
    ruta = [red.destino]
    while ruta[-1] != red.origen:
        ruta.append(previo[ruta[-1]])
    ruta.reverse()
    km = mejor[red.destino]
    return Camino(km, km / red.velocidad_kmh * 60.0, tuple(ruta))


def camino_mas_corto(
    red: ParametrosRed,
    origen: str | None = None,
    destino: str | None = None,
    cerrados: tuple[tuple[str, str], ...] = (),
) -> Camino:
    """El camino más corto en km entre dos nodos, sin pasar por los arcos `cerrados`.

    Devuelve `(km, minutos, ruta)`; si los cortes aíslan el destino, `(inf, inf, ())`.
    """
    if origen is not None or destino is not None:
        red = replace(red, origen=origen or red.origen, destino=destino or red.destino)
    return _camino(red, frozenset(_clave(a, b) for a, b in cerrados))


def arcos_de_la_ruta(ruta: tuple[str, ...]) -> frozenset[frozenset[str]]:
    """Los arcos que recorre una ruta (pares de nodos consecutivos)."""
    return frozenset(_clave(a, b) for a, b in zip(ruta, ruta[1:]))


def demora_por_corte(
    red: ParametrosRed,
    cerrados: tuple[tuple[str, str], ...],
    restante_min: float,
) -> float:
    """Minutos que se demora un viaje que sale con `cerrados` cortados.

    Cero si ningún arco cerrado está en el camino óptimo. Si lo está:
    mín(desvío por el mejor camino alternativo, minutos que faltan para que se reabra).
    Si no hay alternativa, el camión espera la reapertura entera.
    """
    optimo = _camino(red, frozenset())
    cierres = frozenset(_clave(a, b) for a, b in cerrados)
    if not cierres & arcos_de_la_ruta(optimo.ruta):
        return 0.0
    alternativo = _camino(red, cierres)
    return min(alternativo.minutos - optimo.minutos, restante_min)


def corte_de(red: ParametrosRed, id_corte: str) -> CorteRuta:
    return next(c for c in red.cortes if c.id == id_corte)


def mes_del_dia(inicio: tuple[int, int], dia: int) -> int:
    """Mes de calendario del día `dia` (1 = `inicio`) de una corrida."""
    from datetime import date, timedelta

    return (date(ANO_REFERENCIA, *inicio) + timedelta(days=dia - 1)).month


def demora_de_viaje(
    red: ParametrosRed,
    ahora_min: float,
    mes: int,
    az: Aleatorio,
    stream: str,
) -> tuple[float, str]:
    """(demora en minutos, causa) del viaje de un camión que sale en el minuto `ahora_min`.

    - `ninguno`: sin demora y sin sortear nada.
    - `aleatorio`: sólo en los meses de `meses_corte`; con probabilidad `prob_corte_viaje`
      el viaje encuentra un corte sobre un arco cortable elegido al azar, de duración
      `duracion_aleatoria` (lo encuentra entero: demora = mín(desvío, duración)).
    - `E1`..`E4`: el corte empieza a las 00:00 del día `corte_dia` y dura la moda de su
      duración; los viajes que salen adentro de esa ventana esperan lo que falte o se
      desvían. La obra (E3) agrega su demora fija a los viajes de su franja horaria, todos
      los días.
    """
    escenario = red.escenario_corte
    if escenario == "ninguno":
        return 0.0, ""

    if escenario == "aleatorio":
        if az.es_determinista or mes not in red.meses_corte:
            return 0.0, ""       # sin azar no hay cortes sorteados (sólo los E1–E4 elegidos)
        if not az.bernoulli(red.prob_corte_viaje, stream):
            return 0.0, ""
        cortables = [a for a in red.arcos if a.cortable]
        arco = cortables[min(int(az.uniforme(stream) * len(cortables)), len(cortables) - 1)]
        duracion_min = az.triangular(red.duracion_aleatoria, stream) * 60.0
        demora = demora_por_corte(red, ((arco.a, arco.b),), duracion_min)
        return demora, (f"corte en la {arco.ruta}" if demora > 0 else "")

    corte = corte_de(red, escenario)
    if corte.demora_fija_min > 0:
        hora = (ahora_min % 1440.0) / 60.0
        desde, hasta = corte.franja or (0.0, 24.0)
        return (corte.demora_fija_min, "obra") if desde <= hora < hasta else (0.0, "")
    inicio = (red.corte_dia - 1) * 1440.0
    fin = inicio + corte.duracion.moda * 60.0
    if inicio <= ahora_min < fin:
        demora = demora_por_corte(red, corte.arcos, fin - ahora_min)
        return demora, (f"corte {corte.id}" if demora > 0 else "")
    return 0.0, ""


def demora_si_encuentra_el_corte(red: ParametrosRed, id_corte: str) -> float:
    """Demora (min) de un viaje que sale justo cuando empieza el corte forzado `id_corte`."""
    corte = corte_de(red, id_corte)
    if corte.demora_fija_min > 0:
        return corte.demora_fija_min
    return demora_por_corte(red, corte.arcos, corte.duracion.moda * 60.0)


def muestrear_plazos(
    plazo_base: Triangular,
    red: ParametrosRed,
    cantidad: int = 4000,
    semilla: int = 1,
    mes: int = 7,
) -> tuple[list[float], list[float]]:
    """Plazos de entrega (horas) de `cantidad` viajes SIN cortes y CON el escenario elegido.

    Para el histograma de la pestaña Red y rutas. En los escenarios forzados (E1–E4) se
    muestrea un viaje que sale justo cuando empieza el corte; en `aleatorio`, un viaje de
    `mes` (por defecto julio) que puede o no encontrarlo. Mismos plazos base en las dos
    listas (números aleatorios comunes): la diferencia es sólo el corte.
    """
    az = Aleatorio(semilla)
    sin_corte: list[float] = []
    con_corte: list[float] = []
    fija = (
        demora_si_encuentra_el_corte(red, red.escenario_corte)
        if red.escenario_corte not in ("ninguno", "aleatorio")
        else 0.0
    )
    for _ in range(cantidad):
        base = az.triangular(plazo_base, "entrega_super")
        sin_corte.append(base)
        if red.escenario_corte == "aleatorio":
            demora, _ = demora_de_viaje(red, 0.0, mes, az, "corte_ruta_super")
        else:
            demora = fija
        con_corte.append(base + demora / 60.0)
    return sin_corte, con_corte


def rutas_posibles(red: ParametrosRed, origen: str | None = None) -> list[Camino]:
    """Todas las rutas simples (sin repetir nodos) del origen al destino, de la más corta a la más larga.

    La red tiene 9 nodos: recorrerla entera es instantáneo y la primera ruta coincide con la de Dijkstra.
    """
    origen = origen or red.origen
    vecinos: dict[str, list[tuple[str, float]]] = {}
    for arco in red.arcos:
        vecinos.setdefault(arco.a, []).append((arco.b, arco.km))
        vecinos.setdefault(arco.b, []).append((arco.a, arco.km))
    salida: list[Camino] = []

    def visitar(nodo: str, km: float, ruta: list[str]) -> None:
        if nodo == red.destino:
            salida.append(Camino(km, km / red.velocidad_kmh * 60.0, tuple(ruta)))
            return
        for siguiente, largo in vecinos.get(nodo, ()):
            if siguiente not in ruta:
                visitar(siguiente, km + largo, ruta + [siguiente])

    visitar(origen, 0.0, [origen])
    return sorted(salida, key=lambda c: (c.km, c.ruta))


def origen_del_pedido(red: ParametrosRed, az: Aleatorio, stream: str) -> tuple[str, bool]:
    """(origen que despacha el pedido, si se redirigió).

    Sin orígenes alternativos ni marcados no disponibles: el habitual, sin sortear nada. Si no, se prueba el
    habitual y después los alternativos en orden; cada uno puede estar marcado a mano o fallar con la
    probabilidad `prob_origen_no_disponible` (sin azar, una cuota exacta). Si ninguno puede, sale del habitual
    con la demora de redirección.
    """
    if not red.origenes_alternativos and not red.origenes_no_disponibles:
        return red.origen, False
    for origen in (red.origen, *red.origenes_alternativos):
        falla = origen in red.origenes_no_disponibles
        if not falla and red.prob_origen_no_disponible > 0:
            falla = az.bernoulli(red.prob_origen_no_disponible, stream)
        if not falla:
            return origen, origen != red.origen
    return red.origen, True


def extra_por_origen(red: ParametrosRed, origen: str, redirigido: bool) -> float:
    """Minutos que se suman al plazo base por salir de otro origen: (viaje desde ese origen − viaje desde el
    habitual) + la demora de redirección si se redirigió."""
    if not redirigido:
        return 0.0
    diferencia = camino_mas_corto(red, origen=origen).minutos - camino_mas_corto(red).minutos
    return diferencia + red.demora_redireccion_h * 60.0


def dias_de_mes_en_corrida(inicio: tuple[int, int], dias: int) -> set[int]:
    """Meses de calendario que toca una corrida (para avisar si no incluye jun–ago)."""
    return {mes_del_dia(inicio, d) for d in range(1, dias + 1)}


__all__ = [
    "NOMBRE_NODO",
    "ETIQUETA_ESCENARIO",
    "descripcion_ruta",
    "Arco",
    "Camino",
    "arcos_de_la_ruta",
    "camino_mas_corto",
    "corte_de",
    "demora_de_viaje",
    "demora_por_corte",
    "demora_si_encuentra_el_corte",
    "dias_de_mes_en_corrida",
    "mes_del_dia",
    "muestrear_plazos",
    "origen_del_pedido",
    "extra_por_origen",
    "rutas_posibles",
]
