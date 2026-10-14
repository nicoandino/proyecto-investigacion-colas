"""Cortes de GNC en invierno (ORQUESTADOR §7.5).

La estación vende GNC con contrato INTERRUMPIBLE (supuesto, GNC-01): cuando hay una ola de
frío, el ENARGAS manda cortar el GNC a las estaciones con ese contrato para priorizar el
gas de las casas (verificado para abril-2026 en el AMBA; San Rafael lo vivió en 2022). Es
un corte TOTAL, no un "−50 %", y llega por EPISODIOS de varios días.

Cada réplica sortea el calendario de episodios de su invierno (stream "corte_gnc"):
`episodios` fechas de inicio al azar entre el 1/jun y el 31/ago, de `dias_por_episodio`
días cada una. Como el sorteo es del invierno entero, un horizonte que no incluye jun–ago
no ve ningún corte, y uno de un mes ve sólo los episodios que caen adentro. Con
`episodios_en_horizonte` los episodios se sortean entre los días de invierno del horizonte,
para poder estudiar el corte sin esperar a que el azar lo ponga adentro.

Este módulo sólo arma el calendario; el motor (`sim/modelo.py`) lo aplica:
  - durante un corte total las 6 caras GNC no atienden (los que ya cargan terminan);
  - con probabilidad `migracion_a_nafta` el cliente pasa a Súper, si no se pierde.
"""

from __future__ import annotations

from datetime import date, timedelta

from sim.config import ANO_REFERENCIA, ParametrosGNC
from sim.distribuciones import Aleatorio

#: Ventana de invierno en la que caen los episodios (1/jun a 31/ago: 92 días).
INICIO_INVIERNO = date(ANO_REFERENCIA, 6, 1)
DIAS_INVIERNO = 92
MESES_INVIERNO = (6, 7, 8)

#: Forma "ventana" (Sitio Andino 23/6/2022): corte de 17 a 01 h de cada día del episodio.
VENTANA_DESDE_H = 17.0
VENTANA_HASTA_H = 25.0


def calendario_de_episodios(
    g: ParametrosGNC, az: Aleatorio, fecha_inicio: date, dias: int
) -> list[tuple[int, int]]:
    """Episodios de la corrida: [(día de inicio relativo a la corrida, duración en días)].

    El día 0 es el primero de la corrida; puede dar negativo si el episodio empezó antes
    del horizonte (el tramo que cae adentro igual se aplica). Siempre se consumen
    `episodios` sorteos del stream, para que cambiar otros parámetros no mueva las fechas.
    """
    if g.contrato != "interrumpible" or g.episodios <= 0:
        return []
    episodios: list[tuple[int, int]] = []
    if az.es_determinista:
        # Sin azar: los episodios quedan equiespaciados dentro del invierno (o de sus días
        # dentro del horizonte), siempre en las mismas fechas.
        n, dur = g.episodios, g.dias_por_episodio
        if g.episodios_en_horizonte:
            candidatos = [
                d for d in range(dias)
                if (fecha_inicio + timedelta(days=d)).month in MESES_INVIERNO
            ]
            for k in range(1, n + 1):
                if candidatos:
                    episodios.append((candidatos[len(candidatos) * k // (n + 1)], dur))
        else:
            hueco = (DIAS_INVIERNO - n * dur) / (n + 1)
            for k in range(1, n + 1):
                corrimiento = round(k * hueco + (k - 1) * dur)
                episodios.append(((INICIO_INVIERNO + timedelta(days=corrimiento) - fecha_inicio).days, dur))
            episodios = _mas_cortes_y_frio(g, az, episodios, fecha_inicio)
        return sorted(episodios)
    if g.episodios_en_horizonte:
        candidatos = [
            d for d in range(dias)
            if (fecha_inicio + timedelta(days=d)).month in MESES_INVIERNO
        ]
        for _ in range(g.episodios):
            u = az.uniforme("corte_gnc")
            if candidatos:
                inicio = candidatos[min(int(u * len(candidatos)), len(candidatos) - 1)]
                episodios.append((inicio, g.dias_por_episodio))
    else:
        for _ in range(g.episodios):
            u = az.uniforme("corte_gnc")
            corrimiento = int(u * (DIAS_INVIERNO - g.dias_por_episodio + 1))
            inicio = (INICIO_INVIERNO + timedelta(days=corrimiento) - fecha_inicio).days
            episodios.append((inicio, g.dias_por_episodio))
        episodios = _mas_cortes_y_frio(g, az, episodios, fecha_inicio)
    return sorted(episodios)


def _mas_cortes_y_frio(
    g: ParametrosGNC, az: Aleatorio, episodios: list[tuple[int, int]], fecha_inicio: date
) -> list[tuple[int, int]]:
    """"Más cortes en todo el invierno" (menú): suma `cortes_extra` episodios y, con probabilidad
    `prob_invierno_frio`, alarga cada corte `dias_extra_frio` días. Con los defaults no hace nada (ni sortea).

    Sin azar los cortes extra caen en el medio de los huecos más largos del invierno (siempre las mismas fechas)
    y el alargue es una cuota exacta; con azar las fechas salen del stream "cortes_extra_gnc" y el alargue del
    stream "invierno_frio" (los dos al final de STREAMS: no mueven ningún otro sorteo).
    """
    corrimiento = (INICIO_INVIERNO - fecha_inicio).days     # día de la corrida en que empieza el invierno
    dur = g.dias_por_episodio
    salida = list(episodios)
    if g.cortes_extra > 0:
        if az.es_determinista:
            ocupados = sorted((i - corrimiento, i - corrimiento + d) for i, d in episodios)
            huecos, cursor = [], 0
            for a, b in ocupados:
                if a > cursor:
                    huecos.append((cursor, a))
                cursor = max(cursor, b)
            if cursor < DIAS_INVIERNO:
                huecos.append((cursor, DIAS_INVIERNO))
            huecos.sort(key=lambda h: -(h[1] - h[0]))       # los más largos primero (empate: el más temprano)
            for a, b in huecos[: g.cortes_extra]:
                if b - a >= dur:
                    salida.append((a + (b - a - dur) // 2 + corrimiento, dur))
        else:
            for _ in range(g.cortes_extra):
                u = az.uniforme("cortes_extra_gnc")
                salida.append((int(u * (DIAS_INVIERNO - dur + 1)) + corrimiento, dur))
    if g.prob_invierno_frio > 0 and g.dias_extra_frio > 0:
        salida = [
            (i, d + g.dias_extra_frio) if az.bernoulli(g.prob_invierno_frio, "invierno_frio") else (i, d)
            for i, d in sorted(salida)
        ]
    return sorted(salida)


def intervalos_de_corte(
    g: ParametrosGNC, episodios: list[tuple[int, int]], dias: int
) -> list[tuple[float, float]]:
    """Intervalos (minuto inicial, minuto final) de la corrida en que el GNC está afectado.

    `total_24h` y `parcial_50`: los días enteros del episodio. `ventana`: de 17 a 01 h de
    cada día. Se recortan al horizonte y se fusionan los que se tocan.
    """
    total = dias * 1440.0
    crudos: list[tuple[float, float]] = []
    for inicio, duracion in episodios:
        for d in range(inicio, inicio + duracion):
            if g.forma == "ventana":
                a, b = d * 1440.0 + VENTANA_DESDE_H * 60.0, d * 1440.0 + VENTANA_HASTA_H * 60.0
            else:
                a, b = d * 1440.0, (d + 1) * 1440.0
            a, b = max(a, 0.0), min(b, total)
            if b > a:
                crudos.append((a, b))
    fusionados: list[tuple[float, float]] = []
    for a, b in sorted(crudos):
        if fusionados and a <= fusionados[-1][1]:
            fusionados[-1] = (fusionados[-1][0], max(fusionados[-1][1], b))
        else:
            fusionados.append((a, b))
    return fusionados


def minutos_de_corte_en_dia(intervalos: list[tuple[float, float]], dia: int) -> float:
    """Minutos del día `dia` (0 = primero de la corrida) con el GNC afectado."""
    desde, hasta = dia * 1440.0, (dia + 1) * 1440.0
    return sum(max(0.0, min(b, hasta) - max(a, desde)) for a, b in intervalos)


def episodios_con_fechas(
    episodios: list[tuple[int, int]], fecha_inicio: date, dias: int
) -> list[tuple[date, date]]:
    """Los episodios que tocan el horizonte, como (primera fecha, última fecha)."""
    salida = []
    for inicio, duracion in episodios:
        if inicio + duracion > 0 and inicio < dias:
            salida.append(
                (fecha_inicio + timedelta(days=inicio),
                 fecha_inicio + timedelta(days=inicio + duracion - 1))
            )
    return salida
