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
    return f"−$ {ent(-x)}" if x < -0.5 else f"$ {ent(x)}"


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
        icon=":material/oil_barrel:",
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

    if not quiebres or all(q[0] == 0 for q in quiebres.values()):
        from sim.datos import valor

        plazo = p.inventario[0].plazo_entrega
        st.success(
            f"**En esta corrida no se vació ningún tanque.** Con la política que usa la app (pedir cuando quedan "
            f"{dec(valor('INV-13')[0], 0)} días de venta) y sin azar, el camión tarda siempre lo mismo "
            f"({dec(plazo.media, 0)} h) y llega antes de que el tanque se vacíe. "
            "Los tanques se vacían cuando: **se pide más tarde** (por ejemplo, la política de INV-07, con 1,5 días, "
            "en un año deja tanques vacíos decenas de veces); **el camión tarda más** (con *Editar simulación* hay "
            f"azar y puede tardar hasta {dec(plazo.maximo, 0)} h); o **hay eventos** (faltante de combustible con cupo, "
            "cortes de ruta, "
            "mucha más demanda). Por eso en otras simulaciones aparecen horas con tanques vacíos.",
            icon=":material/check_circle:",
        )
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
        + ". La venta perdida = lo que no se vendió × el margen por litro (por m³ el GNC) "
        "(ECO-01, supuesto; ECO-03 del GNC, heredado): es un **costo de oportunidad** y se informa aparte, no se resta del margen. El GNC va en m³ "
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


def cifra_html(titulo: str, valor: str, ayuda: str = "", debajo: str = "") -> str:
    """Una cifra del tótem: rótulo chico, dígitos grandes condensados y la unidad chica al lado.

    La unidad es lo que sigue al último número ("8.511 L" → "8.511" + "L"); un valor sin número (el nombre de un
    método) se muestra entero, en un tamaño menor. Los `$` se escriben como entidad (dos se leerían como LaTeX).
    """
    import html as _html
    import re

    m = re.match(r"^(.*\d)\s+([^\d]+)$", valor.strip())
    numero, unidad = (m.group(1), m.group(2)) if m else (valor, "")
    def esc(t: str) -> str:
        return _html.escape(t).replace("$", "&#36;")
    clase = "tot-cifra-valor" + ("" if any(c.isdigit() for c in numero) else " tot-texto")
    cola = f"<span>{esc(unidad)}</span>" if unidad else ""
    # La ayuda va en el rótulo (subrayado de puntos, se lee al pasar el mouse o con el lector de pantalla).
    # tabindex: también se abre con el teclado (Tab) y con un toque, no sólo con el mouse.
    rotulo = (f"<abbr tabindex='0' data-ayuda='{esc(ayuda)}' aria-label='{esc(titulo)}: {esc(ayuda)}'>"
              f"{esc(titulo)}</abbr>" if ayuda else esc(titulo))
    extra = f"<div class='tot-cifra-debajo'>{esc(debajo)}</div>" if debajo else ""
    return (f"<div class='tot-cifra'><div class='tot-cifra-rotulo'>{rotulo}</div>"
            f"<div class='{clase}'>{esc(numero)}{cola}</div>{extra}</div>")


def _nota(nota: str) -> str:
    """Una nota debajo de una cifra: un "+ " o "- " al principio no tiene que leerse como lista de Markdown."""
    return "\\" + nota if nota[:2] in ("+ ", "- ", "* ") else nota


def _tarjetas(filas: list[tuple[str, str, str]]) -> None:
    columnas = st.columns(len(filas))
    for col, (titulo, valor, nota) in zip(columnas, filas):
        col.markdown(cifra_html(titulo, valor), unsafe_allow_html=True)
        col.caption(_nota(nota))


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
        seccion_formulas_colas(p, r, traza, modo)

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
                   "Pronóstico.")
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
    """La pestaña Eventos: cómo se sortearon, la tabla de los que ocurrieron y lo que costaron."""
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
        icon=":material/bolt:",
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
def _mes_corto(mes: tuple[int, int]) -> str:
    return MESES_ES[mes[1] - 1].capitalize()


def _tabla_de_errores(comp, fmt, unidad: str) -> None:
    """La tabla del parcial: Mes | Pronóstico | Real | Error | Error ÷ real | Error², con Σ y el promedio abajo."""
    filas = [{
        "Mes": _mes_corto(x.mes),
        "Pronóstico": fmt(x.pronostico),
        "Real": fmt(x.real),
        "Error |P − R|": fmt(x.error),
        "Error ÷ real": f"{dec(100 * x.error_relativo, 2)} %",
        "Error²": _num(x.error_cuadrado),
    } for x in comp.filas]
    n = len(comp.filas)
    filas.append({"Mes": "Suma", "Pronóstico": "", "Real": "", "Error |P − R|": fmt(comp.mae * n),
                  "Error ÷ real": f"{dec(100 * comp.mape * n, 2)} %", "Error²": _num(comp.mse * n)})
    filas.append({"Mes": f"Suma ÷ {n}", "Pronóstico": "", "Real": "", "Error |P − R|": f"MAE = {fmt(comp.mae)}",
                  "Error ÷ real": f"MAPE = {dec(100 * comp.mape, 2)} %", "Error²": f"MSE = {_num(comp.mse)}"})
    st.dataframe(pd.DataFrame(filas), hide_index=True, height=36 * (len(filas) + 1) + 3)
    _tarjetas([
        ("MAE", f"{fmt(comp.mae)} {unidad}".strip(), "error absoluto medio: Σ|P − R| ÷ n"),
        ("MAPE", f"{dec(100 * comp.mape, 2)} %", "error porcentual medio: Σ(|P − R| ÷ R) ÷ n × 100"),
        ("RMSE", f"{fmt(comp.rmse)} {unidad}".strip(), f"√MSE = √{_num(comp.mse)}"),
    ])


def _num(x: float) -> str:
    """Con decimales si es chico (precios), entero si es grande."""
    return dec(x, 2) if abs(x) < 100 else ent(x)


def _calidad(mape: float) -> str:
    """Escala habitual para leer el MAPE (Lewis): < 10 % muy preciso, 10–20 % bueno, 20–50 % razonable."""
    if mape < 0.10:
        return "muy preciso (menos del 10 %)"
    if mape < 0.20:
        return "bueno (entre 10 % y 20 %)"
    if mape < 0.50:
        return "razonable (entre 20 % y 50 %)"
    return "poco confiable (más del 50 %)"


def _explicacion(comp, fmt, que: str, unidad: str, por_que: str) -> None:
    """Debajo de cada tabla: qué quiere decir el MAE, el MAPE y el RMSE que dieron."""
    peor = max(comp.filas, key=lambda x: x.error)
    cociente = comp.rmse / comp.mae if comp.mae else 1.0

    def u(x: float) -> str:
        return fmt(x) + (f" {unidad}" if unidad else "")

    st.markdown(_md(
        f"- **MAE = {u(comp.mae)}**: en promedio, el pronóstico de {que} se equivoca en {u(comp.mae)} por mes, "
        "para arriba o para abajo.\n"
        f"- **MAPE = {dec(100 * comp.mape, 2)} %**: ese error es, en promedio, el {dec(100 * comp.mape, 2)} % del valor "
        f"real. Es un pronóstico {_calidad(comp.mape)}.\n"
        f"- **RMSE = {u(comp.rmse)}**: eleva cada error al cuadrado, así que castiga más los meses con "
        f"errores grandes. Es {dec(cociente, 2)} veces el MAE: "
        + ("los errores son parejos, ningún mes se escapa mucho." if cociente < 1.15 else
           f"hay meses que se escapan más que el resto (el mayor es {_mes_corto(peor.mes).lower()}, con "
           f"{u(peor.error)}).")
        + f"\n- **Por qué hay error**: {por_que}"
    ))


def pestania_pronostico(p: ParametrosSimulacion, anio: ResultadoReplica, eco: ParametrosEconomicos) -> None:
    """La pestaña Pronóstico: tres tablas como el ejercicio 1 del parcial (clientes, precio y ganancias por mes)."""
    from sim.datos import valor
    from sim.pronostico import (
        clientes_pronosticados, comparar, escala_a_la_estacion, factores_de_precio, ganancias_por_mes,
        inflacion_esperada, inflacion_real, recta_de_la_serie,
    )

    meses = [(a, m) for a, m, _, _ in anio.por_mes]
    st.subheader("Pronóstico contra simulación")
    st.markdown(
        "Como el **ejercicio 1 del parcial**: un modelo da un pronóstico para cada mes, se lo compara con el valor "
        "**real** (acá, lo que dio la **simulación del año**) y se mide qué tan bueno es con tres errores."
    )
    st.latex(r"\text{MAE} = \frac{\sum |P - R|}{n} \qquad \text{MAPE} = \frac{\sum |P - R| / R}{n} \times 100"
             r" \qquad \text{RMSE} = \sqrt{\frac{\sum (P - R)^2}{n}}")
    st.caption(f"P = pronóstico · R = real · n = {len(meses)} meses. Error = |P − R| (valor absoluto). El año simulado "
               "usa los mismos ajustes que esta corrida (si la corrida no era el año completo, se simuló aparte).")

    # --- 1. Clientes ------------------------------------------------------------------------------------------
    a, b, (anio0, mes0) = recta_de_la_serie()
    st.markdown("##### 1. Clientes por mes")
    st.caption(_md(
        f"**Pronóstico:** la recta de tendencia **F = A + B·t** (A = {ent(a)} m³, B = {dec(b)} m³ por mes, t = 0 en "
        f"{MESES_ES[mes0 - 1]} de {anio0}) ajustada a las ventas reales de Shell en Mendoza (PRO-01), llevada a esta "
        f"estación (× {dec(escala_a_la_estacion())} L por m³) y a clientes (÷ {dec(p.litros_medios_por_cliente)} L por "
        f"cliente ÷ (1 − {dec(p.pct_gnc, 2)}) por el GNC). **Real:** los clientes que llegaron en la simulación."
    ))
    reales = [n for _, _, n, _ in anio.por_mes]
    comp = comparar(meses, clientes_pronosticados(p, meses), reales)
    _tabla_de_errores(comp, ent, "clientes")
    _explicacion(
        comp, ent, "clientes", "clientes",
        f"la recta sólo ve la tendencia (baja {dec(-b)} m³ por mes en la provincia); la simulación además reparte la "
        "demanda según cuánto pesa cada mes (índices de la serie real) y según los días que tiene cada mes, así que "
        "los meses más fuertes o más cortos se le escapan a la recta.",
    )

    # --- 2. Precio ------------------------------------------------------------------------------------------
    minimo, maximo, _ = valor("PRO-05")
    esperada = inflacion_esperada()
    real_i = inflacion_real(len(meses))
    f_pron = factores_de_precio([esperada] * len(meses))
    f_real = factores_de_precio(real_i)
    st.markdown("##### 2. Precio por mes")
    productos = {"super": "Súper ($/L)", "diesel_g2": "Evolux Diesel ($/L)", "gnc": "GNC ($/m³)"}
    elegido = st.radio("Producto", list(productos), format_func=productos.get, horizontal=True, key="pron_precio")
    precio0 = float(dict(eco.precios)[elegido])
    st.caption(_md(
        f"Se parte del precio de referencia (ECO-08: ${ent(precio0)}) y cada mes sube por la inflación. "
        f"**Pronóstico:** {dec(100 * esperada)} % todos los meses (el punto medio). **Real:** la inflación de cada mes "
        f"varía entre {dec(100 * minimo)} % y {dec(100 * maximo)} % (PRO-05, supuesto; sorteada con semilla fija, "
        "así que siempre da lo mismo). Precio del mes = precio del mes anterior × (1 + inflación)."
    ))
    comp_p = comparar(meses, [precio0 * f for f in f_pron], [precio0 * f for f in f_real])
    st.dataframe(pd.DataFrame({
        "Mes": [_mes_corto(m) for m in meses],
        "Inflación del pronóstico": [f"{dec(100 * esperada)} %"] * len(meses),
        "Inflación real": [f"{dec(100 * i)} %" for i in real_i],
    }).set_index("Mes").T)
    _tabla_de_errores(comp_p, lambda x: f"$ {dec(x, 2)}", "")
    _explicacion(
        comp_p, lambda x: f"${dec(x, 2)}", f"precio ({productos[elegido].split(' (')[0]})", 
        "por m³" if elegido == "gnc" else "por litro",
        "el pronóstico supone la misma inflación todos los meses y la real sube unos meses más y otros menos; como "
        "el precio de cada mes arrastra la inflación de todos los anteriores, el error de un mes se acumula en los "
        "siguientes. Los tres productos suben con la misma inflación: el MAPE es el mismo para los tres.",
    )

    # --- 3. Ganancias ----------------------------------------------------------------------------------------
    st.markdown("##### 3. Ganancias por mes")
    margenes = {pr.id: eco.margen_de(pr.id) for pr in p.productos}
    st.caption(_md(
        "**Ganancia bruta del combustible** = litros (m³ el GNC) × margen por litro, y el margen sube con el precio "
        "(misma inflación). **Pronóstico:** los litros de la recta (punto 1) repartidos por producto (DEM-04) con la "
        f"inflación de {dec(100 * esperada)} %. **Real:** lo que vendió la simulación en cada mes con la inflación "
        "real. Márgenes de hoy: " + " · ".join(f"{pr.nombre} ${ent(margenes[pr.id])}" for pr in p.productos)
        + " (ECO-01, supuesto del grupo; ECO-03, heredado sin fuente: los pesos muestran cómo se calcula, no cifras del negocio)."
    ))
    g_pron, g_real = ganancias_por_mes(p, margenes, meses, [v for *_, v in anio.por_mes], f_pron, f_real)
    comp_g = comparar(meses, g_pron, g_real)
    _tabla_de_errores(comp_g, _pesos, "")
    _explicacion(
        comp_g, _pesos, "ganancia", "",
        "junta los dos errores anteriores: los litros del mes (la recta no ve la estacionalidad) y el precio (la "
        "inflación real no es pareja). Además la simulación cuenta lo que se **vendió**, que puede ser menos que lo "
        "pedido si faltó combustible o hubo cortes de GNC.",
    )

    with st.expander("De dónde salen los índices mensuales de la demanda"):
        from sim.pronostico import analizar

        st.plotly_chart(graficos.grafico_indices(analizar().indices), key="g_indices")
        st.caption("Cuánto pesa cada mes en la serie real de Shell Mendoza (promedio 1). Con la opción 'Índices de la "
                   "serie real' del menú (la de siempre), la simulación reparte los litros del año con estos índices.")


# =============================================================================
# Economía: cuánto va a valer el litro (la inflación de PRO-05)
# =============================================================================
def seccion_precio_futuro(eco: ParametrosEconomicos) -> None:
    """El precio de nafta, gasoil y GNC mes a mes, con la inflación de cada mes (la 'real' de la pestaña Pronóstico)."""
    from sim.datos import valor
    from sim.pronostico import factores_de_precio, inflacion_real

    minimo, maximo, _ = valor("PRO-05")
    inflacion = inflacion_real(12)
    factores = factores_de_precio(inflacion)
    precios = dict(eco.precios)
    nombres = {"super": "Súper", "premium": "V-Power Nafta", "diesel_g2": "Evolux Diesel", "diesel_g3": "V-Power Diesel",
               "gnc": "GNC"}
    st.markdown("##### Cuánto va a valer el litro")
    st.caption(_md(
        f"Desde el precio de hoy (ECO-08), cada mes sube por la inflación de ese mes, que varía entre "
        f"{dec(100 * minimo)} % y {dec(100 * maximo)} % (PRO-05, supuesto; la misma que usa la pestaña Pronóstico). "
        "Precio del mes = precio del mes anterior × (1 + inflación). El GNC va por m³."
    ))
    mes = st.select_slider("¿Para qué mes?", options=list(range(1, 13)), value=12,
                           format_func=lambda m: MESES_ES[m - 1].capitalize(), key="eco_mes_precio")
    _tarjetas([
        (f"{nombres[k]} en {MESES_ES[mes - 1]}", f"$ {ent(precios[k] * factores[mes - 1])}",
         f"hoy $ {ent(precios[k])} (+{dec(100 * (factores[mes - 1] - 1))} %)")
        for k in ("super", "premium", "diesel_g2", "diesel_g3")
    ])
    st.dataframe(pd.DataFrame([{
        "Mes": MESES_ES[k].capitalize(),
        "Inflación del mes": f"{dec(100 * inflacion[k])} %",
        **{f"{nombres[x]} ($/{'m³' if x == 'gnc' else 'L'})": f"$ {dec(precios[x] * factores[k], 2)}" for x in nombres},
    } for k in range(12)]), hide_index=True, height=36 * 13 + 3)


# =============================================================================
# Indicadores · Colas: las fórmulas de la cátedra con los números de la simulación
# =============================================================================
def _playeros_a_la_hora(p: ParametrosSimulacion, hora: int) -> int:
    """Playeros en turno a esa hora (el último tramo de `turnos` que empezó antes)."""
    return [n for inicio, n in sorted(p.turnos) if inicio <= hora][-1]


def seccion_formulas_colas(p: ParametrosSimulacion, r: ResultadoReplica, traza: Traza, modo: str) -> None:
    """M/M/1 o M/M/s con λ, μ y s de la simulación, y las leyes de Little con lo que midió la simulación."""
    from sim.colas import mms

    st.markdown("##### Las fórmulas de la cátedra con los números de la simulación")
    st.caption(
        "La estación como un sistema de colas: los **servidores son los playeros** (cada cliente necesita uno, también "
        "el de GNC: PER-04). Notación de la cátedra: λ = clientes que llegan por hora · μ = clientes que atiende un "
        "playero por hora · s = playeros · ρ = λ ÷ (s·μ) = utilización."
    )
    st.latex(r"L = \lambda W \qquad L_q = \lambda W_q \qquad W = W_q + \frac{1}{\mu} \qquad L = L_q + \frac{\lambda}{\mu}")
    dias = max(len(traza.llegadas_dia_hora), 1)
    llegadas_h = [sum(d[h] for d in traza.llegadas_dia_hora) / dias for h in range(24)]
    pico = max(range(24), key=lambda h: llegadas_h[h])
    hora = st.selectbox(
        "Hora del día", list(range(24)), index=pico, key="colas_hora",
        format_func=lambda h: f"{h:02d}–{(h + 1) % 24:02d} h" + (" (la de más llegadas)" if h == pico else ""),
    )
    lam = llegadas_h[hora]
    servicio = p.media_servicio_playero()
    mu = 60.0 / servicio
    s = _playeros_a_la_hora(p, hora)
    suma = sum(d[hora][0] for d in traza.espera_dia_hora)
    cant = sum(d[hora][1] for d in traza.espera_dia_hora)
    wq_sim = (suma / cant if cant else 0.0) / 60.0          # horas

    st.markdown(
        f"**1. Datos (en horas).** λ = {dec(lam, 2)} clientes/h (promedio de los {dias} días en esa hora) · "
        f"1/μ = {dec(servicio, 2)} min de atención (TIE-02 y TIE-04 ponderados por producto) ⇒ "
        f"μ = 60 ÷ {dec(servicio, 2)} = {dec(mu, 2)} clientes/h por playero · s = {s} "
        f"playero{'s' if s != 1 else ''} en turno · ρ = λ ÷ (s·μ) = {dec(lam, 2)} ÷ ({s} × {dec(mu, 2)}) = "
        f"**{dec(lam / (s * mu), 3)}**."
    )
    if lam <= 0:
        st.info("A esa hora no llega nadie: no hay cola que calcular.", icon=":material/info:")
        return
    try:
        f = mms(lam, mu, s)
    except ValueError:
        st.warning("ρ ≥ 1: con estas tasas la cola crecería sin límite y las fórmulas no tienen solución.",
                   icon=":material/warning:")
        return
    a = lam / mu
    sup = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    if s == 1:
        st.latex(r"\text{M/M/1:}\quad P_0 = 1 - \rho \qquad L_q = \frac{\rho^2}{1-\rho} \qquad "
                 r"W_q = \frac{L_q}{\lambda} \qquad W = W_q + \frac{1}{\mu} \qquad L = \lambda W")
        cuenta_p0 = f"P0 = 1 − {dec(f.rho, 3)} = {dec(f.p0, 4)}"
        cuenta_lq = f"Lq = {dec(f.rho, 3)}² ÷ (1 − {dec(f.rho, 3)}) = {dec(f.lq, 4)} clientes"
    else:
        st.latex(r"\text{M/M/s:}\quad P_0 = \left[\sum_{n=0}^{s-1}\frac{(\lambda/\mu)^n}{n!} + "
                 r"\frac{(\lambda/\mu)^s}{s!\,(1-\rho)}\right]^{-1} \qquad "
                 r"L_q = \frac{P_0\,(\lambda/\mu)^s\,\rho}{s!\,(1-\rho)^2}")
        st.latex(r"W_q = \frac{L_q}{\lambda} \qquad W = W_q + \frac{1}{\mu} \qquad L = \lambda W")
        cuenta_p0 = (f"λ/μ = {dec(a, 3)} ⇒ P0 = 1 ÷ [" + " + ".join(
            f"{dec(a, 3)}{str(n).translate(sup)} ÷ {n}!" for n in range(s)) + f" + {dec(a, 3)}{str(s).translate(sup)} ÷ ({s}! × (1 − {dec(f.rho, 3)}))] = "
            f"{dec(f.p0, 4)}")
        cuenta_lq = (f"Lq = {dec(f.p0, 4)} × {dec(a, 3)}{str(s).translate(sup)} × {dec(f.rho, 3)} ÷ ({s}! × (1 − {dec(f.rho, 3)})²) = "
                     f"{dec(f.lq, 4)} clientes")
    st.markdown(
        f"**2. Las fórmulas.** {cuenta_p0} · {cuenta_lq} · Wq = Lq ÷ λ = {dec(f.lq, 4)} ÷ {dec(lam, 2)} = "
        f"{dec(f.wq, 4)} h = **{dec(60 * f.wq, 2)} min** · W = Wq + 1/μ = {dec(60 * f.wq, 2)} + {dec(servicio, 2)} = "
        f"**{dec(60 * f.w, 2)} min** · L = λ·W = {dec(lam, 2)} × {dec(f.w, 4)} = **{dec(f.l, 3)} clientes**."
    )
    w_sim = wq_sim + 1.0 / mu
    st.markdown(
        f"**3. La simulación en esa hora, con Little.** Wq medida = {dec(60 * wq_sim, 2)} min ⇒ Lq = λ·Wq = "
        f"{dec(lam, 2)} × {dec(wq_sim, 4)} = {dec(lam * wq_sim, 4)} · W = Wq + 1/μ = {dec(60 * w_sim, 2)} min · "
        f"L = λ·W = {dec(lam * w_sim, 3)}."
    )
    st.dataframe(pd.DataFrame({
        "": ["ρ (utilización)", "Wq (min en la cola)", "W (min en el sistema)", "Lq (clientes en la cola)",
             "L (clientes en el sistema)"],
        "Fórmula M/M/" + ("1" if s == 1 else "s"): [dec(f.rho, 3), dec(60 * f.wq, 2), dec(60 * f.w, 2),
                                                    dec(f.lq, 4), dec(f.l, 3)],
        "Simulación (+ Little)": [dec(lam / (s * mu), 3), dec(60 * wq_sim, 2), dec(60 * w_sim, 2),
                                  dec(lam * wq_sim, 4), dec(lam * w_sim, 3)],
    }), hide_index=True)
    lam_min = sum(llegadas_h) / (24 * 60)
    st.caption(
        "**Por qué no dan igual:** la fórmula supone llegadas al azar (Poisson) y atención exponencial con una sola "
        "cola. En la simulación la atención es triangular (menos variable), cada zona tiene su propia cola, hace falta "
        "una cara libre además del playero y la cola tiene un tope"
        + (", y **sin azar los clientes llegan parejos** (cuotas exactas), así que casi no se forma cola."
           if modo != "editada" else ".")
        + f" Little vale siempre: en todo el período, λ = {dec(60 * lam_min, 2)} clientes/h y Wq = "
        f"{dec(r.espera_surtidor, 2)} min ⇒ Lq = λ·Wq = {dec(lam_min * r.espera_surtidor, 4)} clientes esperando en "
        f"promedio. La cola que se ve frente a los surtidores es más chica ({dec(r.cola_surtidor, 4)} autos) porque "
        "parte de esa espera es ya en la cara, esperando que se libere un playero; Little con la espera hasta la "
        "cara da exactamente esa cola (control 3 de `verificar.py`)."
    )



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
        "fuente). El plazo es el de INV-01 (× km del origen ÷ km de Dock Sud si salió de otro origen) más la demora de un corte."
    ))



# =============================================================================
# §24 · Red y rutas: la red de cada producto (nafta, diésel y GNC)
# =============================================================================
def seccion_red_por_producto(p: ParametrosSimulacion, r: ResultadoReplica) -> None:
    """Nafta y diésel llegan en camión por la red de rutas; el GNC llega por gasoducto (GNC-11)."""
    from sim.datos import valor
    from sim.red import NOMBRE_NODO, camino_mas_corto

    st.markdown("##### La red de cada producto: nafta, diésel y GNC")
    grupos = {"Nafta (Súper y V-Power)": ("super", "vpower"), "Diésel (G2 y G3)": ("diesel_g2", "diesel_g3")}
    filas = []
    for nombre, productos in grupos.items():
        camiones = [x for x in r.camiones if x.producto in productos]
        origenes = dict.fromkeys(x.origen or p.red.origen for x in camiones) or {p.red.origen: None}
        rutas = " · ".join(
            " → ".join(NOMBRE_NODO.get(n, n) for n in camino_mas_corto(p.red, origen=o).ruta) for o in origenes)
        plazo = sum(x.t_llegada - x.t_pedido for x in camiones) / len(camiones) / 60 if camiones else 0.0
        filas.append({
            "Producto": nombre, "Cómo llega": "camión cisterna (un producto por camión)",
            "Desde": ", ".join(NOMBRE_NODO.get(o, o) for o in origenes), "Por": rutas,
            "Camiones en el período": ent(len(camiones)),
            "Plazo medio": f"{dec(plazo)} h" if camiones else "—",
            "Litros pedidos": ent(sum(x.litros for x in camiones)),
        })
    cadena = valor("GNC-11")
    filas.append({
        "Producto": "GNC", "Cómo llega": "gasoducto (no tiene tanque ni camión)", "Desde": cadena[0][0],
        "Por": " → ".join(t for t, _ in cadena[1:]), "Camiones en el período": "—", "Plazo medio": "—",
        "Litros pedidos": "—",
    })
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    nodos = [f"{t}\\n{d}" if d else t for t, d in cadena] + [
        f"La estación\\n{valor('SUR-06')} compresores (SUR-06)"]
    dot = "digraph { rankdir=LR; node [shape=box, style=rounded, fontsize=11];\n" + "\n".join(
        f'"{a}" -> "{b}";' for a, b in zip(nodos, nodos[1:])) + "\n}"
    st.graphviz_chart(dot)
    st.caption(
        "El gas de San Rafael se toma del gasoducto internacional GasAndes: el gasoducto nuevo de la ciudad (inaugurado "
        "en junio de 2026) empalma en el paraje La Tosca, pasa por una planta reguladora sobre la RN 143 y la "
        "distribuidora Ecogas lo lleva a los usuarios (GNC-11, nota 13; informativo: el modelo no simula la red de gas). "
        "Con contrato **interrumpible** (GNC-01), en invierno se le corta el gas a la estación (pestaña GNC)."
    )
