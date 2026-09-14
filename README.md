# Simulador de Estación de Servicio

Simulador de eventos discretos de una estación de servicio, desarrollado para el Trabajo
Práctico de **Investigación Operativa**.

En lugar de usar un software comercial (Simul8, FlexSim), se desarrolló el simulador
completo: motor propio en Python con SimPy e interfaz web con Streamlit.

El modelo junta **las tres unidades de la materia** en un solo sistema:

- **Modelos de colas** — red de dos colas: surtidores y caja del minimarket, con abandono.
- **Simulación Monte Carlo** — la demanda de cada día se sortea de una tabla de
  frecuencias empírica, con los cinco pasos del apunte.
- **Transporte / inventario** — el tanque de combustible, con política de reposición y
  camión cisterna con plazo de entrega aleatorio.

Y responde **dos preguntas económicas** que compiten por la misma plata:

1. ¿Conviene agregar un surtidor y/o un cajero?
2. ¿Cuál es la mejor política de reposición de combustible?

## Cómo ejecutarlo

Con el entorno ya creado (carpeta `.venv`):

```bash
.venv/Scripts/streamlit run app.py
```

Se abre solo en el navegador, en `http://localhost:8501`.

### Si hay que instalarlo desde cero

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/streamlit run app.py
```

### Verificar que el motor está bien

```bash
.venv/Scripts/python verificar.py
```

Corre 22 controles: reproducibilidad, conservación de clientes, **ley de Little**,
utilización, monotonía, que la demanda simulada respete la tabla empírica, que las
llegadas sigan el perfil horario, **conservación de litros** y el comportamiento de la
política de reposición. Todos tienen que dar OK.

## Qué hace

| Pestaña | Qué muestra |
|---|---|
| 🎬 **Animación** | Un día completo funcionando: autos llegando, surtidores ocupándose, colas, gente pagando y el nivel del tanque bajando hasta que llega el camión. Con reloj, velocidad y barra de posición. |
| 📊 **Indicadores** | Los indicadores de colas, de clientes y de inventario, con su intervalo de confianza del 95 %, y un diagnóstico automático de dónde está el cuello de botella. |
| 🎲 **Demanda** | El método Monte Carlo paso a paso: la tabla de frecuencias, las probabilidades acumuladas, los intervalos de números aleatorios y el sorteo de cada uno de los 30 días. |
| 🛢️ **Inventario** | El nivel del tanque durante el mes (dientes de sierra) y el barrido de políticas de reposición, con el costo total abierto en flete, almacenamiento y faltante. |
| ⚖️ **Escenarios** | Comparación de Base / A / B / C con tabla, barras con IC y dispersión entre réplicas. |
| 💰 **Economía** | Ingresos, costos de inventario, costo de capacidad, margen operativo, beneficio neto y repago de cada escenario. |
| 📝 **Conclusión** | La recomendación, redactada a partir de los números, comparando las dos decisiones. |
| 📖 **Modelo y método** | El modelo, los supuestos, ρ teórico y por qué el método es estadísticamente válido. |

Todos los parámetros se cambian desde la barra lateral, incluida la tabla de frecuencias
de la demanda.

## El modelo

```
Monte Carlo: se sortea la demanda del día de una tabla de frecuencias
      ↓
Perfil horario: los autos se reparten en las 24 h (pico mañana, valle, pico tarde)
      ↓
[cola] → N surtidores → 30% → [cola] → M cajas → salida
   ↓        (Triangular)            (Triangular)   ↓
abandono                                       abandono
   ↑
   └── si el tanque está vacío, el auto ni siquiera hace la cola
              ↑
   TANQUE: política (s, Q) + camión cisterna con plazo de entrega aleatorio
```

- **Entidad**: auto/cliente. **Atributos**: litros a cargar, si compra en el minimarket.
- **Recursos**: surtidores, cajas y el tanque de combustible.
- **Una réplica es un mes completo** de operación (30 días).

### Escenarios de capacidad

| Escenario | Descripción |
|---|---|
| Base | Situación actual (3 surtidores, 1 caja) |
| A | +1 surtidor |
| B | +1 cajero |
| C | Ambos |

### Política de inventario

Se prueban varias combinaciones de **punto de pedido (s)** y **cantidad a pedir (Q)**, y
se elige la de menor costo total mensual:

**costo total = flete de los pedidos + almacenamiento + venta perdida por faltante**

## Rigor estadístico

- **Período de calentamiento**: la estación arranca vacía y con el tanque lleno; ese
  transitorio se simula pero no se mide.
- **Réplicas independientes**: cada escenario se corre varias veces con semillas distintas
  y se informa promedio ± **intervalo de confianza del 95 %** (t de Student).
- **Números aleatorios comunes**: los escenarios comparten las semillas, así que llegan
  los mismos autos, cargan los mismos litros y el camión tarda lo mismo. La comparación
  aísla el efecto de la capacidad.
- **Promedios temporales**: cola, utilización y nivel del tanque se calculan como área
  bajo la curva sobre tiempo, no como promedio de observaciones sueltas.

## Guion para la demo

1. **Arrancar** con `streamlit run app.py`. Ya abre con la simulación corrida.
2. **Animación** → ▶. Mientras corre, señalar el reloj, cómo se llena el playón en la hora
   pico y cómo el tanque baja hasta cruzar el punto de pedido y sale el camión.
3. **Demanda**: mostrar la tabla de los 5 pasos de Monte Carlo y el registro día por día,
   que es exactamente el formato del apunte. Los días de demanda alta son los que rompen
   el sistema.
4. **Indicadores**: los surtidores están ocupados menos de la mitad del tiempo, pero en la
   hora pico se espera varios minutos. El promedio de 24 h esconde el problema.
5. **Inventario**: el gráfico de dientes de sierra, y después apretar *Buscar la mejor
   política* para mostrar el barrido y el compromiso entre flete, almacenamiento y
   faltante.
6. **Escenarios**: el escenario B (+1 cajero) da **exactamente igual** que el Base en los
   surtidores, porque el minimarket no bloquea la carga. Se ve así de limpio gracias a los
   números aleatorios comunes.
7. **Conclusión**: el remate. El cuello de botella no es la capacidad de atención sino el
   abastecimiento, y arreglar la política de reposición rinde más que comprar un surtidor
   — sin invertir un peso.

### Preguntas probables y su respuesta corta

- *¿Por qué exponencial en las llegadas?* Porque los clientes llegan de forma independiente
  entre sí; es el proceso de Poisson. La tasa cambia hora a hora según el perfil.
- *¿Por qué triangular en el servicio?* Porque no hay datos históricos: sólo se puede
  estimar mínimo, valor más probable y máximo.
- *¿Por qué Monte Carlo para la demanda diaria?* Porque no se supone ninguna distribución
  teórica: se usa directamente la tabla de frecuencias observada.
- *¿Por qué el calentamiento?* Porque la estación arranca vacía y con el tanque lleno, y
  eso no representa su estado normal.
- *¿Por qué varias réplicas?* Porque una corrida es una sola muestra de un proceso
  aleatorio. El intervalo de confianza dice cuánta confianza merece el promedio.
- *¿Cómo sé que el simulador está bien?* `python verificar.py`: 22 controles, entre ellos
  la ley de Little y la conservación de litros, que dan exactos.

## Estructura del código

```
app.py                 interfaz Streamlit (única entrada del programa)
verificar.py           22 controles de correctitud del motor
sim/                   motor de simulación (Python puro, sin Streamlit)
  config.py            parámetros, perfil horario, tabla empírica, tanque, escenarios
  distribuciones.py    generación aleatoria con semilla y streams separados
  modelo.py            procesos SimPy: días, llegadas, colas, tanque, reposición
  estadisticas.py      colectores de indicadores
  traza.py             cuadros de animación, serie del tanque y registro Monte Carlo
  runner.py            réplicas, intervalos de confianza, escenarios y barrido
  economia.py          análisis económico y recomendación
ui/                    presentación
  animacion.py         reproductor de la animación
  graficos.py          gráficos Plotly
  textos.py            etiquetas y textos de la interfaz
docs/                  la propuesta original del trabajo
```

## Tecnologías

Python 3.14 · SimPy 4 (motor de eventos discretos) · Streamlit (interfaz) ·
Plotly (gráficos) · pandas (tablas).
#   p r o y e c t o - i n v e s t i g a c i o n - c o l a s  
 