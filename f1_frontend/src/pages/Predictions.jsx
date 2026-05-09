import { useState, useEffect } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, ProbabilityBar, Select } from '../components/UI.jsx';
import { 
  predictSafetyCar, predictPitStop, predictTyreStrategy, getMLStatus 
} from '../api/api.js';
import { 
  Shield, Timer, Disc, Activity, AlertTriangle, Trophy 
} from 'lucide-react';

function PredictionCard({ icon: Icon, title, color, children }) {
  return (
    <div style={{
      background: 'var(--f1-surface)',
      border: `1px solid ${color}25`,
      borderTop: `3px solid ${color}`,
      borderRadius: 4,
      overflow: 'hidden',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--f1-border)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <Icon size={16} color={color} />
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-muted)' }}>{title}</span>
      </div>
      <div style={{ padding: 18, flex: 1 }}>{children}</div>
    </div>
  );
}

function ResultBox({ result, color, type = 'prob' }) {
  if (!result) return null;

  if (type === 'list') {
    return (
      <div style={{ marginTop: 16, padding: 16, background: 'var(--f1-surface-2)', borderRadius: 4, border: '1px solid var(--f1-border)' }}>
        <span style={{ fontSize: 11, color: 'var(--f1-text-muted)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>Recomendación</span>
        {result.map((item, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontWeight: 700, fontSize: 13 }}>{item.compound}</span>
              <span style={{ color, fontSize: 12, fontWeight: 700 }}>{Math.round(item.probability * 100)}%</span>
            </div>
            <div className="prob-bar" style={{ height: 4 }}>
              <div className="prob-bar-fill" style={{ width: `${item.probability * 100}%`, background: color }} />
            </div>
          </div>
        ))}
      </div>
    );
  }

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
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 14 }}>
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
      </div>
    </div>
  );
}

export default function Predictions() {
  const [modelStatus, setModelStatus] = useState(null);
  const [loading, setLoading] = useState({});
  const [results, setResults] = useState({});
  const [errors, setErrors] = useState({});

  // Unified Form for ML Features
  const [form, setForm] = useState({
    Year: 2023,
    TyreLife: 12,
    LapTime: 92.5,
    LapDelta: 0.2,
    RollingLapTime: 92.3,
    TrackTemp: 34.5,
    Rainfall: 0,
    Compound: 'MEDIUM'
  });

  useEffect(() => {
    getMLStatus().then(setModelStatus).catch(() => {});
  }, []);

  const run = async (key, fn) => {
    setLoading(l => ({ ...l, [key]: true }));
    setErrors(e => ({ ...e, [key]: null }));
    try {
      const res = await fn(form);
      setResults(r => ({ ...r, [key]: res }));
    } catch (e) {
      setErrors(er => ({ ...er, [key]: e.response?.data?.detail || e.message }));
    } finally {
      setLoading(l => ({ ...l, [key]: false }));
    }
  };

  const Field = ({ label, name, step = 'any', type = 'number' }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-dim)' }}>{label}</label>
      <input
        type={type}
        step={step}
        value={form[name]}
        onChange={e => setForm(f => ({ ...f, [name]: type === 'number' ? parseFloat(e.target.value) : e.target.value }))}
        className="input-f1"
        style={{ padding: '6px 10px', fontSize: 12 }}
      />
    </div>
  );

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Predicciones IA" subtitle="Modelos basados en FastF1, Polars y XGBoost">
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
        
        {/* Parametros de Entrada */}
        <SectionCard title="Condiciones Actuales (Input de Telemetría)">
          <div className="grid-4" style={{ gap: 16 }}>
            <Field label="Año" name="Year" />
            <Field label="Vueltas Neumático" name="TyreLife" />
            <Field label="Tiempo Vuelta (s)" name="LapTime" />
            <Field label="Delta Vuelta (s)" name="LapDelta" />
            <Field label="Media Móvil 3v (s)" name="RollingLapTime" />
            <Field label="Temp. Pista (°C)" name="TrackTemp" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-dim)' }}>Lluvia</label>
              <Select 
                value={form.Rainfall} 
                onChange={v => setForm(f => ({ ...f, Rainfall: parseInt(v) }))}
                options={[{value: 0, label: 'No'}, {value: 1, label: 'Sí'}]}
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-dim)' }}>Compuesto Actual</label>
              <Select 
                value={form.Compound} 
                onChange={v => setForm(f => ({ ...f, Compound: v }))}
                options={[
                  {value: 'SOFT', label: 'Blando (S)'},
                  {value: 'MEDIUM', label: 'Medio (M)'},
                  {value: 'HARD', label: 'Duro (H)'}
                ]}
              />
            </div>
          </div>
        </SectionCard>

        <div className="grid-3" style={{ alignItems: 'stretch' }}>
          {/* Parada en Boxes */}
          <PredictionCard icon={Timer} title="Probabilidad de Parada" color="var(--f1-red)">
            <p style={{ fontSize: 12, color: 'var(--f1-text-muted)', marginBottom: 16 }}>Predice si el piloto entrará en boxes en la siguiente vuelta basado en degradación.</p>
            <button className="btn-primary" style={{ width: '100%' }}
              onClick={() => run('pit', predictPitStop)}
              disabled={loading.pit}>
              {loading.pit ? 'Analizando...' : 'Calcular Probabilidad'}
            </button>
            {errors.pit && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 8 }}>⚠ {errors.pit}</div>}
            <ResultBox result={results.pit} color="var(--f1-red)" />
          </PredictionCard>

          {/* Estrategia Neumaticos */}
          <PredictionCard icon={Disc} title="Recomendación de Neumáticos" color="#27F4D2">
            <p style={{ fontSize: 12, color: 'var(--f1-text-muted)', marginBottom: 16 }}>Sugerencia del mejor compuesto para el siguiente stint según condiciones.</p>
            <button className="btn-primary" style={{ width: '100%', background: '#27F4D2', color: '#000' }}
              onClick={() => run('tyre', predictTyreStrategy)}
              disabled={loading.tyre}>
              {loading.tyre ? 'Calculando...' : 'Ver Recomendación'}
            </button>
            {errors.tyre && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 8 }}>⚠ {errors.tyre}</div>}
            <ResultBox result={results.tyre} color="#27F4D2" type="list" />
          </PredictionCard>

          {/* Safety Car */}
          <PredictionCard icon={Shield} title="Riesgo de Safety Car" color="#FF8000">
            <p style={{ fontSize: 12, color: 'var(--f1-text-muted)', marginBottom: 16 }}>Probabilidad de SC/VSC en las próximas vueltas basado en historial y clima.</p>
            <button className="btn-primary" style={{ width: '100%', background: '#FF8000' }}
              onClick={() => run('sc', predictSafetyCar)}
              disabled={loading.sc}>
              {loading.sc ? 'Escaneando...' : 'Evaluar Riesgo'}
            </button>
            {errors.sc && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 8 }}>⚠ {errors.sc}</div>}
            <ResultBox result={results.sc} color="#FF8000" />
          </PredictionCard>
        </div>

        {/* Telemetry Insight */}
        <SectionCard title="Análisis de Telemetría e Inteligencia de Carrera">
          <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <Activity size={20} color="var(--f1-red)" />
                <h3 style={{ margin: 0, fontSize: 16 }}>Estado del Monoplaza</h3>
              </div>
              <p style={{ fontSize: 13, color: 'var(--f1-text-muted)', lineHeight: 1.5 }}>
                Basado en el <strong>Delta de Vuelta ({form.LapDelta}s)</strong> y la <strong>Media Móvil ({form.RollingLapTime}s)</strong>, el sistema detecta 
                {form.LapDelta > 0.5 ? ' una degradación crítica ' : ' un ritmo constante '} 
                en el compuesto <strong>{form.Compound}</strong>. La temperatura de pista de <strong>{form.TrackTemp}°C</strong> sugiere un desgaste 
                {form.TrackTemp > 40 ? ' acelerado ' : ' moderado '} por ampollamiento (blistering).
              </p>
            </div>
            <div style={{ width: 200, padding: 16, background: 'var(--f1-surface-2)', borderRadius: 4, textAlign: 'center' }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--f1-text-dim)', textTransform: 'uppercase' }}>Efficiency Index</span>
              <div style={{ fontSize: 32, fontWeight: 900, color: '#27F4D2', margin: '8px 0' }}>84.2</div>
              <span style={{ fontSize: 11, color: '#27F4D2' }}>OPTIMAL</span>
            </div>
          </div>
        </SectionCard>

      </div>
    </div>
  );
}
