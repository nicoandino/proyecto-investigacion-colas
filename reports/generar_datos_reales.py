"""Genera `DATOS_REALES.md` desde el Registro de datos (`sim/datos.py`).

El Registro es la única fuente de verdad de los números del modelo; este archivo es su versión legible.
Se regenera con:

    .venv/Scripts/python reports/generar_datos_reales.py
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.datos import CONTRADICCIONES, REGISTRO  # noqa: E402

SECCIONES = {
    "EST": "La estación",
    "SUR": "Surtidores y compresores",
    "PER": "Personal",
    "DEM": "Demanda",
    "VEH": "Vehículos y litros por carga",
    "TIE": "Tiempos de servicio",
    "INV": "Abastecimiento e inventario",
    "RED": "Red de rutas",
    "GNC": "GNC y cortes de invierno",
    "ECO": "Economía",
    "REC": "Configuración del caso clásico",
    "CAL": "Calendario y corrida",
    "MOD": "Modelo",
    "EVT": "Eventos aleatorios",
}
ETIQUETA_TIPO = {
    "dato": "🟢 dato", "estimacion": "🟡 estimación", "observacion": "🔵 observación",
    "supuesto": "🟠 supuesto", "heredado": "⚪ heredado",
}
NIVEL = {"A": "la estación", "B": "San Rafael", "C": "Mendoza", "D": "ciudad parecida", "E": "Argentina / otro"}


def texto(valor: object) -> str:
    """Valor legible y corto (las tuplas largas se resumen)."""
    s = str(valor).replace("|", "/")
    return s if len(s) <= 150 else s[:147] + "…"


def main() -> None:
    por_seccion: dict[str, list] = defaultdict(list)
    for d in REGISTRO:
        por_seccion[d.id.split("-")[0]].append(d)

    cuenta: dict[str, int] = defaultdict(int)
    for d in REGISTRO:
        cuenta[d.tipo] += 1

    lineas = [
        "# DATOS_REALES — los datos del modelo, con su fuente",
        "",
        "> Generado desde el Registro (`sim/datos.py`) con `reports/generar_datos_reales.py`. **No se edita a mano:**",
        "> si un dato cambia, se cambia en el Registro y se regenera este archivo.",
        "",
        "## Cómo leerlo",
        "",
        "- **No hay mediciones de la propia estación.** Los datos vienen de fuentes públicas (Shell, Secretaría de Energía,",
        "  ENARGAS, prensa, papers) o son supuestos del grupo. Cada fila dice cuál es cuál.",
        "- **Tipo:** 🟢 dato (fuente primaria u oficial) · 🟡 estimación (se deriva de fuentes débiles) · 🔵 observación propia",
        "  (medida en la estación; todavía no hay ninguna) · 🟠 supuesto del grupo · ⚪ heredado (del proyecto hipotético, **sin fuente**).",
        "- **Nivel:** A la estación · B San Rafael · C Mendoza · D ciudad parecida · E Argentina u otro.",
        "- **Confianza:** alta · media · baja · sin dato.",
        "- **Alternativas:** los valores que perdieron frente al adoptado; no se descartan, se usan como escenarios.",
        "- El GNC se mide en **m³**, nunca en litros. Los clientes por día **se derivan** de litros/mes ÷ litros medios por cliente.",
        "",
        f"**Resumen:** {len(REGISTRO)} datos · " + " · ".join(f"{ETIQUETA_TIPO[t]} {n}" for t, n in sorted(cuenta.items())),
        "",
    ]
    for prefijo, titulo in SECCIONES.items():
        filas = por_seccion.get(prefijo)
        if not filas:
            continue
        lineas += [f"## {titulo}", "", "| ID | Dato | Valor adoptado | Unidad | Tipo | Nivel | Confianza | Fuente | Alternativas |",
                   "|---|---|---|---|---|---|---|---|---|"]
        for d in filas:
            alt = " · ".join(f"{n} = {texto(v)}" if v is not None else n for n, v, _ in d.alternativas) or "—"
            lineas.append(
                f"| {d.id} | {d.nombre} | {texto(d.valor)} | {d.unidad} | {ETIQUETA_TIPO.get(d.tipo, d.tipo)} | "
                f"{NIVEL.get(d.nivel, d.nivel)} | {d.confianza} | {texto(d.fuente)} | {texto(alt)} |"
            )
        lineas.append("")

    lineas += ["## Contradicciones entre fuentes: qué se eligió y por qué", "",
               "Criterio único (nota 07): que mida lo mismo; oficial o primaria y vigente; más reciente; más "
               "específica de San Rafael/Mendoza; ante empate, la más conservadora.", "",
               "| ID | Tema | Impacto | Valor elegido | Por qué | Descartadas (sensibilidad) |",
               "|---|---|---|---|---|---|"]
    for c in CONTRADICCIONES:
        lineas.append(
            f"| {c.id} | {c.tema} | {c.impacto} | {texto(c.adoptado)} | {texto(c.criterio)} | {texto(c.alternativas)} |"
        )
    lineas += [
        "",
        "## Lo que todavía no sabemos (a relevar en la estación)",
        "",
        "1. **Demanda real:** litros por mes por producto y clientes por franja, un día hábil y uno de fin de semana.",
        "2. **Dotación:** playeros, cajeros y encargado por turno; horario real de la playa y del shop; si hay autoservicio.",
        "3. **Litros por carga y tiempo en la cara:** cronometrar 5–10 vehículos por producto.",
        "4. **GNC:** contrato (firme o interrumpible), compresores, cortes de los últimos inviernos.",
        "5. **Economía:** margen por litro y por compra, flete real por km y sueldos vigentes.",
        "6. **Mix diésel G2/G3** y porcentaje de clientes que entran al shop.",
        "7. **Estacionalidad real:** ventas mensuales de la Secretaría de Energía.",
        "",
        "Las notas de investigación con las citas textuales y las URL están en `research_notes/`.",
        "",
    ]
    destino = Path(__file__).resolve().parents[1] / "DATOS_REALES.md"
    destino.write_text("\n".join(lineas), encoding="utf-8")
    print(f"{destino.name}: {len(REGISTRO)} datos, {len(CONTRADICCIONES)} contradicciones")


if __name__ == "__main__":
    main()
