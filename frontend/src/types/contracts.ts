// Mirrors Python dt_contracts — source of truth is the Python package.
// Replace with generated types from OpenAPI once the API exposes the schema.

export type Phase = 'ascent' | 'insertion' | 'orbit' | 'failed';

export type EventKind =
  | 'liftoff'
  | 'max_q'
  | 'stage_burnout'
  | 'stage_separation'
  | 'drag_negligible'
  | 'payload_separation'
  | 'orbit_insertion'
  | 'apogee'
  | 'impact';

export interface Stage {
  name: string;
  dry_mass: number;        // kg
  thrust: number;          // N
  isp: number;             // s
  burn_time: number;       // s
  drag_coefficient: number;
  reference_area: number;  // m²
  // computed fields returned by API (read-only):
  mass_flow?: number;
  propellant_mass?: number;
  total_impulse?: number;
  wet_mass?: number;
  mass_fraction?: number;
}

export interface Payload {
  mass: number;  // kg
  name: string;
}

export interface RocketParams {
  stages: Stage[];
  payload: Payload;
  launch_angle_deg: number;  // deg [0, 90]
  liftoff_mass?: number;     // kg, computed
}

export interface SimRequest {
  rocket: RocketParams;
  include_telemetry: boolean;
  max_flight_time: number;   // s
}

export interface TelemetryFrame {
  t: number;                // s
  x: number;                // m
  y: number;                // m
  vx: number;               // m/s
  vy: number;               // m/s
  mass: number;             // kg
  altitude: number;         // m
  speed: number;            // m/s
  dynamic_pressure: number; // Pa
  acceleration: number;     // m/s²
  phase: Phase;
  active_stage: number;
}

export interface MissionEvent {
  kind: EventKind;
  t: number;        // s
  altitude: number; // m
  speed: number;    // m/s
  note: string;
}

export interface OrbitalElements {
  semi_major_axis: number;     // m
  eccentricity: number;
  periapsis_altitude: number;  // m
  apoapsis_altitude: number;   // m
  specific_energy: number;     // J/kg
  period: number | null;       // s
}

export interface OrbitVerdict {
  reached_orbit: boolean;
  reason: string;
  elements: OrbitalElements | null;
}

export interface SimResult {
  verdict: OrbitVerdict;
  events: MissionEvent[];
  final_phase: Phase;
  max_altitude: number;          // m
  max_dynamic_pressure: number;  // Pa
  flight_time: number;           // s
  telemetry: TelemetryFrame[];
}

// Full response shape from GET /capabilities (dt_api.routes.CapabilitiesResponse)
export interface CapabilitiesResponse {
  contract_version: string;
  engine_available: boolean;
  ai_available: boolean;
  api_version: string;
}

// Backward-compat alias used internally before full type was known
export type Capabilities = CapabilitiesResponse;
