"""Simulador de Estación de Servicio — Investigación Operativa.

Interfaz del simulador: se configuran los parámetros en la barra lateral, se corre la
simulación y se ven la animación, los indicadores, la demanda Monte Carlo, el inventario,
la comparación de escenarios, el análisis económico y la conclusión.

Para ejecutar:
    .venv/Scripts/streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import streamlit.components.v1 as componentes

from sim.config import (
    DEMANDA_TIPICA,
    ESTACIONALIDAD_LEVE,
    ESTACIONALIDAD_NEUTRA,
    ESTACIONALIDAD_PROXY,
    DemandaDiaria,
    ParametrosEconomicos,
    ParametrosSimulacion,
    ParametrosTanque,
    Triangular,
    dias_y_fecha,
)
from sim.datos import ADVERTENCIAS, CONTRADICCIONES, PIE_NO_AFILIADO, REGISTRO, por_id
from sim.economia import (
    analizar_escenarios,
    analizar_politicas,
    mejor_politica,
    pesos,
    recomendacion,
)
from sim.runner import (
    ResultadoEscenario,
    barrer_politicas,
    buscar,
    con_politica,
    correr_escenarios,
    correr_replica,
    grilla_sugerida,
)
from ui import animacion, graficos
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
    INDICADORES_INVENTARIO,
    SUPUESTOS,
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
    # Si en la pestaña Inventario se apretó "Usar esta política", los valores se aplican
    # ACÁ, antes de crear los controles: Streamlit no permite modificar un widget que ya
    # fue instanciado en esta misma ejecución.
    sugerida = st.session_state.pop("politica_sugerida", None)
    if sugerida is not None:
        st.session_state["w_punto_pedido"] = int(sugerida[0])
        st.session_state["w_cantidad_pedido"] = int(sugerida[1])

    st.sidebar.title("⛽ Parámetros")
    st.sidebar.caption("Al cambiar algo hay que volver a correr la simulación.")

    with st.sidebar.expander("🏪 Capacidad actual", expanded=True):
        st.markdown(
            f"El motor todavía usa la configuración clásica "
            f"{insignia_html(por_id('REC-01'))}{insignia_html(por_id('REC-02'))} "
            f"(el rediseño de 12 caras y grupos entra en la Fase 2 del orquestador).",
            unsafe_allow_html=True,
        )
        surtidores = st.number_input("Surtidores instalados", 1, 8, 3, 1)
        cajas = st.number_input("Cajas en el minimarket", 1, 4, 1, 1)

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
            format_func=lambda x: (
                "Demanda esperada (litros por mes)"
                if x == "esperada"
                else "Monte Carlo (tabla empírica)"
            ),
            horizontal=True,
            help="Con 'esperada' el total diario sale de los litros por mes y el "
                 "calendario; con 'Monte Carlo' se sortea de la tabla de frecuencias. "
                 "En ambos modos las llegadas son Poisson y los tiempos aleatorios, "
                 "así que se mantienen las réplicas y el calentamiento.",
        )
        if modo_demanda == "esperada":
            litros_mes = st.slider(
                "Demanda mensual (litros/mes)", 50_000, 600_000, 270_000, 10_000,
                help="Es la variable de entrada: los clientes por día se derivan de "
                     "acá, nunca al revés.",
            )
            litros_medios_por_cliente = st.number_input(
                "Litros medios por cliente (L)", 5.0, 200.0, 35.7, 0.1,
                help="Litros que carga en promedio un cliente de combustible líquido "
                     "(mezcla de productos y tipos de vehículo).",
            )
            clientes_dia = (litros_mes / 30.0) / litros_medios_por_cliente
            st.caption(
                f"≈ {litros_mes / 30.0:,.0f} L/día ⇒ **{clientes_dia:,.0f} "
                f"clientes/día** (antes de sumar el GNC)."
            )
        else:
            litros_mes = 270_000.0
            litros_medios_por_cliente = 35.7

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
        fecha_inicio, dias_por_horizonte = dias_y_fecha(
            horizonte, mes_elegido, dia_elegido, estacion_elegida
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
                "Factor de fin de semana", 1.0, 2.0, 1.30, 0.01,
                help="El finde vende más que un día hábil; el nivel diario se "
                     "normaliza para conservar los litros del mes.",
            )
        else:
            estacionalidad = ESTACIONALIDAD_NEUTRA
            factor_fin_de_semana = 1.30

    if modo_demanda == "monte_carlo":
        with st.sidebar.expander("🚗 Demanda diaria (tabla Monte Carlo)"):
            st.caption(
                "Tabla de frecuencias observada: en cuántos días se registró cada nivel de "
                "demanda. De acá se sortea la demanda de cada día simulado."
            )
            tabla = st.data_editor(
                pd.DataFrame(
                    {"Autos por día": [280, 320, 360, 400, 440],
                     "Días observados": [10, 20, 40, 20, 10]}
                ),
                num_rows="dynamic",
                hide_index=True,
                key="tabla_demanda",
            )
            demanda = construir_demanda(tabla)
            st.caption(f"Demanda media: **{demanda.media:.0f} autos por día**")
    else:
        demanda = DEMANDA_TIPICA

    with st.sidebar.expander("⏱️ Tiempos de servicio"):
        st.markdown(
            f"Fuentes {insignia_html(por_id('TIE-02'))} {insignia_html(por_id('TIE-05'))}",
            unsafe_allow_html=True,
        )
        st.markdown("**Carga de combustible** — Triangular (min)")
        c1, c2, c3 = st.columns(3)
        carga = Triangular(
            c1.number_input("mín", 0.5, 30.0, 2.0, 0.5, key="carga_min"),
            c2.number_input("moda", 0.5, 30.0, 5.0, 0.5, key="carga_moda"),
            c3.number_input("máx", 0.5, 30.0, 8.0, 0.5, key="carga_max"),
        )
        st.markdown("**Compra en el minimarket** (min)")
        d1, d2, d3 = st.columns(3)
        compra = Triangular(
            d1.number_input("mín", 0.2, 30.0, 2.0, 0.5, key="compra_min"),
            d2.number_input("moda", 0.2, 30.0, 4.0, 0.5, key="compra_moda"),
            d3.number_input("máx", 0.2, 30.0, 10.0, 0.5, key="compra_max"),
        )
        caja_exponencial = st.checkbox(
            "Usar Exponencial en la caja", value=False,
            help="La propuesta admite Triangular o Exponencial para el tiempo en caja. "
                 "Con Exponencial se usa la misma media que la triangular cargada.",
        )

    with st.sidebar.expander("⛽ Litros por carga"):
        st.markdown(
            f"Fuente {insignia_html(por_id('VEH-06'))} (el desglose por tipo de "
            f"vehículo — VEH-01..05 — entra en la Fase 2).",
            unsafe_allow_html=True,
        )
        st.caption("Cuánto carga cada auto. Es lo que consume el tanque.")
        e1, e2, e3 = st.columns(3)
        litros = Triangular(
            e1.number_input("mín", 1.0, 200.0, 15.0, 5.0, key="litros_min"),
            e2.number_input("moda", 1.0, 200.0, 30.0, 5.0, key="litros_moda"),
            e3.number_input("máx", 1.0, 200.0, 60.0, 5.0, key="litros_max"),
        )

    with st.sidebar.expander("🧍 Comportamiento del cliente"):
        st.markdown(
            f"Fuentes {insignia_html(por_id('DEM-08'))} {insignia_html(por_id('TIE-06'))}",
            unsafe_allow_html=True,
        )
        prob_compra = st.slider(
            "Probabilidad de entrar al minimarket", 0.0, 1.0, 0.20, 0.05,
            help="Ensayo de Bernoulli después de cargar combustible.",
        )
        paciencia_surtidor = st.slider(
            "Paciencia en la cola del surtidor (min)", 1.0, 30.0, 10.0, 1.0,
            help="Si la espera supera este umbral, el cliente abandona y se pierde la venta.",
        )
        paciencia_caja = st.slider("Paciencia en la cola de la caja (min)", 1.0, 30.0, 8.0, 1.0)

    with st.sidebar.expander("🛢️ Tanque y reposición", expanded=True):
        st.markdown(
            f"Fuentes {insignia_html(por_id('INV-03'))} {insignia_html(por_id('INV-07'))} "
            f"{insignia_html(por_id('INV-01'))}",
            unsafe_allow_html=True,
        )
        capacidad = st.number_input("Capacidad del tanque (L)", 5_000, 200_000, 20_000, 5_000)
        nivel_inicial = st.number_input("Nivel inicial (L)", 0, int(capacidad), 15_000, 1_000)
        punto_pedido = st.number_input(
            "Punto de pedido s (L)", 0, int(capacidad), 13_500, 1_000,
            key="w_punto_pedido",
            help="Cuando el combustible disponible (lo que hay más lo que viene en "
                 "camino) baja de este valor, se pide un camión.",
        )
        cantidad_pedido = st.number_input(
            "Cantidad a pedir Q (L)", 1_000, int(capacidad), 6_500, 1_000,
            key="w_cantidad_pedido",
            help="Cuántos litros trae cada camión cisterna.",
        )
        st.markdown("**Plazo de entrega del camión** — Triangular (horas)")
        f1, f2, f3 = st.columns(3)
        plazo = Triangular(
            f1.number_input("mín", 1.0, 200.0, 24.0, 1.0, key="plazo_min"),
            f2.number_input("moda", 1.0, 200.0, 36.0, 1.0, key="plazo_moda"),
            f3.number_input("máx", 1.0, 200.0, 48.0, 1.0, key="plazo_max"),
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
                "Días de calentamiento", 0, max_calentamiento, min(2, max_calentamiento), 1,
                help="Días que se simulan pero no se miden: la estación arranca con las colas "
                     "vacías y el tanque al 75 %, que no es su estado habitual.",
            )

        dia_animado = st.slider("Día a animar", 1, min(dias, 90), min(2, int(dias)), 1)
        replicas = st.slider(
            "Réplicas por escenario", 2, 15, 4, 1,
            help="Cada réplica es un mes completo con otra semilla. Más réplicas dan "
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

    p = ParametrosSimulacion(
        surtidores=int(surtidores),
        cajas=int(cajas),
        demanda=demanda,
        carga=carga,
        compra=compra,
        caja_exponencial=bool(caja_exponencial),
        litros=litros,
        prob_compra=float(prob_compra),
        paciencia_surtidor=float(paciencia_surtidor),
        paciencia_caja=float(paciencia_caja),
        tanque=ParametrosTanque(
            capacidad=float(capacidad),
            nivel_inicial=float(nivel_inicial),
            punto_pedido=float(punto_pedido),
            cantidad_pedido=float(cantidad_pedido),
            plazo_entrega=plazo,
        ),
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
    traza = st.session_state.traza

    st.subheader(f"Animación del día {p.dia_animado}")
    st.caption(
        f"Escenario Base ({p.surtidores} surtidores, {p.cajas} caja/s). Se anima un día "
        f"completo, de 00:00 a 24:00. Abajo se ve el tanque: cuando el nivel cruza el "
        f"punto de pedido se despacha un camión, y si llega a cero la estación deja de vender."
    )

    componentes.html(
        animacion.reproductor_html(
            cuadros=traza.cuadros,
            surtidores=p.surtidores,
            cajas=p.cajas,
            dt=p.dt_traza,
            capacidad_tanque=p.tanque.capacidad,
            punto_pedido=p.tanque.punto_pedido,
            dia=p.dia_animado,
            litros_minimos=p.litros.minimo,
        ),
        height=animacion.ALTO_COMPONENTE,
    )

    st.divider()
    g1, g2 = st.columns(2)
    g1.plotly_chart(graficos.grafico_evolucion_colas(traza, p.dia_animado), key="g_colas")
    g2.plotly_chart(
        graficos.grafico_ocupacion(traza, p.surtidores, p.dia_animado), key="g_ocupacion"
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


def pestania_indicadores(p: ParametrosSimulacion) -> None:
    base = buscar(st.session_state.resultados, "Base")

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
def pestania_demanda(p: ParametrosSimulacion) -> None:
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
def pestania_inventario(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> None:
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


def pestania_conclusion() -> None:
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
def pestania_modelo(p: ParametrosSimulacion) -> None:
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
    """Corre los 4 escenarios y la réplica con traza, y guarda todo en la sesión."""
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

    if correr or "resultados" not in st.session_state:
        with st.spinner(
            f"Simulando {replicas} réplicas de {p.dias} días en 4 escenarios…"
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
        pestania_escenarios()
    with pestanias[6]:
        pestania_economia(p_corrida, st.session_state.parametros_eco)
    with pestanias[7]:
        pestania_conclusion()
    with pestanias[8]:
        pestania_modelo(p_corrida)
    with pestanias[9]:
        pestania_datos_fuentes()

    st.divider()
    st.caption(PIE_NO_AFILIADO)
    st.sidebar.divider()
    st.sidebar.caption(PIE_NO_AFILIADO)


if __name__ == "__main__":
    main()
