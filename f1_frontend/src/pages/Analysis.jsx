import { useState, useEffect, useRef } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, EmptyState, Select, Input, YEARS } from '../components/UI.jsx';
import { getDrivers, getHeadToHead, getDriverLapProgression } from '../api/api.js';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  CartesianGrid
} from 'recharts';

// ── Autocomplete driver picker ────────────────────────────────────────────────
function DriverPicker({ label, value, onChange, drivers, accentColor = 'var(--f1-red)' }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Display name of selected driver
  const selected = drivers.find(d => d.driverId === value);
  const displayName = selected ? `${selected.forename} ${selected.surname}` : '';

  // Close on outside click
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const filtered = query.length >= 1
    ? drivers.filter(d =>
        `${d.forename} ${d.surname}`.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 10)
    : [];

  const handleSelect = (driver) => {
    onChange(driver.driverId);
    setQuery('');
    setOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setQuery('');
  };

  return (
    <div style={{ flex: 1, minWidth: 200, position: 'relative' }} ref={ref}>
      <div style={{
        fontSize: 10, color: 'var(--f1-text-dim)', fontWeight: 700,
        letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6,
      }}>
        {label}
      </div>

      {value ? (
        // Show selected driver as a chip
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'var(--f1-surface-2)', border: `1px solid ${accentColor}44`,
          borderRadius: 4, padding: '8px 12px', height: 38,
        }}>
          <div style={{
            width: 8, height: 8, borderRadius: 2,
            background: accentColor, flexShrink: 0,
          }} />
          <span style={{ flex: 1, fontSize: 13, fontWeight: 600 }}>{displayName}</span>
          <button
            onClick={handleClear}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--f1-text-dim)', fontSize: 16, lineHeight: 1, padding: 0,
            }}
          >×</button>
        </div>
      ) : (
        // Search input
        <div>
          <input
            className="input-f1"
            value={query}
            onChange={e => { setQuery(e.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            placeholder="Escribir nombre..."
            style={{ width: '100%' }}
          />
          {open && filtered.length > 0 && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
              background: 'var(--f1-surface-2)', border: '1px solid var(--f1-border)',
              borderRadius: 4, marginTop: 2, maxHeight: 220, overflowY: 'auto',
              boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            }}>
              {filtered.map(d => (
                <div
                  key={d.driverId}
                  onMouseDown={() => handleSelect(d)}
                  style={{
                    padding: '8px 12px', cursor: 'pointer', fontSize: 13,
                    borderBottom: '1px solid var(--f1-border)',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <span style={{ fontWeight: 600 }}>{d.forename} {d.surname}</span>
                  {d.nationality && (
                    <span style={{ fontSize: 11, color: 'var(--f1-text-dim)', marginLeft: 8 }}>
                      {d.nationality}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Stat box for H2H ──────────────────────────────────────────────────────────
function H2HStat({ label, valueA, valueB, higherIsBetter = true }) {
  const numA = parseFloat(valueA);
  const numB = parseFloat(valueB);
  const aWins = higherIsBetter ? numA > numB : numA < numB;
  const bWins = higherIsBetter ? numB > numA : numB < numA;
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1fr auto 1fr',
      gap: 8, alignItems: 'center', padding: '8px 0',
      borderBottom: '1px solid var(--f1-border)',
    }}>
      <span style={{
        fontSize: 15, fontWeight: 700, color: aWins ? 'var(--f1-red)' : 'var(--f1-text-muted)',
        textAlign: 'right',
      }}>{valueA ?? '—'}</span>
      <span style={{
        fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase',
        color: 'var(--f1-text-dim)', textAlign: 'center', minWidth: 80,
      }}>{label}</span>
      <span style={{
        fontSize: 15, fontWeight: 700, color: bWins ? '#27F4D2' : 'var(--f1-text-muted)',
        textAlign: 'left',
      }}>{valueB ?? '—'}</span>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function Analysis() {
  const [tab, setTab] = useState('h2h');
  const [year, setYear] = useState(2024);
  const [drivers, setDrivers] = useState([]);
  const [driverA, setDriverA] = useState(null);
  const [driverB, setDriverB] = useState(null);
  const [h2hData, setH2hData] = useState(null);
  const [lapProg, setLapProg] = useState([]);
  const [lapDriver, setLapDriver] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDrivers({ page_size: 1000 }).then(d => setDrivers(d.items || []));
  }, []);

  const runH2H = () => {
    if (!driverA || !driverB) return;
    setLoading(true); setError(null); setH2hData(null);
    getHeadToHead(driverA, driverB, year || undefined)
      .then(setH2hData)
      .catch(e => setError(e.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  };

  const runLapProg = () => {
    if (!lapDriver || !year) return;
    setLoading(true); setError(null); setLapProg([]);
    getDriverLapProgression(lapDriver, year)
      .then(data => setLapProg(data || []))
      .catch(e => setError(e.response?.data?.detail || e.message))
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

        {/* ── Head to Head ───────────────────────────────────────────────── */}
        {tab === 'h2h' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <SectionCard title="Configurar comparativa">
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <DriverPicker
                  label="Piloto A"
                  value={driverA}
                  onChange={setDriverA}
                  drivers={drivers}
                  accentColor="var(--f1-red)"
                />
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--f1-red)', paddingBottom: 10 }}>VS</div>
                <DriverPicker
                  label="Piloto B"
                  value={driverB}
                  onChange={setDriverB}
                  drivers={drivers}
                  accentColor="#27F4D2"
                />
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

            {h2hData && !loading && (() => {
              const nameA = h2hData.driver_a_name || 'Piloto A';
              const nameB = h2hData.driver_b_name || 'Piloto B';
              const total = h2hData.races_together || 0;
              const winsA = h2hData.driver_a_wins ?? 0;
              const winsB = h2hData.driver_b_wins ?? 0;
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* Header chips */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 8, alignItems: 'center' }}>
                    <div style={{
                      padding: '12px 16px', background: 'rgba(232,0,45,0.08)',
                      border: '1px solid rgba(232,0,45,0.25)', borderRadius: 4, textAlign: 'center',
                    }}>
                      <div style={{ fontSize: 11, color: 'var(--f1-red)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Piloto A</div>
                      <div style={{ fontSize: 18, fontWeight: 900, marginTop: 4 }}>{nameA}</div>
                    </div>
                    <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--f1-text-dim)' }}>
                      <div style={{ fontSize: 22, fontWeight: 900, color: 'var(--f1-red)' }}>VS</div>
                      <div style={{ marginTop: 4 }}>{total} carreras</div>
                    </div>
                    <div style={{
                      padding: '12px 16px', background: 'rgba(39,244,210,0.08)',
                      border: '1px solid rgba(39,244,210,0.25)', borderRadius: 4, textAlign: 'center',
                    }}>
                      <div style={{ fontSize: 11, color: '#27F4D2', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Piloto B</div>
                      <div style={{ fontSize: 18, fontWeight: 900, marginTop: 4 }}>{nameB}</div>
                    </div>
                  </div>

                  <div className="grid-2">
                    {/* Stats table */}
                    <SectionCard title="Estadísticas comparadas">
                      <div style={{ fontSize: 11, display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 8, marginBottom: 8 }}>
                        <span style={{ textAlign: 'right', color: 'var(--f1-red)', fontWeight: 700 }}>{nameA}</span>
                        <span />
                        <span style={{ color: '#27F4D2', fontWeight: 700 }}>{nameB}</span>
                      </div>
                      <H2HStat label="Victorias" valueA={winsA} valueB={winsB} />
                      <H2HStat label="Podios" valueA={h2hData.driver_a_podiums ?? 0} valueB={h2hData.driver_b_podiums ?? 0} />
                      <H2HStat label="Poles" valueA={h2hData.driver_a_poles ?? 0} valueB={h2hData.driver_b_poles ?? 0} />
                      <H2HStat label="Pos. media" valueA={h2hData.driver_a_avg_position?.toFixed(2)} valueB={h2hData.driver_b_avg_position?.toFixed(2)} higherIsBetter={false} />
                      <H2HStat label="Clasif. media" valueA={h2hData.driver_a_avg_grid?.toFixed(2) ?? '—'} valueB={h2hData.driver_b_avg_grid?.toFixed(2) ?? '—'} higherIsBetter={false} />
                      <H2HStat label="Puntos totales" valueA={h2hData.driver_a_total_points} valueB={h2hData.driver_b_total_points} />
                      {(h2hData.driver_a_teammate_name || h2hData.driver_b_teammate_name) && (
                        <H2HStat 
                          label="Dif. vs Compañero" 
                          valueA={h2hData.driver_a_teammate_name 
                            ? `${h2hData.driver_a_teammate_diff > 0 ? '+' : ''}${h2hData.driver_a_teammate_diff?.toFixed(1)}` 
                            : '—'
                          } 
                          valueB={h2hData.driver_b_teammate_name 
                            ? `${h2hData.driver_b_teammate_diff > 0 ? '+' : ''}${h2hData.driver_b_teammate_diff?.toFixed(1)}` 
                            : '—'
                          } 
                        />
                      )}
                      <H2HStat label="Abandonos" valueA={h2hData.driver_a_dnfs ?? 0} valueB={h2hData.driver_b_dnfs ?? 0} higherIsBetter={false} />
                    </SectionCard>

                    {/* Win bars */}
                    <SectionCard title="Duelos directos">
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, paddingTop: 8 }}>
                        {[
                          { name: nameA, wins: winsA, color: 'var(--f1-red)' },
                          { name: nameB, wins: winsB, color: '#27F4D2' },
                        ].map(({ name, wins, color }) => (
                          <div key={name}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 8 }}>
                              <span style={{ color, fontWeight: 700 }}>{name}</span>
                              <span style={{ color: 'var(--f1-text-muted)' }}>{wins} victorias</span>
                            </div>
                            <div style={{ height: 10, background: 'var(--f1-surface-3)', borderRadius: 5, overflow: 'hidden' }}>
                              <div style={{
                                height: '100%', background: color, borderRadius: 5,
                                width: `${total > 0 ? (wins / total * 100) : 0}%`,
                                transition: 'width 0.8s cubic-bezier(0.16,1,0.3,1)',
                              }} />
                            </div>
                          </div>
                        ))}
                        <div style={{ fontSize: 11, color: 'var(--f1-text-dim)', textAlign: 'center' }}>
                          {total} carreras disputadas juntos
                        </div>
                      </div>
                    </SectionCard>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* ── Lap Progression ────────────────────────────────────────────── */}
        {tab === 'lapprog' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <SectionCard title="Progresión de tiempos de vuelta por temporada">
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <DriverPicker
                  label="Piloto"
                  value={lapDriver}
                  onChange={setLapDriver}
                  drivers={drivers}
                  accentColor="var(--f1-red)"
                />
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
                        formatter={(v) => [v ? `${(v / 1000).toFixed(3)}s` : '—', '']}
                      />
                      <Line type="monotone" dataKey="avg_lap_ms" name="Tiempo medio" stroke="var(--f1-red)" strokeWidth={2} dot={{ r: 3, fill: 'var(--f1-red)' }} connectNulls />
                      <Line type="monotone" dataKey="best_lap_ms" name="Mejor tiempo" stroke="#27F4D2" strokeWidth={2} dot={{ r: 3, fill: '#27F4D2' }} strokeDasharray="4 2" connectNulls />
                      <Legend />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </SectionCard>
            )}

            {lapProg.length === 0 && !loading && lapDriver && (
              <EmptyState message="Sin datos de tiempos de vuelta para este piloto y temporada" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
