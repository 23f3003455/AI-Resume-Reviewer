# AI Resume Reviewer

An AI-powered web application that analyzes resumes and provides actionable feedback to help job seekers improve their chances of getting hired. Upload a PDF or DOCX resume, optionally paste a job description, and get instant analysis covering ATS compatibility, grammar, keywords, AI content detection, and copy-paste ready improvements.

Built with **React** (frontend) and **FastAPI** (backend). Deployable for free on Render or Railway.

---

## What It Does

**Upload your resume** and the app will:

- Score it from 0 to 100 on ATS (Applicant Tracking System) compatibility
- Find grammar mistakes and weak phrasing with suggested fixes
- Extract skills and keywords from your resume
- Detect if your resume sounds AI-generated and provide humanized rewrites
- Give you rewritten sentences you can copy-paste directly into your resume
- Compare your resume against a job description and show which keywords you're missing

---

## Features

### ATS Compatibility Score (0–100)

Your resume is scored across five dimensions:

- **Sections (30 pts)** — checks for Contact, Experience, Education, Skills, Summary, Projects, Certifications
- **Keywords (25 pts)** — matches against a bank of 100+ industry skills and technologies
- **Readability (20 pts)** — Flesch-Kincaid grade level analysis (ideal: grade 8–12)
- **Formatting (15 pts)** — word count, bullet points, quantified achievements
- **Action Verbs (10 pts)** — presence of strong verbs like led, built, optimized, scaled

Each dimension shows a progress bar and score. You also get a letter grade (A+ through F) and specific suggestions on what to fix.

### Grammar and Style Check

Detects spelling errors, repeated words, passive voice overuse, and weak action verbs (like "helped" or "was responsible for"). Each issue shows the context, the problem, and a suggestion.

Uses LanguageTool when available locally, with a built-in regex-based fallback for deployed environments.

### Keyword Extraction

Pulls keywords using three methods:

- **KeyBERT** — ML-based keyphrase extraction (local only)
- **spaCy NER** — named entity recognition for organizations, locations, technologies (local only)
- **Skill Bank** — matches against 100+ curated skills (Python, AWS, Docker, Agile, etc.) — works everywhere

### Job Description Matching

Paste any job description and the app will:

- Calculate a semantic similarity percentage between your resume and the JD
- Show which keywords from the JD appear in your resume (matched)
- Show which keywords are missing from your resume
- Give a recommendation (Excellent / Good / Moderate / Low match)

Uses SentenceTransformers locally, Jaccard similarity as fallback.

### Copy-Paste Ready Improvements

The app finds weak sentences in your resume (those using phrases like "responsible for", "helped with", "was involved in") and generates rewritten versions. Each improved sentence has a **Copy** button so you can paste it directly into your resume.

Uses a T5 paraphrase model locally, rule-based rewriting as fallback.

### AI Content Detection

Analyzes your resume for signs of AI-generated text using statistical heuristics:

- AI-typical phrase density (buzzwords like "leveraging", "synergy", "cutting-edge")
- Vocabulary diversity (type-token ratio)
- Sentence length uniformity
- Sentence start repetition patterns
- Passive voice density
- Absence of personal voice markers

Shows an overall AI score (0–100%), flags specific sentences that sound AI-generated, and provides a **humanized rewrite** for each flagged sentence with a copy button.

### Dark / Light Mode

Toggle between dark and light themes using the button in the top bar. Automatically detects your system preference on first visit.

---

## Tech Stack

**Frontend:** React 18, Vite, Lucide React icons, CSS custom properties (no CSS framework)

**Backend:** Python, FastAPI, PyMuPDF, python-docx, Gunicorn

**ML Models (local only):** LanguageTool, spaCy, KeyBERT, SentenceTransformers (all-MiniLM-L6-v2), HuggingFace T5 (Vamsi/T5_Paraphrase_Paws)

**Fonts:** Outfit, Playfair Display, JetBrains Mono

---

## Project Structure

```
resume-reviewer/
├── backend/
│   ├── app.py                # All backend logic (single file)
│   └── requirements.txt      # Full dependencies (local dev with ML models)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx          # Entry point
│       ├── App.jsx           # Root component
│       ├── hooks/
│       │   └── useTheme.jsx  # Dark/light mode hook
│       ├── utils/
│       │   └── api.js        # API calls
│       ├── styles/
│       │   ├── globals.css   # Theme variables, reset, animations
│       │   └── components.css # All component styles
│       └── components/
│           ├── Topbar.jsx        # Navigation bar with theme toggle
│           ├── UploadSection.jsx # File upload and JD textarea
│           ├── ScoreRing.jsx     # Animated circular score display
│           ├── ATSBreakdown.jsx  # Score breakdown with progress bars
│           ├── Suggestions.jsx   # Improvement suggestions list
│           ├── KeywordsPanel.jsx # Skills and keyword tags
│           ├── JDMatch.jsx       # Job description match results
│           ├── GrammarPanel.jsx  # Grammar and style issues
│           ├── Improvements.jsx  # Copy-paste ready rewrites
│           └── AIDetection.jsx   # AI content detection results
├── requirements.txt    # Lightweight deps (for deployment)
├── render.yaml         # Render.com deployment config
├── Dockerfile          # Docker deployment
├── build.sh            # Build script (installs deps + builds frontend)
├── .python-version     # Forces Python 3.11 on Render
├── .node-version       # Forces Node 20 on Render
└── .gitignore
```

---

## Local Development

You need two terminals running simultaneously.

### Terminal 1 — Backend

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py
```

Backend starts at http://localhost:8000

### Terminal 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at http://localhost:3000

Open **http://localhost:3000** in your browser.

The first-time setup (pip install, npm install, spacy download) only needs to be done once. After that, just run `python app.py` and `npm run dev`.

---

## Deploy for Free

### Option 1 — Render (Recommended)

1. Push the project to a GitHub repository
2. Go to [render.com](https://render.com) and sign up (free, no credit card)
3. Click **New → Web Service** and connect your GitHub repo
4. Set these settings:
   - **Build Command:** `bash build.sh`
   - **Start Command:** `gunicorn backend.app:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120`
5. Select the **Free** plan and deploy
6. Your app will be live at `https://your-app-name.onrender.com`

The free tier sleeps after 15 minutes of inactivity. First visit after sleep takes about 30 seconds to wake up.

### Option 2 — Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) and sign up (gives $5 free credit)
3. Click **New Project → Deploy from GitHub Repo**
4. Railway auto-detects the Dockerfile
5. Add environment variable: `PORT` = `8000`
6. Your app will be live at `https://your-app.up.railway.app`

### Option 3 — Docker (any server)

```bash
docker build -t resume-reviewer .
docker run -p 8000:8000 resume-reviewer
```

Open http://localhost:8000

---

## How Free Deployment Works

Free hosting platforms have limited RAM (512 MB), which isn't enough for the heavy ML models. The app handles this gracefully — every ML feature has a built-in lightweight fallback:

| Feature | Local (full ML) | Deployed (fallback) |
|---|---|---|
| Resume parsing | PyMuPDF + python-docx | Same |
| Grammar check | LanguageTool | Regex-based (misspellings, passive voice, weak verbs) |
| Keyword extraction | KeyBERT + spaCy NER | TF frequency analysis + skill bank matching |
| Job description matching | SentenceTransformers cosine similarity | Jaccard word-overlap similarity |
| Sentence improvements | T5 paraphrase model | Rule-based verb replacement |
| AI content detection | Statistical heuristics | Same |
| ATS scoring | Full algorithm | Same |

All features work on free hosting. The ML models just add extra accuracy when running locally.

---

## API

The backend exposes two endpoints:

**POST /api/analyze** — Analyze a resume

- `resume` (file) — PDF or DOCX file
- `job_description` (string, optional) — Job description text

Returns JSON with: `ats`, `grammar`, `keywords`, `jd_match`, `improvements`, `ai_detection`, `word_count`, `char_count`

**GET /api/health** — Health check

Returns `{"status": "ok"}`

---

## Uninstall

```bash
# Python packages
pip uninstall -y fastapi uvicorn python-multipart PyMuPDF python-docx gunicorn numpy language-tool-python spacy keybert sentence-transformers transformers torch
python -m pip uninstall -y en-core-web-sm

# Node packages
cd frontend && rm -rf node_modules
```

---

## License

Open source. Free to use, modify, and deploy.
