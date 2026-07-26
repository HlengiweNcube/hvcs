import { useEffect, useState } from 'react'
import { getClients, createClient, updateClient, deleteClient } from '../api'
import Navbar from '../components/Navbar'

const ADMIN_LINKS = [
  { to: '/admin',      label: 'Dashboard'  },
  { to: '/clients',    label: 'Clients'    },
  { to: '/caregivers', label: 'Caregivers' },
  { to: '/visits',     label: 'Visits'     },
  { to: '/compliance', label: 'Compliance' },
]

const EMPTY = { first_name: '', last_name: '', address: '', contact_phone: '', care_needs: '', is_active: true }

export default function Clients({ user, onLogout }) {
  const [clients, setClients]   = useState([])
  const [modal, setModal]       = useState(null)   // null | 'add' | 'edit' | 'delete'
  const [selected, setSelected] = useState(null)
  const [form, setForm]         = useState(EMPTY)
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState('')

  const load = () => getClients().then(setClients)
  useEffect(() => { load() }, [])

  const openAdd  = () => { setForm(EMPTY); setError(''); setModal('add') }
  const openEdit = c  => { setForm({ ...c }); setSelected(c); setError(''); setModal('edit') }
  const openDel  = c  => { setSelected(c); setModal('delete') }
  const close    = () => { setModal(null); setSelected(null) }

  const handleChange = e => {
    const { name, value, type, checked } = e.target
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
  }

  const handleSave = async e => {
    e.preventDefault()
    setSaving(true); setError('')
    try {
      if (modal === 'add') await createClient(form)
      else await updateClient(selected.id, form)
      await load(); close()
    } catch (err) {
      setError(Object.values(err || {}).flat().join(' ') || 'Save failed.')
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    setSaving(true)
    try { await deleteClient(selected.id); await load(); close() }
    finally { setSaving(false) }
  }

  return (
    <div className="page">
      <Navbar user={user} onLogout={onLogout} links={ADMIN_LINKS} />
      <main className="main">
        <div className="flex-between">
          <h1 className="page-title">Clients</h1>
          <button className="btn btn-primary" onClick={openAdd}>+ Add Client</button>
        </div>

        <div className="table-wrap card">
          <table>
            <thead>
              <tr><th>Name</th><th>Address</th><th>Phone</th><th>Care Needs</th><th>Active</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {clients.map(c => (
                <tr key={c.id}>
                  <td>{c.first_name} {c.last_name}</td>
                  <td>{c.address}</td>
                  <td>{c.contact_phone || '—'}</td>
                  <td style={{ maxWidth: 200 }}>{c.care_needs || '—'}</td>
                  <td>{c.is_active ? '✓' : '✗'}</td>
                  <td>
                    <button className="btn btn-outline btn-sm" onClick={() => openEdit(c)}>Edit</button>{' '}
                    <button className="btn btn-danger btn-sm" onClick={() => openDel(c)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>

      {/* Add / Edit Modal */}
      {(modal === 'add' || modal === 'edit') && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{modal === 'add' ? 'Add Client' : 'Edit Client'}</h3>
            <form onSubmit={handleSave}>
              {[
                { name: 'first_name',    label: 'First Name' },
                { name: 'last_name',     label: 'Last Name'  },
                { name: 'address',       label: 'Address'    },
                { name: 'contact_phone', label: 'Phone'      },
              ].map(({ name, label }) => (
                <div className="field" key={name}>
                  <label>{label}</label>
                  <input name={name} value={form[name]} onChange={handleChange}
                    required={['first_name','last_name','address'].includes(name)} />
                </div>
              ))}
              <div className="field">
                <label>Care Needs</label>
                <textarea name="care_needs" value={form.care_needs} onChange={handleChange} rows={3} />
              </div>
              <div className="field" style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                <input type="checkbox" name="is_active" checked={form.is_active} onChange={handleChange} id="ca" />
                <label htmlFor="ca" style={{ margin: 0 }}>Active</label>
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

      {/* Delete Modal */}
      {modal === 'delete' && selected && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Delete Client</h3>
            <p>Are you sure you want to delete <strong>{selected.first_name} {selected.last_name}</strong>? This cannot be undone.</p>
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
