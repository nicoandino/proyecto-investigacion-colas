"""Pronóstico de la demanda mensual (parte 3 del orquestador, §15–19), con los métodos de la cátedra.

La serie es REAL: las ventas mensuales al público de Shell en Mendoza (PRO-01, Secretaría de Energía). No es la
estación sino la suma de las Shell de la provincia: el simulador usa su FORMA (cuánto pesa cada mes, la tendencia en
%) escalada a los litros de la estación (DEM-01).

Métodos (los del práctico de Pronóstico, programados a mano; sin dependencias nuevas):

  · de nivel:      promedio móvil de n meses · suavizado exponencial simple (α)
  · de tendencia:  recta de mínimos cuadrados  F_t = A + B·t   (t = 0 el primer mes)
  · estacional:    el promedio × el índice del mes
  · tendencia estacional (multiplicativo):  F_t = (A + B·t) × I_mes
        I_mes = promedio de y_t ÷ (promedio móvil centrado de 12 meses) en ese mes, normalizado a promedio 1;
        A y B salen de la recta ajustada a la serie desestacionalizada (y_t ÷ I_mes).

Errores (en los meses de PRUEBA, que no se usan para ajustar):
  MAE = Σ|e|/n · MAPE = Σ|e/y|/n · RMSE = √(Σe²/n) · sesgo = Σe/n, con e = y − F.
Se elige el método de menor RMSE y el intervalo del pronóstico es F ± z·RMSE (PRO-03).

Este módulo no importa Streamlit ni `ui/` y no imprime nada.
"""

from __future__ import annotations

import math
from typing import NamedTuple

from sim.datos import valor

#: Los métodos, en el orden en que se muestran.
METODOS: dict[str, str] = {
    "promedio_movil": "Promedio móvil",
    "suavizado": "Suavizado exponencial simple",
    "tendencia": "Tendencia (recta de mínimos cuadrados)",
    "estacional": "Estacional (promedio × índice del mes)",
    "tendencia_estacional": "Tendencia estacional (recta × índice del mes)",
}


class Errores(NamedTuple):
    mae: float
    mape: float        # fracción (0,05 = 5 %)
    rmse: float
    sesgo: float       # promedio de (real − pronóstico): > 0 = el método se queda corto


class Ajuste(NamedTuple):
    """Un método ajustado con los meses de entrenamiento y probado en los de prueba."""

    metodo: str
    ajustados: tuple[float | None, ...]   # pronóstico de cada mes de entrenamiento (None si no hay con qué)
    prueba: tuple[float, ...]             # pronóstico de cada mes de prueba (desde el final del entrenamiento)
    errores: Errores                      # en los meses de prueba
    detalle: str                          # los parámetros, en palabras


class Pronostico(NamedTuple):
    """Todo el análisis de la serie: los métodos, el elegido y los próximos meses."""

    meses: tuple[tuple[int, int], ...]          # (año, mes) de la ventana usada (entrenamiento + prueba)
    reales: tuple[float, ...]
    n_prueba: int
    ajustes: tuple[Ajuste, ...]
    elegido: str
    futuros: tuple[tuple[int, int], ...]        # los próximos meses
    pronostico: tuple[float, ...]               # con el método elegido, reajustado con toda la ventana
    intervalo: tuple[tuple[float, float], ...]  # ± z · RMSE de prueba
    indices: tuple[float, ...]                  # 12 índices estacionales (enero…diciembre), promedio 1
    tendencia_mensual: float                    # B ÷ nivel medio: cuánto cambia por mes, en fracción


# =============================================================================
# Errores
# =============================================================================
def errores(reales: list[float] | tuple[float, ...], pronosticos: list[float] | tuple[float, ...]) -> Errores:
    """MAE, MAPE, RMSE y sesgo (sólo los pares con pronóstico)."""
    pares = [(y, f) for y, f in zip(reales, pronosticos) if f is not None]
    n = len(pares)
    if n == 0:
        return Errores(0.0, 0.0, 0.0, 0.0)
    e = [y - f for y, f in pares]
    return Errores(
        mae=sum(abs(x) for x in e) / n,
        mape=sum(abs(x / y) for x, (y, _) in zip(e, pares) if y) / n,
        rmse=math.sqrt(sum(x * x for x in e) / n),
        sesgo=sum(e) / n,
    )


# =============================================================================
# Métodos
# =============================================================================
def recta(y: list[float] | tuple[float, ...]) -> tuple[float, float]:
    """(A, B) de la recta de mínimos cuadrados y = A + B·t, con t = 0, 1, …, n − 1."""
    n = len(y)
    t_medio = (n - 1) / 2.0
    y_medio = sum(y) / n
    sxy = sum((t - t_medio) * (v - y_medio) for t, v in enumerate(y))
    sxx = sum((t - t_medio) ** 2 for t in range(n))
    b = sxy / sxx if sxx else 0.0
    return y_medio - b * t_medio, b


def promedio_movil(y, n: int, horizonte: int) -> tuple[list[float | None], list[float]]:
    """F_t = promedio de los n meses anteriores; hacia adelante, el último promedio (plano)."""
    ajustados = [None if t < n else sum(y[t - n:t]) / n for t in range(len(y))]
    ultimo = sum(y[-n:]) / n
    return ajustados, [ultimo] * horizonte


def suavizado(y, alfa: float, horizonte: int) -> tuple[list[float | None], list[float]]:
    """F_1 = y_0 y F_t+1 = α·y_t + (1 − α)·F_t; hacia adelante, el último F (plano)."""
    ajustados: list[float | None] = [None]       # el primer mes no tiene pronóstico
    f = y[0]                                     # F_1 = y_0
    for t in range(1, len(y)):
        ajustados.append(f)                      # F_t
        f = alfa * y[t] + (1 - alfa) * f         # F_t+1 = α·y_t + (1 − α)·F_t
    return ajustados, [f] * horizonte            # f = el pronóstico del mes siguiente al último


def indices_estacionales(y, posicion: list[int], periodo: int = 12) -> list[float]:
    """Índice de cada estación (mes o trimestre), por cocientes al promedio móvil centrado; promedio 1.

    `posicion[t]` es la estación del dato t (0…periodo − 1). Con periodo par, el promedio móvil centrado es el de
    2 × periodo (cada punta pesa la mitad).
    """
    n = len(y)
    mitad = periodo // 2
    cocientes: dict[int, list[float]] = {k: [] for k in range(periodo)}
    for t in range(mitad, n - mitad):
        if periodo % 2 == 0:
            centrado = (0.5 * y[t - mitad] + sum(y[t - mitad + 1:t + mitad]) + 0.5 * y[t + mitad]) / periodo
        else:
            centrado = sum(y[t - mitad:t + mitad + 1]) / periodo
        cocientes[posicion[t]].append(y[t] / centrado)
    crudos = [sum(c) / len(c) if c else 1.0 for k, c in sorted(cocientes.items())]
    promedio = sum(crudos) / periodo
    return [c / promedio for c in crudos]


def tendencia_estacional(y, posicion: list[int], horizonte: int, periodo: int = 12):
    """(ajustados, hacia adelante, índices, A, B): la recta de la serie desestacionalizada × el índice."""
    indices = indices_estacionales(y, posicion, periodo)
    desest = [v / indices[posicion[t]] for t, v in enumerate(y)]
    a, b = recta(desest)
    n = len(y)
    ajustados = [(a + b * t) * indices[posicion[t]] for t in range(n)]
    adelante = [(a + b * (n + h)) * indices[(posicion[-1] + 1 + h) % periodo] for h in range(horizonte)]
    return ajustados, adelante, indices, a, b


def _ajustar(metodo: str, y, posicion: list[int], horizonte: int):
    """(ajustados, hacia adelante, detalle) de un método."""
    n_movil, alfa = valor("PRO-04")
    if metodo == "promedio_movil":
        aj, ad = promedio_movil(y, int(n_movil), horizonte)
        return aj, ad, f"{int(n_movil)} meses"
    if metodo == "suavizado":
        aj, ad = suavizado(y, float(alfa), horizonte)
        return aj, ad, f"α = {alfa:g}".replace(".", ",")
    if metodo == "tendencia":
        a, b = recta(y)
        n = len(y)
        return ([a + b * t for t in range(n)], [a + b * (n + h) for h in range(horizonte)],
                f"A = {a:,.0f} · B = {b:+,.1f} por mes".replace(",", "X").replace(".", ",").replace("X", "."))
    indices = indices_estacionales(y, posicion)
    if metodo == "estacional":
        nivel = sum(v / indices[posicion[t]] for t, v in enumerate(y)) / len(y)
        return ([nivel * indices[posicion[t]] for t in range(len(y))],
                [nivel * indices[(posicion[-1] + 1 + h) % 12] for h in range(horizonte)],
                f"nivel desestacionalizado {nivel:,.0f}".replace(",", "."))
    aj, ad, _, a, b = tendencia_estacional(y, posicion, horizonte)
    return aj, ad, f"A = {a:,.0f} · B = {b:+,.1f} por mes".replace(",", "X").replace(".", ",").replace("X", ".")


# =============================================================================
# La serie del Registro y el análisis completo
# =============================================================================
def meses_desde(inicio: tuple[int, int], n: int) -> tuple[tuple[int, int], ...]:
    anio, mes = inicio
    salida = []
    for _ in range(n):
        salida.append((anio, mes))
        mes += 1
        if mes > 12:
            anio, mes = anio + 1, 1
    return tuple(salida)


def serie_registro() -> tuple[tuple[tuple[int, int], ...], tuple[float, ...]]:
    """(meses, m³) de PRO-01 completos (ene-2019 – ago-2026)."""
    inicio, valores = valor("PRO-01")
    return meses_desde(tuple(inicio), len(valores)), tuple(float(v) for v in valores)


def analizar(horizonte: int = 12) -> Pronostico:
    """Ajusta los métodos en la ventana PRO-02, los prueba en los últimos meses y pronostica los próximos."""
    meses_todos, valores_todos = serie_registro()
    primero, n_prueba = valor("PRO-02")
    desde = meses_todos.index(tuple(primero))
    meses, reales = meses_todos[desde:], valores_todos[desde:]
    posicion = [m - 1 for _, m in meses]
    corte = len(reales) - int(n_prueba)
    entrenamiento, prueba = list(reales[:corte]), list(reales[corte:])
    ajustes = []
    for metodo in METODOS:
        aj, ad, detalle = _ajustar(metodo, entrenamiento, posicion[:corte], len(prueba))
        ajustes.append(Ajuste(metodo, tuple(aj), tuple(ad), errores(prueba, ad), detalle))
    elegido = min(ajustes, key=lambda a: a.errores.rmse)
    # El elegido se vuelve a ajustar con toda la ventana para pronosticar los próximos meses.
    _, futuro, _ = _ajustar(elegido.metodo, list(reales), posicion, horizonte)
    z = float(valor("PRO-03"))
    banda = z * elegido.errores.rmse
    futuros = meses_desde(meses[-1], horizonte + 1)[1:]
    _, _, indices, a, b = tendencia_estacional(list(reales), posicion, horizonte)
    nivel = sum(reales) / len(reales)
    return Pronostico(
        meses=meses, reales=reales, n_prueba=int(n_prueba), ajustes=tuple(ajustes), elegido=elegido.metodo,
        futuros=futuros, pronostico=tuple(futuro), intervalo=tuple((f - banda, f + banda) for f in futuro),
        indices=tuple(indices), tendencia_mensual=b / nivel,
    )


def estacionalidad_del_pronostico() -> tuple[float, ...]:
    """Los 12 índices estacionales (enero…diciembre) de la serie real, promedio 1: la opción del calendario."""
    return analizar().indices



# =============================================================================
# Stock de seguridad (P4): del error del pronóstico al punto de pedido s
# =============================================================================
class StockSeguridad(NamedTuple):
    """La cuenta del punto de pedido por pronóstico de un tanque."""

    producto: str
    consumo_dia: float      # D: litros por día del producto (DEM-01 × su parte ÷ 30)
    plazo_dias: float       # L: plazo medio del camión (INV-01), en días
    error_relativo: float   # RMSE del método elegido ÷ el promedio de los meses de prueba
    sigma_dia: float        # σ_día = error_relativo × D × 30 ÷ √30
    seguridad: float        # z · σ_día · √L
    s: float                # D · L + seguridad (redondeado a 100 L, con lugar para el camión)
    q: float                # Q de la política cargada (no cambia)


def stock_de_seguridad(p, z: float | None = None) -> tuple[StockSeguridad, ...]:
    """s = D·L + z·σ_día·√L para cada tanque, con σ del error del pronóstico (supuesto: errores diarios independientes).

    La demanda del plazo (D·L) cubre lo que se vende mientras viaja el camión; el stock de seguridad cubre que la
    demanda real se aparte del pronóstico. El error sale de la serie real (RMSE de prueba del método elegido, en % del
    nivel) y se lleva a la estación: σ_mes = error × D × 30 y σ_día = σ_mes ÷ √30.
    """
    analisis = analizar()
    elegido = next(a for a in analisis.ajustes if a.metodo == analisis.elegido)
    prueba = analisis.reales[-analisis.n_prueba:]
    error = elegido.errores.rmse / (sum(prueba) / len(prueba))
    z = float(valor("PRO-03")) if z is None else z
    parte = {pr.id: pr.pct_litros for pr in p.productos}
    salida = []
    for i in p.inventario:
        d = p.litros_mes / 30.0 * parte[i.producto]
        largo = i.plazo_entrega.media / 24.0
        sigma = error * d * 30.0 / math.sqrt(30.0)
        seguridad = z * sigma * math.sqrt(largo)
        s = min(round(d * largo + seguridad, -2), i.capacidad - 500.0)
        q = max(500.0, min(i.cantidad_pedido, i.capacidad - s))
        salida.append(StockSeguridad(i.producto, d, largo, error, sigma, seguridad, s, q))
    return tuple(salida)


def politica_por_pronostico(p) -> dict[str, tuple[float, float]]:
    """{producto: (s, Q)} con el stock de seguridad del pronóstico (la Q de la política cargada)."""
    return {x.producto: (x.s, x.q) for x in stock_de_seguridad(p)}
