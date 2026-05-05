import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, PositionBadge, TeamDot, Select, YEARS } from '../components/UI.jsx';
import { getDriverStandings, getConstructorStandings, getRaces } from '../services/api.js';
import { Trophy, Zap, Users, Flag } from 'lucide-react';

export default function Dashboard() {
  const [year, setYear] = useState(2024);
  const [drivers, setDrivers] = useState([]);
  const [constructors, setConstructors] = useState([]);
  const [races, setRaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getDriverStandings(year).catch(() => []),
      getConstructorStandings(year).catch(() => []),
      getRaces({ year, page_size: 30 }).catch(() => ({ items: [] })),
    ]).then(([d, c, r]) => {
      setDrivers(d.slice(0, 10));
      setConstructors(c.slice(0, 10));
      setRaces(r.items || []);
    }).catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [year]);

  const leader = drivers[0];
  const teamLeader = constructors[0];

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Dashboard" subtitle="Resumen de temporada F1">
        <Select
          value={year}
          onChange={v => setYear(Number(v))}
          options={YEARS}
          style={{ width: 100 }}
        />
      </PageHeader>

      <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>
        {error && <ErrorBanner message={error} />}

        {/* Quick stats */}
        <div className="grid-4" style={{ gap: 12 }}>
          {[
            { label: 'Líder pilotos', value: leader ? `${leader.driver_name || '—'}` : '—', sub: `${leader?.points ?? 0} pts`, icon: Trophy, color: 'var(--gold)' },
            { label: 'Líder equipos', value: teamLeader?.constructor_name || '—', sub: `${teamLeader?.points ?? 0} pts`, icon: Zap, color: 'var(--f1-red)' },
            { label: 'Carreras disputadas', value: races.length, sub: `Temporada ${year}`, icon: Flag, color: 'var(--mercedes)' },
            { label: 'Pilotos activos', value: drivers.length, sub: 'en clasificación', icon: Users, color: 'var(--mclaren)' },
          ].map(({ label, value, sub, icon: Icon, color }) => (
            <div key={label} className="card" style={{ padding: 18, display: 'flex', gap: 14, alignItems: 'center' }}>
              <div style={{ width: 44, height: 44, borderRadius: 4, background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Icon size={20} color={color} />
              </div>
              <div>
                <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{label}</div>
                <div style={{ fontSize: 16, fontWeight: 700, marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 140 }}>{value}</div>
                <div style={{ fontSize: 11, color: 'var(--f1-text-muted)' }}>{sub}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid-2">
          {/* Driver standings top 10 */}
          <SectionCard title="Top 10 Pilotos" action={
            <Link to="/standings" style={{ fontSize: 11, color: 'var(--f1-red)', textDecoration: 'none', fontWeight: 600 }}>Ver todo →</Link>
          }>
            {loading ? <LoadingPane /> : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                {drivers.map((d, i) => (
                  <div key={d.driver_id || i} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '8px 0',
                    borderBottom: i < drivers.length - 1 ? '1px solid var(--f1-border)' : 'none',
                  }}>
                    <PositionBadge pos={d.position || i + 1} />
                    <TeamDot constructorName={d.constructor_name} />
                    <span style={{ flex: 1, fontSize: 13, fontWeight: i === 0 ? 700 : 400 }}>
                      {d.driver_name || '—'}
                    </span>
                    <span className="mono" style={{ fontSize: 13, color: 'var(--f1-text-muted)' }}>
                      {d.points} pts
                    </span>
                    {d.wins > 0 && (
                      <span className="badge badge-gold" style={{ fontSize: 10 }}>{d.wins}V</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          {/* Constructor standings */}
          <SectionCard title="Top 10 Constructores" action={
            <Link to="/standings" style={{ fontSize: 11, color: 'var(--f1-red)', textDecoration: 'none', fontWeight: 600 }}>Ver todo →</Link>
          }>
            {loading ? <LoadingPane /> : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                {constructors.map((c, i) => (
                  <div key={c.constructor_id || i} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '8px 0',
                    borderBottom: i < constructors.length - 1 ? '1px solid var(--f1-border)' : 'none',
                  }}>
                    <PositionBadge pos={c.position || i + 1} />
                    <TeamDot constructorName={c.constructor_name} />
                    <span style={{ flex: 1, fontSize: 13, fontWeight: i === 0 ? 700 : 400 }}>
                      {c.constructor_name || '—'}
                    </span>
                    <span className="mono" style={{ fontSize: 13, color: 'var(--f1-text-muted)' }}>
                      {c.points} pts
                    </span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        {/* Points chart - top 5 drivers season */}
        {drivers.length > 0 && (
          <SectionCard title={`Puntos acumulados — Top 5 — ${year}`}>
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={drivers.slice(0, 5)} margin={{ top: 0, right: 0, bottom: 0, left: -10 }}>
                  <XAxis dataKey="driver_name" tick={{ fill: 'var(--f1-text-muted)', fontSize: 11 }} />
                  <YAxis tick={{ fill: 'var(--f1-text-muted)', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: 'var(--f1-surface-2)', border: '1px solid var(--f1-border)', borderRadius: 4, fontSize: 12 }}
                    labelStyle={{ color: 'var(--f1-text)' }}
                    itemStyle={{ color: 'var(--f1-red)' }}
                  />
                  <Bar dataKey="points" radius={[2, 2, 0, 0]}>
                    {drivers.slice(0, 5).map((_, i) => (
                      <Cell key={i} fill={i === 0 ? 'var(--f1-red)' : `rgba(232,0,45,${0.6 - i * 0.1})`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>
        )}

        {/* Recent races */}
        {races.length > 0 && (
          <SectionCard title="Carreras de la temporada" action={
            <Link to="/races" style={{ fontSize: 11, color: 'var(--f1-red)', textDecoration: 'none', fontWeight: 600 }}>Ver todas →</Link>
          }>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 8 }}>
              {races.slice(0, 12).map(race => (
                <Link key={race.race_id} to={`/races?raceId=${race.race_id}`} style={{ textDecoration: 'none' }}>
                  <div style={{
                    background: 'var(--f1-surface-2)',
                    border: '1px solid var(--f1-border)',
                    borderRadius: 4,
                    padding: '12px 14px',
                    cursor: 'pointer',
                    transition: 'border-color 0.15s',
                  }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--f1-red)'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--f1-border)'}
                  >
                    <div style={{ fontSize: 10, color: 'var(--f1-red)', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4 }}>
                      Ronda {race.round}
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, lineHeight: 1.3 }}>{race.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--f1-text-muted)', marginTop: 4 }}>{race.date}</div>
                  </div>
                </Link>
              ))}
            </div>
          </SectionCard>
        )}
      </div>
    </div>
  );
}
