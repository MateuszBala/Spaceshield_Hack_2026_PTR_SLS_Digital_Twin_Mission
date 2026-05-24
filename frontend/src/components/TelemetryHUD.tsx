import React, { useState } from 'react';
import type { TelemetryFrame, Phase } from '../types/contracts';

const G0 = 9.806_65;

const PHASE_LABELS: Record<Phase, string> = {
  ascent:    'ASCENT',
  insertion: 'INSERTION',
  orbit:     'ORBIT',
  failed:    'FAILED',
};

const PHASE_COLORS: Record<Phase, string> = {
  ascent:    '#ff6b35',
  insertion: '#00d4ff',
  orbit:     '#00e676',
  failed:    '#ff1744',
};

function tPlus(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `T+${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

interface Props {
  telemetry: TelemetryFrame[];
}

export default function TelemetryHUD({ telemetry }: Props) {
  const [idx, setIdx] = useState(telemetry.length - 1);
  const frame = telemetry[Math.min(idx, telemetry.length - 1)];
  if (!frame) return null;

  const speedKmh = Math.round(frame.speed * 3.6).toLocaleString('pl');
  const altKm    = (frame.altitude / 1000).toFixed(1);
  const gForce   = (frame.acceleration / G0).toFixed(2);
  const massT    = (frame.mass / 1000).toFixed(1);
  const dynQ     = Math.round(frame.dynamic_pressure).toLocaleString('pl');

  return (
    <div className="hud-wrapper">
      <div className="hud-header">
        <span className="hud-title">Telemetria lotu</span>
        <span className="hud-tplus">{tPlus(frame.t)}</span>
        <span
          className="hud-phase"
          style={{ color: PHASE_COLORS[frame.phase] }}
        >
          {PHASE_LABELS[frame.phase]}
        </span>
        <span className="hud-stage">Stage {frame.active_stage + 1}</span>
      </div>

      <div className="hud-main">
        <div className="hud-block">
          <span className="hud-value">{speedKmh}</span>
          <span className="hud-unit">KM/H</span>
          <span className="hud-sublabel">SPEED</span>
        </div>
        <div className="hud-divider" />
        <div className="hud-block">
          <span className="hud-value">{altKm}</span>
          <span className="hud-unit">KM</span>
          <span className="hud-sublabel">ALTITUDE</span>
        </div>
        <div className="hud-divider" />
        <div className="hud-block hud-block-sm">
          <span className="hud-value-sm">{gForce}</span>
          <span className="hud-unit">g</span>
          <span className="hud-sublabel">G-FORCE</span>
        </div>
        <div className="hud-block hud-block-sm">
          <span className="hud-value-sm">{massT}</span>
          <span className="hud-unit">t</span>
          <span className="hud-sublabel">MASS</span>
        </div>
        <div className="hud-block hud-block-sm">
          <span className="hud-value-sm">{dynQ}</span>
          <span className="hud-unit">Pa</span>
          <span className="hud-sublabel">DYN-Q</span>
        </div>
      </div>

      <div className="hud-scrubber-row">
        <span className="hud-scrub-label">T+0:00</span>
        <input
          className="hud-scrubber"
          type="range"
          min={0}
          max={telemetry.length - 1}
          value={idx}
          onChange={e => setIdx(Number(e.target.value))}
        />
        <span className="hud-scrub-label">{tPlus(telemetry[telemetry.length - 1].t)}</span>
      </div>
    </div>
  );
}
