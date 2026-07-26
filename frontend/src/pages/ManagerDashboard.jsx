import { useEffect, useState } from 'react'
import { getManagerDashboard } from '../api'
import Navbar from '../components/Navbar'

const MANAGER_LINKS = [
  { to: '/visits',     label: 'Visits'     },
  { to: '/compliance', label: 'Compliance' },
]

function StatusBadge({ status }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status.replace('_', ' ')}</span>
}

export default function ManagerDashboard({ user, onLogout }) {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getManagerDashboard().then(setData).finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <Navbar user={user} onLogout={onLogout} links={MANAGER_LINKS} />
      <main className="main">
        <h1 className="page-title">Manager Dashboard</h1>

        {loading && <p className="loading">Loading…</p>}
        {data && <>
          {data.alerts.missed_checkin.length > 0 && (
            <div className="alert alert-danger">
              <strong>Missed check-ins ({data.alerts.missed_checkin.length}):</strong>{' '}
              {data.alerts.missed_checkin.map(v => `${v.caregiver_name} → ${v.client_name}`).join('; ')}
            </div>
          )}
          {data.alerts.never_started.length > 0 && (
            <div className="alert alert-warning">
              <strong>Never started ({data.alerts.never_started.length})</strong> — past visits still showing SCHEDULED.
            </div>
          )}

          <h2 className="section-title">Today's Visits</h2>
          {data.todays_visits.length === 0
            ? <p style={{ color: 'var(--muted)' }}>No visits today.</p>
            : (
              <div className="table-wrap card">
                <table>
                  <thead>
                    <tr><th>Time</th><th>Caregiver</th><th>Client</th><th>Status</th><th>Check-in</th></tr>
                  </thead>
                  <tbody>
                    {data.todays_visits.map(v => (
                      <tr key={v.id}>
                        <td>{v.scheduled_time}</td>
                        <td>{v.caregiver_name}</td>
                        <td>{v.client_name}</td>
                        <td><StatusBadge status={v.status} /></td>
                        <td>{v.check_in_time ? new Date(v.check_in_time).toLocaleTimeString() : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

          <h2 className="section-title">Active Caregivers</h2>
          <div className="table-wrap card">
            <table>
              <thead><tr><th>Name</th><th>Phone</th><th>Qualifications</th></tr></thead>
              <tbody>
                {data.caregivers.map(c => (
                  <tr key={c.id}>
                    <td>{c.first_name} {c.last_name}</td>
                    <td>{c.phone || '—'}</td>
                    <td>{c.qualifications || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>}
      </main>
    </div>
  )
}
