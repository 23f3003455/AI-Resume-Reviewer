import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function GrammarPanel({ issues }) {
  if (!issues) return null;

  return (
    <div className="card full animate-fade-up stagger-5">
      <div className="section-title">
        <AlertTriangle size={15} />
        Grammar &amp; Style Issues
        <span className="section-count">{issues.length}</span>
      </div>
      {issues.length === 0 ? (
        <p style={{ fontSize: '0.85rem', color: 'var(--green)', fontWeight: 500 }}>
          No issues found — nice work!
        </p>
      ) : (
        issues.map((g, i) => (
          <div key={i} className="issue-item">
            <div className="issue-msg">{g.message}</div>
            <div className="issue-ctx">{g.context}</div>
            {g.suggestions && g.suggestions.length > 0 && (
              <div className="issue-sug">
                Suggestion: {g.suggestions.join(', ')}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}
