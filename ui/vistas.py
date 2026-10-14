"""Vistas de resultados del rediseño v3: Indicadores y Demanda verificables.

Todo número que se muestra se puede **comprobar**: al lado de cada indicador está la cuenta con los datos de
la corrida. Los clientes se cuentan (enteros); sólo los tiempos, las utilizaciones y los porcentajes llevan
decimales. Con datos reales (sin azar) no aparece nada de Monte Carlo: eso va en la pestaña *Qué se sorteó*,
que existe sólo si la simulación fue editada.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from types import SimpleNamespace

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


def _md(texto: str) -> str:
    """Escapa el $ para Markdown: dos $ en una línea se leen como una fórmula LaTeX (regla de CLAUDE.md)."""
    return texto.replace("$", r"\$")


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


#: Nombre para mostrar de cada temporada del calendario (DEM-14).
NOMBRE_TEMPORADA = {
    "verano": "Verano (dic–feb)",
    "vacaciones_invierno": "Vacaciones de invierno de Mendoza",
    "invierno": "Resto del invierno (jun–ago)",
    "": "Otoño y primavera",
}
#: Estación del año de cada mes (CAL-08), para el filtro de fechas.
ESTACION_DEL_MES = {12: "Verano", 1: "Verano", 2: "Verano", 3: "Otoño", 4: "Otoño", 5: "Otoño",
                    6: "Invierno", 7: "Invierno", 8: "Invierno", 9: "Primavera", 10: "Primavera", 11: "Primavera"}
MESES_ES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
            "noviembre", "diciembre")
#: Hasta cuántos días la corrida es "corta" (sin filtros) y desde cuántos es "larga" (con filtro de período).
DIAS_CORTA = 7
DIAS_LARGA = 31


def _rango_por_temporada(p: ParametrosSimulacion) -> pd.DataFrame:
    """Clientes por día mínimo y máximo de cada temporada del calendario, en todo el año (sin simular)."""
    anio = replace(p, fecha_inicio=(1, 1), dias=365, dia_animado=1)
    inicio = _fecha(p, 1)
    fin = _fecha(p, p.dias)
    grupos: dict[str, list[tuple[float, date]]] = {k: [] for k in NOMBRE_TEMPORADA}
    for d in range(1, 366):
        f = _fecha(anio, d)
        grupos[anio.temporada_del_calendario(f)].append((anio.autos_por_dia_fecha(d), f))
    filas = []
    for clave, nombre in NOMBRE_TEMPORADA.items():
        valores = grupos[clave]
        minimo, f_min = min(valores)
        maximo, f_max = max(valores)
        en_periodo = any(
            anio.temporada_del_calendario(inicio + timedelta(days=k)) == clave for k in range((fin - inicio).days + 1)
        )
        filas.append({
            "Temporada": nombre,
            "Factor del calendario": f"× {dec(dict(p.calendario_demanda).get(clave, 1.0), 2)}",
            "Clientes por día: mínimo": f"{ent(minimo)} ({f_min.day}/{f_min.month})",
            "máximo": f"{ent(maximo)} ({f_max.day}/{f_max.month})",
            "¿En el período simulado?": "sí" if en_periodo else "",
        })
    return pd.DataFrame(filas)


def _filtro_de_fechas(p: ParametrosSimulacion, clave: str) -> list[int]:
    """Días (1 = el primero de la corrida) elegidos con el filtro. Corrida corta: todos, sin filtros.
    Hasta un mes: sólo el selector de fechas. Más larga: además, un filtro por estación, mes o vacaciones."""
    todos = list(range(1, p.dias + 1))
    if p.dias <= DIAS_CORTA:
        return todos
    fechas = {d: _fecha(p, d) for d in todos}
    candidatos = todos
    c1, c2 = st.columns(2)
    if p.dias > DIAS_LARGA:
        opciones: dict[str, list[int]] = {"Todo el período": todos}
        for nombre in ("Verano", "Otoño", "Invierno", "Primavera"):
            dias = [d for d in todos if ESTACION_DEL_MES[fechas[d].month] == nombre]
            if dias and len(dias) < len(todos):
                opciones[nombre] = dias
        vacaciones = [d for d in todos if p.temporada_del_calendario(fechas[d]) == "vacaciones_invierno"]
        if vacaciones:
            opciones["Vacaciones de invierno"] = vacaciones
        meses = sorted({(fechas[d].year, fechas[d].month) for d in todos})
        if len(meses) > 1:
            for anio, mes in meses:
                opciones[MESES_ES[mes - 1].capitalize()] = [
                    d for d in todos if (fechas[d].year, fechas[d].month) == (anio, mes)
                ]
        elegido = c1.selectbox("Ver", list(opciones), key=f"{clave}_periodo",
                               help="Estación, mes o vacaciones de invierno dentro del período simulado.")
        candidatos = opciones[elegido]
    else:
        elegido = "todo"
    desde, hasta = fechas[candidatos[0]], fechas[candidatos[-1]]
    rango = c2.date_input(
        "Fechas", value=(desde, hasta), min_value=desde, max_value=hasta, format="DD/MM/YYYY",
        key=f"{clave}_fechas_{elegido}",
    )
    if isinstance(rango, (tuple, list)) and len(rango) == 2:
        a, b = rango
    else:
        a = b = rango[0] if isinstance(rango, (tuple, list)) and rango else desde
    elegidos = [d for d in candidatos if a <= fechas[d] <= b]
    return elegidos or candidatos


def pestania_demanda(
    p: ParametrosSimulacion, resultado: ResultadoEscenario, traza: Traza, periodo: Periodo
) -> None:
    r = resultado.replicas[0]
    t = _tot(r)
    nombres = _nombres(p)

    st.subheader("Demanda: cuántos clientes llegan y cuándo")
    st.markdown(
        "La demanda de entrada son **litros por mes**; los clientes por día **se derivan**. Todo lo de esta "
        "pestaña se puede comprobar con una cuenta: no hay sorteos en la simulación con datos reales."
    )

    st.markdown("##### 1. De los litros por mes a los clientes por día")
    f1 = _fecha(p, 1)
    litros_dia = p.litros_del_dia(1)
    liquidos = litros_dia / p.litros_medios_por_cliente
    total_dia = p.autos_por_dia_fecha(1)
    factor_cal = p.factor_calendario(f1)
    st.dataframe(
        pd.DataFrame({
            "Paso": ["Litros por mes", f"Litros del día 1 ({f1.strftime('%d/%m')})",
                     "Clientes de nafta y diésel", "Clientes de GNC", "Clientes del día"],
            "Cuenta": [
                "dato (DEM-01)",
                f"{ent(p.litros_mes)} L ÷ {ent(_dias_del_mes_de(p))} días × tipo de día"
                + (f" × calendario {dec(factor_cal, 2)} ({NOMBRE_TEMPORADA[p.temporada_del_calendario(f1)].lower()})"
                   if p.calendario_demanda else "")
                + (f" × índice de {MESES_ES[f1.month - 1]} "
                   f"{dec(p.estacionalidad.indice_mes(f1.month) / p.estacionalidad.promedio, 3)} (serie real)"
                   if len(set(p.estacionalidad.indices)) > 1 else ""),
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
        f"En un mes de 31 días sin calendario: {ent(p.litros_mes)} L ÷ 31 = {ent(p.litros_mes / 31)} L por día ÷ "
        f"{dec(p.litros_medios_por_cliente)} L ÷ (1 − {dec(p.pct_gnc, 2)}) ≈ "
        f"**{ent(p.litros_mes / 31 / p.litros_medios_por_cliente / (1 - p.pct_gnc))} clientes por día**. "
        f"Cada día se corrige por el tipo de día (fin de semana × {dec(p.factor_fin_de_semana, 2)}, normalizado "
        f"para conservar los litros del mes) y por el calendario de temporadas."
    )
    if p.calendario_demanda:
        st.markdown("**Rango de clientes por día en cada temporada** (sale del calendario, no del azar)")
        st.dataframe(_rango_por_temporada(p), hide_index=True)
        st.caption(
            "Verano más alto por el turismo; vacaciones de invierno de Mendoza (6–17 de julio, DGE 2026) más alto; "
            "el resto del invierno un poco más bajo porque la gente sale menos. Los factores son supuestos "
            "moderados (la mitad del desvío del proxy turístico, nota 08) y se editan en el menú. El mínimo y el "
            "máximo de cada temporada son un día hábil y un fin de semana. No se renormaliza al año: el total anual "
            "queda ≈ 0,4 % arriba de 12 × 270.000 L."
        )
    elif len(set(p.estacionalidad.indices)) > 1:
        st.caption("Forma de la demanda: los **índices mensuales de la serie real** de Shell Mendoza (elegido en el "
                   "menú): cada mes × su índice, que promedian 1, así que el total del año no cambia. Están en la pestaña "
                   "📈 Pronóstico.")
    else:
        st.caption("Calendario de temporadas apagado en el menú: todos los meses pesan igual.")

    st.markdown("##### Elegí qué días mirar (vale para el perfil del día y el día a día)")
    if p.dias <= DIAS_CORTA:
        st.caption(f"Son {p.dias} días: se muestran todos.")
    elegidos = _filtro_de_fechas(p, "dem")
    n = len(elegidos)
    llegadas_h = [sum(traza.llegadas_dia_hora[d - 1][h] for d in elegidos if d - 1 < len(traza.llegadas_dia_hora))
                  for h in range(24)]
    espera_h = []
    for h in range(24):
        suma = sum(traza.espera_dia_hora[d - 1][h][0] for d in elegidos if d - 1 < len(traza.espera_dia_hora))
        cant = sum(traza.espera_dia_hora[d - 1][h][1] for d in elegidos if d - 1 < len(traza.espera_dia_hora))
        espera_h.append(suma / cant if cant else 0.0)

    st.markdown("##### 2. Cuándo llegan: el perfil del día")
    fr = p.perfil.fracciones
    esperado_dia = sum(p.autos_por_dia_fecha(d) for d in elegidos) / max(n, 1)
    st.dataframe(
        pd.DataFrame({
            "Hora": [f"{h:02d}–{(h + 1) % 24:02d}" for h in range(24)],
            "Peso del perfil": [dec(x, 1) for x in p.perfil.factores],
            "% de los clientes del día": [f"{dec(100 * f)} %" for f in fr],
            "Clientes esperados por día": [dec(esperado_dia * f) for f in fr],
            "Clientes simulados por día": [dec(x / max(n, 1)) for x in llegadas_h],
            "Espera promedio (min)": [dec(x) for x in espera_h],
        }),
        hide_index=True, height=36 * 25 + 3,
    )
    perfil = SimpleNamespace(llegadas_por_hora=llegadas_h, espera_por_hora=espera_h)
    st.plotly_chart(graficos.grafico_perfil_horario(perfil, n), key="g_dem_perfil")
    st.caption(
        f"Verificación: la suma de las 24 horas es {ent(sum(llegadas_h))} clientes = los que llegaron en los "
        f"{n} días elegidos ({ent(sum(x.autos_llegados for x in traza.dias if x.dia in set(elegidos)))})."
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
        "(las pequeñas diferencias son los clientes de GNC que pasaron a Súper en un corte). Es todo el período."
    )

    st.markdown("##### 4. Día a día")
    elegidos_set = set(elegidos)
    dias_vista = [x for x in traza.dias if x.dia in elegidos_set]
    filas = []
    for x in dias_vista:
        f = _fecha(p, x.dia)
        filas.append({
            "Día": x.dia,
            "Fecha": f"{DIAS_SEMANA[f.weekday()]} {f.strftime('%d/%m')}",
            "Temporada": NOMBRE_TEMPORADA[p.temporada_del_calendario(f)] if p.calendario_demanda else "",
            "Clientes del día": x.autos_sorteados,
            "Llegaron": x.autos_llegados,
            "Atendidos": x.atendidos,
            "Perdidos": x.perdidos_cola + x.perdidos_sin_combustible,
            "Litros vendidos": ent(x.litros_vendidos),
            "Quiebre": "sí" if x.hubo_quiebre else "",
            "Corte de GNC": f"{ent(x.gnc_corte_min / 60)} h" if x.gnc_corte_min else "",
        })
    tabla = pd.DataFrame(filas)
    if not p.calendario_demanda:
        tabla = tabla.drop(columns=["Temporada"])
    st.dataframe(tabla, hide_index=True, height=min(36 * len(filas) + 3, 420))
    st.plotly_chart(graficos.grafico_demanda_diaria(SimpleNamespace(dias=dias_vista)), key="g_dem_dias")
    st.caption(
        f"Verificación: la suma de 'Llegaron' en los días elegidos es {ent(sum(x.autos_llegados for x in dias_vista))}; "
        f"en todo el período, {ent(sum(x.autos_llegados for x in traza.dias))} = los {ent(t['llegadas'])} de los "
        f"indicadores. Período: {periodo.texto}."
    )


def _dias_del_mes_de(p: ParametrosSimulacion) -> int:
    from sim.config import dias_del_mes

    return dias_del_mes(p.fecha_inicio[0])


# =============================================================================
# Eventos aleatorios (parte 4): qué pasó, cuándo y qué le hizo a la estación
# =============================================================================
def _cuando(p: ParametrosSimulacion, minuto: float) -> str:
    """'mié 7/1 15:02' a partir del minuto de la corrida."""
    instante = datetime(ANO_REFERENCIA, *p.fecha_inicio) + timedelta(minutes=minuto)
    return f"{DIAS_SEMANA[instante.weekday()][:3]} {instante.day}/{instante.month} {instante:%H:%M}"


def _duracion(e) -> str:
    if e.id == "EVT-09":
        return "desde ese día"
    horas = (e.fin - e.inicio) / 60.0
    if e.id in ("EVT-02", "EVT-04", "EVT-10", "EVT-13"):
        dias = int(e.valor) if e.id in ("EVT-02", "EVT-04") else round(horas / 24)
        return f"{dias} día{'s' if dias != 1 else ''}"
    return f"{dec(horas)} h" if horas < 48 else f"{dec(horas / 24)} días"


def pestania_eventos(p: ParametrosSimulacion, r: ResultadoReplica, eco: ParametrosEconomicos) -> None:
    """La pestaña ⚡ Eventos: cómo se sortearon, la tabla de los que ocurrieron y lo que costaron."""
    from sim.eventos import CATALOGO, POR_ID, costo_de_eventos, horas_extra, texto_frecuencia

    ev = p.eventos
    inicio = date(ANO_REFERENCIA, *p.fecha_inicio)
    st.subheader("Eventos aleatorios del período")
    st.info(
        f"Prendidos en el menú: **{len(ev.activos)}** de {len(CATALOGO)}. Se sortearon con la semilla **{ev.semilla}**"
        + (f" y la frecuencia × {dec(ev.frecuencia, 1)}" if ev.frecuencia != 1 else "")
        + ": cada día, y para cada evento, se sortea si ocurre con su probabilidad por día del Registro (EVT-01…14, "
        "supuestos del grupo). **Con la misma semilla salen siempre los mismos eventos.** "
        + ("El resto de la simulación sigue con los datos reales, sin azar." if p.determinista else
           "El resto es la simulación editada, con su propia semilla."),
        icon="⚡",
    )
    ocurridos = r.eventos
    costo = costo_de_eventos(ocurridos, p, eco.sueldo_playero_mensual)
    _tarjetas([
        ("Eventos que ocurrieron", ent(len(ocurridos)), f"{len({e.id for e in ocurridos})} tipos distintos"),
        ("Clientes perdidos mientras duraban", ent(sum(e.perdidos for e in ocurridos)),
         "si dos eventos se superponen, el cliente cuenta en los dos"),
        ("Costo de los eventos", _pesos(costo), "horas extra y técnico, en el período (la venta perdida va aparte)"),
    ])
    if not ocurridos:
        st.caption("No ocurrió ninguno de los prendidos. Probá con un período más largo, otra semilla o la frecuencia × 5.")
    else:
        valor_hora = eco.sueldo_playero_mensual / float(_valor_registro("EVT-15"))
        factor_precio = 1.0
        precio_super = dict(eco.precios).get("super", 0.0)
        filas = []
        for e in ocurridos:
            que = "—"
            if e.id in ("EVT-09", "EVT-13"):
                que = f"+{ent(e.extra)} clientes" + (" el día anterior" if e.id == "EVT-09" else "")
                if e.id == "EVT-09":
                    antes = precio_super * factor_precio
                    factor_precio *= 1 + e.valor
                    que += f" · Súper $ {ent(antes)} → $ {ent(precio_super * factor_precio)} (margen igual)"
            elif e.id == "EVT-12":
                que = f"{ent(e.extra)} clientes no pudieron entrar"
            elif e.id == "EVT-10":
                que = f"{ent(e.extra)} L recortados por el cupo"
            elif e.id == "EVT-11":
                que = f"{dec(e.extra, 0)} h de demora"
            elif e.id == "EVT-02":
                al_50, al_100 = horas_extra(e, inicio, p.dias)
                que = (f"{ent(al_50 + al_100)} h extra = "
                       f"{_pesos(valor_hora * (al_50 * 1.5 + al_100 * 2.0))}")
            filas.append({
                "Cuándo": _cuando(p, e.inicio),
                "Evento": POR_ID[e.id].nombre,
                "Duración": _duracion(e),
                "Clientes perdidos mientras duraba": "—" if e.id in ("EVT-02", "EVT-11") else ent(e.perdidos),
                "Qué hizo": que,
                "Detalle": e.detalle[:1].upper() + e.detalle[1:],
            })
        st.markdown("##### Lo que pasó, en orden")
        st.dataframe(pd.DataFrame(filas), hide_index=True, height=min(36 * len(filas) + 3, 460))
    no_salieron = [POR_ID[i] for i in ev.activos if i not in {e.id for e in ocurridos}]
    if no_salieron:
        st.caption("Prendidos que no ocurrieron en este período: " + " · ".join(
            f"{t.nombre} ({texto_frecuencia(t.id)})" for t in no_salieron) + ".")
    _comprobacion([
        "Cada evento cuenta los clientes que se fueron **sin cargar mientras duraba** (por espera, cola llena, falta de "
        "stock o corte de GNC). Son parte de los perdidos de Indicadores: no se suman aparte.",
        "Un playero menos = una reserva en el recurso de playeros hasta el cambio de turno (06, 14 o 22 h), igual que los "
        "turnos; la estación parada (corte de luz, asalto) reserva todos los playeros y compresores.",
        _md(f"Horas extra (licencia cubierta): 8 h por día de licencia dentro del período × valor de la hora "
        f"({_pesos(eco.sueldo_playero_mensual)} ÷ {ent(_valor_registro('EVT-15'))} h = {_pesos(eco.sueldo_playero_mensual / float(_valor_registro('EVT-15')))}) "
        "× 1,5 (× 2 el domingo; LCT art. 201). Entra en los costos de Economía."),
        "Aumento de precio: el margen por litro queda igual (pedido del grupo), así que no cambia la ganancia; lo que se ve "
        "es la gente que se adelanta a cargar el día anterior.",
        "Frecuencias y duraciones: supuestos del grupo (no hay registros de la estación); detalle en Datos y fuentes (EVT-00…15).",
    ])


def _valor_registro(id_: str):
    from sim.datos import valor

    return valor(id_)


# =============================================================================
# Pronóstico (parte 3): la serie real de Shell en Mendoza y los métodos de la cátedra
# =============================================================================
def pestania_pronostico(p: ParametrosSimulacion) -> None:
    """La pestaña 📈 Pronóstico: la serie real, los métodos, el elegido y cómo entra al simulador."""
    from sim.datos import valor
    from sim.pronostico import METODOS, analizar, serie_registro

    analisis = analizar()
    meses_todos, valores_todos = serie_registro()
    elegido = next(a for a in analisis.ajustes if a.metodo == analisis.elegido)
    st.subheader("Pronóstico de la demanda con la serie real")
    st.info(
        "La serie es **real y oficial**: las ventas mensuales **al público de Shell en Mendoza** (Súper, V-Power, "
        "gasoil G2 y G3), declaradas a la Secretaría de Energía (datos abiertos, PRO-01). **No hay datos por "
        "estación**: es la suma de todas las Shell de la provincia, así que el simulador usa su **forma** (cuánto "
        "pesa cada mes) y la escala a los litros de esta estación (DEM-01).",
        icon="📈",
    )
    primero, n_prueba = valor("PRO-02")
    _tarjetas([
        ("Método elegido", METODOS[analisis.elegido].split(" (")[0], "el de menor RMSE en los meses de prueba"),
        ("Error en la prueba (MAPE)", f"{dec(100 * elegido.errores.mape)} %", f"RMSE {ent(elegido.errores.rmse)} m³"),
        ("Tendencia", f"{dec(100 * analisis.tendencia_mensual, 2)} % por mes",
         "la recta de la serie desestacionalizada ÷ el nivel medio"),
    ])
    st.plotly_chart(graficos.grafico_pronostico(analisis, meses_todos, valores_todos), key="g_pronostico")
    st.caption(
        f"Se ajusta con {MESES_ES[primero[1] - 1]} de {primero[0]} a {MESES_ES[analisis.meses[-n_prueba - 1][1] - 1]} de "
        f"{analisis.meses[-n_prueba - 1][0]} y se prueba en los {n_prueba} meses siguientes (zona gris), que el método "
        "no vio. La pandemia (2020) y el rebote de 2021 quedan afuera del ajuste. La banda es ± z·RMSE (95 %)."
    )

    st.markdown("##### Los cinco métodos en los meses de prueba")
    filas = [{
        "Método": METODOS[a.metodo] + ("  ✅" if a.metodo == analisis.elegido else ""),
        "Parámetros": a.detalle,
        "MAE (m³)": ent(a.errores.mae),
        "MAPE": f"{dec(100 * a.errores.mape)} %",
        "RMSE (m³)": ent(a.errores.rmse),
        "Sesgo (m³)": f"{a.errores.sesgo:+,.0f}".replace(",", "."),
    } for a in analisis.ajustes]
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    st.caption("Sesgo = promedio de (real − pronóstico): negativo quiere decir que el método esperaba más de lo que se "
               "vendió (la serie bajó más de lo previsto).")

    st.markdown("##### Cuánto pesa cada mes")
    st.plotly_chart(graficos.grafico_indices(analisis.indices), key="g_indices")
    verano = sum(analisis.indices[m - 1] for m in (12, 1, 2)) / 3
    st.caption(
        f"En la serie real el verano (dic–feb) pesa {dec(verano, 2)} — casi un mes promedio —, mientras que el "
        f"calendario de temporadas del menú (DEM-14, supuesto) lo sube 6 %. Para simular con la forma real, elegí "
        f"**'Índices de la serie real'** en el desplegable 📅 del menú principal."
    )

    st.markdown("##### Los próximos meses (y la estación escalada)")
    ultimos = analisis.reales[-12:]
    escala = float(valor("DEM-01")) / (sum(ultimos) / len(ultimos) * 1000.0)
    filas = [{
        "Mes": f"{MESES_ES[m - 1]} {a}",
        "Shell Mendoza (m³)": ent(f),
        "Intervalo 95 % (m³)": f"{ent(lo)} – {ent(hi)}",
        "La estación (L)": ent(f * 1000 * escala),
    } for (a, m), f, (lo, hi) in zip(analisis.futuros, analisis.pronostico, analisis.intervalo)]
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    _comprobacion([
        "Errores en los meses de prueba, con e = real − pronóstico: MAE = Σ|e| ÷ n · MAPE = Σ|e ÷ real| ÷ n · "
        "RMSE = √(Σe² ÷ n) · sesgo = Σe ÷ n. Se elige el de menor RMSE.",
        "Validación con el práctico de la cátedra (control 39 de `verificar.py`): Cable Televisora da MAE = 8,92 y "
        "RMSE = 10,68, y la recta de mínimos cuadrados de sus datos reproduce los pronósticos del práctico.",
        "Índices: cociente de cada mes al promedio móvil centrado de 12 meses, promediados por mes y normalizados "
        "para que promedien 1.",
        f"Escala a la estación: {ent(float(valor('DEM-01')))} L por mes (DEM-01) ÷ el promedio de los últimos 12 meses "
        f"de Shell Mendoza ({ent(sum(ultimos) / len(ultimos))} m³) = {dec(100 * escala, 2)} % de la provincia. Supuesto: "
        "la estación sigue la misma forma que el conjunto de las Shell de Mendoza.",
        "Fuente: Secretaría de Energía, datos abiertos (nota 12 en research_notes; PRO-01 a PRO-04 en Datos y fuentes).",
    ])



def bloque_stock_seguridad(p: ParametrosSimulacion) -> None:
    """Inventario: la cuenta del punto de pedido con el stock de seguridad del pronóstico (P4)."""
    from sim.pronostico import stock_de_seguridad

    filas_calc = stock_de_seguridad(p)
    nombres = _nombres(p)
    en_uso = all(abs(i.punto_pedido - x.s) < 1e-6 for i, x in zip(p.inventario, filas_calc))
    st.markdown("##### 4. El punto de pedido con el pronóstico (stock de seguridad)")
    st.caption(
        "**s = D · L + z · σ_día · √L**: lo que se vende mientras viaja el camión (D·L) más un colchón por el error del "
        "pronóstico. El error sale de la **serie real** (pestaña 📈 Pronóstico): el RMSE del método elegido en los meses "
        f"de prueba es el **{dec(100 * filas_calc[0].error_relativo)} %** de lo que se vende en un mes; se lleva a cada "
        "tanque (σ_mes = error × D × 30) y a un día suponiendo errores diarios independientes (σ_día = σ_mes ÷ √30). "
        "z = 1,96 (95 %). La Q no cambia. "
        + ("**Esta corrida usa esta política** (elegida en el menú 🚚)." if en_uso else
           "Esta corrida **no** la usa: se prende en el menú 🚚 Abastecimiento, y en el Caso de informe compite con las "
           "otras 13 políticas.")
    )
    filas = [{
        "Tanque": nombres[x.producto],
        "D (L por día)": ent(x.consumo_dia),
        "L (días)": dec(x.plazo_dias, 2),
        "D · L": f"{ent(x.consumo_dia * x.plazo_dias)} L",
        "σ por día": f"{ent(x.sigma_dia)} L",
        "Stock de seguridad z·σ·√L": f"{ent(x.seguridad)} L",
        "s por pronóstico": f"{ent(x.s)} L",
        "s cargada": f"{ent(i.punto_pedido)} L",
    } for x, i in zip(filas_calc, p.inventario)]
    st.dataframe(pd.DataFrame(filas), hide_index=True)



# =============================================================================
# Flujos en la red (parte 3, F3): el plan del período en Red y rutas
# =============================================================================
def seccion_plan_red(p: ParametrosSimulacion, r: ResultadoReplica, topes_menu: dict[str, float]) -> None:
    """El plan de abastecimiento del período (transbordo), la matriz de transporte y las rutas independientes."""
    from sim.flujos import (
        M_GRANDE, arcos_de_ruta, matriz_transbordo, plan_de_abastecimiento, resolver_transporte, rutas_independientes,
        solucion_inicial,
    )
    from sim.red import NOMBRE_NODO, camino_mas_corto

    red = p.red
    nombres = _nombres(p)
    st.divider()
    st.markdown("#### El plan del período: flujos en la red (transbordo, transporte y flujo máximo)")
    st.caption(
        "Dijkstra elige la ruta de **cada** camión. Esto mira **todos los camiones del período juntos**: cuántos "
        "conviene traer de cada origen y por qué tramos, con el **flujo de costo mínimo** (transbordo) en camión-km. Lo "
        "que limita es **cuánto puede despachar cada origen** (FLU-02: hoy todo sale de Dock Sud; Arroyo Seco y Luján "
        "son supuestos) y los **cortes**. Probá topes y cortes acá; para que la simulación despache así, prendé "
        "**'Despachar según el plan'** en el menú 🚚 Abastecimiento."
    )
    camiones_por = {pr: n for pr, n in r.pedidos_total if n > 0}
    camiones = float(sum(camiones_por.values()))
    if camiones <= 0:
        st.info("En este período no se pidió ningún camión.", icon="🚚")
        return
    cortes = {"ninguno": "Sin cortes"} | {c.id: f"{c.id}: {c.nombre}" for c in red.cortes if c.arcos}
    c1, c2, c3 = st.columns(3)
    tope_arroyo = c1.slider("Arroyo Seco puede despachar (%)", 0, 100, int(round(100 * topes_menu.get("ARROYO", 0))), 5,
                            key="plan_arroyo", help="Terminal de Raízen/Shell (nota 09). Hoy: 0 % (FLU-02).") / 100
    tope_lujan = c2.slider("Luján de Cuyo puede despachar (%)", 0, 100, int(round(100 * topes_menu.get("LUJAN", 0))), 5,
                           key="plan_lujan", help="Refinería de YPF: otra empresa, sólo emergencia. Hoy: 0 %.") / 100
    corte = c3.selectbox("Corte de ruta", list(cortes), format_func=cortes.get, key="plan_corte")
    cerrados = next((c.arcos for c in red.cortes if c.id == corte), ())
    topes = {"DOCK": 1.0, "ARROYO": tope_arroyo, "LUJAN": tope_lujan}
    plan = plan_de_abastecimiento(red, camiones, topes, cerrados)
    hoy = plan_de_abastecimiento(red, camiones, {"DOCK": 1.0})
    rutas = rutas_independientes(red, [o for o, t in topes.items() if t > 0], cerrados)
    _tarjetas([
        ("Camiones del período", ent(camiones), "los que pidió la simulación (los 4 tanques)"),
        ("Camión-km del plan (ida)", ent(plan.km_total), f"hoy, todo desde Dock Sud por la ruta más corta: {ent(hoy.km_total)}"),
        ("Diferencia contra hoy", f"{dec(100 * (plan.km_total - hoy.km_total) / hoy.km_total)} %",
         "negativo = el plan ahorra kilómetros"),
        ("Rutas independientes", ent(rutas.valor), "rutas que no comparten ningún tramo (flujo máximo)"),
    ])
    if plan.enviados < camiones - 1e-9:
        st.error(f"Con este corte y estos topes sólo se pueden traer {ent(plan.enviados)} de {ent(camiones)} camiones: "
                 "ningún origen habilitado llega a San Rafael.", icon="⛔")
    filas = []
    for origen, n in plan.por_origen:
        km = camino_mas_corto(red, origen=origen, cerrados=cerrados).km
        filas.append({"Origen": NOMBRE_NODO.get(origen, origen), "Camiones": dec(n), "% de los camiones": pct(n, camiones),
                      "km por camión (ruta más corta)": dec(km), "Camión-km": ent(n * km)})
    st.markdown("##### De dónde sale cada camión y por dónde viene")
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    nombre_tramo = {frozenset((a.a, a.b)): a.ruta for a in red.arcos}
    st.dataframe(pd.DataFrame([{
        "Tramo": f"{NOMBRE_NODO.get(d, d)} → {NOMBRE_NODO.get(h, h)}", "Ruta": nombre_tramo.get(frozenset((d, h)), ""),
        "Camiones": dec(f)} for d, h, f in plan.tramos]), hide_index=True)
    st.caption(
        "El plan es un flujo continuo (puede dar 8,8 camiones); al despachar según el plan, la simulación reparte los "
        "camiones enteros con cuotas exactas en esa misma proporción. "
        f"Para aislar San Rafael de los orígenes habilitados hay que cortar **{ent(len(rutas.corte))} tramos** (el corte "
        "mínimo): " + " · ".join(f"{NOMBRE_NODO.get(a, a)}–{NOMBRE_NODO.get(b, b)}" for a, b in rutas.corte) + "."
    )

    with st.expander("La misma cuenta como problema de transporte (orígenes × tanques), como en la cátedra"):
        origenes = [o for o, t in topes.items() if t > 0]
        oferta = [round(topes[o] * camiones, 6) for o in origenes]
        productos = list(camiones_por)
        demanda = [float(camiones_por[x]) for x in productos]
        km_de = {o: camino_mas_corto(red, origen=o, cerrados=cerrados).km for o in origenes}
        costos = [[km_de[o] if km_de[o] != float("inf") else M_GRANDE for _ in productos] for o in origenes]
        no = solucion_inicial(oferta, demanda, costos, "rincon_noroeste")
        cm = solucion_inicial(oferta, demanda, costos, "costo_minimo")
        opt = resolver_transporte(oferta, demanda, costos)
        st.markdown(
            f"Oferta = tope × camiones; demanda = camiones de cada tanque; costo = km por camión. Rincón noroeste: "
            f"**{ent(no.costo)}** camión-km · costo mínimo: **{ent(cm.costo)}** · óptimo (MODI / Stepping-Stone, "
            f"{opt.iteraciones} mejoras): **{ent(opt.costo)}**"
            + (" · se agregó un **destino ficticio** (sobra oferta) con costo 0." if opt.ficticio == "destino" else ".")
        )
        columnas = [nombres[x] for x in productos] + (["Ficticio"] if opt.ficticio == "destino" else [])
        filas_o = [NOMBRE_NODO.get(o, o) for o in origenes] + (["Ficticio"] if opt.ficticio == "origen" else [])
        st.dataframe(pd.DataFrame([[dec(v) for v in fila] for fila in opt.asignacion], index=filas_o, columns=columnas))
        mt = matriz_transbordo(arcos_de_ruta(red, cerrados),
                               {**{o: n for o, n in plan.por_origen}, red.destino: -plan.enviados})
        tr = resolver_transporte(mt.oferta, mt.demanda, mt.costos)
        st.caption(
            f"Y como **transbordo** con la matriz de la cátedra ({len(mt.filas)} filas × {len(mt.columnas)} columnas, "
            f"B = {ent(mt.b)}; nodos de paso con oferta y demanda B y costo 0 consigo mismos): {ent(tr.costo)} camión-km, "
            f"igual que el flujo de costo mínimo ({ent(plan.km_total)})."
        )
    _comprobacion([
        "Plan: flujo de costo mínimo (caminos más cortos sucesivos) desde un nodo que reparte los camiones entre los "
        "orígenes, cada uno hasta su tope × los camiones; costo = km de cada tramo (RED-*). Control 43 de `verificar.py`.",
        _md("Los métodos se probaron con los ejercicios de la cátedra (control 42): transporte $4.200 / $4.100 / "
            "$3.900, transbordo $20.700 y oleoducto 205.000 gal/h."),
        "Rutas independientes: flujo máximo con capacidad 1 en cada tramo (FLU-01, teorema de Menger); el corte mínimo son "
        "los tramos que habría que cortar para aislar la estación.",
        "El flete en pesos sale de ECO-06 (por km sin dato: 0), por eso el plan se mide en camión-km.",
    ])



# =============================================================================
# §24 · Inventario: cada camión, de punta a punta
# =============================================================================
def tabla_camiones(p: ParametrosSimulacion, r: ResultadoReplica, eco: ParametrosEconomicos) -> None:
    """Cada camión del período: cuándo se pidió y llegó, de dónde salió, por dónde vino, km, litros y flete."""
    from sim.red import NOMBRE_NODO, ruta_del_viaje

    st.markdown("##### 5. Cada camión, de punta a punta")
    if not r.camiones or p.red is None:
        st.caption("En este período no se pidió ningún camión.")
        return
    nombres = _nombres(p)
    elegidos = st.multiselect("Tanques", list(dict.fromkeys(x.producto for x in r.camiones)),
                              default=list(dict.fromkeys(x.producto for x in r.camiones)),
                              format_func=nombres.get, key="camiones_tanques")
    filas, total_km, total_flete = [], 0.0, 0.0
    for k, x in enumerate(r.camiones, start=1):
        origen = x.origen or p.red.origen
        camino, como = ruta_del_viaje(p.red, origen, x.demora_ruta, x.causa)
        flete = eco.costo_pedido + eco.flete_por_km * 2.0 * camino.km
        if x.producto not in elegidos:
            continue
        total_km += camino.km
        total_flete += flete
        llego = "todavía en camino" if x.t_llegada > p.duracion else _cuando(p, x.t_llegada)
        filas.append({
            "N°": k,
            "Tanque": nombres[x.producto],
            "Se pidió": _cuando(p, x.t_pedido),
            "Llegó": llego,
            "Plazo": f"{dec((x.t_llegada - x.t_pedido) / 60)} h",
            "Origen": NOMBRE_NODO.get(origen, origen) + (" (redirigido)" if x.redirigido else ""),
            "Ruta": " → ".join(NOMBRE_NODO.get(n, n) for n in camino.ruta),
            "km (ida)": dec(camino.km),
            "Cómo vino": como + (f" (+{dec(x.demora_ruta / 60)} h, {x.causa})" if x.demora_ruta > 0 else ""),
            "Litros": ent(x.litros),
            "Flete": _pesos(flete),
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, height=min(36 * (len(filas) + 1) + 3, 460))
    st.caption(_md(
        f"{ent(len(filas))} camiones de los tanques elegidos ({ent(len(r.camiones))} en total = los pedidos de "
        f"Indicadores) · {ent(total_km)} km de ida · flete {_pesos(total_flete)} = {ent(len(filas))} × "
        f"{_pesos(eco.costo_pedido)} fijo + {_pesos(eco.flete_por_km)}/km × km de ida y vuelta (ECO-06, heredado sin "
        "fuente). El plazo es el de INV-01 más la diferencia de viaje si salió de otro origen y la demora de un corte."
    ))
