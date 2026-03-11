import React, { useState } from 'react';
import { Bot, Copy, Check, ShieldAlert } from 'lucide-react';

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button className={`copy-btn${copied ? ' copied' : ''}`} onClick={handleCopy}>
      {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
    </button>
  );
}

function meterColor(score) {
  if (score <= 25) return 'var(--green)';
  if (score <= 50) return 'var(--amber)';
  return 'var(--red)';
}

export default function AIDetection({ data }) {
  if (!data) return null;

  const flagged = data.flagged_sentences || [];
  const details = data.details || [];
  const color = meterColor(data.ai_score);

  return (
    <div className="card full animate-fade-up stagger-6">
      <div className="section-title">
        <Bot size={15} />
        AI Content Detection
        <span className="section-count">{data.confidence} confidence</span>
      </div>

      {/* Score meter */}
      <div className="ai-meter">
        <ShieldAlert size={18} style={{ color, flexShrink: 0 }} />
        <div className="ai-meter-bar">
          <div
            className="ai-meter-fill"
            style={{ width: `${data.ai_score}%`, background: color }}
          />
        </div>
        <div className="ai-meter-label" style={{ color }}>
          {data.ai_score}%
        </div>
      </div>

      {/* Explanation */}
      {data.ai_score <= 25 && (
        <p style={{ fontSize: '0.85rem', color: 'var(--green)', fontWeight: 500, marginBottom: '0.75rem' }}>
          Your resume appears to be mostly human-written. Great job!
        </p>
      )}
      {data.ai_score > 25 && data.ai_score <= 50 && (
        <p style={{ fontSize: '0.85rem', color: 'var(--amber)', fontWeight: 500, marginBottom: '0.75rem' }}>
          Some AI-like patterns detected. Consider personalizing the flagged sections.
        </p>
      )}
      {data.ai_score > 50 && (
        <p style={{ fontSize: '0.85rem', color: 'var(--red)', fontWeight: 500, marginBottom: '0.75rem' }}>
          High AI-content probability. Many recruiters use AI detectors — humanize your resume.
        </p>
      )}

      {/* Detail signals */}
      {details.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          {details.map((d, i) => (
            <div key={i} className="ai-detail">
              <div className="ai-detail-dot" />
              <span>{d}</span>
            </div>
          ))}
        </div>
      )}

      {/* Flagged sentences with humanized rewrites */}
      {flagged.length > 0 && (
        <>
          <div style={{
            fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.1em', color: 'var(--text-muted)',
            marginBottom: '0.6rem', marginTop: '0.5rem',
          }}>
            Flagged Sentences — with Humanized Rewrites
          </div>
          {flagged.map((f, i) => (
            <div key={i} className="ai-flagged">
              <div className="ai-flagged-sent">
                <span style={{
                  fontSize: '0.6rem', fontWeight: 700, color: 'var(--purple)',
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                }}>
                  AI-like ({f.score}%):{' '}
                </span>
                {f.sentence}
              </div>
              {f.humanized && f.humanized !== f.sentence && (
                <div>
                  <div className="ai-flagged-human-label">Humanized version:</div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                    <div className="ai-flagged-human">{f.humanized}</div>
                    <CopyBtn text={f.humanized} />
                  </div>
                </div>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
