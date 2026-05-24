"""Silnik fizyczny - czysta numeryka (NumPy/SciPy).

Publiczne API:
  simulate(RocketParams) -> SimResult  — oblicz trajektorie misji
  golden_preset() -> RocketParams      — trojstopniowa rakieta referencyjna
"""

from .engine import simulate
from .presets import golden_preset

__all__ = ["simulate", "golden_preset"]
