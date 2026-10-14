# 10 · El GNC lo carga un playero (PER-04)

Fecha: 14-oct-2026. Lo usa la etapa E0 de la parte 4 (Registro PER-04 y SUR-00).

## 1. Qué decía el modelo y por qué estaba mal

Hasta la etapa E0, PER-04 era un **supuesto del orquestador viejo**: "el GNC no retiene playero, sólo conecta la
manguera". En el motor, el cliente de GNC tomaba una cara y un compresor, pero **nunca un playero**. Nico lo
marcó como error de lógica (14/10/2026): en las estaciones de GNC la carga la hace el playero.

## 2. Qué lo respalda

| Fuente | Qué dice | Peso |
|---|---|---|
| **EST-07** (lista oficial de servicios de Shell para esta estación) | "servicio atendido" | Dato de la propia estación |
| Observación del grupo (Nico, 14/10/2026) | En las estaciones de GNC el que carga es el playero | Observación directa |
| ENARGAS, Res. 369/2020 (citada en surtidores.com.ar y en guías de consumo) | Prohíbe cargar GNC con personas a bordo: los ocupantes bajan y el auto queda a cargo del personal | Norma: apoya que la carga es operada por la estación |
| Decreto 70/2023 | Derogó la prohibición del Decreto 2407/83 y habilita el **autoservicio como opción** | No obliga: esta estación informa servicio atendido |

No se encontró una norma vigente que prohíba en forma expresa el autoservicio de GNC (habría que leer la NAG-420
completa). Por eso PER-04 queda como **dato, confianza media**: lo sostienen el servicio atendido de la propia
estación y la observación, no una prohibición legal.

## 3. Cómo entra al modelo

- **PER-04 = sí:** el cliente de GNC necesita **cara → playero → compresor**, siempre en ese orden (sin
  bloqueos cruzados). El playero queda con el auto mientras espera el compresor y mientras dura la carga (TIE-04),
  igual que en nafta y diésel. Si se cansa de esperar al playero o al compresor, se va (paciencia TIE-06).
- **Alternativa (tornado, eje C9):** "GNC en autoservicio (sin playero)", el caso que habilita el Decreto 70/2023.
- **ρ teórico:** ahora cuenta todos los minutos de playero: `λ_pico · [(1 − g) · E[S_líquidos] + g · E[S_GNC]] ÷
  playeros`, con g = clientes de GNC (DEM-05).
- **Efecto medido** (datos reales, sin azar): ρ en la hora pico 0,85 → **0,89**. Julio: atendidos 7.677 → **7.664**
  (14 clientes más se van por la espera). Año completo: atendidos 91.949 → **91.760**; los que se van por la espera,
  73 → **286**. Es chico porque el GNC es el 3 % de las llegadas (DEM-05); importa para los eventos de la parte 4 (si
  el único playero de la noche se va, la estación entera queda sin atención, GNC incluido).

## Fuentes

- ENARGAS, Res. 369/2020: https://ligadelconsorcista.org/enargas-resolucion-369-2020-gnc-codigo-qr-
- Decreto 70/2023 y autoservicio: https://www.derechoenzapatillas.com/2025/se-permite-el-autoservicio-de-combustible-autodespacho/
- Normativa de GNC (resoluciones ENARGAS publicadas): https://surtidores.com.ar/wp-content/uploads/2024/01/Resoluccion-ENARGAS-24-2004-con-Adenda-1.pdf
