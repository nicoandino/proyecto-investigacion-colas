# 14 · Vehículos por tipo: motos, autos, colectivos y camiones (2/11/2026)

Pedido de Nico: una pestaña que sortee por día cuántas motos, autos, colectivos y camiones cargan. Si hay un
promedio publicado por día o por mes, se usa; si no, Monte Carlo.

## ¿Hay un dato publicado por día o por mes? No.

Búsqueda del 2/11/2026 (Vialidad Nacional, Secretaría de Energía, DNRPA/ACARA, DEIE Mendoza, prensa de San Rafael):

- **Ninguna fuente cuenta cargas por tipo de vehículo en una estación** de San Rafael ni de Mendoza. La Secretaría de
  Energía publica litros por producto y por estación (es la serie PRO-01), no vehículos.
- **Vialidad Nacional (TMDA)** cuenta tránsito en las rutas, no cargas. El portal de datos abiertos de Transporte
  tiene el TMDA de 2017 (datos.transporte.gob.ar/dataset/tmda); hay un expediente del 4º Distrito Mendoza con censos de
  RN 40 y RN 143 (IF-2021-06581772-APN-DMZA#DNV) que no se pudo abrir desde el entorno (dominio bloqueado). **Pendiente:**
  bajar ese PDF y ver si trae la composición del tramo urbano de la RN 143 (Av. Balloffet).
- **No hay un TMDA publicado de la RN 143 en San Rafael** en la prensa (sólo notas de la obra de refuncionalización
  San Rafael – Pareditas, 107 km).

Conclusión: se sortea (Monte Carlo). Los clientes por día salen de la simulación (litros/mes ⇒ clientes); el sorteo
dice de qué tipo es cada uno.

## Proporciones que sí hay (referencias del sorteo)

| Fuente | Qué dice | Uso |
|---|---|---|
| Vialidad, citada por MDZ (8/6/2019), accesos Este y Sur de Mendoza (RN 7 / RN 40) | 86,7 % autos y camionetas · 9,9 % camiones sin acoplado, ómnibus de corta distancia y combis · 3,4 % ómnibus de larga distancia y camiones con acoplado (TMDA ≈ 91.342) | Control: el modelo da 86,7 % de livianos sin haber usado este dato |
| AFAC (julio 2024, parque 2023, nacional) | 79,5 % autos · 17,5 % comerciales livianos · 3 % comerciales pesados (camiones y ómnibus); sin motos | Los pesados son pocos |
| Sitio Andino (2026): inscripciones 0 km en Mendoza 2025 | 25.282 autos y 22.671 motos | Las motos son muchas, pero cargan ≈ 2 L |
| Diario San Rafael (ene-2025): 0 km en San Rafael 2024 | 1.442 autos y máquinas · 2.808 motos (+35 %) | Ídem, a nivel departamento |
| DEIE Mendoza (cierre 2024, vía El Sol) | 907.079 vehículos en condiciones de circular | Contexto; sin desglose por tipo |
| Sociedad de Transporte de Mendoza, estadísticas 2025 | 27 buses diésel y 18 eléctricos (Gran Mendoza) | Los colectivos urbanos cargan en su depósito |

## La tabla de Monte Carlo (pestaña Vehículos)

Paso 1 — probabilidad de cada tipo, del propio modelo: Σ productos (probabilidad de llegada del producto, DEM-04 y
DEM-05) × (tipo de vehículo según el producto, VEH-00). Con 310.000 L/mes:

| Tipo del motor | % de los clientes | Categoría de la pestaña |
|---|---|---|
| moto | 5,4 % | Motos |
| auto + pick-up + auto GNC | 86,7 % | Autos y camionetas |
| camión / ómnibus (VEH-04) | 7,9 % | se parte: 15 % colectivos (VEH-08, supuesto) → 1,2 %; 85 % camiones → 6,7 % |

Los colectivos son un **supuesto del grupo** (VEH-08 = 15 % de los pesados, rango 5–30 %): los urbanos cargan en el
depósito de la empresa; los que paran en una estación son de media y larga distancia, chárter y turismo.

Pasos 2 a 5: acumulada, intervalos de 0000 a 9999, un número aleatorio por cliente y conteo por día.

## URLs

- https://www.mdzol.com/sociedad/2019/6/8/ranking-de-las-rutas-mas-transitadas-de-mendoza-31383.html
- https://datos.transporte.gob.ar/dataset/tmda
- https://www2.vialidad.gob.ar/sites/default/files/IF-2021-06581772-APN-DMZA%25DNV.pdf (no se pudo abrir)
- https://mendozatoday.com.ar/2024/07/24/hay-casi-153-millones-de-vehiculos-circulando-por-el-pais-y-mendoza-es-una-de-las-tres-provincias-con-mayor-flota/
- https://www.sitioandino.com.ar/economia/crece-el-parque-automotor-mendoza-las-inscripciones-0km-aumentaron-casi-54-2025-n5715684
- https://diariosanrafael.com.ar/san-rafael-cerro-el-2024-con-menos-ventas-de-autos-y-maquinas-pero-muchas-mas-motos/
- https://www.elsol.com.ar/mendoza/el-parque-automotor-en-mendoza-tuvo-un-notable-crecimiento-calculan-que-hay-un-vehiculo-cada-dos-personas/
- https://stmendoza.com/wp-content/uploads/2026/04/Estadisticas-de-Operaciones-2025-Sociedad-de-Transporte-de-Mendoza.pdf

Las cifras se tomaron de los resúmenes del buscador; las páginas de Vialidad y El Sol no se pudieron abrir desde el
entorno de trabajo. Antes de citarlas en el informe, abrirlas y confirmar.
