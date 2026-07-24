// src/pages/Recovery.jsx
import { useAthlete } from '../context/AthleteContext';
import { getRecoveryTips, getACWRZone } from '../utils/calculations';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';
import './Recovery.css';

const intensityColors = { Low: 'var(--green)', Medium: 'var(--yellow)', High: 'var(--red)' };

export default function Recovery() {
  const { todayLog, acwr, injuryRisk, dailyLogs } = useAthlete();
  const tips = getRecoveryTips(todayLog?.readinessScore, acwr.ratio, injuryRisk);
  const zone = getACWRZone(acwr.ratio);

  const historyData = dailyLogs.slice(-14).map(l => ({
    date: l.date.slice(5),
    readiness: l.readinessScore,
  }));

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Recovery Hub</h1>
          <p className="page-subtitle">Personalized recovery guidance based on your readiness and workload</p>
        </div>
      </div>

      <div className="recovery-layout">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card card-glow recovery-status-card">
            <h3 style={{ marginBottom: 16 }}>Today's Recovery Status</h3>
            <div className="recovery-status-row">
              <div className="recovery-metric">
                <div className="rm-val" style={{ color: intensityColors[injuryRisk] }}>{injuryRisk}</div>
                <div className="rm-label">Injury Risk</div>
              </div>
              <div className="recovery-divider" />
              <div className="recovery-metric">
                <div className="rm-val" style={{ color: zone.color }}>{acwr.ratio || '—'}</div>
                <div className="rm-label">ACWR Ratio</div>
              </div>
              <div className="recovery-divider" />
              <div className="recovery-metric">
                <div className="rm-val" style={{ color: 'var(--cyan)' }}>{todayLog?.readinessScore ?? '—'}</div>
                <div className="rm-label">Readiness</div>
              </div>
            </div>

            <div className="recovery-recommendation">
              {injuryRisk === 'High' ? (
                <div className="rec-alert high">
                  🛑 <strong>Full Rest Recommended</strong> — Your injury risk is high. Skip today's training session and focus on active recovery.
                </div>
              ) : injuryRisk === 'Medium' ? (
                <div className="rec-alert medium">
                  ⚠️ <strong>Light Training Only</strong> — Stick to low-intensity work. Prioritize mobility and recovery activities.
                </div>
              ) : (
                <div className="rec-alert low">
                  ✅ <strong>Ready to Train</strong> — Your body shows good recovery. Proceed with your planned session.
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 16 }}>Recovery Recommendations</h3>
            <div className="tips-grid">
              {tips.map((tip, i) => (
                <div key={i} className="tip-card animate-fade-in" style={{ animationDelay: `${i * 0.06}s` }}>
                  <div className="tip-icon">{tip.icon}</div>
                  <div>
                    <div className="tip-title">{tip.title}</div>
                    <div className="tip-desc">{tip.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <h3 style={{ marginBottom: 16 }}>14-Day Readiness Trend</h3>
            {historyData.length > 1 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={historyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="date" tick={{ fill: '#94A3B8', fontSize: 10 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 11 }} />
                  <Line type="monotone" dataKey="readiness" stroke="var(--cyan)" strokeWidth={2} dot={{ fill: 'var(--cyan)', r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Log more readiness data to see your trend.</p>
            )}
          </div>

          <div className="card recovery-protocols-card">
            <h3 style={{ marginBottom: 14 }}>Recovery Protocols</h3>
            {[
              { emoji: '🧊', name: 'Cold Water Immersion', time: '10–15 min', benefit: 'Reduces inflammation' },
              { emoji: '🛁', name: 'Contrast Therapy', time: '3 cycles × 1 min', benefit: 'Boosts circulation' },
              { emoji: '🧴', name: 'Foam Rolling', time: '15–20 min', benefit: 'Releases muscle tension' },
              { emoji: '😴', name: 'Sleep Optimization', time: '8–9 hours', benefit: 'Peak recovery' },
              { emoji: '🍌', name: 'Carb + Protein Refuel', time: 'Within 45 min', benefit: 'Glycogen replenishment' },
            ].map(p => (
              <div key={p.name} className="protocol-row">
                <span className="protocol-emoji">{p.emoji}</span>
                <div style={{ flex: 1 }}>
                  <div className="protocol-name">{p.name}</div>
                  <div className="protocol-time">{p.time}</div>
                </div>
                <span className="protocol-benefit">{p.benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
