// Default two-stage rocket preset that reaches LEO.
// Calculated delta-v budget (Tsiolkovsky per stage):
//   Stage 1: ~3275 m/s  Stage 2: ~9595 m/s  Total: ~12870 m/s
//   Minus losses ~1750 m/s → effective ~11120 m/s > 9300 m/s required.
// Parameter values are within SMAD chapter 17 bounds (dt_contracts.constants).

import type { RocketParams } from '../types/contracts';

export const DEFAULT_PRESET: RocketParams = {
  stages: [
    {
      name: 'Stopień I – kerozyna/LOX',
      dry_mass: 5_000,      // kg
      thrust: 1_500_000,    // N  (1.5 MN)
      isp: 290,             // s  — sea-level kerosene/LOX (Merlin class)
      burn_time: 120,       // s
      drag_coefficient: 0.4,
      reference_area: 3.14, // m²
    },
    {
      name: 'Stopień II – LOX/LH2',
      dry_mass: 1_500,      // kg
      thrust: 200_000,      // N  (200 kN)
      isp: 360,             // s  — vacuum LOX/LH2
      burn_time: 400,       // s
      drag_coefficient: 0.3,
      reference_area: 2.0,  // m²
    },
  ],
  payload: {
    mass: 100,              // kg
    name: 'MicroSat-1',
  },
  launch_angle_deg: 90.0,
};
