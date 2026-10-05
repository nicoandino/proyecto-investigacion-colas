"""Colectores de indicadores de la simulación.

Distinción clave del TP (y pregunta típica de parcial):

  - La ESPERA PROMEDIO es un promedio POR CLIENTE: se suman las esperas observadas y
    se divide por la cantidad de clientes. -> clase `Muestras`.

  - La LONGITUD PROMEDIO DE COLA, la UTILIZACIÓN y el NIVEL PROMEDIO DE TANQUE son
    promedios EN EL TIEMPO: se integra el valor de la variable a lo largo de la corrida
    (área bajo la curva escalonada) y se divide por el tiempo transcurrido.
    -> clase `SerieTemporal`.

Promediar "cuánta cola había cada vez que llegó alguien" daría un número distinto y
equivocado, porque no pondera cuánto tiempo duró cada estado.

Desde la Fase 2 hay colectores POR GRUPO (A nafta, B diésel, C GNC), POR PRODUCTO y
POR MOTIVO de pérdida (§7.6): los agregados clásicos (cola de surtidores, litros
vendidos, etc.) siguen existiendo y suman toda la estación, para que la interfaz
clásica y los dorados sigan funcionando.

Nota de implementación: los colectores NO guardan la historia completa de valores. Una
corrida de 30 días mueve decenas de miles de clientes y guardar cada cambio de estado
gastaría memoria sin aportar nada: los gráficos se arman con la traza, que muestrea el
sistema a intervalos regulares.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sim.config import ParametrosSimulacion

HORAS_POR_DIA = 24


class Muestras:
    """Acumulador de observaciones individuales (esperas, tiempos en sistema).

    Guarda sólo los acumuladores que hacen falta (suma, cantidad y máximo), no la lista
    completa de valores.
    """

    def __init__(self) -> None:
        self.suma = 0.0
        self.n = 0
        self.maximo = 0.0

    def agregar(self, valor: float) -> None:
        self.suma += valor
        self.n += 1
        if valor > self.maximo:
            self.maximo = valor

    def reiniciar(self) -> None:
        """Descarta lo observado durante el calentamiento."""
        self.suma = 0.0
        self.n = 0
        self.maximo = 0.0

    @property
    def promedio(self) -> float:
        return self.suma / self.n if self.n else 0.0


class SerieTemporal:
    """Variable escalonada en el tiempo, con promedio temporal (área / tiempo)."""

    def __init__(self, t_inicial: float = 0.0, valor_inicial: float = 0.0) -> None:
        self.valor = float(valor_inicial)
        self._t_ultimo = float(t_inicial)
        self._t_inicio = float(t_inicial)
        self._area = 0.0
        self.maximo = float(valor_inicial)
        self.minimo = float(valor_inicial)

    def _acumular_hasta(self, t: float) -> None:
        self._area += self.valor * (t - self._t_ultimo)
        self._t_ultimo = t

    def cambiar(self, t: float, nuevo_valor: float) -> None:
        """Registra que en el instante t la variable pasa a valer nuevo_valor."""
        self._acumular_hasta(t)
        self.valor = float(nuevo_valor)
        if self.valor > self.maximo:
            self.maximo = self.valor
        if self.valor < self.minimo:
            self.minimo = self.valor

    def sumar(self, t: float, delta: float) -> None:
        """Atajo para incrementar o decrementar en delta (entra o sale un cliente)."""
        self.cambiar(t, self.valor + delta)

    def reiniciar(self, t: float) -> None:
        """Arranca de nuevo el promedio temporal en t (fin del calentamiento).

        El valor actual de la variable NO se toca (la cola o el combustible que hay siguen
        estando); lo que se reinicia es la acumulación de área y los extremos observados.
        """
        self._acumular_hasta(t)
        self._area = 0.0
        self._t_inicio = t
        self.maximo = self.valor
        self.minimo = self.valor

    def cerrar(self, t: float) -> None:
        """Cierra el último tramo al terminar la corrida."""
        self._acumular_hasta(t)

    @property
    def promedio(self) -> float:
        duracion = self._t_ultimo - self._t_inicio
        return self._area / duracion if duracion > 0 else 0.0

    @property
    def area(self) -> float:
        return self._area


@dataclass
class Contadores:
    """Conteos de la corrida (se reinician al terminar el calentamiento)."""

    # Clientes (agregados de toda la estación)
    llegadas: int = 0
    atendidos_surtidor: int = 0
    perdidos_surtidor: int = 0          # abandono_espera: se cansó de hacer cola
    perdidos_sin_combustible: int = 0   # sin_combustible: no había producto
    perdidos_cola_llena: int = 0        # cola_llena: no entró a la cola finita
    entraron_minimarket: int = 0
    compras_atendidas: int = 0
    perdidos_caja: int = 0              # abandono_caja
    abandonos_playero: int = 0          # de perdidos_surtidor: se fue esperando al playero

    # Combustible
    litros_vendidos: float = 0.0
    litros_no_vendidos: float = 0.0     # los que se habrían vendido a quienes se fueron
    litros_recibidos: float = 0.0
    pedidos_emitidos: int = 0
    pedidos_recibidos: int = 0
    dias_con_quiebre: int = 0

    def reiniciar(self) -> None:
        for campo in self.__dataclass_fields__:
            setattr(self, campo, type(getattr(self, campo))())


@dataclass
class ContadoresGrupo:
    """Conteos de UN grupo de surtidores (A, B o C), por motivo de pérdida (§7.6)."""

    llegadas: int = 0
    atendidos: int = 0
    perdidos_espera: int = 0            # abandono_espera
    perdidos_cola_llena: int = 0        # cola_llena
    perdidos_sin_combustible: int = 0   # sin_combustible
    abandonos_playero: int = 0          # de perdidos_espera: se fue esperando al playero

    def reiniciar(self) -> None:
        for campo in self.__dataclass_fields__:
            setattr(self, campo, 0)


@dataclass
class ContadoresProducto:
    """Conteos de UN producto (litros y clientes)."""

    llegadas: int = 0
    atendidos: int = 0
    litros_vendidos: float = 0.0
    litros_no_vendidos: float = 0.0
    litros_recibidos: float = 0.0
    perdidos_sin_combustible: int = 0
    pedidos_emitidos: int = 0
    pedidos_recibidos: int = 0
    dias_con_quiebre: int = 0

    def reiniciar(self) -> None:
        for campo in self.__dataclass_fields__:
            setattr(self, campo, 0)


@dataclass
class PorHora:
    """Acumuladores por hora del día, para descubrir dónde está realmente el pico."""

    llegadas: list[int] = field(default_factory=lambda: [0] * HORAS_POR_DIA)
    espera_suma: list[float] = field(default_factory=lambda: [0.0] * HORAS_POR_DIA)
    espera_n: list[int] = field(default_factory=lambda: [0] * HORAS_POR_DIA)
    perdidos: list[int] = field(default_factory=lambda: [0] * HORAS_POR_DIA)

    def contar_llegada(self, hora: int) -> None:
        self.llegadas[hora] += 1

    def contar_espera(self, hora: int, espera: float) -> None:
        self.espera_suma[hora] += espera
        self.espera_n[hora] += 1

    def contar_perdido(self, hora: int) -> None:
        self.perdidos[hora] += 1

    def reiniciar(self) -> None:
        self.llegadas = [0] * HORAS_POR_DIA
        self.espera_suma = [0.0] * HORAS_POR_DIA
        self.espera_n = [0] * HORAS_POR_DIA
        self.perdidos = [0] * HORAS_POR_DIA

    def espera_promedio(self, hora: int) -> float:
        n = self.espera_n[hora]
        return self.espera_suma[hora] / n if n else 0.0


def _nivel_inicial_total(p: ParametrosSimulacion) -> float:
    """Litros iniciales de toda la estación (suma de los tanques)."""
    if p.estacion_real:
        return sum(i.nivel_inicial for i in p.inventario)
    return p.tanque.nivel_inicial


def _capacidad_total(p: ParametrosSimulacion) -> float:
    """Capacidad total de almacenamiento (suma de los tanques)."""
    if p.estacion_real:
        return sum(i.capacidad for i in p.inventario)
    return p.tanque.capacidad


def nivel_inicial_total(p: ParametrosSimulacion) -> float:
    """Helper público (lo usan los controles de conservación)."""
    return _nivel_inicial_total(p)


def capacidad_total(p: ParametrosSimulacion) -> float:
    """Helper público (lo usan los controles de conservación)."""
    return _capacidad_total(p)


class Indicadores:
    """Todos los colectores de una corrida, en un solo objeto."""

    def __init__(self, p: ParametrosSimulacion) -> None:
        self.p = p
        self.capacidad_surtidores = p.surtidores
        self.capacidad_cajas = p.cajas

        ids_grupos = tuple(g.id for g in p.grupos)
        ids_productos = tuple(pr.id for pr in p.productos)
        ids_liquidos = tuple(pr.id for pr in p.productos if not pr.es_gnc)
        ids_tipos = tuple(t.id for t in p.tipos_vehiculo)

        # Colas y servidores (agregados de toda la estación + por grupo)
        self.cola_surtidor = SerieTemporal()
        self.cola_caja = SerieTemporal()
        self.ocupados_surtidores = SerieTemporal()
        self.ocupadas_cajas = SerieTemporal()
        self.playeros_ocupados = SerieTemporal()
        self.playeros_en_turno = SerieTemporal(valor_inicial=float(p.playeros_por_turno[0]))
        self.colas_grupo = {g: SerieTemporal() for g in ids_grupos}
        self.ocupados_grupo = {g: SerieTemporal() for g in ids_grupos}

        # Esperas
        self.espera_surtidor = Muestras()    # total hasta empezar a ser atendido
        self.espera_cara = Muestras()        # hasta tener la cara (Little / N4)
        self.espera_caja = Muestras()
        self.tiempo_sistema = Muestras()
        self.esperas_grupo = {g: Muestras() for g in ids_grupos}
        self.esperas_cara_grupo = {g: Muestras() for g in ids_grupos}
        self.servicio_suma = 0.0             # Σ tiempo de carga de los atendidos (control 4)

        # Inventario
        self.nivel_tanque = SerieTemporal(valor_inicial=_nivel_inicial_total(p))
        self.niveles = {
            pr: SerieTemporal(valor_inicial=inv.nivel_inicial)
            for pr, inv in zip(ids_liquidos, p.inventario)
        }
        self.sin_combustible = SerieTemporal()   # indicador 0/1: fracción de tiempo sin nafta
        self.plazo_entrega = Muestras()

        # Litros por tipo de vehículo (N10)
        self.litros_por_tipo = {t: Muestras() for t in ids_tipos}

        # Conteos
        self.c = Contadores()
        self.c_total = Contadores()
        self.c_grupo = {g: ContadoresGrupo() for g in ids_grupos}
        self.c_grupo_total = {g: ContadoresGrupo() for g in ids_grupos}
        self.c_producto = {pr: ContadoresProducto() for pr in ids_productos}
        self.c_producto_total = {pr: ContadoresProducto() for pr in ids_productos}

        self.por_hora = PorHora()
        # Sin días de calentamiento no hay transitorio que descartar: se mide desde el inicio.
        self.calentamiento_terminado = p.dias_calentamiento == 0

    @property
    def series(self) -> tuple[SerieTemporal, ...]:
        return (
            self.cola_surtidor,
            self.cola_caja,
            self.ocupados_surtidores,
            self.ocupadas_cajas,
            self.playeros_ocupados,
            self.playeros_en_turno,
            self.nivel_tanque,
            self.sin_combustible,
            *self.colas_grupo.values(),
            *self.ocupados_grupo.values(),
            *self.niveles.values(),
        )

    def contar(self, nombre: str, cantidad: float = 1) -> None:
        """Incrementa un contador, tanto el del período de medición como el total."""
        for contadores in (self.c, self.c_total):
            setattr(contadores, nombre, getattr(contadores, nombre) + cantidad)

    def contar_grupo(self, grupo: str, nombre: str, cantidad: float = 1) -> None:
        """Incrementa un contador de grupo, en el medido y en el total."""
        for contadores in (self.c_grupo[grupo], self.c_grupo_total[grupo]):
            setattr(contadores, nombre, getattr(contadores, nombre) + cantidad)

    def contar_producto(self, producto: str, nombre: str, cantidad: float = 1) -> None:
        """Incrementa un contador de producto, en el medido y en el total."""
        for contadores in (self.c_producto[producto], self.c_producto_total[producto]):
            setattr(contadores, nombre, getattr(contadores, nombre) + cantidad)

    def reiniciar(self, t: float) -> None:
        """Fin del período de calentamiento: se descarta todo lo medido hasta acá."""
        for serie in self.series:
            serie.reiniciar(t)
        for muestras in (
            self.espera_surtidor,
            self.espera_cara,
            self.espera_caja,
            self.tiempo_sistema,
            self.plazo_entrega,
            *self.esperas_grupo.values(),
            *self.esperas_cara_grupo.values(),
            *self.litros_por_tipo.values(),
        ):
            muestras.reiniciar()
        self.servicio_suma = 0.0
        self.c.reiniciar()
        for g in self.c_grupo:
            self.c_grupo[g].reiniciar()
        for pr in self.c_producto:
            self.c_producto[pr].reiniciar()
        self.por_hora.reiniciar()
        self.calentamiento_terminado = True

    def cerrar(self, t: float) -> None:
        for serie in self.series:
            serie.cerrar(t)

    # --- Indicadores finales --------------------------------------------------
    @property
    def utilizacion_surtidores(self) -> float:
        """Fracción del tiempo que, en promedio, está ocupada cada cara."""
        total_caras = sum(g.caras for g in self.p.grupos) if self.p.estacion_real \
            else self.capacidad_surtidores
        return self.ocupados_surtidores.promedio / max(total_caras, 1)

    @property
    def utilizacion_cajas(self) -> float:
        return self.ocupadas_cajas.promedio / self.capacidad_cajas

    @property
    def fraccion_sin_combustible(self) -> float:
        """Fracción del tiempo medido en que la estación estuvo sin poder vender."""
        return self.sin_combustible.promedio

    @property
    def nivel_tanque_promedio(self) -> float:
        return self.nivel_tanque.promedio

    @property
    def nivel_servicio(self) -> float:
        """Fracción de la demanda de litros que se pudo satisfacer."""
        total = self.c.litros_vendidos + self.c.litros_no_vendidos
        return self.c.litros_vendidos / total if total else 1.0
