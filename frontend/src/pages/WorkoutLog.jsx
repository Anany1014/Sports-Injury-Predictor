// src/pages/WorkoutLog.jsx
import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { Plus, Calendar, Clock, Flame, Trophy, Filter } from 'lucide-react';
import './WorkoutLog.css';

const SPORTS = ['Running','Football','Cricket','Basketball','Badminton','Athletics','Fitness Training','Cycling','Swimming','Tennis'];

const SPORT_EMOJI = {
  Running:'🏃',Football:'⚽',Cricket:'🏏',Basketball:'🏀',Badminton:'🏸',
  Athletics:'🏅','Fitness Training':'🏋️',Cycling:'🚴',Swimming:'🏊',Tennis:'🎾',
};

const RPE_LABELS = ['','Very Light','Light','Moderate','Somewhat Hard','Hard','Hard','Very Hard','Very Hard','Maximal','Maximal'];

export default function WorkoutLog() {
  const { workouts, addWorkout } = useAthlete();
  const today = new Date().toISOString().split('T')[0];

  const [form, setForm] = useState({ date: today, sport: 'Running', duration: 45, rpe: 6 });
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState('All');
  const [added, setAdded] = useState(false);

  const handleAdd = () => {
    if (!form.duration || !form.rpe) return;
    addWorkout(form);
    setAdded(true);
    setTimeout(() => { setAdded(false); setShowForm(false); }, 1500);
  };

  const filtered = filter === 'All' ? workouts : workouts.filter(w => w.sport === filter);
  const totalLoad7d = workouts
    .filter(w => { const d=new Date();d.setDate(d.getDate()-7);return new Date(w.date)>=d; })
    .reduce((s,w)=>s+w.load,0);

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Workout Log</h1>
          <p className="page-subtitle">Track every training session and monitor your workload</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(v=>!v)}>
          <Plus size={15}/> Log Session
        </button>
      </div>

      <div className="grid-4" style={{marginBottom:20}}>
        <div className="stat-card">
          <div style={{display:'flex',gap:6,alignItems:'center'}}><Trophy size={14} color="var(--yellow)"/><span className="stat-label">Total Sessions</span></div>
          <div className="stat-value">{workouts.length}</div>
        </div>
        <div className="stat-card">
          <div style={{display:'flex',gap:6,alignItems:'center'}}><Flame size={14} color="var(--orange)"/><span className="stat-label">7-Day Load</span></div>
          <div className="stat-value" style={{color:'var(--orange)'}}>{totalLoad7d.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div style={{display:'flex',gap:6,alignItems:'center'}}><Clock size={14} color="var(--cyan)"/><span className="stat-label">Avg Duration</span></div>
          <div className="stat-value" style={{color:'var(--cyan)'}}>
            {workouts.length ? Math.round(workouts.reduce((s,w)=>s+w.duration,0)/workouts.length) : 0}<span style={{fontSize:'1rem'}}>m</span>
          </div>
        </div>
        <div className="stat-card">
          <div style={{display:'flex',gap:6,alignItems:'center'}}><Calendar size={14} color="var(--purple)"/><span className="stat-label">Avg RPE</span></div>
          <div className="stat-value" style={{color:'var(--purple)'}}>
            {workouts.length ? (workouts.reduce((s,w)=>s+w.rpe,0)/workouts.length).toFixed(1) : '--'}
          </div>
        </div>
      </div>

      {showForm && (
        <div className="card card-glow workout-form-card animate-fade-in" style={{marginBottom:20}}>
          <h3 style={{marginBottom:20}}>Log New Session</h3>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Sport</label>
              <select className="form-input" value={form.sport} onChange={e=>setForm(p=>({...p,sport:e.target.value}))}>
                {SPORTS.map(s=><option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Date</label>
              <input type="date" className="form-input" value={form.date} max={today}
                onChange={e=>setForm(p=>({...p,date:e.target.value}))} />
            </div>
          </div>
          <div className="form-group" style={{marginTop:16}}>
            <div style={{display:'flex',justifyContent:'space-between'}}>
              <label className="form-label">Duration (minutes)</label>
              <span style={{fontWeight:700,color:'var(--cyan)'}}>{form.duration} min</span>
            </div>
            <input type="range" className="slider" min="10" max="240" value={form.duration}
              onChange={e=>setForm(p=>({...p,duration:+e.target.value}))} />
          </div>
          <div className="form-group" style={{marginTop:16}}>
            <div style={{display:'flex',justifyContent:'space-between'}}>
              <label className="form-label">Session RPE (Borg Scale 1–10)</label>
              <span style={{fontWeight:700,color:'var(--orange)'}}>{form.rpe} – {RPE_LABELS[form.rpe]}</span>
            </div>
            <input type="range" className="slider" min="1" max="10" value={form.rpe}
              onChange={e=>setForm(p=>({...p,rpe:+e.target.value}))} />
            <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.7rem',color:'var(--text-muted)',marginTop:4}}>
              <span>1 – Very Light</span><span>10 – Max</span>
            </div>
          </div>
          <div style={{background:'rgba(0,212,255,0.06)',borderRadius:8,padding:'10px 14px',marginTop:12,fontSize:'0.82rem',color:'var(--text-secondary)'}}>
            Estimated Training Load: <span style={{color:'var(--cyan)',fontWeight:700}}>{form.duration * form.rpe} AU</span>
            <span style={{marginLeft:8,color:'var(--text-muted)'}}>(Duration × RPE)</span>
          </div>
          <div style={{display:'flex',gap:10,marginTop:18}}>
            <button className="btn btn-primary" onClick={handleAdd} disabled={added}>
              {added ? '✓ Added!' : <><Plus size={14}/> Add Session</>}
            </button>
            <button className="btn btn-secondary" onClick={()=>setShowForm(false)}>Cancel</button>
          </div>
        </div>
      )}

      <div className="workout-filters">
        <Filter size={14} color="var(--text-muted)" />
        {['All',...SPORTS.filter(s=>workouts.some(w=>w.sport===s))].map(s => (
          <button key={s} className={`filter-chip ${filter===s?'active':''}`} onClick={()=>setFilter(s)}>
            {SPORT_EMOJI[s] || '🏅'} {s}
          </button>
        ))}
      </div>

      <div className="workout-list">
        {filtered.length === 0 ? (
          <div className="card" style={{textAlign:'center',padding:40,color:'var(--text-muted)'}}>
            <div style={{fontSize:'2rem',marginBottom:8}}>🏋️</div>
            <p>No sessions logged yet. Start by clicking "Log Session".</p>
          </div>
        ) : (
          filtered.map(w => (
            <div key={w.id} className="workout-card">
              <div className="workout-card-emoji">{SPORT_EMOJI[w.sport] || '🏅'}</div>
              <div className="workout-card-info">
                <div className="workout-card-sport">{w.sport}</div>
                <div className="workout-card-date">{new Date(w.date+'T00:00').toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'})}</div>
              </div>
              <div className="workout-card-stats">
                <div className="wc-stat"><Clock size={12}/> {w.duration}m</div>
                <div className="wc-stat"><Flame size={12}/> RPE {w.rpe}</div>
              </div>
              <div className="workout-card-load">
                <div style={{fontSize:'1.2rem',fontWeight:800,color:'var(--cyan)'}}>{w.load}</div>
                <div style={{fontSize:'0.65rem',color:'var(--text-muted)'}}>AU Load</div>
              </div>
              <div className="rpe-bar-wrap">
                <div className="rpe-bar" style={{width:`${w.rpe*10}%`,background: w.rpe<=4?'var(--green)':w.rpe<=7?'var(--orange)':'var(--red)'}} />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
