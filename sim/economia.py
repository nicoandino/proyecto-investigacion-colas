"""Análisis económico: ¿en qué conviene poner la plata?

La simulación dice cuántos autos se atienden, cuántos litros se venden, cuántos clientes
se pierden y cuánto combustible queda inmovilizado en el tanque. Este módulo traduce todo
eso a pesos y responde las dos preguntas del trabajo:

  1. ¿Conviene agregar un surtidor y/o un cajero?  -> `analizar_escenarios`
  2. ¿Cuál es la mejor política de reposición?     -> `analizar_politicas`

Las dos compiten por la misma plata, así que se comparan con el mismo criterio.

Estructura de costos de inventario (la clásica de la teoría de inventarios):

    costo total = costo de pedido + costo de almacenamiento + costo de faltante

  - Costo de pedido: el flete del camión cisterna, por cada pedido.
  - Costo de almacenamiento: el capital inmovilizado en combustible, proporcional al
    nivel promedio del tanque.
  - Costo de faltante: la venta que se pierde cuando la estación se queda sin nafta.

Pedir seguido y poco baja el almacenamiento pero dispara el flete; pedir de a mucho hace
lo contrario; y pedir tarde ahorra en ambos pero se paga con quiebres de stock. El mínimo
está en el medio, y es lo que busca el barrido de políticas.
"""

from __future__ import annotations

from dataclasses import dataclass

from sim.config import ParametrosEconomicos, ParametrosSimulacion
from sim.runner import (
    ResultadoBarridoReal,
    ResultadoEscenario,
    ResultadoPolitica,
    buscar,
    promedio_por_producto,
)

DIAS_DEL_MES = 30


def pesos(valor: float) -> str:
    """Formatea un importe con el signo delante del símbolo: -$860.000, no $-860.000."""
    signo = "-" if valor < 0 else ""
    return f"{signo}${abs(valor):,.0f}"


# =============================================================================
# Escenarios de capacidad
# =============================================================================
@dataclass(frozen=True)
class ResultadoEconomico:
    """Traducción a pesos de los resultados de un escenario de capacidad."""

    nombre: str
    descripcion: str
    surtidores: int
    cajas: int
    surtidores_extra: int
    cajas_extra: int

    # Operación (promedio por día)
    litros_dia: float
    compras_dia: float
    perdidos_dia: float

    # Ingresos mensuales
    ingreso_combustible: float
    ingreso_minimarket: float
    ingreso_mensual: float

    # Costos mensuales
    costo_inventario: float          # flete + almacenamiento
    costo_capacidad: float           # incremental: operativo del surtidor + sueldo del cajero
    venta_perdida: float             # costo de oportunidad (no sale del bolsillo)

    # Resultado
    margen_operativo: float          # ingreso - costo de inventario - costo de capacidad
    ingreso_extra: float             # contra el escenario Base
    beneficio_neto: float            # margen operativo contra el del Base
    inversion_inicial: float
    payback_meses: float | None

    @property
    def conviene(self) -> bool:
        return self.beneficio_neto > 0

    @property
    def es_base(self) -> bool:
        return self.surtidores_extra == 0 and self.cajas_extra == 0

    @property
    def payback_texto(self) -> str:
        if self.es_base:
            return "-"
        if self.payback_meses is None:
            return "nunca se repaga"
        if self.payback_meses <= 0.05:
            return "inmediato (sin inversión)"
        if self.payback_meses > 240:
            return "más de 20 años"
        return f"{self.payback_meses:.1f} meses"


def _economia_de(
    r: ResultadoEscenario,
    eco: ParametrosEconomicos,
    p: ParametrosSimulacion,
    surtidores_extra: int,
    cajas_extra: int,
) -> dict[str, float]:
    """Los números en pesos de un escenario, antes de compararlo con el Base."""
    litros_dia = r.prom("litros_vendidos_dia")
    compras_dia = r.prom("compras_dia")
    perdidos_dia = (
        r.prom("perdidos_cola_dia")
        + r.prom("perdidos_sin_combustible_dia")
        + r.prom("perdidos_cola_llena_dia")
        + r.prom("perdidos_corte_gnc_dia")
    )

    ingreso_combustible = litros_dia * eco.margen_por_litro * DIAS_DEL_MES
    ingreso_minimarket = compras_dia * eco.margen_compra * DIAS_DEL_MES

    costo_flete = r.prom("pedidos_dia") * DIAS_DEL_MES * eco.costo_pedido
    costo_almacenamiento = (
        r.prom("nivel_tanque_promedio") * eco.costo_almacenamiento_litro_mes
    )

    # Lo que se dejó de ganar: el combustible que no se vendió más las compras de
    # minimarket que esos clientes habrían hecho.
    venta_perdida = (
        r.prom("litros_no_vendidos_dia") * eco.margen_por_litro
        + perdidos_dia * p.prob_compra * eco.margen_compra
    ) * DIAS_DEL_MES

    costo_capacidad = (
        surtidores_extra * eco.operativo_surtidor_mensual
        + cajas_extra * eco.sueldo_cajero_mensual
    )

    ingreso_mensual = ingreso_combustible + ingreso_minimarket
    costo_inventario = costo_flete + costo_almacenamiento

    return {
        "litros_dia": litros_dia,
        "compras_dia": compras_dia,
        "perdidos_dia": perdidos_dia,
        "ingreso_combustible": ingreso_combustible,
        "ingreso_minimarket": ingreso_minimarket,
        "ingreso_mensual": ingreso_mensual,
        "costo_inventario": costo_inventario,
        "costo_capacidad": costo_capacidad,
        "venta_perdida": venta_perdida,
        "margen_operativo": ingreso_mensual - costo_inventario - costo_capacidad,
    }


def analizar_escenarios(
    resultados: list[ResultadoEscenario],
    eco: ParametrosEconomicos,
    p: ParametrosSimulacion,
) -> list[ResultadoEconomico]:
    """Calcula la economía de cada escenario de capacidad, contra el escenario Base."""
    base = buscar(resultados, "Base")
    numeros_base = _economia_de(base, eco, p, 0, 0)

    salida: list[ResultadoEconomico] = []
    for r in resultados:
        surtidores_extra = r.escenario.surtidores - base.escenario.surtidores
        cajas_extra = r.escenario.cajas - base.escenario.cajas
        n = _economia_de(r, eco, p, surtidores_extra, cajas_extra)

        inversion = surtidores_extra * eco.inversion_surtidor
        beneficio = n["margen_operativo"] - numeros_base["margen_operativo"]
        payback = inversion / beneficio if beneficio > 0 else None

        salida.append(
            ResultadoEconomico(
                nombre=r.escenario.nombre,
                descripcion=r.escenario.descripcion,
                surtidores=r.escenario.surtidores,
                cajas=r.escenario.cajas,
                surtidores_extra=surtidores_extra,
                cajas_extra=cajas_extra,
                litros_dia=n["litros_dia"],
                compras_dia=n["compras_dia"],
                perdidos_dia=n["perdidos_dia"],
                ingreso_combustible=n["ingreso_combustible"],
                ingreso_minimarket=n["ingreso_minimarket"],
                ingreso_mensual=n["ingreso_mensual"],
                costo_inventario=n["costo_inventario"],
                costo_capacidad=n["costo_capacidad"],
                venta_perdida=n["venta_perdida"],
                margen_operativo=n["margen_operativo"],
                ingreso_extra=n["ingreso_mensual"] - numeros_base["ingreso_mensual"],
                beneficio_neto=beneficio,
                inversion_inicial=inversion,
                payback_meses=payback,
            )
        )
    return salida


# =============================================================================
# Políticas de reposición
# =============================================================================
@dataclass(frozen=True)
class CostoPolitica:
    """Costo mensual de una política de reposición (punto de pedido, cantidad a pedir)."""

    punto_pedido: float
    cantidad_pedido: float

    pedidos_mes: float
    costo_pedidos: float
    nivel_promedio: float
    costo_almacenamiento: float
    litros_no_vendidos_mes: float
    costo_faltante: float
    costo_total: float

    nivel_servicio: float
    porcentaje_dias_quiebre: float
    litros_vendidos_mes: float
    margen_operativo: float

    @property
    def etiqueta(self) -> str:
        return f"s={self.punto_pedido:,.0f} / Q={self.cantidad_pedido:,.0f}"

    @property
    def cobertura_dias(self) -> float:
        """Cuántos días de venta cubre el punto de pedido."""
        venta_diaria = self.litros_vendidos_mes / DIAS_DEL_MES
        return self.punto_pedido / venta_diaria if venta_diaria else 0.0


def analizar_politicas(
    politicas: list[ResultadoPolitica],
    eco: ParametrosEconomicos,
    p: ParametrosSimulacion,
) -> list[CostoPolitica]:
    """Costo total mensual de cada política probada en el barrido."""
    salida: list[CostoPolitica] = []
    for pol in politicas:
        pedidos_mes = pol.prom("pedidos_dia") * DIAS_DEL_MES
        costo_pedidos = pedidos_mes * eco.costo_pedido
        nivel_promedio = pol.prom("nivel_tanque_promedio")
        costo_almacenamiento = nivel_promedio * eco.costo_almacenamiento_litro_mes

        litros_no_vendidos_mes = pol.prom("litros_no_vendidos_dia") * DIAS_DEL_MES
        perdidos_mes = (
            pol.prom("perdidos_cola_dia")
            + pol.prom("perdidos_sin_combustible_dia")
            + pol.prom("perdidos_cola_llena_dia")
        ) * DIAS_DEL_MES
        costo_faltante = (
            litros_no_vendidos_mes * eco.margen_por_litro
            + perdidos_mes * p.prob_compra * eco.margen_compra
        )

        litros_vendidos_mes = pol.prom("litros_vendidos_dia") * DIAS_DEL_MES
        ingreso = (
            litros_vendidos_mes * eco.margen_por_litro
            + pol.prom("compras_dia") * DIAS_DEL_MES * eco.margen_compra
        )

        salida.append(
            CostoPolitica(
                punto_pedido=pol.punto_pedido,
                cantidad_pedido=pol.cantidad_pedido,
                pedidos_mes=pedidos_mes,
                costo_pedidos=costo_pedidos,
                nivel_promedio=nivel_promedio,
                costo_almacenamiento=costo_almacenamiento,
                litros_no_vendidos_mes=litros_no_vendidos_mes,
                costo_faltante=costo_faltante,
                costo_total=costo_pedidos + costo_almacenamiento + costo_faltante,
                nivel_servicio=pol.prom("nivel_servicio"),
                porcentaje_dias_quiebre=pol.prom("porcentaje_dias_quiebre"),
                litros_vendidos_mes=litros_vendidos_mes,
                margen_operativo=ingreso - costo_pedidos - costo_almacenamiento,
            )
        )
    return salida


def analizar_politicas_real(
    barrido: ResultadoBarridoReal,
    eco: ParametrosEconomicos,
    p: ParametrosSimulacion,
) -> dict[str, list[CostoPolitica]]:
    """Costo mensual de la política (s, Q) de CADA tanque, punto por punto del barrido.

    El camión es independiente por producto (un flete por pedido de cada tanque), así que
    el costo de un tanque sale sólo de lo que pasa en ese tanque:
        costo = pedidos × flete + nivel promedio × $/L-mes + faltante,
    con faltante = litros que no se vendieron por falta de stock × margen por litro +
    clientes perdidos por falta de stock × prob. de compra × margen del minimarket.
    (El abandono por cola o por playero no depende de la política: no se imputa.)
    """
    salida: dict[str, list[CostoPolitica]] = {pr: [] for pr in barrido.productos}
    for punto in barrido.puntos:
        pedidos = promedio_por_producto(punto.replicas, "pedidos_por_producto")
        niveles = promedio_por_producto(punto.replicas, "nivel_por_producto")
        sin_stock = promedio_por_producto(punto.replicas, "litros_sin_stock_por_producto")
        perdidos = promedio_por_producto(punto.replicas, "perdidos_sin_stock_por_producto")
        vendidos = promedio_por_producto(punto.replicas, "litros_vendidos_por_producto")
        quiebre = promedio_por_producto(punto.replicas, "dias_quiebre_por_producto")
        for producto in barrido.productos:
            s_, q_ = punto.politicas[producto]
            pedidos_mes = pedidos[producto] * DIAS_DEL_MES
            costo_pedidos = pedidos_mes * eco.costo_pedido
            costo_almacenamiento = niveles[producto] * eco.costo_almacenamiento_litro_mes
            litros_perdidos_mes = sin_stock[producto] * DIAS_DEL_MES
            costo_faltante = (
                litros_perdidos_mes * eco.margen_por_litro
                + perdidos[producto] * DIAS_DEL_MES * p.prob_compra * eco.margen_compra
            )
            vendidos_mes = vendidos[producto] * DIAS_DEL_MES
            pedido_total = vendidos_mes + litros_perdidos_mes
            salida[producto].append(
                CostoPolitica(
                    punto_pedido=s_,
                    cantidad_pedido=q_,
                    pedidos_mes=pedidos_mes,
                    costo_pedidos=costo_pedidos,
                    nivel_promedio=niveles[producto],
                    costo_almacenamiento=costo_almacenamiento,
                    litros_no_vendidos_mes=litros_perdidos_mes,
                    costo_faltante=costo_faltante,
                    costo_total=costo_pedidos + costo_almacenamiento + costo_faltante,
                    nivel_servicio=vendidos_mes / pedido_total if pedido_total else 1.0,
                    porcentaje_dias_quiebre=quiebre[producto],
                    litros_vendidos_mes=vendidos_mes,
                    margen_operativo=(
                        vendidos_mes * eco.margen_por_litro
                        - costo_pedidos
                        - costo_almacenamiento
                    ),
                )
            )
    return salida


def ahorro_por_producto(costos: dict[str, list[CostoPolitica]]) -> dict[str, float]:
    """Cuánto baja el costo mensual de cada tanque al pasar de la política cargada (la
    primera del barrido) a la mejor. Nunca es negativo: la cargada también compite."""
    return {
        producto: lista[0].costo_total - min(c.costo_total for c in lista)
        for producto, lista in costos.items()
    }


def mejor_politica(costos: list[CostoPolitica]) -> CostoPolitica | None:
    """La política de menor costo total mensual."""
    return min(costos, key=lambda c: c.costo_total) if costos else None


# =============================================================================
# Recomendación final
# =============================================================================
def mejor_escenario(economia: list[ResultadoEconomico]) -> ResultadoEconomico | None:
    """El escenario de inversión con mayor beneficio neto mensual, si alguno conviene."""
    candidatos = [e for e in economia if not e.es_base and e.conviene]
    return max(candidatos, key=lambda e: e.beneficio_neto) if candidatos else None


def recomendacion(
    economia: list[ResultadoEconomico],
    resultados: list[ResultadoEscenario],
    costos_politicas: list[CostoPolitica] | None = None,
    politica_actual: CostoPolitica | None = None,
) -> dict[str, object]:
    """Arma la conclusión del TP a partir de los números.

    Compara las dos decisiones (capacidad de atención y política de reposición) con el
    mismo criterio, en pesos por mes, y dice cuál de las dos mueve más la aguja.
    """
    base_eco = next(e for e in economia if e.es_base)
    base_res = buscar(resultados, "Base")
    mejor_capacidad = mejor_escenario(economia)

    diagnostico: list[str] = []
    diagnostico.append(
        f"En la situación actual ({base_eco.surtidores} surtidores, {base_eco.cajas} caja/s) "
        f"la espera promedio es de {base_res.prom('espera_surtidor'):.1f} min, pero en la "
        f"hora pico trepa a {base_res.prom('espera_pico'):.1f} min. La utilización promedio "
        f"de los surtidores es del {base_res.prom('util_surtidores') * 100:.0f} %."
    )
    perdidos_cola = base_res.prom("perdidos_cola_dia")
    perdidos_nafta = base_res.prom("perdidos_sin_combustible_dia")
    diagnostico.append(
        f"Se pierden {perdidos_cola + perdidos_nafta:.1f} clientes por día: "
        f"{perdidos_cola:.1f} por cola larga y {perdidos_nafta:.1f} por falta de combustible. "
        f"En total son {pesos(base_eco.venta_perdida)} por mes de venta no realizada."
    )

    # ¿Cuál de los dos problemas es el grande?
    if perdidos_nafta > perdidos_cola * 1.5:
        cuello = "inventario"
        diagnostico.append(
            "El cuello de botella NO es la capacidad de atención sino el abastecimiento: "
            "se pierden más clientes por quedarse sin combustible que por hacer cola."
        )
    elif perdidos_cola > perdidos_nafta * 1.5:
        cuello = "capacidad"
        diagnostico.append(
            "El cuello de botella es la capacidad de atención: casi todos los clientes "
            "que se pierden lo hacen por la cola, no por falta de combustible."
        )
    else:
        cuello = "ambos"
        diagnostico.append(
            "Los dos problemas pesan parecido: hay que atacar la capacidad de atención y "
            "el abastecimiento a la vez."
        )

    acciones: list[str] = []

    # --- Decisión 1: capacidad ---
    if mejor_capacidad is None:
        veredicto_capacidad = (
            "No conviene agregar capacidad: ningún escenario cubre su costo."
        )
        acciones.append(veredicto_capacidad)
    else:
        elegido = buscar(resultados, mejor_capacidad.nombre)
        veredicto_capacidad = (
            f"Conviene el escenario {mejor_capacidad.nombre} ({mejor_capacidad.descripcion})"
        )
        acciones.append(
            f"{veredicto_capacidad}: baja la espera de la hora pico de "
            f"{base_res.prom('espera_pico'):.1f} a {elegido.prom('espera_pico'):.1f} min y deja "
            f"{pesos(mejor_capacidad.beneficio_neto)} por mes de beneficio neto. "
            f"Se repaga en {mejor_capacidad.payback_texto}."
        )
        base_ic = base_res.resumen["espera_pico"]
        mejor_ic = elegido.resumen["espera_pico"]
        if mejor_ic.ic_superior < base_ic.ic_inferior:
            acciones.append(
                "La mejora en la espera es estadísticamente significativa: los intervalos "
                "de confianza del 95 % no se superponen con los del escenario Base."
            )
        else:
            acciones.append(
                "Atención: los intervalos de confianza del 95 % se superponen con los del "
                "Base, así que con esta cantidad de réplicas la mejora podría ser azar."
            )

    # --- Decisión 2: política de inventario ---
    ahorro_inventario = 0.0
    if costos_politicas:
        mejor_pol = mejor_politica(costos_politicas)
        if mejor_pol is not None and politica_actual is not None:
            ahorro_inventario = politica_actual.costo_total - mejor_pol.costo_total
            if ahorro_inventario > 0:
                acciones.append(
                    f"Conviene cambiar la política de reposición a punto de pedido "
                    f"{mejor_pol.punto_pedido:,.0f} L y pedidos de {mejor_pol.cantidad_pedido:,.0f} L: "
                    f"ahorra {pesos(ahorro_inventario)} por mes y sube el nivel de servicio del "
                    f"{politica_actual.nivel_servicio * 100:.1f} % al {mejor_pol.nivel_servicio * 100:.1f} %. "
                    f"No requiere inversión."
                )
            else:
                acciones.append(
                    f"La política de reposición actual (punto de pedido "
                    f"{politica_actual.punto_pedido:,.0f} L, pedidos de "
                    f"{politica_actual.cantidad_pedido:,.0f} L) ya es la mejor de las probadas."
                )

    # --- Cuál de las dos decisiones rinde más ---
    beneficio_capacidad = mejor_capacidad.beneficio_neto if mejor_capacidad else 0.0
    if ahorro_inventario > beneficio_capacidad and ahorro_inventario > 0:
        veredicto = (
            "Primero corregir la política de reposición: rinde más que invertir en un "
            "surtidor y no cuesta nada."
        )
    elif beneficio_capacidad > 0:
        veredicto = f"Conviene invertir: escenario {mejor_capacidad.nombre}."
    elif ahorro_inventario > 0:
        veredicto = "No conviene invertir en capacidad, pero sí ajustar la reposición."
    else:
        veredicto = "Conviene quedarse como está: ninguna alternativa cubre su costo."

    return {
        "veredicto": veredicto,
        "cuello_de_botella": cuello,
        "conviene_invertir": mejor_capacidad is not None,
        "elegido": mejor_capacidad,
        "diagnostico": diagnostico,
        "acciones": acciones,
        "ahorro_inventario": ahorro_inventario,
        "beneficio_capacidad": beneficio_capacidad,
        "descartados": [
            f"{e.nombre} ({e.descripcion}): beneficio neto {pesos(e.beneficio_neto)}/mes"
            for e in economia
            if not e.es_base
            and (mejor_capacidad is None or e.nombre != mejor_capacidad.nombre)
        ],
    }
