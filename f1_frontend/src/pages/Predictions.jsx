import { useState, useEffect } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, ProbabilityBar, Select } from '../components/UI.jsx';
import { 
  predictSafetyCar, predictPitStop, predictTyreStrategy, getMLStatus 
} from '../api/api.js';
import { 
  Shield, Timer, Disc, Activity, AlertCircle, CheckCircle2
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
        <span style={{ fontSize: 11, color: 'var(--f1-text-muted)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>
          {type === 'list' ? 'Recomendaciones' : 'Resultado'}
        </span>
        {Array.isArray(result) ? result.map((item, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontWeight: 700, fontSize: 13 }}>{item.compound}</span>
              <span style={{ color, fontSize: 12, fontWeight: 700 }}>{Math.round(item.probability * 100)}%</span>
            </div>
            <div className="prob-bar" style={{ height: 4, background: color + '22', borderRadius: 2, overflow: 'hidden' }}>
              <div className="prob-bar-fill" style={{ width: `${item.probability * 100}%`, background: color, height: '100%' }} />
            </div>
          </div>
        )) : (
          <div style={{ color: 'var(--f1-text-muted)' }}>Sin datos</div>
        )}
      </div>
    );
  }

  const probValue = typeof result.probability === 'number' ? result.probability : 0;
  const pct = Math.round(probValue * 100);
  const confidenceColor = result.confidence === 'alta' ? '#27F4D2' : result.confidence === 'media' ? '#FF8000' : 'var(--f1-text-muted)';

  return (
    <div style={{ marginTop: 16, padding: 16, background: 'var(--f1-surface-2)', borderRadius: 4, border: '1px solid var(--f1-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 11, color: 'var(--f1-text-muted)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Predicción</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', background: result.label ? 'var(--f1-red)25' : 'var(--f1-text-dim)25', borderRadius: 4, fontSize: 11, fontWeight: 700 }}>
          {result.label ? <AlertCircle size={14} color="var(--f1-red)" /> : <CheckCircle2 size={14} color="var(--f1-text-muted)" />}
          {result.label ? 'ALTO RIESGO' : 'BAJO RIESGO'}
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
          <span className="stat-value" style={{ fontSize: 14, color: confidenceColor }}>
            {result.confidence?.toUpperCase() || '—'}
          </span>
        </div>
      </div>
      {result.description && (
        <div style={{ fontSize: 11, color: 'var(--f1-text-muted)', marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--f1-border)' }}>
          {result.description}
        </div>
      )}
    </div>
  );
}

export default function Predictions() {
  const [modelStatus, setModelStatus] = useState(null);
  const [loading, setLoading] = useState({});
  const [results, setResults] = useState({});
  const [errors, setErrors] = useState({});

  // Pit Stop Form
  const [pitForm, setPitForm] = useState({ 
    Year: 2024, 
    TyreLife: 15, 
    LapTime: '1:32.500', 
    LapDelta: 0.3, 
    RollingLapTime: '1:32.200', 
    TrackTemp: 35, 
    Rainfall: 0,
    TrackType: 'Permanent',
    Compound: 'MEDIUM'
  });
  
  // Tyre Form
  const [tyreForm, setTyreForm] = useState({ 
    Year: 2024, 
    TyreLife: 20, 
    LapTime: '1:33.000',
    LapDelta: 0.5,
    RollingLapTime: '1:32.500',
    TrackTemp: 32, 
    Rainfall: 0,
    TrackType: 'Permanent',
    Compound: 'SOFT'
  });
  
  // Safety Car Form
  const [scForm, setScForm] = useState({ 
    Circuit_Risk_Score: 0.3,
    Adjusted_Risk: 0.35,
    TrackType: 'Permanent', 
    TrackTemp_Avg: 30, 
    Rainfall_Any: 0
  });

  useEffect(() => {
    getMLStatus().then(data => {
      console.log('ML Status:', data);
      setModelStatus(data);
    }).catch(err => {
      console.error('Error fetching ML status:', err);
      setModelStatus({});
    });
  }, []);

  const run = async (key, fn, payload) => {
    setLoading(l => ({ ...l, [key]: true }));
    setErrors(e => ({ ...e, [key]: null }));
    try {
      console.log(`Running ${key} with payload:`, payload);
      const res = await fn(payload);
      console.log(`${key} result:`, res);
      setResults(r => ({ ...r, [key]: res }));
    } catch (e) {
      const errorMsg = e.response?.data?.detail || e.message || 'Error desconocido';
      console.error(`Error in ${key}:`, errorMsg);
      setErrors(er => ({ ...er, [key]: errorMsg }));
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
      <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Compuesto Actual</label>
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

  const ModelStatusBadge = ({ status, label }) => {
    const colors = {
      'ready': '#27F4D2',
      'not_available': 'var(--f1-red)',
      'fallback_heuristic': '#FF8000'
    };
    const labels = {
      'ready': '✓',
      'not_available': '✗',
      'fallback_heuristic': '⚠'
    };
    return (
      <span style={{ 
        padding: '4px 10px', 
        background: colors[status] + '22',
        color: colors[status],
        borderRadius: 4,
        fontSize: 10,
        fontWeight: 700,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4
      }}>
        {labels[status]} {label}
      </span>
    );
  };

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader 
        title="Predicciones IA" 
        subtitle="Análisis avanzado con FastF1, Polars y XGBoost"
      >
        {modelStatus && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {modelStatus.pit_stop && <ModelStatusBadge status={modelStatus.pit_stop} label="Pit Stops" />}
            {modelStatus.tyre_strategy && <ModelStatusBadge status={modelStatus.tyre_strategy} label="Neumáticos" />}
            {modelStatus.safety_car && <ModelStatusBadge status={modelStatus.safety_car} label="Safety Car" />}
          </div>
        )}
      </PageHeader>

      <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>
        
        <div className="grid-3" style={{ alignItems: 'start' }}>
          {/* Parada en Boxes */}
          <PredictionCard icon={Timer} title="Predicción de Pit Stop" color="var(--f1-red)">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
              <InlineField label="Vueltas Neumático" value={pitForm.TyreLife} onChange={v => setPitForm(f => ({ ...f, TyreLife: Math.max(0, v) }))} />
              <InlineField label="Delta (s)" value={pitForm.LapDelta} onChange={v => setPitForm(f => ({ ...f, LapDelta: v }))} />
              <InlineField label="Tiempo Vuelta" type="text" placeholder="min:ss.ms" value={pitForm.LapTime} onChange={v => setPitForm(f => ({ ...f, LapTime: v }))} />
              <InlineField label="Media Móvil" type="text" placeholder="min:ss.ms" value={pitForm.RollingLapTime} onChange={v => setPitForm(f => ({ ...f, RollingLapTime: v }))} />
              <InlineField label="Temp. Pista (°C)" value={pitForm.TrackTemp} onChange={v => setPitForm(f => ({ ...f, TrackTemp: v }))} />
              <div>
                <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Lluvia</label>
                <Select 
                  value={pitForm.Rainfall} 
                  onChange={v => setPitForm(f => ({ ...f, Rainfall: parseInt(v) }))}
                  options={[{value: 0, label: 'Seco'}, {value: 1, label: 'Lluvia'}]}
                  style={{ width: '100%', fontSize: 11, padding: '4px 8px' }}
                />
              </div>
            </div>
            <CompoundSelect value={pitForm.Compound} onChange={v => setPitForm(f => ({ ...f, Compound: v }))} />
            <button className="btn-primary" style={{ width: '100%' }}
              onClick={() => run('pit', predictPitStop, pitForm)}
              disabled={loading.pit}>
              {loading.pit ? '🔄 Analizando...' : '🎯 Calcular Probabilidad'}
            </button>
            {errors.pit && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 8 }}>❌ {errors.pit}</div>}
            <ResultBox result={results.pit} color="var(--f1-red)" />
          </PredictionCard>

          {/* Estrategia Neumáticos */}
          <PredictionCard icon={Disc} title="Estrategia de Neumáticos" color="#27F4D2">
             <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
              <InlineField label="Vueltas Restantes" value={tyreForm.TyreLife} onChange={v => setTyreForm(f => ({ ...f, TyreLife: Math.max(0, v) }))} />
              <InlineField label="Tiempo Vuelta" type="text" placeholder="min:ss.ms" value={tyreForm.LapTime} onChange={v => setTyreForm(f => ({ ...f, LapTime: v }))} />
              <InlineField label="Delta (s)" value={tyreForm.LapDelta} onChange={v => setTyreForm(f => ({ ...f, LapDelta: v }))} />
              <InlineField label="Media Móvil" type="text" placeholder="min:ss.ms" value={tyreForm.RollingLapTime} onChange={v => setTyreForm(f => ({ ...f, RollingLapTime: v }))} />
              <InlineField label="Temp. Pista (°C)" value={tyreForm.TrackTemp} onChange={v => setTyreForm(f => ({ ...f, TrackTemp: v }))} />
              <div>
                <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Condiciones</label>
                <Select 
                  value={tyreForm.Rainfall} 
                  onChange={v => setTyreForm(f => ({ ...f, Rainfall: parseInt(v) }))}
                  options={[{value: 0, label: 'Seco'}, {value: 1, label: 'Lluvia'}]}
                  style={{ width: '100%', fontSize: 11, padding: '4px 8px' }}
                />
              </div>
            </div>
            <button className="btn-primary" style={{ width: '100%', background: '#27F4D2', color: '#000', fontWeight: 700 }}
              onClick={() => run('tyre', predictTyreStrategy, tyreForm)}
              disabled={loading.tyre}>
              {loading.tyre ? '🔄 Calculando...' : '💡 Ver Recomendación'}
            </button>
            {errors.tyre && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 8 }}>❌ {errors.tyre}</div>}
            <ResultBox result={results.tyre} color="#27F4D2" type="list" />
          </PredictionCard>

          {/* Safety Car */}
          <PredictionCard icon={Shield} title="Riesgo de Safety Car" color="#FF8000">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Tipo de Circuito</label>
                <Select 
                  value={scForm.TrackType} 
                  onChange={v => setScForm(f => ({ ...f, TrackType: v }))}
                  options={[
                    {value: 'Permanent', label: 'Permanente (Spa, Monza, Silverstone...)'},
                    {value: 'Street', label: 'Urbano (Mónaco, Singapur, Jeddah...)'}
                  ]}
                  style={{ width: '100%', fontSize: 11, padding: '4px 8px' }}
                />
              </div>
              <InlineField label="Riesgo Histórico (0-1)" value={scForm.Circuit_Risk_Score} onChange={v => setScForm(f => ({ ...f, Circuit_Risk_Score: Math.max(0, Math.min(1, v)) }))} step="0.1" />
              <InlineField label="Riesgo Ajustado (0-1)" value={scForm.Adjusted_Risk} onChange={v => setScForm(f => ({ ...f, Adjusted_Risk: Math.max(0, Math.min(1, v)) }))} step="0.1" />
              <InlineField label="Temp. Pista (°C)" value={scForm.TrackTemp_Avg} onChange={v => setScForm(f => ({ ...f, TrackTemp_Avg: v }))} />
              <div>
                <label style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', display: 'block', marginBottom: 4 }}>Lluvia</label>
                <Select 
                  value={scForm.Rainfall_Any} 
                  onChange={v => setScForm(f => ({ ...f, Rainfall_Any: parseInt(v) }))}
                  options={[{value: 0, label: 'Seco'}, {value: 1, label: 'Lluvia'}]}
                  style={{ width: '100%', fontSize: 11, padding: '4px 8px' }}
                />
              </div>
            </div>
            <button className="btn-primary" style={{ width: '100%', background: '#FF8000', fontWeight: 700 }}
              onClick={() => run('sc', predictSafetyCar, scForm)}
              disabled={loading.sc}>
              {loading.sc ? '🔄 Escaneando...' : '⚠️  Evaluar Riesgo'}
            </button>
            {errors.sc && <div style={{ fontSize: 11, color: 'var(--f1-red)', marginTop: 8 }}>❌ {errors.sc}</div>}
            <ResultBox result={results.sc} color="#FF8000" />
          </PredictionCard>
        </div>

        {/* Información */}
        <SectionCard title="🤖 Sobre estos Modelos">
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
            <div>
              <h4 style={{ margin: '0 0 8px 0', fontSize: 14, fontWeight: 700 }}>Arquitectura ML</h4>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12, color: 'var(--f1-text-muted)', lineHeight: 1.6 }}>
                <li><strong>Ingesta:</strong> FastF1 API con manejo de rate limits</li>
                <li><strong>Features:</strong> Polars lazy evaluation + aggregations</li>
                <li><strong>Modelos:</strong> XGBoost con support para features categóricas</li>
                <li><strong>Pit Stops:</strong> Predicción binaria con datos a nivel de vuelta</li>
                <li><strong>Neumáticos:</strong> Clasificación multi-clase (HARD/MEDIUM/SOFT/INTER/WET)</li>
                <li><strong>Safety Car:</strong> Regresión logística a nivel de GP con risk scoring</li>
              </ul>
            </div>
            <div style={{ padding: 16, background: 'var(--f1-surface-2)', borderRadius: 4 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--f1-text-dim)', textTransform: 'uppercase', marginBottom: 8 }}>Datos de Entrenamiento</div>
              <div style={{ fontSize: 20, fontWeight: 900, color: '#27F4D2', marginBottom: 12 }}>2020-2024</div>
              <div style={{ fontSize: 11, color: 'var(--f1-text-muted)', lineHeight: 1.5 }}>
                <div>📊 1000+ carreras</div>
                <div>🏁 5000+ vueltas/carrera</div>
                <div>🎯 30+ features</div>
              </div>
            </div>
          </div>
        </SectionCard>

      </div>
    </div>
  );
}
