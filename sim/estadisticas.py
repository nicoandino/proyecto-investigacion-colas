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

Nota de implementación: los colectores NO guardan la historia completa de valores. Una
corrida de 30 días mueve decenas de miles de clientes y guardar cada cambio de estado
gastaría memoria sin aportar nada: los gráficos se arman con la traza, que muestrea el
sistema a intervalos regulares.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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

    # Clientes
    llegadas: int = 0
    atendidos_surtidor: int = 0
    perdidos_surtidor: int = 0          # abandono por cola larga
    perdidos_sin_combustible: int = 0   # se fueron porque no había nafta
    entraron_minimarket: int = 0
    compras_atendidas: int = 0
    perdidos_caja: int = 0

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


class Indicadores:
    """Todos los colectores de una corrida, en un solo objeto."""

    def __init__(
        self,
        capacidad_surtidores: int,
        capacidad_cajas: int,
        nivel_inicial_tanque: float = 0.0,
        capacidad_tanque: float = 1.0,
    ) -> None:
        self.capacidad_surtidores = capacidad_surtidores
        self.capacidad_cajas = capacidad_cajas
        self.capacidad_tanque = capacidad_tanque

        # Colas y servidores
        self.cola_surtidor = SerieTemporal()
        self.cola_caja = SerieTemporal()
        self.ocupados_surtidores = SerieTemporal()
        self.ocupadas_cajas = SerieTemporal()

        # Esperas
        self.espera_surtidor = Muestras()
        self.espera_caja = Muestras()
        self.tiempo_sistema = Muestras()

        # Inventario
        self.nivel_tanque = SerieTemporal(valor_inicial=nivel_inicial_tanque)
        self.sin_combustible = SerieTemporal()   # indicador 0/1: fracción de tiempo sin nafta
        self.plazo_entrega = Muestras()

        self.c = Contadores()
        self.c_total = Contadores()
        self.por_hora = PorHora()
        self.calentamiento_terminado = False

    @property
    def series(self) -> tuple[SerieTemporal, ...]:
        return (
            self.cola_surtidor,
            self.cola_caja,
            self.ocupados_surtidores,
            self.ocupadas_cajas,
            self.nivel_tanque,
            self.sin_combustible,
        )

    def contar(self, nombre: str, cantidad: float = 1) -> None:
        """Incrementa un contador, tanto el del período de medición como el total."""
        for contadores in (self.c, self.c_total):
            setattr(contadores, nombre, getattr(contadores, nombre) + cantidad)

    def reiniciar(self, t: float) -> None:
        """Fin del período de calentamiento: se descarta todo lo medido hasta acá."""
        for serie in self.series:
            serie.reiniciar(t)
        for muestras in (
            self.espera_surtidor,
            self.espera_caja,
            self.tiempo_sistema,
            self.plazo_entrega,
        ):
            muestras.reiniciar()
        self.c.reiniciar()
        self.por_hora.reiniciar()
        self.calentamiento_terminado = True

    def cerrar(self, t: float) -> None:
        for serie in self.series:
            serie.cerrar(t)

    # --- Indicadores finales --------------------------------------------------
    @property
    def utilizacion_surtidores(self) -> float:
        """Fracción del tiempo que, en promedio, está ocupado cada surtidor."""
        return self.ocupados_surtidores.promedio / self.capacidad_surtidores

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
