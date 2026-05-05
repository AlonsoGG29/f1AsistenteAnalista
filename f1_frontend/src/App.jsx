import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Standings from './pages/Standings.jsx'
import Drivers from './pages/Drivers.jsx'
import Constructors from './pages/Constructors.jsx'
import Races from './pages/Races.jsx'
import Analysis from './pages/Analysis.jsx'
import Predictions from './pages/Predictions.jsx'
import Chat from './pages/Chat.jsx'

// Circuits y placeholder pages
function Circuits() {
  return (
    <div style={{ flex: 1, padding: 32 }}>
      <h1 style={{ fontSize: 28, fontWeight: 900, marginBottom: 8 }}>Circuitos</h1>
      <p style={{ color: 'var(--f1-text-muted)', fontSize: 13 }}>Próximamente — vista de circuitos con estadísticas históricas.</p>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <Routes>
            <Route path="/"             element={<Dashboard />} />
            <Route path="/standings"    element={<Standings />} />
            <Route path="/drivers"      element={<Drivers />} />
            <Route path="/constructors" element={<Constructors />} />
            <Route path="/circuits"     element={<Circuits />} />
            <Route path="/races"        element={<Races />} />
            <Route path="/analysis"     element={<Analysis />} />
            <Route path="/predictions"  element={<Predictions />} />
            <Route path="/chat"         element={<Chat />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
