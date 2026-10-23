---
version: 1
slug: "app-py"
primary_target: "app.py"
related_targets: ["ui/tema.py","ui/animacion.py","ui/vistas.py"]
---

# Surface brief: la app del simulador (app.py)

Scope: toda la app de Streamlit (menú inicial, resultados en pestañas, editar, escenario único, caso de informe) y el
tablero animado. Mode: **Operate**. Audiencia: Nico presentando en vivo en su notebook, el profesor mirando.
Pedido: colores de Shell, modo oscuro, más elegante (tipografías incluidas), sin emojis (íconos de línea Material
Symbols); pestañas arriba; fuentes guardadas en el proyecto (sin internet).
Intocable: contenido, números, flujo, "¿Cómo se comprueba?", reglas de CLAUDE.md (colores sólo en ui/tema.py).

## Direction contract

THESIS: La app se lee como el tótem de precios de la estación de noche: pocas cifras enormes, iluminadas, sobre negro,
y todo lo demás callado. Rechaza el dashboard de tarjetas con borde y emojis.

OWN-WORLD: Asfalto casi negro cálido, paneles apenas más claros con filetes de 1 px; el amarillo Shell es la luz (la
franja de la marquesina, la acción principal, la pestaña activa) y el rojo Shell sólo alerta (quiebres, pérdidas, la
línea bajo la franja). Una sola grotesca de ancho variable (Archivo): condensada y pesada para las cifras del tótem,
normal para el texto; cifras tabulares. Íconos de línea finos.

STORY: Nico elige el período, simula y defiende cada número; el profesor ve primero las cifras grandes y después la
cuenta.

FIRST VIEWPORT: Arriba, la franja amarilla de la marquesina con la línea roja; debajo, el encabezado en mayúsculas
condensadas con el período a la derecha y "Cambiar período"; las pestañas con íconos y el indicador amarillo; las
cifras clave como dígitos de tótem.

FORM: Tótem de precios nocturno, candidato 1 de mi lista (IMPECCABLE'S PICK), seed 75b538a9. Interacción firma: las
cifras de tótem con su unidad chica y su filete amarillo; la pestaña activa se enciende como un precio.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
