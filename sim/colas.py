"""Colas como en el ejercicio 2 del parcial: con λ, μ, s y la espera en la cola, las leyes de Little dan el resto.

Notación de la cátedra: λ = clientes que llegan por hora · μ = clientes que atiende un servidor por hora ·
s = servidores (acá, los playeros) · Wq = tiempo promedio en la cola.

  ρ = λ ÷ (s·μ)      utilización: qué parte del tiempo están ocupados los servidores
  W = Wq + 1/μ       tiempo promedio en el sistema (esperar + ser atendido)
  Lq = λ·Wq          clientes promedio en la cola
  L = λ·W            clientes promedio en el sistema

Las tasas van por hora y los tiempos en minutos (se pasan a horas adentro). Este módulo no importa Streamlit.
"""

from __future__ import annotations

from typing import NamedTuple


class Colas(NamedTuple):
    """Lo que dan las leyes de Little para una hora de la estación."""

    lam: float        # λ, clientes por hora
    mu: float         # μ, clientes por hora que atiende UN servidor
    s: int            # servidores
    rho: float        # utilización
    wq: float         # minutos en la cola (dato)
    w: float          # minutos en el sistema
    lq: float         # clientes en la cola
    l: float          # clientes en el sistema


def con_little(lam: float, atencion_min: float, s: int, wq_min: float) -> Colas:
    """ρ, W, Lq y L a partir de λ (por hora), el tiempo de atención (min), los servidores y la espera Wq (min)."""
    mu = 60.0 / atencion_min
    w = wq_min + atencion_min
    return Colas(lam=lam, mu=mu, s=s, rho=lam / (s * mu), wq=wq_min, w=w, lq=lam * wq_min / 60.0, l=lam * w / 60.0)
