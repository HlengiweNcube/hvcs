import { useEffect, useState } from 'react'
import { getCaregiverDashboard, checkinVisit, checkoutVisit } from '../api'
import Navbar from '../components/Navbar'

function StatusBadge({ status }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status.replace('_', ' ')}</span>
}

export default function CaregiverDashboard({ user, onLogout }) {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(null)

  const refresh = () => getCaregiverDashboard().then(setData).finally(() => setLoading(false))

  useEffect(() => { refresh() }, [])

  const handleCheckin = async (visitId) => {
    setActionLoading(visitId)
    try {
      let lat = null, lng = null
      if (navigator.geolocation) {
        await new Promise(resolve =>
          navigator.geolocation.getCurrentPosition(
            pos => { lat = pos.coords.latitude; lng = pos.coords.longitude; resolve() },
            () => resolve(),
            { timeout: 5000 }
          )
        )
      }
      await checkinVisit(visitId, { lat, lng })
      refresh()
    } finally {
      setActionLoading(null)
    }
  }

  const handleCheckout = async (visitId) => {
    setActionLoading(visitId)
    try {
      await checkoutVisit(visitId)
      refresh()
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="page">
      <Navbar user={user} onLogout={onLogout} links={[]} />
      <main className="main">
        <h1 className="page-title">
          Welcome, {data?.caregiver?.first_name || user.first_name}
        </h1>

        {loading && <p className="loading">Loading…</p>}
        {data && <>
          <h2 className="section-title">My Visits</h2>
          {data.visits.length === 0
            ? <p style={{ color: 'var(--muted)' }}>No visits assigned yet.</p>
            : (
              <div className="table-wrap card">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th><th>Time</th><th>Client</th><th>Status</th><th>Notes</th><th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.visits.map(v => (
                      <tr key={v.id}>
                        <td>{v.scheduled_date}</td>
                        <td>{v.scheduled_time}</td>
                        <td>{v.client_name}</td>
                        <td><StatusBadge status={v.status} /></td>
                        <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {v.notes || '—'}
                        </td>
                        <td style={{ whiteSpace: 'nowrap' }}>
                          {v.status === 'SCHEDULED' && (
                            <button
                              className="btn btn-primary btn-sm"
                              disabled={actionLoading === v.id}
                              onClick={() => handleCheckin(v.id)}
                            >
                              {actionLoading === v.id ? '…' : 'Check In'}
                            </button>
                          )}
                          {v.status === 'IN_PROGRESS' && (
                            <button
                              className="btn btn-outline btn-sm"
                              disabled={actionLoading === v.id}
                              onClick={() => handleCheckout(v.id)}
                            >
                              {actionLoading === v.id ? '…' : 'Check Out'}
                            </button>
                          )}
                          {(v.status === 'COMPLETED' || v.status === 'CANCELLED') && '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

          <h2 className="section-title">My Profile</h2>
          <div className="card" style={{ maxWidth: 360 }}>
            <p><strong>Name:</strong> {data.caregiver.first_name} {data.caregiver.last_name}</p>
            <p style={{ marginTop: '.5rem' }}><strong>Phone:</strong> {data.caregiver.phone || '—'}</p>
            <p style={{ marginTop: '.5rem' }}><strong>Qualifications:</strong> {data.caregiver.qualifications || '—'}</p>
            <p style={{ marginTop: '.5rem' }}><strong>Status:</strong> {data.caregiver.is_active ? 'Active' : 'Inactive'}</p>
          </div>
        </>}
      </main>
    </div>
  )
}
