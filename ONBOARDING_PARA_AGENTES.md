# 🚀 Onboarding para agentes — Simulador de la Shell de San Rafael (v2)

> **Leé esto primero (5 minutos).** Después leé `ORQUESTADOR_SIMULADOR.md`, que es la especificación completa.
> **Versión:** v2.0 · **5/10/2026** · Reemplaza a la v1, que tenía errores (listados en §3). **Si este archivo y otro documento se contradicen, mandan este archivo y el orquestador.**

---

## 1. En 30 segundos

Simulador de **eventos discretos** (Python + SimPy + Streamlit + Plotly) de **una estación Shell real**: **Av. Balloffet 1810 esq. Av. Los Sauces, San Rafael, Mendoza** (operador LOS SAUCES S.R.L.). Es el TP de **Investigación Operativa** (colas + Monte Carlo + inventario/redes).

- **Producto del TP:** un **informe del caso**. El simulador ilustra escenarios; tiene que ser **completo, defendible y mostrar cada dato con su fuente**.
- **Preguntas que responde:** (1) ¿alcanza la dotación de playeros en el pico? ¿conviene agregar capacidad? (2) ¿cuál es la mejor política de reposición de combustible, con camión desde Dock Sud y rutas que se cortan con nieve? (3) ¿cuánto se pierde cuando se corta el GNC en invierno y adónde va esa demanda? Todo en **pesos por mes**.
- **Estética:** paleta **Shell** (amarillo `#FBCE07`, rojo `#DD1D21`; los hex difieren según la fuente). **Sin logo.**

---

## 2. Estado real (verificado el 5/10/2026)

| Cosa | Estado | Detalle |
|---|---|---|
| Motor DES (colas, abandono, tanque (s,Q), camión) | ✅ **Anda** | `python verificar.py` → **22/22 OK** |
| UI Streamlit + animación SVG | ✅ **Anda** | la app levanta (`/_stcore/health` = 200) |
| Con `modo_determinista = False` (default) | ✅ | números **idénticos** al proyecto original (dorados en `ORQUESTADOR §14.1`) |
| **Modo "determinista" de Fase 2** | ❌ **Incorrecto** | trata **litros como autos** (120.000 L/mes ⇒ 4.000 autos/día ⇒ **4,2 M L/mes**), siempre simula **enero**, y no es determinista de verdad (`ORQUESTADOR §3`) |
| Estación real (12 caras, 3 grupos, playeros, 5 productos, GNC, red) | ⏳ **No existe todavía** | el motor sigue siendo "3 surtidores + 1 caja + 1 tanque" |
| Registro de datos con fuente y paleta Shell | ⏳ **No existe todavía** | |
| Datos operacionales | ⚠️ **Hay, pero con contradicciones** | 20 conflictos catalogados en `ORQUESTADOR §4.2`, con el valor adoptado |
| Datos **de la propia estación** | ❌ **Ninguno** | todo es estimación/supuesto hasta el relevamiento |

**Lo que hay que hacer:** corregir Fase 2 (Fase 0 del orquestador) y construir el resto por fases con compuertas. **No empieces por el rediseño: empezá por la Fase 0.**

---

## 3. ⚠️ Errores conocidos en los documentos que vas a leer

No te creas estos puntos aunque estén escritos con aplomo:

1. **"270k L/mes = ~9.000 autos/día"** (v1 de este archivo) y **"100–150k L/mes = 3.300–5.000 autos/día"** (`DATOS_OPERACIONALES §1`): son **litros por día**, no autos. Con ~36 L por cliente, 270.000 L/mes son **≈ 250 clientes/día**. Si ponés 9.000 autos/día, el simulador colapsa (ρ_pico ≈ 22).
2. **"El modelo determinista no necesita réplicas ni calentamiento"** (`FASE2`, `CLAUDE.md`): **falso.** Llegadas Poisson y tiempos aleatorios siguen ahí; el tanque arranca al 75 %. Réplicas, IC 95 % y calentamiento (2 días) **se mantienen**.
3. **"Datos únicamente de fuentes verificadas"** (`CLAUDE.md`): **no.** Las etiquetas "Alta" de `DATOS_OPERACIONALES` **sobreestiman** la confianza (p. ej. "tanque de camión 300 L: Alta", sin dato argentino). Aplicá la **jerarquía de evidencia** (`ORQUESTADOR §4.1`).
4. **"Horario 06–22, NO 24 h"** (`DATOS §5`): lo contradice la API oficial de Shell (`twenty_four_hour`) y los propios turnos nocturnos del documento. Default: **24 h**.
5. **"2–3 playeros por turno, 21 personas"** (v1 de este archivo): `DATOS §4` dice **5 personas por turno = encargado 1 + playeros 2 + cajero 1 + tienda 1** (noche: 2 personas). Playeros adoptados: **1 · 2 · 2** (noche · mañana · tarde).
6. **El código no tiene** un widget `playeros`, ni GNC, ni mix de diésel, ni "restricción −50 % en invierno" (la v1 lo insinuaba). **"−50 %" no tiene fuente**; el corte documentado es **total** (ENARGAS, estaciones con contrato interrumpible).

Más detalle, y el resto de las contradicciones, en `ORQUESTADOR §3` y `§4.2`.

---

## 4. Qué archivo manda (y mapa del repo)

**Orden de autoridad:** `ORQUESTADOR_SIMULADOR.md` > este archivo > `CASO_SHELL_SAN_RAFAEL.md` (contexto y plan de investigación) > `research_notes/…` (datos verificados, por parámetro) > `DATOS_OPERACIONALES_…md` (útil pero con errores) > `CLAUDE.md` / `TASK.md` / `FASE2_IMPLEMENTACION.md` (**desactualizados**, ver §3).

```
proyecto-investigacion-colas/
├── ORQUESTADOR_SIMULADOR.md        # ★ especificación completa + fases + compuertas
├── ONBOARDING_PARA_AGENTES.md      # ESTE archivo
├── CASO_SHELL_SAN_RAFAEL.md        # contexto del caso, V1–V13, plan de investigación
├── DATOS_OPERACIONALES_…md         # compilado de 8 áreas (con contradicciones: ORQUESTADOR §4.2)
├── research_notes/…/               # 01 identidad · 03 vehículos/litros/tiempos · 06 logística/rutas (verificadas)
│                                   #   (faltan 02, 04, 05: no asumir su contenido)
├── app.py                          # Streamlit (única entrada)
├── verificar.py                    # 22 controles del motor
├── sim/                            # MOTOR: Python puro, sin Streamlit
│   ├── config.py · distribuciones.py · modelo.py · estadisticas.py
│   └── economia.py · runner.py · traza.py
├── ui/                             # PRESENTACIÓN: animacion.py (SVG en JS) · graficos.py (Plotly) · textos.py
└── .streamlit/config.toml          # fileWatcherType = "poll" (NO quitar)
```
Se **van a agregar**: `sim/datos.py` (Registro), `sim/red.py` (Dijkstra), `sim/sensibilidad.py`, `ui/tema.py` (paleta única), `ui/datos_ui.py`.

**Ramas:** `main` (original) · `main-7ss6h3` (Fase 2) · **`claude/simulator-graphic-orchestrator-wu2xh4` = rama de trabajo** (incluye todo lo anterior mergeado). **No crear Pull Request** salvo pedido del usuario.

---

## 5. Los 14 números que tenés que saber (valores adoptados)

| Qué | Valor adoptado | Conflicto / confianza |
|---|---|---|
| Surtidores | 6 de doble cara = **12 caras**: A nafta 4 · B diésel 2 · C GNC 6 | grupo; V3 abierta |
| Horario | **24 h** | C1 |
| Demanda | **270.000 L/mes** ⇒ 9.000 L/día ⇒ **≈ 252 clientes líquidos/día** (+ GNC 3 %) | **C2/C3 🔴**; estimación, baja-media |
| Perfil horario | picos **07–10 h** y **16–18 h** (factor 3,5 y 3,0 vs. 1,0 de madrugada) | C16 |
| Fin de semana | ×1,30 (normalizado al mes) | C17 |
| Estacionalidad | **neutra** por defecto (hay presets) | C10 |
| Mezcla en litros | Súper 28 · V-Power 19,5 · G2 29,3 · G3 23,2 % | C6, C7 |
| Carga por vehículo | `Triangular(0,2 ; 0,3 ; 1,0) × tanque` (media 0,5·T): auto 47 L, pick-up 80 L, moto 3,7 L, camión 300 L (supuesto) | **C12 🔴** |
| Tiempo en la cara | nafta/diésel `Triangular(2,5,8)` min; GNC `(5,7,12)` | C11 |
| Playeros (noche · mañana · tarde) | **1 · 2 · 2**; 1 caja | **C5 🔴** (ρ_pico = 0,86 con 2) |
| Minimarket | entra el **20 %** | C4 |
| Plazo del camión | `Triangular(24,36,48)` h desde **Dock Sud** (991 km) | fuente: Shell Mendoza capital, 2023 |
| GNC en invierno | corte **total** por episodios (2 × 6 días jun–ago), contrato interrumpible, 3 compresores, 30 % migra a nafta | **C8/C9** |
| Economía | márgenes y flete **heredados sin fuente** (placeholders visibles); playero ≈ $1.680.000/mes | C18 |

---

## 6. Unidades y vocabulario (para no repetir el error de §3)

- **Tiempo:** minutos (el día = 1440). **Dinero:** pesos. **Volumen:** litros, **salvo el GNC, que es en m³**. **Nunca** sumes litros con m³ ni los llames "autos".
- **Litros/mes es la entrada de demanda; los clientes por día se derivan** (`ORQUESTADOR §14.2`).
- **Cara** = lado de un surtidor = una posición de carga = un vehículo a la vez. **Playero** = quien atiende (servicio atendido).
- **Réplica** = una corrida con otra semilla; se informa **promedio ± IC 95 %** (t de Student). **Números aleatorios comunes** = misma semilla entre escenarios.
- **Dato / estimación / observación / supuesto / heredado**: los cinco tipos del Registro. **Heredado** = del proyecto hipotético, sin fuente.
- **`[RESUMEN]`** = cifra vista sólo en el resumen de un buscador (no verificada). **`OK-orig`** = abierta y leída en el original.

---

## 7. Cómo correr (comandos probados)

```bash
cd proyecto-investigacion-colas
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt                         # simpy, streamlit>=1.40, plotly>=6, pandas, numpy

python verificar.py                                     # debe terminar con "Todos los controles pasaron" (22/22)
python -m streamlit run app.py --server.headless true --server.port 8501    # http://localhost:8501
python -m py_compile app.py sim/*.py ui/*.py            # chequeo de sintaxis
```
- Si cambiás la **firma** de un módulo de `sim/` o `ui/`, **reiniciá Streamlit**: recarga `app.py` pero conserva el módulo importado viejo.
- Para ver la app en un navegador headless (QA visual): `ORQUESTADOR §10.4`.
- Corrida de referencia (mismo resultado siempre): `correr_replica(ParametrosSimulacion(), semilla=1)` → `espera_pico = 3.609402`.

---

## 8. Primeros pasos (Fase 0)

1. `git checkout claude/simulator-graphic-orchestrator-wu2xh4` y verificá `python verificar.py` (22/22).
2. Guardá los **números dorados** (`ORQUESTADOR §14.1`) como control N1.
3. Corregí **B1, B2, B4, B5** (`ORQUESTADOR §3`): demanda desde **litros ÷ litros medios por cliente**, `fecha_inicio` real, "determinista" → "demanda esperada", calentamiento 2 días, **una** función `horizonte → (fecha_inicio, dias)`.
4. Pasá la compuerta de la Fase 0 (incluye **N16**: 270.000 L/mes ⇒ 270.000 ± 3 % simulados).
5. Reportá con el formato de `ORQUESTADOR §13` y esperá el OK antes de la Fase 2.

---

## 9. Cómo agregar una variable (proceso v2)

1. **Registrala** en `sim/datos.py` (`Dato` con valor, unidad, **fuente, tipo, confianza**, alternativas si hay conflicto).
2. Leé su **default desde el Registro** en `sim/config.py` (dataclass `frozen=True`, **tuplas**, no listas/dicts).
3. Usala en `sim/modelo.py` (si es aleatoria, con un **stream nuevo agregado AL FINAL** de `STREAMS`).
4. Mostrala en `app.py` con su **insignia** (`ui/datos_ui.py`) y en la pestaña **Datos y fuentes**.
5. Agregale un **control** en `verificar.py` y corré los 22 + los nuevos.
6. Si es `supuesto`/`heredado`/`estimacion`, definí `bajo`/`alto` para que entre en el **tornado**.

---

## 10. Qué NO hacer

- ❌ Inventar un número sin pasarlo por el Registro (regla de oro del caso).
- ❌ Usar una cifra "Alta" de un documento compilado como si fuera evidencia (§3-3).
- ❌ Dividir litros por 30 y llamarlo "autos" (§3-1).
- ❌ Reordenar `STREAMS` o reutilizar un stream (rompe los números aleatorios comunes y los dorados).
- ❌ `import streamlit` o `ui` dentro de `sim/`; `print()` en `sim/`.
- ❌ Base de datos, login, API REST, Docker, plugins, multiprocessing, lavadero.
- ❌ Hex de color fuera de `ui/tema.py`; amarillo como texto sobre blanco; el logo de Shell.
- ❌ Declarar "verificado visualmente" sin haber abierto la app en un navegador.
- ❌ Crear un Pull Request sin que lo pidan.

---

## 11. Preguntas frecuentes de agentes

**¿Por qué no usamos el modo determinista tal cual?** Porque está mal en unidades y en calendario (§3). Se conserva la idea (demanda esperada por día, con estacionalidad) pero **corregida**; el **Monte Carlo** se mantiene para el **tipo de cliente y el producto** (es una unidad de la materia).

**¿Cuál de dos datos que se contradicen uso?** El de mayor nivel en la jerarquía (`ORQUESTADOR §4.1`); el otro queda como **alternativa** y como eje del tornado. Está resuelto para los 20 conflictos conocidos en `§4.2`; si encontrás uno nuevo, agregalo ahí.

**¿Por qué 270.000 L/mes si la fuente dice 100–150k?** Porque las fuentes débiles convergen ahí (informe regional citado en la nota 03, promedio nacional de 270–380k, punto de equilibrio de una estación ≈ 315–400k) y 120k sólo se apoya en "San Rafael cayó 30 %". **No pude confirmar la cita "CREEBBA 270k"**: por eso es *estimación, confianza baja-media*, con **150k y 400k** como ejes de sensibilidad.

**¿Qué falta de verdad?** Datos **de la propia estación**: demanda, dotación, GNC, mix diésel, shop (`ORQUESTADOR §12`). Sin relevamiento, todo es estimación y la app lo dice.

**¿Y el relevamiento?** Una visita con el encargado + conteo de un día hábil y uno de fin de semana. Checklist en `ORQUESTADOR §12`. Lo que se cargue entra al Registro como `observacion` (🔵).

---

## 12. Mensaje de arranque

> *"Leé `ONBOARDING_PARA_AGENTES.md` y después `ORQUESTADOR_SIMULADOR.md` completo. Ejecutá la Fase 0 (corregir el código de Fase 2) y la Fase 1 (registro de datos + tema Shell). Pasá sus compuertas y reportame con el formato de §13. No avances a la Fase 2 sin mi OK."*

---
**Última actualización:** 5/10/2026 · **Grupo:** Andino–Assenza · **Próxima revisión:** después del relevamiento en la estación.
