import { useEffect, useState } from 'react'
import { getVisits, getCaregivers, getClients, createVisit, updateVisit, deleteVisit } from '../api'
import Navbar from '../components/Navbar'

const ADMIN_LINKS = [
  { to: '/admin',      label: 'Dashboard'  },
  { to: '/clients',    label: 'Clients'    },
  { to: '/caregivers', label: 'Caregivers' },
  { to: '/visits',     label: 'Visits'     },
  { to: '/compliance', label: 'Compliance' },
]
const MANAGER_LINKS = [
  { to: '/manager',    label: 'Dashboard'  },
  { to: '/visits',     label: 'Visits'     },
  { to: '/compliance', label: 'Compliance' },
]

const STATUSES = ['SCHEDULED','IN_PROGRESS','COMPLETED','CANCELLED']
const EMPTY = { caregiver: '', client: '', scheduled_date: '', scheduled_time: '', status: 'SCHEDULED', notes: '' }

function StatusBadge({ status }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status.replace('_', ' ')}</span>
}

export default function Visits({ user, onLogout }) {
  const isAdmin = user.role === 'ADMIN'
  const [visits,     setVisits]     = useState([])
  const [caregivers, setCaregivers] = useState([])
  const [clients,    setClients]    = useState([])
  const [filters,    setFilters]    = useState({ date_from: '', date_to: '', status: '' })
  const [modal,      setModal]      = useState(null)
  const [selected,   setSelected]   = useState(null)
  const [form,       setForm]       = useState(EMPTY)
  const [saving,     setSaving]     = useState(false)
  const [error,      setError]      = useState('')

  const load = () => {
    const params = Object.fromEntries(Object.entries(filters).filter(([,v]) => v))
    getVisits(params).then(setVisits)
  }
  useEffect(() => { load(); getCaregivers().then(setCaregivers); getClients().then(setClients) }, [])
  useEffect(() => { load() }, [filters])

  const openAdd  = () => { setForm(EMPTY); setError(''); setModal('add') }
  const openEdit = v  => { setForm({ caregiver: v.caregiver, client: v.client, scheduled_date: v.scheduled_date, scheduled_time: v.scheduled_time, status: v.status, notes: v.notes }); setSelected(v); setError(''); setModal('edit') }
  const openDel  = v  => { setSelected(v); setModal('delete') }
  const close    = () => { setModal(null); setSelected(null) }

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  const handleFilter = e => setFilters(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSave = async e => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      if (modal === 'add') await createVisit(form)
      else await updateVisit(selected.id, form)
      load(); close()
    } catch (err) {
      setError(Object.values(err || {}).flat().join(' ') || 'Save failed.')
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    setSaving(true)
    try { await deleteVisit(selected.id); load(); close() }
    finally { setSaving(false) }
  }

  return (
    <div className="page">
      <Navbar user={user} onLogout={onLogout} links={isAdmin ? ADMIN_LINKS : MANAGER_LINKS} />
      <main className="main">
        <div className="flex-between">
          <h1 className="page-title">Visits</h1>
          {isAdmin && <button className="btn btn-primary" onClick={openAdd}>+ Schedule Visit</button>}
        </div>

        {/* Filters */}
        <div className="card" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem', alignItems: 'flex-end' }}>
          <div className="field" style={{ margin: 0, flex: '1 1 140px' }}>
            <label>From</label>
            <input type="date" name="date_from" value={filters.date_from} onChange={handleFilter} />
          </div>
          <div className="field" style={{ margin: 0, flex: '1 1 140px' }}>
            <label>To</label>
            <input type="date" name="date_to" value={filters.date_to} onChange={handleFilter} />
          </div>
          <div className="field" style={{ margin: 0, flex: '1 1 140px' }}>
            <label>Status</label>
            <select name="status" value={filters.status} onChange={handleFilter}>
              <option value="">All</option>
              {STATUSES.map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
            </select>
          </div>
        </div>

        <div className="table-wrap card">
          <table>
            <thead>
              <tr><th>Date</th><th>Time</th><th>Caregiver</th><th>Client</th><th>Status</th><th>Check-in</th>{isAdmin && <th>Actions</th>}</tr>
            </thead>
            <tbody>
              {visits.map(v => (
                <tr key={v.id}>
                  <td>{v.scheduled_date}</td>
                  <td>{v.scheduled_time}</td>
                  <td>{v.caregiver_name}</td>
                  <td>{v.client_name}</td>
                  <td><StatusBadge status={v.status} /></td>
                  <td>{v.check_in_time ? new Date(v.check_in_time).toLocaleTimeString() : '—'}</td>
                  {isAdmin && (
                    <td>
                      <button className="btn btn-outline btn-sm" onClick={() => openEdit(v)}>Edit</button>{' '}
                      <button className="btn btn-danger btn-sm" onClick={() => openDel(v)}>Delete</button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>

      {(modal === 'add' || modal === 'edit') && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{modal === 'add' ? 'Schedule Visit' : 'Edit Visit'}</h3>
            <form onSubmit={handleSave}>
              <div className="field">
                <label>Caregiver</label>
                <select name="caregiver" value={form.caregiver} onChange={handleChange} required>
                  <option value="">— select —</option>
                  {caregivers.map(c => <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Client</label>
                <select name="client" value={form.client} onChange={handleChange} required>
                  <option value="">— select —</option>
                  {clients.filter(c => c.is_active).map(c => <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Date</label>
                <input type="date" name="scheduled_date" value={form.scheduled_date} onChange={handleChange} required />
              </div>
              <div className="field">
                <label>Time</label>
                <input type="time" name="scheduled_time" value={form.scheduled_time} onChange={handleChange} required />
              </div>
              <div className="field">
                <label>Status</label>
                <select name="status" value={form.status} onChange={handleChange}>
                  {STATUSES.map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Notes</label>
                <textarea name="notes" value={form.notes} onChange={handleChange} rows={3} />
              </div>
              {error && <p className="error-msg">{error}</p>}
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={close}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modal === 'delete' && selected && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Delete Visit</h3>
            <p>Delete the visit on <strong>{selected.scheduled_date}</strong> for <strong>{selected.client_name}</strong>?</p>
            <div className="modal-actions">
              <button className="btn btn-outline" onClick={close}>Cancel</button>
              <button className="btn btn-danger" disabled={saving} onClick={handleDelete}>{saving ? '…' : 'Delete'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
