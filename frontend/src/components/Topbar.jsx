import React from 'react';
import { useTheme } from '../hooks/useTheme';
import { Sun, Moon } from 'lucide-react';

export default function Topbar() {
  const { theme, toggle } = useTheme();

  return (
    <nav className="topbar">
      <div className="topbar-logo">R</div>
      <span className="topbar-title">Resume Reviewer</span>
      <span className="topbar-badge">AI-Powered</span>
      <div className="topbar-right">
        <button className="theme-toggle" onClick={toggle} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </nav>
  );
}
