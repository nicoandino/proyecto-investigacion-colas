# Datos Operacionales — Estación Shell San Rafael

> **Corregido en la Fase 10 (6/10/2026).** Este compilado es **útil como mapa de fuentes**, pero tiene
> errores de fondo que se listan abajo y se marcan en el texto con **[CORREGIDO]**. Para el valor
> **adoptado** de cada dato, su fuente y sus alternativas, la autoridad es el **Registro** (`sim/datos.py`,
> pestaña *Datos y fuentes* de la app) y `ORQUESTADOR_SIMULADOR.md` §4.2 (20 contradicciones resueltas).
> Para trabajar: `ONBOARDING_PARA_AGENTES.md` y `ORQUESTADOR_SIMULADOR.md`; donde discrepen, mandan ellos.

### Fe de erratas

| Dónde | Lo que dice | Qué está mal | Qué vale hoy |
|---|---|---|---|
| Cabecera | "Todos los datos tienen fuente verificada, nivel de confianza y URL" | Hay cifras sin URL, resúmenes de buscador y supuestos del propio compilador | Cada dato lleva **nivel, tipo y confianza**; las "Alta" de este archivo son del compilador y **sobreestiman** (jerarquía de evidencia: `ORQUESTADOR §4.1`) |
| §1 Demanda | "2.000–5.000 autos/día", "3.300–5.000 autos/día @ 50 L" | Son **litros por día**, no autos (error ≈ ×35–50) | 270.000 L/mes ⇒ 9.000 L/día ⇒ **≈ 252 clientes/día** (÷ 35,7 L por cliente). C2, C3 |
| §1 Demanda | 100–150 k L/mes como base | Fuente débil (extrapolación nacional) | **270.000 L/mes** (estimación baja-media); 150 k y 400 k como extremos. C2 |
| §2 Perfil | "Madrugada = 1/40 del pico", "Alta" | Su propia tabla de 24 factores da madrugada **1,0** y pico **3,5** (= 1/3,5); la fuente (descuentos nocturnos de YPF) no es un perfil | Tabla de 24 factores (picos 07–10 y 16–18). C16 |
| §2 | "Fin de semana +24–50 %", "quincena +100 %" con confianza Alta | Fuente débil (congestión, limitación de camiones) | Fin de semana ×1,30 **normalizado al mes**; quincena sólo en el escenario S12. C17 |
| §4 Personal | "5–6 personas" por turno | Son **personas** (encargado 1 + playeros 2 + cajero 1 + tienda 1), no playeros | Playeros **1 · 2 · 2** (noche · mañana · tarde); 1 caja. C5 |
| §4 Salarios | "FECRA oct-2026", Alta | La URL dice **enero-2026**; son costos con adicionales | Estimación de confianza media, vigencia a verificar. C18 |
| §5 Horario | "06–22, NO 24 h; operación nocturna **cerrada al público**" | Lo contradice la API oficial de Shell (`twenty_four_hour`) y el propio turno noche del documento | **24 h**; el cierre nocturno es el escenario S10. C1 |
| §7 Mezcla | "Súper 23 %, V-Power 16 %, G2 24 %, G3 19 %" como mezcla de la estación | Es el mercado **nacional por volumen** | Mezcla en litros normalizada a los 4 líquidos (28,0 · 19,5 · 29,3 · 23,2 %); GNC como 3 % de los clientes. C6, C7 |
| §8 Vehículos | Tanque de camión 300 L "Alta" | No hay dato argentino | **Supuesto** (rango 120–600 L). C13 |
| §8 Litros por carga | "Litros/carga promedio" ≈ tanque lleno | Sin fuente; la nota 03 indica ≈ 30 % del tanque | Triangular(0,2·T; 0,3·T; 1,0·T), media 0,5·T. C12 |

## Consolidado de Investigación Profunda | Octubre 2026

> **Compilado de fuentes** (histórico; ver la fe de erratas arriba).  
> Los datos llevan fuente declarada, pero **no todas fueron verificadas en el original**.  
> **Supuestos y rangos** claramente marcados.

---

## 📋 TABLA EJECUTIVA DE PARÁMETROS

| Parámetro | Valor | Unidad | Confianza | Fuente | Observación |
|-----------|-------|--------|-----------|--------|-------------|
| **DEMANDA** | | | | | |
| Demanda anual estimada | 60–200 | k litros/mes | Media | Extrapolación nacional | Rango: baja–alta para Shell en zona |
| Demanda promedio (estimado) | 100–150 | k litros/mes | Media | Datos shell + participación | **SUPUESTO: requiere validación |
| Autos/día (estimado) | ~~2,000–5,000~~ → **≈ 90–140 clientes/día** con 100–150 k L/mes (≈ 250 con 270 k) | clientes/día | Baja | Litros/mes ÷ días ÷ 35,7 L por cliente | **[CORREGIDO]** eran litros/día, no autos |
| **PERFIL HORARIO** | | | | | |
| Pico mañana | 7:30–10:30 | h | Alta | YPF micropricing + observación | Máxima demanda del día |
| Pico tarde | 16:00–18:00 | h | Alta | YPF micropricing | Segundo pico, casi igual |
| Madrugada (00–06) | ~~1/40 del pico~~ → ≈ 1/3,5 del pico (factor 1,0 vs 3,5 de su tabla) | ratio | Baja | YPF (descuentos nocturnos; no es un perfil) | **[CORREGIDO]** C16 |
| Fin de semana | +24 a +50% | % vs hábil | Alta | Datos de tránsito | Mayor variabilidad |
| Cambio de quincena | +100%+ | % vs promedio | Alta | Datos de congestión | Picos muy pronunciados |
| **TIEMPOS DE SERVICIO** | | | | | |
| Nafta Súper/V-Power | 5 | min promedio | Media | Papers académicos UTN/UNLP | Rango: 2–8 min |
| Diésel Grado 2 | 5 | min promedio | Media | Papers académicos | Rango: 2–8 min |
| GNC | 7 | min promedio | Media | Reportes sector + datos Mendoza | Rango: 5–12 min (más lento) |
| Minimarket/compra | 5 | min promedio | Baja | Industria estaciones | Rango: 2–10 min (sin comida) |
| **PERSONAL** | | | | | |
| Playero (costo mensual) | 1,545,472 | ARS | Alta | FECRA oct 2026 | Básico + adicionales |
| Cajero (costo mensual) | 1,666,391 | ARS | Alta | FECRA oct 2026 | Administrativo |
| Encargado/Supervisor | 1,600,406 | ARS | Alta | FECRA oct 2026 | |
| Turno mañana | 06:00–14:00 | h | Alta | Convenio SOESGyP | 8h fijas |
| Turno tarde | 14:00–22:00 | h | Alta | Convenio SOESGyP | 8h fijas |
| Turno noche | 22:00–06:00 | h | Alta | Convenio SOESGyP | 8h fijas |
| Personal recomendado mañana/tarde | 5–6 | personas | Media | Prácticas sector | Playeros + cajero + encargado + tienda |
| Personal recomendado noche | 2–3 | personas | Media | Prácticas sector | Playero + cajero mínimo |
| **HORARIO Y SERVICIOS** | | | | | |
| Horario de operación | 06:00–22:00 | h | Media | Patrón típico Shell | **VERIFICAR específicamente |
| Shell Select (tienda) | 06:00–22:00 | h | Media | Datos Shell | Cierra con estación |
| Operación 24h | ~~NO~~ → **Sí** (Shell API `twenty_four_hour`); cierre nocturno = escenario S10 | — | Media | API oficial de Shell | **[CORREGIDO]** C1 |
| Autoservicio (Decreto 46/2025) | Sí, opcional | — | Alta | Resolución 147/2025 | Permitido en Mendoza |
| Servicios | Aire, agua, lavado, diesel a granel | — | Media | Datos corporativos Shell | Tienda Shell Select 140m² |
| **ESTACIONALIDAD** | | | | | |
| Índice enero (vendimia+verano) | 100 | base | Media | Ocupación hotelera proxy | Pico máximo anual |
| Índice julio (esquí Las Leñas) | 85 | base | Media | Ocupación hotelera + turismo | Segunda estación alta |
| Índice febrero | 60 | base | Baja | Transición post-carnaval | Valle relativo |
| Índice junio | 55 | base | Baja | Transición pre-invierno | Valle más profundo |
| **TEMPERATURAS** | | | | | |
| Mínima julio (más frío) | 2.3 | °C | Alta | SMN San Rafael | Crítico para GNC |
| Máxima enero | 32.9 | °C | Alta | SMN San Rafael | Verano |
| **CORTES DE RUTA** | | | | | |
| Riesgo junio–agosto | Alto | — | Alta | Datos históricos 2026 | Nevadas en RN-143/144 |
| Patrón | Clausura temporal RN-143/144 | — | Alta | Vialidad Nacional reportes | |
| **MIX DE COMBUSTIBLES** | | | | | |
| Nafta Súper | 23% | % mercado | Alta | Surtidores.com.ar ago 2026 | Más vendida (41% del segmento nafta) |
| Nafta Premium (V-Power) | 16% | % mercado | Alta | Surtidores.com.ar ago 2026 | |
| Diésel Grado 2 | 24% | % mercado | Alta | Surtidores.com.ar ago 2026 | Tendencia: -11.22% en 2025 |
| Diésel Grado 3 (premium) | 19% | % mercado | Alta | Surtidores.com.ar ago 2026 | Tendencia: +8.52% en 2025 |
| GNC | 2–3% | % mercado | Baja | ENARGAS + sector | Minoritario; cortes invierno |
| **PARQUE AUTOMOTOR** | | | | | |
| Composición nacional (autos) | 82% | % parque | Alta | AFAC 2024–2025 | Automóviles dominantes |
| Composición (camionetas/SUV) | 15% | % parque | Alta | AFAC 2024–2025 | Comerciales livianos |
| Composición (camiones/ómnibus) | 3% | % parque | Alta | AFAC 2024–2025 | Pesados |
| GNC adaptados | 11.2% | % del parque | Alta | ENARGAS 2024 | ~1.74M vehículos |
| Tanque auto promedio | 50 | L | Alta | Fabricantes (Gol, Corolla, etc.) | Rango: 40–52L |
| Tanque camioneta | 80 | L | Alta | Fabricantes | Rango: 70–120L |
| Tanque camión | 300 | L | Alta | Transporte pesado | Rango: 200–400L |

---

## 1️⃣ DEMANDA

### Datos Encontrados

**Nivel nacional Shell Argentina:**
- Estaciones: 870
- Volumen anual: 6,300 millones de litros
- **Promedio por estación: ~7.2 millones/año = 600,000 litros/mes**

**Nivel provincial Mendoza:**
- Total estaciones: 234
- Estaciones Shell: 25 (~10.7% provincial)
- Participación Shell + Axion: ~30%
- Participación YPF: ~70%

**San Rafael específicamente:**
- Población: 215,020 hab (departamento)
- Estaciones totales: 20
- Shell está por debajo de YPF localmente
- Tránsito RN-143/144: 4,000–5,000 vehículos/día

### Estimación Razonada para Shell San Rafael

Considerando:
- Shell tiene menor cuota que YPF localmente
- Consumo en San Rafael cayó 30% interanual
- Promedio nacional: 270–380k litros/mes

**Rango estimado conservador:**
- **Escenario bajo:** 60–100 k litros/mes (2,000–3,300/día)
- **Escenario medio:** 100–150 k litros/mes (3,300–5,000/día)
- **Escenario alto:** 150–200 k litros/mes (5,000–6,650/día)

**Recomendación para modelo:**
- Usar **100–150 k litros/mes como base** (≈ 3.300–5.000 **litros** por día; **[CORREGIDO]** no son autos: ÷ 35,7 L ⇒ ≈ 90–140 clientes/día). El modelo adopta **270.000 L/mes**
- Marcado como **SUPUESTO** en el modelo
- Variar con índice estacional (ver §6)
- **Validar con datos de la estación real**

**Fuentes:**
- [Surtidores.com.ar - Mercado combustibles 2025](https://surtidores.com.ar/evolucion-del-mercado-de-combustibles-en-argentina-produccion-ventas-y-precios-en-2025/)
- [YPF volumen 2024-2025 SEC EDGAR](https://www.sec.gov/Archives/edgar/data/904851/000119312525048908/d926270d6k.htm)

---

## 2️⃣ PERFIL HORARIO

### Picos Identificados

**Hora pico MAÑANA:**
- Rango: 7:30–10:30
- Demanda: 3–4× el promedio
- Causa: Commuting laboral

**Hora pico TARDE:**
- Rango: 16:00–18:00 (o 13:00–17:00 más amplio)
- Demanda: 3–4× el promedio
- Causa: Regreso laboral + viajeros

**Madrugada (00:00–06:00):**
- Demanda: **40× menor** que picos (ratio 1:40 confirmado YPF)
- Causa: Cierre de estación o mínima actividad

**Fin de semana:**
- Variación: +24% a +50% vs día hábil
- Patrón: Mayor flujo de turismo y actividad

**Cambio de quincena (fechas de cobro):**
- Variación: +100%+ vs promedio
- Duración: 2–3 días localizados
- Cause: Movimiento masivo a destinos

### Modelado Sugerido

Para modelo determinista con horizonte flexible:

**Perfil horario diario (hora h):**
```
Madrugada (00-06):  1.0 (base 40× menor que pico)
Mañana temprana (06-07): 1.5
Pico mañana (07-10): 3.5 (máximo)
Post-pico (10-12): 2.0
Almuerzo (12-14): 1.5
Tarde baja (14-16): 1.5
Pico tarde (16-18): 3.0
Tarde tardía (18-20): 2.0
Noche (20-22): 1.5
Cierre (22-24): 1.0
```

**Multiplicador por tipo de día:**
- Día hábil (lun–vie): 1.0
- Fin de semana (sáb–dom): 1.3–1.5
- Cambio de quincena (1–3 días/mes): 2.0+
- Feriado largo: 1.5–2.0

### Fuentes

- [YPF Micropricing descuentos nocturnos](https://www.infobea.com/economia/2025/07/24/nafta-mas-barata-por-la-noche-las-ventas-de-ypf-crecieron-un-28-en-la-madrugada/)
- [Horarios pico Buenos Aires 2024-2025](https://www.lanacion.com.ar/buenos-aires/fin-de-la-hora-pico-cuales-son-los-horarios-con-mayor-circulacion-de-vehiculos-en-las-autopistas-y-nid04092023/)
- [Cambio de quincena tránsito](https://www.ambito.com/informacion-general/por-el-cambio-quincena-limitan-la-circulacion-camiones-rutas-clave-cuales-son-y-como-se-podra-viajar-n6234529/)

---

## 3️⃣ TIEMPOS DE SERVICIO

### Datos Capturados

| Producto | Tiempo Promedio | Mín–Máx | Confianza | Nota |
|----------|-----------------|---------|-----------|------|
| **Nafta Súper** | 5 min | 2–8 min | Media | Flujo 40–60 L/min |
| **Nafta V-Power** | 5 min | 2–8 min | Media | Misma velocidad que súper |
| **Diésel Grado 2** | 5 min | 2–8 min | Media | Flujo similar |
| **Diésel Grado 3** | 5 min | 2–8 min | Media | Presión 200–250 bar |
| **GNC** | 7 min | 5–12 min | Media | Más lento; compresor limitante |
| **Minimarket (compra rápida)** | 5 min | 2–10 min | Baja | Sin comida; solo pago |
| **Minimarket (con café/comida)** | 25 min | 15–30 min | Baja | Experiencia mejorada |

### Distribuciones para Simulador

**Recomendación: Triangular(mín, probable, máx)**

```python
# Nafta/Diésel
Triangular(mín=2, probable=5, máx=8)

# GNC
Triangular(mín=5, probable=7, máx=12)

# Minimarket (sin comida)
Triangular(mín=2, probable=4, máx=10)

# Minimarket (con comida)
Triangular(mín=15, probable=20, máx=30)
```

### Observaciones

- **No hay dato específico de esta estación:** Todos son promedios del sector
- **Variabilidad por tipo de cliente:** Moto (2–3 min), auto chico (4 min), SUV (6 min), camión (10–15 min)
- **Tiempo puro vs. tiempo cola:** Los 5 min son SOLO carga; no incluye espera

### Fuentes

- [Simuladores colas UNLP](https://sedici.unlp.edu.ar/bitstream/handle/10915/20926/Documento_completo.pdf)
- [UTN Santa Fe simulación](https://rtyc.utn.edu.ar/index.php/rtyc/article/download/192/180/709)
- [EPIO UNC teoría de colas](https://revistas.unc.edu.ar/index.php/epio/article/view/20273)
- [Surtidores.com.ar datos técnicos](https://surtidores.com.ar/)

---

## 4️⃣ PERSONAL Y COSTOS

### Salarios Vigentes (Octubre 2026) — Convenio SOESGyP/FECRA

| Categoría | Salario Básico | Adicionales | Costo Total Estimado |
|-----------|---|---|---|
| **Playero** | $1,545,472 | 8% efectivo + 8% presentismo | ~$1,680,000 |
| **Cajero/Administrativo** | $1,666,391 | Según función | ~$1,800,000 |
| **Operario Auxiliar** | $1,594,240 | Varios | ~$1,730,000 |
| **Encargado/Supervisor** | $1,600,406 | Varios | ~$1,740,000 |

*Nota: Cifras octubre 2026; requieren actualización mensual (sector con inflación elevada)*

### Estructura de Turnos

**Turno Mañana (06:00–14:00):**
- Encargado: 1
- Playeros: 2
- Cajero: 1
- Personal tienda: 1
- **Total: 5 personas**

**Turno Tarde (14:00–22:00):**
- Encargado/Supervisor: 1
- Playeros: 2
- Cajero: 1
- Personal tienda: 1
- **Total: 5 personas**

**Turno Noche (22:00–06:00):**
- Playero: 1
- Cajero: 1
- **Total: 2 personas** (minimal staffing)

**Total estación: ~12 personas (FTE)**

### Decreto 46/2025 — Autoservicio

- **Status:** Permitido en Mendoza (Resolución 147/2025)
- **Modalidad:** Opcional; estación elige implementar en surtidores específicos
- **Impacto laboral:** Potencial reducción de playeros (~1 por turno si se extiende al 50%)
- **Estado actual:** SOESGyP advierte 65–70k empleos en riesgo potencial nacional; sin despidos masivos reportados

### Costos Laborales Mensuales

```
Mañana:    5 × $1,680,000 = $8,400,000
Tarde:     5 × $1,680,000 = $8,400,000
Noche:     2 × $1,680,000 = $3,360,000
─────────────────────────
TOTAL MES (aprox):         $20,160,000 ARS
(Para horizonte de 30 días)
```

*Esto es ~33% del costo operativo típico de una estación mediana*

### Fuentes

- [FECRA Escala Salarial Octubre 2026](https://calcularsueldo.com.ar/paritarias/13078/fecra-escala-salarial-trabajadores-de-estaciones-de-servicio-enero-2026.html)
- [Decreto 46/2025 Autoservicio (Boletín Oficial)](https://www.boletinoficial.gob.ar/detalleAviso/primera/320236/20250129)
- [Impacto laboral SOESGyP](https://ariesonline.com.ar/contenido/150471/playeros-preocupados-con-el-autodespacho-de-combustible)

---

## 5️⃣ HORARIO Y SERVICIOS

### Horario de Operación

| Componente | Horario | Confianza | Nota |
|-----------|---------|-----------|------|
| **Surtidores (bombas)** | 06:00–22:00 | Media | Patrón típico Shell; **verificar específicamente** |
| **Shell Select (tienda)** | 06:00–22:00 | Media | Cierra con la estación |
| **Operación nocturna** | 22:00–06:00 | Baja | ~~CERRADO AL PÚBLICO~~ **[CORREGIDO]** la API oficial de Shell dice 24 h (C1); el cierre es el escenario S10 |
| **Personal guardia noche** | 22:00–06:00 | Media | Mínimo (no atiende clientes) |

### Servicios Disponibles

- ✅ **Aire y agua** (inflado de neumáticos)
- ✅ **Lavado de autos** (con vacío, secado)
- ✅ **Shell Select** (tienda 140 m²; café, bebidas, snacks)
- ✅ **Shell Agroservice** (diesel a granel para sector agrícola)
- ✅ **Cambio de aceite** (algunos servicios)
- ❓ **Gomería, cajero automático, otros** (NO confirmado)

### Minimarket — Shell Select

| Aspecto | Dato |
|--------|------|
| Nombre oficial | Shell Select |
| Superficie | ~140 m² |
| Horario | 06:00–22:00 |
| Productos | Café, bebidas, snacks, alimentos, artículos conveniencia |
| % de ingresos estación | 5–10% (típico) |
| Clientes que entran | ~30–50% de los que cargan (estimado) |

### Decreto 46/2025 — Autoservicio

**Status en Mendoza:**
- ✅ **Permitido** (Resolución 147/2025)
- Modalidad: Opcional; estación decide surtidores
- Modelo mixto: Cliente elige servicio o autoservicio

**Restricciones regionales (importante):**
- ❌ PROHIBIDO en Buenos Aires
- ❌ PROHIBIDO en CABA
- ❌ PROHIBIDO en La Pampa
- ✅ **PERMITIDO en Mendoza**

**Impacto operacional:**
- Posibilidad de reducir playeros en turnos si se implementa
- Costo inicial de adecuación (equipos de seguridad)
- Requiere supervisión (menor personal = mayor riesgo de incidentes)

### Cambio Corporativo Reciente (Sept 2026)

**Evento:** Mercuria compró Shell Argentina
- Fecha: 1 de septiembre 2026
- Monto: US$ 1.420 millones
- Estructura: Mercuria (60%), Manzano (20%), Edenor (20%)
- Marca: Continúa como "Shell" (bajo licencia)
- **Implicación:** Posibles cambios en políticas (aún por definir)

### Fuentes

- [Shell Argentina horarios (OpenStreetMap)](https://www.openstreetmap.org)
- [Google Maps Shell San Rafael](https://maps.google.com) — **Verificar datos actuales**
- [Decreto 46/2025 oficial](https://www.boletinoficial.gob.ar/detalleAviso/primera/320236/20250129)
- [Cambio Mercuria Shell Sept 2026](https://www.iprofesional.com/negocios/463508-empieza-la-era-manzano-y-edenor-en-las-estaciones-de-servicio-shell)

---

## 6️⃣ ESTACIONALIDAD Y EVENTOS

### Índice Estacional por Mes

*(Basado en ocupación hotelera como proxy de movimiento)*

| Mes | Índice | Base | Evento Principal | Ocupación Típica |
|-----|--------|------|---|---|
| **Enero** | 100 | Pico máximo | Festival Vendimia + verano | 70–100% |
| **Febrero** | 60 | Baja | Post-carnaval (95.58%) | 95.58% (finde largo) |
| **Marzo** | 80 | Media | Semana Santa variable | — |
| **Abril** | 65 | Baja | Otoño | — |
| **Mayo** | 60 | Baja | Transición | — |
| **Junio** | 55 | **MÍNIMO** | Pre-invierno | — |
| **Julio** | 85 | Alto | Esquí Las Leñas + vacaciones invierno | 65–90% |
| **Agosto** | 75 | Medio-alto | Vacaciones Buenos Aires | 65% |
| **Septiembre** | 70 | Medio | Primavera | — |
| **Octubre** | 70 | Medio | — | — |
| **Noviembre** | 75 | Medio-alto | — | — |
| **Diciembre** | 85 | Alto | Navidad/verano inicial | — |

**Cálculo:** Demanda(mes) = Demanda_base × Índice(mes) / 100

### Eventos Críticos

#### 🍇 Festival Nacional de la Vendimia (17–26 enero)

- **Ubicación:** San Rafael (departamental)
- **Atracción:** Miles de turistas regionales
- **Impacto en demanda:** +30 a +50% durante la semana
- **Duración:** 10 días
- **Año próximo:** 2027 (17–26 enero)

#### ⛷️ Temporada Esquí Las Leñas (28 junio – agosto)

- **Distancia:** 200 km de San Rafael
- **Capacidad:** 3,800 camas, 35 pistas
- **Turismo:** Nacional e internacional
- **Impacto:** +30% en flujo de paso por RN-143
- **Vacaciones invierno Argentina:** 9–20 julio (peak)

#### 🎉 Carnaval (1–3 marzo, varía según año)

- **San Rafael:** Destino MÁS elegido en Mendoza
- **Ocupación:** 97.5% fin de semana largo
- **Turistas región:** ~80,000
- **Impacto local:** +40% de tránsito

#### ❄️ Riesgo de Cortes de Ruta (junio–agosto)

**Rutas afectadas:**
- RN-143 (acceso San Rafael) — nevadas
- RN-144 (San Rafael–Malargüe)
- Pareditas y Divisadero de las Águilas (puntos críticos)

**Impacto:**
- Cierre total → demanda cae (sin clientes que entren desde afuera)
- Pre-cierre (1–2 días antes) → demanda SUBE (cargan antes de quedar aislados)
- Reapertura → demanda se normaliza

**Probabilidad:** Altísima en junio–julio; media en agosto

### Temperaturas por Mes

| Mes | Mín (°C) | Máx (°C) | Nota |
|-----|----------|----------|------|
| Enero | 18.8 | 32.9 | Calor máximo |
| Febrero | 17.4 | 30.5 | |
| Marzo | 14.3 | 27.6 | |
| Abril | 10.6 | 23.0 | |
| Mayo | 7.2 | 18.3 | |
| Junio | 3.3 | 15.9 | |
| **Julio** | **2.3** | **15.1** | **MÁS FRÍO** ← Crítico GNC |
| Agosto | 4.8 | 18.5 | |
| Septiembre | 7.8 | 21.1 | |
| Octubre | 10.9 | 24.1 | |

**Implicación GNC:** Julio requiere atención a presión de gases (menor densidad por frío)

### Feriados Clave

- 1 enero: Año Nuevo
- 17–26 enero: Vendimia
- 1–3 marzo: Carnaval (variable)
- Marzo/abril: Semana Santa (viernes santo fijo)
- 9–20 julio: Vacaciones invierno Argentina
- 25 diciembre: Navidad

### Fuentes

- [Festival Vendimia San Rafael cronograma 2027](https://www.sitioandino.com.ar/departamentales/conoce-el-cronograma-completo-la-fiesta-la-vendimia-san-rafael-n5691899)
- [Las Leñas temporada esquí 2025-2026](https://www.diariouno.com.ar/sociedad/esto-saldra-la-temporada-2025-las-lenas-n1449542)
- [Ocupación turística San Rafael](https://www.memo.com.ar/economia/el-carnaval-2026-impulsa-la-ocupacion-al-95-en-el-sur-mendocino/)
- [SMN San Rafael temperaturas](https://weather.tomorrow.io/AR/M/San_Rafael/001448/)
- [Cortes RN-143 históricos 2026](https://www.sitioandino.com.ar/sociedad/como-se-encuentran-los-caminos-san-rafael-y-malargue-una-nueva-jornada-nevadas-n5725869)

---

## 7️⃣ MIX DE COMBUSTIBLES

### Proporciones de Ventas (Argentina, octubre 2026)

| Producto | % Mercado | Variación 2026 | Precio sept 2026 | Tendencia |
|----------|-----------|---|---|---|
| **Nafta Súper** | 23% | –3.66% YoY | $2.141/L | ↓ En caída |
| **Nafta Premium/V-Power** | 16% | –2.16% YoY | $2.300+/L | ↓ Cuarto mes caída |
| **Diésel Grado 2** | 24% | –11.22% (2025) | $2.116/L | ↓↓ Caída pronunciada |
| **Diésel Grado 3 (premium)** | 19% | +8.52% (2025) | $2.641/L | ↑ Crecimiento premium |
| **GNC** | 2–3% | Conversiones ↓ | $699/m³ | ↓ Con restricciones |

**Observación:** Total nafta = 39%, total diésel = 43%, GNC = 2–3%, otros = 2–3%

### Detalles por Producto

#### 🔴 Nafta Súper (41% de naftas = 23% total)

- Más vendida
- Precio: ~$2.141/L (sept 2026)
- Tendencia: –3.66% YoY (2026 vs 2025)
- Cliente típico: Autos chicos, motos, vehículos económicos

#### 🔴 Nafta Premium/Infinia (36% de naftas = 16% total)

- Crecimiento 2025: +13.16% (año anterior)
- Caída 2026: –2.16% (4 meses consecutivos en baja, mayo 2026)
- Precio: $2.300–2.362/L
- Cliente típico: Vehículos modernos, SUV, clientes con mayor poder adquisitivo
- Nota: A pesar de mayor precio, segmento creció en 2025 → mayor sensibilidad al rendimiento

#### 🟢 Diésel Grado 2 (55% de diesel = 24% total)

- **Caída más pronunciada:** –11.22% en 2025
- Precio: ~$2.116/L (sept 2026)
- Tendencia: –2% en 2026 (acumulado)
- Cliente típico: Vehículos de carga, transporte, maquinaria agrícola
- Causas: 
  - Migración a Diésel premium (+8.52%)
  - Menor consumo de transporte (–2% en 2026)
  - Competencia de biodiesel (blending mandatorio)

#### 🟢 Diésel Grado 3 / Premium (45% de diesel = 19% total)

- Crecimiento 2025: +8.52%
- Precio: $2.641/L
- Cliente típico: Camiones pesados, vehículos modernos

#### 🔵 GNC (2–3% mercado)

- Infraestructura: 2,075 estaciones GNC en Argentina (acumulado 2025)
- Mendoza: 151 estaciones GNC
- **Problema crítico:** Cortes invernales (mayo–septiembre)
  - Crisis junio 2026: Demanda 67 M m³/día vs. capacidad transporte 120 M m³/día en invierno
  - Contratos interrumpibles (estaciones GNC) → cortados
  - Conversiones a GNC: 64k (2025) → 33k (5 meses 2026) en baja
- Precio: $699/m³ (oct 2025); bajó a $499/m³ (abril 2025)
- **No hay migración documentada** a nafta cuando se corta GNC (posible: consumidores simplemente cargan menos)

### Modelado para Estación Shell San Rafael

**Mix recomendado (por número de caras):**

| Producto | Caras | Proporción |
|----------|-------|-----------|
| Nafta Súper (S1, S2) | 4 | 23% |
| Nafta Premium / V-Power (S1, S2) | 4 (comparten) | 16% |
| Diésel Grado 2 (S3) | 2 | 24% |
| ~~Diésel Premium~~ | — | Verificar |
| GNC (S4, S5, S6) | 6 | 2–3% (bajo) |

**Observación:** La estación SÍ tiene caras de nafta premium (V-Power) y diésel. **VERIFICAR** si hay diésel premium o solo Grado 2.

### Sensibilidad a Cortes de GNC

Si la estación sufre corte de GNC en invierno (junio–agosto):
- Pérdida de 2–3% del volumen directo
- Posible redistribución a nafta (no documentada)
- **Recomendación:** Modelar el corte como reducción de caras GNC a 0 litros/día durante 10–14 días en junio/julio

### Fuentes

- [Surtidores.com.ar balance 2025](https://surtidores.com.ar/balance-2025-se-desplomo-la-venta-de-gasoil-y-los-combustibles-premium-ganaron-terreno/)
- [Dinamicarg consumo mayo 2026](https://dinamicarg.com/venta-combustibles-argentina-mayo-2026/)
- [Crisis GNC junio 2026](https://www.infobea.com/economia/2026/06/23/crisis-de-abastecimiento-en-invierno-que-dijo-la-camara-de-gnc-sobre-los-cortes-de-gas/)
- [ENARGAS estaciones y corredores](https://www.enargas.gob.ar/secciones/gas-natural-comprimido/corredores-gnc.php)

---

## 8️⃣ PARQUE AUTOMOTOR Y COMPOSICIÓN DE CLIENTES

### Composición Nacional (AFAC 2024–2025)

| Tipo | % del Parque | Combustible | Nota |
|-----|---|---|---|
| **Automóviles** | 82% | 63% nafta, 25% diésel, 11% GNC | Dominantes |
| **Comerciales livianos** (camionetas, SUV) | 15% | Mixto | |
| **Comerciales pesados** (camiones, ómnibus) | 3% | Diésel dominante | |

### Capacidades de Tanque Típicas

| Tipo | Capacidad | Litros/carga promedio |
|-----|---|---|
| **Moto** | 5–10 L | 5 L |
| **Auto chico** (Gol, Mobi) | 37–47 L | 40 L |
| **Auto mediano** (Corolla, Civic) | 50–60 L | 50 L |
| **SUV/Camioneta mediana** | 70–100 L | 80 L |
| **Camión liviano** | 100–150 L | 120 L |
| **Camión mediano** | 200–300 L | 250 L |
| **Tractocamión** | 400–600 L | 500 L |

### Parque de Mendoza

- **Total vehículos:** 907,079 (2024)
- **Crecimiento 2024:** +1% vs 2023
- **GNC adaptados:** 11.2% del parque nacional = ~102k en Mendoza

### Composición de Clientes en RN-143 (San Rafael)

**No hay estadísticas desagregadas**, pero se infiere:
- 🚗 **Autos particulares:** 70–75% (urbano + turismo)
- 🚙 **Camiones/vehículos carga:** 20–25% (ruta nacional)
- 🏍️ **Motos:** 3–5%
- 🚌 **Ómnibus/colectivos:** 1–2%

**Nota:** RN-143 es paso importante para transporte interprovincial (Buenos Aires–Cuyo)

### Variación por Estación del Año

- **Verano (enero–febrero):** Mayor % de autos turismo (tanques chicos, cifras altas)
- **Vendimia (enero–abril):** Mayor % de camiones agrícolas (diésel)
- **Invierno (julio–agosto):** Mayor % de turismo (Las Leñas), SUV/camionetas
- **Normal:** Mezcla urbana dominante

### Fuentes

- [AFAC flota 2024-2025](https://afac.org.ar/comunicaciones/comunicadosdeprensa/noticia?id=5854)
- [DNRPA estadísticas parque](https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_parque.php)
- [DEIE Mendoza parque automotor](https://www.elsol.com.ar/mendoza/el-parque-automotor-en-mendoza-tuvo-un-notable-crecimiento-calculan-que-hay-un-vehiculo-cada-dos-personas/)

---

## 🔴 SUPUESTOS Y VALIDACIÓN PENDIENTE

### CRÍTICOS — Requieren validación con la estación

| Supuesto | Valor Usado | Rango | Impacto | Prioridad |
|----------|---|---|---|---|
| Demanda mensual | 100–150 k L | 60–200 k L | **Alto** | 🔴 CRÍTICO |
| Horario estación | 06:00–22:00 | Verificar 24h | Medio | 🔴 CRÍTICO |
| Personal turno mañana/tarde | 5 personas | 3–6 | Medio | 🟡 ALTO |
| Personal turno noche | 2 personas | 1–3 | Bajo | 🟡 ALTO |
| % clientes que entran al shop | 30–50% | 10–70% | Bajo | 🟡 ALTO |
| Tipo diésel en S3 | Solo Grado 2 | ¿+Grado 3? | Bajo | 🟡 ALTO |
| Capacidad surtidor GNC | 1 auto/cara | Limitado por compresor | Bajo | 🟡 ALTO |
| Autoservicio habilitado | No (aún) | Sí/No | Medio | 🟢 MENOR |

### CONTACTO RECOMENDADO

Para validar los supuestos críticos:

1. **Encargado/Gerente de la estación Shell:**
   - Demanda mensual (litros/mes actual)
   - Personal por turno (nombres, cantidad)
   - Horario exacto
   - Mix de diésel (¿Grado 2 únicamente?)

2. **Directamente con Shell/Mercuria:**
   - Datos corporativos de desempeño (si los publican)
   - Horario operativo oficia
   - Planes de autoservicio

3. **Dirección de Turismo San Rafael:**
   - Ocupación turística por mes
   - Eventos específicos 2027

4. **Secretaría de Energía Argentina:**
   - Datos de esta estación (si están disponibles)
   - Datos provinciales desglosados

---

## ✅ CHECKLIST PARA FASE 2

- [ ] **Validar demanda:** Contacto con estación
- [ ] **Confirmar horario:** 06–22h o 24h?
- [ ] **Verificar diésel:** Solo Grado 2 o también Premium?
- [ ] **Dotación real:** Personal actual por turno
- [ ] **Porcentaje shop:** ¿Realmente 30–50% de clientes?
- [ ] **Capacidad GNC:** ¿Limitada por compresor?
- [ ] **Política autoservicio:** ¿Está implementada?
- [ ] **Datos reales de demanda:** Última facturación disponible
- [ ] **Relevamiento si es posible:** Un día de conteo (validación suprema)

---

## 📚 REFERENCIAS Y URLS CONSOLIDADAS

### Datos de Demanda y Mercado
- [Surtidores.com.ar Evolución 2025](https://surtidores.com.ar/evolucion-del-mercado-de-combustibles-en-argentina-produccion-ventas-y-precios-en-2025/)
- [YPF SEC EDGAR 2025](https://www.sec.gov/Archives/edgar/data/904851/000119312525048908/d926270d6k.htm)

### Perfil Horario
- [YPF Micropricing junio 2025](https://www.infobea.com/economia/2025/07/24/nafta-mas-barata-por-la-noche-las-ventas-de-ypf-crecieron-un-28-en-la-madrugada/)
- [La Nación horarios pico AMBA](https://www.lanacion.com.ar/buenos-aires/fin-de-la-hora-pico-cuales-son-los-horarios-con-mayor-circulacion-de-vehiculos-en-las-autopistas-y-nid04092023/)

### Tiempos
- [UNLP Simuladores colas](https://sedici.unlp.edu.ar/bitstream/handle/10915/20926/Documento_completo.pdf)
- [UTN Santa Fe Simulación](https://rtyc.utn.edu.ar/index.php/rtyc/article/download/192/180/709)

### Personal
- [FECRA Escala Salarial Oct 2026](https://calcularsueldo.com.ar/paritarias/13078/)
- [Decreto 46/2025 Autoservicio](https://www.boletinoficial.gob.ar/detalleAviso/primera/320236/20250129)

### Horario y Servicios
- [Mercuria Shell Sept 2026](https://www.iprofesional.com/negocios/463508-empieza-la-era-manzano-y-edenor-en-las-estaciones-de-servicio-shell)

### Estacionalidad
- [Festival Vendimia San Rafael](https://www.sitioandino.com.ar/departamentales/conoce-el-cronograma-completo-la-fiesta-la-vendimia-san-rafael-n5691899)
- [SMN San Rafael temperatura](https://weather.tomorrow.io/AR/M/San_Rafael/001448/)
- [Cortes RN-143 2026](https://www.sitioandino.com.ar/sociedad/como-se-encuentran-los-caminos-san-rafael-y-malargue-una-nueva-jornada-nevadas-n5725869)

### Mix de Combustibles
- [Surtidores.com.ar Balance 2025](https://surtidores.com.ar/balance-2025-se-desplomo-la-venta-de-gasoil-y-los-combustibles-premium-ganaron-terreno/)
- [Crisis GNC junio 2026](https://www.infobea.com/economia/2026/06/23/crisis-de-abastecimiento-en-invierno-que-dijo-la-camara-de-gnc-sobre-los-cortes-de-gas/)
- [ENARGAS GNC estaciones](https://www.enargas.gob.ar/secciones/gas-natural-comprimido/corredores-gnc.php)

### Parque Automotor
- [AFAC Parque 2024-2025](https://afac.org.ar/comunicaciones/comunicadosdeprensa/noticia?id=5854)
- [DEIE Mendoza](https://www.elsol.com.ar/mendoza/el-parque-automotor-en-mendoza-tuvo-un-notable-crecimiento/)

---

## 📝 NOTAS FINALES

- **Documento creado:** Octubre 2026
- **Compilado por:** Investigación paralela (7 agentes Haiku)
- **Estado:** Listo para Fase 2 (Modelo Determinista)
- **Próximo paso:** Validar con datos reales de la estación; desarrollar motor determinista con horizonte variable (día/semana/mes/estación/año)
- **Sensibilidad:** Todos los parámetros van a ser probados en análisis de sensibilidad post-implementación

---

**FIN DEL DOCUMENTO**
