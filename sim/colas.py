"""Las fórmulas de colas de la cátedra (M/M/1 y M/M/s), para compararlas con lo que da la simulación.

Notación de la cátedra: λ = tasa de llegadas · μ = tasa de servicio de UN servidor · s = servidores ·
ρ = λ / (s·μ) = utilización (tiene que ser < 1 para que la cola no crezca sin límite).

  Leyes de Little (valen siempre):   L = λ·W · Lq = λ·Wq · W = Wq + 1/μ · L = Lq + λ/μ
  M/M/1:   P0 = 1 − ρ · L = λ/(μ − λ) · Lq = ρ²/(1 − ρ) · W = 1/(μ − λ) · Wq = ρ/(μ − λ)
  M/M/s:   P0 = 1 / [ Σ(n=0..s−1) (λ/μ)ⁿ/n! + (λ/μ)ˢ / (s!·(1 − ρ)) ]
           Lq = P0·(λ/μ)ˢ·ρ / (s!·(1 − ρ)²) · Wq = Lq/λ · W = Wq + 1/μ · L = λ·W
  Costos:  C = s·Cs + Cw·L

Las tasas van en la misma unidad de tiempo (en la app, por hora). Este módulo no importa Streamlit.
"""

from __future__ import annotations

import math
from typing import NamedTuple


class ResultadoColas(NamedTuple):
    """Lo que dan las fórmulas para un sistema M/M/s (s = 1 es el M/M/1)."""

    rho: float        # utilización ρ = λ/(s·μ)
    p0: float         # probabilidad de que no haya nadie en el sistema
    lq: float         # clientes promedio en la cola
    l: float          # clientes promedio en el sistema
    wq: float         # tiempo promedio en la cola (unidad de las tasas)
    w: float          # tiempo promedio en el sistema


def mms(lam: float, mu: float, s: int = 1) -> ResultadoColas:
    """M/M/s con las fórmulas de la cátedra. Si ρ ≥ 1 no hay régimen estable y se levanta ValueError."""
    if lam <= 0 or mu <= 0 or s < 1:
        raise ValueError("λ y μ tienen que ser positivos y s ≥ 1.")
    rho = lam / (s * mu)
    if rho >= 1:
        raise ValueError("ρ ≥ 1: la cola crece sin límite (no hay régimen estable).")
    a = lam / mu
    p0 = 1.0 / (sum(a ** n / math.factorial(n) for n in range(s)) + a ** s / (math.factorial(s) * (1 - rho)))
    lq = p0 * a ** s * rho / (math.factorial(s) * (1 - rho) ** 2)
    wq = lq / lam
    w = wq + 1.0 / mu
    return ResultadoColas(rho=rho, p0=p0, lq=lq, l=lam * w, wq=wq, w=w)


def costo_total(s: int, costo_servidor: float, costo_espera: float, l: float) -> float:
    """C = s·Cs + Cw·L (costo por unidad de tiempo)."""
    return s * costo_servidor + costo_espera * l
