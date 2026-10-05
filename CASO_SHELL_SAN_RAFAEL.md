# Caso de estudio — Estación Shell, Av. Ing. Julio Balloffet y Av. Los Sauces (San Rafael, Mendoza)

> **Estado:** BORRADOR v0.1 para que el grupo (Andino, Assenza) lo lea y lo verifique.
> **Fecha:** 5 de octubre de 2026.
> **Qué es y qué no es:** es el contexto nuevo del proyecto: lo que entendí de la estación, las ideas que se suman y el plan de investigación. **No hay código nuevo ni datos investigados todavía.** La búsqueda extensa de datos con fuentes se hace *después* de que verifiquen este borrador.

### Cómo leer las etiquetas

| Etiqueta | Significa |
|---|---|
| **[GRUPO]** | Dato que aportó el grupo (mensaje y capturas de Google Maps). Falta verlo en el lugar. |
| **[FUENTE]** | Respaldado por una fuente que ya consulté (el detalle está en la §10). |
| **[VERIFICAR]** | Hay una duda o una contradicción: tienen que decidir ustedes. |
| **[INVESTIGAR]** | Todavía no hay dato; se busca en la fase 2. |
| **[SUPUESTO]** | Valor provisorio, sólo si no se encuentra dato. Siempre se marca y se prueba cuánto cambia el resultado. |

---

## 0. En pocas palabras

- El profesor objetó que el proyecto se apoyaba en una **simulación hipotética**: demanda, tiempos y costos inventados, con Monte Carlo sobre tablas de ejemplo.
- Se pasa a un **caso real: una estación concreta** (la Shell de Balloffet y Los Sauces), con **datos comprobables y fuente** para cada parámetro.
- El **producto es un informe del caso**. El simulador es la herramienta para mostrar escenarios, no el centro del trabajo.
- Se suman complejidades realistas: surtidores reales por producto (nafta, diésel, GNC), minimarket real, personal por turno, estaciones del año, horarios pico, abastecimiento con camión y rutas (lógica de redes) y el corte de GNC en invierno.
- Regla de oro: **ningún número entra al modelo sin valor, fuente y nivel de confianza.** Si no se encuentra, se marca como supuesto y se prueba cuánto cambia el resultado.
- Lo que necesito de ustedes ahora: la **lista de verificación de la §1**.

---

## 1. Qué necesito que verifiquen

Pueden contestar por número ("V3: el tercero es diésel").

| # | Lo que entendí | Qué hay que confirmar |
|---|---|---|
| **V1** | La estación está en la **esquina de Av. Ing. Julio Balloffet y Av. Los Sauces**, San Rafael. (En el audio figuraba "Bayofet"; la grafía habitual es *Balloffet* y algunos avisos escriben *Ballofet*.) | ¿Es esa esquina y esa grafía? |
| **V2** | Hay **6 surtidores, todos de doble cara, o sea 12 caras**. Decisión del grupo: contar cada cara como una posición de carga independiente. | ¿Se atiende **un vehículo por cara**? |
| **V3** | Reparto: **S1 y S2 = nafta** (Súper y V-Power), **S3 = sólo diésel**, **S4, S5 y S6 = GNC**. | **Contradicción:** al principio dijiste que los tres primeros eran Súper y V-Power; al final, que el tercero es sólo diésel. La captura 1 está rotulada "surtidores a nafta" (los tres). Tomé la versión final. ¿Cuál es la correcta? |
| **V4** | Cada cara de nafta tiene **2 mangueras (Súper y V-Power)** pero atiende **1 vehículo a la vez**. | ¿Es así, o se pueden usar las dos mangueras de una cara al mismo tiempo? |
| **V5** | El surtidor de diésel tiene diésel en las dos caras. | ¿Una sola calidad (común) o también premium (V-Power Diesel)? |
| **V6** | GNC: 3 surtidores por 2 caras = **6 caras**. | ¿Cuántos compresores hay? Eso limita cuántos autos cargan a la vez. |
| **V7** | Los autos los carga un **playero** (en Argentina lo habitual es el servicio atendido). | ¿Siempre? ¿Hay autoservicio en alguna franja (de noche)? |
| **V8** | En cada captura hay **6 flechas** (6 + 6 = 12). Leí: **una flecha = una cara de surtidor = un acceso o carril de carga**. | ¿Es así? |
| **V9** | "Seguir esa lógica en el minimarket" = describirlo y calibrarlo con datos reales, igual que los surtidores. | ¿Es eso lo que querías decir? ¿Cómo se llama, cuántas cajas tiene? |
| **V10** | Horario de la estación y servicios extra (lavadero, gomería, aire y agua, baños, cajero): **[INVESTIGAR]**. | ¿Abre las 24 h? ¿El minimarket también? ¿Algún servicio genera tráfico propio? |
| **V11** | Los datos puntuales de esta estación probablemente no estén publicados en ningún lado (ver §3.1). | ¿Pueden ir a **relevar en el lugar**? Es lo que más fortalece el informe (§9). |
| **V12** | El año tiene 4 estaciones. | ¿Simulamos un **año completo** o **un mes representativo por estación**? |
| **V13** | Para lo que no se consiga de esta estación vale cualquier bandera de San Rafael (YPF, Axion, Puma…) y, si tampoco hay, ciudades **de tamaño parecido** (no CABA ni La Plata). | ¿Algún criterio de "parecido"? Propongo ciudades intermedias del interior del país, con perfil agrícola-turístico. |

---

## 2. Qué cambia respecto del proyecto anterior

| Antes (hipotético) | Ahora (caso real) |
|---|---|
| Estación genérica: 3 surtidores y 1 caja | Estación real: 12 caras en 3 grupos (nafta, diésel, GNC) y minimarket |
| Un solo combustible, un solo tanque | Súper, V-Power y diésel con tanque propio; GNC sin tanque (depende de la red de gas) |
| Tabla de demanda diaria inventada | Tabla calibrada con datos reales y relevamiento en la estación |
| Perfil horario "típico" supuesto | Perfil por franja con datos (pico, valle, día hábil o fin de semana) |
| Servidores = surtidores | Servidores = **mínimo entre caras libres y playeros en turno** |
| Personal no modelado | Dotación por turno y costo laboral |
| Un mes genérico | Ciclo por estación del año (verano, otoño, invierno, primavera) |
| Plazo de entrega triangular inventado | **Red de abastecimiento**: origen, rutas, cortes, camino más corto |
| Sin GNC | GNC con disponibilidad y cortes invernales |
| Resultado: una presentación abstracta | Resultado: **informe del caso**, ilustrado con el simulador |

**Se conserva:** el motor (SimPy), las colas, el Monte Carlo (ahora con tablas de datos reales), el inventario (s, Q), el análisis económico y los 22 controles de verificación.

**Queda superado al implementar** (ver §11): en `CLAUDE.md`, la lista de "NO hacer" (varios combustibles, fallas de equipos), "una réplica = un mes" y "un solo producto".

---

## 3. La estación

### 3.1 Ficha

| Dato | Valor | Estado |
|---|---|---|
| Bandera | Shell | [FUENTE] OpenStreetMap y [GRUPO] |
| Razón social del operador | LOS SAUCES S.R.L. | [FUENTE] OpenStreetMap (campo `operator`, cargado por la comunidad; no está contrastado con un registro oficial) |
| Titular de la red Shell | Raízen (empresa conjunta de Shell y Cosan). En junio de 2026 se informó la venta de la red (894 estaciones) a Mercuria por USD 1.420 millones; la marca Shell se mantiene y el traspaso estaba pendiente de aprobaciones | [FUENTE] Tiempo de San Juan, 4/6/2026. Es contexto: no entra al modelo |
| Ubicación | Esquina Av. Ing. J. Balloffet y Av. Los Sauces | [GRUPO]. Coherente con [FUENTE] OSM: la estación está a **48–55 m** de los dos nodos donde se cruzan las dos avenidas |
| Coordenadas | −34,62833 ; −68,35832 | [FUENTE] OpenStreetMap (nodo 3497437279) |
| Combustibles | Súper (95 octanos), V-Power (98), diésel y GNC | [FUENTE] OSM (`fuel:octane_95`, `octane_98`, `diesel`, `cng`). Coincide con lo que describió el grupo |
| Horario | — | [INVESTIGAR] |
| Minimarket | Sí | [GRUPO] |
| Otros servicios | — | [INVESTIGAR] |

> **Lo que no encontré:** ninguna fuente web publica los datos puntuales de esta estación (cantidad de surtidores, horarios, personal, volúmenes). La descripción de la §3.2 sale del grupo y de las capturas. De ahí la importancia del relevamiento en el lugar (§9).

### 3.2 Surtidores (según el grupo)

**Vocabulario que uso:** *surtidor* = la unidad física; *cara* = cada lado del surtidor, que atiende un vehículo; *manguera* = cada producto de una cara (Súper, V-Power…); *posición de carga* = el lugar donde para el vehículo = una cara.

| Grupo | Surtidores | Caras | Productos por cara | Estado |
|---|---|---|---|---|
| **A · Nafta** | S1, S2 | 4 | Súper y V-Power (2 mangueras) | [GRUPO] [VERIFICAR] |
| **B · Diésel** | S3 | 2 | Diésel (¿común y/o premium?) | [GRUPO] [VERIFICAR] |
| **C · GNC** | S4, S5, S6 | 6 | GNC | [GRUPO] |
| **Total** | **6** | **12** | | |

**Capacidad real de atención:** no es "12" sin más. La limitan tres cosas: las **caras libres**, los **playeros en turno** (si los autos los carga un playero) y, en el GNC, los **compresores**. El modelo anterior no tenía ninguna de las tres.

### 3.3 Lo que se ve en las capturas

- **Captura 1** (rotulada "surtidores a nafta"): playón techado con surtidores amarillos y blancos de la marca. Se ven una camioneta blanca, una camioneta oscura, un auto rojo, un SUV blanco en primer plano, una moto y un ómnibus a la derecha. **6 flechas rojas.**
- **Captura 2** (rotulada "SURTIDORES GNC"): otro sector techado, con el edificio detrás (ventanales; probablemente el minimarket o la administración). Se distinguen tres surtidores, una camioneta blanca al centro y una gris a la derecha. **6 flechas rojas.**
- No se alcanzan a leer los carteles de producto: **el reparto de productos sale del mensaje del grupo, no de las capturas.**

### 3.4 Entorno

- OSM registra **15 estaciones** de combustible en la ciudad (3 son Shell). **Ninguna a menos de 1,5 km** de esta: la más cercana es una de bandera blanca sólo con GNC, a 1,6 km. Entre 2,2 y 2,6 km están YPF (Opessa Sarmiento), Shell (Car Gas), Axion, ACA/YPF e YPF (Cía. Hnos.).
- OSM es colaborativo y puede estar incompleto: se usa para orientarse, no como padrón oficial.

---

## 4. Minimarket

Mismo criterio que los surtidores: describirlo como es, con datos y fuente.

| Aspecto | Qué se necesita | Estado |
|---|---|---|
| Descripción física | Superficie aproximada, cantidad de cajas, accesos (¿se entra desde el playón y desde la calle?) | [INVESTIGAR] en el lugar |
| Personal | Cajeros por turno | [INVESTIGAR] |
| Horario | ¿24 h? | [INVESTIGAR] |
| Clientes | Qué porcentaje de los que cargan entra; si hay quienes sólo entran al minimarket | [INVESTIGAR] en el lugar |
| Ticket | Gasto medio por compra y por franja | [INVESTIGAR] (probablemente sólo vía encargado) |
| Hipótesis a probar | Los clientes de **GNC**, que esperan más tiempo, compran más que los de nafta | [SUPUESTO]: se contrasta en el relevamiento |
| Cómo entra al modelo | Segunda cola (cajas), con probabilidad de entrada y tiempo de compra **por tipo de cliente** | — |

---

## 5. Complejidades realistas que se suman

Para cada una: qué se modela, qué dato hace falta, dónde se busca y cómo entra al simulador.

**Jerarquía de datos:** (1) la propia estación → (2) San Rafael, cualquier bandera → (3) Mendoza → (4) ciudades intermedias parecidas. Cada dato lleva anotado de qué nivel salió. Las fuentes que dicen "candidata" son lugares donde buscar: **todavía no verifiqué qué publican.**

### 5.1 Cantidad de vehículos que cargan

- **Se modela:** autos por día y por producto; día hábil, fin de semana y feriado.
- **Dato:** autos por día, o litros vendidos por mes y producto (con los litros promedio por carga se estiman los autos).
- **Dónde:** relevamiento propio; datos abiertos de la Secretaría de Energía (ventas de combustibles); estadísticas de Mendoza (DEIE); notas de prensa y cámaras de expendedores.
- **Entra como:** tabla de frecuencias de Monte Carlo (los 5 pasos de la cátedra) por tipo de día y estación del año.

### 5.2 Cuánto carga cada auto y qué vehículos cargan más

- **Se modela:** litros promedio, mínimo y máximo por carga; qué vehículos cargan más (pickups, camionetas, camiones, ómnibus) y cuáles menos (motos, autos chicos); si se carga "por monto" o "tanque lleno".
- **Dato:** composición del parque automotor local; capacidad de tanque por tipo de vehículo; litros por carga.
- **Dónde:** parque automotor y patentamientos (candidatas: DNRPA, ACARA, DEIE Mendoza); fichas técnicas de los fabricantes (capacidad del tanque); relevamiento propio; consulta al encargado.
- **Entra como:** tabla de Monte Carlo *tipo de vehículo → producto → litros → tiempo de carga*.

### 5.3 Horarios de mayor concurrencia

- **Se modela:** perfil horario real (pico y valle); qué hace la estación en el pico (¿refuerza personal?, ¿habilita más caras?, ¿se arma cola?); **capacidad finita de la cola**: si la fila llega a la avenida, el cliente no entra (es la "capacidad de la cola" de la cátedra).
- **Dato:** afluencia por franja (15 min o 1 h), día hábil contra fin de semana; cuántos autos entran en la fila antes de salir a la calle.
- **Dónde:** relevamiento propio (la fuente principal); entrevista al encargado; los "horarios populares" de Google Maps sólo como dato **orientativo** (no es una estadística oficial).
- **Entra como:** perfil horario por tipo de día, que reemplaza al perfil supuesto.

### 5.4 Personal por turno

- **Se modela:** playeros, cajeros y encargado por turno; qué pasa de noche (¿1 o 2 personas?); servidores = mínimo entre caras y playeros.
- **Dato:** dotación por franja, esquema de turnos, categorías y salarios.
- **Dónde:** relevamiento propio y encargado; convenio colectivo del gremio de estaciones de servicio y su escala salarial vigente (hay que verificar nombre y vigencia); avisos laborales de San Rafael (esquemas de turnos).
- **Entra como:** capacidad de atención por hora y costo laboral por turno.

### 5.5 Estaciones del año

- **Se modela:** verano, otoño, invierno y primavera: nivel de demanda, perfil horario, mezcla de productos (GNC), olas de frío, cortes de ruta y turismo (vendimia, vacaciones de invierno, temporada de nieve en la zona).
- **Dato:** índice estacional mensual de ventas de combustibles; turismo por mes en San Rafael; temperaturas.
- **Dónde:** Secretaría de Energía (ventas mensuales por provincia); DEIE Mendoza; dirección de turismo de San Rafael; Servicio Meteorológico Nacional (estación San Rafael).
- **Entra como:** un juego de parámetros por estación; se corre un mes representativo por estación o el año completo (V12).

### 5.6 Abastecimiento de nafta y diésel por camión → ver §6.1

### 5.7 GNC y su corte en invierno → ver §6.2

### 5.8 Economía real

- **Se modela:** ingresos (margen por litro y por producto, margen del minimarket), costos (flete, personal, almacenamiento y capital) y pérdidas por faltante, **con valores reales**.
- **Dato y dónde:** precios al público (datos abiertos de la Secretaría de Energía); márgenes del expendedor (cámaras del sector: CECHA, FECRA); salarios (convenio); flete (consulta a transportistas o notas del sector).
- **Entra como:** reemplaza los valores económicos estimados del proyecto anterior.

---

## 6. Red de abastecimiento (lógica de redes de la cátedra)

En el TP 5 de redes ya resolvieron: **flujo máximo** (oleoducto Neuquén → Buenos Aires, con aumento de demanda en invierno), **camino más corto** (método del "nodo no resuelto más cercano"), **árbol de expansión mínima** (fibra óptica en San Rafael) y **transbordo** (QM o Solver). Esos mismos problemas se aplican acá.

### 6.1 Nafta y diésel: el camión cisterna

- **La red:** *nodos* = el origen donde se carga el camión **[INVESTIGAR: ¿planta de despacho de Luján de Cuyo u otra?]**, las localidades o empalmes intermedios y la estación; *arcos* = tramos de ruta con distancia, tiempo de viaje y probabilidad de corte.
- **Camino más corto** (TP 5, ej. 2): la ruta de menor tiempo o distancia del camión.
- **Camino cortado:** se elimina el arco bloqueado y se recalcula la ruta; la diferencia de tiempo se suma al plazo de entrega y alimenta el inventario (riesgo de quiebre).
- **Transbordo** (TP 5, ej. 4 y 5): sólo si hay más de un origen o un depósito intermedio entre la planta y la estación **[VERIFICAR cuando se sepa cómo se abastece]**.
- **Monte Carlo sobre el estado de cada arco** (abierto o cortado), con probabilidades por estación del año (nieve, viento, accidentes, obras) **[INVESTIGAR: Vialidad Nacional y Provincial, defensa civil, noticias de rutas cortadas]**.
- **Qué se muestra:** el diagrama de la red con la ruta óptima y las alternativas; la distribución del plazo de entrega con y sin cortes; el efecto en el nivel del tanque y en los días con quiebre.
- **Dato a conseguir:** de dónde sale el combustible de esta estación, cada cuánto viene el camión, con cuántos litros, qué plazo tiene y qué capacidad tiene cada tanque subterráneo **[INVESTIGAR; el encargado lo sabe]**.

### 6.2 GNC: no llega en camión

- El GNC se toma de la **red de distribución de gas** y se comprime en la estación: no hay tanque que reponer. Lo que existe es **disponibilidad** (presión y caudal) e **interrupciones**.
- **En invierno** sube la demanda residencial y se restringe el GNC para priorizar el servicio domiciliario. **[FUENTE]** Sitio Andino, 23/6/2022: la nota informa que son **ocho** las estaciones de servicio de San Rafael perjudicadas. Hubo un corte "entre las 17 y la 1 de la madrugada" y otro que arrancó "a las 9", "hasta nuevo aviso", por una orden de Ecogas ante la ola de frío (lo informó Amena, la asociación de estaciones).
- **Flujo máximo** (TP 5, ej. 1): capacidad de la red de gas hasta San Rafael contra la demanda de invierno; el residencial tiene prioridad y el GNC es el remanente, o sea una "capacidad disponible para GNC" por hora **[INVESTIGAR si hay datos de capacidad; si no, se modela como *ventana de corte* aleatoria]**.
- **Monte Carlo del corte:** probabilidad de día con corte según el frío (temperatura mínima, SMN) y la estación del año; inicio y duración de la ventana según los casos relevados en noticias y comunicados.
- **Efecto sobre el resto:** muchos vehículos a GNC tienen también nafta, así que parte de esos clientes **se pasa a nafta** durante el corte y sube la cola de los surtidores de nafta **[SUPUESTO: porcentaje de migración, a relevar]**.
- **Dato a conseguir:** horarios y frecuencia de los cortes en San Rafael en los últimos inviernos; cómo lo manejan las estaciones (turnos de carga, límites por vehículo); cantidad de compresores y tiempo de carga de GNC.

---

## 7. Cómo se modelaría (visión, sin código)

| Subsistema | Qué hace | Tema de la cátedra |
|---|---|---|
| Demanda | Sortea autos por día, tipo de vehículo, producto y litros | Monte Carlo |
| Surtidores (3 grupos) | Colas separadas por grupo; servidores = mínimo entre caras y playeros | Colas |
| Minimarket | Segunda cola, con cajas por turno | Colas (red de colas) |
| Inventario líquido | Un tanque por producto; política (s, Q) | Inventario |
| Red de abastecimiento | Ruta del camión, cortes, plazo de entrega | Redes (camino más corto, transbordo) |
| GNC | Disponibilidad con cortes invernales | Redes (flujo máximo) y Monte Carlo |
| Personal | Dotación y costo por turno | Colas y economía |
| Economía | Ingresos, costos y pérdidas con valores reales | — |

### Decisiones de modelado abiertas

- **Una cola por grupo o una fila por cara.** El modelo anterior usaba una cola única compartida (FIFO). En la realidad los autos suelen hacer fila por surtidor (el "sistema de línea múltiple" de la cátedra). Se observa en el relevamiento y se pueden comparar las dos versiones.
- **Qué hace el cliente cuando no hay lugar o hay corte:** se va, espera o cambia de producto.

### Escenarios que se mostrarían

1. **Un día típico de cada estación del año** (animación): cómo se ve la estación en verano y en invierno.
2. **Hora pico con distinta dotación de playeros:** ¿alcanza?
3. **Ola de frío con corte de GNC:** pérdida directa y migración a nafta.
4. **Corte de la ruta del camión:** red, ruta alternativa, plazo, quiebre.
5. **Política de reposición** con el plazo real y el riesgo de cortes.
6. **Decisión económica:** ¿personal extra en el pico?, ¿más stock en invierno?

### Preguntas que respondería el informe **[PROPUESTA: ajustar]**

- ¿Alcanza la dotación actual en la hora pico de cada estación del año?
- ¿Cuándo y cuánto pedir para no quedarse sin combustible, dado el plazo real y el riesgo de cortes?
- ¿Cuánto se pierde cuando se corta el GNC en invierno y adónde va esa demanda?
- ¿Qué conviene hacer, en pesos por mes?

---

## 8. Qué se entrega

1. **Informe del caso** (Word o PDF): descripción de la estación real → relevamiento de datos con fuentes → modelo → simulación por estación del año y escenarios → análisis económico → conclusiones.
2. **Simulador:** el programa actual, adaptado al caso, para mostrar los escenarios. No es el centro del informe.
3. **Anexo de fuentes:** una ficha por dato (valor, unidad, fuente, fecha de consulta, nivel geográfico, confianza).
4. *(Opcional)* Presentación breve derivada del informe.

---

## 9. Cómo se garantiza que todo sea comprobable

### Reglas de evidencia

- Cada parámetro del modelo lleva: **valor · unidad · fuente (título, enlace, fecha de consulta) · nivel (estación, San Rafael, Mendoza, ciudad parecida) · tipo (dato, estimación u observación propia) · confianza**.
- **Nunca se inventa en silencio.** Si no hay dato, se usa un [SUPUESTO] justificado y se hace un análisis de sensibilidad para ver cuánto cambia el resultado.
- Una **observación propia** (un conteo en la estación, con fecha, hora y método) **también es comprobable**, y es la más valiosa.
- Cada fuente se verifica en el original: en esta fase ya pasó que el resumen de un buscador dató una nota de 2022 como si fuera de 2026.

### Relevamiento en la estación (muy recomendado)

- **Contar** vehículos por tipo y producto cada 15 min, en 3 franjas (mañana, tarde, noche), un día hábil y un fin de semana. Es la tabla de frecuencias del TP de Monte Carlo (las "últimas 250 horas" de la playa de estacionamiento), pero con datos propios.
- **Cronometrar** el tiempo de carga por producto y por tipo de vehículo.
- **Contar** el personal visible por turno y las cajas abiertas.
- **Medir** cuántos autos entran en la fila de cada grupo antes de salir a la calle.
- **Preguntar al encargado** (pidiendo permiso): días y litros de cada entrega del camión, de dónde sale, horario de los cortes de GNC en invierno, dotación por turno y horario de atención.
- Anotar siempre fecha, hora y clima.

### Orden de búsqueda (lo que más mueve el modelo, primero)

1. Demanda y perfil horario → 2. Vehículos y litros → 3. Abastecimiento (origen, ruta, frecuencia) → 4. GNC en invierno → 5. Personal y turnos → 6. Estacionalidad → 7. Precios y costos.

---

## 10. Fuentes consultadas hasta ahora

| Fuente | Qué aporta | Estado |
|---|---|---|
| [OpenStreetMap](https://www.openstreetmap.org), vía Overpass API, consultado el 5/10/2026 (licencia ODbL) | 15 estaciones de combustible en la ciudad de San Rafael (3 Shell). Nodo 3497437279: Shell, operador LOS SAUCES S.R.L., −34,62833 / −68,35832, combustibles 95, 98, diésel y GNC. El cruce Balloffet y Los Sauces está en los nodos 1094951519 y 5276771943 | Comunitaria: sirve para ubicar y orientar, no es dato oficial. No trae horarios ni servicios |
| [Sitio Andino, 23/6/2022](https://www.sitioandino.com.ar/departamentales/estaciones-servicio-cortaron-el-gnc-san-rafael-n5629707) | Cortes de GNC por ola de frío en San Rafael (orden de Ecogas): 8 estaciones afectadas; corte de 17 a 1 h y otro desde las 9 h; prioridad al servicio domiciliario | Verificada en el original (detalle en §6.2). La nota **no** da ventas ni horarios de las estaciones |
| [Tiempo de San Juan, 4/6/2026](https://www.tiempodesanjuan.com/economia/se-confirmo-la-venta-894-estaciones-servicio-shell-el-pais-un-grupo-suizo-pago-usd-1420-millones-n431977) | Venta de la red Shell (894 estaciones) de Raízen a Mercuria por USD 1.420 millones; la marca se mantiene | Verificada en el original. No menciona Mendoza |
| Material de la cátedra: TP 5 de redes, TP de Monte Carlo, apuntes de colas y de simulación | Vocabulario y métodos que se aplican (flujo máximo, camino más corto, árbol de expansión mínima, transbordo, Monte Carlo de 5 pasos, colas, FIFO, Poisson) | Propio del grupo |

**Lo que busqué y no encontré:** datos puntuales de esta estación (horarios, cantidad de surtidores, personal, volúmenes) y un listado oficial de estaciones de San Rafael con direcciones.

---

## 11. Pendientes, riesgos y próximo paso

- **El volumen de trabajo es grande.** Si hay que recortar, la prioridad es: (1) demanda y perfil horario, (2) abastecimiento y red, (3) GNC en invierno. Personal y economía fina pueden quedar con supuestos marcados.
- **Los datos de esta estación seguramente no son públicos:** el relevamiento en el lugar es la vía para tenerlos.
- **`CLAUDE.md` queda desactualizado** con este giro (prohíbe varios combustibles y fija un producto, un mes y un tanque). No lo toqué: lo actualizo cuando verifiquen este borrador.
- **El anteproyecto anterior** (`Anteproyecto_Simulacion_Estacion_de_Servicio.docx`) lleva en la portada sólo a Nicolás Andino; el grupo es Andino–Assenza. Se corrige en el próximo documento.
- **Próximo paso:** cuando verifiquen la §1, hago la **fase 2: búsqueda extensa con fuentes** (San Rafael primero; después Mendoza y ciudades parecidas). Entrega una tabla de datos con la ficha de cada fuente. Para bajar bases de datos abiertas voy a pedir su OK antes, indicando archivo, origen y tamaño.

---

*Historial: v0.1, 5/10/2026, primer borrador.*
