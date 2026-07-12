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
import type { Language } from '../i18n';

interface Props {
  telemetry: TelemetryFrame[];
  events: MissionEvent[];
  lang: Language;
}

interface ChartPoint {
  t: number;
  alt: number;   // km
  speed: number; // km/s
}

const MILESTONE_EVENTS: Partial<Record<MissionEvent['kind'], { label: string; color: string }>> = {
  max_q:            { label: 'MAX-Q',     color: '#ffd740' },
  stage_burnout:    { label: 'MECO',      color: '#ff6b35' },
  stage_separation: { label: 'SEP',       color: '#ff9966' },
  orbit_insertion:  { label: 'ORBIT',     color: '#00e676' },
  apogee:           { label: 'APOGEE',    color: '#00d4ff' },
  impact:           { label: 'IMPACT',    color: '#ff1744' },
};

const ACCENT_ALT   = '#00d4ff';
const ACCENT_SPEED = '#ff6b35';

export default function TrajectoryChart({ telemetry, events, lang }: Props) {
  const isEn = lang === 'en';
  const altitudeLabel = isEn ? 'Altitude' : 'Wysokosc';
  const speedLabel = isEn ? 'Speed' : 'Predkosc';

  if (telemetry.length === 0) return null;

  const data: ChartPoint[] = telemetry.map(f => ({
    t: Math.round(f.t),
    alt: parseFloat((f.altitude / 1000).toFixed(2)),
    speed: parseFloat((f.speed / 1000).toFixed(3)),
  }));

  const deduped = data.filter((d, i) => i === data.length - 1 || d.t !== data[i + 1].t);

  // Build burnout count for MECO/SECO labels
  const BURNOUT_LABELS = ['MECO', 'SECO', 'TECO'];
  let burnoutCount = 0;
  const markedEvents = events.flatMap(ev => {
    const meta = MILESTONE_EVENTS[ev.kind];
    if (!meta) return [];
    let lbl = meta.label;
    if (ev.kind === 'stage_burnout') { lbl = BURNOUT_LABELS[burnoutCount++] ?? lbl; }
    return [{ t: Math.round(ev.t), label: lbl, color: meta.color }];
  });

  return (
    <div className="chart-wrapper">
      <div className="chart-header">
        <h3 className="chart-title">
          {isEn ? '2D trajectory - altitude and speed' : 'Trajektoria 2D - wysokosc i predkosc'}
        </h3>
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={deduped} margin={{ top: 8, right: 28, left: 4, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#111e30" />
          <XAxis
            dataKey="t"
            tick={{ fill: '#6a8099', fontSize: 11 }}
            label={{ value: isEn ? 'Time [s]' : 'Czas [s]', position: 'insideBottom', offset: -12, fill: '#6a8099', fontSize: 11 }}
          />
          <YAxis
            yAxisId="alt"
            tick={{ fill: ACCENT_ALT, fontSize: 11 }}
            label={{ value: isEn ? 'Altitude [km]' : 'Wysokosc [km]', angle: -90, position: 'insideLeft', offset: 14, fill: ACCENT_ALT, fontSize: 11 }}
          />
          <YAxis
            yAxisId="speed"
            orientation="right"
            tick={{ fill: ACCENT_SPEED, fontSize: 11 }}
            label={{ value: isEn ? 'Speed [km/s]' : 'Predkosc [km/s]', angle: 90, position: 'insideRight', offset: 14, fill: ACCENT_SPEED, fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ background: '#0a1222', border: '1px solid #1a2840', borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: '#6a8099' }}
            formatter={(v: number, name: string) => [
              name === altitudeLabel ? `${v} km` : `${v} km/s`, name,
            ]}
          />
          <Legend
            wrapperStyle={{ color: '#6a8099', fontSize: 12, paddingTop: 8 }}
          />

          {/* Milestone reference lines */}
          {markedEvents.map((ev, i) => (
            <ReferenceLine
              key={`${ev.label}-${ev.t}-${i}`}
              yAxisId="alt"
              x={ev.t}
              stroke={ev.color + '66'}
              strokeDasharray="4 3"
              label={{ value: ev.label, fill: ev.color, fontSize: 9, position: 'insideTopLeft' }}
            />
          ))}

          <Line
            yAxisId="alt"
            type="monotone"
            dataKey="alt"
            name={altitudeLabel}
            stroke={ACCENT_ALT}
            dot={false}
            strokeWidth={2}
            activeDot={{ r: 4, fill: ACCENT_ALT, stroke: '#0a1222', strokeWidth: 2 }}
          />
          <Line
            yAxisId="speed"
            type="monotone"
            dataKey="speed"
            name={speedLabel}
            stroke={ACCENT_SPEED}
            dot={false}
            strokeWidth={2}
            activeDot={{ r: 4, fill: ACCENT_SPEED, stroke: '#0a1222', strokeWidth: 2 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
