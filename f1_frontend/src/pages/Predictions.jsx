import { useState, useEffect } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, ProbabilityBar, Select } from '../components/UI.jsx';
import { predictSafetyCar, predictMechanicalFailure, predictPodium, getMLStatus, getFeatureImportance } from '../api/api.js';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Cpu, AlertTriangle, Shield, Trophy } from 'lucide-react';

function PredictionCard({ icon: Icon, title, color, children }) {
  return (
    <div style={{
      background: 'var(--f1-surface)',
      border: `1px solid ${color}25`,
      borderTop: `3px solid ${color}`,
      borderRadius: 4,
      overflow: 'hidden',
    }}>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--f1-border)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <Icon size={16} color={color} />
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-muted)' }}>{title}</span>
      </div>
      <div style={{ padding: 18 }}>{children}</div>
    </div>
  );
}

function ResultBox({ result, color }) {
  if (!result) return null;
  const pct = Math.round(result.probability * 100);
  return (
    <div style={{ marginTop: 16, padding: 16, background: 'var(--f1-surface-2)', borderRadius: 4, border: '1px solid var(--f1-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 11, color: 'var(--f1-text-muted)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Resultado</span>
        <span className={`badge ${result.label ? 'badge-red' : 'badge-gray'}`}>
          {result.label ? 'SÍ' : 'NO'}
        </span>
      </div>
      <ProbabilityBar value={result.probability} label="Probabilidad" color={color} />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginTop: 14 }}>
        <div className="stat-box">
          <span className="stat-label">Prob.</span>
          <span className="stat-value" style={{ fontSize: 20, color }}>{pct}%</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Confianza</span>
          <span className="stat-value" style={{ fontSize: 14, color: result.confidence === 'alta' ? '#27F4D2' : result.confidence === 'media' ? '#FF8000' : 'var(--f1-text-muted)' }}>
            {result.confidence?.toUpperCase()}
          </span>
        </div>
        <div className="stat-box">
          <span className="stat-label">AUC modelo</span>
          <span className="stat-value" style={{ fontSize: 14 }}>{result.model_auc ? result.model_auc.toFixed(3) : '—'}</span>
        </div>
      </div>
    </div>
  );
}

export default function Predictions() {
  const [modelStatus, setModelStatus] = useState(null);
  const [loading, setLoading] = useState({});
  const [results, setResults] = useState({});
  const [errors, setErrors] = useState({});

  // Safety Car form
  const [scForm, setScForm] = useState({
    year: 2024, round: 8, season_progress: 0.38,
    lat: 43.7347, lng: 7.4205, alt: 7,
    country_sc_rate: 0.7, circuit_sc_rate_3y: 0.67, circuit_sc_rate_all: 0.65,
    n_finishers: 17, n_pit_stops: 52, is_modern_era: 1,
  });

  // Mechanical Failure form
  const [dnfForm, setDnfForm] = useState({
    year: 2024, round: 8, season_progress: 0.38, is_modern_era: 1,
    grid_position: 5, laps_completed: 0,
    driver_dnf_rate_5r: 0.1, driver_dnf_rate_all: 0.08,
    driver_races_count: 120, constructor_dnf_rate_5r: 0.05,
  });

  // Podium form
  const [podForm, setPodForm] = useState({
    year: 2024, round: 8, season_progress: 0.38, is_modern_era: 1,
    quali_pos: 3,
    driver_podium_rate_5r: 0.6, driver_win_rate_all: 0.3,
    driver_avg_pos_5r: 2.4, constr_podium_rate_5r: 0.7,
    driver_circuit_podium_rate: 0.5,
  });

  useEffect(() => {
    getMLStatus().then(setModelStatus).catch(() => {});
  }, []);

  const run = async (key, fn, payload) => {
    setLoading(l => ({ ...l, [key]: true }));
    setErrors(e => ({ ...e, [key]: null }));
    try {
      const res = await fn(payload);
      setResults(r => ({ ...r, [key]: res }));
    } catch (e) {
      setErrors(er => ({ ...er, [key]: e.response?.data?.detail || e.message }));
    } finally {
      setLoading(l => ({ ...l, [key]: false }));
    }
  };

  const Field = ({ label, value, onChange, step = 'any', type = 'number' }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-dim)' }}>{label}</label>
      <input
        type={type}
        step={step}
        value={value}
        onChange={e => onChange(type === 'number' ? parseFloat(e.target.value) : e.target.value)}
        className="input-f1"
        style={{ padding: '6px 10px', fontSize: 12 }}
      />
    </div>
  );

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Predicciones IA" subtitle="Modelos ML para Safety Car, fallos mecánicos y podio">
        {modelStatus && (
          <div style={{ display: 'flex', gap: 8 }}>
            {Object.entries(modelStatus).map(([key, val]) => (
              <span key={key} className={`badge ${val.loaded ? 'badge-green' : 'badge-red'}`}>
                {key.replace('_', ' ')} {val.loaded ? '✓' : '✗'}
              </span>
            ))}
          </div>
        )}
      </PageHeader>

      <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>
        {/* Models info */}
        {modelStatus && (
          <div className="grid-3">
            {[
              { key: 'safety_car', label: 'Safety Car', color: '#FF8000' },
              { key: 'mechanical_failure', label: 'Fallo Mecánico', color: 'var(--f1-red)' },
              { key: 'position', label: 'Podio', color: 'var(--gold)' },
            ].map(({ key, label, color }) => {
              const m = modelStatus[key] || {};
              return (
                <div key={key} className="card" style={{ padding: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color }}>{label}</span>
                    <span className={`badge ${m.loaded ? 'badge-green' : 'badge-gray'}`}>{m.loaded ? 'Cargado' : 'No disponible'}</span>
                  </div>
                  <div className="grid-2" style={{ gap: 8 }}>
                    <div className="stat-box">
                      <span className="stat-label">AUC CV</span>
                      <span className="stat-value" style={{ fontSize: 16 }}>{m.cv_auc ? m.cv_auc.toFixed(3) : '—'}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Muestras</span>
                      <span className="stat-value" style={{ fontSize: 16 }}>{m.n_samples ? m.n_samples.toLocaleString() : '—'}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="grid-3" style={{ alignItems: 'start' }}>
          {/* Safety Car */}
          <PredictionCard icon={Shield} title="Safety Car" color="#FF8000">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div className="grid-2" style={{ gap: 8 }}>
                <Field label="Año" value={scForm.year} onChange={v => setScForm(f => ({ ...f, year: v }))} />
                <Field label="Ronda" value={scForm.round} onChange={v => setScForm(f => ({ ...f, round: v }))} />
                <Field label="Progreso temp." value={scForm.season_progress} onChange={v => setScForm(f => ({ ...f, season_progress: v }))} step="0.01" />
                <Field label="Altitud (m)" value={scForm.alt} onChange={v => setScForm(f => ({ ...f, alt: v }))} />
                <Field label="Tasa SC circuito" value={scForm.circuit_sc_rate_all} onChange={v => setScForm(f => ({ ...f, circuit_sc_rate_all: v }))} step="0.01" />
                <Field label="Tasa SC 3 años" value={scForm.circuit_sc_rate_3y} onChange={v => setScForm(f => ({ ...f, circuit_sc_rate_3y: v }))} step="0.01" />
                <Field label="Tasa SC país" value={scForm.country_sc_rate} onChange={v => setScForm(f => ({ ...f, country_sc_rate: v }))} step="0.01" />
                <Field label="Pit stops medios" value={scForm.n_pit_stops} onChange={v => setScForm(f => ({ ...f, n_pit_stops: v }))} />
              </div>
              <button className="btn-primary" style={{ marginTop: 4 }}
                onClick={() => run('sc', predictSafetyCar, scForm)}
                disabled={loading.sc}>
                {loading.sc ? 'Calculando...' : 'Predecir'}
              </button>
              {errors.sc && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 4 }}>⚠ {errors.sc}</div>}
              <ResultBox result={results.sc} color="#FF8000" />
            </div>
          </PredictionCard>

          {/* Mechanical Failure */}
          <PredictionCard icon={AlertTriangle} title="Fallo Mecánico" color="var(--f1-red)">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div className="grid-2" style={{ gap: 8 }}>
                <Field label="Año" value={dnfForm.year} onChange={v => setDnfForm(f => ({ ...f, year: v }))} />
                <Field label="Ronda" value={dnfForm.round} onChange={v => setDnfForm(f => ({ ...f, round: v }))} />
                <Field label="Pos. salida" value={dnfForm.grid_position} onChange={v => setDnfForm(f => ({ ...f, grid_position: v }))} />
                <Field label="Vueltas complet." value={dnfForm.laps_completed} onChange={v => setDnfForm(f => ({ ...f, laps_completed: v }))} />
                <Field label="DNF piloto (5c)" value={dnfForm.driver_dnf_rate_5r} onChange={v => setDnfForm(f => ({ ...f, driver_dnf_rate_5r: v }))} step="0.01" />
                <Field label="DNF piloto (hist.)" value={dnfForm.driver_dnf_rate_all} onChange={v => setDnfForm(f => ({ ...f, driver_dnf_rate_all: v }))} step="0.01" />
                <Field label="Carreras piloto" value={dnfForm.driver_races_count} onChange={v => setDnfForm(f => ({ ...f, driver_races_count: v }))} />
                <Field label="DNF equipo (5c)" value={dnfForm.constructor_dnf_rate_5r} onChange={v => setDnfForm(f => ({ ...f, constructor_dnf_rate_5r: v }))} step="0.01" />
              </div>
              <button className="btn-primary" style={{ marginTop: 4 }}
                onClick={() => run('dnf', predictMechanicalFailure, dnfForm)}
                disabled={loading.dnf}>
                {loading.dnf ? 'Calculando...' : 'Predecir'}
              </button>
              {errors.dnf && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 4 }}>⚠ {errors.dnf}</div>}
              <ResultBox result={results.dnf} color="var(--f1-red)" />
            </div>
          </PredictionCard>

          {/* Podium */}
          <PredictionCard icon={Trophy} title="Predicción de Podio" color="var(--gold)">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div className="grid-2" style={{ gap: 8 }}>
                <Field label="Año" value={podForm.year} onChange={v => setPodForm(f => ({ ...f, year: v }))} />
                <Field label="Ronda" value={podForm.round} onChange={v => setPodForm(f => ({ ...f, round: v }))} />
                <Field label="Pos. qualifying" value={podForm.quali_pos} onChange={v => setPodForm(f => ({ ...f, quali_pos: v }))} />
                <Field label="Podio piloto (5c)" value={podForm.driver_podium_rate_5r} onChange={v => setPodForm(f => ({ ...f, driver_podium_rate_5r: v }))} step="0.01" />
                <Field label="Victoria hist." value={podForm.driver_win_rate_all} onChange={v => setPodForm(f => ({ ...f, driver_win_rate_all: v }))} step="0.01" />
                <Field label="Pos. media (5c)" value={podForm.driver_avg_pos_5r} onChange={v => setPodForm(f => ({ ...f, driver_avg_pos_5r: v }))} step="0.1" />
                <Field label="Podio equipo (5c)" value={podForm.constr_podium_rate_5r} onChange={v => setPodForm(f => ({ ...f, constr_podium_rate_5r: v }))} step="0.01" />
                <Field label="Podio en circuito" value={podForm.driver_circuit_podium_rate} onChange={v => setPodForm(f => ({ ...f, driver_circuit_podium_rate: v }))} step="0.01" />
              </div>
              <button className="btn-primary" style={{ marginTop: 4 }}
                onClick={() => run('pod', predictPodium, podForm)}
                disabled={loading.pod}>
                {loading.pod ? 'Calculando...' : 'Predecir'}
              </button>
              {errors.pod && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 4 }}>⚠ {errors.pod}</div>}
              <ResultBox result={results.pod} color="var(--gold)" />
            </div>
          </PredictionCard>
        </div>
      </div>
    </div>
  );
}
