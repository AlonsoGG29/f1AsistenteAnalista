import { useState, useEffect } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, ProbabilityBar, Select } from '../components/UI.jsx';
import { 
  predictSafetyCar, predictPitStop, predictTyreStrategy, getMLStatus 
} from '../api/api.js';
import { 
  Shield, Timer, Disc, Activity 
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
  
  if (result.error) {
    return (
      <div style={{ marginTop: 16 }}>
        <ErrorBanner message={result.error} />
      </div>
    );
  }

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

  const probValue = typeof result.probability === 'number' ? result.probability : 0;
  const pct = Math.round(probValue * 100);

  return (
    <div style={{ marginTop: 16, padding: 16, background: 'var(--f1-surface-2)', borderRadius: 4, border: '1px solid var(--f1-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 11, color: 'var(--f1-text-muted)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Resultado</span>
        <span className={`badge ${result.label ? 'badge-red' : 'badge-gray'}`}>
          {result.label ? 'SÍ' : 'NO'}
        </span>
      </div>
      <ProbabilityBar value={probValue} label="Probabilidad" color={color} />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 14 }}>
        <div className="stat-box">
          <span className="stat-label">Prob.</span>
          <span className="stat-value" style={{ fontSize: 20, color }}>{pct}%</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Confianza</span>
          <span className="stat-value" style={{ fontSize: 14, color: result.confidence === 'alta' ? '#27F4D2' : result.confidence === 'media' ? '#FF8000' : 'var(--f1-text-muted)' }}>
            {result.confidence?.toUpperCase() || '—'}
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

  // Individual forms for each card
  const [pitForm, setPitForm] = useState({ 
    Year: 2023, 
    TyreLife: 15, 
    LapTime: '1:32.500', 
    LapDelta: 0.3, 
    RollingLapTime: '1:32.200', 
    TrackTemp: 35, 
    Rainfall: 0,
    Compound: 'MEDIUM'
  });
  
  const [tyreForm, setTyreForm] = useState({ 
    Year: 2023, 
    TyreLife: 20, 
    TrackTemp: 32, 
    Rainfall: 0,
    Compound: 'SOFT'
  });
  
  const [scForm, setScForm] = useState({ 
    Year: 2023, 
    TrackType: 'Street', 
    TrackTemp: 30, 
    Rainfall: 0 
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

  const InlineField = ({ label, value, onChange, type = 'number', step = 'any', placeholder }) => (
    <div style={{ marginBottom: 10 }}>
      <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>{label}</label>
      <input
        type={type}
        step={step}
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(type === 'number' ? parseFloat(e.target.value) : e.target.value)}
        className="input-f1"
        style={{ padding: '4px 8px', fontSize: 11, width: '100%' }}
      />
    </div>
  );

  const CompoundSelect = ({ value, onChange }) => (
    <div style={{ marginBottom: 10 }}>
      <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Compuesto</label>
      <Select 
        value={value} 
        onChange={onChange}
        options={[
          {value: 'SOFT', label: 'SOFT (Rojo)'},
          {value: 'MEDIUM', label: 'MEDIUM (Amarillo)'},
          {value: 'HARD', label: 'HARD (Blanco)'},
          {value: 'INTERMEDIATE', label: 'INTERMEDIATE (Verde)'},
          {value: 'WET', label: 'WET (Azul)'},
        ]}
        style={{ width: '100%', fontSize: 11, padding: '4px 8px' }}
      />
    </div>
  );

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Predicciones IA" subtitle="Análisis avanzado con FastF1 y XGBoost">
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
        
        <div className="grid-3" style={{ alignItems: 'start' }}>
          {/* Parada en Boxes */}
          <PredictionCard icon={Timer} title="Probabilidad de Parada" color="var(--f1-red)">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <InlineField label="Vueltas Neum." value={pitForm.TyreLife} onChange={v => setPitForm(f => ({ ...f, TyreLife: v }))} />
              <InlineField label="Delta (s)" value={pitForm.LapDelta} onChange={v => setPitForm(f => ({ ...f, LapDelta: v }))} />
              <InlineField label="Tiempo Vuelta" type="text" placeholder="min:ss.ms" value={pitForm.LapTime} onChange={v => setPitForm(f => ({ ...f, LapTime: v }))} />
              <InlineField label="Temp. Pista" value={pitForm.TrackTemp} onChange={v => setPitForm(f => ({ ...f, TrackTemp: v }))} />
            </div>
            <CompoundSelect value={pitForm.Compound} onChange={v => setPitForm(f => ({ ...f, Compound: v }))} />
            <button className="btn-primary" style={{ width: '100%' }}
              onClick={() => run('pit', predictPitStop, pitForm)}
              disabled={loading.pit}>
              {loading.pit ? 'Analizando...' : 'Calcular Probabilidad'}
            </button>
            {errors.pit && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 8 }}>⚠ {errors.pit}</div>}
            <ResultBox result={results.pit} color="var(--f1-red)" />
          </PredictionCard>

          {/* Estrategia Neumaticos */}
          <PredictionCard icon={Disc} title="Recomendación de Neumáticos" color="#27F4D2">
             <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <InlineField label="Vueltas Rest." value={tyreForm.TyreLife} onChange={v => setTyreForm(f => ({ ...f, TyreLife: v }))} />
              <InlineField label="Temp. Pista" value={tyreForm.TrackTemp} onChange={v => setTyreForm(f => ({ ...f, TrackTemp: v }))} />
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Lluvia</label>
                <Select 
                  value={tyreForm.Rainfall} 
                  onChange={v => setTyreForm(f => ({ ...f, Rainfall: parseInt(v) }))}
                  options={[{value: 0, label: 'Seco'}, {value: 1, label: 'Lluvia'}]}
                  style={{ width: '100%', fontSize: 11, padding: '4px 8px' }}
                />
              </div>
            </div>
            <button className="btn-primary" style={{ width: '100%', background: '#27F4D2', color: '#000' }}
              onClick={() => run('tyre', predictTyreStrategy, tyreForm)}
              disabled={loading.tyre}>
              {loading.tyre ? 'Calculando...' : 'Ver Recomendación'}
            </button>
            {errors.tyre && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 8 }}>⚠ {errors.tyre}</div>}
            <ResultBox result={results.tyre} color="#27F4D2" type="list" />
          </PredictionCard>

          {/* Safety Car */}
          <PredictionCard icon={Shield} title="Riesgo de Safety Car" color="#FF8000">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Tipo de Circuito</label>
                <Select 
                  value={scForm.TrackType} 
                  onChange={v => setScForm(f => ({ ...f, TrackType: v }))}
                  options={[{value: 'Permanent', label: 'Permanente (Spa, Monza...)'}, {value: 'Street', label: 'Urbano (Mónaco, Singapur...)'}]}
                  style={{ width: '100%', fontSize: 11, padding: '4px 8px' }}
                />
              </div>
              <InlineField label="Temp. Pista" value={scForm.TrackTemp} onChange={v => setScForm(f => ({ ...f, TrackTemp: v }))} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Lluvia</label>
                <Select 
                  value={scForm.Rainfall} 
                  onChange={v => setScForm(f => ({ ...f, Rainfall: parseInt(v) }))}
                  options={[{value: 0, label: 'No'}, {value: 1, label: 'Sí'}]}
                  style={{ width: '100%', fontSize: 11, padding: '4px 8px' }}
                />
              </div>
            </div>
            <button className="btn-primary" style={{ width: '100%', background: '#FF8000' }}
              onClick={() => run('sc', predictSafetyCar, scForm)}
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
                El motor de inferencia ha sido actualizado con soporte para compuestos de lluvia (Intermediate/Wet) y distinción de circuitos urbanos. 
                El tiempo de vuelta ingresado como <strong>{pitForm.LapTime}</strong> es procesado internamente para evaluar el ritmo relativo. 
                Los circuitos urbanos como <strong>{scForm.TrackType === 'Street' ? 'Mónaco o Singapur' : 'Circuitos permanentes'}</strong> tienen un multiplicador de riesgo de incidentes del 50% adicional.
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
