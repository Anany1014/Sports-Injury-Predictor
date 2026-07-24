// src/pages/WearableSync.jsx
import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { Bluetooth, RefreshCw, CheckCircle, Clock, Watch, ChevronDown, Activity, Heart, Moon, Zap } from 'lucide-react';
import './WearableSync.css';

const WATCH_DEVICES = [
  {
    id: 'COROS',
    name: 'COROS Training Hub',
    brand: 'COROS',
    logo: '⚡',
    desc: 'PACE 2/3, APEX 2/Pro, VERTIX 1/2/2S Series',
    metrics: ['HRV Index', 'Resting HR', 'Sleep Performance', 'Running Fitness', 'Training Load', 'SpO₂'],
    color: '#FF6B00',
    popular: true,
  },
  {
    id: 'Garmin',
    name: 'Garmin Connect',
    brand: 'Garmin',
    logo: '🟢',
    desc: 'Forerunner, Fenix, Epix, Venu & Instinct series',
    metrics: ['HRV Status', 'Resting HR', 'Body Battery', 'Sleep Score', 'SpO₂', 'Stress Score'],
    color: '#00A8FF',
    popular: true,
  },
  {
    id: 'Apple Watch',
    name: 'Apple Health (Apple Watch)',
    brand: 'Apple',
    logo: '🍎',
    desc: 'Apple Watch Ultra, Series 4+, SE Series',
    metrics: ['HRV (SDNN)', 'Resting HR', 'Sleep Stages', 'VO2 Max', 'Wrist Temp'],
    color: '#FF2D55',
    popular: true,
  },
  {
    id: 'Samsung Watch',
    name: 'Samsung Health',
    brand: 'Samsung',
    logo: '🔵',
    desc: 'Galaxy Watch 4 / 5 / 6 / Ultra',
    metrics: ['HRV', 'Resting HR', 'Sleep Score', 'Body Composition (BIA)', 'SpO₂'],
    color: '#1428A0',
    popular: false,
  },
  {
    id: 'WHOOP',
    name: 'WHOOP Strap',
    brand: 'WHOOP',
    logo: '⬛',
    desc: 'WHOOP 4.0 Performance Strap',
    metrics: ['Recovery %', 'Day Strain', 'Sleep Performance', 'HRV', 'RHR'],
    color: '#00FF66',
    popular: false,
  },
  {
    id: 'Oura',
    name: 'Oura Ring',
    brand: 'Oura',
    logo: '💍',
    desc: 'Oura Ring Gen 3 / Horizon',
    metrics: ['Readiness Score', 'HRV Balance', 'Sleep Quality', 'Skin Temp'],
    color: '#D4AF37',
    popular: false,
  }
];

export default function WearableSync() {
  const { wearableSync, syncWearable } = useAthlete();
  const [selectedDeviceId, setSelectedDeviceId] = useState(wearableSync.device || 'COROS');
  const [syncing, setSyncing] = useState(false);
  const [justSynced, setJustSynced] = useState(false);

  const selectedDevice = WATCH_DEVICES.find(d => d.id === selectedDeviceId) || WATCH_DEVICES[0];
  const isConnected = wearableSync.device === selectedDevice.id;

  const handleSync = async () => {
    setSyncing(true);
    await new Promise(r => setTimeout(r, 1400));
    syncWearable(selectedDevice.id);
    setSyncing(false);
    setJustSynced(true);
    setTimeout(() => setJustSynced(false), 3000);
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
          <h1 className="page-title">Watch & Wearable Sync</h1>
          <p className="page-subtitle">Select your smartwatch or wearable device to automatically import HRV, Resting HR, and Sleep metrics</p>
        </div>
      </div>

      {wearableSync.lastSync && (
        <div className="sync-banner animate-fade-in">
          <CheckCircle size={16} color="var(--green)" />
          <span>Active Device Synced: <strong>{wearableSync.device}</strong> at {formatTime(wearableSync.lastSync)}</span>
          <div className="sync-banner-pills">
            <span className="pill"><Activity size={10} style={{ marginRight: 4 }} /> HRV: {wearableSync.hrv} ms</span>
            <span className="pill"><Heart size={10} style={{ marginRight: 4 }} /> RHR: {wearableSync.rhr} bpm</span>
            <span className="pill"><Moon size={10} style={{ marginRight: 4 }} /> Sleep: {wearableSync.sleepHours}h</span>
          </div>
        </div>
      )}

      {/* Dropdown Menu & Watch Selector */}
      <div className="card card-glow watch-selector-card" style={{ marginBottom: 24 }}>
        <div className="watch-selector-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Watch size={22} color="var(--cyan)" />
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Select Your Watch / Device</h3>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)' }}>Choose from COROS, Garmin, Apple Watch, Samsung, WHOOP, or Oura</p>
            </div>
          </div>

          <span className={`badge ${isConnected ? 'badge-low' : 'badge-cyan'}`}>
            {isConnected ? '✓ Currently Connected' : 'Available for Pairing'}
          </span>
        </div>

        {/* Dropdown Menu */}
        <div className="dropdown-container" style={{ margin: '20px 0' }}>
          <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <span>Choose Watch Brand / System:</span>
          </label>
          <div style={{ position: 'relative' }}>
            <select
              className="watch-dropdown-select form-input"
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              style={{
                width: '100%',
                padding: '14px 18px',
                fontSize: '1.02rem',
                fontWeight: 700,
                appearance: 'none',
                background: 'var(--bg-card-alt)',
                border: '2px solid var(--cyan-dim)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
                cursor: 'pointer'
              }}
            >
              {WATCH_DEVICES.map(device => (
                <option key={device.id} value={device.id}>
                  {device.logo} {device.name} — ({device.desc})
                </option>
              ))}
            </select>
            <ChevronDown size={18} color="var(--cyan)" style={{ position: 'absolute', right: 16, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
          </div>
        </div>

        {/* Selected Watch Details View */}
        <div className="selected-device-detail-card" style={{ background: 'var(--bg-card-alt)', borderRadius: 'var(--radius-md)', padding: 22, border: `1px solid ${selectedDevice.color}44` }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{ fontSize: '2.5rem', background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 12, border: '1px solid var(--border)' }}>
                {selectedDevice.logo}
              </div>
              <div>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  {selectedDevice.name}
                  {selectedDevice.id === 'COROS' && <span className="badge badge-orange" style={{ fontSize: '0.68rem' }}>🔥 COROS Hub Supported</span>}
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 2 }}>{selectedDevice.desc}</div>
              </div>
            </div>

            <button
              className={`btn ${isConnected ? 'btn-secondary' : 'btn-primary'}`}
              style={{ minWidth: 180, padding: '12px 24px', fontSize: '0.95rem' }}
              onClick={handleSync}
              disabled={syncing}
            >
              {syncing ? (
                <><RefreshCw size={16} className="spin-icon" /> Syncing {selectedDevice.brand}...</>
              ) : justSynced ? (
                <><CheckCircle size={16} /> Connected & Synced!</>
              ) : (
                <><Bluetooth size={16} /> {isConnected ? 'Re-Sync Device' : `Connect & Sync ${selectedDevice.brand}`}</>
              )}
            </button>
          </div>

          <div style={{ marginTop: 20 }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>
              Supported Telemetry Metrics
            </div>
            <div className="device-metrics">
              {selectedDevice.metrics.map(m => (
                <span key={m} className="metric-pill" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-primary)', fontSize: '0.78rem', padding: '4px 12px' }}>
                  ✓ {m}
                </span>
              ))}
            </div>
          </div>

          {isConnected && wearableSync.lastSync && (
            <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px dashed var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <Clock size={14} />
                <span>Last Synced Telemetry: {formatTime(wearableSync.lastSync)}</span>
              </div>
              <div style={{ display: 'flex', gap: 20 }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--cyan)' }}>{wearableSync.hrv} ms</div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>HRV</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--red)' }}>{wearableSync.rhr} bpm</div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>RHR</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#7C3AED' }}>{wearableSync.sleepHours}h</div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Sleep</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Grid of all compatible watches for quick selection */}
      <h3 style={{ marginBottom: 14, fontSize: '1.1rem' }}>All Supported Watch Ecosystems</h3>
      <div className="devices-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
        {WATCH_DEVICES.map(device => {
          const isSelected = selectedDeviceId === device.id;
          const isConn = wearableSync.device === device.id;
          return (
            <div
              key={device.id}
              className={`device-card card ${isSelected ? 'card-glow' : ''}`}
              style={{ cursor: 'pointer', border: isSelected ? `2px solid ${device.color}` : '1px solid var(--border)' }}
              onClick={() => setSelectedDeviceId(device.id)}
            >
              <div className="device-header">
                <div className="device-logo">{device.logo}</div>
                <div style={{ flex: 1 }}>
                  <div className="device-name" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {device.name}
                    {device.id === 'COROS' && <span className="badge badge-orange" style={{ fontSize: '0.6rem' }}>NEW</span>}
                  </div>
                  <div className="device-desc">{device.desc}</div>
                </div>
                {isConn && <span className="badge badge-low"><CheckCircle size={10} /> Active</span>}
              </div>

              <div className="device-metrics">
                {device.metrics.slice(0, 3).map(m => (
                  <span key={m} className="metric-pill">{m}</span>
                ))}
                {device.metrics.length > 3 && (
                  <span className="metric-pill">+{device.metrics.length - 3} more</span>
                )}
              </div>

              <button
                className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'} sync-btn`}
                style={{ marginTop: 8 }}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedDeviceId(device.id);
                  handleSync();
                }}
              >
                {isSelected ? 'Selected in Menu' : `Select ${device.brand}`}
              </button>
            </div>
          );
        })}
      </div>

      <div className="card" style={{ marginTop: 24, padding: 24 }}>
        <h3 style={{ marginBottom: 16 }}>How Watch & Wearable Sync Works</h3>
        <div className="sync-steps">
          {[
            { icon: '⌚', step: '1', title: 'Select Your Watch', desc: 'Choose COROS, Garmin, Apple Watch, Samsung, or WHOOP from the dropdown menu.' },
            { icon: '📡', step: '2', title: 'Telemetry Import', desc: 'HRV Index, resting heart rate, and sleep duration are imported automatically.' },
            { icon: '🧠', step: '3', title: 'Readiness Score', desc: 'Your Daily Readiness Score is updated in real time from your watch data.' },
            { icon: '💡', step: '4', title: 'Injury Predictor', desc: 'The ML model incorporates fresh watch telemetry into injury risk forecasting.' },
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
