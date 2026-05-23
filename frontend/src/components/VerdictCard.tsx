import React from 'react';
import type { OrbitVerdict } from '../types/contracts';

interface Props {
  verdict: OrbitVerdict;
  maxAltitude: number;
  flightTime: number;
}

function fmt(m: number, decimals = 1): string {
  return (m / 1000).toFixed(decimals);
}

export default function VerdictCard({ verdict, maxAltitude, flightTime }: Props) {
  const { reached_orbit, reason, elements } = verdict;

  return (
    <div className={`verdict-card ${reached_orbit ? 'orbit-ok' : 'orbit-fail'}`}>
      <div className="verdict-headline">
        {reached_orbit ? '✓ ORBITA OSIĄGNIĘTA' : '✗ BRAK ORBITY'}
      </div>
      <p className="verdict-reason">{reason}</p>

      <div className="verdict-metrics">
        <div className="metric">
          <span className="metric-label">Maks. wysokość</span>
          <span className="metric-value">{fmt(maxAltitude)} km</span>
        </div>
        <div className="metric">
          <span className="metric-label">Czas lotu</span>
          <span className="metric-value">{flightTime.toFixed(0)} s</span>
        </div>
        {elements && (
          <>
            <div className="metric">
              <span className="metric-label">Perygeum</span>
              <span className="metric-value">{fmt(elements.periapsis_altitude)} km</span>
            </div>
            <div className="metric">
              <span className="metric-label">Apogeum</span>
              <span className="metric-value">{fmt(elements.apoapsis_altitude)} km</span>
            </div>
            <div className="metric">
              <span className="metric-label">Mimośród</span>
              <span className="metric-value">{elements.eccentricity.toFixed(4)}</span>
            </div>
            {elements.period !== null && (
              <div className="metric">
                <span className="metric-label">Okres</span>
                <span className="metric-value">{(elements.period / 60).toFixed(1)} min</span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
