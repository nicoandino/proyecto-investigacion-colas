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
- **Tanda 2 ✅ (contradicciones).** Criterio único en `research_notes/…/07_decisiones_fuentes.md`: (0) que mida lo mismo,
  (1) oficial o primaria y vigente, (2) más reciente, (3) más local, (4) empate → la más conservadora. Cada `Contradiccion`
  tiene ahora su `criterio`; ningún valor del motor cambió (todas las decisiones confirman lo adoptado, salvo las fechas de
  vacaciones de invierno: 6–17 jul, DGE 2026, que se usan en la tanda 5). `ADVERTENCIAS` se reemplazó por `AVISO_FUENTES`, la
  única frase general. La estación ya no muestra advertencias ni contradicciones; Datos y fuentes muestra el valor elegido y
  "por qué" (las alternativas siguen en el Registro y en el CSV porque son los extremos del tornado). La "alerta C8" pasa a
  ser una observación del modelo (la capacidad de GNC sobra para esa demanda). `DATOS_REALES.md` regenerado. QA
  `reports/qa_tanda2_fuentes.py`: 0 excepciones, 0 errores de consola; `verificar.py` 118/118.
- **Tanda 3 ✅ (inventario y quiebre).** Motor, sin azar: contadores de litros perdidos por causa en cada producto
  (`litros_perdidos_espera / _cola_llena / _corte_gnc`, además del de falta de stock) y el registro de cada quiebre (cuándo
  se vació y cuándo volvió a tener un tanque) a partir de la serie "tanque vacío" que ya existía. `ResultadoReplica` trae
  `litros_perdidos_causa` y `quiebres` (sólo la estación real: los dorados no se mueven). Pantalla: un bloque único
  (`vistas.bloque_quiebres`) en Indicadores → Inventario y en la pestaña Inventario: qué es un quiebre, cuántas veces
  quedó vacío cada tanque, cuánto duró (total y el más largo), clientes sin cargar y **venta perdida** (costo de oportunidad,
  margen heredado), y la tabla **"Lo que no se vendió, y por qué"** (falta de stock · se cansó de esperar · cola llena · GNC
  cortado; el GNC en m³). La pestaña Inventario se reordenó: 1) cómo se movió cada tanque, 2) quiebres, 3) la política (s, Q)
  con rótulos en palabras. Matiz que el rótulo dice: se pierde por falta de stock también cuando el tanque **no alcanza para la
  carga de ese cliente** aunque no esté vacío. Control nuevo (29): Σ causas = litros no vendidos; Σ horas de quiebre = tiempo
  sin combustible. `verificar.py` **120/120**; QA `reports/qa_tanda3_inventario.py`: 0 excepciones, 0 errores de consola.
- **Tanda 4 ✅ (menú con parámetros).** `sim/periodo.py`: `Ajustes` (márgenes por producto, flete fijo y por km,
  almacenamiento, sueldo del playero, modo de cortes de GNC, % de clientes GNC) y `aplicar_ajustes`; los defaults son los del
  Registro y dan **exactamente** la misma corrida. Motor: `ParametrosEconomicos.margenes_producto` + `margen_de(producto)` (una
  sola fórmula del margen, usada en la economía, el barrido y la venta perdida); `ParametrosGNC.cortes_extra /
  prob_invierno_frio / dias_extra_frio` (0 por defecto) con los valores del Registro **GNC-08** (2 cortes extra), **GNC-09**
  (30 %) y **GNC-10** (+4 días ⇒ 10, la alternativa larga de GNC-06), y dos streams nuevos al final (`cortes_extra_gnc`,
  `invierno_frio`). Sin azar, los cortes extra caen en el medio de los huecos más largos del invierno y el alargue es una cuota:
  11/6–16/6 · 28/6–7/7 (alargado) · 30/7–4/8 · 15/8–20/8. Menú: desplegables "💰 Economía" (con valor del Registro, rango de
  prueba y la aclaración de heredado/no confirmado en cada ayuda) y "🔥 GNC"; los ajustes se guardan al simular y el encabezado
  dice cuáles difieren del Registro; Economía muestra los márgenes usados. Control nuevo (30); GNC-08/09/10 clasificados en el
  listado del tornado. `verificar.py` **122/122**; QA `reports/qa_tanda4_menu.py`: 0 excepciones, 0 errores de consola.
- **Tanda 5 ✅ (calendario de demanda y filtros).** Nota `research_notes/…/08_calendario_temporadas.md`: vacaciones de
  invierno de Mendoza 2026 = **6–17 de julio** (calendario de la DGE, vía Los Andes, Ámbito y El Sol; el sitio de la DGE no se
  pudo abrir, así que queda nivel C, confianza media) y el criterio de los factores: **la mitad del desvío del proxy
  turístico** (C10: la ocupación hotelera exagera el efecto). Registro: **DEM-14** (verano × 1,06 · vacaciones de invierno
  × 1,08 · resto del invierno × 0,94; supuesto) y **DEM-15** (las fechas). Motor: `calendario_demanda` (vacío por defecto ⇒
  `clasico()` y `ParametrosSimulacion()` sin cambios) y `factor_calendario(fecha)` en `litros_del_dia`; no se renormaliza al
  año (+0,44 %). La traza guarda llegadas y esperas **por día y hora** (sin azar). Menú: "📅 Calendario de demanda" (prendido
  por defecto, % editables). Demanda: la cuenta litros/mes ⇒ clientes/día a la vista (≈ 252 en un mes de 31 días) con el
  factor del día, el **rango mínimo–máximo de clientes por temporada** (sale del calendario) y un filtro único para el perfil
  del día y el día a día: sin filtros hasta 7 días, selector de fechas hasta 31, y además estación / mes / vacaciones de
  invierno si la corrida es más larga. Controles nuevos (31); DEM-14 clasificado en el tornado. `verificar.py` **124/124**;
  QA `reports/qa_tanda5_calendario.py`: 0 excepciones, 0 errores de consola.
- **Tanda 6 ✅ (escenario único, conclusión y caso de informe).** `sim/periodo.py`: `EscenarioUnico` (playeros, franja,
  temporada, clientela) que arma un `Escenario` declarativo (el mismo objeto del catálogo) con `turnos_con_refuerzo` y los
  picos de `sim/escenarios.py` (**intacto**); la semana representativa de cada temporada es **CAL-09** (lunes a domingo:
  12/1, 13/4, 10/8, 12/10 y 6/7 para las vacaciones). Clientela: poca/media/alta = DEM-01; máxima = alta y el doble en el pico
  (DEM-13). Menú: "🎯 Simular el escenario único" abre una pantalla **sólo con ese escenario**: tarjetas de la franja (clientes
  por hora, playeros, ρ teórico, espera, perdidos), hora por hora, perfil del día y una **conclusión armada con esos números**
  (no alcanza / al límite / alcanza con margen). Sale la pestaña Escenarios. La **Conclusión** del flujo normal se arma con los
  resultados de la corrida (veredicto por la causa principal de pérdida, demanda, colas y ρ, pérdidas por causa, tanques, GNC,
  plata) y sugiere qué probar según lo que pasó; ya no menciona escenarios ni la búsqueda. **"📑 Caso de informe"** (botón del
  menú, fuera del flujo normal): la búsqueda de la mejor política (datos reales), el catálogo S0–S12 + la decisión en $/mes
  (sacada de Economía) y el tornado (estos dos con azar y réplicas, porque usan diferencias pareadas). Se quitó "Usar las
  mejores políticas" (el informe muestra, no aplica). Control nuevo (32). `verificar.py` **125/125**; QA
  `reports/qa_tanda6_escenario.py`: 0 excepciones, 0 errores de consola (2 → 4 playeros en el pico de verano con clientela
  máxima: ρ 2,67 → 1,34 y perdidos 59 % → 26 %).
- **Tanda 8 ✅ (red y rutas; se hizo antes que la 7).** Nota `research_notes/…/09_origenes_alternativos.md`: **La Paz y
  Pareditas no se agregan** (son cruces de ruta, no plantas); se agrega la **terminal de Arroyo Seco** (Raízen/Shell, en la
  venta a Mercuria) con un arco de 806 km a General Alvear (OSRM, estimación: **RED-18**), y Luján de Cuyo (YPF) queda como
  último recurso. Registro: RED-19 (orden: Arroyo Seco, Luján), RED-20 (5 % de pedidos que el origen no puede cumplir,
  supuesto) y RED-21 (12 h de demora por redirigir). Motor: `ParametrosRed.origenes_alternativos /
  prob_origen_no_disponible / origenes_no_disponibles` (apagados por defecto: el camión sale siempre de Dock Sud, sin sortear
  nada), `red.origen_del_pedido` y `extra_por_origen` (plazo = base − viaje desde Dock Sud + viaje desde el origen usado +
  12 h), cuatro streams nuevos al final (`origen_<producto>`), y cada `PedidoCamion` guarda su origen. `red.rutas_posibles`
  enumera las rutas simples (la primera coincide con Dijkstra). Pantalla Red y rutas: las otras rutas de mejor a peor con
  distancia, viaje y plazo; la tabla de orígenes (qué es, distancia, plazo, estado, camiones de la corrida); Arroyo Seco en
  el mapa y en la tabla de cortes. Menú: "🚚 Abastecimiento" con el interruptor de eventos y el marcado manual de orígenes.
  Control nuevo (33). `verificar.py` **127/127**; QA `reports/qa_tanda8_red.py` (Dock Sud marcado: 21 camiones desde Arroyo
  Seco a 46,6 h): 0 excepciones, 0 errores de consola.
- **Tanda 7 ✅ (alertas con pausa).** Motor: `Traza.eventos` anota, **sin sortear nada**, cada pedido de camión (con el nivel
  del tanque al cruzar s, el origen realmente usado y si se redirigió), cada descarga y cada corte de GNC (con el inicio y el
  fin del episodio entero, aunque pase el final del período). Tablero: al reproducir, se detiene en el cuadro del evento y
  muestra los carteles **de a uno y en orden** ("+N avisos más"), sin perder ninguno: "Bajo nivel de combustible: Diésel G2,
  19 %" (con el origen y la llegada) con los botones **"Seguir trayectoria del camión"** y **"Ok, seguir"**, y "El GNC se cortó
  por N días" con **cuenta regresiva** en la zona GNC y en el panel. Se puede apagar ("Pausar en los avisos"); saltar con la
  barra no dispara avisos viejos; Escape cierra. El camión se ve **llegar por la avenida y descargar** (45 min, INV-04) con el
  color de su producto. **Cambio de pestaña:** el iframe tiene `allow-same-origin`, así que el botón hace clic en la pestaña
  Red y rutas de la página y le pasa el pedido (evento del navegador + `sessionStorage`, filtrado por un número de corrida
  para no mostrar pedidos viejos). Red y rutas tiene arriba un **"Seguimiento del camión"** (componente aparte) con el segundo
  cartel ("Se ha pedido el camión de Diésel G2 a Dock Sud") y el camión moviéndose sobre su ruta. Plan B si el navegador no
  deja: el cartel dice "Abrí la pestaña 🗺️ Red y rutas". Control nuevo (34). `verificar.py` **128/128**; QA
  `reports/qa_tanda7_avisos.py`: pausa, botón, cambio de pestaña, cartel y camión descargando; 0 excepciones, 0 errores de consola.
- **Tanda 9 ✅ (mapa con relieve, opcional).** Sin Google Maps: `graficos_red.grafico_red_mapa` dibuja la red sobre teselas
  de **OpenTopoMap** (relieve, sobre OpenStreetMap y SRTM) con la atribución que pide el proveedor, coordenadas reales
  aproximadas de OSM y la ruta óptima gruesa con borde (cortes en rojo, desvío en azul). No usa dependencias nuevas (el
  `Scattermap` ya viene en Plotly) pero **necesita internet**: por eso Red y rutas deja elegir "Mapa con relieve" o
  "Esquema" (el de antes, sin conexión). Dos detalles resueltos de raíz: (1) en el Plotly de Streamlit cada texto sobre el
  mapa pide un ícono vacío a unpkg y falla (error de consola): el mapa no lleva capas de texto (las ciudades ya están rotuladas
  en el mapa base; ruta y km al pasar el mouse); (2) un mapa dibujado en una pestaña oculta quedaba angosto: el script auxiliar
  avisa un `resize` al cambiar de pestaña y el gráfico va con `responsive`. QA `reports/qa_tanda9_mapa.py`: teselas 200 OK,
  atribución visible, 0 excepciones, 0 errores de consola. `verificar.py` 128/128.

---

# Parte 3 — Temas de la cátedra: Pronóstico y Flujos en redes (14/10/2026)

> Nico eligió sumar **Pronóstico** y **Flujos en redes** (transporte, transbordo, flujo de costo mínimo, flujo máximo)
> para darle más complejidad al TP **sin perder realismo**. Teoría de juegos y Asignación quedan afuera por ahora
> (juegos necesita una elasticidad que no tenemos; asignación tendría habilidades inventadas). Árbol de expansión
> mínima: sin uso natural en una estación, no se hace.

## 15. Qué se quiere

- **Pronóstico:** pronosticar la demanda mensual con los métodos de la cátedra, medir el error (MAE, MAPE, RMSE) y que
  el pronóstico **alimente al simulador**: (1) la estacionalidad de la demanda (DEM-06, hoy neutra) y (2) el stock de
  seguridad de la política (s, Q) de cada tanque.
- **Flujos en redes:** la red de abastecimiento que ya existe (9 nodos, arcos RED-01…18, orígenes Dock Sud, Arroyo Seco
  y Luján) resuelta como **problema de transbordo / flujo de costo mínimo** para el volumen del período, y como **flujo
  máximo** para saber cuánto se puede reabastecer con una ruta cortada. Hoy Dijkstra elige la ruta de **cada camión**;
  esto agrega el **plan del mes** (cuántos camiones por qué origen y por qué arcos) y el **arco crítico** (corte mínimo).
- Todo **verificable**: cada método se prueba contra un ejercicio resuelto de la cátedra y la app muestra la cuenta.

## 16. Reglas para esta parte

- Las de la parte 2 (§10) siguen valiendo: parámetros nuevos con su `Dato`, **neutros por defecto** (dorados y 128
  controles intactos), streams nuevos sólo al final, `sim/` sin Streamlit.
- **Sin dependencias nuevas** (no hay `scipy` ni `statsmodels` en el entorno): los métodos se programan a mano en
  `numpy`, **como se enseñan en la cátedra** (es lo que se defiende en el coloquio).
- Cada método tiene un **control contra un ejercicio de la cátedra** con su resultado conocido.
- **Nada de series inventadas:** si no se consigue la serie real de ventas, se frena y se avisa (ver P1).
- Una etapa = un commit, con `verificar.py` en verde y QA con Playwright. Se informa al cerrar cada etapa; se sigue sin
  esperar salvo que falte un dato o cambie el alcance (como en la parte 2).

## 17. Decisiones y lecturas

- **Serie de ventas:** la fuente buscada son los datos abiertos de la Secretaría de Energía (ventas mensuales de
  combustibles; la prensa los cita por provincia y por empresa). Prioridad: **por estación** (si el dataset la trae, la
  Shell de Balloffet 1810) > **San Rafael / Mendoza por empresa (Shell)** > **Mendoza total**. Si sólo hay agregado, se
  usa **la forma** de la serie (índices estacionales, tendencia en %) escalada a DEM-01 (270.000 L/mes) y se rotula.
- **Métodos:** promedio móvil, suavizado exponencial simple, tendencia (A + B·t por mínimos cuadrados) y **tendencia
  estacional multiplicativa** (índices estacionales × tendencia). Se elige por **RMSE en los meses de prueba**
  (entrenamiento con todos menos los últimos 12). IC del pronóstico = ± z·RMSE.
- **Estacionalidad en el simulador:** los índices del pronóstico entran como **una opción más** del menú "📅 Calendario
  de demanda" (calendario de temporadas DEM-14 / **índices del pronóstico** / neutra). Cuál queda por defecto lo decide
  Nico al ver los números (P3).
- **Stock de seguridad:** `s = D̂_día × plazo + z · σ_día · √plazo`, con D̂ del pronóstico del mes, plazo de INV-01 (36 h)
  y σ_día derivado del RMSE (supuesto rotulado: errores diarios independientes). Entra como **una política candidata
  más** en la búsqueda de la mejor política y como opción del menú "🚚 Abastecimiento"; el simulador la compara (quiebres,
  camiones, costo) contra la (s, Q) actual.
- **Red como flujo:** un solo bien, **camiones cisterna** (Σ litros del período por producto ÷ carga INV-02), porque la
  capacidad de los arcos es de camiones y no de producto; después se reparte por producto en proporción. El GNC no entra
  (viene por gasoducto). Datos nuevos, todos **supuestos rotulados**: capacidad de cada arco (camiones/día), oferta de
  cada origen para esta estación (camiones/mes) y costo por km (ECO-06, heredado). Con la red sana y sin límites el plan
  manda todo desde Dock Sud, que es lo que pasa en la realidad. **Lo interesante aparece con cortes, un origen no
  disponible o un límite de capacidad**, y eso es lo que se muestra.
- **Del plan a la simulación:** opción (apagada por defecto) "Despachar según el plan": los pedidos de camión salen de los
  orígenes en las proporciones del plan (cuotas exactas, sin azar). Así el flujo es el **plan** y la simulación la
  **ejecución** (plazos, quiebres).

## 18. Etapas

| Etapa | Qué incluye | Compuerta |
|---|---|---|
| **P1 · Serie real** | Buscar y bajar la serie mensual de ventas (Secretaría de Energía, datos abiertos); nota `research_notes/…/12_serie_ventas.md` con URL, alcance, unidad y criterio (§17); la serie entra al Registro (**PRO-01**, nivel y confianza según lo que se consiga) junto con los meses de prueba (**PRO-02** = 12) y el z del IC (**PRO-03**) | La serie tiene fuente y URL. **Si no se consigue ni la provincial, se frena y se le pregunta a Nico** (no se inventa) |
| **P2 · Métodos de pronóstico** | `sim/pronostico.py` (sin Streamlit, `numpy`): los cuatro métodos, MAE / MAPE / RMSE / sesgo, IC, backtest entrenamiento/prueba y elección por RMSE | Controles con el práctico de Pronóstico: Cable Televisora con los pronósticos dados ⇒ **MAE = 107/12 = 8,92** y **RMSE = 37/√12 = 10,68**; tendencia A = 1.650, B = 30 ⇒ **2.010 · 2.040 · 2.070** para t = 12, 13, 14; los índices estacionales promedian 1 |
| **P3 · Pronóstico en la app** | Pestaña **📈 Pronóstico** (después de Demanda): la serie real y el ajuste de cada método, tabla de errores, el método elegido y por qué, los próximos 12 meses con su IC, "¿Cómo se comprueba?" con las cuentas; en el menú, la opción de estacionalidad "índices del pronóstico" (§17) | Control: con la opción apagada la corrida es idéntica; con la opción, Σ de litros del año = la del pronóstico; QA, 0 errores de consola |
| **P4 · Stock de seguridad** | Política "por pronóstico" (§17) en la búsqueda de la mejor política (Caso de informe) y en el menú de abastecimiento; Inventario muestra la cuenta del s de cada tanque | Control: con z = 0 el s es la demanda del plazo; el s de la app = la fórmula a mano; la búsqueda la evalúa como una más |
| **F1 · Algoritmos de red** | `sim/flujos.py` (sin Streamlit): transporte (rincón noroeste, costo mínimo, Stepping-Stone), transbordo / flujo de costo mínimo (caminos más cortos sucesivos), flujo máximo (trayectorias de aumento) con corte mínimo | Controles con la cátedra: transbordo **P1/P2 → T1/T2 → D1/D2/D3 = $20.700**; flujo máximo del **oleoducto Neuquén → Buenos Aires** (TP 5, ej. 1) con el resultado del TP resuelto; transporte del Problema 1 (Tijuana / Boston / Montreal) con rincón noroeste y costo mínimo; en redes chicas, el óptimo = la enumeración de todas las soluciones |
| **F2 · Datos de la red como flujo** | Registro: capacidad de cada arco, oferta de cada origen y costo por km (§17, supuestos rotulados, con nota de dónde saldría el dato real); `ParametrosRed` gana esos campos, neutros por defecto | Control: con los defaults la corrida es idéntica (dorados, 128 controles) |
| **F3 · Red y rutas: el plan del mes** | En Red y rutas: el **plan de transbordo** del período (camiones por arco y por origen, costo total, contra "todo por la ruta más corta"); qué pasa con un corte (RN 143, RN 40) o con un origen no disponible; **flujo máximo** con la ruta cortada y el **arco crítico**; la matriz de transporte al estilo de la cátedra; opción "Despachar según el plan" (§17) | Control: Σ salidas de los orígenes = camiones del período; el costo del plan ≤ el de cualquier ruta única; con "Despachar según el plan" apagado la corrida es idéntica; QA, 0 errores de consola |
| **C3 · Cierre** | `CLAUDE.md` (qué modela, controles), `DATOS_REALES.md` regenerado, memoria al día | `verificar.py` en verde; QA de las pestañas nuevas |

**Orden:** P1 primero porque todo el pronóstico depende de la serie; si P1 se traba esperando un dato, se adelanta **F1**
(no depende de nada) y se vuelve. P2 antes que P3 y P4. F1 → F2 → F3. El cierre al final.

## 19. Avance

- **P1 ✅ (serie real).** Fuente: Secretaría de Energía, datos abiertos, "Refinación y comercialización… (Tablas
  dinámicas)", recurso "Ventas (excluye ventas a empresas del sector)" (actualizado el 2-oct-2026). Filtro: **SHELL
  C.A.P.S.A.** (la bandera de la estación), **Al Público**, **Mendoza**, Súper + Ultra + gasoil G2 + G3: 92 meses
  (ene-2019 – ago-2026), sin faltantes. **No hay datos por estación**: es la suma de las Shell de Mendoza (≈ 11–16 mil m³
  por mes, 16,6 % del mercado provincial en 2026), así que se usa la forma de la serie escalada a DEM-01. Nota
  `research_notes/…/12_serie_ventas.md` (URL, filtro, totales por año verificados). Registro: **PRO-01** (la serie, dato,
  nivel C), **PRO-02** (ventana desde ene-2022 —sin la pandemia ni el rebote de 2021— y 12 meses de prueba), **PRO-03**
  (z = 1,96) y **PRO-04** (promedio móvil de 3 meses, α = 0,3). `verificar.py` 133/133.
- **P2 ✅ (métodos).** `sim/pronostico.py` (sin Streamlit ni dependencias nuevas): promedio móvil, suavizado exponencial
  simple, tendencia (recta de mínimos cuadrados), estacional (promedio × índice) y tendencia estacional multiplicativa
  (índices por cocientes al promedio móvil centrado de 12 meses, normalizados a 1; recta sobre la serie
  desestacionalizada); MAE, MAPE, RMSE y sesgo; se ajusta con ene-2022 – ago-2025, se prueba en los 12 meses siguientes,
  se elige el de menor RMSE, se reajusta con toda la ventana y se pronostican 12 meses con ± z·RMSE. **Validación con la
  cátedra:** Cable Televisora da MAE = 107/12 = 8,92 y RMSE = 37/√12 = 10,68, y **la recta de mínimos cuadrados de sus
  datos (A = 1.702,4, B = 23,09) reproduce los pronósticos del práctico**; Lincoln Motors da índices trimestrales
  0,81 · 1,28 · 1,19 · 0,73. **Resultado con la serie real:** los métodos quedan casi empatados (RMSE en m³: promedio
  móvil 812 · tendencia 814 · tendencia estacional 832 · suavizado 1.148 · estacional 2.100); gana el **promedio móvil**
  (MAPE 6,2 %). Todos tienen sesgo negativo: la serie bajó más de lo que cualquiera esperaba. Índices estacionales:
  ene 0,99 · feb 1,00 · **mar 1,06** · abr 0,95 · may 1,02 · **jun 0,91** · jul 1,00 · ago 1,03 · sep 0,97 · oct 1,03 ·
  nov 1,00 · **dic 1,05**; tendencia −0,46 % por mes. **Hallazgo:** en Shell Mendoza el verano **no** vende más
  (enero 0,99), al revés del supuesto DEM-14 (verano × 1,06). Control nuevo (39). `verificar.py` **135/135**.
- **P3 ✅ (pronóstico en la app).** Pestaña **📈 Pronóstico** (después de Demanda): de dónde sale la serie (oficial, Shell
  Mendoza, no la estación), tarjetas (método elegido, MAPE, tendencia), el gráfico de la serie con el ajuste del elegido,
  la zona de prueba y el pronóstico con su banda ± z·RMSE, la tabla de los cinco métodos (MAE, MAPE, RMSE, sesgo), el
  gráfico de los 12 índices, los próximos 12 meses en m³ y **escalados a la estación** (DEM-01 ÷ el promedio de los últimos
  12 meses de Shell Mendoza = 2,31 %) y "¿Cómo se comprueba?". Menú: en 📅 Calendario de demanda, **cómo cambia la
  demanda a lo largo del año**: calendario de temporadas (por defecto) · **índices de la serie real** · neutra; con los
  índices reales, `Estacionalidad` = los 12 índices y sin calendario (el total del año no cambia: 3.240.000 L con o sin
  índices). Demanda muestra el índice del mes en la cuenta del día. **Queda por defecto el calendario** (decide Nico).
  Control nuevo (40). `verificar.py` **136/136**; QA `reports/qa_p3_pronostico.py`: 2 gráficos y 2 tablas, el encabezado
  dice la forma elegida, 0 excepciones, 0 errores de consola (se corrigió el orden del eje: los meses del pronóstico
  aparecían a la izquierda).
- **P4 ✅ (stock de seguridad).** `pronostico.stock_de_seguridad`: **s = D·L + z·σ_día·√L**, con D = litros por día del
  producto (DEM-01 × su parte ÷ 30), L = plazo medio del camión (INV-01: 1,5 días), z = 1,96 y σ del **error del
  pronóstico de la serie real** (RMSE de prueba ÷ nivel = **6,94 %**; σ_mes = error × D × 30 y σ_día = σ_mes ÷ √30,
  supuesto: errores diarios independientes); Q queda la cargada. Resultado: s Súper 6.100 · V-Power 4.200 · G2 6.400 · G3
  5.000 L (la cargada, INV-07, es 1,5 días de venta: 3.780 · 2.633 · 3.956 · 3.132). Menú 🚚: interruptor **"Punto de
  pedido por pronóstico"**; Inventario: sección 4 con la cuenta de cada tanque y si la corrida la usa; Caso de informe:
  la búsqueda prueba **14 políticas** (la del pronóstico es la candidata 14; la grilla de 13 no se tocó porque la usan los
  escenarios y el control 18). **Efecto, año completo con datos reales:** clientes sin combustible **1.423 → 0**, días con
  quiebre **113 → 0**, camiones 314 → 320. Control nuevo (41). `verificar.py` **137/137**; QA `reports/qa_p4_stock.py`: 0
  excepciones, 0 errores de consola (la búsqueda de 30 días termina en 7 s).
- **F1 ✅ (algoritmos de red).** `sim/flujos.py` (sin Streamlit ni dependencias nuevas): transporte con **rincón
  noroeste**, **costo mínimo** (empate: la primera celda en orden de lectura, como en las diapositivas) y **MODI /
  Stepping-Stone** (potenciales, índice de mejora, circuito con θ; ficticio si no está balanceado y celdas con 0 si es
  degenerado); **matriz de transbordo** de la cátedra (nodos de paso con oferta y demanda B, costo 0 consigo mismos, M sin
  arco); **flujo de costo mínimo** (caminos más cortos sucesivos con Bellman-Ford) y **flujo máximo** (trayectorias de
  aumento por BFS) con el **corte mínimo**. **Validación con la cátedra:** el ejemplo de las diapositivas da rincón noroeste
  $4.200, costo mínimo $4.100 y óptimo **$3.900** desde las dos (igual a enumerar todas las asignaciones); el transbordo
  P1/P2 → T1/T2 → D1/D2/D3 da **$20.700** con el flujo de costo mínimo **y** con la matriz (B = 2.200; D1 y D2 con demanda
  3.000 y 3.100); el oleoducto Neuquén → Buenos Aires (TP 5) da **205.000 gal/h**, igual a la capacidad del corte mínimo
  (Galleta→Buenos Aires + Pirámide→Río Negro). Control nuevo (42). `verificar.py` **139/139**.
- **F2 ✅ (la red real como flujo).** Registro: **FLU-01** (capacidad 1 por tramo para contar **rutas independientes**:
  teorema de Menger, no es tránsito) y **FLU-02** (cuánto puede despachar cada origen para esta estación: hoy Dock Sud
  100 %, Arroyo Seco 0 %, Luján 0 %; supuesto, editable). **Cambio de plan respecto de §17:** las capacidades por tramo en
  camiones por día se descartaron (serían inventadas y nunca limitan con tan pocos camiones); lo que limita son los
  **topes de los orígenes** y los **cortes**. `sim/flujos.py`: `plan_de_abastecimiento` (transbordo con un nodo ficticio
  que reparte los camiones entre los orígenes hasta su tope, costo = km) y `rutas_independientes` (flujo máximo con
  capacidad 1 y corte mínimo). `ParametrosRed.cuotas_origen` (vacío por defecto): **despachar según el plan**, con cuotas
  exactas por producto y el plazo corregido por la diferencia de viaje (sin la demora de redirección). **Resultados:** con
  la red sana el plan manda todo desde Dock Sud (991,3 km por camión); si Arroyo Seco pudiera despachar la mitad, el
  camión-km baja 4,9 % (Arroyo Seco está 97,8 km más cerca); con el corte E4 (Alvear–San Rafael) todo va por Luján y
  Pareditas (1.278 km) y Arroyo Seco deja de convenir; a San Rafael llegan **3 rutas independientes** y el corte mínimo
  son 3 tramos (Luján–Pareditas, Alvear–San Rafael, Luján–La Paz). Control nuevo (43; con 100 % Dock Sud la corrida es
  idéntica). `verificar.py` **141/141**.
- **F3 ✅ (Red y rutas: el plan del período).** Sección nueva al final de 🗺️ Red y rutas: los topes de Arroyo Seco y Luján
  y el corte se prueban ahí mismo; tarjetas (camiones del período = los que pidió la simulación, camión-km del plan,
  diferencia contra "todo desde Dock Sud", rutas independientes), de dónde sale cada camión, los tramos usados, el corte
  mínimo, y un desplegable con **la misma cuenta como problema de transporte de la cátedra** (orígenes × tanques: rincón
  noroeste, costo mínimo, óptimo con MODI y ficticio si sobra oferta) y **como transbordo con la matriz B** (da lo mismo que
  el flujo). Menú 🚚: los topes de Arroyo Seco y Luján y **"Despachar según el plan"** (`Ajustes.topes_origen /
  despachar_plan` → `cuotas_origen`); con los topes de hoy el plan es todo Dock Sud y la corrida no cambia. Ejemplo, enero
  con Arroyo Seco al 40 %: −3,9 % de camión-km (20.948 contra 21.809). Control nuevo (44). `verificar.py` **142/142**; QA
  `reports/qa_f3_plan.py`: 0 excepciones, 0 errores de consola.
- **C3 ✅ (cierre de la parte 3).** `verificar.py` **142/142**; se repitieron los QA de las partes 3 y 4 sobre la app final
  (`qa_e0_gnc`, `qa_e3_eventos`, `qa_p3_pronostico`, `qa_p4_stock`, `qa_f3_plan`): 0 excepciones y 0 errores de consola en
  todos. `CLAUDE.md` dice qué modela ahora (pronóstico y flujos) y `DATOS_REALES.md` trae PRO-01…04 y FLU-01…02.
  **Para decidir (Nico):** (1) el calendario de temporadas sigue por defecto aunque la serie real dice que en Shell
  Mendoza el verano no vende más (enero 0,99); se puede pasar a "índices de la serie real" por defecto; (2) el punto de
  pedido por pronóstico elimina los quiebres del año con datos reales (1.423 → 0 clientes sin combustible) con 6 camiones
  más: se puede volver la política por defecto. **Parte 3 cerrada.**

## 26. Pendientes de §24 (Nico eligió 1, 2 y 4 el 14/10/2026)

- **G1 ✅ (tabla de camiones).** `ResultadoReplica.camiones` (cada `PedidoCamion` del período medido) y
  `red.ruta_del_viaje` (la ruta que hizo cada camión: la óptima desde su origen, el **desvío** si la demora coincide con lo
  que alarga el camino sin el tramo cortado, o la misma ruta si **esperó** que reabrieran). Inventario, sección **5. Cada
  camión, de punta a punta**: N°, tanque, cuándo se pidió y llegó, plazo, origen (y si se redirigió), ruta, km, cómo vino
  (con la demora y la causa), litros y flete (ECO-06), con filtro por tanque y el total que cierra con los pedidos de
  Indicadores. El control 19 ahora compara los camiones sin el origen (sin red queda vacío). Se corrigió que dos `$` en un
  mismo texto de pantalla se leían como fórmula (pie de la tabla, horas extra de Eventos y comprobación del plan de red).
  Control nuevo (45). `verificar.py` **143/143**.
- **G2 ✅ (Red y rutas: nafta, diésel y GNC; cortes sólo si se editó).** Sección **"La red de cada producto"**: nafta y
  diésel llegan en camión (desde dónde, por qué ruta, camiones, plazo medio y litros de la corrida) y el **GNC por
  gasoducto**, con un diagrama de la cadena real: gasoducto internacional GasAndes → empalme en el paraje La Tosca (planta
  ESMO) → gasoducto San Rafael (inaugurado el 17-jun-2026) → planta reguladora sobre la RN 143 (42.000 m³/h) → red de
  Ecogas → la estación (3 compresores). Registro **GNC-11** (informativo; nota `research_notes/…/13_red_gnc.md` con las
  fuentes; las notas de prensa no aclaran si el gasoducto mide 28 o 50 km y se dicen los dos). **"Qué le hace cada corte a
  cada origen"**, el plazo con y sin cortes y el efecto en el quiebre aparecen **sólo si se editó** (simulación editada,
  escenario de cortes, eventos de abastecimiento o despacho según el plan); con datos reales, una línea explica por qué no
  están y que los cortes se prueban en el plan del período. Se sacaron las menciones a la "barra lateral" de esa pestaña.
  `verificar.py` **143/143**; QA `reports/qa_g_pendientes.py`: 0 excepciones, 0 errores de consola.
- **G3 ✅ (limpieza de `app.py`).** Se calculó qué funciones de `app.py` se alcanzan desde `main()` y se borró el resto en
  vueltas (la barra lateral `leer_parametros` y lo que sólo ella usaba, las pestañas viejas de Escenarios, Economía y
  Estaciones, tablas y promedios del modo clásico); los despachadores `if p.estacion_real: … else <modo clásico>`
  (Inventario, Conclusión, Modelo, Demanda vieja), los avisos "no hay red / no hay GNC en el caso clásico", la
  recomendación del modo clásico que se calculaba y no se leía, los imports y constantes sin uso y los encabezados
  huérfanos. **`app.py`: 3.743 → 2.368 líneas** (−1.375), sin menciones a la barra lateral. `ParametrosSimulacion.clasico()` y el
  motor clásico siguen en `sim/` (los usa `verificar.py` para los dorados, N1). `verificar.py` **143/143**; se corrió la
  batería de QA completa (`qa_g_pendientes`, `qa_e0_gnc`, `qa_e3_eventos`, `qa_p3_pronostico`, `qa_p4_stock`,
  `qa_f3_plan`, `qa_tanda3`…`qa_tanda8`): 0 excepciones; 0 errores de consola (la tanda 7 dio 14 "Failed to fetch" con el
  servidor cargado y 0 al repetirla sola).

## 27. Decisiones de Nico sobre los valores por defecto (14/10/2026)

- **"Poné lo real":** la forma de la demanda a lo largo del año sale por defecto de los **índices de la serie real** de
  Shell Mendoza (PRO-01); el calendario de temporadas (DEM-14, supuesto) y la demanda sin forma quedan como opciones del
  menú. El total del año no cambia (los índices promedian 1).
- **"La real o la más conveniente":** la política real de la estación no está documentada (INV-06), así que va **la más
  conveniente**: se evaluaron las 14 candidatas (la de INV-07, las 13 de la grilla y la del pronóstico) en el año completo
  con datos reales y los índices reales, y la más barata es **s = 2 días y Q = 4,5 días de venta** (**INV-13**, supuesto con
  su evaluación): $4,52 M/mes contra $4,66 M la del pronóstico y $4,95 M la de INV-07, con 14 L/mes sin vender. Por tanque,
  Súper y G2 prefieren esta y V-Power y G3 la del pronóstico; se eligió una sola para todos por simple. Las otras dos quedan
  como opciones en el menú 🚚. Ojo: los costos usan márgenes y flete heredados sin fuente (ordenan, no son del negocio).
- `Ajustes()` ahora **es** lo que usa la app por defecto (`politica="conveniente"`, `indices_reales=True`,
  `calendario=False`); los controles que probaban el Registro puro o el calendario lo piden explícito. `runner.politica_en_dias`
  arma (s, Q) en días de venta (la grilla la usa). Control nuevo (46: INV-13 es la más barata de las 14 en el año y es la
  que carga la app). `verificar.py` **144/144** (ahora tarda ≈ 5 min por ese control). QA: los scripts que dependían del
  valor por defecto viejo (`qa_p4_stock`, `qa_tanda5_calendario`, `qa_p3_pronostico`) piden la opción explícita; 0
  excepciones, 0 errores de consola.

---

# Parte 4 — Eventos aleatorios que alteran la estación (14/10/2026)

> Pedido de Nico: eventos discretos **al azar** que cambian el funcionamiento de la estación (un playero que se va, una
> licencia con horas extra, un aumento de precio, un faltante con cupo…), **por lo menos 10**, que se prenden y apagan
> desde el **menú principal**. Aprobó la lista de 14 de §21 el 14/10/2026.

## 20. Decisiones de Nico (14/10/2026)

- **El GNC lo carga un playero** (en las estaciones argentinas el GNC es atendido, no hay autoservicio). Hoy el modelo
  dice lo contrario (PER-04 = "no retiene playero, sólo conecta la manguera"): **es un error de lógica y se corrige
  primero** (etapa E0; el efecto medido está en §25).
- **Turnos:** los que ya están (noche 22–06 · mañana 06–14 · tarde 14–22, PER-01). El ejemplo "se va a las 3 y vuelve
  alguien a las 8" era ilustrativo: **el hueco dura hasta el próximo cambio de turno** (a las 06 si es de noche).
- **Aumento de precio (+10 %):** sube el precio; **el margen en $ por litro queda igual** (si se ganaban $100 por litro,
  se siguen ganando $100). Cambia la facturación, no la ganancia por litro; lo que se ve es la gente que **se adelanta a
  cargar el día anterior**.
- **"Caída de nafta" = faltante con cupo:** menos camiones (tardan más y traen menos) y **cada cliente carga como máximo
  30 L**, es decir, menos litros por cliente.
- Se suman los dos de reserva: **evento masivo en San Rafael** y **asalto**. Total: 14 eventos.

## 21. Los 14 eventos

Frecuencias y duraciones: **supuestos rotulados** (no hay registros de la estación); donde hay un dato real que respalde
el evento, se cita. Cada evento es un `Dato` del Registro (**EVT-01…EVT-14**) con frecuencia, duración y efecto editables.

| # | Evento | Qué hace en la simulación | Frecuencia · duración (supuesto) | Costo / efecto |
|---|---|---|---|---|
| **Personal** |||||
| 1 | Abandono repentino del turno | A una hora sorteada, un playero se va; **nadie lo reemplaza hasta el próximo cambio de turno** | ≈ 1 cada 2 meses · hasta el cambio de turno | De noche (1 playero) **la estación queda sin atención**; en el pico, 2 → 1. Venta perdida |
| 2 | Licencia por accidente, cubierta con horas extra | Un playero falta N días; otro hace horas extra y el turno **no** queda corto | ≈ 1 cada 6 meses · 3–15 días | **Horas extra** con recargo 50 % (día hábil) y 100 % (sábado después de las 13, domingo y feriado), LCT art. 201 |
| 3 | Falta sin aviso | El turno arranca con un playero menos las 8 h | ≈ 2 por mes · un turno | Venta perdida |
| 4 | Licencia sin reemplazo | Como el 2, pero no consiguen a nadie: el turno queda corto esos días | 30 % de las licencias | Venta perdida (sin horas extra) |
| **Equipos** |||||
| 5 | Falla de un surtidor | Una cara sorteada queda fuera de servicio hasta que llega el técnico | ≈ 1 por mes · 2–24 h | En diésel (2 caras) queda 1. Venta perdida + visita del técnico |
| 6 | Falla de un compresor de GNC | 3 → 2 compresores (SUR-06) | ≈ 1 cada 2 meses · 4–48 h | Más espera en GNC |
| 7 | Corte de luz | Sin surtidores ni compresores: **la estación se para** | más probable dic–feb · 1–4 h | Venta perdida |
| 8 | Se cae el sistema de cobro | Sólo efectivo: el cobro tarda más | ≈ 1 por mes · 1–6 h | Más espera y abandonos |
| **Precio y abastecimiento** |||||
| 9 | Aumento de precio +10 % | Desde la fecha, precio × 1,10 con **margen igual**; el día anterior, **+20 % de clientes** (se adelantan a cargar) | ≈ 1 por mes | Pico de colas y riesgo de quiebre el día anterior; facturación +10 % |
| 10 | Faltante con cupo | N días: camiones con más plazo y menos carga, y **máximo 30 L por cliente** | ≈ 1 por año · 3–7 días. Precedentes: faltante de gasoil 2022 con cupos; crisis de Mendoza 2023 (INV-09) | Menos litros por cliente, tanques bajos, quiebres. La crisis S7 pasa a ser también un evento |
| 11 | Rotura del camión en ruta | Un pedido sorteado llega 12–48 h tarde | 5 % de los viajes | Riesgo de quiebre en ese tanque |
| **Demanda y seguridad** |||||
| 12 | Corte de la avenida (choque u obra) | La mitad de las llegadas durante N horas | ≈ 1 por mes · 2–8 h | Menos ventas |
| 13 | Evento masivo en San Rafael (fiesta, fin de semana largo) | Más llegadas ese día (DEM-09 "Eventos" ya está en el Registro) | ≈ 4 por año · 1–3 días | Más colas, más ventas |
| 14 | Asalto | La estación se para mientras actúa la policía | ≈ 1 por año · 30–60 min | Venta perdida |

## 22. Cómo funcionan

- **Apagados por defecto:** con todos apagados la corrida es **idéntica** a la de hoy (dorados y controles intactos).
- **Sólo se sortean los eventos.** Llegadas, mezcla y tiempos siguen con los datos reales sin azar. Cada evento tiene su
  **stream propio al final de `STREAMS`** y la **semilla se muestra**: con la misma semilla se repiten los mismos eventos.
  El encabezado dice "datos reales + eventos sorteados (semilla N)".
- **Mecanismos del motor** (cada uno se prueba por separado): playeros de menos hasta una hora (reserva extra en el
  recurso de playeros, como hoy los turnos), cara fuera de servicio, compresor fuera de servicio, estación parada,
  factor sobre las llegadas en una franja, cobro más lento, tope de litros por cliente, demora o menor carga de un
  camión, precio × factor desde una fecha.
- **Pantalla:** desplegable **"⚡ Eventos aleatorios"** en el menú principal (casilla por evento, frecuencia editable,
  semilla); cada evento es un **aviso con pausa** en la animación (el sistema de la tanda 7); tabla **"Eventos del
  período"** (cuándo, cuánto duró, clientes perdidos, costo); los eventos también figuran en "Qué se sorteó" y en la
  Conclusión; Economía suma **"Costo de los eventos"** (horas extra, técnico) aparte de la venta perdida.

## 23. Etapas

| Etapa | Qué incluye | Compuerta |
|---|---|---|
| **E0 · GNC con playero** | PER-04 pasa a "sí": el cliente de GNC necesita playero **y** compresor durante la carga; nota en `research_notes/` (el GNC es atendido); se corrigen los textos y las cuentas de ρ que dicen "el GNC no usa playero" (`config.rho_pico`, escenario único, Indicadores, `ui/textos.py`); el eje del tornado que probaba "GNC con playero" se reemplaza | `clasico()` intacto (no tiene zonas); se actualizan los controles que suponían GNC sin playero; QA |
| **E1 · Motor de eventos: personal y equipos** | `sim/eventos.py` (catálogo, sorteo con streams nuevos, calendario de eventos de la corrida); eventos 1–8 y 14 en el motor; registro en `Traza.eventos` | Apagado ⇒ idéntico; misma semilla ⇒ mismos eventos; un control por mecanismo (p. ej. estación parada ⇒ 0 atendidos en esa franja; playero de menos ⇒ la dotación vuelve en el cambio de turno) |
| **E2 · Precio, abastecimiento y demanda** | Eventos 9–13; costo de horas extra (LCT art. 201) y del técnico | Cupo ⇒ ninguna carga supera 30 L; aumento ⇒ margen por litro igual y facturación × 1,10; Σ costos de eventos = suma de la tabla |
| **E3 · Menú y pantalla** | Desplegable "⚡ Eventos aleatorios", avisos en la animación, tabla de eventos, Qué se sorteó, Conclusión y Economía | QA con Playwright: prender y apagar cada evento, avisos con pausa, 0 errores de consola |

**Orden:** E0 primero (el evento 1 depende de que el GNC use playero: de noche deja **toda** la estación sin atención).
Después E1 → E2 → E3. Esta parte puede ir antes o después de la parte 3; lo decide Nico.

## 24. Lo que falta del orquestador (al 14/10/2026)

Lo de la parte 1 que **no** quedó cubierto por las tandas de la parte 2:

- ~~**Inventario (etapa 5):** tabla de camiones~~ → hecho en G1 (§26). Antes: no había una **tabla de camiones** con día de pedido, día de llegada, origen, ruta, km y costo
  de cada viaje (los datos ya están en el motor, `PedidoCamion` y `Traza.eventos`; falta mostrarlos).
- ~~**Red y rutas (etapa 5)**~~ → hecho en G2 (§26). Pedía "la red de nafta, de diésel **y de GNC**": la del GNC (gasoducto) no está dibujada; la
  pestaña GNC sólo dice que el gas viene de la red. "Qué le hace cada corte a cada origen sólo si se editó": hoy la tabla
  de cortes se muestra siempre.
- **Frontend (etapa 7):** el tema oscuro en toda la app y el menú lateral como la imagen; **Nico inicia la skill de
  diseño ("impeccable")** cuando llegue el momento.
- ~~**Limpieza:** la barra lateral vieja~~ → hecho en G3 (§26).
- **Cierre (etapa 8):** la tabla de §3 y los pendientes de §5 quedaron viejos (no marcan lo hecho en la parte 2).

Partes nuevas: **parte 3** (Pronóstico y Flujos, P1–P4, F1–F3, C3) y **parte 4** (Eventos, E0–E3), cerradas.
Orden acordado con Nico (14/10/2026): **E0 → eventos (E1–E3) → pronóstico y flujos → pendientes de arriba → frontend**.

## 25. Avance de la parte 4

- **E0 ✅ (el GNC lo carga un playero).** Nota `research_notes/…/10_gnc_atendido.md`: servicio atendido de la propia
  estación (EST-07), observación de Nico, ENARGAS Res. 369/2020 (sin personas a bordo); el Decreto 70/2023 habilita el
  autoservicio como **opción**, que queda como alternativa. Registro: **PER-04 = sí** (dato, confianza media) y la zona C
  de SUR-00 con playero; `grupos_desde_registro` lee PER-04. Motor: el cliente de GNC toma **cara → playero →
  compresor** (siempre en ese orden) y el playero queda con el auto mientras espera el compresor y mientras carga; la
  alternativa sin playero sigue funcionando (eje C9 del tornado: "GNC en autoservicio"). Antes, esa alternativa saltaba
  el compresor y el chequeo del corte: quedó corregido en el mismo camino. ρ teórico =
  λ_pico · [(1 − g) · E[S_líquidos] + g · E[S_GNC]] ÷ playeros (`media_servicio_playero`), en el método, en el escenario
  único y en el tornado. **Economía:** la venta perdida "por corte de GNC" sumaba **todo** el GNC no vendido (también el
  de los clientes que se cansan de esperar): ahora cuenta sólo los m³ perdidos por el corte. Textos corregidos (modelo,
  supuestos, tablero: "lo carga un playero"). **Efecto** (datos reales): ρ pico 0,85 → **0,89**; julio 7.677 → **7.664**
  atendidos; año completo 91.949 → **91.760** atendidos, 73 → **286** clientes que se van por la espera. Control nuevo
  (35: autos cargando = playeros ocupados en los 89.280 cuadros de julio; ρ a mano). `verificar.py` **129/129**; QA
  `reports/qa_e0_gnc.py`: escenario único, tablero, modelo y método e indicadores sin textos viejos, 0 excepciones, 0
  errores de consola.
- **E1 ✅ (motor de eventos: personal y equipos).** `sim/eventos.py` (sin Streamlit): el catálogo de los 14 eventos y el
  **calendario** de la corrida, sorteado antes de correr con una **semilla propia** y **un stream por evento** (al final
  de `STREAMS`); se sortean todos aunque estén apagados y después se filtran, así que prender uno no corre las fechas de
  los otros. Registro: **EVT-00** (prendidos, semilla, multiplicador de frecuencia; apagados por defecto), **EVT-01…14**
  (probabilidad por día, duración y efecto; supuestos del grupo, con los respaldos reales que hay: LCT art. 201, INV-09,
  DEM-09) y **EVT-15** (200 h/mes para el valor de la hora); nota `research_notes/…/11_eventos_aleatorios.md`.
  `ParametrosEventos` en `ParametrosSimulacion.eventos` (N14). Motor, eventos 1–8 y 14: un playero menos (reserva con
  prioridad −1 hasta el cambio de turno, un turno, o el mismo turno todos los días de la licencia), estación parada (todos
  los playeros y compresores reservados), cara fuera de servicio (reserva en la zona, dibujada tachada: código −2 en los
  carriles), compresor fuera, cobro lento (+1 min por carga, caja × 1,5); la licencia cubierta no cambia el servicio. Las
  caras pasaron a `PriorityResource` (los autos piden con la misma prioridad: sigue siendo FIFO; **sin eventos la
  corrida da idéntica** a la anterior en enero, julio, el año y con azar). Cada evento cuenta los clientes que se fueron
  mientras duraba (`ResultadoReplica.eventos`) y se anota en la traza para los avisos. Control nuevo (36: mismo
  calendario con la misma semilla, filtrado sin correr fechas, sin eventos idéntico; cada mecanismo en su propia
  corrida de enero ×5 —17 paradas, 12 de un playero, 4 caras, 3 compresores— sin descuadres playero/auto y con
  conservación de clientes). `verificar.py` **131/131**; la app corre igual (QA de E0: 0 excepciones, 0 errores de consola).
  Ejemplo, enero con datos reales y los eventos de E1 (semilla 1): 10 eventos (3 cortes de luz, 1 cara de GNC 23 h, 1
  licencia sin reemplazo de 9 días en la mañana, 3 faltas…); atendidos 7.682 → 7.284.
- **E2 ✅ (precio, abastecimiento y demanda; costos).** Eventos 9–13 en el calendario y el motor: **aumento de precio**
  (+10 % con el mismo margen en $/L; el día anterior +20 % de clientes), **faltante con cupo** (máx. 30 L por cliente; los
  camiones pedidos esos días traen la mitad y tardan el plazo de crisis INV-09), **rotura del camión** (se sortea en cada
  viaje, stream `evento_11_viaje`: 12–48 h más), **corte de la avenida** (cada cliente entra con probabilidad 0,5, stream
  `evento_12_llegadas`; los que no entran no son llegadas) y **evento masivo** (+30 %, el piso de DEM-09).
  `EventoOcurrido.extra` guarda lo que hizo cada uno (clientes de más o que no llegaron, litros recortados, horas de
  demora). **Economía:** `costo_eventos` (horas extra de las licencias cubiertas con el recargo de la LCT art. 201 y la
  visita del técnico, sin dato = 0) entra en `costo_total`; la venta perdida sigue aparte. Control nuevo (37: llegadas =
  base + de más − no llegaron; cupo ⇒ ≤ 30 L por carga y camiones con la mitad y ≥ 72 h; cada rotura es un pedido 12–48 h
  más tarde; costo de las horas extra calculado a mano). `verificar.py` **132/132**. Ejemplo, enero con los 14 eventos y
  frecuencia × 2 (semilla 1): 27 eventos, llegadas 7.791 → 7.988, atendidos 7.682 → 7.053, horas extra $403.200/mes.
- **E3 ✅ (menú y pantalla).** Menú principal: desplegable **"⚡ Eventos aleatorios"** con una casilla por evento en
  cuatro grupos (la ayuda "?" dice qué hace y cada cuánto pasa), **Prender todos / Apagar todos**, la **frecuencia**
  (la del Registro, el doble, × 5 para verlos en un período corto, la mitad), la **semilla** y una vista previa ("con
  esta semilla, en el período salen N eventos"). `Ajustes` guarda los eventos y `aplicar_ajustes` arma
  `ParametrosEventos`; sin eventos, la corrida es la del Registro. Resultados: aviso "Con eventos aleatorios: ocurrieron
  N (semilla S)" y la pestaña **⚡ Eventos** (sólo si hay eventos prendidos): cómo se sortearon, tarjetas (cuántos,
  clientes perdidos mientras duraban, costo), la tabla **"Lo que pasó, en orden"** (cuándo, evento, duración, clientes
  perdidos, qué hizo —clientes de más o que no llegaron, litros recortados, horas de demora, horas extra con su costo,
  el precio del Súper antes y después—, detalle), los prendidos que no salieron y "¿Cómo se comprueba?". **Tablero:**
  cada evento es un **aviso con pausa** (⚡, título, qué pasó y la semilla), los eventos en curso se listan en el panel
  de playeros y la cara fuera de servicio se dibuja **tachada** ("fuera"). Economía: "Eventos aleatorios" en la cascada
  y en "Cómo se calcula"; Conclusión: una línea con los eventos que más clientes costaron; Qué se sorteó (simulación
  editada) los menciona. **Decisión:** la frecuencia es **un multiplicador para todos** en vez de una por evento (14
  campos más en el menú era demasiado; cada probabilidad sigue editable en el Registro). Control nuevo (38: menú sin
  eventos = Registro; cada evento ocurrido es un aviso). `verificar.py` **133/133**; QA `reports/qa_e3_eventos.py`
  (los 14 prendidos × 5 en enero: 56 eventos, 56 avisos, 281 cuadros con una cara tachada, pestaña, economía y
  conclusión; después apagados: sin pestaña ni aviso), 0 excepciones, 0 errores de consola. **Parte 4 cerrada.**
