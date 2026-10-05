# ORQUESTADOR — Del simulador hipotético al simulador de la Shell de San Rafael

> **Para quién es este archivo:** para un agente de código que arranca en frío. Leelo entero antes de tocar nada. Es la fuente de verdad del *trabajo gráfico y práctico* que falta. Si algo de acá contradice a `CLAUDE.md` o `TASK.md`, **gana este archivo** (esos dos describen el proyecto hipotético anterior; ver §2.3).
>
> **Versión:** v1.0 · **Fecha de redacción:** 5/10/2026 · **Rama de trabajo:** `claude/simulator-graphic-orchestrator-wu2xh4`
>
> **Aviso sobre el origen:** el pedido original hablaba de un `onboarding.md` con "todo el contexto". **Ese archivo no existe en el repo** (ni en ninguna rama). Este orquestador se armó con: `CASO_SHELL_SAN_RAFAEL.md` (borrador v0.1), `research_notes/Datos reales estación Shell San Rafael/{01,03,06}_*.md`, `CLAUDE.md`, `TASK.md`, `README.md` y la lectura completa del código. Si aparece un `onboarding.md`, **reconciliarlo con §5 y §6 antes de seguir** (si difiere, avisar al usuario; no elegir en silencio).
>
> **Mensaje de arranque sugerido para pegarle al agente:**
> *"Leé `ORQUESTADOR_SIMULADOR.md` completo. Ejecutá la Fase 0 y la Fase 1, pasá sus compuertas (gates) y reportame con el formato de §13. No avances a la Fase 2 sin mi OK."*

---

## 0. Cómo trabajar con este archivo (protocolo del agente)

1. **Orden de lectura obligatorio** (≈ 25 min): este archivo → `CASO_SHELL_SAN_RAFAEL.md` → `CLAUDE.md` → `sim/config.py` → `sim/modelo.py` → `app.py` → `ui/animacion.py` → `ui/graficos.py` → `ui/textos.py` → `verificar.py`. Las notas de investigación (`research_notes/…`) se consultan **por parámetro** (la tabla de §5 dice en qué archivo y sección está cada dato).
2. **Trabajá por fases (§9).** Cada fase tiene archivos, entregable visible y **compuerta** (comandos que deben pasar). No se abre la fase siguiente con la compuerta en rojo.
3. **Un commit por fase** (mensajes en castellano, descriptivos). Pushear a la rama de trabajo. **No crear Pull Request** salvo que el usuario lo pida.
4. **Nunca inventes un número en silencio.** Todo valor nuevo entra por el **Registro de datos** (§5.1) con `tipo`, `fuente` y `confianza`. Si no hay dato, es `SUPUESTO` y la interfaz lo muestra con su insignia (§8.4). Esta es la regla de oro del caso (`CASO §0`).
5. **Distinguí tres cosas en todo lo que escribas:** *dato* (tiene fuente), *supuesto* (sin fuente, marcado) y *propuesta del orquestador* (decisión de diseño de este archivo, reversible). La columna "Origen" de §5 lo indica.
6. **Si una decisión abierta (§6) bloquea tu trabajo**, usá el **default** que está ahí, dejalo detrás de un parámetro y anotalo en el reporte. Preguntale al usuario sólo si el default no existe.
7. **Reportá con el formato de §13** al cerrar cada fase.

---

## 1. Misión y definición de "terminado"

**Misión.** Pasar de un simulador *hipotético* (3 surtidores, 1 caja, 1 tanque, números inventados, paleta oscura genérica) a **la herramienta del caso real**: la estación **Shell de Av. Balloffet 1810 esq. Av. Los Sauces, San Rafael, Mendoza** (operador LOS SAUCES S.R.L.). El producto central del TP es un **informe del caso**; el simulador ilustra los escenarios. Pero el simulador tiene que ser **completo, defendible, y mostrar cada dato con su fuente**.

**Está terminado cuando se cumplen TODAS:**

| # | Criterio verificable |
|---|---|
| D1 | La estación modelada tiene **12 caras en 3 grupos** (A nafta 4 · B diésel 2 · C GNC 6), minimarket y **playeros por turno**; servidores = *mín(caras libres, playeros en turno)* para nafta/diésel. |
| D2 | **Cinco productos** (Súper, V-Power, Diésel común, V-Power Diesel, GNC). Líquidos con **tanque propio**; GNC sin tanque (depende de **disponibilidad**). |
| D3 | **Red de abastecimiento** con camino más corto (Dijkstra), cortes de ruta y su efecto en el plazo de entrega y en el quiebre de stock. |
| D4 | **Corte de GNC en invierno** con ventana horaria, y **migración** de parte de esos clientes a nafta. |
| D5 | **Cuatro estaciones del año** con juego de parámetros propio, y comparativa entre ellas. |
| D6 | **Cada parámetro del modelo** se muestra en la app con valor, unidad, fuente, nivel, tipo y confianza, y se puede **exportar a CSV** (anexo de fuentes). Cero parámetros "huérfanos" (lo verifica un control automático). |
| D7 | La interfaz usa la **paleta Shell** (§8.1) de forma coherente en tema de Streamlit, gráficos Plotly y animación SVG, con contraste legible (control automático, §10.3). |
| D8 | La **animación** muestra el playón real: 3 zonas, 12 posiciones de carga, playeros, cola que puede desbordar a la avenida, minimarket, **tanques por producto**, camión en ruta y estado del GNC. |
| D9 | **Análisis de sensibilidad** (tornado) sobre los `SUPUESTO`s: cuánto mueven el resultado en $/mes. |
| D10 | `python verificar.py` pasa **los 22 controles originales + los nuevos** de §10.2; el **caso degenerado** reproduce *exactamente* los números dorados de §14.1. |
| D11 | `CLAUDE.md`, `TASK.md` y `README.md` actualizados al nuevo alcance (§9, Fase 10). |

---

## 2. Contexto condensado (lo imprescindible)

### 2.1 Qué pasó
El profesor objetó que el proyecto se apoyaba en una **simulación hipotética** (demanda, tiempos y costos inventados). Se pivotó a **un caso real comprobable**: una estación concreta con datos con fuente. Consigna original: *"cualquier tema, que corra en algún software, que tenga alguna complejidad, preferiblemente aspectos económicos. Colas, transporte, Montecarlo, etc."* Se usa **motor propio** (no Simul8). Grupo: **Andino–Assenza**. Materia: Investigación Operativa.

### 2.2 La estación (resumen; detalle en §5 y en `research_notes/…/01_*.md`)
- **Dirección oficial (Shell):** "BALLOFFET 1810 ESQ. LOS SAUCES", San Rafael, CP 5600. Grafía correcta **Balloffet** (la SE y OSM escriben "Ballofet"). "Bayofet/Bayofed" **no existe** en ninguna fuente: es una deformación fonética del audio original; **no usarla**.
- **Surtidores (según el grupo, captura de Google Maps):** 6 surtidores de doble cara = **12 caras**. S1–S2 nafta (Súper y V-Power), S3 diésel, S4–S6 GNC. Cada captura muestra 6 flechas rojas (6+6): *una flecha = una cara = un carril de acceso*.
- **Servicio atendido por playero** (Shell: `full_service` + `manned`), **playa 24 h**, minimarket (`shop`, horario **sin confirmar**), baño, aire y agua. No figuran ATM ni lavadero.
- **Entorno:** Av. Balloffet es la **RN 143** (tramo urbano, 4 carriles, 60 km/h); Av. Los Sauces es la **RP 158**. Zona **urbana consolidada** (no rural). Otras Shell a 2,26 y 3,60 km; ninguna estación a < 1,5 km.
- **Abastecimiento líquido:** camión cisterna; para Shell el origen documentado es **Dock Sud** (Buenos Aires), ≈ 991 km vía Gral. Alvear (nivel C, 2023, confianza media). Luján de Cuyo es origen de otras banderas.
- **GNC:** viene de la red de gas, se comprime en la estación; en **invierno** se restringe por orden de Ecogas (caso documentado: San Rafael, 23/6/2022, 8 estaciones afectadas).

### 2.3 Qué se conserva y qué queda superado
| Se conserva | Queda superado (ya NO rige) |
|---|---|
| Motor SimPy, streams RNG con semilla y **números aleatorios comunes** | `CLAUDE.md` § "NO hacer": **varios combustibles** y **fallas de equipos** (ahora se hacen). |
| Colas (FIFO), Monte Carlo de **5 pasos**, inventario **(s, Q)**, economía, **22 controles** | "**Un solo producto**" y "**un solo tanque**". |
| IC 95 % (t de Student), calentamiento, promedios temporales | "**Una réplica = un mes genérico**": ahora un mes por **estación del año**. |
| Convenciones: castellano, `frozen=True`, `sim/` sin Streamlit, sin `print()` en `sim/` | Tabla de demanda, perfil horario y tiempos **inventados** (pasan a `SUPUESTO` visibles hasta tener dato). |

**Siguen prohibidos** (no escalable a propósito): base de datos, autenticación, API REST, Docker, plugins, capas de abstracción "para el futuro", **multiprocessing**, lavadero, camiones como *clientes del surtidor de forma masiva*, turnos de empleados con **horas extra/ausentismo**.

---

## 3. Reglas inamovibles (invariantes)

1. **`sim/` nunca importa `streamlit` ni `ui/`.** El motor corre solo (script o notebook).
2. **Todo en castellano** (nombres, docstrings, textos de UI).
3. **Unidades:** tiempo en **minutos** (día = 1440), dinero en **pesos**, volumen en **litros**. **Excepción única y explícita: el GNC se mide en m³** (así se vende; su precio es $/m³). Cada `Producto` declara su `unidad`. **Prohibido sumar litros con m³**: agregá en **pesos** o por producto.
4. `@dataclass(frozen=True)` para parámetros; **tuplas, no listas/dicts mutables** dentro de las dataclasses de parámetros.
5. **Reproducibilidad:** toda aleatoriedad sale de `sim/distribuciones.py` con semilla explícita. **Streams nuevos se AGREGAN AL FINAL de `STREAMS`** (la semilla de cada stream depende de su índice; reordenar rompe la reproducción de todo lo anterior).
6. Los atributos del cliente (tipo de vehículo, producto, litros, si compra) se sortean **al llegar**, no al ser atendido (números aleatorios comunes entre escenarios).
7. Sin `print()` en `sim/`. El motor devuelve datos.
8. **No romper los 22 controles de `verificar.py`.** El **caso degenerado** (§10.1) existe justamente para garantizarlo.
9. **Ningún parámetro sin fila en el Registro de datos** (§5.1).
10. **No usar el logo/pecten de Shell** (marca registrada). Se usa **sólo la paleta**. Pie fijo en la app: *"Proyecto académico de Investigación Operativa; no es oficial ni está afiliado a Shell."*

---

## 4. Mapa del código actual y qué cambia

Línea base **verificada el 5/10/2026**: `python verificar.py` → "Todos los controles pasaron" (22/22). Python 3.11 en este entorno (el proyecto declara 3.14; no usar nada específico de 3.14). Dependencias: `simpy`, `streamlit>=1.40`, `plotly>=6`, `pandas`, `numpy`.

| Archivo | Hoy | Cambio requerido | Fase |
|---|---|---|---|
| `sim/config.py` (410 l.) | `ParametrosSimulacion` plano: `surtidores`, `cajas`, 1 `ParametrosTanque`, `PerfilHorario`, `DemandaDiaria`, `Escenario`(+1 surtidor/cajero), `ParametrosEconomicos` | Agregar **`Producto`, `GrupoSurtidores`, `TipoVehiculo`, `Turno`, `EstacionDelAnio`, `ParametrosRed`, `ParametrosGNC`**; `ParametrosSimulacion` pasa a componerlos. **Mantener un constructor de compatibilidad** (`ParametrosSimulacion.clasico()` = defaults de hoy). | 2, 4–7 |
| `sim/datos.py` | **No existe** | **NUEVO:** Registro de datos (§5.1) con TODAS las filas de §5. Fuente única de los defaults. | 1 |
| `sim/distribuciones.py` | 7 streams | Agregar al final: `"vehiculo"`, `"producto"`, `"corte_gnc"`, `"corte_ruta"`, `"migracion"`. Agregar `discreta(pesos, stream)` (sorteo por pesos). | 2 |
| `sim/modelo.py` (404 l.) | 1 `Resource` surtidores + 1 caja + 1 tanque | Recursos **por grupo**; **playeros por turno**; cola finita/balking; tanque **por producto**; camión con **plazo = base + efecto de la red**; **ventana de corte GNC** + migración; clientes con `tipo`, `producto`. | 2, 4, 5, 6 |
| `sim/red.py` | **No existe** | **NUEVO:** grafo + Dijkstra (`heapq`, sin dependencias) + estado de arcos (§7.4). | 5 |
| `sim/estadisticas.py` | contadores globales | Contadores **por grupo y por producto**, por **motivo de pérdida** (§7.6), por franja horaria y por estación del año. | 2, 4 |
| `sim/traza.py` | `Cuadro` de 13 campos | `Cuadro` **v2** (§8.6): por grupo y por producto, playeros, GNC, camión. Serie de tanques ×4. | 3 |
| `sim/runner.py` | `ResultadoReplica` plano; `escenarios_desde` | Resultados **por grupo/producto**; catálogo de escenarios **S1–S8** (§7.7); corrida **por estación del año**; `barrer_politicas` por producto. | 4, 7, 8 |
| `sim/economia.py` | margen único, 1 tanque | Márgenes **por producto**; flete **por km**; costo de playeros; anualización. | 8 |
| `sim/sensibilidad.py` | **No existe** | **NUEVO:** tornado (§7.9). | 9 |
| `ui/tema.py` | **No existe** | **NUEVO:** **única fuente** de la paleta (§8.1): constantes Python + `css_global()` + `paleta_json()` para el SVG. | 1 |
| `ui/datos_ui.py` | **No existe** | **NUEVO:** insignias, `etiqueta(dato_id)`, tabla de fuentes, export CSV. | 1 |
| `ui/animacion.py` (415 l.) | SVG 1000×520, 3 columnas, 1 tanque, paleta oscura propia | **Rediseño completo** (§8.5). | 3 |
| `ui/graficos.py` (490 l.) | Plotly `plotly_white`, colores sueltos | Todo consume `ui/tema.py`; gráficos nuevos (§8.3). | 1, 4–9 |
| `ui/textos.py` | Métricas y textos del modelo viejo | Métricas nuevas; `SUPUESTOS` pasa a **generarse desde el Registro**. | 1, 4 |
| `app.py` (948 l.) | 8 pestañas, sidebar de números sueltos | Reestructura (§8.2); sidebar **alimentada por el Registro**. | 1–9 |
| `.streamlit/config.toml` | `fileWatcherType = "poll"` | Agregar `[theme]` (§8.1). **No quitar el `poll`.** | 1 |
| `verificar.py` | 22 controles | + controles de §10.2. | todas |
| `CLAUDE.md`, `TASK.md`, `README.md` | Proyecto hipotético | Reescribir (Fase 10). | 10 |

Rendimiento de partida: réplica de 30 días ≈ 0,5 s; corrida de 4 escenarios × 4 réplicas ≈ 12–15 s; barrido de 13 políticas × 2 réplicas ≈ 16 s. **Presupuesto nuevo:** réplica ≤ 1,5 s; todo lo pesado va **detrás de un botón propio** y con `st.cache_data`.

---

## 5. Los datos

### 5.1 Registro de datos (contrato — Fase 1)

Crear `sim/datos.py`:

```python
@dataclass(frozen=True)
class Dato:
    id: str                      # "DEM-05"
    nombre: str                  # "Litros por carga (autos nafta)"
    valor: float | str | tuple   # el valor que usa el modelo
    unidad: str                  # "L", "min", "h", "$/L", "m³", "%", "km", "-"
    bajo: float | None = None    # rango de sensibilidad
    alto: float | None = None
    nivel: str = "?"             # A estación · B San Rafael · C Mendoza · D ciudad parecida · E Argentina/otro
    tipo: str = "supuesto"       # "dato" | "estimacion" | "observacion" | "supuesto" | "heredado"
    confianza: str = "baja"      # "alta" | "media" | "baja" | "sin_dato"
    fuente: str = ""             # título corto + organismo
    url: str = ""
    fecha_fuente: str = ""       # fecha ORIGINAL de la nota (no la del buscador)
    nota: str = ""               # contradicciones, advertencias
    origen: str = "investigacion"# "investigacion" | "grupo" | "orquestador"
```

Reglas: (a) `REGISTRO: tuple[Dato, ...]` + `por_id(id)`; (b) **los defaults de `config.py` se construyen leyendo el Registro** (nunca literales sueltos); (c) `tipo="heredado"` = valor del proyecto hipotético **sin fuente**, se mantiene como placeholder hasta tener dato y se muestra como tal; (d) el control **N14** (§10.2) falla si algún campo de `ParametrosSimulacion` no tiene `Dato` asociado.

### 5.2 Tabla maestra de parámetros

Leyenda de **Origen**: `INV` = nota de investigación (`01`/`03`/`06`) · `GRP` = lo dijo el grupo · `ORQ` = propuesta de este orquestador · `HER` = heredado del proyecto hipotético. **Conf.**: A/M/B/— (alta/media/baja/sin dato). Todas las fuentes se consultaron el 5/10/2026 salvo indicación; las fechas de cada nota original están en las notas de investigación (usar *esas* fechas, no las del buscador).

#### A. Identidad y servicios (nota 01 §1A)
| ID | Dato | Valor | Nivel | Tipo | Conf. | Origen / fuente |
|---|---|---|---|---|---|---|
| EST-01 | Dirección | Balloffet 1810 esq. Los Sauces, San Rafael, CP 5600 | A | dato | A | INV · Shell localizador (API geoapp) + SE |
| EST-02 | Operador / CUIT | LOS SAUCES S.R.L. / 30-67218048-8 | A | dato | A | INV · Shell, SE y OSM coinciden |
| EST-03 | Bandera | Shell (SHELL C.A.P.S.A., idempresa 674) | A | dato | A | INV · SE |
| EST-04 | Coordenadas | −34,62833 ; −68,35832 | A | dato | A | INV · SE y Shell (dif. ≈ 6 m) |
| EST-05 | Horario playa | 24 h todos los días | A | dato | A | INV · Shell `twenty_four_hour` |
| EST-06 | Horario minimarket | 24 h (**sin confirmar**; Shell: `shop_open_status: unknown`) | A | supuesto | B | GRP · V10 |
| EST-07 | Servicios | tienda, baño, aire y agua, servicio atendido, pago en surtidor/móvil, tarjeta de flota. **No figuran** ATM ni lavadero ("no figura" ≠ "no existe") | A | dato | A/M | INV · Shell |
| EST-08 | Calzadas | Balloffet = RN 143 (4 carriles, 60 km/h, OSM); Los Sauces = RP 158 | A | dato | M | INV · Gob. Mendoza 2018/2025 + OSM |
| EST-09 | Otras Shell | CAR GAS (2,26 km), PUNTO MITRE (3,60 km); ninguna estación a < 1,5 km | B | dato | A | INV · Shell API; CASO §3.4 |

#### B. Surtidores y personal
| ID | Dato | Valor | Nivel | Tipo | Conf. | Origen / fuente |
|---|---|---|---|---|---|---|
| SUR-01 | Surtidores / caras | 6 / 12 | A | dato | M | GRP · V2 |
| SUR-02 | Grupo A nafta | S1, S2 → 4 caras → Súper y V-Power | A | dato | M | GRP · V3 (**contradicción a resolver**, §6) |
| SUR-03 | Grupo B diésel | S3 → 2 caras → Diésel común y V-Power Diesel | A | dato | M | GRP · V3/V5 + SE declara Gas Oil G2 **y** G3 |
| SUR-04 | Grupo C GNC | S4, S5, S6 → 6 caras | A | dato | M | GRP |
| SUR-05 | Vehículos por cara | 1 a la vez (una manguera activa por cara) | A | supuesto | M | GRP · V2/V4 |
| SUR-06 | Compresores GNC | = nº de caras GNC (**sin límite** hasta relevar) | A | supuesto | — | ORQ · V6 |
| PER-01 | Playeros por turno | **placeholder:** noche 22–06 → 2 · mañana 06–14 → 4 · tarde 14–22 → 4 | A | supuesto | — | ORQ · **sin dato**, relevar (CASO §5.4) |
| PER-02 | Cajeros por turno | 1 en los tres turnos | A | heredado | — | HER (caja única) |
| PER-03 | GNC retiene playero | No (el playero sólo conecta, ≈ 1 min; se desprecia) | A | supuesto | — | ORQ |
| PER-04 | Capacidad de cola antes de la avenida | 8 autos por grupo (excedente = no entra) | A | supuesto | — | ORQ · relevar (CASO §5.3) |
| PER-05 | Disciplina de cola | **cola única por grupo** (default) · opción **fila por cara** (línea múltiple, sin cambio de fila) | A | supuesto | — | ORQ · CASO §7 |

#### C. Demanda (nota 03 + herencia; **es el hueco más grande**)
| ID | Dato | Valor | Nivel | Tipo | Conf. | Origen / fuente |
|---|---|---|---|---|---|---|
| DEM-01 | Autos por día (Monte Carlo) | tabla: 280/320/360/400/440 con frecuencias 10/20/40/20/10 (media 360) | — | heredado | — | HER. **No tiene fuente.** Orden de magnitud coherente con 200–330 m³/mes por estación (D5 Surtidores.com.ar 2018, baja; tesis UCES [RESUMEN]). **Reemplazar con el relevamiento.** |
| DEM-02 | Perfil horario | `PERFIL_TIPICO` (24 factores; picos 08 h y 19 h) | — | heredado | — | HER |
| DEM-03 | Tipo de día | hábil 1,00 · fin de semana 1,00 · feriado 1,00 (**sin dato** → neutro, pero editable) | — | supuesto | — | ORQ (CASO §5.1) |
| DEM-04 | Mezcla de tipo de vehículo | moto 10 % · auto 73,8 % · pick-up/utilitario 13,5 % · camión/ómnibus 2,7 % | E | estimación | B | ORQ sobre D10 (flota nacional 82/15/3 % → ×0,9) + motos 10 % supuesto |
| DEM-05 | Mezcla de producto (de los que cargan) | Súper 52,1 · V-Power 11,4 · Diésel común 21,7 · V-Power Diesel 3,8 · GNC 10,6 (**normalizar a 100**) | E | estimación | B | ORQ sobre D11 (flota nac.: nafta 63,5 / diésel 25,5 / GNC 10,6 %); reparto premium/común **supuesto** (18 % / 15 %) |
| DEM-06 | Estacionalidad de la demanda | verano/otoño/invierno/primavera = 1,00 cada una (**sin dato**) | B/C | supuesto | — | ORQ. Fuentes candidatas: SE ventas mensuales por provincia, DEIE Mendoza, turismo San Rafael (vendimia = marzo, vacaciones de invierno = julio) |

#### D. Vehículos y litros por carga (nota 03 §1C–1D)
Regla del orquestador (**derivada y verificada algebraicamente**): litros de una carga ~ `Triangular(0,20·T ; 0,30·T ; 1,00·T)`, con `T` = tanque. Moda 0,30·T (único anclaje empírico: D1, ≈ 30 % del tanque, 2020, **baja**), máximo 1,00·T (límite físico), media **exacta 0,50·T** (convención de la nota). El mínimo 0,20·T es `SUPUESTO`. *La nota da 0,30/0,50/1,00·T como tres **escenarios de la media**, no como una distribución; esta triangular es la forma de cumplir la media base con un máximo físico. Para sensibilidad: escalar toda la distribución por k ∈ {0,6; 1,0; 1,6} con tope en T.*

| ID | Tipo | Tanque T | Litros por carga (mín · moda · máx) → media | Participación | Fuente | Conf. |
|---|---|---|---|---|---|---|
| VEH-01 | Auto nafta | **47 L** (promedio ponderado de Yaris/Cronos/208/Polo; rango 42–52) | 9,4 · 14,1 · 47 → **23,5** | 73,8 % | INV D16 (Autocosmos, OK-orig) | M |
| VEH-02 | Pick-up / utilitario | **80 L** (Hilux/Ranger/Amarok) | 16 · 24 · 80 → **40** | 13,5 % | INV D18 (**[RESUMEN]**: fichas oficiales dieron 403) | M-B |
| VEH-03 | Moto 110 cc | **3,7 L** (3,5–4,1) | 0,74 · 1,11 · 3,7 → **1,85** | 10 % | INV D19 ([RESUMEN]) | M-B |
| VEH-04 | Camión / ómnibus | **300 L** (**sin dato argentino**; Europa 120–1.000 L) | 60 · 90 · 300 → **150** | 2,7 % | ORQ (el "300–400 L" del informe externo es *no verificable*). Hay un ómnibus en la captura 1. | — |
| VEH-05 | Auto GNC (m³) | cilindro mediano **14 m³** | 2,8 · 4,2 · 14 → **7 m³** | (parte del 10,6 %) | INV D25/§2.10 ([RESUMEN]); regla ORQ | B |
| — | Tractor / maquinaria | **excluido** (sin evidencia de que carguen en estación) | — | 0 % | INV D21 | — |

Chequeo de calibración que **la app debe mostrar**: litros/día esperados = Σ(autos × participación × media de litros) y compararlo contra la banda 200.000–330.000 L/mes por estación (D5; confianza baja). Con los defaults, ≈ 360 autos × 27 L ≈ 9.700 L/día ≈ 290.000 L/mes, **sin descontar** los clientes GNC (que miden m³, no litros), así que el valor real será algo menor (**coherente en orden de magnitud, no una validación**).

#### E. Tiempos de servicio (nota 03 §1E)
| ID | Dato | Valor | Nivel | Tipo | Conf. | Origen |
|---|---|---|---|---|---|---|
| TIE-01 | Caudal de surtidor | 40 L/min estándar · 90–120 L/min alto caudal (diésel) | E | dato | B | INV D22/D23 (Paraguay 2012, no es norma argentina) |
| TIE-02 | **Tiempo total por vehículo en la cara** (maniobra + carga + cobro + salida) nafta/diésel | `Triangular(2,4 ; 3,7 ; 5,0)` min | E | supuesto | muy baja | INV §1E (punto medio de dos referencias débiles; **sin medición**) |
| TIE-03 | Extra camión/ómnibus | `+ litros / 90` min | E | supuesto | B | ORQ (con 40 L/min el caudal **no** es cuello de botella para autos) |
| TIE-04 | Tiempo de carga GNC | `Triangular(10 ; 15 ; 30)` min | E | supuesto | B | INV D25 ([RESUMEN]; 10–30 min, "probablemente incluye espera"); moda = ORQ |
| TIE-05 | Compra en minimarket | `Triangular(1,5 ; 3 ; 6)` min | — | heredado | — | HER |
| TIE-06 | Prob. de entrar al minimarket | 0,30 en todos los tipos (**hipótesis a contrastar:** GNC compra más → escenario 0,45, *no* default) | — | heredado | — | HER · CASO §4 |
| TIE-07 | Paciencia (cola de cara / caja) | 10 / 8 min | — | heredado | — | HER |

#### F. Inventario y logística (nota 06)
| ID | Dato | Valor | Nivel | Tipo | Conf. | Origen / fuente |
|---|---|---|---|---|---|---|
| INV-01 | Plazo pedido→entrega | `Triangular(24 ; 36 ; 48)` h | C | dato (extremos supuestos) | M | INV 06 §1.5 · Sitio Andino 27-oct-2023: "casi 1 día y medio" (estación Shell de Mendoza **capital**, no San Rafael). **Reemplaza** el `Triangular(8,16,36)` h inventado. |
| INV-02 | Carga del camión | 30.000 L (27.000–34.000) | C | estimación | M | INV 06 §1.4 · 27.000 L (2023) y 34.000 L (2009); promedio redondeado |
| INV-03 | Capacidad de cada tanque subterráneo | 20.000 L por producto líquido (10.000–25.000) | C | supuesto | B | INV 06 §1.4 · aviso de venta de Guaymallén, **no verificado** |
| INV-04 | Tiempo de descarga | 45 min (30–90) | — | supuesto | — | INV 06 (sin fuente; sensibilidad baja) |
| INV-05 | Origen del combustible | **Dock Sud** (default; Shell/Raízen) · alternativa **Luján de Cuyo** (YPF; inferencia) | C | dato/inferencia | M | INV 06 §1.1. Shell fue vendida a Mercuria (jun-2026); la logística puede cambiar. |
| INV-06 | Política de reposición real | **no documentada** (pedido "a demanda" del encargado: *"solicitamos a la refinería y nos mandan el volumen necesario"*) | C | — | B | INV 06 §1.6 |
| INV-07 | Política (s, Q) inicial por producto | s ≈ consumo en el plazo + seguridad ⇒ cubrir **1,5 días**; Q = lo que entra sin pasar el tanque. Calcularlo en código (`grilla_sugerida` adaptada). | — | ORQ | — | ORQ |
| INV-08 | Camión **consolidado** | un viaje lleva varios productos (observado: 27.000 L de gasoil **y** naftas en un solo camión) | C | dato | M | INV 06 §1.4. Ver §7.3 |
| INV-09 | Crisis de abastecimiento Shell | faltante 3–4 días en el Gran Mendoza (29-jul→1/2-ago-2023); Shell sin combustible a media mañana en San Rafael el 27-oct-2023 | B/C | dato | B-M | INV 06 §1.1/1.5 → **escenario S7** |

#### G. Red de abastecimiento (nota 06 §1.2, §1.3)
Tiempo de viaje del camión = `km ÷ 70 km/h` (**supuesto**: promedio entre 80 km/h legales para camiones/sustancias peligrosas —Ley 24.449 art. 51— y 60 km/h de cruces urbanos/obras; OSRM da 81 km/h promedio, inalcanzable para un camión).

| Nodo A | Nodo B | Ruta | km | min a 70 km/h | Cortable |
|---|---|---|---|---|---|
| `LUJAN` (refinería YPF) | `PAREDITAS` | RN 40 | 114 *(derivado: 221,8 − 107 − ≈3)* | 98 | sí (nieve) |
| `PAREDITAS` | `SANRAFAEL` (estación) | RN 143 | 107 | 92 | **sí** (nieve jun–ago; obra) |
| `PAREDITAS` | `SOSNEADO` | RN 40 | 176 | 151 | sí (nieve) |
| `SOSNEADO` | `SANRAFAEL` | RN 144 | 132 | 113 | sí (nieve) |
| `ALVEAR` (Gral. Alvear) | `SANRAFAEL` | RN 143 este | 87,5 (84–94) | 75 | opcional (sin datos de corte) |
| `SANRAFAEL` | `MONTECOMAN` | RN 146 | 54,1 | 46 | no |
| `MONTECOMAN` | `LAPAZ` | RP 153 *(trazado **no verificado**)* | 204,7 | 175 | no |
| `LAPAZ` | `LUJAN` | RN 7 | 141,0 | 121 | no |
| `DOCK` (Dock Sud) | `ALVEAR` | ruta **no verificada** | 903,8 | 775 | no |
| `DOCK` | `LUJAN` | ruta **no verificada** | 1.056,5 | 906 | no |

**Resultados esperados (los usa el control N6):** Luján→estación directo = **221,8 km / 190 min** (por Pareditas). Con RN 143 cortada el mínimo es la variante **norte** (141 + 204,7 + 54,1 = **399,8 km**, **+178 km**, **+153 min**) frente a la sur (114 + 176 + 132 = 422 km). Dock Sud→estación vía Alvear = **991,3 km / 14,2 h** < vía Luján 1.279,0 km / 18,3 h.
**Consecuencia clave que la app debe mostrar:** si el origen es **Dock Sud** (Shell), el corte nevado de la RN 143 *Pareditas–San Rafael* **no está en su ruta**; sí lo estaría para un origen Luján. (Inferencia sin confirmar: que los camiones Shell entren por Gral. Alvear.)

**Cortes documentados → escenarios, NO probabilidades** (hay 3 casos, no una estadística):
| Escenario | Descripción | Duración | Base |
|---|---|---|---|
| E1 | RN 143 (Pareditas–San Rafael) cerrada por nieve | 6 h (supuesto sobre el caso 17-ago-2026: cerrada a las 12:55, reabierta ≈ 16:00) | 3 medios |
| E2 | RN 143 + RN 40 + RN 144 cerradas (caso 1–2-jul-2026) | 24–48 h (supuesto; seguía cortada a las 09:00 del 2-jul) | Los Andes, Sitio Andino |
| E3 | Obra de reconstrucción de la RN 143: restricción 8–18 h | demora = **30 min por viaje** (**sin dato**; NO ENCONTRADO) | Sitio Andino 27-jun-2026 |
Estacionalidad de los cortes por nieve: **jun–ago** (media; 3 casos). Fuera de esos meses `p_corte = 0` por defecto.

#### H. GNC (CASO §6.2; sin nota de investigación aún)
| ID | Dato | Valor | Tipo | Conf. | Origen |
|---|---|---|---|---|---|
| GNC-01 | Disponibilidad | corte por orden de Ecogas en olas de frío; el residencial tiene prioridad | dato | M | CASO §6.2 · Sitio Andino 23/6/2022 (8 estaciones afectadas en San Rafael) |
| GNC-02 | Ventanas observadas | (a) 17:00→01:00 (8 h) · (b) desde 09:00 "hasta nuevo aviso" | dato | M | idem |
| GNC-03 | Prob. de día con corte | invierno **0,10** · resto 0 (**placeholder**; 1 solo caso documentado) | supuesto | — | ORQ |
| GNC-04 | Migración a nafta durante el corte | **30 %** del GNC pasa a Súper (el resto se pierde) | supuesto | — | ORQ (CASO §6.2 pide relevarlo; sensibilidad 0–60 %) |
| GNC-05 | Flujo máximo de la red de gas | **no hay datos de capacidad** → se modela como **ventana de corte aleatoria** (fallback que autoriza `CASO §6.2`). El flujo máximo (Edmonds-Karp) es **opcional y último** (Fase 6b): sólo con capacidades reales. | — | — | CASO |

#### I. Economía (**el otro gran hueco**; todo lo "heredado" es placeholder visible)
| ID | Dato | Valor | Tipo | Conf. | Nota |
|---|---|---|---|---|---|
| ECO-01 | Margen por litro | $100/L | heredado | — | Equivale a ≈ 4,8 % del Súper a $2.099. **Sin fuente.** Candidatas: CECHA, FECRA. Parametrizar también como **% del precio**. |
| ECO-02 | Margen minimarket por compra | $2.500 | heredado | — | |
| ECO-03 | Precios al público (referencia) | Mendoza, 6/5/2026: Súper **$2.099** · V-Power **$2.399** · V-Power Diesel **$2.411** · YPF Diésel 500 $2.173 | dato | A (a esa fecha) | INV 01 D4. **+15,4 % en 2 meses:** actualizar a octubre-2026 antes de usar. |
| ECO-04 | Precios declarados por la propia estación a la SE | Súper $1.315 · Premium $1.555 · Gas Oil G2 $1.389 · G3 $1.574 (fecha 21/6/2025); **GNC $668,50/m³** (8/11/2024) | dato | **baja como precio vigente** | INV 01 §1B. **Congelados 15–23 meses: NO usar como precio de octubre 2026.** Otras de San Rafael (Puma/DAPSA, sep-2026): $2.171–2.189 (B, baja). |
| ECO-05 | Inversión por surtidor / operativo mensual | $18.000.000 / $250.000 | heredado | — | |
| ECO-06 | Sueldo cajero / playero | $900.000 / **sin dato** (usar el mismo placeholder, rotulado) | heredado | — | Convenio del gremio de estaciones de servicio: **verificar nombre y vigencia** (CASO §5.4) |
| ECO-07 | **Flete** | `costo_fijo + costo_por_km × km_ida_y_vuelta` | ORQ | — | $150.000 por viaje (heredado) es **implausible** para ≈ 1.000 km con 30.000 L; **parametrizar por km** y consultar transportistas. Placeholder rotulado. |
| ECO-08 | Almacenamiento | $25 por litro-mes | heredado | — | |
| ECO-09 | Anualización | año = 3 × Σ(4 meses representativos) | ORQ | — | Rotularlo siempre como estimación |

### 5.3 Advertencias de datos que la app debe MOSTRAR (pestaña "Datos y fuentes")
1. **Precios congelados** de la propia estación en la SE (ECO-04) y +15,4 % en 2 meses en Mendoza (ECO-03).
2. **Fuentes [RESUMEN]** (D18, D19, D20, D21, D25): cifras vistas sólo en el resumen del buscador, **no verificadas en el original**.
3. **Nombre/Grafía:** Balloffet vs Ballofet; "Bayofet/Bayofed" no existe.
4. **Parque de Mendoza:** 907.079 (2024) vs ≈ 789.000 (5 % de la flota nacional 2025): definiciones distintas, sin resolver.
5. **Dock Sud** es el origen documentado para una Shell de Mendoza **capital** en 2023; Shell se vendió a Mercuria (jun-2026).
6. **GNC en m³**, no en litros; sin datos de carga ni de tiempos argentinos.
7. **Sin datos de la propia estación** (volúmenes, horarios del shop, personal): hoy todo es `SUPUESTO`/`heredado` hasta el relevamiento (§12).
8. **Fechas del buscador erróneas** en varias notas (ya corregidas en las fichas con la fecha del original).

---

## 6. Decisiones abiertas (V1–V13) y el default a usar

Si el usuario no respondió, **usá el default, dejalo detrás de un parámetro y documentalo**. Ningún default debe ser irreversible.

| # | Pregunta | Default | Cómo se hace reversible |
|---|---|---|---|
| V1 | Grafía y esquina | "Balloffet", esquina Los Sauces | constante en `ui/textos.py` |
| V2 | ¿Un vehículo por cara? | Sí (12 posiciones de carga) | `GrupoSurtidores.caras`, `SUR-05` |
| V3 | **Contradicción:** ¿S3 es sólo diésel o los tres primeros son nafta? | **S1–S2 nafta, S3 sólo diésel** (versión final del grupo). Nota: la captura 1 está rotulada "surtidores a nafta" (los tres) y Shell lista también `midgrade_gasoline` y `premium_diesel`. | Grupos y productos **por configuración**, no por código |
| V4 | ¿2 mangueras de una cara a la vez? | No (una manguera activa por cara) | — |
| V5 | ¿Diésel común y/o premium? | **Ambos** (la SE los declara: Gas Oil G2 y G3); V-Power Diesel = G3 (equivalencia **media-baja**, no verificada en original) | `Producto.activo` |
| V6 | ¿Cuántos compresores GNC? | Sin límite (= caras GNC) | `ParametrosGNC.compresores` |
| V7 | ¿Siempre playero? | Sí, 24 h, sin autoservicio | `Turno.playeros` |
| V8 | ¿Una flecha = una cara = un carril? | Sí | animación (§8.5) |
| V9 | ¿"Seguir esa lógica en el minimarket"? | Describirlo y calibrarlo como los surtidores; **1 caja** (heredado); nombre genérico "Minimarket" (el nombre comercial **no está confirmado**: Shell sólo dice `shop`) | `Turno.cajeros` |
| V10 | Horario y servicios extra | Playa 24 h (fuente); shop 24 h (supuesto); no modelar lavadero/ATM | `EST-06` |
| V11 | ¿Relevamiento en el lugar? | **Pendiente.** La app debe tener el camino listo para cargarlo (§12) | importador CSV |
| V12 | ¿Año completo o mes por estación? | **Un mes representativo por estación** (4 corridas); opción "año completo" = 12 meses (con aviso de tiempo) | `ParametrosSimulacion.meses` |
| V13 | Criterio de "ciudad parecida" | Jerarquía A→B→C→D; D = ciudades intermedias del interior (hoy sin uso) | campo `nivel` |
| N1 | (nuevo) ¿Cola única por grupo o fila por cara? | **Cola única por grupo**; opción fila por cara para comparar (escenario S8) | `PER-05` |
| N2 | (nuevo) ¿Camión consolidado? | Primero **un camión por producto** (simple); **después** consolidado (§7.3) | `ParametrosTanque.consolidado` |
| N3 | (nuevo) ¿Origen del combustible? | Dock Sud | `ParametrosRed.origen` |
| N4 | (nuevo) ¿Hex exactos de la paleta? | `#FBCE07` / `#DD1D21` (ver §8.1: las fuentes **difieren**) | un solo archivo: `ui/tema.py` |

---

## 7. Especificación del motor (`sim/`)

> Los bloques de código son **contratos**, no implementaciones completas. Respetar nombres y semántica; completar el resto según las convenciones del repo.

### 7.1 Configuración (`sim/config.py`)

```python
@dataclass(frozen=True)
class Producto:
    id: str                 # "super", "vpower", "diesel", "vpower_diesel", "gnc"
    nombre: str
    unidad: str             # "L" | "m3"
    grupo: str              # "A" | "B" | "C"
    tiene_tanque: bool      # False para GNC
    activo: bool = True
    precio: float = 0.0     # $/unidad (referencia, ver ECO-03)
    margen: float = 0.0     # $/unidad (ECO-01)

@dataclass(frozen=True)
class GrupoSurtidores:
    id: str                 # "A", "B", "C"
    nombre: str             # "Nafta", "Diésel", "GNC"
    surtidores: tuple[str, ...]      # ("S1","S2")
    caras_por_surtidor: int = 2
    productos: tuple[str, ...] = ()
    compresores: int | None = None   # sólo GNC; None = sin límite
    requiere_playero: bool = True    # False para GNC (PER-03)
    @property
    def caras(self) -> int: return len(self.surtidores) * self.caras_por_surtidor

@dataclass(frozen=True)
class TipoVehiculo:
    id: str                 # "moto", "auto", "pickup", "camion"
    nombre: str
    tanque: float           # litros
    participacion: float    # 0..1 (se normaliza)
    mezcla_producto: tuple[tuple[str, float], ...]   # (producto, peso)
    litros: Triangular      # ya calculado desde el tanque (regla §5.2-D)
    extra_servicio_por_litro: float = 0.0            # min/L (camión)

@dataclass(frozen=True)
class Turno:
    nombre: str; desde_h: int; hasta_h: int; playeros: int; cajeros: int

@dataclass(frozen=True)
class EstacionDelAnio:
    nombre: str                     # "verano" | "otoño" | "invierno" | "primavera"
    mes_representativo: int         # 1..12 (para rotular y para la nieve)
    factor_demanda: float = 1.0
    p_corte_gnc_dia: float = 0.0
    p_corte_ruta_viaje: float = 0.0 # prob. por viaje de que haya un corte activo
    perfil: PerfilHorario | None = None   # None = usa el base
```

`ParametrosSimulacion` compone: `grupos`, `productos`, `tipos_vehiculo`, `turnos`, `cajas` (por turno vía `Turno`), `tanques` (uno por producto con tanque, cada uno con su `(s, Q)`), `red`, `gnc`, `estacion_del_anio`, `tipo_de_dia`, `capacidad_cola`, `disciplina_cola`. **`ParametrosSimulacion.clasico()`** devuelve exactamente los defaults de hoy (ver §10.1).

### 7.2 Proceso de un cliente (`sim/modelo.py`)

Al **llegar** (todo se sortea acá, con streams propios):
1. `tipo` ← `discreta(participaciones, "vehiculo")`; `producto` ← `discreta(mezcla del tipo, "producto")`; `litros` ← `Triangular` del tipo (stream `"litros"`); `t_servicio` según §5.2-E (stream `"carga"`); `compra` ← Bernoulli (stream `"decision"`).
2. **¿Producto disponible?** Líquido: `nivel[producto] ≥ litros`. GNC: ¿hay ventana de corte activa? → ver §7.5. Si no hay: se registra la pérdida con su **motivo** (§7.6) y el cliente **no hace cola**.
3. **¿Hay lugar en la cola?** Si `len(cola del grupo) ≥ capacidad_cola` → **no entra** (`perdido_cola_llena`).
4. **Cola y servicio:** pedir una **cara** del grupo; si el grupo `requiere_playero`, pedir además un **playero** (ver abajo). Paciencia como hoy (`pedido | timeout`). El combustible se **descuenta al empezar a cargar** (decisión 6 de `CLAUDE.md`, que sigue vigente), **del tanque del producto**.
5. Si compra → cola de **cajas** como hoy (con `cajeros` del turno vigente).

**Playeros por turno.** Orden de adquisición: **cara primero, playero después**. No hay *deadlock* porque un playero sólo se retiene mientras se atiende a un auto que ya tiene cara. Capacidad dinámica: usar `simpy.PriorityResource(capacity=max_playeros)` y un proceso `controlar_turnos()` que, en cada cambio de turno, **toma** (prioridad −1) o **libera** "reservas ficticias" hasta que `capacity − reservas = playeros del turno`. El efecto emergente *"servidores = mín(caras libres, playeros en turno)"* es el deseado: un auto puede ocupar una cara esperando que lo atiendan (fiel a la realidad). Mismo patrón para cajeros si varían por turno.

**Disciplina de cola.** `por_grupo` = un `Resource` por grupo (FIFO). `por_cara` = un `Resource(capacity=1)` por cara; el cliente elige la fila más corta **al llegar** y **no cambia** (línea múltiple de la cátedra). Misma interfaz de indicadores.

### 7.3 Inventario por producto y camión
- Un `nivel` por producto con `tiene_tanque`. `posición = nivel + litros_en_camino` (decisión vigente). Política `(s, Q)` **por producto**.
- **N2 (dos etapas).** *Etapa 1:* un camión por producto (cada pedido su flete). *Etapa 2 (consolidado):* un viaje se dispara cuando **cualquier** posición ≤ `s`; carga hasta `capacidad_camion` (30.000 L) repartida entre los productos con posición ≤ `1,3·s` (proporcional a su `Q`); **un solo flete por viaje**. Dejar la etapa 2 detrás de `consolidado=True`.
- **Plazo de entrega = `plazo_base` (INV-01, triangular 24–36–48 h) + `demora_por_corte`** (§7.4). Conservar el stream `"entrega"` para el plazo base; el efecto de la red sale de `"corte_ruta"`.
- Quiebre por producto: `sin_combustible` pasa a ser **una serie temporal por producto**.
- **Escenario S7 (crisis de abastecimiento):** el plazo se extiende 72–96 h (INV-09) durante una ventana configurable.

### 7.4 Red (`sim/red.py`)
```python
@dataclass(frozen=True)
class Arco:
    a: str; b: str; km: float; ruta: str
    cortable: bool = False
@dataclass(frozen=True)
class ParametrosRed:
    arcos: tuple[Arco, ...]
    origen: str = "DOCK"           # "DOCK" | "LUJAN"
    destino: str = "SANRAFAEL"
    velocidad_kmh: float = 70.0
    # cada corte: (id_arco, duracion_h) activo en una ventana del mes
    escenario_corte: str = "ninguno"   # "ninguno" | "E1" | "E2" | "E3"
```
- `camino_mas_corto(red, origen, destino, arcos_cerrados) -> (km, minutos, ruta)` por Dijkstra con `heapq` (**sin networkx**, para no sumar dependencias).
- Si un corte parte la ruta óptima: `demora = min( tiempo_ruta_alternativa − tiempo_ruta_original , duración_restante_del_corte )` (el camión toma el desvío o espera la reapertura, lo que sea menor). Esa demora **se suma al plazo** (CASO §6.1).
- Los cortes se sortean **por mes** (stream `"corte_ruta"`): en invierno (jun–ago) con `p_corte_ruta_viaje`; E1/E2/E3 se pueden **forzar** como escenarios.
- La red es **determinista salvo el estado de los arcos**.

### 7.5 GNC (`sim/modelo.py`)
- `ParametrosGNC`: `p_corte_dia`, `ventanas: tuple[tuple[float,float],...]` (hora inicio/fin; defaults GNC-02), `migracion_a_nafta` (GNC-04), `compresores`.
- Cada día, con `p_corte_dia` (stream `"corte_gnc"`), se elige una ventana de GNC-02 y queda activa. Durante la ventana: los clientes GNC **no se atienden en GNC**; con prob. `migracion` (stream `"migracion"`) **se convierten en cliente de Súper** (mismo auto, litros según su tipo; entra a la cola del grupo A) y el resto se pierde (`perdido_corte_gnc`). **Los GNC que ya están cargando terminan.**
- Cliente migrado: se cuenta aparte (`migrados_gnc_a_nafta`) para poder mostrar "adónde va esa demanda".

### 7.6 Motivos de pérdida (taxonomía fija; la UI usa estos nombres)
`sin_combustible` (por producto) · `abandono_espera` (reneging) · `cola_llena` (balking) · `corte_gnc` · `abandono_caja` (compra perdida). Más: `migrados_gnc_a_nafta` (no es pérdida). **Todo cliente que llega termina en exactamente una de: atendido · perdido (un motivo) · migrado→atendido/perdido · sigue adentro** (base del control de conservación).

### 7.7 Catálogo de escenarios (reemplaza Base/A/B/C; basado en CASO §7)
| ID | Escenario | Qué varía | Pregunta que responde |
|---|---|---|---|
| S0 | **Hoy** | nada | línea base por estación |
| S1 | Día típico por estación | estación del año | animación y comparativa |
| S2 | **Dotación de playeros en el pico** | playeros −1 / base / +1 / +2 en el pico | ¿alcanza la dotación? |
| S3 | **Ola de frío con corte de GNC** | ventana (a)/(b), migración | pérdida directa y adónde va la demanda |
| S4 | **Corte de la ruta del camión** | E1 / E2 / E3, origen Dock Sud o Luján | plazo, quiebre |
| S5 | **Política de reposición** | barrido (s, Q) por producto, con red y cortes | ¿cuándo y cuánto pedir? |
| S6 | **Decisión económica** | playero extra en pico vs. stock extra en invierno | ¿qué conviene en $/mes? |
| S7 | Crisis de abastecimiento Shell | plazo 72–96 h durante 3–4 días | resiliencia |
| S8 | Cola por grupo vs. fila por cara | `PER-05` | ¿cambia la espera? |
Resultado de cada uno: promedio ± IC 95 % sobre réplicas con **números aleatorios comunes**, igual que hoy. Los "+1 surtidor / +1 cajero" siguen existiendo como variantes de S2/S6 (agregar una **cara** a un grupo, o un **cajero**).

### 7.8 Estaciones del año
`runner.correr_estaciones(p, replicas, semilla)` → 4 `ResultadoEscenario` (uno por estación) con su `EstacionDelAnio`. Sólo difieren parámetros con **base** (hoy: probabilidad de corte de GNC, probabilidad de corte de ruta, y los factores de demanda **si el usuario los carga**). **No inventar factores estacionales**: con 1,00 la comparativa será casi plana *excepto* en GNC/ruta, y eso es lo correcto y honesto hasta tener la serie de la SE.

### 7.9 Sensibilidad (`sim/sensibilidad.py`)
Para cada `Dato` con `tipo in {"supuesto","heredado","estimacion"}` y `bajo/alto` definidos: correr el modelo con `bajo` y con `alto` (resto en base; mismas semillas) y devolver el **delta del beneficio mensual** (o de la métrica elegida). Salida: tabla ordenada + datos para el **tornado**. Costo: ≈ 2 × N corridas; correr **detrás de un botón** y cachear. Objetivo del TP (CASO §9): *"si no hay dato, supuesto justificado + cuánto cambia el resultado"*.

### 7.10 Economía (`sim/economia.py`)
Margen **por producto** (ECO-01 en $/unidad, o % del precio), minimarket, flete `fijo + $/km × km`, almacenamiento por producto, costo de **playeros extra**, venta perdida por motivo. Mantener el criterio actual: *venta perdida = costo de oportunidad* (no se resta del margen: sería contarla dos veces). Reportar **mensual por estación** y **anual estimado** (ECO-09).

---

## 8. Especificación gráfica (`app.py`, `ui/`, `.streamlit/`)

### 8.1 Tema Shell — única fuente: `ui/tema.py`

**Fuentes de color discrepantes** (verificado por búsqueda web el 5/10/2026): una paleta digital habitual da **amarillo `#FBCE07` / rojo `#DD1D21`**; otras fuentes dan **`#FFCD00` / `#DA291C`**. **Default: `#FBCE07` / `#DD1D21`.** Todo el proyecto lee los hex desde `ui/tema.py`; cambiar de variante = **una línea**. Contrastar con las fotos del grupo (surtidores amarillos y blancos, techo del playón) y con el manual de marca si el grupo lo consigue. No usar logo.

```python
# ui/tema.py  (tokens; nombres en castellano)
AMARILLO      = "#FBCE07"   # marca
ROJO          = "#DD1D21"   # marca
AMARILLO_SUAVE= "#FFF6C2"   # fondos tenues, hover
TINTA         = "#1A1A1A"   # texto principal (sobre blanco y sobre amarillo)
TINTA_TENUE   = "#5B5B5B"
FONDO         = "#FFFFFF"
FONDO_PANEL   = "#F6F4EC"   # gris cálido
BORDE         = "#E2DED0"
ASFALTO       = "#2B2F36"   # sólo en la animación (el playón)
# Semánticos (los estados NO dependen sólo del color: siempre llevan texto/ícono)
LIBRE         = "#1E9E5A"
OCUPADO       = AMARILLO
PERDIDO       = ROJO
# Categóricos por producto (separables por daltonismo; ver 10.3)
PRODUCTO = {"super": AMARILLO, "vpower": ROJO, "diesel": "#4B5563",
            "vpower_diesel": "#0F766E", "gnc": "#1D6FB8"}
ESCENARIO = (...)  # 4–9 colores propios, distintos de PRODUCTO
```
**Reglas de uso (obligatorias):**
1. **Amarillo = fondo/relleno/acento, nunca texto sobre blanco** (contraste ≈ 1,6:1). Texto sobre amarillo = `TINTA`. Texto amarillo sólo sobre `ASFALTO`/oscuro.
2. **Rojo de marca** = barra superior, línea de acento, botón primario, pestaña activa. Como el rojo también significa "pérdida", **toda pérdida lleva rótulo** ("SIN COMBUSTIBLE", "GNC CORTADO") y los gráficos de pérdida usan además **trama o etiqueta de valor**, no sólo color.
3. **Un solo tema (claro).** Quitar el diseño oscuro suelto de la animación; el *escenario* del playón (`ASFALTO`) es parte del dibujo, no del tema.
4. Plotly: **un `template` propio** (`ui.tema.plantilla_plotly()`) con `colorway`, fuente, fondo `FONDO`, grilla `BORDE`; reemplazar los `template="plotly_white"` y los hex sueltos de `ui/graficos.py` (`COLOR_ESCENARIO`, `COLOR_SURTIDOR`, `VERDE`, `ROJO`, `NARANJA`, `GRIS`…).
5. Streamlit `[theme]` en `.streamlit/config.toml` (**conservar `fileWatcherType = "poll"`**):
```toml
[theme]
base = "light"
primaryColor = "#DD1D21"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#FFF6C2"
textColor = "#1A1A1A"
font = "sans serif"
```
6. `ui/tema.css_global()` inyecta CSS mínimo (`st.markdown(..., unsafe_allow_html=True)`): franja superior **amarilla con texto `TINTA` y filete rojo inferior**, métricas con borde `BORDE`, insignias (§8.4). `ui/tema.paleta_json()` se inyecta en el HTML de la animación (reemplaza las constantes `FONDO/PANEL/…` hoy hardcodeadas en JS). **Prohibido** repetir un hex fuera de `ui/tema.py` (control N15 lo busca con `grep`).

### 8.2 Estructura de la app (≤ 7 pestañas principales; sub-pestañas adentro)
| Pestaña | Contiene |
|---|---|
| 🏪 **La estación** | ficha (EST-*), esquema de la estación (12 caras, 3 grupos, minimarket), mapa esquemático de la esquina (Balloffet/RN 143 × Los Sauces/RP 158), servicios, **advertencias de datos** (§5.3) |
| 🎬 **Animación** | reproductor (§8.5) + selector de **estación del año, tipo de día y día**, gráficos de colas/ocupación por grupo |
| 📊 **Resultados** | sub-pestañas: *Indicadores* · *Por hora (pico real)* · *Por grupo y producto* · *Comparar escenarios (S0–S8)* |
| 🎲 **Demanda** | Monte Carlo de 5 pasos (**conservar** los pasos 1–5 y la tabla de números aleatorios) + mezcla de vehículos y de productos + perfil por tipo de día/estación + calibración (litros/día vs. banda D5) |
| 🛢️ **Abastecimiento** | sub-pestañas: *Tanques* (4 dientes de sierra + política (s,Q) por producto) · *Red y rutas* · *GNC* · *Estaciones del año* |
| 💰 **Economía y decisión** | *Economía* ($/mes por escenario y anual) · *Sensibilidad* (tornado) · *Conclusión* (las preguntas de §7 del caso, respondidas en $/mes) |
| 📚 **Datos y método** | *Datos y fuentes* (Registro completo, filtros por tipo/confianza/nivel, **descarga CSV**) · *Modelo y método* · *Verificación* (botón que corre los controles y muestra el resultado) |

### 8.3 Gráficos nuevos o modificados (`ui/graficos.py`)
- **Tanques ×4**: dientes de sierra superpuestos o en *small multiples*, con su punto de pedido, color por producto, rótulo de quiebres.
- **Perfil horario por tipo de día** y por estación (llegadas vs. espera, **hora pico descubierta**, no supuesta).
- **Por grupo:** espera, cola y utilización de A/B/C; **playeros** ocupados vs. en turno por hora (aquí se ve el cuello de botella).
- **Pérdidas por motivo** apiladas (6 motivos de §7.6) por escenario/estación.
- **Red:** diagrama de nodos y arcos (Plotly `scatter` con coordenadas esquemáticas o SVG), **ruta óptima resaltada**, arcos cortados tachados, tabla km/min; **distribución del plazo de entrega con y sin cortes** (histograma doble) y su efecto en días con quiebre.
- **GNC:** línea de tiempo del día con la ventana de corte sombreada; barras *atendidos GNC · migrados a nafta · perdidos*.
- **Estaciones del año:** 4 columnas con KPI comparables.
- **Tornado** de sensibilidad (barras horizontales ordenadas por impacto en $/mes).
- Todos: etiquetas de valor, `separators=",."` (castellano), títulos que *dicen la conclusión* cuando se pueda, unidad en el eje.

### 8.4 Insignias de confianza y barra lateral (`ui/datos_ui.py`)
Cada widget de la barra lateral y cada fila de tabla lleva la **insignia de su `Dato`**:
`🟢 dato` · `🟡 estimación` · `🔵 observación propia` · `🟠 supuesto` · `⚪ heredado (sin fuente)`. Más: tooltip (`help=`) con **fuente, nivel, fecha y nota**. `etiqueta(dato_id)` devuelve el texto del widget; `valor_por_defecto(dato_id)` su default. La sidebar se organiza en expanders **por grupo del Registro** (Estación · Personal · Demanda · Vehículos · Tiempos · Abastecimiento · Red · GNC · Economía · Corrida) y se **genera recorriendo el Registro** donde sea posible.
**Anulación por relevamiento:** un `st.data_editor` (o CSV importado) permite pisar cualquier `Dato`; al hacerlo su `tipo` pasa a `observacion` y la insignia cambia a 🔵. Lo cargado se **exporta** junto con el Registro.

### 8.5 Animación (`ui/animacion.py`) — rediseño
Mantener la arquitectura (Python manda JSON, **el navegador dibuja SVG**; `st.components.v1.html`, **no** `st.html`). Lienzo 1200×680.
**Composición** (derivada de las capturas del grupo: playón techado, surtidores amarillos y blancos, edificio con ventanales):
1. **Barra superior**: reloj, *estación del año*, *tipo de día*, día N, estado de medición (calentamiento / midiendo), **contadores** (atendidos, compraron, perdidos por motivo, migrados GNC).
2. **Avenida Balloffet (RN 143)** abajo/izquierda con tráfico de fondo y **entrada**; la **cola desborda a la avenida** cuando supera `capacidad_cola` (autos "no entran": efecto visual + contador).
3. **Playón techado** con **techo amarillo y filete rojo**: **Zona A** (S1–S2: 4 caras = 2 surtidores de doble cara), **Zona B** (S3: 2 caras), **Zona C** (S4–S6: 6 caras). Cada **cara** es una posición de carga con **flecha de acceso** (V8), color de estado (libre/ocupado/sin combustible/cortado) **más texto**, y el auto cargando.
4. **Playeros**: íconos de persona ("n en turno / m ocupados"); un playero aparece junto a la cara que atiende. Si faltan playeros se ve el auto **esperando con la cara ocupada**.
5. **Colas** por grupo, con "+N más" y número.
6. **Minimarket** (edificio con ventanales): cola, cajas, cobrando/libre.
7. **Tanques por producto** (4 barras con color de producto, marca del punto de pedido, litros) y **GNC** con indicador **DISPONIBLE / CORTADO** (franja roja con rótulo).
8. **Camión en ruta**: mini-mapa de la red con el camión avanzando por la **ruta activa**; si hay arco cortado se ve tachado y el camión toma el desvío; texto "llega en X h".
9. Controles: play/pausa, reiniciar, velocidad, barra de tiempo, **saltar a hora pico**, **saltar a quiebre/corte**.
**Contrato de datos del cuadro (v2): formato columnar** (`{"t":[...], "cola":{"A":[...],"B":[...],"C":[...]}, ...}`), **no** listas posicionales como hoy (los índices mágicos son una fuente de errores al ampliar). Campos mínimos por cuadro: `t`, por grupo `{ocupadas, cola, rechazados_cola_llena}`, `playeros {en_turno, ocupados}`, `cajas {ocupadas, cola}`, por producto `nivel` (y `en_camino`), `gnc_cortado`, `camion {en_viaje, progreso, ruta, arco_cortado}`, acumulados por motivo, `migrados`, `en_calentamiento`. Grabar **un solo día** (decisión 5 de `CLAUDE.md`, vigente); `dt_traza` por defecto 0,5 min → 2.880 cuadros; si el JSON pesa demasiado subir `dt` a 1 min.
**Accesibilidad:** nada se comunica sólo por color; contraste de texto ≥ 4,5:1; respetar `prefers-reduced-motion` (arrancar en pausa).

### 8.6 `Cuadro` v2 (`sim/traza.py`)
Reemplazar el `Cuadro` posicional por uno con los campos del contrato anterior; agregar `Traza.serie_tanque(producto)` y `serie_playeros()`; `DiaSimulado` suma: estación del año, tipo de día, ventana GNC activa, corte de ruta activo, litros/m³ por producto, pérdidas por motivo.

### 8.7 Textos (`ui/textos.py`)
Las métricas nuevas (`Metrica`) cubren: espera/cola/utilización **por grupo**, ocupación de **playeros**, pérdidas **por motivo**, nivel de servicio **por producto**, plazo de entrega **con cortes**, GNC atendido/migrado/perdido. `SUPUESTOS` se **genera** desde el Registro (`tipo in {supuesto, heredado}`), no se mantiene a mano. Actualizar `DESCRIPCION_MODELO` (ya no es "un solo producto").

---

## 9. Plan por fases con compuertas

> Cada compuerta lista comandos. **Todas** deben pasar para cerrar la fase. En cada fase: commit en castellano + reporte (§13).

### Fase 0 — Línea base y orden (½ h)
- Instalar dependencias (`pip install -r requirements.txt`); correr `python verificar.py` (debe dar 22/22) y la app (`python -m streamlit run app.py --server.headless true --server.port 8501`).
- **Capturar números dorados** con el script de §14.1 y guardarlos en `verificar.py` (control N1) o en `tests_dorados.json`. *Si no se hace antes de tocar el motor, no hay regresión posible.*
- **Gate:** 22/22 OK + dorados guardados + app levanta.

### Fase 1 — Registro de datos + tema Shell (visible y sin riesgo) ★
- Crear `sim/datos.py` (todas las filas de §5.2), `ui/tema.py`, `ui/datos_ui.py`; `[theme]` en `config.toml`.
- Migrar `ui/graficos.py` al tema (sin cambiar lógica); sidebar con **insignias**; pestaña **📚 Datos y fuentes** con tabla filtrable y **CSV**; pestaña **🏪 La estación** (ficha + advertencias); pie "no afiliado".
- Todavía **no** se toca el motor: los números de resultados no cambian.
- **Gate:** `verificar.py` 22/22 · N14 (parámetros huérfanos) y N15 (hex fuera de `tema.py`, contraste) · captura de pantalla de la app con el tema Shell (§10.4) · el CSV descarga y tiene todas las filas.

### Fase 2 — Núcleo del motor nuevo (grupos, tipos de vehículo, playeros, cola finita)
- `config.py` (§7.1), `distribuciones.py` (streams al final + `discreta`), `modelo.py` (§7.2), `estadisticas.py` (por grupo/motivo).
- **Productos y tanques aún "de a uno"**: sólo se introduce la estructura. `clasico()` **debe reproducir los dorados exactamente**.
- **Gate:** 22/22 · N1 (dorados exactos) · N2–N5, N9, N10 · tiempo de réplica ≤ 1,5 s.

### Fase 3 — Animación nueva
- `Cuadro` v2, columnar; `ui/animacion.py` rediseñada (§8.5) leyendo `paleta_json()`.
- **Gate:** captura de pantalla de cada zona (A/B/C), de la cola desbordada y del camión · sin errores de consola del navegador · controles de saltos funcionando · 22/22.

### Fase 4 — Cinco productos, 4 tanques, política por producto, plazo real
- `Producto`, tanque por producto, plazo INV-01, `grilla_sugerida` por producto, `barrer_politicas` por producto; camión **independiente por producto** (N2 etapa 1).
- Pestaña **Abastecimiento › Tanques**; métricas por producto.
- **Gate:** 22/22 + N3 (conservación **por producto**, y m³ del GNC) · el barrido encuentra una política mejor o igual que la inicial.

### Fase 5 — Red de abastecimiento
- `sim/red.py` (Dijkstra, §7.4), cortes E1/E2/E3, demora → plazo; pestaña **Red y rutas** con el diagrama y la distribución del plazo.
- **Gate:** N6 (los kilómetros/minutos de §5.2-G **exactos**) · N11 (plazo con cortes ≥ sin cortes) · gráfico de la red capturado.

### Fase 6 — GNC y corte invernal (6b opcional: flujo máximo)
- `ParametrosGNC`, ventanas, migración (§7.5); pestaña **GNC**.
- **Gate:** N7, N8 · captura de la ventana sombreada.
- *6b (sólo si aparecen capacidades reales):* Edmonds-Karp en `sim/red.py` + control contra un ejemplo del TP 5. Si no, **omitir y dejarlo documentado**.

### Fase 7 — Estaciones del año y escenarios S0–S8
- `EstacionDelAnio`, `correr_estaciones`, catálogo de §7.7; pestañas **Estaciones del año** y **Resultados › Comparar**.
- **Gate:** N12 · tiempos: corrida de las 4 estaciones × 4 réplicas ≤ 90 s (detrás de botón y cacheada).

### Fase 8 — Economía real
- `economia.py` (§7.10); pestaña **Economía y decisión**; anualización rotulada; conclusión por pregunta del caso (§7 del `CASO`) con textos que **nombran los supuestos** que mueven el resultado.
- **Gate:** el análisis económico reconcilia (ingresos − costos = margen; *venta perdida* **no** se resta) · textos pasan por `escapar_pesos` · 22/22.

### Fase 9 — Sensibilidad
- `sensibilidad.py` + tornado (§7.9).
- **Gate:** el tornado lista **todos** los `supuesto`/`heredado` con `bajo/alto` y el ranking no es constante.

### Fase 10 — Verificación final y documentación
- Todos los controles (§10.2) · QA visual completo (§10.4) · pase de rendimiento.
- Reescribir `CLAUDE.md` (alcance nuevo, §2.3), `TASK.md` (checklist por fases), `README.md` (guion de demo para el caso real; respuestas a preguntas del profesor: ¿por qué datos supuestos?, ¿cómo se validó?, ¿qué es "heredado"?).
- Los `.docx` (`Anteproyecto…`, `Guia_teorica…`) **no se tocan** salvo que el usuario lo pida: están a nombre de un solo integrante y describen el modelo viejo (`CASO §11`).
- **Gate:** checklist D1–D11 de §1 completa.

**Orden recomendado si hay poco tiempo (cada hito deja algo mostrable):** F0 → **F1** → F2 → F3 → F4 → F5 → F6 → F7 → F8 → F9 → F10. Si hay que recortar, **mantener** F1, F2, F4, F5, F6 y **recortar** F9 (parcial) y 6b. (Prioridad del caso: 1 demanda y perfil horario, 2 abastecimiento y red, 3 GNC en invierno; personal y economía fina pueden quedar con supuestos marcados.)

---

## 10. Verificación

### 10.1 Caso degenerado y números dorados
`ParametrosSimulacion.clasico()` = 1 grupo de 3 caras, 1 producto, tanque único 40.000 L con `(s=12.000, Q=20.000)`, plazo `Triangular(8,16,36)` h, playeros ilimitados, sin cola finita, sin red ni GNC, un solo tipo de vehículo con `litros = Triangular(15,30,60)`, `carga = Triangular(3,5,8)`. Con él, el nuevo motor **debe dar idénticos** (a 6 decimales) los valores de §14.1. Si no coinciden, **la fase no cierra**: se rompió el orden de sorteo de algún stream.

### 10.2 Controles nuevos (agregar a `verificar.py`; los 22 originales se mantienen)
| ID | Control |
|---|---|
| N1 | `clasico()` reproduce los dorados de §14.1 (semillas 1 y 2 + 4 escenarios × 4 réplicas) |
| N2 | **Conservación por grupo y motivo:** llegadas = atendidos + Σ perdidos(motivo) + migrados no atendidos + los que quedaron adentro |
| N3 | **Conservación de combustible por producto** (litros por tanque; **m³ del GNC** = Σ cargas) · ningún tanque negativo ni sobre capacidad |
| N4 | **Ley de Little** por grupo (L = λ·W) |
| N5 | Simultáneos en servicio en A/B ≤ playeros del turno y ≤ caras del grupo |
| N6 | Red: Luján→estación = 221,8 km / ≈190 min; con RN 143 cortada = 399,8 km (+178 km, +153 min); Dock Sud vía Alvear 991,3 km < vía Luján 1.279,0 km |
| N7 | Sin cortes (`p=0`) no hay pérdidas `corte_gnc`; con corte total sin migración, **todos** los GNC de la ventana se pierden |
| N8 | Con migración: `migrados + perdidos_corte = afectados` |
| N9 | La mezcla de productos y de vehículos simulada ≈ la configurada (diferencia < 1,5 pp con ≥ 30.000 llegadas) |
| N10 | Media muestral de litros de un auto ≈ **23,5 L** (±2 %); de un pick-up ≈ 40 L |
| N11 | Monotonía: el plazo medio con cortes ≥ sin cortes · más playeros ⇒ menos espera · más demanda ⇒ más espera |
| N12 | Estaciones: duplicar `factor_demanda` empeora la espera; el invierno con cortes de GNC tiene más `migrados` que el verano |
| N13 | *(opcional)* **M/M/c**: con servicio exponencial, λ constante y sin abandono, Lq/Wq/ρ ≈ Erlang C (cierra el pendiente de `TASK.md` Fase 5) |
| N14 | **Cero huérfanos:** todo campo numérico de `ParametrosSimulacion` y sus componentes tiene un `Dato` en el Registro |
| N15 | **Tema:** ningún hex de color fuera de `ui/tema.py` (`grep`); contraste WCAG ≥ 4,5:1 en los pares texto/fondo declarados; los 5 colores de `PRODUCTO` son distinguibles entre sí |

### 10.3 Color
Implementar `contraste(hex1, hex2)` (luminancia relativa WCAG) en `ui/tema.py` o en `verificar.py`. Pares a verificar: `TINTA/AMARILLO`, `TINTA/FONDO`, `TINTA/FONDO_PANEL`, `AMARILLO/ASFALTO`, `FONDO/ROJO` (texto blanco sobre botón rojo). Si hay una skill de visualización de datos disponible (`dataviz`), usarla para validar la paleta categórica.

### 10.4 QA visual (no alcanza con "corre")
Con Playwright/Chromium (en el entorno cloud está en `/opt/pw-browsers/chromium`; **no** ejecutar `playwright install`):
1. Levantar `python -m streamlit run app.py --server.headless true --server.port 8501`.
2. Capturar cada pestaña principal (y sub-pestaña) a 1440×900 y a 390×844 (móvil), y la **animación** en 3 instantes (madrugada, pico de la mañana, corte de GNC).
3. Revisar a ojo: paleta Shell coherente, sin texto amarillo sobre blanco, sin desbordes, insignias presentes, sin errores en la consola del navegador ni en el log de Streamlit.
Adjuntar las capturas al reporte. Si el entorno no permite navegador, decirlo explícitamente en el reporte (no declarar "verificado visualmente").

### 10.5 Rendimiento
Réplica ≤ 1,5 s · barrido por producto detrás de botón con estimación de tiempo visible · todo con `st.cache_data` · **no multiprocessing**. Si hay que acelerar: bajar días/réplicas, no meter paralelismo.

---

## 11. Trampas conocidas (heredadas y nuevas)

1. **`st.html` descarta el SVG** → usar `st.components.v1.html` (iframe).
2. Dos `$` en la misma línea de Markdown se leen como LaTeX → **`escapar_pesos`** en todo texto con importes.
3. No se puede escribir en `st.session_state` de un widget ya creado → patrón `politica_sugerida` en `leer_parametros()` (aplicar **antes** de crear los controles). Si se agregan más "usar esta sugerencia", repetir el patrón.
4. La conclusión se arma **antes** de las pestañas → tras el barrido (o la sensibilidad) hay que `st.rerun()`.
5. Si cambia la **firma** de un módulo hay que **reiniciar el servidor** (Streamlit recarga el script principal pero conserva el módulo importado viejo). Mantener `fileWatcherType = "poll"`.
6. **Orden de los streams:** sólo agregar al final de `STREAMS`. No reutilizar un stream para dos fuentes de azar (rompe los números aleatorios comunes).
7. **Atributos sorteados al llegar**, no al atender. El cliente migrado conserva su identidad (mismo auto).
8. **Combustible se descuenta al empezar a cargar** (no al terminar), por producto.
9. `st.cache_data` con parámetros: usar dataclasses con **tuplas** (hashables y comparables); un `dict` mutable dentro de `ParametrosSimulacion` rompe la comparación `p != p_corrida` de `app.py`.
10. **Litros ≠ m³:** nunca sumar; el GNC tiene su propia unidad en tarjetas, ejes y tablas.
11. El **JSON de la animación** crece con productos/grupos: usar columnar y `round()`; vigilar el peso (< ~3 MB).
12. **Calentamiento:** con 4 tanques y plazo de 36 h, 1 día **no alcanza** para salir del transitorio; recomendar y fijar **2–3 días** de calentamiento por defecto cuando los tanques arrancan llenos.
13. **Playeros + cajas por turno:** al cambiar de turno no se "expulsa" a quien está en servicio; la capacidad se ajusta cuando se libera (efecto realista, pero verificarlo en N5).
14. **Fechas:** usar siempre la fecha **de la nota original** (los buscadores rotulan mal). Precios: fijar y mostrar la **fecha de valuación**.
15. **Rojo de marca = rojo de pérdida:** ver §8.1 regla 2. Es el error de diseño más fácil de cometer acá.

---

## 12. Lo que NO se puede resolver desde el código: relevamiento y datos faltantes

El código **no puede inventar** estos datos; la app debe tener lugar para cargarlos (§8.4) y avisar mientras falten:

| Prioridad | Falta | Cómo se obtiene | Dónde entra |
|---|---|---|---|
| 1 | **Demanda real** (autos por franja de 15 min, hábil vs. fin de semana; autos/día; litros/mes por producto) | **Relevamiento en la estación** (contar vehículos por tipo y producto, 3 franjas, un día hábil y uno de fin de semana) + encargado; datos abiertos de la SE (ventas por provincia) | `DEM-01..03`, `DEM-06` |
| 2 | **Litros por carga y tiempos de servicio** reales (por producto y tipo) | Cronometrar en el lugar | `VEH-*`, `TIE-*` |
| 3 | **Abastecimiento real**: de dónde sale, cada cuánto viene, cuántos litros, plazo, tamaño de cada tanque subterráneo | Preguntar al **encargado** (con permiso) | `INV-01..05` |
| 4 | **GNC en invierno**: frecuencia/horario de cortes, compresores, tiempo de carga, migración a nafta | Encargado, AMENA, Ecogas, notas | `GNC-*`, `SUR-06` |
| 5 | **Personal**: dotación por turno, convenio y escala salarial | Encargado, convenio vigente | `PER-*`, `ECO-06` |
| 6 | **Estacionalidad** (índice mensual de ventas, turismo, temperatura) | SE, DEIE Mendoza, turismo San Rafael, SMN | `DEM-06`, `EstacionDelAnio` |
| 7 | **Economía**: márgenes, flete, precios vigentes de octubre-2026 | CECHA/FECRA, transportistas, SE | `ECO-*` |
| 8 | Confirmar: V3 (S3), V5 (diésel premium), V9/V10 (shop 24 h, cajas) | Ver la estación | §6 |

Faltan además las notas de investigación `02`, `04`, `05` (y quizá `07+`): la carpeta sólo tiene `01`, `03` y `06`. **No asumir su contenido.** Cuando lleguen, **actualizar el Registro** (reemplazar `heredado/supuesto` por `dato` con fuente) y re-correr sensibilidad.

---

## 13. Formato de reporte al cerrar cada fase

```
FASE N — <título>            [CERRADA | BLOQUEADA]
Archivos tocados: ...
Compuerta:  verificar.py → X/Y OK · N1 dorados → OK/FALLA · N14/N15 → ...
Visual:     capturas adjuntas: <lista>  (o: "sin navegador disponible")
Defaults usados de §6: V.., N..   (cada uno detrás de qué parámetro)
Supuestos NUEVOS agregados al Registro: ID — valor — por qué
Decisiones que necesitan al usuario: ...
Riesgos / deuda: ...
Commit: <hash> en claude/simulator-graphic-orchestrator-wu2xh4
```

---

## 14. Apéndices

### 14.1 Números dorados del motor actual (medidos el 5/10/2026 con `ParametrosSimulacion()` por defecto)
Reproducir con:
```python
from sim.config import ParametrosSimulacion
from sim.runner import correr_replica, correr_escenarios
p = ParametrosSimulacion()
for s in (1, 2): r, _ = correr_replica(p, semilla=s)          # imprimir los campos de abajo
res = correr_escenarios(p, replicas=4, semilla_base=1)
```
| Campo (réplica) | semilla 1 | semilla 2 |
|---|---|---|
| `espera_surtidor` | 1.391928 | 1.237307 |
| `espera_pico` | 3.609402 | 3.192477 |
| `cola_surtidor` | 0.372363 | 0.314959 |
| `util_surtidores` | 0.435195 | 0.427934 |
| `atendidos_dia` | 350.896552 | 345.793103 |
| `perdidos_cola_dia` | 4.758621 | 2.482759 |
| `perdidos_sin_combustible_dia` | 12.482759 | 14.206897 |
| `litros_vendidos_dia` | 12333.565057 | 12058.172473 |
| `nivel_servicio` | 0.953355 | 0.953909 |
| `pedidos_dia` | 0.62069 | 0.62069 |
| `compras_dia` | 104.689655 | 104.689655 |
| `hora_pico` | 19 | 19 |

Escenarios (4 réplicas, semilla base 1): `espera_pico` / `atendidos_dia` / `litros_vendidos_dia` →
Base **3.249536 / 346.465517 / 12140.09** · A **0.844787 / 348.327586 / 12207.652** · B (= Base en surtidores: números aleatorios comunes) **3.249536 / 346.465517 / 12140.09** · C (= A) **0.844787 / 348.327586 / 12207.652**.
Analíticos: `rho_pico` = 0,8761 · `rho_pico_dia_malo` = 1,0708 · `rho_cajas` = 0,5175 · 360 autos/día · 12.600 L/día · cobertura del punto de pedido 22,86 h.
*Observación útil para la narrativa:* el modelo hipotético **ya** pierde ≈ 12–14 autos/día por falta de combustible (con plazo 8–36 h y s = 12.000 L); con el plazo real de 24–48 h el quiebre será peor si no se corrige la política: es una de las conclusiones que el simulador nuevo debe poder mostrar.

### 14.2 Perfil horario heredado (`PERFIL_TIPICO`, factores relativos; **sin fuente**)
`00:0,30 · 01:0,20 · 02:0,15 · 03:0,15 · 04:0,25 · 05:0,60 · 06:1,10 · 07:1,80 · 08:2,00 · 09:1,50 · 10:1,10 · 11:1,00 · 12:1,20 · 13:1,10 · 14:0,90 · 15:0,90 · 16:1,00 · 17:1,40 · 18:1,90 · 19:2,00 · 20:1,60 · 21:1,10 · 22:0,70 · 23:0,40`
Tabla de demanda heredada: `280/320/360/400/440` autos con frecuencias `10/20/40/20/10`.

### 14.3 Fuentes principales (todas consultadas el 5/10/2026; detalle y URLs en las notas)
- Shell, localizador oficial (API geoapp, id 10129175) · Secretaría de Energía, Precios en surtidor Res. 314/2016 (CKAN) · OpenStreetMap (nodo 3497437279; sólo orientativo).
- Sitio Andino 27-oct-2023 (plazo 36 h, 27.000 L, Dock Sud) · Los Andes 31-jul-2023 · Sitio Andino 23/6/2022 (corte de GNC) · MDZ/El Sol/Los Andes 17-ago-2026 y Los Andes/Sitio Andino 1–2-jul-2026 (cortes por nieve) · Sitio Andino 27-jun-2026 (obra RN 143) · Sitio Andino 6-may-2026 (precios Mendoza).
- El Economista 7-abr-2026 y Infonegocios 8-abr-2026 (flota nacional/provincial) · Autocosmos (tanques) · Ley 24.449 art. 51 · OSRM/OSM (distancias).
- Material de la cátedra: TP 5 de redes (flujo máximo, camino más corto, árbol de expansión mínima, transbordo), TP de Monte Carlo, apuntes de colas.
- Paleta: [brandpalettes.com](https://brandpalettes.com/shell-logo-colors/) y otras (los hex difieren entre fuentes; ver §8.1).

*Fin del orquestador. Si algo de acá no se puede cumplir, no lo recortes en silencio: dejalo escrito en el reporte de la fase.*
