import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { PageHeader, SectionCard, LoadingPane, ErrorBanner, EmptyState, PositionBadge, TeamDot, Select, YEARS } from '../components/UI.jsx';
import { getRaces, getRaceResults, getRaceLapTimes, getRacePitStops } from '../api/api.js';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const LAP_COLORS = ['#E8002D', '#27F4D2', '#FF8000', '#3671C6', '#FF87BC', '#FFD700'];

export default function Races() {
  const [searchParams] = useSearchParams();
  const [year, setYear] = useState(2024);
  const [races, setRaces] = useState([]);
  const [selectedRace, setSelectedRace] = useState(searchParams.get('raceId') ? Number(searchParams.get('raceId')) : null);
  const [results, setResults] = useState([]);
  const [lapTimes, setLapTimes] = useState([]);
  const [pitStops, setPitStops] = useState([]);
  const [activeTab, setActiveTab] = useState('results');
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getRaces({ year, page_size: 30 })
      .then(data => setRaces(data.items || []))
      .finally(() => setLoading(false));
  }, [year]);

  useEffect(() => {
    if (!selectedRace) return;
    setDetailLoading(true);
    Promise.all([
      getRaceResults(selectedRace).catch(() => []),
      getRacePitStops(selectedRace).catch(() => []),
    ]).then(([r, p]) => {
      setResults(r);
      setPitStops(p);
    }).finally(() => setDetailLoading(false));
  }, [selectedRace]);

  const selectedRaceObj = races.find(r => r.race_id === selectedRace);

  // Build lap times chart from results (using fastest lap info as proxy)
  const lapChart = results.slice(0, 6).map(r => ({
    name: r.driver_code || r.driver_name?.split(' ').slice(-1)[0] || '—',
    fastest: r.fastest_lap_speed ? parseFloat(r.fastest_lap_speed) : null,
    laps: r.laps,
    constructor: r.constructor_name,
  }));

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <PageHeader title="Carreras" subtitle="Resultados y análisis de carrera">
        <Select value={year} onChange={v => { setYear(Number(v)); setSelectedRace(null); }} options={YEARS} style={{ width: 100 }} />
      </PageHeader>

      <div style={{ padding: '24px 32px', display: 'flex', gap: 20 }}>
        {/* Race list */}
        <div style={{ width: 280, flexShrink: 0 }}>
          <SectionCard title={`Temporada ${year}`}>
            {loading ? <LoadingPane /> : races.length === 0 ? <EmptyState /> : (
              <div style={{ maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' }}>
                {races.map(race => (
                  <div
                    key={race.race_id}
                    onClick={() => setSelectedRace(race.race_id)}
                    style={{
                      padding: '10px 0',
                      borderBottom: '1px solid var(--f1-border)',
                      cursor: 'pointer',
                      borderLeft: selectedRace === race.race_id ? '3px solid var(--f1-red)' : '3px solid transparent',
                      paddingLeft: selectedRace === race.race_id ? 8 : 2,
                      background: selectedRace === race.race_id ? 'rgba(232,0,45,0.05)' : 'transparent',
                      transition: 'all 0.1s',
                    }}
                  >
                    <div style={{ fontSize: 10, color: 'var(--f1-red)', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                      Ronda {race.round}
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, marginTop: 2 }}>{race.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--f1-text-muted)', marginTop: 2 }}>{race.date}</div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        {/* Race detail */}
        <div style={{ flex: 1 }}>
          {!selectedRace ? (
            <div style={{ textAlign: 'center', padding: 60, color: 'var(--f1-text-dim)' }}>
              ← Selecciona una carrera
            </div>
          ) : (
            <>
              {/* Race header */}
              {selectedRaceObj && (
                <div style={{
                  background: 'var(--f1-surface)',
                  border: '1px solid var(--f1-border)',
                  borderTop: '3px solid var(--f1-red)',
                  borderRadius: 4,
                  padding: '18px 20px',
                  marginBottom: 16,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--f1-red)', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                      Ronda {selectedRaceObj.round} — {year}
                    </div>
                    <h2 style={{ fontSize: 22, fontWeight: 900, marginTop: 4 }}>{selectedRaceObj.name}</h2>
                    <div style={{ fontSize: 12, color: 'var(--f1-text-muted)', marginTop: 4 }}>{selectedRaceObj.date}</div>
                  </div>
                  {results[0] && (
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Ganador</div>
                      <div style={{ fontSize: 18, fontWeight: 900, color: 'var(--gold)', marginTop: 2 }}>🏆 {results[0].driver_name}</div>
                      <div style={{ fontSize: 12, color: 'var(--f1-text-muted)' }}>{results[0].constructor_name}</div>
                    </div>
                  )}
                </div>
              )}

              {/* Tabs */}
              <div style={{ display: 'flex', gap: 0, border: '1px solid var(--f1-border)', borderRadius: 4, overflow: 'hidden', width: 'fit-content', marginBottom: 16 }}>
                {['results', 'pitstops'].map(t => (
                  <button key={t} onClick={() => setActiveTab(t)} style={{
                    padding: '7px 16px',
                    background: activeTab === t ? 'var(--f1-red)' : 'var(--f1-surface)',
                    color: activeTab === t ? 'white' : 'var(--f1-text-muted)',
                    border: 'none', cursor: 'pointer',
                    fontSize: 11, fontWeight: 700, fontFamily: 'Titillium Web, sans-serif',
                    letterSpacing: '0.06em', textTransform: 'uppercase',
                  }}>
                    {t === 'results' ? 'Resultados' : 'Pit Stops'}
                  </button>
                ))}
              </div>

              {detailLoading ? <LoadingPane /> : (
                <>
                  {activeTab === 'results' && (
                    <SectionCard title="Clasificación de carrera">
                      {results.length === 0 ? <EmptyState message="Sin resultados para esta carrera" /> : (
                        <div>
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: '44px 1fr 120px 60px 80px 80px',
                            gap: 8, padding: '0 0 8px',
                            borderBottom: '2px solid var(--f1-border)',
                            fontSize: 9, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--f1-text-dim)',
                          }}>
                            <span>Pos</span><span>Piloto</span><span>Equipo</span><span>Vueltas</span><span>Tiempo</span><span>Puntos</span>
                          </div>
                          {results.map((r, i) => (
                            <div key={r.result_id || i} style={{
                              display: 'grid',
                              gridTemplateColumns: '44px 1fr 120px 60px 80px 80px',
                              gap: 8, alignItems: 'center',
                              padding: '8px 0',
                              borderBottom: '1px solid var(--f1-border)',
                              animation: `fadeIn 0.2s ease ${i * 0.015}s both`,
                            }}>
                              <PositionBadge pos={r.position || r.position_order} />
                              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                                <span style={{ fontSize: 10, fontFamily: 'Share Tech Mono', color: 'var(--f1-text-dim)', width: 26 }}>{r.driver_code || ''}</span>
                                <span style={{ fontSize: 13, fontWeight: i < 3 ? 700 : 400 }}>{r.driver_name}</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <TeamDot constructorName={r.constructor_name} size={8} />
                                <span style={{ fontSize: 11, color: 'var(--f1-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.constructor_name}</span>
                              </div>
                              <span className="mono" style={{ fontSize: 12, color: 'var(--f1-text-muted)' }}>{r.laps}</span>
                              <span className="mono" style={{ fontSize: 11, color: 'var(--f1-text-muted)' }}>{r.time || r.status || '—'}</span>
                              <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: r.points > 0 ? 'var(--f1-text)' : 'var(--f1-text-dim)' }}>{r.points}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </SectionCard>
                  )}

                  {activeTab === 'pitstops' && (
                    <SectionCard title="Pit Stops">
                      {pitStops.length === 0 ? <EmptyState message="Sin datos de pit stops para esta carrera" /> : (
                        <div>
                          <div style={{
                            display: 'grid', gridTemplateColumns: '1fr 60px 60px 80px 100px',
                            gap: 8, padding: '0 0 8px',
                            borderBottom: '2px solid var(--f1-border)',
                            fontSize: 9, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--f1-text-dim)',
                          }}>
                            <span>Piloto</span><span>Stop</span><span>Vuelta</span><span>Hora</span><span>Duración</span>
                          </div>
                          {pitStops.map((p, i) => (
                            <div key={i} style={{
                              display: 'grid', gridTemplateColumns: '1fr 60px 60px 80px 100px',
                              gap: 8, alignItems: 'center', padding: '8px 0',
                              borderBottom: '1px solid var(--f1-border)',
                            }}>
                              <span style={{ fontSize: 13 }}>{p.driver_name || `Driver ${p.driver_id}`}</span>
                              <span className="mono" style={{ fontSize: 12, color: 'var(--f1-text-muted)' }}>{p.stop}</span>
                              <span className="mono" style={{ fontSize: 12, color: 'var(--f1-text-muted)' }}>{p.lap}</span>
                              <span className="mono" style={{ fontSize: 11, color: 'var(--f1-text-muted)' }}>{p.time}</span>
                              <span className="mono" style={{ fontSize: 13, color: parseFloat(p.duration) < 3 ? 'var(--f1-red)' : 'var(--f1-text)' }}>{p.duration}s</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </SectionCard>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
