"""Vistas de resultados del rediseño v3: Indicadores y Demanda verificables.

Todo número que se muestra se puede **comprobar**: al lado de cada indicador está la cuenta con los datos de
la corrida. Los clientes se cuentan (enteros); sólo los tiempos, las utilizaciones y los porcentajes llevan
decimales. Con datos reales (sin azar) no aparece nada de Monte Carlo: eso va en la pestaña *Qué se sorteó*,
que existe sólo si la simulación fue editada.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from sim.config import ANO_REFERENCIA, ParametrosEconomicos, ParametrosSimulacion
from sim.periodo import Periodo
from sim.runner import ResultadoEscenario, ResultadoReplica
from sim.traza import Traza
from ui import graficos

DIAS_SEMANA = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


# =============================================================================
# Formato: enteros con punto de miles y decimales con coma
# =============================================================================
def ent(n: float) -> str:
    """7.683 (entero con punto de miles)."""
    return f"{int(round(n)):,}".replace(",", ".")


def dec(x: float, d: int = 1) -> str:
    """1,6 (decimales con coma, miles con punto)."""
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(parte: float, total: float, d: int = 1) -> str:
    return f"{dec(100.0 * parte / total, d)} %" if total else "—"


def _tot(r: ResultadoReplica) -> dict[str, int]:
    return dict(r.totales)


def _nombres(p: ParametrosSimulacion) -> dict[str, str]:
    return {pr.id: pr.nombre for pr in p.productos}


def _horas(h: float) -> str:
    """'—' si no hubo, '3,4 h' si hubo."""
    return "—" if h <= 0 else f"{dec(h)} h"


def _pesos(x: float) -> str:
    return f"$ {ent(x)}"


# =============================================================================
# Quiebres de stock y litros que no se vendieron (tanda 3)
# =============================================================================
CAUSAS = (
    ("Falta de stock", "el tanque no alcanzaba para su carga"),
    ("Se cansó de esperar", "superó su paciencia en la cola"),
    ("Cola llena", "no había lugar en su zona (3 por cara)"),
    ("GNC cortado", "no pasó a Súper durante el corte"),
)


def bloque_quiebres(p: ParametrosSimulacion, r: ResultadoReplica, eco: ParametrosEconomicos) -> None:
    """Qué es un quiebre, cuántos hubo, cuánto duraron y qué costaron; y por qué no se vendió cada litro."""
    t = _tot(r)
    dias = max(r.dias_medidos, 1)
    nombres = _nombres(p)
    causas = {f[0]: f[1:] for f in r.litros_perdidos_causa}
    quiebres = {q[0]: q[1:] for q in r.quiebres}
    dias_falta = dict(r.dias_quiebre_total)
    pedidos = dict(r.pedidos_total)
    niveles = dict(r.nivel_por_producto)
    capacidad = {i.producto: i.capacidad for i in p.inventario}

    st.info(
        "**¿Qué es un quiebre de stock?** El tanque de un producto **no alcanza para la carga que pide el "
        "cliente** (en el peor caso, está vacío). Ese cliente se va sin cargar y el producto no se vende hasta "
        "que llega el camión; los otros productos siguen vendiéndose. El GNC no tiene tanque: no tiene "
        "quiebres, tiene cortes (pestaña GNC).",
        icon="🛢️",
    )
    venta_falta = sum(causas[pr][0] * eco.margen_de(pr) for pr in capacidad)
    _tarjetas([
        ("Veces que un tanque quedó vacío", ent(sum(q[0] for q in quiebres.values())),
         f"sumando los 4 tanques, en {ent(dias)} días"),
        ("Horas con un tanque vacío", _horas(sum(q[1] for q in quiebres.values())),
         "sumando los 4 tanques"),
        ("Clientes sin cargar por falta de stock", ent(t["perdidos_sin_combustible"]),
         f"{pct(t['perdidos_sin_combustible'], t['llegadas'])} de los que llegaron"),
        ("Venta perdida por falta de stock", _pesos(venta_falta),
         "costo de oportunidad: no se resta del margen"),
    ])

    st.markdown("##### Cada tanque")
    filas = []
    for pr in capacidad:
        n, horas, mas_largo = quiebres.get(pr, (0, 0.0, 0.0))
        filas.append({
            "Tanque": nombres[pr],
            "Veces que quedó vacío": ent(n),
            "Tiempo vacío (total)": _horas(horas),
            "El quiebre más largo": _horas(mas_largo),
            "Días con clientes sin cargar": f"{ent(dias_falta.get(pr, 0))} de {ent(dias)}",
            "Litros sin vender por falta de stock": f"{ent(causas[pr][0])} L",
            "Venta perdida": _pesos(causas[pr][0] * eco.margen_de(pr)),
            "Camiones pedidos": ent(pedidos.get(pr, 0)),
            "Nivel promedio": f"{ent(niveles[pr])} L ({pct(niveles[pr], capacidad[pr], 0)})",
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True)

    st.markdown("##### Lo que no se vendió, y por qué")
    filas = []
    for pr, valores in causas.items():
        unidad = "m³" if pr == "gnc" else "L"
        total = sum(valores)
        fila = {"Producto": nombres[pr]}
        for (causa, _), v in zip(CAUSAS, valores):
            fila[causa] = "—" if v <= 0 else f"{ent(v)} {unidad}"
        fila["Total"] = f"{ent(total)} {unidad}"
        fila["Venta perdida"] = _pesos(total * eco.margen_de(pr))
        filas.append(fila)
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    st.caption(
        " · ".join(f"**{c}**: {d}" for c, d in CAUSAS)
        + ". La venta perdida = lo que no se vendió × el margen por litro (por m³ el GNC), heredado sin fuente "
        "(ECO-01/03): es un **costo de oportunidad** y se informa aparte, no se resta del margen. El GNC va en m³ "
        "y nunca se suma con los litros."
    )
    _comprobacion([
        "Total de cada producto = falta de stock + se cansó de esperar + cola llena + GNC cortado: es todo lo "
        "que pidieron los clientes que se fueron sin cargar.",
        "Un tanque está **vacío** cuando no alcanza ni para la carga más chica de su producto; 'veces que quedó "
        "vacío' cuenta cada vez que entra en ese estado y el tiempo vacío suma lo que dura cada una.",
        "Puede haber clientes sin cargar por falta de stock aunque el tanque nunca quede vacío: alcanzaba para "
        "una carga chica pero no para la de ese cliente.",
    ])


# =============================================================================
# Indicadores
# =============================================================================
SECCIONES = (
    "Resumen",
    "Colas y esperas",
    "Clientes",
    "Playeros y surtidores",
    "Inventario",
    "Detalle completo",
)


def _diagnostico(r: ResultadoReplica, p: ParametrosSimulacion, modo: str) -> list[tuple[str, str]]:
    """Qué hay que mirar: (nivel, texto). Los clientes en enteros."""
    t = _tot(r)
    por_espera = t["perdidos_espera"] + t["perdidos_cola_llena"]
    sin_stock = t["perdidos_sin_combustible"]
    lista: list[tuple[str, str]] = []
    if sin_stock + por_espera == 0:
        lista.append(("success", "No se perdió ningún cliente por falta de combustible ni por la cola."))
    if sin_stock > por_espera * 1.5 and sin_stock > 0:
        lista.append((
            "error",
            f"Se perdieron {ent(sin_stock)} clientes por **falta de combustible** y {ent(por_espera)} "
            f"por la cola: el cuello de botella está en el abastecimiento, no en la atención.",
        ))
    elif por_espera > sin_stock * 1.5 and por_espera > 0:
        lista.append((
            "warning",
            f"Se perdieron {ent(por_espera)} clientes por **la cola** y {ent(sin_stock)} por falta de "
            f"combustible: el cuello de botella es la atención (playeros en el pico).",
        ))
    if r.util_surtidores < 0.5 and r.espera_pico > 1.5:
        lista.append((
            "info",
            f"Ojo con el promedio: las caras están ocupadas el {dec(100 * r.util_surtidores, 0)} % del "
            f"tiempo y los playeros el {dec(100 * r.util_playeros, 0)} %, pero en la hora pico se espera "
            f"{dec(r.espera_pico)} min.",
        ))
    if modo == "real" and r.cola_surtidor < 0.1:
        lista.append((
            "info",
            "Con datos reales (sin azar) los clientes llegan a intervalos exactos y casi no se forman "
            "colas. Para ver colas, usá *Editar simulación* (por ejemplo, el doble de demanda en la hora pico).",
        ))
    return lista


def _tarjetas(filas: list[tuple[str, str, str]]) -> None:
    columnas = st.columns(len(filas))
    for col, (titulo, valor, nota) in zip(columnas, filas):
        col.metric(titulo, valor, border=True)
        col.caption(nota)


def _comprobacion(lineas: list[str]) -> None:
    with st.expander("¿Cómo se comprueba?"):
        for linea in lineas:
            st.markdown(f"- {linea}")


def _tabla_detalle(p: ParametrosSimulacion, r: ResultadoReplica, periodo: Periodo) -> pd.DataFrame:
    """Todos los indicadores, ordenados por tema, cada uno con su cuenta."""
    t = _tot(r)
    dias = max(r.dias_medidos, 1)
    nombres = _nombres(p)
    perdidos = (
        t["perdidos_espera"] + t["perdidos_cola_llena"] + t["perdidos_sin_combustible"] + t["perdidos_corte_gnc"]
    )
    filas: list[tuple[str, str, str, str, str]] = [
        ("Clientes", "Llegaron", ent(t["llegadas"]), "clientes", f"suma de los clientes de cada uno de los {dias} días"),
        ("Clientes", "Atendidos", ent(t["atendidos"]), "clientes", f"{pct(t['atendidos'], t['llegadas'])} de los que llegaron"),
        ("Clientes", "Perdidos", ent(perdidos), "clientes", "espera + cola llena + sin combustible + corte de GNC"),
        ("Clientes", "  por esperar demasiado", ent(t["perdidos_espera"]), "clientes", "superaron su paciencia en la cola"),
        ("Clientes", "  porque la cola estaba llena", ent(t["perdidos_cola_llena"]), "clientes", "no había lugar en la zona (3 por cara)"),
        ("Clientes", "  por falta de combustible", ent(t["perdidos_sin_combustible"]), "clientes", "el tanque de su producto estaba vacío"),
        ("Clientes", "  por el corte de GNC", ent(t["perdidos_corte_gnc"]), "clientes", "no migraron a nafta"),
        ("Clientes", "Pasaron de GNC a Súper", ent(t["migrados_gnc"]), "clientes", "durante un corte; se atienden como nafta"),
        ("Clientes", "Compraron en el minimarket", ent(t["compras"]), "clientes", f"{pct(t['compras'], t['atendidos'])} de los atendidos"),
        ("Clientes", "Litros vendidos por día", ent(r.litros_vendidos_dia - r.m3_gnc_vendidos_dia), "L/día", "nafta y diésel vendidos ÷ días medidos"),
        ("Clientes", "GNC vendido por día", ent(r.m3_gnc_vendidos_dia), "m³/día", "m³ vendidos ÷ días medidos"),
        ("Colas y esperas", "Espera promedio hasta ser atendido", dec(r.espera_surtidor), "min", "promedio de todos los clientes atendidos"),
        ("Colas y esperas", f"Espera en la hora pico ({r.hora_pico:02d} h)", dec(r.espera_pico), "min", "promedio de esa hora en todos los días"),
        ("Colas y esperas", "Espera máxima", dec(r.max_espera_surtidor), "min", "el cliente que más esperó"),
        ("Colas y esperas", "Autos en cola (promedio)", dec(r.cola_surtidor, 2), "autos", "promedio en el tiempo (área bajo la curva ÷ tiempo)"),
        ("Colas y esperas", "Autos en cola (máximo)", ent(r.max_cola_surtidor), "autos", "el momento de más cola"),
        ("Playeros y surtidores", "Utilización de los playeros", dec(100 * r.util_playeros), "%", "playeros ocupados ÷ playeros en turno, promedio en el tiempo"),
        ("Playeros y surtidores", "Utilización de las caras", dec(100 * r.util_surtidores), "%", "caras ocupadas ÷ 12, promedio en el tiempo"),
    ]
    for g, u in zip(p.grupos, r.util_por_grupo):
        filas.append(("Playeros y surtidores", f"  caras de la zona {g.id} ({g.nombre})", dec(100 * u), "%", f"{g.caras} caras"))
    filas.append(("Playeros y surtidores", "Utilización de los compresores de GNC", dec(100 * r.util_compresores), "%", "cargas GNC en curso ÷ compresores"))
    for pr, d in r.dias_quiebre_total:
        if pr == "gnc":
            continue
        filas.append(("Inventario", f"Días con quiebre de {nombres[pr]}", f"{ent(d)} de {ent(dias)}", "días", "días con algún cliente sin cargar por falta de stock en ese tanque"))
    for pr, fr in r.tiempo_sin_stock:
        filas.append(("Inventario", f"Tiempo sin combustible de {nombres[pr]}", f"{dec(100 * fr)} % ({ent(fr * dias * 24)} h)", "del tiempo", "tiempo con ese tanque sin poder cargar ni al cliente más chico ÷ tiempo total"))
    filas.append(("Inventario", "Estación sin ningún combustible", dec(r.porcentaje_tiempo_sin_combustible), "% del tiempo", "los 4 tanques vacíos a la vez"))
    for pr, n in r.pedidos_total:
        filas.append(("Inventario", f"Camiones pedidos de {nombres[pr]}", ent(n), "camiones", "uno cada vez que el inventario cae al punto de pedido"))
    return pd.DataFrame(filas, columns=["Tema", "Indicador", "Valor", "Unidad", "Cómo se calcula"])


def pestania_indicadores(
    p: ParametrosSimulacion, resultado: ResultadoEscenario, traza: Traza, periodo: Periodo, modo: str
) -> None:
    r = resultado.replicas[0]
    t = _tot(r)
    dias = max(r.dias_medidos, 1)
    nombres = _nombres(p)

    st.subheader("Indicadores del período")
    st.caption(
        f"**Promedio de {periodo.titulo.lower()}** — {periodo.texto}. Los clientes se cuentan (números "
        f"enteros); los tiempos y las utilizaciones son promedios. Cada indicador trae su cuenta."
    )
    seccion = st.radio("¿Qué querés saber?", SECCIONES, horizontal=True, key="indicadores_seccion")
    perdidos = (
        t["perdidos_espera"] + t["perdidos_cola_llena"] + t["perdidos_sin_combustible"] + t["perdidos_corte_gnc"]
    )

    if seccion == "Resumen":
        _tarjetas([
            ("Clientes atendidos", ent(t["atendidos"]),
             f"de {ent(t['llegadas'])} que llegaron ({pct(t['atendidos'], t['llegadas'])})"),
            ("Clientes perdidos", ent(perdidos), f"{pct(perdidos, t['llegadas'])} de los que llegaron"),
            ("Espera promedio", f"{dec(r.espera_surtidor)} min",
             f"en la hora pico ({r.hora_pico:02d} h): {dec(r.espera_pico)} min"),
            ("Litros vendidos por día", f"{ent(r.litros_vendidos_dia - r.m3_gnc_vendidos_dia)} L",
             f"+ {ent(r.m3_gnc_vendidos_dia)} m³ de GNC por día"),
        ])
        for nivel, texto in _diagnostico(r, p, modo):
            getattr(st, nivel)(texto)
        _comprobacion([
            f"Llegaron {ent(t['llegadas'])} clientes en {dias} días (≈ {ent(t['llegadas'] / dias)} por día).",
            f"Atendidos = llegaron − perdidos − los que quedaron adentro: {ent(t['llegadas'])} − "
            f"{ent(perdidos)} = {ent(t['llegadas'] - perdidos)} (atendidos: {ent(t['atendidos'])}).",
            f"Litros por día = litros de los 4 combustibles líquidos ÷ {dias} días.",
        ])

    elif seccion == "Colas y esperas":
        _tarjetas([
            ("Espera promedio", f"{dec(r.espera_surtidor)} min", "hasta empezar a ser atendido"),
            (f"Espera en la hora pico ({r.hora_pico:02d} h)", f"{dec(r.espera_pico)} min", "promedio de esa hora"),
            ("Espera máxima", f"{dec(r.max_espera_surtidor)} min", "el cliente que más esperó"),
            ("Autos en cola", dec(r.cola_surtidor, 2), f"promedio; máximo {ent(r.max_cola_surtidor)} autos"),
        ])
        for nivel, texto in _diagnostico(r, p, modo):
            if nivel == "info":
                st.info(texto)
        st.markdown("##### Por zona de surtidores")
        st.dataframe(
            pd.DataFrame({
                "Zona": [f"{g.id} · {g.nombre}" for g in p.grupos],
                "Caras": [g.caras for g in p.grupos],
                "Lugares de cola": [p.capacidad_de(g.id) for g in p.grupos],
                "Espera promedio (min)": [dec(x) for x in r.espera_por_grupo],
                "Autos en cola (promedio)": [dec(x, 2) for x in r.cola_por_grupo],
            }),
            hide_index=True,
        )
        st.plotly_chart(graficos.grafico_perfil_horario(traza, dias), key="g_ind_perfil")
        _comprobacion([
            "Espera = minutos entre que el auto llega y empieza a ser atendido, promediada sobre todos los clientes.",
            "La hora pico es la hora del día con mayor espera promedio; las barras son los clientes por hora.",
        ])

    elif seccion == "Clientes":
        st.markdown("##### Qué pasó con los clientes")
        st.dataframe(
            pd.DataFrame({
                "": ["Llegaron", "Atendidos", "Se fueron por esperar demasiado", "Se fueron porque la cola estaba llena",
                     "Se fueron por falta de combustible", "Se fueron por el corte de GNC",
                     "Pasaron de GNC a Súper (no se pierden)", "Compraron en el minimarket"],
                "Clientes": [ent(t["llegadas"]), ent(t["atendidos"]), ent(t["perdidos_espera"]),
                             ent(t["perdidos_cola_llena"]), ent(t["perdidos_sin_combustible"]),
                             ent(t["perdidos_corte_gnc"]), ent(t["migrados_gnc"]), ent(t["compras"])],
                "% de los que llegaron": [
                    "100 %", pct(t["atendidos"], t["llegadas"]), pct(t["perdidos_espera"], t["llegadas"]),
                    pct(t["perdidos_cola_llena"], t["llegadas"]), pct(t["perdidos_sin_combustible"], t["llegadas"]),
                    pct(t["perdidos_corte_gnc"], t["llegadas"]), pct(t["migrados_gnc"], t["llegadas"]),
                    pct(t["compras"], t["llegadas"])],
            }),
            hide_index=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Por zona")
            st.dataframe(
                pd.DataFrame({
                    "Zona": [f"{g.id} · {g.nombre}" for g in p.grupos],
                    "Llegaron": [ent(z[1]) for z in r.totales_zona],
                    "Atendidos": [ent(z[2]) for z in r.totales_zona],
                    "Perdidos": [ent(sum(z[3:7])) for z in r.totales_zona],
                }),
                hide_index=True,
            )
        with c2:
            st.markdown("##### Por producto")
            st.dataframe(
                pd.DataFrame({
                    "Producto": [nombres[x[0]] for x in r.totales_producto],
                    "Atendidos": [ent(x[2]) for x in r.totales_producto],
                    "Vendido": [f"{ent(x[3])} {'m³' if x[0] == 'gnc' else 'L'}" for x in r.totales_producto],
                    "Por día": [f"{ent(x[3] / dias)} {'m³' if x[0] == 'gnc' else 'L'}" for x in r.totales_producto],
                }),
                hide_index=True,
            )
        _comprobacion([
            f"Llegaron {ent(t['llegadas'])} = atendidos {ent(t['atendidos'])} + perdidos {ent(perdidos)} "
            f"+ los que seguían adentro al terminar ({ent(t['llegadas'] - t['atendidos'] - perdidos)}).",
            "Los clientes que pasaron de GNC a Súper se cuentan como Súper (llegaron a la zona A).",
            "El GNC se mide en m³: nunca se suma con los litros.",
        ])

    elif seccion == "Playeros y surtidores":
        _tarjetas([
            ("Utilización de los playeros", f"{dec(100 * r.util_playeros)} %", "ocupados ÷ en turno"),
            ("Utilización de las caras", f"{dec(100 * r.util_surtidores)} %", "caras ocupadas ÷ 12"),
            ("Compresores de GNC", f"{dec(100 * r.util_compresores)} %", "cargas en curso ÷ compresores"),
        ])
        st.dataframe(
            pd.DataFrame({
                "Zona": [f"{g.id} · {g.nombre}" for g in p.grupos],
                "Caras": [g.caras for g in p.grupos],
                "Utilización de las caras": [f"{dec(100 * u)} %" for u in r.util_por_grupo],
            }),
            hide_index=True,
        )
        _comprobacion([
            "Utilización = promedio en el tiempo de (ocupados ÷ disponibles); un valor bajo es un promedio de "
            "24 horas: en la hora pico la dotación puede estar al límite.",
            f"Playeros por turno (noche · mañana · tarde): {' · '.join(str(x) for x in p.playeros_por_turno)}.",
        ])

    elif seccion == "Inventario":
        bloque_quiebres(p, r, st.session_state.get("parametros_eco") or ParametrosEconomicos())
        _tarjetas([
            ("Estación sin ningún combustible", f"{dec(r.porcentaje_tiempo_sin_combustible)} %",
             "los 4 tanques vacíos a la vez"),
            ("Días con algún cliente sin cargar", f"{ent(t['dias_con_quiebre'])} de {ent(dias)}",
             "por falta de stock en algún tanque"),
        ])

    else:
        detalle = _tabla_detalle(p, r, periodo)
        st.dataframe(detalle, hide_index=True, height=36 * (len(detalle) + 1) + 3)


# =============================================================================
# Demanda verificable (sin Monte Carlo)
# =============================================================================
def _fecha(p: ParametrosSimulacion, dia: int) -> date:
    return date(ANO_REFERENCIA, *p.fecha_inicio) + timedelta(days=dia - 1)


def pestania_demanda(
    p: ParametrosSimulacion, resultado: ResultadoEscenario, traza: Traza, periodo: Periodo
) -> None:
    r = resultado.replicas[0]
    t = _tot(r)
    dias = max(r.dias_medidos, 1)
    nombres = _nombres(p)

    st.subheader("Demanda: cuántos clientes llegan y cuándo")
    st.markdown(
        "La demanda de entrada son **litros por mes**; los clientes por día **se derivan**. Todo lo de esta "
        "pestaña se puede comprobar con una cuenta: no hay sorteos en la simulación con datos reales."
    )

    st.markdown("##### 1. De los litros por mes a los clientes por día")
    litros_dia = p.litros_del_dia(1)
    liquidos = litros_dia / p.litros_medios_por_cliente
    total_dia = p.autos_por_dia_fecha(1)
    st.dataframe(
        pd.DataFrame({
            "Paso": ["Litros por mes", f"Litros del día 1 ({_fecha(p, 1).strftime('%d/%m')})",
                     "Clientes de nafta y diésel", "Clientes de GNC", "Clientes del día"],
            "Cuenta": [
                "dato (DEM-01)",
                f"{ent(p.litros_mes)} L ÷ {ent(_dias_del_mes_de(p))} días × estacionalidad × tipo de día",
                f"{ent(litros_dia)} L ÷ {dec(p.litros_medios_por_cliente)} L por cliente",
                f"{dec(100 * p.pct_gnc, 0)} % de las llegadas",
                f"{ent(liquidos)} ÷ (1 − {dec(p.pct_gnc, 2)})",
            ],
            "Resultado": [f"{ent(p.litros_mes)} L", f"{ent(litros_dia)} L", ent(liquidos),
                          ent(total_dia - liquidos), ent(total_dia)],
        }),
        hide_index=True,
    )
    st.caption(
        f"Estacionalidad: {'neutra (todos los meses pesan igual)' if len(set(p.estacionalidad.indices)) == 1 else 'con índices por mes'}; "
        f"fin de semana ×{dec(p.factor_fin_de_semana, 2)}, normalizado para conservar los litros del mes."
    )

    st.markdown("##### 2. Cuándo llegan: el perfil del día")
    fr = p.perfil.fracciones
    esperados_hora = [p.autos_por_dia * f for f in fr]
    sim_hora = [x / dias for x in traza.llegadas_por_hora]
    st.dataframe(
        pd.DataFrame({
            "Hora": [f"{h:02d}–{(h + 1) % 24:02d}" for h in range(24)],
            "Peso del perfil": [dec(x, 1) for x in p.perfil.factores],
            "% de los clientes del día": [f"{dec(100 * f)} %" for f in fr],
            "Clientes esperados por día": [dec(x) for x in esperados_hora],
            "Clientes simulados por día": [dec(x) for x in sim_hora],
            "Espera promedio (min)": [dec(x) for x in traza.espera_por_hora],
        }),
        hide_index=True, height=36 * 25 + 3,
    )
    st.plotly_chart(graficos.grafico_perfil_horario(traza, dias), key="g_dem_perfil")
    st.caption(
        f"Verificación: la suma de las 24 horas es {ent(sum(traza.llegadas_por_hora))} clientes = los "
        f"{ent(t['llegadas'])} que llegaron en {dias} días."
    )

    st.markdown("##### 3. Qué producto carga cada cliente")
    pesos = dict(zip((pr.id for pr in p.productos), p.pesos_llegada()))
    por_producto = {x[0]: x for x in r.totales_producto}
    st.dataframe(
        pd.DataFrame({
            "Producto": [pr.nombre for pr in p.productos],
            "% de los litros": ["—" if pr.es_gnc else f"{dec(100 * pr.pct_litros)} %" for pr in p.productos],
            "Carga media por cliente": [f"{dec(pr.carga_media)} {'m³' if pr.es_gnc else 'L'}" for pr in p.productos],
            "% de los clientes": [f"{dec(100 * pesos[pr.id], 2)} %" for pr in p.productos],
            "Clientes esperados": [ent(pesos[pr.id] * t["llegadas"]) for pr in p.productos],
            "Clientes simulados": [ent(por_producto[pr.id][1]) for pr in p.productos],
        }),
        hide_index=True,
    )
    st.caption(
        "% de los clientes = (% de los litros ÷ carga media), normalizado; el GNC entra como "
        f"{dec(100 * p.pct_gnc, 0)} % de las llegadas. Sin azar, cada producto aparece en las proporciones exactas "
        "(las pequeñas diferencias son los clientes de GNC que pasaron a Súper en un corte)."
    )

    st.markdown("##### 4. Día a día")
    filas = []
    for x in traza.dias:
        f = _fecha(p, x.dia)
        filas.append({
            "Día": x.dia,
            "Fecha": f"{DIAS_SEMANA[f.weekday()]} {f.strftime('%d/%m')}",
            "Clientes del día": x.autos_sorteados,
            "Llegaron": x.autos_llegados,
            "Atendidos": x.atendidos,
            "Perdidos": x.perdidos_cola + x.perdidos_sin_combustible,
            "Litros vendidos": ent(x.litros_vendidos),
            "Quiebre": "sí" if x.hubo_quiebre else "",
            "Corte de GNC": f"{ent(x.gnc_corte_min / 60)} h" if x.gnc_corte_min else "",
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, height=min(36 * len(filas) + 3, 420))
    st.plotly_chart(graficos.grafico_demanda_diaria(traza), key="g_dem_dias")
    st.caption(
        f"Verificación: la suma de 'Llegaron' es {ent(sum(x.autos_llegados for x in traza.dias))} = los {ent(t['llegadas'])} "
        f"de los indicadores. Periodo: {periodo.texto}."
    )


def _dias_del_mes_de(p: ParametrosSimulacion) -> int:
    from sim.config import dias_del_mes

    return dias_del_mes(p.fecha_inicio[0])
