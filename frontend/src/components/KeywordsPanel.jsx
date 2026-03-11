import React from 'react';
import { Tag } from 'lucide-react';

export default function KeywordsPanel({ keywords }) {
  if (!keywords) return null;
  const skills = keywords.skills_found || [];
  const kbert = keywords.keybert || [];
  const total = skills.length + kbert.length;

  return (
    <div className="card animate-fade-up stagger-3">
      <div className="section-title">
        <Tag size={15} />
        Skills &amp; Keywords
        <span className="section-count">{total}</span>
      </div>
      <div className="tag-cloud">
        {skills.map((s, i) => (
          <span key={`s-${i}`} className="tag skill">{s}</span>
        ))}
        {kbert.map((k, i) => (
          <span key={`k-${i}`} className="tag">
            {k.keyword}
            <span className="score">{k.score}</span>
          </span>
        ))}
        {total === 0 && (
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            No keywords found.
          </span>
        )}
      </div>
    </div>
  );
}
