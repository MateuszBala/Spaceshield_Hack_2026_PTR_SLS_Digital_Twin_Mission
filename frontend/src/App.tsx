import React, { useState, useEffect } from 'react';
import { DEFAULT_PRESET } from './data/preset';
import { generateSyntheticResult } from './data/syntheticResult';
import { fetchCapabilities, fetchSimulate } from './api/client';
import type { RocketParams, SimResult } from './types/contracts';
import RocketForm from './components/RocketForm';
import TrajectoryChart from './components/TrajectoryChart';
import VerdictCard from './components/VerdictCard';

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
      // API unreachable — use synthetic data (Digital Twin demo mode)
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
        <aside className="params-panel">
          <RocketForm
            params={rocket}
            onChange={setRocket}
            onSimulate={handleSimulate}
            isLoading={isLoading}
            aiAvailable={aiAvailable}
          />
        </aside>

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
              <VerdictCard
                verdict={result.verdict}
                maxAltitude={result.max_altitude}
                flightTime={result.flight_time}
              />
              <TrajectoryChart
                telemetry={result.telemetry}
                events={result.events}
              />
            </div>
          )}

          {error && <div className="error-msg">{error}</div>}
        </section>
      </main>
    </div>
  );
}
