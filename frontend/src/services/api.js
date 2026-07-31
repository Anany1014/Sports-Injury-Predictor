// src/services/api.js

/**
 * Ensures athlete_id matches backend schema validation: r"^ATH-[a-zA-Z0-9_-]+$"
 */
export function formatAthleteId(rawId) {
  if (!rawId) return 'ATH-101';
  const str = String(rawId).trim();
  if (/^ATH-[a-zA-Z0-9_-]+$/.test(str)) {
    return str;
  }
  const sanitized = str.replace(/[^a-zA-Z0-9_-]/g, '');
  return `ATH-${sanitized || '101'}`;
}

/**
 * Format raw frontend profile/log/workout into a valid AthleteRecord payload.
 */
export function buildAthleteRecordPayload(profile = {}, todayLog = {}, workouts = []) {
  const todayStr = new Date().toISOString().split('T')[0];

  // Calculate past week volume & intensity from workouts
  const now = new Date();
  const last7 = new Date(now);
  last7.setDate(last7.getDate() - 7);

  const past7Workouts = workouts.filter(w => new Date(w.date) >= last7);
  const totalVolumeHrs = past7Workouts.reduce((sum, w) => sum + (w.duration || 0), 0) / 60.0;
  const avgIntensity = past7Workouts.length > 0
    ? past7Workouts.reduce((sum, w) => sum + (w.rpe || 5), 0) / past7Workouts.length
    : 7.0;

  return {
    athlete_id: formatAthleteId(profile.athlete_id || 'ATH-101'),
    date: todayLog?.date || todayStr,
    sport: String(profile.sport || 'Football').trim(),
    position: String(profile.position || 'Midfielder').trim(),
    age: Math.min(50, Math.max(15, Number(profile.age) || 24)),
    weight_kg: Math.min(150, Math.max(40, Number(profile.weight) || 75.5)),
    height_cm: Math.min(220, Math.max(140, Number(profile.height) || 178.0)),
    weekly_volume_hrs: Math.min(40, Math.max(0, +(totalVolumeHrs || 14.5).toFixed(1))),
    weekly_intensity_score: Math.min(10, Math.max(0, +(avgIntensity || 7.5).toFixed(1))),
    sleep_hours: Math.min(12, Math.max(0, Number(todayLog?.sleepHours) || 7.5)),
    hrv_ms: Math.min(200, Math.max(0, Number(todayLog?.hrv) || 58.0)),
    soreness_score: Math.min(10, Math.max(0, Number(todayLog?.sorenessScore) || 4.0)),
    rest_days: Math.min(7, Math.max(0, Number(profile.rest_days ?? 1))),
    prior_injuries: Math.min(20, Math.max(0, Number(profile.prior_injuries) || 2)),
    days_since_last_injury: Math.min(10000, Math.max(0, Number(profile.days_since_last_injury) || 90.0)),
  };
}

/**
 * Call the backend ML model prediction endpoint (/predict or /api/v1/predict)
 */
export async function predictInjuryRisk(recordPayload) {
  const endpoints = ['/predict', 'http://127.0.0.1:8000/predict', 'http://localhost:8000/predict'];
  let lastError = null;

  for (const url of endpoints) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(recordPayload),
      });

      if (res.ok) {
        return await res.json();
      }

      let detailMsg = `HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) {
          detailMsg = typeof errJson.detail === 'string'
            ? errJson.detail
            : JSON.stringify(errJson.detail);
        }
      } catch (_) {
        detailMsg = await res.text();
      }
      lastError = new Error(`API ${res.status}: ${detailMsg}`);
    } catch (err) {
      lastError = err;
    }
  }

  console.error('Failed to query ML prediction model across endpoints:', lastError);
  throw lastError || new Error('Failed to fetch prediction from ML server');
}

/**
 * Call the OpenRouter LLM AI Recovery Prescription endpoint
 */
export async function fetchAIRecoveryPlan(recordPayload, predictionResult) {
  const endpoints = ['/api/v1/recommendations', 'http://127.0.0.1:8000/api/v1/recommendations', 'http://localhost:8000/api/v1/recommendations'];
  let lastError = null;

  for (const url of endpoints) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          record: recordPayload,
          prediction: predictionResult,
        }),
      });

      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error('Failed to generate AI recovery plan');
}
