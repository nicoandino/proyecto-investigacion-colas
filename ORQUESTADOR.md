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
| **3 · Animación ✅** | Todos los días (1 por 5 s), diseño según la imagen, S1–S4 arriba y cola abajo (3 lugares por cara), gráficos opcionales | todos los días se reproducen; QA con capturas |
| **4 · Indicadores y Demanda ✅** | Menú "qué querés saber", enteros, sin lo que no se entiende; Demanda verificable; pestaña "Qué se sorteó" sólo si se editó | cada indicador se puede comprobar contra los datos |
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

## 8. Etapa 3 cerrada (6/10/2026)

- **Tablero nuevo** (`ui/animacion.py`, reescrito; tema oscuro de `ui/tema.py`, sin logo de Shell): barra superior (estado,
  día y hora, clientes de hoy, litros de hoy, ventas de hoy, tiempo simulado, ▶/⏸), el playón visto desde arriba con las zonas
  A, B y C, **cada cara con su surtidor (S1…) arriba y 3 lugares de cola abajo**, panel derecho (minimarket, playeros, GNC,
  camión cisterna, color = producto) y panel inferior (tanques, colas actuales con su espera, indicadores del día con barras de
  avance y un **gráfico a elección**: clientes por hora, ventas acumuladas, autos en cola, caras ocupadas, u ocultarlo).
- **Se anima todo el período**: un día cada 5 segundos (2, 5, 10 o 20 s por día), con ◀ Día / Día ▶, barra para saltar y los
  saltos a la hora pico, el primer quiebre, la próxima descarga y el corte de GNC (deshabilitados si no ocurren en el período).
  Un cuadro cada 12 min hasta 133 días; para el año completo, cada 36 min (14.600 cuadros, 3,8 MB).
- **Motor:** la cola es de **3 lugares por cara** (PER-07: A 12 · B 6 · C 18; antes 8 por zona, PER-05); cada cuadro trae los
  litros por producto y las esperas acumuladas de cada zona. `clasico()` no tiene cola finita y los dorados siguen exactos.
- **Compuerta:** `verificar.py` 116/116 (control 27) · QA con Playwright (`reports/qa_animacion.py` sin Streamlit y
  `reports/qa_etapa3_app.py` dentro de la app): 7 s de reproducción caen en el día 2 a las 09:36, el corte de GNC se habilita
  sólo en invierno, el año completo carga, **0 errores de consola**. Capturas en `reports/qa/etapa3/`.
- **Pendiente:** los números "esperados" de las barras (clientes, litros, ventas) son los del día según el Registro, no un
  objetivo del negocio; la pestaña Animación sigue dentro de las pestañas de arriba (el menú lateral del diseño llega en la etapa 7).

## 9. Etapa 4 cerrada (6/10/2026)

- **Indicadores** (`ui/vistas.py`): un menú **"¿Qué querés saber?"** con Resumen · Colas y esperas · Clientes · Playeros y
  surtidores · Inventario · Detalle completo, sobre el **promedio del período elegido**. Los clientes se cuentan (enteros, punto de
  miles); sólo los tiempos y las utilizaciones llevan decimales. Cada sección trae **"¿Cómo se comprueba?"** con la cuenta y los
  números de la corrida; el diagnóstico (se pierden clientes por X, "ojo con el promedio") queda en el Resumen. Se sacaron *nivel de
  servicio* y los litros vendidos del inventario; se mantienen *días con quiebre* y *tiempo sin combustible* (ahora **por tanque**).
  El detalle completo es una sola tabla ordenada por tema (Indicador · Valor · Unidad · Cómo se calcula).
- **Demanda** verificable: la cadena litros → clientes con su cuenta, el perfil del día (peso, % del día, clientes esperados contra
  simulados, espera por hora), la mezcla de productos (esperados contra simulados) y el día a día. **Sin Monte Carlo** y sin
  "número aleatorio". La pestaña vieja pasa a **🎲 Qué se sorteó**, que **sólo existe si la simulación fue editada**: explica la
  semilla, el Poisson, los dos Monte Carlo de 5 pasos, las triangulares y los cortes de GNC.
- **Motor:** `ResultadoReplica` trae totales enteros (llegadas, atendidos, perdidos por motivo, por zona y por producto, días con quiebre,
  camiones pedidos) y el **tiempo sin combustible de cada tanque**. Se corrigió que el **último día de la corrida nunca se registraba**
  (la corrida cortaba justo cuando se cerraba): en la estación real se corre un instante más; el caso clásico no se toca (dorados).
- **Compuerta:** `verificar.py` **118/118** (control 28: llegadas = Σ por zona = Σ por producto = Σ por hora = Σ por día) · dorados
  exactos · QA con Playwright (`reports/qa_etapa4_app.py`): las 6 secciones de Indicadores, Demanda sin Monte Carlo ni "número
  aleatorio", "Qué se sorteó" ausente con datos reales y presente al editar, **0 errores de consola**. Capturas en `reports/qa/etapa4/`.
- **Pendiente:** con estacionalidad neutra (default, C10) el verano **no** es más cargado que el invierno; para que el turismo suba la
  demanda hay que usar el preset "proxy turístico" (hoy sólo en el escenario S11). Inventario, Red y GNC siguen con el diseño viejo (etapa 5).

---

# Parte 2 — Pulido de la app en tandas (13/10/2026)

> Pedido unificado de Nico después de probar la app entera (reemplaza a `PROMPT_AJUSTES_ESTACION_Y_ALERTAS.md` y
> `PROMPT_PARTE_2_INDICADORES_RED_GNC_ECONOMIA.md`). **Una tanda = un commit**, con `verificar.py` en verde y QA con
> Playwright mirando la pantalla. No se espera aprobación entre tandas salvo que algo falle o cambie el alcance.

## 10. Reglas para esta parte

- Lo que Nico aprobó **no se toca** (indicadores generales, "¿Cómo se comprueba?", colas, clientes, playeros, detalle, gráficos).
- Todo comportamiento nuevo es un **parámetro con su `Dato`**, apagado o neutro en `clasico()` y en los defaults de
  `ParametrosSimulacion()` (así no se mueven los dorados ni los 118 controles); la app lo enciende desde el menú.
- Un cambio de presentación no toca `sim/`. Si hace falta marcar un momento (alerta, causa de pérdida), es un **registro
  en la traza o en los indicadores, sin consumir números aleatorios**.
- Streams nuevos sólo al final de `STREAMS`. Nada de multiprocessing, hilos, dependencias nuevas ni componentes a medida.
- Si algo cuesta mucho más de lo que aporta, se hace la versión mínima y se anota acá qué quedó afuera.

## 11. Diagnóstico previo (lo que encontré al leer el código)

- **El cuelgue de "Buscar la mejor política"** (pestaña Inventario): la búsqueda corre 13 políticas × 2 réplicas **de todo
  el período elegido** dentro de la ejecución del script, con un spinner y nada más. Medido: una réplica de un año tarda
  5,2 s ⇒ **≈ 135 s bloqueado**. Además: (1) con datos reales (sin azar) las 2 réplicas son **idénticas**, así que la mitad
  del tiempo se tira; (2) cualquier clic durante esos 2 minutos corta la ejecución, Streamlit vuelve a correr el script y la
  búsqueda **arranca de cero** (parece colgada para siempre); (3) cada vuelta de script reenvía el tablero animado (≈ 3,8 MB
  para un año), lo que puede tumbar la pestaña del navegador (el "crash").
- **Orígenes alternativos:** de los nombrados por Nico, **La Paz y Pareditas son cruces de ruta de la red, no puntos de
  despacho** de combustible: no se agregan. Lo que sí se puede respaldar: la **terminal de despacho de Arroyo Seco**
  (Santa Fe), activo de Raízen/Shell incluido en la venta a Mercuria (jun-2026), a 806 km de General Alvear por ruta
  (OSRM), y la refinería de **Luján de Cuyo** (YPF), que ya estaba en el Registro como alternativa de INV-05.
- **Vacaciones de invierno de Mendoza 2026:** receso del **6 al 17 de julio** (calendario de la DGE citado por Los Andes,
  Ámbito y El Sol). El Registro (DEM-09) decía 9–20 jul, que no coincide.

## 12. Tandas (ordenadas por valor para el informe ÷ costo)

| Tanda | Qué incluye | Riesgo | Cómo se verifica |
|---|---|---|---|
| **0 · Cuelgue** | La búsqueda corre **de a una política por vez** dentro de un `st.fragment` (barra de progreso, botón Detener, tope de tiempo, sigue sola sin bloquear la app); 1 réplica si no hay azar; al terminar, **tabla de las 13 evaluaciones con la ganadora marcada** | Bajo: sólo `app.py`; el motor no cambia | Playwright: el año completo termina, la barra avanza, un clic en otra pestaña no la reinicia; tiempo medido |
| **1 · Limpieza** | La estación sin insignias ni imagen del playón (una aclaración corta); "Shell Shop"; la ayuda "?" que aparece al pasar el mouse y se va al salir (arreglo de raíz + foco de teclado); Economía sin el estado de resultados detallado ni "por estación / año estimado" | Bajo | Capturas de cada pantalla; prueba del tooltip con el mouse y el teclado |
| **2 · Contradicciones** | Criterio único (oficial/primaria > secundaria; más reciente; más local; empate → conservadora) aplicado a C1–C20 y a las advertencias; nota en `research_notes/`; en pantalla sólo el valor elegido + una frase honesta general; nada estimado se marca "confirmado" | Medio (textos y Registro, sin cambiar valores del motor salvo que el criterio lo exija) | `verificar.py`; capturas de La estación y Datos y fuentes |
| **3 · Inventario y quiebre** | Rótulos y orden para alguien que lo ve por primera vez (qué es un quiebre, cuántos, cuánto duraron, qué costaron); **litros no vendidos por causa** en cada tanque (quiebre, abandono por espera, cola llena, GNC cortado que no pasó a Súper). Motor: contadores nuevos sin azar | Medio (campos nuevos en `ResultadoReplica`) | Control nuevo: Σ causas = litros no vendidos; capturas |
| **4 · Menú con parámetros** | Desplegables antes de simular: **Economía** (margen por litro de cada producto, flete fijo y por km, almacenamiento, sueldo de playeros, con su valor del Registro y rango si existe, y la aclaración de heredado); **GNC** (cortes habituales / más cortes en todo el invierno + invierno frío que alarga el corte, stream nuevo `invierno_frio`; % de clientes GNC = DEM-05) | Medio (parámetros nuevos neutros por defecto) | Control: con los defaults da exactamente lo mismo; capturas del menú |
| **5 · Calendario de demanda** | Factores por fecha (verano, vacaciones de invierno de Mendoza, resto del invierno) como `Dato` editables desde el menú, activos en la app y neutros en `clasico()`; Demanda con la cuenta a la vista y el **rango mín–máx por temporada**; Perfil del día y Día a día con selector de fechas y filtro de período sólo si la corrida es larga | Medio | Control: factores = 1 ⇒ mismos números; Σ por día = total; capturas |
| **6 · Escenario único y conclusión** | Sale la pestaña Escenarios; en el menú, **"Simular escenario único"** (playeros, franja horaria, temporada, clientela) que muestra sólo ese escenario; conclusión armada con los resultados de la corrida; búsqueda de política, catálogo S0–S12 y tornado pasan a **"Caso de informe"**, fuera del flujo normal (`sim/escenarios.py` intacto) | Medio-alto (reordena la navegación) | Playwright: el flujo completo; `verificar.py` |
| **8 · Red y rutas** (antes que la 7) | Rutas alternativas debajo de la óptima (todas las rutas simples de la red, de mejor a peor, con km y plazo); **orígenes alternativos** (Dock Sud → Arroyo Seco → Luján) con indisponibilidad aleatoria (streams nuevos al final) y marcado manual de un origen como no disponible; interruptor en el menú (apagado = siempre la ruta óptima) | Medio | Control: apagado ⇒ mismos números; con Dock Sud no disponible el pedido sale de Arroyo Seco con su plazo |
| **7 · Alertas con pausa** | La animación se detiene en cada pedido de camión (cruce del punto s: "Bajo nivel de combustible: Diésel G2, 18 %", con el **origen realmente usado**) y en cada corte de GNC ("El GNC se cortó por N días" + contador en la zona GNC); "Seguir trayectoria del camión" cambia a Red y rutas (clic sobre la pestaña desde el iframe) donde se ve el camión sobre la ruta y el cartel del pedido; carteles en cola, de a uno; el camión se ve llegar y descargar en el playón | Medio (JS del tablero; el cambio de pestaña desde el iframe puede no estar permitido → plan B: mensaje claro de dónde mirar) | Playwright: la pausa, los dos botones, el cambio de pestaña, 0 errores de consola |
| **9 · Mapa con relieve** (opcional) | Mapa base abierto con relieve (OpenTopoMap/OSM con su atribución) y rutas más visibles; si choca con el QA o pide algo pesado, sólo más contraste | Bajo | Captura |

**Por qué este orden:** la 0 primero (todo lo demás la usa). Limpieza y contradicciones son baratas y mejoran lo que el
profesor ve primero. La 3 y la 5 son las de más valor para el informe (por qué se pierde venta; temporadas sin azar). La 4
va antes que la 5 y la 6 porque arma el menú donde ellas se enganchan. **La 8 va antes que la 7** porque el cartel del
camión tiene que decir el origen realmente usado: hacerlas al revés obliga a rehacer el cartel. La 9 última y opcional.

## 13. Lecturas tomadas (del pedido y mías)

- "Caso de informe" = modo aparte con el catálogo completo, el tornado y la búsqueda de la mejor política.
- "Escenario único" reemplaza la pestaña Escenarios; es una micro simulación lanzada desde el menú principal.
- Economía: se quitan el estado de resultados detallado y el bloque **"Por estación y año estimado"** ("prestaciones" en
  el dictado lo leí como "por estación"); la sección de ingresos (tarjetas y cascada) queda.
- Los "óptimos" de márgenes y flete son **valores por defecto con rango de referencia**, no un optimizador.
- "Diésel G12" = Diésel G2; "Duxac" = Dock Sud. Los orígenes alternativos son para los líquidos (el GNC sale de la red de gas).
- El calendario multiplica los litros del día (no se renormaliza al año): el promedio anual sube < 1 % y se dice en pantalla.

## 14. Avance

- **Tanda 0 ✅ (cuelgue).** La búsqueda vive en un `st.fragment(run_every=0.2)` que evalúa **una política por vuelta**
  y guarda el avance en la sesión: la barra se ve, hay botón *Detener*, se corta sola a los 180 s mostrando lo evaluado y
  los clics en otras pestañas no la reinician. Sin azar corre 1 réplica por política (antes 2 idénticas). Al terminar,
  **las 13 evaluaciones en una tabla con la ganadora 🏆** (costo de los 4 tanques) y debajo la mejor de cada tanque.
  QA (`reports/qa_tanda0_busqueda.py`): año completo en **84 s** (antes ≈ 135 s bloqueados), avance 0→12 monótono con 2
  clics en otras pestañas en el medio, 0 excepciones, 0 errores de consola. `verificar.py` 118/118.
  Causa de raíz del "crash": no se pudo reproducir un cierre del programa; la explicación más probable es la
  re-ejecución completa del script en cada clic durante la búsqueda (que la reiniciaba) con el tablero de un año (≈ 3,8 MB)
  reenviado cada vez. Con el fragmento, durante la búsqueda sólo se re-ejecuta el fragmento.
- **Tanda 1 ✅ (limpieza).** La estación: sin insignias ni fuente por dato (siguen en Datos y fuentes) y sin la imagen del
  playón (una línea de texto). Tablero: "Shell Shop". Economía: sin el estado de resultados detallado ni "Por estación y año
  estimado" (quedan tarjetas y cascada; el ± IC sólo si hay réplicas). **Ayuda "?"**, causa de raíz medida con Playwright:
  Streamlit la abre al pasar el mouse **y mientras el botón tiene el foco**; un clic le daba el foco y quedaba abierta hasta
  otro clic. Arreglo: un script mínimo (iframe invisible, mismo origen) evita que el clic con el mouse enfoque el botón, y el
  cartel deja de atrapar el mouse (`pointer-events: none`). Medido: abre con el mouse, se va 0,3 s después de salir (también
  tras un clic), Tab la abre y Escape la cierra. QA `reports/qa_tanda1_limpieza.py`: 0 excepciones, 0 errores de consola.
