// src/pages/ACWRMonitor.jsx
import { useAthlete } from '../context/AthleteContext';
import { getACWRZone, getLast28DaysACWRData } from '../utils/calculations';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import './ACWRMonitor.css';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: '10px 14px', fontSize: 12 }}>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>{label}</p>
        {payload.map(p => (
          <p key={p.name} style={{ color: p.color, fontWeight: 600 }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function ACWRMonitor() {
  const { workouts, acwr } = useAthlete();
  const zone = getACWRZone(acwr.ratio);
  const chartData = getLast28DaysACWRData(workouts);

  const zoneIcon = acwr.ratio === 0 ? Info
    : acwr.ratio < 0.8 || acwr.ratio > 1.5 ? AlertTriangle : CheckCircle;
  const ZoneIcon = zoneIcon;

  const weeklyLoads = [0,1,2,3].map(weekOffset => {
    const end = new Date(); end.setDate(end.getDate() - weekOffset * 7);
    const start = new Date(end); start.setDate(start.getDate() - 6);
    const load = workouts
      .filter(w => new Date(w.date) >= start && new Date(w.date) <= end)
      .reduce((s,w) => s + w.load, 0);
    const label = weekOffset === 0 ? 'This Week' : weekOffset === 1 ? 'Last Week' : `${weekOffset}w ago`;
    return { label, load };
  }).reverse();

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">ACWR Monitor</h1>
          <p className="page-subtitle">Acute-to-Chronic Workload Ratio — the gold standard for injury risk assessment</p>
        </div>
      </div>

      <div className="acwr-hero">
        <div className="card card-glow acwr-ratio-card">
          <div className="acwr-ratio-label">Current ACWR</div>
          <div className="acwr-ratio-big" style={{ color: zone.color }}>
            {acwr.ratio || '—'}
          </div>
          <div className="acwr-zone-badge" style={{ background: `${zone.color}22`, color: zone.color, border: `1px solid ${zone.color}44` }}>
            <ZoneIcon size={13} /> {zone.label}
          </div>
          <p className="acwr-hint">{zone.hint}</p>

          <div className="acwr-gauge-wrap">
            <div className="acwr-gauge">
              <div className="gauge-zone" style={{ background: '#94A3B8', flex: 0.8 }} />
              <div className="gauge-zone" style={{ background: '#39FF14', flex: 0.5 }} />
              <div className="gauge-zone" style={{ background: '#FFD700', flex: 0.2 }} />
              <div className="gauge-zone" style={{ background: '#FF4444', flex: 0.5 }} />
              {acwr.ratio > 0 && (
                <div
                  className="gauge-needle"
                  style={{ left: `${Math.min(Math.max((acwr.ratio / 2.0) * 100, 2), 98)}%` }}
                />
              )}
            </div>
            <div className="gauge-labels">
              <span>0</span><span>0.8</span><span>1.3</span><span>1.5</span><span>2.0+</span>
            </div>
          </div>
        </div>

        <div className="acwr-loads">
          <div className="card acwr-load-card">
            <div className="acwr-load-label">Acute Load</div>
            <div className="acwr-load-val" style={{ color: 'var(--cyan)' }}>{acwr.acuteLoad.toLocaleString()}</div>
            <div className="acwr-load-sub">Sum of last 7 days (AU)</div>
          </div>
          <div className="card acwr-load-card">
            <div className="acwr-load-label">Chronic Load</div>
            <div className="acwr-load-val" style={{ color: 'var(--purple)' }}>{acwr.chronicLoad.toLocaleString()}</div>
            <div className="acwr-load-sub">Avg weekly load over 28d (AU)</div>
          </div>
          <div className="card acwr-info-card">
            <h4 style={{ marginBottom: 10 }}>Zone Guide</h4>
            {[
              { range: '< 0.8', label: 'Undertraining', color: '#94A3B8' },
              { range: '0.8 – 1.3', label: 'Optimal Zone', color: '#39FF14' },
              { range: '1.3 – 1.5', label: 'Caution', color: '#FFD700' },
              { range: '> 1.5', label: 'Danger Zone', color: '#FF4444' },
            ].map(z => (
              <div key={z.range} className="zone-row">
                <div className="zone-dot" style={{ background: z.color }} />
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{z.range}</span>
                <span style={{ color: z.color, fontSize: '0.8rem', fontWeight: 600, marginLeft: 'auto' }}>{z.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 20, padding: 24 }}>
        <h3 style={{ marginBottom: 4 }}>28-Day Workload Analysis</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginBottom: 20 }}>Acute load (bars) vs chronic baseline and ACWR ratio trend</p>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="label" tick={{ fill: '#94A3B8', fontSize: 10 }} interval={3} />
            <YAxis yAxisId="load" tick={{ fill: '#94A3B8', fontSize: 10 }} />
            <YAxis yAxisId="ratio" orientation="right" domain={[0, 2.5]} tick={{ fill: '#94A3B8', fontSize: 10 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#94A3B8' }} />
            <Bar yAxisId="load" dataKey="acute" name="Acute Load" fill="rgba(0,212,255,0.3)" radius={[3,3,0,0]} />
            <Line yAxisId="load" type="monotone" dataKey="chronic" name="Chronic Load" stroke="#7C3AED" strokeWidth={2} dot={false} />
            <Line yAxisId="ratio" type="monotone" dataKey="ratio" name="ACWR Ratio" stroke="#FFD700" strokeWidth={2.5} dot={false} />
            <ReferenceLine yAxisId="ratio" y={1.3} stroke="#FFD700" strokeDasharray="4 4" label={{ value: '1.3', fill: '#FFD700', fontSize: 10 }} />
            <ReferenceLine yAxisId="ratio" y={1.5} stroke="#FF4444" strokeDasharray="4 4" label={{ value: '1.5', fill: '#FF4444', fontSize: 10 }} />
            <ReferenceLine yAxisId="ratio" y={0.8} stroke="#94A3B8" strokeDasharray="4 4" label={{ value: '0.8', fill: '#94A3B8', fontSize: 10 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="card" style={{ marginTop: 20, padding: 24 }}>
        <h3 style={{ marginBottom: 16 }}>Weekly Load Breakdown</h3>
        <div className="weekly-load-grid">
          {weeklyLoads.map((w, i) => (
            <div key={w.label} className="weekly-load-card" style={{ borderColor: i === 3 ? 'var(--border-active)' : 'var(--border)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{w.label}</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: i === 3 ? 'var(--cyan)' : 'var(--text-primary)', marginTop: 4 }}>{w.load.toLocaleString()}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>AU</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
