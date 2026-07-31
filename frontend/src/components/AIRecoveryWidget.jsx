import React, { useState, useRef } from 'react';
import { Bot, Sparkles, Copy, Check, Share2, AlertCircle, RefreshCw, Zap, Brain } from 'lucide-react';
import './AIRecoveryWidget.css';

const STREAM_ENDPOINTS = [
  '/api/v1/recommendations/stream',
  'http://127.0.0.1:8000/api/v1/recommendations/stream',
  'http://localhost:8000/api/v1/recommendations/stream',
];

function parseMarkdownLine(line, idx) {
  // Bold: **text**
  const parts = [];
  const regex = /\*\*(.+?)\*\*/g;
  let last = 0;
  let match;
  while ((match = regex.exec(line)) !== null) {
    if (match.index > last) parts.push(<span key={`t${idx}-${last}`}>{line.slice(last, match.index)}</span>);
    parts.push(<strong key={`b${idx}-${match.index}`}>{match[1]}</strong>);
    last = match.index + match[0].length;
  }
  if (last < line.length) parts.push(<span key={`t${idx}-end`}>{line.slice(last)}</span>);
  return parts.length > 0 ? parts : line;
}

function MarkdownRenderer({ text }) {
  const blocks = text.split('\n\n').filter(Boolean);
  return (
    <div className="ai-markdown-body">
      {blocks.map((block, bIdx) => {
        const lines = block.split('\n').filter(Boolean);
        // Section heading: ### or ## or #
        if (/^#{1,3}\s/.test(lines[0])) {
          const headingText = lines[0].replace(/^#{1,3}\s*/, '');
          const rest = lines.slice(1);
          return (
            <div key={bIdx} className="ai-section-block">
              <h4 className="ai-sec-heading">{parseMarkdownLine(headingText, bIdx)}</h4>
              {rest.length > 0 && (
                <ul className="ai-bullets">
                  {rest.map((l, lIdx) => {
                    const trimmed = l.trim();
                    if (trimmed.startsWith('-') || trimmed.startsWith('*')) {
                      return (
                        <li key={lIdx} className="ai-bullet-item">
                          <span className="ai-bullet-dot" />
                          {parseMarkdownLine(trimmed.replace(/^[-*]\s*/, ''), lIdx)}
                        </li>
                      );
                    }
                    return <p key={lIdx} className="ai-line-text">{parseMarkdownLine(l, lIdx)}</p>;
                  })}
                </ul>
              )}
            </div>
          );
        }
        // Pure bullet list
        if (lines.every(l => l.trim().startsWith('-') || l.trim().startsWith('*'))) {
          return (
            <ul key={bIdx} className="ai-bullets">
              {lines.map((l, lIdx) => (
                <li key={lIdx} className="ai-bullet-item">
                  <span className="ai-bullet-dot" />
                  {parseMarkdownLine(l.trim().replace(/^[-*]\s*/, ''), lIdx)}
                </li>
              ))}
            </ul>
          );
        }
        // Plain paragraph
        return (
          <p key={bIdx} className="ai-paragraph">
            {parseMarkdownLine(lines.join(' '), bIdx)}
          </p>
        );
      })}
    </div>
  );
}

function AIRecoveryWidget({ record, prediction }) {
  const [loading, setLoading] = useState(false);
  const [streamedText, setStreamedText] = useState('');
  const [planMeta, setPlanMeta] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const abortRef = useRef(null);

  const handleGenerate = async () => {
    if (!record || !prediction) return;
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    setStreamedText('');
    setPlanMeta(null);

    const body = JSON.stringify({ record, prediction });

    for (const url of STREAM_ENDPOINTS) {
      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
          credentials: 'include',
          body,
          signal: controller.signal,
        });

        if (!res.ok) continue;

        setPlanMeta({ model: 'nvidia/nemotron-nano-9b-v2:free', provider: 'OpenRouter' });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const raw = line.slice(6).trim();
              if (raw === '[DONE]') break;
              try {
                const parsed = JSON.parse(raw);
                if (parsed.content) {
                  setStreamedText(prev => prev + parsed.content);
                }
              } catch (_) { /* skip */ }
            }
          }
        }

        setLoading(false);
        return;
      } catch (err) {
        if (err.name === 'AbortError') { setLoading(false); return; }
        // try next endpoint
      }
    }

    // All endpoints failed — show error
    setError('Could not reach AI service. Please check backend is running.');
    setLoading(false);
  };

  const handleCopy = () => {
    if (!streamedText) return;
    navigator.clipboard.writeText(streamedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleShare = () => {
    if (!streamedText) return;
    const shareText = `AI Athletic Recovery Prescription (${record?.sport} – ${record?.position}):\n\n` + streamedText;
    if (navigator.share) {
      navigator.share({ title: 'AI Recovery Prescription', text: shareText }).catch(() => {});
    } else {
      navigator.clipboard.writeText(shareText);
    }
  };

  return (
    <div className="ai-recovery-container">
      {/* Header */}
      <div className="ai-recovery-header">
        <div className="ai-recovery-title">
          <div className="ai-badge-icon">
            <Brain size={20} color="#a5b4fc" />
          </div>
          <div>
            <h3 className="ai-header-text">AI Sports Science Recovery Prescription</h3>
            <p className="ai-header-sub">
              Powered by{' '}
              <span className="ai-model-tag">nvidia/nemotron-nano-9b-v2</span>
              {' '}via{' '}
              <span className="ai-model-tag">OpenRouter</span>
            </p>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          className={`ai-generate-btn ${loading ? 'ai-btn-loading' : ''}`}
        >
          {loading ? (
            <>
              <RefreshCw size={14} className="ai-spin-icon" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles size={14} />
              {streamedText ? 'Regenerate' : 'Generate AI Prescription'}
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="ai-error-box">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading && !streamedText && (
        <div className="ai-loading-state">
          <div className="ai-loading-brain">
            <Brain size={32} color="#818cf8" className="ai-pulse-icon" />
            <div className="ai-loading-dots">
              <span /><span /><span />
            </div>
          </div>
          <p className="ai-loading-label">Nemotron AI is analyzing your biometrics...</p>
          <p className="ai-loading-sub">Generating personalized recovery prescription</p>
        </div>
      )}

      {/* Streaming / final content */}
      {streamedText && (
        <div className="ai-response-content">
          {planMeta && (
            <div className="ai-meta-bar">
              <div className="ai-meta-left">
                <span className="ai-meta-badge">
                  <Zap size={11} />
                  {planMeta.model}
                </span>
                <span className="ai-meta-badge">{planMeta.provider}</span>
                {loading && <span className="ai-streaming-pill"><span className="ai-stream-dot" />Streaming</span>}
              </div>
              <div className="ai-actions-group">
                <button onClick={handleCopy} className="ai-action-btn">
                  {copied ? <Check size={13} color="#4ade80" /> : <Copy size={13} />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
                <button onClick={handleShare} className="ai-action-btn">
                  <Share2 size={13} color="#38bdf8" />
                  Share
                </button>
              </div>
            </div>
          )}

          <MarkdownRenderer text={streamedText} />

          {loading && (
            <span className="ai-cursor-blink" />
          )}
        </div>
      )}
    </div>
  );
}

class AIRecoveryErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error, info) { console.error('AIRecoveryWidget error:', error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="ai-recovery-container" style={{ borderColor: 'rgba(239,68,68,0.4)' }}>
          <div className="ai-error-box">
            <AlertCircle size={16} />
            <span>AI Recovery Widget encountered a display error. Please try regenerating.</span>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function AIRecoveryWidgetWrapper(props) {
  return (
    <AIRecoveryErrorBoundary>
      <AIRecoveryWidget {...props} />
    </AIRecoveryErrorBoundary>
  );
}
