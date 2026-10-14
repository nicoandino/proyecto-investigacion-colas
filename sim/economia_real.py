"""Economía de la estación real (Fase 8, ORQUESTADOR §7.9).

Todo se calcula **réplica por réplica** y recién después se promedia: así cada importe tiene su
IC 95 % y la diferencia entre escenarios se puede restar réplica a réplica (números aleatorios
comunes), igual que con los indicadores de colas.

    margen operativo mensual = ingresos − costos
        ingresos = margen de cada producto (L o m³) + margen del minimarket
        costos   = flete (fijo + $/km × km) + almacenamiento + personal

La **venta perdida es un costo de oportunidad**: se informa aparte, por motivo, y NO se resta del
margen (sería contarla dos veces: ya falta el ingreso de esos clientes).

Todos los importes salen de `ParametrosEconomicos` (Registro ECO-*); la mayoría es `heredado`
o `supuesto` y la app lo rotula. Estos pesos muestran **cómo se calcula**, no una conclusión
económica con datos propios (§12, prioridad 9).
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from sim.config import ParametrosEconomicos, ParametrosSimulacion, dias_del_mes
from sim.escenarios import es_significativa
from sim.red import camino_mas_corto
from sim.runner import ResultadoEscenario, ResultadoReplica, Resumen, resumen_de

#: Horas de un turno de trabajo: convierte "playeros × horas" en personas-turno.
HORAS_POR_TURNO = 8.0

#: Motivos de pérdida (§7.6) y el campo de `ResultadoReplica` con sus clientes por día.
MOTIVOS: tuple[tuple[str, str, str], ...] = (
    ("abandono_espera", "Abandonó la espera", "perdidos_cola_dia"),
    ("cola_llena", "Cola llena", "perdidos_cola_llena_dia"),
    ("sin_combustible", "Sin combustible", "perdidos_sin_combustible_dia"),
    ("corte_gnc", "Corte de GNC", "perdidos_corte_gnc_dia"),
    ("abandono_caja", "Dejó la caja", "perdidos_caja_dia"),
)


@dataclass(frozen=True)
class EconomiaMensual:
    """Los importes de UN mes de UNA réplica, en pesos."""

    dias_mes: int
    # Ingresos (margen bruto)
    ingreso_combustible: float       # nafta y diésel
    ingreso_gnc: float
    ingreso_minimarket: float
    ingreso_total: float
    # Costos
    flete: float
    almacenamiento: float
    personal_playeros: float
    personal_cajeros: float
    personal_encargado: float
    personal_tienda: float
    personal_total: float
    costo_total: float
    # Resultado
    margen_operativo: float
    # Costo de oportunidad (NO se resta del margen)
    vp_abandono_espera: float
    vp_cola_llena: float
    vp_sin_combustible: float
    vp_corte_gnc: float
    vp_abandono_caja: float
    venta_perdida_total: float
    # Por producto (no se resume entre réplicas; se promedia con `ingreso_por_producto`)
    ingreso_por_producto: tuple[tuple[str, float], ...] = ()


#: Campos numéricos de `EconomiaMensual` (todos menos los no numéricos).
CAMPOS: tuple[str, ...] = tuple(
    f.name for f in fields(EconomiaMensual) if f.name not in ("ingreso_por_producto",)
)


# =============================================================================
# Personal y flete
# =============================================================================
def personas_turno_playeros(p: ParametrosSimulacion) -> float:
    """Personas-turno de playeros por día: Σ (playeros del tramo × horas del tramo) ÷ 8 h.

    Sale de `p.turnos`, así que un refuerzo en el pico (S2) o −1 por turno (S9) cambian el costo.
    Es una aproximación por horas de dotación (no modela jornadas partidas).
    """
    tramos = sorted(p.turnos)
    total = 0.0
    for i, (hora, n) in enumerate(tramos):
        fin = tramos[i + 1][0] if i + 1 < len(tramos) else 24.0
        total += n * (fin - hora) / HORAS_POR_TURNO
    return total


def km_por_viaje(p: ParametrosSimulacion) -> float:
    """Kilómetros de ida y vuelta del camión desde el origen configurado (0 si no hay red)."""
    if p.red is None:
        return 0.0
    return 2.0 * camino_mas_corto(p.red).km


def flete_por_pedido(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> float:
    """Flete de un pedido: fijo + $/km × km de ida y vuelta (§7.9)."""
    return eco.costo_pedido + eco.flete_por_km * km_por_viaje(p)


# =============================================================================
# Una réplica
# =============================================================================
def economia_mensual(
    r: ResultadoReplica, p: ParametrosSimulacion, eco: ParametrosEconomicos
) -> EconomiaMensual:
    """Los importes de un mes de la réplica `r`, simulada con los parámetros `p`."""
    dias = dias_del_mes(p.fecha_inicio[0])

    # --- Ingresos: margen de cada producto (litros o m³ por día × días del mes)
    por_producto = tuple(
        (producto, vendido * dias * eco.margen_de(producto))
        for producto, vendido in r.litros_vendidos_por_producto
    )
    ingreso_gnc = sum(v for k, v in por_producto if k == "gnc")
    ingreso_combustible = sum(v for k, v in por_producto if k != "gnc")
    ingreso_minimarket = r.compras_dia * dias * eco.margen_compra
    ingreso_total = ingreso_combustible + ingreso_gnc + ingreso_minimarket

    # --- Costos
    pedidos_mes = sum(v for _, v in r.pedidos_por_producto) * dias
    flete = pedidos_mes * flete_por_pedido(p, eco)
    almacenamiento = sum(v for _, v in r.nivel_por_producto) * eco.costo_almacenamiento_litro_mes
    factor = eco.cobertura_francos
    personal_playeros = personas_turno_playeros(p) * factor * eco.sueldo_playero_mensual
    personal_cajeros = (
        p.cajas * (24.0 / HORAS_POR_TURNO) * factor * eco.sueldo_cajero_mensual
    )
    personal_encargado = eco.puestos_encargado * factor * eco.sueldo_encargado_mensual
    personal_tienda = eco.puestos_tienda * factor * eco.sueldo_cajero_mensual
    personal_total = personal_playeros + personal_cajeros + personal_encargado + personal_tienda
    costo_total = flete + almacenamiento + personal_total

    # --- Venta perdida por motivo (costo de oportunidad): cliente líquido típico =
    # litros medios × margen + probabilidad de compra × margen del minimarket.
    valor_cliente = (
        p.litros_medios_por_cliente * eco.margen_por_litro + p.prob_compra * eco.margen_compra
    )
    # El GNC que no se vendió POR EL CORTE (los clientes de GNC que se cansan de esperar al playero o al
    # compresor van con su motivo, como cualquier cliente).
    m3_corte = next((c[4] for c in r.litros_perdidos_causa if c[0] == "gnc"), None)
    m3_corte_dia = (
        m3_corte / max(r.dias_medidos, 1) if m3_corte is not None else r.m3_gnc_perdidos_dia
    )
    perdidas: dict[str, float] = {}
    for clave, _, campo in MOTIVOS:
        clientes = float(getattr(r, campo)) * dias
        if clave == "abandono_caja":
            perdidas[clave] = clientes * eco.margen_compra       # ya cargó: sólo falta la compra
        elif clave == "corte_gnc":
            perdidas[clave] = (
                m3_corte_dia * dias * eco.margen_gnc
                + clientes * p.prob_compra * eco.margen_compra
            )
        else:
            perdidas[clave] = clientes * valor_cliente

    return EconomiaMensual(
        dias_mes=dias,
        ingreso_combustible=ingreso_combustible,
        ingreso_gnc=ingreso_gnc,
        ingreso_minimarket=ingreso_minimarket,
        ingreso_total=ingreso_total,
        flete=flete,
        almacenamiento=almacenamiento,
        personal_playeros=personal_playeros,
        personal_cajeros=personal_cajeros,
        personal_encargado=personal_encargado,
        personal_tienda=personal_tienda,
        personal_total=personal_total,
        costo_total=costo_total,
        margen_operativo=ingreso_total - costo_total,
        vp_abandono_espera=perdidas["abandono_espera"],
        vp_cola_llena=perdidas["cola_llena"],
        vp_sin_combustible=perdidas["sin_combustible"],
        vp_corte_gnc=perdidas["corte_gnc"],
        vp_abandono_caja=perdidas["abandono_caja"],
        venta_perdida_total=sum(perdidas.values()),
        ingreso_por_producto=por_producto,
    )


# =============================================================================
# Un escenario (varias réplicas)
# =============================================================================
def economia_de(resultado: ResultadoEscenario, eco: ParametrosEconomicos) -> list[EconomiaMensual]:
    """La economía mensual de cada réplica de un escenario (con SUS parámetros)."""
    return [economia_mensual(r, resultado.parametros, eco) for r in resultado.replicas]


def resumir_economia(lista: list[EconomiaMensual]) -> dict[str, Resumen]:
    """Promedio e IC 95 % de cada importe a lo largo de las réplicas."""
    return {c: resumen_de([float(getattr(e, c)) for e in lista]) for c in CAMPOS}


def ingreso_promedio_por_producto(lista: list[EconomiaMensual]) -> dict[str, float]:
    """Margen mensual promedio de cada producto."""
    acumulado: dict[str, float] = {}
    for e in lista:
        for producto, v in e.ingreso_por_producto:
            acumulado[producto] = acumulado.get(producto, 0.0) + v
    return {k: v / len(lista) for k, v in acumulado.items()}


def diferencia_economia(
    base: list[EconomiaMensual], otra: list[EconomiaMensual], campo: str
) -> Resumen:
    """(otra − base) réplica a réplica, con su IC 95 % (números aleatorios comunes)."""
    pares = zip(base, otra, strict=True)
    return resumen_de([float(getattr(o, campo)) - float(getattr(b, campo)) for b, o in pares])


def margen_de_equilibrio_por_litro(e: EconomiaMensual, eco: ParametrosEconomicos) -> float:
    """Margen por litro que haría que el margen operativo del mes sea 0 (con lo demás igual).

    Es el número que más le dice al grupo: si es muy distinto de ECO-01 ($100/L, heredado), la
    conclusión económica depende de un dato que hoy no tenemos.
    """
    # Litros vendidos = ingreso de cada producto ÷ su margen (con márgenes por producto, cada uno el suyo).
    litros = sum(v / eco.margen_de(k) for k, v in e.ingreso_por_producto if k != "gnc" and eco.margen_de(k))
    if litros <= 0:
        return float("nan")
    return (e.costo_total - e.ingreso_gnc - e.ingreso_minimarket) / litros


# =============================================================================
# Anualización (ECO-09)
# =============================================================================
def anualizar(
    estaciones: list[ResultadoEscenario], eco: ParametrosEconomicos
) -> dict[str, Resumen]:
    """Año estimado = 3 × Σ de los 4 meses representativos (ECO-09), réplica a réplica.

    Cada réplica k arma su propio año (3 × la suma de sus 4 meses): las réplicas son
    independientes entre sí, así que el IC 95 % del año es válido aunque dentro de una réplica
    los meses compartan semilla. Es una **estimación**, no un año simulado.
    """
    por_mes = [economia_de(r, eco) for r in estaciones]
    n = len(por_mes[0])
    return {
        c: resumen_de([3.0 * sum(float(getattr(mes[k], c)) for mes in por_mes) for k in range(n)])
        for c in CAMPOS
    }


# =============================================================================
# Conclusión por pregunta del CASO (§7.7)
# =============================================================================
@dataclass(frozen=True)
class ConclusionEscenario:
    """Qué le hace un escenario al margen mensual de la estación, contra S0."""

    id: str
    nombre: str
    pregunta: str
    d_margen: Resumen              # Δ margen operativo mensual (pesos)
    d_personal: Resumen            # Δ costo de personal
    d_ingreso: Resumen             # Δ ingresos
    d_venta_perdida: Resumen       # Δ venta perdida (informativa)

    @property
    def significativa(self) -> bool:
        return es_significativa(self.d_margen)

    @property
    def veredicto(self) -> str:
        """'suma margen' · 'resta margen' · 'no se distingue' (según el IC 95 % de la diferencia)."""
        if not self.significativa:
            return "no se distingue"
        return "suma margen" if self.d_margen.promedio > 0 else "resta margen"


def conclusiones(
    resultados: list[ResultadoEscenario], eco: ParametrosEconomicos
) -> list[ConclusionEscenario]:
    """Δ de margen, personal, ingresos y venta perdida de cada escenario contra el primero (S0)."""
    base = economia_de(resultados[0], eco)
    salida = []
    for r in resultados[1:]:
        otro = economia_de(r, eco)
        salida.append(
            ConclusionEscenario(
                id=r.escenario.id,
                nombre=r.escenario.nombre,
                pregunta=r.escenario.pregunta,
                d_margen=diferencia_economia(base, otro, "margen_operativo"),
                d_personal=diferencia_economia(base, otro, "personal_total"),
                d_ingreso=diferencia_economia(base, otro, "ingreso_total"),
                d_venta_perdida=diferencia_economia(base, otro, "venta_perdida_total"),
            )
        )
    return salida


def decision_s6(
    resultados: list[ResultadoEscenario], eco: ParametrosEconomicos
) -> dict[str, object] | None:
    """S6: ¿un playero más en el pico (S2 +1) o más stock (S6)? Se mide en $/mes.

    Devuelve los dos Δ de margen y la diferencia pareada entre ellos (playero − stock);
    `None` si alguno de los dos no se corrió.
    """
    por_nombre = {r.escenario.nombre: r for r in resultados}
    playero = por_nombre.get("S2 · Playeros en el pico +1")
    stock = por_nombre.get("S6 · Stock extra (s × 1,5)")
    if playero is None or stock is None:
        return None
    base = economia_de(resultados[0], eco)
    e_playero, e_stock = economia_de(playero, eco), economia_de(stock, eco)
    d_playero = diferencia_economia(base, e_playero, "margen_operativo")
    d_stock = diferencia_economia(base, e_stock, "margen_operativo")
    directa = diferencia_economia(e_stock, e_playero, "margen_operativo")   # playero − stock
    if not es_significativa(directa):
        mejor = "empate (la diferencia entre las dos no se distingue del azar)"
    else:
        mejor = "el playero extra" if directa.promedio > 0 else "el stock extra"
    return {
        "d_playero": d_playero,
        "d_stock": d_stock,
        "playero_menos_stock": directa,
        "mejor": mejor,
        "costo_playero": diferencia_economia(base, e_playero, "personal_total"),
    }


# =============================================================================
# Avisos que la app debe mostrar
# =============================================================================
def avisos(p: ParametrosSimulacion, eco: ParametrosEconomicos) -> list[str]:
    """Advertencias de la economía (textos sin formato de pesos; la app los escapa)."""
    lista = [
        "Los márgenes por litro, por m³ de GNC y por compra (ECO-01/02/03) son placeholders "
        "heredados del proyecto hipotético, sin fuente: estos pesos muestran cómo se calcula, "
        "no son una conclusión económica con datos propios.",
        "El costo de personal usa los sueldos de FECRA con adicionales (ECO-04, la URL dice "
        "enero-2026) y un factor de francos supuesto (ECO-10): cubrir 24 h los 7 días "
        "necesita más personas que puestos.",
    ]
    if p.red is not None and p.red.origen == "DOCK" and eco.flete_por_km == 0:
        lista.append(
            f"El flete es un fijo de ${eco.costo_pedido:,.0f} por viaje y $0 por km (ECO-06): con "
            f"origen Dock Sud el camión hace ≈ {km_por_viaje(p):,.0f} km de ida y vuelta, así que "
            "el flete está casi seguro subestimado. Consultar transportistas."
        )
    return lista
