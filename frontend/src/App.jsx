import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getMe } from './api'

import Login from './pages/Login'
import Register from './pages/Register'
import AdminDashboard from './pages/AdminDashboard'
import ManagerDashboard from './pages/ManagerDashboard'
import CaregiverDashboard from './pages/CaregiverDashboard'
import Clients from './pages/Clients'
import Caregivers from './pages/Caregivers'
import Visits from './pages/Visits'
import Compliance from './pages/Compliance'

/**
 * App
 *
 * Loads the current user once from /api/v1/auth/me/ and stores it in state.
 * Child pages receive `user` as a prop so they can gate content by role.
 */
export default function App() {
  const [user, setUser]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading…</div>

  const isAdmin    = user?.role === 'ADMIN'
  const isManager  = user?.role === 'MANAGER'
  const isCaregiver = user?.role === 'CAREGIVER'

  return (
    <BrowserRouter basename="/react">
      <Routes>
        {/* Public */}
        <Route path="/login"    element={!user ? <Login    onLogin={setUser} /> : <Navigate to="/" />} />
        <Route path="/register" element={!user ? <Register onLogin={setUser} /> : <Navigate to="/" />} />

        {/* Role-based home redirect */}
        <Route path="/" element={
          !user ? <Navigate to="/login" /> :
          isAdmin    ? <Navigate to="/admin"     /> :
          isManager  ? <Navigate to="/manager"   /> :
                       <Navigate to="/caregiver" />
        } />

        {/* Admin */}
        <Route path="/admin"       element={isAdmin ? <AdminDashboard user={user} onLogout={() => setUser(null)} /> : <Navigate to="/" />} />
        <Route path="/clients"     element={isAdmin ? <Clients user={user} onLogout={() => setUser(null)} />        : <Navigate to="/" />} />
        <Route path="/caregivers"  element={isAdmin ? <Caregivers user={user} onLogout={() => setUser(null)} />     : <Navigate to="/" />} />
        <Route path="/visits"      element={(isAdmin || isManager) ? <Visits user={user} onLogout={() => setUser(null)} />    : <Navigate to="/" />} />
        <Route path="/compliance"  element={(isAdmin || isManager) ? <Compliance user={user} onLogout={() => setUser(null)} /> : <Navigate to="/" />} />

        {/* Manager */}
        <Route path="/manager" element={isManager ? <ManagerDashboard user={user} onLogout={() => setUser(null)} /> : <Navigate to="/" />} />

        {/* Caregiver */}
        <Route path="/caregiver" element={isCaregiver ? <CaregiverDashboard user={user} onLogout={() => setUser(null)} /> : <Navigate to="/" />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}
