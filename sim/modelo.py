"""Modelo de eventos discretos de la estación de servicio, en SimPy.

El sistema tiene DOS SUBSISTEMAS ACOPLADOS:

1. LÍNEAS DE ESPERA (el playón)

       llega -> cola de caras -> carga -> con probabilidad p: cola de caja -> compra
                     │                                                   │
                     └── abandona si espera > paciencia                  └── abandona

2. INVENTARIO (los tanques por producto)

       cada carga descuenta litros del tanque de su producto. Cuando la posición de
       inventario (lo que hay + lo que viene en camino) cae por debajo del PUNTO DE
       PEDIDO, se pide un camión cisterna, que tarda un PLAZO DE ENTREGA aleatorio.

Los dos subsistemas están acoplados: si el tanque se vacía, no importa cuántas caras
haya, la estación no vende ese producto. Y al revés, cuantos más autos se atienden,
más rápido se consume el tanque. Por eso las dos decisiones (cuánta capacidad de
atención y qué política de reposición) compiten por la misma plata.

Desde la Fase 2 hay DOS montajes:

  - Estación REAL (§7): 3 grupos (A nafta 4 caras, B diésel 2, C GNC 6), 5 productos,
    cliente "producto primero" con Monte Carlo de 5 pasos, playeros por turno
    (servidores = mín(caras libres, playeros en turno)), cola finita y un tanque con
    política (s, Q) por producto líquido.
  - Caso CLÁSICO (`ParametrosSimulacion.clasico()`): 1 grupo, 1 producto, sin playeros,
    sin cola finita. Reproduce EXACTAMENTE los números dorados (§14.1): por eso su
    rama conserva el orden original de sorteos y de eventos.

La demanda no es constante: cada día se sortea cuántos autos van a llegar (Monte Carlo
de la tabla empírica, o "demanda esperada" derivada de los litros por mes) y esos autos
se reparten en el día según el perfil horario, mediante un proceso de Poisson no
homogéneo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import simpy

from sim.config import ANO_REFERENCIA, MINUTOS_POR_DIA, ParametrosSimulacion
from sim.distribuciones import Aleatorio
from sim.estadisticas import Indicadores
from sim.gnc import calendario_de_episodios, intervalos_de_corte, minutos_de_corte_en_dia
from sim.red import demora_de_viaje, mes_del_dia
from sim.traza import DT_INVENTARIO, DiaSimulado, Traza

MOTIVOS = ("sin_combustible", "abandono_espera", "cola_llena", "corte_gnc", "abandono_caja")


@dataclass
class Auto:
    """La entidad del modelo, con sus atributos sorteados al llegar."""

    id: int
    t_llegada: float
    hora: int          # hora del día en que llegó (para los indicadores por franja)
    producto: str      # "super" | "vpower" | "diesel_g2" | "diesel_g3" | "gnc"
    tipo: str          # "moto" | "auto" | "pick_up" | "camion" | "auto_gnc"
    litros: float      # litros (o m³ para el GNC)
    t_carga: float
    compra: bool       # atributo "tipo de cliente": solo carga / carga + compra
    t_compra: float
    grupo: str = ""    # "A" | "B" | "C" (en el clásico queda vacío)
    numero_producto: int = 0   # número aleatorio (01-100) del sorteo de producto
    numero_tipo: int = 0       # número aleatorio del sorteo de tipo de vehículo
    espera_playero: bool = False   # tiene la cara pero todavía no un playero (animación)
    afectado_gnc: bool = False     # se topó con un corte de GNC (se cuenta una sola vez)
    migrado: bool = False          # era de GNC y pasó a Súper durante el corte


class EstacionDeServicio:
    """Los recursos de la estación, los tanques y la lógica de los procesos."""

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

        self.hubo_quiebre_hoy = False
        # Pedidos en camino por producto: [(minuto del pedido, plazo en minutos), ...]
        # (la animación dibuja el camión según cuánto del plazo ya transcurrió).
        self.pedidos_abiertos: dict[str, list[tuple[float, float, float]]] = {}
        self.autos_del_dia = int(p.demanda.media)
        self.tasas_hora = p.perfil.tasas_por_hora(self.autos_del_dia)
        self.numero_aleatorio_dia = 0
        self.autos_llegados_hoy = 0

        if p.estacion_real:
            self._montar_real()
        else:
            self._montar_clasico()

        # Procesos
        env.process(self.correr_dias())
        env.process(self.generar_llegadas())
        if traza is not None:
            env.process(self.registrar_animacion())
            env.process(self.registrar_inventario())

    # =========================================================================
    # Montaje de los recursos
    # =========================================================================
    def _montar_clasico(self) -> None:
        """El caso clásico: una cola FIFO única y N surtidores, sin playeros."""
        self.es_real = False
        self.surtidores = simpy.Resource(self.env, capacity=self.p.surtidores)
        self.cajas = simpy.Resource(self.env, capacity=self.p.cajas)
        self.playeros = None
        self.gnc_cortado = 0
        self.compresores = None
        self.intervalos_gnc: list[tuple[float, float]] = []
        self.nivel = self.p.tanque.nivel_inicial
        self.litros_en_camino = 0.0
        self.pedidos_en_camino = 0

    def _montar_real(self) -> None:
        """La estación real: grupos de caras, playeros por turno, cola finita."""
        self.es_real = True
        self.info_grupo = {g.id: g for g in self.p.grupos}
        self.gnc_cortado = 0                # 0 normal · 1 cortado · 2 compresores al 50 %

        # Qué auto ocupa cada cara (carril) y quién espera en cada zona: sólo sirven para
        # dibujar la animación (el motor no los consulta).
        self.carriles: dict[str, list[Auto | None]] = {
            g.id: [None] * g.caras for g in self.p.grupos
        }
        self.cola_lista: dict[str, list[Auto]] = {g.id: [] for g in self.p.grupos}

        # Caras: un recurso por grupo (FIFO) o una fila por cara, según la disciplina.
        self.cola_recurso: dict[str, simpy.Resource] = {}
        self.caras: dict[str, tuple[simpy.Resource, ...]] = {}
        for grupo in self.p.grupos:
            if self.p.disciplina_cola == "por_grupo":
                self.cola_recurso[grupo.id] = simpy.Resource(
                    self.env, capacity=grupo.caras
                )
            else:
                self.caras[grupo.id] = tuple(
                    simpy.Resource(self.env, capacity=1) for _ in range(grupo.caras)
                )

        # Playeros por turno: reservas ficticias con prioridad -1 ajustan la capacidad.
        self.max_playeros = max(self.p.playeros_por_turno)
        self.playeros = simpy.PriorityResource(self.env, capacity=self.max_playeros)
        self.reservas_playeros: list[simpy.events.Event] = []
        self.env.process(self.controlar_turnos())

        # Cajas del minimarket: 1 caja constante (PER-02 = 1·1·1).
        self.cajas = simpy.Resource(self.env, capacity=self.p.cajas)

        # GNC (§7.5): los compresores limitan las cargas simultáneas (no las 6 caras) y los
        # episodios de corte invernales se sortean ahora, con su stream propio.
        g = self.p.gnc
        self.compresores = None
        self.reservas_compresores: list[simpy.events.Event] = []
        self.episodios_gnc: list[tuple[int, int]] = []
        self.intervalos_gnc = []
        if g is not None:
            self.compresores = simpy.PriorityResource(self.env, capacity=g.compresores)
            self.episodios_gnc = calendario_de_episodios(
                g, self.az, date(ANO_REFERENCIA, *self.p.fecha_inicio), self.p.dias
            )
            self.intervalos_gnc = intervalos_de_corte(g, self.episodios_gnc, self.p.dias)
            if self.intervalos_gnc:
                self.env.process(self.controlar_gnc())

        # Inventario por producto líquido.
        self.niveles: dict[str, float] = {
            i.producto: i.nivel_inicial for i in self.p.inventario
        }
        self.en_camino: dict[str, float] = {i.producto: 0.0 for i in self.p.inventario}
        self.pedidos_en_camino: dict[str, int] = {i.producto: 0 for i in self.p.inventario}
        self.hubo_quiebre_hoy = {i.producto: False for i in self.p.inventario}
        self.info_inventario = {i.producto: i for i in self.p.inventario}

        # Pesos de sorteo: producto (§14.2) y tipo de vehículo por producto (VEH-00).
        self.pesos_producto = self.p.pesos_llegada()
        self.productos_liquidos = [pr for pr in self.p.productos if not pr.es_gnc]
        tipos = {t.id: t for t in self.p.tipos_vehiculo}
        self.info_tipo = tipos
        self.tipos_en_orden = tuple(t.id for t in self.p.tipos_vehiculo)
        matriz = dict(self.p.matriz_tipos)
        self.pesos_tipo = {
            pr.id: matriz[pr.id] for pr in self.p.productos
        }
        self.tipo_gnc = "auto_gnc"

        # Carga mínima de cada producto (para el indicador "sin combustible").
        self.min_carga = {}
        for pr in self.p.productos:
            if pr.es_gnc:
                continue
            minimos = [
                tipos[t].litros.minimo for t, w in zip(self.tipos_en_orden, matriz[pr.id])
                if w > 0 and not tipos[t].es_gnc
            ]
            self.min_carga[pr.id] = min(minimos)

        self._actualizar_sin_combustible()

    # =========================================================================
    # Playeros por turno (§7.2): capacidad - reservas = playeros del turno
    # =========================================================================
    def controlar_turnos(self):
        """En cada borde de turno ajusta las reservas ficticias de playeros."""
        turnos = list(self.p.turnos)
        self._ajustar_playeros(turnos[0][1])
        while True:                                  # los turnos se repiten todos los días
            for i, (hora, _) in enumerate(turnos):
                siguiente = turnos[(i + 1) % len(turnos)]
                borde = ((siguiente[0] - hora) % 24) * 60.0
                yield self.env.timeout(borde)
                self._ajustar_playeros(siguiente[1])

    def _ajustar_playeros(self, playeros_del_turno: int) -> None:
        """Toma (prioridad -1) o libera reservas hasta `capacidad - reservas = turno`."""
        objetivo = self.max_playeros - playeros_del_turno
        actual = len(self.reservas_playeros)
        if objetivo > actual:
            for _ in range(objetivo - actual):
                self.reservas_playeros.append(self.playeros.request(priority=-1))
        elif objetivo < actual:
            for _ in range(actual - objetivo):
                pedido = self.reservas_playeros.pop()
                if pedido.triggered:
                    self.playeros.release(pedido)
                else:
                    pedido.cancel()
        self.ind.playeros_en_turno.cambiar(self.env.now, float(playeros_del_turno))

    # =========================================================================
    # GNC: episodios de corte y compresores (§7.5)
    # =========================================================================
    def controlar_gnc(self):
        """Aplica el calendario de cortes: GNC cortado (o compresores al 50 %) en cada tramo."""
        parcial = self.p.gnc.forma == "parcial_50"
        for desde, hasta in self.intervalos_gnc:
            if desde > self.env.now:
                yield self.env.timeout(desde - self.env.now)
            if parcial:
                self.gnc_cortado = 2
                self._ajustar_compresores(max(1, self.p.gnc.compresores // 2))
            else:
                self.gnc_cortado = 1
            yield self.env.timeout(hasta - self.env.now)
            self.gnc_cortado = 0
            if parcial:
                self._ajustar_compresores(self.p.gnc.compresores)

    def _ajustar_compresores(self, disponibles: int) -> None:
        """Reservas ficticias (prioridad −1) bajan la capacidad, igual que con los playeros."""
        objetivo = self.p.gnc.compresores - disponibles
        actual = len(self.reservas_compresores)
        if objetivo > actual:
            for _ in range(objetivo - actual):
                self.reservas_compresores.append(self.compresores.request(priority=-1))
        elif objetivo < actual:
            for _ in range(actual - objetivo):
                pedido = self.reservas_compresores.pop()
                if pedido.triggered:
                    self.compresores.release(pedido)
                else:
                    pedido.cancel()

    def _compresores_habilitados(self) -> int:
        if self.compresores is None:
            return 0
        return self.compresores.capacity - len(self.reservas_compresores)

    def _gnc_al_llegar_con_corte(self, auto: Auto) -> bool:
        """Cliente GNC que llega con el GNC cortado: pasa a Súper o se pierde (§7.5).

        Devuelve True si migró (sigue su recorrido como cliente de nafta). Conserva su
        identidad (el mismo auto) pero se vuelve a sortear cuántos litros carga, con el
        stream "migracion", y se re-etiquetan sus llegadas para que cada grupo siga
        cerrando (llegadas = atendidos + perdidos + adentro).
        """
        auto.afectado_gnc = True
        self.ind.contar("gnc_afectados")
        g = self.p.gnc
        if self.az.bernoulli(g.migracion_a_nafta, "migracion"):
            tipo = self.info_tipo["auto"]
            auto.litros = self.az.triangular(tipo.litros, "migracion")
            auto.t_carga = self.az.triangular(self.p.carga, "migracion")
            grupo_viejo = auto.grupo
            auto.producto = "super"
            auto.grupo = next(pr.grupo for pr in self.p.productos if pr.id == "super")
            auto.tipo = "auto"
            auto.migrado = True
            self.ind.contar_producto("gnc", "llegadas", -1)
            self.ind.contar_grupo(grupo_viejo, "llegadas", -1)
            self.ind.contar_producto(auto.producto, "llegadas")
            self.ind.contar_grupo(auto.grupo, "llegadas")
            self.ind.contar("migrados_gnc_a_nafta")
            return True
        self.registrar_perdida(auto, motivo="corte_gnc")
        return False

    # =========================================================================
    # Procesos de control
    # =========================================================================
    def correr_dias(self):
        """Un proceso por día: sortea la demanda (Monte Carlo) o deriva la esperada."""
        for dia in range(1, self.p.dias + 1):
            if self.p.modo_demanda == "esperada":
                autos, numero = self.az.esperada(self.p.autos_por_dia_fecha(dia))
            elif self.p.tabla_demanda_relativa and self.es_real:
                # Monte Carlo real: un factor relativo (DEM-07) multiplica el nivel
                # del día derivado de los litros del mes.
                factor, numero = self.az.empirica(self.p.demanda_relativa, "demanda")
                liquidos = (
                    self.p.litros_del_dia(dia) / self.p.litros_medios_por_cliente
                )
                autos = round(liquidos * factor / (1.0 - self.p.pct_gnc))
            else:
                autos, numero = self.az.empirica(self.p.demanda, "demanda")

            self.autos_del_dia = autos
            self.tasas_hora = self.p.perfil.tasas_por_hora(autos)
            self.numero_aleatorio_dia = numero
            self.autos_llegados_hoy = 0
            self.hubo_quiebre_hoy = (
                {i.producto: False for i in self.p.inventario} if self.es_real else False
            )

            antes = _foto(self.ind.c_total)
            antes_gnc = self._conteo_gnc()
            yield self.env.timeout(MINUTOS_POR_DIA)
            despues = _foto(self.ind.c_total)
            despues_gnc = self._conteo_gnc()
            minutos_corte = (
                minutos_de_corte_en_dia(self.intervalos_gnc, dia - 1) if self.es_real else 0.0
            )
            if minutos_corte > 0:
                self.ind.contar("dias_con_corte_gnc")

            if self.es_real:
                if any(self.hubo_quiebre_hoy.values()):
                    self.ind.contar("dias_con_quiebre")
                for producto, quiebre in self.hubo_quiebre_hoy.items():
                    if quiebre:
                        self.ind.contar_producto(producto, "dias_con_quiebre")
            elif self.hubo_quiebre_hoy:
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
                        hubo_quiebre=(
                            any(self.hubo_quiebre_hoy.values())
                            if self.es_real else self.hubo_quiebre_hoy
                        ),
                        en_calentamiento=dia <= self.p.dias_calentamiento,
                        gnc_atendidos=despues_gnc[0] - antes_gnc[0],
                        gnc_migrados=despues_gnc[1] - antes_gnc[1],
                        gnc_perdidos=despues_gnc[2] - antes_gnc[2],
                        gnc_corte_min=minutos_corte,
                    )
                )

            # El calentamiento termina justo al cerrar su último día.
            if dia == self.p.dias_calentamiento:
                self.ind.reiniciar(self.env.now)

    def _conteo_gnc(self) -> tuple[int, int, int]:
        """(atendidos GNC, migrados a nafta, perdidos por el corte), acumulados."""
        c = self.ind.c_total
        return (
            self.ind.c_producto_total["gnc"].atendidos,
            c.migrados_gnc_a_nafta,
            c.perdidos_corte_gnc,
        )

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
            auto = self._crear_auto(contador, ahora)
            self.env.process(self.atender(auto))

    def _crear_auto(self, contador: int, ahora: float) -> Auto:
        """Sorteo de todos los atributos del cliente AL LLEGAR (streams propios).

        El orden de los sorteos es parte del contrato de reproducibilidad:
          - clásico: t_carga, litros, compra, t_compra (el orden original, para los
            dorados);
          - real: producto (Monte Carlo), tipo de vehículo (Monte Carlo), litros,
            t_carga, compra, t_compra.
        """
        hora = int((ahora % MINUTOS_POR_DIA) // 60)
        if not self.es_real:
            compra = self.az.bernoulli(self.p.prob_compra, "decision")
            t_compra = (
                self.az.exponencial(self.p.compra.media, "compra")
                if self.p.caja_exponencial
                else self.az.triangular(self.p.compra, "compra")
            )
            return Auto(
                id=contador,
                t_llegada=ahora,
                hora=hora,
                producto="super",
                tipo="auto",
                t_carga=self.az.triangular(self.p.carga, "carga"),
                litros=self.az.triangular(self.p.litros, "litros"),
                compra=compra,
                t_compra=t_compra,
            )

        # --- Producto (Monte Carlo de 5 pasos, tabla visible en la interfaz) ---
        i_producto, n_producto = self.az.discreta_con_numero(
            self.pesos_producto, "producto"
        )
        producto = self.p.productos[i_producto]
        grupo = producto.grupo

        # --- Tipo de vehículo condicionado al producto (segunda tabla) ---
        pesos_tipo = self.pesos_tipo[producto.id]
        i_tipo, n_tipo = self.az.discreta_con_numero(pesos_tipo, "tipo_vehiculo")
        tipo = self.tipo_gnc if producto.es_gnc else self.tipos_en_orden[i_tipo]
        info_tipo = self.info_tipo[tipo]

        litros = self.az.triangular(info_tipo.litros, "litros")
        if producto.id == "gnc":
            t_carga = self.az.triangular(self.p.carga_gnc, "carga")   # TIE-04
        else:
            t_carga = self.az.triangular(self.p.carga, "carga")       # TIE-02
        if info_tipo.es_camion:
            t_carga += litros / 90.0                      # TIE-03: alto caudal
        compra = self.az.bernoulli(self.p.prob_compra, "decision")
        t_compra = (
            self.az.exponencial(self.p.compra.media, "compra")
            if self.p.caja_exponencial
            else self.az.triangular(self.p.compra, "compra")
        )
        return Auto(
            id=contador,
            t_llegada=ahora,
            hora=hora,
            producto=producto.id,
            tipo=tipo,
            litros=litros,
            t_carga=t_carga,
            compra=compra,
            t_compra=t_compra,
            grupo=grupo,
            numero_producto=n_producto,
            numero_tipo=n_tipo,
        )

    def registrar_animacion(self):
        """Graba los cuadros de la animación, sólo durante el día elegido."""
        inicio, fin = self.p.ventana_animacion
        if inicio > 0:
            yield self.env.timeout(inicio)
        while self.env.now < fin:
            self.traza.capturar(
                t=self.env.now,
                surtidores_ocupados=self._caras_ocupadas(),
                cola_surtidor=self._cola_total(),
                cajas_ocupadas=self.cajas.count,
                cola_caja=len(self.cajas.queue),
                atendidos=self.ind.c_total.atendidos_surtidor,
                perdidos_surtidor=self.ind.c_total.perdidos_surtidor,
                compras=self.ind.c_total.compras_atendidas,
                perdidos_caja=self.ind.c_total.perdidos_caja,
                nivel_tanque=self._nivel_total(),
                perdidos_sin_combustible=self.ind.c_total.perdidos_sin_combustible,
                pedidos_en_camino=self._pedidos_en_camino_total(),
                en_calentamiento=not self.ind.calentamiento_terminado,
                playeros_ocupados=int(self.ind.playeros_ocupados.valor),
                playeros_en_turno=int(self.ind.playeros_en_turno.valor),
                perdidos_cola_llena=self.ind.c_total.perdidos_cola_llena,
                gnc_cortado=int(self.gnc_cortado),
                compresores_ocupados=int(self.ind.compresores_ocupados.valor),
                compresores_total=self._compresores_habilitados(),
                migrados_gnc=self.ind.c_total.migrados_gnc_a_nafta,
                perdidos_corte_gnc=self.ind.c_total.perdidos_corte_gnc,
                grupos=self._foto_grupos(),
                tanques=self._foto_tanques(),
            )
            yield self.env.timeout(self.p.dt_traza)

    # Códigos de los carriles en la foto: -1 libre · 2·k cargando · 2·k+1 con la cara
    # ocupada esperando al playero (k = índice del producto en `p.productos`).
    def _indice_producto(self, producto: str) -> int:
        for i, pr in enumerate(self.p.productos):
            if pr.id == producto:
                return i
        return 0

    def _foto_grupos(self) -> tuple:
        """((id, carriles, cola, largo de la cola, rechazados), ...) de cada zona."""
        if not self.es_real:
            ocupadas = self.surtidores.count
            carriles = tuple(0 if i < ocupadas else -1 for i in range(self.p.surtidores))
            largo = len(self.surtidores.queue)
            return (("A", carriles, (0,) * min(largo, 24), largo, 0),)
        salida = []
        for grupo in self.p.grupos:
            carriles = tuple(
                -1 if auto is None
                else 2 * self._indice_producto(auto.producto) + (1 if auto.espera_playero else 0)
                for auto in self.carriles[grupo.id]
            )
            cola = self.cola_lista[grupo.id]
            salida.append(
                (
                    grupo.id,
                    carriles,
                    tuple(self._indice_producto(a.producto) for a in cola[:24]),
                    len(cola),
                    self.ind.c_grupo_total[grupo.id].perdidos_cola_llena,
                )
            )
        return tuple(salida)

    def _foto_tanques(self) -> tuple:
        """((producto, nivel, litros en camino, progreso del camión, horas que faltan), ...)."""
        ahora = self.env.now
        if not self.es_real:
            niveles = (("super", self.nivel, self.litros_en_camino),)
        else:
            niveles = tuple(
                (i.producto, self.niveles[i.producto], self.en_camino[i.producto])
                for i in self.p.inventario
            )
        salida = []
        for producto, nivel, en_camino in niveles:
            abiertos = self.pedidos_abiertos.get(producto, [])
            if abiertos:
                # El camión que llega primero (el que menos falta).
                t0, plazo, demora = min(abiertos, key=lambda x: x[0] + x[1])
                progreso = min(1.0, max(0.0, (ahora - t0) / plazo))
                faltan_horas = max(0.0, (t0 + plazo - ahora) / 60.0)
                demora_horas = demora / 60.0
            else:
                progreso, faltan_horas, demora_horas = -1.0, 0.0, 0.0
            salida.append((producto, nivel, en_camino, progreso, faltan_horas, demora_horas))
        return tuple(salida)

    def registrar_inventario(self):
        """Muestrea el nivel de los tanques durante toda la corrida (gráfico del mes)."""
        while True:
            self.traza.capturar_inventario(
                self.env.now,
                self._nivel_total(),
                self._pedidos_en_camino_total(),
                tuple(self.niveles[i.producto] for i in self.p.inventario)
                if self.es_real else (),
            )
            yield self.env.timeout(DT_INVENTARIO)

    # =========================================================================
    # Inventario
    # =========================================================================
    def _nivel_total(self) -> float:
        if self.es_real:
            return sum(self.niveles.values())
        return self.nivel

    def _pedidos_en_camino_total(self) -> int:
        if self.es_real:
            return sum(self.pedidos_en_camino.values())
        return self.pedidos_en_camino

    def _caras_ocupadas(self) -> int:
        if not self.es_real:
            return self.surtidores.count
        if self.cola_recurso:
            return sum(r.count for r in self.cola_recurso.values())
        return sum(c.count for caras in self.caras.values() for c in caras)

    def _cola_total(self) -> int:
        if not self.es_real:
            return len(self.surtidores.queue)
        if self.cola_recurso:
            return sum(len(r.queue) for r in self.cola_recurso.values())
        return sum(len(c.queue) for caras in self.caras.values() for c in caras)

    def _actualizar_nivel_clasico(self, nuevo: float) -> None:
        self.nivel = nuevo
        self.ind.nivel_tanque.cambiar(self.env.now, nuevo)
        sin_stock = 1.0 if nuevo < self.p.litros.minimo else 0.0
        if sin_stock != self.ind.sin_combustible.valor:
            self.ind.sin_combustible.cambiar(self.env.now, sin_stock)

    def _actualizar_niveles(self, producto: str, nuevo: float) -> None:
        self.niveles[producto] = nuevo
        self.ind.niveles[producto].cambiar(self.env.now, nuevo)
        self.ind.nivel_tanque.cambiar(self.env.now, self._nivel_total())
        self._actualizar_sin_combustible()

    def _actualizar_sin_combustible(self) -> None:
        """La estación está 'sin combustible' cuando ningún líquido alcanza para su
        carga mínima (el GNC no entra: en la Fase 2 nunca se corta)."""
        sin_stock = 1.0 if all(
            self.niveles[p] < self.min_carga[p] for p in self.niveles
        ) else 0.0
        if sin_stock != self.ind.sin_combustible.valor:
            self.ind.sin_combustible.cambiar(self.env.now, sin_stock)

    def hay_combustible(self, auto: Auto) -> bool:
        if not self.es_real:
            return self.nivel >= auto.litros
        if auto.producto == "gnc":
            return self.gnc_cortado != 1         # 1 = corte total (2 = sólo menos compresores)
        return self.niveles[auto.producto] >= auto.litros

    def consumir(self, auto: Auto) -> None:
        """Descuenta del tanque del producto y revisa si hay que pedir."""
        if not self.es_real:
            self._actualizar_nivel_clasico(self.nivel - auto.litros)
            self.ind.contar("litros_vendidos", auto.litros)
            self.ind.contar_producto(auto.producto, "litros_vendidos", auto.litros)
            self.revisar_punto_pedido_clasico()
            return
        if auto.producto == "gnc":
            # Sin tanque: sólo se registran los m³ del producto (no se suman a los litros).
            self.ind.contar_producto("gnc", "litros_vendidos", auto.litros)
            return
        nuevo = self.niveles[auto.producto] - auto.litros
        self._actualizar_niveles(auto.producto, nuevo)
        self.ind.contar("litros_vendidos", auto.litros)
        self.ind.contar_producto(auto.producto, "litros_vendidos", auto.litros)
        self.revisar_punto_pedido(auto.producto)

    def revisar_punto_pedido_clasico(self) -> None:
        posicion = self.nivel + self.litros_en_camino
        if posicion <= self.p.tanque.punto_pedido:
            self.env.process(self.pedir_camion_clasico())

    def pedir_camion_clasico(self):
        cantidad = self.p.tanque.cantidad_pedido
        self.litros_en_camino += cantidad
        self.pedidos_en_camino += 1
        self.ind.contar("pedidos_emitidos")

        plazo = self.az.triangular(self.p.tanque.plazo_entrega_minutos, "entrega")
        self.ind.plazo_entrega.agregar(plazo / 60.0)   # se registra en horas
        pedido = (self.env.now, plazo, 0.0)
        self.pedidos_abiertos.setdefault("super", []).append(pedido)
        yield self.env.timeout(plazo)
        self.pedidos_abiertos["super"].remove(pedido)

        self.litros_en_camino -= cantidad
        self.pedidos_en_camino -= 1
        recibido = min(cantidad, self.p.tanque.capacidad - self.nivel)
        self._actualizar_nivel_clasico(self.nivel + recibido)
        self.ind.contar("litros_recibidos", recibido)

    def revisar_punto_pedido(self, producto: str) -> None:
        """Política (s, Q) por producto: pide si la posición cae bajo el punto.

        La POSICIÓN de inventario es lo que hay en el tanque más lo que ya viene en
        camino. Usarla (en vez del nivel a secas) evita pedir dos veces lo mismo
        mientras el primer camión todavía está viajando.
        """
        posicion = self.niveles[producto] + self.en_camino[producto]
        if posicion <= self.info_inventario[producto].punto_pedido:
            self.env.process(self.pedir_camion(producto))

    def pedir_camion(self, producto: str):
        """Emite un pedido por producto y espera el plazo de entrega del camión."""
        info = self.info_inventario[producto]
        cantidad = info.cantidad_pedido
        self.en_camino[producto] += cantidad
        self.pedidos_en_camino[producto] += 1
        self.ind.contar("pedidos_emitidos")
        self.ind.contar_producto(producto, "pedidos_emitidos")

        plazo = self.az.triangular(info.plazo_entrega_minutos, f"entrega_{producto}")
        # Cortes de ruta (Fase 5): el plazo base ya incluye el viaje normal; si el camión
        # encuentra un corte, se le SUMA la demora (desvío o espera, la menor).
        demora = 0.0
        if self.p.red is not None:
            dia = int(self.env.now // MINUTOS_POR_DIA) + 1
            demora, _ = demora_de_viaje(
                self.p.red,
                self.env.now,
                mes_del_dia(self.p.fecha_inicio, dia),
                self.az,
                f"corte_ruta_{producto}",
            )
            if demora > 0:
                self.ind.contar_producto(producto, "viajes_demorados")
                self.ind.contar("viajes_demorados")
                self.ind.demora_ruta.agregar(demora / 60.0)
        plazo += demora
        self.ind.plazo_entrega.agregar(plazo / 60.0)   # se registra en horas
        pedido = (self.env.now, plazo, demora)
        self.pedidos_abiertos.setdefault(producto, []).append(pedido)
        yield self.env.timeout(plazo)
        self.pedidos_abiertos[producto].remove(pedido)

        self.en_camino[producto] -= cantidad
        self.pedidos_en_camino[producto] -= 1
        # No se puede meter más de lo que entra en el tanque.
        recibido = min(cantidad, info.capacidad - self.niveles[producto])
        self._actualizar_niveles(producto, self.niveles[producto] + recibido)
        self.ind.contar("litros_recibidos", recibido)
        self.ind.contar_producto(producto, "litros_recibidos", recibido)
        self.ind.contar_producto(producto, "pedidos_recibidos")

    # =========================================================================
    # Pérdidas (§7.6)
    # =========================================================================
    def registrar_perdida(self, auto: Auto, motivo: str) -> None:
        """Un cliente que se va sin cargar, con su motivo (taxonomía fija §7.6)."""
        if auto.producto != "gnc":
            self.ind.contar("litros_no_vendidos", auto.litros)
        self.ind.contar_producto(auto.producto, "litros_no_vendidos", auto.litros)
        if motivo == "sin_combustible":
            self.ind.contar("perdidos_sin_combustible")
            self.ind.contar_producto(auto.producto, "perdidos_sin_combustible")
            if auto.producto != "gnc":
                self.ind.contar_producto(
                    auto.producto, "litros_perdidos_sin_combustible", auto.litros
                )
            self._marcar_quiebre(auto.producto)
            if self.es_real:
                self.ind.contar_grupo(auto.grupo, "perdidos_sin_combustible")
        elif motivo == "cola_llena":
            self.ind.contar("perdidos_cola_llena")
            if self.es_real:
                self.ind.contar_grupo(auto.grupo, "perdidos_cola_llena")
        elif motivo == "corte_gnc":
            self.ind.contar("perdidos_corte_gnc")
            if self.es_real:
                self.ind.contar_grupo(auto.grupo, "perdidos_corte_gnc")
        else:  # abandono_espera
            self.ind.contar("perdidos_surtidor")
            if self.es_real:
                self.ind.contar_grupo(auto.grupo, "perdidos_espera")
        self.ind.por_hora.contar_perdido(auto.hora)

    def _marcar_quiebre(self, producto: str) -> None:
        if self.es_real:
            self.hubo_quiebre_hoy[producto] = True
        else:
            self.hubo_quiebre_hoy = True

    # =========================================================================
    # Proceso principal: el recorrido de un auto
    # =========================================================================
    def atender(self, auto: Auto):
        """Recorrido completo de un auto por la estación."""
        ahora = self.env.now
        self.ind.contar("llegadas")
        self.ind.por_hora.contar_llegada(auto.hora)
        self.ind.contar_producto(auto.producto, "llegadas")
        if self.es_real:
            self.ind.contar_grupo(auto.grupo, "llegadas")
            self.ind.litros_por_tipo[auto.tipo].agregar(auto.litros)

        # ---------- GNC cortado: pasa a Súper o se pierde (§7.5) ----------
        if self.es_real and auto.producto == "gnc" and self.gnc_cortado == 1:
            if not self._gnc_al_llegar_con_corte(auto):
                return

        # ---------- ¿Hay combustible para atenderlo? ----------
        if not self.hay_combustible(auto):
            # Cartel de "sin nafta": ni siquiera hace la cola.
            self.registrar_perdida(auto, motivo="sin_combustible")
            return

        # ---------- Cola y servicio en las caras ----------
        # Los subgeneradores devuelven False si el cliente se fue sin cargar: ese cliente
        # NO pasa por la caja del minimarket.
        if self.es_real:
            cargo = yield from self._atender_real(auto)
        else:
            cargo = yield from self._atender_clasico(auto)
        if not cargo:
            return

        # ---------- Cola y servicio en la caja del minimarket ----------
        if not auto.compra:
            self.ind.tiempo_sistema.agregar(self.env.now - auto.t_llegada)
            return
        self.ind.contar("entraron_minimarket")
        yield from self._pasar_por_caja(auto)

    def _atender_clasico(self, auto: Auto) -> bool:
        """El flujo original del proyecto hipotético, sin cambios (dorados)."""
        ahora = self.env.now
        self.ind.cola_surtidor.sumar(ahora, +1)
        with self.surtidores.request() as pedido:
            if pedido.triggered:
                yield pedido
                atendido = True
            else:
                resultado = yield pedido | self.env.timeout(self.p.paciencia_surtidor)
                atendido = pedido in resultado
            self.ind.cola_surtidor.sumar(self.env.now, -1)

            if not atendido:
                self.registrar_perdida(auto, motivo="abandono_espera")
                return False

            # Pudo haberse acabado el combustible mientras hacía la cola.
            if not self.hay_combustible(auto):
                self.registrar_perdida(auto, motivo="sin_combustible")
                return False

            espera_real = self.env.now - auto.t_llegada
            self.ind.espera_surtidor.agregar(espera_real)
            self.ind.espera_cara.agregar(espera_real)
            self.ind.por_hora.contar_espera(auto.hora, espera_real)

            self.consumir(auto)

            self.ind.ocupados_surtidores.sumar(self.env.now, +1)
            yield self.env.timeout(auto.t_carga)
            self.ind.ocupados_surtidores.sumar(self.env.now, -1)
            self.ind.contar("atendidos_surtidor")
            self.ind.contar_producto(auto.producto, "atendidos")
            self.ind.servicio_suma += auto.t_carga
        return True

    def _largo_cola(self, grupo: str) -> int:
        if self.cola_recurso:
            return len(self.cola_recurso[grupo].queue)
        return sum(len(c.queue) for c in self.caras[grupo])

    def _pedir_cara(self, grupo: str):
        """Devuelve el pedido por una cara del grupo (según la disciplina)."""
        if self.cola_recurso:
            return self.cola_recurso[grupo].request()
        caras = self.caras[grupo]
        fila = min(
            caras, key=lambda c: len(c.queue) + c.count
        )
        return fila.request()

    def _atender_real(self, auto: Auto) -> bool:
        """Grupos de caras + playeros por turno + cola finita (§7.2)."""
        ahora = self.env.now
        grupo = auto.grupo

        # ¿Hay lugar en la cola? (capacidad finita, PER-05)
        if self.p.capacidad_cola is not None and (
            self._largo_cola(grupo) >= self.p.capacidad_cola
        ):
            self.registrar_perdida(auto, motivo="cola_llena")
            return False

        self.ind.colas_grupo[grupo].sumar(ahora, +1)
        self.ind.cola_surtidor.sumar(ahora, +1)
        self.cola_lista[grupo].append(auto)

        with self._pedir_cara(grupo) as pedido_cara:
            if pedido_cara.triggered:
                yield pedido_cara
                atendido = True
            else:
                resultado = yield pedido_cara | self.env.timeout(
                    self.p.paciencia_surtidor
                )
                atendido = pedido_cara in resultado
            self.ind.colas_grupo[grupo].sumar(self.env.now, -1)
            self.ind.cola_surtidor.sumar(self.env.now, -1)
            self.cola_lista[grupo].remove(auto)

            if not atendido:
                self.registrar_perdida(auto, motivo="abandono_espera")
                return False

            espera_cara = self.env.now - auto.t_llegada
            self.ind.espera_cara.agregar(espera_cara)
            self.ind.esperas_cara_grupo[grupo].agregar(espera_cara)

            # Ocupa un carril (una cara concreta) hasta que se va.
            carril = self._tomar_carril(grupo, auto)
            try:
                return (yield from self._cargar_en_cara(auto, grupo, espera_cara))
            finally:
                self.carriles[grupo][carril] = None

    def _tomar_carril(self, grupo: str, auto: Auto) -> int:
        """Primera cara libre del grupo (sólo para dibujar: la cara real la da el recurso)."""
        carriles = self.carriles[grupo]
        indice = next(i for i, ocupante in enumerate(carriles) if ocupante is None)
        carriles[indice] = auto
        auto.espera_playero = self.info_grupo[grupo].requiere_playero
        return indice

    def _cargar_en_cara(self, auto: Auto, grupo: str, espera_cara: float) -> bool:
        """Ya tiene la cara: espera al playero (si el grupo lo pide) y carga."""

        # Playero: primero la cara, después el playero (sin deadlock).
        info_grupo = self.info_grupo[grupo]
        if info_grupo.requiere_playero:
            restante = self.p.paciencia_surtidor - espera_cara
            with self.playeros.request(priority=0) as pedido_playero:
                if pedido_playero.triggered:
                    yield pedido_playero
                else:
                    resultado = yield pedido_playero | self.env.timeout(
                        max(restante, 0.0)
                    )
                    if pedido_playero not in resultado:
                        # Se cansó esperando al playero: libera la cara y se va.
                        self.registrar_perdida(auto, motivo="abandono_espera")
                        self.ind.contar("abandonos_playero")
                        self.ind.contar_grupo(grupo, "abandonos_playero")
                        return False

                # Pudo haberse acabado el combustible mientras hacía la cola.
                if not self.hay_combustible(auto):
                    self.registrar_perdida(auto, motivo="sin_combustible")
                    return False
                self.ind.playeros_ocupados.sumar(self.env.now, +1)
                auto.espera_playero = False

                espera_real = self.env.now - auto.t_llegada
                self.ind.espera_surtidor.agregar(espera_real)
                self.ind.esperas_grupo[grupo].agregar(espera_real)
                self.ind.por_hora.contar_espera(auto.hora, espera_real)

                self.consumir(auto)
                yield from self._servir(auto, grupo)

                self.ind.playeros_ocupados.sumar(self.env.now, -1)
        else:
            # El GNC no retiene playero (PER-04: sólo conecta la manguera), pero sí un
            # COMPRESOR mientras carga: el compresor, no las 6 caras, limita el GNC.
            return (yield from self._cargar_gnc(auto, grupo, espera_cara))
        return True

    def _cargar_gnc(self, auto: Auto, grupo: str, espera_cara: float) -> bool:
        """Con la cara tomada, espera un compresor (con paciencia) y carga."""
        if self.compresores is None:
            return (yield from self._empezar_carga_gnc(auto, grupo))
        restante = self.p.paciencia_surtidor - espera_cara
        with self.compresores.request(priority=0) as pedido:
            if pedido.triggered:
                yield pedido
            else:
                resultado = yield pedido | self.env.timeout(max(restante, 0.0))
                if pedido not in resultado:
                    # Se cansó esperando el compresor: libera la cara y se va.
                    self.registrar_perdida(auto, motivo="abandono_espera")
                    self.ind.contar("abandonos_playero")
                    self.ind.contar_grupo(grupo, "abandonos_playero")
                    return False
            self.ind.compresores_ocupados.sumar(self.env.now, +1)
            try:
                return (yield from self._empezar_carga_gnc(auto, grupo))
            finally:
                self.ind.compresores_ocupados.sumar(self.env.now, -1)

    def _empezar_carga_gnc(self, auto: Auto, grupo: str) -> bool:
        """Ya tiene cara y compresor: si el corte llegó mientras esperaba, se pierde."""
        if self.gnc_cortado == 1:
            if not auto.afectado_gnc:
                auto.afectado_gnc = True
                self.ind.contar("gnc_afectados")
            self.registrar_perdida(auto, motivo="corte_gnc")
            return False
        espera_real = self.env.now - auto.t_llegada
        self.ind.espera_surtidor.agregar(espera_real)
        self.ind.esperas_grupo[grupo].agregar(espera_real)
        self.ind.por_hora.contar_espera(auto.hora, espera_real)
        self.consumir(auto)
        yield from self._servir(auto, grupo)
        return True

    def _servir(self, auto: Auto, grupo: str) -> None:
        """El tiempo de carga en la cara, contado para la utilización del grupo."""
        self.ind.ocupados_grupo[grupo].sumar(self.env.now, +1)
        self.ind.ocupados_surtidores.sumar(self.env.now, +1)
        yield self.env.timeout(auto.t_carga)
        self.ind.ocupados_grupo[grupo].sumar(self.env.now, -1)
        self.ind.ocupados_surtidores.sumar(self.env.now, -1)
        self.ind.contar("atendidos_surtidor")
        self.ind.contar_grupo(grupo, "atendidos")
        self.ind.contar_producto(auto.producto, "atendidos")
        self.ind.servicio_suma += auto.t_carga

    def _pasar_por_caja(self, auto: Auto) -> None:
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
    indicadores = Indicadores(p)
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
