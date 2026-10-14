# 08 · Calendario de demanda: verano, vacaciones de invierno de Mendoza y resto del invierno

Fecha: 13-oct-2026. Lo usa el calendario de temporadas del simulador (Registro DEM-14 y DEM-15, tanda 5).

## 1. Vacaciones de invierno de Mendoza 2026 (DEM-15)

| Dato | Valor | Fuente | Fecha | Nivel / confianza |
|---|---|---|---|---|
| Receso invernal escolar en Mendoza | **lunes 6 al viernes 17 de julio de 2026**; vuelta a clases el lunes 20 | Calendario escolar 2026 de la Dirección General de Escuelas (DGE) de Mendoza, según Los Andes ("Más de 430.000 chicos están oficialmente de vacaciones en Mendoza", 6-jul-2026: https://www.losandes.com.ar/sociedad/mas-430000-chicos-estan-oficialmente-vacaciones-mendoza-las-fechas-tener-cuenta-adelante-n5997491), Ámbito ("Ciclo lectivo 2026: cuándo empiezan las clases en Mendoza, receso invernal y vacaciones de verano": https://www.ambito.com/informacion-general/ciclo-lectivo-2026-cuando-empiezan-las-clases-mendoza-receso-invernal-y-vacaciones-verano-n6233238) y El Sol (https://www.elsol.com.ar/mendoza/empiezan-las-vacaciones-de-invierno-y-este-dia-hay-que-volver-a-clases/) | 2026 | C (Mendoza) · media |

- Son fechas **distintas de las de Buenos Aires** (CABA y PBA salen más tarde en julio).
- No se pudo abrir el sitio de la DGE (dge.mendoza.edu.ar): las tres notas citan el calendario oficial y coinciden.
  Por eso el dato queda como nivel C, confianza media, y no como "confirmado".
- Los Andes cuenta que una ola polar suspendió las clases presenciales el jueves 2 y viernes 3 de julio: es una
  suspensión puntual, no cambia el receso. No se modela.
- El Registro anterior (DEM-09) decía "9–20 jul" sin fuente: no coincide y se corrigió (criterio de la nota 07: oficial
  y más reciente).

## 2. Cuánto cambia la demanda en cada temporada (DEM-14)

**No hay un dato de ventas de combustible por temporada para San Rafael.** La única serie con forma estacional que
tiene el Registro es el "proxy turístico" de DATOS §6 (índices de ocupación turística por mes: ene 100 · feb 60 ·
mar 80 · abr 65 · may 60 · jun 55 · jul 85 · ago 75 · sep 70 · oct 70 · nov 75 · dic 85; promedio 73,3). La
contradicción C10 ya decidió que **la ocupación hotelera no es venta de combustible**: un turista más no es un tanque
más por día, y la mayor parte de los clientes de una estación urbana son de la ciudad.

**Criterio (repetible):** el factor de cada temporada es **la mitad del desvío** del proxy turístico respecto de su
promedio, redondeado a un punto. La mitad, porque la ocupación hotelera exagera el efecto sobre el combustible (C10), y
es la regla del empate de la nota 07: ante la duda, el valor que menos exagera.

| Temporada | Meses del proxy | Proxy ÷ promedio | Mitad del desvío | Factor adoptado |
|---|---|---|---|---|
| Verano (1/dic – 28/feb), por el turismo | dic, ene, feb: (85 + 100 + 60) / 3 = 81,7 | 1,114 | +5,7 % | **× 1,06** |
| Vacaciones de invierno de Mendoza (6–17/jul) | jul: 85 | 1,159 | +8,0 % | **× 1,08** |
| Resto del invierno (jun–ago fuera de las vacaciones): la gente sale menos | jun, ago: (55 + 75) / 2 = 65 | 0,886 | −5,7 % | **× 0,94** |
| Otoño y primavera | — | — | — | **× 1,00** (neutro) |

- Son **supuestos** (tipo `supuesto`, confianza baja), editables desde el menú de la app.
- El factor multiplica los litros de cada día de esa temporada (además del fin de semana × 1,30 normalizado). **No se
  renormaliza al año**: el promedio anual sube ≈ +0,4 % (90 días × 6 % + 12 × 8 % − 80 × 6 % ≈ +1,6 días de venta en
  365), y la app lo dice.
- Está **activo por defecto en la app** y **neutro en `ParametrosSimulacion()` y en `clasico()`**, así que los números
  dorados y los controles anteriores no cambian.
- Con datos reales de la estación (ventas mensuales de la Secretaría de Energía o del encargado) estos factores se
  reemplazan directamente en el Registro.
