# ORQUESTADOR — Rediseño del flujo de la app (v3)

> Plan por etapas del rediseño pedido el 6/10/2026. Reemplaza al orquestador viejo (en `..\Contextoviejo\`).
> **Una etapa por vez, un commit por etapa, y no se avanza sin el OK del usuario.**
> Reglas de oro y contexto: `CLAUDE.md`. Datos: `DATOS_REALES.md`.

## 1. Qué se quiere (en las palabras del usuario, ordenado)

**La app tiene demasiada información y no se entiende.** Lo que se mantiene es lo que se puede **verificar**.

### 1.1 Flujo
1. **Menú inicial: ¿qué se quiere simular?** (antes de cualquier número)
   - **Por días:** cantidad de días y de qué mes a qué mes (si el rango incluye invierno, entran los cortes de GNC).
   - **Por meses:** elegir uno o varios (enero, febrero, marzo…).
   - **Por estaciones:** sólo verano, sólo invierno, etc.
   - **Año completo.**
2. **Se simula con los datos reales** (los del Registro) y se muestran los resultados.
3. Abajo, un botón **Editar simulación** (menú aparte) con pocas opciones: playeros, demanda (poca / media /
   alta / el doble en la hora pico), % de clientes GNC, precios. La simulación principal **nunca** usa estas.
4. Los **parámetros** salen de la barra lateral y pasan a un **menú de ajustes** (un botón, no tres puntos de
   Streamlit, que no se pueden personalizar).

### 1.2 Datos reales = nada al azar
- En la simulación con datos reales **no hay azar**: se saca el Monte Carlo, los sorteos y las réplicas.
- Todo tiene que ser **verificable**: el usuario tiene que poder comprobar cada número con los datos.
- Si la simulación **fue editada**, aparece una pestaña nueva que **explica todo lo que se sorteó**.

### 1.3 Animación
- Hoy anima **un solo día**. Tiene que animar **todos los días** del período: **un día cada 5 segundos**.
- Mantener el reloj y la fecha. **No se entiende qué se anima**: dejar claro el tablero.
- Diseño nuevo, más moderno, **según la imagen que pase el usuario** (pendiente).
- **Arriba** los surtidores S1, S2, S3, S4…, **abajo** la cola. **Todas las caras con la misma cola: 3 lugares.**
- Los gráficos (colas a lo largo del día, ocupación de surtidores) pasan a ser **opciones para mostrar**.

### 1.4 Pestañas (lo que pidió, una por una)
| Pestaña | Qué pidió |
|---|---|
| **Indicadores** | Un menú de **"qué querés saber"** sobre el promedio del período (ej.: en verano hay más gente y más espera). Colas: espera en cola, tiempo de espera. Inventario: **sacar** nivel de servicio y litros vendidos poco claros; **dejar** días con quiebre y tiempo sin combustible. Clientes: atendidos, por zona, por producto, litros vendidos por día (todo lo de clientes está bien). Utilización de playeros y de surtidores. **Todo número de clientes es entero** (no 109,3). La tabla detallada se queda, más ordenada. |
| **Demanda** | Verificable. Sin Monte Carlo si no se editó. Perfil del día (cuándo llegan, cuánto esperan) comprobable. |
| **Inventario** | Gráficos de los **tanques desde el momento cero (siempre llenos)**: qué día se pidió cada camión, qué día llegó, **qué ruta tomó, cuántos km y cuánto costó**. Todo verificable. |
| **Red y rutas** | La red de abastecimiento **de nafta, de diésel y de GNC**. "Qué le hace cada corte a cada origen" va **sólo si se editó** (ej.: se cortó una ruta y el camión tomó otra). |
| **GNC** | Si el período no incluye invierno: cartel **"no hay datos: no se realizaron cortes de GNC"** (o todo en cero). Si lo incluye: fechas programadas de corte y clientes perdidos por corte. |
| **Estaciones del año** | Entra en el **menú inicial** (por estaciones). La pestaña desaparece. |
| **Escenarios** | Se mantiene, **con una explicación de cada escenario**, y se **elige cuál** correr **antes** de simular (por fechas, meses o temporadas). |
| **Economía** | Se mantiene, **separando lo verificable de lo supuesto**. |
| **Conclusión** | Según las etapas elegidas (el período simulado). |
| **Sensibilidad (tornado)** | **Se quita por ahora.** |
| **Réplicas / efecto de cortes** | **Pestaña aparte**, opcional. |

### 1.5 Frontend
No le gusta el frontend actual. Usar una skill de diseño (la que mencionó, "impecable"/*impeccable*) si hace falta.

## 2. Problemas que veo (para decidir antes de programar)

1. **Datos reales sin azar ⇒ casi no hay colas.** Si los autos llegan a intervalos exactos y tardan lo
   promedio, con 2 playeros (ρ_pico ≈ 0,85) la cola casi nunca se forma: la espera sale ≈ 0 y la "hora pico"
   deja de verse. Las colas aparecen **por el azar**. Es una consecuencia, no un bug. En modo editado (con
   azar, o el doble de demanda en el pico) sí aparecen.
2. **Animar todos los días:** un año son 365 × 1.440 minutos. Hay que grabar menos cuadros por día (≈ 100 en
   vez de 2.880) y cargar por tandas para que la página no pese decenas de MB.
3. **Precios:** el modelo usa **márgenes**, no precios. Para "modificar el precio" hay que definir el margen
   como porcentaje del precio (hoy $100/L ≈ 4,7 % de un Súper de $2.141, un valor heredado sin fuente).
4. **"Todos con números enteros":** los promedios se redondean al mostrar; los totales de clientes ya son enteros.
5. **Réplicas e IC:** sin azar no hay réplicas ni IC en la simulación principal; quedan sólo en la pestaña
   aparte y en el modo editado.

## 3. Etapas

| Etapa | Qué incluye | Compuerta |
|---|---|---|
| **0** | Limpieza de documentos (hecha, `0eaae74`) | un solo md de contexto y uno de datos |
| **1 · Motor ✅** | Modo `real` (determinista) y modo `editado` (con azar); tanques llenos al día 0; registro de pedidos de camión (día de pedido y de llegada, ruta, km, costo); grabación de todos los días | `clasico()` sigue dando los dorados; el modo real da siempre lo mismo; conservación de clientes y litros |
| **2 · Menú inicial ✅** | Por días (con rango de meses), meses, estaciones y año; flujo Menú → Simulación → Resultados; "Editar simulación" aparte | captura del menú; las 4 formas de elegir el tiempo corren |
| **3 · Animación** | Todos los días (1 por 5 s), diseño según la imagen, S1–S4 arriba y cola abajo (3 lugares por cara), gráficos opcionales | todos los días se reproducen; QA con capturas |
| **4 · Indicadores y Demanda** | Menú "qué querés saber", enteros, sin lo que no se entiende; Demanda verificable; pestaña "Qué se sorteó" sólo si se editó | cada indicador se puede comprobar contra los datos |
| **5 · Inventario, Red y GNC** | Tanques desde el día 0 con pedidos, rutas, km y costo; red por producto; GNC con cartel si no hay cortes | idem |
| **6 · Escenarios, Economía, Conclusión** | Escenario elegido antes de simular y explicado; economía separando verificable y supuesto; conclusión según el período; réplicas y efecto de cortes en pestaña aparte; tornado fuera | idem |
| **7 · Frontend** | Ajustes en un menú (no en la barra lateral), nuevo diseño con una skill de diseño | QA visual en escritorio y celular |
| **8 · Cierre** | `verificar.py` completo, QA visual, `CLAUDE.md` y `DATOS_REALES.md` al día | todo en verde |

## 4. Decisiones tomadas (6/10/2026)

- **Sin azar = determinista puro.** Autos a intervalos exactos según el perfil horario, mezcla de productos y de
  vehículos por cuotas (el reparto exacto del Registro), tiempos de servicio promedio. Siempre da el mismo
  resultado y se comprueba a mano. En esta modalidad las colas casi no aparecen (se ven con el modo editado).
- **Precio editable por litro.** En *Editar simulación* se puede poner el precio del litro de cada combustible
  (los de referencia son ECO-08: Súper $2.141, G2 $2.116, G3 $2.641, GNC $699/m³). Para que el precio afecte
  la plata hace falta un costo: se toma **costo = precio de referencia − margen heredado ($100/L)**, fijo, así
  que subir el precio $50 sube el margen $50 por litro. **La demanda no cambia con el precio** (sin
  elasticidad): es un supuesto y se rotula.
- **Skill de diseño:** el usuario la inicia él mismo cuando llegue la etapa de Frontend; yo le aviso en ese momento.

## 5. Pendientes
- **La imagen del diseño de la animación** (la pasa el usuario).
- El OK del usuario para arrancar la **Etapa 1**.

## 6. Etapa 1 cerrada (6/10/2026)

- `sim/distribuciones.py`: `AleatorioDeterminista`: el mismo contrato que `Aleatorio` pero **sin azar**. Tiempos y litros = el
  promedio; producto, tipo de vehículo, compra y migración del GNC = **cuotas exactas** (reparto proporcional suave);
  como el motor pide todo a `self.az`, alcanza con cambiar ese objeto: el modelo con azar y los dorados no se tocan.
- `sim/modelo.py`: `_llegadas_deterministas` (los clientes de cada día repartidos por el perfil horario, equiespaciados
  dentro de cada hora, la suma exacta); registro de **cada camión** (`PedidoCamion`: día de pedido, de llegada, litros,
  demora de ruta y causa); `simular` elige el generador según `p.determinista`.
- `sim/gnc.py`: episodios de GNC **equiespaciados** en jun–ago (con los defaults: 28/jun–3/jul y 30/jul–4/ago), siempre
  en las mismas fechas. `sim/red.py`: sin cortes de ruta sorteados.
- `sim/config.py`: `determinista`, `animar_todo` y `ParametrosSimulacion.datos_reales()` (sin azar, sin calentamiento,
  tanques llenos, sin cortes aleatorios, animación de todos los días). Registro: MOD-02, INV-12, CAL-07.
- **Compuerta:** `verificar.py` **107/107** (control 25) · dorados exactos · otra semilla da exactamente el mismo
  resultado · llegadas exactas (7.783 clientes en julio = la suma día por día) · mezcla y compra por cuotas · camiones
  a 36 h exactas · GNC: 35 afectados = 11 migrados + 24 perdidos, y 0 en enero · la animación graba los 31 días.
- **Lo que se ve en julio con datos reales:** espera media 0,19 min y en la hora pico 1,0 min (casi no hay colas, como se
  anticipó), nivel de servicio 98,7 %, 22 pedidos de camión y quiebres por falta de combustible en 19 % de los días con la
  política (s, Q) por defecto.
- **Pendiente para la Etapa 3:** la cola de **3 lugares por cara** cambia PER-05 (hoy 8 por zona) y por lo tanto los resultados.

## 7. Etapa 2 cerrada (6/10/2026)

- `sim/periodo.py` (nuevo, sin Streamlit): `Periodo` (por días, por meses, por estación, año completo), si **incluye
  invierno** y las fechas de los cortes de GNC previstas, y `Edicion` / `aplicar_edicion` (playeros, demanda poca / media /
  alta = 150 / 270 / 400 mil L del Registro DEM-01, el doble en la hora pico DEM-13, % de clientes GNC, precio por litro,
  semilla). Una edición **usa azar**; la simulación principal no.
- Temporadas (CAL-08): verano dic–feb (90 días, cruza el año), otoño mar–may (92), invierno jun–ago (92), primavera
  sep–nov (91): suman los 365 días.
- **Precio por litro:** `ParametrosEconomicos.precios` (ECO-08) y `delta_precio`: el margen sube $ por $ con el precio
  (costo fijo, sin elasticidad: la demanda no reacciona al precio). Se rotula como supuesto.
- `app.py`: flujo nuevo **Inicio → Simular → Resultados → Editar**. La barra lateral de parámetros **ya no se usa** (los
  datos son los del Registro); el caso clásico queda sólo para las verificaciones. Se sacaron las pestañas *Estaciones* (entra
  en el menú) y *Sensibilidad* (el tornado, por ahora fuera). Quedan 12 pestañas. Al final de los resultados: **Editar
  simulación** y, si se editó, **Volver a los datos reales**. Aviso visible de "con datos reales (sin azar)" o "EDITADA (con azar)".
- La pestaña GNC dice **"No hay datos de cortes de GNC en este período"** si no incluye invierno.
- **Compuerta:** `verificar.py` 112/112 (control 26) · dorados exactos · QA Playwright (`reports/qa_etapa2_menu.py`, capturas
  en `reports/qa/etapa2/`): las 4 formas de elegir el período, 7 pestañas con resultados, Editar y Volver a real, **0
  excepciones y 0 errores de consola**. Tiempos: 90 días 6 s · 180 días 8 s · año completo 13 s.
- **Pendiente para las etapas siguientes:** la animación sigue siendo de un día (etapa 3); los indicadores todavía muestran
  "± IC" con 0 réplicas y decimales (etapa 4); la pestaña Demanda todavía muestra el Monte Carlo y no hay pestaña "Qué se
  sorteó" (etapa 4); Escenarios, Economía y Conclusión no distinguen aún lo verificable de lo supuesto (etapa 6).
