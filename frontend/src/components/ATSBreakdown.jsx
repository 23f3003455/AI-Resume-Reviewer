import React from 'react';
import { BarChart3 } from 'lucide-react';

function barColor(pct) {
  if (pct >= 75) return 'var(--green)';
  if (pct >= 50) return 'var(--amber)';
  return 'var(--red)';
}

export default function ATSBreakdown({ breakdown }) {
  if (!breakdown) return null;

  return (
    <div className="card animate-fade-up stagger-1">
      <div className="section-title">
        <BarChart3 size={15} />
        Score Breakdown
      </div>
      <div>
        {Object.entries(breakdown).map(([key, val]) => {
          const pct = (val.score / val.max) * 100;
          return (
            <div key={key} className="breakdown-item">
              <span className="breakdown-label">{key.replace(/_/g, ' ')}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${pct}%`, background: barColor(pct) }}
                />
              </div>
              <span className="breakdown-value">{val.score}/{val.max}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
