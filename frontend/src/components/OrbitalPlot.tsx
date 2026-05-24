// Rysuje tor lotu w układzie inercjalnym (x, y) z centrum Ziemi w (0,0).
// UWAGA architektoniczna: komponent tylko prezentuje dane z TelemetryFrame —
// nie liczy żadnej fizyki. x, y płyną z silnika przez SimResult.telemetry.

import React, { useMemo } from 'react';
import type { TelemetryFrame, MissionEvent, OrbitVerdict } from '../types/contracts';

// Źródło: dt_contracts.constants.R_EARTH — NIE wpisuj własnej wartości.
const R_EARTH = 6_378_136.49; // m
// Źródło: dt_contracts.constants.MU — standardowy parametr grawitacyjny Ziemi
const MU = 3.986_004_418e14; // m³/s²

const SVG_W = 560;
const SVG_H = 560;
const PAD   = 0.12; // 12 % marginesu względem zakresu danych

// ---------------------------------------------------------------------------
// Mapowanie układu inercjalnego (dane) → piksele SVG.
// KRYTYCZNE: jednakowy zakres dla x i y → koła pozostają kołami.
// ---------------------------------------------------------------------------
interface Transform {
  toSvg: (dx: number, dy: number) => [number, number];
  earthR: number; // promień Ziemi w pikselach SVG
}

// Pełna elipsa orbitalna z elementów keplerowskich, orientacja z ostatniego frame'a.
// Zwraca tablicę [x,y] w metrach (układ inercjalny, środek Ziemi = (0,0)).
function computeOrbitEllipse(frame: TelemetryFrame, a: number, e: number): [number, number][] {
  const { x, y, vx, vy } = frame;
  const rMag = Math.sqrt(x * x + y * y);
  const h = x * vy - y * vx; // moment pędu na jednostkę masy (2D, skalar)

  // Wektor mimośrodu (kierunek ku perygeum)
  const ex = (vy * h) / MU - x / rMag;
  const ey = (-vx * h) / MU - y / rMag;
  const omega = Math.atan2(ey, ex); // argument perygeum

  const p = a * (1 - e * e); // semi-latus rectum
  const N = 200;
  const pts: [number, number][] = [];
  for (let i = 0; i <= N; i++) {
    const theta = (2 * Math.PI * i) / N;
    const r = p / (1 + e * Math.cos(theta));
    pts.push([r * Math.cos(theta + omega), r * Math.sin(theta + omega)]);
  }
  return pts;
}

function buildTransform(telemetry: TelemetryFrame[], extraPts: [number, number][] = []): Transform {
  // reduce zamiast spread, bo spread może rzucić stack-overflow przy 1500+ punktach
  let minX =  Infinity, maxX = -Infinity;
  let minY =  Infinity, maxY = -Infinity;
  for (const f of telemetry) {
    if (f.x < minX) minX = f.x;
    if (f.x > maxX) maxX = f.x;
    if (f.y < minY) minY = f.y;
    if (f.y > maxY) maxY = f.y;
  }
  for (const [px, py] of extraPts) {
    if (px < minX) minX = px;
    if (px > maxX) maxX = px;
    if (py < minY) minY = py;
    if (py > maxY) maxY = py;
  }
  // Uwzględnij kulo Ziemi
  minX = Math.min(minX, -R_EARTH);
  maxX = Math.max(maxX,  R_EARTH);
  minY = Math.min(minY, -R_EARTH);
  maxY = Math.max(maxY,  R_EARTH);

  const spanX = maxX - minX;
  const spanY = maxY - minY;
  // JEDNAKOWY zakres w x i y → aspect 1:1
  const span  = Math.max(spanX, spanY) * (1 + PAD);
  const cX    = (minX + maxX) / 2;
  const cY    = (minY + maxY) / 2;

  const dataLeft   = cX - span / 2;
  const dataBottom = cY - span / 2;

  const toSvg = (dx: number, dy: number): [number, number] => {
    const svgX = ((dx - dataLeft) / span) * SVG_W;
    // Odwrócenie osi Y: dane mają Y w górę, SVG ma Y w dół
    const svgY = SVG_H - ((dy - dataBottom) / span) * SVG_H;
    return [svgX, svgY];
  };

  const earthR = (R_EARTH / span) * SVG_W;

  return { toSvg, earthR };
}

// ---------------------------------------------------------------------------
// Etykiety zdarzeń (tylko te, które mają sens na mapie 2D)
// ---------------------------------------------------------------------------
const EVENT_META: Partial<Record<MissionEvent['kind'], { label: string; color: string; r: number }>> = {
  stage_separation:  { label: 'SEP',    color: '#ff9966', r: 3.5 },
  payload_separation:{ label: 'DEPLOY', color: '#ffd740', r: 3.5 },
  orbit_insertion:   { label: 'ORBIT',  color: '#00e676', r: 5.5 },
  apogee:            { label: 'APOGEE', color: '#00d4ff', r: 3.5 },
  impact:            { label: 'IMPACT', color: '#ff1744', r: 4.0 },
};

function closestFrame(telemetry: TelemetryFrame[], t: number): TelemetryFrame {
  return telemetry.reduce((best, f) =>
    Math.abs(f.t - t) < Math.abs(best.t - t) ? f : best, telemetry[0]);
}

// ---------------------------------------------------------------------------
// Komponent
// ---------------------------------------------------------------------------
interface Props {
  telemetry: TelemetryFrame[];
  events: MissionEvent[];
  verdict?: OrbitVerdict;
}

export default function OrbitalPlot({ telemetry, events, verdict }: Props) {
  const orbitEllipsePts = useMemo<[number, number][] | null>(() => {
    const el = verdict?.elements;
    if (!el || !verdict.reached_orbit || telemetry.length < 1) return null;
    const lastFrame = telemetry[telemetry.length - 1];
    return computeOrbitEllipse(lastFrame, el.semi_major_axis, el.eccentricity);
  }, [verdict, telemetry]);

  const transform = useMemo(
    () => (telemetry.length > 1 ? buildTransform(telemetry, orbitEllipsePts ?? []) : null),
    [telemetry, orbitEllipsePts],
  );

  // Dane dla widoku flat-Earth: dystans od startu (tangencjalny) vs. wysokość.
  const flatPts = useMemo(() => {
    const frames = telemetry.filter(f => f.phase === 'ascent' || f.phase === 'insertion');
    if (frames.length < 2) return null;
    const f0 = frames[0];
    const r0 = Math.sqrt(f0.x * f0.x + f0.y * f0.y);
    if (r0 === 0) return null;
    // wektor tangencjalny (prostopadle do radialnego w kierunku ruchu)
    const tx = -f0.y / r0;
    const ty =  f0.x / r0;
    return frames.map(f => ({
      downrange: (f.x - f0.x) * tx + (f.y - f0.y) * ty,
      altitude:  f.altitude,
      t:         f.t,
    }));
  }, [telemetry]);

  if (!transform) return null;
  const { toSvg, earthR } = transform;

  // Punkty trajektorii — LINIA, nie markery per-punkt
  const ascentPts = telemetry
    .filter(f => f.phase === 'ascent' || f.phase === 'insertion')
    .map(f => toSvg(f.x, f.y).join(','))
    .join(' ');

  const orbitPts = telemetry
    .filter(f => f.phase === 'orbit')
    .map(f => toSvg(f.x, f.y).join(','))
    .join(' ');

  const failedPts = telemetry
    .filter(f => f.phase === 'failed')
    .map(f => toSvg(f.x, f.y).join(','))
    .join(' ');

  // Kula Ziemi
  const [ecx, ecy] = toSvg(0, 0);

  // Punkt startu
  const [lx, ly] = toSvg(telemetry[0].x, telemetry[0].y);

  // Markery zdarzeń — TYLKO wybrane EventKind
  const markers = events
    .filter(ev => ev.kind in EVENT_META)
    .map(ev => {
      const meta = EVENT_META[ev.kind]!;
      const frame = closestFrame(telemetry, ev.t);
      const [sx, sy] = toSvg(frame.x, frame.y);
      return { ...meta, sx, sy, kind: ev.kind };
    });

  const hasOrbit  = orbitPts.length  > 0;
  const hasFailed = failedPts.length > 0;

  // Pełna elipsa orbitalna — jako string SVG points
  const ellipseSvgPts = orbitEllipsePts
    ? orbitEllipsePts.map(([px, py]) => toSvg(px, py).join(',')).join(' ')
    : null;

  // ── Widok flat-Earth — faza wznoszenia ──────────────────────────────────────
  const FGW = SVG_W;
  const FGH = 400;
  const FL = 52, FR = 12, FB = 52, FT = 16; // padding: left, right, bottom, top

  let flatToSvg: ((d: number, alt: number) => [number, number]) | null = null;
  let flatGroundY = FGH - FB;
  let flatTrajPts = '';
  let flatLx = FL, flatLy = flatGroundY;
  let flatMarkers: Array<{ sx: number; sy: number; r: number; color: string; label: string; kind: MissionEvent['kind'] }> = [];
  let flatGridLines: Array<{ y: number; label: string }> = [];

  if (flatPts) {
    let minD = Infinity, maxD = -Infinity, maxAlt = -Infinity;
    for (const p of flatPts) {
      if (p.downrange < minD) minD = p.downrange;
      if (p.downrange > maxD) maxD = p.downrange;
      if (p.altitude > maxAlt) maxAlt = p.altitude;
    }
    const xScale = (FGW - FL - FR) / Math.max(maxD - minD, 1);
    const xOff   = FL - minD * xScale;
    const yScale = (FGH - FB - FT) / Math.max(maxAlt, 1);
    flatGroundY  = FGH - FB;

    flatToSvg = (d: number, alt: number): [number, number] => [
      d * xScale + xOff,
      flatGroundY - alt * yScale,
    ];

    flatTrajPts = flatPts.map(p => flatToSvg!(p.downrange, p.altitude).join(',')).join(' ');
    [flatLx, flatLy] = flatToSvg(flatPts[0].downrange, flatPts[0].altitude);

    flatMarkers = events
      .filter(ev => ev.kind in EVENT_META)
      .map(ev => {
        const meta = EVENT_META[ev.kind]!;
        const frame = closestFrame(telemetry, ev.t);
        if (frame.phase !== 'ascent' && frame.phase !== 'insertion') return null;
        const fp = flatPts.reduce((best, p) =>
          Math.abs(p.t - ev.t) < Math.abs(best.t - ev.t) ? p : best, flatPts[0]);
        const [sx, sy] = flatToSvg!(fp.downrange, fp.altitude);
        return { ...meta, sx, sy, kind: ev.kind };
      })
      .filter((m): m is NonNullable<typeof m> => m !== null);

    const step = maxAlt > 800_000 ? 200_000 : maxAlt > 300_000 ? 100_000 : 50_000;
    for (let alt = step; alt < maxAlt * 1.05; alt += step) {
      const [, gy] = flatToSvg(0, alt);
      flatGridLines.push({ y: gy, label: `${Math.round(alt / 1000)} km` });
    }
  }

  return (
    <>
    <div className="chart-wrapper">
      <div className="chart-header">
        <h3 className="chart-title">Tor lotu — układ inercjalny (x, y)</h3>
        <span className="chart-unit-badge">ECI · środek Ziemi = (0, 0)</span>
      </div>

      <svg
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        style={{ width: '100%', maxHeight: SVG_H, display: 'block' }}
        aria-label="Tor lotu rakiety w układzie inercjalnym"
      >
        {/* Tło */}
        <rect width={SVG_W} height={SVG_H} fill="#070c17" rx="6" />

        {/* Siatka pomocnicza — linie przez środek Ziemi */}
        <line x1={ecx} y1={0} x2={ecx} y2={SVG_H} stroke="#0d1a2a" strokeWidth="1" />
        <line x1={0} y1={ecy} x2={SVG_W} y2={ecy} stroke="#0d1a2a" strokeWidth="1" />

        {/* Kula Ziemi */}
        <circle cx={ecx} cy={ecy} r={earthR} fill="#0a2040" stroke="#1a4a80" strokeWidth="1.5" />
        {/* Kontynenty — dekoracyjna sieć równoleżników (opcjonalna) */}
        <circle cx={ecx} cy={ecy} r={earthR * 0.66} fill="none" stroke="#112a50" strokeWidth="0.7" strokeDasharray="3 4" />
        <line
          x1={ecx - earthR * 0.9} y1={ecy}
          x2={ecx + earthR * 0.9} y2={ecy}
          stroke="#112a50" strokeWidth="0.7" strokeDasharray="3 4"
        />
        <text
          x={ecx} y={ecy + 4}
          textAnchor="middle"
          fill="#2a6aaa"
          fontSize={Math.max(10, earthR * 0.18)}
          fontWeight="700"
        >
          Ziemia
        </text>

        {/* Pełna elipsa orbitalna (analityczna z elementów keplerowskich) */}
        {ellipseSvgPts && (
          <polyline
            points={ellipseSvgPts}
            fill="none"
            stroke="#ffd740"
            strokeWidth="1.2"
            strokeLinejoin="round"
            strokeDasharray="6 4"
            opacity="0.65"
          />
        )}

        {/* Trajektoria wznoszenia / wstawienia */}
        {ascentPts && (
          <polyline
            points={ascentPts}
            fill="none"
            stroke="#00d4ff"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
        )}

        {/* Trajektoria orbitalna */}
        {hasOrbit && (
          <polyline
            points={orbitPts}
            fill="none"
            stroke="#00e676"
            strokeWidth="2.8"
            strokeLinejoin="round"
          />
        )}

        {/* Trajektoria nieudana */}
        {hasFailed && (
          <polyline
            points={failedPts}
            fill="none"
            stroke="#ff1744"
            strokeWidth="1.6"
            strokeLinejoin="round"
            strokeDasharray="5 3"
          />
        )}

        {/* Punkt startowy */}
        <circle cx={lx} cy={ly} r={4.5} fill="#ff6b35" />
        <text x={lx + 8} y={ly - 3} fill="#ff6b35" fontSize="9" fontWeight="700">LIFTOFF</text>

        {/* Markery zdarzeń */}
        {markers.map(({ sx, sy, r, color, label, kind }, i) => (
          <g key={`${kind}-${i}`}>
            <circle cx={sx} cy={sy} r={r} fill={color} />
            <text x={sx + r + 4} y={sy + 4} fill={color} fontSize="9" fontWeight="700">
              {label}
            </text>
          </g>
        ))}

        {/* Legenda */}
        <g transform={`translate(10, ${SVG_H - 82})`}>
          <rect x="-4" y="-8" width="182" height={ellipseSvgPts ? 90 : 74} fill="#070c17aa" rx="4" />
          <circle cx="8" cy="6" r="4.5" fill="#ff6b35" />
          <text x="17" y="10" fill="#6a8099" fontSize="9">Start</text>
          <line x1="0" y1="22" x2="18" y2="22" stroke="#00d4ff" strokeWidth="1.6" />
          <text x="22" y="26" fill="#6a8099" fontSize="9">Wznoszenie / wstawienie</text>
          {hasOrbit && (
            <>
              <line x1="0" y1="38" x2="18" y2="38" stroke="#00e676" strokeWidth="2.8" />
              <text x="22" y="42" fill="#6a8099" fontSize="9">Faza orbitalna</text>
            </>
          )}
          {hasFailed && (
            <>
              <line x1="0" y1="38" x2="18" y2="38" stroke="#ff1744" strokeWidth="1.6" strokeDasharray="4 3" />
              <text x="22" y="42" fill="#6a8099" fontSize="9">Nieudana (FAILED)</text>
            </>
          )}
          {ellipseSvgPts && (
            <>
              <line x1="0" y1="54" x2="18" y2="54" stroke="#ffd740" strokeWidth="1.2" strokeDasharray="5 3" opacity="0.65" />
              <text x="22" y="58" fill="#6a8099" fontSize="9">Elipsa orbitalna (kepler.)</text>
            </>
          )}
        </g>
      </svg>
    </div>

    {/* ── Widok flat-Earth: wysokość vs. dystans od startu ── */}
    {flatPts && flatToSvg && (
      <div className="chart-wrapper">
        <div className="chart-header">
          <h3 className="chart-title">Wznoszenie — przekrój boczny</h3>
          <span className="chart-unit-badge">dystans od startu vs. wysokość</span>
        </div>
        <svg
          viewBox={`0 0 ${FGW} ${FGH}`}
          style={{ width: '100%', maxHeight: FGH, display: 'block' }}
          aria-label="Faza wznoszenia — widok boczny"
        >
          {/* Tło */}
          <rect width={FGW} height={FGH} fill="#070c17" rx="6" />

          {/* Wypełnienie Ziemi */}
          <rect x="0" y={flatGroundY} width={FGW} height={FGH - flatGroundY} fill="#0a2040" />

          {/* Siatka wysokości */}
          {flatGridLines.map(({ y, label }) => (
            <g key={label}>
              <line x1={FL} y1={y} x2={FGW - FR} y2={y} stroke="#0d1a2a" strokeWidth="1" />
              <text x={FL - 6} y={y + 4} fill="#2a4060" fontSize="9" textAnchor="end">{label}</text>
            </g>
          ))}

          {/* Linia powierzchni Ziemi */}
          <line x1="0" y1={flatGroundY} x2={FGW} y2={flatGroundY} stroke="#1a4a80" strokeWidth="2.5" />
          <text x={FGW / 2} y={flatGroundY + 18} fill="#2a6aaa" fontSize="10" fontWeight="700" textAnchor="middle">ZIEMIA</text>

          {/* Trajektoria wznoszenia */}
          {flatTrajPts && (
            <polyline
              points={flatTrajPts}
              fill="none"
              stroke="#00d4ff"
              strokeWidth="2.4"
              strokeLinejoin="round"
            />
          )}

          {/* Start */}
          <circle cx={flatLx} cy={flatLy} r={5.5} fill="#ff6b35" />
          <text x={flatLx + 10} y={flatLy - 6} fill="#ff6b35" fontSize="11" fontWeight="700">LIFTOFF</text>

          {/* Markery zdarzeń */}
          {flatMarkers.map(({ sx, sy, r, color, label, kind }, i) => (
            <g key={`fe-${kind}-${i}`}>
              <circle cx={sx} cy={sy} r={r + 1.5} fill={color} />
              <text x={sx + r + 8} y={sy + 4} fill={color} fontSize="10" fontWeight="700">{label}</text>
            </g>
          ))}
        </svg>
      </div>
    )}
    </>
  );
}
