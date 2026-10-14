# 09 · Orígenes alternativos del camión cisterna (sólo los que se pueden respaldar)

Fecha: 13-oct-2026. Lo usa la tanda 8 (Registro RED-18 a RED-21). Alcance: combustibles **líquidos**; el GNC sale de la
red de gas y lo comprimen los 3 compresores de la estación, así que no tiene camión ni origen.

## 1. Qué se pidió revisar y qué se encontró

| Candidato | ¿Es un punto de despacho de combustible líquido? | Decisión |
|---|---|---|
| **Dock Sud** (Avellaneda, Buenos Aires) | Sí: refinería de Shell/Raízen; es el origen **documentado** de las estaciones Shell de Mendoza (Sitio Andino 27-oct-2023; Los Andes 31-jul-2023, nota 06) | Origen habitual (INV-05) |
| **Arroyo Seco** (Santa Fe) | Sí: **terminal de almacenamiento y despacho** de combustibles de Raízen/Shell, incluida en los activos vendidos a Mercuria (Diario Uno 4-jun-2026, nota 06; Perfil, El Economista, LM Neuquén: "terminales de almacenamiento y despacho de combustibles en Arroyo Seco y Santa Fe") | **Se agrega** como primer origen alternativo |
| **Luján de Cuyo** (Mendoza) | Sí: refinería de YPF, la única de Mendoza (Unidiversidad 2017, nota 06). No es de Shell: para una estación Shell es un abastecimiento de emergencia | Ya estaba en el Registro como alternativa de INV-05; queda como **segundo** origen alternativo |
| **La Paz** (Mendoza) | No. Es un nodo de la red de rutas (cruce de la RN 7 con la RP 153). No se encontró ninguna planta de despacho de combustibles ahí | **No se agrega** |
| **Pareditas** (San Carlos, Mendoza) | No. Es el empalme de la RN 40 con la RN 143 (nodo de la red). No hay planta de despacho | **No se agrega** |
| Terminal "Santa Fe" de Raízen | Sí existe, pero las fuentes no dicen dónde exactamente (ciudad de Santa Fe o el cordón portuario) | **No se agrega**: sin ubicación no hay ruta defendible |

No se encontró ninguna instalación de Shell/Raízen en Cuyo (nota 06: "ninguna en Cuyo citada").

## 2. La ruta de Arroyo Seco (RED-18)

| Tramo | km | Fuente |
|---|---|---|
| Arroyo Seco (−33,155; −60,508) → General Alvear, Mendoza (−34,977; −67,694) | **806,0** | OSRM sobre OpenStreetMap (router.project-osrm.org, perfil auto, consultado 13-oct-2026), cálculo propio |
| General Alvear → San Rafael (ya en la red, RED-05) | 87,5 (OSRM da 87,2: coincide) | nota 06 |

Arroyo Seco → San Rafael = 893,5 km, unos 98 km menos que Dock Sud (991 km). El arco es **una estimación** (OSRM es
para autos; el camión puede tomar otra ruta) y no es cortable.

## 3. Cómo se usa en el modelo (supuestos del grupo)

- **Orden de redirección (RED-19):** si el origen habitual no puede cumplir un pedido, se pasa a **Arroyo Seco** (misma
  empresa) y, si tampoco, a **Luján de Cuyo** (otra empresa: es el último recurso). Si ninguno puede, el pedido sale del
  habitual igual, con la demora de redirección.
- **Probabilidad de que un origen no pueda cumplir un pedido (RED-20): 5 %** (supuesto, sin estadística). La única
  referencia son los faltantes de Shell en Mendoza de julio y octubre de 2023 (Los Andes; Sitio Andino), sin una
  frecuencia. Alternativas para sensibilidad: 0 % y 15 %. Sin azar es una cuota exacta: uno de cada 20 pedidos de cada
  producto.
- **Demora de redirección (RED-21): 12 h** (supuesto): volver a gestionar el pedido con otra terminal. El plazo de un
  pedido redirigido es: plazo base (INV-01, que ya incluye el viaje desde Dock Sud) − viaje desde Dock Sud + viaje desde el
  origen usado + 12 h. Con los promedios: Arroyo Seco ≈ 36 − 14,2 + 12,8 + 12 ≈ 46,6 h; Luján ≈ 36 − 14,2 + 3,2 + 12 ≈ 37 h.
- Se puede **marcar a mano un origen como no disponible** desde el menú (por ejemplo, Dock Sud) para forzar el caso.
- Todo está **apagado por defecto**: sin los eventos, el camión sale siempre de Dock Sud por la ruta óptima, como antes.

## 4. Para el GNC

No se encontró nada verificable de "orígenes" del GNC para esta estación (el gas llega por gasoducto y el corte lo decide
el ENARGAS para todo el contrato interrumpible). No se propone nada.
