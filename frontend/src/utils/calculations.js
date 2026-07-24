// src/utils/calculations.js

export function calculateReadiness(hrv, rhr, sleepHours) {
  if (!hrv || !rhr || !sleepHours) return null;
  // HRV: higher is better. 20–100ms typical range. Score 0–100.
  const hrvScore = Math.min(100, Math.max(0, ((hrv - 20) / 80) * 100));
  // RHR: lower is better. 40–100 bpm typical. Score 0–100.
  const rhrScore = Math.min(100, Math.max(0, ((100 - rhr) / 60) * 100));
  // Sleep: 7–9h is ideal. Score 0–100.
  const sleepScore = sleepHours >= 9 ? 100
    : sleepHours >= 7 ? 75 + ((sleepHours - 7) / 2) * 25
    : sleepHours >= 5 ? (sleepHours - 5) / 2 * 75
    : 0;
  return Math.round(hrvScore * 0.4 + rhrScore * 0.3 + sleepScore * 0.3);
}

export function calculateACWR(workouts) {
  if (!workouts || workouts.length === 0) {
    return { acute: 0, chronic: 0, ratio: 0, acuteLoad: 0, chronicLoad: 0 };
  }
  const now = new Date();
  const last7 = new Date(now); last7.setDate(last7.getDate() - 7);
  const last28 = new Date(now); last28.setDate(last28.getDate() - 28);

  const recent7 = workouts.filter(w => new Date(w.date) >= last7);
  const recent28 = workouts.filter(w => new Date(w.date) >= last28);

  const acuteLoad = recent7.reduce((s, w) => s + (w.load || 0), 0);
  // Chronic = avg weekly load over 4 weeks
  const chronicLoad = recent28.reduce((s, w) => s + (w.load || 0), 0) / 4;
  const ratio = chronicLoad > 0 ? +(acuteLoad / chronicLoad).toFixed(2) : 0;

  return { acuteLoad, chronicLoad: +chronicLoad.toFixed(0), ratio };
}

export function calculateInjuryRisk(readinessScore, acwrRatio) {
  if (readinessScore === null || readinessScore === undefined) {
    if (acwrRatio > 1.5) return 'High';
    if (acwrRatio > 1.3) return 'Medium';
    return 'Low';
  }
  if (readinessScore < 45 || acwrRatio > 1.6) return 'High';
  if (readinessScore < 65 || acwrRatio > 1.3 || acwrRatio < 0.7) return 'Medium';
  return 'Low';
}

export function getACWRZone(ratio) {
  if (ratio < 0.8) return { label: 'Undertraining', color: '#94A3B8', hint: 'Increase training load gradually' };
  if (ratio <= 1.3) return { label: 'Optimal Zone', color: '#39FF14', hint: 'Maintain current training load' };
  if (ratio <= 1.5) return { label: 'Caution', color: '#FFD700', hint: 'Reduce load or increase recovery' };
  return { label: 'Danger Zone', color: '#FF4444', hint: 'High injury risk — rest immediately' };
}

export function getReadinessLabel(score) {
  if (score === null || score === undefined) return { label: 'No Data', color: '#94A3B8' };
  if (score >= 80) return { label: 'Peak Ready', color: '#39FF14' };
  if (score >= 65) return { label: 'Good', color: '#00D4FF' };
  if (score >= 45) return { label: 'Moderate', color: '#FFD700' };
  return { label: 'Low', color: '#FF4444' };
}

export function getRecoveryTips(readinessScore, acwrRatio, injuryRisk) {
  const tips = [];
  if (!readinessScore || readinessScore < 65) {
    tips.push({ icon: '💤', title: 'Prioritize Sleep', desc: 'Aim for 8–9 hours tonight. Avoid screens 1 hour before bed.' });
  }
  if (acwrRatio > 1.3) {
    tips.push({ icon: '📉', title: 'Reduce Training Load', desc: 'Your acute load is elevated. Consider an easy session or rest day.' });
  }
  if (acwrRatio < 0.8 && acwrRatio > 0) {
    tips.push({ icon: '📈', title: 'Gradual Load Increase', desc: 'Safely increase training volume by 10% this week.' });
  }
  if (injuryRisk === 'High') {
    tips.push({ icon: '🧊', title: 'Ice & Compression', desc: 'Apply cold therapy to areas of discomfort for 15–20 minutes.' });
    tips.push({ icon: '🛌', title: 'Complete Rest Recommended', desc: 'Your body needs full recovery. Skip today\'s session.' });
  }
  tips.push({ icon: '💧', title: 'Hydration', desc: 'Drink at least 2.5–3L of water today. Add electrolytes post-workout.' });
  tips.push({ icon: '🧘', title: 'Mobility Work', desc: '10–15 min of stretching or yoga improves recovery and reduces soreness.' });
  tips.push({ icon: '🥗', title: 'Nutrition Timing', desc: 'Consume protein within 45 minutes of your session for optimal recovery.' });
  return tips;
}

export function getLast28DaysACWRData(workouts) {
  const data = [];
  for (let i = 27; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    const label = `${d.getMonth() + 1}/${d.getDate()}`;

    const slice28 = workouts.filter(w => {
      const wd = new Date(w.date);
      const start28 = new Date(d); start28.setDate(start28.getDate() - 27);
      return wd >= start28 && wd <= d;
    });
    const slice7 = workouts.filter(w => {
      const wd = new Date(w.date);
      const start7 = new Date(d); start7.setDate(start7.getDate() - 6);
      return wd >= start7 && wd <= d;
    });

    const acute = slice7.reduce((s, w) => s + (w.load || 0), 0);
    const chronic = slice28.reduce((s, w) => s + (w.load || 0), 0) / 4;
    const ratio = chronic > 0 ? +(acute / chronic).toFixed(2) : 0;

    data.push({ date: dateStr, label, acute: Math.round(acute), chronic: Math.round(chronic), ratio });
  }
  return data;
}
