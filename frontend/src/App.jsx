import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import Motos from './pages/Motos'
import MotoDetalhes from './pages/MotoDetalhes'
import Checklists from './pages/Checklists'
import ChecklistDetalhes from './pages/ChecklistDetalhes'
import Analytics from './pages/Analytics'
import Financeiro from './pages/Financeiro'
import { ToastContainer } from './components/Toast'
import './App.css'

function App() {
  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-container">
            <Link to="/" className="nav-logo">
            🔧 SGO
          </Link>
          <div className="nav-menu">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/motos" className="nav-link">Motos</Link>
            <Link to="/checklists" className="nav-link">Checklists</Link>
            <Link to="/financeiro" className="nav-link">Financeiro</Link>
            <Link to="/analytics" className="nav-link">Analytics</Link>
          </div>
        </div>
      </nav>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/motos" element={<Motos />} />
          <Route path="/motos/:placa" element={<MotoDetalhes />} />
          <Route path="/checklists" element={<Checklists />} />
          <Route path="/checklists/:id" element={<ChecklistDetalhes />} />
          <Route path="/financeiro" element={<Financeiro />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
      <ToastContainer />
    </div>
  )
}

export default App

