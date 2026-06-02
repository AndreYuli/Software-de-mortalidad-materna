import { useState } from 'react'
import Login from './components/Login'
import Register from './components/Register'
import DashboardOKD from './components/DashboardOKD'

function App() {
  const [view, setView] = useState('login')

  if (view === 'dashboard') return <DashboardOKD onLogout={() => setView('login')} />
  if (view === 'register') return <Register onRegistered={() => setView('login')} onBack={() => setView('login')} />
  return <Login onLogin={() => setView('dashboard')} onRegister={() => setView('register')} />
}

export default App

