# CLAUDE.md — Simulador de Estación de Servicio

## Qué es esto

Software de simulación de eventos discretos (DES) desarrollado a medida para el
Trabajo Práctico de **Investigación Operativa (4to año, segundo semestre)**.

La propuesta original (`docs/propuesta_simulacion_estacion_servicio.docx`) planteaba
usar **Simul8**. Decisión tomada: **no usamos Simul8**, construimos nuestro propio
simulador.

### Consigna del profesor

> "Puede ser sobre el tema que deseen, que corra en algún software (Simul8, flexsim,
> etc… cualquier otro) y que tenga **alguna complejidad**, preferiblemente que contemple
> **aspectos económicos**. Colas, transporte, Montecarlo, etc."

El proyecto usa **las tres unidades** que se dieron en clase:

| Unidad de la materia | Dónde aparece |
|---|---|
| **Modelos de colas** | Red de dos colas (surtidores y caja), disciplina FIFO, Wq, Lq, W, L, ρ, utilización, abandono |
| **Simulación Monte Carlo** | La demanda de cada día se sortea de una tabla de frecuencias empírica, con los 5 pasos del apunte |
| **Transporte / inventario** | Tanque de combustible con política (s, Q) y camión cisterna con plazo de entrega aleatorio |

### Las dos preguntas que responde

1. ¿Conviene agregar un surtidor y/o un cajero?
2. ¿Cuál es la mejor política de reposición de combustible?

Las dos compiten por la misma plata y se comparan con el mismo criterio: pesos por mes.

## Alcance — LEER ANTES DE AGREGAR CUALQUIER COSA

Este proyecto **no es escalable a propósito**. Es un entregable académico, no un producto.

**NO hacer** (aunque parezca "buena práctica"):

- Base de datos, autenticación, usuarios, multi-tenant, API REST, Docker.
- Plugins, capas de abstracción "para el futuro", inyección de dependencias.
- Varios tipos de combustible: multiplica tanques sin cambiar la naturaleza del problema.
- Lavadero, GNC, camiones como clientes, turnos de empleados, fallas de equipos.
- Multiprocessing para acelerar: no vale la fragilidad que trae en Windows + Streamlit.

**SÍ hacer**: que lo que hay esté **completo, correcto, visible y defendible frente al
profesor**. Rigor estadístico antes que cantidad de funcionalidades.

## Stack

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| Motor de simulación | **SimPy 4** | Librería DES estándar en ámbito académico |
| Cálculo y datos | **NumPy**, **pandas** | Promedios, réplicas, tablas |
| Interfaz | **Streamlit** | Web app sin escribir HTML del lado del servidor |
| Gráficos | **Plotly** | Gráficos interactivos |
| Animación | **SVG generado en JavaScript** | Ver "Decisiones de arquitectura" |

Python **3.14.4**, entorno virtual en `.venv/`.

## Estructura

```
Proyecto/
├── CLAUDE.md              # este archivo (contexto para Claude)
├── TASK.md                # checklist de tareas
├── README.md              # cómo correrlo + guion de demo
├── requirements.txt
├── app.py                 # interfaz Streamlit (única entrada del programa)
├── verificar.py           # 22 controles de correctitud del motor
├── sim/                   # MOTOR: Python puro, sin dependencia de Streamlit
│   ├── config.py          # parámetros, perfil horario, tabla empírica, tanque, escenarios
│   ├── distribuciones.py  # RNG con semilla, streams separados, muestreo empírico
│   ├── modelo.py          # procesos SimPy: días, llegadas, colas, tanque, reposición
│   ├── estadisticas.py    # colectores (por cliente, temporales y por hora)
│   ├── economia.py        # análisis económico de capacidad y de inventario
│   ├── traza.py           # cuadros de animación, serie del tanque, registro Monte Carlo
│   └── runner.py          # réplicas, IC 95 %, escenarios y barrido de políticas
├── ui/                    # solo presentación
│   ├── animacion.py       # reproductor de la animación (HTML + SVG dibujado en JS)
│   ├── graficos.py        # figuras Plotly
│   └── textos.py          # etiquetas, ayudas y textos largos
└── docs/
    └── propuesta_simulacion_estacion_servicio.docx
```

**Regla de oro de arquitectura**: `sim/` nunca importa `streamlit` ni `ui/`. Así el motor
se puede correr desde un script o un notebook, y se puede testear solo.

## Modelo del sistema

```
  Monte Carlo: cada día se sortea la demanda de una tabla de frecuencias empírica
        │
        ▼
  Perfil horario: esos autos se reparten en las 24 h (pico mañana, valle, pico tarde)
        │
        ▼
  ┌──────────────┐                                  ┌──────────┐
  │ Cola surtidor│ ─► N surtidores ─┬─► 70% se va    │Cola caja │─► M cajas ─► salida
  └──────────────┘   (Triangular)   └─► 30% ────────►└──────────┘  (Triangular)
        │ abandono                                        │ abandono
        ▼ (espera > paciencia)                            ▼
   cliente perdido                                  compra perdida
        ▲
        │ si no hay combustible, el auto ni siquiera hace la cola
  ┌─────┴─────────────────────────────────────────────┐
  │ TANQUE: cada carga descuenta litros.              │
  │ Si la posición de inventario ≤ s ──► pide Q litros│
  │ El camión tarda un plazo aleatorio en llegar.     │
  └───────────────────────────────────────────────────┘
```

- **Entidad**: auto/cliente. **Atributos**: litros a cargar, si compra o no, sus tiempos.
- **Recursos**: surtidores (N), cajas (M), tanque (litros).
- **Una réplica = un mes** (30 días por defecto), con 1 día de calentamiento.

### Escenarios de capacidad

Base (lo que hay hoy), A (+1 surtidor), B (+1 cajero), C (ambos).

### Política de inventario

Se barre una grilla de (punto de pedido s, cantidad a pedir Q) y se elige la de menor
**costo total = flete + almacenamiento + faltante**.

## Convenciones de código

- **Todo en castellano**: nombres, docstrings, interfaz. Es un TP que se defiende en
  castellano; que el código se lea igual que el informe.
- **Unidades**: tiempo en **minutos** (el día tiene 1440), volumen en **litros**, dinero
  en **pesos**. Sin excepciones ni conversiones implícitas.
- `@dataclass(frozen=True)` para parámetros; nada de diccionarios sueltos pasando de
  función en función.
- Reproducibilidad: **toda** la aleatoriedad viene de `sim/distribuciones.py` con semilla
  explícita. Misma semilla ⇒ mismo resultado, siempre.
- Streams RNG separados por fuente (llegadas, carga, compra, decisión, litros, demanda,
  entrega) para poder usar **números aleatorios comunes** entre escenarios.
- Los atributos del auto se sortean **al llegar**, no al ser atendido: así el auto
  número 57 es idéntico en los cuatro escenarios.
- Sin `print()` en `sim/`: el motor devuelve datos, la interfaz los muestra.

## Rigor estadístico

- **Calentamiento**: la estación arranca vacía y con el tanque lleno, que no es su estado
  habitual. Ese transitorio se simula pero no se mide.
- **Réplicas independientes** con semillas distintas. Se informa **promedio ± IC 95 %**
  (t de Student; la tabla está en `runner.py` para no depender de scipy).
- **Números aleatorios comunes** entre escenarios, para que la comparación sea justa.
- **Promedios temporales** (área/tiempo) para cola, utilización y nivel de tanque; los
  promedios por cliente son otra cosa y se calculan aparte.
- `verificar.py`: 22 controles, incluidas la **ley de Little** y la **conservación de
  litros**, que dan exactos.

## Decisiones de arquitectura (y por qué)

1. **La animación se dibuja en JavaScript, no en Python.** Con el reproductor del lado del
   servidor cada cuadro costaba unos 0,8 s (ida y vuelta por websocket más volver a montar
   el componente) y la película iba a los saltos. Ahora Python manda los cuadros como JSON
   y el navegador los dibuja. Es la única parte con JS y sólo dibuja: no simula nada.
2. **`st.html` no sirve para SVG**: Streamlit lo sanea y lo descarta entero. Hay que usar
   `st.components.v1.html`, que lo monta dentro de un iframe.
3. **Los importes se escapan antes de pasarlos a Markdown** (`escapar_pesos`): dos signos
   `$` en la misma línea hacen que Streamlit lo interprete como fórmula LaTeX.
4. **No se puede escribir en `st.session_state` de un widget ya instanciado.** El botón
   "Usar esta política" guarda la sugerencia en otra clave, y se aplica al principio de
   `leer_parametros()`, antes de crear los controles.
5. **La animación graba un solo día.** Los 30 días serían más de 80.000 cuadros. El nivel
   del tanque, en cambio, se muestrea cada 10 minutos durante todo el mes.
6. **El combustible se descuenta al EMPEZAR a cargar**, no al terminar: si no, varios
   autos cargando a la vez pasan cada uno el control de stock y entre todos sacan más
   litros de los que hay. Lo detectó el control de conservación de litros.
7. **Las llegadas usan la tasa de la hora en curso** y se vuelve a sortear al cruzar de
   hora (es exacto por la falta de memoria de la exponencial). Antes se usaba
   adelgazamiento (thinning), que descartaba la mitad de los sorteos y era más lento.
8. **La conclusión se arma antes que las pestañas**, así que después del barrido de
   políticas hay que llamar a `st.rerun()` o queda desactualizada.

## Rendimiento

Una réplica de 30 días tarda unos **0,5 s**. La corrida completa (4 escenarios × 4
réplicas) tarda **12 a 15 s**, y el barrido de políticas (13 × 2 réplicas) unos **16 s**,
por eso va aparte con su propio botón. Todo pasa por `st.cache_data`: volver a una pestaña
no vuelve a calcular.

Si hace falta acelerar: bajar los días simulados o la cantidad de réplicas. **No** meter
multiprocessing.

## Cómo correrlo

```bash
.venv/Scripts/streamlit run app.py     # la aplicación
.venv/Scripts/python verificar.py      # los 22 controles del motor
```

`.streamlit/config.toml` usa `fileWatcherType = "poll"` porque el watcher por eventos no
detecta los cambios de `sim/` y `ui/` en esta ruta (tiene espacios y acentos). Aun así,
**si se cambia la firma de un módulo hay que reiniciar el servidor**: Streamlit recarga el
script principal pero se queda con la versión vieja del módulo importado.

## Estado

Ver `TASK.md`.
