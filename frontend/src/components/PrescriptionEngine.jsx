// src/components/PrescriptionEngine.jsx
import React, { useState, useRef } from 'react';
import { Moon, Zap, Snowflake, Droplets, Brain, RefreshCw, ChevronRight, Sparkles } from 'lucide-react';
import './PrescriptionEngine.css';

const ENDPOINTS = [
  '/api/v1/recommendations/stream/prescription',
  'http://127.0.0.1:8000/api/v1/recommendations/stream/prescription',
  'http://localhost:8000/api/v1/recommendations/stream/prescription',
];

const CARD_META = {
  SLEEP: {
    key: 'SLEEP',
    label: 'Sleep Target',
    icon: Moon,
    color: '#818cf8',
    bg: 'rgba(99,102,241,0.08)',
    border: 'rgba(99,102,241,0.25)',
    unit: 'hrs',
    suffix: 'tonight',
  },
  WORKLOAD: {
    key: 'WORKLOAD',
    label: 'Workload Cap',
    icon: Zap,
    color: '#fb923c',
    bg: 'rgba(251,146,60,0.08)',
    border: 'rgba(251,146,60,0.25)',
    unit: '/10 RPE',
    suffix: 'max intensity',
  },
  THERAPY: {
    key: 'THERAPY',
    label: 'Therapy Protocol',
    icon: Snowflake,
    color: '#38bdf8',
    bg: 'rgba(56,189,248,0.08)',
    border: 'rgba(56,189,248,0.25)',
    unit: 'min',
    suffix: 'session',
  },
  NUTRITION: {
    key: 'NUTRITION',
    label: 'Nutrition & Hydration',
    icon: Droplets,
    color: '#4ade80',
    bg: 'rgba(74,222,128,0.08)',
    border: 'rgba(74,222,128,0.25)',
    unit: '',
    suffix: '',
  },
};

/**
 * Parse SSE streamed text into 4 prescription card objects.
 * Looks for labeled keys: SLEEP_HEADLINE, SLEEP_TARGET, SLEEP_DETAIL etc.
 */
function parsePrescription(text) {
  const cards = {};
  const keys = ['SLEEP', 'WORKLOAD', 'THERAPY', 'NUTRITION'];

  for (const key of keys) {
    const headline = extractField(text, `${key}_HEADLINE`);
    const target = extractField(text, `${key}_TARGET`);
    const detail = extractField(text, `${key}_DETAIL`);
    if (headline || target || detail) {
      cards[key] = { headline, target, detail };
    }
  }
  return cards;
}

function extractField(text, fieldName) {
  const regex = new RegExp(`${fieldName}:\\s*(.+?)(?=\\n[A-Z_]+:|$)`, 's');
  const match = text.match(regex);
  return match ? match[1].trim() : '';
}

function PrescriptionCard({ meta, data, streaming, isActive }) {
  const Icon = meta.icon;
  const target = data?.target || '';
  // Try to pull just the leading number for the big display
  const numMatch = target.match(/^[\d.]+/);
  const bigNum = numMatch ? numMatch[0] : null;

  return (
    <div
      className={`rx-card ${isActive ? 'rx-card-active' : ''} ${!data ? 'rx-card-empty' : ''}`}
      style={{ '--card-color': meta.color, '--card-bg': meta.bg, '--card-border': meta.border }}
    >
      <div className="rx-card-header">
        <div className="rx-card-icon" style={{ background: meta.bg, borderColor: meta.border }}>
          <Icon size={16} color={meta.color} />
        </div>
        <span className="rx-card-label">{meta.label}</span>
        {streaming && isActive && <span className="rx-live-dot" />}
      </div>

      {!data && (
        <div className="rx-card-waiting">
          <div className="rx-skeleton rx-skeleton-h" />
          <div className="rx-skeleton rx-skeleton-sm" />
        </div>
      )}

      {data && (
        <>
          {/* Big metric display */}
          {bigNum && (
            <div className="rx-metric-row">
              <span className="rx-big-num" style={{ color: meta.color }}>{bigNum}</span>
              <div className="rx-metric-labels">
                {meta.unit && <span className="rx-unit" style={{ color: meta.color }}>{meta.unit}</span>}
                {meta.suffix && <span className="rx-suffix">{meta.suffix}</span>}
              </div>
            </div>
          )}

          {/* Headline */}
          {data.headline && (
            <p className="rx-headline">
              <ChevronRight size={12} color={meta.color} style={{ flexShrink: 0, marginTop: 2 }} />
              {data.headline}
            </p>
          )}

          {/* Detail */}
          {data.detail && (
            <p className="rx-detail">{data.detail}{streaming && isActive && <span className="rx-cursor" />}</p>
          )}
        </>
      )}
    </div>
  );
}

function PrescriptionEngine({ record, prediction }) {
  const [loading, setLoading] = useState(false);
  const [rawText, setRawText] = useState('');
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);
  const abortRef = useRef(null);

  const handleGenerate = async () => {
    if (!record || !prediction) return;
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setDone(false);
    setError(null);
    setRawText('');

    const body = JSON.stringify({ record, prediction });

    for (const url of ENDPOINTS) {
      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
          credentials: 'include',
          body,
          signal: controller.signal,
        });
        if (!res.ok) continue;

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done: streamDone, value } = await reader.read();
          if (streamDone) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const raw = line.slice(6).trim();
              if (raw === '[DONE]') break;
              try {
                const parsed = JSON.parse(raw);
                if (parsed.content) setRawText(prev => prev + parsed.content);
              } catch (_) {}
            }
          }
        }

        setLoading(false);
        setDone(true);
        return;
      } catch (err) {
        if (err.name === 'AbortError') { setLoading(false); return; }
      }
    }
    setError('Could not reach AI service. Ensure backend is running on port 8000.');
    setLoading(false);
  };

  const cards = parsePrescription(rawText);
  const cardKeys = ['SLEEP', 'WORKLOAD', 'THERAPY', 'NUTRITION'];

  // Determine which card is currently streaming (last one with partial data)
  const activeCard = loading
    ? cardKeys.slice().reverse().find(k => cards[k]) || null
    : null;

  const riskColor =
    prediction?.injury_risk_label === 'HIGH' ? '#f87171' :
    prediction?.injury_risk_label === 'MEDIUM' ? '#fbbf24' : '#4ade80';

  return (
    <div className="rx-engine">
      {/* Header */}
      <div className="rx-header">
        <div className="rx-header-left">
          <div className="rx-header-icon">
            <Brain size={20} color="#a5b4fc" />
          </div>
          <div>
            <h3 className="rx-title">AI Recovery & Prescription Engine</h3>
            <p className="rx-subtitle">
              Personalised to your biometrics · Powered by{' '}
              <span className="rx-model-tag">Nvidia Nemotron</span>
            </p>
          </div>
        </div>

        <div className="rx-header-right">
          {prediction && (
            <div className="rx-risk-badge" style={{ color: riskColor, borderColor: riskColor + '44', background: riskColor + '12' }}>
              {prediction.injury_risk_label} RISK · {Math.round(prediction.injury_probability * 100)}%
            </div>
          )}
          <button
            className={`rx-btn ${loading ? 'rx-btn-loading' : ''}`}
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading
              ? <><RefreshCw size={13} className="rx-spin" /> Generating...</>
              : <><Sparkles size={13} /> {rawText ? 'Regenerate' : 'Generate Prescription'}</>
            }
          </button>
        </div>
      </div>

      {/* Error */}
      {error && <div className="rx-error">{error}</div>}

      {/* Idle state */}
      {!rawText && !loading && !error && (
        <div className="rx-idle">
          <div className="rx-idle-icons">
            {[Moon, Zap, Snowflake, Droplets].map((Icon, i) => (
              <div key={i} className="rx-idle-icon" style={{ animationDelay: `${i * 0.15}s` }}>
                <Icon size={18} color="#334155" />
              </div>
            ))}
          </div>
          <p>Click <strong>Generate Prescription</strong> to get a personalised 4-category recovery plan based on your ML risk score and live biometrics.</p>
        </div>
      )}

      {/* Loading skeleton before first data */}
      {loading && !rawText && (
        <div className="rx-cards-grid">
          {cardKeys.map(key => (
            <PrescriptionCard
              key={key}
              meta={CARD_META[key]}
              data={null}
              streaming={true}
              isActive={false}
            />
          ))}
        </div>
      )}

      {/* Cards grid — shown while streaming and after done */}
      {rawText && (
        <div className="rx-cards-grid">
          {cardKeys.map(key => (
            <PrescriptionCard
              key={key}
              meta={CARD_META[key]}
              data={cards[key] || null}
              streaming={loading}
              isActive={activeCard === key}
            />
          ))}
        </div>
      )}

      {done && rawText && (
        <p className="rx-footer">
          <Sparkles size={11} color="#6366f1" />
          Generated by nvidia/nemotron-nano-9b-v2 · For reference only — consult your medical team for clinical decisions.
        </p>
      )}
    </div>
  );
}

class PrescriptionErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(e, i) { console.error('PrescriptionEngine error:', e, i); }
  render() {
    if (this.state.hasError) return (
      <div className="rx-engine rx-error">AI Prescription Engine encountered an error. Please refresh the page.</div>
    );
    return this.props.children;
  }
}

export default function PrescriptionEngineWrapper(props) {
  return (
    <PrescriptionErrorBoundary>
      <PrescriptionEngine {...props} />
    </PrescriptionErrorBoundary>
  );
}
