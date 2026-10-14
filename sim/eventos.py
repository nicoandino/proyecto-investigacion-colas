"""Eventos aleatorios que alteran la estación (parte 4 del orquestador, §20–23).

Cómo funciona:

1. **Antes de correr** se arma el CALENDARIO de eventos de la corrida: para cada día y cada evento se sortea si
   ocurre (una probabilidad por día, EVT-01…14), y si ocurre, a qué hora, cuánto dura y a quién afecta. Se usa una
   semilla propia (`ParametrosEventos.semilla`) y un stream por evento al final de `STREAMS`, así que:
     · con la misma semilla salen siempre los mismos eventos (se pueden comprobar);
     · prender o apagar un evento no cambia las fechas de los otros (cada uno tiene su stream y se sortean todos
       siempre; después se filtran los prendidos);
     · el resto de la simulación no se toca: con datos reales sigue sin azar.
2. El motor (`sim/modelo.py`) **aplica** el calendario con mecanismos simples: un playero de menos (una reserva en
   el recurso de playeros, como los turnos), una cara o un compresor fuera de servicio, la estación parada (todos
   los playeros reservados), el cobro más lento, etc.
3. Cada evento ocurrido se informa con lo que le hizo a la estación (clientes que se fueron mientras duraba).

Este módulo no importa Streamlit ni `ui/` y no imprime nada.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import NamedTuple

from sim.config import ANO_REFERENCIA, MINUTOS_POR_DIA, ParametrosSimulacion
from sim.datos import valor
from sim.distribuciones import Aleatorio


class TipoEvento(NamedTuple):
    """Un evento del catálogo (§21)."""

    id: str          # "EVT-01"
    nombre: str
    grupo: str       # Personal · Equipos · Precio y abastecimiento · Demanda y seguridad
    efecto: str      # qué le hace a la estación, en una frase


CATALOGO: tuple[TipoEvento, ...] = (
    TipoEvento("EVT-01", "Abandono repentino del turno", "Personal",
               "un playero se va y nadie lo reemplaza hasta el próximo cambio de turno"),
    TipoEvento("EVT-02", "Licencia por accidente (con horas extra)", "Personal",
               "otro playero cubre el turno con horas extra: el servicio no cambia, sube el costo"),
    TipoEvento("EVT-03", "Falta sin aviso", "Personal",
               "un turno entero con un playero menos"),
    TipoEvento("EVT-04", "Licencia sin reemplazo", "Personal",
               "ese turno queda con un playero menos todos los días de la licencia"),
    TipoEvento("EVT-05", "Falla de un surtidor", "Equipos",
               "una cara fuera de servicio hasta que llega el técnico"),
    TipoEvento("EVT-06", "Falla de un compresor de GNC", "Equipos",
               "un compresor menos"),
    TipoEvento("EVT-07", "Corte de luz", "Equipos",
               "sin surtidores ni compresores: la estación se para"),
    TipoEvento("EVT-08", "Se cae el sistema de cobro", "Equipos",
               "sólo efectivo: cada carga tarda más y la caja del minimarket también"),
    TipoEvento("EVT-09", "Aumento de precio", "Precio y abastecimiento",
               "precio +10 % con el mismo margen por litro; el día anterior la gente se adelanta a cargar"),
    TipoEvento("EVT-10", "Faltante con cupo", "Precio y abastecimiento",
               "cupo de 30 L por cliente; los camiones tardan más y traen la mitad"),
    TipoEvento("EVT-11", "Rotura del camión en la ruta", "Precio y abastecimiento",
               "el camión llega de 12 a 48 h tarde"),
    TipoEvento("EVT-12", "Corte de la avenida", "Demanda y seguridad",
               "llega la mitad de los clientes mientras dura"),
    TipoEvento("EVT-13", "Evento masivo en San Rafael", "Demanda y seguridad",
               "más clientes esos días"),
    TipoEvento("EVT-14", "Asalto", "Demanda y seguridad",
               "la estación se para mientras actúa la policía"),
)
POR_ID = {t.id: t for t in CATALOGO}

#: Mecanismo con el que el motor aplica cada evento (los que tienen calendario).
MECANISMO = {
    "EVT-01": "playero", "EVT-03": "playero", "EVT-04": "playero_diario",
    "EVT-05": "cara", "EVT-06": "compresor", "EVT-07": "parada", "EVT-14": "parada",
    "EVT-08": "cobro",
}

#: Turnos de PER-01: (nombre, hora de inicio, hora de fin); la noche termina a las 06 del día siguiente.
TURNOS = (("noche", 22, 30), ("mañana", 6, 14), ("tarde", 14, 22))
#: Cambios de turno (h del día).
CAMBIOS_DE_TURNO = (6, 14, 22)


class Evento(NamedTuple):
    """Un evento del calendario de la corrida."""

    id: str            # "EVT-05"
    inicio: float      # minuto de la corrida
    fin: float         # minuto de la corrida (puede pasar el final)
    objetivo: str      # turno ("noche"), zona ("B"), "" si es toda la estación
    valor: float       # días de la licencia, etc. (según el evento)
    detalle: str       # texto corto para la tabla y el aviso


def probabilidad(id_: str, mes: int = 1) -> float:
    """Probabilidad por día del evento (del Registro); el corte de luz depende de la temporada."""
    if id_ == "EVT-07":
        verano, resto = valor("EVT-07")[:2]
        return verano if mes in (12, 1, 2) else resto
    if id_ in ("EVT-02", "EVT-04"):
        return valor("EVT-02")[0]
    return valor(id_)[0]


def _hora(minutos: float) -> str:
    m = int(round(minutos)) % MINUTOS_POR_DIA
    return f"{m // 60:02d}:{m % 60:02d}"


def _fin_de_turno(t: float) -> float:
    """El próximo cambio de turno después del minuto t."""
    dia = int(t // MINUTOS_POR_DIA)
    for h in (*CAMBIOS_DE_TURNO, 24 + CAMBIOS_DE_TURNO[0]):
        borde = dia * MINUTOS_POR_DIA + h * 60.0
        if borde > t:
            return borde
    return (dia + 1) * MINUTOS_POR_DIA + CAMBIOS_DE_TURNO[0] * 60.0


def _turno_de(t: float) -> str:
    h = (t % MINUTOS_POR_DIA) / 60.0
    if 6 <= h < 14:
        return "mañana"
    if 14 <= h < 22:
        return "tarde"
    return "noche"


def _entre(az: Aleatorio, stream: str, minimo: float, maximo: float) -> float:
    return minimo + az.uniforme(stream) * (maximo - minimo)


def _entero(az: Aleatorio, stream: str, minimo: int, maximo: int) -> int:
    return min(maximo, minimo + int(az.uniforme(stream) * (maximo - minimo + 1)))


def _turno_sorteado(az: Aleatorio, stream: str, p: ParametrosSimulacion) -> tuple[str, int, int]:
    """Un turno, con probabilidad proporcional a sus playeros (le pasa a una persona, no a un turno)."""
    i = az.discreta(tuple(float(n) for n in p.playeros_por_turno), stream)
    return TURNOS[i]


def calendario(p: ParametrosSimulacion) -> tuple[Evento, ...]:
    """Los eventos de la corrida, en orden de inicio (vacío si no hay ninguno prendido)."""
    ev = p.eventos
    if not ev.activos or not p.estacion_real:
        return ()
    az = Aleatorio(ev.semilla)
    inicio = date(ANO_REFERENCIA, *p.fecha_inicio)
    salida: list[Evento] = []
    caras = [(g.id, g.nombre) for g in p.grupos for _ in range(g.caras)]
    for d in range(p.dias):
        fecha = inicio + timedelta(days=d)
        t0 = d * MINUTOS_POR_DIA
        # Se sortean TODOS los eventos todos los días (cada uno con su stream) y después se filtran los
        # prendidos: así prender uno no corre las fechas de los demás.
        for tipo in CATALOGO:
            if tipo.id not in MECANISMO and tipo.id != "EVT-02":
                continue
            if tipo.id == "EVT-04":
                continue                      # sale de las licencias de EVT-02
            stream = f"evento_{tipo.id[-2:]}"
            if not az.bernoulli(min(1.0, probabilidad(tipo.id, fecha.month) * ev.frecuencia), stream):
                continue
            salida.extend(_eventos_del_dia(tipo.id, az, stream, p, t0, caras))
    elegidos = [e for e in salida if e.id in ev.activos]
    return tuple(sorted(elegidos, key=lambda e: (e.inicio, e.id)))


def _eventos_del_dia(id_: str, az: Aleatorio, stream: str, p: ParametrosSimulacion,
                     t0: float, caras: list[tuple[str, str]]) -> list[Evento]:
    """Los detalles de un evento que ocurre el día que arranca en t0."""
    if id_ == "EVT-01":
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        fin = _fin_de_turno(t)
        turno = _turno_de(t)
        return [Evento(id_, t, fin, turno, 0.0,
                       f"un playero del turno {turno} se va a las {_hora(t)}; vuelve a haber dotación completa "
                       f"a las {_hora(fin)}")]
    if id_ == "EVT-03":
        nombre, desde, hasta = _turno_sorteado(az, stream, p)
        return [Evento(id_, t0 + desde * 60.0, t0 + hasta * 60.0, nombre, 0.0,
                       f"el turno {nombre} arranca con un playero menos")]
    if id_ == "EVT-02":
        _, d_min, d_max, _, _ = valor("EVT-02")
        dias = _entero(az, stream, int(d_min), int(d_max))
        nombre, desde, hasta = _turno_sorteado(az, stream, p)
        sin_reemplazo = az.uniforme(stream) < valor("EVT-04")[0]
        id_real = "EVT-04" if sin_reemplazo else "EVT-02"
        texto = (f"un playero del turno {nombre} falta {dias} días: "
                 + ("nadie lo reemplaza, el turno queda corto" if sin_reemplazo
                    else "otro playero lo cubre con horas extra"))
        return [Evento(id_real, t0 + desde * 60.0, t0 + (dias - 1) * MINUTOS_POR_DIA + hasta * 60.0,
                       nombre, float(dias), texto)]
    if id_ == "EVT-05":
        zona, nombre = caras[min(len(caras) - 1, int(az.uniforme(stream) * len(caras)))]
        _, h_min, h_max, _ = valor("EVT-05")
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        horas = _entre(az, stream, h_min, h_max)
        return [Evento(id_, t, t + horas * 60.0, zona, horas,
                       f"una cara de la zona {zona} ({nombre.lower()}) queda fuera de servicio a las {_hora(t)} "
                       f"durante {horas:.1f} h")]
    if id_ == "EVT-06":
        _, h_min, h_max = valor("EVT-06")
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        horas = _entre(az, stream, h_min, h_max)
        return [Evento(id_, t, t + horas * 60.0, "C", horas,
                       f"un compresor de GNC se rompe a las {_hora(t)} durante {horas:.1f} h")]
    if id_ in ("EVT-07", "EVT-14"):
        h_min, h_max = valor(id_)[-2:]
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        horas = _entre(az, stream, h_min, h_max)
        que = "corte de luz" if id_ == "EVT-07" else "asalto"
        return [Evento(id_, t, t + horas * 60.0, "", horas,
                       f"{que} a las {_hora(t)}: la estación se para {horas * 60:.0f} min")]
    if id_ == "EVT-08":
        _, h_min, h_max, extra, factor = valor("EVT-08")
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        horas = _entre(az, stream, h_min, h_max)
        return [Evento(id_, t, t + horas * 60.0, "", horas,
                       f"se cae el cobro con tarjeta a las {_hora(t)} durante {horas:.1f} h: cada carga tarda "
                       f"{extra:g} min más y la caja × {factor:g}")]
    return []


class EventoOcurrido(NamedTuple):
    """Un evento con lo que le hizo a la estación (para la tabla "Eventos del período")."""

    id: str
    inicio: float
    fin: float
    objetivo: str
    valor: float
    detalle: str
    perdidos: int      # clientes que se fueron sin cargar mientras duraba
