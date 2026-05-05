// ── Shared Components ─────────────────────────────────────────────────────────

export function PageHeader({ title, subtitle, children }) {
  return (
    <div style={{
      borderBottom: '1px solid var(--f1-border)',
      padding: '24px 32px',
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      gap: 16,
      background: 'linear-gradient(180deg, rgba(232,0,45,0.03) 0%, transparent 100%)',
    }}>
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 900, letterSpacing: '-0.02em' }}>{title}</h1>
        {subtitle && <p style={{ fontSize: 13, color: 'var(--f1-text-muted)', marginTop: 4 }}>{subtitle}</p>}
      </div>
      {children && <div style={{ display: 'flex', gap: 8 }}>{children}</div>}
    </div>
  );
}

export function SectionCard({ title, children, style = {}, action }) {
  return (
    <div className="card card-red" style={style}>
      {title && (
        <div style={{
          padding: '14px 18px',
          borderBottom: '1px solid var(--f1-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--f1-text-muted)' }}>
            {title}
          </span>
          {action}
        </div>
      )}
      <div style={{ padding: 18 }}>{children}</div>
    </div>
  );
}

export function StatRow({ stats }) {
  return (
    <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
      {stats.map(({ label, value, color }) => (
        <div key={label} className="stat-box">
          <span className="stat-label">{label}</span>
          <span className={`stat-value${color ? ` ${color}` : ''}`}>{value ?? '—'}</span>
        </div>
      ))}
    </div>
  );
}

export function Spinner({ size = 24 }) {
  return (
    <div style={{
      width: size, height: size,
      border: '2px solid var(--f1-border)',
      borderTopColor: 'var(--f1-red)',
      borderRadius: '50%',
      animation: 'spin 0.7s linear infinite',
    }} />
  );
}

export function LoadingPane() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 48 }}>
      <Spinner size={32} />
    </div>
  );
}

export function ErrorBanner({ message }) {
  return (
    <div style={{
      background: 'rgba(232,0,45,0.08)',
      border: '1px solid rgba(232,0,45,0.25)',
      borderRadius: 4,
      padding: '12px 16px',
      color: 'var(--f1-red)',
      fontSize: 13,
    }}>
      ⚠ {message}
    </div>
  );
}

export function EmptyState({ message = 'Sin datos disponibles' }) {
  return (
    <div style={{ textAlign: 'center', padding: 40, color: 'var(--f1-text-dim)', fontSize: 13 }}>
      {message}
    </div>
  );
}

export function ProbabilityBar({ value, label, color = 'var(--f1-red)' }) {
  const pct = Math.round(value * 100);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
          <span style={{ color: 'var(--f1-text-muted)' }}>{label}</span>
          <span className="mono" style={{ color, fontWeight: 700 }}>{pct}%</span>
        </div>
      )}
      <div className="prob-bar">
        <div
          className="prob-bar-fill"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}99, ${color})` }}
        />
      </div>
    </div>
  );
}

export function TeamDot({ constructorName, size = 10 }) {
  const colors = {
    ferrari: '#E8002D', red_bull: '#3671C6', mercedes: '#27F4D2',
    mclaren: '#FF8000', alpine: '#FF87BC', aston_martin: '#358C75',
    haas: '#B6BABD', williams: '#64C4FF', alphatauri: '#2B4562', sauber: '#00E701',
    renault: '#FFF500', force_india: '#FF80C7', toro_rosso: '#469BFF',
  };
  const key = (constructorName || '').toLowerCase().replace(/\s+/g, '_');
  const color = colors[key] || '#888';
  return (
    <span style={{
      display: 'inline-block',
      width: size, height: size,
      borderRadius: 2,
      background: color,
      flexShrink: 0,
    }} />
  );
}

export function PositionBadge({ pos }) {
  const styles = {
    1: { background: 'rgba(255,215,0,0.15)', color: '#FFD700', border: '1px solid rgba(255,215,0,0.3)' },
    2: { background: 'rgba(192,192,192,0.1)', color: '#C0C0C0', border: '1px solid rgba(192,192,192,0.2)' },
    3: { background: 'rgba(205,127,50,0.1)', color: '#CD7F32', border: '1px solid rgba(205,127,50,0.2)' },
  };
  const s = styles[pos] || { background: 'rgba(255,255,255,0.04)', color: 'var(--f1-text-muted)', border: '1px solid var(--f1-border)' };
  return (
    <span style={{ ...s, padding: '1px 7px', borderRadius: 2, fontSize: 12, fontFamily: 'Share Tech Mono, monospace', fontWeight: 700, minWidth: 28, display: 'inline-block', textAlign: 'center' }}>
      {pos}
    </span>
  );
}

export function Select({ value, onChange, options, placeholder, style = {} }) {
  return (
    <select
      className="input-f1"
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{ ...style }}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(o => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

export function Input({ value, onChange, placeholder, style = {} }) {
  return (
    <input
      className="input-f1"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={style}
    />
  );
}

// Years from 1950 to 2024
export const YEARS = Array.from({ length: 75 }, (_, i) => 2024 - i)
  .map(y => ({ value: y, label: String(y) }));
