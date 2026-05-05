import { useState, useEffect, useCallback } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, EmptyState, TeamDot, Select, Input, YEARS } from '../components/UI.jsx';
import { getDrivers, getDriver, getDriverSeasonStats } from '../services/api.js';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Search, ChevronRight } from 'lucide-react';

export default function Drivers() {
  const [search, setSearch] = useState('');
  const [nationality, setNationality] = useState('');
  const [drivers, setDrivers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [driverDetail, setDriverDetail] = useState(null);
  const [seasonStats, setSeasonStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    const params = { page, page_size: 30 };
    if (search) params.search = search;
    if (nationality) params.nationality = nationality;
    getDrivers(params)
      .then(data => { setDrivers(data.items || []); setTotal(data.total || 0); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [search, nationality, page]);

  const loadDriver = useCallback((id) => {
    setSelectedDriver(id);
    setDetailLoading(true);
    Promise.all([
      getDriver(id).catch(() => null),
      getDriverSeasonStats(id).catch(() => []),
    ]).then(([detail, stats]) => {
      setDriverDetail(detail);
      setSeasonStats(stats || []);
    }).finally(() => setDetailLoading(false));
  }, []);

  const nationalities = ['British', 'German', 'Brazilian', 'Finnish', 'Spanish', 'French', 'Italian', 'Dutch', 'Australian', 'American'];

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Pilotos" subtitle={`${total} pilotos en la base de datos`} />

      <div style={{ padding: '24px 32px', display: 'flex', gap: 20 }}>
        {/* List */}
        <div style={{ flex: 1 }}>
          {/* Filters */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--f1-text-dim)' }} />
              <Input
                value={search}
                onChange={v => { setSearch(v); setPage(1); }}
                placeholder="Buscar piloto..."
                style={{ paddingLeft: 32 }}
              />
            </div>
            <Select
              value={nationality}
              onChange={v => { setNationality(v); setPage(1); }}
              options={nationalities.map(n => ({ value: n, label: n }))}
              placeholder="Todas las nacionalidades"
              style={{ width: 200 }}
            />
          </div>

          {error && <ErrorBanner message={error} />}

          <SectionCard>
            {loading ? <LoadingPane /> : drivers.length === 0 ? <EmptyState /> : (
              <div>
                {/* Table header */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 120px 80px 32px',
                  gap: 8,
                  padding: '0 0 8px',
                  borderBottom: '2px solid var(--f1-border)',
                  fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--f1-text-dim)',
                }}>
                  <span>Piloto</span>
                  <span>Nacionalidad</span>
                  <span>Nº</span>
                  <span></span>
                </div>
                {drivers.map((d, i) => (
                  <div
                    key={d.driver_id}
                    onClick={() => loadDriver(d.driver_id)}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 120px 80px 32px',
                      gap: 8,
                      alignItems: 'center',
                      padding: '9px 0',
                      borderBottom: '1px solid var(--f1-border)',
                      cursor: 'pointer',
                      background: selectedDriver === d.driver_id ? 'rgba(232,0,45,0.05)' : 'transparent',
                      borderLeft: selectedDriver === d.driver_id ? '3px solid var(--f1-red)' : '3px solid transparent',
                      paddingLeft: 6,
                      transition: 'all 0.1s',
                    }}
                    onMouseEnter={e => { if (selectedDriver !== d.driver_id) e.currentTarget.style.background = 'rgba(255,255,255,0.02)'; }}
                    onMouseLeave={e => { if (selectedDriver !== d.driver_id) e.currentTarget.style.background = 'transparent'; }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: 2,
                        background: 'var(--f1-surface-3)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 10, fontWeight: 700, color: 'var(--f1-red)',
                        fontFamily: 'Share Tech Mono, monospace',
                        flexShrink: 0,
                      }}>
                        {d.code || '—'}
                      </div>
                      <span style={{ fontSize: 13 }}>{d.forename} <strong>{d.surname}</strong></span>
                    </div>
                    <span style={{ fontSize: 12, color: 'var(--f1-text-muted)' }}>{d.nationality}</span>
                    <span className="mono" style={{ fontSize: 12, color: 'var(--f1-text-muted)' }}>#{d.number || '—'}</span>
                    <ChevronRight size={14} color="var(--f1-text-dim)" />
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          {/* Pagination */}
          {total > 30 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
              <button className="btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>← Anterior</button>
              <span style={{ padding: '8px 16px', fontSize: 12, color: 'var(--f1-text-muted)' }}>Pág. {page}</span>
              <button className="btn-ghost" onClick={() => setPage(p => p + 1)} disabled={page * 30 >= total}>Siguiente →</button>
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selectedDriver && (
          <div style={{ width: 360, flexShrink: 0 }}>
            {detailLoading ? (
              <SectionCard><LoadingPane /></SectionCard>
            ) : driverDetail ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {/* Driver header */}
                <div className="card card-red">
                  <div style={{ padding: '20px 18px' }}>
                    <div style={{ fontSize: 10, color: 'var(--f1-red)', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>
                      {driverDetail.code || '—'}
                    </div>
                    <h2 style={{ fontSize: 22, fontWeight: 900 }}>
                      {driverDetail.forename} {driverDetail.surname}
                    </h2>
                    <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      {[
                        { label: 'Nac.', value: driverDetail.nationality },
                        { label: 'Nº', value: driverDetail.number ? `#${driverDetail.number}` : '—' },
                        { label: 'F. nacimiento', value: driverDetail.dob || '—' },
                        { label: 'ID', value: driverDetail.driver_id },
                      ].map(({ label, value }) => (
                        <div key={label} className="stat-box">
                          <span className="stat-label">{label}</span>
                          <span style={{ fontSize: 13, fontWeight: 600 }}>{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Season stats chart */}
                {seasonStats.length > 0 && (
                  <SectionCard title="Puntos por temporada">
                    <div style={{ height: 180 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={seasonStats.slice(-15)} margin={{ top: 4, right: 0, bottom: 0, left: -20 }}>
                          <XAxis dataKey="year" tick={{ fill: 'var(--f1-text-muted)', fontSize: 10 }} />
                          <YAxis tick={{ fill: 'var(--f1-text-muted)', fontSize: 10 }} />
                          <Tooltip
                            contentStyle={{ background: 'var(--f1-surface-2)', border: '1px solid var(--f1-border)', borderRadius: 4, fontSize: 11 }}
                          />
                          <Bar dataKey="total_points" radius={[2, 2, 0, 0]}>
                            {seasonStats.slice(-15).map((_, i, arr) => (
                              <Cell key={i} fill={i === arr.length - 1 ? 'var(--f1-red)' : 'rgba(232,0,45,0.5)'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </SectionCard>
                )}

                {/* Season stats table */}
                {seasonStats.length > 0 && (
                  <SectionCard title="Estadísticas por temporada">
                    <div style={{ maxHeight: 280, overflowY: 'auto' }}>
                      <div style={{
                        display: 'grid', gridTemplateColumns: '50px 1fr 60px 50px 40px',
                        gap: 4, padding: '0 0 6px',
                        fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-dim)',
                        borderBottom: '1px solid var(--f1-border)',
                      }}>
                        <span>Año</span><span>Equipo</span><span>Pts</span><span>V</span><span>Pos</span>
                      </div>
                      {[...seasonStats].reverse().slice(0, 20).map((s, i) => (
                        <div key={i} style={{
                          display: 'grid', gridTemplateColumns: '50px 1fr 60px 50px 40px',
                          gap: 4, padding: '7px 0',
                          borderBottom: '1px solid var(--f1-border)',
                          fontSize: 11, alignItems: 'center',
                        }}>
                          <span className="mono" style={{ color: 'var(--f1-text-muted)' }}>{s.year}</span>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <TeamDot constructorName={s.constructor_name} size={8} />
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.constructor_name || '—'}</span>
                          </div>
                          <span className="mono" style={{ fontWeight: 700 }}>{s.total_points}</span>
                          <span className="mono" style={{ color: s.wins > 0 ? 'var(--gold)' : 'var(--f1-text-muted)' }}>{s.wins}</span>
                          <span className="mono" style={{ color: s.best_position === 1 ? 'var(--gold)' : 'var(--f1-text-muted)' }}>{s.best_position || '—'}</span>
                        </div>
                      ))}
                    </div>
                  </SectionCard>
                )}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
