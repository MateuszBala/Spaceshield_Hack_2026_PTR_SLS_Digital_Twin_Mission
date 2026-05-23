import React from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import type { TelemetryFrame, MissionEvent } from '../types/contracts';

interface Props {
  telemetry: TelemetryFrame[];
  events: MissionEvent[];
}

interface ChartPoint {
  t: number;
  alt: number;   // km
  speed: number; // km/s
}

const EVENT_LABELS: Partial<Record<MissionEvent['kind'], string>> = {
  liftoff: 'Start',
  max_q: 'Max-Q',
  stage_burnout: 'Wypal.',
  stage_separation: 'Sep.',
  orbit_insertion: 'Orbita',
  impact: 'Upadek',
};

const ACCENT_ALT = '#00d4ff';
const ACCENT_SPEED = '#ff6b35';

export default function TrajectoryChart({ telemetry, events }: Props) {
  if (telemetry.length === 0) return null;

  const data: ChartPoint[] = telemetry.map(f => ({
    t: Math.round(f.t),
    alt: parseFloat((f.altitude / 1000).toFixed(2)),
    speed: parseFloat((f.speed / 1000).toFixed(3)),
  }));

  // Deduplicate by t (keep last frame for each second)
  const deduped = data.filter((d, i) => i === data.length - 1 || d.t !== data[i + 1].t);

  // Events to mark (exclude liftoff — it's at t=0, always visible)
  const refEvents = events.filter(e => e.kind !== 'liftoff' && EVENT_LABELS[e.kind]);

  return (
    <div className="chart-wrapper">
      <h3 className="chart-title">Trajektoria 2D — wysokość i prędkość</h3>
      <ResponsiveContainer width="100%" height={340}>
        <ComposedChart data={deduped} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2a3a" />
          <XAxis
            dataKey="t"
            label={{ value: 'Czas [s]', position: 'insideBottom', offset: -4, fill: '#8899aa' }}
            tick={{ fill: '#8899aa', fontSize: 11 }}
          />
          <YAxis
            yAxisId="alt"
            label={{ value: 'Wys. [km]', angle: -90, position: 'insideLeft', offset: 12, fill: ACCENT_ALT }}
            tick={{ fill: ACCENT_ALT, fontSize: 11 }}
          />
          <YAxis
            yAxisId="speed"
            orientation="right"
            label={{ value: 'Prędkość [km/s]', angle: 90, position: 'insideRight', offset: 12, fill: ACCENT_SPEED }}
            tick={{ fill: ACCENT_SPEED, fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ background: '#0d1520', border: '1px solid #1e2a3a', borderRadius: 6 }}
            labelStyle={{ color: '#8899aa' }}
            formatter={(value: number, name: string) => [
              name === 'Wysokość' ? `${value} km` : `${value} km/s`,
              name,
            ]}
          />
          <Legend wrapperStyle={{ color: '#8899aa', fontSize: 12 }} />

          {refEvents.map(ev => (
            <ReferenceLine
              key={`${ev.kind}-${ev.t}`}
              yAxisId="alt"
              x={Math.round(ev.t)}
              stroke="#2a3a50"
              strokeDasharray="4 2"
              label={{ value: EVENT_LABELS[ev.kind] ?? '', fill: '#445566', fontSize: 10, position: 'top' }}
            />
          ))}

          <Line
            yAxisId="alt"
            type="monotone"
            dataKey="alt"
            name="Wysokość"
            stroke={ACCENT_ALT}
            dot={false}
            strokeWidth={2}
          />
          <Line
            yAxisId="speed"
            type="monotone"
            dataKey="speed"
            name="Prędkość"
            stroke={ACCENT_SPEED}
            dot={false}
            strokeWidth={2}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
