# 12 · Serie mensual real de ventas: Shell en Mendoza (PRO-01)

Fecha: 14-oct-2026. La usa la parte 3 del orquestador (Pronóstico, etapas P1–P4).

## 1. La fuente

- **Secretaría de Energía de la Nación, portal de datos abiertos** (datos.energia.gob.ar), conjunto
  **"Refinación y Comercialización de petróleo, gas y derivados (Tablas Dinámicas)"**, recurso
  **"Ventas (excluye ventas a empresas del sector)"** (CSV, ≈ 770 MB, 6,5 millones de filas; última actualización del
  recurso: 2-oct-2026; descargado el 14-oct-2026).
- URL del conjunto: http://datos.energia.gob.ar/dataset/refinacion-y-comercializacion-de-petroleo-gas-y-derivados-tablas-dinamicas
- URL del recurso: http://datos.energia.gob.ar/dataset/5bdc436c-60d4-4c86-98ab-59834d047700/resource/f0e4e10a-e4b8-44e6-bd16-763a43742107/download/ventas-excluye-ventas-a-empresas-del-sector-.csv
- Columnas: año, mes, empresa, tipo y subtipo de comercialización, producto, unidad, provincia, cantidad.
- Es la declaración obligatoria de las petroleras (régimen de información de la Secretaría): dato **oficial**.

## 2. El filtro

| Columna | Valor |
|---|---|
| empresa | **SHELL C.A.P.S.A.** (la misma razón social de la bandera de la estación, EST-03) |
| subtipo de comercialización | **Al Público** (lo que se vende en las estaciones de servicio) |
| provincia | **Mendoza** |
| producto | Nafta Grado 2 (Súper) + Nafta Grado 3 (Ultra = V-Power) + Gasoil Grado 2 + Gasoil Grado 3 |
| período guardado | enero 2019 – agosto 2026 (92 meses, sin faltantes) |

Unidad: **m³ por mes** (1 m³ = 1.000 L). El GNC no está (no lo comercializan las petroleras: viene por gasoducto).

## 3. Qué es y qué no es

- **No es la estación de Balloffet**: el dataset no trae datos por estación. Es **la suma de todas las estaciones Shell
  de Mendoza** (≈ 11.000–16.000 m³ por mes; Shell vende el 16,6 % de lo que se vende al público en Mendoza en 2026).
  Nivel C (Mendoza), confianza alta en el dato y media como representante de la estación.
- Por eso el modelo usa **la forma de la serie** (cuánto pesa cada mes del año y cómo viene la tendencia, en %) y la
  **escala a DEM-01** (270.000 L/mes de la estación). Supuesto: la estación sigue el mismo patrón mensual que el
  conjunto de las Shell de la provincia.

## 4. Lo que se ve en la serie (totales por año, m³)

| Año | Total | Comentario |
|---|---|---|
| 2019 | 115.491 | base pre-pandemia |
| 2020 | 118.317 | abril de 2020: 5.278 m³ (cuarentena) |
| 2021 | 177.109 | rebote fuerte: la participación de Shell sube de 15 % (2019) a 20 % |
| 2022 | 175.561 | |
| 2023 | 165.057 | baja desde mitad de año |
| 2024 | 157.502 | |
| 2025 | 153.416 | el gasoil G2 baja 31 % (51.262 → 35.540 m³) |
| 2026 (ene–ago) | 91.001 | ≈ 11.400 por mes |

**Ventana de ajuste (PRO-02):** desde enero de 2022. Se dejan afuera la pandemia (2020) y el rebote de 2021, que no
se repiten; con 56 meses alcanzan para estimar los 12 índices estacionales (más de 4 años). Los últimos 12 meses
(sep-2025 – ago-2026) quedan **para probar** los métodos (no se usan para ajustarlos).
