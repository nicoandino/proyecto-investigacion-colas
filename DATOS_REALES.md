# DATOS_REALES — los datos del modelo, con su fuente

> Generado desde el Registro (`sim/datos.py`) con `reports/generar_datos_reales.py`. **No se edita a mano:**
> si un dato cambia, se cambia en el Registro y se regenera este archivo.

## Cómo leerlo

- **No hay mediciones de la propia estación.** Los datos vienen de fuentes públicas (Shell, Secretaría de Energía,
  ENARGAS, prensa, papers) o son supuestos del grupo. Cada fila dice cuál es cuál.
- **Tipo:** 🟢 dato (fuente primaria u oficial) · 🟡 estimación (se deriva de fuentes débiles) · 🔵 observación propia
  (medida en la estación; todavía no hay ninguna) · 🟠 supuesto del grupo · ⚪ heredado (del proyecto hipotético, **sin fuente**).
- **Nivel:** A la estación · B San Rafael · C Mendoza · D ciudad parecida · E Argentina u otro.
- **Confianza:** alta · media · baja · sin dato.
- **Alternativas:** los valores que perdieron frente al adoptado; no se descartan, se usan como escenarios.
- El GNC se mide en **m³**, nunca en litros. Los clientes por día **se derivan** de litros/mes ÷ litros medios por cliente.

**Resumen:** 119 datos · 🟢 dato 37 · 🟡 estimación 18 · ⚪ heredado 13 · 🟠 supuesto 51

## La estación

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| EST-01 | Dirección | Balloffet 1810 esq. Los Sauces, San Rafael, Mendoza, CP 5600 | — | 🟢 dato | la estación | alta | Shell (API oficial) + Secretaría de Energía | — |
| EST-02 | Operador / CUIT | LOS SAUCES S.R.L. / 30-67218048-8 | — | 🟢 dato | la estación | alta | Shell, Secretaría de Energía, OSM | — |
| EST-03 | Bandera | Shell (SHELL C.A.P.S.A., id 674) | — | 🟢 dato | la estación | alta | Secretaría de Energía | — |
| EST-04 | Coordenadas | −34,62833 ; −68,35832 | ° | 🟢 dato | la estación | alta | OSM / relevamiento del grupo | — |
| EST-05 | Horario de la playa | 24 h (abre todos los días) | h | 🟢 dato | la estación | alta | Shell API `twenty_four_hour` (leída el 5/10/2026) | — |
| EST-06 | Horario del minimarket | 24 h (supuesto: igual que la playa) | h | 🟠 supuesto | la estación | baja | grupo / DATOS §5 (Shell API: unknown) | 06–22 = 06–22 |
| EST-07 | Servicios | tienda (Shell Shop, ≈ 140 m²), baño, aire y agua, servicio atendido, pago en surtidor/móvil, tarjeta de flota | — | 🟢 dato | la estación | media | lista oficial Shell + DATOS §5 | — |
| EST-08 | Calzadas | Balloffet = RN 143 (tramo urbano, 4 carriles, 60 km/h); Los Sauces = RP 158 | — | 🟢 dato | la estación | media | Vialidad / OSM | — |
| EST-09 | Cercanía | otras Shell a 2,26 y 3,60 km; ninguna estación a < 1,5 km | km | 🟢 dato | San Rafael | alta | relevamiento del grupo (OSM) | — |
| EST-10 | Contexto corporativo | venta a Mercuria (firmada en jun-2026; informativo) | — | 🟢 dato | Argentina / otro | media | nota 01 (jun-2026) / DATOS §5 ('1/9/2026') | — |

## Surtidores y compresores

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| SUR-00 | Grupos de la estación real (zona · caras · productos) | (('A', 'Nafta', 4, ('super', 'vpower'), True), ('B', 'Diésel', 2, ('diesel_g2', 'diesel_g3'), True), ('C', 'GNC', 6, ('gnc',), False)) | caras | 🟢 dato | la estación | media | capturas de Google Maps (grupo) + Secretaría de Energía | — |
| SUR-01 | Caras por surtidor | 2 | caras | 🟢 dato | la estación | media | capturas de Google Maps (grupo) | — |
| SUR-02 | Grupo A (nafta) | S1, S2 → 4 caras → Súper y V-Power | caras | 🟢 dato | la estación | media | capturas de Google Maps (grupo) · V3 | — |
| SUR-03 | Grupo B (diésel) | S3 → 2 caras → G2 y G3 | caras | 🟢 dato | la estación | media | capturas del grupo + Secretaría de Energía | sólo G2 = sólo G2 |
| SUR-04 | Grupo C (GNC) | S4–S6 → 6 caras | caras | 🟢 dato | la estación | media | capturas de Google Maps (grupo) | — |
| SUR-05 | Vehículos por cara | 1 | vehículos | 🟠 supuesto | la estación | media | grupo | — |
| SUR-06 | Compresores GNC | 3 | compresores | 🟠 supuesto | la estación | sin_dato | ONBOARDING sin fuente · C9 | sin límite = 6 · 2 = 2 |

## Personal

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| PER-01 | Playeros por turno (noche·mañana·tarde) | (1, 2, 2) | personas | 🟡 estimación | la estación | baja | DATOS §4 (único desglose por rol) | 2·3·3 = (2, 3, 3) |
| PER-02 | Cajeros (cajas) por turno | (1, 1, 1) | cajas | 🟡 estimación | la estación | baja | DATOS §4 | — |
| PER-03 | Encargado / personal de tienda | encargado 1 (M, T); tienda 1 (M, T) — sólo costo | personas | 🟡 estimación | la estación | baja | DATOS §4 | — |
| PER-04 | El GNC retiene playero | False | — | 🟠 supuesto | la estación | sin_dato | orquestador | sí = True |
| PER-05 | Capacidad de cola por grupo | 8 | autos | 🟠 supuesto | la estación | sin_dato | orquestador (relevar) | 4 = 4 · 14 = 14 |
| PER-07 | Lugares de cola por cara | 3 | autos | 🟠 supuesto | la estación | sin_dato | pedido del grupo (6/10/2026): todas las caras tienen la misma capacidad de cola | 8 por zona = 8 |
| PER-06 | Disciplina de cola | por_grupo | — | 🟠 supuesto | la estación | sin_dato | CASO §7 | por_cara = por_cara |

## Demanda

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| DEM-00 | Modo de demanda por defecto | esperada | — | 🟠 supuesto | la estación | sin_dato | orquestador (N5: el Monte Carlo se conserva para tipo de cliente y producto; el total diario sale de los litros) | monte_carlo = monte_carlo |
| DEM-01 | Demanda mensual | 270000.0 | L/mes | 🟡 estimación | San Rafael | baja | ONBOARDING + notas 01/03 + DATOS §1 (sin URL confirmada) | 150.000 = 150000.0 · 400.000 = 400000.0 |
| DEM-02 | Perfil horario (24 factores) | (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.5, 3.5, 3.5, 3.5, 2.0, 2.0, 1.5, 1.5, 1.5, 1.5, 3.0, 3.0, 2.0, 2.0, 1.5, 1.5, 1.0, 1.0) | factor | 🟡 estimación | San Rafael | baja | DATOS §2 (tabla de 24 factores, §14.3) | heredado = (0.3, 0.2, 0.15, 0.15, 0.25, 0.6, 1.1, 1.8, 2.0, 1.5, 1.1, 1.0, 1.2, 1.1, 0.9, 0.9, 1.0, 1.4, 1.9, 2.0, 1.6, 1.1, 0.7, 0.4) |
| DEM-03 | Factor de fin de semana | 1.3 | × | 🟡 estimación | San Rafael | media | DATOS §2 (tabla ×1,3–1,5) | 1,24 = 1.24 · 1,50 = 1.5 |
| DEM-04 | Mezcla de producto en litros (líquidos) | (('super', 28.0), ('vpower', 19.5), ('diesel_g2', 29.3), ('diesel_g3', 23.2)) | % | 🟡 estimación | San Rafael | baja | DATOS §7 (Surtidores.com.ar, mercado por volumen) | mix de flota · G2/G3 75/25 = 0.75 · sólo G2 (100/0) = 1.0 |
| DEM-05 | Clientes GNC (% de las llegadas) | 0.03 | % | 🟡 estimación | San Rafael | baja | DATOS §7 | 11 % = 0.11 · 20 % = 0.2 |
| DEM-06 | Estacionalidad mensual (12 factores) | (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0) | factor | 🟠 supuesto | San Rafael | sin_dato | orquestador (C10) | leve ±6 % = (1.06, 1.052, 1.03, 1.0, 0.97, 0.948, 0.94, 0.948, 0.97, 1.0, 1.03, 1.052) · proxy turístico = (1.3636425620116455, 0.8181855372069873,… |
| DEM-07 | Variabilidad día a día (Monte Carlo) | ((0.78, 0.89, 1.0, 1.11, 1.22), (10, 20, 40, 20, 10)) | factor | ⚪ heredado | San Rafael | sin_dato | tabla original del proyecto hipotético, reescalada a relativa | — |
| DEM-07C | Tabla de demanda del motor (valores absolutos) | ((280, 320, 360, 400, 440), (10, 20, 40, 20, 10)) | autos/día | ⚪ heredado | San Rafael | sin_dato | proyecto hipotético (la reescala relativa de DEM-07 entra en Fase 2) | — |
| DEM-08 | Entrada al minimarket | 0.2 | % | 🟡 estimación | San Rafael | baja | ONBOARDING ('dato directo YPF', no confirmado) | 15 % = 0.15 · 30 % = 0.3 · 45 % = 0.45 |
| DEM-09 | Eventos (opcionales) | Vendimia, Las Leñas, Carnaval, vacaciones de invierno (escenarios, no default) | — | 🟢 dato | San Rafael | baja | DATOS §6 | — |
| DEM-10 | Cierre de ruta y demanda | la cuantificación es un escenario, no un default | — | 🟠 supuesto | San Rafael | sin_dato | DATOS §6 | — |
| DEM-11 | Litros medios por cliente líquido | 35.7 | L/cliente | 🟡 estimación | San Rafael | media | cadena de demanda §14.2 (mezcla DEM-04 × cargas medias §5-D) | — |
| DEM-13 | Duplicar la demanda en la hora pico (Editar simulación) | 2.0 | × | 🟠 supuesto | San Rafael | sin_dato | pedido del grupo (6/10/2026) | — |
| DEM-14 | Calendario de demanda: factor de cada temporada | (('verano', 1.06), ('vacaciones_invierno', 1.08), ('invierno', 0.94)) | × | 🟠 supuesto | San Rafael | baja | grupo (13/10/2026), nota 08: la mitad del desvío del proxy turístico (DATOS §6) respecto de su promedio, porque la ocupación hotelera exagera el ef… | neutro = (('verano', 1.0), ('vacaciones_invierno', 1.0), ('invierno', 1.0)) |
| DEM-15 | Vacaciones de invierno de Mendoza (receso escolar 2026) | ((7, 6), (7, 17)) | mes, día | 🟢 dato | Mendoza | media | calendario escolar 2026 de la DGE de Mendoza, citado por Los Andes (6-jul-2026), Ámbito y El Sol (nota 08; el sitio de la DGE no se pudo abrir) | 9–20 jul = ((7, 9), (7, 20)) |
| DEM-12 | Cambio de quincena (S12): factor y días del mes | (2.0, (16, 17, 18)) | × · día del mes | 🟠 supuesto | San Rafael | sin_dato | DATOS §2 (+100 % 1–3 días/mes; limitación de camiones, fuente débil); los días 16–18 (cambio de quincena) son una elección del grupo | +50 % = (1.5, (16, 17, 18)) · fin de mes = (2.0, (1, 2, 3)) |

## Vehículos y litros por carga

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| VEH-01 | Auto: tanque y carga | (47.0, (9.4, 14.1, 47.0)) | L | 🟢 dato | San Rafael | media | nota 03 D16 (Autocosmos, leído en el original) | 42 L = 42.0 · 52 L = 52.0 |
| VEH-02 | Pick-up / utilitario: tanque y carga | (80.0, (16.0, 24.0, 80.0)) | L | 🟢 dato | San Rafael | media | nota 03 D18 (sólo resumen de buscador) | — |
| VEH-03 | Moto 110 cc: tanque y carga | (3.7, (0.74, 1.11, 3.7)) | L | 🟢 dato | San Rafael | media | nota 03 D19 (sólo resumen de buscador) | 3,5 L = 3.5 · 4,1 L = 4.1 |
| VEH-04 | Camión / ómnibus: tanque y carga | (300.0, (60.0, 90.0, 300.0)) | L | 🟠 supuesto | San Rafael | sin_dato | orquestador / DATOS §8 ('Alta' sin fuente argentina) | 120 L = 120.0 · 600 L = 600.0 |
| VEH-05 | Auto GNC: cilindro y carga | (14.0, (2.8, 4.2, 14.0)) | m³ | 🟢 dato | San Rafael | baja | nota 03 §2.10 (sólo resumen de buscador) | — |
| VEH-06 | Litros por carga del motor (una sola distribución) | (15.0, 30.0, 60.0) | L | ⚪ heredado | San Rafael | sin_dato | proyecto hipotético (el desglose por tipo de vehículo entra en Fase 2) | — |
| VEH-07 | Presets de litros por carga (C12): media baja y alta | (('bajo', (0.1, 0.3, 0.5)), ('alto', (0.6, 0.8, 1.0))) | × tanque | 🟠 supuesto | San Rafael | sin_dato | orquestador C12 (nota 03: se carga ≈ 30 % del tanque; llenar es raro) | — |
| VEH-00 | Tipo de vehículo por producto (matriz) | (('super', (0.12, 0.85, 0.03, 0.0)), ('vpower', (0.0, 0.85, 0.15, 0.0)), ('diesel_g2', (0.0, 0.2, 0.55, 0.25)), ('diesel_g3', (0.0, 0.15, 0.45, 0.4… | % | 🟠 supuesto | San Rafael | sin_dato | orquestador (diseño 'producto primero', §7.2) | — |

## Tiempos de servicio

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| TIE-01 | Caudal de la manguera | 40.0 | L/min | 🟢 dato | Argentina / otro | baja | nota 03 D22/D23 (Paraguay 2012) | 90 L/min = 90.0 · 120 L/min = 120.0 |
| TIE-02 | Carga nafta/diésel (por vehículo en la cara) | (2.0, 5.0, 8.0) | min | 🟠 supuesto | Argentina / otro | media | DATOS §3 (papers UNLP/UTN/UNC, sin medición en San Rafael) | nota 03 = (2.4, 3.7, 5.0) |
| TIE-03 | Extra de camión/ómnibus | + litros ÷ 90 | min | 🟠 supuesto | San Rafael | baja | orquestador | — |
| TIE-04 | Carga GNC | (5.0, 7.0, 12.0) | min | 🟠 supuesto | San Rafael | media | DATOS §3 | nota 03 = (10.0, 15.0, 30.0) |
| TIE-05 | Compra en el minimarket | (2.0, 4.0, 10.0) | min | 🟠 supuesto | San Rafael | baja | DATOS §3 | heredado = (1.5, 3.0, 6.0) |
| TIE-06 | Paciencia (cola de cara / cola de caja) | (10.0, 8.0) | min | ⚪ heredado | San Rafael | sin_dato | proyecto hipotético | 5 min = 5.0 · 20 min = 20.0 |

## Abastecimiento e inventario

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| INV-01 | Plazo pedido→entrega | (24.0, 36.0, 48.0) | h | 🟢 dato | Mendoza | media | Sitio Andino 27-oct-2023 'casi 1 día y medio' (Shell Mendoza capital); extremos supuestos | — |
| INV-02 | Carga del camión | 30000.0 | L | 🟡 estimación | Argentina / otro | media | 27.000 L (2023) y 34.000 L (2009) | 27.000 = 27000.0 · 34.000 = 34000.0 |
| INV-03 | Tanque por producto líquido | 20000.0 | L | 🟠 supuesto | la estación | baja | aviso de venta Guaymallén, no verificado | 10.000 = 10000.0 · 25.000 = 25000.0 |
| INV-04 | Descarga del camión | 45.0 | min | 🟠 supuesto | Mendoza | sin_dato | orquestador | — |
| INV-05 | Origen del abastecimiento | Dock Sud | — | 🟢 dato | Mendoza | media | Sitio Andino 2023, Los Andes 2023 | Luján de Cuyo = Luján de Cuyo |
| INV-06 | Política real de reposición | no documentada (pedido 'a demanda') | — | 🟢 dato | Mendoza | baja | Sitio Andino 2023 | — |
| INV-07 | Política (s, Q) inicial | (13500.0, 6500.0) | L | 🟠 supuesto | la estación | sin_dato | orquestador | — |
| INV-08 | Camión consolidado | True | — | 🟠 supuesto | Mendoza | media | Sitio Andino 2023 | — |
| INV-09 | Crisis de abastecimiento (S7) | (72.0, 84.0, 96.0) | h | 🟡 estimación | Mendoza | baja | Los Andes 31-jul-2023 | — |
| INV-11 | Ventana de la crisis de abastecimiento (S7): día de inicio y duración | (10, 3.5) | día · días | 🟠 supuesto | Mendoza | sin_dato | INV-09 (Los Andes 31-jul-2023: 3–4 días); el día de inicio es arbitrario | 3 días = (10, 3.0) · 4 días = (10, 4.0) |
| INV-12 | Nivel inicial de los tanques en la simulación con datos reales | 1.0 | % | 🟠 supuesto | la estación | sin_dato | pedido del grupo (6/10/2026): los tanques arrancan llenos | 75 % = 0.75 |
| INV-10 | Nivel inicial del tanque | 0.75 | % | 🟠 supuesto | la estación | sin_dato | orquestador (INV-07) | — |

## Red de rutas

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| RED-01 | Arco LUJAN–PAREDITAS | 114.8 | km | 🟢 dato | Mendoza | media | nota 06 §1.2 (RN 40; km derivado de los tramos) | 114 km = 114.0 |
| RED-02 | Arco PAREDITAS–SANRAFAEL | 107.0 | km | 🟢 dato | Mendoza | media | nota 06 §1.2 (RN 143) | — |
| RED-03 | Arco PAREDITAS–SOSNEADO | 176.0 | km | 🟢 dato | Mendoza | media | nota 06 §1.2 (RN 40) | — |
| RED-04 | Arco SOSNEADO–SANRAFAEL | 132.0 | km | 🟢 dato | Mendoza | media | nota 06 §1.2 (RN 144) | — |
| RED-05 | Arco ALVEAR–SANRAFAEL | 87.5 | km | 🟢 dato | Mendoza | media | nota 06 §1.2 (RN 143 este) | — |
| RED-06 | Arco SANRAFAEL–MONTECOMAN | 54.1 | km | 🟢 dato | Mendoza | media | nota 06 §1.2 (RN 146) | — |
| RED-07 | Arco MONTECOMAN–LAPAZ | 204.7 | km | 🟢 dato | Mendoza | media | nota 06 §1.2 (RP 153, no verificada) | — |
| RED-08 | Arco LAPAZ–LUJAN | 141.0 | km | 🟢 dato | Mendoza | media | nota 06 §1.2 (RN 7) | — |
| RED-09 | Arco DOCK–ALVEAR | 903.8 | km | 🟢 dato | Mendoza | media | nota 06 §1.3 (no verificada) | — |
| RED-10 | Arco DOCK–LUJAN | 1056.5 | km | 🟢 dato | Mendoza | media | nota 06 §1.3 (no verificada) | — |
| RED-11 | Velocidad del camión | 70.0 | km/h | 🟠 supuesto | Mendoza | sin_dato | orquestador (entre 80 km/h legales y 60 urbanos) | — |
| RED-12 | Escenario de cortes de ruta | aleatorio | — | 🟠 supuesto | Mendoza | sin_dato | orquestador (CASO §6.1; 3 cortes documentados en jul/ago-2026) | ninguno = ninguno · E1 = E1 · E2 = E2 · E3 = E3 · E4 = E4 |
| RED-13 | Probabilidad de que un viaje encuentre un corte (jun–ago) | 0.1 | prob. | 🟠 supuesto | Mendoza | sin_dato | orquestador (CASO §6.1: no hay estadística de cortes) | sin cortes = 0.0 · 30 % = 0.3 |
| RED-14 | Duración de un corte aleatorio | (3.0, 6.0, 24.0) | h | 🟠 supuesto | Mendoza | sin_dato | orquestador (E1 = 6 h; E2 = 24–48 h) | — |
| RED-15 | Cortes forzados E1–E4 | (('E1', 'RN 143 cerrada 6 h (17-ago-2026)', (('PAREDITAS', 'SANRAFAEL'),), (6.0, 6.0, 6.0), 0.0, None), ('E2', 'RN 143 + RN 40 + RN 144 cerradas 24… | — | 🟢 dato | Mendoza | media | Sitio Andino / Los Andes / MDZ (nota 06 §1.3); E3 y E4 son supuestos | — |
| RED-16 | Día de la corrida en que arranca un corte forzado | 10 | día | 🟠 supuesto | Mendoza | sin_dato | orquestador | — |
| RED-17 | Meses con cortes sorteados | (6, 7, 8) | meses | 🟡 estimación | Mendoza | baja | DATOS §6 (cortes RN-143/144 por nieve, invierno) | — |

## GNC y cortes de invierno

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| GNC-01 | Contrato de suministro | interrumpible | — | 🟠 supuesto | la estación | sin_dato | ONBOARDING '80 % de las estaciones' sin fuente; ENARGAS abr-2026 (verificado) | firme = firme |
| GNC-02 | Episodios de corte en invierno | 2 | episodios | 🟡 estimación | San Rafael | baja | DATOS §7 ('10–14 días en jun/jul') | 0 episodios = 0 · 4 episodios = 4 |
| GNC-03 | Forma del corte | total_24h | — | 🟢 dato | la estación | media | ENARGAS abr-2026; Sitio Andino 23/6/2022 | ventanas = ventana · parcial_50 = parcial_50 |
| GNC-04 | Migración a nafta durante el corte | 0.3 | % | 🟠 supuesto | la estación | sin_dato | DATOS: 'no hay migración documentada' → supuesto explícito | 0 % = 0.0 · 60 % = 0.6 |
| GNC-06 | Duración de cada episodio de corte | 6 | días | 🟡 estimación | San Rafael | baja | DATOS §7 ('10–14 días en jun/jul' ⇒ 2 episodios de 6 días) | 3 días = 3 · 10 días = 10 |
| GNC-07 | Forzar que los episodios caigan dentro del horizonte | False | — | 🟠 supuesto | la estación | sin_dato | orquestador (herramienta de análisis, no un dato) | no = False |
| GNC-08 | Cortes de GNC extra si se eligen 'más cortes en todo el invierno' | 2 | episodios | 🟠 supuesto | San Rafael | sin_dato | grupo (13/10/2026) sobre GNC-02: el Registro ya traía '4 episodios' como alternativa | 0 extra = 0 |
| GNC-09 | Probabilidad de invierno más frío que alarga cada corte | 0.3 | prob. | 🟠 supuesto | San Rafael | sin_dato | grupo (13/10/2026); no hay estadística de olas de frío por episodio | sin alargue = 0.0 |
| GNC-10 | Días que se alarga un corte en un invierno más frío | 4 | días | 🟠 supuesto | San Rafael | sin_dato | grupo (13/10/2026): con el alargue el corte llega a 10 días, la alternativa larga de GNC-06 | — |
| GNC-05 | Flujo máximo de la red de gas | sin datos (ventana/episodio aleatorio) | — | 🟠 supuesto | la estación | sin_dato | CASO §6.2 | — |

## Economía

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| ECO-01 | Margen por litro | 100.0 | $/L | ⚪ heredado | Argentina / otro | sin_dato | proyecto hipotético | prueba −50 % = 50.0 · prueba +50 % = 150.0 |
| ECO-02 | Margen por compra en minimarket | 2500.0 | $/compra | ⚪ heredado | Argentina / otro | sin_dato | proyecto hipotético | prueba −50 % = 1250.0 · prueba +50 % = 3750.0 |
| ECO-03 | Margen por m³ de GNC | 100.0 | $/m³ | ⚪ heredado | Argentina / otro | sin_dato | proyecto hipotético | prueba −50 % = 50.0 · prueba +50 % = 150.0 |
| ECO-04 | Sueldos (playero / cajero / encargado) | (1680000.0, 1800000.0, 1740000.0) | $/mes | 🟡 estimación | Argentina / otro | media | DATOS §4 (FECRA); la URL dice enero-2026 | básicos = (1545472.0, 1666391.0, 1600406.0) |
| ECO-04C | Sueldo del cajero (motor) | 1800000.0 | $/mes | 🟡 estimación | Argentina / otro | media | ECO-04 (cajero, con adicionales) | heredado = 900000.0 |
| ECO-05 | Inversión por cara/surtidor nuevo; operativo mensual | (18000000.0, 250000.0) | $ | ⚪ heredado | Argentina / otro | sin_dato | proyecto hipotético | — |
| ECO-06 | Flete del camión | (150000.0, 0.0) | $/viaje | ⚪ heredado | Argentina / otro | sin_dato | proyecto hipotético (fijo); $/km sin dato | prueba ×0,5 = 75000.0 · prueba ×10 = 1500000.0 |
| ECO-07 | Almacenamiento | 25.0 | $/litro-mes | ⚪ heredado | Argentina / otro | sin_dato | proyecto hipotético | prueba −50 % = 12.5 · prueba +50 % = 37.5 |
| ECO-08 | Precios (referencia, informativos) | (('super', 2141.0), ('premium', 2300.0), ('diesel_g2', 2116.0), ('diesel_g3', 2641.0), ('gnc', 699.0)) | $ | 🟢 dato | San Rafael | media | DATOS §7, sept-2026 (GNC oct-2025) | — |
| ECO-09 | Anualización | año = 3 × Σ de los 4 meses representativos | — | 🟠 supuesto | Argentina / otro | sin_dato | orquestador | — |
| ECO-10 | Cobertura de francos (personas por puesto cubierto 24 h) | 1.4 | × | 🟠 supuesto | Argentina / otro | sin_dato | 7 días de operación ÷ 5 días trabajados por persona | sin francos = 1.0 · 6 de 7 días = 1.1666666666666667 |
| ECO-11 | Puestos fijos por día que el motor no modela (encargado · tienda) | (2.0, 2.0) | puestos-turno | 🟡 estimación | Argentina / otro | baja | DATOS §4 (encargado 1 y tienda 1 en mañana y tarde) | — |

## Configuración del caso clásico

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| REC-01 | Surtidores del motor (configuración clásica) | 3 | surtidores | ⚪ heredado | San Rafael | sin_dato | proyecto hipotético (los 12 caras reales son SUR-01..04; el rediseño de grupos entra en Fase 2) | — |
| REC-02 | Cajas del motor (configuración clásica) | 1 | cajas | ⚪ heredado | San Rafael | sin_dato | proyecto hipotético (PER-02 da 1 caja por turno) | — |
| REC-03 | Caja exponencial | False | — | ⚪ heredado | San Rafael | sin_dato | proyecto hipotético | — |

## Calendario y corrida

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| CAL-01 | Fecha de inicio | (1, 1) | mes, día | 🟠 supuesto | la estación | sin_dato | orquestador | — |
| CAL-02 | Días simulados | 30 | días | 🟠 supuesto | la estación | sin_dato | orquestador (dias_y_fecha) | — |
| CAL-03 | Días de calentamiento | 2 | días | 🟠 supuesto | la estación | sin_dato | orquestador (B4) | — |
| CAL-04 | Día animado | 2 | día | 🟠 supuesto | la estación | sin_dato | orquestador | — |
| CAL-05 | Intervalo de la traza | 0.5 | min | 🟠 supuesto | la estación | sin_dato | orquestador | — |
| CAL-08 | Temporadas del menú inicial | (('Verano', (12, 3)), ('Otoño', (3, 3)), ('Invierno', (6, 3)), ('Primavera', (9, 3))) | mes de inicio · meses | 🟠 supuesto | la estación | sin_dato | estaciones meteorológicas del hemisferio sur (elección del grupo) | — |
| CAL-07 | Grabar la animación de todos los días | True | — | 🟠 supuesto | la estación | sin_dato | pedido del grupo (6/10/2026): se anima todo el período, un día cada 5 s | — |
| CAL-06 | Horizonte | mes | — | 🟠 supuesto | la estación | sin_dato | orquestador | — |

## Modelo

| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |
|---|---|---|---|---|---|---|---|---|
| MOD-02 | Simulación con datos reales: sin azar (determinista) | True | — | 🟠 supuesto | la estación | sin_dato | pedido del grupo (6/10/2026): con datos reales no se sortea nada | con azar = False |
| MOD-01 | Modelo de la estación (real vs. clásico) | True | — | 🟠 supuesto | la estación | sin_dato | orquestador (el clásico reproduce los dorados, §10.1) | clasico = False |

## Contradicciones entre fuentes: qué se eligió y por qué

Criterio único (nota 07): que mida lo mismo; oficial o primaria y vigente; más reciente; más específica de San Rafael/Mendoza; ante empate, la más conservadora.

| ID | Tema | Impacto | Valor elegido | Por qué | Descartadas (sensibilidad) |
|---|---|---|---|---|---|
| C1 | Horario de la playa | Medio | 24 h, todos los días. | Oficial: API de Shell (twenty_four_hour, 5/10/2026). | S10: cierre nocturno 22–06 (DATOS §5, sin fuente). |
| C2 | Demanda mensual | Alto | 270.000 L/mes (estimación). | Más específica: estimación regional, dentro del promedio nacional (270–380 mil) y del punto de equilibrio (315–400 mil). No hay fuente oficial de e… | 150.000 y 400.000 L/mes como ejes de sensibilidad. |
| C3 | Litros vs. autos | Crítico | Litros/mes es la variable de entrada; los clientes se derivan (÷ litros medios por cliente). | Misma cosa: no es una disputa de datos sino de unidades. | — (los documentos confundían litros/día con autos/día, error ×35–50). |
| C4 | Entrada al minimarket | Bajo-medio | 20 % de los clientes atendidos. | Primaria: es la única cifra con fuente declarada. | 15 % · 30 % · 45 %. |
| C5 | Personal | Alto | Playeros (noche · mañana · tarde) = 1 · 2 · 2; 1 caja; encargado y tienda sólo como costo. | Más específica: DATOS §4 es el único desglose por rol y turno. | Playeros 2·3·3 (ONBOARDING); autoservicio S9 (−1 por turno). |
| C6 | Mix diésel G2/G3 | Medio | 55 % G2 / 45 % G3 del diésel; se venden los dos. | Más reciente y con fuente: Surtidores.com.ar (ago-2026); la Secretaría de Energía confirma ambos productos. | 75/25 (ONBOARDING) y 100/0 (sólo G2). |
| C7 | Mezcla de producto | Medio | En litros: Súper 28,0 · V-Power 19,5 · G2 29,3 · G3 23,2 %; GNC = 3 % de los clientes. | Misma cosa: el 11 % de ENARGAS es el parque de autos a GNC, no los clientes de esta estación. | GNC 11 % (parque GNC ENARGAS); mezcla por flota. |
| C8 | GNC: 6 caras vs. ≈ 3 % de los clientes | Medio | La estación se modela como está (6 caras, 3 % de clientes GNC). | Misma cosa: las caras se observaron y el 3 % es la demanda; que los compresores queden poco usados es un resultado del modelo. | GNC 3 % / 11 % / 20 %. |
| C9 | GNC en invierno | Alto en invierno | Corte total por episodios (2 × 6 días, jun–ago), contrato interrumpible, 3 compresores. | Oficial (ENARGAS, abr-2026) para la forma del corte y más específica (Sitio Andino, San Rafael 2022) para la duración. | Contrato firme (sin cortes); ventanas horarias (17–01, 09–24); −50 % de capacidad; migración 0–60 %. |
| C10 | Estacionalidad | Medio | Neutra por mes + calendario de temporadas (verano, vacaciones de invierno de Mendoza, resto del invierno) editable. | Misma cosa: la ocupación hotelera no es venta de combustible; el calendario es un supuesto moderado (nota 08). | Leve ±6 %; proxy turístico (DATOS §6). |
| C11 | Tiempo de servicio | Medio | Nafta/diésel Triangular(2, 5, 8) min · GNC (5, 7, 12) · minimarket (2, 4, 10). | Empate → conservadora: ninguna es local ni más reciente; la media de 5 min no subestima la espera. | Nota 03: (2,4; 3,7; 5,0) para nafta y GNC 10–30 min (probablemente incluye la espera). |
| C12 | Litros por carga | Alto | Carga Triangular(0,20·T; 0,30·T; 1,00·T): media 0,5 × tanque. | Primaria: único anclaje empírico (nota 03, ≈ 30 % del tanque). | Preset alto (media 0,8·T) y bajo (0,3·T). |
| C13 | Tanques de vehículos | Bajo | Auto 47 L; camión 300 L. | Primaria: ficha del fabricante (Autocosmos) para el auto; el camión es un supuesto sin fuente mejor. | Auto 42–52 L; camión 120–600 L. |
| C14 | Servicios | Bajo | Shop (en la app, «Shell Shop»), baño, aire y agua. No se modela lavadero. | Oficial: lista de servicios de Shell. | DATOS §5 suma lavado/Agroservice. |
| C15 | Autoservicio | Medio | Servicio atendido por playeros. | Oficial: API de Shell (full_service, manned). | S9 autoservicio: −1 playero por turno. |
| C16 | Perfil horario | Medio | Tabla de 24 factores de DATOS §2 (picos 07–10 y 16–18). | Más específica: el perfil heredado es del proyecto hipotético. | Perfil heredado (picos 08 y 19 con factor 2,0). |
| C17 | Fin de semana / quincena | Bajo-medio | Fin de semana × 1,30, normalizado al mes. La quincena es un escenario aparte. | Empate → conservadora: valor central del rango de la única fuente (DATOS §2). | × 1,24 – × 1,50. |
| C18 | Salarios | Medio | Costo con adicionales: playero $1.680.000 · cajero $1.800.000 · encargado $1.740.000 por mes (enero-2026). | Oficial del sector (FECRA); el básico subestima lo que cuesta un empleado. | Básico sin adicionales. |
| C19 | Precios | Informativo | Súper $2.141 · Premium $2.300 · G2 $2.116 · G3 $2.641 · GNC $699/m³ (sept-2026). | Más reciente: los de la Secretaría de Energía son oficiales pero están congelados desde 2025 (no vigentes). | Nota 01 (Mendoza, 6/5/2026); precios de la propia estación en la Secretaría de Energía (2025). |
| C20 | Otros | Nulo | Informativos: ninguno entra al modelo (Mercuria, estaciones en San Rafael, tránsito RN 143, temperatura de julio). | No hay valor que elegir. | — |

## Lo que todavía no sabemos (a relevar en la estación)

1. **Demanda real:** litros por mes por producto y clientes por franja, un día hábil y uno de fin de semana.
2. **Dotación:** playeros, cajeros y encargado por turno; horario real de la playa y del shop; si hay autoservicio.
3. **Litros por carga y tiempo en la cara:** cronometrar 5–10 vehículos por producto.
4. **GNC:** contrato (firme o interrumpible), compresores, cortes de los últimos inviernos.
5. **Economía:** margen por litro y por compra, flete real por km y sueldos vigentes.
6. **Mix diésel G2/G3** y porcentaje de clientes que entran al shop.
7. **Estacionalidad real:** ventas mensuales de la Secretaría de Energía.

Las notas de investigación con las citas textuales y las URL están en `research_notes/`.
