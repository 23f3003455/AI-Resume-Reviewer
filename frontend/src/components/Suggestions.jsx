import React from 'react';
import { Lightbulb } from 'lucide-react';

export default function Suggestions({ items }) {
  if (!items || items.length === 0) return null;

  return (
    <div className="card animate-fade-up stagger-2">
      <div className="section-title">
        <Lightbulb size={15} />
        Improvement Suggestions
        <span className="section-count">{items.length}</span>
      </div>
      <ul className="sug-list">
        {items.map((s, i) => (
          <li key={i} className="sug-item">
            <span className="sug-arrow">→</span>
            <span>{s}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
