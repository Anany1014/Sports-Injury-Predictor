// src/pages/Profile.jsx
import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { Save, CheckCircle } from 'lucide-react';
import './Profile.css';

const SPORTS = ['Running','Football','Cricket','Basketball','Badminton','Athletics','Fitness Training','Cycling','Swimming','Tennis'];
const SPORT_EMOJI = { Running:'🏃',Football:'⚽',Cricket:'🏏',Basketball:'🏀',Badminton:'🏸',Athletics:'🏅','Fitness Training':'🏋️',Cycling:'🚴',Swimming:'🏊',Tennis:'🎾' };

export default function Profile() {
  const { profile, setProfile, workouts, dailyLogs } = useAthlete();
  const [form, setForm] = useState({ ...profile });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setProfile({ ...form, createdAt: profile.createdAt || new Date().toISOString() });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const initials = form.name ? form.name.split(' ').map(n=>n[0]).join('').slice(0,2).toUpperCase() : 'AT';

  const stats = [
    { label: 'Total Sessions', val: workouts.length },
    { label: 'Days Tracked', val: dailyLogs.length },
    { label: 'Total Load', val: workouts.reduce((s,w)=>s+w.load,0).toLocaleString() },
    { label: 'Avg RPE', val: workouts.length ? (workouts.reduce((s,w)=>s+w.rpe,0)/workouts.length).toFixed(1) : '--' },
  ];

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Athlete Profile</h1>
          <p className="page-subtitle">Manage your personal information, physical stats, and injury history</p>
        </div>
      </div>

      <div className="profile-layout">
        <div style={{display:'flex',flexDirection:'column',gap:16}}>
          <div className="card profile-avatar-card">
            <div className="profile-big-avatar">{initials}</div>
            <div className="profile-avatar-name">{form.name || 'Your Name'}</div>
            <div className="profile-avatar-sport">
              {SPORT_EMOJI[form.sport] || '🏅'} {form.sport} {form.position ? `(${form.position})` : ''}
            </div>
            <div className="badge badge-cyan" style={{ marginTop: 4 }}>ID: {form.athlete_id || 'ATH-101'}</div>
            {form.age && <div className="profile-avatar-meta" style={{ marginTop: 4 }}>Age {form.age} · {form.gender || 'Athlete'}</div>}
          </div>

          <div className="card">
            <h3 style={{marginBottom:14}}>Training Stats</h3>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
              {stats.map(s => (
                <div key={s.label} className="profile-stat">
                  <div className="profile-stat-val">{s.val}</div>
                  <div className="profile-stat-label">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {form.createdAt && (
            <div className="card" style={{padding:'14px 18px'}}>
              <div style={{fontSize:'0.72rem',color:'var(--text-muted)',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.06em',marginBottom:4}}>Member Since</div>
              <div style={{fontWeight:700}}>{new Date(form.createdAt).toLocaleDateString('en-US',{month:'long',year:'numeric'})}</div>
            </div>
          )}
        </div>

        <div className="card profile-form-card">
          <h3 style={{marginBottom:20}}>Personal & Assessment Fields (AthleteRecord Spec)</h3>

          <div className="grid-2" style={{gap:16}}>
            <div className="form-group">
              <label className="form-label">Athlete ID (athlete_id)</label>
              <input className="form-input" placeholder="e.g. ATH-101" value={form.athlete_id || ''}
                onChange={e=>setForm(p=>({...p,athlete_id:e.target.value}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" placeholder="e.g. Alex Rivera" value={form.name || ''}
                onChange={e=>setForm(p=>({...p,name:e.target.value}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Primary Sport (sport)</label>
              <select className="form-input" value={form.sport || 'Football'} onChange={e=>setForm(p=>({...p,sport:e.target.value}))}>
                {SPORTS.map(s=><option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Playing Position (position)</label>
              <input className="form-input" placeholder="e.g. Midfielder / Point Guard" value={form.position || ''}
                onChange={e=>setForm(p=>({...p,position:e.target.value}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Age (15 - 50 years)</label>
              <input className="form-input" type="number" min="15" max="50" placeholder="e.g. 24" value={form.age || ''}
                onChange={e=>setForm(p=>({...p,age:e.target.value}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Gender</label>
              <select className="form-input" value={form.gender || ''} onChange={e=>setForm(p=>({...p,gender:e.target.value}))}>
                <option value="">Select</option>
                <option>Male</option>
                <option>Female</option>
                <option>Non-binary</option>
                <option>Prefer not to say</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Height (cm) [140 - 220 cm]</label>
              <input className="form-input" type="number" step="0.1" min="140" max="220" placeholder="e.g. 178.0" value={form.height || ''}
                onChange={e=>setForm(p=>({...p,height:e.target.value}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Weight (kg) [40 - 150 kg]</label>
              <input className="form-input" type="number" step="0.1" min="40" max="150" placeholder="e.g. 75.5" value={form.weight || ''}
                onChange={e=>setForm(p=>({...p,weight:e.target.value}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Prior Career Injuries (prior_injuries)</label>
              <input className="form-input" type="number" min="0" placeholder="e.g. 2" value={form.prior_injuries ?? ''}
                onChange={e=>setForm(p=>({...p,prior_injuries:e.target.value}))} />
            </div>
            <div className="form-group">
              <label className="form-label">Days Since Last Injury (days_since_last_injury)</label>
              <input className="form-input" type="number" min="0" step="1" placeholder="e.g. 90" value={form.days_since_last_injury ?? ''}
                onChange={e=>setForm(p=>({...p,days_since_last_injury:e.target.value}))} />
            </div>
          </div>

          <div className="divider" style={{margin:'20px 0'}} />

          <div className="form-group" style={{marginBottom:20}}>
            <label className="form-label">Training History / Notes</label>
            <textarea
              className="form-input"
              style={{minHeight:90,resize:'vertical',lineHeight:1.6}}
              placeholder="e.g. Football midfielder. Focused on agility and high weekly volume."
              value={form.trainingHistory || ''}
              onChange={e=>setForm(p=>({...p,trainingHistory:e.target.value}))}
            />
          </div>

          <button className="btn btn-primary" style={{padding:'12px 24px'}} onClick={handleSave}>
            {saved ? <><CheckCircle size={15}/> Profile Saved!</> : <><Save size={15}/> Save Profile</>}
          </button>
        </div>
      </div>
    </div>
  );
}
