"""Insignias y tablas del Registro de datos (§8.4).

Cada widget y cada fila lleva la insignia de su `Dato` con un tooltip con la fuente,
el nivel, la fecha, la nota y las alternativas. La pestaña "Datos y fuentes" se arma
con `tabla_registro()` y el CSV con `csv_registro()`.
"""

from __future__ import annotations

import html as _html
import io

import pandas as pd

from sim.datos import CONTRADICCIONES, Dato, MAPA_PARAMETROS, REGISTRO, por_id

#: Cómo se muestra cada tipo del Registro (color y texto, §8.4).
INSIGNIAS: dict[str, tuple[str, str]] = {
    "dato": ("dato", "dato"),
    "estimacion": ("estimacion", "estimación"),
    "observacion": ("observacion", "observación propia"),
    "supuesto": ("supuesto", "supuesto"),
    "heredado": ("heredado", "heredado (sin fuente)"),
}


def tooltip(dato: Dato) -> str:
    """Texto del tooltip: fuente, nivel, fecha, nota y alternativas."""
    partes = [f"Fuente: {dato.fuente}" if dato.fuente else "Fuente: sin declarar"]
    partes.append(f"Nivel: {dato.nivel} · Confianza: {dato.confianza}")
    if dato.fecha_fuente:
        partes.append(f"Fecha de la fuente: {dato.fecha_fuente}")
    if dato.nota:
        partes.append(dato.nota)
    if dato.alternativas:
        partes.append(
            "Alternativas: "
            + " · ".join(f"{nombre} = {valor} ({fuente})"
                         for nombre, valor, fuente in dato.alternativas)
        )
    return "\n".join(partes)


def insignia_html(dato: Dato) -> str:
    """La insignia HTML del Dato (para `st.markdown(..., unsafe_allow_html=True)`)."""
    clase, texto = INSIGNIAS.get(dato.tipo, ("heredado", "heredado (sin fuente)"))
    titulo = _html.escape(tooltip(dato), quote=True)
    return (
        f"<span class='insignia insignia-{clase}' title='{titulo}'>{texto}</span>"
    )


def insignia_texto(dato: Dato) -> str:
    """La insignia como texto plano (para captions, donde no entra HTML)."""
    return INSIGNIAS.get(dato.tipo, ("heredado", "heredado"))[1]


def fila_registro(dato: Dato) -> dict:
    """Una fila de la tabla/csv del Registro.

    `Valor` va como texto: la columna mezcla números, tuplas y cadenas, y pyarrow
    (el serializador de `st.dataframe`) no acepta columnas de objetos mixtos.
    """
    return {
        "ID": dato.id,
        "Dato": dato.nombre,
        "Valor": str(dato.valor),
        "Unidad": dato.unidad,
        "Nivel": dato.nivel,
        "Tipo": dato.tipo,
        "Confianza": dato.confianza,
        "Fuente": dato.fuente,
        "Fecha de la fuente": dato.fecha_fuente,
        "Origen": dato.origen,
        "Conflicto": dato.conflicto,
        "Nota": dato.nota,
    }


def tabla_registro(solo_motor: bool = False, con_alternativas: bool = True) -> pd.DataFrame:
    """El Registro completo como DataFrame (con una fila por alternativa, salvo `con_alternativas=False`)."""
    filas = []
    for d in REGISTRO:
        filas.append(fila_registro(d))
        for nombre, alt, fuente in (d.alternativas if con_alternativas else ()):
            filas.append({
                "ID": f"{d.id} · alternativa",
                "Dato": f"{d.nombre} — alternativa: {nombre}",
                "Valor": str(alt),
                "Unidad": d.unidad,
                "Nivel": d.nivel,
                "Tipo": "alternativa",
                "Confianza": d.confianza,
                "Fuente": fuente,
                "Fecha de la fuente": "",
                "Origen": d.origen,
                "Conflicto": d.conflicto,
                "Nota": "valor que perdió en la contradicción (queda como eje de sensibilidad)",
            })
    if solo_motor:
        ids_motor = set(MAPA_PARAMETROS.values())
        filas = [f for f in filas if f["ID"].split(" ·")[0] in ids_motor
                 or f["Tipo"] == "alternativa" and f["ID"].split(" ·")[0] in ids_motor]
    return pd.DataFrame(filas)


def csv_registro() -> str:
    """CSV completo: todas las filas del Registro + alternativas + contradicciones."""
    buffer = io.StringIO()
    tabla_registro().to_csv(buffer, index=False, sep=";")
    buffer.write("\n\n# Contradicciones entre fuentes (ORQUESTADOR §4.2)\n")
    pd.DataFrame(
        {
            "ID": [c.id for c in CONTRADICCIONES],
            "Tema": [c.tema for c in CONTRADICCIONES],
            "Impacto": [c.impacto for c in CONTRADICCIONES],
            "Valor elegido": [c.adoptado for c in CONTRADICCIONES],
            "Criterio": [c.criterio for c in CONTRADICCIONES],
            "Descartadas (sensibilidad)": [c.alternativas for c in CONTRADICCIONES],
        }
    ).to_csv(buffer, index=False, sep=";")
    return buffer.getvalue()


def nombre_del_id(id_: str) -> str:
    """Nombre corto de un Dato por su id (para la barra lateral)."""
    return por_id(id_).nombre
