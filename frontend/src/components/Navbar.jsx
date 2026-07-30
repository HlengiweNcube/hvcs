import { useState } from 'react'
import { Link } from 'react-router-dom'
import { logout } from '../api'

export default function Navbar({ user, onLogout, links = [] }) {
  const [open, setOpen] = useState(false)
  const handleLogout = () => { logout(); onLogout() }
  return (
    <nav className="navbar">
      <span className="navbar-brand">HVCS</span>
      <button
        className={`nav-toggle${open ? ' open' : ''}`}
        aria-label="Toggle navigation"
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}
      >
        <span></span><span></span><span></span>
      </button>
      <div className={`navbar-menu${open ? ' open' : ''}`}>
        <div className="navbar-links">
          {links.map(({ to, label }) => (
            <Link key={to} to={to} onClick={() => setOpen(false)}>{label}</Link>
          ))}
          <span style={{ color: '#c7f5d9', fontSize: '.85rem' }}>{user?.first_name || user?.username}</span>
          <button className="btn btn-outline btn-sm" style={{ color: '#fff', borderColor: '#c7f5d9' }} onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}
