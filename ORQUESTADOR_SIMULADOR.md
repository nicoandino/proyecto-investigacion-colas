# ORQUESTADOR v2 — Simulador de la Shell de San Rafael (de hipotético a caso real)

> **Para quién es este archivo:** un agente de código que arranca en frío. Leelo **entero** antes de tocar nada. Es la fuente de verdad del trabajo **gráfico y práctico** que falta. **Si este archivo contradice a `CLAUDE.md`, `TASK.md`, `FASE2_IMPLEMENTACION.md`, `DATOS_OPERACIONALES_…md` o `ONBOARDING_PARA_AGENTES.md`, gana este archivo** (los otros tienen errores documentados en §3 y §4).
>
> **Versión:** v2.0 · **Fecha:** 5/10/2026 · **Reemplaza a:** v1.0 (escrita antes de que existieran los datos operacionales y el código de "Fase 2").
> **Compañero:** `ONBOARDING_PARA_AGENTES.md` (lectura rápida de 5 min; este archivo es la especificación completa).
>
> **Mensaje de arranque sugerido para pegarle al agente:**
> *"Leé `ONBOARDING_PARA_AGENTES.md` y después `ORQUESTADOR_SIMULADOR.md` completo. Ejecutá la Fase 0 (corregir el código de Fase 2) y la Fase 1 (registro de datos + tema Shell). Pasá sus compuertas y reportame con el formato de §13. No avances a la Fase 2 sin mi OK."*

---

## 0. Protocolo del agente

1. **Orden de lectura** (≈ 30 min): `ONBOARDING_PARA_AGENTES.md` → este archivo → `CASO_SHELL_SAN_RAFAEL.md` → `DATOS_OPERACIONALES_ESTACION_SHELL_SAN_RAFAEL.md` → `research_notes/…/{01,03,06}_*.md` (consultarlas **por parámetro**; §5 dice dónde está cada dato) → `sim/config.py` → `sim/modelo.py` → `app.py` → `ui/*` → `verificar.py`.
2. **Fases con compuertas (§9).** No se abre la fase siguiente con la compuerta en rojo. **Un commit por fase**, en castellano. Pushear a la rama de trabajo. **No crear Pull Request** salvo que el usuario lo pida.
3. **Nunca inventes un número en silencio.** Todo valor entra por el **Registro de datos** (§5.1) con `tipo`, `fuente` y `confianza`. Sin dato ⇒ `SUPUESTO` visible en la interfaz.
4. **Tres clases de afirmación**, siempre distinguidas: *dato* (tiene fuente), *supuesto* (sin fuente, marcado) y *propuesta del orquestador* (decisión de diseño reversible; columna "Origen" de §5).
5. **Una cifra con etiqueta "Alta" en un documento NO es alta por eso.** Los documentos nuevos (`DATOS_OPERACIONALES…`, `ONBOARDING…`) fueron compilados por agentes en paralelo y **sobreestiman la confianza** (§4). Aplicá la jerarquía de evidencia de §4.1.
6. **Si una decisión abierta (§6) te bloquea**, usá el **default**, dejalo detrás de un parámetro y anotalo en el reporte. Preguntale al usuario sólo si no hay default.
7. **Reportá con el formato de §13** al cerrar cada fase.

### 0.1 Estado del repositorio (verificado el 5/10/2026)
| Rama | Contenido |
|---|---|
| `main` | Proyecto hipotético original (b83b4db): estación genérica, 22 controles. |
| `main-7ss6h3` | **Fase 2** (f41adb6): `DATOS_OPERACIONALES…`, `FASE2_IMPLEMENTACION.md`, modo "determinista" (`config.py`, `distribuciones.py`, `modelo.py`, `app.py`) + `ONBOARDING_PARA_AGENTES.md` (08250f0). |
| `claude/simulator-graphic-orchestrator-wu2xh4` | **Rama de trabajo.** Es `main` + **merge de `main-7ss6h3`** + este orquestador. Es la que hay que usar. |

Sobre el código mergeado: `python verificar.py` → **22/22 OK**; `py_compile` OK; la app levanta (`/_stcore/health` = 200); con `modo_determinista=False` (default) los números son **idénticos** a los del proyecto original (§14.1). **El problema no es que "no ande": es que el modo nuevo es numéricamente incorrecto (§3).**

---

## 1. Misión y definición de "terminado"

**Misión.** Pasar de un simulador *hipotético* a **la herramienta del caso real**: la estación **Shell de Av. Balloffet 1810 esq. Av. Los Sauces, San Rafael, Mendoza** (LOS SAUCES S.R.L.). El producto central del TP es un **informe del caso**; el simulador ilustra escenarios. Tiene que ser **completo, defendible y mostrar cada dato con su fuente y su confianza**, con la **paleta Shell**.

| # | Criterio verificable (todos deben cumplirse) |
|---|---|
| D0 | **El modo de demanda por litros mensuales es numéricamente correcto**: con `demanda_mensual = 270.000 L`, el motor simula **270.000 L/mes ± 3 %** (control N16). Hoy simula ≈ 9,4 millones (§3-B1). |
| D1 | La estación tiene **12 caras en 3 grupos** (A nafta 4 · B diésel 2 · C GNC 6), minimarket y **playeros por turno**; servidores = *mín(caras libres, playeros en turno)* en nafta/diésel. |
| D2 | **Cinco productos** (Súper, V-Power, Diésel G2, Diésel G3/V-Power Diesel, GNC). Líquidos con **tanque propio**; GNC sin tanque (**disponibilidad** + capacidad de compresores). |
| D3 | **Red de abastecimiento** con camino más corto, cortes de ruta y su efecto en plazo y quiebre. |
| D4 | **Corte de GNC en invierno** (corte **total** por episodios, no "−50 %") con **migración** a nafta. |
| D5 | **Calendario real**: el horizonte (día/semana/mes/estación/año) simula **meses concretos**, con estacionalidad **elegible** (§5-C). |
| D6 | **Cada parámetro** se muestra con valor, unidad, fuente, nivel, tipo y confianza, **con las alternativas en conflicto**, y se exporta a CSV. Cero parámetros huérfanos (N14). |
| D7 | **Paleta Shell** coherente en Streamlit, Plotly y animación, con contraste legible (N15). |
| D8 | **Animación** del playón real: 3 zonas, 12 posiciones, playeros, cola que desborda a la avenida, minimarket, **tanques por producto**, camión en ruta, estado del GNC. |
| D9 | **Sensibilidad** (tornado) sobre todos los `supuesto`/`heredado`/`estimacion`, **incluyendo cada contradicción de §4** como eje. |
| D10 | `verificar.py`: los **22 controles originales + los de §10.2**; el **caso degenerado** reproduce los números dorados de §14.1. |
| D11 | `CLAUDE.md`, `TASK.md`, `README.md` y los documentos de Fase 2 **corregidos** (Fase 10). |

---

## 2. Contexto condensado

### 2.1 Qué pasó
El profesor objetó la **simulación hipotética** (datos inventados). Se pivotó a **un caso real comprobable**. Consigna: *"cualquier tema, que corra en algún software, con alguna complejidad, preferiblemente aspectos económicos. Colas, transporte, Montecarlo, etc."* Motor propio (no Simul8). Grupo **Andino–Assenza**. Materia: Investigación Operativa. Fase 2 (otro agente, 5/10/2026) consolidó datos operacionales y agregó el modo "determinista".

### 2.2 La estación (detalle en §5-A)
- **Dirección oficial (Shell):** "BALLOFFET 1810 ESQ. LOS SAUCES", San Rafael, CP 5600. Grafía correcta **Balloffet**. "Bayofet/Bayofed" **no existe** en ninguna fuente.
- **Surtidores (grupo, capturas de Google Maps):** 6 surtidores de doble cara = **12 caras**; S1–S2 nafta, S3 diésel, S4–S6 GNC; *una flecha = una cara = un carril* (6 + 6 flechas).
- **Servicio atendido por playero** (Shell API: `full_service` + `manned`), **playa 24 h** (Shell API: `twenty_four_hour`). Minimarket (Datos: "Shell Select", ≈ 140 m², **nombre y horario sin confirmar**).
- **Entorno:** Av. Balloffet = **RN 143** (tramo urbano, 4 carriles, 60 km/h); Av. Los Sauces = **RP 158**. Zona **urbana consolidada**.
- **Abastecimiento líquido:** camión cisterna; origen documentado **Dock Sud** (≈ 991 km vía Gral. Alvear; nivel C, 2023). **GNC:** red de gas + compresión; en invierno se corta por orden del ENARGAS a las estaciones con contrato **interrumpible**.

### 2.3 Qué se conserva y qué queda superado
| Se conserva | Queda superado |
|---|---|
| SimPy, streams RNG con semilla y **números aleatorios comunes**; colas FIFO; inventario (s, Q); economía; 22 controles; IC 95 %; **calentamiento** y **réplicas** | `CLAUDE.md` "NO hacer": **varios combustibles** y **fallas de equipos**; "un solo producto"; "una réplica = un mes genérico" |
| Monte Carlo de **5 pasos** (ahora también para **tipo de cliente** y **producto**, §7.2) | La tabla de demanda diaria y el perfil horario **inventados** (pasan a `heredado` visible o se reemplazan por los de §5-C) |
| `sim/` sin Streamlit, castellano, `frozen=True`, sin `print()` en `sim/` | **Las afirmaciones de Fase 2** de §3-B6 ("no se necesitan réplicas", "calentamiento innecesario", "datos únicamente de fuentes verificadas") |

**Siguen prohibidos** (no escalable a propósito): base de datos, autenticación, API REST, Docker, plugins, abstracciones "para el futuro", **multiprocessing**, lavadero, camiones como clientes masivos, horas extra/ausentismo.

---

## 3. Auditoría del código de Fase 2 (hay que corregirlo **primero**)

Evidencia reproducible con `python` sobre la rama de trabajo. Resumen: el modo "determinista" de `main-7ss6h3` **mezcla litros con autos**, **siempre simula enero** y **no es determinista**.

| ID | Defecto | Evidencia | Corrección (Fase 0) |
|---|---|---|---|
| **B1** | **Error de unidades.** `autos_por_dia = demanda_base_mensual / 30` divide **litros por mes** y lo trata como **autos por día**. | `modo_determinista=True, demanda_base_mensual=120.000` ⇒ `autos_por_dia = 4.000`, `litros_por_dia = 140.000`, ⇒ **4,2 M L/mes** (35× lo pedido); ρ_pico = **9,7**. Con 270.000 ⇒ 9.000 autos/día, **9,45 M L/mes**, ρ_pico = **21,9**; una corrida de 3 días da `perdidos_cola/día = 6.931` y `sin_combustible/día = 3.204`. El propio ejemplo de `FASE2_IMPLEMENTACION.md` ("120.000 L ⇒ 4.000 autos") **está mal**. | `autos_por_dia = (demanda_mensual_L / días_del_mes) / litros_medios_por_cliente` (§7.1). Correcto: 270.000 L/mes ⇒ 9.000 L/día ⇒ **≈ 252 clientes líquidos/día** (§14.2). |
| **B2** | **Un "mes" siempre es enero.** `mes = ((dia_del_anio-1)//30)+1` recibe `dia` = 1..`dias` (contado desde el inicio de la corrida, no del calendario). | Para `dias=1..30` hay **un solo valor** de demanda (índice enero = 100). "Estación (90)" = ene–mar. Invierno **nunca** se simula salvo con "año". | Parámetro `fecha_inicio` (mes y día); mapear día→mes con calendario real (§7.1). |
| **B3** | **La tabla de estacionalidad del código no coincide con su fuente.** | Código: Mar 70, Abr 75, May 80, Ago 90, Sep 95, Oct 92, Nov 98, Dic 105 (media 83,75). `DATOS_OPERACIONALES §6`: Mar 80, Abr 65, May 60, Ago 75, Sep 70, Oct 70, Nov 75, Dic 85 (media 73,3). Además es un **proxy de ocupación hotelera** (rango 55–100, ×1,8), mientras `ONBOARDING` dice "~6 % máximo (insignificante)". | Tres presets elegibles y **neutro por defecto** (§5-C, DEM-06). |
| **B4** | **"Determinista" es un nombre engañoso.** Sólo el **total diario** es fijo: las llegadas siguen siendo Poisson y los tiempos de servicio aleatorios. | `FASE2` y `CLAUDE.md` afirman "no se necesitan réplicas" y "calentamiento innecesario": **falso**. El tanque arranca al 75 %, las colas vacías y los tiempos son aleatorios ⇒ hay transitorio y varianza. Y con `dias_calentamiento = 0` el transitorio **contamina** los indicadores. | Renombrar a **"demanda esperada"**; **mantener réplicas e IC**; calentamiento por defecto **2 días** en ambos modos. |
| **B5** | **`horizonte` no hace nada en el motor.** `_dias_segun_horizonte()` **nunca se llama**; el campo `horizonte` sólo viaja a `ParametrosSimulacion`; la UI calcula los días por su cuenta. `Estacionalidad` se importa en `app.py` y no se usa. | `grep` (§0.1). | Que `dias` y `fecha_inicio` salgan de **una sola** función `horizonte → (fecha_inicio, dias)`. |
| **B6** | **Documentos con afirmaciones falsas o engañosas.** | (i) `FASE2`: "no se necesitan réplicas", "calentamiento innecesario"; (ii) `CLAUDE.md`: "Datos únicamente de fuentes verificadas", "la fórmula es exacta"; (iii) `ONBOARDING`: manda cambiar la demanda a "**~9.000 autos/día = 270k L/mes**" (**son 9.000 L/día**, no autos) y describe un widget `playeros` y un "21 personas" que no existen en el código ni en la fuente (§4-C5). | Corregir los tres (Fase 10). **Hasta entonces llevan un aviso en la primera línea.** |
| **B7** | **Rendimiento del horizonte "año".** 365 días ≈ 12 × una réplica de un mes (≈ 6 s) **por réplica y por escenario**. | — | Año = **una corrida por escenario** (más réplicas sólo si el usuario las pide); cacheada y detrás de botón. |

---

## 4. Contradicciones entre fuentes y cómo se resuelven

### 4.1 Jerarquía de evidencia (aplicar siempre, en este orden)
1. **Observación propia en la estación** (relevamiento con fecha, hora y método).
2. **Registro primario** de la estación u organismo oficial **abierto en el original** (API de Shell, Secretaría de Energía).
3. **Prensa/organismos abiertos en el original** `[OK-orig]` con fecha de la nota.
4. **Agregados nacionales o proxies** (flota, mercado, ocupación hotelera).
5. **Resúmenes de buscador `[RESUMEN]`**, cifras **sin URL** o "confirmadas" por un documento compilado sin enlace.
6. **Supuesto del orquestador.**

**Reglas:** (a) gana el nivel más alto; (b) a igual nivel, gana el que **declara fuente**; (c) el valor perdedor **no se descarta**: queda como **alternativa** en el Registro y como **eje de sensibilidad**; (d) un conflicto que cambia un resultado ≥ 20 % se marca **🔴 relevar** (§12).

### 4.2 Registro de contradicciones
| ID | Tema | Fuentes en conflicto | **Valor adoptado** (y por qué) | Alternativas (sensibilidad) | Impacto |
|---|---|---|---|---|---|
| **C1** | **Horario** | Shell API: playa `twenty_four_hour` (nivel 2, leído el 5/10/2026; **hoy el proxy bloqueó una re-lectura**). `DATOS §5`: "06–22, NO 24 h" (patrón típico, **sin fuente**, "verificar"). El mismo `DATOS` lista turno noche 22–06 con personal; `ONBOARDING`: "21 personas en 3 turnos de 24 h". | **24 h** (fuente primaria + los propios turnos de ambos documentos). | **S10: cierre nocturno 22–06.** El perfil horario de `DATOS §2` ya asigna demanda a la madrugada (factor 1,0). | 🔴 Medio |
| **C2** | **Demanda mensual** | `ONBOARDING`: "270k L/mes **confirmado** (CREEBBA + Surtidores.com.ar), rango 260–280k" — **sin URL; no pude confirmarlo**. `DATOS §1`: base **100–150k** ("SUPUESTO"). Código: 120k. Hipotético heredado: 360 autos × 35 L ≈ 378k. `DATOS §1`: Shell país 600k L/estación/mes; promedio nacional 270–380k. Nota 03 D5: 330 m³ por boca (2018, baja); "≈ 270.000 L/mes" en un resumen de informe regional (sin fecha). Búsqueda web: punto de equilibrio de una estación ≈ 315.000–400.000 L/mes (2021). | **270.000 L/mes** (central; **estimación, confianza baja-media**): es el valor donde convergen las fuentes débiles; el de 120k tiene sólo el argumento "San Rafael cayó 30 %". | **150.000 / 400.000 L/mes** (ejes de sensibilidad). | 🔴 **Alto** |
| **C3** | **Litros vs. autos** | `DATOS §1` ("100–150 k L/mes = 3.300–5.000 autos/día @ 50 L") y `ONBOARDING` ("~9.000 autos/día = 270k L/mes") confunden **litros/día** con **autos/día** (error ≈ ×35–50). Código: B1. | **Litros/mes es la variable de entrada; los autos se derivan** (÷ litros medios por cliente, §14.2). | — | 🔴 **Crítico** |
| **C4** | **Entrada al minimarket** | Heredado 30 % (sin fuente); `ONBOARDING`: **20 %** "dato directo YPF: 300k clientes/día × 20 %" (**no pude confirmarlo**; la búsqueda sólo halló otras cifras de YPF Full); `DATOS §5`: "30–50 % de los que cargan (estimado)"; el propio `ONBOARDING` da el rango 15 % (chica) a 30 % (Shell premium). | **20 %** (el único con fuente declarada, aunque débil). | **15 % / 30 % / 45 %** | Bajo-medio |
| **C5** | **Personal** | `ONBOARDING`: "**2–3 playeros por turno**, 21 personas, 1 encargado por turno". `DATOS §4`: mañana y tarde **5 personas = encargado 1 + playeros 2 + cajero 1 + tienda 1**; noche **2 = playero 1 + cajero 1**; total ≈ 12. (`DATOS §tabla` dice "5–6 *personas*", y `ONBOARDING` lo leyó como "5–6 *playeros*".) | **Playeros (noche, mañana, tarde) = 1 · 2 · 2**; **cajas = 1**; encargado y personal de tienda **sólo como costo**. Es el único desglose por rol. | Playeros **2·3·3** (`ONBOARDING`); autoservicio (S9, −1 por turno). | 🔴 **Alto** (con 2 playeros ρ_pico = 0,86) |
| **C6** | **Mix diésel G2/G3** | `ONBOARDING`: **75 % / 25 %** (tendencias −12,47 % / +11,52 %). `DATOS §7`: G2 24 %, G3 19 % del mercado (= **55 % / 45 %** del diésel; −11,22 % / +8,52 %). Nota 01: la **SE declara ambos** productos para esta estación. `DATOS` también dice "S3 sólo G2 (verificar)". | **55 % / 45 %** (tabla con fuente declarada, Surtidores.com.ar ago-2026) y **ambos activos** (SE). | **75 / 25** y **100 / 0** (sólo G2). | Medio |
| **C7** | **Mezcla de producto** | `DATOS §7`: mercado nacional **por volumen** (Súper 23, V-Power 16, G2 24, G3 19, GNC 2–3). Flota nacional **por cantidad** (nafta 63,5 / diésel 25,5 / GNC 10,6; nota 03). | **Mezcla en LITROS** (`DATOS §7`, normalizada a los 4 líquidos: 28,0 / 19,5 / 29,3 / 23,2) y **GNC como 3 % de los clientes**. Las llegadas se derivan por producto (§14.2). | GNC **11 %** (parque GNC 11,2 %, ENARGAS); mezcla de flota. | Medio |
| **C8** | **GNC: 6 caras vs. 2–3 %** | La estación dedica **6 de 12 caras** al GNC; `DATOS` le asigna **2–3 %** del volumen. | Se modela como está, **y la app muestra una alerta de coherencia**: "6 caras para ≈ 3 % de los clientes: probable sobredimensionamiento o subestimación de la demanda GNC". | GNC 3 % / 11 % / 20 %. | 🔴 Medio |
| **C9** | **GNC en invierno** | `ONBOARDING`: "−50 % de oferta jun–ago, **Res. ENARGAS 409/2026**, 80 % de estaciones interrumpibles, compresor 20–25 autos/h" (**sin URL; no hallé la Resolución 409/2026**). `DATOS §7`: "cortes de **10–14 días** en jun/jul, caras GNC = 0". Nota 06/CASO: ventanas horarias 17–01 h y 09 h "hasta nuevo aviso" (San Rafael, 2022, 8 estaciones). **Verificado hoy:** ENARGAS ordenó (abril-2026, AMBA) **cortes de 24 h "hasta nuevo aviso"** a las estaciones con **contrato interrumpible**; las de contrato firme siguen. | **Corte TOTAL** (no −50 %), por **episodios**: 2 episodios × 6 días en jun–ago (≈ 12 días, `DATOS`), con **contrato interrumpible** por defecto. **No citar "Res. 409/2026".** Compresores = **3** (20–25 autos/h × 7 min ÷ 60 ≈ 2,6; **cifra sin fuente**). | Contrato **firme** (sin cortes); ventanas horarias (17–01, 09–24); **−50 %** como capacidad parcial; 0–60 % de migración. | Alto en invierno |
| **C10** | **Estacionalidad** | Código (tabla propia) ≠ `DATOS §6` ≠ `ONBOARDING` ("~6 %"). Todo proxy hotelero. | **Neutra (1,00)** por defecto + presets (B3). La ocupación hotelera **no** es ventas de combustible; la serie real está en la SE (§12). | Leve ±6 %; Proxy turístico (`DATOS §6`). | Medio |
| **C11** | **Tiempo de servicio** | `DATOS §3`: nafta/diésel **Triangular(2,5,8)** (3 papers UNLP/UTN/UNC, sin medir en San Rafael); GNC **(5,7,12)**; minimarket **(2,4,10)**. Nota 03: **(2,4 ; 3,7 ; 5,0)** (punto medio de dos refs. débiles) y GNC **10–30 min** `[RESUMEN]` (probablemente incluye espera); heredado minimarket (1,5 ; 3 ; 6). | `DATOS §3` (fuentes argentinas con URL). | Nota 03 (bajo para nafta; alto para GNC). | Medio |
| **C12** | **Litros por carga** | `DATOS §8`: autos 40–50 L, SUV 80, camión 120–500 L ("litros/carga promedio" ≈ tanque lleno, **sin fuente**). Nota 03: la gente carga **≈ 30 % del tanque**, llenar "es muy raro" (único anclaje empírico, 2020, baja). | **Regla de nota 03** (media = 0,5 × tanque; §5-D). | Preset **alto** (media 0,8·T, **casi lleno**, `DATOS`) y **bajo** (0,3·T). **Para los mismos litros cambia ×0,6 / ×1,7 la cantidad de clientes** (158 / 420 por día) y ρ_pico con 2 playeros pasa de 0,86 a 0,54 / 1,43. | 🔴 **Alto** |
| **C13** | **Tanques de vehículos** | `DATOS`: auto 50 L (**"Alta"**), camión 300 L ("Alta"). Nota 03: auto **47 L** (Autocosmos `OK-orig`; rango 42–52), camión **sin dato argentino**. | **47 L**; camión **300 L como supuesto** (la "Alta" no tiene fuente). | 42–52 L; camión 120–600 L. | Bajo |
| **C14** | **Servicios** | `DATOS §5`: lavado, Agroservice, cambio de aceite, Shell Select 140 m². Nota 01 (lista oficial Shell): sólo shop, baño, aire y agua; "no figura" lavadero ni ATM. | No se modela lavadero (fuera de alcance). Nombre del shop: **"Shell Select (nombre sin confirmar)"**. | — | Bajo |
| **C15** | **Autoservicio** | `DATOS §5`: permitido en Mendoza (Decreto 46/2025, Res. 147/2025; **no verificado por mí**). Shell API: `full_service` + `manned`. | **Servicio atendido.** | **S9 autoservicio**: −1 playero por turno. | Medio |
| **C16** | **Perfil horario** | `DATOS §2` (texto): madrugada = **1/40** del pico. `DATOS §2` (su propia tabla): madrugada **1,0** vs. pico **3,5** (= 1/3,5). Heredado: picos 08 y 19 con factor 2,0. | **La tabla de `DATOS §2`** (24 factores, §14.3); la afirmación "1/40" **no se usa** (la tabla la contradice y su fuente —ventas YPF por descuento nocturno— no es un perfil). | Perfil heredado. | Medio |
| **C17** | **Fin de semana / quincena** | `DATOS §2`: fin de semana **+24 % a +50 %** (tabla ×1,3–1,5); cambio de quincena **+100 %** 1–3 días/mes (fuente: limitación de camiones, débil). | Fin de semana **×1,30**, **normalizado** para conservar los litros del mes (§14.4). Quincena: **escenario S12**, no default. | ×1,24 – ×1,50. | Bajo-medio |
| **C18** | **Salarios** | Heredado: $900.000. `DATOS §4`: playero **$1.545.472** básico (≈ $1.680.000 con adicionales), cajero $1.666.391 (≈ $1.800.000), encargado $1.600.406; fuente "FECRA oct-2026" pero **la URL dice "enero-2026"**. | **Costos totales estimados** ($1.680.000 / $1.800.000 / $1.740.000), confianza **media**; **vigencia a verificar**. | Básico sin adicionales. | Medio |
| **C19** | **Precios** | `DATOS §7` (sept-2026): Súper $2.141, Premium $2.300+, G2 $2.116, **G3 $2.641**, GNC $699/m³ (**oct-2025**). Nota 01 (Mendoza, 6/5/2026): Súper $2.099, V-Power $2.399, **V-Power Diesel $2.411**. SE de la propia estación: **congelados** (2025). | Para **referencia** usar `DATOS §7` (más reciente). **El modelo usa márgenes, no precios.** | — | Informativo |
| **C20** | **Otros** | Mercuria: nota 01 "jun-2026, cierre pendiente" vs. `DATOS §5` "1/9/2026, Mercuria 60 % / Manzano 20 % / Edenor 20 %". Estaciones en San Rafael: 15 (OSM), 16 (SE), 20 (`DATOS`). Tránsito RN 143/144 "4.000–5.000 veh/día" (`DATOS`, sin fuente) vs. TMDA (tramo urbano **sin cifra**). Temperatura jul: mín media **2,3 °C** (`DATOS`) vs. "−2 °C" (`ONBOARDING`): no son contradictorios (media vs. extremo). | Registrar y mostrar; **ninguno entra al modelo**. | — | Nulo |

---

## 5. Los datos (valores adoptados)

### 5.1 Registro de datos (contrato — Fase 1)
Crear `sim/datos.py`:

```python
@dataclass(frozen=True)
class Dato:
    id: str                       # "DEM-01"
    nombre: str
    valor: object                 # lo que usa el modelo
    unidad: str
    bajo: float | None = None     # extremos de sensibilidad
    alto: float | None = None
    nivel: str = "?"              # A estación · B San Rafael · C Mendoza · D ciudad parecida · E Argentina/otro
    tipo: str = "supuesto"        # dato | estimacion | observacion | supuesto | heredado
    confianza: str = "baja"       # alta | media | baja | sin_dato
    fuente: str = ""; url: str = ""; fecha_fuente: str = ""
    nota: str = ""
    origen: str = "investigacion" # investigacion | grupo | datos_operacionales | orquestador | heredado
    conflicto: str = ""           # id de §4.2 (p. ej. "C2")
    alternativas: tuple = ()      # ((nombre, valor, fuente), ...) los valores que perdieron
```
Reglas: (a) `REGISTRO` + `por_id()` + `valor()`; (b) **todos los defaults de `config.py` salen del Registro**; (c) `tipo="heredado"` = placeholder visible sin fuente; (d) `con_valor(id, nuevo)` crea una copia con `tipo="observacion"` (relevamiento propio); (e) N14 falla si un campo de los parámetros no tiene `Dato`. Hay un **borrador** de este módulo del v1 descartado (valores de §5 v1); **no reutilizarlo sin reconciliarlo con esta sección**.

### 5.2 Tabla maestra
Leyenda **Origen**: `INV` = notas 01/03/06 · `DO` = `DATOS_OPERACIONALES` · `ONB` = `ONBOARDING` · `GRP` = grupo · `ORQ` = orquestador · `HER` = heredado. Todas las fuentes se consultaron el 5/10/2026; usar la **fecha de la nota original**, no la del buscador.

#### A. Estación (informativos; no alimentan el modelo)
| ID | Dato | Valor | Nivel | Tipo | Conf. | Origen / fuente |
|---|---|---|---|---|---|---|
| EST-01 | Dirección | Balloffet 1810 esq. Los Sauces, San Rafael, CP 5600 | A | dato | A | INV · Shell API + SE |
| EST-02 | Operador / CUIT | LOS SAUCES S.R.L. / 30-67218048-8 | A | dato | A | INV · Shell, SE, OSM |
| EST-03 | Bandera | Shell (SHELL C.A.P.S.A., id 674) | A | dato | A | INV · SE |
| EST-04 | Coordenadas | −34,62833 ; −68,35832 | A | dato | A | INV |
| EST-05 | Horario de la playa | **24 h** (C1) | A | dato | A | INV · Shell API `twenty_four_hour` |
| EST-06 | Horario del minimarket | 24 h **sin confirmar** (Shell: `unknown`; `DO`: 06–22) | A | supuesto | B | GRP / DO · V10 |
| EST-07 | Servicios | tienda ("Shell Select", ≈ 140 m², nombre sin confirmar), baño, aire y agua, servicio atendido, pago en surtidor/móvil, tarjeta de flota. `DO` suma lavado/Agroservice (**no figuran en la lista oficial**) | A | dato | M | INV + DO (C14) |
| EST-08 | Calzadas | Balloffet = RN 143; Los Sauces = RP 158 | A | dato | M | INV |
| EST-09 | Cercanía | otras Shell a 2,26 y 3,60 km; ninguna estación a < 1,5 km | B | dato | A | INV |
| EST-10 | Contexto corporativo | venta a Mercuria (jun-2026, cierre pendiente según nota 01; "1/9/2026" según `DO`) | E | dato | M | INV / DO (C20) |

#### B. Surtidores y personal
| ID | Dato | **Adoptado** | Alternativa | Nivel | Tipo | Conf. | Origen |
|---|---|---|---|---|---|---|---|
| SUR-01 | Caras por surtidor | 2 (6 surtidores = 12 caras) | — | A | dato | M | GRP |
| SUR-02 | Grupo A (nafta) | S1, S2 → 4 caras → Súper y V-Power | — | A | dato | M | GRP · V3 |
| SUR-03 | Grupo B (diésel) | S3 → 2 caras → **G2 y G3** | sólo G2 | A | dato | M | GRP + SE (C6) |
| SUR-04 | Grupo C (GNC) | S4–S6 → 6 caras | — | A | dato | M | GRP |
| SUR-05 | Vehículos por cara | 1 | — | A | supuesto | M | GRP |
| SUR-06 | Compresores GNC | **3** simultáneos (derivado de 20–25 autos/h × 7 min) | sin límite (6) · 2 | A | supuesto | sin dato | ONB (**sin fuente**) · C9 |
| PER-01 | Playeros por turno (noche 22–06 · mañana 06–14 · tarde 14–22) | **1 · 2 · 2** | 2·3·3 (ONB) | A | estimacion | B | DO §4 (C5) |
| PER-02 | Cajeros (cajas) por turno | 1 · 1 · 1 | — | A | estimacion | B | DO §4 |
| PER-03 | Encargado / personal de tienda | encargado 1 (M, T); tienda 1 (M, T) — **sólo costo** | — | A | estimacion | B | DO §4 |
| PER-04 | El GNC retiene playero | No (sólo conecta la manguera) | sí | A | supuesto | sin dato | ORQ |
| PER-05 | Capacidad de cola por grupo | 8 autos | 4 – 14 | A | supuesto | sin dato | ORQ (relevar) |
| PER-06 | Disciplina de cola | `por_grupo` (FIFO único) | `por_cara` | A | supuesto | sin dato | CASO §7 |

#### C. Demanda ★ (lo que más mueve el modelo)
| ID | Dato | **Adoptado** | Alternativas / rango | Tipo | Conf. | Origen · conflicto |
|---|---|---|---|---|---|---|
| DEM-01 | **Demanda mensual** | **270.000 L/mes** (≈ 9.000 L/día) | 150.000 · 400.000 | estimacion | B-M | ONB + INV/DO · **C2, C3** |
| DEM-02 | Perfil horario (24 factores) | `[1,1,1,1,1,1, 1,5, 3,5,3,5,3,5, 2,2, 1,5,1,5, 1,5,1,5, 3,3, 2,2, 1,5,1,5, 1,1]` (§14.3) | perfil heredado (08 y 19 h) | estimacion | B | DO §2 · C16 |
| DEM-03 | Fin de semana | **×1,30**, normalizado al mes (§14.4) | 1,24 – 1,50 | estimacion | M | DO §2 · C17 |
| DEM-04 | Mezcla de producto en **litros** (líquidos) | Súper **28,0** · V-Power **19,5** · G2 **29,3** · G3 **23,2** % | mix de flota; G2/G3 = 75/25 | estimacion | B | DO §7 · C6, C7 |
| DEM-05 | Clientes GNC (% de las llegadas) | **3 %** | 11 % · 20 % | estimacion | B | DO §7 · C8 |
| DEM-06 | Estacionalidad mensual (12 factores) | **Neutra** `1,00 × 12` | Leve ±6 % · Proxy turístico (Ene 100, Feb 60, Mar 80, Abr 65, May 60, **Jun 55**, Jul 85, Ago 75, Sep 70, Oct 70, Nov 75, Dic 85) | supuesto | sin dato | C10 |
| DEM-07 | Variabilidad día a día | modo "esperada" (fija) o **Monte Carlo** con factores relativos `(0,78 · 0,89 · 1,00 · 1,11 · 1,22)` y frecuencias `(10·20·40·20·10)` | — | heredado | sin dato | HER (la tabla original, **reescalada a relativa**) |
| DEM-08 | **Entrada al minimarket** | **20 %** | 15 · 30 · 45 | estimacion | B | ONB · C4 |
| DEM-09 | Eventos (opcionales) | Vendimia 17–26 ene **+30–50 %** · Las Leñas (jun-ago) **+30 %** de paso por RN 143 · Carnaval **+40 %** · vacaciones de invierno 9–20 jul | — | dato | B | DO §6 |
| DEM-10 | Cierre de ruta y demanda | al cerrarse la RN 143 la demanda **externa baja**; en el pre-cierre (1–2 días) **sube** | — | supuesto | sin dato | DO §6 (cuantificación = **escenario**, no default) |

#### D. Vehículos y litros por carga (nota 03 §1C–1D; sin cambios respecto de v1)
Regla (verificada algebraicamente): litros de una carga ~ `Triangular(0,20·T ; 0,30·T ; 1,00·T)`; moda 0,30·T (único anclaje: nota 03 D1, ≈ 30 % del tanque), máx 1,00·T (límite físico), **media exacta 0,50·T**. Sensibilidad = **tres presets de la distribución** (no escalar por un factor: con el tope en T, escalar 1,6× daría media 0,6·T, no 0,8·T): **bajo** `(0,10 ; 0,20 ; 0,60)·T` → media 0,30·T (nota 03, escenario bajo) · **base** `(0,20 ; 0,30 ; 1,00)·T` → 0,50·T · **alto** `(0,50 ; 0,90 ; 1,00)·T` → 0,80·T (≈ la "carga casi llena" de `DO §8`, C12).

| ID | Tipo | Tanque T | Litros/carga (mín · moda · máx) → media | Fuente · conf. |
|---|---|---|---|---|
| VEH-01 | Auto | **47 L** (42–52) | 9,4 · 14,1 · 47 → **23,5** | INV D16 (Autocosmos `OK-orig`) · M |
| VEH-02 | Pick-up / utilitario | **80 L** | 16 · 24 · 80 → **40** | INV D18 (`RESUMEN`) · M-B |
| VEH-03 | Moto 110 cc | **3,7 L** (3,5–4,1) | 0,74 · 1,11 · 3,7 → **1,85** | INV D19 (`RESUMEN`) · M-B |
| VEH-04 | Camión / ómnibus | **300 L** (**supuesto**; 120–600) | 60 · 90 · 300 → **150** | ORQ / DO · sin dato (C13) |
| VEH-05 | Auto GNC | cilindro **14 m³** | 2,8 · 4,2 · 14 → **7 m³** | INV §2.10 (`RESUMEN`) · B |

**Tipo de vehículo por producto** (diseño **"producto primero"**, §7.2): *supuestos* ORQ, sin fuente.
| Producto | moto | auto | pick-up | camión/ómnibus | Carga media del producto |
|---|---|---|---|---|---|
| Súper | 12 % | 85 % | 3 % | — | 21,4 L |
| V-Power | — | 85 % | 15 % | — | 26,0 L |
| Diésel G2 | — | 20 % | 55 % | 25 % | 64,2 L |
| Diésel G3 | — | 15 % | 45 % | 40 % | 81,5 L |
| GNC | — | 100 % | — | — | 7 m³ |

#### E. Tiempos de servicio (C11)
| ID | Dato | **Adoptado** | Alternativa (nota 03) | Tipo · conf. | Origen |
|---|---|---|---|---|---|
| TIE-01 | Caudal | 40 L/min (90–120 alto caudal) | — | dato · B | INV D22/D23 (Paraguay 2012) |
| TIE-02 | Nafta y diésel (por vehículo en la cara) | **Triangular(2 ; 5 ; 8) min** | (2,4 ; 3,7 ; 5,0) | supuesto · M | DO §3 (UNLP/UTN/UNC, sin medición local) |
| TIE-03 | Extra de camión/ómnibus | `+ litros ÷ 90` min | — | supuesto · B | ORQ |
| TIE-04 | GNC | **Triangular(5 ; 7 ; 12) min** | (10 ; 15 ; 30) | supuesto · M-B | DO §3 |
| TIE-05 | Compra en el minimarket | **Triangular(2 ; 4 ; 10) min** | (1,5 ; 3 ; 6) heredado | supuesto · B | DO §3 |
| TIE-06 | Paciencia (cola de cara / caja) | 10 / 8 min | 5 – 20 | heredado · sin dato | HER |

#### F. Abastecimiento (nota 06; sin cambios)
| ID | Dato | Valor | Tipo · conf. | Fuente |
|---|---|---|---|---|
| INV-01 | Plazo pedido→entrega | **Triangular(24 ; 36 ; 48) h** (reemplaza `Triangular(8,16,36)` h) | dato · M | Sitio Andino 27-oct-2023 "casi 1 día y medio" (Shell **Mendoza capital**); extremos supuestos |
| INV-02 | Carga del camión | 30.000 L (27.000–34.000) | estimación · M | 27.000 L (2023) y 34.000 L (2009) |
| INV-03 | Tanque por producto líquido | 20.000 L (10.000–25.000) | supuesto · B | aviso de venta Guaymallén **no verificado** |
| INV-04 | Descarga | 45 min (**incluida** en el plazo base; informativo) | supuesto | — |
| INV-05 | Origen | **Dock Sud**; alternativa Luján de Cuyo (YPF) | dato · M | Sitio Andino 2023, Los Andes 2023 |
| INV-06 | Política real | no documentada (pedido "a demanda") | dato · B | Sitio Andino 2023 |
| INV-07 | Política (s, Q) inicial | `s` = **1,5 días** de consumo del producto; `Q = min(cap − s, máx(2,5 × consumo/día, 0,5 × cap))`; nivel inicial 75 % | supuesto | ORQ |
| INV-08 | Camión consolidado | un viaje lleva varios productos (observado: 27.000 L de gasoil **y** naftas) | supuesto · M | Sitio Andino 2023 |
| INV-09 | Crisis de abastecimiento (S7) | plazo **Triangular(72 ; 84 ; 96) h** durante 3–4 días | estimación · B | Los Andes 31-jul-2023 |

#### G. Red de rutas (nota 06 §1.2–1.3; sin cambios respecto de v1 §5-G)
Tiempo de viaje = `km ÷ 70 km/h` (RED-11, supuesto: entre 80 km/h legales y 60 km/h urbanos; OSRM da 81 km/h, inalcanzable para un camión).

| Arco | Ruta | km | min | Cortable |
|---|---|---|---|---|
| `LUJAN`–`PAREDITAS` | RN 40 | 114 *(derivado)* | 98 | sí |
| `PAREDITAS`–`SANRAFAEL` | RN 143 | 107 | 92 | **sí** (nieve jun–ago; obra) |
| `PAREDITAS`–`SOSNEADO` | RN 40 | 176 | 151 | sí |
| `SOSNEADO`–`SANRAFAEL` | RN 144 | 132 | 113 | sí |
| `ALVEAR`–`SANRAFAEL` | RN 143 este | 87,5 | 75 | opcional |
| `SANRAFAEL`–`MONTECOMAN` | RN 146 | 54,1 | 46 | no |
| `MONTECOMAN`–`LAPAZ` | RP 153 *(no verificado)* | 204,7 | 175 | no |
| `LAPAZ`–`LUJAN` | RN 7 | 141,0 | 121 | no |
| `DOCK`–`ALVEAR` | *(no verificada)* | 903,8 | 775 | no |
| `DOCK`–`LUJAN` | *(no verificada)* | 1.056,5 | 906 | no |

**Resultados esperados (control N6):** Luján→estación = **221,8 km / ≈ 190 min**; con RN 143 cortada = **399,8 km** (+178 km, **+153 min**) por el norte (141 + 204,7 + 54,1; la variante sur suma 422); Dock Sud→estación vía Alvear = **991,3 km / 14,2 h** < vía Luján 1.279,0 km. **Consecuencia que la app debe mostrar:** con origen Dock Sud, el corte nevado de la RN 143 *Pareditas–San Rafael* **no está en la ruta**.
**Cortes (escenarios, no probabilidades; 3 casos documentados):** E1 = RN 143 cerrada **6 h** (17-ago-2026); E2 = RN 143 + RN 40 + RN 144 **24–48 h** (1–2-jul-2026); E3 = obra: restricción 8–18 h, demora **30 min por viaje** (sin dato); probabilidad de que un viaje encuentre un corte (invierno): **0,10** (supuesto); fuera de invierno 0. Duración de un corte aleatorio: Triangular(3 ; 6 ; 24) h (supuesto).

#### H. GNC (C8, C9)
| ID | Dato | **Adoptado** | Alternativa | Tipo · conf. | Origen |
|---|---|---|---|---|---|
| GNC-01 | Contrato de suministro | **interrumpible** (sufre cortes) | firme (sin cortes) | supuesto · sin dato | ONB "80 % de las estaciones" **sin fuente**; ENARGAS abr-2026 (verificado) |
| GNC-02 | Episodios de corte en invierno | **2 episodios × 6 días** entre el 1/jun y el 31/ago (≈ 12 días) | 0 – 4 episodios | estimación · B | DO §7 ("10–14 días en jun/jul") |
| GNC-03 | Forma del corte | **total, 24 h** ("hasta nuevo aviso") | ventanas 17–01 h y 09–24 h (San Rafael 2022); **−50 %** de capacidad | dato · M | ENARGAS abr-2026; Sitio Andino 23/6/2022 |
| GNC-04 | Migración a nafta durante el corte | **30 %** | 0 – 60 % | supuesto · sin dato | `DO`: "no hay migración documentada" ⇒ supuesto explícito |
| GNC-05 | Flujo máximo de la red de gas | sin datos de capacidad ⇒ **ventana/episodio aleatorio** | Edmonds-Karp sólo con capacidades reales | — | CASO §6.2 |

#### I. Economía (el otro hueco; todo "heredado" es placeholder visible)
| ID | Dato | **Adoptado** | Tipo · conf. | Nota |
|---|---|---|---|---|
| ECO-01 | Margen por litro | $100/L (≈ 4,7 % del Súper a $2.141) | **heredado** · sin dato | Candidatas: CECHA, FECRA. Parametrizar también como % del precio. |
| ECO-02 | Margen por compra en minimarket | $2.500 | heredado | `DO`: el shop = 5–10 % de los ingresos de la estación |
| ECO-03 | Margen por m³ de GNC | $100/m³ | heredado | mismo placeholder |
| ECO-04 | Sueldo playero / cajero / encargado | **$1.680.000 / $1.800.000 / $1.740.000** (con adicionales) | estimación · M | `DO §4` (FECRA); **la URL dice enero-2026** (C18) |
| ECO-05 | Inversión por cara/surtidor nuevo; operativo mensual | $18.000.000; $250.000/mes | heredado | |
| ECO-06 | Flete | `fijo + $/km × km ida y vuelta`: fijo **$150.000** (heredado), $/km **0** (sin dato) | heredado / supuesto | $150.000 es **implausible** para ≈ 1.000 km con 30.000 L: consultar transportistas. La app avisa si origen = Dock Sud y $/km = 0. |
| ECO-07 | Almacenamiento | $25 por litro-mes | heredado | |
| ECO-08 | Precios (referencia, informativos) | Súper $2.141 · Premium $2.300+ · G2 $2.116 · G3 $2.641 · GNC $699/m³ (oct-2025) | dato · M | `DO §7`, sept-2026 (C19) |
| ECO-09 | Anualización | año = 3 × Σ de los 4 meses representativos | supuesto | rotular **estimación** |

### 5.3 Advertencias que la app debe mostrar (pestaña "Datos y fuentes")
1. **Cada contradicción de §4.2** con el valor adoptado y las alternativas.
2. **Precios de la propia estación en la SE congelados** (2025) y subas de 15 % en 2 meses.
3. **`[RESUMEN]`**: tanques de pick-up y moto, cilindro de GNC, tiempo de GNC (no verificados en el original).
4. **Cifras "confirmadas" sin URL** (270.000 L/mes, 20 % de minimarket, "Res. ENARGAS 409/2026", compresor 20–25 autos/h).
5. **Alerta de coherencia C8** (6 caras GNC vs. 3 % de clientes).
6. Dock Sud = origen documentado para una Shell de **Mendoza capital**, 2023.
7. **GNC en m³**, no en litros.
8. **Sin datos de la propia estación:** hoy todo es estimación/supuesto hasta el relevamiento (§12).

---

## 6. Decisiones abiertas y defaults

| # | Pregunta | Default | Reversible por |
|---|---|---|---|
| V1 | Grafía | "Balloffet" | constante en `ui/textos.py` |
| V2/V8 | ¿Un vehículo por cara? ¿una flecha = una cara? | Sí / Sí (12 posiciones) | `SUR-01`, `SUR-05` |
| V3 | **S3: ¿sólo diésel o nafta?** (la captura 1 dice "surtidores a nafta" para los tres) | S1–S2 nafta, S3 sólo diésel | grupos por configuración |
| V4 | ¿Dos mangueras a la vez? | No | — |
| V5 | ¿Diésel común y/o premium? | **Ambos** (SE los declara) | `Producto.activo` |
| V6 | ¿Compresores GNC? | 3 | `SUR-06` |
| V7 | ¿Siempre playero? | Sí, 24 h | autoservicio = S9 |
| V9/V10 | Minimarket y horario | 1 caja; **"Shell Select (nombre sin confirmar)"**; playa 24 h, shop 24 h (supuesto) | `EST-06` |
| V11 | Relevamiento | **Pendiente**: camino de carga listo en la app (§8.4) | importador CSV |
| V12 | ¿Año o mes por estación? | **Mes representativo por estación** (ene · abr · **jul** · oct); "año" = 365 días con calendario | `fecha_inicio`, `dias` |
| V13 | "Ciudad parecida" | jerarquía A→B→C→D; D sin uso | campo `nivel` |
| N1 | ¿Cola única por grupo o por cara? | única por grupo | `PER-06` |
| N2 | ¿Camión consolidado? | primero 1 por producto; después consolidado | `consolidado` |
| N3 | ¿Origen? | Dock Sud | `ParametrosRed.origen` |
| N4 | ¿Hex de la paleta? | `#FBCE07` / `#DD1D21` (las fuentes **difieren**; §8.1) | `ui/tema.py` |
| **N5** | ¿Se conserva el Monte Carlo? | **Sí**: (a) variabilidad diaria opcional (DEM-07); (b) **Monte Carlo de 5 pasos para tipo de cliente y producto** (§7.2). Es una unidad de la materia y se defiende mejor que "determinista". | `modo_demanda` |
| **N6** | ¿Calentamiento? | **2 días** en ambos modos (B4) | `dias_calentamiento` |
| **N7** | ¿Estacionalidad? | **Neutra** + presets (C10) | DEM-06 |

---

## 7. Especificación del motor (`sim/`)

> Los bloques son **contratos**, no implementaciones. Respetar nombres y semántica.

### 7.1 Demanda (corrige B1, B2, B5)
```python
@dataclass(frozen=True)
class ParametrosDemanda:
    litros_mes: float = 270_000.0          # DEM-01  (LITROS por mes; la variable de entrada)
    modo: str = "esperada"                  # "esperada" (fija por día) | "monte_carlo" (factores relativos DEM-07)
    perfil: PerfilHorario = ...             # DEM-02
    factor_fin_de_semana: float = 1.30      # DEM-03
    estacionalidad: tuple[float, ...] = (1.0,) * 12   # DEM-06 (preset)
    pct_gnc: float = 0.03                   # DEM-05 (clientes)
    pct_minimarket: float = 0.20            # DEM-08
```
- **`fecha_inicio: tuple[int,int]`** (mes, día) en `ParametrosSimulacion`; **una sola función** `dias_y_fecha(horizonte, estacion|mes) -> (fecha_inicio, dias)`: día = 1, semana = 7, mes = 30 (o el real), **estación = 90 desde el 1 del mes representativo**, año = 365 desde el 1/ene. Cada día se mapea a su **mes de calendario** y su **día de la semana**.
- **Litros del día** = `litros_mes / días_del_mes_ref × índice_mes(÷ media de los índices) × factor_tipo_de_día(normalizado, §14.4)`.
- **Clientes del día** = `litros_día / litros_medios_por_cliente_líquido` (§14.2), más los clientes GNC (`pct_gnc`). **Se prohíbe** dividir litros por 30 y llamarlo "autos".
- Si `modo = "monte_carlo"`: se sortea un **factor relativo** de la tabla empírica (5 pasos, intervalos 01–00) y se multiplica; el registro por día de la pestaña Demanda se conserva.
- El motor **sigue** usando llegadas Poisson no homogéneas (λ(t) por hora) y tiempos aleatorios: **réplicas, IC 95 % y calentamiento se mantienen** (B4).

### 7.2 Cliente: "producto primero" + Monte Carlo de 5 pasos
Al **llegar** (todo se sortea acá, con streams propios):
1. **Producto** ← sorteo por pesos de llegada derivados de la mezcla en **litros** (§14.2), más `pct_gnc` para GNC. *(Monte Carlo de 5 pasos, tabla visible: frecuencia → probabilidad → acumulada → intervalo de números aleatorios → sorteo.)*
2. **Tipo de vehículo** ← sorteo condicionado al producto (matriz de §5-D). *(Segunda tabla Monte Carlo, también visible.)*
3. **Litros** ← `Triangular` del tipo (stream `"litros"`); GNC: `carga_m3`. **Tiempo de servicio** según el grupo (TIE-02/04) + `litros/90` si es camión. **Compra** ← Bernoulli(`pct_minimarket`).
4. **¿Hay producto?** Líquido: `nivel[producto] ≥ litros`. GNC: ver §7.5. Si no, pérdida con **motivo** (§7.6); el cliente **no hace cola**.
5. **¿Hay lugar en la cola?** Si `len(cola del grupo) ≥ capacidad_cola` ⇒ no entra (`cola_llena`).
6. **Cola y servicio:** cara del grupo (+ **playero** si el grupo lo requiere; adquisición **cara primero, playero después**, sin *deadlock*); paciencia como hoy sobre el tiempo **total** hasta empezar a ser atendido. El combustible se descuenta **al empezar a cargar**, **del tanque del producto**.
7. Si compra ⇒ cola de **cajas** como hoy.

**Playeros por turno.** `simpy.PriorityResource(capacity=máx_playeros)` + proceso `controlar_turnos()` que en cada borde de turno/refuerzo toma (prioridad −1) o libera "reservas ficticias" hasta que `capacity − reservas = playeros del turno` (`req.cancel()` si la reserva todavía no se concedió, `release` si sí). Efecto emergente buscado: **servidores = mín(caras libres, playeros)**. Mismo patrón para cajas por turno. **Refuerzo en el pico** (`((desde_h, hasta_h, extra), …)`) para el escenario S2.
**Disciplina:** `por_grupo` = un `Resource` por grupo (FIFO); `por_cara` = un `Resource(1)` por cara, el cliente elige la fila más corta **al llegar** y no cambia.

### 7.3 Inventario por producto y camión
- Un `nivel` por producto líquido; posición = nivel + en camino; **(s, Q) por producto**. Quiebre = **serie temporal por producto**.
- **N2 (dos etapas):** etapa 1, un camión por producto; etapa 2 (`consolidado=True`), un viaje se dispara cuando **cualquier** posición ≤ `s`, carga hasta 30.000 L entre los productos con posición ≤ `1,3·s` (proporcional a su Q) y **un solo flete**.
- **Plazo = base (INV-01) + demora por corte de ruta (§7.4)**; el stream `"entrega"` se conserva para la base. **S7:** plazo (72 ; 84 ; 96) h durante una ventana.

### 7.4 Red (`sim/red.py`)
`Arco(a, b, km, ruta, cortable)`, `ParametrosRed(arcos, origen, destino, velocidad_kmh, escenario_corte)`. `camino_mas_corto(red, origen, destino, cerrados) -> (km, min, ruta)` con **Dijkstra (`heapq`), sin networkx**. Demora = `min(tiempo_alternativa − tiempo_original, duración_restante_del_corte)`, **sumada al plazo**. Cortes forzados E1–E4 o sorteados (jun–ago, `p = 0,10` por viaje; stream `"corte_ruta"`).

### 7.5 GNC (corrige C9)
`ParametrosGNC(contrato, episodios, dias_por_episodio, forma, compresores, migracion_a_nafta, carga_m3)`.
- Con `contrato = "interrumpible"`, en jun–ago se sortean **episodios** (stream `"corte_gnc"`): durante un episodio las **6 caras GNC no atienden** (los que ya cargan terminan). `forma = "total_24h"` (default) | `"ventana"` (17–01 / 09–24) | `"parcial_50"` (mitad de los compresores).
- **Compresores** = recurso con capacidad `compresores` (default 3) que se toma tras la cara y se retiene durante la carga ⇒ **el compresor, no las 6 caras, limita el GNC**.
- Cliente GNC durante el corte: con prob. `migracion` (stream `"migracion"`) **pasa a Súper** (mismo auto; litros según su tipo; entra a la cola del grupo A), si no se pierde (`corte_gnc`). Se cuenta `migrados_gnc_a_nafta` aparte.

### 7.6 Motivos de pérdida (taxonomía fija; la UI usa estos nombres)
`sin_combustible` (por producto) · `abandono_espera` · `cola_llena` · `corte_gnc` · `abandono_caja`; y `migrados_gnc_a_nafta` (no es pérdida). **Todo cliente que llega termina en exactamente una de:** atendido · perdido (un motivo) · migrado→atendido/perdido · sigue adentro.

### 7.7 Catálogo de escenarios (CASO §7 + datos nuevos)
| ID | Escenario | Qué varía | Pregunta |
|---|---|---|---|
| S0 | Hoy | — | línea base por estación del año |
| S1 | Día típico por estación | estación | animación y comparativa |
| S2 | **Playeros en el pico** | −1 / base / +1 / +2 en (07–10, 16–18) | ¿alcanza la dotación? (con 2 playeros ρ_pico ≈ 0,86) |
| S3 | **Ola de frío con corte de GNC** | forma del corte, episodios, migración, compresores | pérdida directa y adónde va |
| S4 | **Corte de la ruta del camión** | E1/E2/E3 × origen Dock Sud / Luján | plazo y quiebre |
| S5 | **Política de reposición** | barrido (s, Q) por producto, con red y cortes | ¿cuándo y cuánto pedir? |
| S6 | **Decisión económica** | playero extra en pico vs. stock extra en invierno | ¿qué conviene en $/mes? |
| S7 | Crisis de abastecimiento | plazo 72–96 h | resiliencia |
| S8 | Cola por grupo vs. fila por cara | PER-06 | ¿cambia la espera? |
| **S9** | **Autoservicio** (Decreto 46/2025) | −1 playero por turno | ¿se puede ahorrar personal? |
| **S10** | **Cierre nocturno 22–06** (`DO`) | perfil = 0 de 22 a 06 | efecto del horario (C1) |
| **S11** | **Estacionalidad turística** | preset "proxy" (jun = 55 … ene = 100) | ¿importa la estacionalidad? |
| **S12** | **Quincena** | +100 % 3 días/mes | picos de cobro |
Resultado de cada uno: promedio ± IC 95 % sobre réplicas con **números aleatorios comunes**. Los "+1 surtidor / +1 cajero" siguen como variantes de S2/S6. `Escenario` guarda **cambios declarativos** `tuple[tuple[str, object], …]` (no lambdas: `st.cache_data` los serializa con pickle).

### 7.8 Estaciones del año y sensibilidad
- `correr_estaciones(p, replicas, semilla)` → 4 corridas (**ene · abr · jul · oct** por defecto; `fecha_inicio` real). Con estacionalidad neutra, las diferencias vienen de **GNC y ruta**: es lo correcto hasta tener la serie de la SE.
- `sim/sensibilidad.py`: para cada `Dato` con `bajo/alto` o `alternativas`, correr con cada extremo (resto en base, mismas semillas) y devolver el delta del **margen operativo mensual** (y de la espera pico). **Cada contradicción de §4.2 es un eje**. Detrás de un botón, cacheado.

### 7.9 Economía (`sim/economia.py`)
Margen por producto (L o m³), minimarket, flete `fijo + $/km × km`, almacenamiento por producto, **costo de personal** (ECO-04), venta perdida por motivo. Criterio vigente: *venta perdida = costo de oportunidad* (no se resta del margen). Mensual por estación y **anual estimado** (ECO-09).

---

## 8. Especificación gráfica (`app.py`, `ui/`, `.streamlit/`)

### 8.1 Tema Shell — única fuente: `ui/tema.py`
**Los hex de Shell difieren entre fuentes** (búsqueda del 5/10/2026): amarillo `#FBCE07` / rojo `#DD1D21` en una paleta digital habitual; `#FFCD00` / `#DA291C` en otras. **Default `#FBCE07` / `#DD1D21`.** Todo lee de `ui/tema.py`; cambiar de variante = una línea. Contrastar con las fotos del grupo (surtidores amarillos y blancos, techo del playón). **No usar logo ni pecten** (marca registrada). Pie fijo: *"Proyecto académico de Investigación Operativa; no es oficial ni está afiliado a Shell."*

```python
AMARILLO="#FBCE07"; ROJO="#DD1D21"; AMARILLO_SUAVE="#FFF6C2"
TINTA="#1A1A1A"; TINTA_TENUE="#5B5B5B"; FONDO="#FFFFFF"; FONDO_PANEL="#F6F4EC"; BORDE="#E2DED0"
ASFALTO="#2B2F36"                      # sólo dentro de la animación
LIBRE="#1E9E5A"; OCUPADO=AMARILLO; PERDIDO=ROJO     # estados: SIEMPRE con texto, no sólo color
PRODUCTO={"super":AMARILLO,"vpower":ROJO,"diesel":"#4B5563","vpower_diesel":"#0F766E","gnc":"#1D6FB8"}
```
**Reglas obligatorias:** (1) amarillo = fondo/relleno/acento, **nunca texto sobre blanco** (contraste ≈ 1,6:1); texto sobre amarillo = `TINTA`; (2) el **rojo de marca también es el rojo de "pérdida"** ⇒ toda pérdida lleva **rótulo** ("SIN COMBUSTIBLE", "GNC CORTADO") y los gráficos de pérdida llevan etiqueta de valor o trama; (3) **un solo tema claro**; (4) un `template` Plotly propio (`plantilla_plotly()`) que reemplaza `plotly_white` y los hex sueltos de `ui/graficos.py`; (5) `[theme]` en `.streamlit/config.toml` (**conservar `fileWatcherType = "poll"`**):
```toml
[theme]
base = "light"
primaryColor = "#DD1D21"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#FFF6C2"
textColor = "#1A1A1A"
font = "sans serif"
```
(6) `css_global()` inyecta CSS mínimo (franja amarilla superior con filete rojo, insignias); `paleta_json()` alimenta el SVG (reemplaza las constantes hardcodeadas de `ui/animacion.py`). **Prohibido** repetir un hex fuera de `ui/tema.py` (N15).

### 8.2 Estructura de la app (≤ 7 pestañas; sub-pestañas adentro)
| Pestaña | Contiene |
|---|---|
| 🏪 **La estación** | ficha (EST-*), esquema (12 caras, 3 grupos, minimarket), esquina Balloffet/Los Sauces, **advertencias (§5.3) y contradicciones (§4.2)** |
| 🎬 **Animación** | reproductor (§8.5) + selector de **fecha/estación**, tipo de día y día; colas y ocupación por grupo |
| 📊 **Resultados** | *Indicadores* · *Por hora (pico descubierto)* · *Por grupo y producto* · *Comparar escenarios (S0–S12)* |
| 🎲 **Demanda** | **litros/mes → clientes/día** (la cadena de §14.2, visible), Monte Carlo de 5 pasos (**producto** y **tipo de vehículo**), perfil por tipo de día/mes, calibración |
| 🛢️ **Abastecimiento** | *Tanques* (4 dientes de sierra, (s,Q) por producto) · *Red y rutas* · *GNC* · *Estaciones del año* |
| 💰 **Economía y decisión** | *Economía* ($/mes y anual) · *Sensibilidad* (tornado) · *Conclusión* (las preguntas del CASO §7 en $/mes) |
| 📚 **Datos y método** | *Datos y fuentes* (Registro completo, filtros, alternativas, **CSV**) · *Modelo y método* · *Verificación* (botón que corre los controles) |

### 8.3 Gráficos
Tanques ×4 (dientes de sierra, punto de pedido, quiebres) · perfil horario por tipo de día/mes · por grupo: espera, cola, utilización, **playeros ocupados vs. en turno por hora** (acá se ve el cuello) · pérdidas apiladas por **motivo** · red (nodos y arcos, ruta óptima, arcos cortados tachados, histograma del plazo con/sin cortes) · GNC (línea de tiempo con episodios sombreados; atendidos / migrados / perdidos) · 4 estaciones comparables · **tornado** · todos con etiquetas de valor, `separators=",."`, unidad en el eje, títulos que dicen la conclusión.

### 8.4 Insignias y barra lateral (`ui/datos_ui.py`)
Cada widget y cada fila lleva la insignia de su `Dato`: `🟢 dato` · `🟡 estimación` · `🔵 observación propia` · `🟠 supuesto` · `⚪ heredado (sin fuente)`; tooltip con **fuente, nivel, fecha, nota y alternativas**. La barra lateral se arma por categoría del Registro. **Anulación por relevamiento:** `st.data_editor`/CSV pisa un `Dato` (⇒ `observacion`, 🔵) y se exporta junto con el Registro. **Los widgets de demanda piden LITROS/MES y muestran al lado los clientes/día resultantes** (no se vuelve a repetir B1).

### 8.5 Animación (`ui/animacion.py`) — rediseño
Se mantiene la arquitectura (Python manda JSON, **el navegador dibuja SVG**; `st.components.v1.html`, **no** `st.html`). Lienzo 1200×680. Composición (de las capturas del grupo):
1. **Barra superior:** reloj, estación/mes, tipo de día, día N, estado de medición, contadores (atendidos, compraron, perdidos por motivo, migrados).
2. **Avenida Balloffet (RN 143)** con entrada; la cola **desborda a la avenida** al superar `capacidad_cola` (efecto + contador).
3. **Playón techado** (techo amarillo, filete rojo): **Zona A** (S1–S2: 4 caras), **Zona B** (S3: 2), **Zona C** (S4–S6: 6, con **compresores** ocupados/3). Cada **cara** tiene flecha de acceso (V8), estado con **texto** (libre/ocupado/sin combustible/cortado) y el auto cargando.
4. **Playeros** (personas): "n en turno / m ocupados"; si faltan se ve el auto **esperando con la cara ocupada**.
5. **Minimarket** ("Shell Select", ventanales): cola, caja, cobrando/libre.
6. **Tanques por producto** (4 barras, punto de pedido, litros) + **GNC: DISPONIBLE / CORTADO**.
7. **Camión en ruta**: mini-mapa de la red con la ruta activa; arco cortado tachado y desvío; "llega en X h".
8. Controles: play/pausa, reiniciar, velocidad, barra, **saltar a hora pico / a quiebre / a corte**.
**Cuadro v2 columnar** (`{"t":[…], "cola":{"A":[…],…}, …}`; **no** listas posicionales): por grupo `{ocupadas, cola, rechazados}`, `playeros{en_turno, ocupados}`, `cajas`, `compresores`, por producto `{nivel, en_camino}`, `gnc_cortado`, `camion{en_viaje, progreso, ruta, arco_cortado}`, acumulados por motivo, `migrados`, `en_calentamiento`. **Se graba un solo día**; `dt_traza` 0,5 min (2.880 cuadros; si el JSON supera ~3 MB, 1 min). **Accesibilidad:** nada sólo por color; contraste ≥ 4,5:1; respetar `prefers-reduced-motion`.

### 8.6 Textos y métricas (`ui/textos.py`)
Métricas nuevas por grupo, playeros, motivo de pérdida, producto, plazo con cortes y GNC. **`SUPUESTOS` se genera desde el Registro** (`tipo ∈ {supuesto, heredado, estimacion}`). `DESCRIPCION_MODELO` ya no dice "un solo producto".

---

## 9. Plan por fases con compuertas

> Cada fase: commit en castellano + reporte (§13). **Todas** las compuertas deben pasar.

### Fase 0 — Auditoría y corrección de Fase 2 ★ (primero, ½ día)
- Instalar (`pip install -r requirements.txt`), correr `python verificar.py` (22/22) y la app. **Guardar los números dorados** (§14.1) en `verificar.py` (control N1).
- **Corregir B1, B2, B4, B5** en el código existente (parche mínimo, sin esperar al rediseño): `autos_por_dia` desde **litros ÷ litros medios por cliente**; `fecha_inicio` real; "determinista" → "demanda esperada"; `dias_calentamiento = 2` por defecto; **una** función `horizonte → (fecha_inicio, dias)`; el slider de demanda muestra **clientes/día** al lado.
- Avisos de una línea al tope de `CLAUDE.md`, `FASE2_IMPLEMENTACION.md`, `DATOS_OPERACIONALES…md` y `ONBOARDING…md` remitiendo a este archivo (la corrección de fondo es Fase 10).
- **Gate:** 22/22 · **N16** (270.000 L/mes ⇒ 270.000 ± 3 % simulados, 3 réplicas) · **N17** (horizonte "estación" de invierno ⇒ meses jun–ago; "mes" de julio ≠ "mes" de enero con el preset "proxy") · dorados intactos con `modo=monte_carlo` · la app corre con 270.000 L/mes **sin colapsar** (ρ_pico < 1 con 2 playeros: §14.2).

### Fase 1 — Registro de datos + tema Shell (visible, sin riesgo) ★
- `sim/datos.py` (§5), `ui/tema.py`, `ui/datos_ui.py`, `[theme]`; migrar `ui/graficos.py`; barra lateral con **insignias**; pestañas **📚 Datos y fuentes** (con **contradicciones y alternativas**, CSV) y **🏪 La estación**; pie "no afiliado".
- **Gate:** 22/22 · N14 · N15 · captura de pantalla con el tema Shell (§10.4) · el CSV tiene todas las filas (incluidas las alternativas de §4.2).

### Fase 2 — Núcleo del motor (grupos, producto primero, playeros, cola finita)
`config.py` (§7.1–7.2), `distribuciones.py` (streams **al final**, `discreta`), `modelo.py`, `estadisticas.py` (por grupo/motivo). Productos y tanques "de a uno". **`clasico()` debe reproducir los dorados exactamente.**
**Gate:** 22/22 · N1–N5, N9, N10, N16 · réplica ≤ 1,5 s.

> **FASE 2 CERRADA (5/10/2026).** Cierre del trabajo que había quedado en el stash.
> **Qué hay en el código:**
> - `sim/config.py`: `Producto`, `Grupo`, `TipoVehiculo` (con `es_gnc`), `InventarioProducto`,
>   builders desde el Registro (`productos_desde_registro` reproduce §14.2: 21,4 / 26,0 / 64,2 /
>   81,5 / 7 m³), `inventario_real(litros_mes, capacidad, plazo, nivel_inicial_pct)` (INV-07),
>   `turnos_de(playeros)` (noche 22–06 · mañana 06–14 · tarde 14–22, cuatro tramos por día) y
>   `ParametrosSimulacion` con `estacion_real=True` por defecto. `clasico()` fija todo lo del §10.1.
> - `sim/modelo.py`: dos montajes (real y clásico). Real = producto primero (Monte Carlo de 5
>   pasos), playeros por turno (`PriorityResource` + reservas), cola finita, disciplina
>   `por_grupo`/`por_cara`, un tanque con (s, Q) por producto líquido, GNC sin tanque y sin
>   playero (los episodios son Fase 6). Los subgeneradores de atención devuelven si el cliente
>   cargó: **quien se va sin cargar no pasa por la caja** (bug hallado y corregido al cerrar la fase).
> - `sim/estadisticas.py`, `sim/runner.py`: colectores por grupo/producto/motivo, `util_playeros`,
>   `abandonos_playero`, `litros_por_tipo`, `correr_estacion_real()`.
> - `sim/distribuciones.py`: streams `"producto"` y `"tipo_vehiculo"` AL FINAL de `STREAMS`.
> - `app.py`: selector **Modelo** (real / clásico; cambiar de modelo vuelve a correr), widgets de
>   playeros, cola, disciplina y GNC, tanques por producto, pestañas adaptadas (Demanda con la
>   cadena litros → clientes y las dos tablas Monte Carlo; Inventario con 4 tanques; Escenarios con
>   el único "Base" real; Conclusión sin veredicto de capacidad). El caso clásico conserva los 4
>   escenarios de capacidad y el barrido de políticas.
>
> **Compuerta (5/10/2026):** `verificar.py` → **51/51 OK** (los 22 originales, ahora
> con el modelo real como default y los clásicos sobre `clasico()`, más N1, N2, N3, N4, N5, N9, N10,
> N14, N15, N16, N17/N18) · **N1 dorados exactos** (diferencia 0,00) · réplica real de 31 días
> de 0,5 a 1,2 s según la carga de la máquina (≤ 1,5 s) · app sin excepciones ni errores de consola (Playwright
> con Chrome instalado).
>
> **Correcciones al stash hechas al cerrar:** `TipoVehiculo.es_gnc` no existía (el modo real no
> arrancaba); los turnos de playeros se aplicaban sólo el primer día (desde el día 2, 1 playero
> siempre ⇒ 22 % de abandono falso); el GNC consumía de un tanque inexistente y sumaba m³ a los
> litros; los clientes perdidos pasaban igual por la caja; `playeros_ocupados` no se decrementaba en
> una salida temprana; el cliente GNC sorteaba el tipo "auto" de nafta en vez del cilindro.
>
> **Deuda conocida:** horizonte "año" = 365 días ⇒ ≈ 10 s por réplica (B7: dejarlo en una corrida
> por escenario en la Fase 7); la animación sigue siendo la agregada de la v1 (Fase 3); el
> barrido de políticas por producto y el camión consolidado son Fase 4.


### Fase 3 — Animación nueva
`Cuadro` v2 (carriles, cola por producto, tanques y camión) y `ui/animacion.py` (§8.5) con `paleta_json()`. **Gate:** capturas de cada zona, de la cola desbordada y del camión · sin errores de consola · saltos funcionando · 22/22.

> **FASE 3 CERRADA (5/10/2026).**
> - `sim/traza.py`: `Cuadro` suma `grupos` (por zona: carriles por cara, cola por producto, largo, rechazados), `tanques` (nivel, litros en camino, progreso del camión, horas que faltan), `perdidos_cola_llena` y `gnc_cortado`.
> - `sim/modelo.py`: carriles (qué auto ocupa cada cara), cola visible por zona y pedidos abiertos por producto; `_cargar_en_cara` separado de `_atender_real` para liberar el carril en un `finally`. Sirve para dibujar: el motor no consulta nada de eso (los dorados siguen exactos).
> - `ui/animacion.py`: reproductor nuevo, columnar, SVG dibujado en el navegador. Avenida con autos que pasan de largo, techo amarillo con filete rojo, zonas A/B/C con 12 caras y surtidores de a dos, cola con lugares numerados, playeros (en turno / atendiendo / autos con la cara ocupada esperando), minimarket, un tanque por producto, camión en viaje por producto, estado del GNC. Cada auto lleva el color de su producto y cada estado lleva texto. Saltos: hora pico, primer quiebre, próxima descarga, corte de GNC (deshabilitado hasta la Fase 6). Sirve también para el caso clásico (una zona, un tanque).
> - `ui/tema.py`: paleta clara de la animación (se eliminó la oscura); `COLOR_PRODUCTO`.
> - `app.py`: el día a animar se elige en la pestaña, con fecha y tipo de día.
> - `verificar.py`: control 17 (cuadros = motor en los 2.880 cuadros, cola ≤ capacidad, JSON < 3 MB; 0,5 MB reales).
> - **Compuerta:** `verificar.py` 54/54 · N1 dorados exactos · N15 (0 hex fuera de `ui/tema.py`) · 0 errores de consola en el reproductor suelto y dentro de Streamlit (real y clásico) · saltos y reproducción verificados con Playwright. Capturas en `reports/qa/fase3/` (`reports/qa_animacion.py`, `reports/qa_fase3_app.py`).
> - **Deuda:** compresores y corte de GNC (Fase 6); ruta y cortes del camión (Fase 5, hoy una línea fija "Dock Sud → estación" sin cortes); el texto del SVG es chico al escalarlo en pantallas angostas.

### Fase 4 — Cinco productos, 4 tanques, política por producto, plazo real
Tanque por producto, plazo INV-01, `grilla_sugerida` y `barrer_politicas` por producto; camión **independiente** (N2 etapa 1). **Gate:** 22/22 + N3 (conservación **por producto**; m³ del GNC) · el barrido encuentra una política ≤ a la inicial.

> **FASE 4 CERRADA (5/10/2026).** Los cinco productos, el tanque por producto, el plazo INV-01 y el camión independiente ya estaban desde la Fase 2 (N3 incluido); esta fase agrega la política por producto.
> - `sim/distribuciones.py`: un stream de plazo **por producto** (`entrega_super`, `entrega_vpower`, `entrega_diesel_g2`, `entrega_diesel_g3`), AL FINAL de `STREAMS`. Sin eso, el sorteo del plazo de un producto dependía de cuántos pedidos habían hecho los otros y las cuatro curvas no se podían medir juntas.
> - `sim/runner.py`: métricas por producto (`pedidos_`, `nivel_`, `litros_sin_stock_`, `perdidos_sin_stock_por_producto`), `con_politicas`, `grilla_politicas_real` (13 puntos: la cargada + 4 s × 3 Q, medidos en días de consumo de cada producto) y `barrer_politicas_real`. Como cada camión y cada plazo son propios, el barrido corre 13 puntos × réplicas con las **4 políticas a la vez** (no 13⁴): ≈ 29 s con 2 réplicas.
> - `sim/economia.py`: `analizar_politicas_real` (costo de cada tanque = pedidos × flete + nivel promedio × $/L-mes + faltante por **falta de stock**; el abandono por cola no se imputa a la política) y `ahorro_por_producto`.
> - `ui/graficos.py`: `grafico_tanques_real` (4 dientes de sierra con su s). `app.py`: pestaña Inventario con tabla por tanque, los 4 dientes, el botón del barrido, la mejor política de cada tanque, "Usar las mejores políticas" (carga s y Q por tanque en la barra lateral, ahora editable), detalle y gráficos por producto, y línea de reposición en la Conclusión. El caso clásico conserva su barrido.
> - **Compuerta:** `verificar.py` 59/59 (control 18: grilla válida, monotonía de s [N11], independencia entre tanques < 0,5 % de cambio en los otros, barrido ≤ política cargada, costo reconcilia) · N1 dorados exactos · 0 excepciones y 0 errores de consola en la app (Playwright). Con la política inicial INV-07 el modo real tenía 29 % de días con quiebre; aplicando las mejores baja a 4 % y el nivel de servicio pasa de 94,8 % a 96,8 % (mes de enero, 4 réplicas).
> - **Resultado a no sobreinterpretar:** el ahorro (≈ $0,8 M/mes con 2 réplicas) usa flete y márgenes **heredados sin fuente** (ECO-01/02/06); lo defendible es la **forma** de la política (s ≈ 2,5 días de consumo, Q ≈ 4–5 días), no los pesos. El flete de $150.000 por ≈ 1.000 km es implausible: lo más probable es que el flete real mueva la Q óptima.
> - **Deuda:** camión consolidado (N2 etapa 2: un viaje con varios productos y un solo flete); el GNC no tiene política (no hay tanque); el barrido optimiza tanque por tanque con las demás variables fijas.

### Fase 5 — Red de abastecimiento
`sim/red.py` (Dijkstra), cortes E1–E4, demora → plazo; pestaña **Red y rutas**. **Gate:** N6 (km y minutos de §5-G **exactos**) · N11 · captura de la red.

> **FASE 5 CERRADA (5/10/2026).**
> - `sim/red.py`: Dijkstra con `heapq` (sin networkx, cacheado), `demora_por_corte` (= 0 si el arco cerrado no está en el camino óptimo; si está, mín(desvío, duración restante); sin alternativa, espera), `demora_de_viaje` (cortes `ninguno` / `aleatorio` jun–ago con p = 0,10 por viaje / E1–E4 con ventana desde `corte_dia`; E3 = obra de +30 min en la franja 8–18 h) y `muestrear_plazos` para el histograma.
> - `sim/config.py`: `Arco`, `CorteRuta`, `ParametrosRed` (valores del Registro) y `ParametrosSimulacion.red` (`None` en `clasico()`). Registro: RED-12 (escenario), RED-13 (p de corte), RED-14 (duración), RED-15 (E1–E4), RED-16 (día del corte), RED-17 (meses con cortes); N14 ahora también revisa `ParametrosRed`.
> - Motor: `pedir_camion` suma la demora al plazo base INV-01 (que ya incluye el viaje normal); métricas `viajes_demorados_pct` y `demora_ruta_promedio`; la animación muestra el escenario, la ruta y el recargo por corte. Un stream de corte **por producto** (`corte_ruta_*`, al final de `STREAMS`) en lugar del único `"corte_ruta"` del §7.4, por la misma razón que el plazo: no romper la independencia entre tanques.
> - UI: expander "Ruta del camión y cortes" (origen, escenario, día del corte, p, velocidad) y pestaña **Red y rutas** (mapa con la ruta óptima, los arcos cortados y el desvío; tabla de qué le hace cada corte a cada origen; histograma del plazo con y sin cortes; botón que simula la estación con y sin cortes).
> - **Compuerta:** `verificar.py` 66/66 · N1 dorados exactos · **N6**: Luján→estación 221,8 km / 190,1 min; con la RN 143 cortada 399,8 km (+178,0 km, +152,6 ≈ +153 min) por La Paz y Monte Comán; Dock Sud→estación 991,3 km / 14,16 h por Alvear · Dijkstra = enumeración de todos los caminos (10 casos) · **N11**: con cortes el plazo sube, el quiebre no baja, más playeros ⇒ menos espera, más demanda ⇒ más espera · sin cortes o fuera de jun–ago el resultado es idéntico al de sin red · 0 excepciones y 0 errores de consola (Playwright). Capturas en `reports/qa/fase5/`.
> - **Corrección de datos (RED-01):** la tabla §5-G dice 114 km, pero con 114 + 107 = 221 no se obtiene el 221,8 km de N6. Se adoptó **114,8 km** (221,8 − 107), que reproduce N6 y la variante sur de 422,8 km; la alternativa de 114 km queda en el Registro. Además, Dock Sud→estación por Luján da 1.278,3 km con los arcos, no los 1.279,0 de la nota 06 (0,7 km de diferencia del arco derivado).
> - **Resultado que se ve en la app:** con origen Dock Sud, los cortes E1 y E2 (RN 143 oeste / RN 40 / RN 144) **no demoran** al camión; sólo lo afecta E4 (RN 143 este, +4,1 h) y la obra (+30 min). Con origen Luján, E1 y E2 demoran +2,5 h (desvío de +178 km por La Paz y Monte Comán). En julio con p = 0,10 el efecto es chico (≈ 6 % de los camiones demorados, plazo +0,2 h): la probabilidad de corte es un supuesto sin dato (RED-13).
> - **Deuda:** los cortes sorteados son independientes por viaje (no hay un calendario común de episodios); las posiciones de los nodos del mapa son aproximadas; la demora se calcula con el viaje saliendo a las 00:00 del corte (sin sortear en qué punto de la ruta lo encuentra).

### Fase 6 — GNC (episodios, compresores, migración)
**Gate:** N7, N8 · captura de los episodios sombreados. *(6b, opcional: Edmonds-Karp sólo con capacidades reales; si no, omitir y dejarlo escrito.)*

> **FASE 6 CERRADA (6/10/2026).**
> - `sim/gnc.py`: calendario de episodios (stream `"corte_gnc"`): `episodios` fechas al azar entre el 1/jun y el 31/ago de `dias_por_episodio` días; `intervalos_de_corte` según la forma (`total_24h` y `parcial_50`: días enteros; `ventana`: 17–01 h). Con `episodios_en_horizonte` se sortean entre los días de invierno del horizonte (herramienta de análisis).
> - `sim/config.py`: `ParametrosGNC` (contrato, episodios, días por episodio, forma, compresores, migración, forzar en el horizonte) y `ParametrosSimulacion.gnc` (`None` en `clasico()`). Registro: GNC-06 (duración del episodio: 6 días) y GNC-07 (forzar en el horizonte); `ParametrosGNC` entra en N14. `carga_m3` no es un campo: sale del tipo `auto_gnc` (VEH-05).
> - Motor: **compresores** como `PriorityResource` (3) que se toma tras la cara y se retiene al cargar (el compresor, no las 6 caras, limita el GNC; con paciencia como los playeros); `controlar_gnc` aplica el calendario (corte total o compresores al 50 % con reservas de prioridad −1); el cliente GNC que llega con el GNC cortado **pasa a Súper** con prob. GNC-04 (stream `"migracion"`: vuelve a sortear litros y tiempo de carga con su identidad, y se re-etiquetan sus llegadas para que cada zona siga cerrando) o se pierde (`corte_gnc`); quien ya estaba en la cola de la zona C y se topa con el corte al empezar a cargar se pierde (no migra). Contadores `gnc_afectados`, `migrados_gnc_a_nafta`, `perdidos_corte_gnc`, `dias_con_corte_gnc`; la economía cuenta el corte como venta perdida.
> - UI: expander "GNC y cortes de invierno", pestaña **🔥 GNC** (alerta de coherencia C8, calendario de episodios de la réplica 1, indicadores, gráfico por día con los **episodios sombreados**, comparación con contrato firme) y animación con compresores en uso, "GNC CORTADO", contador de corte y de pasados a nafta; el botón "el corte de GNC" ya funciona.
> - **Compuerta:** `verificar.py` 72/72 · N1 dorados exactos · **N7** (sin episodios o con contrato firme: 0 afectados; corte total sin migración: 96 afectados = 96 perdidos y 0 GNC atendido en los días de corte completo) · **N8** (34 migrados + 62 perdidos = 96 afectados, y cada zona cierra) · **N12** (julio con episodios: 34 migrados; enero: 0) · `ventana` corta ≤ 8 h por día · `parcial_50` no corta a nadie · con 1 compresor nunca cargan 2 autos GNC a la vez (espera en la zona C 2,19 min contra 0,00 con 6) · en enero el resultado es **idéntico** al de la Fase 5 · 0 excepciones y 0 errores de consola (Playwright). Capturas en `reports/qa/fase6/`.
> - **6b (Edmonds-Karp):** omitido a propósito: no hay datos de capacidad de la red de gas (GNC-05), así que el corte se modela como episodios aleatorios, como dice §7.5.
> - **Resultado a no sobreinterpretar:** con 2 episodios de 6 días el GNC afecta a ≈ 2,4 clientes por día en promedio del mes de julio (≈ 10 por día en los días de corte). El GNC es ≈ 3 % de los clientes, así que el corte duele poco en clientes; la pregunta de fondo es la alerta C8 (6 caras de GNC para ≈ 3 % de la demanda), que sólo cierra el relevamiento. Episodios, duración, forma y migración son supuestos (GNC-02/03/04/06).
> - **Deuda:** los clientes que ya esperan en la cola de GNC cuando empieza el corte no migran (se pierden); la forma `ventana` modela 17–01 h pero no la segunda ventana de 9 h "hasta nuevo aviso" de 2022; el calendario es independiente de la temperatura.

### Fase 7 — Estaciones del año y escenarios S0–S12
`correr_estaciones`, catálogo §7.7; pestañas **Estaciones del año** y **Comparar**. **Gate:** N12 · 4 estaciones × 4 réplicas ≤ 90 s (botón + caché).

### Fase 8 — Economía real
§7.9, anualización rotulada, conclusión por pregunta del CASO. **Gate:** el análisis reconcilia (ingresos − costos = margen; *venta perdida* no se resta) · textos por `escapar_pesos` · 22/22.

### Fase 9 — Sensibilidad
Tornado con **cada C1–C19 como eje**. **Gate:** lista **todos** los `supuesto`/`heredado`/`estimacion` y las alternativas; el ranking no es constante.

### Fase 10 — Verificación final y documentación
Todos los controles · QA visual completo (§10.4) · rendimiento. Reescribir `CLAUDE.md` (alcance, §2.3), `TASK.md`, `README.md` (guion de demo del caso real y respuestas al profesor: *¿por qué datos supuestos? ¿cómo se validó? ¿qué es "heredado"? ¿por qué 270.000 L?*), **corregir** `FASE2_IMPLEMENTACION.md`, `DATOS_OPERACIONALES…md` y `ONBOARDING…md` con §3 y §4. Los `.docx` no se tocan salvo pedido (describen el modelo viejo). **Gate:** D0–D11 completos.

**Orden recomendado:** F0 → **F1** → F2 → F3 → F4 → F5 → F6 → F7 → F8 → F9 → F10. Si hay que recortar: **mantener F0, F1, F2, F4, F5, F6**; recortar F9 (parcial) y 6b. (Prioridad del CASO: demanda y perfil, abastecimiento y red, GNC; personal y economía fina pueden quedar con supuestos marcados.)

---

## 10. Verificación

### 10.1 Caso degenerado y dorados
`ParametrosSimulacion.clasico()` = 1 grupo de 3 caras (1 por surtidor), 1 producto, tanque 40.000 L `(s=12.000, Q=20.000)`, plazo `Triangular(8,16,36)` h, playeros ilimitados, sin cola finita, sin red ni GNC, un tipo de vehículo `litros = Triangular(15,30,60)`, carga `Triangular(3,5,8)`, `modo = monte_carlo` con la tabla heredada, `dias_calentamiento = 1`. Debe dar **idénticos** (6 decimales) los valores de §14.1. Si no, se rompió el orden de sorteo de algún stream.

### 10.2 Controles nuevos (se suman a los 22)
| ID | Control |
|---|---|
| N1 | `clasico()` reproduce los dorados (semillas 1 y 2 + 4 escenarios × 4 réplicas) |
| N2 | **Conservación por grupo y motivo:** llegadas = atendidos + Σ perdidos(motivo) + migrados no atendidos + los que quedaron adentro |
| N3 | **Conservación por producto:** litros por tanque; **m³ del GNC**; ningún tanque negativo ni sobre capacidad |
| N4 | **Little** por grupo |
| N5 | Simultáneos en servicio en A/B ≤ playeros del turno y ≤ caras |
| N6 | Red: 221,8 km / ≈ 190 min; con RN 143 cortada 399,8 km (+178 km, +153 min); Dock Sud 991,3 km < 1.279,0 km |
| N7 | Sin episodios ⇒ cero pérdidas `corte_gnc`; con corte total sin migración ⇒ **todos** los GNC del episodio se pierden |
| N8 | Con migración: `migrados + perdidos_corte = afectados` |
| N9 | Mezcla de producto **en litros** simulada ≈ DEM-04 (< 1,5 pp con ≥ 30.000 llegadas) y **clientes GNC ≈ 3 %** |
| N10 | Media muestral de litros: auto ≈ 23,5 L (±2 %); pick-up ≈ 40 L |
| N11 | Monotonía: plazo con cortes ≥ sin cortes · más playeros ⇒ menos espera · más demanda ⇒ más espera |
| N12 | Estaciones: invierno con episodios ⇒ más `migrados` que verano |
| N13 | *(opcional)* **M/M/c** (Erlang C) con servicio exponencial, λ constante, sin abandono |
| N14 | **Cero huérfanos:** todo campo de los parámetros tiene `Dato` en el Registro |
| N15 | **Tema:** ningún hex fuera de `ui/tema.py`; contraste WCAG ≥ 4,5:1 en los pares declarados; los 5 `PRODUCTO` distinguibles |
| **N16** | **Unidades de la demanda:** `litros_mes = 270.000` ⇒ litros vendidos + no vendidos simulados = **270.000 ± 3 %** por mes (**habría detectado B1**) |
| **N17** | **Calendario:** el horizonte "estación" de invierno usa jun–ago; "mes" de julio usa el índice de julio; día de la semana correcto |
| **N18** | **Normalización fin de semana:** los litros del mes no cambian al variar `factor_fin_de_semana` (§14.4) |
| **N19** | **Cadena de demanda:** `clientes_día × litros_medios_por_cliente = litros_día` (±0,1 %) |

### 10.3 Color
`contraste(hex1, hex2)` (luminancia relativa WCAG). Pares: `TINTA/AMARILLO`, `TINTA/FONDO`, `TINTA/FONDO_PANEL`, `AMARILLO/ASFALTO`, `FONDO/ROJO`. Si está disponible la skill `dataviz`, usarla para validar la paleta categórica.

### 10.4 QA visual (no alcanza con "corre")
Con Playwright/Chromium (cloud: `/opt/pw-browsers/chromium`; **no** ejecutar `playwright install`; si falta el paquete, `pip install playwright` con `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`):
1. `python -m streamlit run app.py --server.headless true --server.port 8501`.
2. Capturar cada pestaña y sub-pestaña a 1440×900 y 390×844, y la **animación** en 3 instantes (madrugada, pico, corte de GNC).
3. Revisar: paleta coherente, sin texto amarillo sobre blanco, sin desbordes, insignias presentes, **sin errores en la consola ni en el log**. Adjuntar capturas. Si no hay navegador, **decirlo** (no declarar "verificado visualmente").

### 10.5 Rendimiento
Réplica ≤ 1,5 s · barrido y sensibilidad detrás de botón con estimación de tiempo · todo con `st.cache_data` · **no multiprocessing** · año = 1 corrida por escenario (B7).

---

## 11. Trampas conocidas

1. **`st.html` descarta el SVG** → `st.components.v1.html`. 2. Dos `$` en una línea de Markdown ⇒ LaTeX → **`escapar_pesos`**. 3. No se escribe en `st.session_state` de un widget ya creado → patrón `politica_sugerida` en `leer_parametros()`. 4. La conclusión se arma **antes** de las pestañas → `st.rerun()` tras barridos. 5. Cambió la **firma** de un módulo ⇒ **reiniciar el servidor**; mantener `fileWatcherType = "poll"`. 6. **Streams nuevos sólo al final** de `STREAMS`; un stream por fuente de azar. 7. Atributos sorteados **al llegar**; el migrado conserva su identidad. 8. Combustible se descuenta **al empezar a cargar**, por producto. 9. `Escenario` con **cambios declarativos**, no lambdas (pickle de `st.cache_data`). 10. **Litros ≠ m³ ≠ autos.** 11. JSON de la animación < ~3 MB (columnar + `round()`). 12. **Calentamiento ≥ 2 días** (tanques al 75 %, plazo de 36 h). 13. Cambio de turno: no se expulsa a quien está en servicio (la capacidad se ajusta al liberarse; verificar en N5). 14. Fechas: usar la **de la nota original**. 15. **Rojo de marca = rojo de pérdida** (§8.1-2). 16. **No repetir B1:** cualquier tasa "por día" se deriva de **litros**, nunca de dividir litros por 30 y llamarlo "autos". 17. Un valor "Alta" de un documento compilado **no es evidencia** (§0-5).

---

## 12. Relevamiento y datos que el código no puede inventar

La app debe tener lugar para cargarlos (§8.4) y avisar mientras falten. **Orden de impacto** (cada fila cita el conflicto que cierra):

| Prioridad | Falta | Cómo se obtiene | Cierra |
|---|---|---|---|
| 1 | **Demanda real**: litros/mes por producto (última facturación), clientes por franja de 15 min, hábil vs. fin de semana | **Conteo en la estación** (un día hábil + uno de fin de semana) + encargado; serie mensual de la SE | **C2, C3, C7, C16, C17** |
| 2 | **Litros por carga y tiempo en la cara**, por producto y tipo | Cronometrar 5–10 vehículos por producto | **C11, C12** |
| 3 | **Dotación por turno** (playeros, cajeros, encargado), horario real de la playa **y del shop**, ¿autoservicio? | Encargado | **C1, C5, C15** |
| 4 | **Abastecimiento**: origen, frecuencia, litros, plazo, tamaño de cada tanque | Encargado | INV-01..05 |
| 5 | **GNC**: tipo de contrato (firme/interrumpible), compresores, tiempo de carga, cortes de los últimos inviernos, migración a nafta | Encargado, AMENA, Ecogas | **C8, C9** |
| 6 | **Mix diésel G2/G3** y si S3 vende los dos | Ver el surtidor + encargado | **C6** |
| 7 | **% de clientes que entran al shop** y nombre/horario del shop | Contar 50–100 clientes | **C4, C14** |
| 8 | **Estacionalidad real** (ventas mensuales por provincia/localidad) | SE (datos abiertos), DEIE Mendoza | **C10** |
| 9 | **Economía**: márgenes, flete por km, salarios vigentes (convenio SOESGyP) | CECHA/FECRA, transportistas, convenio | C18, ECO-* |

**Checklist para el encargado (una sola visita):** litros/mes actual · playeros/cajeros/encargado por turno · horario de playa y shop · ¿hay G3/V-Power Diesel en S3? · % que entra al shop y nombre · ¿GNC firme o interrumpible?, ¿cuántos compresores?, ¿cortes el último invierno? · día/frecuencia/litros de las entregas y de dónde sale · tamaño de cada tanque. **Anotar siempre fecha, hora y clima.**

---

## 13. Formato de reporte al cerrar cada fase
```
FASE N — <título>            [CERRADA | BLOQUEADA]
Archivos tocados: ...
Compuerta:  verificar.py → X/Y OK · N1 dorados → OK/FALLA · N14/N15/N16.. → ...
Visual:     capturas adjuntas: <lista>  (o: "sin navegador disponible")
Defaults usados de §6 y §4.2: V.., N.., C..   (detrás de qué parámetro)
Supuestos NUEVOS al Registro: ID — valor — por qué
Contradicciones nuevas halladas: ...
Decisiones que necesitan al usuario: ...
Riesgos / deuda: ...
Commit: <hash> en claude/simulator-graphic-orchestrator-wu2xh4
```

---

## 14. Apéndices

### 14.1 Números dorados (código original = código mergeado con `modo_determinista=False`; medidos el 5/10/2026)
```python
from sim.config import ParametrosSimulacion
from sim.runner import correr_replica, correr_escenarios
p = ParametrosSimulacion()
for s in (1, 2): r, _ = correr_replica(p, semilla=s)
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

Escenarios (4 réplicas, semilla base 1): `espera_pico / atendidos_dia / litros_vendidos_dia` → Base **3.249536 / 346.465517 / 12140.09** · A **0.844787 / 348.327586 / 12207.652** · B (= Base: números aleatorios comunes) **3.249536 / 346.465517 / 12140.09** · C (= A) **0.844787 / 348.327586 / 12207.652**. Analíticos: `rho_pico` 0,8761 · `rho_pico_dia_malo` 1,0708 · `rho_cajas` 0,5175 · 360 autos/día · 12.600 L/día ⇒ **378.000 L/mes** (hipotético heredado).

### 14.2 Cadena de demanda: litros/mes → clientes/día (calibración por defecto)
Reproducible con `sim/` o con un script de 20 líneas; **N19 la verifica**.
1. **Carga media por producto** (§5-D, matriz tipo-por-producto × media de cada tipo): Súper **21,4 L**, V-Power **26,0**, G2 **64,2**, G3 **81,5**.
2. **Litros por producto** (DEM-04, normalizados a los 4 líquidos): 28,0 / 19,5 / 29,3 / 23,2 %.
3. **Peso de llegada** = `% litros ÷ carga media` ⇒ clientes líquidos: Súper **46,8 %**, V-Power **26,8 %**, G2 **16,3 %**, G3 **10,1 %**.
4. **Litros medios por cliente líquido** = **35,7 L**.
5. **Clientes líquidos/día** = `litros_día ÷ 35,7`; **+ GNC** al 3 % de las llegadas (÷ 0,97).

| `litros_mes` | L/día | clientes líquidos/día | con GNC (3 %) |
|---|---|---|---|
| 150.000 | 5.000 | 140 | 144 |
| **270.000** | **9.000** | **252** | **260** |
| 400.000 | 13.333 | 374 | 385 |

Con el perfil de §14.3 (pico 3,5/43 = **8,1 %** de las llegadas en una hora) y 260 clientes/día: **λ_pico = 0,353 clientes/min (≈ 21/h)**. ρ_pico de los grupos A+B con tiempo medio 5 min y 97 % de las llegadas: **1 playero ⇒ 1,71 · 2 playeros ⇒ 0,86 · 3 playeros ⇒ 0,57**. *Con la mezcla y los defaults de C12 (carga ≈ 0,5·T), la dotación de 2 playeros en el pico queda **al límite**: esa es la conclusión que el simulador debe poder mostrar y defender, y depende de C5, C11 y C12.* (Con el preset **alto** —carga casi llena, media 0,8·T— los clientes bajan a ≈ 158/día y ρ_pico a ≈ 0,54; con el **bajo** —media 0,3·T— suben a ≈ 420/día y ρ_pico a ≈ 1,43: **C12 mueve la conclusión de "sobra" a "se satura"**.)

### 14.3 Perfil horario adoptado (`DATOS §2`; 24 factores; suma 43)
`00–05: 1,0 · 06: 1,5 · 07–09: 3,5 · 10–11: 2,0 · 12–13: 1,5 · 14–15: 1,5 · 16–17: 3,0 · 18–19: 2,0 · 20–21: 1,5 · 22–23: 1,0`. Picos 07–10 y 16–18 (los dos de `DO`, ≈ 3–4× el promedio). Perfil heredado (alternativa): `0,30 0,20 0,15 0,15 0,25 0,60 1,10 1,80 2,00 1,50 1,10 1,00 1,20 1,10 0,90 0,90 1,00 1,40 1,90 2,00 1,60 1,10 0,70 0,40`.

### 14.4 Normalización del tipo de día
Con `f` = factor de fin de semana y un mes de `n_h` días hábiles y `n_f` de fin de semana, el nivel diario hábil es `D_h = D·(n_h + n_f) / (n_h + f·n_f)` y el de fin de semana `D_f = f·D_h`, de modo que **la suma del mes = `D × días`** (con `D = litros_mes / días`). Ej.: 22 + 8 días y `f = 1,30` ⇒ `D_h = 0,926·D`, `D_f = 1,204·D`. Aplicar lo mismo con la estacionalidad (índice ÷ media de los 12 índices).

### 14.5 Fuentes principales (consultadas el 5/10/2026; URLs y detalle en las notas y en `DATOS_OPERACIONALES`)
- **Verificadas en el original** (notas 01/03/06): Shell (API oficial), Secretaría de Energía, Sitio Andino, Los Andes, MDZ, El Sol, El Economista, Infonegocios, Autocosmos, Ley 24.449, OSRM/OSM.
- **Hoy:** ENARGAS abr-2026 (cortes de GNC a estaciones interrumpibles; Canal 26, Ámbito, La Gaceta, A24); punto de equilibrio 315.000–400.000 L/mes (resultado de búsqueda sobre CREEBBA/surtidores); paleta Shell ([brandpalettes.com](https://brandpalettes.com/shell-logo-colors/), los hex difieren).
- **No verificadas por mí** (aparecen en `DATOS`/`ONBOARDING`): FECRA salarios (URL "enero-2026"), Decreto 46/2025 y Res. 147/2025, Mercuria 1/9/2026, CREEBBA 270k, YPF 300k clientes × 20 %, Res. ENARGAS 409/2026, tiempos UNLP/UTN/UNC, mix de Surtidores.com.ar ago-2026.
- Material de cátedra: TP 5 de redes (flujo máximo, camino más corto, árbol de expansión mínima, transbordo), TP de Monte Carlo, apuntes de colas.

*Fin del orquestador v2. Si algo de acá no se puede cumplir, no lo recortes en silencio: dejalo escrito en el reporte de la fase.*
