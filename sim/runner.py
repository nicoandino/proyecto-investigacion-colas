"""Orquestación de corridas: una réplica, N réplicas, los escenarios y el barrido de políticas.

Por qué hacen falta RÉPLICAS y no una sola corrida:
la simulación es un experimento estadístico. Una sola corrida es UNA muestra de un
proceso aleatorio; si se repite con otra semilla da otro número. Por eso cada escenario
se corre N veces con semillas distintas e independientes, y se informa el promedio con
su INTERVALO DE CONFIANZA del 95%. Si los intervalos de dos escenarios se superponen,
no se puede afirmar que uno sea mejor que el otro.

Una réplica = un mes completo de operación (30 días por defecto).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace

from sim.config import (
    Escenario,
    ParametrosSimulacion,
    ParametrosTanque,
    escenarios_desde,
)
from sim.modelo import simular
from sim.traza import Traza

# t de Student para un intervalo de confianza bilateral del 95%, según los grados de
# libertad (n - 1). Se usa tabla en lugar de scipy para no agregar una dependencia.
_T_95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
    15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080,
    22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048,
    29: 2.045, 30: 2.042,
}


def t_critico(grados_libertad: int) -> float:
    """Valor t de Student al 95% bilateral. Para más de 30 g.l. se usa 1.96 (normal)."""
    if grados_libertad < 1:
        return float("nan")
    return _T_95.get(grados_libertad, 1.96)


@dataclass(frozen=True)
class ResultadoReplica:
    """Indicadores de UNA réplica: un mes de operación con una semilla.

    Las cantidades de flujo (autos, litros, pedidos) están expresadas POR DÍA, para que
    no dependan de cuántos días se hayan simulado.
    """

    semilla: int

    # --- Colas: los indicadores clásicos del modelo de colas -----------------
    espera_surtidor: float        # minutos promedio en la cola del surtidor
    espera_caja: float
    espera_pico: float            # espera promedio en la peor hora del día
    cola_surtidor: float          # longitud promedio de cola (promedio temporal)
    cola_caja: float
    util_surtidores: float        # 0 a 1
    util_cajas: float
    tiempo_sistema: float
    max_cola_surtidor: float
    max_espera_surtidor: float

    # --- Clientes por día ----------------------------------------------------
    llegadas_dia: float
    atendidos_dia: float
    perdidos_cola_dia: float          # abandono por cola larga
    perdidos_sin_combustible_dia: float
    perdidos_caja_dia: float
    compras_dia: float
    tasa_abandono: float              # % de los que llegan y se van sin cargar

    # --- Inventario ----------------------------------------------------------
    litros_vendidos_dia: float
    litros_no_vendidos_dia: float
    nivel_servicio: float             # 0 a 1: fracción de la demanda de litros satisfecha
    nivel_tanque_promedio: float      # litros
    nivel_tanque_minimo: float
    pedidos_dia: float
    plazo_entrega: float              # horas
    porcentaje_dias_quiebre: float    # % de días con al menos un quiebre
    porcentaje_tiempo_sin_combustible: float

    # --- Por hora (para el gráfico del perfil) -------------------------------
    hora_pico: int

    # --- Estación real (Fase 2): por motivo, grupo y producto -----------------
    perdidos_cola_llena_dia: float = 0.0
    util_playeros: float = 0.0            # playeros ocupados ÷ playeros en turno (promedio temporal)
    viajes_demorados_pct: float = 0.0     # % de los camiones que encontraron un corte (Fase 5)
    gnc_afectados_dia: float = 0.0        # clientes GNC que se toparon con el corte (Fase 6)
    migrados_gnc_dia: float = 0.0         # ... y pasaron a Súper
    perdidos_corte_gnc_dia: float = 0.0   # ... y se fueron sin cargar
    m3_gnc_vendidos_dia: float = 0.0      # GNC vendido, en m³
    m3_gnc_perdidos_dia: float = 0.0      # GNC que pidieron los que se fueron, en m³
    dias_corte_gnc_pct: float = 0.0       # % de los días medidos con algún tramo de corte
    util_compresores: float = 0.0         # compresores ocupados ÷ compresores
    demora_ruta_promedio: float = 0.0     # horas de demora por viaje (incluye los que no se demoran)
    espera_por_grupo: tuple[float, ...] = ()
    cola_por_grupo: tuple[float, ...] = ()
    util_por_grupo: tuple[float, ...] = ()
    atendidos_por_producto: tuple[tuple[str, float], ...] = ()
    litros_vendidos_por_producto: tuple[tuple[str, float], ...] = ()
    dias_quiebre_por_producto: tuple[tuple[str, float], ...] = ()
    # Fase 4: lo que hace falta para costear la política (s, Q) de CADA tanque
    pedidos_por_producto: tuple[tuple[str, float], ...] = ()          # camiones pedidos por día
    nivel_por_producto: tuple[tuple[str, float], ...] = ()            # litros promedio en el tanque
    litros_sin_stock_por_producto: tuple[tuple[str, float], ...] = () # litros no vendidos por día
    perdidos_sin_stock_por_producto: tuple[tuple[str, float], ...] = ()  # clientes por día


#: Campos que NO son métricas numéricas (no se promedian en `resumir`).
NO_METRICAS = {
    "semilla",
    "espera_por_grupo",
    "cola_por_grupo",
    "util_por_grupo",
    "atendidos_por_producto",
    "litros_vendidos_por_producto",
    "dias_quiebre_por_producto",
    "pedidos_por_producto",
    "nivel_por_producto",
    "litros_sin_stock_por_producto",
    "perdidos_sin_stock_por_producto",
}

#: Métricas que se promedian entre réplicas (todas menos las no numéricas).
METRICAS: tuple[str, ...] = tuple(
    f.name for f in fields(ResultadoReplica) if f.name not in NO_METRICAS
)


@dataclass(frozen=True)
class Resumen:
    """Resultado de una métrica a lo largo de las réplicas."""

    promedio: float
    desvio: float
    semiamplitud: float   # mitad del ancho del IC 95%
    minimo: float
    maximo: float
    n: int

    @property
    def ic_inferior(self) -> float:
        return self.promedio - self.semiamplitud

    @property
    def ic_superior(self) -> float:
        return self.promedio + self.semiamplitud


@dataclass(frozen=True)
class ResultadoEscenario:
    """Todo lo que produjo un escenario de capacidad."""

    escenario: Escenario
    parametros: ParametrosSimulacion
    replicas: list[ResultadoReplica]
    resumen: dict[str, Resumen]

    def prom(self, metrica: str) -> float:
        return self.resumen[metrica].promedio


@dataclass(frozen=True)
class ResultadoPolitica:
    """Todo lo que produjo una política de reposición (punto de pedido, cantidad)."""

    punto_pedido: float
    cantidad_pedido: float
    replicas: list[ResultadoReplica]
    resumen: dict[str, Resumen]

    @property
    def etiqueta(self) -> str:
        return f"s={self.punto_pedido:,.0f} / Q={self.cantidad_pedido:,.0f}"

    def prom(self, metrica: str) -> float:
        return self.resumen[metrica].promedio


# --- Una réplica --------------------------------------------------------------
def _por_tanque(p: ParametrosSimulacion, ind, valor) -> tuple[tuple[str, float], ...]:
    """((producto, valor), ...) de cada tanque; vacío en el caso clásico (un solo tanque)."""
    if not p.estacion_real:
        return ()
    return tuple((i.producto, float(valor(i.producto))) for i in p.inventario)


def correr_replica(
    p: ParametrosSimulacion,
    semilla: int,
    con_traza: bool = False,
) -> tuple[ResultadoReplica, Traza | None]:
    """Corre una réplica (un mes) y arma su `ResultadoReplica`."""
    ind, traza = simular(p, semilla=semilla, con_traza=con_traza)
    c = ind.c
    dias = max(p.dias_medidos, 1)

    esperas_por_hora = [ind.por_hora.espera_promedio(h) for h in range(24)]
    espera_pico = max(esperas_por_hora)
    hora_pico = esperas_por_hora.index(espera_pico)

    resultado = ResultadoReplica(
        semilla=semilla,
        espera_surtidor=ind.espera_surtidor.promedio,
        espera_caja=ind.espera_caja.promedio,
        espera_pico=espera_pico,
        cola_surtidor=ind.cola_surtidor.promedio,
        cola_caja=ind.cola_caja.promedio,
        util_surtidores=ind.utilizacion_surtidores,
        util_cajas=ind.utilizacion_cajas,
        tiempo_sistema=ind.tiempo_sistema.promedio,
        max_cola_surtidor=ind.cola_surtidor.maximo,
        max_espera_surtidor=ind.espera_surtidor.maximo,
        llegadas_dia=c.llegadas / dias,
        atendidos_dia=c.atendidos_surtidor / dias,
        perdidos_cola_dia=c.perdidos_surtidor / dias,
        perdidos_sin_combustible_dia=c.perdidos_sin_combustible / dias,
        perdidos_caja_dia=c.perdidos_caja / dias,
        compras_dia=c.compras_atendidas / dias,
        tasa_abandono=(
            100.0
            * (
                c.perdidos_surtidor + c.perdidos_sin_combustible + c.perdidos_cola_llena
                + c.perdidos_corte_gnc
            )
            / c.llegadas
            if c.llegadas
            else 0.0
        ),
        litros_vendidos_dia=c.litros_vendidos / dias,
        litros_no_vendidos_dia=c.litros_no_vendidos / dias,
        nivel_servicio=ind.nivel_servicio,
        nivel_tanque_promedio=ind.nivel_tanque_promedio,
        nivel_tanque_minimo=ind.nivel_tanque.minimo,
        pedidos_dia=c.pedidos_emitidos / dias,
        plazo_entrega=ind.plazo_entrega.promedio,
        porcentaje_dias_quiebre=100.0 * c.dias_con_quiebre / dias,
        porcentaje_tiempo_sin_combustible=100.0 * ind.fraccion_sin_combustible,
        gnc_afectados_dia=c.gnc_afectados / dias,
        migrados_gnc_dia=c.migrados_gnc_a_nafta / dias,
        perdidos_corte_gnc_dia=c.perdidos_corte_gnc / dias,
        m3_gnc_vendidos_dia=ind.c_producto["gnc"].litros_vendidos / dias,
        m3_gnc_perdidos_dia=ind.c_producto["gnc"].litros_no_vendidos / dias,
        dias_corte_gnc_pct=100.0 * c.dias_con_corte_gnc / dias,
        util_compresores=(
            ind.compresores_ocupados.promedio / p.gnc.compresores
            if p.estacion_real and p.gnc is not None
            else 0.0
        ),
        viajes_demorados_pct=(
            100.0 * c.viajes_demorados / c.pedidos_emitidos if c.pedidos_emitidos else 0.0
        ),
        demora_ruta_promedio=(
            ind.demora_ruta.suma / c.pedidos_emitidos if c.pedidos_emitidos else 0.0
        ),
        hora_pico=hora_pico,
        # --- Estación real: por motivo, grupo y producto ---
        perdidos_cola_llena_dia=c.perdidos_cola_llena / dias,
        util_playeros=(
            ind.playeros_ocupados.promedio / ind.playeros_en_turno.promedio
            if ind.playeros_en_turno.promedio > 0
            else 0.0
        ),
        espera_por_grupo=tuple(
            ind.esperas_grupo[g.id].promedio for g in p.grupos
        ),
        cola_por_grupo=tuple(ind.colas_grupo[g.id].promedio for g in p.grupos),
        util_por_grupo=tuple(
            ind.ocupados_grupo[g.id].promedio / g.caras for g in p.grupos
        ),
        atendidos_por_producto=tuple(
            (pr, ind.c_producto[pr].atendidos / dias) for pr in ind.c_producto
        ),
        litros_vendidos_por_producto=tuple(
            (pr, ind.c_producto[pr].litros_vendidos / dias) for pr in ind.c_producto
        ),
        dias_quiebre_por_producto=tuple(
            (pr, 100.0 * ind.c_producto[pr].dias_con_quiebre / dias)
            for pr in ind.c_producto
        ),
        pedidos_por_producto=_por_tanque(
            p, ind, lambda pr: ind.c_producto[pr].pedidos_emitidos / dias
        ),
        nivel_por_producto=_por_tanque(p, ind, lambda pr: ind.niveles[pr].promedio),
        litros_sin_stock_por_producto=_por_tanque(
            p, ind, lambda pr: ind.c_producto[pr].litros_perdidos_sin_combustible / dias
        ),
        perdidos_sin_stock_por_producto=_por_tanque(
            p, ind, lambda pr: ind.c_producto[pr].perdidos_sin_combustible / dias
        ),
    )
    return resultado, traza


# --- N réplicas ---------------------------------------------------------------
def resumen_de(valores: list[float]) -> Resumen:
    """Promedio, desvío e IC 95 % (t de Student) de una lista de valores, uno por réplica."""
    n = len(valores)
    promedio = sum(valores) / n
    if n > 1:
        varianza = sum((v - promedio) ** 2 for v in valores) / (n - 1)
        desvio = math.sqrt(varianza)
        semiamplitud = t_critico(n - 1) * desvio / math.sqrt(n)
    else:
        desvio = 0.0
        semiamplitud = 0.0
    return Resumen(
        promedio=promedio,
        desvio=desvio,
        semiamplitud=semiamplitud,
        minimo=min(valores),
        maximo=max(valores),
        n=n,
    )


def resumir(replicas: list[ResultadoReplica]) -> dict[str, Resumen]:
    """Promedio, desvío e intervalo de confianza 95% de cada métrica."""
    return {
        metrica: resumen_de([float(getattr(r, metrica)) for r in replicas])
        for metrica in METRICAS
    }


def correr_replicas(
    p: ParametrosSimulacion,
    replicas: int = 5,
    semilla_base: int = 1,
) -> list[ResultadoReplica]:
    """Corre `replicas` réplicas independientes, con semillas semilla_base + i."""
    return [correr_replica(p, semilla=semilla_base + i)[0] for i in range(replicas)]


# --- Escenarios de capacidad --------------------------------------------------
def correr_escenarios(
    p: ParametrosSimulacion | None = None,
    replicas: int = 5,
    semilla_base: int = 1,
) -> list[ResultadoEscenario]:
    """Corre Base / A / B / C con NÚMEROS ALEATORIOS COMUNES.

    La réplica i de todos los escenarios usa la misma semilla, así que los autos llegan
    en los mismos instantes, cargan los mismos litros y el camión tarda lo mismo en los
    cuatro escenarios. La comparación aísla el efecto de agregar surtidores o cajas.
    """
    p = p or ParametrosSimulacion()
    salida: list[ResultadoEscenario] = []

    for escenario in escenarios_desde(p):
        p_esc = escenario.aplicar(p)
        reps = correr_replicas(p_esc, replicas=replicas, semilla_base=semilla_base)
        salida.append(
            ResultadoEscenario(
                escenario=escenario,
                parametros=p_esc,
                replicas=reps,
                resumen=resumir(reps),
            )
        )
    return salida


def buscar(resultados: list[ResultadoEscenario], nombre: str) -> ResultadoEscenario:
    """Devuelve el escenario con ese nombre (por ejemplo 'Base')."""
    for r in resultados:
        if r.escenario.nombre == nombre:
            return r
    raise KeyError(f"No existe el escenario {nombre}")


def correr_estacion_real(
    p: ParametrosSimulacion,
    replicas: int = 5,
    semilla_base: int = 1,
) -> ResultadoEscenario:
    """Corre la estación real (3 grupos, 5 productos, playeros) y la envuelve en un
    único "escenario Base" para que la interfaz clásica la muestre.

    El catálogo de escenarios del caso real (S0–S12) llega en la Fase 7; por ahora
    la comparación de capacidad es la del caso clásico.
    """
    total_caras = sum(g.caras for g in p.grupos)
    escenario = Escenario(
        nombre="Base",
        descripcion=f"Estación real (Shell San Rafael, {total_caras} caras)",
        surtidores=total_caras,
        cajas=p.cajas,
    )
    replicas_corridas = correr_replicas(p, replicas=replicas, semilla_base=semilla_base)
    return ResultadoEscenario(
        escenario=escenario,
        parametros=p,
        replicas=replicas_corridas,
        resumen=resumir(replicas_corridas),
    )


# --- Barrido de políticas de inventario ---------------------------------------
def con_politica(
    p: ParametrosSimulacion,
    punto_pedido: float,
    cantidad_pedido: float,
) -> ParametrosSimulacion:
    """Los mismos parámetros pero con otra política de reposición."""
    tanque = replace(
        p.tanque, punto_pedido=punto_pedido, cantidad_pedido=cantidad_pedido
    )
    return replace(p, tanque=tanque)


def barrer_politicas(
    p: ParametrosSimulacion,
    puntos_pedido: list[float],
    cantidades: list[float],
    replicas: int = 3,
    semilla_base: int = 1,
) -> list[ResultadoPolitica]:
    """Prueba todas las combinaciones de punto de pedido y cantidad a pedir.

    Es el "problema de diseño" del apunte aplicado al inventario: en vez de comparar
    cuatro escenarios armados a mano, se barre una grilla y se elige la política de
    menor costo total. Todas las combinaciones usan las mismas semillas (números
    aleatorios comunes) para que la comparación sea justa.
    """
    salida: list[ResultadoPolitica] = []
    for punto in puntos_pedido:
        for cantidad in cantidades:
            if punto + cantidad > p.tanque.capacidad:
                # No tiene sentido pedir más de lo que entra en el tanque.
                continue
            p_pol = con_politica(p, punto, cantidad)
            reps = correr_replicas(p_pol, replicas=replicas, semilla_base=semilla_base)
            salida.append(
                ResultadoPolitica(
                    punto_pedido=punto,
                    cantidad_pedido=cantidad,
                    replicas=reps,
                    resumen=resumir(reps),
                )
            )
    return salida


def grilla_sugerida(p: ParametrosSimulacion) -> tuple[list[float], list[float]]:
    """Grilla razonable de políticas alrededor del consumo real de la estación.

    El punto de pedido se mueve entre medio día y día y medio de venta; la cantidad a
    pedir, entre uno y dos días y medio. La grilla se adapta sola si cambia la demanda, y
    siempre incluye la política que está configurada, para poder compararla contra el resto.
    """
    consumo_diario = p.litros_por_dia
    capacidad = p.tanque.capacidad

    def redondear(valor: float) -> float:
        return round(valor / 1000) * 1000

    puntos = [redondear(consumo_diario * f) for f in (0.5, 0.8, 1.1, 1.5)]
    cantidades = [redondear(consumo_diario * f) for f in (1.0, 1.6, 2.2)]

    # La política actual tiene que estar en la grilla para poder compararla.
    puntos.append(p.tanque.punto_pedido)
    cantidades.append(p.tanque.cantidad_pedido)

    puntos = sorted({x for x in puntos if 0 < x < capacidad})
    cantidades = sorted({x for x in cantidades if 0 < x <= capacidad})
    return puntos, cantidades


# --- Política (s, Q) por producto (Fase 4) --------------------------------------
def promedio_por_producto(
    replicas: list[ResultadoReplica], campo: str
) -> dict[str, float]:
    """Promedio entre réplicas de un campo ((producto, valor), ...)."""
    acumulado: dict[str, float] = {}
    for r in replicas:
        for producto, valor in getattr(r, campo):
            acumulado[producto] = acumulado.get(producto, 0.0) + valor
    return {k: v / len(replicas) for k, v in acumulado.items()}


def con_politicas(
    p: ParametrosSimulacion, politicas: dict[str, tuple[float, float]]
) -> ParametrosSimulacion:
    """Los mismos parámetros pero con (s, Q) distintos en algunos tanques."""
    inventario = tuple(
        replace(i, punto_pedido=politicas[i.producto][0], cantidad_pedido=politicas[i.producto][1])
        if i.producto in politicas
        else i
        for i in p.inventario
    )
    return replace(p, inventario=inventario)


#: Puntos de pedido y cantidades de la grilla, en DÍAS de consumo del producto. El camión
#: tarda 24–48 h, así que s por debajo de 1 día casi seguro quiebra.
S_EN_DIAS = (1.0, 1.5, 2.0, 2.5)
Q_EN_DIAS = (2.0, 3.0, 4.5)


def grilla_politicas_real(p: ParametrosSimulacion) -> list[dict[str, tuple[float, float]]]:
    """Puntos de la grilla; cada uno trae la política (s, Q) de TODOS los tanques.

    El punto 0 es la política cargada (para poder compararla). Los demás combinan s y Q
    medidos en días de consumo de cada producto, así que la grilla se adapta sola a la
    demanda y a la mezcla. Como cada camión es independiente (un pedido por producto)
    y cada producto tiene su propio stream de plazos, las cuatro curvas de costo se
    miden en las MISMAS corridas: 13 puntos × réplicas, no 13⁴.
    """
    consumo_mes = p.litros_mes / 30.0
    pct = {pr.id: pr.pct_litros for pr in p.productos}
    puntos: list[dict[str, tuple[float, float]]] = [
        {i.producto: (i.punto_pedido, i.cantidad_pedido) for i in p.inventario}
    ]
    for s_dias in S_EN_DIAS:
        for q_dias in Q_EN_DIAS:
            punto: dict[str, tuple[float, float]] = {}
            for i in p.inventario:
                consumo_dia = consumo_mes * pct[i.producto]
                s_ = min(round(s_dias * consumo_dia, -2), i.capacidad - 500.0)
                q_ = max(500.0, min(round(q_dias * consumo_dia, -2), i.capacidad - s_))
                punto[i.producto] = (s_, q_)
            puntos.append(punto)
    return puntos


@dataclass(frozen=True)
class PuntoBarrido:
    """Una corrida del barrido: la política de cada tanque y las réplicas de la estación."""

    politicas: dict[str, tuple[float, float]]
    replicas: list[ResultadoReplica]


@dataclass(frozen=True)
class ResultadoBarridoReal:
    """El barrido de políticas de la estación real (todos los tanques a la vez)."""

    productos: tuple[str, ...]
    puntos: list[PuntoBarrido]


def barrer_politicas_real(
    p: ParametrosSimulacion,
    replicas: int = 2,
    semilla_base: int = 1,
) -> ResultadoBarridoReal:
    """Barre la grilla de (s, Q) de los 4 tanques con números aleatorios comunes."""
    puntos = [
        PuntoBarrido(
            politicas=politicas,
            replicas=correr_replicas(
                con_politicas(p, politicas), replicas=replicas, semilla_base=semilla_base
            ),
        )
        for politicas in grilla_politicas_real(p)
    ]
    return ResultadoBarridoReal(
        productos=tuple(i.producto for i in p.inventario), puntos=puntos
    )
