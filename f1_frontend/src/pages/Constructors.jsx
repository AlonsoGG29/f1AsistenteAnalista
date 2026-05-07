// Constructors.jsx
import { useState, useEffect } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, EmptyState, TeamDot, Input, Select } from '../components/UI.jsx';
import { getConstructors, getConstructor, getConstructorSeasonStats } from '../api/api.js';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Search, ChevronRight } from 'lucide-react';

export default function Constructors() {
  const [search, setSearch] = useState('');
  const [constructors, setConstructors] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getConstructors({ page, page_size: 30, search: search || undefined })
      .then(d => { setConstructors(d.items || []); setTotal(d.total || 0); })
      .finally(() => setLoading(false));
  }, [search, page]);

  const loadDetail = (id) => {
    setSelected(id);
    setDetailLoading(true);
    Promise.all([
      getConstructor(id).catch(() => null),
      getConstructorSeasonStats(id).catch(() => []),
    ]).then(([d, s]) => { setDetail(d); setStats(s || []); })
      .finally(() => setDetailLoading(false));
  };

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Equipos" subtitle={`${total} constructores en la base de datos`} />
      <div style={{ padding: '24px 32px', display: 'flex', gap: 20 }}>
        <div style={{ flex: 1 }}>
          <div style={{ position: 'relative', marginBottom: 16 }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--f1-text-dim)' }} />
            <Input value={search} onChange={v => { setSearch(v); setPage(1); }} placeholder="Buscar equipo..." style={{ paddingLeft: 32 }} />
          </div>
          <SectionCard>
            {loading ? <LoadingPane /> : constructors.length === 0 ? <EmptyState /> : (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 32px', gap: 8, padding: '0 0 8px', borderBottom: '2px solid var(--f1-border)', fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--f1-text-dim)' }}>
                  <span>Equipo</span><span>Nacionalidad</span><span></span>
                </div>
                {constructors.map(c => (
                  <div key={c.constructorId} onClick={() => loadDetail(c.constructorId)} style={{
                    display: 'grid', gridTemplateColumns: '1fr 120px 32px', gap: 8, alignItems: 'center',
                    padding: '9px 0', borderBottom: '1px solid var(--f1-border)', cursor: 'pointer',
                    borderLeft: selected === c.constructorId ? '3px solid var(--f1-red)' : '3px solid transparent',
                    paddingLeft: selected === c.constructorId ? 8 : 2,
                    background: selected === c.constructorId ? 'rgba(232,0,45,0.05)' : 'transparent',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <TeamDot constructorName={c.name} />
                      <span style={{ fontSize: 13, fontWeight: 600 }}>{c.name}</span>
                    </div>
                    <span style={{ fontSize: 12, color: 'var(--f1-text-muted)' }}>{c.nationality}</span>
                    <ChevronRight size={14} color="var(--f1-text-dim)" />
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
          {total > 30 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
              <button className="btn-ghost" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>← Anterior</button>
              <span style={{ padding: '8px 16px', fontSize: 12, color: 'var(--f1-text-muted)' }}>Pág. {page}</span>
              <button className="btn-ghost" onClick={() => setPage(p => p + 1)} disabled={page * 30 >= total}>Siguiente →</button>
            </div>
          )}
        </div>

        {selected && (
          <div style={{ width: 340, flexShrink: 0 }}>
            {detailLoading ? <SectionCard><LoadingPane /></SectionCard> : detail && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div className="card card-red" style={{ padding: '20px 18px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                    <TeamDot constructorName={detail.name} size={16} />
                    <h2 style={{ fontSize: 20, fontWeight: 900 }}>{detail.name}</h2>
                  </div>
                  <div className="grid-2" style={{ gap: 10 }}>
                    {[
                      { label: 'Nacionalidad', value: detail.nationality },
                      { label: 'ID', value: detail.constructorId },
                    ].map(({ label, value }) => (
                      <div key={label} className="stat-box">
                        <span className="stat-label">{label}</span>
                        <span style={{ fontSize: 13, fontWeight: 600 }}>{value || '—'}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {stats.length > 0 && (
                  <SectionCard title="Puntos por temporada">
                    <div style={{ height: 180 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={stats.slice(-15)} margin={{ top: 4, right: 0, bottom: 0, left: -20 }}>
                          <XAxis dataKey="year" tick={{ fill: 'var(--f1-text-muted)', fontSize: 10 }} />
                          <YAxis tick={{ fill: 'var(--f1-text-muted)', fontSize: 10 }} />
                          <Tooltip contentStyle={{ background: 'var(--f1-surface-2)', border: '1px solid var(--f1-border)', borderRadius: 4, fontSize: 11 }} />
                          <Bar dataKey="total_points" radius={[2, 2, 0, 0]}>
                            {stats.slice(-15).map((_, i, arr) => (
                              <Cell key={i} fill={i === arr.length - 1 ? 'var(--f1-red)' : 'rgba(232,0,45,0.5)'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </SectionCard>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
