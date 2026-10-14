"""Flujos en redes (parte 3 del orquestador, §15–19): transporte, transbordo, flujo de costo mínimo y flujo máximo.

Los métodos se programan a mano, **como se enseñan en la cátedra** (sin dependencias nuevas):

  · Transporte (matriz oferta × demanda × costo):
        solución inicial por el RINCÓN NOROESTE o por el COSTO MÍNIMO, y mejora con MODI / Stepping-Stone
        (potenciales u_i + v_j = c_ij en las celdas usadas; índice de mejora c_ij − u_i − v_j en las vacías; el
        circuito de la celda que entra reparte θ con signos + y − alternados). Si la oferta y la demanda no
        coinciden se agrega un origen o un destino FICTICIO con costo 0; si la solución usa menos de m + n − 1
        celdas (degenerada) se agregan celdas con 0.
  · Transbordo: la matriz de la cátedra (los nodos que envían son filas, los que reciben son columnas; los de
        paso tienen oferta B y demanda B, con costo 0 consigo mismos) resuelta como transporte.
  · Flujo de costo mínimo: caminos más cortos sucesivos (Bellman-Ford sobre la red residual).
  · Flujo máximo: trayectorias de aumento (la más corta en arcos, BFS) y el corte mínimo.

Este módulo no importa Streamlit ni `ui/` y no imprime nada.
"""

from __future__ import annotations

from collections import deque
from typing import NamedTuple

#: Costo de una celda sin arco en la matriz de transbordo ("M grande").
M_GRANDE = 10.0 ** 9


# =============================================================================
# Transporte
# =============================================================================
class Transporte(NamedTuple):
    """Una solución de transporte (balanceada)."""

    asignacion: tuple[tuple[float, ...], ...]   # filas = orígenes, columnas = destinos
    costo: float
    iteraciones: int = 0                        # mejoras de MODI / Stepping-Stone
    ficticio: str = ""                          # "origen" | "destino" | "" si ya estaba balanceado


def balancear(oferta, demanda, costos):
    """(oferta, demanda, costos, ficticio): agrega un origen o un destino ficticio con costo 0 si hace falta."""
    oferta, demanda = list(map(float, oferta)), list(map(float, demanda))
    costos = [list(map(float, fila)) for fila in costos]
    diferencia = sum(oferta) - sum(demanda)
    if abs(diferencia) < 1e-9:
        return oferta, demanda, costos, ""
    if diferencia > 0:                          # sobra oferta: un destino ficticio
        demanda.append(diferencia)
        for fila in costos:
            fila.append(0.0)
        return oferta, demanda, costos, "destino"
    oferta.append(-diferencia)                  # sobra demanda: un origen ficticio
    costos.append([0.0] * len(demanda))
    return oferta, demanda, costos, "origen"


def costo_de(asignacion, costos) -> float:
    return sum(x * c for fila_x, fila_c in zip(asignacion, costos) for x, c in zip(fila_x, fila_c))


def _con_base(asig, base, m, n):
    """Completa la base hasta m + n − 1 celdas sin formar circuitos (degeneración: celdas con 0)."""
    padre = list(range(m + n))

    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    for i, j in base:
        padre[raiz(i)] = raiz(m + j)
    for i in range(m):
        for j in range(n):
            if len(base) >= m + n - 1:
                return base
            if (i, j) not in base and raiz(i) != raiz(m + j):
                base.add((i, j))
                padre[raiz(i)] = raiz(m + j)
    return base


def rincon_noroeste(oferta, demanda):
    """(asignación, base): se llena desde la esquina de arriba a la izquierda."""
    o, d = list(oferta), list(demanda)
    m, n = len(o), len(d)
    asig = [[0.0] * n for _ in range(m)]
    base = set()
    i = j = 0
    while i < m and j < n:
        x = min(o[i], d[j])
        asig[i][j] = x
        base.add((i, j))
        o[i] -= x
        d[j] -= x
        if o[i] <= 1e-9 and i < m - 1:
            i += 1
        else:
            j += 1
    return asig, _con_base(asig, base, m, n)


def costo_minimo(oferta, demanda, costos):
    """(asignación, base): la celda más barata primero (empate: la primera en orden de lectura)."""
    o, d = list(oferta), list(demanda)
    m, n = len(o), len(d)
    asig = [[0.0] * n for _ in range(m)]
    base = set()
    filas, columnas = set(range(m)), set(range(n))
    while filas and columnas:
        _, i, j = min((costos[i][j], i, j) for i in filas for j in columnas)
        x = min(o[i], d[j])
        asig[i][j] = x
        base.add((i, j))
        o[i] -= x
        d[j] -= x
        # Se tacha la fila si se agotó la oferta (si se agotaron las dos, sólo la fila: la columna queda con 0 y
        # la próxima asignación en ella es la celda con 0 de la degeneración); si no, la columna.
        if o[i] <= 1e-9:
            filas.discard(i)
        else:
            columnas.discard(j)
    return asig, _con_base(asig, base, m, n)


def _potenciales(base, costos, m, n):
    """u_i + v_j = c_ij en las celdas de la base (u_0 = 0)."""
    u: list[float | None] = [None] * m
    v: list[float | None] = [None] * n
    u[0] = 0.0
    cambio = True
    while cambio:
        cambio = False
        for i, j in base:
            if u[i] is not None and v[j] is None:
                v[j] = costos[i][j] - u[i]
                cambio = True
            elif v[j] is not None and u[i] is None:
                u[i] = costos[i][j] - v[j]
                cambio = True
    return [x or 0.0 for x in u], [x or 0.0 for x in v]


def _circuito(base, entra, m, n):
    """Las celdas del circuito de Stepping-Stone que empieza en `entra` (camino de la fila a la columna en la base)."""
    i0, j0 = entra
    # Grafo bipartito de la base: nodo fila i = i, nodo columna j = m + j.
    vecinos: dict[int, list[int]] = {}
    for i, j in base:
        vecinos.setdefault(i, []).append(m + j)
        vecinos.setdefault(m + j, []).append(i)
    previo = {i0: None}
    cola = deque([i0])
    while cola:
        a = cola.popleft()
        if a == m + j0:
            break
        for b in vecinos.get(a, []):
            if b not in previo:
                previo[b] = a
                cola.append(b)
    camino = []
    a = m + j0
    while a is not None:
        camino.append(a)
        a = previo[a]
    camino.reverse()                            # fila i0 … columna j0
    celdas = [entra]
    for a, b in zip(camino, camino[1:]):
        celdas.append((a, b - m) if a < m else (b, a - m))
    return celdas                               # signos: + − + − … (la que entra es +)


def modi(oferta, demanda, costos, asig, base, max_iter: int = 500):
    """Mejora una solución inicial hasta el óptimo (MODI para los índices, Stepping-Stone para el circuito)."""
    m, n = len(oferta), len(demanda)
    asig = [fila[:] for fila in asig]
    base = set(base)
    iteraciones = 0
    while iteraciones < max_iter:
        u, v = _potenciales(base, costos, m, n)
        mejor, entra = -1e-9, None
        for i in range(m):
            for j in range(n):
                if (i, j) not in base:
                    indice = costos[i][j] - u[i] - v[j]
                    if indice < mejor:
                        mejor, entra = indice, (i, j)
        if entra is None:
            break
        celdas = _circuito(base, entra, m, n)
        menos = celdas[1::2]
        theta = min(asig[i][j] for i, j in menos)
        sale = next(c for c in menos if abs(asig[c[0]][c[1]] - theta) < 1e-9)
        for k, (i, j) in enumerate(celdas):
            asig[i][j] += theta if k % 2 == 0 else -theta
        base.add(entra)
        base.discard(sale)
        iteraciones += 1
    return asig, iteraciones


def resolver_transporte(oferta, demanda, costos, inicial: str = "costo_minimo") -> Transporte:
    """Transporte balanceado y resuelto: solución inicial (rincón noroeste o costo mínimo) + MODI."""
    o, d, c, ficticio = balancear(oferta, demanda, costos)
    asig, base = rincon_noroeste(o, d) if inicial == "rincon_noroeste" else costo_minimo(o, d, c)
    final, iteraciones = modi(o, d, c, asig, base)
    return Transporte(tuple(tuple(f) for f in final), costo_de(final, c), iteraciones, ficticio)


def solucion_inicial(oferta, demanda, costos, metodo: str) -> Transporte:
    """Sólo la solución inicial (para mostrar cuánto cuesta cada método de partida)."""
    o, d, c, ficticio = balancear(oferta, demanda, costos)
    asig, _ = rincon_noroeste(o, d) if metodo == "rincon_noroeste" else costo_minimo(o, d, c)
    return Transporte(tuple(tuple(f) for f in asig), costo_de(asig, c), 0, ficticio)


# =============================================================================
# Redes: arcos dirigidos
# =============================================================================
class ArcoRed(NamedTuple):
    desde: str
    hasta: str
    costo: float = 0.0
    capacidad: float = float("inf")


class Flujo(NamedTuple):
    """Resultado de un flujo: cuánto pasa por cada arco."""

    valor: float                                   # flujo total (o lo que se envió)
    costo: float
    flujos: tuple[tuple[str, str, float], ...]     # (desde, hasta, flujo) de los arcos con flujo > 0
    corte: tuple[tuple[str, str], ...] = ()        # arcos del corte mínimo (flujo máximo)


def _residual(arcos):
    """Red residual: por cada arco, uno hacia adelante y su reverso (capacidad 0, costo −c)."""
    grafo: dict[str, list[list]] = {}
    for k, a in enumerate(arcos):
        ida = [a.hasta, a.capacidad, a.costo, None, k]
        vuelta = [a.desde, 0.0, -a.costo, ida, None]
        ida[3] = vuelta
        grafo.setdefault(a.desde, []).append(ida)
        grafo.setdefault(a.hasta, []).append(vuelta)
    return grafo


def flujo_costo_minimo(arcos, ofertas: dict[str, float]) -> Flujo:
    """Transbordo / flujo de costo mínimo: `ofertas` > 0 envía y < 0 recibe (caminos más cortos sucesivos).

    Se agregan una fuente y un sumidero ficticios; mientras quede algo por enviar se busca el camino más barato de
    la red residual (Bellman-Ford, que acepta los costos negativos de los reversos) y se manda por él lo máximo posible.
    """
    fuente, sumidero = "__FUENTE__", "__SUMIDERO__"
    extra = [ArcoRed(fuente, n, 0.0, b) for n, b in ofertas.items() if b > 0] + \
            [ArcoRed(n, sumidero, 0.0, -b) for n, b in ofertas.items() if b < 0]
    todos = list(arcos) + extra
    grafo = _residual(todos)
    pedido = sum(b for b in ofertas.values() if b > 0)
    enviado = costo = 0.0
    while enviado < pedido - 1e-9:
        dist = {fuente: 0.0}
        previo: dict[str, list] = {}
        for _ in range(len(grafo)):
            cambio = False
            for a in list(dist):
                for borde in grafo.get(a, []):
                    destino, cap, c = borde[0], borde[1], borde[2]
                    if cap > 1e-9 and dist[a] + c < dist.get(destino, float("inf")) - 1e-12:
                        dist[destino] = dist[a] + c
                        previo[destino] = borde
                        cambio = True
            if not cambio:
                break
        if sumidero not in dist:
            break                               # no hay más caminos: lo que falta no se puede enviar
        camino, nodo = [], sumidero
        while nodo != fuente:
            borde = previo[nodo]
            camino.append(borde)
            nodo = borde[3][0]
        delta = min(min(b[1] for b in camino), pedido - enviado)
        for borde in camino:
            borde[1] -= delta
            borde[3][1] += delta
        enviado += delta
        costo += delta * dist[sumidero]
    flujos = []
    for n, bordes in grafo.items():
        for borde in bordes:
            k = borde[4]
            if k is not None and k < len(arcos):
                pasado = arcos[k].capacidad - borde[1] if arcos[k].capacidad != float("inf") else borde[3][1]
                if pasado > 1e-9:
                    flujos.append((arcos[k].desde, arcos[k].hasta, pasado))
    return Flujo(enviado, costo, tuple(sorted(flujos)))


def flujo_maximo(arcos, fuente: str, sumidero: str) -> Flujo:
    """Flujo máximo por trayectorias de aumento (la de menos arcos primero) y el corte mínimo."""
    grafo = _residual(arcos)
    total = 0.0
    while True:
        previo: dict[str, list] = {}
        cola = deque([fuente])
        vistos = {fuente}
        while cola and sumidero not in vistos:
            a = cola.popleft()
            for borde in grafo.get(a, []):
                if borde[1] > 1e-9 and borde[0] not in vistos:
                    vistos.add(borde[0])
                    previo[borde[0]] = borde
                    cola.append(borde[0])
        if sumidero not in vistos:
            break
        camino, nodo = [], sumidero
        while nodo != fuente:
            borde = previo[nodo]
            camino.append(borde)
            nodo = borde[3][0]
        delta = min(b[1] for b in camino)
        for borde in camino:
            borde[1] -= delta
            borde[3][1] += delta
        total += delta
    # Corte mínimo: los nodos que todavía se alcanzan desde la fuente en la red residual.
    alcanzables = {fuente}
    cola = deque([fuente])
    while cola:
        a = cola.popleft()
        for borde in grafo.get(a, []):
            if borde[1] > 1e-9 and borde[0] not in alcanzables:
                alcanzables.add(borde[0])
                cola.append(borde[0])
    corte = tuple((a.desde, a.hasta) for a in arcos if a.desde in alcanzables and a.hasta not in alcanzables)
    flujos = []
    for bordes in grafo.values():
        for borde in bordes:
            if borde[4] is not None and borde[3][1] > 1e-9:
                a = arcos[borde[4]]
                flujos.append((a.desde, a.hasta, borde[3][1]))
    costo = sum(f * arcos[[(a.desde, a.hasta) for a in arcos].index((d, h))].costo for d, h, f in flujos)
    return Flujo(total, costo, tuple(sorted(flujos)), corte)


# =============================================================================
# Transbordo con la matriz de la cátedra
# =============================================================================
class MatrizTransbordo(NamedTuple):
    filas: tuple[str, ...]           # nodos que envían
    columnas: tuple[str, ...]        # nodos que reciben
    oferta: tuple[float, ...]
    demanda: tuple[float, ...]
    costos: tuple[tuple[float, ...], ...]
    b: float                         # B = máx(Σ oferta, Σ demanda)


def matriz_transbordo(arcos, ofertas: dict[str, float]) -> MatrizTransbordo:
    """La matriz de transporte del transbordo, como en la cátedra.

    Filas: los nodos que envían (tienen arcos de salida); columnas: los que reciben. Un nodo de paso (envía y
    recibe) tiene oferta B + su oferta propia y demanda B + su demanda propia, y costo 0 consigo mismo; las celdas sin
    arco cuestan M (muy grande).
    """
    salen = list(dict.fromkeys(a.desde for a in arcos))
    entran = list(dict.fromkeys(a.hasta for a in arcos))
    b = max(sum(x for x in ofertas.values() if x > 0), -sum(x for x in ofertas.values() if x < 0))
    costo_arco = {(a.desde, a.hasta): a.costo for a in arcos}
    oferta = tuple(max(ofertas.get(n, 0.0), 0.0) + (b if n in entran else 0.0) for n in salen)
    demanda = tuple(max(-ofertas.get(n, 0.0), 0.0) + (b if n in salen else 0.0) for n in entran)
    costos = tuple(
        tuple(0.0 if f == c else costo_arco.get((f, c), M_GRANDE) for c in entran) for f in salen
    )
    return MatrizTransbordo(tuple(salen), tuple(entran), oferta, demanda, costos, b)
