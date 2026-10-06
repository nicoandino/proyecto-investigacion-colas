# CLAUDE.md — Simulador de la Shell de San Rafael

> **Versión final (6/10/2026, Fase 10).** Reemplaza al `CLAUDE.md` de la Fase 2, que tenía afirmaciones
> falsas ("datos únicamente de fuentes verificadas", "la fórmula es exacta", "no hacen falta réplicas").
> Si este archivo discrepa de `ORQUESTADOR_SIMULADOR.md`, **manda el orquestador**.

## Qué es esto

Simulador de **eventos discretos** (Python + SimPy + Streamlit + Plotly), hecho a medida para el TP de
**Investigación Operativa** (4º año), de **una estación real**: la **Shell de Av. Balloffet 1810 esq.
Av. Los Sauces, San Rafael, Mendoza**. Grupo Andino–Assenza. No usamos Simul8: el motor es propio.

El producto del TP es un **informe del caso**; el simulador ilustra escenarios. Tiene que ser
**defendible**: cada dato se muestra con su fuente, su nivel y su confianza, y **casi todos son
estimaciones o supuestos** porque no hay datos de la propia estación (se dice en la app).

Consigna del profesor: *"cualquier tema, que corra en algún software, con alguna complejidad,
preferiblemente aspectos económicos. Colas, transporte, Montecarlo, etc."*

| Unidad de la materia | Dónde aparece |
|---|---|
| **Colas** | 3 zonas de caras (nafta, diésel, GNC) con playeros por turno, cola finita, abandono, caja del minimarket; Wq, Lq, ρ, Little |
| **Monte Carlo** | Producto y tipo de vehículo de cada cliente (5 pasos, tablas visibles); variación día a día opcional |
| **Inventario / transporte / redes** | Un tanque por producto líquido con política (s, Q); camión desde Dock Sud o Luján por una red con cortes de ruta (Dijkstra) |

### Las preguntas que responde (todo en pesos por mes)
1. ¿Alcanza la dotación de playeros en el pico? ¿Conviene un playero más, o más stock? (S2, S6, S9)
2. ¿Cuál es la mejor política de reposición de cada tanque, con camión desde Dock Sud y rutas que se cortan? (S4, S5, S7)
3. ¿Cuánto se pierde cuando se corta el GNC en invierno y adónde va esa demanda? (S3)
4. ¿Qué dato incierto mueve más la conclusión, y por lo tanto hay que relevar primero? (tornado)

## Estado

**Fases 0–10 del orquestador cerradas.** `python verificar.py` → **100/100 OK** (los 22 controles originales
+ los N1–N19 del orquestador y los de cada fase). Detalle y deuda: `ORQUESTADOR_SIMULADOR.md` §9 y `TASK.md`.

## Reglas de oro (no romper)

1. **`ParametrosSimulacion.clasico()` reproduce los números dorados** del orquestador §14.1 (control N1).
   Es el caso degenerado (3 surtidores, 1 producto, 1 tanque): demuestra que el motor nuevo no rompió el viejo.
2. **Streams RNG nuevos sólo AL FINAL de `STREAMS`**; nunca reordenar ni reutilizar uno (rompe los dorados y los números aleatorios comunes).
3. **Ningún número sin pasar por el Registro** (`sim/datos.py`): valor, unidad, fuente, nivel, tipo, confianza, alternativas. Todo campo de los parámetros tiene su `Dato` (control N14).
4. **Litros ≠ m³ ≠ autos.** Los clientes por día se **derivan** de litros/mes ÷ litros medios por cliente; nunca "litros ÷ 30 = autos". El GNC se mide en m³.
5. `sim/` **nunca** importa `streamlit` ni `ui/`; **sin `print()` en `sim/`**.
6. **Ningún hex de color fuera de `ui/tema.py`** (control N15). Amarillo nunca como texto sobre blanco. Sin logo de Shell.
7. Si cambia la **firma** de un módulo, **reiniciar Streamlit** (recarga `app.py` pero conserva el módulo viejo). `fileWatcherType = "poll"` en `.streamlit/config.toml` **no se quita**.
8. `Escenario` guarda **cambios declarativos** `((campo, valor), …)`, no lambdas (`st.cache_data` los serializa con pickle).
9. Un commit por fase, en castellano. **Sin Pull Request** salvo que lo pidan.

## Alcance — qué NO se hace (no es escalable a propósito)

Base de datos, login, API REST, Docker, plugins, capas "para el futuro", **multiprocessing**,
lavadero, camiones como clientes masivos, horas extra/ausentismo. (Se superó la vieja prohibición de
"varios combustibles" y "GNC": hoy están **dentro** del alcance.)

## Stack

Python 3.14 · **SimPy 4** · NumPy/pandas · **Streamlit** · **Plotly** · animación en **JavaScript/SVG** dibujada por el navegador.
Entorno virtual en `.venv/`.

## Estructura

```
app.py                  Streamlit (única entrada): 14 pestañas
verificar.py            100 controles (correr antes de commitear)
sim/                    MOTOR — Python puro, sin Streamlit
  datos.py              REGISTRO de datos (108 filas) + MAPA_PARAMETROS (N14) + contradicciones C1–C20
  config.py             dataclasses frozen: parámetros, grupos, productos, red, GNC, economía, calendario
  distribuciones.py     RNG con semilla, un stream por fuente de azar, muestreo empírico
  modelo.py             procesos SimPy: llegadas, "producto primero", playeros por turno, caras, GNC, tanques, camión
  estadisticas.py       colectores (por cliente, temporales, por hora, por grupo y producto)
  traza.py              cuadros de animación y series
  runner.py             réplicas, IC 95 % (t de Student), barrido de políticas por producto
  red.py                Dijkstra (heapq), cortes E1–E4, demora → plazo
  gnc.py                episodios de corte invernales (calendario)
  escenarios.py         estaciones del año y catálogo S0–S12, diferencias pareadas
  economia.py           análisis económico del caso clásico y del barrido de políticas
  economia_real.py      estado de resultados mensual, personal, flete, año estimado, decisión en $/mes
  sensibilidad.py       tornado: 26 ejes, 56 variantes, listado de todos los datos inciertos
ui/                     PRESENTACIÓN
  tema.py               paleta Shell (única fuente de colores), plantilla Plotly, CSS
  animacion.py          reproductor del playón (columnar → SVG en el navegador)
  graficos*.py          figuras Plotly (colas/inventario, red, GNC, escenarios y tornado)
  datos_ui.py           insignias, tabla del Registro, CSV, esquema de la estación
  textos.py             etiquetas, ayudas y textos largos
reports/                scripts de QA con Playwright + capturas por fase
research_notes/         notas de investigación verificadas
```

## El modelo en una pantalla

- **Demanda:** `litros_mes` (270.000) ÷ días del mes × estacionalidad (neutra por defecto) × tipo de día (fin de semana ×1,30, **normalizado** para conservar los litros del mes) ÷ litros medios por cliente (35,7 L) ⇒ ≈ 252 clientes líquidos/día + 3 % de clientes GNC. Llegadas Poisson no homogéneas con el perfil horario (picos 07–10 y 16–18).
- **Cliente "producto primero":** se sortea producto (Súper, V-Power, Diésel G2, G3, GNC) y tipo de vehículo; litros ~ `Triangular(0,2·T ; 0,3·T ; 1,0·T)`. Todo se sortea **al llegar**.
- **Playón:** zona A nafta (4 caras), B diésel (2), C GNC (6). Servidores = `mín(caras libres, playeros en turno)` (playeros 1·2·2). Cola finita por zona, paciencia, caja del minimarket (20 % entra).
- **GNC:** 3 compresores limitan las cargas simultáneas; en jun–ago hay episodios de **corte total** (contrato interrumpible); el cliente pasa a Súper (30 %) o se pierde.
- **Inventario:** un tanque por líquido, política (s, Q) por producto, un camión independiente por producto; plazo = base `Triangular(24,36,48)` h + demora por corte de ruta.
- **Pérdidas con motivo fijo:** `sin_combustible` · `abandono_espera` · `cola_llena` · `corte_gnc` · `abandono_caja`; los migrados a nafta se cuentan aparte.

## Rigor estadístico

- **Calentamiento de 2 días** (el tanque arranca al 75 %): se simula y no se mide.
- **Réplicas independientes** con semillas distintas; **promedio ± IC 95 %** (t de Student, tabla en `runner.py`).
- **Números aleatorios comunes** entre escenarios; las comparaciones usan la **diferencia pareada** réplica a réplica (IC mucho más angosto).
- **Promedios temporales** (área/tiempo) para colas, utilización y niveles.
- Controles de `verificar.py`: ley de Little, conservación de clientes (por grupo y motivo) y de litros (por producto), unidades de la demanda (N16), calendario (N17), normalización (N18), monotonías (N11), Dijkstra = enumeración de caminos, ingresos − costos = margen, etc.

## Cómo correrlo

```bash
.venv/Scripts/streamlit run app.py          # la aplicación (http://localhost:8501)
.venv/Scripts/python verificar.py           # 100 controles (≈ 2 min); debe terminar en "Todos los controles pasaron"
```

En Windows con salida a un archivo: `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`.

## Rendimiento (medido el 6/10/2026)

Una réplica de un mes ≈ 0,4 s · de un año ≈ 5 s · 4 estaciones × 4 réplicas ≈ 7 s · catálogo S0–S12 (19 escenarios × 4 réplicas) ≈ 34 s · tornado con 2 réplicas ≈ 40 s. Todo lo pesado va detrás de un botón y con `st.cache_data`. **No** meter multiprocessing.

## Decisiones de arquitectura (y por qué)

1. **La animación se dibuja en JavaScript**, no en Python: Python manda JSON columnar y el navegador dibuja el SVG (`st.components.v1.html`; `st.html` descarta el SVG).
2. **Los importes se escapan** antes de pasarlos a Markdown (`escapar_pesos`): dos `$` en una línea se leen como LaTeX.
3. **No se escribe en `st.session_state` de un widget ya creado:** "Usar esta política" guarda la sugerencia en otra clave y se aplica al principio de `leer_parametros()`.
4. **La conclusión se arma antes de las pestañas:** tras un barrido hay que llamar a `st.rerun()`.
5. **El combustible se descuenta al EMPEZAR a cargar**, del tanque de su producto (si no, varios autos pasan el control de stock a la vez y sacan más de lo que hay).
6. **Un stream de plazo y de corte de ruta por producto:** si no, el sorteo de un tanque dependía de cuántos pedidos hizo otro y no se podían medir las políticas por separado.
7. **La venta perdida es un costo de oportunidad:** se informa aparte y no se resta del margen.
8. **Todo corre por réplica y recién después se promedia** (también la economía), para tener IC y diferencias pareadas.

## Documentos

| Archivo | Para qué |
|---|---|
| `ORQUESTADOR_SIMULADOR.md` | **Especificación completa**, fases, compuertas, controles y cierre de cada fase (§9) |
| `ONBOARDING_PARA_AGENTES.md` | Arranque rápido para un agente nuevo |
| `README.md` | Cómo correrlo, guion de demo y respuestas al profesor |
| `TASK.md` | Qué está hecho y qué falta |
| `CASO_SHELL_SAN_RAFAEL.md` | Contexto del caso y plan de investigación |
| `DATOS_OPERACIONALES_…md` | Compilado de datos **con errores corregidos en la Fe de erratas inicial**; el valor adoptado de cada dato está en el Registro |
| `FASE2_IMPLEMENTACION.md` | Historia de la Fase 2 (superada; trae su corrección) |
