"""Etiquetas, unidades y ayudas de la interfaz, en un solo lugar.

Tener las descripciones acá (y no desparramadas en la app) permite que las tablas, los
gráficos y las tarjetas de indicadores usen exactamente los mismos nombres, que son los
mismos que van a ir en el informe.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Metrica:
    """Cómo se muestra una métrica del motor en la interfaz."""

    clave: str            # nombre del campo en ResultadoReplica
    etiqueta: str         # nombre para mostrar
    unidad: str
    decimales: int = 2
    porcentaje: bool = False   # el motor la devuelve entre 0 y 1 y se muestra en %
    mejor_bajo: bool = True    # True si un valor más bajo es mejor
    ayuda: str = ""

    def valor_mostrado(self, valor: float) -> float:
        return valor * 100 if self.porcentaje else valor

    @property
    def unidad_mostrada(self) -> str:
        return "%" if self.porcentaje else self.unidad

    def formatear(self, valor: float) -> str:
        v = self.valor_mostrado(valor)
        return f"{v:,.{self.decimales}f} {self.unidad_mostrada}".strip()


# --- Líneas de espera: los indicadores que pide la consigna -------------------
INDICADORES_COLAS: tuple[Metrica, ...] = (
    Metrica(
        "espera_surtidor", "Espera en cola del surtidor", "min", 2,
        ayuda="Tiempo promedio que espera un auto desde que llega hasta que empieza a "
              "cargar, promediado sobre todo el día.",
    ),
    Metrica(
        "espera_pico", "Espera en la hora pico", "min", 2,
        ayuda="La espera promedio de la peor hora del día. Es el número que de verdad "
              "siente el cliente: el promedio de 24 horas lo disimula porque de "
              "madrugada no espera nadie.",
    ),
    Metrica(
        "cola_surtidor", "Longitud promedio de cola (surtidor)", "autos", 2,
        ayuda="Promedio EN EL TIEMPO de la cantidad de autos esperando: el área bajo la "
              "curva de la cola dividida por la duración de la medición.",
    ),
    Metrica(
        "util_surtidores", "Utilización de surtidores", "", 1, porcentaje=True,
        mejor_bajo=False,
        ayuda="Fracción del tiempo que cada surtidor está ocupado, sobre las 24 horas.",
    ),
    Metrica(
        "espera_caja", "Espera en cola de la caja", "min", 2,
        ayuda="Tiempo promedio de espera en el minimarket antes de ser cobrado.",
    ),
    Metrica(
        "cola_caja", "Longitud promedio de cola (caja)", "clientes", 2,
        ayuda="Promedio en el tiempo de la cantidad de clientes esperando para pagar.",
    ),
    Metrica(
        "util_cajas", "Utilización de cajas", "", 1, porcentaje=True, mejor_bajo=False,
        ayuda="Fracción del tiempo que cada caja está ocupada cobrando.",
    ),
)

# --- Clientes ----------------------------------------------------------------
INDICADORES_CLIENTES: tuple[Metrica, ...] = (
    Metrica(
        "atendidos_dia", "Autos atendidos por día", "autos", 1, mejor_bajo=False,
        ayuda="Autos que efectivamente cargaron combustible.",
    ),
    Metrica(
        "perdidos_cola_dia", "Perdidos por cola larga", "autos/día", 2,
        ayuda="Se fueron sin cargar porque la espera superó su paciencia. Se arreglan "
              "con más capacidad de atención.",
    ),
    Metrica(
        "perdidos_sin_combustible_dia", "Perdidos por falta de combustible", "autos/día", 2,
        ayuda="Llegaron y no había nafta para venderles. Se arreglan con una mejor "
              "política de reposición, no con más surtidores.",
    ),
    Metrica(
        "tasa_abandono", "Tasa de abandono", "%", 2,
        ayuda="Porcentaje de los autos que llegan y se van sin cargar, por cualquier motivo.",
    ),
    Metrica(
        "compras_dia", "Compras en el minimarket", "compras/día", 1, mejor_bajo=False,
        ayuda="Clientes que efectivamente compraron y pagaron.",
    ),
    Metrica(
        "perdidos_caja_dia", "Compras perdidas en la caja", "clientes/día", 2,
        ayuda="Dejaron la compra por la cola de la caja. El combustible ya se había vendido.",
    ),
    Metrica(
        "llegadas_dia", "Autos que llegan por día", "autos/día", 1, mejor_bajo=False,
        ayuda="Demanda total que se presentó, atendida o no.",
    ),
)

# --- Inventario --------------------------------------------------------------
INDICADORES_INVENTARIO: tuple[Metrica, ...] = (
    Metrica(
        "nivel_servicio", "Nivel de servicio", "", 1, porcentaje=True, mejor_bajo=False,
        ayuda="Fracción de los litros demandados que se pudieron vender. Es el indicador "
              "central de una política de inventario.",
    ),
    Metrica(
        "porcentaje_dias_quiebre", "Días con quiebre de stock", "%", 1,
        ayuda="Porcentaje de días en los que la estación se quedó sin combustible en "
              "algún momento.",
    ),
    Metrica(
        "porcentaje_tiempo_sin_combustible", "Tiempo sin combustible", "%", 2,
        ayuda="Porcentaje del tiempo total en que la estación no pudo vender.",
    ),
    Metrica(
        "litros_vendidos_dia", "Litros vendidos por día", "L/día", 0, mejor_bajo=False,
        ayuda="Volumen efectivamente despachado.",
    ),
    Metrica(
        "litros_no_vendidos_dia", "Litros no vendidos por día", "L/día", 0,
        ayuda="Lo que habrían cargado los clientes que se fueron. Es la venta perdida.",
    ),
    Metrica(
        "nivel_tanque_promedio", "Nivel promedio del tanque", "L", 0, mejor_bajo=False,
        ayuda="Promedio en el tiempo del combustible almacenado. Es el capital "
              "inmovilizado: cuanto más alto, más cuesta mantenerlo.",
    ),
    Metrica(
        "pedidos_dia", "Pedidos al camión por día", "ped./día", 2,
        ayuda="Cuántos camiones cisterna se piden. Cada uno cuesta el flete.",
    ),
    Metrica(
        "nivel_tanque_minimo", "Nivel mínimo alcanzado", "L", 0, mejor_bajo=False,
        ayuda="El peor momento del mes. Si llegó a cero, hubo quiebre.",
    ),
    Metrica(
        "plazo_entrega", "Plazo de entrega promedio", "h", 1,
        ayuda="Cuánto tardó el camión cisterna, en promedio. Es una variable aleatoria.",
    ),
)

# --- Complementarios ---------------------------------------------------------
INDICADORES_COMPLEMENTARIOS: tuple[Metrica, ...] = (
    Metrica("tiempo_sistema", "Tiempo total en el sistema", "min", 2,
            ayuda="Desde que el auto llega hasta que se retira, incluyendo el minimarket."),
    Metrica("max_cola_surtidor", "Cola máxima (surtidor)", "autos", 0,
            ayuda="El peor momento del mes: sirve para dimensionar el espacio físico."),
    Metrica("max_espera_surtidor", "Espera máxima (surtidor)", "min", 1,
            ayuda="La peor espera que sufrió un cliente en todo el mes."),
    Metrica("util_playeros", "Utilización de playeros", "", 1, porcentaje=True,
            mejor_bajo=False,
            ayuda="Playeros atendiendo ÷ playeros en turno, promedio en el tiempo. En la "
                  "estación real el cuello de botella son los playeros, no las caras."),
    Metrica("perdidos_cola_llena_dia", "Perdidos por cola llena", "autos/día", 2,
            ayuda="Llegaron y la fila de su zona ya estaba completa: no entraron "
                  "(capacidad de cola finita)."),
)

# --- GNC (Fase 6) -------------------------------------------------------------
INDICADORES_GNC: tuple[Metrica, ...] = (
    Metrica("gnc_afectados_dia", "Clientes GNC afectados por el corte", "por día", 2,
            ayuda="Los que llegaron (o ya esperaban) cuando el GNC estaba cortado. Es el "
                  "promedio de TODOS los días medidos: con 2 episodios de 6 días, sólo 12 "
                  "de los ≈ 92 días de invierno tienen corte."),
    Metrica("migrados_gnc_dia", "Pasaron a Súper", "por día", 2,
            ayuda="De los afectados, los que cargaron nafta en lugar de GNC (migración, "
                  "GNC-04). No son una pérdida: suben la cola de la zona A."),
    Metrica("perdidos_corte_gnc_dia", "Perdidos por el corte", "por día", 2,
            ayuda="De los afectados, los que se fueron sin cargar (motivo `corte_gnc`)."),
    Metrica("m3_gnc_vendidos_dia", "GNC vendido", "m³/día", 1, mejor_bajo=False,
            ayuda="El GNC se mide en m³, nunca en litros."),
    Metrica("m3_gnc_perdidos_dia", "GNC no vendido", "m³/día", 1,
            ayuda="Lo que habrían cargado los clientes que se fueron."),
    Metrica("dias_corte_gnc_pct", "Días con corte de GNC", "%", 1,
            ayuda="Porcentaje de los días medidos con algún tramo de corte."),
    Metrica("util_compresores", "Utilización de compresores", "", 1, porcentaje=True,
            mejor_bajo=False,
            ayuda="Cargas GNC en curso ÷ compresores, promedio en el tiempo. El compresor, "
                  "no las 6 caras, limita cuántos autos cargan GNC a la vez."),
)

TODAS: tuple[Metrica, ...] = (
    INDICADORES_COLAS
    + INDICADORES_CLIENTES
    + INDICADORES_INVENTARIO
    + INDICADORES_COMPLEMENTARIOS
    + INDICADORES_GNC
)

POR_CLAVE: dict[str, Metrica] = {m.clave: m for m in TODAS}

#: Las que se muestran en la tabla comparativa de escenarios.
COMPARACION: tuple[Metrica, ...] = (
    POR_CLAVE["espera_pico"],
    POR_CLAVE["espera_surtidor"],
    POR_CLAVE["cola_surtidor"],
    POR_CLAVE["util_surtidores"],
    POR_CLAVE["espera_caja"],
    POR_CLAVE["atendidos_dia"],
    POR_CLAVE["perdidos_cola_dia"],
    POR_CLAVE["perdidos_sin_combustible_dia"],
    POR_CLAVE["litros_vendidos_dia"],
)


# =============================================================================
# Textos largos
# =============================================================================
DESCRIPCION_MODELO_REAL = """
El modelo reproduce la **estación Shell de Av. Balloffet y Los Sauces** (San Rafael, Mendoza)
durante el horizonte elegido. Cada día se simula con calendario real y hay dos subsistemas
que se afectan entre sí.

#### 1. Líneas de espera (el playón)

1. **Llegadas**: **proceso de Poisson no homogéneo**; la tasa sigue el perfil horario de
   `DEM-02`. Los clientes por día **se derivan de los litros por mes** (nunca al revés).
2. **Cliente "producto primero"** (Monte Carlo de 5 pasos, tablas en la pestaña Demanda):
   se sortea el **producto** (Súper, V-Power, Diésel G2, Diésel G3 o GNC) y, condicionado a
   él, el **tipo de vehículo** (moto, auto, pick-up, camión). Los litros salen de una
   triangular `(0,20 · T ; 0,30 · T ; 1,00 · T)` según el tanque del vehículo.
3. **Tres zonas de caras**: A nafta (4), B diésel (2) y C GNC (6). Cada zona tiene su cola
   FIFO (o una fila por cara) y una **capacidad de cola finita**: si está llena, el auto
   no entra.
4. **Playeros por turno** (noche · mañana · tarde): para cargar nafta o diésel hace falta
   una **cara libre y un playero**, así que los servidores son `mín(caras libres,
   playeros en turno)`. El GNC sólo conecta la manguera y no retiene playero.
5. **Caja del minimarket**: los que cargaron entran con probabilidad p (Bernoulli); es la
   segunda cola de la red. Quien se va sin cargar **no** pasa por la caja.
6. **Abandono (reneging)**: si la espera hasta empezar a ser atendido supera la paciencia,
   el cliente se va.

#### 2. Inventario (un tanque por producto líquido)

7. **Consumo**: cada carga descuenta litros **del tanque de su producto** al empezar a
   cargar. El GNC no tiene tanque (se mide en m³).
8. **Política (s, Q) por producto**: cuando la posición de inventario del producto cae por
   debajo de `s` se pide un camión con `Q` litros; tarda un plazo aleatorio en llegar.
9. **Quiebre de stock**: si el tanque de un producto se vacía, ese producto no se vende.

#### Pérdidas por motivo
`sin_combustible` · `abandono_espera` · `cola_llena` · `abandono_caja` (y `corte_gnc` y la
migración del GNC a nafta, que llegan en la Fase 6). Todo cliente que llega termina en
exactamente una categoría: atendido, perdido (un motivo) o todavía adentro.
"""

DESCRIPCION_MODELO = """
El modelo reproduce un **mes completo** de una estación de servicio, con dos subsistemas
que se afectan entre sí.

#### 1. Líneas de espera (el playón)

1. **Llegadas**: los autos llegan según un **proceso de Poisson**, es decir que el tiempo
   entre dos llegadas es una variable **exponencial**. Pero la tasa **no es constante**:
   sigue el perfil horario, con pico a la mañana, valle al mediodía y pico a la tarde.
2. **Surtidores**: N surtidores en paralelo con **cola única FIFO**. El tiempo de carga
   sigue una **triangular** (mínimo, más probable, máximo), que es la distribución que se
   usa cuando no hay datos históricos y sólo se puede estimar el rango.
3. **Decisión de compra**: terminada la carga, cada cliente entra al minimarket con
   probabilidad p (ensayo de **Bernoulli**). El resto se retira.
4. **Caja**: los que entran hacen una segunda cola frente a M cajas. Es una **red de
   colas**: dos procesos consecutivos.
5. **Abandono (reneging)**: si la espera supera la paciencia del cliente, se va.

#### 2. Inventario (el tanque)

6. **Consumo**: cada carga descuenta del tanque los litros que se despachan, sorteados
   con una triangular.
7. **Política (s, Q)**: cuando la **posición de inventario** (lo que hay más lo que viene
   en camino) cae por debajo del **punto de pedido s**, se pide un camión cisterna con
   **Q litros**.
8. **Plazo de entrega**: el camión tarda un tiempo aleatorio en llegar.
9. **Quiebre de stock**: si el tanque se vacía, la estación no vende. No se pierde un
   cliente: se pierden todos los que llegan hasta que descargue el camión.

#### Cómo se acoplan

Cuantos más autos se atienden, más rápido se vacía el tanque. Y si el tanque está vacío,
no importa cuántos surtidores haya. Por eso las dos decisiones —cuánta capacidad de
atención y qué política de reposición— **no se pueden analizar por separado**.
"""

DESCRIPCION_MONTECARLO = """
La cantidad de autos de cada día no se inventa ni se supone: se sortea con el **método de
simulación Monte Carlo**, a partir de una tabla de frecuencias observada.

1. **Distribución de probabilidad**: cada demanda observada dividida por el total de días
   registrados.
2. **Probabilidad acumulada**: la probabilidad de que la demanda sea menor o igual a cada
   valor.
3. **Intervalos de números aleatorios**: se le asigna a cada valor un tramo del 01 al 00,
   proporcional a su probabilidad.
4. **Generación del número aleatorio**: uno por día simulado.
5. **Simulación**: se busca en qué intervalo cayó y ése es el número de autos del día.

Después, esos autos se reparten dentro del día según el **perfil horario**, mediante un
proceso de Poisson cuya tasa cambia hora a hora.
"""

DESCRIPCION_METODO = """
**Por qué los resultados son confiables y no "lo que salió esa vez":**

- **Período de calentamiento**: la estación arranca vacía y con el tanque lleno, que no es
  su estado habitual. Los primeros días se simulan pero **no se miden**.
- **Réplicas independientes**: cada escenario se corre varias veces con semillas distintas.
  Se informa el **promedio ± el intervalo de confianza del 95 %** (t de Student). Si los
  intervalos de dos escenarios se superponen, la diferencia **no** es significativa.
- **Números aleatorios comunes**: la réplica i usa la misma semilla en todos los
  escenarios, así que llegan los mismos autos, cargan los mismos litros y el camión tarda
  lo mismo. La diferencia observada se debe a la capacidad, no al azar.
- **Promedios temporales**: la longitud de cola, la utilización y el nivel del tanque se
  calculan como área bajo la curva dividida por el tiempo, no como promedio de
  observaciones sueltas.
- **Verificación del motor**: `verificar.py` corre 22 controles, entre ellos la **ley de
  Little** y la **conservación de litros**, que dan exacto.
"""

SUPUESTOS = [
    "Se modela un solo producto (nafta súper). Varios combustibles multiplicarían los "
    "tanques sin cambiar la naturaleza del problema.",
    "La estación atiende las 24 horas.",
    "Los surtidores son todos iguales e intercambiables, y hay una sola cola para todos.",
    "Un cliente que se va no vuelve más tarde: se cuenta como venta perdida.",
    "La paciencia del cliente es un umbral fijo, igual para todos.",
    "El camión cisterna siempre trae la cantidad pedida, salvo que no entre en el tanque.",
    "No se modelan fallas de equipos, cortes de luz ni faltantes del proveedor.",
    "El precio y el margen por litro se consideran constantes.",
    "Los días son independientes entre sí: no hay efecto de día de semana ni de quincena.",
]


SUPUESTOS_REAL = [
    "Los datos de la propia estación **todavía no existen**: la demanda, la dotación y el "
    "resto son estimaciones o supuestos del Registro (pestaña Datos y fuentes).",
    "Playa de 24 horas con servicio atendido; el GNC no retiene playero (PER-04).",
    "Un vehículo por cara y una cola FIFO única por zona (PER-06); capacidad de cola finita "
    "(PER-05, sin dato: hay que relevarla).",
    "Playeros por turno 1 · 2 · 2 (noche · mañana · tarde) y una sola caja (PER-01/PER-02).",
    "El tipo de vehículo por producto es un supuesto del orquestador (VEH-00).",
    "Las cargas siguen `Triangular(0,2·T ; 0,3·T ; 1,0·T)`: carga media = 0,5 × tanque (C12).",
    "Un tanque por producto líquido de 20.000 L con política (s, Q) derivada de la demanda "
    "(INV-07); el GNC no tiene tanque y se corta por episodios en invierno (GNC-01..07).",
    "Márgenes, flete y almacenamiento son placeholders heredados del proyecto hipotético "
    "(ECO-*): los pesos que se informan no son todavía una conclusión económica.",
    "Un cliente que se va no vuelve más tarde: se cuenta como venta perdida.",
]
