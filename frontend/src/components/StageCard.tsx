import type { Stage } from '../types/contracts';
import type { Language } from '../i18n';

const G0 = 9.806_65;

function computed(stage: Stage) {
  const mf = stage.thrust / (stage.isp * G0);
  const prop = mf * stage.burn_time;
  const wet = stage.dry_mass + prop;
  return {
    massFlow: mf,
    propellantMass: prop,
    wetMass: wet,
    massFraction: prop / wet,
  };
}

interface Props {
  stage: Stage;
  index: number;
  onChange: (updated: Stage) => void;
  lang: Language;
}

function NumInput({
  label, value, unit, min, max, step, onChange,
}: {
  label: string; value: number; unit: string;
  min: number; max: number; step: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <div className="field-row">
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={e => {
            const v = parseFloat(e.target.value);
            if (!isNaN(v)) onChange(v);
          }}
        />
        <span className="unit">{unit}</span>
      </div>
    </div>
  );
}

export default function StageCard({ stage, index, onChange, lang }: Props) {
  const isEn = lang === 'en';
  const c = computed(stage);

  const set = (key: keyof Stage) => (v: number) =>
    onChange({ ...stage, [key]: v });

  return (
    <div className="stage-card">
      <h3 className="stage-title">
        <span className="stage-badge">{index + 1}</span>
        {stage.name}
      </h3>

      <div className="fields-grid">
        <NumInput label={isEn ? 'Thrust' : 'Ciag'} value={stage.thrust} unit="N"
          min={1000} max={20_000_000} step={10_000} onChange={set('thrust')} />
        <NumInput label="Isp" value={stage.isp} unit="s"
          min={1} max={455} step={1} onChange={set('isp')} />
        <NumInput label={isEn ? 'Burn time' : 'Czas pracy'} value={stage.burn_time} unit="s"
          min={1} max={2000} step={5} onChange={set('burn_time')} />
        <NumInput label={isEn ? 'Dry mass' : 'Masa sucha'} value={stage.dry_mass} unit="kg"
          min={1} max={500_000} step={100} onChange={set('dry_mass')} />
      </div>

      <div className="computed-row">
        <span title={isEn ? 'propellant mass = thrust / (Isp*g0) * burn time' : 'masa paliwa = ciag / (Isp*g0) * czas'}>
          {isEn ? 'Propellant' : 'Paliwo'}: <strong>{(c.propellantMass / 1000).toFixed(1)} t</strong>
        </span>
        <span title={isEn ? 'wet mass = dry + propellant' : 'masa mokra = sucha + paliwo'}>
          {isEn ? 'Wet' : 'Mokra'}: <strong>{(c.wetMass / 1000).toFixed(1)} t</strong>
        </span>
        <span title={isEn ? 'propellant mass fraction (SMAD: 0.80-0.95)' : 'frakcja masowa paliwa (SMAD: 0.80-0.95)'}>
          η<sub>m</sub>: <strong className={c.massFraction < 0.8 || c.massFraction > 0.95 ? 'warn' : ''}>
            {(c.massFraction * 100).toFixed(1)}%
          </strong>
        </span>
        <span title={isEn ? 'propellant mass flow' : 'strumien masy paliwa'}>
          ṁ: <strong>{c.massFlow.toFixed(1)} kg/s</strong>
        </span>
      </div>
    </div>
  );
}
