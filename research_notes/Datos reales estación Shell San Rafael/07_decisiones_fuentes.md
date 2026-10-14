# 07 · Cómo se resolvió cada contradicción entre fuentes (criterio único)

Fecha: 13-oct-2026. Reemplaza las "advertencias abiertas" de la app: cada contradicción C1–C20 tiene ahora **un valor
elegido** con un criterio que se puede repetir. Las alternativas que perdieron siguen en el Registro (`sim/datos.py`)
porque son los extremos del análisis de sensibilidad (tornado), pero la app muestra sólo el valor elegido.

## El criterio (se aplica en este orden; el primer paso que desempata, decide)

0. **Que mida la misma cosa.** Una fuente oficial que mide otra magnitud (por ejemplo, el parque de autos a GNC del
   país) no le gana a una que mide lo que el modelo necesita (los clientes de una estación).
1. **Fuente oficial o primaria** sobre secundaria (Secretaría de Energía, ENARGAS, DGE, API de Shell, ficha del
   fabricante > prensa > documentos del grupo sin fuente). Una fuente oficial **no vigente** (precios congelados) no gana.
2. **Más reciente** sobre más vieja.
3. **Más específica** de San Rafael / Mendoza sobre la general (Argentina, otra ciudad).
4. **Empate:** la **más conservadora**, la que menos exagera el efecto que se estudia (el valor central de un rango, o
   el que no favorece la conclusión).

**Lo que este criterio NO hace:** convertir una estimación en una medición. La estación no aportó datos propios; elegir
la mejor fuente disponible no cambia eso. En la app queda una sola frase general: *"Los valores provienen de fuentes
públicas y estimaciones; la estación no aporta mediciones propias."* Los márgenes por litro, el flete y el costo de
almacenamiento siguen siendo **heredados sin fuente** y se rotulan así (no se marcan como confirmados).

## Decisiones

| ID | Tema | Valor elegido | Paso que decide | Por qué |
|---|---|---|---|---|
| C1 | Horario de la playa | 24 h | 1 (oficial) | API de Shell (`twenty_four_hour`, leída 5-oct-2026) contra un "cierre 22–06" sin fuente. |
| C2 | Demanda mensual | 270.000 L/mes | 3 (más específica) | Ninguna fuente es oficial para esta estación; 270.000 es la estimación regional y cae dentro del promedio nacional (270–380 mil) y del punto de equilibrio (315–400 mil). 150 y 400 mil quedan como extremos de sensibilidad. |
| C3 | Litros vs. autos | Litros/mes de entrada; clientes derivados | 0 (misma cosa) | No es una disputa de datos: los documentos viejos llamaban "autos" a los litros. |
| C4 | Entrada al minimarket | 20 % | 1 (la única con fuente declarada) | 15, 30 y 45 % no tienen fuente. |
| C5 | Personal | Playeros 1·2·2; 1 caja | 3 (más específica) | DATOS §4 es el único desglose por rol y turno; 2·3·3 (ONBOARDING) no tiene fuente. |
| C6 | Mix diésel G2/G3 | 55 / 45 | 2 (más reciente) y 1 | Surtidores.com.ar (ago-2026) con fuente declarada; la Secretaría de Energía confirma que se venden ambos. |
| C7 | Mezcla de producto | Litros: Súper 28,0 · V-Power 19,5 · G2 29,3 · G3 23,2 %; GNC 3 % de los clientes | 0 (misma cosa) | El 11 % de ENARGAS es la proporción del **parque** de autos a GNC, no de clientes de esta estación. |
| C8 | 6 caras de GNC para ≈ 3 % | Se modela la estación como está | 0 | No son dos fuentes en conflicto: el número de caras se observó y el 3 % es la demanda. Que los compresores queden poco usados es un **resultado** del modelo, y así se informa. |
| C9 | GNC en invierno | Corte total por episodios (2 × 6 días, jun–ago), contrato interrumpible, 3 compresores | 1 (oficial) + 3 | ENARGAS (abr-2026) para la forma del corte y Sitio Andino (San Rafael, 2022) para la duración. |
| C10 | Estacionalidad | Neutra + calendario de temporadas (tanda 5) | 0 | La ocupación hotelera no es venta de combustible; la serie mensual de la Secretaría de Energía no está cargada. El calendario es un supuesto moderado y editable (nota 08). |
| C11 | Tiempo de servicio | Triangular(2, 5, 8) min; GNC (5, 7, 12); caja (2, 4, 10) | 4 (conservadora) | Ninguna fuente es local ni más reciente que la otra; la media de 5 min es más larga que la de 3,7: no subestima la espera. |
| C12 | Litros por carga | Triangular(0,20·T; 0,30·T; 1,00·T) | 1 (único dato empírico) | Nota 03: ≈ 30 % del tanque. |
| C13 | Tanques de vehículos | Auto 47 L; camión 300 L | 1 (ficha del fabricante) | Autocosmos para el auto; el camión es supuesto (no hay fuente mejor). |
| C14 | Servicios | Shop, baño, aire y agua (lista oficial de Shell); en la app el shop se llama "Shell Shop" | 1 (oficial) | Lavadero y Agroservice no figuran en la lista oficial. "Shell Shop" es el nombre genérico que usa la app. |
| C15 | Autoservicio | Servicio atendido | 1 (oficial) | API de Shell (`full_service`, `manned`). |
| C16 | Perfil horario | Tabla de 24 factores de DATOS §2 (picos 07–10 y 16–18) | 3 (más específica) | El perfil heredado es del proyecto hipotético. |
| C17 | Fin de semana | × 1,30 normalizado al mes | 4 (conservadora) | Única fuente (DATOS §2) da un rango 1,24–1,50: se toma el valor central. |
| C18 | Salarios | Playero $1.680.000 · cajero $1.800.000 · encargado $1.740.000 (costo con adicionales) | 1 (cámara del sector, FECRA) | Es la escala de enero-2026; el básico sin adicionales subestima el costo de un empleado. |
| C19 | Precios de referencia | Súper $2.141 · Premium $2.300 · G2 $2.116 · G3 $2.641 · GNC $699/m³ | 2 (más reciente) | Los precios de la propia estación en la Secretaría de Energía están congelados desde 2025 (oficial pero no vigente). |
| C20 | Otros (Mercuria, tránsito, etc.) | Informativos: no entran al modelo | — | — |
| DEM-09 | Vacaciones de invierno | **6 al 17 de julio de 2026** | 1 (oficial) + 2 | Calendario escolar de la DGE de Mendoza (citado por Los Andes, Ámbito y El Sol); el "9–20 jul" anterior no coincide. Detalle en la nota 08. |

## Qué pasó con las "advertencias" de la pantalla La estación

| Advertencia vieja | Qué se hizo |
|---|---|
| "Cada contradicción se muestra con el valor adoptado y las alternativas" | Ahora se muestra sólo el valor elegido y el criterio. |
| Precios de la estación congelados en la SE | Resuelto en C19 (gana la fuente más reciente). |
| `[RESUMEN]`: tanques de pick-up, moto, cilindro y tiempo de GNC sin verificar en el original | Sigue como nota de cada dato en el Registro (tipo y confianza), no como advertencia. |
| Cifras "confirmadas" sin URL (270.000 L/mes, 20 % de minimarket, compresor 20–25 autos/h) | Son estimaciones: así figuran en el Registro (tipo `estimacion`/`supuesto`, confianza baja). Ninguna se presenta como confirmada. La "Res. ENARGAS 409/2026" no se cita. |
| Alerta de coherencia C8 | Resuelta en C8: es un resultado del modelo y se informa como tal. |
| Dock Sud como origen documentado | Es el origen elegido (INV-05); los alternativos están en la nota 09. |
| El GNC se mide en m³ | Es una regla del modelo, no una advertencia: sigue en la pestaña GNC. |
| Sin datos de la propia estación | Queda como **la única frase general** de la pantalla. |
