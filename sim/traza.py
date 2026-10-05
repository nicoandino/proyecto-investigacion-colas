"""Traza de la corrida: lo que el motor registra para poder mostrarse después.

Tiene tres partes:

  - `cuadros`: fotos del estado del sistema cada `dt` minutos, pero SÓLO del día elegido
    para animar. Grabar los 30 días serían más de 80.000 cuadros y no aportarían nada:
    la animación se mira un día.
  - `inventario`: el nivel del tanque muestreado cada 10 minutos durante toda la corrida.
    Es el gráfico de dientes de sierra del mes completo.
  - `dias`: el registro Monte Carlo de cada día (qué número aleatorio salió y qué demanda
    le correspondió), igual que la tabla de simulación del apunte.

Separar la simulación de la presentación tiene dos ventajas: la corrida es igual de rápida
con o sin traza, y la reproducción se puede pausar, acelerar o rebobinar sin volver a
simular.
"""

from __future__ import annotations

from dataclasses import dataclass

MINUTOS_POR_DIA = 1440
#: Cada cuánto se muestrea el nivel del tanque a lo largo de toda la corrida.
DT_INVENTARIO = 10.0


@dataclass(frozen=True)
class Cuadro:
    """Estado del sistema en un instante de la simulación."""

    t: float                      # minuto absoluto de la corrida
    surtidores_ocupados: int
    cola_surtidor: int
    cajas_ocupadas: int
    cola_caja: int
    atendidos: int                # autos que terminaron de cargar (acumulado)
    perdidos_surtidor: int        # abandonos en la cola del surtidor (acumulado)
    compras: int                  # compras cobradas en el minimarket (acumulado)
    perdidos_caja: int            # abandonos en la cola de la caja (acumulado)
    nivel_tanque: float           # litros
    perdidos_sin_combustible: int # los que se fueron porque no había nafta (acumulado)
    pedidos_en_camino: int        # camiones cisterna pedidos y todavía no llegados
    en_calentamiento: bool
    playeros_ocupados: int = 0    # playeros atendiendo en este instante (estación real)
    playeros_en_turno: int = 0    # playeros que corresponden al turno (estación real)
    perdidos_cola_llena: int = 0  # no entraron porque la cola de su zona estaba llena (acumulado)
    gnc_cortado: int = 0          # 1 si el GNC está cortado (episodios: Fase 6)
    # Una foto por zona: (id, carriles, cola, largo de la cola, rechazados acumulados).
    #   carriles: un código por cara: -1 libre · 2·k cargando · 2·k+1 esperando al
    #   playero con la cara ocupada (k = índice del producto).
    #   cola: el producto (índice) de cada auto que espera, en orden de llegada.
    grupos: tuple = ()
    # Una foto por tanque: (producto, litros, litros en camino, progreso del camión
    # entre 0 y 1 (-1 si no hay pedido), horas que faltan para que llegue).
    tanques: tuple = ()

    @property
    def perdidos(self) -> int:
        return self.perdidos_surtidor + self.perdidos_caja + self.perdidos_sin_combustible

    @property
    def minuto_del_dia(self) -> float:
        return self.t % MINUTOS_POR_DIA

    @property
    def hora_reloj(self) -> str:
        """La hora del día, con el minuto 0 de la simulación como las 00:00."""
        minuto = int(self.minuto_del_dia)
        return f"{minuto // 60:02d}:{minuto % 60:02d}"


@dataclass(frozen=True)
class DiaSimulado:
    """El registro Monte Carlo de un día: el sorteo y lo que pasó."""

    dia: int
    numero_aleatorio: int      # 01 a 100 (el 100 se escribe "00", como en el apunte)
    autos_sorteados: int       # lo que dijo la tabla de frecuencias
    autos_llegados: int        # los que efectivamente llegaron (Poisson alrededor del valor)
    atendidos: int
    perdidos_cola: int
    perdidos_sin_combustible: int
    litros_vendidos: float
    hubo_quiebre: bool
    en_calentamiento: bool

    @property
    def numero_texto(self) -> str:
        return "00" if self.numero_aleatorio >= 100 else f"{self.numero_aleatorio:02d}"

    @property
    def perdidos(self) -> int:
        return self.perdidos_cola + self.perdidos_sin_combustible


class Traza:
    """Todo lo que el motor registra para que la interfaz lo muestre."""

    def __init__(self) -> None:
        self.cuadros: list[Cuadro] = []
        self.inventario: list[tuple[float, float, int]] = []   # (minuto, litros, pedidos en camino)
        self.dias: list[DiaSimulado] = []
        # Indicadores por hora del día, copiados al terminar la corrida. Sirven para el
        # gráfico del perfil: muestran en qué hora está realmente el pico.
        self.llegadas_por_hora: list[int] = [0] * 24
        self.espera_por_hora: list[float] = [0.0] * 24
        self.perdidos_por_hora: list[int] = [0] * 24

    def capturar(self, **datos) -> None:
        self.cuadros.append(Cuadro(**datos))

    def capturar_inventario(self, t: float, nivel: float, pedidos_en_camino: int) -> None:
        self.inventario.append((t, nivel, pedidos_en_camino))

    def registrar_dia(self, dia: DiaSimulado) -> None:
        self.dias.append(dia)

    def __len__(self) -> int:
        return len(self.cuadros)

    # --- Series para graficar -------------------------------------------------
    def serie(self, atributo: str) -> tuple[list[float], list[float]]:
        """Devuelve (tiempos, valores) de un atributo de los cuadros, para graficar."""
        tiempos = [c.minuto_del_dia for c in self.cuadros]
        valores = [float(getattr(c, atributo)) for c in self.cuadros]
        return tiempos, valores

    def serie_inventario(self) -> tuple[list[float], list[float]]:
        """(días, litros) del nivel del tanque a lo largo de toda la corrida."""
        dias = [t / MINUTOS_POR_DIA for t, _, _ in self.inventario]
        litros = [nivel for _, nivel, _ in self.inventario]
        return dias, litros

    @property
    def dias_medidos(self) -> list[DiaSimulado]:
        return [d for d in self.dias if not d.en_calentamiento]
