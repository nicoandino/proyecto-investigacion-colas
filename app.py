"""Simulador de Estación de Servicio — Investigación Operativa.

Interfaz del simulador: se configuran los parámetros en la barra lateral, se corre la
simulación y se ven la animación, los indicadores, la demanda Monte Carlo, el inventario,
la comparación de escenarios, el análisis económico y la conclusión.

Para ejecutar:
    .venv/Scripts/streamlit run app.py
"""

from __future__ import annotations

import time
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
    ParametrosEventos,
    ParametrosGNC,
    ParametrosSimulacion,
    ParametrosTanque,
    Triangular,
    dias_del_mes,
    dias_y_fecha,
    inventario_real,
    turnos_de,
)
from sim.economia_real import (
    MOTIVOS as MOTIVOS_ECO,
    avisos as avisos_economia,
    conclusiones as conclusiones_economia,
    decision_s6,
    economia_de,
    km_por_viaje,
    margen_de_equilibrio_por_litro,
    resumir_economia,
)
from sim.periodo import (
    CLIENTELAS,
    FRANJAS,
    MARGENES_REGISTRO,
    SEMANAS,
    MESES as MESES_PERIODO,
    NIVELES_DEMANDA,
    TEMPORADAS,
    Ajustes,
    Edicion,
    EscenarioUnico,
    Periodo,
    anio_completo,
    aplicar_ajustes,
    aplicar_edicion,
    con_periodo,
    cortes_gnc_previstos,
    gnc_con_ajustes,
    litros_de_nivel,
    por_dias,
    por_meses,
    por_temporada,
    texto_fecha,
)
from sim.sensibilidad import (
    EJES,
    contradicciones_y_ejes,
    correr_sensibilidad,
    listado_registro,
)
from sim.escenarios import (
    ESTACIONES,
    MESES,
    catalogo,
    correr_catalogo,
    correr_estaciones,
    diferencia_pareada,
    es_significativa,
    para_mes,
)
from sim.datos import AVISO_FUENTES, CONTRADICCIONES, PIE_NO_AFILIADO, REGISTRO, por_id, valor
from sim.distribuciones import Aleatorio
from sim.eventos import CATALOGO as CATALOGO_EVENTOS, POR_ID as CATALOGO_EVENTOS_POR_ID
from sim.eventos import calendario as calendario_eventos, texto_frecuencia
from sim.pronostico import politica_por_pronostico
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
    Q_EN_DIAS,
    S_EN_DIAS,
    PuntoBarrido,
    ResultadoBarridoReal,
    ResultadoEscenario,
    barrer_politicas,
    buscar,
    con_politica,
    con_politicas,
    correr_escenarios,
    correr_estacion_real,
    correr_replica,
    correr_replicas,
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
    rutas_posibles,
)
from ui import animacion, graficos, graficos_escenarios, graficos_gnc, graficos_red, vistas
from ui.datos_ui import (
    csv_registro,
    insignia_html,
    tabla_registro,
)
from ui.tema import css_global
from ui.textos import (
    COMPARACION,
    COMPARACION_CATALOGO,
    DESCRIPCION_METODO,
    DESCRIPCION_MODELO,
    DESCRIPCION_MONTECARLO,
    INDICADORES_CLIENTES,
    INDICADORES_COLAS,
    INDICADORES_COMPLEMENTARIOS,
    INDICADORES_DIFERENCIA,
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
def correr_estaciones_cacheado(p: ParametrosSimulacion, replicas: int, semilla: int):
    return correr_estaciones(p, replicas=replicas, semilla_base=semilla)


@st.cache_data(show_spinner=False, max_entries=4)
def correr_catalogo_cacheado(
    p: ParametrosSimulacion, mes: int, replicas: int, semilla: int, nombres: tuple[str, ...]
):
    return correr_catalogo(p, mes, replicas=replicas, semilla_base=semilla, nombres=nombres)


@st.cache_data(show_spinner=False, max_entries=3)
def correr_sensibilidad_cacheado(
    p: ParametrosSimulacion, eco: ParametrosEconomicos, mes: int, replicas: int, semilla: int
):
    return correr_sensibilidad(p, eco, mes=mes, replicas=replicas, semilla_base=semilla)


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
                     "dedican 6 de las 12 caras (C8).",
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
def precios_por_producto(eco: ParametrosEconomicos) -> dict[str, float]:
    """Precio de cada producto del motor ($/L; el GNC por m³), con V-Power = el 'premium' de ECO-08."""
    d = dict(eco.precios)
    return {
        "super": d["super"], "vpower": d["premium"], "diesel_g2": d["diesel_g2"],
        "diesel_g3": d["diesel_g3"], "gnc": d["gnc"],
    }


def pestania_animacion(p: ParametrosSimulacion) -> None:
    """El tablero animado de TODO el período: un día cada 5 segundos (se puede cambiar)."""
    dt = animacion.dt_para(p.dias)
    p_anim = replace(p, animar_todo=True, dt_traza=dt, dia_animado=1)
    with st.spinner("Preparando la animación de todos los días…"):
        traza = correr_traza_cacheada(p_anim, st.session_state.semilla_usada)
    periodo = st.session_state.get("periodo")
    st.caption(
        f"{periodo.titulo + ' — ' + periodo.texto + '. ' if periodo else ''}"
        f"Se reproducen los {p.dias} días uno detrás de otro (por defecto, 5 segundos cada día); "
        f"la barra de abajo permite saltar a cualquier día. Cada auto tiene el color de su producto; "
        f"cada cara tiene 3 lugares de cola. Un cuadro cada {dt:g} minutos simulados. Cuando se pide un camión o "
        f"se corta el GNC, la reproducción se detiene y aparece un aviso (se puede apagar abajo)."
    )
    componentes.html(
        animacion.reproductor_html(
            traza, p_anim, precios_por_producto(st.session_state.parametros_eco),
            periodo.titulo if periodo else "", str(st.session_state.get("corrida_n", 0)),
        ),
        height=animacion.ALTO_COMPONENTE,
    )


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


# =============================================================================
# Pestaña: qué se sorteó (sólo en la simulación editada)
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


def pestania_sorteos(p: ParametrosSimulacion) -> None:
    """Qué se sorteó en la simulación EDITADA: los Monte Carlo de 5 pasos, la semilla y los demás azares."""
    traza = st.session_state.traza
    mes_inicio = p.fecha_inicio[0]

    st.subheader("Qué se sorteó en esta simulación")
    st.warning(
        f"Esta simulación fue **editada**, así que usa azar (semilla **{st.session_state.semilla_usada}**; con la "
        f"misma semilla da siempre lo mismo). Acá se explica cada cosa que se sorteó. En la simulación con "
        f"datos reales no se sortea nada y esta pestaña no existe.",
        icon="🎲",
    )
    st.markdown(
        "- **Cuándo llega cada cliente:** proceso de Poisson no homogéneo (tiempos exponenciales con la tasa de "
        "cada hora del perfil).\n"
        "- **Qué producto y qué vehículo es:** dos sorteos Monte Carlo de 5 pasos (tablas de abajo).\n"
        "- **Cuántos litros carga y cuánto tarda:** distribuciones triangulares (mínimo, moda, máximo).\n"
        "- **Si entra al minimarket y cuánto tarda en la caja:** Bernoulli y triangular.\n"
        "- **Cuánto tarda cada camión:** triangular (24 · 36 · 48 h) más la demora de un corte de ruta, si hay.\n"
        "- **Las fechas de los cortes de GNC y cuántos clientes pasan a Súper.**"
        + ("\n- **Los eventos aleatorios** prendidos en el menú, con su propia semilla "
           f"({p.eventos.semilla}): detalle en la pestaña ⚡ Eventos." if p.eventos.activos else "")
    )

    st.markdown("##### De los litros por mes a los clientes por día")
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
        pestania_sorteos(p)
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
        f"Cada combustible líquido tiene su tanque y su propio camión (un pedido lleva un solo producto). "
        f"El camión tarda entre {plazo.minimo:.0f} y {plazo.maximo:.0f} horas (lo más probable, "
        f"{plazo.moda:.0f} h). El GNC no tiene tanque: sale de la red de gas y está en la pestaña GNC."
    )

    st.markdown("##### 1. Cómo se movió cada tanque")
    st.plotly_chart(graficos.grafico_tanques_real(traza, p), key="g_tanques_real")
    st.caption(
        "Un diente de sierra por tanque: baja mientras se vende y sube de golpe cuando descarga el "
        "camión. La línea naranja es el punto de pedido s; donde la curva toca el cero, ese producto "
        "dejó de venderse aunque los otros sigan."
    )

    st.markdown("##### 2. Quiebres de stock y lo que no se vendió")
    vistas.bloque_quiebres(p, base.replicas[0], eco)

    st.markdown("##### 3. Cuándo se pide el camión: la política (s, Q) de cada tanque")
    st.caption(
        "Cuando lo que hay en el tanque **más lo que ya viene en camino** baja hasta el **punto de pedido s**, "
        "se pide un camión con **Q litros**. Si s es menor que lo que se vende mientras viaja el camión, el "
        "tanque se vacía antes de que llegue."
    )
    nombres = {pr.id: pr.nombre for pr in p.productos}
    litros_dia = promedio_por_producto(base.replicas, "litros_vendidos_por_producto")
    filas = []
    riesgosos = []
    for inv in p.inventario:
        consumo_dia = litros_dia[inv.producto]
        consumo_en_plazo = consumo_dia / 24.0 * inv.plazo_entrega.media
        filas.append(
            {
                "Tanque": nombres[inv.producto],
                "Capacidad": f"{vistas.ent(inv.capacidad)} L",
                "Punto de pedido (s)": f"{vistas.ent(inv.punto_pedido)} L",
                "Cantidad por camión (Q)": f"{vistas.ent(inv.cantidad_pedido)} L",
                "Se vende por día": f"{vistas.ent(consumo_dia)} L",
                "s alcanza para": f"{vistas.dec(inv.punto_pedido / consumo_dia)} días" if consumo_dia else "—",
                "Se vende mientras viaja el camión": f"{vistas.ent(consumo_en_plazo)} L",
            }
        )
        if inv.punto_pedido < consumo_en_plazo:
            riesgosos.append(nombres[inv.producto])
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    if riesgosos:
        st.warning(
            f"En {', '.join(riesgosos)} el punto de pedido es menor que lo que se vende mientras viaja el "
            f"camión: ahí el quiebre es esperable con esta política.",
            icon="⚠️",
        )

    vistas.bloque_stock_seguridad(p)

    st.caption(
        "¿Cuál sería la mejor política (s, Q) de cada tanque? Esa búsqueda está en el **Caso de informe** (botón "
        "en el menú principal), fuera del flujo normal porque prueba 14 políticas (13 de la grilla y la del pronóstico)."
    )


# --- Búsqueda de la mejor política (s, Q): de a una política por vez ------------------
#: Tope de tiempo real de la búsqueda (segundos). Si se pasa, se detiene y muestra lo evaluado.
TOPE_BUSQUEDA_S = 180.0
#: Segundos reales por día simulado de una réplica (medido: un año ≈ 5,2 s); sólo para estimar.
SEGUNDOS_POR_DIA = 5.2 / 365


def etiquetas_grilla() -> list[str]:
    """Nombre de cada punto de la grilla, en el orden de `grilla_politicas_real`."""
    return ["La cargada en esta corrida (INV-07 o la elegida en el menú)"] + [
        f"s = {s:g} · Q = {q:g} días de venta".replace(".", ",") for s in S_EN_DIAS for q in Q_EN_DIAS
    ] + ["Por pronóstico: s con stock de seguridad (pestaña 📈 Pronóstico)"]


def puntos_de_busqueda(p: ParametrosSimulacion) -> list[dict[str, tuple[float, float]]]:
    """Las 13 políticas de la grilla y, como candidata 14, la del pronóstico (stock de seguridad, P4)."""
    return grilla_politicas_real(p) + [politica_por_pronostico(p)]


def seccion_mejor_politica(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> None:
    """Explicación + el buscador (que corre en un fragmento aparte, sin bloquear la app)."""
    st.subheader("¿Cuál es la mejor política de reposición de cada tanque?")
    st.markdown(
        "Se prueban 13 combinaciones de **punto de pedido (s)** y **cantidad a pedir (Q)** "
        "—medidas en días de venta de cada producto— **más la política por pronóstico** (s con el stock de "
        "seguridad que sale del error de la serie real) y se elige, **tanque por tanque**, la "
        "de menor costo mensual:\n\n"
        "**costo = flete de los pedidos + almacenamiento + venta perdida por falta de stock**\n\n"
        "Como cada camión es independiente y cada producto tiene su propio stream de plazos, "
        "las 4 curvas se miden en las mismas corridas. La política cargada es la primera "
        "evaluación, así que la mejor nunca es peor que ella."
    )
    busqueda = st.session_state.get("busqueda")
    corriendo = busqueda is not None and busqueda["estado"] == "corriendo" and busqueda["p"] == p
    # Mientras corre, el fragmento se vuelve a ejecutar solo y evalúa UNA política por vuelta: el resto
    # de la app sigue respondiendo y un clic en otra parte no la reinicia (el avance queda en la sesión).
    st.fragment(run_every=0.2 if corriendo else None)(_buscador_de_politicas)(p, eco)


def _buscador_de_politicas(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> None:
    busqueda = st.session_state.get("busqueda")
    if busqueda is not None and busqueda["p"] != p:
        busqueda = None                      # es de otra corrida: no vale
    total = len(puntos_de_busqueda(p))

    if busqueda is None or busqueda["estado"] != "corriendo":
        c1, c2 = st.columns([1, 2])
        if p.determinista:
            replicas = 1
            c1.caption("Sin azar: **1 corrida por política** (dos réplicas darían idénticas).")
        else:
            replicas = c1.slider("Réplicas por política", 1, 4, 2, 1, key="rep_barrido_real")
        estimado = total * replicas * p.dias * SEGUNDOS_POR_DIA
        c2.caption(
            f"Se van a evaluar **{total} políticas** × {replicas} corrida{'s' if replicas > 1 else ''} "
            f"de {p.dias} días: ≈ {estimado:.0f} s. Se ve el avance, se puede detener y se corta sola "
            f"a los {TOPE_BUSQUEDA_S:.0f} s mostrando lo evaluado."
        )
        if st.button("🔎 Buscar la mejor política de cada tanque", type="primary", key="btn_buscar_pol"):
            st.session_state.busqueda = {
                "p": p, "replicas": replicas, "semilla": st.session_state.semilla_usada,
                "puntos": puntos_de_busqueda(p), "hechos": [], "inicio": time.time(),
                "estado": "corriendo", "segundos": 0.0,
            }
            st.session_state.costos_real = None
            st.rerun()                       # vuelta completa: el fragmento queda con run_every
        if busqueda is not None:
            _resultados_busqueda(p, busqueda)
        else:
            st.info("Todavía no se buscó la mejor política.", icon="ℹ️")
        return

    # --- Corriendo: la barra y el botón Detener primero (quedan a la vista mientras se evalúa),
    # después UNA evaluación. La vuelta siguiente la dispara `run_every`.
    hechos = busqueda["hechos"]
    st.progress(
        len(hechos) / total,
        text=f"Evaluando políticas: {len(hechos)} de {total} listas · {time.time() - busqueda['inicio']:.0f} s "
             f"(tope {TOPE_BUSQUEDA_S:.0f} s)",
    )
    if st.button("⏹ Detener la búsqueda", key="btn_detener_pol"):
        _cerrar_busqueda(p, eco, busqueda, "detenida")
    if len(hechos) < total:
        politicas = busqueda["puntos"][len(hechos)]
        replicas = correr_replicas(
            con_politicas(p, politicas), replicas=busqueda["replicas"], semilla_base=busqueda["semilla"]
        )
        hechos.append(PuntoBarrido(politicas=politicas, replicas=replicas))
    busqueda["segundos"] = time.time() - busqueda["inicio"]
    if len(hechos) >= total:
        _cerrar_busqueda(p, eco, busqueda, "terminada")
    if busqueda["segundos"] > TOPE_BUSQUEDA_S:
        _cerrar_busqueda(p, eco, busqueda, "tope")


def _cerrar_busqueda(p: ParametrosSimulacion, eco: ParametrosEconomicos, busqueda: dict, estado: str) -> None:
    """Costea lo evaluado (todo o una parte) y vuelve a correr la app para mostrar los resultados."""
    busqueda["estado"] = estado
    busqueda["segundos"] = time.time() - busqueda["inicio"]
    if busqueda["hechos"]:
        barrido = ResultadoBarridoReal(
            productos=tuple(i.producto for i in p.inventario), puntos=list(busqueda["hechos"])
        )
        st.session_state.costos_real = analizar_politicas_real(barrido, eco, p)
    st.rerun()


def _resultados_busqueda(p: ParametrosSimulacion, busqueda: dict) -> None:
    """Las evaluaciones juntas, con la ganadora marcada, y el detalle por tanque."""
    costos = st.session_state.get("costos_real")
    total = len(busqueda["puntos"])
    hechas = len(busqueda["hechos"])
    if not costos:
        st.info("La búsqueda se detuvo antes de evaluar alguna política.", icon="⏹")
        return
    if busqueda["estado"] != "terminada":
        motivo = "la detuviste" if busqueda["estado"] == "detenida" else f"llegó al tope de {TOPE_BUSQUEDA_S:.0f} s"
        st.warning(
            f"Búsqueda **incompleta** ({motivo}): se evaluaron {hechas} de {total} políticas. "
            f"La ganadora es la mejor **entre esas**.",
            icon="⏱",
        )
    else:
        st.success(f"Se evaluaron las {total} políticas en {busqueda['segundos']:.0f} s.", icon="✅")

    nombres = {pr.id: pr.nombre for pr in p.productos}
    etiquetas = etiquetas_grilla()
    totales = [sum(lista[k].costo_total for lista in costos.values()) for k in range(hechas)]
    ganadora = min(range(hechas), key=lambda k: totales[k])
    filas = []
    for k in range(hechas):
        filas.append({
            "": "🏆 ganadora" if k == ganadora else "",
            "N°": k + 1,
            "Política (igual en los 4 tanques)": etiquetas[k],
            "Camiones por mes": vistas.dec(sum(lista[k].pedidos_mes for lista in costos.values()), 1),
            "Litros sin vender por quiebre (por mes)": f"{sum(lista[k].litros_no_vendidos_mes for lista in costos.values()):,.0f} L".replace(",", "."),
            "Flete": pesos(sum(lista[k].costo_pedidos for lista in costos.values())),
            "Almacenamiento": pesos(sum(lista[k].costo_almacenamiento for lista in costos.values())),
            "Venta perdida": pesos(sum(lista[k].costo_faltante for lista in costos.values())),
            "COSTO TOTAL por mes": pesos(totales[k]),
        })
    st.markdown(f"##### Las {hechas} evaluaciones (costo de los 4 tanques juntos)")
    st.dataframe(pd.DataFrame(filas), hide_index=True, height=36 * (len(filas) + 1) + 3)
    st.caption(
        f"Ganadora: **{etiquetas[ganadora]}**. Costos con márgenes y flete heredados sin fuente (ECO-01/06/07): "
        "ordenan las políticas, no son cifras del negocio. Abajo, la mejor de **cada tanque** por separado."
    )

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
    """Comparación de capacidad del caso clásico (el caso real usa `pestania_comparar`)."""
    resultados = st.session_state.resultados

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
# =============================================================================
# Pestaña: sensibilidad (Fase 9, §7.8)
# =============================================================================
def pestania_sensibilidad(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> None:
    st.subheader("Sensibilidad: qué dato incierto mueve más la conclusión")
    if not p.estacion_real:
        st.info("La sensibilidad es del caso real. Elegí la **estación real** en la barra "
                "lateral.", icon="🌪️")
        return
    st.markdown(
        "Casi todos los datos del modelo son **supuestos o estimaciones** (no hay datos de la "
        "propia estación). Esta pestaña mide cuánto cambia el resultado si cada uno vale lo "
        "que dicen sus alternativas del Registro: se corre la estación con cada extremo, "
        "**dejando todo lo demás igual y con las mismas semillas**, y se mira el cambio en el "
        "margen mensual, la espera en la hora pico y el nivel de servicio. Los que están arriba "
        "son los que **hay que relevar primero**."
    )
    n_sim = sum(len(e.variantes) for e in EJES if not e.solo_economia) + 1
    c1, c2, c3 = st.columns([1, 1, 2])
    mes = c1.selectbox("Mes", list(range(1, 13)), index=6, key="sen_mes",
                       format_func=lambda m: MESES[m - 1].capitalize())
    replicas = c2.slider("Réplicas por variante", 1, 4, 2, 1, key="sen_rep")
    c3.caption(
        f"{len(EJES)} ejes, {sum(len(e.variantes) for e in EJES)} variantes "
        f"({n_sim} simulaciones × {replicas} réplicas ≈ {n_sim * replicas * 1.0:.0f} s; los ejes "
        f"económicos ◆ no vuelven a simular). Queda en caché. La base es el mes elegido con los "
        f"episodios de GNC forzados adentro."
    )
    semilla = st.session_state.semilla_usada
    if st.button("🌪️ Correr el tornado", type="primary", key="btn_tornado"):
        with st.spinner(f"Simulando {n_sim} configuraciones × {replicas} réplicas…"):
            resultado = correr_sensibilidad_cacheado(p, eco, mes, replicas, semilla)
        st.session_state.sensibilidad = (p, eco, resultado)
    guardado = st.session_state.get("sensibilidad")
    if not guardado:
        st.info("Apretá **Correr el tornado** para medirlo.", icon="▶")
    else:
        p_usado, eco_usado, res = guardado
        if p_usado != p or eco_usado != eco:
            st.info("Cambiaste parámetros: lo que se ve es el último tornado.", icon="🔄")
        etiquetas = {"Margen operativo ($/mes)": "margen", "Espera en la hora pico (min)": "espera",
                     "Nivel de servicio (puntos %)": "servicio"}
        elegida = st.radio("Métrica", list(etiquetas), horizontal=True, key="sen_metrica")
        metrica = etiquetas[elegida]
        cantidad = st.slider("Cuántos ejes mostrar", 5, len(res.ejes), 15, 1, key="sen_cant")
        st.plotly_chart(graficos_escenarios.grafico_tornado(res, metrica, cantidad),
                        key="g_tornado")
        ranking_margen = res.ranking("margen")
        mas_margen = ranking_margen[0]
        mas_margen_dato = next(e for e in ranking_margen if not e.rango_de_prueba)
        mas_espera = res.ranking("espera")[0]
        st.caption(escapar_pesos(
            f"Base ({MESES[res.mes - 1]}, {res.replicas} réplicas): margen "
            f"{pesos(res.base_margen.promedio)} ± {pesos(res.base_margen.semiamplitud)} por mes, "
            f"espera pico {res.base_espera.promedio:.2f} min, servicio "
            f"{res.base_servicio.promedio * 100:.1f} %. Para el **margen** manda "
            f"**{mas_margen.id} ({mas_margen.nombre})**"
            + (
                f", y entre los datos con rango del Registro **{mas_margen_dato.id} "
                f"({mas_margen_dato.nombre})**" if mas_margen.rango_de_prueba else ""
            )
            + f"; para la **espera** manda **{mas_espera.id} ({mas_espera.nombre})**: el ranking "
            f"cambia según lo que se mire. ◆ = eje económico (no vuelve a simular). † = los "
            f"extremos son un **rango de prueba** que puso el grupo (ECO-01/02/03/06/07/10), no "
            f"un dato: dicen qué tan sensible es el margen a ese número, no qué valor tiene. "
            f"Con {res.replicas} réplicas los intervalos son anchos: leelos como órdenes de "
            f"magnitud, no como cifras."
        ))
        filas = []
        for eje in res.ranking(metrica):
            for v in eje.variantes:
                filas.append({
                    "Eje": f"{eje.id} · {eje.nombre}" + (" ◆" if eje.solo_economia else "")
                    + (" †" if eje.rango_de_prueba else ""),
                    "Extremo": v.etiqueta,
                    "Δ margen por mes": f"{pesos(v.d_margen.promedio)} ± {pesos(v.d_margen.semiamplitud)}",
                    "Δ espera pico (min)": f"{v.d_espera.promedio:+.2f} ± {v.d_espera.semiamplitud:.2f}",
                    "Δ servicio (pp)": f"{v.d_servicio.promedio * 100:+.2f} ± {v.d_servicio.semiamplitud * 100:.2f}",
                })
        with st.expander("Todos los extremos con su IC 95 % (ordenados por la métrica elegida)"):
            st.dataframe(pd.DataFrame(filas), hide_index=True,
                         height=min(900, 36 * (len(filas) + 1) + 3))

    st.markdown("##### Qué datos son eje y cuáles no")
    st.caption(
        "Todas las contradicciones del §4.2 y todos los datos supuesto, heredado o estimación del "
        "Registro, con su eje (o el motivo por el que no lo son)."
    )
    with st.expander("Contradicciones C1–C20 y su eje"):
        st.dataframe(pd.DataFrame(contradicciones_y_ejes()), hide_index=True)
    with st.expander("Todos los datos supuesto / heredado / estimación"):
        listado = pd.DataFrame(listado_registro())
        st.dataframe(listado, hide_index=True, height=min(900, 36 * (len(listado) + 1) + 3))


def pestania_economia_real(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> None:
    st.subheader("Economía de la estación real")
    for aviso in avisos_economia(p, eco):
        st.warning(escapar_pesos(aviso), icon="💰")

    base = st.session_state.resultados[0]
    lista = economia_de(base, eco)
    res = resumir_economia(lista)
    dias = lista[0].dias_mes
    st.markdown(f"##### Ingresos y costos de un mes de {dias} días")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos", escapar_pesos(pesos(res["ingreso_total"].promedio)))
    c2.metric("Costos", escapar_pesos(pesos(res["costo_total"].promedio)))
    margen = res["margen_operativo"]
    c3.metric("Margen operativo", escapar_pesos(pesos(margen.promedio)))
    if len(lista) > 1:
        c3.caption(escapar_pesos(f"± {pesos(margen.semiamplitud)} (IC 95 %)"))
    equilibrio = margen_de_equilibrio_por_litro(lista[0], eco)
    c4.metric("Margen por litro de equilibrio", escapar_pesos(f"${equilibrio:,.0f}/L"))
    liquidos = [pr.id for pr in p.productos if not pr.es_gnc]
    usados = sorted({eco.margen_de(x) for x in liquidos})
    c4.caption(escapar_pesos(
        f"hoy se usa ${usados[0]:,.0f}/L (heredado sin fuente)" if len(usados) == 1
        else "hoy se usan " + " · ".join(f"{NOMBRES_PRODUCTO[x]} ${eco.margen_de(x):,.0f}" for x in liquidos)
    ))
    if margen.promedio < 0:
        st.error(
            escapar_pesos(
                f"Con los márgenes adoptados la estación **no cubre sus costos** "
                f"({pesos(margen.promedio)} por mes). Para empatar haría falta un margen de "
                f"${equilibrio:,.0f} por litro (hoy ${eco.margen_por_litro:,.0f}, heredado sin "
                f"fuente). O el margen real es mayor, o la demanda real es mayor que los "
                f"{p.litros_mes:,.0f} L/mes (C2): es lo primero que cierra el relevamiento."
            ),
            icon="⚖️",
        )

    ingresos = [(n, v) for n, v in (
        ("Combustible líquido", res["ingreso_combustible"].promedio),
        ("GNC", res["ingreso_gnc"].promedio),
        ("Minimarket", res["ingreso_minimarket"].promedio),
    )]
    costos = [(n, res[k].promedio) for n, k in (
        ("Flete", "flete"), ("Almacenamiento", "almacenamiento"), ("Personal", "personal_total"),
    )]
    if res["costo_eventos"].promedio > 0:
        costos.append(("Eventos aleatorios", res["costo_eventos"].promedio))
    st.plotly_chart(
        graficos_escenarios.grafico_cascada_economica(
            ingresos, costos, "De los ingresos al margen operativo (un mes)"),
        key="g_cascada",
    )
    st.caption(
        escapar_pesos(
            f"El costo de personal sale de la dotación del modelo (playeros por tramo horario, "
            f"cajas, más encargado y tienda de ECO-11) × {eco.cobertura_francos:g} personas por "
            f"puesto (francos, ECO-10) × sueldo con adicionales (ECO-04). El flete usa "
            f"{km_por_viaje(p):,.0f} km de ida y vuelta desde el origen elegido."
        )
    )

    st.caption(
        "Lo que cada escenario S0–S12 le suma o resta al margen mensual está en el **Caso de informe** (menú principal)."
    )

    with st.expander("Cómo se calcula"):
        st.markdown(escapar_pesos(
            f"""
| Concepto | Fórmula |
|---|---|
| Ingreso por producto | litros (o m³ de GNC) vendidos × margen (${eco.margen_por_litro:,.0f}/L · ${eco.margen_gnc:,.0f}/m³) |
| Ingreso del minimarket | compras × ${eco.margen_compra:,.0f} |
| Flete | pedidos del mes × (fijo ${eco.costo_pedido:,.0f} + ${eco.flete_por_km:,.0f}/km × km de ida y vuelta) |
| Almacenamiento | litros promedio en los tanques × ${eco.costo_almacenamiento_litro_mes:,.0f} por litro y por mes |
| Personal | personas-turno × {eco.cobertura_francos:g} (francos) × sueldo: playero ${eco.sueldo_playero_mensual:,.0f}, cajero y tienda ${eco.sueldo_cajero_mensual:,.0f}, encargado ${eco.sueldo_encargado_mensual:,.0f} |
| Eventos aleatorios (si se prendieron) | horas extra de las licencias cubiertas × valor de la hora (sueldo ÷ 200 h, EVT-15) × 1,5 (× 2 el domingo) + visitas del técnico (sin dato: $0) |
| **Margen operativo** | **ingresos − costos** (la venta perdida NO entra) |
| Venta perdida (por motivo) | clientes perdidos × (litros medios × margen + prob. de compra × margen del minimarket); corte de GNC en m³ |

La venta perdida es un **costo de oportunidad**: no sale del bolsillo, pero es plata que la
estación deja sobre la mesa. No se resta del margen (sería contarla dos veces: ya falta el
ingreso de esos clientes) y se informa aparte.
"""))


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


def seccion_decision(eco: ParametrosEconomicos) -> None:
    """Caso de informe: qué le hace cada escenario del catálogo al margen mensual (Fase 8)."""
    st.markdown("##### Decisión en $/mes: qué le hace cada escenario al margen")
    comparacion = st.session_state.get("comparacion")
    if not comparacion:
        st.info("Corré los escenarios arriba y acá aparece lo que cada uno suma o resta al margen mensual.",
                icon="🧪")
    else:
        _, mes_usado, resultados_cmp = comparacion
        conc = conclusiones_economia(resultados_cmp, eco)
        tabla = pd.DataFrame([
            {
                "ID": c.id,
                "Escenario": c.nombre,
                "Pregunta": c.pregunta,
                "Δ margen por mes": f"{pesos(c.d_margen.promedio)} ± {pesos(c.d_margen.semiamplitud)}",
                "Δ personal": pesos(c.d_personal.promedio),
                "Δ ingresos": pesos(c.d_ingreso.promedio),
                "Δ venta perdida (no se resta)": pesos(c.d_venta_perdida.promedio),
                "Veredicto": c.veredicto,
            }
            for c in conc
        ])
        st.markdown(f"Mes de la comparación: **{MESES[mes_usado - 1]}**; Δ contra S0, con la "
                    "diferencia pareada y su IC 95 %.")
        st.dataframe(tabla, hide_index=True, height=38 * (len(tabla) + 1))
        st.plotly_chart(
            graficos_escenarios.grafico_delta_margen(
                conc, "Δ del margen operativo mensual contra S0 (promedio ± IC 95 % de la diferencia)"),
            key="g_delta_margen",
        )
        d6 = decision_s6(resultados_cmp, eco)
        if d6:
            st.markdown(escapar_pesos(
                f"**S6 — ¿un playero más en el pico o más stock?** Playero extra: "
                f"{pesos(d6['d_playero'].promedio)} ± {pesos(d6['d_playero'].semiamplitud)} por mes "
                f"(cuesta {pesos(d6['costo_playero'].promedio)} de personal). Stock extra: "
                f"{pesos(d6['d_stock'].promedio)} ± {pesos(d6['d_stock'].semiamplitud)} por mes. "
                f"Diferencia (playero − stock): {pesos(d6['playero_menos_stock'].promedio)} ± "
                f"{pesos(d6['playero_menos_stock'].semiamplitud)} → **{d6['mejor']}**."
            ))
        st.caption(
            "Veredicto según el IC 95 % de la diferencia con S0: *suma margen* y *resta margen* "
            "son efectos que no se explican por azar; *no se distingue* quiere decir que con "
            "estas réplicas y estos márgenes placeholder no se puede afirmar nada."
        )



# =============================================================================
# Pestaña: conclusión
# =============================================================================
def escapar_pesos(texto: str) -> str:
    """Escapa el signo $ para que Streamlit no lo interprete como fórmula LaTeX."""
    return texto.replace("$", r"\$")


def pestania_conclusion_real(p: ParametrosSimulacion) -> None:
    """La conclusión de ESTA corrida: cada frase sale de sus resultados (no hay texto fijo)."""
    r = st.session_state.resultados[0].replicas[0]
    eco = st.session_state.parametros_eco
    periodo: Periodo = st.session_state.periodo
    economia = resumir_economia(economia_de(st.session_state.resultados[0], eco))
    t = dict(r.totales)
    dias = max(r.dias_medidos, 1)
    llegadas = max(t["llegadas"], 1)
    por_espera = t["perdidos_espera"] + t["perdidos_cola_llena"]
    por_stock = t["perdidos_sin_combustible"]
    por_gnc = t["perdidos_corte_gnc"]
    perdidos = por_espera + por_stock + por_gnc
    vacios = sum(q[1] for q in r.quiebres)
    horas_vacio = sum(q[2] for q in r.quiebres)
    causas = {f[0]: f[1:] for f in r.litros_perdidos_causa}
    venta_perdida = sum(sum(v) * eco.margen_de(pr) for pr, v in causas.items())

    st.subheader(f"Conclusión: {periodo.titulo.lower()} ({periodo.texto})")
    principal = max((por_espera, "la atención (colas y playeros)"), (por_stock, "el abastecimiento (tanques vacíos)"),
                    (por_gnc, "los cortes de GNC"))
    if perdidos <= 0.005 * llegadas:
        st.success(
            f"La estación atiende **casi toda** la demanda del período: se perdieron {vistas.ent(perdidos)} de "
            f"{vistas.ent(llegadas)} clientes ({vistas.pct(perdidos, llegadas)}).", icon="✅",
        )
    else:
        st.warning(
            f"Se perdieron **{vistas.ent(perdidos)} clientes** ({vistas.pct(perdidos, llegadas)}); la causa principal es "
            f"**{principal[1]}** ({vistas.ent(principal[0])} clientes).", icon="🧭",
        )

    lineas = [
        f"**Demanda:** llegaron {vistas.ent(llegadas)} clientes en {dias} días (≈ {vistas.ent(llegadas / dias)} por día) y se "
        f"vendieron {vistas.ent(r.litros_vendidos_dia - r.m3_gnc_vendidos_dia)} L de nafta y diésel por día.",
        f"**Colas:** la espera promedio fue {vistas.dec(r.espera_surtidor)} min y en la hora pico ({r.hora_pico:02d} h) "
        f"{vistas.dec(r.espera_pico)} min. ρ analítico en el pico: **{vistas.dec(p.rho_pico, 2)}** con "
        f"{max(p.playeros_por_turno)} playeros"
        + (" (al límite: más de 0,85)." if p.rho_pico >= 0.85 else " (con margen)."),
        f"**Por qué se perdieron clientes:** {vistas.ent(t['perdidos_espera'])} se cansaron de esperar, "
        f"{vistas.ent(t['perdidos_cola_llena'])} encontraron la cola llena, {vistas.ent(por_stock)} no pudieron cargar por "
        f"falta de stock y {vistas.ent(por_gnc)} se fueron por el corte de GNC.",
        f"**Tanques:** "
        + (f"quedaron vacíos {vistas.ent(vacios)} veces, {vistas.dec(horas_vacio)} h en total (sumando los tanques)."
           if vacios else "ningún tanque quedó vacío.")
        + (f" Hubo {vistas.ent(t['dias_con_quiebre'])} días con clientes sin cargar por falta de stock."
           if t["dias_con_quiebre"] else ""),
        f"**GNC:** "
        + (f"{vistas.ent(t['dias_con_corte_gnc'])} días con corte; {vistas.ent(t['migrados_gnc'])} clientes pasaron a Súper y "
           f"{vistas.ent(por_gnc)} se perdieron." if t["dias_con_corte_gnc"] else "no hubo cortes en este período."),
        *([escapar_pesos(
            f"**Eventos aleatorios** (semilla {p.eventos.semilla}): ocurrieron {len(r.eventos)}; los que más clientes "
            f"costaron: " + ", ".join(
                f"{CATALOGO_EVENTOS_POR_ID[e.id].nombre.lower()} del {vistas._cuando(p, e.inicio)} ({vistas.ent(e.perdidos)})"
                for e in sorted(r.eventos, key=lambda x: -x.perdidos)[:3] if e.perdidos
            ) + (f"; horas extra y técnico: {pesos(economia['costo_eventos'].promedio)} por mes." if economia['costo_eventos'].promedio else ".")
        )] if r.eventos else []),
        escapar_pesos(
            f"**Plata (márgenes heredados sin fuente):** margen operativo del mes "
            f"{pesos(economia['margen_operativo'].promedio)}; la venta que no se hizo vale ≈ {pesos(venta_perdida)} en "
            f"el período (costo de oportunidad, no se resta del margen)."
        ),
    ]
    for linea in lineas:
        st.markdown(f"- {linea}")

    st.markdown("#### Qué conviene probar después")
    sugerencias = []
    if por_espera > 0.005 * llegadas or p.rho_pico >= 0.85:
        sugerencias.append("Un **escenario único** (menú principal) con un playero más en la franja del pico, para ver "
                           "cuánto baja la espera y cuántos clientes se recuperan.")
    if vacios or por_stock:
        sugerencias.append("En el **Caso de informe**, la búsqueda de la mejor política (s, Q): los quiebres dependen de "
                           "cuándo y cuánto se pide.")
    if por_gnc:
        sugerencias.append("En el menú, la opción de **más cortes de GNC en todo el invierno** para ver el peor caso.")
    if st.session_state.get("modo") != "editada" and r.cola_surtidor < 0.1:
        sugerencias.append("**Editar simulación** (con azar o el doble de demanda en el pico): sin azar los clientes "
                           "llegan a intervalos exactos y casi no se forman colas.")
    if not sugerencias:
        sugerencias.append("Otro período (por ejemplo, el verano o las vacaciones de invierno) para comparar.")
    for linea in sugerencias:
        st.markdown(f"- {linea}")

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
            "ρ = λ_pico · E[minutos de playero por cliente] ÷ playeros, con todos los clientes (nafta, "
            "diésel y GNC: a todos los atiende un playero). Si ρ ≥ 1 la cola crece sin límite mientras dure el pico."
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
        "El camión sale del origen por el **camino más corto** (Dijkstra sobre los km de la red, "
        "notas 06 y 09). Un corte demora el viaje sólo si el arco cerrado está en ese camino: "
        "con origen Dock Sud, el corte nevado de la RN 143 Pareditas–San Rafael no está en la "
        "ruta. La demora se suma al plazo base (INV-01)."
    )
    st.markdown("##### Seguimiento del camión")
    componentes.html(
        animacion.seguimiento_html(p, str(st.session_state.get("corrida_n", 0))), height=animacion.ALTO_SEGUIMIENTO,
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

    plazo_medio = p.inventario[0].plazo_entrega.media
    st.markdown("##### Las otras rutas posibles, de mejor a peor")
    rutas = rutas_posibles(red)
    st.dataframe(pd.DataFrame([
        {
            "N°": k + 1,
            "Ruta": " → ".join(NOMBRE_NODO[n] for n in c.ruta),
            "Distancia": f"{vistas.dec(c.km)} km",
            f"Viaje a {red.velocidad_kmh:.0f} km/h": f"{vistas.dec(c.minutos / 60)} h",
            "Plazo de entrega promedio": f"{vistas.dec(plazo_medio + (c.minutos - optimo.minutos) / 60)} h",
            "Más que la óptima": "— (la óptima)" if k == 0 else f"+{vistas.dec((c.minutos - optimo.minutos) / 60)} h",
        }
        for k, c in enumerate(rutas)
    ]), hide_index=True)
    st.caption(
        f"Todas las rutas sin repetir ciudades desde {NOMBRE_NODO[red.origen]}. Plazo promedio = {vistas.dec(plazo_medio)} h "
        f"(INV-01, que ya incluye el viaje por la óptima) + lo que tarda de más esa ruta. Los cortes de ruta usan "
        f"estas mismas rutas para desviarse."
    )

    st.markdown("##### De dónde puede salir el camión")
    r = st.session_state.resultados[0].replicas[0]
    usados = {o: (n, red_) for o, n, red_ in r.pedidos_por_origen} or {
        red.origen: (sum(n for _, n in r.pedidos_total), 0)
    }
    descripcion = {
        "DOCK": "refinería de Shell/Raízen (origen documentado)",
        "ARROYO": "terminal de despacho de Raízen/Shell (Santa Fe)",
        "LUJAN": "refinería de YPF (último recurso: otra empresa)",
    }
    alternativos = tuple(valor("RED-19"))
    filas = []
    for o in ("DOCK", *alternativos):
        camino = camino_mas_corto(red, origen=o)
        extra = 0.0 if o == red.origen else camino.minutos - optimo.minutos + red.demora_redireccion_h * 60.0
        if o in red.origenes_no_disponibles:
            estado = "no disponible (marcado en el menú)"
        elif o == red.origen:
            estado = "habitual"
        elif o in red.origenes_alternativos:
            estado = f"alternativo n.º {red.origenes_alternativos.index(o) + 1}"
        else:
            estado = "alternativo (apagado)"
        n, redirigidos = usados.get(o, (0, 0))
        filas.append({
            "Origen": NOMBRE_NODO[o],
            "Qué es": descripcion.get(o, ""),
            "Distancia a la estación": f"{vistas.dec(camino.km)} km",
            "Plazo promedio": f"{vistas.dec(plazo_medio + extra / 60)} h",
            "Estado": estado,
            "Camiones de esta corrida": vistas.ent(n),
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    total_redirigidos = sum(x[2] for x in r.pedidos_por_origen)
    if red.origenes_alternativos:
        st.caption(
            f"Eventos de abastecimiento {'prendidos' if red.prob_origen_no_disponible > 0 else 'apagados'}"
            + (f" ({vistas.dec(100 * red.prob_origen_no_disponible, 0)} % de los pedidos, RED-20)"
               if red.prob_origen_no_disponible > 0 else "")
            + f". Si un origen no puede, el pedido pasa al siguiente con su ruta, su distancia y "
            f"{vistas.dec(red.demora_redireccion_h, 0)} h de demora por volver a gestionarlo (RED-21). En esta corrida se "
            f"redirigieron {vistas.ent(total_redirigidos)} camiones."
        )
    else:
        st.caption(
            "Eventos de abastecimiento apagados (menú): el camión sale siempre de Dock Sud por la ruta óptima. La Paz y "
            "Pareditas son cruces de ruta, no plantas de despacho (nota 09)."
        )

    corte_activo = next((c for c in red.cortes if c.id == red.escenario_corte), None)
    cerrados = corte_activo.arcos if corte_activo else ()
    vista_mapa = st.radio("Ver la red como", ("Mapa con relieve", "Esquema"), horizontal=True, key="red_vista_mapa",
                          help="El mapa con relieve necesita internet (teselas de OpenTopoMap); el esquema no.")
    if vista_mapa == "Mapa con relieve":
        st.plotly_chart(graficos_red.grafico_red_mapa(red, cerrados), key="g_red_mapa", config={"responsive": True})
        st.caption(
            "Amarillo con borde: la ruta óptima; rojo: un tramo cortado; azul: el desvío. Pasá el mouse por un tramo o "
            "una ciudad para ver la ruta y los km. " + graficos_red.ATRIBUCION_MAPA
            + ". Posiciones aproximadas; sin conexión a internet, usá el esquema."
        )
    else:
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
                "Arroyo Seco": _demora_texto(red, "ARROYO", corte),
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

    vistas.seccion_plan_red(p, st.session_state.resultados[0].replicas[0], dict(ajustes_actuales().topes_origen))


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
    st.info(
        f"**Lo que muestra el modelo:** {caras_gnc} de {caras_total} caras "
        f"({caras_gnc / caras_total:.0%}) son de GNC y los clientes GNC son ≈ {p.pct_gnc:.0%} de las "
        f"llegadas, así que los {g.compresores} compresores están ocupados sólo el "
        f"{base.prom('util_compresores') * 100:.1f} % del tiempo: la capacidad de GNC sobra para esa demanda.",
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
            "**No hay datos de cortes de GNC en este período:** no se realizaron cortes porque "
            "el período no incluye invierno (los cortes caen entre el 1/jun y el 31/ago). "
            "Para verlos, elegí un período que lo incluya (por ejemplo *Invierno* o el año completo).",
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
            f"(margen de ${float(por_id('ECO-03').valor):,.0f}/m³: ECO-03, heredado sin fuente)."
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
# Pestaña: estaciones del año (Fase 7, §7.8)
# =============================================================================
PRESETS_ESTACIONALIDAD = {
    "La de la barra lateral": None,
    "Neutra (default)": ESTACIONALIDAD_NEUTRA,
    "Leve (±6 %)": ESTACIONALIDAD_LEVE,
    "Proxy turístico": ESTACIONALIDAD_PROXY,
}

#: Segundos por réplica de un mes (medido: ≈ 1,3 s); sólo para estimar el tiempo de espera.
SEGUNDOS_POR_REPLICA = 1.3


def _litros_por_dia_de_cada_mes(p: ParametrosSimulacion) -> list[float]:
    """Litros por día esperados en cada mes (estacionalidad y calendario real, sin simular)."""
    salida = []
    for mes in range(1, 13):
        p_mes = para_mes(p, mes)
        salida.append(
            sum(p_mes.litros_del_dia(d) for d in range(1, p_mes.dias + 1)) / p_mes.dias
        )
    return salida


def _celda(resumen, metrica: Metrica) -> str:
    """'promedio ± semiamplitud del IC 95 %' con la unidad de la métrica."""
    return (
        f"{metrica.valor_mostrado(resumen.promedio):,.{metrica.decimales}f} "
        f"± {metrica.valor_mostrado(resumen.semiamplitud):,.{metrica.decimales}f}"
    )


def pestania_estaciones(p: ParametrosSimulacion) -> None:
    st.subheader("Estaciones del año: verano · otoño · invierno · primavera")
    if not p.estacion_real:
        st.info("Las estaciones del año son del caso real. Elegí la **estación real** en la "
                "barra lateral.", icon="🍂")
        return
    st.markdown(
        "Cuatro corridas del **mes real completo** (enero, abril, julio y octubre) con su "
        "calendario: días del mes, fines de semana y, en invierno, los episodios de corte de "
        "GNC y los cortes de ruta de jun–ago. Con la estacionalidad **neutra** (la que "
        "tiene el modelo hasta conseguir la serie mensual de la Secretaría de Energía, C10) "
        "todos los meses venden los mismos litros: las diferencias vienen sólo del calendario, "
        "del GNC y de la ruta, y eso es lo correcto."
    )

    c1, c2, c3 = st.columns([2, 1, 2])
    nombre_preset = c1.selectbox(
        "Estacionalidad de la demanda", list(PRESETS_ESTACIONALIDAD), key="est_preset",
        help="Neutra: todos los meses pesan igual (DEM-06, supuesto). Leve y proxy turístico "
             "son alternativas del Registro; ninguna tiene serie real todavía.",
    )
    replicas = c2.slider("Réplicas por estación", 1, 6, 4, 1, key="est_rep")
    c3.caption(f"Tiempo estimado: ≈ {4 * replicas * SEGUNDOS_POR_REPLICA:.0f} s "
               f"(4 estaciones × {replicas} réplicas). Queda en caché.")
    preset = PRESETS_ESTACIONALIDAD[nombre_preset]
    p_est = p if preset is None else replace(p, estacionalidad=preset)

    st.plotly_chart(
        graficos_escenarios.grafico_litros_por_mes(
            _litros_por_dia_de_cada_mes(p_est), MESES, {m for _, _, m in ESTACIONES},
            "Litros por día esperados de cada mes (en amarillo, los 4 meses que se simulan)",
        ),
        key="g_litros_mes",
    )

    semilla = st.session_state.semilla_usada
    if st.button("🍂 Correr las 4 estaciones", type="primary", key="btn_estaciones"):
        with st.spinner(f"Simulando 4 estaciones × {replicas} réplicas…"):
            resultados = correr_estaciones_cacheado(p_est, replicas, semilla)
        st.session_state.estaciones = (p_est, resultados)
    guardado = st.session_state.get("estaciones")
    if not guardado:
        st.info("Apretá **Correr las 4 estaciones** para simular el año por estaciones.", icon="▶")
        return
    p_usado, resultados = guardado
    if p_usado != p_est:
        st.info("Cambiaste parámetros o la estacionalidad: lo que se ve es la última corrida.",
                icon="🔄")

    filas = []
    for r in resultados:
        fila = {"Estación": r.escenario.nombre, "Días": r.parametros.dias}
        for m in (POR_CLAVE["llegadas_dia"], POR_CLAVE["litros_vendidos_dia"],
                  POR_CLAVE["espera_pico"], POR_CLAVE["nivel_servicio"],
                  POR_CLAVE["tasa_abandono"], POR_CLAVE["porcentaje_dias_quiebre"],
                  POR_CLAVE["gnc_afectados_dia"], POR_CLAVE["migrados_gnc_dia"],
                  POR_CLAVE["viajes_demorados_pct"], POR_CLAVE["plazo_entrega"]):
            unidad = m.unidad_mostrada
            fila[f"{m.etiqueta} ({unidad})" if unidad else m.etiqueta] = _celda(r.resumen[m.clave], m)
        filas.append(fila)
    st.markdown("##### Resultados por estación (promedio ± IC 95 % de las réplicas)")
    st.dataframe(pd.DataFrame(filas), hide_index=True)

    g1, g2 = st.columns(2)
    g1.plotly_chart(
        graficos_escenarios.grafico_barras_ic(
            resultados, "espera_pico", "Espera en la hora pico, por estación", "min", 2),
        key="g_est_espera",
    )
    g2.plotly_chart(
        graficos_escenarios.grafico_barras_ic(
            resultados, "nivel_servicio", "Nivel de servicio (litros pedidos que se vendieron)",
            "%", 1, escala=100.0),
        key="g_est_servicio",
    )
    st.plotly_chart(graficos_escenarios.grafico_perdidos_por_motivo(resultados),
                    key="g_est_perdidos")

    esperas = {r.escenario.nombre: r.prom("espera_pico") for r in resultados}
    mayor, menor = max(esperas, key=esperas.get), min(esperas, key=esperas.get)
    migrados = {r.escenario.nombre: r.prom("migrados_gnc_dia") for r in resultados}
    st.caption(
        f"Lectura: la espera en la hora pico va de {esperas[menor]:.2f} min ({menor}) a "
        f"{esperas[mayor]:.2f} min ({mayor}); los clientes de GNC que pasan a Súper por el "
        f"corte son {max(migrados.values()):.2f} por día en el peor mes "
        f"({max(migrados, key=migrados.get)}) y {min(migrados.values()):.2f} en el mejor. "
        "Si dos barras se parecen, mirá las barras de error: el IC 95 % de las réplicas "
        "dice cuánto de la diferencia puede ser azar."
    )
    if p_usado.gnc is not None and not p_usado.gnc.episodios_en_horizonte:
        st.caption(
            "Los episodios de GNC se sortean entre el 1/jun y el 31/ago, así que cada réplica "
            "de julio puede o no tener uno. Para ver siempre el corte en invierno, tildá "
            "*Forzar que los episodios caigan dentro del horizonte* (GNC y cortes de invierno)."
        )


# =============================================================================
# Pestaña: comparar escenarios S0–S12 (Fase 7, §7.7)
# =============================================================================
def tabla_catalogo(p_mes: ParametrosSimulacion) -> pd.DataFrame:
    """ID, nombre, qué cambia y qué pregunta contesta cada escenario del catálogo."""
    return pd.DataFrame(
        [
            {"ID": e.id, "Escenario": e.nombre, "Qué cambia": e.descripcion,
             "Pregunta": e.pregunta}
            for e in catalogo(p_mes)
        ]
    )


def tabla_comparacion_catalogo(resultados: list[ResultadoEscenario]) -> pd.DataFrame:
    """Promedio ± IC de cada indicador y la diferencia pareada de la espera pico contra S0."""
    base = resultados[0]
    filas = []
    for r in resultados:
        fila = {"Escenario": r.escenario.nombre}
        for m in COMPARACION_CATALOGO:
            unidad = m.unidad_mostrada
            fila[f"{m.etiqueta} ({unidad})" if unidad else m.etiqueta] = _celda(r.resumen[m.clave], m)
        if r is base:
            fila["Δ espera pico vs S0 (min)"] = "—"
        else:
            d = diferencia_pareada(base, r, "espera_pico")
            fila["Δ espera pico vs S0 (min)"] = (
                f"{d.promedio:+.2f} ± {d.semiamplitud:.2f}" + (" *" if es_significativa(d) else "")
            )
        filas.append(fila)
    return pd.DataFrame(filas)


def pestania_comparar(p: ParametrosSimulacion) -> None:
    st.subheader("Comparar escenarios S0–S12")
    st.markdown(
        "Cada escenario cambia **una cosa** de la estación y se corre en el mismo mes con los "
        "**mismos números aleatorios**: la réplica *i* de todos usa la misma semilla, así que "
        "llegan los mismos autos y el camión sortea los mismos plazos. Por eso se puede restar "
        "réplica a réplica: la **diferencia pareada** tiene un intervalo de confianza mucho "
        "más angosto que comparar dos promedios por separado."
    )
    c1, c2 = st.columns([1, 1])
    mes = c1.selectbox(
        "Mes de la comparación", list(range(1, 13)), index=6, key="cmp_mes",
        format_func=lambda m: MESES[m - 1].capitalize(),
        help="Julio por defecto: es donde tienen sentido el corte de GNC (S3) y los cortes de "
             "ruta (S4). S0 y todos los demás se corren en el mismo mes.",
    )
    replicas = c2.slider("Réplicas por escenario", 2, 8, 4, 1, key="cmp_rep")
    p_mes = para_mes(p, mes)
    lista = catalogo(p_mes)

    with st.expander("El catálogo: qué cambia cada escenario y qué pregunta contesta"):
        st.dataframe(tabla_catalogo(p_mes), hide_index=True)
        st.caption(
            "S1 (día típico por estación) se ve simulando cada estación desde el menú. S6 compara "
            "**S2 +1** (un playero más en el pico) contra **S6** (más stock): el costo en "
            "$/mes de cada opción llega con la economía real (Fase 8)."
        )
    elegidos = st.multiselect(
        "Escenarios a correr (S0 siempre se corre: es la referencia)",
        [e.nombre for e in lista[1:]], default=[e.nombre for e in lista[1:]], key="cmp_sel",
    )
    n_corridas = 1 + len(elegidos)
    st.caption(f"Tiempo estimado: ≈ {n_corridas * replicas * SEGUNDOS_POR_REPLICA:.0f} s "
               f"({n_corridas} escenarios × {replicas} réplicas). Queda en caché.")

    semilla = st.session_state.semilla_usada
    if st.button("🧪 Correr los escenarios", type="primary", key="btn_comparar"):
        with st.spinner(f"Simulando {n_corridas} escenarios × {replicas} réplicas…"):
            resultados = correr_catalogo_cacheado(p, mes, replicas, semilla, tuple(elegidos))
        st.session_state.comparacion = (p, mes, resultados)
    guardado = st.session_state.get("comparacion")
    if not guardado:
        st.info("Elegí el mes y apretá **Correr los escenarios**.", icon="▶")
        return
    p_usado, mes_usado, resultados = guardado
    if p_usado != p:
        st.info("Cambiaste parámetros: lo que se ve es la última corrida.", icon="🔄")

    st.markdown(f"##### Resultados en {MESES[mes_usado - 1]} (promedio ± IC 95 % de las réplicas)")
    st.dataframe(tabla_comparacion_catalogo(resultados), hide_index=True,
                 height=38 * (len(resultados) + 1))
    st.caption(
        "* = la diferencia contra S0 es significativa: su IC 95 % (de las diferencias réplica "
        "a réplica) no contiene el 0. Sin asterisco, el efecto no se distingue del azar con "
        "estas réplicas."
    )

    base = resultados[0]
    opciones = {m.etiqueta: m for m in INDICADORES_DIFERENCIA}
    elegida = st.selectbox("Indicador a comparar contra S0", list(opciones), index=1,
                           key="cmp_indicador")
    m = opciones[elegida]
    st.plotly_chart(
        graficos_escenarios.grafico_diferencias(
            base, resultados, m.clave, m.etiqueta, m.unidad_mostrada, m.mejor_bajo,
            max(m.decimales, 1), escala=100.0 if m.porcentaje else 1.0),
        key="g_cmp_dif",
    )
    st.plotly_chart(
        graficos_escenarios.grafico_perdidos_por_motivo(resultados, horizontal=True),
        key="g_cmp_perdidos",
    )
    st.caption(
        "Cómo leerlo: verde = mejora significativa, rojo = empeora significativamente, gris = "
        "no se distingue del azar. **Ojo con el stock:** los clientes que abandonan la cola "
        "dejan de consumir, así que con menos playeros (S2 −1, S9) el tanque se vacía **menos** "
        "y hay menos 'sin combustible'. No es una mejora: es la misma pérdida, que cambió de "
        "motivo. Por eso conviene mirar la **tasa de abandono total** y las pérdidas apiladas. Y en S10 "
        "el abandono baja porque la demanda nocturna **nunca llega** (no cuenta como abandono): "
        "mirá los clientes por día y los litros vendidos."
    )


# =============================================================================
# Pestaña: la estación (caso real)
# =============================================================================
def pestania_estacion() -> None:
    """Ficha de la estación (los valores; la fuente y el tipo de cada dato están en Datos y fuentes)."""
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
            st.markdown(f"**{d.nombre}**<br/><small>{d.valor}</small>", unsafe_allow_html=True)

    st.markdown("#### El playón")
    st.markdown(
        "6 surtidores de doble cara = **12 caras en 3 zonas**: S1–S2 nafta (Súper y V-Power) · "
        "S3 diésel (G2 y G3) · S4–S6 GNC. Servicio atendido por playeros, playa 24 h. "
        "La pestaña **Animación** lo muestra funcionando."
    )

    st.info(AVISO_FUENTES, icon="ℹ️")
    st.caption(
        "Cuando dos fuentes no coincidían se eligió una con un criterio único (oficial antes que secundaria, "
        "más reciente, más local y, ante empate, la más conservadora). El valor elegido, su fuente y el "
        "criterio de cada caso están en la pestaña **Datos y fuentes**."
    )


# =============================================================================
# Pestaña: datos y fuentes (el Registro completo)
# =============================================================================
def pestania_datos_fuentes() -> None:
    """El Registro de datos (valor elegido, fuente, tipo y confianza) y cómo se resolvió cada contradicción."""
    st.subheader("Registro de datos")
    st.caption(
        "Todo número del modelo tiene su `Dato` con fuente, nivel de evidencia, tipo y confianza. "
        + AVISO_FUENTES
    )

    tabla = tabla_registro(con_alternativas=False)
    filtro_tipo = st.multiselect(
        "Filtrar por tipo", ["dato", "estimacion", "observacion", "supuesto", "heredado"],
    )
    vista = tabla if not filtro_tipo else tabla[tabla["Tipo"].isin(filtro_tipo)]
    st.dataframe(vista, hide_index=True, height=420)

    st.download_button(
        "⬇️ Descargar el Registro completo (CSV)",
        data=csv_registro(),
        file_name="registro_datos_shell_san_rafael.csv",
        mime="text/csv",
        help="Incluye todas las filas, los valores que se descartaron (ejes de sensibilidad) y las decisiones.",
    )

    st.markdown("#### Cuando las fuentes no coincidían: qué se eligió y por qué")
    st.caption(
        "Criterio único, en orden: que la fuente mida lo mismo; oficial o primaria (y vigente) antes que "
        "secundaria; más reciente; más específica de San Rafael o Mendoza; ante empate, la más conservadora. "
        "Detalle en research_notes/…/07_decisiones_fuentes.md."
    )
    st.dataframe(
        pd.DataFrame(
            [{"ID": c.id, "Tema": c.tema, "Valor elegido": c.adoptado, "Por qué": c.criterio}
             for c in CONTRADICCIONES]
        ),
        hide_index=True,
        height=36 * (len(CONTRADICCIONES) + 1) + 3,
    )


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
        # Un único "escenario Base" real; el catálogo S0–S12 está en la pestaña Escenarios.
        resultados = [correr_estacion_real_cacheado(p, replicas, semilla)]
    else:
        resultados = correr_escenarios_cacheado(p, replicas, semilla)
    traza = correr_traza_cacheada(p, semilla)

    st.session_state.resultados = resultados
    st.session_state.traza = traza
    # Identifica la corrida: el aviso del tablero y el seguimiento del camión sólo se hablan si son de la misma.
    st.session_state.corrida_n = st.session_state.get("corrida_n", 0) + 1
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


# =============================================================================
# Flujo de la app (rediseño v3): inicio → simulación → resultados → editar
# =============================================================================
TIPOS_DE_PERIODO = ("Por días", "Por meses", "Por estaciones", "Año completo")


def menu_de_periodo() -> Periodo | None:
    """El menú inicial: qué período se simula. Devuelve el `Periodo` elegido (o None si es inválido)."""
    tipo = st.radio("Período a simular", TIPOS_DE_PERIODO, horizontal=True, key="menu_tipo")
    periodo: Periodo | None = None

    if tipo == "Por días":
        st.caption("Elegí cuántos días y desde qué fecha: el período termina solo.")
        c1, c2, c3 = st.columns(3)
        dias = c1.number_input("Cantidad de días", 1, 365, 30, 1, key="menu_dias")
        mes = c2.selectbox("Empezar en", list(range(1, 13)), index=0, key="menu_mes_ini",
                           format_func=lambda m: MESES_PERIODO[m - 1].capitalize())
        dia = c3.number_input("Día de inicio", 1, 31, 1, 1, key="menu_dia_ini")
        periodo = por_dias(int(dias), int(mes), int(dia))
    elif tipo == "Por meses":
        st.caption("Elegí el primer y el último mes: se simulan enteros, uno detrás del otro.")
        c1, c2 = st.columns(2)
        desde = c1.selectbox("Desde", list(range(1, 13)), index=0, key="menu_desde",
                             format_func=lambda m: MESES_PERIODO[m - 1].capitalize())
        hasta = c2.selectbox("Hasta", list(range(1, 13)), index=0, key="menu_hasta",
                             format_func=lambda m: MESES_PERIODO[m - 1].capitalize())
        if hasta < desde:
            st.error("El mes final tiene que ser igual o posterior al inicial.", icon="📅")
        else:
            periodo = por_meses(int(desde), int(hasta))
    elif tipo == "Por estaciones":
        st.caption("Una estación entera; el verano de diciembre a febrero cruza el año.")
        nombre = st.radio("Estación", list(TEMPORADAS), horizontal=True, key="menu_estacion",
                          format_func=lambda n: f"{n} · {por_temporada(n).texto}")
        periodo = por_temporada(nombre)
    else:
        st.caption("Del 1 de enero al 31 de diciembre: pasan las cuatro estaciones.")
        periodo = anio_completo()
    return periodo


def simular_periodo(periodo: Periodo, edicion: Edicion | None = None) -> None:
    """Corre el período con los datos reales (sin azar) o editado (con azar) y pasa a los resultados."""
    base = con_periodo(ParametrosSimulacion().datos_reales(), periodo)
    base, eco = aplicar_ajustes(base, ParametrosEconomicos(), ajustes_actuales())
    semilla = 1
    if edicion is not None:
        base, eco = aplicar_edicion(base, eco, edicion)
        semilla = edicion.semilla
    # La animación de todos los días llega en la etapa 3: por ahora se graba el día elegido.
    base = replace(base, animar_todo=False)
    etiqueta = "datos reales" if edicion is None else "edición con azar"
    with st.spinner(f"Simulando {periodo.dias} días ({etiqueta})…"):
        correr_todo(base, eco, 1, semilla)
    for clave in ("estaciones", "comparacion", "sensibilidad"):
        st.session_state.pop(clave, None)
    st.session_state.periodo = periodo
    st.session_state.edicion = edicion
    st.session_state.modo = "real" if edicion is None else "editada"
    st.session_state.vista = "resultados"


def ajustes_actuales() -> Ajustes:
    """Los ajustes guardados al simular (los widgets se borran al salir del menú; esto no)."""
    return st.session_state.get("ajustes") or Ajustes()


NOMBRES_PRODUCTO = {"super": "Súper", "vpower": "V-Power", "diesel_g2": "Diésel G2", "diesel_g3": "Diésel G3",
                    "gnc": "GNC"}


def menu_de_ajustes(periodo: Periodo | None) -> Ajustes:
    """Los desplegables del menú inicial: Economía y GNC. Devuelve los `Ajustes` elegidos."""
    previo = ajustes_actuales()
    margenes_previos = dict(previo.margenes)

    with st.expander("💰 Economía: márgenes, flete, almacenamiento y sueldos"):
        st.caption(
            "Los márgenes, el flete y el almacenamiento son **heredados sin fuente** (del proyecto hipotético): "
            "muestran cómo se calcula, no son cifras del negocio. Los sueldos son la escala de FECRA de enero-2026 "
            "con adicionales, **no confirmados** para esta estación. Cambiar esto no cambia la simulación: sólo la plata."
        )
        rango_l = por_id("ECO-01")
        rango_m3 = por_id("ECO-03")
        columnas = st.columns(5)
        margenes = []
        for col, (pr, defecto) in zip(columnas, MARGENES_REGISTRO):
            d = rango_m3 if pr == "gnc" else rango_l
            unidad = "m³" if pr == "gnc" else "L"
            margenes.append((pr, float(col.number_input(
                f"Margen {NOMBRES_PRODUCTO[pr]} ($/{unidad})", 0, 5000, int(margenes_previos.get(pr, defecto)), 10,
                key=f"aj_margen_{pr}",
                help=f"Registro: ${defecto:,.0f}/{unidad} ({d.id}, heredado sin fuente). Rango de prueba del tornado: "
                     f"${d.bajo:,.0f}–{d.alto:,.0f} (no es un dato).".replace(",", "."),
            ))))
        flete = por_id("ECO-06")
        c1, c2, c3, c4 = st.columns(4)
        flete_fijo = float(c1.number_input(
            "Flete por viaje ($)", 0, 5_000_000, int(previo.flete_fijo), 10_000, key="aj_flete_fijo",
            help=f"Registro: ${flete.valor[0]:,.0f} por viaje (ECO-06, heredado sin fuente; implausible para ≈ 1.000 km). "
                 f"Rango de prueba: ${flete.bajo:,.0f}–{flete.alto:,.0f}.".replace(",", "."),
        ))
        flete_km = float(c2.number_input(
            "Flete por km ($/km)", 0, 20_000, int(previo.flete_km), 50, key="aj_flete_km",
            help="Registro: $0 (sin dato). Se multiplica por los km de ida y vuelta desde el origen.",
        ))
        alm = por_id("ECO-07")
        almacenamiento = float(c3.number_input(
            "Almacenamiento ($ por litro y por mes)", 0, 500, int(previo.almacenamiento), 1, key="aj_almacen",
            help=f"Registro: ${alm.valor:,.0f} (ECO-07, heredado sin fuente). Rango de prueba: "
                 f"${alm.bajo:,.1f}–{alm.alto:,.1f}.".replace(".", ","),
        ))
        sueldos = por_id("ECO-04")
        sueldo = float(c4.number_input(
            "Sueldo de un playero ($/mes)", 0, 10_000_000, int(previo.sueldo_playero), 10_000, key="aj_sueldo",
            help=f"Registro: ${sueldos.valor[0]:,.0f} con adicionales (FECRA, enero-2026; no confirmado para esta "
                 f"estación). El básico sin adicionales es ${sueldos.alternativas[0][1][0]:,.0f}.".replace(",", "."),
        ))

    with st.expander("🔥 GNC: cortes de invierno y clientes"):
        opciones = {
            "habituales": "Sólo los cortes habituales (2 cortes de 6 días entre junio y agosto)",
            "todo_invierno": "Pueden ocurrir más cortes en todo el invierno (y un invierno más frío los alarga)",
        }
        cortes = st.radio(
            "Cortes de GNC", list(opciones), index=list(opciones).index(previo.cortes_gnc),
            format_func=opciones.get, key="aj_cortes_gnc",
        )
        if cortes == "todo_invierno":
            st.caption(
                f"Se suman {valor('GNC-08')} cortes en los huecos más largos del invierno y, con probabilidad "
                f"{valor('GNC-09'):.0%}, cada corte se alarga {valor('GNC-10')} días por un invierno más frío "
                f"(GNC-08/09/10, supuestos del grupo). Sin azar el alargue es una cuota exacta: siempre los mismos cortes."
            )
        pct = st.slider(
            "Clientes que entran por GNC", 0, 30, int(round(100 * previo.pct_gnc)), 1, key="aj_pct_gnc",
            format="%d %%",
            help="DEM-05: 3 % de las llegadas (estimación). El Registro trae 11 % (parque GNC de ENARGAS) y 20 % "
                 "como alternativas de sensibilidad.",
        ) / 100.0

    with st.expander("📅 Calendario de demanda: verano, vacaciones de invierno y resto del invierno"):
        formas = {
            "calendario": "Calendario de temporadas (supuesto del grupo, DEM-14)",
            "real": "Índices de la serie real de Shell Mendoza (pestaña 📈 Pronóstico, PRO-01)",
            "neutra": "Neutra: todos los meses iguales",
        }
        actual = "real" if previo.indices_reales else ("calendario" if previo.calendario else "neutra")
        forma = st.radio(
            "Cómo cambia la demanda a lo largo del año", list(formas), index=list(formas).index(actual),
            format_func=formas.get, key="aj_forma_demanda",
            help="Por defecto, el calendario de temporadas. La serie real (Secretaría de Energía) dice que en Shell "
                 "Mendoza el verano casi no cambia; marzo y diciembre son los meses fuertes y junio el más flojo.",
        )
        calendario = forma == "calendario"
        indices_reales = forma == "real"
        st.caption(
            "No es azar: cada fecha tiene su factor. Verano (dic–feb) sube por el turismo; las **vacaciones de "
            "invierno de Mendoza** (6–17 de julio de 2026, calendario de la DGE) suben; el resto del invierno baja un "
            "poco porque la gente sale menos; otoño y primavera quedan igual. Son **supuestos** moderados (DEM-14: la "
            "mitad del desvío del proxy turístico, nota 08)."
        )
        previos = dict(previo.factores)
        etiquetas = {"verano": "Verano (dic–feb)", "vacaciones_invierno": "Vacaciones de invierno",
                     "invierno": "Resto del invierno"}
        columnas = st.columns(3)
        factores = []
        for col, (clave, defecto) in zip(columnas, valor("DEM-14")):
            cambio = col.number_input(
                f"{etiquetas[clave]} (% de cambio)", -50, 100, int(round(100 * (previos.get(clave, defecto) - 1))), 1,
                key=f"aj_cal_{clave}", disabled=not calendario,
                help=f"Registro (DEM-14, supuesto): {100 * (defecto - 1):+.0f} %.",
            )
            factores.append((clave, round(1 + cambio / 100.0, 4)))

    with st.expander("🚚 Abastecimiento: de dónde sale el camión"):
        eventos = st.toggle(
            "Eventos aleatorios de abastecimiento", value=previo.eventos_abastecimiento, key="aj_eventos",
            help="Apagado: el camión sale siempre de Dock Sud por la ruta óptima.",
        )
        st.caption(
            f"Prendido, un origen puede no cumplir un pedido ({valor('RED-20'):.0%} de las veces, RED-20, supuesto) y el "
            f"pedido pasa al siguiente: **Arroyo Seco** (terminal de Raízen/Shell) y después **Luján de Cuyo** (refinería "
            f"de YPF), con su propia ruta y {valor('RED-21'):.0f} h de demora por volver a gestionarlo. Sin azar es una "
            f"cuota: 1 de cada 20 pedidos de cada producto, así que en un mes casi no aparece. Sólo los líquidos (el GNC "
            f"sale de la red de gas). La Paz y Pareditas no se incluyen: son cruces de ruta, no plantas (nota 09)."
        )
        opciones_origen = ("DOCK", *valor("RED-19"))
        no_disponibles = st.multiselect(
            "Marcar a mano como no disponible", opciones_origen,
            default=[o for o in previo.origenes_no_disponibles if o in opciones_origen],
            format_func=lambda o: NOMBRE_NODO[o], key="aj_no_disponibles",
            help="Para forzar el caso: por ejemplo, Dock Sud no disponible ⇒ todos los pedidos salen de Arroyo Seco.",
        )
        st.markdown("**Plan de abastecimiento (flujo de costo mínimo, pestaña 🗺️ Red y rutas)**")
        topes_previos = dict(previo.topes_origen)
        t1, t2 = st.columns(2)
        tope_arroyo = t1.number_input(
            "Arroyo Seco puede despachar (% de los camiones)", 0, 100, int(round(100 * topes_previos.get("ARROYO", 0))), 5,
            key="aj_tope_arroyo", help="FLU-02, supuesto: hoy 0 % (todo sale de Dock Sud).",
        ) / 100
        tope_lujan = t2.number_input(
            "Luján de Cuyo puede despachar (% de los camiones)", 0, 100, int(round(100 * topes_previos.get("LUJAN", 0))), 5,
            key="aj_tope_lujan", help="FLU-02, supuesto: hoy 0 % (YPF, sólo emergencia).",
        ) / 100
        despachar = st.toggle(
            "Despachar según el plan", value=previo.despachar_plan, key="aj_despachar_plan",
            help="Prendido: cada camión sale del origen que indica el plan de costo mínimo (cuotas exactas). Con los "
                 "topes de hoy el plan es todo desde Dock Sud y la corrida no cambia.",
        )
        politica_pron = st.toggle(
            "Punto de pedido por pronóstico (stock de seguridad)", value=previo.politica_pronostico,
            key="aj_pol_pronostico",
            help="s = lo que se vende mientras viaja el camión + 1,96 × el error del pronóstico de la serie real "
                 "(pestaña 📈 Pronóstico). Apagado: la política cargada (INV-07, s = 1,5 días de venta).",
        )
        if len(no_disponibles) == len(opciones_origen):
            st.warning("Si ninguno está disponible, el pedido sale igual de Dock Sud con la demora de redirección.",
                       icon="⚠️")

    elegidos, semilla_ev, frecuencia_ev = menu_de_eventos(previo, periodo)

    return Ajustes(
        margenes=tuple(margenes), flete_fijo=flete_fijo, flete_km=flete_km, almacenamiento=almacenamiento,
        sueldo_playero=sueldo, cortes_gnc=cortes, pct_gnc=pct, calendario=bool(calendario),
        indices_reales=bool(indices_reales), politica_pronostico=bool(politica_pron),
        topes_origen=(("DOCK", 1.0), ("ARROYO", float(tope_arroyo)), ("LUJAN", float(tope_lujan))),
        despachar_plan=bool(despachar),
        factores=tuple(factores), eventos_abastecimiento=bool(eventos),
        origenes_no_disponibles=tuple(no_disponibles),
        eventos=elegidos, semilla_eventos=semilla_ev, frecuencia_eventos=frecuencia_ev,
    )


#: Multiplicadores de la frecuencia de los eventos que ofrece el menú.
FRECUENCIAS_EVENTOS = {
    1.0: "La del Registro",
    2.0: "El doble",
    5.0: "× 5 (para verlos en un período corto)",
    0.5: "La mitad",
}


def _marcar_eventos(prender: bool) -> None:
    """Botones 'Prender todos' / 'Apagar todos' (se ejecuta antes de dibujar las casillas)."""
    for t in CATALOGO_EVENTOS:
        st.session_state[f"ev_{t.id}"] = prender


def menu_de_eventos(previo: Ajustes, periodo: Periodo | None) -> tuple[tuple[str, ...], int, float]:
    """El desplegable de los eventos aleatorios (parte 4): casillas por grupo, frecuencia y semilla."""
    with st.expander("⚡ Eventos aleatorios: cosas que le pueden pasar a la estación"):
        st.caption(
            "Apagados por defecto. Los que prendas **se sortean con su propia semilla** (siempre los mismos con la "
            "misma semilla); el resto de la simulación sigue con los datos reales, sin azar. Frecuencias y "
            "duraciones: **supuestos del grupo** (EVT-01…14), editables en el Registro. Pasá el mouse por cada uno "
            "para ver qué hace y cada cuánto pasa."
        )
        b1, b2, _ = st.columns([1, 1, 4])
        b1.button("Prender todos", key="ev_todos", on_click=_marcar_eventos, args=(True,))
        b2.button("Apagar todos", key="ev_ninguno", on_click=_marcar_eventos, args=(False,))
        grupos = list(dict.fromkeys(t.grupo for t in CATALOGO_EVENTOS))
        elegidos: list[str] = []
        for col, grupo in zip(st.columns(len(grupos)), grupos):
            col.markdown(f"**{grupo}**")
            for t in CATALOGO_EVENTOS:
                if t.grupo != grupo:
                    continue
                clave = f"ev_{t.id}"
                if clave not in st.session_state:
                    st.session_state[clave] = t.id in previo.eventos
                if col.checkbox(t.nombre, key=clave,
                                help=f"{t.efecto[:1].upper()}{t.efecto[1:]}. Frecuencia: {texto_frecuencia(t.id)} "
                                     f"({t.id}, supuesto del grupo)."):
                    elegidos.append(t.id)
        c1, c2 = st.columns(2)
        opciones = list(FRECUENCIAS_EVENTOS)
        frecuencia = c1.selectbox(
            "Frecuencia", opciones, index=opciones.index(previo.frecuencia_eventos)
            if previo.frecuencia_eventos in opciones else 0, format_func=FRECUENCIAS_EVENTOS.get, key="aj_ev_frecuencia",
            help="Multiplica la probabilidad por día de todos los eventos prendidos.",
        )
        semilla = int(c2.number_input(
            "Semilla del sorteo de los eventos", 1, 9999, previo.semilla_eventos, 1, key="aj_ev_semilla",
            help="Con la misma semilla salen siempre los mismos eventos; otra semilla, otro calendario.",
        ))
        if elegidos and periodo is not None:
            prueba = con_periodo(ParametrosSimulacion().datos_reales(), periodo)
            prueba = replace(prueba, eventos=ParametrosEventos(activos=tuple(elegidos), semilla=semilla,
                                                               frecuencia=float(frecuencia)))
            cal = calendario_eventos(prueba)
            st.caption(
                f"Con esta semilla, en {periodo.titulo.lower()} salen **{len(cal)} eventos** del calendario"
                + (" (la rotura del camión se sortea aparte, en cada viaje)" if "EVT-11" in elegidos else "") + "."
            )
    return tuple(elegidos), semilla, float(frecuencia)


def menu_escenario_unico() -> EscenarioUnico:
    """Las cuatro cosas que se eligen para el escenario único."""
    previo: EscenarioUnico = st.session_state.get("eu_previo") or EscenarioUnico()
    c1, c2, c3, c4 = st.columns(4)
    playeros = int(c1.number_input("Playeros en la franja", 1, 6, previo.playeros, 1, key="eu_playeros",
                                   help="Hoy (PER-01): 1 de noche, 2 de mañana y 2 de tarde."))
    franja = c2.selectbox("Franja horaria", list(FRANJAS), index=list(FRANJAS).index(previo.franja), key="eu_franja")
    temporada = c3.selectbox("Temporada", list(SEMANAS), index=list(SEMANAS).index(previo.temporada), key="eu_temporada",
                             help="Se simula una semana representativa (CAL-09), de lunes a domingo.")
    clientela = c4.selectbox(
        "Clientela", CLIENTELAS, index=CLIENTELAS.index(previo.clientela), key="eu_clientela",
        format_func=lambda n: {"poca": "Poca (150.000 L/mes)", "media": "Media (270.000 L/mes)",
                               "alta": "Alta (400.000 L/mes)", "máxima": "Máxima (alta y el doble en el pico)"}[n],
    )
    return EscenarioUnico(playeros=playeros, franja=franja, temporada=temporada, clientela=clientela)


def simular_escenario_unico(eu: EscenarioUnico) -> None:
    """Corre la semana del escenario (sin azar) y pasa a su pantalla."""
    periodo = eu.periodo()
    base, eco = aplicar_ajustes(
        con_periodo(ParametrosSimulacion().datos_reales(), periodo), ParametrosEconomicos(), ajustes_actuales()
    )
    p = replace(eu.escenario(base).aplicar(base), animar_todo=False)
    with st.spinner(f"Simulando: {eu.titulo}…"):
        resultado, traza = correr_replica(p, semilla=1, con_traza=True)
    st.session_state.eu_previo = eu
    st.session_state.escenario_unico = (eu, periodo, p, eco, resultado, traza)
    st.session_state.vista = "escenario"


def pantalla_escenario_unico() -> None:
    """Sólo los datos del escenario elegido, en su franja, y una conclusión armada con esos resultados."""
    eu, periodo, p, eco, r, traza = st.session_state.escenario_unico
    c1, c2 = st.columns([5, 1])
    c1.title("🎯 Escenario único")
    if c2.button("← Volver al menú", key="btn_volver_eu"):
        st.session_state.vista = "inicio"
        st.rerun()
    st.info(f"**{eu.titulo}** · {periodo.texto}. Datos del Registro, sin azar; se muestra sólo la franja elegida.",
            icon="🎯")

    horas = eu.horas()
    dias = p.dias
    llegadas = sum(traza.llegadas_dia_hora[d][h] for d in range(dias) for h in horas)
    suma = sum(traza.espera_dia_hora[d][h][0] for d in range(dias) for h in horas)
    cant = sum(traza.espera_dia_hora[d][h][1] for d in range(dias) for h in horas)
    espera = suma / cant if cant else 0.0
    perdidos = sum(traza.perdidos_por_hora[h] for h in horas)
    por_hora = llegadas / dias / len(horas)
    rho = por_hora * p.media_servicio_playero() / 60.0 / eu.playeros
    vistas_ent, vistas_dec = vistas.ent, vistas.dec
    filas = st.columns(5)
    for col, (titulo, valor_, nota) in zip(filas, (
        ("Clientes por hora", vistas_dec(por_hora), "promedio de la franja, todos los productos"),
        ("Playeros", vistas_ent(eu.playeros), "en la franja"),
        ("ρ (ocupación teórica)", vistas_dec(rho, 2), "llegadas × servicio ÷ playeros; ≥ 1 no alcanza"),
        ("Espera promedio", f"{vistas_dec(espera)} min", "de los atendidos en la franja"),
        ("Clientes perdidos", vistas_ent(perdidos / dias), f"por día en la franja ({vistas_ent(perdidos)} en la semana)"),
    )):
        col.metric(titulo, valor_, border=True)
        col.caption(nota)

    st.markdown("##### Hora por hora (promedio de los 7 días)")
    st.dataframe(pd.DataFrame({
        "Hora": [f"{h:02d}–{h + 1:02d}" for h in horas],
        "Clientes que llegaron": [vistas_dec(sum(traza.llegadas_dia_hora[d][h] for d in range(dias)) / dias) for h in horas],
        "Espera promedio (min)": [
            vistas_dec(sum(traza.espera_dia_hora[d][h][0] for d in range(dias))
                       / max(1, sum(traza.espera_dia_hora[d][h][1] for d in range(dias))))
            for h in horas
        ],
        "Se fueron sin cargar": [vistas_dec(traza.perdidos_por_hora[h] / dias) for h in horas],
    }), hide_index=True)

    st.markdown("##### Conclusión de este escenario")
    if rho >= 1.0 or perdidos > 0.05 * max(llegadas, 1):
        st.error(
            f"Con {eu.playeros} playero{'s' if eu.playeros != 1 else ''} la franja **no alcanza**: ρ = {vistas_dec(rho, 2)} "
            f"y se va sin cargar el {vistas.pct(perdidos, llegadas)} de los que llegan en esas horas.", icon="🚗",
        )
    elif rho >= 0.85 or espera > 3.0:
        st.warning(
            f"La franja está **al límite**: ρ = {vistas_dec(rho, 2)} y la espera promedio es {vistas_dec(espera)} min; "
            f"cualquier aumento de clientes la satura.", icon="⚠️",
        )
    else:
        st.success(
            f"La franja **alcanza con margen**: ρ = {vistas_dec(rho, 2)}, espera de {vistas_dec(espera)} min y "
            f"{vistas_ent(perdidos)} clientes perdidos en la semana.", icon="✅",
        )
    t = dict(r.totales)
    extras = []
    if t["perdidos_sin_combustible"]:
        extras.append(f"en la semana hubo {vistas_ent(t['perdidos_sin_combustible'])} clientes sin cargar por falta de stock "
                      f"(es de todo el día, no sólo de la franja)")
    if t["dias_con_corte_gnc"]:
        extras.append(f"hubo {vistas_ent(t['dias_con_corte_gnc'])} días con el GNC cortado")
    if extras:
        st.caption("Además, " + "; ".join(extras) + ".")
    st.caption(
        f"ρ = {vistas_dec(por_hora)} clientes por hora × {vistas_dec(p.media_servicio_playero())} min de playero por "
        f"cliente ÷ 60 ÷ {eu.playeros} playeros. Los minutos por cliente promedian nafta y diésel "
        f"({vistas_dec(p.media_servicio_liquidos())} min) con el GNC ({vistas_dec(p.carga_gnc.media)} min, "
        f"{vistas_dec(100 * p.pct_gnc, 0)} % de los clientes): a todos los carga un playero."
    )
    st.plotly_chart(graficos.grafico_perfil_horario(traza, dias), key="g_eu_perfil")
    st.divider()
    st.caption(PIE_NO_AFILIADO)


def pantalla_informe() -> None:
    """Caso de informe: la búsqueda de la mejor política, el catálogo S0–S12 y el tornado, fuera del flujo normal."""
    periodo = st.session_state.get("periodo_informe") or por_meses(7, 7)
    p, eco = aplicar_ajustes(
        con_periodo(ParametrosSimulacion().datos_reales(), periodo), ParametrosEconomicos(), ajustes_actuales()
    )
    p = replace(p, animar_todo=False)
    if "semilla_usada" not in st.session_state:
        st.session_state.semilla_usada = 1
    c1, c2 = st.columns([5, 1])
    c1.title("📑 Caso de informe")
    if c2.button("← Volver al menú", key="btn_volver_informe"):
        st.session_state.vista = "inicio"
        st.rerun()
    st.info(
        f"Período: **{periodo.titulo}** — {periodo.texto} (el elegido en el menú). La búsqueda de la mejor política usa "
        f"los datos reales (sin azar); el catálogo y el tornado usan **azar con réplicas**, porque comparan escenarios "
        f"con diferencias pareadas e intervalos de confianza.", icon="📑",
    )
    p_azar = replace(p, determinista=False)
    t1, t2, t3 = st.tabs(["🔎 Mejor política de reposición", "⚖️ Escenarios S0–S12 y decisión en $/mes",
                          "🌪️ Sensibilidad (tornado)"])
    with t1:
        seccion_mejor_politica(p, eco)
    with t2:
        pestania_comparar(p_azar)
        st.divider()
        seccion_decision(eco)
    with t3:
        pestania_sensibilidad(p_azar, eco)
    st.divider()
    st.caption(PIE_NO_AFILIADO)


def pantalla_inicio() -> None:
    st.title("⛽ Simulador de la Estación Shell — San Rafael")
    st.caption("Av. Balloffet 1810 esq. Los Sauces · San Rafael, Mendoza · Investigación Operativa")
    st.subheader("¿Qué querés simular?")
    st.markdown(
        "Se simula con los **datos reales del Registro**: no hay azar, así que siempre da el "
        "mismo resultado y se puede comprobar. Si querés cambiar algo (playeros, demanda, "
        "precios), después de simular aparece **Editar simulación**."
    )
    periodo = menu_de_periodo()
    if periodo is not None:
        st.success(f"**{periodo.titulo}** — {periodo.texto}", icon="📅")

    st.markdown("##### Ajustes (opcionales; arrancan con los valores del Registro)")
    ajustes = menu_de_ajustes(periodo)
    if periodo is not None and periodo.incluye_invierno:
        cortes = cortes_gnc_previstos(periodo, gnc_con_ajustes(ParametrosSimulacion().gnc, ajustes))
        if cortes:
            st.info(
                "Incluye invierno: se aplican los **cortes de GNC** (sin azar, fechas fijas): "
                + " · ".join(f"{texto_fecha(a)} al {texto_fecha(b)} ({(b - a).days + 1} días)" for a, b in cortes)
                + ".",
                icon="🔥",
            )
    elif periodo is not None:
        st.caption("No incluye invierno: no hay cortes de GNC en este período.")
    if st.button("▶ Simular con datos reales", type="primary", disabled=periodo is None):
        st.session_state.ajustes = ajustes
        simular_periodo(periodo)
        st.rerun()

    st.divider()
    st.markdown("#### O un escenario único")
    st.caption(
        "Una micro simulación de **una semana** que muestra sólo ese escenario: cuántos playeros hay en una franja, en "
        "qué temporada y con cuánta clientela. Usa los datos del Registro y los ajustes de arriba, sin azar."
    )
    eu = menu_escenario_unico()
    if st.button("🎯 Simular el escenario único", key="btn_escenario_unico"):
        st.session_state.ajustes = ajustes
        simular_escenario_unico(eu)
        st.rerun()

    st.divider()
    st.markdown("#### Caso de informe")
    st.caption(
        "El análisis completo para el informe, fuera del flujo normal (tarda más): la búsqueda de la mejor política de "
        "reposición, el catálogo de escenarios S0–S12 con su decisión en $/mes y el tornado de sensibilidad."
    )
    if st.button("📑 Abrir el caso de informe", key="btn_informe"):
        st.session_state.ajustes = ajustes
        st.session_state.periodo_informe = periodo
        st.session_state.vista = "informe"
        st.rerun()
    st.divider()
    st.caption(PIE_NO_AFILIADO)


def pantalla_editar() -> None:
    """Editar simulación: pocas opciones; la simulación editada usa azar (Monte Carlo)."""
    periodo: Periodo = st.session_state.periodo
    base = ParametrosSimulacion()
    previa: Edicion = st.session_state.get("edicion") or Edicion()
    st.title("✏️ Editar simulación")
    st.markdown(
        f"Período: **{periodo.titulo}** — {periodo.texto}. Lo que cambies acá **ya no son datos "
        f"reales**: la simulación usa azar (Monte Carlo) y aparece una pestaña que explica qué se "
        f"sorteó. La simulación principal no se toca."
    )

    st.markdown("##### Playeros por turno")
    p1, p2, p3 = st.columns(3)
    playeros = (
        int(p1.number_input("Noche 22–06", 1, 6, (previa.playeros or base.playeros_por_turno)[0], 1, key="ed_p1")),
        int(p2.number_input("Mañana 06–14", 1, 6, (previa.playeros or base.playeros_por_turno)[1], 1, key="ed_p2")),
        int(p3.number_input("Tarde 14–22", 1, 6, (previa.playeros or base.playeros_por_turno)[2], 1, key="ed_p3")),
    )

    st.markdown("##### Demanda de vehículos")
    nivel = st.radio(
        "Nivel de demanda", list(NIVELES_DEMANDA), horizontal=True,
        index=list(NIVELES_DEMANDA).index(previa.nivel_demanda), key="ed_nivel",
        format_func=lambda n: f"{n.capitalize()} · {litros_de_nivel(n):,.0f} L/mes".replace(",", "."),
        help="Poca y alta son los extremos del Registro (DEM-01); media es la que se usa con datos reales.",
    )
    doble = st.checkbox("Duplicar la demanda en la hora pico (07–10 y 16–18 h)", value=previa.doble_pico,
                        key="ed_doble", help="DEM-13: las otras horas conservan su cantidad de clientes.")

    st.markdown("##### Clientes de GNC")
    pct_gnc = st.slider("Porcentaje de clientes que cargan GNC", 0, 30,
                        int(round(100 * (previa.pct_gnc if previa.pct_gnc is not None else ajustes_actuales().pct_gnc))),
                        1, key="ed_gnc", format="%d %%",
                        help="Hoy se usa 3 % (DEM-05); el Registro trae 11 % y 20 % como alternativas.") / 100.0

    st.markdown("##### Precio del litro")
    st.caption(
        "El precio mueve el margen $ por $: se supone un costo fijo y que la demanda **no** reacciona "
        "al precio (sin elasticidad). Los de referencia son ECO-08."
    )
    nombres = {"super": "Súper", "premium": "V-Power", "diesel_g2": "Diésel G2", "diesel_g3": "Diésel G3", "gnc": "GNC (por m³)"}
    actuales = dict(previa.precios or valor_registro_precios())
    columnas = st.columns(len(nombres))
    precios = tuple(
        (clave, float(col.number_input(etiqueta, 1, 20000, int(actuales[clave]), 10, key=f"ed_precio_{clave}")))
        for (clave, etiqueta), col in zip(nombres.items(), columnas)
    )

    semilla = int(st.number_input(
        "Semilla del azar", 1, 9999, previa.semilla, 1, key="ed_semilla",
        help="Con la misma semilla la simulación editada da siempre lo mismo.",
    ))

    edicion = Edicion(playeros=playeros, nivel_demanda=nivel, doble_pico=bool(doble),
                      pct_gnc=pct_gnc, precios=precios, semilla=semilla)
    b1, b2 = st.columns([1, 1])
    if b1.button("▶ Simular editada", type="primary"):
        simular_periodo(periodo, edicion)
        st.rerun()
    if b2.button("Cancelar"):
        st.session_state.vista = "resultados"
        st.rerun()
    st.divider()
    st.caption(PIE_NO_AFILIADO)


def valor_registro_precios() -> tuple:
    """Precios de referencia (ECO-08), como `((producto, precio), …)`."""
    return ParametrosEconomicos().precios


def encabezado_resultados() -> None:
    periodo: Periodo = st.session_state.periodo
    editada = st.session_state.get("modo") == "editada"
    c1, c2 = st.columns([5, 1])
    c1.title("⛽ Simulador de la Estación Shell — San Rafael")
    if c2.button("← Cambiar período", key="btn_cambiar_periodo"):
        st.session_state.vista = "inicio"
        st.rerun()
    if editada:
        st.warning(
            f"**Simulación EDITADA (con azar)** · {periodo.titulo} — {periodo.texto}. No son datos "
            f"reales: playeros, demanda, GNC o precios fueron cambiados y los sorteos usan la "
            f"semilla {st.session_state.semilla_usada}.",
            icon="✏️",
        )
    else:
        st.success(
            f"**Simulación con datos reales (sin azar)** · {periodo.titulo} — {periodo.texto}. "
            f"Siempre da el mismo resultado.",
            icon="✅",
        )
    cambios = ajustes_actuales().cambios()
    if cambios:
        st.caption("Ajustes del menú distintos del Registro: " + ", ".join(cambios) + ".")
    p_corrida: ParametrosSimulacion = st.session_state.parametros
    if p_corrida.eventos.activos:
        ocurridos = st.session_state.resultados[0].replicas[0].eventos
        st.info(
            f"**Con eventos aleatorios:** ocurrieron {len(ocurridos)} (semilla {p_corrida.eventos.semilla}; con la "
            f"misma semilla, los mismos). Detalle en la pestaña **⚡ Eventos**; en la animación cada uno es un aviso.",
            icon="⚡",
        )


def pie_de_resultados() -> None:
    st.divider()
    st.markdown("#### ¿Querés probar otra cosa?")
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button("✏️ Editar simulación", key="btn_editar", type="primary"):
        st.session_state.vista = "editar"
        st.rerun()
    if st.session_state.get("modo") == "editada" and c2.button("↩ Volver a los datos reales", key="btn_volver_real"):
        simular_periodo(st.session_state.periodo)
        st.rerun()
    st.caption(PIE_NO_AFILIADO)


#: La ayuda "?" de Streamlit se abre al pasar el mouse **y** mientras el botón tiene el foco. Un clic con el
#: mouse le daba el foco, así que la ayuda quedaba abierta hasta hacer otro clic (el "se traba"). Esto hace
#: que el clic con el mouse no enfoque el botón: la ayuda aparece sólo con el mouse encima y se va al salir.
#: Con el teclado sigue andando: Tab la abre y Escape (o salir con Tab) la cierra. El mismo script avisa un cambio de
#: tamaño al cambiar de pestaña, para que los gráficos dibujados en una pestaña oculta tomen el ancho correcto.
AYUDAS_JS = """<!doctype html><title>ayudas</title><script>
(function () {
  try {
    const doc = window.parent.document;
    if (doc.__ayudasInstaladas) return;
    doc.__ayudasInstaladas = true;
    doc.addEventListener("mousedown", function (e) {
      if (e.target.closest && e.target.closest("[data-testid='stTooltipIcon'] button")) e.preventDefault();
    }, true);
    // Un gráfico dibujado en una pestaña oculta queda angosto (el mapa no se re-acomoda solo): al cambiar de
    // pestaña se avisa un cambio de tamaño de la ventana y Plotly vuelve a medir el ancho.
    doc.addEventListener("click", function (e) {
      if (e.target.closest && e.target.closest("[role='tab']")) {
        setTimeout(function () { window.parent.dispatchEvent(new Event("resize")); }, 150);
      }
    }, true);
  } catch (err) { /* sin acceso a la página: queda el comportamiento de Streamlit */ }
})();
</script>"""


def main() -> None:
    st.markdown(css_global(), unsafe_allow_html=True)
    componentes.html(AYUDAS_JS, height=0)
    vista = st.session_state.get("vista", "inicio")
    if vista == "editar" and "periodo" in st.session_state:
        pantalla_editar()
        return
    if vista == "escenario" and "escenario_unico" in st.session_state:
        pantalla_escenario_unico()
        return
    if vista == "informe":
        pantalla_informe()
        return
    if vista != "resultados" or "resultados" not in st.session_state:
        pantalla_inicio()
        return

    # --- Resultados ---------------------------------------------------------------------
    encabezado_resultados()

    p_corrida: ParametrosSimulacion = st.session_state.parametros
    # La recomendación se arma acá, antes de las pestañas, con lo que haya en la sesión.
    costos = st.session_state.get("costos_politicas")
    st.session_state.politica_actual = politica_configurada(costos, p_corrida)
    st.session_state.recomendacion = recomendacion(
        st.session_state.economia,
        st.session_state.resultados,
        costos,
        st.session_state.politica_actual,
    )

    editada = st.session_state.get("modo") == "editada"
    nombres_tabs = [
        "🏪 La estación", "🎬 Animación", "📊 Indicadores", "🎲 Demanda", "📈 Pronóstico", "🛢️ Inventario",
        "🗺️ Red y rutas", "🔥 GNC", "💰 Economía", "📝 Conclusión",
        "📖 Modelo y método", "📚 Datos y fuentes",
    ]
    con_eventos = bool(p_corrida.eventos.activos)
    if con_eventos:
        nombres_tabs.insert(3, "⚡ Eventos")            # sólo si se prendieron eventos aleatorios en el menú
    if editada:
        nombres_tabs.insert(nombres_tabs.index("🛢️ Inventario"), "🎲 Qué se sorteó")   # sólo si se editó
    pestanias = dict(zip(nombres_tabs, st.tabs(nombres_tabs)))
    resultado = st.session_state.resultados[0]
    with pestanias["🏪 La estación"]:
        pestania_estacion()
    with pestanias["🎬 Animación"]:
        pestania_animacion(p_corrida)
    with pestanias["📊 Indicadores"]:
        vistas.pestania_indicadores(
            p_corrida, resultado, st.session_state.traza, st.session_state.periodo,
            st.session_state.modo,
        )
    if con_eventos:
        with pestanias["⚡ Eventos"]:
            vistas.pestania_eventos(p_corrida, resultado.replicas[0], st.session_state.parametros_eco)
    with pestanias["🎲 Demanda"]:
        vistas.pestania_demanda(p_corrida, resultado, st.session_state.traza, st.session_state.periodo)
    with pestanias["📈 Pronóstico"]:
        vistas.pestania_pronostico(p_corrida)
    if editada:
        with pestanias["🎲 Qué se sorteó"]:
            pestania_sorteos(p_corrida)
    with pestanias["🛢️ Inventario"]:
        pestania_inventario(p_corrida, st.session_state.parametros_eco)
    with pestanias["🗺️ Red y rutas"]:
        pestania_red(p_corrida)
    with pestanias["🔥 GNC"]:
        pestania_gnc(p_corrida)
    with pestanias["💰 Economía"]:
        pestania_economia_real(p_corrida, st.session_state.parametros_eco)
    with pestanias["📝 Conclusión"]:
        pestania_conclusion()
    with pestanias["📖 Modelo y método"]:
        pestania_modelo(p_corrida)
    with pestanias["📚 Datos y fuentes"]:
        pestania_datos_fuentes()

    pie_de_resultados()


if __name__ == "__main__":
    main()
