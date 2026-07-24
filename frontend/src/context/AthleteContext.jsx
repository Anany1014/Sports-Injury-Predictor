// src/context/AthleteContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import { calculateACWR, calculateInjuryRisk, calculateReadiness } from '../utils/calculations';

const AthleteContext = createContext(null);

const defaultProfile = {
  athlete_id: 'ATH-101',
  name: 'Alex Rivera',
  age: 24,
  gender: 'Male',
  sport: 'Football',
  position: 'Midfielder',
  height: 178.0,
  weight: 75.5,
  prior_injuries: 2,
  days_since_last_injury: 90.0,
  createdAt: new Date().toISOString(),
};

const generateSeedRecords = () => [
  {
    athlete_id: 'ATH-101',
    date: '2026-07-24',
    sport: 'Football',
    position: 'Midfielder',
    age: 24,
    weight_kg: 75.5,
    height_cm: 178.0,
    weekly_volume_hrs: 14.5,
    weekly_intensity_score: 8.2,
    sleep_hours: 7.5,
    hrv_ms: 58.0,
    soreness_score: 4.5,
    rest_days: 1,
    prior_injuries: 2,
    days_since_last_injury: 90.0,
  },
  {
    athlete_id: 'ATH-101',
    date: '2026-07-17',
    sport: 'Football',
    position: 'Midfielder',
    age: 24,
    weight_kg: 76.0,
    height_cm: 178.0,
    weekly_volume_hrs: 12.0,
    weekly_intensity_score: 7.5,
    sleep_hours: 8.0,
    hrv_ms: 62.0,
    soreness_score: 3.0,
    rest_days: 2,
    prior_injuries: 2,
    days_since_last_injury: 83.0,
  },
  {
    athlete_id: 'ATH-102',
    date: '2026-07-20',
    sport: 'Running',
    position: 'Marathoner',
    age: 28,
    weight_kg: 64.0,
    height_cm: 172.0,
    weekly_volume_hrs: 18.0,
    weekly_intensity_score: 8.8,
    sleep_hours: 8.2,
    hrv_ms: 74.0,
    soreness_score: 2.5,
    rest_days: 1,
    prior_injuries: 1,
    days_since_last_injury: 140.0,
  }
];

const generateSeedWorkouts = () => {
  const sports = ['Running', 'Football', 'Badminton', 'Basketball', 'Fitness Training'];
  const sessions = [];
  for (let i = 27; i >= 1; i--) {
    if (Math.random() > 0.35) {
      const d = new Date(); d.setDate(d.getDate() - i);
      const duration = Math.floor(Math.random() * 70) + 30;
      const rpe = Math.floor(Math.random() * 5) + 4;
      sessions.push({
        id: `seed-${i}`,
        date: d.toISOString().split('T')[0],
        sport: sports[Math.floor(Math.random() * sports.length)],
        duration, rpe, load: duration * rpe,
      });
    }
  }
  return sessions;
};

const generateSeedReadiness = () => {
  const logs = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const hrv = Math.floor(Math.random() * 30) + 45;
    const rhr = Math.floor(Math.random() * 15) + 52;
    const sleepHours = +(Math.random() * 3 + 5.5).toFixed(1);
    logs.push({
      date: d.toISOString().split('T')[0],
      hrv, rhr, sleepHours,
      sorenessScore: +(Math.random() * 4 + 2).toFixed(1),
      readinessScore: calculateReadiness(hrv, rhr, sleepHours),
    });
  }
  return logs;
};

export function AthleteProvider({ children }) {
  const [profile, setProfile] = useState(() => {
    const s = localStorage.getItem('athlete_profile');
    return s ? JSON.parse(s) : defaultProfile;
  });

  const [athleteRecords, setAthleteRecords] = useState(() => {
    const s = localStorage.getItem('athlete_records');
    if (s) return JSON.parse(s);
    const seeded = generateSeedRecords();
    localStorage.setItem('athlete_records', JSON.stringify(seeded));
    return seeded;
  });

  const [dailyLogs, setDailyLogs] = useState(() => {
    const s = localStorage.getItem('athlete_daily_logs');
    if (s) return JSON.parse(s);
    const seeded = generateSeedReadiness();
    localStorage.setItem('athlete_daily_logs', JSON.stringify(seeded));
    return seeded;
  });

  const [workouts, setWorkouts] = useState(() => {
    const s = localStorage.getItem('athlete_workouts');
    if (s) return JSON.parse(s);
    const seeded = generateSeedWorkouts();
    localStorage.setItem('athlete_workouts', JSON.stringify(seeded));
    return seeded;
  });

  const [bodyDiscomfort, setBodyDiscomfort] = useState(() => {
    const s = localStorage.getItem('athlete_discomfort');
    return s ? JSON.parse(s) : [];
  });

  const [wearableSync, setWearableSync] = useState(() => {
    const s = localStorage.getItem('athlete_wearable');
    return s ? JSON.parse(s) : { device: null, lastSync: null, hrv: null, rhr: null, sleepHours: null };
  });

  useEffect(() => { localStorage.setItem('athlete_profile', JSON.stringify(profile)); }, [profile]);
  useEffect(() => { localStorage.setItem('athlete_records', JSON.stringify(athleteRecords)); }, [athleteRecords]);
  useEffect(() => { localStorage.setItem('athlete_daily_logs', JSON.stringify(dailyLogs)); }, [dailyLogs]);
  useEffect(() => { localStorage.setItem('athlete_workouts', JSON.stringify(workouts)); }, [workouts]);
  useEffect(() => { localStorage.setItem('athlete_discomfort', JSON.stringify(bodyDiscomfort)); }, [bodyDiscomfort]);
  useEffect(() => { localStorage.setItem('athlete_wearable', JSON.stringify(wearableSync)); }, [wearableSync]);

  const today = new Date().toISOString().split('T')[0];
  const todayLog = dailyLogs.find(l => l.date === today) || null;
  const acwr = calculateACWR(workouts);
  const injuryRisk = calculateInjuryRisk(todayLog?.readinessScore, acwr.ratio);

  const addDailyLog = (log) => {
    const withScore = { ...log, readinessScore: calculateReadiness(log.hrv, log.rhr, log.sleepHours) };
    setDailyLogs(prev => {
      const filtered = prev.filter(l => l.date !== log.date);
      return [...filtered, withScore].sort((a, b) => a.date.localeCompare(b.date));
    });
  };

  const addAthleteRecord = (record) => {
    setAthleteRecords(prev => {
      const filtered = prev.filter(r => !(r.athlete_id === record.athlete_id && r.date === record.date));
      return [record, ...filtered];
    });
  };

  const addWorkout = (w) => {
    const session = { ...w, id: Date.now().toString(), load: w.duration * w.rpe };
    setWorkouts(prev => [session, ...prev]);
  };

  const addDiscomfort = (entry) => {
    setBodyDiscomfort(prev => {
      const filtered = prev.filter(e => e.date !== entry.date);
      return [...filtered, entry];
    });
  };

  const syncWearable = (device) => {
    const synced = {
      device,
      lastSync: new Date().toISOString(),
      hrv: Math.floor(Math.random() * 25) + 50,
      rhr: Math.floor(Math.random() * 12) + 54,
      sleepHours: +(Math.random() * 2.5 + 5.5).toFixed(1),
    };
    setWearableSync(synced);
    addDailyLog({ date: today, hrv: synced.hrv, rhr: synced.rhr, sleepHours: synced.sleepHours });
    return synced;
  };

  return (
    <AthleteContext.Provider value={{
      profile, setProfile,
      athleteRecords, addAthleteRecord,
      dailyLogs, addDailyLog, todayLog,
      workouts, addWorkout,
      bodyDiscomfort, addDiscomfort,
      wearableSync, syncWearable,
      acwr, injuryRisk,
    }}>
      {children}
    </AthleteContext.Provider>
  );
}

export const useAthlete = () => useContext(AthleteContext);
