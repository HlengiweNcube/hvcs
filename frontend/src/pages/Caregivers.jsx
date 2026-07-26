import { useEffect, useState } from 'react'
import { getCaregivers, createCaregiver, updateCaregiver, deleteCaregiver } from '../api'
import Navbar from '../components/Navbar'

const ADMIN_LINKS = [
  { to: '/admin',      label: 'Dashboard'  },
  { to: '/clients',    label: 'Clients'    },
  { to: '/caregivers', label: 'Caregivers' },
  { to: '/visits',     label: 'Visits'     },
  { to: '/compliance', label: 'Compliance' },
]

const EMPTY_CREATE = { username: '', email: '', password: '', first_name: '', last_name: '', phone: '', qualifications: '', is_active: true }
const EMPTY_EDIT   = { username: '', email: '', first_name: '', last_name: '', phone: '', qualifications: '', is_active: true }

export default function Caregivers({ user, onLogout }) {
  const [caregivers, setCaregivers] = useState([])
  const [modal, setModal]           = useState(null)
  const [selected, setSelected]     = useState(null)
  const [form, setForm]             = useState(EMPTY_CREATE)
  const [saving, setSaving]         = useState(false)
  const [error, setError]           = useState('')

  const load = () => getCaregivers().then(setCaregivers)
  useEffect(() => { load() }, [])

  const openAdd  = () => { setForm(EMPTY_CREATE); setError(''); setModal('add') }
  const openEdit = c  => {
    setForm({
      username: c.user.username, email: c.user.email,
      first_name: c.first_name, last_name: c.last_name,
      phone: c.phone, qualifications: c.qualifications, is_active: c.is_active,
    })
    setSelected(c); setError(''); setModal('edit')
  }
  const openDel  = c  => { setSelected(c); setModal('delete') }
  const close    = () => { setModal(null); setSelected(null) }

  const handleChange = e => {
    const { name, value, type, checked } = e.target
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
  }

  const handleSave = async e => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      if (modal === 'add') await createCaregiver(form)
      else await updateCaregiver(selected.id, form)
      await load(); close()
    } catch (err) {
      setError(Object.values(err || {}).flat().join(' ') || 'Save failed.')
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    setSaving(true)
    try { await deleteCaregiver(selected.id); await load(); close() }
    finally { setSaving(false) }
  }

  return (
    <div className="page">
      <Navbar user={user} onLogout={onLogout} links={ADMIN_LINKS} />
      <main className="main">
        <div className="flex-between">
          <h1 className="page-title">Caregivers</h1>
          <button className="btn btn-primary" onClick={openAdd}>+ Add Caregiver</button>
        </div>

        <div className="table-wrap card">
          <table>
            <thead>
              <tr><th>Name</th><th>Username</th><th>Phone</th><th>Qualifications</th><th>Active</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {caregivers.map(c => (
                <tr key={c.id}>
                  <td>{c.first_name} {c.last_name}</td>
                  <td>{c.user.username}</td>
                  <td>{c.phone || '—'}</td>
                  <td>{c.qualifications || '—'}</td>
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

      {(modal === 'add' || modal === 'edit') && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{modal === 'add' ? 'Add Caregiver' : 'Edit Caregiver'}</h3>
            <form onSubmit={handleSave}>
              {[
                { name: 'first_name',    label: 'First Name' },
                { name: 'last_name',     label: 'Last Name'  },
                { name: 'username',      label: 'Username'   },
                { name: 'email',         label: 'Email', type: 'email' },
                ...(modal === 'add' ? [{ name: 'password', label: 'Password', type: 'password' }] : []),
                { name: 'phone',         label: 'Phone'      },
                { name: 'qualifications',label: 'Qualifications' },
              ].map(({ name, label, type = 'text' }) => (
                <div className="field" key={name}>
                  <label>{label}</label>
                  <input name={name} type={type} value={form[name] ?? ''} onChange={handleChange}
                    required={['first_name','last_name','username'].includes(name) || (modal === 'add' && name === 'password')} />
                </div>
              ))}
              <div className="field" style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                <input type="checkbox" name="is_active" checked={form.is_active} onChange={handleChange} id="cga" />
                <label htmlFor="cga" style={{ margin: 0 }}>Active</label>
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
            <h3>Delete Caregiver</h3>
            <p>Delete <strong>{selected.first_name} {selected.last_name}</strong>? Their login account and all visit records will also be removed.</p>
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
