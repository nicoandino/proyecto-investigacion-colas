# Simulador de la Shell de San Rafael

Simulador de **eventos discretos** de una **estación de servicio real** —la Shell de **Av. Balloffet 1810
esq. Los Sauces, San Rafael, Mendoza**— para el trabajo práctico de **Investigación Operativa**
(grupo Andino–Assenza). Motor propio en Python (SimPy) con interfaz en Streamlit.

> **Proyecto académico; no es oficial ni está afiliado a Shell.**
> **Ojo con los datos:** no hay mediciones de la propia estación. Casi todo es **estimación o supuesto**,
> y la aplicación lo dice en cada número (insignia, fuente, nivel y confianza). Lo que sí está verificado
> es que el **motor se comporta bien** (100 controles). Ver *Respuestas al profesor*.

## Contenido

- [Qué resuelve](#qué-resuelve)
- [Las pestañas](#las-pestañas)
- [Cómo correrlo](#cómo-correrlo)
- [El modelo](#el-modelo)
- [Escenarios](#escenarios)
- [Criterio estadístico y verificación](#criterio-estadístico-y-verificación)
- [Guion de demo (7 minutos)](#guion-de-demo-7-minutos)
- [Respuestas al profesor](#respuestas-al-profesor)
- [Estructura del proyecto](#estructura-del-proyecto)

## Qué resuelve

Integra las tres unidades de la materia en un solo sistema:

- **Colas:** tres zonas de surtidores (nafta, diésel, GNC) atendidas por playeros por turno, con cola finita, abandono y la caja del minimarket.
- **Monte Carlo:** el producto y el tipo de vehículo de cada cliente se sortean con el método de 5 pasos (las tablas se ven en pantalla).
- **Inventario, transporte y redes:** un tanque por combustible con política (s, Q); el camión viene de Dock Sud (≈ 991 km) o Luján por una red de rutas que se puede cortar.

Y responde, **en pesos por mes**:

1. ¿Alcanza la dotación de playeros en el pico? ¿Conviene un playero más o más stock?
2. ¿Cuál es la mejor política de reposición de cada tanque?
3. ¿Cuánto se pierde cuando se corta el GNC en invierno y adónde va esa demanda?
4. ¿Qué dato incierto mueve más la conclusión (qué hay que relevar primero)?

## Las pestañas

| Pestaña | Contenido |
| --- | --- |
| 🏪 **La estación** | Ficha, esquema (12 caras, 3 zonas, minimarket), advertencias y las 20 contradicciones entre fuentes |
| 🎬 **Animación** | Un día del playón: colas, playeros, caras, tanques por producto, camión en ruta, GNC; saltos a la hora pico, al primer quiebre, a la descarga y al corte de GNC |
| 📊 **Indicadores** | Colas, clientes, inventario y complementarios, con IC 95 % |
| 🎲 **Demanda** | De litros por mes a clientes por día; Monte Carlo de producto y de vehículo; perfil horario |
| 🛢️ **Inventario** | Los 4 tanques (dientes de sierra), política (s, Q) por producto y barrido de políticas |
| 🗺️ **Red y rutas** | Mapa con la ruta óptima, cortes E1–E4, desvíos y plazo con y sin cortes |
| 🔥 **GNC** | Episodios de corte sombreados, compresores, migración a Súper y alerta de coherencia (6 caras para ≈ 3 % de clientes) |
| 🍂 **Estaciones** | Verano, otoño, invierno y primavera con su calendario real |
| ⚖️ **Escenarios** | Catálogo S0–S12 con diferencias pareadas contra S0 |
| 💰 **Economía** | Estado de resultados mensual, margen de equilibrio, año estimado y decisión en $/mes por escenario |
| 🌪️ **Sensibilidad** | Tornado de 26 ejes: qué dato incierto mueve más el margen, la espera y el servicio |
| 📝 **Conclusión** | Diagnóstico y respuesta a cada pregunta en pesos por mes |
| 📖 **Modelo y método** | Supuestos, formulación y fundamento estadístico |
| 📚 **Datos y fuentes** | El Registro completo con filtros, alternativas en conflicto y exportación a CSV |

Los parámetros se cambian desde la barra lateral; cada uno lleva la insignia de su dato.

## Cómo correrlo

Requisitos: Python 3.10 o superior (se usó 3.14). En la carpeta raíz del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Abrí [http://localhost:8501](http://localhost:8501). En macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`.

Para comprobar el motor (tarda ≈ 2 minutos):

```powershell
.\.venv\Scripts\python verificar.py
```

Debe terminar con *"Todos los controles pasaron (100 en total)"*.

## El modelo

```text
Litros por mes ─► clientes por día (÷ litros medios por cliente) ─► perfil horario (Poisson no homogéneo)
        │
        ▼
Cliente "producto primero" (Monte Carlo): producto → tipo de vehículo → litros → ¿compra en el shop?
        │
        ▼
¿Hay combustible? ──no──► se pierde (sin_combustible)
        │sí
¿Hay lugar en la cola de la zona? ──no──► se pierde (cola_llena)
        │sí
Zona A nafta (4 caras) · B diésel (2) · C GNC (6, limitada por 3 compresores)
servidores = mín(caras libres, playeros en turno 1·2·2)   ──► paciencia: abandono_espera
        │
        ▼ (20 % entra)
Caja del minimarket ──► abandono_caja

TANQUES (uno por líquido): política (s, Q) ─► camión (plazo 24–36–48 h + demora por corte de ruta)
GNC: en jun–ago, episodios de corte total ─► 30 % pasa a Súper, el resto se pierde (corte_gnc)
```

- **Entidad:** el cliente; sus atributos se sortean **al llegar**.
- **Recursos:** caras por zona, playeros por turno, compresores, caja y un tanque por combustible.
- **Calendario real:** el horizonte (día, semana, mes, estación, año) simula meses concretos con su estacionalidad (neutra por defecto) y su tipo de día.
- **Caso clásico:** el modelo original de 3 surtidores y 1 tanque se conserva como caso degenerado y reproduce sus números exactos (control N1).

## Escenarios

| ID | Escenario | Pregunta |
| --- | --- | --- |
| S0 | Hoy | línea base |
| S1 | Día típico por estación | pestaña Estaciones |
| S2 | Playeros en el pico (−1 / +1 / +2) | ¿alcanza la dotación? |
| S3 | Corte de GNC (total 24 h, ventana 17–01 h, nadie migra) | pérdida directa y adónde va |
| S4 | Corte de la ruta (E2, E4, obra; origen Dock Sud o Luján) | plazo y quiebre |
| S5 | Política s = 2,5 d · Q = 4,5 d | ¿cuándo y cuánto pedir? |
| S6 | Stock extra (s × 1,5) contra S2 +1 | ¿qué conviene en $/mes? |
| S7 | Crisis de abastecimiento (plazo 72–96 h) | resiliencia |
| S8 | Fila por cara en vez de cola por zona | ¿cambia la espera? |
| S9 | Autoservicio (−1 playero por turno) | ¿se puede ahorrar personal? |
| S10 | Cierre nocturno 22–06 | efecto del horario |
| S11 | Estacionalidad turística | ¿importa la estacionalidad? |
| S12 | Cambio de quincena | picos de cobro |

Todos se corren con los **mismos números aleatorios**: la diferencia contra S0 es el efecto del escenario, no del azar.

## Criterio estadístico y verificación

- **Calentamiento de 2 días:** el transitorio inicial se simula pero no se mide.
- **Réplicas independientes** con otras semillas; **promedio ± IC 95 %** (t de Student).
- **Números aleatorios comunes** entre escenarios y **diferencia pareada** réplica a réplica.
- **Promedios temporales** (área sobre el tiempo) para colas, utilización y niveles.
- **100 controles** en `verificar.py`: reproducibilidad, ley de Little, conservación de clientes (por zona y motivo) y de litros (por producto), unidades de la demanda (270.000 L/mes ⇒ 270.000 ± 3 %), calendario, monotonías, Dijkstra contra enumeración de todos los caminos, episodios de GNC, ingresos − costos = margen, sensibilidad, y que el **caso clásico reproduce los números dorados** del proyecto original.

## Guion de demo (7 minutos)

1. **La estación (30 s).** Mostrar el esquema de 12 caras y la advertencia: *"no hay datos de la estación; todo es estimación y está marcado"*.
2. **Animación (90 s).** Saltar a *la hora pico*: se ven los playeros ocupados, autos esperando con la cara libre y la cola. Saltar al *primer quiebre*: un tanque vacío con su rótulo. Dejar correr la descarga del camión.
3. **Demanda (60 s).** La cadena *litros por mes → clientes por día* (≈ 250) y las tablas de Monte Carlo del producto y del vehículo.
4. **Indicadores y Escenarios (90 s).** Espera promedio ≈ 1,6 min pero ≈ 3,1 min en la hora pico (ρ ≈ 0,85 con 2 playeros). En **Escenarios**, S2: un playero menos duplica la espera; uno más la baja a 2,2 min; mostrar el asterisco (efecto no atribuible al azar).
5. **GNC y Red (60 s).** Julio con episodios: el calendario sombreado, cuántos pasan a Súper y cuántos se pierden. Un corte de la RN 143 y su desvío.
6. **Economía (60 s).** Con los márgenes heredados el margen operativo es negativo (≈ −$3,8 M/mes): **la estación empata con ≈ $116 por litro**. Esto no es un resultado del negocio: muestra que la conclusión depende de un dato que hay que relevar.
7. **Sensibilidad (60 s).** El tornado: lo que más mueve el margen (demanda, margen por litro) y lo que más mueve la espera (dotación, paciencia, litros por carga). Cierre: *"estos son los datos que hay que ir a medir"*.

## Respuestas al profesor

**¿Por qué datos supuestos?** Porque no tenemos mediciones de la estación y los datos públicos son agregados nacionales o regionales. En vez de esconderlo, **cada dato se muestra con su fuente, nivel (de la estación a Argentina), tipo y confianza**, con las alternativas que perdieron, y la pestaña *Sensibilidad* mide cuánto cambia la conclusión si el supuesto es otro. La visita a la estación (demanda, dotación, GNC, márgenes) es lo que convertiría supuestos en observaciones.

**¿Cómo se validó?** En dos planos distintos. **El motor** se validó con 100 controles: ley de Little, conservación de clientes y de litros, que el modelo viejo (caso clásico) siga dando los mismos números, que 270.000 L/mes simulen 270.000 ± 3 %, que Dijkstra coincida con enumerar todos los caminos, que ingresos − costos = margen. **Los datos de entrada no se validaron contra la estación** (no hay mediciones): están marcados como estimación o supuesto y se evalúa su sensibilidad.

**¿Qué es "heredado"?** Un valor que viene del proyecto hipotético original (márgenes por litro, flete, costo de almacenamiento) y **no tiene fuente**. Se conserva como *placeholder visible* con la insignia ⚪. Por eso los pesos del simulador muestran **cómo se calcula** la economía, no cifras del negocio.

**¿Por qué 270.000 L/mes?** Porque es donde convergen tres fuentes débiles (un informe regional, el promedio nacional de 270–380 mil L y el punto de equilibrio de una estación, ≈ 315–400 mil L). No pudimos confirmar la cita original, por eso es *estimación, confianza baja-media*, con **150.000 y 400.000** como extremos del tornado. Ese valor se convierte en ≈ 250 clientes por día (nunca "litros ÷ 30 = autos").

**¿Por qué el margen operativo da negativo?** Con $100/L (heredado) y los sueldos de FECRA, los ingresos no cubren el personal. El equilibrio está en ≈ $116/L, apenas 16 % más. O el margen real es mayor o la demanda real es mayor: es lo primero que hay que relevar.

**¿Por qué réplicas, calentamiento y números aleatorios comunes?** Una corrida es una muestra de un proceso aleatorio: con otra semilla da otro número. Se corren varias y se informa el IC 95 %. El tanque arranca al 75 % y las colas vacías, así que los primeros 2 días se descartan. Con las mismas semillas en todos los escenarios, la diferencia entre ellos es el efecto del cambio y no del azar.

**¿Por qué llegadas de Poisson y tiempos triangulares?** Llegadas independientes con tasa que varía por hora ⇒ Poisson no homogéneo (exacto por la falta de memoria de la exponencial). Para los tiempos de servicio y litros no hay medición local; la triangular (mínimo, moda, máximo) es la forma estándar de expresar un juicio experto o un rango de la literatura.

**¿Por qué un motor propio y no Simul8?** Decisión del grupo; el motor es pequeño, está verificado y permite correr cientos de réplicas y escenarios con números aleatorios comunes desde la app.

## Estructura del proyecto

```text
app.py                 interfaz Streamlit (única entrada, 14 pestañas)
verificar.py           100 controles de correctitud
requirements.txt       dependencias
sim/                   motor (Python puro, sin Streamlit)
  datos.py             Registro de datos con fuentes y contradicciones
  config.py            parámetros, calendario, grupos, productos, red, GNC y economía
  distribuciones.py    RNG con streams separados
  modelo.py            procesos SimPy
  estadisticas.py      colectores de indicadores
  traza.py             animación y series
  runner.py            réplicas, IC y barrido de políticas
  red.py · gnc.py      rutas (Dijkstra) y cortes de GNC
  escenarios.py        estaciones del año y catálogo S0–S12
  economia.py          economía del caso clásico y de las políticas
  economia_real.py     economía mensual, personal, flete y año estimado
  sensibilidad.py      tornado
ui/                    presentación (tema, animación SVG, gráficos, textos)
reports/               scripts de QA con Playwright y capturas por fase
research_notes/        notas de investigación
docs/                  propuesta original del trabajo
```

Documentación de trabajo: `ORQUESTADOR_SIMULADOR.md` (especificación y cierre de fases), `ONBOARDING_PARA_AGENTES.md`, `TASK.md` y `CLAUDE.md`.

## Tecnologías

Python · SimPy · Streamlit · Plotly · pandas · NumPy
