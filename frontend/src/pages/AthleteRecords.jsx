// src/pages/AthleteRecords.jsx
import { useState } from 'react';
import { useAthlete } from '../context/AthleteContext';
import { Plus, Download, Upload, CheckCircle, AlertTriangle, FileText, Search, RefreshCw } from 'lucide-react';
import './AthleteRecords.css';

const SCHEMA_FIELDS = [
  { key: 'athlete_id', name: 'Athlete ID', type: 'string', req: true, range: 'Any string', example: 'ATH-101', desc: 'Unique identifier' },
  { key: 'date', name: 'Assessment Date', type: 'date', req: true, range: 'YYYY-MM-DD', example: '2026-07-24', desc: 'ISO-8601 date string' },
  { key: 'sport', name: 'Sport', type: 'string', req: true, range: 'Text', example: 'Football', desc: 'Athlete\'s primary sport' },
  { key: 'position', name: 'Playing Position', type: 'string', req: true, range: 'Text', example: 'Midfielder', desc: 'Athlete\'s playing position' },
  { key: 'age', name: 'Age (years)', type: 'number', min: 15, max: 50, req: true, range: '15 to 50 years', example: 24, desc: 'Athlete\'s age' },
  { key: 'weight_kg', name: 'Weight (kg)', type: 'number', min: 40.0, max: 150.0, step: 0.1, req: true, range: '40.0 to 150.0 kg', example: 75.5, desc: 'Body weight in kilograms' },
  { key: 'height_cm', name: 'Height (cm)', type: 'number', min: 140.0, max: 220.0, step: 0.1, req: true, range: '140.0 to 220.0 cm', example: 178.0, desc: 'Height in centimeters' },
  { key: 'weekly_volume_hrs', name: 'Weekly Volume (hrs)', type: 'number', min: 0.0, max: 40.0, step: 0.5, req: true, range: '0.0 to 40.0 hrs', example: 14.5, desc: 'Total training hours logged this week' },
  { key: 'weekly_intensity_score', name: 'Weekly Intensity (0-10)', type: 'number', min: 0.0, max: 10.0, step: 0.1, req: true, range: '0.0 to 10.0', example: 8.2, desc: 'Average session intensity rating' },
  { key: 'sleep_hours', name: 'Sleep (hours)', type: 'number', min: 0.0, max: 12.0, step: 0.5, req: true, range: '0.0 to 12.0 hrs', example: 7.5, desc: 'Average nightly sleep duration' },
  { key: 'hrv_ms', name: 'HRV (ms)', type: 'number', min: 0.0, max: 200.0, step: 1, req: true, range: '0.0 to 200.0 ms', example: 58.0, desc: 'Heart Rate Variability' },
  { key: 'soreness_score', name: 'Soreness Score (0-10)', type: 'number', min: 0.0, max: 10.0, step: 0.1, req: true, range: '0.0 to 10.0', example: 4.5, desc: 'Self-reported muscle soreness' },
  { key: 'rest_days', name: 'Rest Days (past week)', type: 'number', min: 0, max: 7, req: true, range: '0 to 7 days', example: 1, desc: 'Complete rest days in past week' },
  { key: 'prior_injuries', name: 'Prior Injuries', type: 'number', min: 0, req: true, range: '0 or greater', example: 2, desc: 'Total previous career injuries' },
  { key: 'days_since_last_injury', name: 'Days Since Last Injury', type: 'number', min: 0, step: 1, req: true, range: '0.0 or greater', example: 90.0, desc: 'Days elapsed since returning from injury' }
];

export default function AthleteRecords() {
  const { athleteRecords, addAthleteRecord, profile } = useAthlete();
  const today = new Date().toISOString().split('T')[0];

  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [errors, setErrors] = useState({});
  const [savedSuccess, setSavedSuccess] = useState(false);

  const defaultForm = {
    athlete_id: profile.athlete_id || 'ATH-101',
    date: today,
    sport: profile.sport || 'Football',
    position: profile.position || 'Midfielder',
    age: profile.age || 24,
    weight_kg: profile.weight || 75.5,
    height_cm: profile.height || 178.0,
    weekly_volume_hrs: 14.5,
    weekly_intensity_score: 8.2,
    sleep_hours: 7.5,
    hrv_ms: 58.0,
    soreness_score: 4.5,
    rest_days: 1,
    prior_injuries: profile.prior_injuries || 2,
    days_since_last_injury: profile.days_since_last_injury || 90.0,
  };

  const [form, setForm] = useState(defaultForm);

  const validateField = (field, val) => {
    if (val === '' || val === null || val === undefined) return 'Field is required';
    if (field.min !== undefined && Number(val) < field.min) return `Must be >= ${field.min}`;
    if (field.max !== undefined && Number(val) > field.max) return `Must be <= ${field.max}`;
    return null;
  };

  const handleSave = () => {
    const errs = {};
    SCHEMA_FIELDS.forEach(f => {
      const err = validateField(f, form[f.key]);
      if (err) errs[f.key] = err;
    });

    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setErrors({});
    const formattedRecord = {
      athlete_id: String(form.athlete_id).trim(),
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

    addAthleteRecord(formattedRecord);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      setShowModal(false);
    }, 1200);
  };

  const exportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(athleteRecords, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `athlete_records_${today}.json`);
    dlAnchorElem.click();
  };

  const handleImportJSON = (e) => {
    const fileReader = new FileReader();
    if (e.target.files[0]) {
      fileReader.readAsText(e.target.files[0], "UTF-8");
      fileReader.onload = (event) => {
        try {
          const parsed = JSON.parse(event.target.result);
          const list = Array.isArray(parsed) ? parsed : [parsed];
          list.forEach(r => addAthleteRecord(r));
          alert(`Successfully imported ${list.length} AthleteRecord entry(s)!`);
        } catch (err) {
          alert('Invalid JSON file format.');
        }
      };
    }
  };

  const filteredRecords = athleteRecords.filter(r =>
    r.athlete_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.sport.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (r.position && r.position.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Assessment Records (AthleteRecord)</h1>
          <p className="page-subtitle">Full Field Schema Specification Manager & Assessment History</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" onClick={exportJSON}>
            <Download size={14} /> Export JSON
          </button>
          <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
            <Upload size={14} /> Import JSON
            <input type="file" accept=".json" onChange={handleImportJSON} style={{ display: 'none' }} />
          </label>
          <button className="btn btn-primary" onClick={() => { setForm(defaultForm); setShowModal(true); }}>
            <Plus size={15} /> New Record
          </button>
        </div>
      </div>

      {/* Schema quick specs banner */}
      <div className="card schema-spec-banner" style={{ marginBottom: 20 }}>
        <div className="ssb-header">
          <FileText size={18} color="var(--cyan)" />
          <h3>PDF Schema Compliance Status (15 Fields)</h3>
          <span className="badge badge-low" style={{ marginLeft: 'auto' }}>
            <CheckCircle size={10} /> Validated Schema
          </span>
        </div>
        <div className="schema-pill-grid">
          {SCHEMA_FIELDS.map(f => (
            <div key={f.key} className="schema-pill">
              <span className="sp-name">{f.key}</span>
              <span className="sp-range">{f.range}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Search bar */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 12, top: 12 }} />
          <input
            className="form-input"
            style={{ paddingLeft: 38 }}
            placeholder="Search by Athlete ID, Sport, or Position..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Records Table */}
      <div className="card records-table-card">
        <div className="table-responsive">
          <table className="athlete-table">
            <thead>
              <tr>
                <th>Athlete ID</th>
                <th>Date</th>
                <th>Sport / Pos</th>
                <th>Age</th>
                <th>Weight / Height</th>
                <th>Wk Volume</th>
                <th>Wk Intensity</th>
                <th>Sleep</th>
                <th>HRV</th>
                <th>Soreness</th>
                <th>Rest Days</th>
                <th>Injuries / Days</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan="12" style={{ textAlign: 'center', padding: 30, color: 'var(--text-muted)' }}>
                    No matching AthleteRecord entries found.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((r, idx) => (
                  <tr key={`${r.athlete_id}-${r.date}-${idx}`}>
                    <td>
                      <span className="badge badge-cyan" style={{ fontWeight: 700 }}>{r.athlete_id}</span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{r.date}</td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{r.sport}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{r.position || '—'}</div>
                    </td>
                    <td>{r.age} yr</td>
                    <td>
                      <div style={{ fontSize: '0.82rem' }}>{r.weight_kg} kg</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{r.height_cm} cm</div>
                    </td>
                    <td>
                      <span style={{ color: 'var(--cyan)', fontWeight: 600 }}>{r.weekly_volume_hrs}h</span>
                    </td>
                    <td>
                      <span style={{ color: r.weekly_intensity_score > 8 ? 'var(--orange)' : 'var(--text-primary)', fontWeight: 600 }}>
                        {r.weekly_intensity_score} / 10
                      </span>
                    </td>
                    <td>{r.sleep_hours}h</td>
                    <td>
                      <span style={{ color: 'var(--green)', fontWeight: 600 }}>{r.hrv_ms} ms</span>
                    </td>
                    <td>
                      <span className={`badge ${r.soreness_score > 6 ? 'badge-high' : r.soreness_score > 3 ? 'badge-medium' : 'badge-low'}`}>
                        {r.soreness_score}
                      </span>
                    </td>
                    <td>{r.rest_days} d</td>
                    <td>
                      <div style={{ fontSize: '0.8rem' }}>{r.prior_injuries} prev</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{r.days_since_last_injury}d ago</div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Entry Modal */}
      {showModal && (
        <div className="modal-overlay animate-fade-in">
          <div className="modal-card card card-glow">
            <div className="modal-header">
              <h3>Log New AthleteRecord (Full Specification)</h3>
              <button className="btn btn-ghost" onClick={() => setShowModal(false)}>✕</button>
            </div>

            <div className="grid-2 modal-grid">
              {SCHEMA_FIELDS.map(f => (
                <div key={f.key} className="form-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label className="form-label">{f.name}</label>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{f.range}</span>
                  </div>
                  <input
                    type={f.type === 'date' ? 'date' : f.type === 'number' ? 'number' : 'text'}
                    step={f.step || 'any'}
                    min={f.min}
                    max={f.max}
                    className={`form-input ${errors[f.key] ? 'input-error' : ''}`}
                    placeholder={`e.g. ${f.example}`}
                    value={form[f.key] ?? ''}
                    onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                  />
                  {errors[f.key] && (
                    <span className="field-err-text">{errors[f.key]}</span>
                  )}
                </div>
              ))}
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave}>
                {savedSuccess ? <><CheckCircle size={15} /> Record Saved!</> : 'Save AthleteRecord'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
