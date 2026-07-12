// Synthetic SimResult generator — used when the real API is unreachable.
// Estimates delta-v using Tsiolkovsky per stage (same formula as the engine).
// Verdict changes when the user edits parameters — the Digital Twin loop works
// even without a running backend.

import type {
  RocketParams,
  SimResult,
  TelemetryFrame,
  MissionEvent,
  OrbitalElements,
  Phase,
} from '../types/contracts';
import type { Language } from '../i18n';

const G0 = 9.806_65;              // m/s²  — dt_contracts.constants.G0
const R_EARTH = 6_378_136.49;     // m     — dt_contracts.constants.R_EARTH
const MU_EARTH = 3.986_004_418e14;// m³/s² — dt_contracts.constants.MU_EARTH
const REQUIRED_DV = 9_300;        // m/s   — approximate for LEO 200 km
const LOSSES = 1_750;             // m/s   — dt_contracts.constants.TYPICAL_LAUNCH_LOSSES_DV
const LEO_ALT = 250_000;          // m     — target orbital altitude (synthetic)

// --- Physics helpers ---

function massFlow(thrust: number, isp: number): number {
  return thrust / (isp * G0);
}

function propellantMass(thrust: number, isp: number, burnTime: number): number {
  return massFlow(thrust, isp) * burnTime;
}

function wetMass(stage: RocketParams['stages'][number]): number {
  return stage.dry_mass + propellantMass(stage.thrust, stage.isp, stage.burn_time);
}

// Tsiolkovsky delta-v for the full multi-stage stack.
export function estimateDeltaV(rocket: RocketParams): number {
  const { stages, payload } = rocket;
  const n = stages.length;

  // massAbove[i] = total mass of stages i+1..n-1 + payload
  const massAbove: number[] = new Array(n).fill(0);
  massAbove[n - 1] = payload.mass;
  for (let i = n - 2; i >= 0; i--) {
    massAbove[i] = massAbove[i + 1] + wetMass(stages[i + 1]);
  }

  let totalDv = 0;
  for (let i = 0; i < n; i++) {
    const s = stages[i];
    const prop = propellantMass(s.thrust, s.isp, s.burn_time);
    const mInit = s.dry_mass + prop + massAbove[i];
    const mFinal = s.dry_mass + massAbove[i]; // after burn, before sep
    if (mFinal <= 0 || mInit <= mFinal) continue;
    totalDv += s.isp * G0 * Math.log(mInit / mFinal);
  }
  return totalDv;
}

// --- Telemetry generation ---

interface BurnSegment {
  t0: number;
  t1: number;
  stageIdx: number;
}

function buildSegments(rocket: RocketParams): BurnSegment[] {
  const segs: BurnSegment[] = [];
  let t = 0;
  for (let i = 0; i < rocket.stages.length; i++) {
    const bt = rocket.stages[i].burn_time;
    segs.push({ t0: t, t1: t + bt, stageIdx: i });
    t += bt;
    if (i < rocket.stages.length - 1) t += 10; // 10 s coast between stages
  }
  return segs;
}

function totalMission(segs: BurnSegment[], extra = 0): number {
  return segs[segs.length - 1].t1 + extra;
}

function massAt(t: number, rocket: RocketParams, segs: BurnSegment[]): number {
  let m = rocket.payload.mass + rocket.stages.reduce((acc, s) => acc + wetMass(s), 0);
  for (const seg of segs) {
    if (t <= seg.t0) break;
    const burned = massFlow(rocket.stages[seg.stageIdx].thrust, rocket.stages[seg.stageIdx].isp)
      * Math.min(t - seg.t0, seg.t1 - seg.t0);
    m -= burned;
    // Jettison dry mass after burnout
    if (t > seg.t1) m -= rocket.stages[seg.stageIdx].dry_mass;
  }
  return Math.max(rocket.payload.mass, m);
}

function activeStageAt(t: number, segs: BurnSegment[]): number {
  for (const seg of segs) {
    if (t <= seg.t1) return seg.stageIdx;
  }
  return segs[segs.length - 1].stageIdx;
}

function phaseAt(t: number, totalTime: number, reachesOrbit: boolean): Phase {
  const norm = t / totalTime;
  if (!reachesOrbit && norm > 0.75) return 'failed';
  if (norm < 0.55) return 'ascent';
  if (norm < 0.95) return 'insertion';
  return reachesOrbit ? 'orbit' : 'failed';
}

// S-curve easing (smooth rise from 0 to 1)
function sCurve(x: number): number {
  const c = Math.max(0, Math.min(1, x));
  return c * c * (3 - 2 * c);
}

function generateTelemetry(
  rocket: RocketParams,
  segs: BurnSegment[],
  reachesOrbit: boolean,
): TelemetryFrame[] {
  const frames: TelemetryFrame[] = [];
  const flightTime = totalMission(segs, reachesOrbit ? 30 : 0);
  const targetAlt = reachesOrbit ? LEO_ALT : LEO_ALT * 0.35;
  const orbitalSpeed = Math.sqrt(MU_EARTH / (R_EARTH + LEO_ALT)); // ~7756 m/s
  const N = 160;

  for (let i = 0; i < N; i++) {
    const t = (i / (N - 1)) * flightTime;
    const norm = t / flightTime;

    // Altitude profile
    let altitude: number;
    if (reachesOrbit) {
      altitude = targetAlt * sCurve(norm * 1.05);
    } else {
      // parabolic: rises then falls back
      altitude = Math.max(0, targetAlt * 4 * norm * (1 - norm) * 1.05);
    }

    // Speed profile
    let speed: number;
    if (reachesOrbit) {
      speed = orbitalSpeed * sCurve(norm * 1.08);
    } else {
      speed = orbitalSpeed * 0.42 * Math.sin(Math.PI * Math.min(1, norm / 0.75));
    }

    // Cartesian position (inertial, Earth center at origin)
    // Gravity turn: launch vertical, then curve east
    const turnAngle = norm * (reachesOrbit ? Math.PI * 0.22 : Math.PI * 0.08);
    const r = R_EARTH + altitude;
    const x = r * Math.sin(turnAngle);
    const y = r * Math.cos(turnAngle);

    // Velocity components (tangential + radial mix)
    const vx = speed * Math.cos(turnAngle);
    const vy = -speed * Math.sin(turnAngle) * 0.3; // mostly tangential

    // Atmospheric density → dynamic pressure
    const rho = altitude < 80_000 ? 1.225 * Math.exp(-altitude / 8_500) : 0;
    const dynQ = 0.5 * rho * speed * speed;

    // Mass
    const mass = massAt(t, rocket, segs);

    // Acceleration (thrust/mass during burns)
    const activeIdx = activeStageAt(t, segs);
    const activeSeg = segs.find(s => s.stageIdx === activeIdx && t >= s.t0 && t <= s.t1);
    const thrustNow = activeSeg ? rocket.stages[activeIdx].thrust : 0;
    const acc = thrustNow > 0 ? thrustNow / mass : 0;

    frames.push({
      t, x, y, vx, vy, mass,
      altitude,
      speed,
      dynamic_pressure: dynQ,
      acceleration: acc,
      phase: phaseAt(t, flightTime, reachesOrbit),
      active_stage: activeStageAt(t, segs),
    });
  }
  return frames;
}

// --- Event list ---

function buildEvents(
  rocket: RocketParams,
  segs: BurnSegment[],
  frames: TelemetryFrame[],
  reachesOrbit: boolean,
  lang: Language,
): MissionEvent[] {
  const isEn = lang === 'en';
  const events: MissionEvent[] = [];
  const frameAt = (t: number): TelemetryFrame => frames.reduce((best, f) =>
    Math.abs(f.t - t) < Math.abs(best.t - t) ? f : best, frames[0]);

  // Liftoff
  events.push({ kind: 'liftoff', t: 0, altitude: 0, speed: 0, note: isEn ? 'Launch' : 'Start' });

  // Max-Q: approximate at ~30s into flight
  const maxQ = frames.reduce((b, f) => f.dynamic_pressure > b.dynamic_pressure ? f : b, frames[0]);
  events.push({ kind: 'max_q', t: maxQ.t, altitude: maxQ.altitude, speed: maxQ.speed, note: 'Max-Q' });

  // Stage events
  for (const seg of segs) {
    const bf = frameAt(seg.t1);
    events.push({
      kind: 'stage_burnout',
      t: seg.t1,
      altitude: bf.altitude,
      speed: bf.speed,
      note: isEn ? `Stage ${seg.stageIdx + 1} burnout` : `Wypalenie stopnia ${seg.stageIdx + 1}`,
    });
    if (seg.stageIdx < rocket.stages.length - 1) {
      events.push({
        kind: 'stage_separation',
        t: seg.t1 + 1,
        altitude: bf.altitude,
        speed: bf.speed,
        note: isEn ? `Stage ${seg.stageIdx + 1} separation` : `Separacja stopnia ${seg.stageIdx + 1}`,
      });
    }
  }

  // Final events (only when orbit reached)
  if (reachesOrbit) {
    const lastSeg = segs[segs.length - 1];
    const ef = frameAt(lastSeg.t1 + 15);
    events.push({
      kind: 'payload_separation',
      t: lastSeg.t1 + 20,
      altitude: ef.altitude,
      speed: ef.speed,
      note: isEn ? 'Payload separation' : 'Separacja ladunku',
    });
    events.push({
      kind: 'orbit_insertion',
      t: lastSeg.t1 + 25,
      altitude: ef.altitude,
      speed: ef.speed,
      note: isEn ? 'Orbit insertion' : 'Wstawienie na orbite',
    });
  } else {
    // Impact/apogee for failed mission
    const apogeeFrame = frames.reduce((b, f) => f.altitude > b.altitude ? f : b, frames[0]);
    events.push({
      kind: 'apogee',
      t: apogeeFrame.t,
      altitude: apogeeFrame.altitude,
      speed: apogeeFrame.speed,
      note: isEn ? 'Apogee (failed mission)' : 'Apogeum (misja nieudana)',
    });
  }

  return events.sort((a, b) => a.t - b.t);
}

// --- Main entry point ---

export function generateSyntheticResult(rocket: RocketParams, lang: Language = 'pl'): SimResult {
  const isEn = lang === 'en';
  const dv = estimateDeltaV(rocket);
  const effectiveDv = dv - LOSSES;
  const reachesOrbit = effectiveDv >= REQUIRED_DV;

  const segs = buildSegments(rocket);
  const telemetry = generateTelemetry(rocket, segs, reachesOrbit);
  const events = buildEvents(rocket, segs, telemetry, reachesOrbit, lang);

  const maxAlt = Math.max(...telemetry.map(f => f.altitude));
  const maxQ = Math.max(...telemetry.map(f => f.dynamic_pressure));
  const flightTime = telemetry[telemetry.length - 1].t;

  let elements: OrbitalElements | null = null;
  let reason: string;

  if (reachesOrbit) {
    const a = R_EARTH + LEO_ALT;
    const e = 0.004;  // near-circular
    elements = {
      semi_major_axis: a,
      eccentricity: e,
      periapsis_altitude: a * (1 - e) - R_EARTH,
      apoapsis_altitude: a * (1 + e) - R_EARTH,
      specific_energy: -MU_EARTH / (2 * a),
      period: 2 * Math.PI * Math.sqrt(a ** 3 / MU_EARTH),
    };
    reason = isEn
      ? `Orbit achieved. Effective Delta-v ${(effectiveDv / 1000).toFixed(1)} km/s >= required ${(REQUIRED_DV / 1000).toFixed(1)} km/s.`
      : `Orbita osiagnieta. Delta-v efektywne ${(effectiveDv / 1000).toFixed(1)} km/s >= wymagane ${(REQUIRED_DV / 1000).toFixed(1)} km/s.`;
  } else if (effectiveDv < 0) {
    reason = isEn
      ? `Thrust too low - the rocket cannot ascend. Effective Delta-v: ${(effectiveDv / 1000).toFixed(1)} km/s.`
      : `Za maly ciag - rakieta nie wznosi sie. Delta-v efektywne: ${(effectiveDv / 1000).toFixed(1)} km/s.`;
  } else {
    const deficit = REQUIRED_DV - effectiveDv;
    reason = isEn
      ? `Delta-v deficit: ${(deficit / 1000).toFixed(1)} km/s. Max altitude reached: ${(maxAlt / 1000).toFixed(0)} km. Required Delta-v (after losses): >= ${(REQUIRED_DV / 1000).toFixed(1)} km/s.`
      : `Niedobor Delta-v: ${(deficit / 1000).toFixed(1)} km/s. Osiagnieto max ${(maxAlt / 1000).toFixed(0)} km. Wymagane Delta-v (po stratach): >= ${(REQUIRED_DV / 1000).toFixed(1)} km/s.`;
  }

  return {
    verdict: {
      reached_orbit: reachesOrbit,
      reason,
      elements,
    },
    events,
    final_phase: reachesOrbit ? 'orbit' : 'failed',
    max_altitude: maxAlt,
    max_dynamic_pressure: maxQ,
    flight_time: flightTime,
    telemetry,
  };
}
