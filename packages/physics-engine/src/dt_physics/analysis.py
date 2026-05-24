"""Analiza orbity — werdykt keplerowski z wektora stanu.

Wzory wg PHYSICS_THEORY_BASE.md (slajdy astrodynamiki MIT 16.346, Lecture 1-2).
Stan 2D: [x, y, vx, vy] w ukladzie inercjalnym, srodek Ziemi = (0,0).

Kluczowe wzory:
  h = x*vy - y*vx          (moment pedu wlasciwy, skalar 2D)
  e_x = vy*h/mu - x/r      (Laplace vector, skladowa x)
  e_y = -vx*h/mu - y/r     (Laplace vector, skladowa y)
  e   = sqrt(e_x^2+e_y^2)  (mimosrod, bezwymiarowy)
  eps = v^2/2 - mu/r        (energia wlasciwa)
  a   = -mu/(2*eps)         (polowa wielka)
  r_p = p/(1+e) = a*(1-e)  (perygeum)

Test poprawnosci: orbita kolowa -> e MUSI wyjs 0 (< 1e-9).
"""

from __future__ import annotations

import math

from dt_contracts import OrbitalElements, OrbitVerdict
from dt_contracts.constants import MAX_ECCENTRICITY_LEO, MIN_PERIAPSIS_ALTITUDE, MU_EARTH, R_EARTH


def keplerian_elements(x: float, y: float, vx: float, vy: float) -> OrbitalElements:
    """Oblicz elementy keplerowskie z wektora stanu 2D.

    Wzory: PHYSICS_THEORY_BASE.md sekcja 1.
    """
    r = math.sqrt(x * x + y * y)
    v2 = vx * vx + vy * vy

    # Energia wlasciwa
    eps = 0.5 * v2 - MU_EARTH / r

    # Moment pedu wlasciwy (skalar 2D, moze byc ujemny dla CW)
    h = x * vy - y * vx

    # Wektor mimosrodu (Laplace vector) — PHYSICS_THEORY_BASE.md sekcja 1
    e_x = vy * h / MU_EARTH - x / r
    e_y = -vx * h / MU_EARTH - y / r
    e = math.sqrt(e_x * e_x + e_y * e_y)

    # Polowa wielka
    if abs(eps) < 1e-3:
        a = float("inf")
    else:
        a = -MU_EARTH / (2.0 * eps)

    # Parametr orbity
    p = h * h / MU_EARTH

    if eps < 0.0 and a > 0:
        r_p = a * (1.0 - e)
        r_a = a * (1.0 + e)
        periapsis_alt = r_p - R_EARTH
        apoapsis_alt = r_a - R_EARTH
        period: float | None = 2.0 * math.pi * math.sqrt(a**3 / MU_EARTH)
    else:
        # Orbita niezwiazana
        if e > 0:
            r_p = p / (1.0 + e)
        else:
            r_p = r
        periapsis_alt = r_p - R_EARTH
        apoapsis_alt = float("inf")
        period = None

    return OrbitalElements(
        semi_major_axis=a,
        eccentricity=e,
        periapsis_altitude=periapsis_alt,
        apoapsis_altitude=apoapsis_alt,
        specific_energy=eps,
        period=period,
    )


def orbit_verdict(elements: OrbitalElements) -> OrbitVerdict:
    """Werdykt: czy elementy keplerowskie spelniaja kryterium LEO."""
    eps = elements.specific_energy
    e = elements.eccentricity
    r_p_alt = elements.periapsis_altitude

    if eps >= 0.0:
        return OrbitVerdict(
            reached_orbit=False,
            reason=f"Orbita niezwiazana: eps={eps:.0f} J/kg >= 0.",
            elements=elements,
        )
    if r_p_alt < MIN_PERIAPSIS_ALTITUDE:
        return OrbitVerdict(
            reached_orbit=False,
            reason=(
                f"Perygeum zbyt niskie: {r_p_alt/1000:.1f} km "
                f"< {MIN_PERIAPSIS_ALTITUDE/1000:.0f} km."
            ),
            elements=elements,
        )
    if e > MAX_ECCENTRICITY_LEO:
        return OrbitVerdict(
            reached_orbit=False,
            reason=f"Mimosrod zbyt duzy: e={e:.4f} > {MAX_ECCENTRICITY_LEO}.",
            elements=elements,
        )

    return OrbitVerdict(
        reached_orbit=True,
        reason=(
            f"LEO osiagniete: eps={eps:.0f} J/kg, e={e:.4f}, "
            f"perygeum={r_p_alt/1000:.1f} km."
        ),
        elements=elements,
    )


def verdict_from_state(x: float, y: float, vx: float, vy: float) -> OrbitVerdict:
    """Skrot: werdykt bezposrednio z wektora stanu."""
    return orbit_verdict(keplerian_elements(x, y, vx, vy))
