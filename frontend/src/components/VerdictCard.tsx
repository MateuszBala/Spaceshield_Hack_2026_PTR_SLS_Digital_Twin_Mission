import type { OrbitVerdict } from '../types/contracts';
import type { Language } from '../i18n';

interface Props {
  verdict: OrbitVerdict;
  maxAltitude: number;
  flightTime: number;
  maxDynQ?: number;
  lang: Language;
}

function fmtKm(m: number, dec = 1): string {
  return (m / 1000).toFixed(dec) + ' km';
}

function fmtMin(s: number): string {
  return (s / 60).toFixed(1) + ' min';
}

function fmtSci(v: number): string {
  // e.g. -29 000 000 → "-2.90 × 10⁷"
  const exp = Math.floor(Math.log10(Math.abs(v)));
  const mantissa = (v / Math.pow(10, exp)).toFixed(2);
  return `${mantissa} × 10${superscript(exp)}`;
}

function superscript(n: number): string {
  return String(n).split('').map(c => '⁰¹²³⁴⁵⁶⁷⁸⁹⁻'['0123456789-'.indexOf(c)] ?? c).join('');
}

export default function VerdictCard({ verdict, maxAltitude, flightTime, maxDynQ, lang }: Props) {
  const isEn = lang === 'en';
  const { reached_orbit, reason, elements } = verdict;

  return (
    <div className={`verdict-card ${reached_orbit ? 'orbit-ok' : 'orbit-fail'}`}>
      {/* Headline */}
      <div className="verdict-top">
        <div className="verdict-icon">{reached_orbit ? '✓' : '✗'}</div>
        <div className="verdict-headline">
          {reached_orbit
            ? (isEn ? 'ORBIT ACHIEVED' : 'ORBITA OSIAGNIETA')
            : (isEn ? 'NO ORBIT' : 'BRAK ORBITY')}
        </div>
      </div>

      <p className="verdict-reason">{reason}</p>

      {/* Flight summary */}
      <div className="verdict-section-label">{isEn ? 'Flight summary' : 'Przebieg lotu'}</div>
      <div className="verdict-metrics">
        <div className="metric">
          <span className="metric-label">{isEn ? 'Max altitude' : 'Maks. wysokosc'}</span>
          <span className="metric-value">{fmtKm(maxAltitude)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">{isEn ? 'Flight time' : 'Czas lotu'}</span>
          <span className="metric-value">{flightTime.toFixed(0)} s</span>
        </div>
        {maxDynQ !== undefined && (
          <div className="metric">
            <span className="metric-label">Max-Q</span>
            <span className="metric-value">{Math.round(maxDynQ / 1000).toFixed(1)} kPa</span>
          </div>
        )}
      </div>

      {/* Orbital elements */}
      {elements && (
        <>
          <div className="verdict-section-label" style={{ marginTop: 16 }}>
            {isEn ? 'Orbital elements' : 'Elementy orbitalne'}
          </div>
          <div className="verdict-metrics">
            <div className="metric">
              <span className="metric-label">{isEn ? 'Perigee' : 'Perygeum'}</span>
              <span className="metric-value orbit-value">{fmtKm(elements.periapsis_altitude)}</span>
            </div>
            <div className="metric">
              <span className="metric-label">{isEn ? 'Apogee' : 'Apogeum'}</span>
              <span className="metric-value orbit-value">{fmtKm(elements.apoapsis_altitude)}</span>
            </div>
            <div className="metric">
              <span className="metric-label">{isEn ? 'Eccentricity (e)' : 'Mimosrod (e)'}</span>
              <span className="metric-value orbit-value">{elements.eccentricity.toFixed(4)}</span>
            </div>
            <div className="metric">
              <span className="metric-label">{isEn ? 'Semi-major axis (a)' : 'Polos wielka (a)'}</span>
              <span className="metric-value orbit-value">{fmtKm(elements.semi_major_axis, 0)}</span>
            </div>
            {elements.period !== null && (
              <div className="metric">
                <span className="metric-label">{isEn ? 'Orbital period' : 'Okres orbitalny'}</span>
                <span className="metric-value orbit-value">{fmtMin(elements.period)}</span>
              </div>
            )}
            <div className="metric">
              <span className="metric-label">{isEn ? 'Specific energy' : 'Energia wlasciwa'}</span>
              <span className="metric-value orbit-value mono">{fmtSci(elements.specific_energy)} J/kg</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
