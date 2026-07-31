// src/pages/Recovery.jsx
import { useState, useRef } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { getACWRZone } from '../utils/calculations';
import { buildAthleteRecordPayload } from '../services/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';
import AIRecoveryFull from '../components/AIRecoveryFull';
import { Brain, Sparkles, RefreshCw, AlertCircle } from 'lucide-react';
import './Recovery.css';

const intensityColors = { Low: 'var(--green)', Medium: 'var(--yellow)', High: 'var(--red)' };

export default function Recovery() {
  const { todayLog, acwr, injuryRisk, dailyLogs, profile, workouts, mlPrediction } = useAthlete();
  const safeAcwr = acwr || { ratio: 0 };
  const zone = getACWRZone(safeAcwr.ratio || 0);

  const historyData = (dailyLogs || []).slice(-14).map(l => ({
    date: l.date.slice(5),
    readiness: l.readinessScore,
  }));

  const liveRecord = buildAthleteRecordPayload(profile || {}, todayLog || {}, workouts || []);
  const livePrediction = mlPrediction || {
    athlete_id: liveRecord.athlete_id,
    injury_probability: injuryRisk === 'High' ? 0.72 : injuryRisk === 'Medium' ? 0.45 : 0.18,
    injury_risk_label: (injuryRisk || 'Low').toUpperCase(),
    top_contributing_factors: [
      `ACWR Ratio: ${safeAcwr.ratio || '—'}`,
      `Readiness Score: ${todayLog?.readinessScore ?? '—'}`,
      `Injury Risk Level: ${injuryRisk || 'Low'}`,
    ],
    model_version: 'xgboost-v1.0',
  };

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Recovery Hub</h1>
          <p className="page-subtitle">Personalised recovery guidance based on your readiness and workload</p>
        </div>
      </div>

      <div className="recovery-layout">
        {/* Left column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Status card */}
          <div className="card card-glow recovery-status-card">
            <h3 style={{ marginBottom: 16 }}>Today's Recovery Status</h3>
            <div className="recovery-status-row">
              <div className="recovery-metric">
                <div className="rm-val" style={{ color: intensityColors[injuryRisk] }}>{injuryRisk}</div>
                <div className="rm-label">Injury Risk</div>
              </div>
              <div className="recovery-divider" />
              <div className="recovery-metric">
                <div className="rm-val" style={{ color: zone.color }}>{safeAcwr.ratio || '—'}</div>
                <div className="rm-label">ACWR Ratio</div>
              </div>
              <div className="recovery-divider" />
              <div className="recovery-metric">
                <div className="rm-val" style={{ color: 'var(--cyan)' }}>{todayLog?.readinessScore ?? '—'}</div>
                <div className="rm-label">Readiness</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right column */}
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
        </div>
      </div>

      {/* Full-width Unified Performance Recovery & Prescription Engine */}
      <AIRecoveryFull record={liveRecord} prediction={livePrediction} />
    </div>
  );
}
