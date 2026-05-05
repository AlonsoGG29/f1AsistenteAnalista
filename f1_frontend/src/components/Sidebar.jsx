import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Users, Building2, MapPin, Flag,
  BarChart3, Cpu, MessageSquare, TrendingUp, Trophy
} from 'lucide-react';

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/standings', icon: Trophy, label: 'Clasificaciones' },
  { to: '/drivers', icon: Users, label: 'Pilotos' },
  { to: '/constructors', icon: Building2, label: 'Equipos' },
  { to: '/circuits', icon: MapPin, label: 'Circuitos' },
  { to: '/races', icon: Flag, label: 'Carreras' },
  { to: '/analysis', icon: BarChart3, label: 'Análisis' },
  { to: '/predictions', icon: Cpu, label: 'Predicciones IA' },
  { to: '/chat', icon: MessageSquare, label: 'Chat IA' },
];

export default function Sidebar() {
  return (
    <aside style={{
      width: 220,
      minHeight: '100vh',
      background: 'var(--f1-carbon)',
      borderRight: '1px solid var(--f1-border)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      position: 'sticky',
      top: 0,
      height: '100vh',
      overflowY: 'auto',
    }}>
      {/* Logo */}
      <div style={{
        padding: '24px 20px 20px',
        borderBottom: '1px solid var(--f1-border)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <div style={{
            width: 32, height: 32,
            background: 'var(--f1-red)',
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 16,
            fontWeight: 900,
            letterSpacing: '-0.05em',
            fontFamily: 'Titillium Web, sans-serif',
          }}>F1</div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Analytics</div>
            <div style={{ fontSize: 10, color: 'var(--f1-text-dim)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>1950 – 2024</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding: '12px 0', flex: 1 }}>
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '9px 20px',
              fontSize: 13,
              fontWeight: isActive ? 700 : 400,
              color: isActive ? 'var(--f1-text)' : 'var(--f1-text-muted)',
              textDecoration: 'none',
              borderLeft: isActive ? '3px solid var(--f1-red)' : '3px solid transparent',
              background: isActive ? 'rgba(232,0,45,0.08)' : 'transparent',
              transition: 'all 0.15s',
              letterSpacing: '0.01em',
            })}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--f1-border)',
        fontSize: 10,
        color: 'var(--f1-text-dim)',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}>
        <div>Powered by Azure AI</div>
        <div style={{ marginTop: 2 }}>FastAPI + PostgreSQL</div>
      </div>
    </aside>
  );
}
