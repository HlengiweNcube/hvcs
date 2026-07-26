import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAdminDashboard } from '../api'
import Navbar from '../components/Navbar'

const ADMIN_LINKS = [
  { to: '/clients',    label: 'Clients'    },
  { to: '/caregivers', label: 'Caregivers' },
  { to: '/visits',     label: 'Visits'     },
  { to: '/compliance', label: 'Compliance' },
]

function StatusBadge({ status }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status.replace('_', ' ')}</span>
}

export default function AdminDashboard({ user, onLogout }) {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAdminDashboard().then(setData).finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <Navbar user={user} onLogout={onLogout} links={ADMIN_LINKS} />
      <main className="main">
        <h1 className="page-title">Admin Dashboard</h1>

        {loading && <p className="loading">Loading…</p>}
        {data && <>
          {/* Stats */}
          <div className="stat-grid">
            {[
              { label: 'Active Clients',    value: data.stats.total_clients    },
              { label: 'Active Caregivers', value: data.stats.total_caregivers },
              { label: 'Managers',          value: data.stats.total_managers   },
              { label: 'Scheduled',         value: data.stats.visits_scheduled },
              { label: 'In Progress',       value: data.stats.visits_in_progress },
              { label: 'Completed',         value: data.stats.visits_completed },
              { label: 'Cancelled',         value: data.stats.visits_cancelled },
              { label: '7-day Compliance',  value: `${data.stats.compliance_rate}%` },
            ].map(s => (
              <div className="stat-card" key={s.label}>
                <div className="value">{s.value}</div>
                <div className="label">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Alerts */}
          {data.alerts.missed_checkin.length > 0 && (
            <div className="alert alert-danger">
              <strong>Missed check-ins ({data.alerts.missed_checkin.length}):</strong>{' '}
              {data.alerts.missed_checkin.map(v => `${v.caregiver_name} → ${v.client_name} @ ${v.scheduled_time}`).join('; ')}
            </div>
          )}
          {data.alerts.never_started.length > 0 && (
            <div className="alert alert-warning">
              <strong>Never started ({data.alerts.never_started.length}):</strong>{' '}
              {data.alerts.never_started.slice(0, 5).map(v => `${v.scheduled_date} ${v.caregiver_name}`).join('; ')}
            </div>
          )}

          {/* Today's visits */}
          <h2 className="section-title">Today's Visits</h2>
          {data.todays_visits.length === 0
            ? <p style={{ color: 'var(--muted)' }}>No visits scheduled for today.</p>
            : (
              <div className="table-wrap card">
                <table>
                  <thead>
                    <tr><th>Time</th><th>Caregiver</th><th>Client</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {data.todays_visits.map(v => (
                      <tr key={v.id}>
                        <td>{v.scheduled_time}</td>
                        <td>{v.caregiver_name}</td>
                        <td>{v.client_name}</td>
                        <td><StatusBadge status={v.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
        </>}
      </main>
    </div>
  )
}
