// Generic chart for any numeric field of TelemetryFrame vs time.
// Parametrize with `field` and optional `transform` to avoid hard-coding
// per-field charts. When new fields arrive from the engine (e.g. thrust),
// add another instance — no code changes needed here.

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import type { TelemetryFrame, MissionEvent } from '../types/contracts';

interface Props {
  telemetry: TelemetryFrame[];
  field: keyof TelemetryFrame;
  label: string;
  unit: string;
  color?: string;
  transform?: (raw: number) => number;
  events?: MissionEvent[];
  height?: number;
}

const EVENT_MARKS: Partial<Record<MissionEvent['kind'], string>> = {
  stage_burnout:   '●',
  stage_separation:'↑',
  orbit_insertion: '★',
  max_q:           'Q',
};

export default function TelemetryFieldChart({
  telemetry,
  field,
  label,
  unit,
  color = '#00d4ff',
  transform,
  events = [],
  height = 200,
}: Props) {
  if (telemetry.length === 0) return null;

  const data = telemetry.map(f => {
    const raw = f[field] as number;
    return { t: Math.round(f.t), value: parseFloat((transform ? transform(raw) : raw).toFixed(3)) };
  });

  // Deduplicate by t
  const deduped = data.filter((d, i) => i === data.length - 1 || d.t !== data[i + 1].t);

  const markedEvents = events.filter(e => EVENT_MARKS[e.kind]);

  return (
    <div className="chart-wrapper">
      <div className="chart-header">
        <h3 className="chart-title">{label}</h3>
        <span className="chart-unit-badge">{unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={deduped} margin={{ top: 6, right: 20, left: 0, bottom: 6 }}>
          <defs>
            <linearGradient id={`grad-${field}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2840" />
          <XAxis
            dataKey="t"
            tick={{ fill: '#6a8099', fontSize: 10 }}
            label={{ value: 't [s]', position: 'insideBottom', offset: -2, fill: '#6a8099', fontSize: 10 }}
          />
          <YAxis
            tick={{ fill: color, fontSize: 10 }}
            width={42}
          />
          <Tooltip
            contentStyle={{ background: '#0d1520', border: `1px solid ${color}33`, borderRadius: 6 }}
            labelStyle={{ color: '#6a8099', fontSize: 11 }}
            formatter={(v: number) => [`${v} ${unit}`, label]}
          />

          {markedEvents.map(ev => (
            <ReferenceLine
              key={`${ev.kind}-${ev.t}`}
              x={Math.round(ev.t)}
              stroke="#2a3a50"
              strokeDasharray="4 3"
              label={{ value: EVENT_MARKS[ev.kind] ?? '', fill: '#445566', fontSize: 11, position: 'top' }}
            />
          ))}

          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.8}
            fill={`url(#grad-${field})`}
            dot={false}
            activeDot={{ r: 3, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
