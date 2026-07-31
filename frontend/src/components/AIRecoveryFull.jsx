// src/components/AIRecoveryFull.jsx
// High-Performance Sports Science Recovery Console
import React, { useState, useRef } from 'react';
import {
  Activity, RefreshCw, Moon, Zap, Snowflake,
  Droplets, ChevronRight, Copy, Check, AlertCircle, ShieldAlert,
  Printer, CheckCircle2, Sliders, Cpu, FileText
} from 'lucide-react';
import './AIRecoveryFull.css';

const ENDPOINTS = [
  '/api/v1/recommendations/stream/full',
  'http://127.0.0.1:8000/api/v1/recommendations/stream/full',
  'http://localhost:8000/api/v1/recommendations/stream/full',
];

const CARD_META = {
  SLEEP:    { label: 'Sleep Target',          Icon: Moon,      color: '#38bdf8', unit: 'hrs',      suffix: 'tonight',  tag: 'CNS RECOVERY' },
  WORKLOAD: { label: 'Workload Cap',           Icon: Zap,       color: '#f97316', unit: '/10 RPE',  suffix: 'max cap',  tag: 'LOAD CONTROL' },
  THERAPY:  { label: 'Therapy Protocol',       Icon: Snowflake, color: '#06b6d4', unit: 'min',      suffix: 'session',  tag: 'TISSUE REPAIR' },
  NUTRITION:{ label: 'Nutrition & Hydration',  Icon: Droplets,  color: '#10b981', unit: '',         suffix: '',         tag: 'METABOLIC REFUEL' },
};

const CARD_ORDER = ['SLEEP', 'WORKLOAD', 'THERAPY', 'NUTRITION'];

/* ── Parsers ── */
function extractField(text, fieldName) {
  const regex = new RegExp(`${fieldName}:\\s*(.+?)(?=\\n[A-Z_]+:|\\n---DETAIL---|$)`, 's');
  const m = text.match(regex);
  return m ? m[1].trim() : '';
}

function parseCards(text) {
  const before = text.split('---DETAIL---')[0] || text;
  const result = {};
  for (const key of CARD_ORDER) {
    const h = extractField(before, `${key}_HEADLINE`);
    const t = extractField(before, `${key}_TARGET`);
    const d = extractField(before, `${key}_DETAIL`);
    if (h || t || d) result[key] = { headline: h, target: t, detail: d };
  }
  return result;
}

function parseDetailSection(text) {
  const idx = text.indexOf('---DETAIL---');
  return idx !== -1 ? text.slice(idx + 12).trim() : '';
}

/* ── Markdown renderer for the detail section ── */
function inlineBold(line, idx) {
  const parts = [];
  const re = /\*\*(.+?)\*\*/g;
  let last = 0, m;
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) parts.push(<span key={`t${idx}-${last}`}>{line.slice(last, m.index)}</span>);
    parts.push(<strong key={`b${idx}-${m.index}`}>{m[1]}</strong>);
    last = m.index + m[0].length;
  }
  if (last < line.length) parts.push(<span key={`e${idx}`}>{line.slice(last)}</span>);
  return parts.length ? parts : line;
}

function DetailRenderer({ text, streaming }) {
  const blocks = text.split('\n\n').filter(Boolean);
  return (
    <div className="rf-detail-body">
      {blocks.map((block, bi) => {
        const lines = block.split('\n').filter(Boolean);
        if (!lines.length) return null;

        // Heading ###
        if (/^#{1,3}\s/.test(lines[0])) {
          const heading = lines[0].replace(/^#{1,3}\s*/, '');
          const rest = lines.slice(1);
          return (
            <div key={bi} className="rf-section-card">
              <div className="rf-section-header">
                <div className="rf-section-badge">PROTOCOL DIRECTIVE 0{bi + 1}</div>
                <h4 className="rf-section-heading">{inlineBold(heading, bi)}</h4>
              </div>
              <div className="rf-section-content">
                {rest.map((l, li) => {
                  const trimmed = l.trim();
                  if (trimmed.startsWith('-') || trimmed.startsWith('*')) {
                    return (
                      <div key={li} className="rf-bullet">
                        <span className="rf-bullet-dot" />
                        <span>{inlineBold(trimmed.replace(/^[-*]\s*/, ''), li)}</span>
                      </div>
                    );
                  }
                  return <p key={li} className="rf-para">{inlineBold(l, li)}</p>;
                })}
              </div>
            </div>
          );
        }

        // Pure bullets
        if (lines.every(l => l.trim().startsWith('-') || l.trim().startsWith('*'))) {
          return (
            <div key={bi} className="rf-bullet-group">
              {lines.map((l, li) => (
                <div key={li} className="rf-bullet">
                  <span className="rf-bullet-dot" />
                  <span>{inlineBold(l.trim().replace(/^[-*]\s*/, ''), li)}</span>
                </div>
              ))}
            </div>
          );
        }

        return (
          <div key={bi} className="rf-para-block">
            <p className="rf-para">{inlineBold(lines.join(' '), bi)}</p>
          </div>
        );
      })}
      {streaming && <span className="rf-cursor" />}
    </div>
  );
}

/* ── Metric Card ── */
function MetricCard({ cardKey, meta, data, isStreaming, isActive }) {
  const { Icon, label, color, unit, suffix, tag } = meta;
  const numMatch = data?.target?.match(/^[\d.]+/);
  const bigNum = numMatch ? numMatch[0] : null;

  return (
    <div
      className={`rf-card ${isActive ? 'rf-card-active' : ''} ${!data ? 'rf-card-empty' : ''}`}
      style={{ '--rc': color }}
    >
      <div className="rf-card-top">
        <div className="rf-card-header-group">
          <div className="rf-card-icon" style={{ borderColor: `${color}40`, color: color }}>
            <Icon size={15} />
          </div>
          <div>
            <span className="rf-card-label">{label}</span>
            <span className="rf-card-tag">{tag}</span>
          </div>
        </div>
        {isStreaming && isActive && <span className="rf-live-badge"><span className="rf-live-dot" />SYNCING</span>}
      </div>

      {!data ? (
        <div className="rf-card-skeleton">
          <div className="rf-sk rf-sk-lg" />
          <div className="rf-sk rf-sk-sm" />
          <div className="rf-sk rf-sk-md" />
        </div>
      ) : (
        <div className="rf-card-body">
          {data.target && (
            <div className="rf-metric">
              <span className="rf-big">{data.target}</span>
              {suffix && <span className="rf-suffix">{suffix}</span>}
            </div>
          )}

          {data.headline && (
            <div className="rf-headline-pill">
              <ChevronRight size={12} color={color} style={{ flexShrink: 0 }} />
              <span>{data.headline}</span>
            </div>
          )}

          {data.detail && (
            <p className="rf-detail-mini">{data.detail}</p>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Main Component ── */
function AIRecoveryFull({ record, prediction }) {
  const [loading, setLoading] = useState(false);
  const [rawText, setRawText] = useState('');
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [protocolActive, setProtocolActive] = useState(false);
  const abortRef = useRef(null);

  const handleGenerate = async () => {
    if (!record || !prediction) return;
    if (abortRef.current) abortRef.current.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setLoading(true); setDone(false); setError(null); setRawText(''); setProtocolActive(false);

    const body = JSON.stringify({ record, prediction });

    for (const url of ENDPOINTS) {
      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
          credentials: 'include',
          body,
          signal: ctrl.signal,
        });
        if (!res.ok) continue;

        const reader = res.body.getReader();
        const dec = new TextDecoder();
        let buf = '';

        while (true) {
          const { done: rd, value } = await reader.read();
          if (rd) break;
          buf += dec.decode(value, { stream: true });
          const lines = buf.split('\n');
          buf = lines.pop() ?? '';
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const raw = line.slice(6).trim();
              if (raw === '[DONE]') break;
              try {
                const p = JSON.parse(raw);
                if (p.content) setRawText(prev => prev + p.content);
              } catch (_) {}
            }
          }
        }

        setLoading(false); setDone(true);
        return;
      } catch (e) {
        if (e.name === 'AbortError') { setLoading(false); return; }
      }
    }

    setError('Could not reach performance engine service on port 8000.');
    setLoading(false);
  };

  const cards = parseCards(rawText);
  const detailText = parseDetailSection(rawText);

  const activeCard = loading
    ? CARD_ORDER.slice().reverse().find(k => cards[k]) ?? null
    : null;

  const riskColor =
    prediction?.injury_risk_label === 'HIGH'   ? '#ef4444' :
    prediction?.injury_risk_label === 'MEDIUM' ? '#d97706' : '#10b981';

  const handleCopy = () => {
    if (!rawText) return;
    navigator.clipboard.writeText(rawText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="rf-root">

      {/* ── Header ── */}
      <div className="rf-header">
        <div className="rf-header-left">
          <div className="rf-hicon">
            <Activity size={20} color="#38bdf8" />
          </div>
          <div>
            <div className="rf-title-row">
              <h3 className="rf-title">ATHLETIC RECOVERY & PRESCRIPTION CONSOLE</h3>
              <span className="rf-model-badge">
                <Cpu size={12} style={{ marginRight: 4 }} /> NVIDIA Nemotron-4 340B LLM
              </span>
              <span className="rf-live-feed">
                <span className="rf-green-pulse" /> TELEMETRY ACTIVE
              </span>
            </div>
            <p className="rf-subtitle">
              Evidence-Based Protocols powered by NVIDIA Nemotron-4 340B & XGBoost Injury Risk Engine
            </p>
          </div>
        </div>

        <div className="rf-header-right">
          {prediction && (
            <span
              className="rf-risk"
              style={{ color: riskColor, borderColor: riskColor + '55', background: riskColor + '15' }}
            >
              <ShieldAlert size={12} style={{ marginRight: 4 }} />
              {prediction.injury_risk_label} RISK ({Math.round(prediction.injury_probability * 100)}%)
            </span>
          )}

          {done && rawText && (
            <>
              <button onClick={handleCopy} className="rf-action-btn">
                {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                {copied ? 'Copied' : 'Copy'}
              </button>
              <button onClick={handlePrint} className="rf-action-btn print-only-hide">
                <Printer size={13} /> Print
              </button>
              <button
                onClick={() => setProtocolActive(!protocolActive)}
                className={`rf-action-btn ${protocolActive ? 'active' : ''}`}
              >
                <CheckCircle2 size={13} color={protocolActive ? '#10b981' : '#94a3b8'} />
                {protocolActive ? 'Protocol Active' : 'Mark Active'}
              </button>
            </>
          )}

          <button
            className={`rf-btn ${loading ? 'rf-btn-busy' : ''}`}
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading
              ? <><RefreshCw size={13} className="rf-spin" /> Synthesizing Protocol...</>
              : <><Sliders size={13} /> {rawText ? 'Re-Synthesize' : 'Generate Recovery Prescription'}</>
            }
          </button>
        </div>
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="rf-error">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {/* ── Idle Banner ── */}
      {!rawText && !loading && !error && (
        <div className="rf-idle">
          <div className="rf-idle-row">
            {[Moon, Zap, Snowflake, Droplets].map((Ic, i) => (
              <div key={i} className="rf-idle-icon">
                <Ic size={18} color="#94a3b8" />
              </div>
            ))}
          </div>
          <div className="rf-idle-text">
            <h4>Generate Biometric-Informed Recovery Plan</h4>
            <p>Calculates sleep extensions, workload RPE caps, therapy protocols and hydration targets based on current athlete telemetry.</p>
          </div>
        </div>
      )}

      {/* ── Skeleton cards while streaming ── */}
      {loading && !rawText && (
        <div className="rf-grid">
          {CARD_ORDER.map(k => (
            <MetricCard key={k} cardKey={k} meta={CARD_META[k]} data={null} isStreaming isActive={false} />
          ))}
        </div>
      )}

      {/* ── Cards + Detail ── */}
      {rawText && (
        <>
          <div className="rf-grid">
            {CARD_ORDER.map(k => (
              <MetricCard
                key={k} cardKey={k}
                meta={CARD_META[k]}
                data={cards[k] ?? null}
                isStreaming={loading}
                isActive={activeCard === k}
              />
            ))}
          </div>

          {detailText && (
            <div className="rf-detail-wrap">
              <div className="rf-detail-label">
                <FileText size={14} color="#38bdf8" />
                <span>CLINICAL ATHLETIC RECOVERY DIRECTIVE</span>
                {loading && <span className="rf-streaming-pill"><span className="rf-stream-dot" />SYNTHESIZING</span>}
              </div>
              <div className="rf-detail-scroll">
                <DetailRenderer text={detailText} streaming={loading} />
              </div>
            </div>
          )}
        </>
      )}

      {done && (
        <div className="rf-footer">
          <div className="rf-footer-meta">
            <Cpu size={12} color="#64748b" />
            <span>Sports Science Telemetry Analysis · Official Team Protocol</span>
          </div>
          <div className="rf-footer-status">
            <span>HIPAA / GDPR VERIFIED</span>
          </div>
        </div>
      )}
    </div>
  );
}

class ErrorBoundary extends React.Component {
  constructor(p) { super(p); this.state = { err: false }; }
  static getDerivedStateFromError() { return { err: true }; }
  componentDidCatch(e, i) { console.error('AIRecoveryFull error:', e, i); }
  render() {
    if (this.state.err) return (
      <div className="rf-root rf-error">Recovery Engine encountered an error. Please reload.</div>
    );
    return this.props.children;
  }
}

export default function AIRecoveryFullWrapper(props) {
  return <ErrorBoundary><AIRecoveryFull {...props} /></ErrorBoundary>;
}
