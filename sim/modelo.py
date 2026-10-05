"""Modelo de eventos discretos de la estación de servicio, en SimPy.

El sistema tiene DOS SUBSISTEMAS ACOPLADOS:

1. LÍNEAS DE ESPERA (el playón)

       llega -> cola de surtidores -> carga -> con probabilidad p: cola de caja -> compra
                     │                                                   │
                     └── abandona si espera > paciencia                  └── abandona

2. INVENTARIO (el tanque)

       cada carga descuenta litros del tanque. Cuando la posición de inventario
       (lo que hay + lo que viene en camino) cae por debajo del PUNTO DE PEDIDO, se
       pide un camión cisterna, que tarda un PLAZO DE ENTREGA aleatorio en llegar.

Los dos subsistemas están acoplados: si el tanque se vacía, no importa cuántos surtidores
haya, la estación no vende. Y al revés, cuantos más autos se atienden, más rápido se
consume el tanque. Por eso las dos decisiones (cuánta capacidad de atención y qué política
de reposición) compiten por la misma plata y no se pueden analizar por separado.

La demanda no es constante: cada día se sortea cuántos autos van a llegar con el método
Monte Carlo (tabla de frecuencias empírica) y esos autos se reparten en el día según el
perfil horario, mediante un proceso de Poisson no homogéneo.
"""

from __future__ import annotations

from dataclasses import dataclass

import simpy

from sim.config import MINUTOS_POR_DIA, ParametrosSimulacion
from sim.distribuciones import Aleatorio
from sim.estadisticas import Indicadores
from sim.traza import DT_INVENTARIO, DiaSimulado, Traza


@dataclass
class Auto:
    """La entidad del modelo, con sus atributos sorteados al llegar."""

    id: int
    t_llegada: float
    hora: int          # hora del día en que llegó (para los indicadores por franja)
    t_carga: float
    litros: float
    compra: bool       # atributo "tipo de cliente": solo carga / carga + compra
    t_compra: float


class EstacionDeServicio:
    """Los recursos de la estación, el tanque y la lógica de los procesos."""

    def __init__(
        self,
        env: simpy.Environment,
        p: ParametrosSimulacion,
        aleatorio: Aleatorio,
        indicadores: Indicadores,
        traza: Traza | None = None,
    ) -> None:
        self.env = env
        self.p = p
        self.az = aleatorio
        self.ind = indicadores
        self.traza = traza

        # Recursos con cola FIFO: es lo que hace SimPy por defecto.
        self.surtidores = simpy.Resource(env, capacity=p.surtidores)
        self.cajas = simpy.Resource(env, capacity=p.cajas)

        # Estado del inventario
        self.nivel = p.tanque.nivel_inicial
        self.litros_en_camino = 0.0
        self.pedidos_en_camino = 0
        self.hubo_quiebre_hoy = False

        # Demanda del día en curso (la fija el proceso de días). `tasas_hora` es la λ de
        # cada hora, precalculada una vez por día en lugar de recalcularla en cada llegada.
        self.autos_del_dia = int(p.demanda.media)
        self.tasas_hora = p.perfil.tasas_por_hora(self.autos_del_dia)
        self.numero_aleatorio_dia = 0
        self.autos_llegados_hoy = 0

        # Procesos
        env.process(self.correr_dias())
        env.process(self.generar_llegadas())
        if traza is not None:
            env.process(self.registrar_animacion())
            env.process(self.registrar_inventario())

    # =========================================================================
    # Procesos de control
    # =========================================================================
    def correr_dias(self):
        """Un proceso por día: sortea la demanda (Monte Carlo) o calcula determinista."""
        for dia in range(1, self.p.dias + 1):
            # --- Demanda: Monte Carlo o determinista según configuración ---
            if self.p.modo_determinista:
                autos, numero = self.az.determinista(self.p.autos_por_dia_fecha(dia))
            else:
                autos, numero = self.az.empirica(self.p.demanda, "demanda")

            self.autos_del_dia = autos
            self.tasas_hora = self.p.perfil.tasas_por_hora(autos)
            self.numero_aleatorio_dia = numero
            self.autos_llegados_hoy = 0
            self.hubo_quiebre_hoy = False

            antes = _foto(self.ind.c_total)
            yield self.env.timeout(MINUTOS_POR_DIA)
            despues = _foto(self.ind.c_total)

            if self.hubo_quiebre_hoy:
                self.ind.contar("dias_con_quiebre")

            if self.traza is not None:
                self.traza.registrar_dia(
                    DiaSimulado(
                        dia=dia,
                        numero_aleatorio=numero,
                        autos_sorteados=autos,
                        autos_llegados=self.autos_llegados_hoy,
                        atendidos=despues["atendidos_surtidor"] - antes["atendidos_surtidor"],
                        perdidos_cola=despues["perdidos_surtidor"] - antes["perdidos_surtidor"],
                        perdidos_sin_combustible=(
                            despues["perdidos_sin_combustible"]
                            - antes["perdidos_sin_combustible"]
                        ),
                        litros_vendidos=despues["litros_vendidos"] - antes["litros_vendidos"],
                        hubo_quiebre=self.hubo_quiebre_hoy,
                        en_calentamiento=dia <= self.p.dias_calentamiento,
                    )
                )

            # El calentamiento termina justo al cerrar su último día.
            if dia == self.p.dias_calentamiento:
                self.ind.reiniciar(self.env.now)

    def generar_llegadas(self):
        """Proceso de Poisson NO HOMOGÉNEO, con la tasa λ(t) que marca el perfil horario.

        Dentro de cada hora la tasa es constante, así que ahí el proceso es un Poisson
        común y el tiempo hasta la próxima llegada es exponencial con esa tasa. Cuando el
        sorteo se pasa del final de la hora, se avanza hasta el borde y se vuelve a
        sortear con la tasa de la hora siguiente: eso es exacto por la propiedad de FALTA
        DE MEMORIA de la exponencial (lo que ya esperó no cambia lo que falta esperar).

        Así, sin aproximaciones, las llegadas se concentran en las horas pico y se ralean
        de madrugada, que es lo que pasa en una estación de verdad.
        """
        contador = 0
        while True:
            ahora_min = self.env.now
            minuto_del_dia = ahora_min % MINUTOS_POR_DIA
            fin_de_hora = ahora_min - minuto_del_dia + (int(minuto_del_dia // 60) + 1) * 60

            tasa = self.tasas_hora[int(minuto_del_dia // 60)]
            if tasa <= 0:
                yield self.env.timeout(fin_de_hora - ahora_min)
                continue

            demora = self.az.exponencial(1.0 / tasa, "llegadas")
            if ahora_min + demora >= fin_de_hora:
                # La llegada caería en la hora siguiente, que tiene otra tasa:
                # se avanza hasta el borde y se vuelve a sortear.
                yield self.env.timeout(fin_de_hora - ahora_min)
                continue

            yield self.env.timeout(demora)

            contador += 1
            self.autos_llegados_hoy += 1
            ahora = self.env.now
            auto = Auto(
                id=contador,
                t_llegada=ahora,
                hora=int((ahora % MINUTOS_POR_DIA) // 60),
                t_carga=self.az.triangular(self.p.carga, "carga"),
                litros=self.az.triangular(self.p.litros, "litros"),
                compra=self.az.bernoulli(self.p.prob_compra, "decision"),
                t_compra=(
                    self.az.exponencial(self.p.compra.media, "compra")
                    if self.p.caja_exponencial
                    else self.az.triangular(self.p.compra, "compra")
                ),
            )
            self.env.process(self.atender(auto))

    def registrar_animacion(self):
        """Graba los cuadros de la animación, sólo durante el día elegido."""
        inicio, fin = self.p.ventana_animacion
        if inicio > 0:
            yield self.env.timeout(inicio)
        while self.env.now < fin:
            self.traza.capturar(
                t=self.env.now,
                surtidores_ocupados=self.surtidores.count,
                cola_surtidor=len(self.surtidores.queue),
                cajas_ocupadas=self.cajas.count,
                cola_caja=len(self.cajas.queue),
                atendidos=self.ind.c_total.atendidos_surtidor,
                perdidos_surtidor=self.ind.c_total.perdidos_surtidor,
                compras=self.ind.c_total.compras_atendidas,
                perdidos_caja=self.ind.c_total.perdidos_caja,
                nivel_tanque=self.nivel,
                perdidos_sin_combustible=self.ind.c_total.perdidos_sin_combustible,
                pedidos_en_camino=self.pedidos_en_camino,
                en_calentamiento=not self.ind.calentamiento_terminado,
            )
            yield self.env.timeout(self.p.dt_traza)

    def registrar_inventario(self):
        """Muestrea el nivel del tanque durante toda la corrida (gráfico del mes)."""
        while True:
            self.traza.capturar_inventario(self.env.now, self.nivel, self.pedidos_en_camino)
            yield self.env.timeout(DT_INVENTARIO)

    # =========================================================================
    # Inventario
    # =========================================================================
    def _actualizar_nivel(self, nuevo: float) -> None:
        self.nivel = nuevo
        self.ind.nivel_tanque.cambiar(self.env.now, nuevo)
        # Se considera que la estación está sin combustible cuando no alcanza ni para la
        # carga más chica posible.
        sin_stock = 1.0 if nuevo < self.p.litros.minimo else 0.0
        if sin_stock != self.ind.sin_combustible.valor:
            self.ind.sin_combustible.cambiar(self.env.now, sin_stock)

    def hay_combustible(self, litros: float) -> bool:
        return self.nivel >= litros

    def consumir(self, litros: float) -> None:
        """Descuenta del tanque y revisa si hay que pedir.

        No se acota en cero a propósito: si alguna vez quedara negativo sería un error de
        modelado, y el control de conservación de litros de `verificar.py` lo detectaría.
        """
        self._actualizar_nivel(self.nivel - litros)
        self.ind.contar("litros_vendidos", litros)
        self.revisar_punto_pedido()

    def revisar_punto_pedido(self) -> None:
        """Política (s, Q): si la posición de inventario cae bajo el punto de pedido, pide.

        La POSICIÓN de inventario es lo que hay en el tanque más lo que ya viene en camino.
        Usarla (en vez del nivel a secas) evita pedir dos veces lo mismo mientras el primer
        camión todavía está viajando.
        """
        posicion = self.nivel + self.litros_en_camino
        if posicion <= self.p.tanque.punto_pedido:
            self.env.process(self.pedir_camion())

    def pedir_camion(self):
        """Emite un pedido y espera el plazo de entrega del camión cisterna."""
        cantidad = self.p.tanque.cantidad_pedido
        self.litros_en_camino += cantidad
        self.pedidos_en_camino += 1
        self.ind.contar("pedidos_emitidos")

        plazo = self.az.triangular(self.p.tanque.plazo_entrega_minutos, "entrega")
        self.ind.plazo_entrega.agregar(plazo / 60.0)   # se registra en horas
        yield self.env.timeout(plazo)

        self.litros_en_camino -= cantidad
        self.pedidos_en_camino -= 1
        # No se puede meter más de lo que entra en el tanque.
        recibido = min(cantidad, self.p.tanque.capacidad - self.nivel)
        self._actualizar_nivel(self.nivel + recibido)
        self.ind.contar("litros_recibidos", recibido)
        self.ind.contar("pedidos_recibidos")

    def registrar_venta_perdida(self, auto: Auto, por_combustible: bool) -> None:
        """Un cliente que se va sin cargar: se pierde el combustible que habría comprado."""
        self.ind.contar("litros_no_vendidos", auto.litros)
        if por_combustible:
            self.ind.contar("perdidos_sin_combustible")
            self.hubo_quiebre_hoy = True
        else:
            self.ind.contar("perdidos_surtidor")
        self.ind.por_hora.contar_perdido(auto.hora)

    # =========================================================================
    # Proceso principal: el recorrido de un auto
    # =========================================================================
    def atender(self, auto: Auto):
        """Recorrido completo de un auto por la estación."""
        ahora = self.env.now
        self.ind.contar("llegadas")
        self.ind.por_hora.contar_llegada(auto.hora)

        # ---------- ¿Hay combustible para atenderlo? ----------
        if not self.hay_combustible(auto.litros):
            # Cartel de "sin nafta": ni siquiera hace la cola.
            self.registrar_venta_perdida(auto, por_combustible=True)
            return

        # ---------- Cola y servicio en el surtidor ----------
        self.ind.cola_surtidor.sumar(ahora, +1)
        with self.surtidores.request() as pedido:
            if pedido.triggered:
                # Había un surtidor libre: entra directo. No se agenda el reloj de
                # paciencia porque no va a hacer falta (esto además acelera la corrida).
                yield pedido
                atendido = True
            else:
                resultado = yield pedido | self.env.timeout(self.p.paciencia_surtidor)
                atendido = pedido in resultado
            self.ind.cola_surtidor.sumar(self.env.now, -1)

            if not atendido:
                # Se cansó de esperar: venta de combustible perdida.
                self.registrar_venta_perdida(auto, por_combustible=False)
                return

            # Pudo haberse acabado el combustible mientras hacía la cola.
            if not self.hay_combustible(auto.litros):
                self.registrar_venta_perdida(auto, por_combustible=True)
                return

            espera_real = self.env.now - auto.t_llegada
            self.ind.espera_surtidor.agregar(espera_real)
            self.ind.por_hora.contar_espera(auto.hora, espera_real)

            # El combustible se descuenta AL EMPEZAR a cargar, no al terminar. Si se
            # descontara al final, varios autos cargando a la vez podrían pasar cada uno
            # el control de stock y entre todos sacar más litros de los que hay.
            self.consumir(auto.litros)

            self.ind.ocupados_surtidores.sumar(self.env.now, +1)
            yield self.env.timeout(auto.t_carga)
            self.ind.ocupados_surtidores.sumar(self.env.now, -1)
            self.ind.contar("atendidos_surtidor")
        # Al salir del `with`, el surtidor queda libre para el siguiente de la cola.

        if not auto.compra:
            self.ind.tiempo_sistema.agregar(self.env.now - auto.t_llegada)
            return

        # ---------- Cola y servicio en la caja del minimarket ----------
        self.ind.contar("entraron_minimarket")
        t_entrada_cola = self.env.now
        self.ind.cola_caja.sumar(t_entrada_cola, +1)
        with self.cajas.request() as pedido:
            if pedido.triggered:
                yield pedido
                cobrado = True
            else:
                resultado = yield pedido | self.env.timeout(self.p.paciencia_caja)
                cobrado = pedido in resultado
            self.ind.cola_caja.sumar(self.env.now, -1)

            if not cobrado:
                # Deja la compra y se va: el combustible ya se vendió, la compra no.
                self.ind.contar("perdidos_caja")
                self.ind.tiempo_sistema.agregar(self.env.now - auto.t_llegada)
                return

            self.ind.espera_caja.agregar(self.env.now - t_entrada_cola)
            self.ind.ocupadas_cajas.sumar(self.env.now, +1)
            yield self.env.timeout(auto.t_compra)
            self.ind.ocupadas_cajas.sumar(self.env.now, -1)
            self.ind.contar("compras_atendidas")

        self.ind.tiempo_sistema.agregar(self.env.now - auto.t_llegada)


def _foto(contadores) -> dict[str, float]:
    """Copia de los contadores que hacen falta para cerrar el día."""
    return {
        "atendidos_surtidor": contadores.atendidos_surtidor,
        "perdidos_surtidor": contadores.perdidos_surtidor,
        "perdidos_sin_combustible": contadores.perdidos_sin_combustible,
        "litros_vendidos": contadores.litros_vendidos,
    }


def simular(
    p: ParametrosSimulacion,
    semilla: int,
    con_traza: bool = False,
) -> tuple[Indicadores, Traza | None]:
    """Corre UNA réplica del modelo y devuelve los indicadores (y la traza, si se pidió)."""
    env = simpy.Environment()
    aleatorio = Aleatorio(semilla)
    indicadores = Indicadores(
        capacidad_surtidores=p.surtidores,
        capacidad_cajas=p.cajas,
        nivel_inicial_tanque=p.tanque.nivel_inicial,
        capacidad_tanque=p.tanque.capacidad,
    )
    traza = Traza() if con_traza else None

    EstacionDeServicio(env, p, aleatorio, indicadores, traza)
    env.run(until=p.duracion)
    indicadores.cerrar(p.duracion)

    if traza is not None:
        # La traza es lo que mira la interfaz: se le copian los indicadores por hora.
        traza.llegadas_por_hora = list(indicadores.por_hora.llegadas)
        traza.espera_por_hora = [
            indicadores.por_hora.espera_promedio(h) for h in range(24)
        ]
        traza.perdidos_por_hora = list(indicadores.por_hora.perdidos)

    return indicadores, traza
