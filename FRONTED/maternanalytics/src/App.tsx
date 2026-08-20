import { useState, Suspense, lazy } from 'react'
import Login from './components/Login'
import Register from './components/Register'

const DashboardOKD = lazy(() => import('./components/DashboardOKD'))

type View = 'login' | 'register' | 'dashboard'

function App() {
  const [view, setView] = useState<View>('login')

  if (view === 'dashboard') return (
    <Suspense fallback={<div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100vh',fontFamily:'sans-serif'}}>Cargando...</div>}>
      <DashboardOKD onLogout={() => setView('login')} />
    </Suspense>
  )
  if (view === 'register') return <Register onRegistered={() => setView('login')} onBack={() => setView('login')} />
  return <Login onLogin={() => setView('dashboard')} onRegister={() => setView('register')} />
}

export default App
