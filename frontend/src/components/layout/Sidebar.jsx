// src/components/layout/Sidebar.jsx
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, User, Activity, Map, Dumbbell,
  TrendingUp, Heart, Bluetooth, ChevronRight, FileText, LogOut,
  Sun, Moon
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
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
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();

  if (!user) return null;

  const displayName = getPrettyName(user.username);
  const initials = displayName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();

  const filteredItems = navItems.filter(item =>
    !item.restrictedRoles || item.restrictedRoles.includes(user.role)
  );

  return (
    <nav className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⚡</div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">AthletIQ</span>
          <span className="sidebar-logo-sub">Telemetry Platform</span>
        </div>

        <button
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {isDark ? <Sun size={16} color="#F59E0B" /> : <Moon size={16} color="#0284C7" />}
        </button>
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

      <div className="sidebar-footer">
        <div className="sidebar-user" onClick={() => { navigate('/profile'); onClose && onClose(); }}>
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{displayName}</div>
            <div className="sidebar-user-role">{user.role || 'Athlete'}</div>
          </div>
        </div>
        <button className="logout-btn-full" onClick={logout} title="Sign Out Session">
          <LogOut size={15} />
          <span>Sign Out</span>
        </button>
      </div>
    </nav>
  );
}
