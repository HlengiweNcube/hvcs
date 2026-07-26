import { useState } from 'react'
import { Link } from 'react-router-dom'
import { login } from '../api'

export default function Login({ onLogin }) {
  const [form, setForm]     = useState({ username: '', password: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      // Fetch the user profile after login so App knows the role
      const { getMe } = await import('../api')
      const me = await getMe()
      onLogin(me)
    } catch (err) {
      setError(err?.detail || 'Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="form-card">
      <h2>HVCS — Sign In</h2>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Username</label>
          <input name="username" value={form.username} onChange={handleChange} required autoFocus />
        </div>
        <div className="field">
          <label>Password</label>
          <input name="password" type="password" value={form.password} onChange={handleChange} required />
        </div>
        {error && <p className="error-msg">{error}</p>}
        <button className="btn btn-primary" style={{ width: '100%', marginTop: '.5rem' }} disabled={loading}>
          {loading ? 'Signing in…' : 'Sign In'}
        </button>
      </form>
      <p style={{ marginTop: '1rem', fontSize: '.875rem', textAlign: 'center' }}>
        New caregiver? <Link to="/register">Register here</Link>
      </p>
    </div>
  )
}
