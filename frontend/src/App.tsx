import { useState, useEffect } from 'react';
import { DEFAULT_PRESET } from './data/preset';
import { generateSyntheticResult } from './data/syntheticResult';
import { fetchCapabilities, fetchSimulate } from './api/client';
import type { RocketParams, SimResult, CapabilitiesResponse } from './types/contracts';
import RocketForm from './components/RocketForm';
import TrajectoryChart from './components/TrajectoryChart';
import VerdictCard from './components/VerdictCard';
import MissionTimeline from './components/MissionTimeline';
import TelemetryHUD from './components/TelemetryHUD';
import TelemetryFieldChart from './components/TelemetryFieldChart';
import OrbitalPlot from './components/OrbitalPlot';
import { detectLanguage } from './i18n';

const G0 = 9.806_65;

export default function App() {
  const lang = detectLanguage();
  const isEn = lang === 'en';

  const [rocket, setRocket] = useState<RocketParams>(DEFAULT_PRESET);
  const [result, setResult] = useState<SimResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [caps, setCaps] = useState<CapabilitiesResponse | null>(null);
  const [dataSource, setDataSource] = useState<'api' | 'synthetic' | null>(null);

  useEffect(() => {
    fetchCapabilities()
      .then(c => setCaps(c))
      .catch(() => setCaps(null));
  }, []);

  const handleSimulate = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchSimulate({ rocket, include_telemetry: true, max_flight_time: 3600 });
      setResult(res);
      setDataSource('api');
    } catch {
      // API unreachable — synthetic fallback (offline demo mode)
      const synth = generateSyntheticResult(rocket, lang);
      setResult(synth);
      setDataSource('synthetic');
    } finally {
      setIsLoading(false);
    }
  };

  const engineAvailable = caps?.engine_available ?? false;
  const aiAvailable     = caps?.ai_available     ?? false;
  const apiReachable    = caps !== null;

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-title">
          <span className="header-icon">🚀</span>
          <h1>Rocket Digital Twin</h1>
        </div>
        <div className="header-badges">
          {dataSource === 'synthetic' && (
            <span
              className="badge badge-synth"
              title={isEn
                ? 'API unavailable - synthetic data (Tsiolkovsky JS)'
                : 'API niedostepne - dane syntetyczne (Tsiolkovsky JS)'}
            >
              {isEn ? 'Offline demo mode' : 'Tryb demo offline'}
            </span>
          )}
          {dataSource === 'api' && engineAvailable && (
            <span className="badge badge-api" title={isEn ? 'Verdict from physical engine' : 'Werdykt z silnika fizycznego'}>
              {isEn ? 'API live · engine ✓' : 'API live · silnik ✓'}
            </span>
          )}
          {dataSource === 'api' && !engineAvailable && (
            <span className="badge badge-synth" title={isEn ? 'API responds, but engine returns stub' : 'API odpowiada, ale silnik zwraca stub'}>
              {isEn ? 'API live · engine stub' : 'API live · silnik stub'}
            </span>
          )}
          {apiReachable && (
            <span
              className={`badge ${aiAvailable ? 'badge-ai-ok' : 'badge-ai-off'}`}
              title={aiAvailable
                ? (isEn ? 'AI package available' : 'Pakiet AI dostepny')
                : (isEn ? 'AI package unavailable (ADR graceful-ai)' : 'Pakiet AI niedostepny (ADR graceful-ai)')}
            >
              AI: {aiAvailable ? 'on' : 'off'}
            </span>
          )}
          {!apiReachable && (
            <span className="badge badge-ai-off" title={isEn ? 'No connection to API' : 'Brak polaczenia z API'}>
              {isEn ? 'API offline' : 'API offline'}
            </span>
          )}
          <span className="badge" title={isEn ? 'Current UI language' : 'Aktualny jezyk interfejsu'}>
            {isEn ? 'EN UI' : 'PL UI'}
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
            lang={lang}
          />
        </aside>

        {/* ── Right: results ── */}
        <section className="results-panel">
          {!result && !isLoading && (
            <div className="empty-state">
              <div className="empty-icon">📡</div>
              <p>
                {isEn ? (
                  <>
                    Set rocket parameters and click <strong>Simulate</strong>,<br />
                    to run the simulation.
                  </>
                ) : (
                  <>
                    Ustaw parametry rakiety i kliknij <strong>Przelicz</strong>,<br />
                    aby uruchomic symulacje.
                  </>
                )}
              </p>
              {!apiReachable && (
                <p style={{ marginTop: 12, fontSize: 12, color: 'var(--accent-yellow)' }}>
                  {isEn
                    ? 'API offline - results will come from the synthetic model.'
                    : 'API offline - wyniki beda z modelu syntetycznego.'}
                </p>
              )}
            </div>
          )}

          {isLoading && (
            <div className="loading-state">
              <div className="spinner" />
              <p>{isEn ? 'Simulation in progress...' : 'Symulacja w toku...'}</p>
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
                lang={lang}
              />

              {/* 2. Orbital plot — 2D space view (x, y from engine) */}
              {result.telemetry.length > 0 && (
                <OrbitalPlot
                  telemetry={result.telemetry}
                  events={result.events}
                  verdict={result.verdict}
                  lang={lang}
                />
              )}

              {/* 3. Mission timeline — SpaceX-style */}
              {result.events.length > 0 && (
                <MissionTimeline events={result.events} lang={lang} />
              )}

              {/* 4. Telemetry HUD — broadcast-style with scrubber */}
              {result.telemetry.length > 0 && (
                <TelemetryHUD telemetry={result.telemetry} lang={lang} />
              )}

              {/* 5. Trajectory chart — altitude vs time */}
              {result.telemetry.length > 0 && (
                <TrajectoryChart
                  telemetry={result.telemetry}
                  events={result.events}
                  lang={lang}
                />
              )}

              {/* 6. G-force chart */}
              {result.telemetry.length > 0 && (
                <TelemetryFieldChart
                  telemetry={result.telemetry}
                  field="acceleration"
                  label={isEn ? 'G-Force (acceleration)' : 'G-Force (przyspieszenie)'}
                  unit="g"
                  color="#ff6b35"
                  transform={v => parseFloat((v / G0).toFixed(3))}
                  events={result.events}
                />
              )}

              {/* 7. Dynamic pressure — Q profile */}
              {result.telemetry.length > 0 && (
                <TelemetryFieldChart
                  telemetry={result.telemetry}
                  field="dynamic_pressure"
                  label={isEn ? 'Dynamic pressure (Q)' : 'Cisnienie dynamiczne (Q)'}
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
