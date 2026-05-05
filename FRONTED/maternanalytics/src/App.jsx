import { useState } from 'react'
import Login from './components/Login'
import DashboardOKD from './components/DashboardOKD'

function App() {
  const [loggedIn, setLoggedIn] = useState(false)

  return loggedIn
    ? <DashboardOKD onLogout={() => setLoggedIn(false)} />
    : <Login onLogin={() => setLoggedIn(true)} />
}

export default App

