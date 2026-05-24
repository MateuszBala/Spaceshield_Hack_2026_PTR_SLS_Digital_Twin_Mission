import React from 'react';
import type { MissionEvent, EventKind } from '../types/contracts';

// Presentation-layer label mapping (SpaceX-style) — not a contract change.
const BURNOUT_LABELS = ['MECO', 'SECO', 'TECO'];

function getLabel(kind: EventKind, burnoutIndex: number): string | null {
  switch (kind) {
    case 'liftoff':           return 'LIFTOFF';
    case 'max_q':             return 'MAX-Q';
    case 'stage_burnout':     return BURNOUT_LABELS[burnoutIndex] ?? `ECO-${burnoutIndex + 1}`;
    case 'stage_separation':  return 'STAGE SEP';
    case 'payload_separation':return 'PAYLOAD\nDEPLOY';
    case 'orbit_insertion':   return 'ORBITAL\nINSERTION';
    case 'apogee':            return 'APOGEE';
    case 'impact':            return 'IMPACT';
    case 'drag_negligible':   return null; // hide — internal engine detail
    default:                  return kind.toUpperCase();
  }
}

function isFailure(kind: EventKind): boolean {
  return kind === 'impact';
}

function isHighlight(kind: EventKind): boolean {
  return kind === 'orbit_insertion' || kind === 'liftoff';
}

function tPlus(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `T+${m}:${s.toString().padStart(2, '0')}`;
}

interface LabeledEvent {
  event: MissionEvent;
  label: string;
}

interface Props {
  events: MissionEvent[];
}

export default function MissionTimeline({ events }: Props) {
  // Assign burnout indices to stage_burnout events in time order
  let burnoutIdx = 0;
  const labeled: LabeledEvent[] = [];
  for (const ev of events) {
    const lbl = getLabel(ev.kind, ev.kind === 'stage_burnout' ? burnoutIdx : 0);
    if (lbl === null) continue;
    labeled.push({ event: ev, label: lbl });
    if (ev.kind === 'stage_burnout') burnoutIdx++;
  }

  return (
    <div className="mission-timeline-wrapper">
      <h3 className="chart-title">Sekwencja misji</h3>
      <div className="mission-timeline">
        {labeled.map(({ event, label }, i) => {
          const cls = isHighlight(event.kind)
            ? 'milestone milestone-highlight'
            : isFailure(event.kind)
              ? 'milestone milestone-fail'
              : 'milestone';

          return (
            <React.Fragment key={`${event.kind}-${event.t}`}>
              {i > 0 && <div className="timeline-connector" />}
              <div className={cls}>
                <div className="milestone-dot" />
                <div className="milestone-label">{label.split('\n').map((l, j) => (
                  <span key={j}>{l}</span>
                ))}</div>
                <div className="milestone-time">{tPlus(event.t)}</div>
                <div className="milestone-data">
                  <span>{(event.altitude / 1000).toFixed(1)} km</span>
                  <span>{(event.speed / 1000).toFixed(2)} km/s</span>
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
