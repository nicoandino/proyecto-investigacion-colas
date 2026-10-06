"""Catálogo de escenarios S0–S12 y estaciones del año (Fase 7, ORQUESTADOR §7.7 y §7.8).

Cada escenario es un `Escenario` con **cambios declarativos** `((campo, valor), …)` sobre
`ParametrosSimulacion` (datos, no lambdas: `st.cache_data` los serializa con pickle). Todos se
corren con **números aleatorios comunes**: la réplica i de cada escenario usa la misma
semilla, así que la diferencia contra S0 es el efecto del escenario y no el azar del sorteo.

Los números que aparecen acá salen del Registro (`sim/datos.py`) o de los parámetros: la única
decisión propia es **qué se cambia** en cada escenario, y está escrita en su descripción.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from sim.config import (
    ESTACIONALIDAD_PROXY,
    Escenario,
    ParametrosSimulacion,
    PerfilHorario,
    dias_del_mes,
    turnos_con_refuerzo,
    turnos_de,
)
from sim.datos import valor
from sim.runner import (
    ResultadoEscenario,
    Resumen,
    con_politicas,
    correr_replicas,
    grilla_politicas_real,
    resumen_de,
    resumir,
)

#: Estaciones del año con su mes representativo (§7.8): (nombre, etiqueta, mes).
ESTACIONES: tuple[tuple[str, str, int], ...] = (
    ("Verano", "ene", 1),
    ("Otoño", "abr", 4),
    ("Invierno", "jul", 7),
    ("Primavera", "oct", 10),
)

#: Picos de la dotación de playeros (PER-01 / DEM-02): 07–10 h y 16–18 h.
PICOS = ((7.0, 10.0), (16.0, 18.0))

#: Horas sin atención en el cierre nocturno de S10 (22 a 06 h).
HORAS_CERRADO = (22, 23, 0, 1, 2, 3, 4, 5)

MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


# =============================================================================
# Estaciones del año (S0 por estación, S1)
# =============================================================================
def para_mes(p: ParametrosSimulacion, mes: int) -> ParametrosSimulacion:
    """Los mismos parámetros pero simulando el mes real completo (días reales, fecha real)."""
    dias = dias_del_mes(mes)
    return replace(
        p,
        fecha_inicio=(mes, 1),
        dias=dias,
        horizonte="mes",
        dia_animado=min(p.dia_animado, dias),
    )


def correr_estaciones(
    p: ParametrosSimulacion, replicas: int = 4, semilla_base: int = 1
) -> list[ResultadoEscenario]:
    """4 corridas (ene · abr · jul · oct), cada una el mes real completo (§7.8).

    Con estacionalidad neutra las diferencias vienen del calendario (días del mes y fines de
    semana), del GNC (episodios de invierno) y de la ruta (cortes de jun–ago). Es lo correcto
    hasta tener la serie mensual de la Secretaría de Energía (C10).
    """
    salida = []
    for nombre, etiqueta, mes in ESTACIONES:
        p_mes = para_mes(p, mes)
        escenario = Escenario(
            nombre=f"{nombre} ({etiqueta})",
            descripcion=f"{MESES[mes - 1].capitalize()}: {p_mes.dias} días desde el 1/{mes:02d}",
            surtidores=p.surtidores,
            cajas=p.cajas,
            id=etiqueta,
            pregunta="línea base por estación del año",
            cambios=(
                ("fecha_inicio", (mes, 1)),
                ("dias", p_mes.dias),
                ("horizonte", "mes"),
                ("dia_animado", p_mes.dia_animado),
            ),
        )
        reps = correr_replicas(escenario.aplicar(p), replicas=replicas, semilla_base=semilla_base)
        salida.append(
            ResultadoEscenario(
                escenario=escenario,
                parametros=escenario.aplicar(p),
                replicas=reps,
                resumen=resumir(reps),
            )
        )
    return salida


# =============================================================================
# Catálogo S0–S12
# =============================================================================
def _dia_dentro(p: ParametrosSimulacion, dia: int, duracion: float) -> int:
    """El día `dia` si la ventana entra en el horizonte; si no, un día después del calentamiento."""
    if dia + duracion <= p.dias:
        return dia
    return min(p.dias_calentamiento + 2, p.dias)


def _esc(
    p: ParametrosSimulacion, id_: str, nombre: str, descripcion: str, pregunta: str, **cambios
) -> Escenario:
    return Escenario(
        nombre=nombre,
        descripcion=descripcion,
        surtidores=p.surtidores,
        cajas=p.cajas,
        id=id_,
        pregunta=pregunta,
        cambios=tuple(cambios.items()),
    )


def cambios_cierre_nocturno(p: ParametrosSimulacion) -> dict[str, object]:
    """Cambios de S10 (y del eje C1 del tornado): perfil en 0 de 22 a 06 h y litros del mes
    reducidos a la parte abierta, así las horas abiertas conservan su tasa de llegadas."""
    factores = p.perfil.factores
    abierto = tuple(0.0 if h in HORAS_CERRADO else f for h, f in enumerate(factores))
    return {
        "perfil": PerfilHorario(abierto),
        "litros_mes": p.litros_mes * sum(abierto) / sum(factores),
    }


def catalogo(p: ParametrosSimulacion) -> list[Escenario]:
    """Los escenarios del caso real (§7.7) armados sobre `p` (que ya es el mes a comparar).

    S1 (día típico por estación) es la pestaña Estaciones del año; S6 compara S2 (+1 playero)
    con S6 (stock extra), y el costo en $/mes de cada opción llega con la economía (Fase 8).
    """
    if not p.estacion_real:
        raise ValueError("El catálogo S0–S12 es del caso real; el clásico tiene sus 4 escenarios.")
    lista: list[Escenario] = [
        _esc(p, "S0", "S0 · Hoy", "La estación como está configurada, sin cambios.",
             "línea base")
    ]

    # --- S2: playeros en el pico -------------------------------------------------------------
    for extra in (-1, 1, 2):
        refuerzo = tuple((d, h, extra) for d, h in PICOS)
        lista.append(_esc(
            p, "S2", f"S2 · Playeros en el pico {extra:+d}",
            f"{extra:+d} playero/s en 07–10 h y 16–18 h (nunca menos de 1).",
            "¿alcanza la dotación?",
            turnos=turnos_con_refuerzo(p.playeros_por_turno, refuerzo),
        ))

    # --- S3: ola de frío con corte de GNC ----------------------------------------------------
    if p.gnc is not None:
        forzado = replace(p.gnc, contrato="interrumpible", episodios_en_horizonte=True)
        lista += [
            _esc(p, "S3", "S3 · Corte de GNC total 24 h",
                 "Episodios de corte total dentro del horizonte; "
                 f"{forzado.migracion_a_nafta:.0%} de los afectados pasa a Súper.",
                 "pérdida directa y adónde va",
                 gnc=replace(forzado, forma="total_24h")),
            _esc(p, "S3", "S3 · Corte de GNC ventana 17–01 h",
                 "Episodios con corte sólo de 17 a 01 h.",
                 "pérdida directa y adónde va",
                 gnc=replace(forzado, forma="ventana")),
            _esc(p, "S3", "S3 · Corte de GNC total, nadie migra",
                 "Corte total y ningún cliente acepta pasarse a nafta (peor caso).",
                 "pérdida directa y adónde va",
                 gnc=replace(forzado, forma="total_24h", migracion_a_nafta=0.0)),
        ]

    # --- S4: corte de la ruta del camión -----------------------------------------------------
    if p.red is not None:
        dia = _dia_dentro(p, p.red.corte_dia, 3)
        for corte, origen, rotulo in (
            ("E2", "DOCK", "E2 · origen Dock Sud"),
            ("E2", "LUJAN", "E2 · origen Luján de Cuyo"),
            ("E4", "DOCK", "E4 · origen Dock Sud"),
            ("E3", "DOCK", "E3 · obra, origen Dock Sud"),
        ):
            lista.append(_esc(
                p, "S4", f"S4 · Corte {rotulo}",
                f"Corte {corte} desde el día {dia} con el camión saliendo de "
                f"{'Dock Sud' if origen == 'DOCK' else 'Luján de Cuyo'}.",
                "plazo y quiebre",
                red=replace(p.red, escenario_corte=corte, origen=origen, corte_dia=dia),
            ))

    # --- S5: política de reposición ----------------------------------------------------------
    sugerida = grilla_politicas_real(p)[-1]   # el punto de la grilla con s = 2,5 y Q = 4,5 días
    lista.append(_esc(
        p, "S5", "S5 · Política s = 2,5 d · Q = 4,5 d",
        "Cada tanque pide cuando le quedan 2,5 días de consumo y pide 4,5 días. No es el "
        "óptimo (eso lo busca el barrido de la pestaña Inventario).",
        "¿cuándo y cuánto pedir?",
        inventario=con_politicas(p, sugerida).inventario,
    ))

    # --- S6: stock extra (la otra mitad de la decisión es S2 +1) -----------------------------
    reforzada = {
        i.producto: (min(i.punto_pedido * 1.5, i.capacidad - 500.0),
                     min(i.cantidad_pedido, i.capacidad - min(i.punto_pedido * 1.5, i.capacidad - 500.0)))
        for i in p.inventario
    }
    lista.append(_esc(
        p, "S6", "S6 · Stock extra (s × 1,5)",
        "Se sube un 50 % el punto de pedido de cada tanque. Se compara con S2 +1: "
        "¿un playero más en el pico o más stock?",
        "¿qué conviene en $/mes?",
        inventario=con_politicas(p, reforzada).inventario,
    ))

    # --- S7: crisis de abastecimiento --------------------------------------------------------
    dia_crisis = _dia_dentro(p, valor("INV-11")[0], valor("INV-11")[1])
    lista.append(_esc(
        p, "S7", "S7 · Crisis de abastecimiento",
        f"Los pedidos tardan Triangular{tuple(valor('INV-09'))} h durante "
        f"{valor('INV-11')[1]:g} días desde el día {dia_crisis}.",
        "resiliencia",
        crisis=tuple(valor("INV-09")), crisis_dia=dia_crisis, crisis_dias=valor("INV-11")[1],
    ))

    # --- S8: disciplina de cola --------------------------------------------------------------
    otra = "por_cara" if p.disciplina_cola == "por_grupo" else "por_grupo"
    lista.append(_esc(
        p, "S8", f"S8 · Cola {'por cara' if otra == 'por_cara' else 'por grupo'}",
        f"Cada cliente elige {'la fila más corta al llegar y no cambia' if otra == 'por_cara' else 'una cola única FIFO por zona'} "
        f"(el default es {'por grupo' if otra == 'por_cara' else 'por cara'}).",
        "¿cambia la espera?",
        disciplina_cola=otra,
    ))

    # --- S9: autoservicio --------------------------------------------------------------------
    menos = tuple(max(1, n - 1) for n in p.playeros_por_turno)
    lista.append(_esc(
        p, "S9", "S9 · Autoservicio (−1 playero por turno)",
        f"Decreto 46/2025: playeros {' · '.join(map(str, p.playeros_por_turno))} → "
        f"{' · '.join(map(str, menos))} (mínimo 1 por turno).",
        "¿se puede ahorrar personal?",
        playeros_por_turno=menos, turnos=turnos_de(menos),
    ))

    # --- S10: cierre nocturno 22–06 ----------------------------------------------------------
    cierre = cambios_cierre_nocturno(p)
    lista.append(_esc(
        p, "S10", "S10 · Cierre nocturno 22–06",
        f"La estación no atiende de 22 a 06 h: pierde el {1 - cierre['litros_mes'] / p.litros_mes:.0%} "
        "de la demanda (la de esas horas); las demás horas siguen igual de cargadas.",
        "efecto del horario",
        **cierre,
    ))

    # --- S11: estacionalidad turística -------------------------------------------------------
    lista.append(_esc(
        p, "S11", "S11 · Estacionalidad turística",
        "Índices mensuales del proxy turístico (jun = 55 … ene = 100): el mes comparado "
        "pesa distinto al promedio.",
        "¿importa la estacionalidad?",
        estacionalidad=ESTACIONALIDAD_PROXY,
    ))

    # --- S12: quincena -----------------------------------------------------------------------
    factor, dias = valor("DEM-12")
    lista.append(_esc(
        p, "S12", "S12 · Cambio de quincena",
        f"Los días {', '.join(map(str, dias))} del mes se vende ×{factor:g}; el mes conserva sus "
        "litros (el pico de cobro concentra la demanda).",
        "picos de cobro",
        factor_quincena=factor, dias_quincena=tuple(dias),
    ))
    return lista


def correr_catalogo(
    p: ParametrosSimulacion,
    mes: int,
    replicas: int = 4,
    semilla_base: int = 1,
    nombres: tuple[str, ...] | None = None,
) -> list[ResultadoEscenario]:
    """Corre S0–S12 en el mes `mes` con números aleatorios comunes.

    `nombres` limita qué escenarios se corren (S0 siempre entra: es la referencia).
    """
    p_mes = para_mes(p, mes)
    salida: list[ResultadoEscenario] = []
    for escenario in catalogo(p_mes):
        if nombres is not None and escenario.id != "S0" and escenario.nombre not in nombres:
            continue
        p_esc = escenario.aplicar(p_mes)
        reps = correr_replicas(p_esc, replicas=replicas, semilla_base=semilla_base)
        salida.append(
            ResultadoEscenario(
                escenario=escenario, parametros=p_esc, replicas=reps, resumen=resumir(reps)
            )
        )
    return salida


# =============================================================================
# Diferencias pareadas (números aleatorios comunes)
# =============================================================================
def diferencia_pareada(
    base: ResultadoEscenario, otro: ResultadoEscenario, metrica: str
) -> Resumen:
    """Promedio e IC 95 % de (otro − base) réplica a réplica.

    Como la réplica i de los dos escenarios usa la misma semilla, la diferencia por réplica
    descuenta el azar común y su intervalo es mucho más angosto que el de comparar los dos
    promedios por separado.
    """
    pares = zip(base.replicas, otro.replicas, strict=True)
    return resumen_de([float(getattr(o, metrica)) - float(getattr(b, metrica)) for b, o in pares])


def es_significativa(diferencia: Resumen) -> bool:
    """True si el IC 95 % de la diferencia no contiene el 0 (hay efecto más allá del azar)."""
    return diferencia.n > 1 and (diferencia.ic_inferior > 0 or diferencia.ic_superior < 0)
