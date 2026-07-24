// src/pages/Readiness.jsx
import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { getReadinessLabel } from '../utils/calculations';
import { Activity, Heart, Moon, CheckCircle, Save, AlertCircle } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import './Readiness.css';

export default function Readiness() {
  const { dailyLogs, addDailyLog, todayLog, wearableSync } = useAthlete();
  const today = new Date().toISOString().split('T')[0];

  const [form, setForm] = useState({
    hrv: todayLog?.hrv ?? wearableSync?.hrv ?? 60,
    rhr: todayLog?.rhr ?? wearableSync?.rhr ?? 65,
    sleepHours: todayLog?.sleepHours ?? wearableSync?.sleepHours ?? 7.5,
    sorenessScore: todayLog?.sorenessScore ?? 4.5,
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    addDailyLog({ date: today, ...form });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const hrvScore = Math.min(100, Math.max(0, ((form.hrv - 20) / 80) * 100));
  const rhrScore = Math.min(100, Math.max(0, ((100 - form.rhr) / 60) * 100));
  const s = form.sleepHours;
  const sleepScore = s >= 9 ? 100 : s >= 7 ? 75 + ((s - 7) / 2) * 25 : s >= 5 ? (s - 5) / 2 * 75 : 0;
  const sorenessComp = Math.max(0, 100 - (form.sorenessScore * 10));

  const calculateReadiness = Math.round(hrvScore * 0.35 + rhrScore * 0.25 + sleepScore * 0.25 + sorenessComp * 0.15);

  const radarData = [
    { metric: 'HRV', value: Math.round(hrvScore) },
    { metric: 'Resting HR', value: Math.round(rhrScore) },
    { metric: 'Sleep', value: Math.round(sleepScore) },
    { metric: 'Muscle Recovery', value: Math.round(sorenessComp) },
  ];

  const scoreLabel = getReadinessLabel(calculateReadiness);

  const historyData = dailyLogs.slice(-14).map(l => ({
    date: l.date.slice(5),
    score: l.readinessScore,
  }));

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Daily Readiness & Soreness Assessment</h1>
          <p className="page-subtitle">Log your morning physiological data & muscle soreness rating (PDF AthleteRecord Spec)</p>
        </div>
      </div>

      <div className="readiness-grid">
        <div className="card readiness-form-card">
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:20}}>
            <h3>Morning Assessment Input</h3>
            {wearableSync?.lastSync && <span className="badge badge-cyan" style={{fontSize:'0.65rem'}}>⚡ Wearable Synced</span>}
          </div>

          <div className="form-group" style={{marginBottom:20}}>
            <div className="metric-header">
              <Activity size={15} color="var(--cyan)" />
              <label className="form-label">HRV (hrv_ms: 0 - 200 ms)</label>
              <span className="metric-val" style={{color:'var(--cyan)'}}>{form.hrv} ms</span>
            </div>
            <input type="range" className="slider" min="20" max="120" value={form.hrv}
              onChange={e => setForm(p => ({...p, hrv: +e.target.value}))} />
            <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.7rem',color:'var(--text-muted)'}}>
              <span>Low (20ms)</span><span>High (120ms)</span>
            </div>
          </div>

          <div className="form-group" style={{marginBottom:20}}>
            <div className="metric-header">
              <Heart size={15} color="var(--red)" />
              <label className="form-label">Resting Heart Rate (rhr)</label>
              <span className="metric-val" style={{color:'var(--red)'}}>{form.rhr} bpm</span>
            </div>
            <input type="range" className="slider" min="40" max="100" value={form.rhr}
              onChange={e => setForm(p => ({...p, rhr: +e.target.value}))} />
            <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.7rem',color:'var(--text-muted)'}}>
              <span>Excellent (40)</span><span>High (100)</span>
            </div>
          </div>

          <div className="form-group" style={{marginBottom:20}}>
            <div className="metric-header">
              <Moon size={15} style={{color:'#7C3AED'}} />
              <label className="form-label">Sleep Hours (sleep_hours: 0 - 12h)</label>
              <span className="metric-val" style={{color:'#7C3AED'}}>{form.sleepHours}h</span>
            </div>
            <input type="range" className="slider" min="3" max="12" step="0.5" value={form.sleepHours}
              onChange={e => setForm(p => ({...p, sleepHours: +e.target.value}))} />
            <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.7rem',color:'var(--text-muted)'}}>
              <span>3h</span><span>12h</span>
            </div>
          </div>

          <div className="form-group" style={{marginBottom:24}}>
            <div className="metric-header">
              <AlertCircle size={15} color="var(--orange)" />
              <label className="form-label">Muscle Soreness Score (soreness_score: 0 - 10)</label>
              <span className="metric-val" style={{color:'var(--orange)'}}>{form.sorenessScore} / 10</span>
            </div>
            <input type="range" className="slider" min="0" max="10" step="0.5" value={form.sorenessScore}
              onChange={e => setForm(p => ({...p, sorenessScore: +e.target.value}))} />
            <div style={{display:'flex',justifyContent:'space-between',fontSize:'0.7rem',color:'var(--text-muted)'}}>
              <span>0 (None)</span><span>10 (Extreme Soreness)</span>
            </div>
          </div>

          <button className="btn btn-primary" style={{width:'100%',justifyContent:'center',padding:'12px'}} onClick={handleSave}>
            {saved ? <><CheckCircle size={15}/> Assessment Saved!</> : <><Save size={15}/> Save Today's Assessment</>}
          </button>
        </div>

        <div style={{display:'flex',flexDirection:'column',gap:16}}>
          <div className="card card-glow readiness-score-card">
            <h3 style={{marginBottom:16}}>Readiness Score</h3>
            <div className="readiness-score-big" style={{color: scoreLabel.color}}>
              {calculateReadiness}
              <span className="readiness-score-unit">/100</span>
            </div>
            <div className={`badge ${calculateReadiness >= 80 ? 'badge-low' : calculateReadiness >= 65 ? 'badge-cyan' : calculateReadiness >= 45 ? 'badge-medium' : 'badge-high'}`} style={{marginTop:8}}>
              {scoreLabel.label}
            </div>
            <div className="score-breakdown">
              <div className="score-bar-row">
                <span>HRV</span>
                <div className="score-bar"><div className="score-fill" style={{width:`${Math.round(hrvScore)}%`,background:'var(--cyan)'}}/></div>
                <span style={{color:'var(--cyan)',fontWeight:600}}>{Math.round(hrvScore)}</span>
              </div>
              <div className="score-bar-row">
                <span>Resting HR</span>
                <div className="score-bar"><div className="score-fill" style={{width:`${Math.round(rhrScore)}%`,background:'var(--red)'}}/></div>
                <span style={{color:'var(--red)',fontWeight:600}}>{Math.round(rhrScore)}</span>
              </div>
              <div className="score-bar-row">
                <span>Sleep</span>
                <div className="score-bar"><div className="score-fill" style={{width:`${Math.round(sleepScore)}%`,background:'#7C3AED'}}/></div>
                <span style={{color:'#7C3AED',fontWeight:600}}>{Math.round(sleepScore)}</span>
              </div>
              <div className="score-bar-row">
                <span>Soreness Recovery</span>
                <div className="score-bar"><div className="score-fill" style={{width:`${Math.round(sorenessComp)}%`,background:'var(--orange)'}}/></div>
                <span style={{color:'var(--orange)',fontWeight:600}}>{Math.round(sorenessComp)}</span>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{marginBottom:12}}>Component Radar</h3>
            <ResponsiveContainer width="100%" height={180}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.06)" />
                <PolarAngleAxis dataKey="metric" tick={{fill:'#94A3B8',fontSize:10}} />
                <Radar dataKey="value" stroke="var(--cyan)" fill="var(--cyan)" fillOpacity={0.15} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {historyData.length > 1 && (
        <div className="card" style={{marginTop:20}}>
          <h3 style={{marginBottom:16}}>14-Day Readiness History</h3>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={historyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{fill:'#94A3B8',fontSize:10}} />
              <YAxis domain={[0,100]} tick={{fill:'#94A3B8',fontSize:10}} />
              <Tooltip contentStyle={{background:'var(--bg-card)',border:'1px solid var(--border)',borderRadius:8,fontSize:11}} />
              <Line type="monotone" dataKey="score" stroke="var(--cyan)" strokeWidth={2} dot={{fill:'var(--cyan)',r:3}} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
