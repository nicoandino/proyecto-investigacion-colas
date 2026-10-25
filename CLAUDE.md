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
  lo tiene que decir. El margen de nafta y diésel es **$200/L, supuesto del grupo** (ECO-01, 25/10/2026); el del GNC,
  el flete y el almacenamiento son **heredados sin fuente** (placeholders). Los **precios** son los del cartel de la
  estación (ECO-08, foto del 25/10/2026): Súper, V-Power Nafta, Evolux Diesel (G2), V-Power Diesel (G3) y GNC.
- Notas de investigación con citas y URL: `research_notes/`.
- La documentación vieja (orquestador de las fases 0–10, onboarding, TASK, README, el compilado de datos
  anterior) está en **`..\Contextoviejo\`** (fuera del repo). Los comentarios del código que dicen
  "ORQUESTADOR §x" apuntan a `Contextoviejo\ORQUESTADOR_SIMULADOR.md`.

## Qué modela hoy

- **Playón:** 12 caras en 3 zonas: A nafta (4), B diésel (2), C GNC (6); playeros por turno (1·2·2); cola finita;
  abandono; caja del minimarket. **El GNC también lo carga un playero** (PER-04) y además usa un compresor.
- **Demanda:** litros/mes (270.000) ⇒ clientes/día (≈ 252) con perfil horario, fin de semana ×1,30 normalizado,
  estacionalidad neutra en `ParametrosSimulacion()`; en la app, por defecto, los **índices mensuales de la serie real**
  (PRO-01) y como opción el **calendario de temporadas** (DEM-14/15, supuesto). Cada cliente: producto → tipo de
  vehículo → litros → ¿compra?
- **Inventario:** un tanque por líquido, política (s, Q) por producto (en la app, por defecto la más conveniente:
  s = 2 y Q = 4,5 días de venta, INV-13), camión por producto (plazo 24–36–48 h)
  desde Dock Sud (991 km) por una red de rutas (Dijkstra) con cortes; orígenes alternativos Arroyo Seco y Luján
  (apagados por defecto; supuesto: la estación se abastece sólo de Dock Sud) con el plazo a la misma velocidad media
  (991 km ÷ 36 h). Quiebres y litros no vendidos por causa.
- **GNC:** 3 compresores; episodios de corte total en jun–ago (opción: más cortes en todo el invierno e invierno
  frío); el cliente pasa a Súper (30 %) o se pierde.
- **Salidas:** menú con ajustes (economía, GNC, calendario, abastecimiento) → resultados del período (sin azar) con
  avisos con pausa en la animación; **escenario único** (una semana); **Caso de informe** aparte (mejor política,
  S0–S12 con diferencias pareadas, tornado). `verificar.py`: **143 controles**.
- **Eventos aleatorios** (parte 4, `sim/eventos.py`): apagados por defecto; se sortean con semilla propia aunque el
  resto no tenga azar (personal, equipos, precio, abastecimiento, demanda).
- **Pronóstico** (parte 3, `sim/pronostico.py`): serie REAL de ventas al público de Shell en Mendoza (Secretaría de
  Energía, PRO-01, ene-2019 – ago-2026); índices mensuales como opción del calendario; punto de pedido con stock de
  seguridad (s = D·L + z·σ·√L) como opción y candidata de la búsqueda. **La pestaña** (23/10/2026, pedido de Nico)
  es como el ejercicio 1 del parcial: tres tablas Pronóstico | Real | error con MAE, MAPE y RMSE y su explicación —
  clientes por mes (recta A + B·t de la serie contra el año simulado), precio (inflación 2,4 % fija contra la sorteada
  entre 1,9 y 2,9 %, PRO-05) y ganancia bruta del combustible. Economía muestra el precio del litro mes a mes.
- **Colas** (`sim/colas.py`): M/M/1, M/M/s, Little y costos de la cátedra; en Indicadores → Colas y esperas, con λ, μ y
  s (playeros) de la simulación y la comparación con lo que midió.

## Reglas de oro (no romper)

1. **`ParametrosSimulacion.clasico()` reproduce los números dorados** del proyecto original (control N1).
2. **Streams RNG nuevos sólo al final de `STREAMS`**; nunca reordenar ni reutilizar uno.
3. **Ningún número fuera del Registro**; todo campo de los parámetros tiene su `Dato` (control N14).
4. **Litros ≠ m³ ≠ clientes.** Los clientes por día se derivan de litros/mes; el GNC va en m³.
5. `sim/` **nunca** importa `streamlit` ni `ui/`; **sin `print()` en `sim/`**.
6. **Ningún hex de color fuera de `ui/tema.py`** (control N15). El logo de Shell sólo aparece dentro de la foto de
   portada al 30 % (decisión de Nico, 14/10/2026), nunca como marca de la app; el aviso de "no afiliado" se mantiene.
7. Si cambia la **firma** de un módulo, **reiniciar Streamlit**; `fileWatcherType = "poll"` no se quita.
8. `Escenario` guarda cambios declarativos (`((campo, valor), …)`), no lambdas.
9. Un commit por etapa, en castellano, en la rama `claude/simulator-graphic-orchestrator-wu2xh4`. **Sin Pull Request.**
10. **Antes de commitear:** `python verificar.py` (≈ 5 min) debe terminar en "Todos los controles pasaron".
11. No se escala: sin base de datos, login, API, Docker, plugins ni multiprocessing.

## Estructura

```
app.py            Streamlit (única entrada; sin barra lateral ni modo clásico: `clasico()` vive sólo en `sim/` para N1)
verificar.py      143 controles
sim/              MOTOR (sin Streamlit): datos · config · distribuciones · modelo · estadisticas · traza · runner
                  red · colas · gnc · eventos · pronostico · escenarios · economia · economia_real · sensibilidad
ui/               PRESENTACIÓN: tema · animacion (SVG en JS) · graficos* · datos_ui · textos · vistas
static/fonts/     Archivo (woff2, SIL OFL) servida por Streamlit en app/static/
reports/          QA con Playwright (usa el Chrome instalado) y generar_datos_reales.py
research_notes/   notas de investigación verificadas
```

## Cómo correrlo

```bash
.venv/Scripts/streamlit run app.py        # http://localhost:8501
.venv/Scripts/python verificar.py         # 143 controles; en Windows: PYTHONIOENCODING=utf-8 PYTHONUTF8=1
```

Rendimiento medido: réplica de un mes ≈ 0,4 s · un año ≈ 5 s · catálogo de 19 escenarios × 4 réplicas ≈ 34 s ·
`verificar.py` completo ≈ 5 min (el control 46 corre 14 políticas en un año).

## Decisiones técnicas que siguen valiendo

- La animación la **dibuja el navegador** (Python manda JSON columnar; `st.components.v1.html`, no `st.html`).
- Los importes se escapan antes de pasarlos a Markdown (`escapar_pesos`): dos `$` en una línea se leen como LaTeX.
- No se escribe en `st.session_state` de un widget ya creado.
- El combustible se descuenta **al empezar a cargar**, del tanque de su producto.
- Todo se calcula **por réplica** y recién después se promedia (IC 95 % y diferencias pareadas).
- La venta perdida es un costo de oportunidad: se informa aparte y no se resta del margen.

## Estado (14/10/2026)

Todo el plan de `ORQUESTADOR.md` está hecho, incluida la **etapa 7 (Frontend, §29)**: tema oscuro "tótem de precios
nocturno" hecho con la skill impeccable (contexto en **`PRODUCT.md`**, sistema en **`DESIGN.md`**). Economía muestra cada
importe como **cantidad de la simulación (verificable) × precio del Registro (supuesto o heredado)**.

## Diseño (etapa 7)

- **Un solo tema, oscuro:** los colores viven en `ui/tema.py` (y se repiten en el `[theme]` de `.streamlit/config.toml`).
  Amarillo Shell = luz (franja, acción principal, pestaña activa); rojo Shell = sólo alerta (como texto, `ROJO_TEXTO`).
- **Tipografía Archivo** guardada en `static/fonts/` (`enableStaticServing = true` no se quita); cifras tabulares.
- **Sin emojis:** íconos `:material/…:` en Streamlit y SVG de trazo fino en los tableros en JavaScript.
- QA visual: `reports/qa_frontend.py` (capturas en `.impeccable/review/`).

## Rediseño y pulido

Rediseño del flujo (etapas 1–4) y pulido en tandas 0–9 (13/10/2026): el plan, las decisiones y el avance de cada
tanda están en **`ORQUESTADOR.md`** (§10–14). Las contradicciones entre fuentes se resolvieron con un criterio único
(`research_notes/…/07_decisiones_fuentes.md`); la app muestra sólo el valor elegido y una frase general.

**Parte 3 (14/10/2026, cerrada):** temas de la cátedra **Pronóstico** (serie real de ventas → estacionalidad y stock de
seguridad). Etapas P1–P4 y cierre en `ORQUESTADOR.md` §15–19. Sin dependencias nuevas: los métodos se programan como
en la cátedra. **Flujos en redes** (F1–F3: transporte, transbordo, flujo máximo, plan del período y "Despachar según
el plan") **se sacó el 23/10/2026** a pedido de Nico (§31); la red de rutas con Dijkstra y cortes sigue.
**Parte 4 (14/10/2026, cerrada):** 14 **eventos aleatorios** (personal, equipos, precio, abastecimiento, demanda) que
se prenden desde el menú; antes se corrige que **el GNC lo carga un playero** (PER-04). Etapas E0–E3 en §20–23; lo que
falta del orquestador, en §24.
