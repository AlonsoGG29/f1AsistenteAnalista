import { useState, useEffect } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, EmptyState, Select, Input, YEARS } from '../components/UI.jsx';
import { getDrivers, getHeadToHead, getDriverLapProgression, getRaces, getRaceLapTimes } from '../api/api.js';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  ScatterChart, Scatter, CartesianGrid
} from 'recharts';

const DRIVER_COLORS = ['#E8002D', '#27F4D2', '#FF8000', '#3671C6', '#FFD700'];

export default function Analysis() {
  const [tab, setTab] = useState('h2h');
  const [year, setYear] = useState(2024);
  const [drivers, setDrivers] = useState([]);
  const [driverA, setDriverA] = useState('');
  const [driverB, setDriverB] = useState('');
  const [h2hData, setH2hData] = useState(null);
  const [lapProg, setLapProg] = useState([]);
  const [lapDriver, setLapDriver] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDrivers({ page_size: 200 }).then(d => setDrivers(d.items || []));
  }, []);

  const driverOptions = drivers.map(d => ({
    value: String(d.driver_id),
    label: `${d.forename} ${d.surname}`,
  }));

  const runH2H = () => {
    if (!driverA || !driverB) return;
    setLoading(true); setError(null);
    getHeadToHead(driverA, driverB, year || undefined)
      .then(setH2hData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  const runLapProg = () => {
    if (!lapDriver || !year) return;
    setLoading(true); setError(null);
    getDriverLapProgression(lapDriver, year)
      .then(setLapProg)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Análisis" subtitle="Comparativas, tiempos de vuelta y estadísticas avanzadas" />

      <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Tab bar */}
        <div style={{ display: 'flex', gap: 0, border: '1px solid var(--f1-border)', borderRadius: 4, overflow: 'hidden', width: 'fit-content' }}>
          {[
            { id: 'h2h', label: 'Head to Head' },
            { id: 'lapprog', label: 'Progresión de tiempos' },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              padding: '8px 20px',
              background: tab === t.id ? 'var(--f1-red)' : 'var(--f1-surface)',
              color: tab === t.id ? 'white' : 'var(--f1-text-muted)',
              border: 'none', cursor: 'pointer',
              fontSize: 12, fontWeight: 700, fontFamily: 'Titillium Web, sans-serif',
              letterSpacing: '0.06em', textTransform: 'uppercase',
            }}>{t.label}</button>
          ))}
        </div>

        {error && <ErrorBanner message={error} />}

        {/* Head to Head */}
        {tab === 'h2h' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <SectionCard title="Configurar comparativa">
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>Piloto A</div>
                  <Select value={driverA} onChange={setDriverA} options={driverOptions} placeholder="Seleccionar..." />
                </div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--f1-red)', paddingBottom: 10 }}>VS</div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>Piloto B</div>
                  <Select value={driverB} onChange={setDriverB} options={driverOptions} placeholder="Seleccionar..." />
                </div>
                <div style={{ minWidth: 100 }}>
                  <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>Temporada</div>
                  <Select value={year} onChange={v => setYear(Number(v))} options={[{ value: '', label: 'Todas' }, ...YEARS]} style={{ width: 100 }} />
                </div>
                <button className="btn-primary" onClick={runH2H} disabled={!driverA || !driverB || loading}>
                  {loading ? '...' : 'Comparar'}
                </button>
              </div>
            </SectionCard>

            {loading && <LoadingPane />}

            {h2hData && !loading && (
              <div className="grid-2">
                {/* Stats comparison */}
                <SectionCard title="Estadísticas comparadas">
                  <div style={{ display: 'flex', gap: 16 }}>
                    {/* Driver A */}
                    <div style={{ flex: 1, textAlign: 'center', padding: 16, background: 'rgba(232,0,45,0.05)', borderRadius: 4, border: '1px solid rgba(232,0,45,0.2)' }}>
                      <div style={{ fontSize: 11, color: 'var(--f1-red)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12 }}>
                        {h2hData.driver_a?.name || 'Piloto A'}
                      </div>
                      {[
                        { label: 'Victorias', value: h2hData.driver_a?.wins },
                        { label: 'Podios', value: h2hData.driver_a?.podiums },
                        { label: 'Puntos', value: h2hData.driver_a?.total_points },
                        { label: 'Pos. media', value: h2hData.driver_a?.avg_position?.toFixed(1) },
                        { label: 'Mejor salida', value: h2hData.driver_a?.best_grid },
                      ].map(({ label, value }) => (
                        <div key={label} style={{ marginBottom: 10 }}>
                          <div className="stat-label">{label}</div>
                          <div className="stat-value red" style={{ fontSize: 18 }}>{value ?? '—'}</div>
                        </div>
                      ))}
                    </div>

                    {/* Driver B */}
                    <div style={{ flex: 1, textAlign: 'center', padding: 16, background: 'rgba(39,244,210,0.05)', borderRadius: 4, border: '1px solid rgba(39,244,210,0.2)' }}>
                      <div style={{ fontSize: 11, color: '#27F4D2', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12 }}>
                        {h2hData.driver_b?.name || 'Piloto B'}
                      </div>
                      {[
                        { label: 'Victorias', value: h2hData.driver_b?.wins },
                        { label: 'Podios', value: h2hData.driver_b?.podiums },
                        { label: 'Puntos', value: h2hData.driver_b?.total_points },
                        { label: 'Pos. media', value: h2hData.driver_b?.avg_position?.toFixed(1) },
                        { label: 'Mejor salida', value: h2hData.driver_b?.best_grid },
                      ].map(({ label, value }) => (
                        <div key={label} style={{ marginBottom: 10 }}>
                          <div className="stat-label">{label}</div>
                          <div className="stat-value" style={{ fontSize: 18, color: '#27F4D2' }}>{value ?? '—'}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{ marginTop: 14, padding: '10px 14px', background: 'var(--f1-surface-2)', borderRadius: 4, fontSize: 12, color: 'var(--f1-text-muted)' }}>
                    Carreras compartidas: <strong style={{ color: 'var(--f1-text)' }}>{h2hData.shared_races ?? '—'}</strong>
                  </div>
                </SectionCard>

                {/* Head to head race wins */}
                <SectionCard title="Duelos directos">
                  {h2hData.race_wins_a !== undefined ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, paddingTop: 8 }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
                          <span style={{ color: 'var(--f1-red)', fontWeight: 700 }}>{h2hData.driver_a?.name}</span>
                          <span style={{ color: 'var(--f1-text-muted)' }}>{h2hData.race_wins_a} victorias</span>
                        </div>
                        <div style={{ height: 8, background: 'var(--f1-surface-3)', borderRadius: 4, overflow: 'hidden' }}>
                          <div style={{
                            height: '100%',
                            background: 'var(--f1-red)',
                            width: `${h2hData.shared_races > 0 ? (h2hData.race_wins_a / h2hData.shared_races * 100) : 0}%`,
                            transition: 'width 0.8s cubic-bezier(0.16,1,0.3,1)',
                          }} />
                        </div>
                      </div>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
                          <span style={{ color: '#27F4D2', fontWeight: 700 }}>{h2hData.driver_b?.name}</span>
                          <span style={{ color: 'var(--f1-text-muted)' }}>{h2hData.race_wins_b} victorias</span>
                        </div>
                        <div style={{ height: 8, background: 'var(--f1-surface-3)', borderRadius: 4, overflow: 'hidden' }}>
                          <div style={{
                            height: '100%',
                            background: '#27F4D2',
                            width: `${h2hData.shared_races > 0 ? (h2hData.race_wins_b / h2hData.shared_races * 100) : 0}%`,
                            transition: 'width 0.8s cubic-bezier(0.16,1,0.3,1)',
                          }} />
                        </div>
                      </div>
                      <div style={{ marginTop: 8, fontSize: 11, color: 'var(--f1-text-dim)', textAlign: 'center' }}>
                        {h2hData.shared_races} carreras disputadas juntos
                      </div>
                    </div>
                  ) : (
                    <EmptyState message="Sin datos de duelos directos" />
                  )}
                </SectionCard>
              </div>
            )}
          </div>
        )}

        {/* Lap progression */}
        {tab === 'lapprog' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <SectionCard title="Progresión de tiempos de vuelta por temporada">
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>Piloto</div>
                  <Select value={lapDriver} onChange={setLapDriver} options={driverOptions} placeholder="Seleccionar piloto..." />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>Año</div>
                  <Select value={year} onChange={v => setYear(Number(v))} options={YEARS} style={{ width: 100 }} />
                </div>
                <button className="btn-primary" onClick={runLapProg} disabled={!lapDriver || loading}>
                  {loading ? '...' : 'Analizar'}
                </button>
              </div>
            </SectionCard>

            {loading && <LoadingPane />}

            {lapProg.length > 0 && !loading && (
              <SectionCard title="Tiempo medio de vuelta por carrera">
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={lapProg} margin={{ top: 4, right: 20, bottom: 0, left: -10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="race_name" tick={{ fill: 'var(--f1-text-muted)', fontSize: 9 }} angle={-45} textAnchor="end" height={60} />
                      <YAxis tick={{ fill: 'var(--f1-text-muted)', fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{ background: 'var(--f1-surface-2)', border: '1px solid var(--f1-border)', borderRadius: 4, fontSize: 11 }}
                        formatter={(v) => [v ? `${(v / 1000).toFixed(3)}s` : '—', 'Tiempo medio']}
                      />
                      <Line type="monotone" dataKey="avg_ms" stroke="var(--f1-red)" strokeWidth={2} dot={{ r: 3, fill: 'var(--f1-red)' }} connectNulls />
                      <Line type="monotone" dataKey="best_ms" stroke="#27F4D2" strokeWidth={2} dot={{ r: 3, fill: '#27F4D2' }} strokeDasharray="4 2" connectNulls />
                      <Legend formatter={(v) => v === 'avg_ms' ? 'Tiempo medio' : 'Mejor tiempo'} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </SectionCard>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
