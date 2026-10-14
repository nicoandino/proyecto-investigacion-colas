"""Parámetros del modelo, escenarios y datos económicos.

Toda la configuración vive acá, en dataclasses inmutables (`frozen=True`), para que
una corrida quede descrita por un único objeto que se puede imprimir y guardar.

Convenciones (ver CLAUDE.md):
  - Tiempo en MINUTOS. El día tiene 1440 minutos y la corrida dura varios días.
  - Volumen en LITROS.
  - Dinero en PESOS ($).
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, replace
from datetime import date, timedelta
from functools import cached_property

from sim.datos import valor

MINUTOS_POR_DIA = 1440
HORAS_POR_DIA = 24
#: Año de referencia del calendario: `fecha_inicio` y los días simulados viven acá (B2).
ANO_REFERENCIA = 2026


@dataclass(frozen=True)
class Triangular:
    """Distribución triangular: valor mínimo, más probable (moda) y máximo.

    Se usa para tiempos de servicio y para los litros cargados porque es la distribución
    típica cuando no hay datos históricos y sólo se puede estimar "entre tanto y tanto,
    lo más común es X".
    """

    minimo: float
    moda: float
    maximo: float

    def __post_init__(self) -> None:
        if not (self.minimo <= self.moda <= self.maximo):
            raise ValueError(
                f"Triangular inválida: debe cumplirse mínimo <= moda <= máximo "
                f"(recibido {self.minimo}, {self.moda}, {self.maximo})"
            )

    @property
    def media(self) -> float:
        """Media teórica de la triangular = (a + m + b) / 3."""
        return (self.minimo + self.moda + self.maximo) / 3.0


# =============================================================================
# Demanda: perfil horario + tabla empírica de autos por día
# =============================================================================
@dataclass(frozen=True)
class PerfilHorario:
    """Cómo se reparte la demanda de un día entre las 24 horas.

    Son factores de intensidad relativos: el 2.0 de las 8 de la mañana significa que a esa
    hora llega el doble de autos que en una hora de factor 1.0. Lo que importa es la
    proporción entre ellos, no su valor absoluto.

    Esto reemplaza al supuesto de "tasa de llegada constante", que es falso en una estación
    de servicio: hay pico de mañana, valle al mediodía y pico a la tarde.
    """

    factores: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.factores) != HORAS_POR_DIA:
            raise ValueError(f"El perfil tiene que tener {HORAS_POR_DIA} factores.")
        if any(f < 0 for f in self.factores):
            raise ValueError("Los factores del perfil no pueden ser negativos.")
        if sum(self.factores) <= 0:
            raise ValueError("El perfil no puede ser todo ceros.")

    # Estos tres se calculan una sola vez por perfil: el motor los consulta en cada
    # llegada y recalcularlos cada vez hacía notablemente más lenta la corrida.
    @cached_property
    def total(self) -> float:
        return sum(self.factores)

    @cached_property
    def fracciones(self) -> tuple[float, ...]:
        """Qué fracción de los autos del día llega en cada hora (suma 1)."""
        total = self.total
        return tuple(f / total for f in self.factores)

    @cached_property
    def factor_maximo(self) -> float:
        return max(self.factores)

    def hora_pico(self) -> int:
        return self.factores.index(self.factor_maximo)

    def tasa(self, minuto: float, autos_del_dia: float) -> float:
        """Tasa de llegada λ (autos por minuto) en ese minuto del día."""
        hora = int((minuto % MINUTOS_POR_DIA) // 60)
        return autos_del_dia * self.fracciones[hora] / 60.0

    def tasas_por_hora(self, autos_del_dia: float) -> tuple[float, ...]:
        """λ de cada una de las 24 horas, en autos por minuto."""
        return tuple(autos_del_dia * f / 60.0 for f in self.fracciones)

    def tasa_maxima(self, autos_del_dia: float) -> float:
        """La λ de la hora pico. Sirve para calcular ρ en el peor momento del día."""
        return autos_del_dia * (self.factor_maximo / self.total) / 60.0


#: Perfil típico de una estación de servicio abierta las 24 horas (heredado; la
#: alternativa adoptada para el caso real es DEM-02 en el Registro).
PERFIL_TIPICO = PerfilHorario(
    (
        # 00    01    02    03    04    05    06    07    08    09    10    11
        0.30, 0.20, 0.15, 0.15, 0.25, 0.60, 1.10, 1.80, 2.00, 1.50, 1.10, 1.00,
        # 12    13    14    15    16    17    18    19    20    21    22    23
        1.20, 1.10, 0.90, 0.90, 1.00, 1.40, 1.90, 2.00, 1.60, 1.10, 0.70, 0.40,
    )
)


@dataclass(frozen=True)
class DemandaDiaria:
    """Tabla de frecuencias empírica de autos por día.

    Es el método de simulación Monte Carlo tal como se ve en la materia:

        Paso 1: distribución de probabilidad a partir de las frecuencias observadas.
        Paso 2: probabilidad acumulada.
        Paso 3: intervalos de números aleatorios (01 a 00).
        Paso 4: generar un número aleatorio.
        Paso 5: leer en qué intervalo cae y así sortear la demanda del día.

    No se supone una distribución teórica: se usa directamente la que se observó.
    """

    valores: tuple[int, ...]        # autos por día observados
    frecuencias: tuple[int, ...]    # en cuántos días se observó cada valor

    def __post_init__(self) -> None:
        if len(self.valores) != len(self.frecuencias):
            raise ValueError("Valores y frecuencias tienen que tener la misma cantidad.")
        if not self.valores:
            raise ValueError("La tabla de demanda no puede estar vacía.")
        if any(f < 0 for f in self.frecuencias):
            raise ValueError("Las frecuencias no pueden ser negativas.")
        if sum(self.frecuencias) <= 0:
            raise ValueError("La suma de las frecuencias tiene que ser positiva.")
        if any(v < 0 for v in self.valores):
            raise ValueError("Los autos por día no pueden ser negativos.")

    @property
    def total_observaciones(self) -> int:
        return sum(self.frecuencias)

    @property
    def probabilidades(self) -> tuple[float, ...]:
        """Paso 1: frecuencia / total."""
        total = self.total_observaciones
        return tuple(f / total for f in self.frecuencias)

    @property
    def acumuladas(self) -> tuple[float, ...]:
        """Paso 2: probabilidad acumulada."""
        acumulado = 0.0
        salida = []
        for p in self.probabilidades:
            acumulado += p
            salida.append(acumulado)
        # El último tiene que dar exactamente 1 aunque se arrastren errores de redondeo.
        salida[-1] = 1.0
        return tuple(salida)

    @property
    def intervalos(self) -> tuple[tuple[int, int], ...]:
        """Paso 3: intervalos de números aleatorios de 01 a 00 (donde 00 vale 100)."""
        salida = []
        desde = 1
        for acumulada in self.acumuladas:
            hasta = round(acumulada * 100)
            salida.append((desde, hasta))
            desde = hasta + 1
        return tuple(salida)

    def intervalo_texto(self, i: int) -> str:
        """El intervalo i escrito como en el apunte: '01 a 10', y '00' en lugar de 100."""
        desde, hasta = self.intervalos[i]
        fin = "00" if hasta >= 100 else f"{hasta:02d}"
        return f"{desde:02d} a {fin}"

    @property
    def media(self) -> float:
        """Autos por día promedio según la tabla."""
        return sum(v * p for v, p in zip(self.valores, self.probabilidades))

    def sortear(self, aleatorio_0_1: float) -> int:
        """Paso 5: dado un número aleatorio en [0, 1), devuelve los autos de ese día."""
        for valor, acumulada in zip(self.valores, self.acumuladas):
            if aleatorio_0_1 < acumulada:
                return valor
        return self.valores[-1]


#: Tabla observada de autos por día (100 días de registro).
DEMANDA_TIPICA = DemandaDiaria(
    valores=(280, 320, 360, 400, 440),
    frecuencias=(10, 20, 40, 20, 10),
)


# =============================================================================
# La estación real: productos, grupos, vehículos e inventario por producto (§7)
# =============================================================================
@dataclass(frozen=True)
class Producto:
    """Un producto que se despacha en la estación (ORQUESTADOR §7.2)."""

    id: str                    # "super" | "vpower" | "diesel_g2" | "diesel_g3" | "gnc"
    nombre: str                # nombre para mostrar
    grupo: str                 # "A" nafta · "B" diésel · "C" GNC
    pct_litros: float          # participación en los LITROS de líquidos (DEM-04)
    carga_media: float         # litros (o m³) medios por cliente (cadena §14.2)
    es_gnc: bool = False


@dataclass(frozen=True)
class Grupo:
    """Una zona de surtidores con sus caras (SUR-01..04)."""

    id: str                    # "A" | "B" | "C"
    nombre: str
    caras: int                 # una cara = un vehículo a la vez
    productos: tuple[str, ...]
    requiere_playero: bool = True   # PER-04: el GNC sólo conecta la manguera


@dataclass(frozen=True)
class TipoVehiculo:
    """Un tipo de vehículo con su tanque y su distribución de litros por carga (§5-D)."""

    id: str                    # "moto" | "auto" | "pick_up" | "camion" | "auto_gnc"
    nombre: str
    tanque: float              # litros (o m³ del cilindro para el GNC)
    litros: Triangular         # Triangular(0,20·T ; 0,30·T ; 1,00·T) — media 0,50·T
    es_camion: bool = False    # TIE-03: suma litros ÷ 90 al tiempo de servicio
    es_moto: bool = False
    es_gnc: bool = False       # el cilindro se mide en m³, no en litros


@dataclass(frozen=True)
class InventarioProducto:
    """Tanque y política (s, Q) de UN producto líquido (INV-03/INV-07/INV-01)."""

    producto: str
    capacidad: float
    nivel_inicial: float
    punto_pedido: float
    cantidad_pedido: float
    plazo_entrega: Triangular      # HORAS

    @property
    def plazo_entrega_minutos(self) -> Triangular:
        return Triangular(
            self.plazo_entrega.minimo * 60.0,
            self.plazo_entrega.moda * 60.0,
            self.plazo_entrega.maximo * 60.0,
        )


#: Orden de los tipos en la matriz tipo-por-producto (VEH-00 del Registro).
_TIPOS_MATRIZ = ("moto", "auto", "pick_up", "camion")


def _tipo_desde(id_tipo: str, dato_id: str, es_camion: bool = False,
                es_moto: bool = False, es_gnc: bool = False) -> TipoVehiculo:
    """TipoVehiculo desde un VEH-0x del Registro: (tanque, (mín, moda, máx))."""
    tanque, _ = valor(dato_id)
    if es_gnc:
        _, carga = valor(dato_id)                       # m³ del cilindro
        return TipoVehiculo(id_tipo, "", tanque, Triangular(*carga),
                            es_camion=es_camion, es_moto=es_moto, es_gnc=True)
    return TipoVehiculo(
        id_tipo, "", tanque, Triangular(0.20 * tanque, 0.30 * tanque, 1.00 * tanque),
        es_camion=es_camion, es_moto=es_moto,
    )


def tipos_vehiculo_desde_registro() -> tuple[TipoVehiculo, ...]:
    """Los cinco tipos de vehículo (§5-D), con la regla de carga 0,20/0,30/1,00 × tanque."""
    return (
        _tipo_desde("moto", "VEH-03", es_moto=True),        # moto 110 cc, 3,7 L
        _tipo_desde("auto", "VEH-01"),                      # auto, 47 L
        _tipo_desde("pick_up", "VEH-02"),                   # pick-up / utilitario, 80 L
        _tipo_desde("camion", "VEH-04", es_camion=True),    # camión, 300 L (supuesto)
        _tipo_desde("auto_gnc", "VEH-05", es_gnc=True),     # auto GNC, cilindro 14 m³
    )


def matriz_tipo_por_producto() -> tuple[tuple[str, tuple[float, ...]], ...]:
    """Matriz tipo de vehículo por producto (VEH-00), en orden (moto, auto, pick-up, camión)."""
    return valor("VEH-00")


def productos_desde_registro() -> tuple[Producto, ...]:
    """Los cinco productos: mezcla en litros (DEM-04) + carga media derivada (§14.2).

    La carga media de cada producto sale de la matriz tipo-por-producto × la media
    de litros de cada tipo: Súper 21,4 · V-Power 26,0 · G2 64,2 · G3 81,5 · GNC 7 m³.
    """
    mezcla = dict(valor("DEM-04"))
    tipos = {t.id: t for t in tipos_vehiculo_desde_registro()}
    matriz = dict(matriz_tipo_por_producto())
    salida = []
    for id_, nombre, grupo in (
        ("super", "Súper", "A"),
        ("vpower", "V-Power", "A"),
        ("diesel_g2", "Diésel G2", "B"),
        ("diesel_g3", "Diésel G3", "B"),
    ):
        cargas = matriz[id_]
        media = sum(
            p * tipos[tipo].litros.media for tipo, p in zip(_TIPOS_MATRIZ, cargas)
        )
        salida.append(Producto(id_, nombre, grupo, mezcla[id_] / 100.0, media))
    salida.append(Producto("gnc", "GNC", "C", 0.0, 7.0, es_gnc=True))
    return tuple(salida)


def turnos_de(playeros: tuple[int, int, int]) -> tuple[tuple[float, int], ...]:
    """(hora de inicio, playeros) de los turnos a partir de (noche, mañana, tarde).

    Noche 22–06, mañana 06–14, tarde 14–22 (PER-01): a las 22 vuelve a entrar la noche,
    así que el día se parte en cuatro tramos.
    """
    noche, manana, tarde = playeros
    return ((0.0, noche), (6.0, manana), (14.0, tarde), (22.0, noche))


def turnos_con_refuerzo(
    playeros: tuple[int, int, int],
    refuerzo: tuple[tuple[float, float, int], ...],
) -> tuple[tuple[float, int], ...]:
    """Los turnos de `turnos_de` más un refuerzo `((desde_h, hasta_h, extra), …)` (S2, §7.2).

    `extra` puede ser negativo (sacar un playero en el pico); siempre queda al menos 1.
    Los tramos contiguos con la misma dotación se funden (salvo en los bordes de los turnos).
    """
    base = turnos_de(playeros)
    cortes = sorted({h for h, _ in base} | {d for d, _, _ in refuerzo} | {h for _, h, _ in refuerzo})
    cortes = [c for c in cortes if 0.0 <= c < 24.0]
    tramos: list[tuple[float, int]] = []
    for desde in cortes:
        vigente = [n for h, n in base if h <= desde][-1]
        extra = sum(e for d, h, e in refuerzo if d <= desde < h)
        n = max(1, vigente + extra)
        if not tramos or tramos[-1][1] != n or desde in {h for h, _ in base}:
            tramos.append((float(desde), n))
    return tuple(tramos)


def grupos_desde_registro() -> tuple[Grupo, ...]:
    """Las tres zonas: A nafta 4 caras · B diésel 2 · C GNC 6 (SUR-02..04)."""
    return (
        Grupo("A", "Nafta", 4, ("super", "vpower"), requiere_playero=True),
        Grupo("B", "Diésel", 2, ("diesel_g2", "diesel_g3"), requiere_playero=True),
        Grupo("C", "GNC", 6, ("gnc",), requiere_playero=False),
    )


def inventario_real(
    litros_mes: float = 270_000.0,
    capacidad: float | None = None,
    plazo: Triangular | None = None,
    nivel_inicial_pct: float | None = None,
) -> tuple[InventarioProducto, ...]:
    """Tanque y política (s, Q) por producto líquido (INV-03, INV-07, INV-01).

    INV-07: s = 1,5 días de consumo del producto;
    Q = min(capacidad − s, máx(2,5 × consumo/día, 0,5 × capacidad)); nivel inicial 75 %.
    Los argumentos opcionales reemplazan al Registro (la interfaz los usa para que el
    usuario pruebe otra capacidad, otro plazo o otro nivel inicial).
    """
    capacidad = valor("INV-03") if capacidad is None else capacidad
    plazo = Triangular(*valor("INV-01")) if plazo is None else plazo
    nivel_inicial_pct = valor("INV-10") if nivel_inicial_pct is None else nivel_inicial_pct
    salida = []
    for p in productos_desde_registro():
        if p.es_gnc:
            continue
        consumo_dia = (litros_mes / 30.0) * p.pct_litros
        s = min(1.5 * consumo_dia, capacidad)
        q = min(capacidad - s, max(2.5 * consumo_dia, 0.5 * capacidad))
        salida.append(
            InventarioProducto(
                producto=p.id,
                capacidad=capacidad,
                nivel_inicial=nivel_inicial_pct * capacidad,
                punto_pedido=s,
                cantidad_pedido=q,
                plazo_entrega=plazo,
            )
        )
    return tuple(salida)


# =============================================================================
# Red de abastecimiento: arcos, cortes y escenario (algoritmos en sim/red.py)
# =============================================================================
@dataclass(frozen=True)
class Arco:
    """Un tramo de ruta entre dos nodos (se recorre en los dos sentidos)."""

    a: str
    b: str
    km: float
    ruta: str
    cortable: bool = False


@dataclass(frozen=True)
class CorteRuta:
    """Un corte forzado (E1–E4): qué arcos cierra, cuánto dura y qué demora fija agrega."""

    id: str
    nombre: str
    arcos: tuple[tuple[str, str], ...]
    duracion: Triangular                  # HORAS
    demora_fija_min: float = 0.0          # obra: minutos extra por viaje
    franja: tuple[float, float] | None = None   # horas del día en que rige la obra


#: (a, b, ruta, cortable) en el orden de RED-01..RED-10 del Registro.
_ARCOS_REGISTRO = (
    ("RED-01", "LUJAN", "PAREDITAS", "RN 40", True),
    ("RED-02", "PAREDITAS", "SANRAFAEL", "RN 143", True),
    ("RED-03", "PAREDITAS", "SOSNEADO", "RN 40", True),
    ("RED-04", "SOSNEADO", "SANRAFAEL", "RN 144", True),
    ("RED-05", "ALVEAR", "SANRAFAEL", "RN 143 este", True),
    ("RED-06", "SANRAFAEL", "MONTECOMAN", "RN 146", False),
    ("RED-07", "MONTECOMAN", "LAPAZ", "RP 153", False),
    ("RED-08", "LAPAZ", "LUJAN", "RN 7", False),
    ("RED-09", "DOCK", "ALVEAR", "ruta sin verificar", False),
    ("RED-10", "DOCK", "LUJAN", "ruta sin verificar", False),
)


def arcos_desde_registro() -> tuple[Arco, ...]:
    """Los 10 arcos de la red (nota 06 §1.2–1.3)."""
    return tuple(Arco(a, b, valor(id_), ruta, cortable)
                 for id_, a, b, ruta, cortable in _ARCOS_REGISTRO)


def cortes_desde_registro() -> tuple[CorteRuta, ...]:
    """Los cortes forzados E1–E4 (RED-15)."""
    return tuple(
        CorteRuta(id_, nombre, tuple(arcos), Triangular(*dur), demora, franja)
        for id_, nombre, arcos, dur, demora, franja in valor("RED-15")
    )


#: Nombre del origen en INV-05 → nodo de la red.
_NODO_DE_ORIGEN = {"Dock Sud": "DOCK", "Luján de Cuyo": "LUJAN"}


@dataclass(frozen=True)
class ParametrosRed:
    """De dónde sale el camión, por qué rutas llega y qué cortes puede encontrar."""

    arcos: tuple[Arco, ...] = arcos_desde_registro()
    origen: str = _NODO_DE_ORIGEN[valor("INV-05")]      # "DOCK" | "LUJAN"
    destino: str = "SANRAFAEL"
    velocidad_kmh: float = valor("RED-11")              # supuesto: 70 km/h
    escenario_corte: str = valor("RED-12")              # ninguno · aleatorio · E1..E4
    cortes: tuple[CorteRuta, ...] = cortes_desde_registro()
    corte_dia: int = valor("RED-16")                    # día en que arranca un corte forzado
    prob_corte_viaje: float = valor("RED-13")           # sólo en meses con cortes
    duracion_aleatoria: Triangular = Triangular(*valor("RED-14"))
    meses_corte: tuple[int, ...] = valor("RED-17")

    def __post_init__(self) -> None:
        nodos = {n for a in self.arcos for n in (a.a, a.b)}
        if self.origen not in nodos or self.destino not in nodos:
            raise ValueError("El origen y el destino tienen que ser nodos de la red.")
        if self.velocidad_kmh <= 0:
            raise ValueError("La velocidad del camión tiene que ser positiva.")
        if not 0.0 <= self.prob_corte_viaje <= 1.0:
            raise ValueError("La probabilidad de corte tiene que estar entre 0 y 1.")
        validos = {"ninguno", "aleatorio", *(c.id for c in self.cortes)}
        if self.escenario_corte not in validos:
            raise ValueError(f"Escenario de corte desconocido: {self.escenario_corte}.")


# =============================================================================
# GNC: contrato, episodios de corte invernales, compresores y migración (sim/gnc.py)
# =============================================================================
@dataclass(frozen=True)
class ParametrosGNC:
    """El GNC de la estación: cuándo se corta, cuántos compresores hay y adónde van los clientes.

    El corte es TOTAL y por episodios de varios días (no un "−50 %"); sólo lo sufre una
    estación con contrato interrumpible. `carga_m3` del cliente GNC sale del tipo de
    vehículo `auto_gnc` (cilindro de 14 m³, VEH-05) y el tiempo de carga de `carga_gnc`.
    """

    contrato: str = valor("GNC-01")                  # "interrumpible" | "firme"
    episodios: int = valor("GNC-02")                 # episodios por invierno
    dias_por_episodio: int = valor("GNC-06")
    forma: str = valor("GNC-03")                     # "total_24h" | "ventana" | "parcial_50"
    compresores: int = valor("SUR-06")               # cargas simultáneas posibles
    migracion_a_nafta: float = valor("GNC-04")       # prob. de pasarse a Súper durante el corte
    episodios_en_horizonte: bool = valor("GNC-07")   # herramienta: forzar el corte adentro
    # "Pueden ocurrir más cortes en todo el invierno" (menú, tanda 4): apagado por defecto. Los valores del
    # Registro (GNC-08/09/10) son los que pone el menú al elegir esa opción.
    cortes_extra: int = 0                            # episodios que se suman a los habituales
    prob_invierno_frio: float = 0.0                  # prob. de que un corte se alargue
    dias_extra_frio: int = 0                         # días que se alarga

    def __post_init__(self) -> None:
        if self.contrato not in ("interrumpible", "firme"):
            raise ValueError("contrato tiene que ser 'interrumpible' o 'firme'.")
        if self.forma not in ("total_24h", "ventana", "parcial_50"):
            raise ValueError("forma tiene que ser 'total_24h', 'ventana' o 'parcial_50'.")
        if self.episodios < 0 or self.dias_por_episodio < 1 or self.compresores < 1:
            raise ValueError("episodios ≥ 0, días por episodio ≥ 1 y compresores ≥ 1.")
        if not 0.0 <= self.migracion_a_nafta <= 1.0:
            raise ValueError("migracion_a_nafta tiene que estar entre 0 y 1.")
        if self.cortes_extra < 0 or self.dias_extra_frio < 0 or not 0.0 <= self.prob_invierno_frio <= 1.0:
            raise ValueError("cortes_extra y dias_extra_frio ≥ 0; prob_invierno_frio entre 0 y 1.")


#: Los cinco productos de la estación real.
PRODUCTOS_REALES = productos_desde_registro()
#: Las tres zonas de surtidores.
GRUPOS_REALES = grupos_desde_registro()
#: Los cinco tipos de vehículo.
TIPOS_REALES = tipos_vehiculo_desde_registro()
#: Inventario por producto (para la demanda por defecto de 270.000 L/mes).
INVENTARIO_REAL = inventario_real()


# =============================================================================
# Inventario: el tanque de combustible
# =============================================================================
@dataclass(frozen=True)
class ParametrosTanque:
    """Tanque de combustible y política de reposición (punto de pedido, cantidad a pedir).

    Cuando el nivel cae por debajo del punto de pedido se emite un pedido al camión
    cisterna, que tarda un plazo de entrega aleatorio en llegar. Si mientras tanto el
    tanque se vacía, la estación no puede atender: no se pierde un cliente, se pierden
    todos los que llegan hasta que el camión descargue.

    Los defaults salen del Registro (INV-03/INV-10/INV-07/INV-01, §5.1-b).
    """

    capacidad: float = valor("INV-03")                              # litros (20.000)
    nivel_inicial: float = valor("INV-10") * valor("INV-03")        # 75 % de la capacidad
    punto_pedido: float = valor("INV-07")[0]                        # 1,5 días de consumo
    cantidad_pedido: float = valor("INV-07")[1]                     # INV-07: Q = min(cap−s, …)
    plazo_entrega: Triangular = Triangular(*valor("INV-01"))        # HORAS (24, 36, 48)

    def __post_init__(self) -> None:
        if self.capacidad <= 0:
            raise ValueError("La capacidad del tanque tiene que ser positiva.")
        if not 0 <= self.nivel_inicial <= self.capacidad:
            raise ValueError("El nivel inicial tiene que estar entre 0 y la capacidad.")
        if not 0 <= self.punto_pedido <= self.capacidad:
            raise ValueError("El punto de pedido tiene que estar entre 0 y la capacidad.")
        if self.cantidad_pedido <= 0:
            raise ValueError("La cantidad a pedir tiene que ser positiva.")

    @property
    def plazo_entrega_minutos(self) -> Triangular:
        """El plazo de entrega expresado en minutos, que es la unidad del motor."""
        return Triangular(
            self.plazo_entrega.minimo * 60.0,
            self.plazo_entrega.moda * 60.0,
            self.plazo_entrega.maximo * 60.0,
        )


# =============================================================================
# Estacionalidad: índices de demanda por mes
# =============================================================================
@dataclass(frozen=True)
class Estacionalidad:
    """Multiplicadores de demanda por mes del año (índice base = 100 en enero)."""

    indices: tuple[float, ...] = (100.0,) * 12  # neutra: todos los meses pesan igual

    def __post_init__(self) -> None:
        if len(self.indices) != 12:
            raise ValueError("Estacionalidad debe tener exactamente 12 índices (enero a diciembre).")
        if any(i <= 0 for i in self.indices):
            raise ValueError("Los índices de estacionalidad deben ser positivos.")

    def indice_mes(self, mes: int) -> float:
        """Índice de estacionalidad para un mes (1=enero, ..., 12=diciembre)."""
        if not 1 <= mes <= 12:
            raise ValueError(f"El mes debe estar entre 1 y 12, recibido {mes}.")
        return self.indices[mes - 1]

    @property
    def promedio(self) -> float:
        """Promedio de todos los índices (se usa para normalizar, §14.4)."""
        return sum(self.indices) / len(self.indices)


#: Estacionalidad neutra (default, C10/DEM-06): todos los meses pesan igual.
ESTACIONALIDAD_NEUTRA = Estacionalidad()

#: Preset "leve": oscilación suave de ±6 % con mínimo en invierno (supuesto del orquestador).
ESTACIONALIDAD_LEVE = Estacionalidad(
    (
        106.0, 105.2, 103.0, 100.0, 97.0, 94.8,   # ene..jun
        94.0, 94.8, 97.0, 100.0, 103.0, 105.2,   # jul..dic
    )
)

#: Preset "proxy turístico" (DATOS_OPERACIONALES §6; B3/C10).
ESTACIONALIDAD_PROXY = Estacionalidad(
    (
        100.0, 60.0, 80.0, 65.0, 60.0, 55.0,     # ene..jun
        85.0, 75.0, 70.0, 70.0, 75.0, 85.0,      # jul..dic
    )
)


def dias_del_mes(mes: int) -> int:
    """Días del mes (1=enero .. 12=diciembre) en el año de referencia."""
    if not 1 <= mes <= 12:
        raise ValueError(f"El mes debe estar entre 1 y 12, recibido {mes}.")
    return calendar.monthrange(ANO_REFERENCIA, mes)[1]


def dias_y_fecha(
    horizonte: str, mes: int = 1, dia: int = 1, estacion: str = "verano"
) -> tuple[tuple[int, int], int]:
    """Una sola función horizonte → (fecha_inicio, dias) (corrige B5).

    dia = 1 día · semana = 7 · mes = los días reales del mes elegido ·
    estacion = 90 días desde el 1 del mes que abre la estación · anio = 365 desde el 1/ene.
    """
    if horizonte == "dia":
        return (mes, dia), 1
    if horizonte == "semana":
        return (mes, dia), 7
    if horizonte == "mes":
        return (mes, 1), dias_del_mes(mes)
    if horizonte == "estacion":
        inicio = {"verano": 1, "otonio": 4, "invierno": 6, "primavera": 9}[estacion]
        return (inicio, 1), 90
    if horizonte == "anio":
        return (1, 1), 365
    raise ValueError(f"Horizonte desconocido: {horizonte}")


# =============================================================================
# Parámetros de la simulación
# =============================================================================
@dataclass(frozen=True)
class ParametrosSimulacion:
    """Todo lo que define una corrida del modelo."""

    # --- Recursos -------------------------------------------------------------
    surtidores: int = 3
    cajas: int = 1

    # --- Demanda --------------------------------------------------------------
    demanda: DemandaDiaria = DemandaDiaria(
        valores=valor("DEM-07C")[0], frecuencias=valor("DEM-07C")[1]
    )
    perfil: PerfilHorario = PerfilHorario(valor("DEM-02"))

    # --- Modo de demanda (corrige B1/B4: antes "modo determinista") ------------
    modo_demanda: str = "esperada"        # "esperada" (litros/mes) | "monte_carlo" (tabla empírica)
    litros_mes: float = valor("DEM-01")   # DEM-01: LITROS por mes, la variable de entrada
    litros_medios_por_cliente: float = valor("DEM-11")  # §14.2: litros medios por cliente líquido
    factor_fin_de_semana: float = valor("DEM-03")  # DEM-03, normalizado al mes (§14.4)
    estacionalidad: Estacionalidad = ESTACIONALIDAD_NEUTRA
    fecha_inicio: tuple[int, int] = (1, 1)  # (mes, día) del primer día simulado (B2)

    # --- Tiempos de servicio --------------------------------------------------
    carga: Triangular = Triangular(*valor("TIE-02"))
    carga_gnc: Triangular = Triangular(*valor("TIE-04"))
    compra: Triangular = Triangular(*valor("TIE-05"))
    caja_exponencial: bool = False

    # --- Volumen cargado ------------------------------------------------------
    litros: Triangular = Triangular(*valor("VEH-06"))

    # --- Comportamiento del cliente ------------------------------------------
    prob_compra: float = valor("DEM-08")      # Bernoulli: entra al minimarket
    paciencia_surtidor: float = valor("TIE-06")[0]   # umbral de abandono en la cola del surtidor
    paciencia_caja: float = valor("TIE-06")[1]       # umbral de abandono en la cola de la caja

    # --- Estación real (§7): grupos, productos, playeros y cola finita ---------
    estacion_real: bool = True
    grupos: tuple[Grupo, ...] = GRUPOS_REALES
    productos: tuple[Producto, ...] = PRODUCTOS_REALES
    tipos_vehiculo: tuple[TipoVehiculo, ...] = TIPOS_REALES
    matriz_tipos: tuple[tuple[str, tuple[float, ...]], ...] = matriz_tipo_por_producto()
    playeros_por_turno: tuple[int, int, int] = valor("PER-01")  # noche · mañana · tarde
    turnos: tuple[tuple[float, int], ...] = turnos_de(valor("PER-01"))  # (hora, playeros)
    pct_gnc: float = valor("DEM-05")
    capacidad_cola: int | None = valor("PER-05")   # por zona; la pisa `cola_por_cara` si está
    cola_por_cara: int | None = valor("PER-07")    # lugares de cola de CADA cara (misma en todas)
    disciplina_cola: str = valor("PER-06")       # "por_grupo" | "por_cara"
    sorteo_producto_primero: bool = True         # clásico lo apaga para reproducir los dorados
    tabla_demanda_relativa: bool = True          # DEM-07: factores relativos × litros del día
    demanda_relativa: DemandaDiaria = DemandaDiaria(
        valores=valor("DEM-07")[0], frecuencias=valor("DEM-07")[1]
    )
    inventario: tuple[InventarioProducto, ...] = INVENTARIO_REAL
    red: ParametrosRed | None = ParametrosRed()   # None = el plazo no suma demoras de ruta
    gnc: ParametrosGNC | None = ParametrosGNC()   # None = sin cortes ni compresores

    # --- Simulación con datos reales (rediseño v3) ------------------------------
    determinista: bool = False         # True = sin azar: cuotas exactas y valores promedio (MOD-02)
    animar_todo: bool = False          # True = grabar la animación de TODOS los días (CAL-07)

    # --- Escenarios S7 y S12 (Fase 7): apagados por defecto -------------------
    factor_quincena: float = valor("DEM-12")[0]            # S12: cuánto se multiplica el día
    dias_quincena: tuple[int, ...] = ()                    # días del mes con pico de cobro (() = ninguno)
    crisis: tuple[float, float, float] | None = None       # S7: plazo (h) de crisis; None = no hay
    crisis_dia: int = valor("INV-11")[0]                   # día de la corrida en que arranca
    crisis_dias: float = valor("INV-11")[1]                # cuántos días dura

    # --- Inventario (clásico: un solo tanque) ---------------------------------
    tanque: ParametrosTanque = ParametrosTanque()

    # --- Control de la corrida ------------------------------------------------
    dias: int = 30                     # días simulados (30 = un mes de operación)
    dias_calentamiento: int = 2        # días descartados (B4: el tanque arranca al 75 %)
    dia_animado: int = 2               # qué día se graba para la animación
    dt_traza: float = 0.5              # cada cuánto se captura un cuadro de animación

    # --- Horizonte (Fase 2) --------- -----------------------------------------
    horizonte: str = "mes"             # "dia", "semana", "mes", "estacion", "anio"

    def __post_init__(self) -> None:
        if self.surtidores < 1 or self.cajas < 1:
            raise ValueError("Tiene que haber al menos 1 surtidor y 1 caja.")
        if not 0.0 <= self.prob_compra <= 1.0:
            raise ValueError("La probabilidad de compra tiene que estar entre 0 y 1.")
        if self.dias < 1:
            raise ValueError("Hay que simular al menos 1 día.")
        if self.dias_calentamiento >= self.dias:
            raise ValueError("El calentamiento tiene que ser menor que los días simulados.")
        if not 1 <= self.dia_animado <= self.dias:
            raise ValueError("El día a animar tiene que estar dentro de la corrida.")
        if self.modo_demanda not in ("esperada", "monte_carlo"):
            raise ValueError("modo_demanda tiene que ser 'esperada' o 'monte_carlo'.")
        if self.determinista and self.modo_demanda != "esperada":
            raise ValueError("La simulación sin azar usa la demanda esperada (litros por mes).")
        if self.litros_mes <= 0:
            raise ValueError("litros_mes tiene que ser positivo.")
        if self.litros_medios_por_cliente <= 0:
            raise ValueError("litros_medios_por_cliente tiene que ser positivo.")
        if self.factor_fin_de_semana <= 0:
            raise ValueError("factor_fin_de_semana tiene que ser positivo.")
        mes_inicio, dia_inicio = self.fecha_inicio
        if not (1 <= mes_inicio <= 12 and 1 <= dia_inicio <= dias_del_mes(mes_inicio)):
            raise ValueError(f"fecha_inicio inválida: {self.fecha_inicio}.")
        if self.estacion_real:
            if not self.grupos or not self.productos:
                raise ValueError("La estación real necesita grupos y productos.")
            if self.disciplina_cola not in ("por_grupo", "por_cara"):
                raise ValueError("disciplina_cola tiene que ser 'por_grupo' o 'por_cara'.")
            if min(self.playeros_por_turno) < 1:
                raise ValueError("Tiene que haber al menos 1 playero por turno.")
            liquidos = {p.id for p in self.productos if not p.es_gnc}
            inventariados = {i.producto for i in self.inventario}
            if liquidos != inventariados:
                raise ValueError(
                    f"El inventario no cubre los productos líquidos: {liquidos} vs {inventariados}."
                )
            if not 0.0 <= self.pct_gnc < 1.0:
                raise ValueError("pct_gnc tiene que estar entre 0 y 1.")

    # --- Valores derivados ----------------------------------------------------
    @property
    def duracion(self) -> float:
        """Duración total de la corrida, en minutos."""
        return self.dias * MINUTOS_POR_DIA

    @property
    def calentamiento(self) -> float:
        """Fin del período de calentamiento, en minutos."""
        return self.dias_calentamiento * MINUTOS_POR_DIA

    @property
    def dias_medidos(self) -> int:
        return self.dias - self.dias_calentamiento

    def capacidad_de(self, id_grupo: str) -> int | None:
        """Lugares de cola de una zona: `cola_por_cara` × sus caras (o la capacidad fija por zona)."""
        if self.cola_por_cara is not None:
            return self.cola_por_cara * next(g.caras for g in self.grupos if g.id == id_grupo)
        return self.capacidad_cola

    def datos_reales(self) -> ParametrosSimulacion:
        """Los mismos parámetros pero para la **simulación con datos reales** (sin azar).

        Determinista, sin calentamiento (arranca en el momento cero), tanques llenos (INV-12), sin
        cortes de ruta sorteados y con la animación de todos los días. Es la modalidad por defecto
        de la app; la que tiene azar es la "editada".
        """
        inventario = tuple(
            replace(i, nivel_inicial=i.capacidad * valor("INV-12")) for i in self.inventario
        )
        red = (
            replace(self.red, escenario_corte="ninguno")
            if self.red is not None and self.red.escenario_corte == "aleatorio"
            else self.red
        )
        return replace(
            self, determinista=True, modo_demanda="esperada", dias_calentamiento=0,
            inventario=inventario, red=red, animar_todo=True, dia_animado=1,
        )

    @property
    def ventana_animacion(self) -> tuple[float, float]:
        """Intervalo de minutos que se graba para la animación (un día, o todos si `animar_todo`)."""
        if self.animar_todo:
            return 0.0, self.duracion
        inicio = (self.dia_animado - 1) * MINUTOS_POR_DIA
        return inicio, inicio + MINUTOS_POR_DIA

    def _dias_segun_horizonte(self) -> int:
        """Días del horizonte elegido (delega en `dias_y_fecha` para no repetir el mapa)."""
        _, dias = dias_y_fecha(self.horizonte)
        return dias

    @classmethod
    def clasico(cls) -> ParametrosSimulacion:
        """El caso degenerado del proyecto hipotético original.

        Reproduce exactamente los números dorados de ORQUESTADOR §14.1: 3 surtidores,
        un solo producto, la tabla empírica heredada, el perfil y los tiempos del
        proyecto original, el tanque de 40.000 L y 1 día de calentamiento. Es la base
        del control N1: cada valor queda fijado acá para que los defaults del caso
        real (que salen del Registro) no los pisen.
        """
        return cls(
            estacion_real=False,
            modo_demanda="monte_carlo",
            dias=30,
            dias_calentamiento=1,
            demanda=DEMANDA_TIPICA,
            perfil=PERFIL_TIPICO,
            carga=Triangular(3.0, 5.0, 8.0),
            compra=Triangular(1.5, 3.0, 6.0),
            litros=Triangular(15.0, 30.0, 60.0),
            prob_compra=0.30,
            sorteo_producto_primero=False,
            tabla_demanda_relativa=False,
            capacidad_cola=None,
            cola_por_cara=None,
            red=None,
            gnc=None,
            tanque=ParametrosTanque(
                capacidad=40_000.0,
                nivel_inicial=30_000.0,
                punto_pedido=12_000.0,
                cantidad_pedido=20_000.0,
                plazo_entrega=Triangular(8.0, 16.0, 36.0),
            ),
        )

    @property
    def autos_por_dia(self) -> float:
        """Clientes por día promedio (todos los productos, incluido el GNC).

        En modo 'esperada': litros del mes ÷ litros medios por cliente, repartidos en
        los días del mes de `fecha_inicio`. Nunca "litros ÷ 30 llamados autos" (B1).
        En modo 'monte_carlo': media de la tabla (absoluta en el clásico; la relativa
        tiene media 1 y se aplica sobre el nivel derivado de los litros).
        """
        if self.modo_demanda == "esperada":
            return self._llegadas_base()
        if self.tabla_demanda_relativa and self.estacion_real:
            return self._llegadas_base()
        return self.demanda.media

    def _llegadas_base(self) -> float:
        """Clientes/día que se derivan de `litros_mes` (líquidos + GNC)."""
        liquidos = (
            self.litros_mes / dias_del_mes(self.fecha_inicio[0])
        ) / self.litros_medios_por_cliente
        if self.estacion_real:
            return liquidos / (1.0 - self.pct_gnc)
        return liquidos

    def _fecha_del_dia(self, dia: int) -> tuple[int, int]:
        """(mes, día de la semana) de la fecha del día `dia` de la corrida.

        `dia = 1` es `fecha_inicio`; el día de la semana es 0=lunes .. 6=domingo
        (como `datetime.weekday()`), en el año de referencia (corrige B2).
        """
        mes_inicio, dia_inicio = self.fecha_inicio
        fecha = date(ANO_REFERENCIA, mes_inicio, dia_inicio) + timedelta(days=dia - 1)
        return fecha.month, fecha.weekday()

    def _factor_tipo_de_dia(self, mes: int, dia_semana: int, dia_mes: int = 0) -> float:
        """Factor del tipo de día, normalizado para conservar los litros del mes (§14.4).

        Con `dias_quincena` (S12) el día de pico de cobro pesa `factor_quincena` veces más y el
        mes se vuelve a normalizar: el escenario concentra la demanda, no agrega volumen.
        """
        total = dias_del_mes(mes)
        primero = date(ANO_REFERENCIA, mes, 1)
        f = self.factor_fin_de_semana
        if not self.dias_quincena:
            fines = sum(
                1 for d in range(total) if (primero + timedelta(days=d)).weekday() >= 5
            )
            habiles = total - fines
            nivel_habil = total / (habiles + f * fines)
            return f * nivel_habil if dia_semana >= 5 else nivel_habil

        def peso(d: int) -> float:
            fecha = primero + timedelta(days=d)
            return (f if fecha.weekday() >= 5 else 1.0) * (
                self.factor_quincena if fecha.day in self.dias_quincena else 1.0
            )

        nivel = total / sum(peso(d) for d in range(total))
        return nivel * peso(dia_mes - 1)

    def litros_del_dia(self, dia: int) -> float:
        """Litros del día `dia` de la corrida (modo 'esperada').

        `litros_mes` ÷ días del mes de esa fecha × estacionalidad del mes
        (índice ÷ media, §14.4) × factor por tipo de día (normalizado, §14.4).
        """
        mes, dia_semana = self._fecha_del_dia(dia)
        dia_mes = (
            date(ANO_REFERENCIA, *self.fecha_inicio) + timedelta(days=dia - 1)
        ).day
        indice = self.estacionalidad.indice_mes(mes)
        return (
            self.litros_mes
            / dias_del_mes(mes)
            * (indice / self.estacionalidad.promedio)
            * self._factor_tipo_de_dia(mes, dia_semana, dia_mes)
        )

    @property
    def playeros_maximos(self) -> int:
        """Dotación más alta de cualquier tramo del día (la capacidad del recurso)."""
        return max(max(n for _, n in self.turnos), max(self.playeros_por_turno))

    def autos_por_dia_fecha(self, dia: int) -> float:
        """Clientes del día `dia` de la corrida, con estacionalidad y tipo de día."""
        if self.modo_demanda != "esperada":
            return self.autos_por_dia
        liquidos = self.litros_del_dia(dia) / self.litros_medios_por_cliente
        if self.estacion_real:
            return liquidos / (1.0 - self.pct_gnc)
        return liquidos

    def pesos_llegada(self) -> tuple[float, ...]:
        """Pesos de llegada por producto (líquidos + GNC al final, cadena §14.2).

        peso = % de litros ÷ carga media del producto, normalizado; el GNC entra
        como `pct_gnc` de las llegadas.
        """
        pesos = [
            p.pct_litros / p.carga_media for p in self.productos if not p.es_gnc
        ]
        total = sum(pesos)
        salida = [w / total * (1.0 - self.pct_gnc) for w in pesos]
        salida.append(self.pct_gnc)
        return tuple(salida)

    def media_servicio_liquidos(self) -> float:
        """Tiempo medio de servicio de un cliente de nafta/diésel.

        TIE-02 (media 5 min) más el extra de camión (litros ÷ 90, TIE-03) ponderado
        por la fracción de camiones de cada producto.
        """
        tipos = {t.id: t for t in self.tipos_vehiculo}
        matriz = dict(self.matriz_tipos)
        base = Triangular(*valor("TIE-02")).media
        litros_camion = tipos["camion"].litros.media
        pesos = self.pesos_llegada()[:-1]          # sin el GNC
        total = sum(pesos)
        extra = 0.0
        for prod, w in zip(
            (p for p in self.productos if not p.es_gnc), pesos
        ):
            extra += (w / total) * matriz[prod.id][_TIPOS_MATRIZ.index("camion")] \
                * litros_camion / 90.0
        return base + extra

    @property
    def litros_por_dia(self) -> float:
        """Consumo diario esperado de combustible (líquidos)."""
        if self.estacion_real:
            liquidos = self.autos_por_dia * (1.0 - self.pct_gnc)
            return liquidos * self.litros_medios_por_cliente
        return self.autos_por_dia * self.litros.media

    @property
    def media_caja(self) -> float:
        return self.compra.media

    @property
    def rho_pico(self) -> float:
        """Intensidad de tráfico en la hora pico de un día promedio: ρ = λ_pico·E[S] / c.

        Es el cálculo analítico previo. Si ρ ≥ 1 en el pico, durante esa hora la cola
        crece sin parar y sólo la frena el abandono de clientes. En la estación real
        el cuello son los playeros (PER-01), no las caras.
        """
        if self.estacion_real:
            # Sólo los clientes de nafta y diésel usan playero (el GNC no, PER-04).
            lambda_pico = self.perfil.tasa_maxima(self.autos_por_dia) * (1.0 - self.pct_gnc)
            return (lambda_pico * self.media_servicio_liquidos()) / self.playeros_maximos
        lambda_pico = self.perfil.tasa_maxima(self.autos_por_dia)
        return (lambda_pico * self.carga.media) / self.surtidores

    @property
    def rho_pico_dia_malo(self) -> float:
        """Lo mismo pero en el día de mayor demanda de la tabla empírica."""
        lambda_pico = self.perfil.tasa_maxima(max(self.demanda.valores))
        return (lambda_pico * self.carga.media) / self.surtidores

    @property
    def rho_cajas(self) -> float:
        """Intensidad de tráfico de las cajas en la hora pico."""
        llegada_caja = self.perfil.tasa_maxima(self.autos_por_dia) * self.prob_compra
        return (llegada_caja * self.media_caja) / self.cajas

    @property
    def cobertura_punto_pedido(self) -> float:
        """Cuántas horas de venta cubre el punto de pedido en un día promedio."""
        consumo_por_hora = self.litros_por_dia / 24.0
        return self.tanque.punto_pedido / consumo_por_hora if consumo_por_hora else 0.0


# =============================================================================
# Escenarios
# =============================================================================
@dataclass(frozen=True)
class Escenario:
    """Una configuración a comparar: recursos (caso clásico) o cambios declarativos (S0–S12).

    `cambios` es `((campo, valor), …)` sobre `ParametrosSimulacion` — datos, no lambdas, para
    que `st.cache_data` pueda serializarlo con pickle (§11-9).
    """

    nombre: str
    descripcion: str
    surtidores: int
    cajas: int
    id: str = ""                                        # "S2", "S3", … (vacío en el clásico)
    pregunta: str = ""                                  # la pregunta que contesta (§7.7)
    cambios: tuple[tuple[str, object], ...] = ()

    def aplicar(self, p: ParametrosSimulacion) -> ParametrosSimulacion:
        base = replace(p, surtidores=self.surtidores, cajas=self.cajas)
        return replace(base, **dict(self.cambios)) if self.cambios else base


def escenarios_desde(p: ParametrosSimulacion) -> list[Escenario]:
    """Los 4 escenarios de capacidad: Base, +1 surtidor, +1 cajero, ambos."""
    s, c = p.surtidores, p.cajas
    return [
        Escenario("Base", f"Situación actual ({s} surtidores, {c} caja/s)", s, c),
        Escenario("A", "+1 surtidor", s + 1, c),
        Escenario("B", "+1 cajero", s, c + 1),
        Escenario("C", "+1 surtidor y +1 cajero", s + 1, c + 1),
    ]


# =============================================================================
# Economía
# =============================================================================
@dataclass(frozen=True)
class ParametrosEconomicos:
    """Costos e ingresos para el análisis económico.

    Los defaults salen del Registro (ECO-01..ECO-07, §5.1-b). La mayoría es `heredado`
    del proyecto hipotético y se muestra como placeholder visible en la interfaz.
    """

    # Ingresos
    precios: tuple[tuple[str, float], ...] = valor("ECO-08")   # $ por litro (GNC: por m³); editables
    margen_por_litro: float = valor("ECO-01")              # $ de ganancia bruta por litro vendido
    margenes_producto: tuple[tuple[str, float], ...] = ()  # $/L por producto (menú); () = todos ECO-01
    margen_compra: float = valor("ECO-02")                 # $ de ganancia bruta por compra en minimarket

    # Inversión y operación de la capacidad de atención
    inversion_surtidor: float = valor("ECO-05")[0]         # $ por instalar un surtidor (una sola vez)
    operativo_surtidor_mensual: float = valor("ECO-05")[1]
    sueldo_cajero_mensual: float = valor("ECO-04C")

    margen_gnc: float = valor("ECO-03")                    # $ de ganancia bruta por m³ de GNC

    # Personal (§7.9): sueldo mensual con adicionales y puestos que el motor no modela
    sueldo_playero_mensual: float = valor("ECO-04")[0]
    sueldo_encargado_mensual: float = valor("ECO-04")[2]
    cobertura_francos: float = valor("ECO-10")             # personas por puesto cubierto los 7 días
    puestos_encargado: float = valor("ECO-11")[0]          # puestos-turno por día (mañana y tarde)
    puestos_tienda: float = valor("ECO-11")[1]

    # Costos de inventario
    costo_pedido: float = valor("ECO-06")[0]               # $ de flete fijo por cada camión cisterna
    flete_por_km: float = valor("ECO-06")[1]               # $ por km de ida y vuelta (sin dato: 0)
    costo_almacenamiento_litro_mes: float = valor("ECO-07")  # $ por litro promedio en tanque, por mes

    def delta_precio(self, producto: str) -> float:
        """Cuánto cambió el precio del producto contra el de referencia (ECO-08), en $ por litro.

        Para que el precio afecte la plata se supone un **costo fijo** (precio de referencia −
        margen heredado): subir el precio $50 sube el margen $50 por litro. La demanda **no**
        reacciona al precio (sin elasticidad): es un supuesto y se avisa en la app.
        """
        clave = "premium" if producto == "vpower" else producto
        actual = dict(self.precios).get(clave)
        referencia = dict(valor("ECO-08")).get(clave)
        return 0.0 if actual is None or referencia is None else float(actual) - float(referencia)

    def margen_de(self, producto: str) -> float:
        """Margen por litro (por m³ el GNC) de un producto, con el cambio de precio si se editó."""
        propio = dict(self.margenes_producto)
        base = propio.get(producto, self.margen_gnc if producto == "gnc" else self.margen_por_litro)
        return base + self.delta_precio(producto)

    def __post_init__(self) -> None:
        if self.margen_por_litro < 0 or self.margen_compra < 0:
            raise ValueError("Los márgenes no pueden ser negativos.")
