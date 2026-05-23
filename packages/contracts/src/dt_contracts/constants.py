"""Stale fizyczne i progi walidacji.

Wartosci pochodza ze Space Mission Analysis and Design (SMAD), 3rd ed.:
- stale Ziemi: Appendix B, Tab. B-2
- standardowe g0: Appendix F (Free fall standard)
- zakresy Isp i frakcje masowe: rozdzial 17 (Tab. 17-3/17-4, s. 712-714)
- progi orbitalne: rozdzial 7.3 + wykres 7-8

Te wartosci sa zrodlem prawdy dla calego projektu. Silnik fizyczny importuje
je stad, nie wpisuje wlasnych.
"""

from __future__ import annotations

from typing import Final

# --- Stale Ziemi (SMAD App. B, Tab. B-2) ---
MU_EARTH: Final[float] = 3.986_004_418e14      # [m^3/s^2] geocentryczna stala grawit. GM_E
R_EARTH: Final[float] = 6_378_136.49           # [m] promien rownikowy
M_EARTH: Final[float] = 5.9737e24              # [kg] masa Ziemi

# --- Standardowe przyspieszenie (SMAD App. F: Free fall standard) ---
G0: Final[float] = 9.806_65                    # [m/s^2] uzywane w definicji Isp

# --- Progi napedu (SMAD rozdz. 17) ---
# Najwyzszy sprawdzony w locie Isp chemiczny: ~446-455 s (LO2/LH2, RL10/SSME).
# Stad gorna granica dla napedu chemicznego wynoszacego z powierzchni.
ISP_MAX_CHEMICAL: Final[float] = 455.0         # [s] twardy gorny limit (chemiczny)
ISP_MIN: Final[float] = 1.0                    # [s] dolny rozsadny prog

# Frakcja masowa stopnia = m_propellant / (m_propellant + m_dry).
# SMAD: solid ~0.91-0.94, liquid ~0.85-0.93 (s. 712-714).
# Szeroki przedzial dopuszczalny; spoza niego -> ostrzezenie, nie blad.
STAGE_MASS_FRACTION_TYPICAL_MIN: Final[float] = 0.80
STAGE_MASS_FRACTION_TYPICAL_MAX: Final[float] = 0.95

# --- Progi orbitalne (SMAD rozdz. 7.3, wykres 7-8) ---
# Ponizej ~400 km Delta-v na podtrzymanie wysokosci silnie rosnie; minimalne
# perygeum dla stabilnej LEO przyjmujemy konserwatywnie.
MIN_PERIAPSIS_ALTITUDE: Final[float] = 200_000.0   # [m] min. wysokosc perygeum dla "orbity"
# Dopuszczalny mimosrod dla orbity uznanej za "kolowa/stabilna LEO".
MAX_ECCENTRICITY_LEO: Final[float] = 0.25

# Typowe straty grawitacyjne + aerodynamiczne (SMAD 7.3): 1500-2000 m/s.
# Pomocnicze przy szacowaniu budzetu Delta-v (nie jest to twarda granica).
TYPICAL_LAUNCH_LOSSES_DV: Final[float] = 1_750.0   # [m/s]
