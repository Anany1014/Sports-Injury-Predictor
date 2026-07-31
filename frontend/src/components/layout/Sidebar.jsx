import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, User, Activity, Map, Dumbbell,
  TrendingUp, Heart, Bluetooth, ChevronRight, FileText, LogOut
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './Sidebar.css';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/readiness', icon: Activity, label: 'Daily Readiness' },
  { to: '/heatmap', icon: Map, label: 'Body Heatmap' },
  { to: '/workout', icon: Dumbbell, label: 'Workout Log' },
  { to: '/acwr', icon: TrendingUp, label: 'ACWR Monitor' },
  { to: '/recovery', icon: Heart, label: 'Recovery' },
  { to: '/records', icon: FileText, label: 'Assessment Records', restrictedRoles: ['Coach', 'Medical Staff', 'Admin'] },
  { to: '/wearable', icon: Bluetooth, label: 'Wearable Sync' },
];

const getPrettyName = (username) => {
  switch (username) {
    case 'alex': return 'Alex Rivera';
    case 'coach_dan': return 'Dan Miller';
    case 'physio_sarah': return 'Sarah Jenkins';
    case 'admin': return 'System Admin';
    default: return username;
  }
};

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const displayName = getPrettyName(user.username);
  const initials = displayName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();

  // Filter items matching user permissions
  const filteredItems = navItems.filter(item =>
    !item.restrictedRoles || item.restrictedRoles.includes(user.role)
  );

  return (
    <nav className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⚡</div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">AthletIQ</span>
          <span className="sidebar-logo-sub">Intelligence Platform</span>
        </div>
      </div>

      <div className="sidebar-nav">
        <span className="sidebar-section-label">Main</span>
        {filteredItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            onClick={onClose}
          >
            <Icon className="nav-icon" size={18} />
            {label}
          </NavLink>
        ))}
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-profile-mini" onClick={() => { navigate('/profile'); onClose && onClose(); }}>
          <div className="profile-avatar">{initials}</div>
          <div className="profile-info">
            <div className="profile-name">{displayName}</div>
            <div className="profile-sport">{user.role}</div>
          </div>
        </div>
        <button
          className="btn-logout-sidebar"
          onClick={logout}
          title="Sign Out Session"
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 8,
            borderRadius: 6,
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
            marginTop: 10,
            width: '100%'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--red)';
            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-muted)';
            e.currentTarget.style.background = 'none';
          }}
        >
          <LogOut size={16} style={{ marginRight: 8 }} />
          <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Logout</span>
        </button>
      </div>
    </nav>
  );
}


