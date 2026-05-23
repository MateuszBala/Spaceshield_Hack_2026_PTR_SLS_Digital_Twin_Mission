import React from 'react';
import type { RocketParams } from '../types/contracts';
import StageCard from './StageCard';
import { estimateDeltaV } from '../data/syntheticResult';

interface Props {
  params: RocketParams;
  onChange: (p: RocketParams) => void;
  onSimulate: () => void;
  isLoading: boolean;
  aiAvailable: boolean;
}

const LOSSES = 1_750; // m/s — from dt_contracts.constants

export default function RocketForm({ params, onChange, onSimulate, isLoading, aiAvailable }: Props) {
  const dv = estimateDeltaV(params);
  const effectiveDv = dv - LOSSES;
  const liftoffMass = params.stages.reduce((acc, s) => {
    const mf = s.thrust / (s.isp * 9.806_65);
    return acc + s.dry_mass + mf * s.burn_time;
  }, params.payload.mass);

  const updateStage = (i: number) => (updated: RocketParams['stages'][number]) => {
    const stages = [...params.stages];
    stages[i] = updated;
    onChange({ ...params, stages });
  };

  const updatePayloadMass = (v: number) => {
    if (!isNaN(v) && v > 0) {
      onChange({ ...params, payload: { ...params.payload, mass: v } });
    }
  };

  return (
    <div className="rocket-form">
      <div className="form-header">
        <h2>Parametry rakiety</h2>
        <div className="dv-badge" title="Szacowane efektywne Δv = Tsiolkovsky − straty grawitacyjne/aerodynamiczne">
          <span className="dv-label">Δv<sub>eff</sub></span>
          <span className={`dv-value ${effectiveDv >= 9300 ? 'ok' : 'nok'}`}>
            {(effectiveDv / 1000).toFixed(1)} km/s
          </span>
        </div>
      </div>

      <div className="stages-list">
        {params.stages.map((stage, i) => (
          <StageCard key={i} stage={stage} index={i} onChange={updateStage(i)} />
        ))}
      </div>

      <div className="payload-card">
        <h3>Ładunek: {params.payload.name}</h3>
        <div className="field">
          <label>Masa ładunku</label>
          <div className="field-row">
            <input
              type="number"
              value={params.payload.mass}
              min={1}
              max={10_000}
              step={10}
              onChange={e => updatePayloadMass(parseFloat(e.target.value))}
            />
            <span className="unit">kg</span>
          </div>
        </div>
        <div className="computed-row">
          <span>Masa startowa: <strong>{(liftoffMass / 1000).toFixed(1)} t</strong></span>
        </div>
      </div>

      <div className="actions">
        <button
          className="btn-simulate"
          onClick={onSimulate}
          disabled={isLoading}
        >
          {isLoading ? 'Symulacja…' : 'Przelicz'}
        </button>

        {aiAvailable && (
          <button className="btn-optimize" disabled>
            Optymalizuj (AI)
          </button>
        )}
      </div>
    </div>
  );
}
