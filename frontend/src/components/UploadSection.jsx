import React, { useRef, useState, useCallback } from 'react';
import { Upload, FileText, Briefcase, Loader2 } from 'lucide-react';

export default function UploadSection({ onAnalyze, loading }) {
  const fileRef = useRef(null);
  const [file, setFile] = useState(null);
  const [jd, setJd] = useState('');
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback((f) => {
    const ext = f.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx'].includes(ext)) {
      alert('Please upload a PDF or DOCX file.');
      return;
    }
    setFile(f);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  return (
    <>
      <div className="upload-grid">
        <div className="card animate-fade-up stagger-1">
          <div className="card-label">
            <Upload size={14} /> Upload Resume
          </div>
          <div
            className={`drop-zone${dragOver ? ' drag-over' : ''}${file ? ' has-file' : ''}`}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files.length && handleFile(e.target.files[0])}
            />
            <div className="drop-zone-icon">
              {file ? <FileText size={40} /> : '📄'}
            </div>
            <div className="drop-zone-text">
              {file
                ? <>Selected: <strong>{file.name}</strong></>
                : <>Drop your <strong>PDF</strong> or <strong>DOCX</strong> here, or click to browse</>
              }
            </div>
            {file && (
              <div className="drop-zone-file">
                {(file.size / 1024).toFixed(1)} KB
              </div>
            )}
          </div>
        </div>

        <div className="card animate-fade-up stagger-2">
          <div className="card-label">
            <Briefcase size={14} /> Job Description (Optional)
          </div>
          <textarea
            className="jd-textarea"
            placeholder="Paste the target job description here to see how well your resume matches the role..."
            value={jd}
            onChange={(e) => setJd(e.target.value)}
          />
        </div>
      </div>

      <div className="action-row animate-fade-up stagger-3">
        <button
          className="btn-analyze"
          disabled={!file || loading}
          onClick={() => onAnalyze(file, jd)}
        >
          {loading ? (
            <>
              <div className="btn-spinner" />
              Analyzing...
            </>
          ) : (
            <>
              <FileText size={18} />
              Analyze Resume
            </>
          )}
        </button>
      </div>
    </>
  );
}
