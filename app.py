"""Simulador de Estación de Servicio — Investigación Operativa.

Interfaz del simulador: se configuran los parámetros en la barra lateral, se corre la
simulación y se ven la animación, los indicadores, la demanda Monte Carlo, el inventario,
la comparación de escenarios, el análisis económico y la conclusión.

Para ejecutar:
    .venv/Scripts/streamlit run app.py
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as componentes

from sim.config import (
    DEMANDA_TIPICA,
    ESTACIONALIDAD_LEVE,
    ESTACIONALIDAD_NEUTRA,
    ESTACIONALIDAD_PROXY,
    ANO_REFERENCIA,
    DemandaDiaria,
    ParametrosEconomicos,
    ParametrosGNC,
    ParametrosSimulacion,
    ParametrosTanque,
    Triangular,
    dias_del_mes,
    dias_y_fecha,
    inventario_real,
    turnos_de,
)
from sim.datos import ADVERTENCIAS, CONTRADICCIONES, PIE_NO_AFILIADO, REGISTRO, por_id
from sim.distribuciones import Aleatorio
from sim.gnc import calendario_de_episodios, episodios_con_fechas
from sim.economia import (
    ahorro_por_producto,
    analizar_escenarios,
    analizar_politicas,
    analizar_politicas_real,
    mejor_politica,
    pesos,
    recomendacion,
)
from sim.runner import (
    ResultadoEscenario,
    barrer_politicas,
    barrer_politicas_real,
    buscar,
    con_politica,
    correr_escenarios,
    correr_estacion_real,
    correr_replica,
    grilla_politicas_real,
    grilla_sugerida,
    promedio_por_producto,
)
from sim.red import (
    ETIQUETA_ESCENARIO,
    NOMBRE_NODO,
    camino_mas_corto,
    demora_por_corte,
    descripcion_ruta,
    dias_de_mes_en_corrida,
    muestrear_plazos,
)
from ui import animacion, graficos, graficos_gnc, graficos_red
from ui.datos_ui import (
    csv_registro,
    esquema_estacion_html,
    insignia_html,
    tabla_registro,
)
from ui.tema import css_global
from ui.textos import (
    COMPARACION,
    DESCRIPCION_METODO,
    DESCRIPCION_MODELO,
    DESCRIPCION_MONTECARLO,
    INDICADORES_CLIENTES,
    INDICADORES_COLAS,
    INDICADORES_COMPLEMENTARIOS,
    INDICADORES_GNC,
    INDICADORES_INVENTARIO,
    POR_CLAVE,
    SUPUESTOS,
    SUPUESTOS_REAL,
    DESCRIPCION_MODELO_REAL,
    Metrica,
)

st.set_page_config(
    page_title="Simulador de Estación de Servicio",
    page_icon="⛽",
    layout="wide",
)


# =============================================================================
# Corridas (con caché: si los parámetros no cambiaron, no se vuelve a simular)
# =============================================================================
@st.cache_data(show_spinner=False, max_entries=8)
def correr_escenarios_cacheado(
    p: ParametrosSimulacion, replicas: int, semilla: int
) -> list[ResultadoEscenario]:
    return correr_escenarios(p, replicas=replicas, semilla_base=semilla)


@st.cache_data(show_spinner=False, max_entries=8)
def correr_estacion_real_cacheado(
    p: ParametrosSimulacion, replicas: int, semilla: int
) -> ResultadoEscenario:
    return correr_estacion_real(p, replicas=replicas, semilla_base=semilla)


@st.cache_data(show_spinner=False, max_entries=4)
def barrer_politicas_real_cacheado(p: ParametrosSimulacion, replicas: int, semilla: int):
    return barrer_politicas_real(p, replicas=replicas, semilla_base=semilla)


@st.cache_data(show_spinner=False, max_entries=8)
def correr_traza_cacheada(p: ParametrosSimulacion, semilla: int):
    return correr_replica(p, semilla=semilla, con_traza=True)[1]


@st.cache_data(show_spinner=False, max_entries=8)
def barrer_politicas_cacheado(
    p: ParametrosSimulacion,
    puntos: tuple[float, ...],
    cantidades: tuple[float, ...],
    replicas: int,
    semilla: int,
):
    return barrer_politicas(
        p, list(puntos), list(cantidades), replicas=replicas, semilla_base=semilla
    )


# =============================================================================
# Barra lateral: parámetros del modelo
# =============================================================================
def leer_parametros() -> tuple[ParametrosSimulacion, ParametrosEconomicos, int, int]:
    """Dibuja los controles de la barra lateral y devuelve la configuración elegida."""
    st.sidebar.title("⛽ Parámetros")
    st.sidebar.caption("Al cambiar algo hay que volver a correr la simulación.")

    modelo = st.sidebar.radio(
        "Modelo",
        options=["real", "clasico"],
        format_func=lambda x: (
            "🏪 Estación real (12 caras · 5 productos · playeros)"
            if x == "real"
            else "📐 Caso clásico (3 surtidores · 1 producto)"
        ),
        help="La estación real es el caso del TP. El caso clásico es el proyecto "
             "hipotético original: reproduce sus números de referencia y sirve para "
             "comparar los escenarios de capacidad (+1 surtidor, +1 cajero).",
    )
    es_real = modelo == "real"
    base = ParametrosSimulacion() if es_real else ParametrosSimulacion.clasico()
    sfx = "_r" if es_real else "_c"     # las claves cambian con el modelo: cada uno con sus defaults

    # Si en la pestaña Inventario se apretó "Usar esta política", los valores se aplican
    # ACÁ, antes de crear los controles: Streamlit no permite modificar un widget que ya
    # fue instanciado en esta misma ejecución. (Sólo existe en el caso clásico.)
    sugerida = st.session_state.pop("politica_sugerida", None)
    if sugerida is not None and not es_real:
        st.session_state["w_punto_pedido"] = int(sugerida[0])
        st.session_state["w_cantidad_pedido"] = int(sugerida[1])
    # Lo mismo para la estación real: una política (s, Q) por tanque.
    sugerida_real = st.session_state.pop("politica_sugerida_real", None)
    if sugerida_real is not None and es_real:
        st.session_state["w_editar_politica"] = True
        for producto, (s_sug, q_sug) in sugerida_real.items():
            st.session_state[f"w_s_{producto}"] = int(round(s_sug, -2))
            st.session_state[f"w_q_{producto}"] = int(round(q_sug, -2))

    if es_real:
        with st.sidebar.expander("🏪 Estación y personal", expanded=True):
            st.markdown(
                f"12 caras en 3 zonas: **A nafta (4) · B diésel (2) · C GNC (6)** "
                f"{insignia_html(por_id('SUR-00'))}. Servidores = mín(caras libres, "
                f"playeros en turno).",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"**Playeros por turno** {insignia_html(por_id('PER-01'))}",
                unsafe_allow_html=True,
            )
            n1, n2, n3 = st.columns(3)
            playeros = (
                int(n1.number_input("Noche 22–06", 1, 6, base.playeros_por_turno[0], 1)),
                int(n2.number_input("Mañana 06–14", 1, 6, base.playeros_por_turno[1], 1)),
                int(n3.number_input("Tarde 14–22", 1, 6, base.playeros_por_turno[2], 1)),
            )
            cajas = st.number_input(
                "Cajas en el minimarket", 1, 4, base.cajas, 1,
                help="PER-02: una caja por turno.",
            )
            capacidad_cola = st.slider(
                "Capacidad de cola por zona (autos)", 2, 20, int(base.capacidad_cola), 1,
                help="PER-05 (sin dato: hay que relevarla). Si la cola de la zona está "
                     "llena, el auto no entra y se pierde por 'cola llena'.",
            )
            disciplina_cola = st.radio(
                "Disciplina de la cola",
                ["por_grupo", "por_cara"],
                index=0 if base.disciplina_cola == "por_grupo" else 1,
                format_func=lambda x: {
                    "por_grupo": "Una cola FIFO por zona",
                    "por_cara": "Una fila por cara (elige la más corta)",
                }[x],
                horizontal=True,
            )
            pct_gnc = st.slider(
                "Clientes GNC (% de las llegadas)", 0, 25, int(round(base.pct_gnc * 100)), 1,
                help="DEM-05 (estimación): el GNC es ≈ 3 % de los clientes, aunque se le "
                     "dedican 6 de las 12 caras (alerta de coherencia C8).",
            ) / 100.0
        surtidores = base.surtidores
    else:
        with st.sidebar.expander("🏪 Capacidad actual", expanded=True):
            st.markdown(
                f"Configuración clásica {insignia_html(por_id('REC-01'))}"
                f"{insignia_html(por_id('REC-02'))}: cola única FIFO, sin playeros.",
                unsafe_allow_html=True,
            )
            surtidores = st.number_input("Surtidores instalados", 1, 8, base.surtidores, 1)
            cajas = st.number_input("Cajas en el minimarket", 1, 4, base.cajas, 1)
        playeros = base.playeros_por_turno
        capacidad_cola = base.capacidad_cola
        disciplina_cola = base.disciplina_cola
        pct_gnc = base.pct_gnc

    # --- Demanda: litros por mes → clientes por día (corrige B1/B2/B5) ---
    with st.sidebar.expander("📊 Demanda", expanded=True):
        st.markdown(
            f"Fuentes {insignia_html(por_id('DEM-01'))} {insignia_html(por_id('DEM-11'))} "
            f"{insignia_html(por_id('DEM-06'))} {insignia_html(por_id('DEM-03'))}",
            unsafe_allow_html=True,
        )
        modo_demanda = st.radio(
            "Modo de demanda",
            options=["esperada", "monte_carlo"],
            index=0 if base.modo_demanda == "esperada" else 1,
            key="modo_demanda" + sfx,
            format_func=lambda x: (
                "Demanda esperada (litros por mes)"
                if x == "esperada"
                else (
                    "Monte Carlo (variación día a día)"
                    if es_real
                    else "Monte Carlo (tabla empírica)"
                )
            ),
            horizontal=True,
            help="Con 'esperada' el total diario sale de los litros por mes y el "
                 "calendario; con 'Monte Carlo' se sortea cada día un factor de una tabla "
                 "de frecuencias. En ambos modos las llegadas son Poisson y los tiempos "
                 "aleatorios, así que se mantienen las réplicas y el calentamiento.",
        )
        if modo_demanda == "esperada" or es_real:
            litros_mes = st.slider(
                "Demanda mensual (litros/mes)", 50_000, 600_000, int(base.litros_mes), 10_000,
                help="Es la variable de entrada: los clientes por día se derivan de "
                     "acá, nunca al revés.",
            )
        else:
            litros_mes = base.litros_mes
        if es_real:
            litros_medios_por_cliente = base.litros_medios_por_cliente
            dias_ref = dias_del_mes(1)
            clientes_dia = (litros_mes / dias_ref) / litros_medios_por_cliente
            st.caption(
                f"Litros medios por cliente de nafta/diésel: **{litros_medios_por_cliente:.1f} L** "
                f"(derivado de la mezcla de productos y vehículos). "
                f"≈ {litros_mes / dias_ref:,.0f} L/día ⇒ **{clientes_dia:,.0f} clientes "
                f"líquidos/día** (+ GNC)."
            )
        elif modo_demanda == "esperada":
            litros_medios_por_cliente = st.number_input(
                "Litros medios por cliente (L)", 5.0, 200.0, base.litros.media, 0.1,
                help="Litros que carga en promedio un cliente de combustible líquido.",
            )
            clientes_dia = (litros_mes / dias_del_mes(1)) / litros_medios_por_cliente
            st.caption(
                f"≈ {litros_mes / dias_del_mes(1):,.0f} L/día ⇒ **{clientes_dia:,.0f} "
                f"clientes/día**."
            )
        else:
            litros_medios_por_cliente = base.litros_medios_por_cliente

        horizonte = st.radio(
            "Horizonte de simulación",
            options=["dia", "semana", "mes", "estacion", "anio"],
            index=2,
            format_func=lambda x: {
                "dia": "📅 Un día",
                "semana": "📅 Una semana (7 días)",
                "mes": "📅 Un mes (calendario real)",
                "estacion": "📅 Una estación (90 días)",
                "anio": "📅 Un año (365 días)",
            }[x],
            horizontal=False,
        )
        mes_elegido = 1
        dia_elegido = 1
        estacion_elegida = "verano"
        if horizonte in ("dia", "semana"):
            c1, c2 = st.columns(2)
            mes_elegido = c1.selectbox("Mes de inicio", range(1, 13), index=0)
            dia_elegido = c2.selectbox("Día de inicio", range(1, 32), index=0)
        elif horizonte == "mes":
            mes_elegido = st.selectbox("Mes a simular", range(1, 13), index=0)
        elif horizonte == "estacion":
            estacion_elegida = st.selectbox(
                "Estación del año",
                ["verano", "otonio", "invierno", "primavera"],
                index=0,
                format_func=lambda x: {
                    "verano": "☀️ Verano (ene–mar)",
                    "otonio": "🍂 Otoño (abr–jun)",
                    "invierno": "❄️ Invierno (jun–ago)",
                    "primavera": "🌱 Primavera (sep–nov)",
                }[x],
            )
        try:
            fecha_inicio, dias_por_horizonte = dias_y_fecha(
                horizonte, mes_elegido, dia_elegido, estacion_elegida
            )
            # El día de inicio tiene que existir en ese mes (p. ej. no hay 31/4).
            ParametrosSimulacion(fecha_inicio=fecha_inicio)
        except ValueError:
            st.warning("Ese día no existe en el mes elegido: se usa el 1.")
            fecha_inicio, dias_por_horizonte = dias_y_fecha(
                horizonte, mes_elegido, 1, estacion_elegida
            )
        if modo_demanda == "esperada":
            presets = {
                "Neutra (default)": ESTACIONALIDAD_NEUTRA,
                "Leve (±6 %)": ESTACIONALIDAD_LEVE,
                "Proxy turístico": ESTACIONALIDAD_PROXY,
            }
            estacionalidad = presets[
                st.selectbox("Estacionalidad mensual", list(presets), index=0)
            ]
            factor_fin_de_semana = st.slider(
                "Factor de fin de semana", 1.0, 2.0, float(base.factor_fin_de_semana), 0.01,
                help="El finde vende más que un día hábil; el nivel diario se "
                     "normaliza para conservar los litros del mes.",
            )
        else:
            estacionalidad = ESTACIONALIDAD_NEUTRA
            factor_fin_de_semana = base.factor_fin_de_semana

    demanda = base.demanda
    if modo_demanda == "monte_carlo":
        if es_real:
            with st.sidebar.expander("🎲 Variación día a día (Monte Carlo)"):
                rel = base.demanda_relativa
                st.markdown(
                    f"Fuente {insignia_html(por_id('DEM-07'))}: cada día se sortea un "
                    f"**factor relativo** (media 1) que multiplica los litros del día.",
                    unsafe_allow_html=True,
                )
                st.dataframe(
                    pd.DataFrame(
                        {"Factor": rel.valores, "Frecuencia": rel.frecuencias}
                    ),
                    hide_index=True,
                )
        else:
            with st.sidebar.expander("🚗 Demanda diaria (tabla Monte Carlo)"):
                st.caption(
                    "Tabla de frecuencias observada: en cuántos días se registró cada nivel "
                    "de demanda. De acá se sortea la demanda de cada día simulado."
                )
                tabla = st.data_editor(
                    pd.DataFrame(
                        {"Autos por día": list(base.demanda.valores),
                         "Días observados": list(base.demanda.frecuencias)}
                    ),
                    num_rows="dynamic",
                    hide_index=True,
                    key="tabla_demanda",
                )
                demanda = construir_demanda(tabla)
                st.caption(f"Demanda media: **{demanda.media:.0f} autos por día**")

    with st.sidebar.expander("⏱️ Tiempos de servicio"):
        st.markdown(
            f"Fuentes {insignia_html(por_id('TIE-02'))} {insignia_html(por_id('TIE-05'))}"
            + (f" {insignia_html(por_id('TIE-04'))}" if es_real else ""),
            unsafe_allow_html=True,
        )
        st.markdown(
            "**Carga de nafta/diésel** — Triangular (min)" if es_real
            else "**Carga de combustible** — Triangular (min)"
        )
        c1, c2, c3 = st.columns(3)
        carga = Triangular(
            c1.number_input("mín", 0.5, 30.0, base.carga.minimo, 0.5, key="carga_min" + sfx),
            c2.number_input("moda", 0.5, 30.0, base.carga.moda, 0.5, key="carga_moda" + sfx),
            c3.number_input("máx", 0.5, 30.0, base.carga.maximo, 0.5, key="carga_max" + sfx),
        )
        if es_real:
            st.markdown("**Carga de GNC** — Triangular (min)")
            g1, g2, g3 = st.columns(3)
            carga_gnc = Triangular(
                g1.number_input("mín", 0.5, 60.0, base.carga_gnc.minimo, 0.5, key="gnc_min"),
                g2.number_input("moda", 0.5, 60.0, base.carga_gnc.moda, 0.5, key="gnc_moda"),
                g3.number_input("máx", 0.5, 60.0, base.carga_gnc.maximo, 0.5, key="gnc_max"),
            )
        else:
            carga_gnc = base.carga_gnc
        st.markdown("**Compra en el minimarket** (min)")
        d1, d2, d3 = st.columns(3)
        compra = Triangular(
            d1.number_input("mín", 0.2, 30.0, base.compra.minimo, 0.5, key="compra_min" + sfx),
            d2.number_input("moda", 0.2, 30.0, base.compra.moda, 0.5, key="compra_moda" + sfx),
            d3.number_input("máx", 0.2, 30.0, base.compra.maximo, 0.5, key="compra_max" + sfx),
        )
        caja_exponencial = st.checkbox(
            "Usar Exponencial en la caja", value=False,
            help="La propuesta admite Triangular o Exponencial para el tiempo en caja. "
                 "Con Exponencial se usa la misma media que la triangular cargada.",
        )

    if es_real:
        litros = base.litros
        with st.sidebar.expander("⛽ Litros por carga"):
            st.markdown(
                f"Fuentes {insignia_html(por_id('VEH-01'))} {insignia_html(por_id('VEH-00'))}: "
                f"cada cliente sortea producto y tipo de vehículo, y carga "
                f"`Triangular(0,2·T ; 0,3·T ; 1,0·T)` (tanque T del vehículo). Las tablas "
                f"están en la pestaña **Demanda**.",
                unsafe_allow_html=True,
            )
    else:
        with st.sidebar.expander("⛽ Litros por carga"):
            st.markdown(
                f"Fuente {insignia_html(por_id('VEH-06'))}",
                unsafe_allow_html=True,
            )
            st.caption("Cuánto carga cada auto. Es lo que consume el tanque.")
            e1, e2, e3 = st.columns(3)
            litros = Triangular(
                e1.number_input("mín", 1.0, 200.0, base.litros.minimo, 5.0, key="litros_min"),
                e2.number_input("moda", 1.0, 200.0, base.litros.moda, 5.0, key="litros_moda"),
                e3.number_input("máx", 1.0, 200.0, base.litros.maximo, 5.0, key="litros_max"),
            )

    with st.sidebar.expander("🧍 Comportamiento del cliente"):
        st.markdown(
            f"Fuentes {insignia_html(por_id('DEM-08'))} {insignia_html(por_id('TIE-06'))}",
            unsafe_allow_html=True,
        )
        prob_compra = st.slider(
            "Probabilidad de entrar al minimarket", 0.0, 1.0, float(base.prob_compra), 0.05,
            key="prob_compra" + sfx,
            help="Ensayo de Bernoulli después de cargar combustible.",
        )
        paciencia_surtidor = st.slider(
            "Paciencia en la cola del surtidor (min)", 1.0, 30.0,
            float(base.paciencia_surtidor), 1.0,
            help="Si la espera supera este umbral, el cliente abandona y se pierde la venta.",
        )
        paciencia_caja = st.slider(
            "Paciencia en la cola de la caja (min)", 1.0, 30.0, float(base.paciencia_caja), 1.0
        )

    # --- Tanques y reposición ---
    if es_real:
        with st.sidebar.expander("🛢️ Tanques y reposición", expanded=True):
            st.markdown(
                f"Fuentes {insignia_html(por_id('INV-03'))} {insignia_html(por_id('INV-07'))} "
                f"{insignia_html(por_id('INV-01'))}: un tanque por producto líquido; la "
                f"política (s, Q) de cada uno se deriva de su consumo (INV-07).",
                unsafe_allow_html=True,
            )
            capacidad_tanque = st.number_input(
                "Capacidad de cada tanque (L)", 5_000, 100_000,
                int(base.inventario[0].capacidad), 5_000,
            )
            nivel_inicial_pct = st.slider(
                "Nivel inicial (% del tanque)", 10, 100,
                int(round(base.inventario[0].nivel_inicial / base.inventario[0].capacidad * 100)),
                5,
            ) / 100.0
            st.markdown("**Plazo de entrega del camión** — Triangular (horas)")
            plazo_base = base.inventario[0].plazo_entrega
            f1, f2, f3 = st.columns(3)
            plazo = Triangular(
                f1.number_input("mín", 1.0, 200.0, plazo_base.minimo, 1.0, key="plazo_min"),
                f2.number_input("moda", 1.0, 200.0, plazo_base.moda, 1.0, key="plazo_moda"),
                f3.number_input("máx", 1.0, 200.0, plazo_base.maximo, 1.0, key="plazo_max"),
            )
            inventario = inventario_real(
                float(litros_mes), float(capacidad_tanque), plazo, float(nivel_inicial_pct)
            )
            nombres = {x.id: x.nombre for x in base.productos}
            editar = st.checkbox(
                "Editar la política (s, Q) de cada tanque",
                key="w_editar_politica",
                help="Sin tildar, s y Q salen de INV-07 (s = 1,5 días de consumo del "
                     "producto). En la pestaña Inventario se busca la mejor por producto.",
            )
            if editar:
                editados = []
                for inv in inventario:
                    st.markdown(f"**{nombres[inv.producto]}**")
                    c_s, c_q = st.columns(2)
                    tope = int(capacidad_tanque)
                    s_nuevo = c_s.number_input(
                        "s (L)", 0, tope, min(int(round(inv.punto_pedido, -2)), tope), 100,
                        key=f"w_s_{inv.producto}",
                    )
                    q_nuevo = c_q.number_input(
                        "Q (L)", 500, tope, min(int(round(inv.cantidad_pedido, -2)), tope), 100,
                        key=f"w_q_{inv.producto}",
                    )
                    editados.append(
                        replace(inv, punto_pedido=float(s_nuevo), cantidad_pedido=float(q_nuevo))
                    )
                inventario = tuple(editados)
            else:
                st.dataframe(
                    pd.DataFrame(
                        {
                            "Tanque": [nombres[i.producto] for i in inventario],
                            "s (L)": [round(i.punto_pedido) for i in inventario],
                            "Q (L)": [round(i.cantidad_pedido) for i in inventario],
                        }
                    ),
                    hide_index=True,
                )
            st.caption(
                "Política inicial según INV-07 (s = 1,5 días de consumo del producto). "
                "La mejor por producto se busca en la pestaña Inventario."
            )
        tanque = base.tanque
    else:
        with st.sidebar.expander("🛢️ Tanque y reposición", expanded=True):
            st.markdown(
                f"Fuentes {insignia_html(por_id('INV-03'))} {insignia_html(por_id('INV-07'))} "
                f"{insignia_html(por_id('INV-01'))}",
                unsafe_allow_html=True,
            )
            capacidad = st.number_input(
                "Capacidad del tanque (L)", 5_000, 200_000, int(base.tanque.capacidad), 5_000
            )
            nivel_inicial = st.number_input(
                "Nivel inicial (L)", 0, int(capacidad), int(base.tanque.nivel_inicial), 1_000
            )
            punto_pedido = st.number_input(
                "Punto de pedido s (L)", 0, int(capacidad), int(base.tanque.punto_pedido), 1_000,
                key="w_punto_pedido",
                help="Cuando el combustible disponible (lo que hay más lo que viene en "
                     "camino) baja de este valor, se pide un camión.",
            )
            cantidad_pedido = st.number_input(
                "Cantidad a pedir Q (L)", 1_000, int(capacidad),
                int(base.tanque.cantidad_pedido), 1_000,
                key="w_cantidad_pedido",
                help="Cuántos litros trae cada camión cisterna.",
            )
            st.markdown("**Plazo de entrega del camión** — Triangular (horas)")
            f1, f2, f3 = st.columns(3)
            plazo = Triangular(
                f1.number_input("mín", 1.0, 200.0, base.tanque.plazo_entrega.minimo, 1.0,
                                key="plazo_min_c"),
                f2.number_input("moda", 1.0, 200.0, base.tanque.plazo_entrega.moda, 1.0,
                                key="plazo_moda_c"),
                f3.number_input("máx", 1.0, 200.0, base.tanque.plazo_entrega.maximo, 1.0,
                                key="plazo_max_c"),
            )
        tanque = ParametrosTanque(
            capacidad=float(capacidad),
            nivel_inicial=float(nivel_inicial),
            punto_pedido=float(punto_pedido),
            cantidad_pedido=float(cantidad_pedido),
            plazo_entrega=plazo,
        )
        inventario = base.inventario

    # --- Ruta del camión y cortes (sólo la estación real) ---
    red = None
    if es_real:
        with st.sidebar.expander("🛣️ Ruta del camión y cortes"):
            st.markdown(
                f"Fuentes {insignia_html(por_id('INV-05'))} {insignia_html(por_id('RED-12'))} "
                f"{insignia_html(por_id('RED-13'))}: el camión sale del origen por el camino "
                f"más corto; un corte en ese camino demora el viaje (desvío o espera, lo menor).",
                unsafe_allow_html=True,
            )
            origen = st.radio(
                "Origen del camión",
                ["DOCK", "LUJAN"],
                index=0 if base.red.origen == "DOCK" else 1,
                format_func=lambda x: {
                    "DOCK": "Dock Sud (991 km por Gral. Alvear)",
                    "LUJAN": "Luján de Cuyo (planta YPF)",
                }[x],
            )
            opciones = ["ninguno", "aleatorio"] + [c.id for c in base.red.cortes]
            nombres_corte = {c.id: f"{c.id} · {c.nombre}" for c in base.red.cortes}
            escenario = st.selectbox(
                "Escenario de cortes",
                opciones,
                index=opciones.index(base.red.escenario_corte),
                format_func=lambda x: ETIQUETA_ESCENARIO.get(x) or nombres_corte[x],
            )
            corte_dia = min(base.red.corte_dia, int(dias_por_horizonte))
            if escenario in ("E1", "E2", "E4") and dias_por_horizonte > 1:
                corte_dia = st.slider(
                    "Día en que empieza el corte", 1, int(dias_por_horizonte), int(corte_dia), 1,
                    help="Arranca a las 00:00 de ese día; los camiones que salen mientras "
                         "dura se desvían o esperan.",
                )
            prob_corte = base.red.prob_corte_viaje
            if escenario == "aleatorio":
                prob_corte = st.slider(
                    "Probabilidad de que un viaje encuentre un corte", 0, 60,
                    int(round(prob_corte * 100)), 5,
                    help="Sólo en jun–ago (RED-13, supuesto): fuera de invierno no hay cortes.",
                ) / 100.0
                if not set(base.red.meses_corte) & dias_de_mes_en_corrida(
                    fecha_inicio, int(dias_por_horizonte)
                ):
                    st.caption(
                        "⚠️ Este horizonte no incluye jun–ago: no se sortea ningún corte. "
                        "Elegí 'Una estación → Invierno' o un mes de invierno."
                    )
            velocidad = st.slider(
                "Velocidad media del camión (km/h)", 40, 90, int(base.red.velocidad_kmh), 5,
                help="RED-11 (supuesto): entre los 80 km/h legales y los 60 urbanos.",
            )
            red = replace(
                base.red,
                origen=origen,
                escenario_corte=escenario,
                corte_dia=int(corte_dia),
                prob_corte_viaje=float(prob_corte),
                velocidad_kmh=float(velocidad),
            )

    # --- GNC: cortes de invierno, compresores y migración (sólo la estación real) ---
    gnc = None
    if es_real:
        with st.sidebar.expander("🔥 GNC y cortes de invierno"):
            st.markdown(
                f"Fuentes {insignia_html(por_id('GNC-01'))} {insignia_html(por_id('GNC-02'))} "
                f"{insignia_html(por_id('GNC-04'))} {insignia_html(por_id('SUR-06'))}: con "
                f"contrato interrumpible, en jun–ago el GNC se corta por episodios (corte "
                f"TOTAL, no −50 %).",
                unsafe_allow_html=True,
            )
            g0 = base.gnc
            contrato = st.radio(
                "Contrato de gas",
                ["interrumpible", "firme"],
                index=0 if g0.contrato == "interrumpible" else 1,
                format_func=lambda x: {
                    "interrumpible": "Interrumpible (sufre los cortes)",
                    "firme": "Firme (sin cortes)",
                }[x],
                horizontal=True,
            )
            episodios = st.slider(
                "Episodios de corte por invierno", 0, 4, int(g0.episodios), 1,
                disabled=contrato == "firme",
            )
            dias_episodio = st.slider(
                "Duración de cada episodio (días)", 1, 14, int(g0.dias_por_episodio), 1,
                disabled=contrato == "firme",
            )
            forma = st.selectbox(
                "Forma del corte",
                ["total_24h", "ventana", "parcial_50"],
                index=["total_24h", "ventana", "parcial_50"].index(g0.forma),
                format_func=lambda x: {
                    "total_24h": "Corte total de 24 h (ENARGAS)",
                    "ventana": "Ventana de 17 a 01 h (San Rafael 2022)",
                    "parcial_50": "Compresores al 50 % (sin fuente)",
                }[x],
                disabled=contrato == "firme",
            )
            compresores = st.slider(
                "Compresores (cargas GNC simultáneas)", 1, 6, int(g0.compresores), 1,
                help="SUR-06 (supuesto, sin dato): derivado de 20–25 autos/h × 7 min ÷ 60.",
            )
            migracion = st.slider(
                "Clientes que pasan a Súper durante el corte (%)", 0, 100,
                int(round(g0.migracion_a_nafta * 100)), 5,
                help="GNC-04 (supuesto): no hay migración documentada. Los demás se pierden.",
            ) / 100.0
            en_horizonte = st.checkbox(
                "Forzar que los episodios caigan dentro del horizonte",
                value=bool(g0.episodios_en_horizonte),
                disabled=contrato == "firme",
                help="Sin tildar, los episodios se sortean entre el 1/jun y el 31/ago: un "
                     "horizonte que no incluye invierno no ve ninguno.",
            )
            gnc = ParametrosGNC(
                contrato=contrato,
                episodios=int(episodios),
                dias_por_episodio=int(dias_episodio),
                forma=forma,
                compresores=int(compresores),
                migracion_a_nafta=float(migracion),
                episodios_en_horizonte=bool(en_horizonte),
            )

    with st.sidebar.expander("🔬 Corrida"):
        st.info(
            f"Horizonte **{horizonte}**: desde el {fecha_inicio[1]}/{fecha_inicio[0]}, "
            f"**{dias_por_horizonte} días**."
        )
        dias = dias_por_horizonte
        max_calentamiento = max(0, dias - 1)
        if max_calentamiento == 0:
            # Un horizonte de un solo día no tiene lugar para calentar.
            dias_calentamiento = 0
            st.caption("(Sin calentamiento: la corrida dura un solo día)")
        else:
            dias_calentamiento = st.slider(
                "Días de calentamiento", 0, max_calentamiento,
                min(base.dias_calentamiento, max_calentamiento), 1,
                key="calentamiento" + sfx,
                help="Días que se simulan pero no se miden: la estación arranca con las colas "
                     "vacías y el tanque al 75 %, que no es su estado habitual.",
            )

        # El día se elige en la pestaña Animación; por defecto, el primero que se mide.
        dia_animado = min(int(dias_calentamiento) + 1, int(dias))
        replicas = st.slider(
            "Réplicas por escenario", 2, 15, 4, 1,
            help="Cada réplica es una corrida completa con otra semilla. Más réplicas dan "
                 "intervalos de confianza más angostos, pero tardan más.",
        )
        semilla = st.number_input("Semilla", 1, 99_999, 1, 1)

    with st.sidebar.expander("💵 Datos económicos"):
        st.markdown(
            f"Fuentes {insignia_html(por_id('ECO-01'))} {insignia_html(por_id('ECO-02'))} "
            f"{insignia_html(por_id('ECO-06'))} {insignia_html(por_id('ECO-04C'))} "
            f"(márgenes y flete son heredados sin fuente: placeholders visibles).",
            unsafe_allow_html=True,
        )
        st.caption("Valores estimados: hay que reemplazarlos por los datos reales.")
        margen_por_litro = st.number_input("Ganancia por litro ($)", 0.0, 1e6, 100.0, 10.0)
        margen_compra = st.number_input(
            "Ganancia por compra en minimarket ($)", 0.0, 1e7, 2500.0, 100.0
        )
        costo_pedido = st.number_input(
            "Flete por camión cisterna ($)", 0.0, 1e8, 150_000.0, 10_000.0
        )
        costo_almacenamiento = st.number_input(
            "Costo de almacenamiento ($/litro/mes)", 0.0, 1e4, 25.0, 5.0,
            help="Capital inmovilizado en combustible: se aplica al nivel promedio del tanque.",
        )
        inversion_surtidor = st.number_input(
            "Inversión: surtidor nuevo ($)", 0.0, 1e9, 18_000_000.0, 500_000.0
        )
        operativo_surtidor = st.number_input(
            "Costo operativo del surtidor ($/mes)", 0.0, 1e8, 250_000.0, 50_000.0
        )
        sueldo_cajero = st.number_input("Sueldo de un cajero ($/mes)", 0.0, 1e8, 1_800_000.0, 50_000.0)

    comunes = dict(
        cajas=int(cajas),
        demanda=demanda,
        carga=carga,
        carga_gnc=carga_gnc,
        compra=compra,
        caja_exponencial=bool(caja_exponencial),
        litros=litros,
        prob_compra=float(prob_compra),
        paciencia_surtidor=float(paciencia_surtidor),
        paciencia_caja=float(paciencia_caja),
        dias=int(dias),
        dias_calentamiento=int(dias_calentamiento),
        dia_animado=int(dia_animado),
        modo_demanda=str(modo_demanda),
        litros_mes=float(litros_mes),
        litros_medios_por_cliente=float(litros_medios_por_cliente),
        factor_fin_de_semana=float(factor_fin_de_semana),
        estacionalidad=estacionalidad,
        fecha_inicio=fecha_inicio,
        horizonte=str(horizonte),
    )
    if es_real:
        p = replace(
            base,
            playeros_por_turno=playeros,
            turnos=turnos_de(playeros),
            capacidad_cola=int(capacidad_cola),
            disciplina_cola=str(disciplina_cola),
            pct_gnc=float(pct_gnc),
            inventario=inventario,
            red=red,
            gnc=gnc,
            **comunes,
        )
    else:
        p = replace(base, surtidores=int(surtidores), tanque=tanque, **comunes)
    eco = ParametrosEconomicos(
        margen_por_litro=margen_por_litro,
        margen_compra=margen_compra,
        inversion_surtidor=inversion_surtidor,
        operativo_surtidor_mensual=operativo_surtidor,
        sueldo_cajero_mensual=sueldo_cajero,
        costo_pedido=costo_pedido,
        costo_almacenamiento_litro_mes=costo_almacenamiento,
    )
    return p, eco, int(replicas), int(semilla)


def construir_demanda(tabla: pd.DataFrame) -> DemandaDiaria:
    """Arma la tabla empírica a partir de lo que cargó el usuario, validando."""
    try:
        filas = [
            (int(v), int(f))
            for v, f in zip(tabla["Autos por día"], tabla["Días observados"])
            if pd.notna(v) and pd.notna(f) and int(f) > 0 and int(v) >= 0
        ]
        if not filas:
            raise ValueError("tabla vacía")
        filas.sort()
        return DemandaDiaria(
            valores=tuple(v for v, _ in filas), frecuencias=tuple(f for _, f in filas)
        )
    except Exception:
        st.sidebar.error(
            "La tabla de demanda no es válida (hacen falta autos por día y días "
            "observados positivos). Se usa la tabla por defecto."
        )
        return DemandaDiaria(valores=(280, 320, 360, 400, 440), frecuencias=(10, 20, 40, 20, 10))


# =============================================================================
# Pestaña: animación
# =============================================================================
def pestania_animacion(p: ParametrosSimulacion) -> None:
    c1, c2 = st.columns([2, 3])
    if p.dias > 1:
        dia = c1.slider(
            "Día a animar", 1, min(p.dias, 90), min(p.dia_animado, p.dias), 1,
            help="Se anima un día completo. Los primeros días son de calentamiento "
                 "(se simulan pero no se miden).",
        )
    else:
        dia = 1
    traza = correr_traza_cacheada(replace(p, dia_animado=int(dia)), st.session_state.semilla_usada)
    c2.markdown(f"**{animacion.fecha_texto(p, int(dia))}**")
    if dia <= p.dias_calentamiento:
        c2.caption("Este día es de calentamiento: el sistema todavía no está en régimen.")

    if p.estacion_real:
        st.caption(
            "Estación real: avenida Balloffet, playón techado con las zonas A (nafta), B "
            "(diésel) y C (GNC), playeros, minimarket, un tanque por producto y el camión "
            "en viaje. Cada auto tiene el color de su producto."
        )
    else:
        st.caption(
            f"Caso clásico ({p.surtidores} surtidores, {p.cajas} caja/s, un solo tanque). "
            f"Se anima un día completo, de 00:00 a 24:00."
        )

    componentes.html(
        animacion.reproductor_html(traza, p, int(dia), animacion.fecha_texto(p, int(dia))),
        height=animacion.ALTO_COMPONENTE,
    )

    st.divider()
    caras = sum(g.caras for g in p.grupos) if p.estacion_real else p.surtidores
    g1, g2 = st.columns(2)
    g1.plotly_chart(graficos.grafico_evolucion_colas(traza, int(dia)), key="g_colas")
    g2.plotly_chart(graficos.grafico_ocupacion(traza, caras, int(dia)), key="g_ocupacion")


# =============================================================================
# Pestaña: indicadores
# =============================================================================
def tarjeta(columna, metrica: Metrica, resultado: ResultadoEscenario) -> None:
    """Una tarjeta con el promedio de la métrica y su intervalo de confianza."""
    resumen = resultado.resumen[metrica.clave]
    valor = metrica.valor_mostrado(resumen.promedio)
    semi = metrica.valor_mostrado(resumen.semiamplitud)

    columna.metric(
        metrica.etiqueta,
        f"{valor:,.{metrica.decimales}f} {metrica.unidad_mostrada}".strip(),
        delta=f"± {semi:,.{metrica.decimales}f} (IC 95 %)",
        delta_color="off",
        help=metrica.ayuda,
        border=True,
    )


def tabla_detalle(base: ResultadoEscenario, metricas) -> pd.DataFrame:
    filas = []
    for metrica in metricas:
        resumen = base.resumen[metrica.clave]
        filas.append(
            {
                "Indicador": metrica.etiqueta,
                "Promedio": round(metrica.valor_mostrado(resumen.promedio), metrica.decimales),
                "IC 95 % (±)": round(
                    metrica.valor_mostrado(resumen.semiamplitud), metrica.decimales
                ),
                "Mínimo": round(metrica.valor_mostrado(resumen.minimo), metrica.decimales),
                "Máximo": round(metrica.valor_mostrado(resumen.maximo), metrica.decimales),
                "Unidad": metrica.unidad_mostrada,
            }
        )
    return pd.DataFrame(filas)


def promedio_tupla(resultado: ResultadoEscenario, campo: str) -> list[float]:
    """Promedio entre réplicas de un campo que es una tupla (por grupo)."""
    columnas = zip(*[getattr(r, campo) for r in resultado.replicas])
    return [sum(c) / len(resultado.replicas) for c in columnas]


def promedio_pares(resultado: ResultadoEscenario, campo: str) -> dict[str, float]:
    """Promedio entre réplicas de un campo que es ((producto, valor), ...)."""
    acumulado: dict[str, float] = {}
    for r in resultado.replicas:
        for clave, valor in getattr(r, campo):
            acumulado[clave] = acumulado.get(clave, 0.0) + valor
    return {k: v / len(resultado.replicas) for k, v in acumulado.items()}


def tablas_real(p: ParametrosSimulacion, base: ResultadoEscenario) -> None:
    """Indicadores por zona y por producto de la estación real."""
    st.markdown("##### Por zona de surtidores")
    esperas = promedio_tupla(base, "espera_por_grupo")
    colas = promedio_tupla(base, "cola_por_grupo")
    utils = promedio_tupla(base, "util_por_grupo")
    st.dataframe(
        pd.DataFrame(
            {
                "Zona": [f"{g.id} · {g.nombre}" for g in p.grupos],
                "Caras": [g.caras for g in p.grupos],
                "Espera hasta ser atendido (min)": [round(x, 2) for x in esperas],
                "Cola promedio (autos)": [round(x, 3) for x in colas],
                "Utilización de las caras": [f"{x * 100:.1f} %" for x in utils],
            }
        ),
        hide_index=True,
    )
    st.markdown("##### Por producto")
    atendidos = promedio_pares(base, "atendidos_por_producto")
    litros = promedio_pares(base, "litros_vendidos_por_producto")
    quiebres = promedio_pares(base, "dias_quiebre_por_producto")
    st.dataframe(
        pd.DataFrame(
            {
                "Producto": [pr.nombre for pr in p.productos],
                "Clientes atendidos/día": [round(atendidos[pr.id], 1) for pr in p.productos],
                "Vendido por día": [
                    f"{litros[pr.id]:,.0f} {'m³' if pr.es_gnc else 'L'}" for pr in p.productos
                ],
                "Días con quiebre": [
                    "—" if pr.es_gnc else f"{quiebres[pr.id]:.1f} %" for pr in p.productos
                ],
            }
        ),
        hide_index=True,
    )
    st.caption(
        "El GNC se mide en **m³**, no en litros, y todavía no tiene cortes de invierno "
        "(Fase 6). Los litros de la estación suman sólo los 4 combustibles líquidos."
    )


def pestania_indicadores(p: ParametrosSimulacion) -> None:
    base = buscar(st.session_state.resultados, "Base")

    if p.estacion_real:
        st.subheader("Indicadores de la estación real")
    else:
        st.subheader("Indicadores del escenario Base (situación actual)")
    st.caption(
        f"Promedio de {st.session_state.replicas} réplicas de {p.dias} días, descartando "
        f"{p.dias_calentamiento} día/s de calentamiento."
    )

    st.markdown("##### Líneas de espera")
    fila = st.columns(4)
    for columna, metrica in zip(fila, INDICADORES_COLAS[:4]):
        tarjeta(columna, metrica, base)

    st.markdown("##### Inventario")
    fila = st.columns(4)
    for columna, metrica in zip(fila, INDICADORES_INVENTARIO[:4]):
        tarjeta(columna, metrica, base)

    st.markdown("##### Clientes")
    fila = st.columns(4)
    for columna, metrica in zip(fila, INDICADORES_CLIENTES[:4]):
        tarjeta(columna, metrica, base)

    if p.estacion_real:
        st.markdown("##### Playeros y cola")
        fila = st.columns(4)
        for columna, metrica in zip(
            fila, (POR_CLAVE["util_playeros"], POR_CLAVE["perdidos_cola_llena_dia"])
        ):
            tarjeta(columna, metrica, base)
        fila[2].metric(
            "ρ analítico en la hora pico",
            f"{p.rho_pico:.2f}",
            help="ρ = λ_pico · E[servicio] ÷ playeros del turno más cargado "
                 "(sólo nafta y diésel usan playero). ρ ≥ 1 ⇒ la cola crece sin parar.",
            border=True,
        )
        tablas_real(p, base)

    # Diagnóstico automático
    utilizacion = base.prom("util_surtidores")
    espera_pico = base.prom("espera_pico")
    perdidos_cola = base.prom("perdidos_cola_dia")
    perdidos_nafta = base.prom("perdidos_sin_combustible_dia")

    if perdidos_nafta > perdidos_cola * 1.5:
        st.error(
            f"Se pierden más clientes por falta de combustible ({perdidos_nafta:.1f} por día) "
            f"que por cola larga ({perdidos_cola:.1f} por día). El cuello de botella está en "
            f"el abastecimiento, no en la cantidad de surtidores.",
            icon="🛢️",
        )
    elif perdidos_cola > perdidos_nafta * 1.5:
        st.warning(
            f"Se pierden más clientes por cola larga ({perdidos_cola:.1f} por día) que por "
            f"falta de combustible ({perdidos_nafta:.1f} por día). El cuello de botella es "
            f"la capacidad de atención.",
            icon="🚗",
        )

    if utilizacion < 0.5 and espera_pico > 2.0:
        if p.estacion_real:
            st.info(
                f"Ojo con el promedio: las caras están ocupadas apenas el "
                f"{utilizacion * 100:.0f} % del tiempo y los playeros el "
                f"{base.prom('util_playeros') * 100:.0f} %, pero en la hora pico se espera "
                f"{espera_pico:.1f} min. El cuello no son las caras sino los playeros en "
                f"las horas pico.",
                icon="⏰",
            )
        else:
            st.info(
                f"Ojo con el promedio: los surtidores están ocupados apenas el "
                f"{utilizacion * 100:.0f} % del tiempo, pero en la hora pico se espera "
                f"{espera_pico:.1f} min. El problema no es de capacidad total sino de "
                f"concentración horaria.",
                icon="⏰",
            )

    st.divider()
    st.subheader("Detalle completo")
    t1, t2, t3, t4 = st.tabs(["Colas", "Clientes", "Inventario", "Complementarios"])
    t1.dataframe(tabla_detalle(base, INDICADORES_COLAS), hide_index=True)
    t2.dataframe(tabla_detalle(base, INDICADORES_CLIENTES), hide_index=True)
    t3.dataframe(tabla_detalle(base, INDICADORES_INVENTARIO), hide_index=True)
    t4.dataframe(tabla_detalle(base, INDICADORES_COMPLEMENTARIOS), hide_index=True)


# =============================================================================
# Pestaña: demanda (Monte Carlo)
# =============================================================================
def tabla_monte_carlo(etiquetas: list[str], pesos_sorteo: tuple[float, ...],
                      titulo_columna: str) -> pd.DataFrame:
    """Los pasos 1 a 3 del Monte Carlo (probabilidad, acumulada, intervalo) de un sorteo."""
    tabla = DemandaDiaria(
        valores=tuple(range(len(etiquetas))),
        frecuencias=tuple(max(1, int(round(w * 10_000))) for w in pesos_sorteo),
    )
    return pd.DataFrame(
        {
            titulo_columna: etiquetas,
            "Probabilidad": [f"{x * 100:.1f} %" for x in tabla.probabilidades],
            "Acumulada": [f"{x:.3f}" for x in tabla.acumuladas],
            "Intervalo de números aleatorios": [
                tabla.intervalo_texto(i) for i in range(len(etiquetas))
            ],
        }
    )


def pestania_demanda_real(p: ParametrosSimulacion) -> None:
    """Litros/mes → clientes/día, y los dos Monte Carlo de 5 pasos de la estación real."""
    traza = st.session_state.traza
    mes_inicio = p.fecha_inicio[0]

    st.subheader("De los litros por mes a los clientes por día")
    st.markdown(
        "La demanda de entrada son **litros por mes**; los clientes por día **se derivan** "
        "(nunca al revés: dividir litros por 30 y llamarlo 'autos' fue el error B1)."
    )
    litros_dia = p.litros_mes / dias_del_mes(mes_inicio)
    liquidos_dia = litros_dia / p.litros_medios_por_cliente
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Litros por mes", f"{p.litros_mes:,.0f} L", border=True)
    c2.metric(f"Litros por día (mes {mes_inicio})", f"{litros_dia:,.0f} L", border=True)
    c3.metric(
        "Clientes de nafta/diésel por día", f"{liquidos_dia:,.0f}",
        help=f"÷ {p.litros_medios_por_cliente:.1f} L medios por cliente líquido (§14.2).",
        border=True,
    )
    c4.metric("Con GNC (llegadas totales)", f"{p.autos_por_dia:,.0f}", border=True)

    pesos_llegada = p.pesos_llegada()
    st.markdown("##### Monte Carlo 1: ¿qué producto carga cada cliente?")
    st.caption(
        "Pasos 1 a 3: la probabilidad de cada producto sale de **litros ÷ carga media** "
        "(más litros por cliente ⇒ menos clientes), y el GNC entra como el "
        f"{p.pct_gnc:.0%} de las llegadas."
    )
    tabla_producto = tabla_monte_carlo(
        [pr.nombre for pr in p.productos], pesos_llegada, "Producto"
    )
    tabla_producto.insert(
        1, "% de los litros",
        [("—" if pr.es_gnc else f"{pr.pct_litros * 100:.1f} %") for pr in p.productos],
    )
    tabla_producto.insert(
        2, "Carga media",
        [f"{pr.carga_media:.1f} {'m³' if pr.es_gnc else 'L'}" for pr in p.productos],
    )
    st.dataframe(tabla_producto, hide_index=True)

    st.markdown("##### Monte Carlo 2: ¿qué vehículo es, dado el producto?")
    st.caption(
        "Segunda tabla, condicionada al producto (supuesto VEH-00). El tipo fija el "
        "tanque T, y los litros salen de `Triangular(0,2·T ; 0,3·T ; 1,0·T)`."
    )
    nombres_tipo = ("moto", "auto", "pick-up", "camión")
    filas = []
    for producto, pesos_tipo in p.matriz_tipos:
        nombre = next(pr.nombre for pr in p.productos if pr.id == producto)
        tabla = DemandaDiaria(
            valores=tuple(range(len(pesos_tipo))),
            frecuencias=tuple(int(round(w * 10_000)) for w in pesos_tipo),
        )
        fila = {"Producto": nombre}
        for i, tipo in enumerate(nombres_tipo):
            fila[tipo] = (
                f"{pesos_tipo[i] * 100:.0f} % ({tabla.intervalo_texto(i)})"
                if pesos_tipo[i] > 0 else "—"
            )
        filas.append(fila)
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    st.dataframe(
        pd.DataFrame(
            {
                "Tipo": [t.id.replace("_", " ") for t in p.tipos_vehiculo],
                "Tanque": [f"{t.tanque:g} {'m³' if t.es_gnc else 'L'}" for t in p.tipos_vehiculo],
                "Carga (mín · moda · máx)": [
                    f"{t.litros.minimo:.1f} · {t.litros.moda:.1f} · {t.litros.maximo:.1f}"
                    for t in p.tipos_vehiculo
                ],
                "Carga media": [
                    f"{t.litros.media:.1f} {'m³' if t.es_gnc else 'L'}" for t in p.tipos_vehiculo
                ],
            }
        ),
        hide_index=True,
    )

    st.markdown("##### Día a día de la corrida")
    dias = pd.DataFrame(
        {
            "Día": [x.dia for x in traza.dias],
            "Número aleatorio": [x.numero_texto for x in traza.dias],
            "Clientes del día": [x.autos_sorteados for x in traza.dias],
            "Llegaron": [x.autos_llegados for x in traza.dias],
            "Atendidos": [x.atendidos for x in traza.dias],
            "Perdidos por espera": [x.perdidos_cola for x in traza.dias],
            "Perdidos sin combustible": [x.perdidos_sin_combustible for x in traza.dias],
            "Litros vendidos": [round(x.litros_vendidos) for x in traza.dias],
            "Quiebre": ["sí" if x.hubo_quiebre else "" for x in traza.dias],
            "Calentamiento": ["sí" if x.en_calentamiento else "" for x in traza.dias],
        }
    )
    st.dataframe(dias, hide_index=True, height=300)
    if p.modo_demanda == "esperada":
        st.caption(
            "Modo **demanda esperada**: los clientes del día salen de los litros del mes, "
            "el calendario (estacionalidad y fin de semana) y la cadena de arriba; no hay "
            "sorteo diario (la columna 'Número aleatorio' no se usa). Las llegadas dentro "
            "del día siguen siendo Poisson."
        )
    else:
        st.caption(
            "Modo **Monte Carlo**: cada día se sortea un factor relativo de DEM-07 "
            "(0,78 · 0,89 · 1,00 · 1,11 · 1,22) que multiplica los clientes del día."
        )

    st.divider()
    st.plotly_chart(
        graficos.grafico_perfil_horario(traza, p.dias_medidos), key="g_perfil"
    )
    st.plotly_chart(graficos.grafico_demanda_diaria(traza), key="g_dia_a_dia")


def pestania_demanda(p: ParametrosSimulacion) -> None:
    if p.estacion_real:
        pestania_demanda_real(p)
        return
    traza = st.session_state.traza

    st.subheader("La demanda se sortea con el método Monte Carlo")
    st.markdown(DESCRIPCION_MONTECARLO)

    st.markdown("##### Pasos 1 a 3: de las frecuencias observadas a los intervalos")
    d = p.demanda
    tabla = pd.DataFrame(
        {
            "Autos por día": d.valores,
            "Días observados": d.frecuencias,
            "Probabilidad": [f"{x:.2f}" for x in d.probabilidades],
            "Probabilidad acumulada": [f"{x:.2f}" for x in d.acumuladas],
            "Intervalo de números aleatorios": [
                d.intervalo_texto(i) for i in range(len(d.valores))
            ],
        }
    )
    st.dataframe(tabla, hide_index=True)
    st.caption(
        f"Total: {d.total_observaciones} días observados · demanda media "
        f"{d.media:.0f} autos/día · consumo esperado {p.litros_por_dia:,.0f} L/día."
    )

    st.markdown("##### Pasos 4 y 5: el sorteo de cada día simulado")
    dias = pd.DataFrame(
        {
            "Día": [x.dia for x in traza.dias],
            "Número aleatorio": [x.numero_texto for x in traza.dias],
            "Autos sorteados": [x.autos_sorteados for x in traza.dias],
            "Autos que llegaron": [x.autos_llegados for x in traza.dias],
            "Atendidos": [x.atendidos for x in traza.dias],
            "Perdidos por cola": [x.perdidos_cola for x in traza.dias],
            "Perdidos sin nafta": [x.perdidos_sin_combustible for x in traza.dias],
            "Litros vendidos": [round(x.litros_vendidos) for x in traza.dias],
            "Quiebre": ["sí" if x.hubo_quiebre else "" for x in traza.dias],
            "Calentamiento": ["sí" if x.en_calentamiento else "" for x in traza.dias],
        }
    )
    st.dataframe(dias, hide_index=True, height=320)
    st.caption(
        "Los autos sorteados y los que llegaron no coinciden exactamente porque el sorteo "
        "fija la media del día y las llegadas siguen un proceso de Poisson alrededor de ella."
    )

    st.divider()
    c1, c2 = st.columns(2)
    c1.plotly_chart(graficos.grafico_distribucion_demanda(p.demanda, traza), key="g_distrib")
    c2.plotly_chart(
        graficos.grafico_perfil_horario(traza, p.dias_medidos), key="g_perfil"
    )
    st.plotly_chart(graficos.grafico_demanda_diaria(traza), key="g_dia_a_dia")


# =============================================================================
# Pestaña: inventario
# =============================================================================
def pestania_inventario_real(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> None:
    """Los 4 tanques (uno por producto líquido), su política (s, Q) y el barrido por producto."""
    traza = st.session_state.traza
    base = buscar(st.session_state.resultados, "Base")

    st.subheader("Inventario: un tanque por producto líquido")
    plazo = p.inventario[0].plazo_entrega
    st.caption(
        f"Cada producto tiene su tanque, su política (s, Q) y su propio camión: un pedido "
        f"lleva un solo producto (INV-08, etapa 1). El camión tarda entre "
        f"{plazo.minimo:.0f} y {plazo.maximo:.0f} horas (más probable {plazo.moda:.0f} h, "
        f"INV-01). El GNC no tiene tanque: se mide en m³ y no aparece acá."
    )

    fila = st.columns(4)
    for columna, metrica in zip(
        fila,
        (
            INDICADORES_INVENTARIO[0],   # nivel de servicio
            INDICADORES_INVENTARIO[1],   # días con quiebre
            INDICADORES_INVENTARIO[5],   # nivel promedio (suma de los 4 tanques)
            INDICADORES_INVENTARIO[6],   # pedidos por día
        ),
    ):
        tarjeta(columna, metrica, base)

    nombres = {pr.id: pr.nombre for pr in p.productos}
    litros_dia = promedio_por_producto(base.replicas, "litros_vendidos_por_producto")
    quiebres = promedio_por_producto(base.replicas, "dias_quiebre_por_producto")
    filas = []
    for inv in p.inventario:
        consumo_dia = litros_dia[inv.producto]
        consumo_en_plazo = consumo_dia / 24.0 * inv.plazo_entrega.media
        filas.append(
            {
                "Tanque": nombres[inv.producto],
                "Capacidad": f"{inv.capacidad:,.0f} L",
                "Nivel inicial": f"{inv.nivel_inicial:,.0f} L",
                "Punto de pedido (s)": f"{inv.punto_pedido:,.0f} L",
                "Cantidad (Q)": f"{inv.cantidad_pedido:,.0f} L",
                "Venta diaria": f"{consumo_dia:,.0f} L",
                "s cubre": f"{inv.punto_pedido / consumo_dia:.1f} días" if consumo_dia else "—",
                "Vendido durante el plazo": f"{consumo_en_plazo:,.0f} L",
                "Días con quiebre": f"{quiebres[inv.producto]:.1f} %",
            }
        )
        if inv.punto_pedido < consumo_en_plazo:
            st.warning(
                f"{nombres[inv.producto]}: el punto de pedido ({inv.punto_pedido:,.0f} L) "
                f"es menor que lo que se vende mientras viaja el camión "
                f"({consumo_en_plazo:,.0f} L): el quiebre de ese tanque es probable.",
                icon="⚠️",
            )
    st.dataframe(pd.DataFrame(filas), hide_index=True)

    st.plotly_chart(graficos.grafico_tanques_real(traza, p), key="g_tanques_real")
    st.caption(
        "Un diente de sierra por tanque: baja mientras se vende y sube de golpe cuando "
        "descarga el camión. La línea naranja es el punto de pedido s; donde la curva toca "
        "el cero, ese producto dejó de venderse aunque los otros sigan."
    )

    st.divider()
    st.subheader("¿Cuál es la mejor política de reposición de cada tanque?")
    st.markdown(
        "Se prueban 13 combinaciones de **punto de pedido (s)** y **cantidad a pedir (Q)** "
        "—medidas en días de consumo de cada producto— y se elige, **tanque por tanque**, la "
        "de menor costo mensual:\n\n"
        "**costo = flete de los pedidos + almacenamiento + venta perdida por falta de stock**\n\n"
        "Como cada camión es independiente y cada producto tiene su propio stream de plazos, "
        "las 4 curvas se miden en las mismas corridas. La política cargada es el primer punto "
        "de la grilla, así que la mejor nunca es peor que ella."
    )
    c1, c2 = st.columns([1, 2])
    replicas_barrido = c1.slider("Réplicas por política", 1, 4, 2, 1, key="rep_barrido_real")
    puntos = len(grilla_politicas_real(p))
    c2.caption(
        f"Se van a probar **{puntos} políticas** × {replicas_barrido} réplicas de {p.dias} días. "
        f"Tarda aproximadamente {puntos * replicas_barrido * 1.1:.0f} segundos."
    )
    if st.button("🔎 Buscar la mejor política de cada tanque", type="primary"):
        with st.spinner("Probando políticas de reposición…"):
            barrido = barrer_politicas_real_cacheado(
                p, replicas_barrido, st.session_state.semilla_usada
            )
            st.session_state.costos_real = analizar_politicas_real(barrido, eco, p)
        st.rerun()

    costos = st.session_state.get("costos_real")
    if not costos:
        st.info("Todavía no se corrió el barrido.", icon="ℹ️")
        return

    ahorros = ahorro_por_producto(costos)
    ahorro_total = sum(ahorros.values())
    st.metric(
        "Ahorro mensual de reponer mejor (los 4 tanques)",
        f"{pesos(ahorro_total)} /mes",
        help="Costo de la política cargada − costo de la mejor de cada tanque, con los "
             "márgenes y el flete de ECO-* (placeholders heredados).",
        border=True,
    )
    resumen = []
    mejores = {}
    for producto, lista in costos.items():
        actual, mejor = lista[0], min(lista, key=lambda c: c.costo_total)
        mejores[producto] = mejor
        resumen.append(
            {
                "Tanque": nombres[producto],
                "Política cargada": f"s = {actual.punto_pedido:,.0f} · Q = {actual.cantidad_pedido:,.0f}",
                "Quiebre": f"{actual.porcentaje_dias_quiebre:.1f} %",
                "Costo actual": pesos(actual.costo_total),
                "Mejor política": f"s = {mejor.punto_pedido:,.0f} · Q = {mejor.cantidad_pedido:,.0f}",
                "Quiebre con la mejor": f"{mejor.porcentaje_dias_quiebre:.1f} %",
                "Costo con la mejor": pesos(mejor.costo_total),
                "Ahorro": pesos(ahorros[producto]),
            }
        )
    st.dataframe(pd.DataFrame(resumen), hide_index=True)
    if ahorro_total > 0 and st.button(
        "✅ Usar las mejores políticas",
        help="Las carga en la barra lateral. Después hay que apretar Correr simulación.",
    ):
        st.session_state.politica_sugerida_real = {
            producto: (m.punto_pedido, m.cantidad_pedido) for producto, m in mejores.items()
        }
        st.rerun()

    elegido = st.selectbox(
        "Ver el detalle de", list(costos), format_func=lambda x: nombres[x], key="detalle_pol_real"
    )
    lista = costos[elegido]
    filas = []
    for c in sorted(lista, key=lambda c: c.costo_total):
        filas.append(
            {
                "Punto de pedido (s)": f"{c.punto_pedido:,.0f} L",
                "Cantidad (Q)": f"{c.cantidad_pedido:,.0f} L",
                "Cobertura": f"{c.cobertura_dias:.1f} días",
                "Pedidos/mes": round(c.pedidos_mes, 1),
                "Costo de pedido": pesos(c.costo_pedidos),
                "Almacenamiento": pesos(c.costo_almacenamiento),
                "Faltante": pesos(c.costo_faltante),
                "COSTO TOTAL": pesos(c.costo_total),
                "Nivel de servicio": f"{c.nivel_servicio * 100:.1f} %",
                "Días con quiebre": f"{c.porcentaje_dias_quiebre:.1f} %",
            }
        )
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    g1, g2 = st.columns(2)
    g1.plotly_chart(graficos.grafico_costos_politicas(lista), key="g_costos_pol_real")
    g2.plotly_chart(graficos.grafico_frontera_politicas(lista), key="g_frontera_real")


def pestania_inventario(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> None:
    if p.estacion_real:
        pestania_inventario_real(p, eco)
        return
    traza = st.session_state.traza
    base = buscar(st.session_state.resultados, "Base")

    st.subheader("Inventario de combustible")
    st.caption(
        f"Política actual: punto de pedido **{p.tanque.punto_pedido:,.0f} L** "
        f"(cubre {p.cobertura_punto_pedido:.1f} horas de venta) y pedidos de "
        f"**{p.tanque.cantidad_pedido:,.0f} L**. El camión tarda entre "
        f"{p.tanque.plazo_entrega.minimo:.0f} y {p.tanque.plazo_entrega.maximo:.0f} horas "
        f"(más probable {p.tanque.plazo_entrega.moda:.0f} h)."
    )

    fila = st.columns(4)
    for columna, metrica in zip(
        fila,
        (
            INDICADORES_INVENTARIO[0],   # nivel de servicio
            INDICADORES_INVENTARIO[1],   # días con quiebre
            INDICADORES_INVENTARIO[5],   # nivel promedio del tanque
            INDICADORES_INVENTARIO[6],   # pedidos por día
        ),
    ):
        tarjeta(columna, metrica, base)

    consumo_en_plazo = p.litros_por_dia / 24 * p.tanque.plazo_entrega.media
    if p.tanque.punto_pedido < consumo_en_plazo:
        st.error(
            f"El punto de pedido ({p.tanque.punto_pedido:,.0f} L) es menor que lo que se "
            f"vende mientras viaja el camión ({consumo_en_plazo:,.0f} L en promedio). "
            f"Con esta política el quiebre de stock es prácticamente seguro.",
            icon="⚠️",
        )

    st.plotly_chart(graficos.grafico_tanque(traza, p), key="g_tanque")
    st.caption(
        "Los dientes de sierra son el ciclo de inventario: baja mientras se vende y sube "
        "de golpe cuando descarga el camión. Donde la curva toca el cero, la estación "
        "estuvo sin poder vender."
    )

    st.divider()
    st.subheader("¿Cuál es la mejor política de reposición?")
    st.markdown(
        "Se prueban varias combinaciones de **punto de pedido (s)** y **cantidad a pedir "
        "(Q)**, y se elige la de menor costo total mensual:\n\n"
        "**costo total = flete de los pedidos + almacenamiento + venta perdida por faltante**\n\n"
        "Pedir seguido y poco baja el almacenamiento pero dispara el flete; pedir tarde "
        "ahorra en los dos pero se paga con quiebres de stock."
    )

    puntos, cantidades = grilla_sugerida(p)
    combinaciones = sum(
        1 for s in puntos for q in cantidades if s + q <= p.tanque.capacidad
    )
    c1, c2 = st.columns([1, 2])
    replicas_barrido = c1.slider("Réplicas por política", 1, 5, 2, 1, key="rep_barrido")
    c2.caption(
        f"Se van a probar **{combinaciones} políticas** × {replicas_barrido} réplicas de "
        f"{p.dias} días. Tarda aproximadamente "
        f"{combinaciones * replicas_barrido * 0.6:.0f} segundos."
    )

    if st.button("🔎 Buscar la mejor política", type="primary"):
        with st.spinner("Probando políticas de reposición…"):
            politicas = barrer_politicas_cacheado(
                p, tuple(puntos), tuple(cantidades), replicas_barrido,
                st.session_state.semilla_usada,
            )
            st.session_state.costos_politicas = analizar_politicas(politicas, eco, p)
        # Se vuelve a ejecutar la app para que la conclusión incorpore esta segunda
        # decisión: se arma antes que las pestañas, así que si no, quedaría desactualizada.
        st.rerun()

    costos = st.session_state.get("costos_politicas")
    if not costos:
        st.info("Todavía no se corrió el barrido.", icon="ℹ️")
        return

    mejor = mejor_politica(costos)
    actual = st.session_state.get("politica_actual")

    if mejor is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("Mejor punto de pedido (s)", f"{mejor.punto_pedido:,.0f} L", border=True)
        c2.metric("Mejor cantidad a pedir (Q)", f"{mejor.cantidad_pedido:,.0f} L", border=True)
        c3.metric(
            "Costo total",
            f"${mejor.costo_total:,.0f} /mes",
            delta=(
                f"{pesos(mejor.costo_total - actual.costo_total)} vs la actual"
                if actual
                else None
            ),
            delta_color="inverse",
            border=True,
        )
        if actual is not None and mejor.costo_total < actual.costo_total:
            if st.button(
                "✅ Usar esta política",
                help="Carga esta política en la barra lateral. Después hay que apretar "
                     "Correr simulación para ver el efecto sobre todo lo demás.",
            ):
                st.session_state.politica_sugerida = (
                    mejor.punto_pedido,
                    mejor.cantidad_pedido,
                )
                st.rerun()

    filas = []
    for c in sorted(costos, key=lambda c: c.costo_total):
        filas.append(
            {
                "Punto de pedido (s)": f"{c.punto_pedido:,.0f} L",
                "Cantidad (Q)": f"{c.cantidad_pedido:,.0f} L",
                "Cobertura": f"{c.cobertura_dias:.1f} días",
                "Pedidos/mes": round(c.pedidos_mes, 1),
                "Costo de pedido": pesos(c.costo_pedidos),
                "Almacenamiento": pesos(c.costo_almacenamiento),
                "Faltante": pesos(c.costo_faltante),
                "COSTO TOTAL": pesos(c.costo_total),
                "Nivel de servicio": f"{c.nivel_servicio * 100:.1f} %",
                "Días con quiebre": f"{c.porcentaje_dias_quiebre:.1f} %",
            }
        )
    st.dataframe(pd.DataFrame(filas), hide_index=True)

    c1, c2 = st.columns(2)
    c1.plotly_chart(graficos.grafico_costos_politicas(costos), key="g_costos_pol")
    c2.plotly_chart(graficos.grafico_frontera_politicas(costos), key="g_frontera")


# =============================================================================
# Pestaña: escenarios
# =============================================================================
def tabla_escenarios(resultados: list[ResultadoEscenario]) -> pd.DataFrame:
    filas = []
    for r in resultados:
        fila = {
            "Escenario": r.escenario.nombre,
            "Descripción": r.escenario.descripcion,
            "Surt.": r.escenario.surtidores,
            "Cajas": r.escenario.cajas,
        }
        for metrica in COMPARACION:
            resumen = r.resumen[metrica.clave]
            fila[metrica.etiqueta] = (
                f"{metrica.valor_mostrado(resumen.promedio):,.{metrica.decimales}f} "
                f"± {metrica.valor_mostrado(resumen.semiamplitud):,.{metrica.decimales}f}"
            )
        filas.append(fila)
    return pd.DataFrame(filas)


def pestania_escenarios() -> None:
    resultados = st.session_state.resultados
    p = st.session_state.parametros

    if p.estacion_real:
        st.subheader("Escenario Base de la estación real")
        st.info(
            "Por ahora hay un único escenario: la estación **como está** (12 caras, "
            "playeros 1 · 2 · 2, una caja). El catálogo de escenarios del caso real "
            "(playeros en el pico, corte de GNC, corte de ruta, autoservicio, etc.) llega "
            "en la Fase 7. Para ver la comparación de capacidad del proyecto original "
            "(+1 surtidor, +1 cajero), elegí el **caso clásico** en la barra lateral.",
            icon="⚖️",
        )
        st.dataframe(tabla_escenarios(resultados), hide_index=True)
        st.caption(
            "Cada celda es el promedio de las réplicas ± la semiamplitud del intervalo de "
            "confianza del 95 %."
        )
        opciones = {m.etiqueta: m for m in COMPARACION}
        elegida = st.selectbox("Indicador a mirar", list(opciones), index=0)
        metrica = opciones[elegida]
        st.plotly_chart(
            graficos.grafico_dispersion_replicas(resultados, metrica), key="g_caja"
        )
        st.plotly_chart(graficos.grafico_atendidos_vs_perdidos(resultados), key="g_atend")
        return

    st.subheader("Comparación de escenarios de capacidad")
    st.caption(
        "Cada celda es el promedio de las réplicas ± la semiamplitud del intervalo de "
        "confianza del 95 %. Los cuatro escenarios se corrieron con números aleatorios "
        "comunes: llegan los mismos autos, cargan los mismos litros y el camión tarda lo "
        "mismo, así que la diferencia es la capacidad."
    )
    st.dataframe(tabla_escenarios(resultados), hide_index=True)

    st.divider()
    opciones = {m.etiqueta: m for m in COMPARACION}
    elegida = st.selectbox("Indicador a comparar", list(opciones), index=0)
    metrica = opciones[elegida]

    c1, c2 = st.columns(2)
    c1.plotly_chart(graficos.grafico_comparativo(resultados, metrica), key="g_comp")
    c2.plotly_chart(graficos.grafico_dispersion_replicas(resultados, metrica), key="g_caja")
    st.caption(
        "El gráfico de la derecha muestra cada réplica por separado: si las cajas de dos "
        "escenarios se solapan mucho, la diferencia entre ellos puede ser sólo azar."
    )

    st.plotly_chart(graficos.grafico_atendidos_vs_perdidos(resultados), key="g_atend")


# =============================================================================
# Pestaña: economía
# =============================================================================
def pestania_economia(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> None:
    economia = st.session_state.economia

    st.subheader("Análisis económico")
    st.caption(
        f"La corrida simula {p.dias} días de operación real, así que los importes "
        f"mensuales salen directo, sin extrapolar. Los costos de inventario (flete y "
        f"almacenamiento) también cambian entre escenarios: vender más obliga a pedir más."
    )

    filas = []
    for e in economia:
        filas.append(
            {
                "Escenario": e.nombre,
                "Descripción": e.descripcion,
                "Litros/día": f"{e.litros_dia:,.0f}",
                "Ingreso combustible": pesos(e.ingreso_combustible),
                "Ingreso minimarket": pesos(e.ingreso_minimarket),
                "Costo de inventario": pesos(e.costo_inventario),
                "Costo de capacidad": pesos(e.costo_capacidad),
                "Margen operativo": pesos(e.margen_operativo),
                "Beneficio vs Base": pesos(e.beneficio_neto),
                "Venta perdida": pesos(e.venta_perdida),
                "Inversión": pesos(e.inversion_inicial),
                "Repago": e.payback_texto,
            }
        )
    st.dataframe(pd.DataFrame(filas), hide_index=True)

    if p.estacion_real:
        st.warning(
            "Los márgenes por litro, por compra y el flete son **placeholders heredados** "
            "del proyecto hipotético (ECO-01/02/06, sin fuente): estos pesos muestran cómo "
            "se calcula, no son todavía una conclusión económica del caso. El GNC (m³) no "
            "entra al ingreso hasta la Fase 8.",
            icon="💰",
        )
        c1, c2 = st.columns(2)
        c1.plotly_chart(graficos.grafico_ingresos_costos(economia), key="g_ing_costos")
        c2.plotly_chart(graficos.grafico_venta_perdida(economia), key="g_perdida")
    else:
        c1, c2 = st.columns(2)
        c1.plotly_chart(graficos.grafico_beneficio(economia), key="g_benef")
        c2.plotly_chart(graficos.grafico_ingresos_costos(economia), key="g_ing_costos")
        st.plotly_chart(graficos.grafico_venta_perdida(economia), key="g_perdida")

    with st.expander("Cómo se calcula"):
        st.markdown(
            f"""
| Concepto | Fórmula |
|---|---|
| Ingreso por combustible | litros vendidos × \\${eco.margen_por_litro:,.0f} por litro |
| Ingreso por minimarket | compras × \\${eco.margen_compra:,.0f} |
| Costo de pedido | pedidos del mes × \\${eco.costo_pedido:,.0f} de flete |
| Costo de almacenamiento | nivel promedio del tanque × \\${eco.costo_almacenamiento_litro_mes:,.0f} por litro y por mes |
| Costo de capacidad | surtidores extra × \\${eco.operativo_surtidor_mensual:,.0f} + cajeros extra × \\${eco.sueldo_cajero_mensual:,.0f} |
| **Margen operativo** | **ingresos − costo de inventario − costo de capacidad** |
| **Beneficio neto** | **margen operativo del escenario − margen operativo del Base** |
| Venta perdida | litros no vendidos × margen + clientes perdidos × probabilidad de compra × margen de minimarket |
| Inversión inicial | surtidores extra × \\${eco.inversion_surtidor:,.0f} |
| **Repago** | **inversión ÷ beneficio neto mensual** |

La venta perdida es un **costo de oportunidad**: no sale del bolsillo, pero es plata que
la estación deja sobre la mesa. Por eso no se resta del margen (sería contarla dos veces)
y se informa aparte.
"""
        )


# =============================================================================
# Pestaña: conclusión
# =============================================================================
def escapar_pesos(texto: str) -> str:
    """Escapa el signo $ para que Streamlit no lo interprete como fórmula LaTeX."""
    return texto.replace("$", r"\$")


def pestania_conclusion_real(p: ParametrosSimulacion) -> None:
    """Diagnóstico de la estación real, sin el veredicto de capacidad (llega en la Fase 7)."""
    base = buscar(st.session_state.resultados, "Base")
    economia = st.session_state.economia[0]

    st.subheader("Diagnóstico de la estación real")
    st.info(
        "Todavía no hay veredicto de inversión: los escenarios del caso real (S0–S12) y la "
        "economía con datos propios llegan en las fases 7 y 8. Esto es el diagnóstico de "
        "la situación actual, con los datos y supuestos del Registro.",
        icon="🧭",
    )
    perdidos_espera = base.prom("perdidos_cola_dia")
    perdidos_cola_llena = base.prom("perdidos_cola_llena_dia")
    perdidos_nafta = base.prom("perdidos_sin_combustible_dia")
    perdidos_total = perdidos_espera + perdidos_cola_llena + perdidos_nafta
    lineas = [
        f"La estación recibe **{base.prom('llegadas_dia'):,.0f} clientes por día** "
        f"({base.prom('litros_vendidos_dia'):,.0f} L de combustible líquido vendidos por día) "
        f"con 12 caras y playeros {p.playeros_por_turno[0]} · {p.playeros_por_turno[1]} · "
        f"{p.playeros_por_turno[2]} (noche · mañana · tarde).",
        f"La espera promedio es de {base.prom('espera_surtidor'):.1f} min, pero en la hora "
        f"pico trepa a {base.prom('espera_pico'):.1f} min "
        f"(± {base.resumen['espera_pico'].semiamplitud:.1f}, IC 95 %). Las caras están "
        f"ocupadas el {base.prom('util_surtidores') * 100:.0f} % del tiempo y los playeros "
        f"el {base.prom('util_playeros') * 100:.0f} %.",
        f"ρ analítico en la hora pico: **{p.rho_pico:.2f}** con "
        f"{max(p.playeros_por_turno)} playeros. Con ρ cerca de 1 la dotación está al límite: "
        f"depende de C5 (dotación), C11 (tiempo de servicio) y C12 (litros por carga).",
        f"Se pierden {perdidos_total:.1f} clientes por día: {perdidos_espera:.1f} por "
        f"esperar demasiado, {perdidos_cola_llena:.1f} por cola llena y "
        f"{perdidos_nafta:.1f} por falta de combustible. Son "
        f"{pesos(economia.venta_perdida)} por mes de venta no realizada (con márgenes "
        f"placeholder).",
        f"Nivel de servicio de combustible: {base.prom('nivel_servicio') * 100:.1f} %.",
    ]
    if p.gnc is not None and base.prom("gnc_afectados_dia") > 0:
        lineas.append(
            f"GNC: el corte de invierno afecta a {base.prom('gnc_afectados_dia'):.1f} clientes "
            f"por día (promedio del período): {base.prom('migrados_gnc_dia'):.1f} pasan a Súper "
            f"y {base.prom('perdidos_corte_gnc_dia'):.1f} se pierden "
            f"({base.prom('m3_gnc_perdidos_dia'):.0f} m³ por día sin vender)."
        )
    if p.gnc is not None:
        caras_gnc = sum(gr.caras for gr in p.grupos if "gnc" in gr.productos)
        lineas.append(
            f"Alerta de coherencia (C8): {caras_gnc} de {sum(gr.caras for gr in p.grupos)} caras "
            f"son de GNC para ≈ {p.pct_gnc:.0%} de los clientes."
        )
    for linea in lineas:
        st.markdown(f"- {escapar_pesos(linea)}")

    costos_real = st.session_state.get("costos_real")
    if costos_real:
        ahorros = ahorro_por_producto(costos_real)
        nombres = {pr.id: pr.nombre for pr in p.productos}
        st.markdown("#### Reposición")
        st.markdown(
            escapar_pesos(
                f"- Con la mejor política de cada tanque se ahorran **{pesos(sum(ahorros.values()))} "
                f"por mes** (márgenes y flete placeholder). Por producto: "
                + " · ".join(f"{nombres[k]} {pesos(v)}" for k, v in ahorros.items())
                + "."
            )
        )
    else:
        st.info(
            "Todavía no se buscó la mejor política de reposición de cada tanque: "
            "andá a **Inventario** y apretá *Buscar la mejor política*.",
            icon="🛢️",
        )

    if perdidos_nafta > (perdidos_espera + perdidos_cola_llena) * 1.5:
        st.error(
            "Se pierden más clientes por falta de combustible que por espera: el cuello "
            "de botella es el abastecimiento, no la dotación.",
            icon="🛢️",
        )
    elif (perdidos_espera + perdidos_cola_llena) > perdidos_nafta * 1.5:
        st.warning(
            "Se pierden más clientes por espera que por falta de combustible: el cuello "
            "de botella es la capacidad de atención (playeros en el pico).",
            icon="🚗",
        )

    st.divider()
    st.markdown("**Supuestos del modelo** (lo que hay que aclarar al presentarlo)")
    for supuesto in SUPUESTOS_REAL:
        st.markdown(f"- {escapar_pesos(supuesto)}")


def pestania_conclusion() -> None:
    p = st.session_state.parametros
    if p.estacion_real:
        pestania_conclusion_real(p)
        return
    recom = st.session_state.recomendacion

    st.subheader("Conclusión y recomendación")
    if recom["conviene_invertir"] or recom["ahorro_inventario"] > 0:
        st.success(f"### {escapar_pesos(str(recom['veredicto']))}")
    else:
        st.warning(f"### {escapar_pesos(str(recom['veredicto']))}")

    st.markdown("#### Diagnóstico")
    for linea in recom["diagnostico"]:
        st.markdown(f"- {escapar_pesos(linea)}")

    st.markdown("#### Qué hacer")
    for linea in recom["acciones"]:
        st.markdown(f"- {escapar_pesos(linea)}")

    if st.session_state.get("costos_politicas") is None:
        st.info(
            "Todavía no se buscó la mejor política de reposición. Andá a la pestaña "
            "**Inventario** y apretá *Buscar la mejor política* para completar la "
            "conclusión con la segunda decisión.",
            icon="🛢️",
        )

    c1, c2 = st.columns(2)
    c1.metric(
        "Beneficio de la mejor inversión en capacidad",
        f"{pesos(float(recom['beneficio_capacidad']))} /mes",
        border=True,
    )
    c2.metric(
        "Ahorro por mejorar la reposición",
        f"{pesos(float(recom['ahorro_inventario']))} /mes",
        help="Requiere inversión cero: es sólo cambiar cuándo y cuánto se pide.",
        border=True,
    )

    if recom["descartados"]:
        with st.expander("Escenarios de capacidad descartados"):
            for d in recom["descartados"]:
                st.markdown(f"- {escapar_pesos(d)}")

    st.divider()
    st.markdown("**Supuestos del modelo** (lo que hay que aclarar al presentarlo)")
    for supuesto in SUPUESTOS:
        st.markdown(f"- {supuesto}")


# =============================================================================
# Pestaña: modelo y método
# =============================================================================
def pestania_modelo_real(p: ParametrosSimulacion) -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("El modelo")
        st.markdown(DESCRIPCION_MODELO_REAL)
    with c2:
        st.subheader("El método")
        st.markdown(DESCRIPCION_METODO)

        st.markdown("**Intensidad de tráfico teórica (ρ) en la hora pico**")
        st.caption(
            "ρ = λ_pico · E[servicio] ÷ playeros, sólo con los clientes de nafta y diésel "
            "(el GNC no usa playero). Si ρ ≥ 1 la cola crece sin límite mientras dure el pico."
        )
        columnas = st.columns(3)
        for columna, n in zip(columnas, (1, 2, 3)):
            rho = p.rho_pico * max(p.playeros_por_turno) / n
            columna.metric(
                f"{n} playero{'s' if n > 1 else ''}", f"{rho:.2f}", border=True,
                help="Misma demanda y mismo servicio; sólo cambia la dotación del pico.",
            )
        if p.rho_pico >= 1:
            st.warning(
                "Con la dotación actual ρ supera 1 en la hora pico: la zona se satura y "
                "sólo la frena el abandono de clientes.",
                icon="⚠️",
            )

    st.divider()
    st.subheader("Configuración de esta corrida")
    if p.modo_demanda == "esperada":
        demanda_txt = (
            f"esperada: {p.litros_mes:,.0f} L/mes ⇒ {p.autos_por_dia:.0f} clientes/día"
        )
    else:
        demanda_txt = (
            f"Monte Carlo (factor relativo DEM-07) sobre {p.litros_mes:,.0f} L/mes ⇒ "
            f"{p.autos_por_dia:.0f} clientes/día en promedio"
        )
    caras_txt = " · ".join(str(g.caras) for g in p.grupos)
    playeros_txt = " · ".join(str(x) for x in p.playeros_por_turno)
    disciplina_txt = p.disciplina_cola.replace("_", " ")
    caja_txt = "Exponencial" if p.caja_exponencial else "Triangular"
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
| Parámetro | Valor |
|---|---|
| Caras (A · B · C) | {caras_txt} |
| Playeros (noche · mañana · tarde) | {playeros_txt} |
| Cajas | {p.cajas} |
| Cola por zona | {p.capacidad_cola} autos ({disciplina_txt}) |
| Demanda | {demanda_txt} |
| Clientes GNC | {p.pct_gnc:.0%} de las llegadas |
| Inicio (mes, día) | {p.fecha_inicio} |
| Perfil horario | pico a las {p.perfil.hora_pico()}:00 |
| Carga nafta/diésel | Triangular({p.carga.minimo:g}, {p.carga.moda:g}, {p.carga.maximo:g}) min |
| Carga GNC | Triangular({p.carga_gnc.minimo:g}, {p.carga_gnc.moda:g}, {p.carga_gnc.maximo:g}) min |
| Compra | {caja_txt} — media {p.media_caja:.2f} min |
| Probabilidad de compra | {p.prob_compra:.0%} (Bernoulli) |
| Paciencia surtidor / caja | {p.paciencia_surtidor:.0f} / {p.paciencia_caja:.0f} min |
"""
        )
    with c2:
        plazo = p.inventario[0].plazo_entrega
        st.markdown(
            f"""
| Parámetro | Valor |
|---|---|
| Tanques | {len(p.inventario)} × {p.inventario[0].capacidad:,.0f} L |
| Política (s, Q) por producto | INV-07 (ver pestaña Inventario) |
| Plazo de entrega | Triangular({plazo.minimo:g}, {plazo.moda:g}, {plazo.maximo:g}) h |
| Consumo esperado (líquidos) | {p.litros_por_dia:,.0f} L/día |
| Días simulados | {p.dias} ({p.dias_calentamiento} de calentamiento) |
| Réplicas | {st.session_state.replicas} |
| Semilla | {st.session_state.semilla_usada} |
"""
        )


def pestania_modelo(p: ParametrosSimulacion) -> None:
    if p.estacion_real:
        pestania_modelo_real(p)
        return
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("El modelo")
        st.markdown(DESCRIPCION_MODELO)
    with c2:
        st.subheader("El método")
        st.markdown(DESCRIPCION_METODO)

        st.markdown("**Intensidad de tráfico teórica (ρ)**")
        st.caption(
            "ρ = λ · E[servicio] / cantidad de servidores. Es el cálculo analítico previo: "
            "si ρ ≥ 1 la cola crece sin límite mientras dure esa condición."
        )
        m1, m2 = st.columns(2)
        m1.metric("ρ en la hora pico de un día medio", f"{p.rho_pico:.3f}", border=True)
        m2.metric(
            "ρ en la hora pico del día más cargado", f"{p.rho_pico_dia_malo:.3f}", border=True
        )
        if p.rho_pico_dia_malo >= 1:
            st.warning(
                "En los días de mayor demanda ρ supera 1 durante la hora pico: ahí el "
                "sistema se satura y la cola sólo la frena el abandono de clientes.",
                icon="⚠️",
            )

    st.divider()
    st.subheader("Configuración de esta corrida")
    if p.modo_demanda == "esperada":
        demanda_txt = (
            f"esperada desde {p.litros_mes:,.0f} L/mes ⇒ {p.autos_por_dia:.0f} clientes/día"
        )
    else:
        demanda_txt = f"tabla empírica, media {p.autos_por_dia:.0f} autos/día"
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
| Parámetro | Valor |
|---|---|
| Surtidores / cajas | {p.surtidores} / {p.cajas} |
| Demanda diaria | {demanda_txt} |
| Modo de demanda | {p.modo_demanda} |
| Inicio (mes, día) | {p.fecha_inicio} |
| Perfil horario | pico a las {p.perfil.hora_pico()}:00 |
| Carga | Triangular({p.carga.minimo:g}, {p.carga.moda:g}, {p.carga.maximo:g}) min — media {p.carga.media:.2f} |
| Litros por carga | Triangular({p.litros.minimo:g}, {p.litros.moda:g}, {p.litros.maximo:g}) L — media {p.litros.media:.1f} |
| Compra | {"Exponencial" if p.caja_exponencial else "Triangular"} — media {p.media_caja:.2f} min |
| Probabilidad de compra | {p.prob_compra:.0%} (Bernoulli) |
| Paciencia surtidor / caja | {p.paciencia_surtidor:.0f} / {p.paciencia_caja:.0f} min |
"""
        )
    with c2:
        st.markdown(
            f"""
| Parámetro | Valor |
|---|---|
| Capacidad del tanque | {p.tanque.capacidad:,.0f} L |
| Punto de pedido (s) | {p.tanque.punto_pedido:,.0f} L ({p.cobertura_punto_pedido:.1f} h de venta) |
| Cantidad a pedir (Q) | {p.tanque.cantidad_pedido:,.0f} L |
| Plazo de entrega | Triangular({p.tanque.plazo_entrega.minimo:g}, {p.tanque.plazo_entrega.moda:g}, {p.tanque.plazo_entrega.maximo:g}) h |
| Consumo esperado | {p.litros_por_dia:,.0f} L/día |
| Días simulados | {p.dias} ({p.dias_calentamiento} de calentamiento) |
| Réplicas por escenario | {st.session_state.replicas} |
| Semilla | {st.session_state.semilla_usada} |
"""
        )


# =============================================================================
# Pestaña: red y rutas (Fase 5)
# =============================================================================
def _demora_texto(red, id_origen: str, corte) -> str:
    """Qué le pasa a un camión de ese origen que sale justo cuando empieza el corte."""
    if corte.demora_fija_min > 0:
        return f"+{corte.demora_fija_min:.0f} min por viaje (franja {corte.franja[0]:.0f}–{corte.franja[1]:.0f} h)"
    r = replace(red, origen=id_origen)
    duracion_min = corte.duracion.moda * 60.0
    demora = demora_por_corte(r, corte.arcos, duracion_min)
    if demora == 0:
        return "no lo afecta (el corte no está en su ruta)"
    alternativo = camino_mas_corto(r, cerrados=corte.arcos)
    if demora < duracion_min - 1e-9:
        base = camino_mas_corto(r)
        return f"+{demora / 60:.1f} h (se desvía: +{alternativo.km - base.km:,.0f} km)"
    return f"+{demora / 60:.1f} h (espera que se reabra)"


def pestania_red(p: ParametrosSimulacion) -> None:
    if p.red is None:
        st.subheader("Red de abastecimiento")
        st.info(
            "El caso clásico no tiene red: su plazo de entrega es una sola triangular "
            "(8–36 h) sin origen ni cortes. Elegí la **estación real** en la barra lateral.",
            icon="🗺️",
        )
        return
    red = p.red
    optimo = camino_mas_corto(red)

    st.subheader("Red de abastecimiento del camión")
    st.caption(
        "El camión sale del origen por el **camino más corto** (Dijkstra sobre los km de 10 "
        "arcos, nota 06). Un corte demora el viaje sólo si el arco cerrado está en ese camino: "
        "con origen Dock Sud, el corte nevado de la RN 143 Pareditas–San Rafael no está en la "
        "ruta. La demora se suma al plazo base (INV-01)."
    )
    st.markdown(f"**Ruta óptima:** {descripcion_ruta(red).split(' · ')[0]}")
    c2, c3 = st.columns(2)
    c2.metric("Distancia", f"{optimo.km:,.1f} km".replace(",", "X").replace(".", ",").replace("X", "."), border=True)
    c3.metric(
        f"Tiempo de viaje a {red.velocidad_kmh:.0f} km/h", f"{optimo.minutos / 60:.1f} h".replace(".", ","),
        help="Es sólo el viaje: el plazo de entrega (24–48 h) incluye además el pedido, "
             "la carga y la descarga.",
        border=True,
    )

    corte_activo = next((c for c in red.cortes if c.id == red.escenario_corte), None)
    cerrados = corte_activo.arcos if corte_activo else ()
    st.plotly_chart(graficos_red.grafico_red(red, cerrados), key="g_red")
    if corte_activo is not None and corte_activo.arcos:
        demora = demora_por_corte(red, corte_activo.arcos, corte_activo.duracion.moda * 60.0)
        if demora == 0:
            st.success(
                f"El corte {corte_activo.id} **no está en la ruta** desde "
                f"{NOMBRE_NODO[red.origen]}: el viaje no se entera.",
                icon="✅",
            )
        else:
            alternativo = camino_mas_corto(red, cerrados=corte_activo.arcos)
            st.warning(
                f"El corte {corte_activo.id} está en la ruta: el camión se demora "
                f"{demora / 60:.1f} h (camino alternativo: {alternativo.km:,.1f} km, "
                f"{alternativo.minutos / 60:.1f} h de viaje).",
                icon="🚧",
            )

    st.markdown("##### Qué le hace cada corte a cada origen")
    st.caption(
        "Demora de un camión que sale justo cuando empieza el corte: mín(desvío, tiempo que "
        "falta para que se reabra). E1 y E2 son cortes documentados (jul/ago-2026); E3 y E4 "
        "son supuestos del grupo."
    )
    filas = []
    for corte in red.cortes:
        filas.append(
            {
                "Corte": f"{corte.id} · {corte.nombre}",
                "Dock Sud": _demora_texto(red, "DOCK", corte),
                "Luján de Cuyo": _demora_texto(red, "LUJAN", corte),
            }
        )
    st.dataframe(pd.DataFrame(filas), hide_index=True)

    st.markdown("##### Plazo de entrega con y sin cortes")
    if red.escenario_corte == "ninguno":
        st.info("Elegí un escenario de cortes en la barra lateral para ver el efecto.", icon="🚧")
    else:
        mes = 7
        sin_corte, con_corte = muestrear_plazos(
            p.inventario[0].plazo_entrega, red, 4000, st.session_state.semilla_usada, mes
        )
        etiqueta = (
            f"Con cortes sorteados (julio, p = {red.prob_corte_viaje:.0%})"
            if red.escenario_corte == "aleatorio"
            else f"Un viaje que encuentra el corte {red.escenario_corte}"
        )
        st.plotly_chart(
            graficos_red.grafico_plazos(sin_corte, con_corte, etiqueta), key="g_plazos_red"
        )
        media0, media1 = sum(sin_corte) / len(sin_corte), sum(con_corte) / len(con_corte)
        st.caption(
            f"Plazo medio: {media0:.1f} h sin cortes · {media1:.1f} h con cortes "
            f"(+{media1 - media0:.2f} h por viaje). 4.000 viajes con los mismos plazos base."
        )

    st.markdown("##### Efecto en el quiebre de stock")
    st.caption(
        "Corre la estación completa con y sin el escenario elegido (mismas semillas) y compara."
    )
    if red.escenario_corte == "aleatorio" and not set(red.meses_corte) & dias_de_mes_en_corrida(
        p.fecha_inicio, p.dias
    ):
        st.warning(
            "El horizonte de esta corrida no incluye jun–ago: no hay cortes sorteados y la "
            "comparación va a dar igual. Elegí 'Una estación → Invierno' en la barra lateral.",
            icon="📅",
        )
    replicas_red = st.slider("Réplicas", 1, 4, 2, 1, key="rep_red")
    if st.button("🚧 Simular el efecto de los cortes", disabled=red.escenario_corte == "ninguno"):
        with st.spinner("Simulando con y sin cortes…"):
            sin = correr_estacion_real_cacheado(
                replace(p, red=replace(red, escenario_corte="ninguno")),
                replicas_red,
                st.session_state.semilla_usada,
            )
            con = correr_estacion_real_cacheado(p, replicas_red, st.session_state.semilla_usada)
        st.session_state.efecto_cortes = (sin, con, red.escenario_corte)
    efecto = st.session_state.get("efecto_cortes")
    if efecto:
        sin, con, escenario = efecto
        filas = []
        for etiqueta_m, clave, fmt in (
            ("Plazo de entrega promedio (h)", "plazo_entrega", "{:.1f}"),
            ("Camiones que encontraron un corte (%)", "viajes_demorados_pct", "{:.1f}"),
            ("Demora por corte, promedio por viaje (h)", "demora_ruta_promedio", "{:.2f}"),
            ("Días con quiebre (%)", "porcentaje_dias_quiebre", "{:.1f}"),
            ("Nivel de servicio (%)", "nivel_servicio", None),
            ("Litros no vendidos por día", "litros_no_vendidos_dia", "{:,.0f}"),
        ):
            if fmt is None:
                v0, v1 = f"{sin.prom(clave) * 100:.1f}", f"{con.prom(clave) * 100:.1f}"
            else:
                v0, v1 = fmt.format(sin.prom(clave)), fmt.format(con.prom(clave))
            filas.append({"Indicador": etiqueta_m, "Sin cortes": v0, f"Con {escenario}": v1})
        st.dataframe(pd.DataFrame(filas), hide_index=True)
        st.caption(
            "Es el resultado de la última comparación; si cambiaste algo en la barra lateral, "
            "volvé a apretar el botón. Un camión demorado deja el tanque más tiempo sin "
            "reposición: el quiebre sube, y el óptimo de (s, Q) también cambia."
        )


# =============================================================================
# Pestaña: GNC (Fase 6)
# =============================================================================
def pestania_gnc(p: ParametrosSimulacion) -> None:
    st.subheader("GNC: cortes de invierno, compresores y migración a nafta")
    if p.gnc is None:
        st.info(
            "El caso clásico no vende GNC. Elegí la **estación real** en la barra lateral.",
            icon="🔥",
        )
        return
    g = p.gnc
    base = buscar(st.session_state.resultados, "Base")

    st.markdown(
        "El GNC no tiene tanque: sale de la red de gas y se comprime en la estación. Con "
        "**contrato interrumpible**, cuando hay una ola de frío el ENARGAS manda cortarlo "
        "para priorizar el gas de las casas (verificado para abril-2026; San Rafael lo vivió "
        "en 2022). El corte es **total** y por **episodios** de varios días. Durante el corte, "
        "las 6 caras no atienden (los que ya cargan terminan) y cada cliente GNC **pasa a "
        "Súper** con la probabilidad elegida o **se pierde**. El GNC se mide en **m³**."
    )

    caras_gnc = sum(gr.caras for gr in p.grupos if "gnc" in gr.productos)
    caras_total = sum(gr.caras for gr in p.grupos)
    st.warning(
        f"**Alerta de coherencia (C8):** {caras_gnc} de {caras_total} caras "
        f"({caras_gnc / caras_total:.0%}) son de GNC, pero los clientes GNC son ≈ "
        f"{p.pct_gnc:.0%} de las llegadas. Con {g.compresores} compresores, los compresores "
        f"están ocupados el {base.prom('util_compresores') * 100:.1f} % del tiempo: o la "
        f"estación está sobredimensionada en GNC, o la demanda GNC está subestimada. Es "
        f"lo primero que hay que relevar con el encargado (§12, prioridad 5).",
        icon="⚖️",
    )

    # Calendario de episodios de la réplica 1
    fecha0 = date(ANO_REFERENCIA, *p.fecha_inicio)
    episodios = calendario_de_episodios(g, Aleatorio(st.session_state.semilla_usada), fecha0, p.dias)
    visibles = episodios_con_fechas(episodios, fecha0, p.dias)
    st.markdown("##### Episodios de corte de esta corrida")
    if g.contrato == "firme" or g.episodios == 0:
        st.info("No hay cortes: contrato firme o 0 episodios.", icon="✅")
    elif not visibles:
        st.warning(
            "Ningún episodio cae dentro de este horizonte: los episodios se sortean entre "
            "el 1/jun y el 31/ago. Elegí **Una estación → Invierno** (o un mes de invierno) "
            "en la barra lateral, o tildá *Forzar que los episodios caigan dentro del "
            "horizonte* en GNC y cortes de invierno.",
            icon="📅",
        )
    else:
        for desde, hasta in visibles:
            st.markdown(
                f"- **{desde.strftime('%d/%m')} al {hasta.strftime('%d/%m')}** "
                f"({(hasta - desde).days + 1} días, {g.forma.replace('_', ' ')})"
            )
        st.caption(
            "Calendario de la réplica 1; cada réplica sortea el suyo (mismas fechas en todos "
            "los escenarios con la misma semilla)."
        )

    st.markdown("##### Indicadores (promedio de todos los días medidos)")
    for fila in (INDICADORES_GNC[:4], INDICADORES_GNC[4:]):
        columnas = st.columns(4)
        for columna, metrica in zip(columnas, fila):
            tarjeta(columna, metrica, base)

    perdida_mes = base.prom("m3_gnc_perdidos_dia") * 30 * float(por_id("ECO-03").valor)
    st.caption(
        escapar_pesos(
            f"Venta de GNC perdida en el período ≈ {pesos(perdida_mes)} por mes de 30 días "
            f"(margen de ${float(por_id('ECO-03').valor):,.0f}/m³: ECO-03, heredado sin fuente). "
            f"La economía completa del GNC llega en la Fase 8."
        )
    )

    st.plotly_chart(
        graficos_gnc.grafico_gnc_dias(st.session_state.traza, p), key="g_gnc_dias"
    )

    st.markdown("##### Efecto del corte en la estación")
    st.caption("Corre la estación con y sin cortes (contrato firme), con las mismas semillas.")
    replicas_gnc = st.slider("Réplicas", 1, 4, 2, 1, key="rep_gnc")
    deshabilitado = g.contrato == "firme" or g.episodios == 0
    if st.button("🔥 Simular el efecto del corte de GNC", disabled=deshabilitado):
        with st.spinner("Simulando con y sin cortes…"):
            sin = correr_estacion_real_cacheado(
                replace(p, gnc=replace(g, contrato="firme")), replicas_gnc,
                st.session_state.semilla_usada,
            )
            con = correr_estacion_real_cacheado(p, replicas_gnc, st.session_state.semilla_usada)
        st.session_state.efecto_gnc = (sin, con)
    efecto = st.session_state.get("efecto_gnc")
    if efecto:
        sin, con = efecto
        super_sin = promedio_por_producto(sin.replicas, "litros_vendidos_por_producto")["super"]
        super_con = promedio_por_producto(con.replicas, "litros_vendidos_por_producto")["super"]
        filas = [
            ("GNC vendido (m³/día)", f"{sin.prom('m3_gnc_vendidos_dia'):.1f}", f"{con.prom('m3_gnc_vendidos_dia'):.1f}"),
            ("Clientes perdidos por el corte (por día)", f"{sin.prom('perdidos_corte_gnc_dia'):.2f}", f"{con.prom('perdidos_corte_gnc_dia'):.2f}"),
            ("Clientes que pasaron a Súper (por día)", f"{sin.prom('migrados_gnc_dia'):.2f}", f"{con.prom('migrados_gnc_dia'):.2f}"),
            ("Súper vendido (L/día)", f"{super_sin:,.0f}", f"{super_con:,.0f}"),
            ("Espera en la hora pico (min)", f"{sin.prom('espera_pico'):.2f}", f"{con.prom('espera_pico'):.2f}"),
            ("Días con corte de GNC (%)", f"{sin.prom('dias_corte_gnc_pct'):.1f}", f"{con.prom('dias_corte_gnc_pct'):.1f}"),
        ]
        st.dataframe(
            pd.DataFrame(filas, columns=["Indicador", "Sin cortes (contrato firme)", "Con los cortes elegidos"]),
            hide_index=True,
        )
        st.caption(
            "Resultado de la última comparación. Los que pasan a Súper suman litros de nafta "
            "(y cola en la zona A); los que se pierden son venta de GNC que no se recupera."
        )


# =============================================================================
# Pestaña: la estación (caso real)
# =============================================================================
def pestania_estacion() -> None:
    """Ficha de la estación, esquema del playón, advertencias y contradicciones."""
    st.subheader("La estación: Shell de Av. Balloffet y Los Sauces")
    st.markdown(
        "Estación de servicio **Shell** — Av. Balloffet 1810 esq. Av. Los Sauces, "
        "San Rafael, Mendoza (operador **LOS SAUCES S.R.L.**). Es el caso real del TP: "
        "una esquina urbana entre la RN 143 y la RP 158."
    )

    est = sorted((d for d in REGISTRO if d.id.startswith("EST-")), key=lambda d: d.id)
    columnas = st.columns(2)
    for i, d in enumerate(est):
        with columnas[i % 2]:
            st.markdown(
                f"**{d.nombre}** {insignia_html(d)}<br/>"
                f"<small>{d.valor}</small>"
                f"<small> — {d.fuente}</small>",
                unsafe_allow_html=True,
            )

    st.markdown("#### El playón: 6 surtidores de doble cara = 12 caras en 3 zonas")
    st.caption(
        "S1–S2 nafta (Súper y V-Power) · S3 diésel (G2 y G3) · S4–S6 GNC. Servicio "
        "atendido por playeros, playa 24 h."
    )
    componentes.html(esquema_estacion_html(), height=340)

    st.markdown("#### Advertencias (§5.3)")
    for aviso in ADVERTENCIAS:
        st.markdown(f"- {aviso}")

    st.markdown("#### Contradicciones entre fuentes (§4.2)")
    st.caption(
        "El valor adoptado se ve en la pestaña **Datos y fuentes**. Las alternativas "
        "que perdieron quedan como ejes del análisis de sensibilidad."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "ID": c.id,
                    "Tema": c.tema,
                    "Impacto": c.impacto,
                    "Valor adoptado": c.adoptado,
                    "Alternativas": c.alternativas,
                }
                for c in CONTRADICCIONES
            ]
        ),
        hide_index=True,
        height=360,
    )


# =============================================================================
# Pestaña: datos y fuentes (el Registro completo)
# =============================================================================
def pestania_datos_fuentes() -> None:
    """El Registro de datos completo, con filtros, alternativas y CSV (§8.2)."""
    st.subheader("Registro de datos (§5.1)")
    st.caption(
        "Todo parámetro del modelo tiene su `Dato` con fuente, nivel de evidencia, tipo "
        "y confianza. Las alternativas que perdieron las contradicciones de §4.2 quedan "
        "en el Registro y entran al análisis de sensibilidad. Todavía no hay datos de la "
        "propia estación: el relevamiento (§12) los cargará como `observacion` (🔵)."
    )

    tabla = tabla_registro()
    filtro_tipo = st.multiselect(
        "Filtrar por tipo",
        ["dato", "estimacion", "observacion", "supuesto", "heredado", "alternativa"],
    )
    vista = tabla if not filtro_tipo else tabla[tabla["Tipo"].isin(filtro_tipo)]
    st.dataframe(vista, hide_index=True, height=420)

    st.download_button(
        "⬇️ Descargar el Registro completo (CSV)",
        data=csv_registro(),
        file_name="registro_datos_shell_san_rafael.csv",
        mime="text/csv",
        help="Incluye todas las filas, las alternativas de §4.2 y las contradicciones.",
    )

    st.markdown("#### Contradicciones y alternativas (§4.2)")
    for c in CONTRADICCIONES:
        with st.expander(f"{c.id} · {c.tema} — impacto {c.impacto}"):
            st.markdown(f"**Valor adoptado:** {c.adoptado}")
            st.markdown(f"**Alternativas (sensibilidad):** {c.alternativas}")


# =============================================================================
# Aplicación
# =============================================================================
def politica_configurada(costos, p: ParametrosSimulacion):
    """Busca en el barrido la política que está configurada ahora, para comparar."""
    if not costos:
        return None
    return next(
        (
            c
            for c in costos
            if c.punto_pedido == p.tanque.punto_pedido
            and c.cantidad_pedido == p.tanque.cantidad_pedido
        ),
        None,
    )


def correr_todo(
    p: ParametrosSimulacion, eco: ParametrosEconomicos, replicas: int, semilla: int
) -> None:
    """Corre los escenarios (o la estación real) y la réplica con traza; guarda todo en la sesión."""
    if p.estacion_real:
        # Un único "escenario Base" real; el catálogo S0–S12 llega en la Fase 7.
        resultados = [correr_estacion_real_cacheado(p, replicas, semilla)]
    else:
        resultados = correr_escenarios_cacheado(p, replicas, semilla)
    traza = correr_traza_cacheada(p, semilla)

    st.session_state.resultados = resultados
    st.session_state.traza = traza
    st.session_state.economia = analizar_escenarios(resultados, eco, p)
    st.session_state.parametros = p
    st.session_state.parametros_eco = eco
    st.session_state.replicas = replicas
    st.session_state.semilla_usada = semilla
    # El barrido de políticas corresponde a otros parámetros: se descarta.
    st.session_state.costos_politicas = None
    st.session_state.politica_actual = None
    st.session_state.costos_real = None
    st.session_state.efecto_cortes = None
    st.session_state.efecto_gnc = None


def main() -> None:
    st.markdown(css_global(), unsafe_allow_html=True)
    p, eco, replicas, semilla = leer_parametros()

    st.sidebar.divider()
    correr = st.sidebar.button("▶ Correr simulación", type="primary", width="stretch")

    st.title("⛽ Simulador de la Estación Shell — San Rafael")
    st.caption(
        "Simulación de eventos discretos — Investigación Operativa · Líneas de espera + "
        "inventario de combustible, con demanda Monte Carlo y análisis económico. "
        "Caso real: Av. Balloffet 1810 esq. Los Sauces."
    )

    # Al cambiar de modelo (real <-> clásico) los resultados anteriores no sirven para nada:
    # se vuelve a correr sin esperar el botón.
    cambio_de_modelo = (
        "parametros" in st.session_state
        and st.session_state.parametros.estacion_real != p.estacion_real
    )
    if correr or "resultados" not in st.session_state or cambio_de_modelo:
        with st.spinner(
            f"Simulando {replicas} réplicas de {p.dias} días "
            f"{'de la estación real' if p.estacion_real else 'en 4 escenarios'}…"
        ):
            correr_todo(p, eco, replicas, semilla)

    p_corrida: ParametrosSimulacion = st.session_state.parametros
    if p != p_corrida or eco != st.session_state.parametros_eco:
        st.info(
            "Cambiaste parámetros: lo que se muestra es la corrida anterior. "
            "Apretá **Correr simulación** para actualizar.",
            icon="🔄",
        )

    # La recomendación se arma acá, antes de las pestañas, con lo que haya en la sesión:
    # los escenarios de capacidad y, si ya se corrió el barrido, la política de reposición.
    costos = st.session_state.get("costos_politicas")
    st.session_state.politica_actual = politica_configurada(costos, p_corrida)
    st.session_state.recomendacion = recomendacion(
        st.session_state.economia,
        st.session_state.resultados,
        costos,
        st.session_state.politica_actual,
    )

    pestanias = st.tabs(
        [
            "🏪 La estación",
            "🎬 Animación",
            "📊 Indicadores",
            "🎲 Demanda",
            "🛢️ Inventario",
            "🗺️ Red y rutas",
            "🔥 GNC",
            "⚖️ Escenarios",
            "💰 Economía",
            "📝 Conclusión",
            "📖 Modelo y método",
            "📚 Datos y fuentes",
        ]
    )
    with pestanias[0]:
        pestania_estacion()
    with pestanias[1]:
        pestania_animacion(p_corrida)
    with pestanias[2]:
        pestania_indicadores(p_corrida)
    with pestanias[3]:
        pestania_demanda(p_corrida)
    with pestanias[4]:
        pestania_inventario(p_corrida, st.session_state.parametros_eco)
    with pestanias[5]:
        pestania_red(p_corrida)
    with pestanias[6]:
        pestania_gnc(p_corrida)
    with pestanias[7]:
        pestania_escenarios()
    with pestanias[8]:
        pestania_economia(p_corrida, st.session_state.parametros_eco)
    with pestanias[9]:
        pestania_conclusion()
    with pestanias[10]:
        pestania_modelo(p_corrida)
    with pestanias[11]:
        pestania_datos_fuentes()

    st.divider()
    st.caption(PIE_NO_AFILIADO)
    st.sidebar.divider()
    st.sidebar.caption(PIE_NO_AFILIADO)


if __name__ == "__main__":
    main()
