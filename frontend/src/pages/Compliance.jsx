import { useEffect, useState } from 'react'
import { getCompliance } from '../api'
import Navbar from '../components/Navbar'

const today = new Date().toISOString().split('T')[0]
const thirtyAgo = new Date(Date.now() - 30 * 864e5).toISOString().split('T')[0]

function rateColor(r) {
  if (r === null) return 'var(--muted)'
  if (r >= 90) return '#166534'
  if (r >= 70) return '#854d0e'
  return '#991b1b'
}

export default function Compliance({ user, onLogout }) {
  const isAdmin = user.role === 'ADMIN'
  const links = isAdmin
    ? [{ to: '/admin', label: 'Dashboard' },{ to: '/clients', label: 'Clients' },{ to: '/caregivers', label: 'Caregivers' },{ to: '/visits', label: 'Visits' },{ to: '/compliance', label: 'Compliance' }]
    : [{ to: '/manager', label: 'Dashboard' },{ to: '/visits', label: 'Visits' },{ to: '/compliance', label: 'Compliance' }]

  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [params,  setParams]  = useState({ date_from: thirtyAgo, date_to: today })

  const load = () => {
    setLoading(true)
    getCompliance(params).then(setData).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [params])

  const handleFilter = e => setParams(p => ({ ...p, [e.target.name]: e.target.value }))

  return (
    <div className="page">
      <Navbar user={user} onLogout={onLogout} links={links} />
      <main className="main">
        <h1 className="page-title">Compliance Report</h1>

        {/* Date filters */}
        <div className="card" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem', alignItems: 'flex-end' }}>
          <div className="field" style={{ margin: 0 }}>
            <label>From</label>
            <input type="date" name="date_from" value={params.date_from} onChange={handleFilter} />
          </div>
          <div className="field" style={{ margin: 0 }}>
            <label>To</label>
            <input type="date" name="date_to" value={params.date_to} onChange={handleFilter} />
          </div>
        </div>

        {loading && <p className="loading">Loading…</p>}

        {data && <>
          {/* Overall summary */}
          <div className="stat-grid">
            {[
              { label: 'Assigned',  value: data.summary.assigned  },
              { label: 'Completed', value: data.summary.completed },
              { label: 'Cancelled', value: data.summary.cancelled },
              { label: 'Missed',    value: data.summary.missed    },
              { label: 'Overall Rate', value: data.summary.overall_rate !== null ? `${data.summary.overall_rate}%` : 'N/A' },
            ].map(s => (
              <div className="stat-card" key={s.label}>
                <div className="value" style={s.label === 'Overall Rate' ? { color: rateColor(data.summary.overall_rate) } : {}}>
                  {s.value}
                </div>
                <div className="label">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Per-caregiver table */}
          <h2 className="section-title">Per-Caregiver Breakdown</h2>
          <div className="table-wrap card">
            <table>
              <thead>
                <tr>
                  <th>Caregiver</th>
                  <th>Assigned</th>
                  <th>Completed</th>
                  <th>Missed</th>
                  <th>Cancelled</th>
                  <th>Late</th>
                  <th>No Notes</th>
                  <th>Rate</th>
                </tr>
              </thead>
              <tbody>
                {data.caregiver_stats.map(s => (
                  <tr key={s.caregiver_id}>
                    <td>{s.caregiver_name}</td>
                    <td>{s.assigned}</td>
                    <td>{s.completed}</td>
                    <td>{s.missed}</td>
                    <td>{s.cancelled}</td>
                    <td>{s.late}</td>
                    <td>{s.no_notes}</td>
                    <td style={{ fontWeight: 700, color: rateColor(s.rate) }}>
                      {s.rate !== null ? `${s.rate}%` : 'N/A'}
                    </td>
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
