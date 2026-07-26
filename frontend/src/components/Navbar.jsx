import { Link } from 'react-router-dom'
import { logout } from '../api'

export default function Navbar({ user, onLogout, links = [] }) {
  const handleLogout = () => { logout(); onLogout() }
  return (
    <nav className="navbar">
      <span className="navbar-brand">HVCS</span>
      <div className="navbar-links">
        {links.map(({ to, label }) => <Link key={to} to={to}>{label}</Link>)}
        <span style={{ color: '#c7f5d9', fontSize: '.85rem' }}>{user?.first_name || user?.username}</span>
        <button className="btn btn-outline btn-sm" style={{ color: '#fff', borderColor: '#c7f5d9' }} onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  )
}
