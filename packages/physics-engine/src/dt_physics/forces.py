"""Sily dzialajace na rakiete — czyste funkcje bez efektow ubocznych.

Kazda funkcja bierze skalary/wektory stanu i zwraca skladowe sily lub
przyspieszenia. Brak I/O, brak efektow ubocznych.
"""

from __future__ import annotations

import math

from dt_contracts.constants import G0, MU_EARTH, R_EARTH

from .atmosphere import air_density


def gravity_accel(x: float, y: float) -> tuple[float, float]:
    """Przyspieszenie grawitacyjne [m/s^2] w ukladzie inercjalnym.

    g(r) = -mu/r^2 * r_hat
    """
    r2 = x * x + y * y
    r = math.sqrt(r2)
    factor = -MU_EARTH / (r2 * r)
    return factor * x, factor * y


def drag_force(
    x: float,
    y: float,
    vx: float,
    vy: float,
    cd: float,
    area: float,
) -> tuple[float, float]:
    """Sila oporu aerodynamicznego [N].

    D = 0.5 * rho * v^2 * Cd * A, kierunek przeciwny do predkosci.
    """
    altitude = math.sqrt(x * x + y * y) - R_EARTH
    rho = air_density(altitude)
    v2 = vx * vx + vy * vy
    if v2 < 1e-12:
        return 0.0, 0.0
    v = math.sqrt(v2)
    d_mag = 0.5 * rho * v2 * cd * area
    return -d_mag * vx / v, -d_mag * vy / v


def thrust_vector(
    thrust: float,
    angle_rad: float,
) -> tuple[float, float]:
    """Wektor ciagu [N] — prosciej: kat od osi X (poziomej).

    angle_rad=pi/2 -> ciag pionowy (start).
    """
    return thrust * math.cos(angle_rad), thrust * math.sin(angle_rad)


def exhaust_velocity(isp: float) -> float:
    """Predkosc gazow wylotowych v_e = isp * g0 [m/s]."""
    return isp * G0


def drag_to_weight_ratio(
    x: float,
    y: float,
    vx: float,
    vy: float,
    cd: float,
    area: float,
    mass: float,
) -> float:
    """Stosunek D / (m*g) — uzywany jako kryterium wylaczenia oporu."""
    altitude = math.sqrt(x * x + y * y) - R_EARTH
    rho = air_density(altitude)
    v2 = vx * vx + vy * vy
    if v2 < 1e-12:
        return 0.0
    d_mag = 0.5 * rho * v2 * cd * area
    g_mag = MU_EARTH / (x * x + y * y)  # g(r) = mu/r^2
    return d_mag / (mass * g_mag)
