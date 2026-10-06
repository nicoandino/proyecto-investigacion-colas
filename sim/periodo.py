"""El período a simular y las ediciones del usuario (rediseño v3, etapa 2).

El menú inicial de la app pide **qué período** se simula —por días, por meses, por estación o el
año completo— y la simulación con datos reales corre todo ese período de punta a punta. Este
módulo es la lógica pura de esa elección (sin Streamlit): arma el `Periodo`, dice si incluye el
invierno (y por lo tanto los cortes de GNC) y aplica las **ediciones** opcionales a los parámetros.

Las ediciones son pocas a propósito: playeros, nivel de demanda, el doble de demanda en la hora
pico, el porcentaje de clientes GNC y el precio del litro. Una simulación editada ya no es la de
datos reales: usa azar (Monte Carlo) y la app explica qué se sorteó.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta

from sim.config import (
    ANO_REFERENCIA,
    ParametrosEconomicos,
    ParametrosGNC,
    ParametrosSimulacion,
    PerfilHorario,
    dias_del_mes,
    turnos_de,
)
from sim.datos import valor
from sim.distribuciones import AleatorioDeterminista
from sim.gnc import MESES_INVIERNO, calendario_de_episodios, episodios_con_fechas

MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

#: Temporadas del menú (CAL-08): estaciones meteorológicas del hemisferio sur, de mes entero.
#: nombre → (mes en que empieza, cantidad de meses).
TEMPORADAS: dict[str, tuple[int, int]] = {
    nombre: (inicio, meses) for nombre, (inicio, meses) in valor("CAL-08")
}

#: Tope de un período: un año de 365 días.
MAXIMO_DIAS = 365

#: Horas pico de la edición "el doble en la hora pico" (07–10 y 16–18 h, perfil DEM-02).
HORAS_PICO = (7, 8, 9, 16, 17)


# =============================================================================
# El período
# =============================================================================
@dataclass(frozen=True)
class Periodo:
    """Qué se simula: desde qué fecha y cuántos días."""

    tipo: str                       # "dias" · "meses" · "estacion" · "anio"
    titulo: str                     # "Verano", "Enero a marzo", "180 días desde el 1 de enero"…
    fecha_inicio: tuple[int, int]   # (mes, día)
    dias: int

    @property
    def inicio(self) -> date:
        return date(ANO_REFERENCIA, *self.fecha_inicio)

    @property
    def fin(self) -> date:
        return self.inicio + timedelta(days=self.dias - 1)

    @property
    def incluye_invierno(self) -> bool:
        """True si algún día del período cae en jun–ago (entran los cortes de GNC)."""
        return any(
            (self.inicio + timedelta(days=d)).month in MESES_INVIERNO for d in range(self.dias)
        )

    @property
    def texto(self) -> str:
        """'Del 1 de enero al 30 de junio · 181 días'."""
        return (
            f"Del {texto_fecha(self.inicio)} al {texto_fecha(self.fin)} · "
            f"{self.dias} día{'s' if self.dias != 1 else ''}"
        )


def texto_fecha(f: date) -> str:
    """'1 de enero' (con el año sólo si cruza al año siguiente)."""
    extra = f" de {f.year}" if f.year != ANO_REFERENCIA else ""
    return f"{f.day} de {MESES[f.month - 1]}{extra}"


def por_dias(dias: int, mes: int, dia: int) -> Periodo:
    """`dias` días a partir del `dia` de `mes`."""
    dias = max(1, min(int(dias), MAXIMO_DIAS))
    dia = max(1, min(int(dia), dias_del_mes(mes)))
    return Periodo("dias", f"{dias} días desde el {dia} de {MESES[mes - 1]}", (mes, dia), dias)


def por_meses(desde: int, hasta: int) -> Periodo:
    """De enero a marzo, etc.: desde el día 1 de `desde` hasta el último día de `hasta`."""
    if hasta < desde:
        raise ValueError("El mes final tiene que ser igual o posterior al inicial.")
    dias = sum(dias_del_mes(m) for m in range(desde, hasta + 1))
    titulo = MESES[desde - 1].capitalize() if desde == hasta else (
        f"{MESES[desde - 1].capitalize()} a {MESES[hasta - 1]}"
    )
    return Periodo("meses", titulo, (desde, 1), dias)


def por_temporada(nombre: str) -> Periodo:
    """Una estación entera: Verano (dic–feb), Otoño (mar–may), Invierno (jun–ago), Primavera (sep–nov)."""
    inicio, meses = TEMPORADAS[nombre]
    dias = sum(dias_del_mes(((inicio - 1 + k) % 12) + 1) for k in range(meses))
    return Periodo("estacion", nombre, (inicio, 1), dias)


def anio_completo() -> Periodo:
    return Periodo("anio", "Año completo", (1, 1), 365)


def cortes_gnc_previstos(periodo: Periodo, g: ParametrosGNC) -> list[tuple[date, date]]:
    """Fechas de los episodios de corte de GNC que caen en el período (sin azar: fijas)."""
    episodios = calendario_de_episodios(g, AleatorioDeterminista(0), periodo.inicio, periodo.dias)
    return episodios_con_fechas(episodios, periodo.inicio, periodo.dias)


def con_periodo(p: ParametrosSimulacion, periodo: Periodo) -> ParametrosSimulacion:
    """Los mismos parámetros pero simulando `periodo`."""
    return replace(
        p, fecha_inicio=periodo.fecha_inicio, dias=periodo.dias,
        horizonte="anio" if periodo.tipo == "anio" else "mes", dia_animado=1,
    )


# =============================================================================
# Las ediciones
# =============================================================================
#: Los tres niveles de demanda salen del rango del Registro (DEM-01: bajo, adoptado, alto).
NIVELES_DEMANDA = ("poca", "media", "alta")


def litros_de_nivel(nivel: str) -> float:
    """Litros por mes de cada nivel de demanda: poca = DEM-01 bajo, media = adoptado, alta = DEM-01 alto."""
    from sim.datos import por_id

    d = por_id("DEM-01")
    return {"poca": float(d.bajo), "media": float(d.valor), "alta": float(d.alto)}[nivel]


@dataclass(frozen=True)
class Edicion:
    """Lo que el usuario cambió en *Editar simulación*. Los valores en None no se tocan."""

    playeros: tuple[int, int, int] | None = None      # noche · mañana · tarde
    nivel_demanda: str = "media"                      # poca · media · alta
    doble_pico: bool = False                          # el doble de clientes en la hora pico
    pct_gnc: float | None = None                      # 0 a 1
    precios: tuple[tuple[str, float], ...] | None = None
    semilla: int = 1                                  # la edición usa azar: la semilla la repite

    def hay_cambios(self, base: ParametrosSimulacion) -> bool:
        return (
            (self.playeros is not None and self.playeros != base.playeros_por_turno)
            or self.nivel_demanda != "media"
            or self.doble_pico
            or (self.pct_gnc is not None and abs(self.pct_gnc - base.pct_gnc) > 1e-9)
            or (self.precios is not None and self.precios != tuple(valor("ECO-08")))
        )


def aplicar_edicion(
    p: ParametrosSimulacion, eco: ParametrosEconomicos, ed: Edicion
) -> tuple[ParametrosSimulacion, ParametrosEconomicos]:
    """Parámetros y economía de una simulación editada: **con azar** (sin `determinista`)."""
    p = replace(p, determinista=False)
    if ed.playeros is not None:
        p = replace(p, playeros_por_turno=ed.playeros, turnos=turnos_de(ed.playeros))
    litros = litros_de_nivel(ed.nivel_demanda)
    if ed.pct_gnc is not None:
        p = replace(p, pct_gnc=ed.pct_gnc)
    if ed.doble_pico:
        factores = p.perfil.factores
        nuevos = tuple(
            f * valor("DEM-13") if h in HORAS_PICO else f for h, f in enumerate(factores)
        )
        # El perfil se reparte entre las 24 h: para que las horas que no son pico conserven su
        # tasa de llegadas, los litros del mes crecen en proporción al peso que suma el pico.
        litros *= sum(nuevos) / sum(factores)
        p = replace(p, perfil=PerfilHorario(nuevos))
    p = replace(p, litros_mes=litros)
    if ed.precios is not None:
        eco = replace(eco, precios=ed.precios)
    return p, eco
