const API_BASE = '/api';

export async function analyzeResume(file, jobDescription = '') {
  const form = new FormData();
  form.append('resume', file);
  form.append('job_description', jobDescription);

  const resp = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: form,
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Server error' }));
    throw new Error(err.error || `HTTP ${resp.status}`);
  }

  return resp.json();
}
