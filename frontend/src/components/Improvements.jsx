import React, { useState } from 'react';
import { Wand2, Copy, Check } from 'lucide-react';

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button className={`copy-btn${copied ? ' copied' : ''}`} onClick={handleCopy}>
      {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
    </button>
  );
}

export default function Improvements({ items }) {
  if (!items || items.length === 0) return null;

  const hasImprovements = items.some(it => it.improved && it.improved.length > 0);
  if (!hasImprovements) return null;

  return (
    <div className="card full animate-fade-up stagger-4">
      <div className="section-title">
        <Wand2 size={15} />
        Copy-Paste Ready Improvements
        <span className="section-count">
          {items.filter(it => it.improved?.length > 0).length}
        </span>
      </div>
      {items.map((item, i) => {
        if (!item.improved || item.improved.length === 0) return null;
        return (
          <div key={i} className="improve-item">
            <div className="improve-label orig-label">Original</div>
            <div className="improve-original">{item.original}</div>
            {item.improved.map((sug, j) => (
              <div key={j}>
                <div className="improve-label new-label">
                  {j === 0 ? 'Recommended' : `Alternative ${j}`}
                </div>
                <div className="improve-suggestion">
                  <div className="improve-text">{sug}</div>
                  <CopyButton text={sug} />
                </div>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
