import React, { useState, useEffect } from 'react';
import { DEFAULT_PRESET } from './data/preset';
import { generateSyntheticResult } from './data/syntheticResult';
import { fetchCapabilities, fetchSimulate } from './api/client';
import type { RocketParams, SimResult } from './types/contracts';
import RocketForm from './components/RocketForm';
import TrajectoryChart from './components/TrajectoryChart';
import VerdictCard from './components/VerdictCard';
import MissionTimeline from './components/MissionTimeline';
import TelemetryHUD from './components/TelemetryHUD';
import TelemetryFieldChart from './components/TelemetryFieldChart';

const G0 = 9.806_65;

export default function App() {
  const [rocket, setRocket] = useState<RocketParams>(DEFAULT_PRESET);
  const [result, setResult] = useState<SimResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiAvailable, setAiAvailable] = useState(false);
  const [dataSource, setDataSource] = useState<'api' | 'synthetic' | null>(null);

  useEffect(() => {
    fetchCapabilities()
      .then(caps => setAiAvailable(caps.ai_available))
      .catch(() => setAiAvailable(false));
  }, []);

  const handleSimulate = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchSimulate({ rocket, include_telemetry: true, max_flight_time: 3600 });
      setResult(res);
      setDataSource('api');
    } catch {
      // API unreachable — synthetic fallback (Digital Twin demo mode)
      const synth = generateSyntheticResult(rocket);
      setResult(synth);
      setDataSource('synthetic');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-title">
          <span className="header-icon">🚀</span>
          <h1>Rocket Digital Twin</h1>
        </div>
        <div className="header-badges">
          {dataSource === 'synthetic' && (
            <span className="badge badge-synth" title="API niedostępne — dane syntetyczne (Tsiolkovsky)">
              Tryb demo
            </span>
          )}
          {dataSource === 'api' && (
            <span className="badge badge-api">API live</span>
          )}
          <span
            className={`badge ${aiAvailable ? 'badge-ai-ok' : 'badge-ai-off'}`}
            title={aiAvailable ? 'Pakiet AI dostępny' : 'Pakiet AI niedostępny (ADR graceful-ai)'}
          >
            AI: {aiAvailable ? 'on' : 'off'}
          </span>
        </div>
      </header>

      <main className="app-main">
        {/* ── Left: parameters ── */}
        <aside className="params-panel">
          <RocketForm
            params={rocket}
            onChange={setRocket}
            onSimulate={handleSimulate}
            isLoading={isLoading}
            aiAvailable={aiAvailable}
          />
        </aside>

        {/* ── Right: results ── */}
        <section className="results-panel">
          {!result && !isLoading && (
            <div className="empty-state">
              <div className="empty-icon">📡</div>
              <p>Ustaw parametry rakiety i kliknij <strong>Przelicz</strong>,<br />aby uruchomić symulację.</p>
            </div>
          )}

          {isLoading && (
            <div className="loading-state">
              <div className="spinner" />
              <p>Symulacja w toku…</p>
            </div>
          )}

          {result && !isLoading && (
            <div className="results-content">
              {/* 1. Verdict — first thing jury sees */}
              <VerdictCard
                verdict={result.verdict}
                maxAltitude={result.max_altitude}
                flightTime={result.flight_time}
                maxDynQ={result.max_dynamic_pressure}
              />

              {/* 2. Mission timeline — SpaceX-style */}
              <MissionTimeline events={result.events} />

              {/* 3. Telemetry HUD — broadcast-style with scrubber */}
              {result.telemetry.length > 0 && (
                <TelemetryHUD telemetry={result.telemetry} />
              )}

              {/* 4. Trajectory chart */}
              <TrajectoryChart
                telemetry={result.telemetry}
                events={result.events}
              />

              {/* 5. G-force chart — generic TelemetryFieldChart */}
              {result.telemetry.length > 0 && (
                <TelemetryFieldChart
                  telemetry={result.telemetry}
                  field="acceleration"
                  label="G-Force (przyspieszenie)"
                  unit="g"
                  color="#ff6b35"
                  transform={v => parseFloat((v / G0).toFixed(3))}
                  events={result.events}
                />
              )}

              {/* 6. Dynamic pressure — Q profile */}
              {result.telemetry.length > 0 && (
                <TelemetryFieldChart
                  telemetry={result.telemetry}
                  field="dynamic_pressure"
                  label="Ciśnienie dynamiczne (Q)"
                  unit="kPa"
                  color="#ffd740"
                  transform={v => parseFloat((v / 1000).toFixed(3))}
                  events={result.events}
                  height={160}
                />
              )}
            </div>
          )}

          {error && <div className="error-msg">{error}</div>}
        </section>
      </main>
    </div>
  );
}
