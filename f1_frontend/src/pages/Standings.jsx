import { useState, useEffect } from 'react';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, PositionBadge, TeamDot, Select, YEARS } from '../components/UI.jsx';
import { getDriverStandings, getConstructorStandings } from '../api/api.js';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const TEAM_COLORS = [
  '#E8002D', '#3671C6', '#27F4D2', '#FF8000', '#FF87BC',
  '#358C75', '#B6BABD', '#64C4FF', '#2B4562', '#00E701',
];

export default function Standings() {
  const [year, setYear] = useState(2024);
  const [tab, setTab] = useState('drivers');
  const [drivers, setDrivers] = useState([]);
  const [constructors, setConstructors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getDriverStandings(year).catch(() => []),
      getConstructorStandings(year).catch(() => []),
    ]).then(([d, c]) => {
      setDrivers(d);
      setConstructors(c);
    }).catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [year]);

  const data = tab === 'drivers' ? drivers : constructors;
  const nameKey = tab === 'drivers' ? 'driver_name' : 'constructor_name';

  // Build chart data from standings
  const chartData = data.slice(0, 8).map(d => ({
    name: (d[nameKey] || '').split(' ').slice(-1)[0], // last name
    points: d.points,
    wins: d.wins,
  }));

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Clasificaciones" subtitle="Campeonato mundial de Fórmula 1">
        <Select value={year} onChange={v => setYear(Number(v))} options={YEARS} style={{ width: 100 }} />
      </PageHeader>

      <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>
        {error && <ErrorBanner message={error} />}

        {/* Tab switcher */}
        <div style={{ display: 'flex', gap: 0, border: '1px solid var(--f1-border)', borderRadius: 4, overflow: 'hidden', width: 'fit-content' }}>
          {['drivers', 'constructors'].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: '8px 20px',
              background: tab === t ? 'var(--f1-red)' : 'var(--f1-surface)',
              color: tab === t ? 'white' : 'var(--f1-text-muted)',
              border: 'none',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 700,
              fontFamily: 'Titillium Web, sans-serif',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              transition: 'all 0.15s',
            }}>
              {t === 'drivers' ? 'Pilotos' : 'Constructores'}
            </button>
          ))}
        </div>

        <div className="grid-2" style={{ alignItems: 'start' }}>
          {/* Table */}
          <SectionCard title={`Clasificación ${tab === 'drivers' ? 'de pilotos' : 'de constructores'} ${year}`}>
            {loading ? <LoadingPane /> : (
              <div>
                {/* Header */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '44px 1fr auto auto',
                  gap: 12,
                  padding: '6px 0 10px',
                  borderBottom: '2px solid var(--f1-border)',
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                  color: 'var(--f1-text-dim)',
                }}>
                  <span>Pos</span>
                  <span>Nombre</span>
                  <span>V</span>
                  <span>Pts</span>
                </div>
                {data.map((d, i) => (
                  <div key={d.driver_id || d.constructor_id || i} style={{
                    display: 'grid',
                    gridTemplateColumns: '44px 1fr auto auto',
                    gap: 12,
                    alignItems: 'center',
                    padding: '9px 0',
                    borderBottom: '1px solid var(--f1-border)',
                    animation: `fadeIn 0.2s ease ${i * 0.02}s both`,
                  }}>
                    <PositionBadge pos={d.position || i + 1} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <TeamDot constructorName={tab === 'constructors' ? d.constructor_name : d.constructor_name} />
                      <span style={{ fontSize: 13, fontWeight: i < 3 ? 700 : 400 }}>{d[nameKey]}</span>
                    </div>
                    <span className="mono" style={{ fontSize: 12, color: 'var(--f1-text-muted)', textAlign: 'right' }}>
                      {d.wins}
                    </span>
                    <span className="mono" style={{
                      fontSize: 14,
                      fontWeight: 700,
                      color: i === 0 ? 'var(--gold)' : 'var(--f1-text)',
                      textAlign: 'right',
                      minWidth: 52,
                    }}>
                      {d.points}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          {/* Chart */}
          <SectionCard title="Distribución de puntos — Top 8">
            {loading ? <LoadingPane /> : (
              <>
                <div style={{ height: 280 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -10 }}>
                      <XAxis dataKey="name" tick={{ fill: 'var(--f1-text-muted)', fontSize: 11 }} />
                      <YAxis tick={{ fill: 'var(--f1-text-muted)', fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: 'var(--f1-surface-2)', border: '1px solid var(--f1-border)', borderRadius: 4, fontSize: 12 }}
                      />
                      <Line type="monotone" dataKey="points" stroke="var(--f1-red)" strokeWidth={2} dot={{ fill: 'var(--f1-red)', r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                {/* Wins leaderboard */}
                <div style={{ marginTop: 16, borderTop: '1px solid var(--f1-border)', paddingTop: 14 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-dim)', marginBottom: 10 }}>Victorias</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {data.filter(d => d.wins > 0).sort((a, b) => b.wins - a.wins).slice(0, 5).map((d, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <TeamDot constructorName={d.constructor_name} />
                        <span style={{ flex: 1, fontSize: 12 }}>{d[nameKey]}</span>
                        <div style={{ display: 'flex', gap: 3 }}>
                          {Array.from({ length: Math.min(d.wins, 10) }).map((_, j) => (
                            <div key={j} style={{ width: 8, height: 8, background: 'var(--f1-red)', borderRadius: 1 }} />
                          ))}
                          {d.wins > 10 && <span className="mono" style={{ fontSize: 10, color: 'var(--f1-red)' }}>+{d.wins - 10}</span>}
                        </div>
                        <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: 'var(--gold)', minWidth: 20, textAlign: 'right' }}>{d.wins}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
