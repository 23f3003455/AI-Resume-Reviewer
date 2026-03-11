import React from 'react';
import { Target } from 'lucide-react';

export default function JDMatch({ jdMatch }) {
  if (!jdMatch || jdMatch.match_pct === null) return null;

  const matched = jdMatch.matched_keywords || [];
  const missing = jdMatch.missing_keywords || [];

  return (
    <div className="card animate-fade-up stagger-4">
      <div className="section-title">
        <Target size={15} />
        Job Match Analysis
      </div>
      <div className="match-rec">{jdMatch.recommendation}</div>
      <div className="match-cols">
        <div>
          <div className="match-col-title">Matched Keywords ({matched.length})</div>
          <div className="tag-cloud">
            {matched.map((k, i) => (
              <span key={i} className="tag matched">{k}</span>
            ))}
            {matched.length === 0 && (
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>None</span>
            )}
          </div>
        </div>
        <div>
          <div className="match-col-title">Missing Keywords ({missing.length})</div>
          <div className="tag-cloud">
            {missing.map((k, i) => (
              <span key={i} className="tag missing">{k}</span>
            ))}
            {missing.length === 0 && (
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>None — great match!</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
