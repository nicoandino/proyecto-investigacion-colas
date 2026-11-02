# Demanda de 310 mil L/mes, personal y mezcla de vehículos (2/11/2026)

Nota del prompt del grupo *"demanda 310 mil litros, personal por turno y pestaña Montecarlo de vehículos"*. Reúne la
investigación del grupo (fuentes abiertas, según el prompt "verificadas") y lo que se buscó en esta sesión.
**Ojo:** desde el entorno de trabajo no se pudieron abrir `www2.vialidad.gob.ar` ni `elsol.com.ar` (dominios
bloqueados en la red de la sesión): los números del censo de la RN 143 se cargaron tal como vienen en el prompt.

## 1. Demanda base: 310.000 L/mes de combustibles líquidos (DEM-01)

**Supuesto adoptado** por el grupo, no un despacho medido de esta boca. Referencias que lo hacen defendible:

| Referencia | Valor | Fuente |
|---|---|---|
| Despacho promedio por estación, Argentina | ≈ 270 mil L/mes | Surtidores.com.ar, informe UNVENU/CLAEC — https://surtidores.com.ar/argentina-con-mas-estaciones-de-servicio-que-el-promedio-regional-pero-con-menos-litros-vendidos/ |
| Distribución de estaciones por volumen | 51 % ≤ 250 mil · 37 % entre 250 y 600 mil · 12 % > 600 mil | CECHA vía Télam / Sitio Andino — https://www.sitioandino.com.ar/n/205382-la-venta-de-combustible-cayo-3-en-5-meses (fecha original vieja: verificar) |
| En Mendoza el gasoil vende más que la nafta | sí | Secretaría de Energía vía Politikon Chaco — https://www.elonce.com/uid-833863 |
| Cargas fijas o menores por el precio | cualitativo | Tiempo de San Juan (2026) — https://www.tiempodesanjuan.com/economia/bajon-los-surtidores-el-aumento-la-nafta-profundiza-la-caida-del-consumo-tercer-mes-consecutivo-n431388 |

No incluye el GNC (m³, DEM-05). Con 39,7 L por vehículo: ≈ 10.200 L/día y ≈ 257 vehículos/día de líquidos.

## 2. Composición del tránsito (VEH-08) y motos (VEH-09)

DNV 4º Distrito, *Estudio de tránsito RN 143*, censo de cobertura de 48 h en El Toledano (prog. 528), marzo de 2018;
IF-2021-06581772-APN-DMZA#DNV (enero de 2021) —
https://www2.vialidad.gob.ar/sites/default/files/IF-2021-06581772-APN-DMZA%25DNV.pdf

| Tipo | Valor |
|---|---|
| Autos | 70,5 % (4.740 de 6.720 veh/día) |
| Camionetas (columna "Cta.+r") | 19,8 % (1.330 de 6.720) |
| Ómnibus | 1,6 % |
| Camiones (sin acoplado 5,3 + con acoplado 0,9 + semi 1,9) | 8,1 % |
| TMDA San Rafael – Emp. RP 150 | 5.615 veh/día (2018), crecimiento 3 %/año (DNV) |

La RN 143 es la propia Av. Balloffet dentro de la ciudad. El censo **no clasifica motos**. En el parque de San Rafael
hay 55.192 motos y 90.065 automotores (Todo Riesgo con datos DNRPA, ago-2021 —
https://www.todoriesgo.com.ar/mendoza-evolucion-interanual-parque-automotor-motovehiculos-2021/): ≈ 38 %, pero cargan
poco y menos seguido ⇒ **20 % de las visitas** (supuesto, confianza baja). El 80 % restante con el censo:

| Moto | Auto | Camioneta | Colectivo | Camión |
|---|---|---|---|---|
| 0,2000 | 0,5640 | 0,1584 | 0,0128 | 0,0648 |

Búsquedas de esta sesión (2/11/2026) que llegan a lo mismo: ninguna fuente publica cargas por tipo de vehículo y por
día en una estación; Vialidad en los accesos de Mendoza (MDZ, 8/6/2019): 86,7 % autos y camionetas; AFAC (2023): 3 %
del parque son pesados; Mendoza 2025: 25.282 autos y 22.671 motos 0 km (Sitio Andino); San Rafael 2024: 2.808 motos
0 km (+35 %, Diario San Rafael). URLs:
https://www.mdzol.com/sociedad/2019/6/8/ranking-de-las-rutas-mas-transitadas-de-mendoza-31383.html ·
https://mendozatoday.com.ar/2024/07/24/hay-casi-153-millones-de-vehiculos-circulando-por-el-pais-y-mendoza-es-una-de-las-tres-provincias-con-mayor-flota/ ·
https://www.sitioandino.com.ar/economia/crece-el-parque-automotor-mendoza-las-inscripciones-0km-aumentaron-casi-54-2025-n5715684 ·
https://diariosanrafael.com.ar/san-rafael-cerro-el-2024-con-menos-ventas-de-autos-y-maquinas-pero-muchas-mas-motos/ ·
https://datos.transporte.gob.ar/dataset/tmda

## 3. Litros y tiempo de playero por tipo (VEH-10, TIE-07; supuestos)

| Tipo | Litros Triangular | Media | Playero (min) | Justificación |
|---|---|---|---|---|
| Moto | (3, 6, 12) | 7,0 | (2, 3, 5) | tanques de 10–15 L |
| Auto | (10, 25, 50) | 28,3 | (3, 4,5, 8) | tanque ≈ 50 L; carga parcial o fija frecuente |
| Camioneta | (15, 40, 80) | 45,0 | (3,5, 5, 9) | Hilux, Ranger, Amarok ≈ 80 L; mayoría diésel |
| Colectivo | (80, 150, 250) | 160,0 | (6, 9, 14) | ≈ 35 L/100 km; tanques de 275+ L |
| Camión | (60, 150, 400) | 203,3 | (6, 10, 16) | 30–40 L/100 km; livianos y semis |

Litros medios por vehículo = 39,73 L (DEM-11). Tiempo medio de playero ≈ 5,3 min. **Ojo con la definición:** el
benchmark de Tucumán (abajo) mide la ocupación de la cara (maniobra + carga + pago, ≈ 9,8 min); el modelo usa estos
tiempos como **tiempo del playero** (el recurso que atiende), que es lo que limita en esta estación.

Nota: VEH-03 (moto 110 cc, tanque 3,7 L) queda en el Registro: ahora sólo escala las cargas en el eje de sensibilidad
C13; los litros de la moto son los de VEH-10.

## 4. Benchmark de cola (REF-01)

UNT, FACE, *Herramientas para análisis de demanda en La Estación SRL* (Shell Tucumán, 8 surtidores), ago-2026 —
https://face.unt.edu.ar/web/iadmin/wp-content/uploads/sites/2/2026/08/A32-HERRAMIENTAS-PARA-ANALISIS-DE-DEMANDA-EN-LA-ESTACION-SRL.pdf:
pico 18–19 h, λ = 40 veh/h, μ = 6,12 veh/h por surtidor, utilización 82 %, Wq 3,32 min, Lq 2,21.

## 5. Encargado (PER-08; supuesto)

Pasa cada 6 h, desfasado de los turnos (06 · 14 · 22): a las 02 · 08 · 14 · 20 h. Se queda una ventana
Triangular(20, 40, 60) min; colabora como un servidor más si hay ≥ 3 vehículos esperando (se mira minuto a minuto) o si
sale un sorteo con p = 0,30. Fuera de la ventana no atiende.
