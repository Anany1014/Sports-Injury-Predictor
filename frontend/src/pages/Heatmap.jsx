// src/pages/Heatmap.jsx
import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { Save, CheckCircle } from 'lucide-react';
import './Heatmap.css';

const BODY_ZONES = [
  { id: 'head', label: 'Head', cx: 200, cy: 40, r: 28 },
  { id: 'neck', label: 'Neck', cx: 200, cy: 82, r: 14 },
  { id: 'left-shoulder', label: 'L. Shoulder', cx: 145, cy: 110, r: 18 },
  { id: 'right-shoulder', label: 'R. Shoulder', cx: 255, cy: 110, r: 18 },
  { id: 'chest', label: 'Chest', cx: 200, cy: 130, r: 22 },
  { id: 'left-arm', label: 'L. Arm', cx: 120, cy: 160, r: 16 },
  { id: 'right-arm', label: 'R. Arm', cx: 280, cy: 160, r: 16 },
  { id: 'abdomen', label: 'Abdomen', cx: 200, cy: 170, r: 22 },
  { id: 'lower-back', label: 'Lower Back', cx: 200, cy: 205, r: 20 },
  { id: 'left-hip', label: 'L. Hip', cx: 165, cy: 230, r: 18 },
  { id: 'right-hip', label: 'R. Hip', cx: 235, cy: 230, r: 18 },
  { id: 'left-thigh', label: 'L. Thigh', cx: 165, cy: 275, r: 18 },
  { id: 'right-thigh', label: 'R. Thigh', cx: 235, cy: 275, r: 18 },
  { id: 'left-knee', label: 'L. Knee', cx: 165, cy: 318, r: 15 },
  { id: 'right-knee', label: 'R. Knee', cx: 235, cy: 318, r: 15 },
  { id: 'left-calf', label: 'L. Calf', cx: 165, cy: 358, r: 14 },
  { id: 'right-calf', label: 'R. Calf', cx: 235, cy: 358, r: 14 },
  { id: 'left-ankle', label: 'L. Ankle', cx: 165, cy: 395, r: 12 },
  { id: 'right-ankle', label: 'R. Ankle', cx: 235, cy: 395, r: 12 },
];

const SEVERITY = [
  { value: 0, label: 'None', color: 'rgba(255,255,255,0.06)' },
  { value: 1, label: 'Mild', color: '#FFD700' },
  { value: 2, label: 'Moderate', color: '#FF8C00' },
  { value: 3, label: 'Severe', color: '#FF4444' },
];

export default function Heatmap() {
  const { bodyDiscomfort, addDiscomfort } = useAthlete();
  const today = new Date().toISOString().split('T')[0];
  const todayEntry = bodyDiscomfort.find(e => e.date === today);

  const [selected, setSelected] = useState(() => {
    const init = {};
    BODY_ZONES.forEach(z => init[z.id] = 0);
    if (todayEntry) todayEntry.regions.forEach(r => { init[r.zone] = r.severity; });
    return init;
  });
  const [activeZone, setActiveZone] = useState(null);
  const [saved, setSaved] = useState(false);

  const handleZoneClick = (zoneId) => {
    setActiveZone(zoneId);
  };

  const handleSeverity = (sev) => {
    if (!activeZone) return;
    setSelected(p => ({...p, [activeZone]: sev}));
  };

  const handleSave = () => {
    const regions = Object.entries(selected)
      .filter(([,sev]) => sev > 0)
      .map(([zone,severity]) => ({zone, severity}));
    addDiscomfort({ date: today, regions });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const getZoneColor = (zoneId) => {
    const sev = selected[zoneId] ?? 0;
    return SEVERITY[sev].color;
  };

  const recentHistory = bodyDiscomfort.slice(-5).reverse();
  const affectedToday = Object.values(selected).filter(s => s > 0).length;

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Body Heatmap</h1>
          <p className="page-subtitle">Click a body region to log discomfort. Track recurring pain patterns over time.</p>
        </div>
      </div>

      <div className="heatmap-layout">
        <div className="card heatmap-body-card">
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16}}>
            <h3>Select Body Region</h3>
            {affectedToday > 0 && <span className="badge badge-medium">{affectedToday} zone{affectedToday>1?'s':''} affected</span>}
          </div>
          <div className="body-svg-wrap">
            <svg viewBox="0 0 400 430" className="body-svg">
              <ellipse cx="200" cy="40" rx="28" ry="32" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.12)" strokeWidth="1.5" />
              <rect x="160" y="97" width="80" height="120" rx="10" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.12)" strokeWidth="1.5" />
              <rect x="100" y="100" width="55" height="90" rx="10" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
              <rect x="245" y="100" width="55" height="90" rx="10" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
              <rect x="160" y="215" width="80" height="100" rx="8" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.12)" strokeWidth="1.5" />
              <rect x="148" y="310" width="45" height="100" rx="8" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
              <rect x="207" y="310" width="45" height="100" rx="8" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />

              {BODY_ZONES.map(zone => (
                <circle
                  key={zone.id}
                  cx={zone.cx} cy={zone.cy} r={zone.r}
                  fill={getZoneColor(zone.id)}
                  stroke={activeZone === zone.id ? 'var(--cyan)' : 'rgba(255,255,255,0.1)'}
                  strokeWidth={activeZone === zone.id ? 2.5 : 1}
                  onClick={() => handleZoneClick(zone.id)}
                  style={{cursor:'pointer',transition:'all 0.2s',filter: selected[zone.id] > 0 ? `drop-shadow(0 0 6px ${SEVERITY[selected[zone.id]].color})` : 'none'}}
                />
              ))}

              {activeZone && (() => {
                const z = BODY_ZONES.find(z => z.id === activeZone);
                return z ? (
                  <text x={z.cx} y={z.cy + z.r + 14} textAnchor="middle" fill="var(--cyan)" fontSize="9" fontFamily="Inter" fontWeight="600">
                    {z.label}
                  </text>
                ) : null;
              })()}
            </svg>
          </div>

          <div className="heatmap-legend">
            {SEVERITY.map(s => (
              <div key={s.value} className="legend-item">
                <div className="legend-dot" style={{background: s.color, boxShadow: s.value > 0 ? `0 0 6px ${s.color}` : 'none'}} />
                <span>{s.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{display:'flex',flexDirection:'column',gap:16}}>
          <div className="card">
            <h3 style={{marginBottom:12}}>Set Severity</h3>
            {activeZone ? (
              <>
                <p style={{color:'var(--cyan)',fontWeight:600,fontSize:'0.9rem',marginBottom:12}}>
                  {BODY_ZONES.find(z=>z.id===activeZone)?.label}
                </p>
                <div className="severity-btns">
                  {SEVERITY.map(s => (
                    <button
                      key={s.value}
                      className={`severity-btn ${selected[activeZone]===s.value?'active':''}`}
                      style={{'--sev-color': s.color}}
                      onClick={() => handleSeverity(s.value)}
                    >
                      <div className="sev-dot" style={{background:s.color}} />
                      {s.label}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <p style={{color:'var(--text-muted)',fontSize:'0.85rem'}}>Click a body zone on the diagram to set its discomfort level.</p>
            )}
          </div>

          <div className="card">
            <h3 style={{marginBottom:12}}>Today's Summary</h3>
            {affectedToday === 0 ? (
              <p style={{color:'var(--green)',fontSize:'0.85rem',fontWeight:600}}>✓ No discomfort reported today</p>
            ) : (
              <div style={{display:'flex',flexDirection:'column',gap:6}}>
                {Object.entries(selected).filter(([,s])=>s>0).map(([zone,sev]) => (
                  <div key={zone} className="zone-summary-row">
                    <span>{BODY_ZONES.find(z=>z.id===zone)?.label}</span>
                    <span className={`badge ${sev===1?'badge-medium':sev===2?'badge-medium':'badge-high'}`} style={{fontSize:'0.65rem'}}>
                      {SEVERITY[sev].label}
                    </span>
                  </div>
                ))}
              </div>
            )}
            <button className="btn btn-primary" style={{marginTop:14,width:'100%',justifyContent:'center'}} onClick={handleSave}>
              {saved ? <><CheckCircle size={14}/> Saved!</> : <><Save size={14}/> Save Heatmap</>}
            </button>
          </div>

          <div className="card">
            <h3 style={{marginBottom:12}}>Recent History</h3>
            {recentHistory.length === 0 ? (
              <p style={{color:'var(--text-muted)',fontSize:'0.82rem'}}>No previous entries</p>
            ) : (
              <div style={{display:'flex',flexDirection:'column',gap:8}}>
                {recentHistory.map(entry => (
                  <div key={entry.date} className="history-entry">
                    <div style={{fontSize:'0.78rem',fontWeight:600,color:'var(--text-secondary)'}}>{entry.date}</div>
                    <div style={{display:'flex',flexWrap:'wrap',gap:4,marginTop:4}}>
                      {entry.regions.length === 0 ? (
                        <span style={{color:'var(--green)',fontSize:'0.72rem'}}>✓ Clear</span>
                      ) : entry.regions.map(r => (
                        <span key={r.zone} className="badge" style={{fontSize:'0.62rem',background:SEVERITY[r.severity].color+'22',color:SEVERITY[r.severity].color,border:`1px solid ${SEVERITY[r.severity].color}44`}}>
                          {BODY_ZONES.find(z=>z.id===r.zone)?.label}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
