import React, { useEffect, useRef } from 'react';

function scoreColor(pct) {
  if (pct >= 75) return 'var(--green)';
  if (pct >= 50) return 'var(--amber)';
  return 'var(--red)';
}

export default function ScoreRing({ value, label, sublabel, color, className = '' }) {
  const fgRef = useRef(null);
  const circ = 2 * Math.PI * 66; // r=66

  useEffect(() => {
    const el = fgRef.current;
    if (el) {
      // Start fully hidden, then animate
      el.style.strokeDashoffset = circ;
      requestAnimationFrame(() => {
        el.style.strokeDashoffset = circ - (circ * (value || 0) / 100);
      });
    }
  }, [value, circ]);

  const stroke = color || scoreColor(value);

  return (
    <div className={`score-ring-wrap ${className}`}>
      <div className="score-ring">
        <svg viewBox="0 0 160 160">
          <circle className="bg" cx="80" cy="80" r="66" />
          <circle
            ref={fgRef}
            className="fg"
            cx="80" cy="80" r="66"
            stroke={stroke}
            strokeDasharray={circ}
            strokeDashoffset={circ}
          />
        </svg>
        <div className="inner">
          <div className="number" style={{ color: stroke }}>{value ?? '—'}</div>
          {sublabel && <div className="grade-label">{sublabel}</div>}
        </div>
      </div>
      <div className="ring-title">{label}</div>
    </div>
  );
}
