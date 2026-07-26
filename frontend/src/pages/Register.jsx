import { useState } from 'react'
import { Link } from 'react-router-dom'
import { register, getMe } from '../api'

export default function Register({ onLogin }) {
  const [form, setForm]     = useState({ username: '', email: '', first_name: '', last_name: '', phone: '', qualifications: '', password: '', password2: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    if (form.password !== form.password2) { setError('Passwords do not match.'); return }
    setLoading(true)
    try {
      await register(form)
      // Auto-login after register
      const { login } = await import('../api')
      await login(form.username, form.password)
      const me = await getMe()
      onLogin(me)
    } catch (err) {
      const msgs = Object.values(err || {}).flat().join(' ')
      setError(msgs || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="form-card" style={{ maxWidth: 520 }}>
      <h2>Caregiver Registration</h2>
      <form onSubmit={handleSubmit}>
        {[
          { name: 'first_name', label: 'First Name' },
          { name: 'last_name',  label: 'Last Name'  },
          { name: 'username',   label: 'Username'   },
          { name: 'email',      label: 'Email', type: 'email' },
          { name: 'phone',      label: 'Phone'      },
          { name: 'qualifications', label: 'Qualifications' },
          { name: 'password',   label: 'Password', type: 'password' },
          { name: 'password2',  label: 'Confirm Password', type: 'password' },
        ].map(({ name, label, type = 'text' }) => (
          <div className="field" key={name}>
            <label>{label}</label>
            <input name={name} type={type} value={form[name]} onChange={handleChange}
              required={['first_name','last_name','username','password','password2'].includes(name)} />
          </div>
        ))}
        {error && <p className="error-msg">{error}</p>}
        <button className="btn btn-primary" style={{ width: '100%', marginTop: '.5rem' }} disabled={loading}>
          {loading ? 'Registering…' : 'Register'}
        </button>
      </form>
      <p style={{ marginTop: '1rem', fontSize: '.875rem', textAlign: 'center' }}>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </div>
  )
}
