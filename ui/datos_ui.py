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
    "dato": ("dato", "🟢 dato"),
    "estimacion": ("estimacion", "🟡 estimación"),
    "observacion": ("observacion", "🔵 observación propia"),
    "supuesto": ("supuesto", "🟠 supuesto"),
    "heredado": ("heredado", "⚪ heredado (sin fuente)"),
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
    clase, texto = INSIGNIAS.get(dato.tipo, ("heredado", "⚪ heredado (sin fuente)"))
    titulo = _html.escape(tooltip(dato), quote=True)
    return (
        f"<span class='insignia insignia-{clase}' title='{titulo}'>{texto}</span>"
    )


def insignia_texto(dato: Dato) -> str:
    """La insignia como texto plano (para captions, donde no entra HTML)."""
    return INSIGNIAS.get(dato.tipo, ("heredado", "⚪"))[1]


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


def tabla_registro(solo_motor: bool = False) -> pd.DataFrame:
    """El Registro completo como DataFrame (con una fila por alternativa)."""
    filas = []
    for d in REGISTRO:
        filas.append(fila_registro(d))
        for nombre, alt, fuente in d.alternativas:
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
            "Valor adoptado": [c.adoptado for c in CONTRADICCIONES],
            "Alternativas (sensibilidad)": [c.alternativas for c in CONTRADICCIONES],
        }
    ).to_csv(buffer, index=False, sep=";")
    return buffer.getvalue()


def nombre_del_id(id_: str) -> str:
    """Nombre corto de un Dato por su id (para la barra lateral)."""
    return por_id(id_).nombre


# =============================================================================
# Esquema del playón real (SVG estático para la pestaña "La estación", §8.2)
# =============================================================================
def esquema_estacion_html() -> str:
    """SVG de la estación: 6 surtidores de doble cara (12 caras) en 3 zonas, el
    minimarket y las dos avenidas. Los colores salen de `ui/tema.py` (N15)."""
    from ui.tema import (
        AMARILLO,
        AMARILLO_SUAVE,
        ASFALTO,
        BORDE,
        FONDO,
        PRODUCTO,
        ROJO,
        TINTA,
        TINTA_TENUE,
    )

    def cara(x: float, y: float, color: str, direccion: int) -> str:
        """Una flecha = una cara = un carril (V8). direccion: +1 arriba, -1 abajo."""
        punta = y + 14 if direccion < 0 else y - 14
        return (
            f"<line x1='{x}' y1='{y}' x2='{x}' y2='{punta + (7 if direccion < 0 else -7)}' "
            f"stroke='{color}' stroke-width='3'/>"
            f"<path d='M {x - 5} {punta} L {x} {punta + (8 if direccion < 0 else -8)} "
            f"L {x + 5} {punta} Z' fill='{color}'/>"
        )

    def surtidor(x: float, y: float, numero: str, color: str, etiqueta: str) -> str:
        return (
            f"<rect x='{x}' y='{y}' width='46' height='96' rx='6' fill='{FONDO}' "
            f"stroke='{color}' stroke-width='3'/>"
            f"<text x='{x + 23}' y='{y + 122}' fill='{TINTA}' font-size='13' "
            f"font-weight='600' text-anchor='middle'>{numero}</text>"
            f"{cara(x + 12, y + 48, color, -1)}"
            f"{cara(x + 34, y + 48, color, -1)}"
            f"{cara(x + 12, y + 48, color, +1)}"
            f"{cara(x + 34, y + 48, color, +1)}"
            f"<text x='{x + 23}' y='{y - 16}' fill='{TINTA_TENUE}' font-size='11' "
            f"text-anchor='middle'>{etiqueta}</text>"
        )

    zonas = (
        (100, "S1", AMARILLO, "NAFTA"),
        (190, "S2", AMARILLO, ""),
        (300, "S3", PRODUCTO["diesel"], "DIÉSEL"),
        (420, "S4", PRODUCTO["gnc"], "GNC"),
        (520, "S5", PRODUCTO["gnc"], ""),
        (620, "S6", PRODUCTO["gnc"], ""),
    )
    surtidores = "".join(surtidor(x, 120, n, c, e) for x, n, c, e in zonas)

    return f"""<!doctype html><html lang="es"><body style="margin:0">
<svg viewBox="0 0 1200 320" xmlns="http://www.w3.org/2000/svg"
     style="font-family:system-ui,-apple-system,Segoe UI,sans-serif; width:100%">
  <rect width="1200" height="320" fill="{FONDO}"/>
  <!-- Avenidas -->
  <rect x="0" y="8" width="1200" height="34" fill="{ASFALTO}"/>
  <text x="16" y="30" fill="{FONDO}" font-size="14" font-weight="700"
        letter-spacing="1.5">AV. BALLOFFET — RN 143 (tramo urbano, 4 carriles)</text>
  <rect x="0" y="0" width="34" height="320" fill="{ASFALTO}"/>
  <text x="17" y="150" fill="{FONDO}" font-size="12" font-weight="700" letter-spacing="1"
        transform="rotate(-90 17 150)" text-anchor="middle">AV. LOS SAUCES — RP 158</text>
  <path d="M 60 60 L 40 80 L 60 100" fill="none" stroke="{ASFALTO}" stroke-width="4"/>
  <!-- Playón con techo amarillo y filete rojo -->
  <rect x="70" y="64" width="900" height="216" rx="10" fill="{FONDO}" stroke="{BORDE}"/>
  <rect x="70" y="64" width="900" height="20" rx="10" fill="{AMARILLO}"/>
  <rect x="70" y="84" width="900" height="4" fill="{ROJO}"/>
  {surtidores}
  <text x="100" y="276" fill="{TINTA}" font-size="13" font-weight="700">ZONA A: nafta — 4 caras (Súper · V-Power)</text>
  <text x="300" y="276" fill="{TINTA}" font-size="13" font-weight="700">ZONA B: diésel — 2 caras (G2 · G3)</text>
  <text x="420" y="276" fill="{TINTA}" font-size="13" font-weight="700">ZONA C: GNC — 6 caras</text>
  <!-- Minimarket -->
  <rect x="760" y="100" width="190" height="160" rx="10" fill="{AMARILLO_SUAVE}"
        stroke="{BORDE}"/>
  <text x="855" y="128" fill="{TINTA}" font-size="14" font-weight="700"
        text-anchor="middle">MINIMARKET</text>
  <text x="855" y="146" fill="{TINTA_TENUE}" font-size="11" text-anchor="middle">
    "Shell Select" (nombre sin confirmar) · ≈ 140 m²</text>
  <rect x="790" y="160" width="130" height="34" rx="6" fill="{FONDO}" stroke="{TINTA_TENUE}"/>
  <text x="855" y="181" fill="{TINTA}" font-size="11" text-anchor="middle">1 caja (por turno)</text>
  <text x="855" y="206" fill="{TINTA_TENUE}" font-size="11" text-anchor="middle">
    entra ≈ 20 % de los que cargan</text>
  <text x="855" y="250" fill="{TINTA_TENUE}" font-size="11" text-anchor="middle">
    servicio atendido · playa 24 h</text>
  <!-- Leyenda de caras -->
  <text x="1000" y="100" fill="{TINTA_TENUE}" font-size="11">▲▼ cada flecha =</text>
  <text x="1000" y="114" fill="{TINTA_TENUE}" font-size="11">una cara = un carril</text>
  <text x="1000" y="132" fill="{TINTA_TENUE}" font-size="11">(1 vehículo a la vez)</text>
  <text x="1000" y="150" fill="{TINTA}" font-size="13" font-weight="700">12 caras en total</text>
</svg></body></html>"""
