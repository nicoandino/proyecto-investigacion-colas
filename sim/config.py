"""Parámetros del modelo, escenarios y datos económicos.

Toda la configuración vive acá, en dataclasses inmutables (`frozen=True`), para que
una corrida quede descrita por un único objeto que se puede imprimir y guardar.

Convenciones (ver CLAUDE.md):
  - Tiempo en MINUTOS. El día tiene 1440 minutos y la corrida dura varios días.
  - Volumen en LITROS.
  - Dinero en PESOS ($).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import cached_property

MINUTOS_POR_DIA = 1440
HORAS_POR_DIA = 24


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


#: Perfil típico de una estación de servicio abierta las 24 horas.
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
# Inventario: el tanque de combustible
# =============================================================================
@dataclass(frozen=True)
class ParametrosTanque:
    """Tanque de combustible y política de reposición (punto de pedido, cantidad a pedir).

    Cuando el nivel cae por debajo del punto de pedido se emite un pedido al camión
    cisterna, que tarda un plazo de entrega aleatorio en llegar. Si mientras tanto el
    tanque se vacía, la estación no puede atender: no se pierde un cliente, se pierden
    todos los que llegan hasta que el camión descargue.
    """

    capacidad: float = 40_000.0          # litros
    nivel_inicial: float = 30_000.0      # litros al empezar la simulación
    punto_pedido: float = 12_000.0       # litros: cuando baja de acá, se pide
    cantidad_pedido: float = 20_000.0    # litros que trae el camión
    plazo_entrega: Triangular = Triangular(8.0, 16.0, 36.0)   # HORAS

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
# Parámetros de la simulación
# =============================================================================
@dataclass(frozen=True)
class ParametrosSimulacion:
    """Todo lo que define una corrida del modelo."""

    # --- Recursos -------------------------------------------------------------
    surtidores: int = 3
    cajas: int = 1

    # --- Demanda --------------------------------------------------------------
    demanda: DemandaDiaria = DEMANDA_TIPICA
    perfil: PerfilHorario = PERFIL_TIPICO

    # --- Tiempos de servicio --------------------------------------------------
    carga: Triangular = Triangular(3.0, 5.0, 8.0)
    compra: Triangular = Triangular(1.5, 3.0, 6.0)
    caja_exponencial: bool = False

    # --- Volumen cargado ------------------------------------------------------
    litros: Triangular = Triangular(15.0, 30.0, 60.0)

    # --- Comportamiento del cliente ------------------------------------------
    prob_compra: float = 0.30          # Bernoulli: 30% entra al minimarket
    paciencia_surtidor: float = 10.0   # umbral de abandono en la cola del surtidor
    paciencia_caja: float = 8.0        # umbral de abandono en la cola de la caja

    # --- Inventario -----------------------------------------------------------
    tanque: ParametrosTanque = ParametrosTanque()

    # --- Control de la corrida ------------------------------------------------
    dias: int = 30                     # días simulados (30 = un mes de operación)
    dias_calentamiento: int = 1        # días descartados (el tanque arranca lleno)
    dia_animado: int = 2               # qué día se graba para la animación
    dt_traza: float = 0.5              # cada cuánto se captura un cuadro de animación

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

    @property
    def ventana_animacion(self) -> tuple[float, float]:
        """Intervalo de minutos que se graba para la animación (un solo día)."""
        inicio = (self.dia_animado - 1) * MINUTOS_POR_DIA
        return inicio, inicio + MINUTOS_POR_DIA

    @property
    def autos_por_dia(self) -> float:
        """Autos por día promedio según la tabla empírica."""
        return self.demanda.media

    @property
    def litros_por_dia(self) -> float:
        """Consumo diario esperado de combustible."""
        return self.autos_por_dia * self.litros.media

    @property
    def media_caja(self) -> float:
        return self.compra.media

    @property
    def rho_pico(self) -> float:
        """Intensidad de tráfico en la hora pico de un día promedio: ρ = λ_pico·E[S] / c.

        Es el cálculo analítico previo. Si ρ ≥ 1 en el pico, durante esa hora la cola
        crece sin parar y sólo la frena el abandono de clientes.
        """
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
    """Una configuración de recursos a comparar."""

    nombre: str
    descripcion: str
    surtidores: int
    cajas: int

    def aplicar(self, p: ParametrosSimulacion) -> ParametrosSimulacion:
        return replace(p, surtidores=self.surtidores, cajas=self.cajas)


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

    Los valores por defecto son ESTIMACIONES provisorias (ver TASK.md: falta definirlos
    con datos reales). Todos son editables desde la interfaz.
    """

    # Ingresos
    margen_por_litro: float = 100.0              # $ de ganancia bruta por litro vendido
    margen_compra: float = 2500.0                # $ de ganancia bruta por compra en minimarket

    # Inversión y operación de la capacidad de atención
    inversion_surtidor: float = 18_000_000.0     # $ por instalar un surtidor (una sola vez)
    operativo_surtidor_mensual: float = 250_000.0
    sueldo_cajero_mensual: float = 900_000.0

    # Costos de inventario
    costo_pedido: float = 150_000.0              # $ de flete por cada camión cisterna
    costo_almacenamiento_litro_mes: float = 25.0  # $ por litro promedio en tanque, por mes

    def __post_init__(self) -> None:
        if self.margen_por_litro < 0 or self.margen_compra < 0:
            raise ValueError("Los márgenes no pueden ser negativos.")
