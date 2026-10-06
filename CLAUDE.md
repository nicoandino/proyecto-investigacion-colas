# CLAUDE.md — Contexto del proyecto

Simulador de **eventos discretos** (Python + SimPy + Streamlit + Plotly) de **una estación real**: la **Shell de
Av. Balloffet 1810 esq. Av. Los Sauces, San Rafael, Mendoza**. Es el TP de **Investigación Operativa**
(4º año, grupo Andino–Assenza). Motor propio, no usamos Simul8. El producto del TP es un **informe del caso**;
el simulador sirve para mostrarlo y tiene que ser **defendible y verificable**.

Consigna del profesor: *"cualquier tema, que corra en algún software, con alguna complejidad, preferiblemente
aspectos económicos. Colas, transporte, Montecarlo, etc."*

## Los datos

- **Todos los números del modelo** están en el Registro (`sim/datos.py`) con valor, unidad, fuente, nivel, tipo
  y confianza. Su versión legible es **`DATOS_REALES.md`** (generado: `reports/generar_datos_reales.py`).
- **No hay mediciones de la propia estación.** Casi todo es estimación o supuesto de fuentes públicas, y la app
  lo tiene que decir. Los márgenes por litro, el flete y el costo de almacenamiento son **heredados sin fuente**
  (placeholders): los pesos muestran cómo se calcula, no cifras del negocio.
- Notas de investigación con citas y URL: `research_notes/`.
- La documentación vieja (orquestador de las fases 0–10, onboarding, TASK, README, el compilado de datos
  anterior) está en **`..\Contextoviejo\`** (fuera del repo). Los comentarios del código que dicen
  "ORQUESTADOR §x" apuntan a `Contextoviejo\ORQUESTADOR_SIMULADOR.md`.

## Qué modela hoy

- **Playón:** 12 caras en 3 zonas: A nafta (4), B diésel (2), C GNC (6); playeros por turno (1·2·2); cola finita;
  abandono; caja del minimarket.
- **Demanda:** litros/mes (270.000) ⇒ clientes/día (≈ 252) con perfil horario, fin de semana ×1,30 normalizado,
  estacionalidad neutra por defecto. Cada cliente: producto → tipo de vehículo → litros → ¿compra?
- **Inventario:** un tanque por líquido, política (s, Q) por producto, camión por producto (plazo 24–36–48 h)
  desde Dock Sud (991 km) o Luján por una red de rutas (Dijkstra) con cortes.
- **GNC:** 3 compresores; episodios de corte total en jun–ago; el cliente pasa a Súper (30 %) o se pierde.
- **Salidas:** indicadores con IC 95 %, 19 escenarios (S0–S12) con diferencias pareadas, estaciones del año,
  economía mensual, tornado de sensibilidad. `verificar.py`: **116 controles**.

## Reglas de oro (no romper)

1. **`ParametrosSimulacion.clasico()` reproduce los números dorados** del proyecto original (control N1).
2. **Streams RNG nuevos sólo al final de `STREAMS`**; nunca reordenar ni reutilizar uno.
3. **Ningún número fuera del Registro**; todo campo de los parámetros tiene su `Dato` (control N14).
4. **Litros ≠ m³ ≠ clientes.** Los clientes por día se derivan de litros/mes; el GNC va en m³.
5. `sim/` **nunca** importa `streamlit` ni `ui/`; **sin `print()` en `sim/`**.
6. **Ningún hex de color fuera de `ui/tema.py`** (control N15). Sin logo de Shell.
7. Si cambia la **firma** de un módulo, **reiniciar Streamlit**; `fileWatcherType = "poll"` no se quita.
8. `Escenario` guarda cambios declarativos (`((campo, valor), …)`), no lambdas.
9. Un commit por etapa, en castellano, en la rama `claude/simulator-graphic-orchestrator-wu2xh4`. **Sin Pull Request.**
10. **Antes de commitear:** `python verificar.py` (≈ 2 min) debe terminar en "Todos los controles pasaron".
11. No se escala: sin base de datos, login, API, Docker, plugins ni multiprocessing.

## Estructura

```
app.py            Streamlit (única entrada)
verificar.py      116 controles
sim/              MOTOR (sin Streamlit): datos · config · distribuciones · modelo · estadisticas · traza · runner
                  red · gnc · escenarios · economia · economia_real · sensibilidad
ui/               PRESENTACIÓN: tema · animacion (SVG en JS) · graficos* · datos_ui · textos
reports/          QA con Playwright (usa el Chrome instalado) y generar_datos_reales.py
research_notes/   notas de investigación verificadas
```

## Cómo correrlo

```bash
.venv/Scripts/streamlit run app.py        # http://localhost:8501
.venv/Scripts/python verificar.py         # 116 controles; en Windows: PYTHONIOENCODING=utf-8 PYTHONUTF8=1
```

Rendimiento medido: réplica de un mes ≈ 0,4 s · un año ≈ 5 s · catálogo de 19 escenarios × 4 réplicas ≈ 34 s.

## Decisiones técnicas que siguen valiendo

- La animación la **dibuja el navegador** (Python manda JSON columnar; `st.components.v1.html`, no `st.html`).
- Los importes se escapan antes de pasarlos a Markdown (`escapar_pesos`): dos `$` en una línea se leen como LaTeX.
- No se escribe en `st.session_state` de un widget ya creado.
- El combustible se descuenta **al empezar a cargar**, del tanque de su producto.
- Todo se calcula **por réplica** y recién después se promedia (IC 95 % y diferencias pareadas).
- La venta perdida es un costo de oportunidad: se informa aparte y no se resta del margen.

## Rediseño en curso

El usuario pidió rehacer el flujo de la app (menú inicial por tiempo, simulación de todos los días, modo "datos
reales" sin azar y modo "editar simulación", indicadores más claros, ajustes en un menú aparte). El plan por
etapas está en **`ORQUESTADOR.md`**.
