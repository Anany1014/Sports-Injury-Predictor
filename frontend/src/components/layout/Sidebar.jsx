// src/components/layout/Sidebar.jsx
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, User, Activity, Map, Dumbbell,
  TrendingUp, Heart, Bluetooth, ChevronRight, FileText
} from 'lucide-react';
import { useAthlete } from '../../context/AthleteContext';
import './Sidebar.css';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/readiness', icon: Activity, label: 'Daily Readiness' },
  { to: '/heatmap', icon: Map, label: 'Body Heatmap' },
  { to: '/workout', icon: Dumbbell, label: 'Workout Log' },
  { to: '/acwr', icon: TrendingUp, label: 'ACWR Monitor' },
  { to: '/recovery', icon: Heart, label: 'Recovery' },
  { to: '/records', icon: FileText, label: 'Assessment Records' },
  { to: '/wearable', icon: Bluetooth, label: 'Wearable Sync' },
];

export default function Sidebar() {
  const { profile } = useAthlete();
  const navigate = useNavigate();
  const initials = profile.name ? profile.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'AT';

  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⚡</div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">AthletIQ</span>
          <span className="sidebar-logo-sub">Intelligence Platform</span>
        </div>
      </div>

      <div className="sidebar-nav">
        <span className="sidebar-section-label">Main</span>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon className="nav-icon" size={18} />
            {label}
          </NavLink>
        ))}
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-profile-mini" onClick={() => navigate('/profile')}>
          <div className="profile-avatar">{initials}</div>
          <div className="profile-info">
            <div className="profile-name">{profile.name || 'Set Up Profile'}</div>
            <div className="profile-sport">{profile.sport || 'Athlete'}</div>
          </div>
          <ChevronRight size={14} color="var(--text-muted)" />
        </div>
      </div>
    </nav>
  );
}
