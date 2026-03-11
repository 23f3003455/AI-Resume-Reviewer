import React, { useState, useRef } from 'react';
import Topbar from './components/Topbar';
import UploadSection from './components/UploadSection';
import ScoreRing from './components/ScoreRing';
import ATSBreakdown from './components/ATSBreakdown';
import Suggestions from './components/Suggestions';
import KeywordsPanel from './components/KeywordsPanel';
import JDMatch from './components/JDMatch';
import GrammarPanel from './components/GrammarPanel';
import Improvements from './components/Improvements';
import AIDetection from './components/AIDetection';
import { analyzeResume } from './utils/api';
import './styles/components.css';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const resultsRef = useRef(null);

  const handleAnalyze = async (file, jd) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await analyzeResume(file, jd);
      if (result.error) {
        setError(result.error);
      } else {
        setData(result);
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    } catch (err) {
      setError(err.message || 'Analysis failed. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const hasJdMatch = data?.jd_match?.match_pct !== null && data?.jd_match?.match_pct !== undefined;

  return (
    <>
      <Topbar />
      <div className="container">
        <UploadSection onAnalyze={handleAnalyze} loading={loading} />

        {error && <div className="error-banner">{error}</div>}

        {data && (
          <div ref={resultsRef}>
            {/* Header */}
            <div className="results-header animate-fade-up">
              <h2>Analysis Results</h2>
              <div className="sub">
                {data.word_count} words · {data.char_count} characters
              </div>
            </div>

            {/* Score rings */}
            <div className="score-hero animate-fade-up">
              <ScoreRing
                value={data.ats?.total_score}
                label="ATS Score"
                sublabel={`Grade: ${data.ats?.grade || '—'}`}
              />
              {hasJdMatch && (
                <ScoreRing
                  value={data.jd_match.match_pct}
                  label="JD Match"
                  color="var(--cyan)"
                />
              )}
              {data.ai_detection && (
                <ScoreRing
                  value={data.ai_detection.ai_score}
                  label="AI Content"
                  sublabel={data.ai_detection.confidence}
                  color={
                    data.ai_detection.ai_score <= 25 ? 'var(--green)' :
                    data.ai_detection.ai_score <= 50 ? 'var(--amber)' : 'var(--red)'
                  }
                />
              )}
            </div>

            {/* Grid of result panels */}
            <div className="results-grid">
              <ATSBreakdown breakdown={data.ats?.breakdown} />
              <Suggestions items={data.ats?.suggestions} />
              <KeywordsPanel keywords={data.keywords} />
              {hasJdMatch && <JDMatch jdMatch={data.jd_match} />}
              <Improvements items={data.improvements} />
              <AIDetection data={data.ai_detection} />
              <GrammarPanel issues={data.grammar} />
            </div>
          </div>
        )}
      </div>
    </>
  );
}
