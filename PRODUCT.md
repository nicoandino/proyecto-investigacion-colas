# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Nico (grupo Andino–Assenza) presentando en vivo** el TP de Investigación Operativa: en el coloquio o la defensa,
desde su notebook, con el profesor mirando y preguntando "¿de dónde sale este número?". La app tiene que dejarlo
mostrar la estación funcionando, contestar con el dato y su fuente, y cambiar algo en el momento (período, ajustes,
eventos, editar la simulación) sin perderse. Otras audiencias (el profesor revisándola solo, el grupo sacando números
para el informe) no se confirmaron como objetivo de diseño.

## Product Purpose

Simulador de eventos discretos de **una estación real**: la Shell de Av. Balloffet 1810 esq. Av. Los Sauces, San
Rafael, Mendoza. El producto del TP es un **informe del caso**; el simulador sirve para mostrarlo y tiene que ser
**defendible y verificable**: cada número se comprueba contra los datos o contra una cuenta a la vista. Éxito = que el
profesor vea que el modelo corre, que usa los temas de la cátedra (colas, Monte Carlo, inventario, pronóstico, redes,
transporte, transbordo, flujos) con aspectos económicos, y que nada de lo que se muestra está inventado.

Consigna del profesor: "cualquier tema, que corra en algún software, con alguna complejidad, preferiblemente aspectos
económicos. Colas, transporte, Montecarlo, etc."

## Positioning

No es una simulación de manual con números puestos a ojo: es **un caso real con cada dato trazado** a un Registro
(valor, fuente, nivel, tipo, confianza) y una simulación con datos reales **sin azar** por defecto, que siempre da lo
mismo y se puede comprobar a mano. El azar aparece sólo cuando se lo pide (editar la simulación, eventos aleatorios con
su semilla a la vista). Los métodos de la cátedra se programaron a mano y se validaron contra sus ejercicios resueltos.

## Operating Context

- Se corre localmente: `.venv/Scripts/streamlit run app.py` (http://localhost:8501) en la notebook de Nico.
- Flujo: **menú inicial** (qué período: días, meses, estación o año; ajustes de economía, GNC, calendario de demanda,
  abastecimiento y eventos aleatorios) → **simulación con datos reales** → **resultados en pestañas** (La estación,
  Animación, Indicadores, Demanda, Pronóstico, Inventario, Red y rutas, GNC, Economía, Conclusión, Modelo y método,
  Datos y fuentes; Eventos y "Qué se sorteó" sólo cuando corresponde) → **Editar simulación** (con azar). Aparte, desde
  el menú: **escenario único** (una semana) y **Caso de informe** (mejor política, catálogo S0–S12, tornado).
- La animación es un tablero que dibuja el navegador (un día cada 5 s, avisos con pausa).
- En vivo, el profesor pregunta por números puntuales: cada sección tiene "¿Cómo se comprueba?" con la cuenta.

## Capabilities and Constraints

- **Stack confirmado: sigue en Streamlit** (Python + SimPy + Plotly). El rediseño se hace con CSS propio y componentes
  HTML dentro de Streamlit (como el tablero animado, `st.components.v1.html`), sin cambiar de framework.
- Reglas del proyecto (`CLAUDE.md`): `sim/` nunca importa Streamlit ni `ui/`; **ningún color fuera de `ui/tema.py`**
  (control N15); ningún número fuera del Registro (`sim/datos.py`); no se escala (sin base de datos, login, API,
  Docker, plugins ni multiprocessing); `verificar.py` (146 controles) en verde antes de cada commit; un commit por etapa
  en castellano, sin Pull Request.
- **Pantalla objetivo: notebook / escritorio.** Celular, tablet y proyector no se pidieron.
- Idioma: castellano rioplatense; números con coma decimal y punto de miles; los importes se escapan antes de pasar a
  Markdown (dos `$` en una línea se leen como LaTeX).
- Pendiente del plan (`ORQUESTADOR.md`, etapa 7): el frontend; la barra lateral ya no existe y los ajustes ya están en el
  menú inicial.

## Brand Commitments

- **El logo de Shell sólo dentro de la foto de portada** (la marquesina al 30 %, decisión de Nico del 14/10/2026), nunca
  como marca de la app, y aclaración visible de que el proyecto es académico y no está afiliado a Shell.
- Referencia visual que Nico dio como vinculante para el tablero animado: su imagen de un **dashboard oscuro**
  ("quiero que sea algo así"), ya aplicada a la animación. Para el resto de la app, el plan anotaba "tema oscuro en toda
  la app y navegación lateral como la imagen"; queda para decidir en el diseño.
- Honestidad sobre los datos: la app dice qué es dato, estimación, supuesto o heredado sin fuente; nada estimado se
  presenta como confirmado.

## Evidence on Hand

- **Registro** `sim/datos.py` (148 datos con fuente) y su versión legible `DATOS_REALES.md`.
- Notas de investigación con citas y URL: `research_notes/Datos reales estación Shell San Rafael/01–13`.
- **Serie real** de ventas al público de Shell en Mendoza (Secretaría de Energía, PRO-01, ene-2019 – ago-2026).
- Validaciones contra la cátedra (Cable Televisora, Lincoln, transporte $4.200/$4.100/$3.900, transbordo $20.700,
  oleoducto 205.000 gal/h) y `verificar.py` con 146 controles.
- Capturas de QA en `reports/qa/`.
- **Ausencias que no se deben inventar:** no hay mediciones de la propia estación (demanda, colas, tiempos); los
  márgenes por litro, el flete y el costo de almacenamiento son heredados sin fuente; la política real de reposición no
  está documentada (INV-06); no hay testimonios, logos ni datos del operador.

## Product Principles

1. **Verificable antes que vistoso:** cada número se puede rastrear a un dato o a una cuenta a la vista.
2. **Datos reales por defecto, azar sólo a pedido:** la simulación principal no sortea nada; lo editado y los eventos lo
   dicen y muestran su semilla.
3. **Decir qué es supuesto:** dato, estimación, supuesto y heredado se distinguen siempre; la plata se muestra como
   cantidad verificable × precio supuesto.
4. **Menos información, mejor elegida:** la app tenía demasiado; se muestra lo que se defiende y se esconde lo que sólo
   aplica cuando se edita.
5. **Hecho para presentar en vivo:** que Nico encuentre cada respuesta rápido delante del profesor.
