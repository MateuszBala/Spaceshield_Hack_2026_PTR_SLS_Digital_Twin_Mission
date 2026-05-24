// Złoty preset rakiety — trójstopniowa, payload 150 kg, start pionowy.
// Wartości z docs/tasks/GOLDEN_PRESET.md (zweryfikowane: Δv ideal ≈ 13 846 m/s,
// masa startowa ≈ 39 304 kg, wszystkie frakcje masowe w zakresie SMAD 0.80–0.95).
// Zweryfikowany wynik silnika: orbita ~1544 km (perygeum ~1509 km, e=0.0044).
// Pola wejściowe kontraktu Stage — computed_field (paliwo, frakcja, ṁ) liczy UI.

import type { RocketParams } from '../types/contracts';

export const DEFAULT_PRESET: RocketParams = {
  stages: [
    {
      name: 'S1-core',
      dry_mass: 3_000,       // kg
      thrust: 780_000,       // N   — kerolox-podobny
      isp: 282,              // s
      burn_time: 105,        // s   → propellant ≈ 29 615 kg, mf ≈ 0.908
      drag_coefficient: 0.30,
      reference_area: 3.0,   // m²
    },
    {
      name: 'S2',
      dry_mass: 700,         // kg
      thrust: 145_000,       // N
      isp: 345,              // s
      burn_time: 120,        // s   → propellant ≈ 5 143 kg, mf ≈ 0.880
      drag_coefficient: 0.25,
      reference_area: 1.2,   // m²
    },
    {
      name: 'S3-upper',
      dry_mass: 120,         // kg
      thrust: 22_000,        // N   — LO2/LH2-podobny
      isp: 448,              // s   (< ISP_MAX_CHEMICAL=455 s)
      burn_time: 115,        // s   → propellant ≈ 576 kg, mf ≈ 0.828
      drag_coefficient: 0.22,
      reference_area: 0.8,   // m²
    },
  ],
  payload: {
    mass: 150,               // kg
    name: 'sat-150',
  },
  launch_angle_deg: 90.0,
};
