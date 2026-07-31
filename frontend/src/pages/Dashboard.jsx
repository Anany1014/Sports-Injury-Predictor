// src/pages/Dashboard.jsx
import { useNavigate } from 'react-router-dom';
import { useAthlete } from '../context/AthleteContext';
import { getReadinessLabel, getACWRZone } from '../utils/calculations';
import { Activity, TrendingUp, Zap, Heart, Moon, ArrowRight, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { LineChart, Line, XAxis, Tooltip, ResponsiveContainer } from 'recharts';
import InjuryPredictorSection from '../components/InjuryPredictorSection';
import './Dashboard.css';

function ReadinessRing({ score }) {
  const label = getReadinessLabel(score);
  const pct = score ?? 0;
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (pct / 100) * circumference;
  return (
    <div className="readiness-ring-wrap">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
        <circle
          cx="70" cy="70" r="54" fill="none"
          stroke={label.color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dashoffset 1s ease', filter: `drop-shadow(0 0 8px ${label.color}66)` }}
        />
        <text x="70" y="62" textAnchor="middle" fill={label.color} fontSize="26" fontWeight="800" fontFamily="Inter">{score ?? '--'}</text>
        <text x="70" y="80" textAnchor="middle" fill="#94A3B8" fontSize="10" fontFamily="Inter">READINESS</text>
        <text x="70" y="95" textAnchor="middle" fill={label.color} fontSize="11" fontWeight="700" fontFamily="Inter">{label.label}</text>
      </svg>
    </div>
  );
}

function InjuryRiskCard({ risk, mlPrediction, isMlLoading }) {
  const normalizedRisk = mlPrediction?.injury_risk_label || risk || 'Low';
  const formattedRisk = normalizedRisk.charAt(0).toUpperCase() + normalizedRisk.slice(1).toLowerCase();
  
  const cfg = {
    Low: { cls: 'badge-low', icon: CheckCircle, msg: 'Training is safe today based on ML metrics' },
    Medium: { cls: 'badge-medium', icon: AlertTriangle, msg: 'Monitor workload and fatigue carefully' },
    High: { cls: 'badge-high', icon: AlertTriangle, msg: 'Elevated injury probability — consider rest or light load' },
  };
  const { cls, icon: Icon, msg } = cfg[formattedRisk] || cfg.Low;
  const probabilityPct = mlPrediction ? Math.round(mlPrediction.injury_probability * 100) : null;

  return (
    <div className="injury-card">
      <div className="injury-card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="injury-label">Injury Risk</span>
          <span style={{ fontSize: '0.65rem', background: 'rgba(0, 212, 255, 0.15)', color: '#00D4FF', border: '1px solid rgba(0, 212, 255, 0.3)', padding: '2px 6px', borderRadius: 4, fontWeight: 700 }}>
            ML Model v1.0
          </span>
        </div>
        <span className={`badge ${cls}`}><Icon size={11} />{formattedRisk} {probabilityPct !== null ? `(${probabilityPct}%)` : ''}</span>
      </div>
      <p className="injury-msg">{msg}</p>
      {mlPrediction?.top_contributing_factors?.length > 0 && (
        <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600 }}>
            Top Contributing Factors:
          </span>
          <ul style={{ margin: 0, paddingLeft: 16, fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            {mlPrediction.top_contributing_factors.map((f, idx) => (
              <li key={idx} style={{ marginBottom: 2 }}>{f}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function MiniSparkline({ data }) {
  if (!data || data.length === 0) return <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No data yet</div>;
  return (
    <ResponsiveContainer width="100%" height={50}>
      <LineChart data={data}>
        <Line type="monotone" dataKey="ratio" stroke="var(--cyan)" strokeWidth={2} dot={false} />
        <XAxis dataKey="label" hide />
        <Tooltip
          contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 11 }}
          labelStyle={{ color: 'var(--text-secondary)' }}
          itemStyle={{ color: 'var(--cyan)' }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

const journeySteps = [
  { id: 'morning', label: 'Morning Sync', icon: '🌅', desc: 'HRV & sleep logged' },
  { id: 'pre', label: 'Pre-Workout', icon: '🔥', desc: 'Readiness assessed' },
  { id: 'session', label: 'Training Session', icon: '💪', desc: 'Log your workout' },
  { id: 'post', label: 'Post-Workout', icon: '📊', desc: 'RPE recorded' },
];

export default function Dashboard() {
  const { todayLog = null, workouts = [], acwr = { ratio: 0, acuteLoad: 0, chronicLoad: 0 }, injuryRisk = 'Low', profile = {}, mlPrediction = null, isMlLoading = false } = useAthlete() || {};
  const navigate = useNavigate();
  const safeWorkouts = Array.isArray(workouts) ? workouts : [];
  const safeAcwr = acwr || { ratio: 0, acuteLoad: 0, chronicLoad: 0 };
  const safeProfile = profile || {};
  const zone = getACWRZone(safeAcwr.ratio || 0);

  const today = new Date().toISOString().split('T')[0];
  const todayWorkout = safeWorkouts.find(w => w && w.date === today);

  const completedSteps = [
    todayLog ? 'morning' : null,
    todayLog ? 'pre' : null,
    todayWorkout ? 'session' : null,
    todayWorkout ? 'post' : null,
  ].filter(Boolean);

  const last7 = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const ds = d.toISOString().split('T')[0];
    const ws = safeWorkouts.filter(w => w && w.date === ds);
    const load = ws.reduce((s, w) => s + (w.load || 0), 0);
    last7.push({ label: ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d.getDay()], load });
  }

  const acwrSparkData = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const start7 = new Date(d); start7.setDate(start7.getDate() - 6);
    const start28 = new Date(d); start28.setDate(start28.getDate() - 27);
    const ac = safeWorkouts.filter(w => w && new Date(w.date) >= start7 && new Date(w.date) <= d).reduce((s, w) => s + (w.load || 0), 0);
    const ch = safeWorkouts.filter(w => w && new Date(w.date) >= start28 && new Date(w.date) <= d).reduce((s, w) => s + (w.load || 0), 0) / 4;
    acwrSparkData.push({ label: `${d.getMonth()+1}/${d.getDate()}`, ratio: ch > 0 ? +(ac/ch).toFixed(2) : 0 });
  }

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="page dashboard animate-fade-in">
      <div className="page-header">
        <div className="dash-greeting">
          <h1 className="page-title">{greeting()}, {profile.name || 'Athlete'} 👋</h1>
          <p className="page-subtitle">{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/readiness')}>
          <Zap size={15} /> Log Today's Data
        </button>
      </div>

      <div className="dash-hero">
        <div className="card card-glow dash-readiness-card">
          <div className="dash-readiness-inner">
            <ReadinessRing score={todayLog?.readinessScore} />
            <div className="dash-readiness-info">
              <h3>Daily Readiness</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 6 }}>
                {todayLog ? 'Based on today\'s HRV, RHR & sleep data' : 'Log your morning data to get your score'}
              </p>
              {todayLog && (
                <div className="readiness-metrics">
                  <div className="rm-item"><Activity size={13} style={{color:'var(--cyan)'}} /><span>HRV: <b>{todayLog.hrv} ms</b></span></div>
                  <div className="rm-item"><Heart size={13} style={{color:'var(--red)'}} /><span>RHR: <b>{todayLog.rhr} bpm</b></span></div>
                  <div className="rm-item"><Moon size={13} style={{color:'var(--purple)'}} /><span>Sleep: <b>{todayLog.sleepHours}h</b></span></div>
                </div>
              )}
              {!todayLog && (
                <button className="btn btn-primary" style={{marginTop:12}} onClick={()=>navigate('/readiness')}>
                  Log Now <ArrowRight size={14}/>
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="dash-side-cards">
          <InjuryRiskCard risk={injuryRisk} mlPrediction={mlPrediction} isMlLoading={isMlLoading} />
          <div className="card acwr-mini-card">
            <div className="acwr-mini-header">
              <span className="injury-label">ACWR Ratio</span>
              <span style={{ color: zone.color, fontWeight: 700, fontSize: '0.85rem' }}>{acwr.ratio || '--'}</span>
            </div>
            <div style={{ margin: '4px 0' }}>
              <span style={{ background: `${zone.color}22`, color: zone.color, padding: '2px 8px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 700 }}>{zone.label}</span>
            </div>
            <MiniSparkline data={acwrSparkData} />
          </div>
        </div>
      </div>

      <div className="grid-4" style={{marginTop: 20}}>
        <div className="stat-card" style={{ borderColor: 'rgba(0,212,255,0.25)' }}>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <Activity size={16} color="var(--cyan)" />
            <span className="stat-label">Acute Load</span>
          </div>
          <div className="stat-value" style={{ color: 'var(--cyan)' }}>{acwr.acuteLoad.toLocaleString()}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Last 7 days (AU)</div>
        </div>
        <div className="stat-card" style={{ borderColor: 'rgba(124,58,237,0.3)' }}>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <TrendingUp size={16} color="var(--purple)" />
            <span className="stat-label">Chronic Load</span>
          </div>
          <div className="stat-value" style={{ color: 'var(--purple)' }}>{acwr.chronicLoad.toLocaleString()}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>28-day avg/week (AU)</div>
        </div>
        <div className="stat-card">
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <Clock size={16} color="var(--orange)" />
            <span className="stat-label">Sessions (7d)</span>
          </div>
          <div className="stat-value" style={{ color: 'var(--orange)' }}>
            {workouts.filter(w => { const d = new Date(); d.setDate(d.getDate()-7); return new Date(w.date) >= d; }).length}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Workouts logged</div>
        </div>
        <div className="stat-card">
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <Heart size={16} color="var(--red)" />
            <span className="stat-label">Avg RPE (7d)</span>
          </div>
          <div className="stat-value" style={{ color: 'var(--text-primary)' }}>
            {(() => { const recent = workouts.filter(w => { const d=new Date();d.setDate(d.getDate()-7);return new Date(w.date)>=d; }); return recent.length ? (recent.reduce((s,w)=>s+w.rpe,0)/recent.length).toFixed(1) : '--'; })()}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Avg RPE this week</div>
        </div>
      </div>

      <div className="card" style={{marginTop:20}}>
        <h3 style={{marginBottom:16}}>Today's Training Journey</h3>
        <div className="journey-steps">
          {journeySteps.map((step, idx) => {
            const done = completedSteps.includes(step.id);
            return (
              <div key={step.id} className={`journey-step ${done ? 'done' : ''}`}>
                <div className={`journey-icon ${done ? 'done' : ''}`}>{done ? '✓' : step.icon}</div>
                <div className="journey-connector" style={{ visibility: idx < journeySteps.length - 1 ? 'visible' : 'hidden' }} />
                <div className="journey-info">
                  <div className="journey-step-label">{step.label}</div>
                  <div className="journey-step-desc">{done ? 'Completed ✓' : step.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* New Interactive ML Injury Risk Predictor Section */}
      <InjuryPredictorSection />

      <div className="card" style={{marginTop:20}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16}}>
          <h3>Weekly Training Load</h3>
          <button className="btn btn-ghost" onClick={()=>navigate('/acwr')} style={{fontSize:'0.8rem'}}>Full Analysis <ArrowRight size={13}/></button>
        </div>
        <div className="weekly-bars">
          {last7.map((d, i) => {
            const max = Math.max(...last7.map(x=>x.load), 1);
            const pct = (d.load / max) * 100;
            const isToday = i === 6;
            return (
              <div key={i} className="week-bar-col">
                <div className="week-bar-wrap">
                  <div
                    className="week-bar"
                    style={{
                      height: `${Math.max(pct, 4)}%`,
                      background: isToday ? 'linear-gradient(to top, var(--cyan), var(--purple))' : 'rgba(0,212,255,0.3)',
                      boxShadow: isToday ? 'var(--shadow-cyan)' : 'none',
                    }}
                  />
                </div>
                <div className="week-bar-label" style={{color: isToday ? 'var(--cyan)' : 'var(--text-muted)'}}>{d.label}</div>
                {d.load > 0 && <div style={{fontSize:'0.62rem',color:'var(--text-muted)',textAlign:'center'}}>{d.load}</div>}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
