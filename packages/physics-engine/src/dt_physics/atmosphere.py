"""Model atmosfery — gestosc powietrza rho(h) i predkosc dzwiekowa.

Uproszczony model eksponencjalny warstwowy (wystarczajacy dla lotu 0-200 km).
Czyste funkcje bez efektow ubocznych.
"""

from __future__ import annotations

import math

# Parametry warstw atmosfery (wysokosc [m], gęstość [kg/m^3], skala [m])
_LAYERS: list[tuple[float, float, float]] = [
    (0.0,      1.225,    8_500.0),   # troposfera / dolna atmosfera
    (11_000.0, 0.3639,   6_340.0),   # niższa stratosfera
    (25_000.0, 0.0401,   7_000.0),   # wyższa stratosfera
    (47_000.0, 0.001476, 8_000.0),   # mezosfera dolna
    (70_000.0, 0.0000530, 9_000.0),  # mezosfera górna
    (86_000.0, 0.0000064, 7_200.0),  # termosfera
]


def air_density(altitude: float) -> float:
    """Gestosc powietrza [kg/m^3] jako funkcja wysokosci nad powierzchnia [m].

    Ponizej 0 m traktuje jak poziom morza. Powyzej 200 km zwraca 0.
    """
    if altitude <= 0.0:
        return _LAYERS[0][1]
    if altitude >= 200_000.0:
        return 0.0

    layer_rho0, layer_H = _LAYERS[0][1], _LAYERS[0][2]
    for i in range(len(_LAYERS) - 1):
        h_bot, rho_bot, H = _LAYERS[i]
        h_top = _LAYERS[i + 1][0]
        if altitude <= h_top:
            return rho_bot * math.exp(-(altitude - h_bot) / H)
        layer_rho0 = _LAYERS[i + 1][1]
        layer_H = _LAYERS[i + 1][2]

    # Ostatnia warstwa (>=86 km)
    h_bot = _LAYERS[-1][0]
    rho_bot = _LAYERS[-1][1]
    H = _LAYERS[-1][2]
    return rho_bot * math.exp(-(altitude - h_bot) / H)


def dynamic_pressure(altitude: float, speed: float) -> float:
    """Cisnienie dynamiczne Q = 0.5 * rho * v^2 [Pa]."""
    return 0.5 * air_density(altitude) * speed * speed
