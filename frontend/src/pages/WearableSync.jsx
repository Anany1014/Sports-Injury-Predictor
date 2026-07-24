// src/pages/WearableSync.jsx
import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { Bluetooth, RefreshCw, CheckCircle, Clock } from 'lucide-react';
import './WearableSync.css';

const DEVICES = [
  { id: 'Garmin', name: 'Garmin Connect', logo: '🟢', desc: 'Forerunner / Fenix / Venu series', metrics: ['HRV', 'Resting HR', 'Sleep', 'SpO₂', 'Stress'] },
  { id: 'Apple Watch', name: 'Apple Health', logo: '🍎', desc: 'Apple Watch Series 4+', metrics: ['HRV', 'Resting HR', 'Sleep', 'ECG'] },
  { id: 'Samsung Watch', name: 'Samsung Health', logo: '🔵', desc: 'Galaxy Watch 4+', metrics: ['HRV', 'Resting HR', 'Sleep', 'BIA'] },
];

export default function WearableSync() {
  const { wearableSync, syncWearable } = useAthlete();
  const [syncing, setSyncing] = useState(null);
  const [justSynced, setJustSynced] = useState(null);

  const handleSync = async (deviceId) => {
    setSyncing(deviceId);
    await new Promise(r => setTimeout(r, 1500));
    syncWearable(deviceId);
    setSyncing(null);
    setJustSynced(deviceId);
    setTimeout(() => setJustSynced(null), 3000);
  };

  const formatTime = (iso) => {
    if (!iso) return 'Never';
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', ' + d.toLocaleDateString();
  };

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Wearable Sync</h1>
          <p className="page-subtitle">Connect your device to automatically import HRV, resting heart rate, and sleep data</p>
        </div>
      </div>

      {wearableSync.lastSync && (
        <div className="sync-banner animate-fade-in">
          <CheckCircle size={16} color="var(--green)" />
          <span>Last sync: <strong>{wearableSync.device}</strong> at {formatTime(wearableSync.lastSync)}</span>
          <div className="sync-banner-pills">
            <span className="pill">HRV: {wearableSync.hrv} ms</span>
            <span className="pill">RHR: {wearableSync.rhr} bpm</span>
            <span className="pill">Sleep: {wearableSync.sleepHours}h</span>
          </div>
        </div>
      )}

      <div className="devices-grid">
        {DEVICES.map(device => {
          const isConnected = wearableSync.device === device.id;
          const isSyncing = syncing === device.id;
          const isJustSynced = justSynced === device.id;
          return (
            <div key={device.id} className={`device-card card ${isConnected ? 'card-glow' : ''}`}>
              <div className="device-header">
                <div className="device-logo">{device.logo}</div>
                <div style={{ flex: 1 }}>
                  <div className="device-name">{device.name}</div>
                  <div className="device-desc">{device.desc}</div>
                </div>
                {isConnected && <span className="badge badge-low"><CheckCircle size={10}/> Active</span>}
              </div>

              <div className="device-metrics">
                {device.metrics.map(m => (
                  <span key={m} className="metric-pill">{m}</span>
                ))}
              </div>

              {isConnected && wearableSync.lastSync && (
                <div className="device-last-sync">
                  <Clock size={12}/>
                  <span>Last synced: {formatTime(wearableSync.lastSync)}</span>
                </div>
              )}

              <div className="device-data-row">
                {isConnected && wearableSync.hrv && (
                  <>
                    <div className="device-data-item">
                      <div className="ddi-val" style={{color:'var(--cyan)'}}>{wearableSync.hrv}</div>
                      <div className="ddi-label">HRV (ms)</div>
                    </div>
                    <div className="device-data-item">
                      <div className="ddi-val" style={{color:'var(--red)'}}>{wearableSync.rhr}</div>
                      <div className="ddi-label">RHR (bpm)</div>
                    </div>
                    <div className="device-data-item">
                      <div className="ddi-val" style={{color:'#7C3AED'}}>{wearableSync.sleepHours}h</div>
                      <div className="ddi-label">Sleep</div>
                    </div>
                  </>
                )}
              </div>

              <button
                className={`btn ${isConnected ? 'btn-secondary' : 'btn-primary'} sync-btn`}
                onClick={() => handleSync(device.id)}
                disabled={isSyncing}
              >
                {isSyncing ? (
                  <><RefreshCw size={14} className="spin-icon" /> Syncing...</>
                ) : isJustSynced ? (
                  <><CheckCircle size={14} /> Synced!</>
                ) : (
                  <><Bluetooth size={14} /> {isConnected ? 'Re-Sync' : 'Connect & Sync'}</>
                )}
              </button>
            </div>
          );
        })}
      </div>

      <div className="card" style={{marginTop:20,padding:24}}>
        <h3 style={{marginBottom:16}}>How Wearable Sync Works</h3>
        <div className="sync-steps">
          {[
            { icon: '📱', step: '1', title: 'Connect Device', desc: 'Tap "Connect & Sync" on your wearable to link it with AthletIQ.' },
            { icon: '📡', step: '2', title: 'Data Import', desc: 'HRV, resting heart rate, and sleep metrics are automatically imported.' },
            { icon: '🧠', step: '3', title: 'Score Generation', desc: 'Your Daily Readiness Score is calculated instantly from the synced data.' },
            { icon: '💡', step: '4', title: 'Smart Insights', desc: 'Recovery recommendations and injury risk are updated based on fresh data.' },
          ].map(s => (
            <div key={s.step} className="sync-step">
              <div className="sync-step-num">{s.step}</div>
              <div className="sync-step-icon">{s.icon}</div>
              <div className="sync-step-title">{s.title}</div>
              <div className="sync-step-desc">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
