// src/components/InjuryPredictorSection.jsx
import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { predictInjuryRisk, formatAthleteId } from '../services/api';
import {
  Cpu, AlertTriangle, CheckCircle, ShieldCheck, Zap, Activity,
  RefreshCw, Sliders, ArrowRight, Loader2, Sparkles, User, Heart, Moon
} from 'lucide-react';
import AIRecoveryFull from './AIRecoveryFull';
import './InjuryPredictorSection.css';

export const SPORT_POSITIONS_MAP = {
  Football: ['Midfielder', 'Goalkeeper', 'Center Back', 'Fullback', 'Central Midfielder', 'Winger', 'Striker / Forward'],
  Basketball: ['Point Guard', 'Shooting Guard', 'Small Forward', 'Power Forward', 'Center'],
  Running: ['Marathoner', 'Sprinter', 'Middle Distance', 'Trail Runner'],
  Tennis: ['Singles', 'Doubles'],
  Badminton: ['Singles', 'Doubles'],
  Rugby: ['Forward (Prop/Hooker/Lock)', 'Back (Scrum-half/Fly-half/Center/Wing)'],
  Cricket: ['Batsman', 'Fast Bowler', 'Spin Bowler', 'Wicketkeeper', 'All-Rounder'],
  Baseball: ['Pitcher', 'Catcher', 'Infielder', 'Outfielder'],
  Swimming: ['Freestyle / Distance', 'Sprint / Butterfly / Backstroke / Breaststroke'],
  Cycling: ['Road Racer', 'Time Trialist', 'Sprinter', 'Climber'],
  'Fitness Training': ['General Athlete', 'Endurance', 'Powerlifting / Crossfit'],
};

export default function InjuryPredictorSection() {
  const { profile, todayLog, workouts, refetchMlPrediction } = useAthlete();
  const todayStr = new Date().toISOString().split('T')[0];

  const initialSport = SPORT_POSITIONS_MAP[profile.sport] ? profile.sport : 'Football';
  const initialPosition = SPORT_POSITIONS_MAP[initialSport].includes(profile.position)
    ? profile.position
    : SPORT_POSITIONS_MAP[initialSport][0];

  const [form, setForm] = useState({
    athlete_id: profile.athlete_id || 'ATH-101',
    date: todayStr,
    sport: initialSport,
    position: initialPosition,
    age: profile.age || 24,
    weight_kg: profile.weight || 75.5,
    height_cm: profile.height || 178.0,
    weekly_volume_hrs: 14.5,
    weekly_intensity_score: 8.2,
    sleep_hours: todayLog?.sleepHours || 7.5,
    hrv_ms: todayLog?.hrv || 58.0,
    soreness_score: 4.5,
    rest_days: 1,
    prior_injuries: profile.prior_injuries || 2,
    days_since_last_injury: profile.days_since_last_injury || 90.0,
  });

  const [prediction, setPrediction] = useState(null);
  const [lastSubmittedRecord, setLastSubmittedRecord] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleSportChange = (e) => {
    const newSport = e.target.value;
    const positions = SPORT_POSITIONS_MAP[newSport] || ['General Athlete'];
    setForm(prev => ({
      ...prev,
      sport: newSport,
      position: positions[0],
    }));
  };

  const handlePreset = (type) => {
    if (type === 'optimal') {
      setForm(prev => ({
        ...prev,
        weekly_volume_hrs: 6.5,
        weekly_intensity_score: 3.5,
        sleep_hours: 8.5,
        hrv_ms: 85.0,
        soreness_score: 1.0,
        rest_days: 2,
        prior_injuries: 0,
        days_since_last_injury: 365.0,
      }));
    } else if (type === 'spike') {
      setForm(prev => ({
        ...prev,
        weekly_volume_hrs: 28.5,
        weekly_intensity_score: 9.2,
        sleep_hours: 5.0,
        hrv_ms: 36.0,
        soreness_score: 8.5,
        rest_days: 0,
        prior_injuries: 2,
        days_since_last_injury: 45.0,
      }));
    } else if (type === 'recovery') {
      setForm(prev => ({
        ...prev,
        weekly_volume_hrs: 8.0,
        weekly_intensity_score: 4.0,
        sleep_hours: 9.0,
        hrv_ms: 65.0,
        soreness_score: 3.0,
        rest_days: 3,
        prior_injuries: 3,
        days_since_last_injury: 21.0,
      }));
    }
  };

  const handlePredict = async (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    const payload = {
      athlete_id: formatAthleteId(form.athlete_id),
      date: String(form.date),
      sport: String(form.sport).trim(),
      position: String(form.position).trim(),
      age: Number(form.age),
      weight_kg: Number(form.weight_kg),
      height_cm: Number(form.height_cm),
      weekly_volume_hrs: Number(form.weekly_volume_hrs),
      weekly_intensity_score: Number(form.weekly_intensity_score),
      sleep_hours: Number(form.sleep_hours),
      hrv_ms: Number(form.hrv_ms),
      soreness_score: Number(form.soreness_score),
      rest_days: Number(form.rest_days),
      prior_injuries: Number(form.prior_injuries),
      days_since_last_injury: Number(form.days_since_last_injury),
    };

    setLastSubmittedRecord(payload);

    try {
      const result = await predictInjuryRisk(payload);
      setPrediction(result);
      if (refetchMlPrediction) refetchMlPrediction();
    } catch (err) {
      console.error('Prediction query failed:', err);
      setErrorMsg(err.message || 'Failed to query prediction server');
    } finally {
      setIsLoading(false);
    }
  };

  const probabilityPct = prediction ? Math.round(prediction.injury_probability * 100) : null;
  const riskLabel = prediction?.injury_risk_label || 'LOW';

  const riskBadgeConfig = {
    LOW: { cls: 'badge-low', icon: CheckCircle, color: '#10B981', msg: 'Training is safe. Metrics are within normal threshold.' },
    MEDIUM: { cls: 'badge-medium', icon: AlertTriangle, color: '#D97706', msg: 'Moderate fatigue detected. Monitor intensity carefully.' },
    HIGH: { cls: 'badge-high', icon: AlertTriangle, color: '#EF4444', msg: 'High risk of injury! Reduce workload or prioritize recovery.' },
  };

  const currentRiskCfg = riskBadgeConfig[riskLabel] || riskBadgeConfig.LOW;
  const RiskIcon = currentRiskCfg.icon;

  return (
    <section className="predictor-section card card-glow animate-fade-in">
      <div className="predictor-header">
        <div className="predictor-title-wrap">
          <div className="predictor-icon-badge">
            <Cpu size={22} color="var(--cyan)" />
          </div>
          <div>
            <h2 className="predictor-title">Interactive ML Injury Risk Predictor</h2>
            <p className="predictor-subtitle">
              Log custom athlete biometrics & training load to query the trained Machine Learning Model in real-time.
            </p>
          </div>
        </div>
        <div className="predictor-badge-tag">
          <Sparkles size={12} color="#00D4FF" />
          <span>XGBoost Model v1.0</span>
        </div>
      </div>

      <div className="predictor-body">
        {/* Left Column: Form */}
        <form className="predictor-form" onSubmit={handlePredict}>
          <div className="form-presets">
            <span className="preset-label"><Sliders size={13} /> Quick Presets:</span>
            <button type="button" className="preset-btn" onClick={() => handlePreset('optimal')}>
              Optimal Recovery
            </button>
            <button type="button" className="preset-btn" onClick={() => handlePreset('spike')}>
              Workload Spike
            </button>
            <button type="button" className="preset-btn" onClick={() => handlePreset('recovery')}>
              Injury Return
            </button>
          </div>

          <div className="form-grid">
            {/* Identity & Sport */}
            <div className="form-group">
              <label><User size={13} /> Athlete ID</label>
              <input
                type="text"
                value={form.athlete_id}
                onChange={e => setForm({ ...form, athlete_id: e.target.value })}
                placeholder="ATH-101"
                required
              />
            </div>

            <div className="form-group">
              <label>Sport</label>
              <select value={form.sport} onChange={handleSportChange}>
                {Object.keys(SPORT_POSITIONS_MAP).map(sp => (
                  <option key={sp} value={sp}>{sp}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Playing Position</label>
              <select
                value={form.position}
                onChange={e => setForm({ ...form, position: e.target.value })}
              >
                {(SPORT_POSITIONS_MAP[form.sport] || ['Athlete']).map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </select>
            </div>

            {/* Demographics */}
            <div className="form-group">
              <label>Age (years)</label>
              <input
                type="number"
                min="15" max="50" step="1"
                value={form.age}
                onChange={e => setForm({ ...form, age: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Weight (kg)</label>
              <input
                type="number"
                min="40" max="150" step="0.5"
                value={form.weight_kg}
                onChange={e => setForm({ ...form, weight_kg: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Height (cm)</label>
              <input
                type="number"
                min="140" max="220" step="0.5"
                value={form.height_cm}
                onChange={e => setForm({ ...form, height_cm: e.target.value })}
              />
            </div>

            {/* Workload */}
            <div className="form-group">
              <label><Activity size={13} /> Weekly Volume (hrs)</label>
              <input
                type="number"
                min="0" max="40" step="0.5"
                value={form.weekly_volume_hrs}
                onChange={e => setForm({ ...form, weekly_volume_hrs: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label><Zap size={13} /> Weekly Intensity (0-10)</label>
              <input
                type="number"
                min="0" max="10" step="0.1"
                value={form.weekly_intensity_score}
                onChange={e => setForm({ ...form, weekly_intensity_score: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Rest Days (past week)</label>
              <input
                type="number"
                min="0" max="7" step="1"
                value={form.rest_days}
                onChange={e => setForm({ ...form, rest_days: e.target.value })}
              />
            </div>

            {/* Physiology */}
            <div className="form-group">
              <label><Moon size={13} /> Sleep (hrs/night)</label>
              <input
                type="number"
                min="0" max="12" step="0.5"
                value={form.sleep_hours}
                onChange={e => setForm({ ...form, sleep_hours: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label><Heart size={13} /> HRV (ms)</label>
              <input
                type="number"
                min="0" max="200" step="1"
                value={form.hrv_ms}
                onChange={e => setForm({ ...form, hrv_ms: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Soreness Score (0-10)</label>
              <input
                type="number"
                min="0" max="10" step="0.5"
                value={form.soreness_score}
                onChange={e => setForm({ ...form, soreness_score: e.target.value })}
              />
            </div>

            {/* History */}
            <div className="form-group">
              <label>Prior Injuries Count</label>
              <input
                type="number"
                min="0" max="20" step="1"
                value={form.prior_injuries}
                onChange={e => setForm({ ...form, prior_injuries: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Days Since Last Injury</label>
              <input
                type="number"
                min="0" max="10000" step="1"
                value={form.days_since_last_injury}
                onChange={e => setForm({ ...form, days_since_last_injury: e.target.value })}
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-predict" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 size={16} className="spin-icon" /> Querying ML Model...
                </>
              ) : (
                <>
                  <Cpu size={16} /> Predict Injury Risk <ArrowRight size={15} />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Right Column: Live Output Card */}
        <div className="predictor-output-card">
          {errorMsg && (
            <div className="predictor-error">
              <AlertTriangle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {!prediction && !isLoading && !errorMsg && (
            <div className="predictor-placeholder">
              <Cpu size={40} color="var(--text-muted)" style={{ opacity: 0.4 }} />
              <h4>Ready for Live Prediction</h4>
              <p>Adjust the biometric & training load values on the left and click <b>Predict Injury Risk</b> to execute the model.</p>
            </div>
          )}

          {isLoading && (
            <div className="predictor-loading">
              <Loader2 size={40} className="spin-icon" color="var(--cyan)" />
              <p>Analyzing feature interactions across XGBoost time-series pipeline...</p>
            </div>
          )}

          {prediction && !isLoading && (
            <div className="prediction-result-panel animate-fade-in">
              <div className="result-header">
                <span className="result-athlete-id">{prediction.athlete_id}</span>
                <span className={`badge ${currentRiskCfg.cls}`}>
                  <RiskIcon size={12} /> {riskLabel} RISK
                </span>
              </div>

              {/* Gauge Meter */}
              <div className="gauge-wrap">
                <svg width="150" height="150" viewBox="0 0 150 150">
                  <circle cx="75" cy="75" r="58" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="12" />
                  <circle
                    cx="75" cy="75" r="58" fill="none"
                    stroke={currentRiskCfg.color}
                    strokeWidth="12"
                    strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 58}
                    strokeDashoffset={(2 * Math.PI * 58) - (probabilityPct / 100) * (2 * Math.PI * 58)}
                    transform="rotate(-90 75 75)"
                    style={{ transition: 'stroke-dashoffset 1s ease', filter: `drop-shadow(0 0 10px ${currentRiskCfg.color}88)` }}
                  />
                  <text x="75" y="68" textAnchor="middle" fill={currentRiskCfg.color} fontSize="28" fontWeight="800" fontFamily="Inter">
                    {probabilityPct}%
                  </text>
                  <text x="75" y="88" textAnchor="middle" fill="var(--text-secondary)" fontSize="10" fontWeight="600" fontFamily="Inter">
                    INJURY PROBABILITY
                  </text>
                </svg>
              </div>

              <p className="result-msg">{currentRiskCfg.msg}</p>

              {/* Factors */}
              {prediction.top_contributing_factors?.length > 0 && (
                <div className="factors-card">
                  <span className="factors-title">Top Contributing Risk Factors:</span>
                  <ul className="factors-list">
                    {prediction.top_contributing_factors.map((factor, idx) => (
                      <li key={idx}>
                        <span className="factor-bullet">•</span> {factor}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Compliance & Audit Footer */}
              <div className="audit-footer">
                <ShieldCheck size={14} color="#39FF14" />
                <span>HIPAA / GDPR Encrypted Audit Logged</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Full-width Unified Performance Recovery & Prescription Engine */}
      {prediction && !isLoading && (
        <>
          <div className="recovery-recommendation-banner">
            {riskLabel === 'HIGH' ? (
              <div className="rec-alert high">
                🛑 <strong>Full Rest Recommended</strong> — Elevated ML injury risk ({probabilityPct}%). Skip high-intensity drills today and focus on active recovery.
              </div>
            ) : riskLabel === 'MEDIUM' ? (
              <div className="rec-alert medium">
                ⚠️ <strong>Light Training Only</strong> — Moderate ML injury risk ({probabilityPct}%). Limit session RPE to low intensity and focus on mobility.
              </div>
            ) : (
              <div className="rec-alert low">
                ✅ <strong>Ready to Train</strong> — Low ML injury risk ({probabilityPct}%). Body shows good readiness for planned session.
              </div>
            )}
          </div>
          <AIRecoveryFull record={lastSubmittedRecord || form} prediction={prediction} />
        </>
      )}
    </section>
  );
}
