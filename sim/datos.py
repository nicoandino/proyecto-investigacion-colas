"""Registro de datos del caso real (ORQUESTADOR_SIMULADOR.md §5).

Cada valor que usa el modelo entra por acá con su unidad, nivel de evidencia, tipo,
confianza, fuente y las alternativas que perdieron en las contradicciones de §4.2.
Reglas del contrato (§5.1):

  - `REGISTRO` + `por_id()` + `valor()`: lectura.
  - Los defaults de `sim/config.py` salen de acá (nada de números sueltos).
  - `tipo="heredado"` = placeholder del proyecto hipotético, visible y sin fuente.
  - `con_valor(id, nuevo)` crea una copia con `tipo="observacion"` (relevamiento propio).
  - N14 falla si un campo de los parámetros no tiene su `Dato` (ver `MAPA_PARAMETROS`).

Tipos: `dato` | `estimacion` | `observacion` | `supuesto` | `heredado`.
Confianza: `alta` | `media` | `baja` | `sin_dato`.
Nivel (jerarquía de evidencia, §4.1): A estación · B San Rafael · C Mendoza ·
D ciudad parecida · E Argentina/otro.
Origen: `investigacion` (notas 01/03/06) · `grupo` · `datos_operacionales` ·
`orquestador` · `heredado`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Dato:
    """Un valor del Registro con su fuente y su incertidumbre."""

    id: str                       # "DEM-01"
    nombre: str
    valor: object                 # lo que usa el modelo (número, tupla, texto)
    unidad: str
    bajo: float | None = None     # extremos de sensibilidad (tornado)
    alto: float | None = None
    nivel: str = "?"              # A estación · B San Rafael · C Mendoza · D ciudad parecida · E Argentina/otro
    tipo: str = "supuesto"        # dato | estimacion | observacion | supuesto | heredado
    confianza: str = "baja"       # alta | media | baja | sin_dato
    fuente: str = ""
    url: str = ""
    fecha_fuente: str = ""
    nota: str = ""
    origen: str = "investigacion"  # investigacion | grupo | datos_operacionales | orquestador | heredado
    conflicto: str = ""            # id de §4.2 (p. ej. "C2")
    alternativas: tuple = ()       # ((nombre, valor, fuente), ...) las que perdieron


# =============================================================================
# Contradicciones entre fuentes (§4.2), para la pestaña "Datos y fuentes"
# =============================================================================
@dataclass(frozen=True)
class Contradiccion:
    """Una contradicción entre fuentes y su resolución con el criterio único de la nota 07.

    Criterio (en orden): 0) que mida la misma cosa; 1) oficial o primaria y vigente; 2) más reciente;
    3) más específica de San Rafael/Mendoza; 4) empate → la más conservadora.
    """

    id: str
    tema: str
    impacto: str
    adoptado: str           # el valor elegido (lo único que muestra la app)
    alternativas: str       # las que perdieron (quedan como ejes de sensibilidad)
    criterio: str = ""      # qué paso del criterio decidió y por qué


CONTRADICCIONES: tuple[Contradiccion, ...] = (
    Contradiccion("C1", "Horario de la playa", "Medio",
                  "24 h, todos los días.",
                  "S10: cierre nocturno 22–06 (DATOS §5, sin fuente).",
                  "Oficial: API de Shell (twenty_four_hour, 5/10/2026)."),
    Contradiccion("C2", "Demanda mensual", "Alto",
                  "270.000 L/mes (estimación).",
                  "150.000 y 400.000 L/mes como ejes de sensibilidad.",
                  "Más específica: estimación regional, dentro del promedio nacional (270–380 mil) y del punto de "
                  "equilibrio (315–400 mil). No hay fuente oficial de esta estación."),
    Contradiccion("C3", "Litros vs. autos", "Crítico",
                  "Litros/mes es la variable de entrada; los clientes se derivan (÷ litros medios por cliente).",
                  "— (los documentos confundían litros/día con autos/día, error ×35–50).",
                  "Misma cosa: no es una disputa de datos sino de unidades."),
    Contradiccion("C4", "Entrada al minimarket", "Bajo-medio",
                  "20 % de los clientes atendidos.",
                  "15 % · 30 % · 45 %.",
                  "Primaria: es la única cifra con fuente declarada."),
    Contradiccion("C5", "Personal", "Alto",
                  "Playeros (noche · mañana · tarde) = 1 · 2 · 2; 1 caja; encargado y tienda sólo como costo.",
                  "Playeros 2·3·3 (ONBOARDING); autoservicio S9 (−1 por turno).",
                  "Más específica: DATOS §4 es el único desglose por rol y turno."),
    Contradiccion("C6", "Mix diésel G2/G3", "Medio",
                  "55 % G2 / 45 % G3 del diésel; se venden los dos.",
                  "75/25 (ONBOARDING) y 100/0 (sólo G2).",
                  "Más reciente y con fuente: Surtidores.com.ar (ago-2026); la Secretaría de Energía confirma ambos "
                  "productos."),
    Contradiccion("C7", "Mezcla de producto", "Medio",
                  "En litros: Súper 28,0 · V-Power 19,5 · G2 29,3 · G3 23,2 %; GNC = 3 % de los clientes.",
                  "GNC 11 % (parque GNC ENARGAS); mezcla por flota.",
                  "Misma cosa: el 11 % de ENARGAS es el parque de autos a GNC, no los clientes de esta estación."),
    Contradiccion("C8", "GNC: 6 caras vs. ≈ 3 % de los clientes", "Medio",
                  "La estación se modela como está (6 caras, 3 % de clientes GNC).",
                  "GNC 3 % / 11 % / 20 %.",
                  "Misma cosa: las caras se observaron y el 3 % es la demanda; que los compresores queden poco "
                  "usados es un resultado del modelo."),
    Contradiccion("C9", "GNC en invierno", "Alto en invierno",
                  "Corte total por episodios (2 × 6 días, jun–ago), contrato interrumpible, 3 compresores.",
                  "Contrato firme (sin cortes); ventanas horarias (17–01, 09–24); −50 % de capacidad; migración 0–60 %.",
                  "Oficial (ENARGAS, abr-2026) para la forma del corte y más específica (Sitio Andino, San Rafael "
                  "2022) para la duración."),
    Contradiccion("C10", "Estacionalidad", "Medio",
                  "Neutra por mes + calendario de temporadas (verano, vacaciones de invierno de Mendoza, resto del "
                  "invierno) editable.",
                  "Leve ±6 %; proxy turístico (DATOS §6).",
                  "Misma cosa: la ocupación hotelera no es venta de combustible; el calendario es un supuesto "
                  "moderado (nota 08)."),
    Contradiccion("C11", "Tiempo de servicio", "Medio",
                  "Nafta/diésel Triangular(2, 5, 8) min · GNC (5, 7, 12) · minimarket (2, 4, 10).",
                  "Nota 03: (2,4; 3,7; 5,0) para nafta y GNC 10–30 min (probablemente incluye la espera).",
                  "Empate → conservadora: ninguna es local ni más reciente; la media de 5 min no subestima la espera."),
    Contradiccion("C12", "Litros por carga", "Alto",
                  "Carga Triangular(0,20·T; 0,30·T; 1,00·T): media 0,5 × tanque.",
                  "Preset alto (media 0,8·T) y bajo (0,3·T).",
                  "Primaria: único anclaje empírico (nota 03, ≈ 30 % del tanque)."),
    Contradiccion("C13", "Tanques de vehículos", "Bajo",
                  "Auto 47 L; camión 300 L.",
                  "Auto 42–52 L; camión 120–600 L.",
                  "Primaria: ficha del fabricante (Autocosmos) para el auto; el camión es un supuesto sin fuente mejor."),
    Contradiccion("C14", "Servicios", "Bajo",
                  "Shop (en la app, «Shell Shop»), baño, aire y agua. No se modela lavadero.",
                  "DATOS §5 suma lavado/Agroservice.",
                  "Oficial: lista de servicios de Shell."),
    Contradiccion("C15", "Autoservicio", "Medio",
                  "Servicio atendido por playeros.",
                  "S9 autoservicio: −1 playero por turno.",
                  "Oficial: API de Shell (full_service, manned)."),
    Contradiccion("C16", "Perfil horario", "Medio",
                  "Tabla de 24 factores de DATOS §2 (picos 07–10 y 16–18).",
                  "Perfil heredado (picos 08 y 19 con factor 2,0).",
                  "Más específica: el perfil heredado es del proyecto hipotético."),
    Contradiccion("C17", "Fin de semana / quincena", "Bajo-medio",
                  "Fin de semana × 1,30, normalizado al mes. La quincena es un escenario aparte.",
                  "× 1,24 – × 1,50.",
                  "Empate → conservadora: valor central del rango de la única fuente (DATOS §2)."),
    Contradiccion("C18", "Salarios", "Medio",
                  "Costo con adicionales: playero $1.680.000 · cajero $1.800.000 · encargado $1.740.000 por mes "
                  "(enero-2026).",
                  "Básico sin adicionales.",
                  "Oficial del sector (FECRA); el básico subestima lo que cuesta un empleado."),
    Contradiccion("C19", "Precios", "Informativo",
                  "Súper $2.141 · Premium $2.300 · G2 $2.116 · G3 $2.641 · GNC $699/m³ (sept-2026).",
                  "Nota 01 (Mendoza, 6/5/2026); precios de la propia estación en la Secretaría de Energía (2025).",
                  "Más reciente: los de la Secretaría de Energía son oficiales pero están congelados desde 2025 "
                  "(no vigentes)."),
    Contradiccion("C20", "Otros", "Nulo",
                  "Informativos: ninguno entra al modelo (Mercuria, estaciones en San Rafael, tránsito RN 143, "
                  "temperatura de julio).",
                  "—",
                  "No hay valor que elegir."),
)


# =============================================================================
# El Registro (§5.2, tablas A–I + filas que cubren los parámetros del motor)
# =============================================================================
def _fila(nombre: str, unidad: str = "", nivel: str = "A", tipo: str = "dato",
          confianza: str = "media", fuente: str = "", origen: str = "investigacion",
          conflicto: str = "", alternativas: tuple = (), nota: str = "",
          bajo: float | None = None, alto: float | None = None) -> tuple:
    """Una fila del Registro sin el id ni el valor: (nombre, unidad, nivel, tipo,
    confianza, fuente, origen, conflicto, alternativas, nota, bajo, alto)."""
    return (nombre, unidad, nivel, tipo, confianza, fuente, origen,
            conflicto, alternativas, nota, bajo, alto)


_CAMPOS = ("nombre", "unidad", "nivel", "tipo", "confianza", "fuente",
           "origen", "conflicto", "alternativas", "nota", "bajo", "alto")

REGISTRO: tuple[Dato, ...] = tuple(
    Dato(id_, valor=valor_, **dict(zip(_CAMPOS, fila)))
    for id_, fila, valor_ in [
        # --------------------------------------------------------- A. Estación
        ("EST-01", ("Dirección", "—", "A", "dato", "alta",
                    "Shell (API oficial) + Secretaría de Energía", "investigacion",
                    "", (), "", None, None),
          "Balloffet 1810 esq. Los Sauces, San Rafael, Mendoza, CP 5600"),
        ("EST-02", ("Operador / CUIT", "—", "A", "dato", "alta",
                    "Shell, Secretaría de Energía, OSM", "investigacion",
                    "", (), "", None, None),
          "LOS SAUCES S.R.L. / 30-67218048-8"),
        ("EST-03", ("Bandera", "—", "A", "dato", "alta",
                    "Secretaría de Energía", "investigacion",
                    "", (), "", None, None),
          "Shell (SHELL C.A.P.S.A., id 674)"),
        ("EST-04", ("Coordenadas", "°", "A", "dato", "alta",
                    "OSM / relevamiento del grupo", "grupo",
                    "", (), "", None, None),
          "−34,62833 ; −68,35832"),
        ("EST-05", ("Horario de la playa", "h", "A", "dato", "alta",
                    "Shell API `twenty_four_hour` (leída el 5/10/2026)", "investigacion",
                    "C1", (), "", None, None),
          "24 h (abre todos los días)"),
        ("EST-06", ("Horario del minimarket", "h", "A", "supuesto", "baja",
                    "grupo / DATOS §5 (Shell API: unknown)", "grupo",
                    "C1", (("06–22", "06–22", "DATOS_OPERACIONALES §5"),),
                    "playa 24 h; el shop se asume 24 h", None, None),
          "24 h (supuesto: igual que la playa)"),
        ("EST-07", ("Servicios", "—", "A", "dato", "media",
                    "lista oficial Shell + DATOS §5", "investigacion",
                    "C14", (), "lavado/Agroservice no figuran en la lista oficial", None, None),
          "tienda (Shell Shop, ≈ 140 m²), baño, aire y agua, "
          "servicio atendido, pago en surtidor/móvil, tarjeta de flota"),
        ("EST-08", ("Calzadas", "—", "A", "dato", "media",
                    "Vialidad / OSM", "investigacion",
                    "", (), "", None, None),
          "Balloffet = RN 143 (tramo urbano, 4 carriles, 60 km/h); Los Sauces = RP 158"),
        ("EST-09", ("Cercanía", "km", "B", "dato", "alta",
                    "relevamiento del grupo (OSM)", "grupo",
                    "", (), "", None, None),
          "otras Shell a 2,26 y 3,60 km; ninguna estación a < 1,5 km"),
        ("EST-10", ("Contexto corporativo", "—", "E", "dato", "media",
                    "nota 01 (jun-2026) / DATOS §5 ('1/9/2026')", "investigacion",
                    "C20", (), "venta a Mercuria con cierre pendiente", None, None),
          "venta a Mercuria (firmada en jun-2026; informativo)"),

        # -------------------------------------------- B. Surtidores y personal
        ("SUR-00", ("Grupos de la estación real (zona · caras · productos)", "caras",
                    "A", "dato", "media",
                    "capturas de Google Maps (grupo) + Secretaría de Energía", "grupo",
                    "C6", (), "A nafta 4 (Súper, V-Power) · B diésel 2 (G2, G3) · "
                           "C GNC 6", None, None),
          (("A", "Nafta", 4, ("super", "vpower"), True),
           ("B", "Diésel", 2, ("diesel_g2", "diesel_g3"), True),
           ("C", "GNC", 6, ("gnc",), True))),
        ("MOD-02", ("Simulación con datos reales: sin azar (determinista)", "—", "A", "supuesto",
                    "sin_dato",
                    "pedido del grupo (6/10/2026): con datos reales no se sortea nada", "grupo",
                    "", (("con azar", False, "modo editado: Poisson, Triangular y Monte Carlo"),),
                    "llegadas a intervalos exactos según el perfil horario; producto, vehículo y "
                    "compra por cuotas exactas; tiempos y litros = el promedio; plazo del camión = "
                    "su media; episodios de GNC equiespaciados en jun–ago; sin cortes de ruta "
                    "aleatorios. Siempre da el mismo resultado",
                    None, None),
          True),
        ("MOD-01", ("Modelo de la estación (real vs. clásico)", "—", "A", "supuesto",
                    "sin_dato",
                    "orquestador (el clásico reproduce los dorados, §10.1)",
                    "orquestador",
                    "", (("clasico", False, "orquestador"),),
                    "el motor corre la estación real por defecto", None, None),
          True),
        ("SUR-01", ("Caras por surtidor", "caras", "A", "dato", "media",
                    "capturas de Google Maps (grupo)", "grupo",
                    "", (), "una flecha = una cara = un carril", None, None),
          2),
        ("SUR-02", ("Grupo A (nafta)", "caras", "A", "dato", "media",
                    "capturas de Google Maps (grupo) · V3", "grupo",
                    "", (), "S1–S2 → 4 caras → Súper y V-Power", None, None),
          "S1, S2 → 4 caras → Súper y V-Power"),
        ("SUR-03", ("Grupo B (diésel)", "caras", "A", "dato", "media",
                    "capturas del grupo + Secretaría de Energía", "grupo",
                    "C6", (("sólo G2", "sólo G2", "DATOS §7 'verificar'"),),
                    "S3 → 2 caras → G2 y G3", None, None),
          "S3 → 2 caras → G2 y G3"),
        ("SUR-04", ("Grupo C (GNC)", "caras", "A", "dato", "media",
                    "capturas de Google Maps (grupo)", "grupo",
                    "", (), "S4–S6 → 6 caras", None, None),
          "S4–S6 → 6 caras"),
        ("SUR-05", ("Vehículos por cara", "vehículos", "A", "supuesto", "media",
                    "grupo", "grupo",
                    "", (), "", None, None),
          1),
        ("SUR-06", ("Compresores GNC", "compresores", "A", "supuesto", "sin_dato",
                    "ONBOARDING sin fuente · C9", "orquestador",
                    "C9", (("sin límite", 6, "ONBOARDING"), ("2", 2, "ONBOARDING")),
                    "derivado de 20–25 autos/h × 7 min ÷ 60 ≈ 2,6", None, None),
          3),
        ("PER-01", ("Playeros por turno (noche·mañana·tarde)", "personas", "A",
                    "estimacion", "baja",
                    "DATOS §4 (único desglose por rol)", "datos_operacionales",
                    "C5", (("2·3·3", (2, 3, 3), "ONBOARDING"),),
                    "", None, None),
          (1, 2, 2)),
        ("PER-02", ("Cajeros (cajas) por turno", "cajas", "A", "estimacion", "baja",
                    "DATOS §4", "datos_operacionales",
                    "C5", (), "", None, None),
          (1, 1, 1)),
        ("PER-03", ("Encargado / personal de tienda", "personas", "A", "estimacion",
                    "baja",
                    "DATOS §4", "datos_operacionales",
                    "C5", (), "encargado 1 (M, T); tienda 1 (M, T) — sólo costo", None, None),
          "encargado 1 (M, T); tienda 1 (M, T) — sólo costo"),
        ("PER-04", ("El GNC lo carga un playero", "—", "A", "dato", "media",
                    "EST-07 (Shell: servicio atendido) + observación del grupo (14/10/2026) + nota 10",
                    "grupo",
                    "", (("no (autoservicio)", False, "Decreto 70/2023: el autoservicio es una opción"),),
                    "el playero conecta, controla la carga y cobra: queda tomado toda la carga, como en "
                    "nafta y diésel; el auto además usa un compresor (SUR-06)", None, None),
          True),
        ("PER-05", ("Capacidad de cola por grupo", "autos", "A", "supuesto", "sin_dato",
                    "orquestador (relevar)", "orquestador",
                    "", (("4", 4, "orquestador"), ("14", 14, "orquestador")),
                    "", 4, 14),
          8),
        ("PER-07", ("Lugares de cola por cara", "autos", "A", "supuesto", "sin_dato",
                    "pedido del grupo (6/10/2026): todas las caras tienen la misma capacidad de cola",
                    "grupo", "", (("8 por zona", 8, "PER-05 (antes)"),),
                    "la capacidad de cada zona es 3 × sus caras: A 12 · B 6 · C 18. Si la cola de la "
                    "zona está llena, el auto no entra y se pierde por 'cola llena'", None, None),
          3),
        ("PER-06", ("Disciplina de cola", "—", "A", "supuesto", "sin_dato",
                    "CASO §7", "investigacion",
                    "", (("por_cara", "por_cara", "CASO §7"),),
                    "cola FIFO única por grupo", None, None),
          "por_grupo"),

        # ---------------------------------------------------- C. Demanda ★
        ("DEM-00", ("Modo de demanda por defecto", "—", "A", "supuesto", "sin_dato",
                    "orquestador (N5: el Monte Carlo se conserva para tipo de cliente y "
                    "producto; el total diario sale de los litros)", "orquestador",
                    "", (("monte_carlo", "monte_carlo", "orquestador"),),
                    "'esperada' = total diario fijo desde litros/mes (las llegadas siguen "
                    "siendo Poisson); 'monte_carlo' = sorteo de la tabla DEM-07", None, None),
          "esperada"),
        ("DEM-01", ("Demanda mensual", "L/mes", "B", "estimacion", "baja",
                    "ONBOARDING + notas 01/03 + DATOS §1 (sin URL confirmada)", "investigacion",
                    "C2",
                    (("150.000", 150_000.0, "DATOS §1 (base)"),
                     ("400.000", 400_000.0, "punto de equilibrio 2021")),
                    "≈ 9.000 L/día; converge el informe regional, el promedio nacional "
                    "(270–380k) y el punto de equilibrio (315–400k)",
                    150_000.0, 400_000.0),
          270_000.0),
        ("DEM-02", ("Perfil horario (24 factores)", "factor", "B", "estimacion", "baja",
                    "DATOS §2 (tabla de 24 factores, §14.3)", "datos_operacionales",
                    "C16",
                    (("heredado", (0.30, 0.20, 0.15, 0.15, 0.25, 0.60, 1.10, 1.80, 2.00,
                                   1.50, 1.10, 1.00, 1.20, 1.10, 0.90, 0.90, 1.00, 1.40,
                                   1.90, 2.00, 1.60, 1.10, 0.70, 0.40),
                      "proyecto hipotético"),),
                    "picos 07–10 y 16–18 (≈ 3–4× el promedio); suma 43", None, None),
          (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.5, 3.5, 3.5, 3.5, 2.0, 2.0,
           1.5, 1.5, 1.5, 1.5, 3.0, 3.0, 2.0, 2.0, 1.5, 1.5, 1.0, 1.0)),
        ("DEM-03", ("Factor de fin de semana", "×", "B", "estimacion", "media",
                    "DATOS §2 (tabla ×1,3–1,5)", "datos_operacionales",
                    "C17", (("1,24", 1.24, "DATOS §2"), ("1,50", 1.50, "DATOS §2")),
                    "normalizado al mes (§14.4)", 1.24, 1.50),
          1.30),
        ("DEM-04", ("Mezcla de producto en litros (líquidos)", "%", "B", "estimacion",
                    "baja",
                    "DATOS §7 (Surtidores.com.ar, mercado por volumen)", "datos_operacionales",
                    "C6",
                    (("mix de flota", None, "nota 03"), ("G2/G3 75/25", 0.75, "ONBOARDING"),
                     ("sólo G2 (100/0)", 1.0, "SUR-03 alternativa")),
                    "Súper 28,0 · V-Power 19,5 · G2 29,3 · G3 23,2 (normalizado)", None, None),
          (("super", 28.0), ("vpower", 19.5), ("diesel_g2", 29.3), ("diesel_g3", 23.2))),
        ("DEM-05", ("Clientes GNC (% de las llegadas)", "%", "B", "estimacion", "baja",
                    "DATOS §7", "datos_operacionales",
                    "C8", (("11 %", 0.11, "parque GNC ENARGAS"), ("20 %", 0.20, "orquestador")),
                    "6 caras para ≈ 3 % de los clientes: la capacidad de GNC sobra (C8, resultado del modelo)",
                    0.03, 0.20),
          0.03),
        ("DEM-06", ("Estacionalidad mensual (12 factores)", "factor", "B", "supuesto",
                    "sin_dato",
                    "orquestador (C10)", "orquestador",
                    "C10",
                    (("leve ±6 %", (1.06, 1.052, 1.03, 1.00, 0.97, 0.948, 0.94, 0.948,
                                   0.97, 1.00, 1.03, 1.052), "orquestador"),
                     ("proxy turístico", (100/73.333, 60/73.333, 80/73.333, 65/73.333,
                                         60/73.333, 55/73.333, 85/73.333, 75/73.333,
                                         70/73.333, 70/73.333, 75/73.333, 85/73.333),
                      "DATOS §6")),
                    "neutra por defecto; la serie real está en la SE", None, None),
          (1.0,) * 12),
        ("DEM-07", ("Variabilidad día a día (Monte Carlo)", "factor", "B", "heredado",
                    "sin_dato",
                    "tabla original del proyecto hipotético, reescalada a relativa",
                    "heredado",
                    "", (), "factores (0,78 · 0,89 · 1,00 · 1,11 · 1,22) y frecuencias "
                           "(10 · 20 · 40 · 20 · 10)", None, None),
          ((0.78, 0.89, 1.00, 1.11, 1.22), (10, 20, 40, 20, 10))),
        ("DEM-07C", ("Tabla de demanda del motor (valores absolutos)", "autos/día", "B",
                     "heredado", "sin_dato",
                     "proyecto hipotético (la reescala relativa de DEM-07 entra en Fase 2)",
                     "heredado",
                     "", (), "es la tabla que sigue usando el modo 'monte_carlo' hoy",
                     None, None),
          ((280, 320, 360, 400, 440), (10, 20, 40, 20, 10))),
        ("DEM-08", ("Entrada al minimarket", "%", "B", "estimacion", "baja",
                    "ONBOARDING ('dato directo YPF', no confirmado)", "datos_operacionales",
                    "C4", (("15 %", 0.15, "ONBOARDING (chica)"),
                           ("30 %", 0.30, "ONBOARDING (Shell premium)"),
                           ("45 %", 0.45, "orquestador")),
                    "el único con fuente declarada, aunque débil", 0.15, 0.45),
          0.20),
        ("DEM-09", ("Eventos (opcionales)", "—", "B", "dato", "baja",
                    "DATOS §6", "datos_operacionales",
                    "", (), "Vendimia 17–26 ene +30–50 % · Las Leñas (jun-ago) +30 % · "
                           "Carnaval +40 % · vacaciones de invierno 6–17 jul (DGE 2026, nota 08)", None, None),
          "Vendimia, Las Leñas, Carnaval, vacaciones de invierno (escenarios, no default)"),
        ("DEM-10", ("Cierre de ruta y demanda", "—", "B", "supuesto", "sin_dato",
                    "DATOS §6", "datos_operacionales",
                    "", (), "al cerrarse la RN 143 la demanda externa baja; en el "
                           "pre-cierre (1–2 días) sube", None, None),
          "la cuantificación es un escenario, no un default"),
        ("DEM-11", ("Litros medios por cliente líquido", "L/cliente", "B", "estimacion",
                    "media",
                    "cadena de demanda §14.2 (mezcla DEM-04 × cargas medias §5-D)",
                    "orquestador",
                    "", (), "35,7 L = Σ (mezcla en litros ÷ carga media por producto)",
                    None, None),
          35.7),
        ("DEM-13", ("Duplicar la demanda en la hora pico (Editar simulación)", "×", "B",
                    "supuesto", "sin_dato",
                    "pedido del grupo (6/10/2026)", "grupo",
                    "", (), "multiplica por 2 el factor de las horas pico (07–10 y 16–18 h) del "
                            "perfil DEM-02; las otras horas conservan su tasa de llegadas",
                    None, None),
          2.0),
        ("DEM-14", ("Calendario de demanda: factor de cada temporada", "×", "B", "supuesto", "baja",
                    "grupo (13/10/2026), nota 08: la mitad del desvío del proxy turístico (DATOS §6) "
                    "respecto de su promedio, porque la ocupación hotelera exagera el efecto sobre el "
                    "combustible (C10)", "grupo",
                    "C10", (("neutro", (("verano", 1.0), ("vacaciones_invierno", 1.0), ("invierno", 1.0)),
                             "orquestador"),),
                    "verano (dic–feb) × 1,06 por el turismo · vacaciones de invierno de Mendoza × 1,08 · resto "
                    "del invierno (jun–ago) × 0,94 porque la gente sale menos · otoño y primavera × 1,00. Activo "
                    "en la app, neutro en los parámetros por defecto; no se renormaliza al año (+0,4 %)",
                    None, None),
          (("verano", 1.06), ("vacaciones_invierno", 1.08), ("invierno", 0.94))),
        ("DEM-15", ("Vacaciones de invierno de Mendoza (receso escolar 2026)", "mes, día", "C", "dato",
                    "media",
                    "calendario escolar 2026 de la DGE de Mendoza, citado por Los Andes (6-jul-2026), Ámbito y "
                    "El Sol (nota 08; el sitio de la DGE no se pudo abrir)", "investigacion",
                    "", (("9–20 jul", ((7, 9), (7, 20)), "DEM-09 anterior, sin fuente"),),
                    "lunes 6 a viernes 17 de julio; distintas de las de Buenos Aires", None, None),
          ((7, 6), (7, 17))),
        ("DEM-12", ("Cambio de quincena (S12): factor y días del mes", "× · día del mes",
                    "B", "supuesto", "sin_dato",
                    "DATOS §2 (+100 % 1–3 días/mes; limitación de camiones, fuente débil); los días "
                    "16–18 (cambio de quincena) son una elección del grupo",
                    "datos_operacionales",
                    "C17", (("+50 %", (1.5, (16, 17, 18)), "orquestador"),
                           ("fin de mes", (2.0, (1, 2, 3)), "DATOS §2 (1–3 días/mes)")),
                    "sólo escenario S12 (no es default); se normaliza para conservar los "
                    "litros del mes: mide la CONCENTRACIÓN del pico de cobro, no más volumen",
                    None, None),
          (2.0, (16, 17, 18))),

        # ----------------------------------------- D. Vehículos y litros/carga
        ("VEH-01", ("Auto: tanque y carga", "L", "B", "dato", "media",
                    "nota 03 D16 (Autocosmos, leído en el original)", "investigacion",
                    "C13", (("42 L", 42.0, "nota 03 (mín)"), ("52 L", 52.0, "nota 03 (máx)")),
                    "carga Triangular(0,20·T; 0,30·T; 1,00·T) → media 0,50·T = 23,5 L",
                    42.0, 52.0),
          (47.0, (9.4, 14.1, 47.0))),
        ("VEH-02", ("Pick-up / utilitario: tanque y carga", "L", "B", "dato", "media",
                    "nota 03 D18 (sólo resumen de buscador)", "investigacion",
                    "", (), "media 0,50·T = 40 L", None, None),
          (80.0, (16.0, 24.0, 80.0))),
        ("VEH-03", ("Moto 110 cc: tanque y carga", "L", "B", "dato", "media",
                    "nota 03 D19 (sólo resumen de buscador)", "investigacion",
                    "", (("3,5 L", 3.5, "nota 03"), ("4,1 L", 4.1, "nota 03")),
                    "media 0,50·T = 1,85 L", 3.5, 4.1),
          (3.7, (0.74, 1.11, 3.7))),
        ("VEH-04", ("Camión / ómnibus: tanque y carga", "L", "B", "supuesto", "sin_dato",
                    "orquestador / DATOS §8 ('Alta' sin fuente argentina)", "orquestador",
                    "C13", (("120 L", 120.0, "orquestador"), ("600 L", 600.0, "orquestador")),
                    "media 0,50·T = 150 L", 120.0, 600.0),
          (300.0, (60.0, 90.0, 300.0))),
        ("VEH-05", ("Auto GNC: cilindro y carga", "m³", "B", "dato", "baja",
                    "nota 03 §2.10 (sólo resumen de buscador)", "investigacion",
                    "", (), "cilindro 14 m³; carga media 7 m³", None, None),
          (14.0, (2.8, 4.2, 14.0))),
        ("VEH-06", ("Litros por carga del motor (una sola distribución)", "L", "B",
                    "heredado", "sin_dato",
                    "proyecto hipotético (el desglose por tipo de vehículo entra en Fase 2)",
                    "heredado",
                    "", (), "Triangular(15, 30, 60) — media 35 L", None, None),
          (15.0, 30.0, 60.0)),
        ("VEH-07", ("Presets de litros por carga (C12): media baja y alta", "× tanque", "B",
                    "supuesto", "sin_dato",
                    "orquestador C12 (nota 03: se carga ≈ 30 % del tanque; llenar es raro)",
                    "orquestador",
                    "C12", (), "Triangular(mín, moda, máx) × tanque: bajo (0,1 · 0,3 · 0,5), media "
                               "0,3 · alto (0,6 · 0,8 · 1,0), media 0,8; el default tiene media 0,5",
                    None, None),
          (("bajo", (0.1, 0.3, 0.5)), ("alto", (0.6, 0.8, 1.0)))),
        ("VEH-00", ("Tipo de vehículo por producto (matriz)", "%", "B", "supuesto",
                    "sin_dato",
                    "orquestador (diseño 'producto primero', §7.2)", "orquestador",
                    "", (), "Súper 12/85/3/0 · V-Power 0/85/15/0 · G2 0/20/55/25 · "
                           "G3 0/15/45/40 · GNC 0/100/0/0 (moto/auto/pick-up/camión)",
                    None, None),
          (("super", (0.12, 0.85, 0.03, 0.0)),
           ("vpower", (0.0, 0.85, 0.15, 0.0)),
           ("diesel_g2", (0.0, 0.20, 0.55, 0.25)),
           ("diesel_g3", (0.0, 0.15, 0.45, 0.40)),
           ("gnc", (0.0, 1.0, 0.0, 0.0)))),

        # --------------------------------------------------- E. Tiempos
        ("TIE-01", ("Caudal de la manguera", "L/min", "E", "dato", "baja",
                    "nota 03 D22/D23 (Paraguay 2012)", "investigacion",
                    "", (("90 L/min", 90.0, "nota 03 (alto caudal)"),
                         ("120 L/min", 120.0, "nota 03 (alto caudal)")),
                    "alto caudal 90–120 L/min", 40.0, 120.0),
          40.0),
        ("TIE-02", ("Carga nafta/diésel (por vehículo en la cara)", "min", "E",
                    "supuesto", "media",
                    "DATOS §3 (papers UNLP/UTN/UNC, sin medición en San Rafael)",
                    "datos_operacionales",
                    "C11", (("nota 03", (2.4, 3.7, 5.0), "punto medio de dos refs. débiles"),),
                    "", None, None),
          (2.0, 5.0, 8.0)),
        ("TIE-03", ("Extra de camión/ómnibus", "min", "B", "supuesto", "baja",
                    "orquestador", "orquestador",
                    "", (), "+ litros ÷ 90 por la manguera de alto caudal", None, None),
          "+ litros ÷ 90"),
        ("TIE-04", ("Carga GNC", "min", "B", "supuesto", "media",
                    "DATOS §3", "datos_operacionales",
                    "C11", (("nota 03", (10.0, 15.0, 30.0), "probablemente incluye espera"),),
                    "", None, None),
          (5.0, 7.0, 12.0)),
        ("TIE-05", ("Compra en el minimarket", "min", "B", "supuesto", "baja",
                    "DATOS §3", "datos_operacionales",
                    "C11", (("heredado", (1.5, 3.0, 6.0), "proyecto hipotético"),),
                    "", None, None),
          (2.0, 4.0, 10.0)),
        ("TIE-06", ("Paciencia (cola de cara / cola de caja)", "min", "B", "heredado",
                    "sin_dato",
                    "proyecto hipotético", "heredado",
                    "", (("5 min", 5.0, "orquestador"), ("20 min", 20.0, "orquestador")),
                    "", 5.0, 20.0),
          (10.0, 8.0)),

        # ---------------------------------------------- F. Abastecimiento
        ("INV-01", ("Plazo pedido→entrega", "h", "C", "dato", "media",
                    "Sitio Andino 27-oct-2023 'casi 1 día y medio' (Shell Mendoza capital); "
                    "extremos supuestos", "investigacion",
                    "", (), "Triangular(24, 36, 48); reemplaza Triangular(8, 16, 36)",
                    None, None),
          (24.0, 36.0, 48.0)),
        ("INV-02", ("Carga del camión", "L", "E", "estimacion", "media",
                    "27.000 L (2023) y 34.000 L (2009)", "investigacion",
                    "", (("27.000", 27_000.0, "Sitio Andino 2023"),
                         ("34.000", 34_000.0, "nota 06, 2009")),
                    "", 27_000.0, 34_000.0),
          30_000.0),
        ("INV-03", ("Tanque por producto líquido", "L", "A", "supuesto", "baja",
                    "aviso de venta Guaymallén, no verificado", "orquestador",
                    "", (("10.000", 10_000.0, "orquestador"),
                         ("25.000", 25_000.0, "orquestador")),
                    "", 10_000.0, 25_000.0),
          20_000.0),
        ("INV-04", ("Descarga del camión", "min", "C", "supuesto", "sin_dato",
                    "orquestador", "orquestador",
                    "", (), "incluida en el plazo base; informativo", None, None),
          45.0),
        ("INV-05", ("Origen del abastecimiento", "—", "C", "dato", "media",
                    "Sitio Andino 2023, Los Andes 2023", "investigacion",
                    "", (("Luján de Cuyo", "Luján de Cuyo", "nota 06 (YPF)"),),
                    "Dock Sud ≈ 991 km vía Gral. Alvear (nivel C, 2023)", None, None),
          "Dock Sud"),
        ("INV-06", ("Política real de reposición", "—", "C", "dato", "baja",
                    "Sitio Andino 2023", "investigacion",
                    "", (), "no documentada (pedido 'a demanda')", None, None),
          "no documentada (pedido 'a demanda')"),
        ("INV-07", ("Política (s, Q) inicial", "L", "A", "supuesto", "sin_dato",
                    "orquestador", "orquestador",
                    "", (), "s = 1,5 días de consumo (9.000 L/día → 13.500 L); "
                           "Q = min(cap − s, máx(2,5 × consumo/día, 0,5 × cap)) = 6.500 L",
                    None, None),
          (13_500.0, 6_500.0)),
        ("INV-08", ("Camión consolidado", "—", "C", "supuesto", "media",
                    "Sitio Andino 2023", "investigacion",
                    "", (), "un viaje lleva varios productos (observado: 27.000 L de "
                           "gasoil y naftas)", None, None),
          True),
        ("INV-09", ("Crisis de abastecimiento (S7)", "h", "C", "estimacion", "baja",
                    "Los Andes 31-jul-2023", "investigacion",
                    "", (), "plazo Triangular(72, 84, 96) durante 3–4 días", None, None),
          (72.0, 84.0, 96.0)),
        ("INV-11", ("Ventana de la crisis de abastecimiento (S7): día de inicio y duración",
                    "día · días", "C", "supuesto", "sin_dato",
                    "INV-09 (Los Andes 31-jul-2023: 3–4 días); el día de inicio es arbitrario",
                    "investigacion",
                    "", (("3 días", (10, 3.0), "Los Andes 2023"), ("4 días", (10, 4.0), "Los Andes 2023")),
                    "los pedidos que se emiten dentro de la ventana tardan el plazo de crisis",
                    None, None),
          (10, 3.5)),
        ("INV-12", ("Nivel inicial de los tanques en la simulación con datos reales", "%", "A",
                    "supuesto", "sin_dato",
                    "pedido del grupo (6/10/2026): los tanques arrancan llenos", "grupo",
                    "", (("75 %", 0.75, "INV-10 (modo editado)"),),
                    "la simulación con datos reales no tiene calentamiento: arranca en el momento "
                    "cero con los tanques llenos", None, None),
          1.0),
        ("INV-10", ("Nivel inicial del tanque", "%", "A", "supuesto", "sin_dato",
                    "orquestador (INV-07)", "orquestador",
                    "", (), "75 % de la capacidad (INV-07)", None, None),
          0.75),

        # ------------------------------------------------- G. Red de rutas
        ("RED-01", ("Arco LUJAN–PAREDITAS", "km", "C", "dato", "media",
                    "nota 06 §1.2 (RN 40; km derivado de los tramos)", "investigacion",
                    "", (("114 km", 114.0, "ORQUESTADOR §5-G (redondeado)"),),
                    "114,8 km ≈ 98 min a 70 km/h; cortable. El 114 de la tabla §5-G es "
                    "un redondeo: Luján→San Rafael = 221,8 km (nota 06) = 114,8 + 107", None, None),
          114.8),
        ("RED-02", ("Arco PAREDITAS–SANRAFAEL", "km", "C", "dato", "media",
                    "nota 06 §1.2 (RN 143)", "investigacion",
                    "", (), "107 km ≈ 92 min; cortable (nieve jun-ago, obra)", None, None),
          107.0),
        ("RED-03", ("Arco PAREDITAS–SOSNEADO", "km", "C", "dato", "media",
                    "nota 06 §1.2 (RN 40)", "investigacion",
                    "", (), "176 km ≈ 151 min; cortable", None, None),
          176.0),
        ("RED-04", ("Arco SOSNEADO–SANRAFAEL", "km", "C", "dato", "media",
                    "nota 06 §1.2 (RN 144)", "investigacion",
                    "", (), "132 km ≈ 113 min; cortable", None, None),
          132.0),
        ("RED-05", ("Arco ALVEAR–SANRAFAEL", "km", "C", "dato", "media",
                    "nota 06 §1.2 (RN 143 este)", "investigacion",
                    "", (), "87,5 km ≈ 75 min; cortable opcional", None, None),
          87.5),
        ("RED-06", ("Arco SANRAFAEL–MONTECOMAN", "km", "C", "dato", "media",
                    "nota 06 §1.2 (RN 146)", "investigacion",
                    "", (), "54,1 km ≈ 46 min; no cortable", None, None),
          54.1),
        ("RED-07", ("Arco MONTECOMAN–LAPAZ", "km", "C", "dato", "media",
                    "nota 06 §1.2 (RP 153, no verificada)", "investigacion",
                    "", (), "204,7 km ≈ 175 min; no cortable", None, None),
          204.7),
        ("RED-08", ("Arco LAPAZ–LUJAN", "km", "C", "dato", "media",
                    "nota 06 §1.2 (RN 7)", "investigacion",
                    "", (), "141,0 km ≈ 121 min; no cortable", None, None),
          141.0),
        ("RED-09", ("Arco DOCK–ALVEAR", "km", "C", "dato", "media",
                    "nota 06 §1.3 (no verificada)", "investigacion",
                    "", (), "903,8 km ≈ 775 min; no cortable", None, None),
          903.8),
        ("RED-10", ("Arco DOCK–LUJAN", "km", "C", "dato", "media",
                    "nota 06 §1.3 (no verificada)", "investigacion",
                    "", (), "1.056,5 km ≈ 906 min; no cortable", None, None),
          1056.5),
        ("RED-18", ("Arco ARROYO–ALVEAR (terminal de Arroyo Seco, Santa Fe)", "km", "E", "estimacion",
                    "media",
                    "OSRM sobre OpenStreetMap (perfil auto), consultado 13-oct-2026, cálculo propio; la "
                    "terminal es de Raízen/Shell (venta a Mercuria, jun-2026, nota 09)", "investigacion",
                    "", (), "806 km ≈ 691 min; no cortable; Arroyo Seco → San Rafael = 893,5 km", None, None),
          806.0),
        ("RED-19", ("Orígenes alternativos del camión, en orden", "—", "C", "supuesto", "media",
                    "nota 09: Arroyo Seco (terminal de Raízen/Shell, misma empresa) y después Luján de Cuyo "
                    "(refinería YPF, último recurso). La Paz y Pareditas son cruces de ruta, no plantas",
                    "investigacion", "", (),
                    "sólo para los líquidos; apagado por defecto (el camión sale siempre de Dock Sud)",
                    None, None),
          ("ARROYO", "LUJAN")),
        ("RED-20", ("Probabilidad de que un origen no pueda cumplir un pedido", "prob.", "C", "supuesto",
                    "sin_dato",
                    "grupo (13/10/2026); sin estadística: faltantes de Shell en Mendoza en jul y oct de 2023 "
                    "(Los Andes, Sitio Andino)", "grupo",
                    "", (("0 %", 0.0, "sin eventos"), ("15 %", 0.15, "orquestador")),
                    "con 'eventos aleatorios de abastecimiento'; sin azar es una cuota: 1 de cada 20 pedidos "
                    "de cada producto", 0.0, 0.15),
          0.05),
        ("RED-21", ("Demora de redirigir un pedido a otro origen", "h", "C", "supuesto", "sin_dato",
                    "grupo (13/10/2026): volver a gestionar el pedido con otra terminal", "grupo",
                    "", (), "plazo = base − viaje desde Dock Sud + viaje desde el origen usado + esta demora",
                    None, None),
          12.0),
        ("RED-11", ("Velocidad del camión", "km/h", "C", "supuesto", "sin_dato",
                    "orquestador (entre 80 km/h legales y 60 urbanos)", "orquestador",
                    "", (), "OSRM da 81 km/h, inalcanzable para un camión", None, None),
          70.0),

        ("RED-12", ("Escenario de cortes de ruta", "—", "C", "supuesto", "sin_dato",
                    "orquestador (CASO §6.1; 3 cortes documentados en jul/ago-2026)",
                    "orquestador",
                    "", (("ninguno", "ninguno", "orquestador"),
                         ("E1", "E1", "17-ago-2026: RN 143 cerrada 6 h"),
                         ("E2", "E2", "1–2-jul-2026: RN 143 + RN 40 + RN 144, 24–48 h"),
                         ("E3", "E3", "obra: +30 min por viaje, 8–18 h"),
                         ("E4", "E4", "RN 143 este cerrada 24 h (supuesto)")),
                    "'aleatorio' = cada viaje de jun–ago encuentra un corte con prob. RED-13; "
                    "fuera de invierno no hay cortes", None, None),
          "aleatorio"),
        ("RED-13", ("Probabilidad de que un viaje encuentre un corte (jun–ago)", "prob.",
                    "C", "supuesto", "sin_dato",
                    "orquestador (CASO §6.1: no hay estadística de cortes)", "orquestador",
                    "", (("sin cortes", 0.0, "orquestador"), ("30 %", 0.30, "orquestador")),
                    "fuera de invierno vale 0", 0.0, 0.30),
          0.10),
        ("RED-14", ("Duración de un corte aleatorio", "h", "C", "supuesto", "sin_dato",
                    "orquestador (E1 = 6 h; E2 = 24–48 h)", "orquestador",
                    "", (), "Triangular(3, 6, 24) h; el viaje la encuentra entera "
                            "(demora = mín(desvío, duración))", None, None),
          (3.0, 6.0, 24.0)),
        ("RED-15", ("Cortes forzados E1–E4", "—", "C", "dato", "media",
                    "Sitio Andino / Los Andes / MDZ (nota 06 §1.3); E3 y E4 son supuestos",
                    "investigacion",
                    "", (), "(id, nombre, arcos cerrados, duración Triangular h, demora fija "
                            "min, franja horaria de la obra)", None, None),
          (
              ("E1", "RN 143 cerrada 6 h (17-ago-2026)",
               (("PAREDITAS", "SANRAFAEL"),), (6.0, 6.0, 6.0), 0.0, None),
              ("E2", "RN 143 + RN 40 + RN 144 cerradas 24–48 h (1–2-jul-2026)",
               (("PAREDITAS", "SANRAFAEL"), ("PAREDITAS", "SOSNEADO"),
                ("SOSNEADO", "SANRAFAEL")), (24.0, 36.0, 48.0), 0.0, None),
              ("E3", "Obra en la ruta: +30 min por viaje, de 8 a 18 h (sin dato)",
               (), (0.0, 0.0, 0.0), 30.0, (8.0, 18.0)),
              ("E4", "RN 143 este (Alvear–San Rafael) cerrada 24 h (supuesto)",
               (("ALVEAR", "SANRAFAEL"),), (24.0, 24.0, 24.0), 0.0, None),
          )),
        ("RED-16", ("Día de la corrida en que arranca un corte forzado", "día", "C",
                    "supuesto", "sin_dato", "orquestador", "orquestador",
                    "", (), "E1, E2 y E4 empiezan a las 00:00 de ese día; E3 vale todos los días",
                    None, None),
          10),
        ("RED-17", ("Meses con cortes sorteados", "meses", "C", "estimacion", "baja",
                    "DATOS §6 (cortes RN-143/144 por nieve, invierno)", "datos_operacionales",
                    "", (), "junio, julio y agosto", None, None),
          (6, 7, 8)),

        # ---------------------------------------------------------- H. GNC
        ("GNC-01", ("Contrato de suministro", "—", "A", "supuesto", "sin_dato",
                    "ONBOARDING '80 % de las estaciones' sin fuente; ENARGAS abr-2026 "
                    "(verificado)", "orquestador",
                    "C9", (("firme", "firme", "orquestador"),),
                    "interrumpible: sufre los cortes de invierno", None, None),
          "interrumpible"),
        ("GNC-02", ("Episodios de corte en invierno", "episodios", "B", "estimacion",
                    "baja",
                    "DATOS §7 ('10–14 días en jun/jul')", "datos_operacionales",
                    "C9", (("0 episodios", 0, "orquestador"), ("4 episodios", 4, "orquestador")),
                    "2 episodios × 6 días entre 1/jun y 31/ago (≈ 12 días)", 0, 4),
          2),
        ("GNC-03", ("Forma del corte", "—", "A", "dato", "media",
                    "ENARGAS abr-2026; Sitio Andino 23/6/2022", "investigacion",
                    "C9",
                    (("ventanas", "ventana", "Sitio Andino 2022 (17–01 y 09–24)"),
                     ("parcial_50", "parcial_50", "ONBOARDING (sin fuente)")),
                    "corte total de 24 h 'hasta nuevo aviso'", None, None),
          "total_24h"),
        ("GNC-04", ("Migración a nafta durante el corte", "%", "A", "supuesto",
                    "sin_dato",
                    "DATOS: 'no hay migración documentada' → supuesto explícito",
                    "orquestador",
                    "C9", (("0 %", 0.0, "orquestador"), ("60 %", 0.60, "orquestador")),
                    "", 0.0, 0.60),
          0.30),
        ("GNC-06", ("Duración de cada episodio de corte", "días", "B", "estimacion",
                    "baja",
                    "DATOS §7 ('10–14 días en jun/jul' ⇒ 2 episodios de 6 días)",
                    "datos_operacionales",
                    "C9", (("3 días", 3, "orquestador"), ("10 días", 10, "orquestador")),
                    "el corte llega 'hasta nuevo aviso': dura varios días seguidos", 3, 10),
          6),
        ("GNC-07", ("Forzar que los episodios caigan dentro del horizonte", "—", "A",
                    "supuesto", "sin_dato",
                    "orquestador (herramienta de análisis, no un dato)", "orquestador",
                    "", (("no", False, "calendario real de jun–ago"),),
                    "sí: los episodios se sortean entre los días de invierno del horizonte "
                    "(para estudiar el corte sin esperar a que el azar lo ponga adentro)",
                    None, None),
          False),
        ("GNC-08", ("Cortes de GNC extra si se eligen 'más cortes en todo el invierno'", "episodios", "B",
                    "supuesto", "sin_dato",
                    "grupo (13/10/2026) sobre GNC-02: el Registro ya traía '4 episodios' como alternativa",
                    "grupo", "C9", (("0 extra", 0, "sólo los cortes habituales"),),
                    "se suman a los habituales (GNC-02) en los huecos más largos del invierno; apagado por "
                    "defecto", 0, 2),
          2),
        ("GNC-09", ("Probabilidad de invierno más frío que alarga cada corte", "prob.", "B", "supuesto",
                    "sin_dato",
                    "grupo (13/10/2026); no hay estadística de olas de frío por episodio", "grupo",
                    "C9", (("sin alargue", 0.0, "orquestador"),),
                    "sólo con 'más cortes en todo el invierno'; sin azar es una cuota exacta", 0.0, 0.5),
          0.30),
        ("GNC-10", ("Días que se alarga un corte en un invierno más frío", "días", "B", "supuesto",
                    "sin_dato",
                    "grupo (13/10/2026): con el alargue el corte llega a 10 días, la alternativa larga de GNC-06",
                    "grupo", "C9", (), "6 días habituales + 4 = 10 días (GNC-06, alternativa)", 0, 4),
          4),
        ("GNC-05", ("Flujo máximo de la red de gas", "—", "A", "supuesto", "sin_dato",
                    "CASO §6.2", "investigacion",
                    "", (), "sin datos de capacidad ⇒ episodios aleatorios "
                           "(Edmonds-Karp sólo con capacidades reales)", None, None),
          "sin datos (ventana/episodio aleatorio)"),

        # ------------------------------------------------------- I. Economía
        ("ECO-01", ("Margen por litro", "$/L", "E", "heredado", "sin_dato",
                    "proyecto hipotético", "heredado",
                    "", (("prueba −50 %", 50.0, "rango de prueba de sensibilidad (no es dato)"),
                         ("prueba +50 %", 150.0, "rango de prueba de sensibilidad (no es dato)")),
                    "≈ 4,7 % del Súper a $2.141; candidatas CECHA/FECRA; "
                    "parametrizar también como % del precio. Los extremos son un rango de "
                    "prueba para el tornado, no un dato", 50.0, 150.0),
          100.0),
        ("ECO-02", ("Margen por compra en minimarket", "$/compra", "E", "heredado",
                    "sin_dato",
                    "proyecto hipotético", "heredado",
                    "", (("prueba −50 %", 1_250.0, "rango de prueba de sensibilidad (no es dato)"),
                         ("prueba +50 %", 3_750.0, "rango de prueba de sensibilidad (no es dato)")),
                    "el shop = 5–10 % de los ingresos de la estación (DATOS); extremos de "
                    "prueba para el tornado", 1_250.0, 3_750.0),
          2_500.0),
        ("ECO-03", ("Margen por m³ de GNC", "$/m³", "E", "heredado", "sin_dato",
                    "proyecto hipotético", "heredado",
                    "", (("prueba −50 %", 50.0, "rango de prueba de sensibilidad (no es dato)"),
                         ("prueba +50 %", 150.0, "rango de prueba de sensibilidad (no es dato)")),
                    "mismo placeholder que ECO-01", 50.0, 150.0),
          100.0),
        ("ECO-04", ("Sueldos (playero / cajero / encargado)", "$/mes", "E",
                    "estimacion", "media",
                    "DATOS §4 (FECRA); la URL dice enero-2026", "datos_operacionales",
                    "C18", (("básicos", (1_545_472.0, 1_666_391.0, 1_600_406.0),
                             "FECRA (básico, sin adicionales)"),),
                    "costos totales con adicionales; vigencia a verificar", None, None),
          (1_680_000.0, 1_800_000.0, 1_740_000.0)),
        ("ECO-04C", ("Sueldo del cajero (motor)", "$/mes", "E", "estimacion", "media",
                     "ECO-04 (cajero, con adicionales)", "datos_operacionales",
                     "C18", (("heredado", 900_000.0, "proyecto hipotético"),),
                     "", None, None),
          1_800_000.0),
        ("ECO-05", ("Inversión por cara/surtidor nuevo; operativo mensual", "$", "E",
                    "heredado", "sin_dato",
                    "proyecto hipotético", "heredado",
                    "", (), "$18.000.000 una vez + $250.000/mes", None, None),
          (18_000_000.0, 250_000.0)),
        ("ECO-06", ("Flete del camión", "$/viaje", "E", "heredado", "sin_dato",
                    "proyecto hipotético (fijo); $/km sin dato", "heredado",
                    "", (("prueba ×0,5", 75_000.0, "rango de prueba de sensibilidad (no es dato)"),
                         ("prueba ×10", 1_500_000.0, "rango de prueba de sensibilidad (no es dato): el fijo de $150.000 es "
                                                      "implausible para ≈ 1.000 km")),
                    "$150.000 es implausible para ≈ 1.000 km con 30.000 L: "
                    "consultar transportistas. La app avisa si origen = Dock Sud "
                    "y $/km = 0. Los extremos (sólo del fijo) son de prueba", 75_000.0, 1_500_000.0),
          (150_000.0, 0.0)),
        ("ECO-07", ("Almacenamiento", "$/litro-mes", "E", "heredado", "sin_dato",
                    "proyecto hipotético", "heredado",
                    "", (("prueba −50 %", 12.5, "rango de prueba de sensibilidad (no es dato)"),
                         ("prueba +50 %", 37.5, "rango de prueba de sensibilidad (no es dato)")),
                    "extremos de prueba para el tornado", 12.5, 37.5),
          25.0),
        ("ECO-08", ("Precios (referencia, informativos)", "$", "B", "dato", "media",
                    "DATOS §7, sept-2026 (GNC oct-2025)", "datos_operacionales",
                    "C19", (), "Súper $2.141 · Premium $2.300+ · G2 $2.116 · "
                              "G3 $2.641 · GNC $699/m³", None, None),
          (("super", 2_141.0), ("premium", 2_300.0), ("diesel_g2", 2_116.0),
           ("diesel_g3", 2_641.0), ("gnc", 699.0))),
        ("ECO-09", ("Anualización", "—", "E", "supuesto", "sin_dato",
                    "orquestador", "orquestador",
                    "", (), "año = 3 × Σ de los 4 meses representativos; "
                           "rotular 'estimación'", None, None),
          "año = 3 × Σ de los 4 meses representativos"),

        ("ECO-10", ("Cobertura de francos (personas por puesto cubierto 24 h)", "×", "E",
                    "supuesto", "sin_dato",
                    "7 días de operación ÷ 5 días trabajados por persona", "orquestador",
                    "C5", (("sin francos", 1.0, "puestos = personas"),
                           ("6 de 7 días", 7.0 / 6.0, "jornada de 6 días")),
                    "una persona no cubre los 7 días: el costo de personal se multiplica por "
                    "este factor (ONBOARDING habla de 21 personas)", 1.0, 1.75),
          1.4),
        ("ECO-11", ("Puestos fijos por día que el motor no modela (encargado · tienda)",
                    "puestos-turno", "E", "estimacion", "baja",
                    "DATOS §4 (encargado 1 y tienda 1 en mañana y tarde)",
                    "datos_operacionales",
                    "C5", (), "sólo entran como costo de personal; el sueldo de tienda es el "
                              "del cajero", None, None),
          (2.0, 2.0)),

        # --------------------- Filas que cubren los campos del motor (N14) ----
        ("REC-01", ("Surtidores del motor (configuración clásica)", "surtidores", "B",
                    "heredado", "sin_dato",
                    "proyecto hipotético (los 12 caras reales son SUR-01..04; "
                    "el rediseño de grupos entra en Fase 2)", "heredado",
                    "", (), "", None, None),
          3),
        ("REC-02", ("Cajas del motor (configuración clásica)", "cajas", "B",
                    "heredado", "sin_dato",
                    "proyecto hipotético (PER-02 da 1 caja por turno)", "heredado",
                    "", (), "", None, None),
          1),
        ("REC-03", ("Caja exponencial", "—", "B", "heredado", "sin_dato",
                    "proyecto hipotético", "heredado",
                    "", (), "con Exponencial se usa la misma media que la triangular",
                    None, None),
          False),
        ("CAL-01", ("Fecha de inicio", "mes, día", "A", "supuesto", "sin_dato",
                    "orquestador", "orquestador",
                    "", (), "elegible en la interfaz; el default es 1/1", None, None),
          (1, 1)),
        ("CAL-02", ("Días simulados", "días", "A", "supuesto", "sin_dato",
                    "orquestador (dias_y_fecha)", "orquestador",
                    "", (), "los fija dias_y_fecha(horizonte): 1/7/real/90/365", None, None),
          30),
        ("CAL-03", ("Días de calentamiento", "días", "A", "supuesto", "sin_dato",
                    "orquestador (B4)", "orquestador",
                    "", (), "2 días por defecto en ambos modos", None, None),
          2),
        ("CAL-04", ("Día animado", "día", "A", "supuesto", "sin_dato",
                    "orquestador", "orquestador",
                    "", (), "", None, None),
          2),
        ("CAL-05", ("Intervalo de la traza", "min", "A", "supuesto", "sin_dato",
                    "orquestador", "orquestador",
                    "", (), "cuadro de animación cada 0,5 min", None, None),
          0.5),
        ("CAL-08", ("Temporadas del menú inicial", "mes de inicio · meses", "A", "supuesto",
                    "sin_dato",
                    "estaciones meteorológicas del hemisferio sur (elección del grupo)", "grupo",
                    "", (),
                    "Verano dic–feb · Otoño mar–may · Invierno jun–ago · Primavera sep–nov, de mes "
                    "entero; el verano cruza el año", None, None),
          (("Verano", (12, 3)), ("Otoño", (3, 3)), ("Invierno", (6, 3)), ("Primavera", (9, 3)))),
        ("CAL-09", ("Semana representativa de cada temporada (escenario único)", "mes, día · días", "A",
                    "supuesto", "sin_dato",
                    "grupo (13/10/2026): una semana de lunes a domingo en el medio de cada temporada, fuera de "
                    "los cortes de GNC habituales; la de vacaciones es la primera semana del receso (DEM-15)",
                    "grupo", "", (),
                    "verano 12/ene · otoño 13/abr · invierno 10/ago · primavera 12/oct · vacaciones de invierno "
                    "6/jul; 7 días cada una", None, None),
          ((("Verano", (1, 12)), ("Otoño", (4, 13)), ("Invierno", (8, 10)), ("Primavera", (10, 12)),
            ("Vacaciones de invierno", (7, 6))), 7)),
        ("CAL-07", ("Grabar la animación de todos los días", "—", "A", "supuesto", "sin_dato",
                    "pedido del grupo (6/10/2026): se anima todo el período, un día cada 5 s",
                    "grupo", "", (), "se graba un cuadro cada `dt_traza` minutos en todo el período",
                    None, None),
          True),
        ("CAL-06", ("Horizonte", "—", "A", "supuesto", "sin_dato",
                    "orquestador", "orquestador",
                    "", (), "dia | semana | mes | estacion | anio", None, None),
          "mes"),

        # ------------------------------------------- J. Eventos aleatorios (parte 4, §20–23)
        # Frecuencias y duraciones: SUPUESTOS del grupo (no hay registros de la estación). Cada día se
        # sortea si ocurre cada evento (probabilidad por día); duración uniforme entre el mínimo y el máximo.
        ("EVT-00", ("Eventos aleatorios: cuáles están prendidos, semilla y frecuencia", "—", "A", "supuesto",
                    "sin_dato", "pedido del grupo (14/10/2026): eventos que se prenden desde el menú", "grupo",
                    "", (),
                    "(eventos prendidos, semilla del sorteo, multiplicador de la frecuencia). Apagados por "
                    "defecto: con ninguno prendido la corrida es idéntica", None, None),
          ((), 1, 1.0)),
        ("EVT-01", ("Abandono repentino del turno", "prob./día", "A", "supuesto", "sin_dato",
                    "grupo (14/10/2026)", "grupo", "", (),
                    "≈ 1 cada 2 meses; a una hora al azar un playero se va y nadie lo reemplaza hasta el "
                    "próximo cambio de turno (06, 14 o 22 h)", None, None),
          (1 / 60,)),
        ("EVT-02", ("Licencia por accidente cubierta con horas extra", "prob./día · días · recargos", "A",
                    "supuesto", "sin_dato",
                    "grupo (14/10/2026); recargos: Ley de Contrato de Trabajo, art. 201", "grupo", "", (),
                    "≈ 1 cada 6 meses; un playero falta de 3 a 15 días y otro cubre su turno con horas extra: "
                    "recargo 50 % (lunes a sábado) y 100 % (domingo; el sábado después de las 13 y los "
                    "feriados se simplifican)", None, None),
          (1 / 180, 3, 15, 0.50, 1.00)),
        ("EVT-03", ("Falta sin aviso", "prob./día", "A", "supuesto", "sin_dato",
                    "grupo (14/10/2026)", "grupo", "", (),
                    "≈ 2 por mes; un turno entero (8 h) arranca con un playero menos", None, None),
          (1 / 15,)),
        ("EVT-04", ("Licencia sin reemplazo", "fracción de las licencias", "A", "supuesto", "sin_dato",
                    "grupo (14/10/2026)", "grupo", "", (),
                    "de las licencias de EVT-02, el 30 % no consigue reemplazo: ese turno queda con un "
                    "playero menos todos los días de la licencia", None, None),
          (0.30,)),
        ("EVT-05", ("Falla de un surtidor", "prob./día · h · $", "A", "supuesto", "sin_dato",
                    "grupo (14/10/2026)", "grupo", "", (),
                    "≈ 1 por mes; una cara queda fuera de servicio de 2 a 24 h hasta que llega el técnico. "
                    "Costo de la visita: sin dato (0)", None, None),
          (1 / 30, 2.0, 24.0, 0.0)),
        ("EVT-06", ("Falla de un compresor de GNC", "prob./día · h", "A", "supuesto", "sin_dato",
                    "grupo (14/10/2026)", "grupo", "", (),
                    "≈ 1 cada 2 meses; un compresor menos (SUR-06) de 4 a 48 h", None, None),
          (1 / 60, 4.0, 48.0)),
        ("EVT-07", ("Corte de luz", "prob./día · h", "B", "supuesto", "sin_dato",
                    "grupo (14/10/2026): tormentas y calor de verano", "grupo", "", (),
                    "dic–feb ≈ 2 por mes, el resto ≈ 1 cada 2 meses; sin surtidores ni compresores la "
                    "estación se para de 1 a 4 h", None, None),
          (1 / 15, 1 / 60, 1.0, 4.0)),
        ("EVT-08", ("Se cae el sistema de cobro", "prob./día · h · min · ×", "A", "supuesto", "sin_dato",
                    "grupo (14/10/2026)", "grupo", "", (),
                    "≈ 1 por mes; de 1 a 6 h sólo efectivo: cada carga tarda 1 min más y la caja del "
                    "minimarket × 1,5", None, None),
          (1 / 30, 1.0, 6.0, 1.0, 1.5)),
        ("EVT-09", ("Aumento de precio", "prob./día · aumento · adelanto", "E", "supuesto", "sin_dato",
                    "grupo (14/10/2026): en Argentina los aumentos son casi mensuales", "grupo", "", (),
                    "≈ 1 por mes; nafta y diésel +10 % desde ese día con el MISMO margen en $/L; el día "
                    "anterior llegan 20 % más clientes (se adelantan a cargar)", None, None),
          (1 / 30, 0.10, 0.20)),
        ("EVT-10", ("Faltante de combustible con cupo", "prob./día · días · L · ×", "C", "supuesto", "sin_dato",
                    "grupo (14/10/2026); precedentes: faltante de gasoil 2022 con cupos y crisis de Mendoza "
                    "2023 (INV-09)", "grupo", "", (),
                    "≈ 1 por año; de 3 a 7 días: cada cliente carga como máximo 30 L, y los camiones pedidos "
                    "tardan el plazo de crisis (INV-09) y traen la mitad", None, None),
          (1 / 365, 3, 7, 30.0, 0.5)),
        ("EVT-11", ("Rotura del camión en la ruta", "prob./viaje · h", "C", "supuesto", "sin_dato",
                    "grupo (14/10/2026)", "grupo", "", (),
                    "5 % de los viajes llegan de 12 a 48 h tarde", None, None),
          (0.05, 12.0, 48.0)),
        ("EVT-12", ("Corte de la avenida (choque u obra)", "prob./día · h · fracción · hora", "A", "supuesto",
                    "sin_dato", "grupo (14/10/2026)", "grupo", "", (),
                    "≈ 1 por mes; de 2 a 8 h, empezando entre las 7 y las 20, llega la mitad de los clientes",
                    None, None),
          (1 / 30, 2.0, 8.0, 0.5, 7.0, 20.0)),
        ("EVT-13", ("Evento masivo en San Rafael", "prob./día · días · aumento", "B", "supuesto", "baja",
                    "grupo (14/10/2026); el aumento es el piso de DEM-09 (Vendimia +30–50 %)", "grupo", "", (),
                    "≈ 4 por año; de 1 a 3 días con 30 % más clientes (fiesta, fin de semana largo)", None, None),
          (4 / 365, 1, 3, 0.30)),
        ("EVT-14", ("Asalto", "prob./día · h", "A", "supuesto", "sin_dato",
                    "grupo (14/10/2026)", "grupo", "", (),
                    "≈ 1 por año; la estación se para de 30 a 60 min mientras actúa la policía", None, None),
          (1 / 365, 0.5, 1.0)),
        ("EVT-15", ("Horas de trabajo por mes de un playero (valor de la hora)", "h/mes", "A", "supuesto",
                    "sin_dato", "grupo (14/10/2026): jornada de 8 h, unos 25 días por mes", "grupo", "", (),
                    "valor de la hora = sueldo del playero (ECO-04) ÷ estas horas; sirve para las horas extra",
                    None, None),
          200.0),

        # ------------------------------------------- K. Pronóstico (parte 3, §15–19)
        ("PRO-01", ("Ventas mensuales al público de Shell en Mendoza (Súper, Ultra, gasoil G2 y G3)", "m³/mes", "C",
                    "dato", "alta",
                    "Secretaría de Energía, datos abiertos: 'Refinación y comercialización… (Tablas dinámicas)', "
                    "recurso 'Ventas (excluye ventas a empresas del sector)'; empresa SHELL C.A.P.S.A., subtipo Al "
                    "Público, provincia Mendoza (descargado 14-oct-2026; nota 12)", "investigacion", "", (),
                    "(primer mes, 92 valores de ene-2019 a ago-2026). Es la suma de TODAS las Shell de Mendoza, no la "
                    "estación: el modelo usa la forma (índices por mes, tendencia en %) escalada a DEM-01", None, None),
          ((2019, 1), (8607, 9188, 9224, 9031, 9625, 9174, 10736, 9770, 9141, 10543, 9477, 10975, 10975, 10711, 8450, 5278, 7336, 8261, 10352, 10719, 8264, 10728, 11487, 15756, 15660, 15790, 16842, 11719, 12323, 14108, 14157, 15279, 15498, 16577, 14174, 14982, 13000, 14958, 14788, 14563, 14691, 14682, 13662, 14782, 14999, 14693, 14623, 16120, 16120, 13892, 15778, 15616, 15384, 12985, 13010, 12398, 12280, 13093, 12488, 12013, 10474, 12516, 13320, 10997, 12853, 11751, 14783, 15310, 12514, 14709, 13807, 14468, 14423, 14858, 13748, 11723, 12638, 11555, 12301, 12909, 12023, 12286, 11863, 13089, 11437, 11048, 12111, 11330, 11495, 11248, 11035, 11297))),
        ("PRO-02", ("Ventana de ajuste del pronóstico: primer mes y meses de prueba", "mes · meses", "C", "supuesto",
                    "media", "grupo (14/10/2026): se excluyen la pandemia (2020) y el rebote de 2021 (nota 12)",
                    "grupo", "", (),
                    "se ajusta desde ene-2022 y los últimos 12 meses (sep-2025 – ago-2026) quedan para probar cada "
                    "método (no se usan para ajustarlo)", None, None),
          ((2022, 1), 12)),
        ("PRO-03", ("Nivel de confianza del intervalo del pronóstico (z)", "—", "E", "dato", "alta",
                    "estadística: z de la normal estándar para 95 %", "investigacion", "", (),
                    "IC del pronóstico = pronóstico ± z · RMSE (como en el práctico de Pronóstico)", None, None),
          1.96),
        ("PRO-04", ("Parámetros de los métodos: meses del promedio móvil y α del suavizado exponencial", "meses · α",
                    "E", "supuesto", "sin_dato", "grupo (14/10/2026): valores típicos de la cátedra", "grupo", "", (),
                    "promedio móvil de 3 meses; suavizado exponencial simple con α = 0,3", None, None),
          (3, 0.3)),

        # ------------------------------------------- L. Flujos en la red (parte 3, §15–19)
        ("FLU-01", ("Capacidad de cada tramo en el análisis de rutas independientes", "rutas", "C", "dato", "alta",
                    "método (teorema de Menger): flujo máximo con capacidad 1 por tramo = cantidad de rutas que no "
                    "comparten ningún tramo", "grupo", "", (),
                    "no es tránsito: cuenta cuántas rutas independientes llegan a San Rafael y qué tramos hay que "
                    "cortar para aislarla (corte mínimo)", None, None),
          1.0),
        ("FLU-02", ("Cuánto puede despachar cada origen para esta estación (fracción de los camiones del período)",
                    "fracción", "C", "supuesto", "sin_dato",
                    "INV-05 (hoy todo sale de Dock Sud) y nota 09 (Arroyo Seco, Luján de Cuyo)", "grupo", "", (),
                    "hoy: Dock Sud 100 %, Arroyo Seco 0 %, Luján 0 % (otra empresa: emergencia). El menú deja "
                    "probar otros topes; el plan de costo mínimo reparte los camiones entre los orígenes", None, None),
          (("DOCK", 1.0), ("ARROYO", 0.0), ("LUJAN", 0.0))),
    ]
)


_POR_ID: dict[str, Dato] = {d.id: d for d in REGISTRO}


def por_id(id_: str) -> Dato:
    """El Dato con ese id (levanta KeyError si no existe)."""
    if id_ not in _POR_ID:
        raise KeyError(f"Dato desconocido: {id_}")
    return _POR_ID[id_]


def valor(id_: str) -> object:
    """El valor que usa el modelo (por_id(id).valor)."""
    return por_id(id_).valor


def con_valor(id_: str, nuevo: object) -> Dato:
    """Copia del Dato con otro valor, marcada como `observacion` (relevamiento propio)."""
    original = por_id(id_)
    return replace(original, valor=nuevo, tipo="observacion", origen="grupo",
                   nota=f"relevamiento propio (antes: {original.valor}). {original.nota}".rstrip())


# =============================================================================
# Mapa campo de parámetros → Dato (control N14: cero huérfanos)
# =============================================================================
MAPA_PARAMETROS: dict[str, str] = {
    # ParametrosSimulacion
    "ParametrosSimulacion.surtidores": "REC-01",
    "ParametrosSimulacion.cajas": "REC-02",
    "ParametrosSimulacion.demanda": "DEM-07C",
    "ParametrosSimulacion.perfil": "DEM-02",
    "ParametrosSimulacion.modo_demanda": "DEM-00",
    "ParametrosSimulacion.litros_mes": "DEM-01",
    "ParametrosSimulacion.litros_medios_por_cliente": "DEM-11",
    "ParametrosSimulacion.factor_fin_de_semana": "DEM-03",
    "ParametrosSimulacion.estacionalidad": "DEM-06",
    "ParametrosSimulacion.fecha_inicio": "CAL-01",
    "ParametrosSimulacion.carga": "TIE-02",
    "ParametrosSimulacion.carga_gnc": "TIE-04",
    "ParametrosSimulacion.compra": "TIE-05",
    "ParametrosSimulacion.caja_exponencial": "REC-03",
    "ParametrosSimulacion.litros": "VEH-06",
    "ParametrosSimulacion.prob_compra": "DEM-08",
    "ParametrosSimulacion.paciencia_surtidor": "TIE-06",
    "ParametrosSimulacion.paciencia_caja": "TIE-06",
    "ParametrosSimulacion.tanque": "INV-03",
    "ParametrosSimulacion.red": "RED-12",
    "ParametrosSimulacion.gnc": "GNC-01",
    "ParametrosGNC.contrato": "GNC-01",
    "ParametrosGNC.episodios": "GNC-02",
    "ParametrosGNC.dias_por_episodio": "GNC-06",
    "ParametrosGNC.forma": "GNC-03",
    "ParametrosGNC.compresores": "SUR-06",
    "ParametrosGNC.migracion_a_nafta": "GNC-04",
    "ParametrosGNC.episodios_en_horizonte": "GNC-07",
    "ParametrosGNC.cortes_extra": "GNC-08",
    "ParametrosGNC.prob_invierno_frio": "GNC-09",
    "ParametrosGNC.dias_extra_frio": "GNC-10",
    "ParametrosRed.arcos": "RED-01",
    "ParametrosRed.origen": "INV-05",
    "ParametrosRed.destino": "EST-01",
    "ParametrosRed.velocidad_kmh": "RED-11",
    "ParametrosRed.escenario_corte": "RED-12",
    "ParametrosRed.cortes": "RED-15",
    "ParametrosRed.corte_dia": "RED-16",
    "ParametrosRed.prob_corte_viaje": "RED-13",
    "ParametrosRed.duracion_aleatoria": "RED-14",
    "ParametrosRed.meses_corte": "RED-17",
    "ParametrosRed.origenes_alternativos": "RED-19",
    "ParametrosRed.prob_origen_no_disponible": "RED-20",
    "ParametrosRed.origenes_no_disponibles": "RED-19",
    "ParametrosRed.demora_redireccion_h": "RED-21",
    "ParametrosRed.cuotas_origen": "FLU-02",
    # ParametrosEventos (parte 4)
    "ParametrosSimulacion.eventos": "EVT-00",
    "ParametrosEventos.activos": "EVT-00",
    "ParametrosEventos.semilla": "EVT-00",
    "ParametrosEventos.frecuencia": "EVT-00",
    "ParametrosSimulacion.estacion_real": "MOD-01",
    "ParametrosSimulacion.grupos": "SUR-00",
    "ParametrosSimulacion.productos": "DEM-04",
    "ParametrosSimulacion.tipos_vehiculo": "VEH-00",
    "ParametrosSimulacion.matriz_tipos": "VEH-00",
    "ParametrosSimulacion.playeros_por_turno": "PER-01",
    "ParametrosSimulacion.turnos": "PER-01",
    "ParametrosSimulacion.pct_gnc": "DEM-05",
    "ParametrosSimulacion.capacidad_cola": "PER-05",
    "ParametrosSimulacion.cola_por_cara": "PER-07",
    "ParametrosSimulacion.disciplina_cola": "PER-06",
    "ParametrosSimulacion.sorteo_producto_primero": "MOD-01",
    "ParametrosSimulacion.tabla_demanda_relativa": "DEM-07",
    "ParametrosSimulacion.demanda_relativa": "DEM-07",
    "ParametrosSimulacion.inventario": "INV-07",
    "ParametrosSimulacion.dias": "CAL-02",
    "ParametrosSimulacion.dias_calentamiento": "CAL-03",
    "ParametrosSimulacion.dia_animado": "CAL-04",
    "ParametrosSimulacion.dt_traza": "CAL-05",
    "ParametrosSimulacion.horizonte": "CAL-06",
    "ParametrosEconomicos.precios": "ECO-08",
    "ParametrosSimulacion.determinista": "MOD-02",
    "ParametrosSimulacion.animar_todo": "CAL-07",
    "ParametrosSimulacion.factor_quincena": "DEM-12",
    "ParametrosSimulacion.calendario_demanda": "DEM-14",
    "ParametrosSimulacion.vacaciones_invierno": "DEM-15",
    "ParametrosSimulacion.dias_quincena": "DEM-12",
    "ParametrosSimulacion.crisis": "INV-09",
    "ParametrosSimulacion.crisis_dia": "INV-11",
    "ParametrosSimulacion.crisis_dias": "INV-11",
    # ParametrosTanque
    "ParametrosTanque.capacidad": "INV-03",
    "ParametrosTanque.nivel_inicial": "INV-10",
    "ParametrosTanque.punto_pedido": "INV-07",
    "ParametrosTanque.cantidad_pedido": "INV-07",
    "ParametrosTanque.plazo_entrega": "INV-01",
    # ParametrosEconomicos
    "ParametrosEconomicos.margen_por_litro": "ECO-01",
    "ParametrosEconomicos.margenes_producto": "ECO-01",
    "ParametrosEconomicos.margen_compra": "ECO-02",
    "ParametrosEconomicos.inversion_surtidor": "ECO-05",
    "ParametrosEconomicos.operativo_surtidor_mensual": "ECO-05",
    "ParametrosEconomicos.sueldo_cajero_mensual": "ECO-04C",
    "ParametrosEconomicos.sueldo_playero_mensual": "ECO-04",
    "ParametrosEconomicos.sueldo_encargado_mensual": "ECO-04",
    "ParametrosEconomicos.margen_gnc": "ECO-03",
    "ParametrosEconomicos.flete_por_km": "ECO-06",
    "ParametrosEconomicos.cobertura_francos": "ECO-10",
    "ParametrosEconomicos.puestos_encargado": "ECO-11",
    "ParametrosEconomicos.puestos_tienda": "ECO-11",
    "ParametrosEconomicos.costo_pedido": "ECO-06",
    "ParametrosEconomicos.costo_almacenamiento_litro_mes": "ECO-07",
}


# =============================================================================
# Aclaración general sobre las fuentes
# =============================================================================
#: La única aclaración general sobre las fuentes que muestra la app. Las contradicciones se resolvieron con el
#: criterio de la nota 07, pero elegir la mejor fuente no convierte una estimación en una medición.
AVISO_FUENTES = (
    "Los valores provienen de fuentes públicas y estimaciones; la estación no aporta mediciones propias."
)

PIE_NO_AFILIADO = (
    "Proyecto académico de Investigación Operativa; no es oficial ni está afiliado a Shell."
)
