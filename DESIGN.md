---
name: Simulador de la Estación Shell — San Rafael
description: Tótem de precios nocturno — pocas cifras enormes e iluminadas sobre asfalto casi negro, y todo lo demás callado.
colors:
  amarillo: "#FBCE07"
  rojo: "#DD1D21"
  noche: "#0E0D0B"
  panel: "#171613"
  panel_2: "#211F1B"
  filete: "#2E2B26"
  filete_fuerte: "#47423A"
  amarillo_suave: "#2A2410"
  asfalto: "#1B1A17"
  asfalto_2: "#24221E"
  texto: "#EEEAE0"
  texto_2: "#B5AFA2"
  texto_3: "#958F82"
  sobre_amarillo: "#16130C"
  rojo_texto: "#FF7A6E"
  referencia: "#CFC9BB"
  azul: "#4F8FE0"
  turquesa: "#1FA894"
  naranja: "#D9772E"
  violeta: "#A47BE8"
  gris: "#8E897E"
  celeste: "#45B0D6"
  indigo: "#7F86E8"
  verde_ok: "#3FAE6A"
  verde_ingreso: "#5BC285"
typography:
  display:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "clamp(2.6rem, 4.2vw, 4rem)"
    fontWeight: 750
    lineHeight: 0.98
    letterSpacing: "-0.01em"
    fontFeature: "'tnum' 1"
    fontVariation: "'wdth' 72"
  display-texto:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "clamp(1.9rem, 2.8vw, 2.7rem)"
    fontWeight: 750
    lineHeight: 0.98
    fontVariation: "'wdth' 72"
  display-metric:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "clamp(2.2rem, 3.4vw, 3.2rem)"
    fontWeight: 750
    lineHeight: 1.02
    letterSpacing: "-0.005em"
    fontFeature: "'tnum' 1"
    fontVariation: "'wdth' 72"
  headline:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "clamp(1.8rem, 2.6vw, 2.4rem)"
    fontWeight: 800
    lineHeight: 1.02
    letterSpacing: "0.005em"
    fontVariation: "'wdth' 72"
  title:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontWeight: 750
    letterSpacing: "0"
    fontVariation: "'wdth' 72"
  title-sm:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 650
    letterSpacing: "0.04em"
    fontVariation: "'wdth' 72"
  periodo:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 750
    lineHeight: 1.15
    letterSpacing: "0.04em"
    fontVariation: "'wdth' 72"
  tab:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 600
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 74"
  body:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    fontFeature: "'tnum' 1"
  label:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "0.74rem"
    fontWeight: 600
    letterSpacing: "0.07em"
  unidad:
    fontFamily: "Archivo, 'Segoe UI', system-ui, sans-serif"
    fontSize: "0.42em"
    fontWeight: 600
    letterSpacing: "0.02em"
rounded:
  tab: "3px"
  base: "4px"
  tablero: "6px"
  pastilla: "999px"
spacing:
  marquesina: "14px"
  contenido-arriba: "2.75rem"
  contenido-max: "1440px"
  cifra-arriba: "0.7rem"
  tablero-gap: "10px"
  texto-max: "72ch"
components:
  button-primary:
    backgroundColor: "{colors.amarillo}"
    textColor: "{colors.sobre_amarillo}"
    rounded: "{rounded.base}"
  button-primary-disabled:
    backgroundColor: "{colors.panel_2}"
    textColor: "{colors.texto_3}"
    rounded: "{rounded.base}"
  button-secondary:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
    rounded: "{rounded.base}"
  button-secondary-hover:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.amarillo}"
  tab:
    textColor: "{colors.texto_2}"
    typography: "{typography.tab}"
    rounded: "{rounded.tab}"
    padding: "0.5rem 0.42rem 0.55rem"
  tab-hover:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
  tab-active:
    backgroundColor: "{colors.amarillo}"
    textColor: "{colors.sobre_amarillo}"
  totem-cifra:
    textColor: "{colors.texto}"
    typography: "{typography.display}"
    padding: "0.7rem 0 0.15rem"
  totem-rotulo:
    textColor: "{colors.texto_2}"
    typography: "{typography.label}"
  periodo:
    textColor: "{colors.amarillo}"
    typography: "{typography.periodo}"
  alert:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
    rounded: "{rounded.base}"
  expander:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
    rounded: "{rounded.base}"
  input:
    backgroundColor: "{colors.panel_2}"
    textColor: "{colors.texto}"
    rounded: "{rounded.base}"
  ayuda:
    backgroundColor: "{colors.panel_2}"
    textColor: "{colors.texto}"
    rounded: "{rounded.base}"
    padding: "0.5rem 0.65rem"
  insignia:
    textColor: "{colors.texto}"
    rounded: "{rounded.pastilla}"
    padding: "1px 9px"
  tablero-panel:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.tablero}"
    padding: "10px 14px"
  tablero-lienzo:
    backgroundColor: "{colors.asfalto}"
    rounded: "{rounded.tablero}"
---

# Design System: Simulador de la Estación Shell — San Rafael

## Overview

**Creative North Star: "El tótem de precios nocturno"**

La app se lee como el cartel de precios de la estación de noche: pocas cifras enormes, iluminadas, sobre asfalto casi negro, y todo lo demás callado. El profesor ve primero el número grande; la cuenta que lo comprueba está debajo, en voz baja, en un desplegable "¿Cómo se comprueba?". Es un instrumento para presentar en vivo en una notebook: denso donde hay datos, pero con una sola jerarquía clara por pantalla.

El mundo es oscuro y cálido, nunca azul ni gris frío. La estructura se hace con filetes de 1 px y paneles apenas más claros que la noche, no con tarjetas, sombras ni degradados. El amarillo Shell es la única luz: la franja de la marquesina arriba de todo, la acción principal, la pestaña activa, el período y el filete de cada cifra. El rojo Shell no decora: alerta (quiebres, pérdidas, cortes) y subraya la marquesina. Una sola grotesca de ancho variable, Archivo, hace todo: condensada y pesada para las cifras y los títulos, normal para el texto, con cifras tabulares en toda la app.

Se rechaza explícitamente el dashboard de tarjetas con borde y emojis. La única excepción es el tablero animado, que sigue la referencia de "dashboard oscuro" que Nico dio como vinculante: ahí sí hay paneles con filete, pero con la misma paleta, la misma tipografía y la fila de cifras con filete amarillo arriba.

**Key Characteristics:**
- Un solo tema, oscuro: asfalto casi negro cálido (`noche`) con paneles tonales (`panel`, `panel_2`).
- Amarillo = luz y acción; rojo = alerta. Nada más compite por la atención.
- Cifras de tótem: dígitos condensados enormes, unidad chica al lado, rótulo en versalitas espaciadas y un filete amarillo arriba; sin tarjeta.
- La pestaña activa se enciende como un precio: ranura amarilla con letra oscura.
- Íconos de línea finos (Material Symbols contorno, peso 300; SVG de trazo 1,75 en el tablero). Ningún emoji.
- Los colores de producto son identidad: el mismo color en el auto animado, el surtidor, el tanque y la serie del gráfico.

## Colors

Asfalto de noche con una sola luz amarilla y un rojo reservado para lo que sale mal; todos los valores viven en `ui/tema.py` (las claves de arriba son sus constantes en minúscula) y `.streamlit/config.toml` `[theme]` los repite.

### Primary
- **Amarillo marquesina** (`amarillo`): la luz. Franja fija de la marquesina (11 px), botón principal, pestaña activa, período del encabezado, filete de las cifras del tótem (al 55 %), foco visible, selección de texto, `accent-color` de controles. También es el color del producto Súper.

### Secondary
- **Rojo surtidor** (`rojo`): sólo alerta. La línea de 3 px bajo la franja amarilla, bordes de avisos de error (al 60 %), zonas llenas o caras cortadas en el tablero, pastillas de alerta. Es también el color del producto V-Power. Como texto sobre la noche no llega a 4,5:1: el texto de alerta va en **Rojo legible** (`rojo_texto`).

### Tertiary (series y estados)
- **Azul GNC** (`azul`): GNC, la caja del minimarket, barras de demanda, ícono de avisos informativos, insignia de "observación".
- **Turquesa** (`turquesa`): Diésel G3 / V-Power Diésel; escenario C.
- **Violeta** (`violeta`): Diésel G2; escenario B.
- **Naranja** (`naranja`): espera de playero en el tablero, caja ocupada, insignia de "supuesto".
- **Gris base** (`gris`): lo neutro; el escenario Base, lo que no es ninguna categoría.
- **Celeste** (`celeste`): nivel del tanque. **Índigo** (`indigo`): flete en los costos por política.
- **Verde libre** (`verde_ok`): estado libre, éxito, insignia de "dato". **Verde ingreso** (`verde_ingreso`): ingresos en Economía.

### Neutral
- **Noche** (`noche`): fondo de la página y de los gráficos (Plotly va transparente encima).
- **Panel** (`panel`): desplegables, avisos, encabezado de tablas, hover de pestañas, botón secundario.
- **Panel 2** (`panel_2`): controles (selects, inputs), paneles dentro de un panel, cartel de ayuda, hover de Plotly.
- **Filete** (`filete`): la única estructura: bordes de 1 px, grilla de gráficos, línea bajo las pestañas, `hr`.
- **Filete fuerte** (`filete_fuerte`): borde de botones secundarios y controles, ejes y línea cero de los gráficos, scrollbar.
- **Amarillo apagado** (`amarillo_suave`): panel apenas encendido para avisos del tablero.
- **Asfalto** (`asfalto`) y **Asfalto 2** (`asfalto_2`): el playón del tablero animado y el panel de cada zona.
- **Acrílico** (`texto`): texto principal, blanco cálido. **Texto 2** (`texto_2`): secundario, captions, rótulos, unidades. **Texto 3** (`texto_3`): terciario, deshabilitados, notas al pie.
- **Tinta sobre luz** (`sobre_amarillo`): todo texto sobre amarillo.
- **Referencia** (`referencia`): ejes y líneas de referencia de los gráficos.

El tablero dibuja además detalles figurativos (faros, neumáticos, vidrio, plata, árboles) con constantes propias de `ui/tema.py`; son ilustración del playón, no roles de interfaz.

### Named Rules
**The Una Sola Luz Rule.** El amarillo es la luz y nada más se enciende: marquesina, acción principal, pestaña activa, período y el filete de las cifras. Una acción amarilla por sección: si en una misma sección hay dos botones amarillos, uno sobra.

**The Rojo Sólo Alerta Rule.** El rojo de marca aparece sólo cuando algo se pierde o se corta (y en la línea de la marquesina). El texto de alerta usa `rojo_texto`, nunca `rojo`.

**The Producto Es Identidad Rule.** Súper = amarillo, V-Power = rojo, Diésel G2 = violeta, G3 = turquesa, GNC = azul (`COLOR_PRODUCTO`). El mismo color en gráficos, tablero y tanques; ninguna otra serie reutiliza esos colores con otro significado dentro del mismo gráfico.

**The Hex Sólo En tema.py Rule.** Ningún hex fuera de `ui/tema.py` (y su espejo `[theme]` en `config.toml`). Los tableros en JavaScript reciben la paleta por `paleta_json()`. `verificar.py` (control 14 / N15) lo hace cumplir, junto con los pares de `PARES_CONTRASTE` (WCAG ≥ 4,5:1) y la distancia entre colores de producto.

**The Serie Validada Rule.** Los colores de series se validan sobre `noche` (banda de luminosidad OKLCH 0,48–0,67, croma ≥ 0,10, daltonismo). Amarillo y rojo quedan fuera de la banda a propósito: son identidad. Todo color nuevo de serie pasa por el mismo validador y, si va como texto, entra en `PARES_CONTRASTE`.

**The Estado Con Palabra Rule.** Libre, ocupado y perdido llevan siempre texto además de color.

## Typography

**Display Font:** Archivo (variable, peso 100–900, ancho 62–125 %), con fallback `'Segoe UI', system-ui, sans-serif`
**Body Font:** Archivo (la misma familia)

**Character:** Una sola grotesca que cambia de voz con el eje de ancho: condensada al 72 % (`ANCHO_TOTEM`) y pesada parece el dígito de un cartel de precios; a ancho normal es texto de lectura sobrio. Los archivos `woff2` (SIL OFL) se sirven desde `static/fonts/`, así que anda sin internet.

### Hierarchy
- **Display** (750, `clamp(2.6rem, 4.2vw, 4rem)`, 0,98): las cifras del tótem. La unidad va al lado en **Unidad** (600, 0,42 em, `texto_2`). Si el valor no tiene dígitos (un nombre de método) usa **Display texto** (`clamp(1.9rem, 2.8vw, 2.7rem)`), con corte de línea permitido. Al aparecer, el dígito se enciende de `texto_2` a `texto` en 520 ms.
- **Display metric** (750, `clamp(2.2rem, 3.4vw, 3.2rem)`, 1,02): el `st.metric` de Streamlit, con el mismo tratamiento de tótem.
- **Headline** (800, `clamp(1.8rem, 2.6vw, 2.4rem)`, 1,02, mayúsculas): el `h1` del encabezado, condensado, como un cartel.
- **Title** (750, ancho 72): `h2`/`h3` de sección, en caja normal, con `text-wrap: balance`. **Title chico** (650, 1,05 rem, mayúsculas, 0,04 em): `h4`. `h5` va en 650 a 0,98 rem.
- **Período** (750, 1,05 rem, mayúsculas, 0,04 em, amarillo, alineado a la derecha): el período simulado en el encabezado, con su aclaración ("datos reales, sin azar") debajo en 450 a 0,8 rem, `texto_2`, ancho normal.
- **Tab** (600, 0,9 rem, ancho 74; 800 cuando está activa).
- **Body** (400, 1 rem): párrafos y listas a un máximo de 72ch; captions en `texto_2` hasta 75ch.
- **Label** (600, 0,74 rem, 0,07 em, mayúsculas, `texto_2`): rótulos de las cifras. En el tablero, el mismo rol va a 11 px, 650, 0,09 em.

### Named Rules
**The Cifras Tabulares Rule.** `font-variant-numeric: tabular-nums` en toda la app, gráficos y tablero: los dígitos no bailan cuando cambian.

**The Una Familia Rule.** Archivo para todo. La jerarquía sale del eje de ancho y del peso, no de una segunda familia.

**The Unidad Chica Rule.** En una cifra el número manda; la unidad ("L", "min", "m³") va al lado, a 0,42 em, en `texto_2`. Nunca del mismo tamaño que el número.

## Layout

Una sola columna centrada de hasta 1440 px, sin barra lateral. Arriba de todo, fija, la marquesina de 14 px (11 px amarillo + 3 px rojo); debajo, el header de Streamlit translúcido (`noche` al 92 % con desenfoque de 6 px) y el contenido arranca a 2,75 rem.

La primera vista de resultados es: marquesina → encabezado (título condensado a la izquierda; período en amarillo, su aclaración y el botón "Cambiar período" a la derecha, en proporción 4:1) → aviso del modo de simulación → la fila de pestañas encendida. Las pestañas se abren en "La estación", que presenta la estación real primero por decisión de Nico; las cifras de tótem viven en las pestañas que llevan números (Indicadores, Economía, Demanda, Pronóstico, Red y rutas y la fila de cifras del tablero animado).

Las cifras del tótem van en fila, una por columna (`st.columns`), separadas por aire y por su propio filete superior, no por cajas. Cada sección termina con su "¿Cómo se comprueba?" en un desplegable.

En notebook, todas las pestañas quedan a la vista: si no entran en una fila pasan a una segunda (sin flechas de scroll). Por debajo de 760 px, una sola fila que se desliza de costado. El tablero animado es una grilla propia (cabecera de cifras · lienzo + columna derecha de 300 px · fila inferior de cuatro paneles) con 10 px de separación; por debajo de 1000 px pasa a dos columnas y a una.

## Elevation & Depth

Plano. La profundidad se hace por capas tonales (`noche` → `panel` → `panel_2`) y filetes de 1 px, nunca por sombras en reposo. Las únicas sombras son de capas que flotan sobre el contenido: el cartel de ayuda de una cifra y el aviso con pausa del tablero. El header translúcido con desenfoque es la única transparencia estructural.

### Shadow Vocabulary
- **Cartel flotante** (`box-shadow: 0 8px 24px rgba(14,13,11,0.6)`): el cartel de ayuda que se abre sobre el rótulo de una cifra.
- **Aviso modal del tablero** (`box-shadow: 0 18px 48px color-mix(in srgb, var(--fondo) 85%, transparent)`): la caja del aviso con pausa (pedido de camión, corte de GNC), sobre un velo de `noche` al 72 %.

### Named Rules
**The Filete Es La Estructura Rule.** Si hay que separar algo, un filete de 1 px (`filete`) o un cambio de panel. Nunca una sombra, nunca un degradado decorativo.

## Shapes

Esquinas apenas suavizadas: 4 px (`base`) para botones, avisos, desplegables, tablas, controles y carteles; 3 px arriba en las pestañas; 6 px en los paneles y el lienzo del tablero animado. Las píldoras (insignias de tipo de dato, pastillas de estado del tablero) son completamente redondas. Las cifras del tótem no tienen forma: sólo un filete superior. Las figuras del tablero (autos, surtidores, zonas) son rectángulos redondeados dibujados en SVG con trazos finos.

## Components

### Buttons
Callados salvo la acción principal, que se enciende.
- **Shape:** esquinas de 4 px.
- **Primary:** fondo `amarillo`, texto `sobre_amarillo` en 700, borde del mismo amarillo. Una por sección: "Simular con datos reales", "Editar simulación", "Buscar la mejor política de cada tanque", "Correr el tornado", "Correr los escenarios", "Reproducir" en el tablero.
- **Hover / Focus:** el primario se aclara con `brightness(1.06)`; foco visible con contorno de 2 px `amarillo` y 2 px de separación (3 px en el tablero).
- **Secondary:** fondo `panel`, filete `filete_fuerte`, texto `texto`; al pasar el mouse el filete y el texto se encienden en amarillo.
- **Disabled:** `panel_2` con texto `texto_3` y filete `filete`, sin luz.
- **Íconos:** Material Symbols de contorno a la izquierda del rótulo (`:material/arrow_back:`, `search`, `play_arrow`…).

### Chips (insignias de tipo de dato)
- **Style:** píldora con filete `filete_fuerte`, texto `texto` en 600 a 0,78 rem, con un punto de 7 px del color del tipo: dato `verde_ok`, estimación `amarillo`, observación `azul`, supuesto `naranja`, el resto `gris`.
- **State:** sólo informativas; no se seleccionan.

### Cards / Containers
- **Corner Style:** 4 px.
- **Background:** `panel` para avisos y desplegables; `panel_2` para controles adentro.
- **Shadow Strategy:** ninguna (ver Elevation & Depth).
- **Border:** 1 px `filete`; los avisos de advertencia pasan a `filete_fuerte` y los de error a `rojo` al 60 %. El ícono del aviso lleva el color del estado (info `azul`, éxito `verde_ok`, advertencia `texto_2`, error `rojo_texto`); el texto siempre en `texto`.
- **Desplegables:** el resumen en 600; al pasar el mouse se enciende en amarillo.

### Inputs / Fields
- **Style:** fondo `panel_2`, filete del tema (`filete`), 4 px; menús desplegables en `panel_2`. Sliders sin sombra en el tirador; radios y checks con `accent-color` amarillo.
- **Focus:** contorno de 2 px `amarillo`.

### Navigation (pestañas)
- **Style:** una barra de filetes: línea inferior de 1 px `filete`, sin espacio entre pestañas. Cada pestaña lleva un ícono Material Symbols de contorno (peso 300, 1,1 rem) y su nombre en ancho 74.
- **Default:** texto `texto_2`. **Hover:** texto `texto` sobre `panel` (160 ms, `cubic-bezier(.16,1,.3,1)`).
- **Active:** se enciende como un precio: ranura `amarillo` con letra `sobre_amarillo` en 800, esquinas de 3 px arriba.
- **Mobile:** una fila que se desliza de costado, sin barra de scroll.

### Cifra del tótem (signature)
La firma del sistema. Un bloque sin caja: filete superior de 1 px `amarillo` al 55 %, rótulo en Label (mayúsculas espaciadas, `texto_2`), dígitos en Display condensado y la unidad chica al lado; debajo, una línea opcional en `texto_2` a 0,85 rem. Si el rótulo tiene ayuda, va subrayado de puntos (`texto_3`) y es enfocable: con mouse, Tab o toque abre un cartel en `panel_2` con filete `filete_fuerte`, 4 px, hasta 32ch. El `$` se escribe como entidad para que Markdown no lo lea como LaTeX.

### Marquesina y encabezado
La franja fija de 14 px (amarillo 11 px + rojo 3 px) arriba de todo. Detrás del encabezado, una foto al 30 % que se funde con la noche hacia abajo (`.st-key-portada`): la marquesina de Shell (`static/img/marquesina.webp`) en el simulador y la playa de GNC (`static/img/playa-gnc.webp`) sólo en el menú; el logo aparece sólo ahí, nunca como marca de la app. Debajo, el título en Headline mayúsculas condensadas, la dirección en caption, y a la derecha el período en amarillo con su aclaración y "Cambiar período" como botón secundario a todo el ancho de su columna.

### Tablero animado
Página propia en un iframe, con la misma paleta (`paleta_json()`), Archivo y cifras tabulares. Cabecera: el bloque de marca con filete amarillo de 3 px y cuatro cifras con filete amarillo al 55 % (rótulo de 11 px, cifra condensada `clamp(22px, 2.3vw, 34px)`), más el botón "Reproducir" amarillo. Lienzo SVG del playón sobre `asfalto` con zonas en `asfalto_2`; paneles laterales en `panel` con filete y 6 px. Íconos SVG de línea propios (16 px, trazo 1,75, puntas redondeadas). Cada surtidor de doble cara es una isla con su número (S1…S6) y las caras numeradas 1…12; los autos entran desde la avenida y salen por ella (a lo sumo 8 moviéndose a la vez), la avenida tiene tránsito decorativo gris, y "Colas ilustrativas" (prendido, con su rótulo sobre la marquesina) suma autos a la cola sólo para la presentación. El botón "Alertas" elige qué avisos pausan la animación (por tipo y por evento). Los avisos con pausa entran en 260 ms desde 8 px abajo, con filete amarillo de 4 px arriba.

## Do's and Don'ts

### Do:
- **Do** poner cada color nuevo en `ui/tema.py` (y en `[theme]` si es del tema de Streamlit) y referenciarlo por su constante; los tableros JS lo reciben por `paleta_json()`.
- **Do** declarar en `PARES_CONTRASTE` todo par texto/fondo nuevo y mantenerlo ≥ 4,5:1.
- **Do** mostrar las cifras clave con `cifra_html` (o `st.metric`): número condensado, unidad chica, filete amarillo, ayuda en el rótulo.
- **Do** usar Material Symbols de contorno peso 300 (`:material/…:`) en Streamlit y SVG de línea de trazo 1,75 en los tableros.
- **Do** pintar cada producto con su color de `COLOR_PRODUCTO` en todo lugar donde aparezca.
- **Do** separar con filetes de 1 px y paneles tonales; dejar el resto en `texto_2`.
- **Do** respetar `prefers-reduced-motion`: sin transiciones ni animaciones.

### Don't:
- **Don't** escribir un hex fuera de `ui/tema.py` y `config.toml` (control 14 / N15).
- **Don't** usar el logo de Shell como marca de la app (ícono, encabezado, botones): sólo aparece dentro de la foto de portada al 30 % (decisión de Nico, 14/10/2026), con el aviso de "no afiliado a Shell" siempre visible.
- **Don't** usar emojis en ningún lugar: rótulos, pestañas, avisos ni botones.
- **Don't** meter las cifras clave en tarjetas con borde, sombra o fondo; el tótem no tiene caja.
- **Don't** usar el rojo de marca como texto ni como decoración; el texto de alerta va en `rojo_texto`.
- **Don't** poner más de una acción amarilla por sección, ni amarillo en algo que no sea luz, acción principal o el producto Súper.
- **Don't** agregar una segunda familia tipográfica ni un tema claro.
- **Don't** reutilizar un color de producto para otra categoría en el mismo gráfico.
