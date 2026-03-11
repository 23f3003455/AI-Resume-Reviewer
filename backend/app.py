"""
AI Resume Reviewer — Backend (FastAPI)
=======================================
Single-file backend with:
  - Resume parsing (PDF / DOCX)
  - Grammar & spelling check (LanguageTool + fallback)
  - Keyword extraction (spaCy + KeyBERT + skill bank)
  - ATS scoring (0–100, 5 weighted dimensions)
  - Job description matching (SentenceTransformers)
  - Paraphrasing / copy-paste-ready improvements (T5)
  - AI content detection (statistical heuristics)
  - Humanized rewrite suggestions
"""

from __future__ import annotations

import io
import re
import math
import logging
import statistics
from collections import Counter
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ───────────────────────────────────────────────────────────────
# Lazy-loaded heavy libs
# ───────────────────────────────────────────────────────────────
_spacy_nlp = None
_kw_model = None
_st_model = None
_t5_tok = None
_t5_mdl = None
_lang_tool = None

def get_spacy():
    global _spacy_nlp
    if _spacy_nlp is None:
        import spacy
        try:
            _spacy_nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess, sys
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            _spacy_nlp = spacy.load("en_core_web_sm")
    return _spacy_nlp

def get_keybert():
    global _kw_model
    if _kw_model is None:
        from keybert import KeyBERT
        _kw_model = KeyBERT()
    return _kw_model

def get_sentence_transformer():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _st_model

def get_t5():
    global _t5_tok, _t5_mdl
    if _t5_mdl is None:
        from transformers import T5ForConditionalGeneration, T5Tokenizer
        name = "Vamsi/T5_Paraphrase_Paws"
        _t5_tok = T5Tokenizer.from_pretrained(name)
        _t5_mdl = T5ForConditionalGeneration.from_pretrained(name)
    return _t5_tok, _t5_mdl

def get_language_tool():
    global _lang_tool
    if _lang_tool is None:
        import language_tool_python
        _lang_tool = language_tool_python.LanguageTool("en-US")
    return _lang_tool

# ───────────────────────────────────────────────────────────────
# App
# ───────────────────────────────────────────────────────────────
app = FastAPI(title="AI Resume Reviewer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger("resume_reviewer")

# ───────────────────────────────────────────────────────────────
# Resume parsing
# ───────────────────────────────────────────────────────────────
def parse_pdf(data: bytes) -> str:
    import fitz
    parts: list[str] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            parts.append(page.get_text())
    return "\n".join(parts)

def parse_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)

# ───────────────────────────────────────────────────────────────
# Grammar & Spelling
# ───────────────────────────────────────────────────────────────
def check_grammar(text: str) -> list[dict]:
    try:
        tool = get_language_tool()
        matches = tool.check(text)
        issues: list[dict] = []
        for m in matches[:40]:
            issues.append({
                "message": m.message,
                "context": m.context,
                "suggestions": m.replacements[:3],
                "category": m.category,
                "offset": m.offset,
                "length": m.errorLength,
            })
        return issues
    except Exception as exc:
        logger.warning("LanguageTool unavailable: %s", exc)
        return _fallback_grammar(text)

def _fallback_grammar(text: str) -> list[dict]:
    issues: list[dict] = []
    misspellings = {
        "recieve": "receive", "occured": "occurred", "seperate": "separate",
        "definately": "definitely", "accomodate": "accommodate",
        "managment": "management", "enviroment": "environment",
        "developement": "development", "responsibilites": "responsibilities",
        "acheive": "achieve", "beleive": "believe", "calender": "calendar",
        "collegue": "colleague", "comittee": "committee", "concensus": "consensus",
        "entreprenur": "entrepreneur", "goverment": "government",
        "immediatly": "immediately", "independant": "independent",
        "knowlege": "knowledge", "liason": "liaison", "maintainance": "maintenance",
        "neccessary": "necessary", "occassion": "occasion", "proffesional": "professional",
        "recomend": "recommend", "refered": "referred", "succesful": "successful",
        "thier": "their", "untill": "until", "wierd": "weird",
    }
    lower = text.lower()
    for wrong, right in misspellings.items():
        if wrong in lower:
            idx = lower.index(wrong)
            s, e = max(0, idx - 20), min(len(text), idx + len(wrong) + 20)
            issues.append({"message": f"Possible misspelling: '{wrong}' → '{right}'",
                           "context": text[s:e], "suggestions": [right],
                           "category": "SPELLING", "offset": idx, "length": len(wrong)})

    for m in re.finditer(r"\b(\w+)\s+\1\b", text, re.I):
        issues.append({"message": f"Repeated word: '{m.group(1)}'",
                       "context": text[max(0, m.start()-15):m.end()+15],
                       "suggestions": [m.group(1)], "category": "DUPLICATION",
                       "offset": m.start(), "length": len(m.group(0))})

    passive_re = re.compile(
        r"\b(was|were|been|being|is|are|am)\s+(being\s+)?"
        r"(given|taken|made|done|said|gone|known|seen|told|found|thought|"
        r"used|called|asked|needed|provided|written|created|developed|"
        r"managed|handled|organized|implemented|executed|delivered|"
        r"achieved|completed|performed|conducted|maintained|supported)\b", re.I)
    for m in passive_re.finditer(text):
        s, e = max(0, m.start()-20), min(len(text), m.end()+30)
        issues.append({"message": "Consider active voice for stronger impact.",
                       "context": text[s:e], "suggestions": ["Rewrite using active voice"],
                       "category": "STYLE", "offset": m.start(), "length": len(m.group(0))})

    weak_verbs = ["helped", "assisted", "worked on", "was responsible for",
                  "participated in", "was involved in", "handled"]
    for verb in weak_verbs:
        idx = lower.find(verb)
        if idx != -1:
            s, e = max(0, idx - 20), min(len(text), idx + len(verb) + 30)
            issues.append({"message": f"Weak action verb '{verb}' — use a stronger verb.",
                           "context": text[s:e],
                           "suggestions": ["led", "spearheaded", "drove", "engineered"],
                           "category": "RESUME_STYLE", "offset": idx, "length": len(verb)})
    return issues[:40]

# ───────────────────────────────────────────────────────────────
# Keyword Extraction
# ───────────────────────────────────────────────────────────────
SKILL_BANK: set[str] = {
    "python","java","javascript","typescript","c++","c#","ruby","go","rust",
    "swift","kotlin","php","scala","r","matlab","sql","nosql","html","css",
    "react","angular","vue","node.js","express","django","flask","fastapi",
    "spring","rails",".net","tensorflow","pytorch","keras","scikit-learn",
    "pandas","numpy","matplotlib","docker","kubernetes","aws","azure","gcp",
    "terraform","ansible","jenkins","ci/cd","git","github","gitlab",
    "machine learning","deep learning","natural language processing","nlp",
    "computer vision","data science","data analysis","data engineering",
    "database","postgresql","mysql","mongodb","redis","elasticsearch",
    "rest api","graphql","microservices","agile","scrum","kanban",
    "project management","team leadership","communication","problem solving",
    "critical thinking","time management","leadership","collaboration",
    "strategic planning","budgeting","stakeholder management",
    "powerpoint","excel","tableau","power bi","jira","confluence",
    "figma","sketch","adobe","photoshop","illustrator",
    "cybersecurity","penetration testing","networking","linux","windows",
    "devops","sre","blockchain","cloud computing","saas","etl",
    "spark","hadoop","kafka","airflow","snowflake","databricks",
}

def extract_keywords(text: str) -> dict:
    results: dict = {"keybert": [], "entities": [], "skills_found": []}
    try:
        kw = get_keybert()
        kw_results = kw.extract_keywords(text, keyphrase_ngram_range=(1, 2),
                                          stop_words="english", top_n=15,
                                          use_mmr=True, diversity=0.5)
        results["keybert"] = [{"keyword": k, "score": round(s, 3)} for k, s in kw_results]
    except Exception:
        results["keybert"] = _fallback_kw(text)

    try:
        nlp = get_spacy()
        doc = nlp(text[:100_000])
        cnt: Counter = Counter()
        for ent in doc.ents:
            if ent.label_ in ("ORG","PRODUCT","GPE","PERSON","DATE","LANGUAGE"):
                cnt[(ent.text.strip(), ent.label_)] += 1
        results["entities"] = [{"text": t, "label": l, "count": c}
                               for (t, l), c in cnt.most_common(20)]
    except Exception:
        pass

    lower = text.lower()
    results["skills_found"] = sorted(s for s in SKILL_BANK if s in lower)
    return results

def _fallback_kw(text: str) -> list[dict]:
    stop = set("the a an and or but in on at to for of with by from is was were are been be have has had do does did will would could should may might shall can this that these those i you he she it we they me him her us them my your his its our their what which who whom where when how not no nor as if then so than too very just about also".split())
    words = re.findall(r"[a-z]{3,}", text.lower())
    counts = Counter(w for w in words if w not in stop)
    total = sum(counts.values()) or 1
    return [{"keyword": w, "score": round(c / total, 3)} for w, c in counts.most_common(15)]

# ───────────────────────────────────────────────────────────────
# ATS Compatibility Score
# ───────────────────────────────────────────────────────────────
SECTION_PATTERNS = {
    "contact":    re.compile(r"(email|phone|address|linkedin|github|portfolio|contact)", re.I),
    "summary":    re.compile(r"(summary|objective|profile|about\s*me|professional\s*summary)", re.I),
    "experience": re.compile(r"(experience|employment|work\s*history|professional\s*experience)", re.I),
    "education":  re.compile(r"(education|academic|degree|university|college|school)", re.I),
    "skills":     re.compile(r"(skills|technical\s*skills|competencies|expertise|proficiency)", re.I),
    "projects":   re.compile(r"(projects|personal\s*projects|portfolio)", re.I),
    "certifications": re.compile(r"(certifications?|licenses?|accreditations?)", re.I),
}

def _syllables(w: str) -> int:
    w = w.lower().rstrip("e")
    return max(len(re.findall(r"[aeiouy]+", w)), 1)

def _fk_grade(text: str) -> float:
    sents = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 3]
    words = re.findall(r"[a-zA-Z]+", text)
    if not sents or not words:
        return 0.0
    syls = sum(_syllables(w) for w in words)
    return 0.39 * len(words) / len(sents) + 11.8 * syls / len(words) - 15.59

def compute_ats_score(text: str, kw_data: dict) -> dict:
    scores, suggestions = {}, []

    # Sections (30)
    essential = ["contact", "experience", "education", "skills"]
    nice = ["summary", "projects", "certifications"]
    found = {n for n, p in SECTION_PATTERNS.items() if p.search(text)}
    ef = found & set(essential)
    nf = found & set(nice)
    ss = min(30, (len(ef)/len(essential))*22 + (len(nf)/len(nice))*8)
    scores["sections"] = {"score": round(ss,1), "max": 30, "found": sorted(found),
                          "missing": sorted(set(essential)-ef)}
    for m in sorted(set(essential)-ef):
        suggestions.append(f"Add a clearly labeled '{m.title()}' section.")
    if "summary" not in found:
        suggestions.append("Consider adding a professional Summary/Objective section.")

    # Keywords (25)
    sk = kw_data.get("skills_found", [])
    ks = min(25, (len(sk)/8)*25)
    scores["keywords"] = {"score": round(ks,1), "max": 25, "count": len(sk), "skills": sk[:15]}
    if len(sk) < 5:
        suggestions.append("Include more industry-relevant keywords and technical skills.")

    # Readability (20)
    grade = _fk_grade(text)
    if 8 <= grade <= 12: rs = 20
    elif 6 <= grade < 8 or 12 < grade <= 14: rs = 15
    else: rs = max(5, 20 - abs(grade-10)*2)
    rs = min(20, max(0, rs))
    scores["readability"] = {"score": round(rs,1), "max": 20, "grade_level": round(grade,1)}
    if grade > 14: suggestions.append("Simplify language — reads at a very high grade level.")
    elif grade < 6: suggestions.append("Add more detail and professional terminology.")

    # Formatting (15)
    wc = len(text.split())
    lines = text.split("\n")
    fs = 15.0
    if wc < 150: fs -= 5; suggestions.append("Resume is very short. Aim for 400–800 words.")
    elif wc > 1200: fs -= 3; suggestions.append("Consider condensing to 1–2 pages.")
    bullets = sum(1 for l in lines if re.match(r"^\s*[•\-\*▪►➤➢]", l))
    if bullets < 3 and wc > 200: fs -= 3; suggestions.append("Use bullet points for ATS scannability.")
    quant = re.findall(r"\d+%|\$[\d,]+|\d+\+?\s*(years?|clients?|projects?|team|users?)", text, re.I)
    if len(quant) < 2: fs -= 2; suggestions.append("Add quantified achievements (%, $, team sizes).")
    fs = max(0, fs)
    scores["formatting"] = {"score": round(fs,1), "max": 15, "word_count": wc,
                            "bullet_points": bullets, "quantified": len(quant)}

    # Action verbs (10)
    strong = {"achieved","led","managed","developed","created","designed","implemented",
              "increased","decreased","improved","launched","built","delivered","drove",
              "established","generated","negotiated","optimized","orchestrated","pioneered",
              "reduced","resolved","revamped","spearheaded","streamlined","transformed",
              "architected","automated","consolidated","engineered","executed","facilitated",
              "mentored","scaled"}
    lower = text.lower()
    fv = [v for v in strong if v in lower]
    vs = min(10, (len(fv)/5)*10)
    scores["action_verbs"] = {"score": round(vs,1), "max": 10, "found": sorted(fv)}
    if len(fv) < 3:
        suggestions.append("Start bullets with strong action verbs (led, built, optimized).")

    total = min(100, max(0, sum(v["score"] for v in scores.values())))
    g = "A+" if total>=90 else "A" if total>=80 else "B+" if total>=70 else "B" if total>=60 else "C" if total>=50 else "D" if total>=40 else "F"
    return {"total_score": round(total), "breakdown": scores, "suggestions": suggestions, "grade": g}

# ───────────────────────────────────────────────────────────────
# Job Description Matching
# ───────────────────────────────────────────────────────────────
def match_job_description(resume: str, jd: str) -> dict:
    if not jd or not jd.strip():
        return {"match_pct": None, "message": "No job description provided."}
    try:
        model = get_sentence_transformer()
        embs = model.encode([resume[:5000], jd[:5000]])
        from numpy import dot
        from numpy.linalg import norm
        cos = float(dot(embs[0], embs[1]) / (norm(embs[0]) * norm(embs[1])))
        pct = round(max(0, min(100, cos * 100)), 1)
    except Exception:
        pct = _fallback_sim(resume, jd)

    jd_lower, res_lower = jd.lower(), resume.lower()
    jd_sk = sorted(s for s in SKILL_BANK if s in jd_lower)
    res_sk = sorted(s for s in SKILL_BANK if s in res_lower)
    missing = sorted(set(jd_sk) - set(res_sk))
    matched = sorted(set(jd_sk) & set(res_sk))

    rec = ("Excellent match!" if pct >= 80 else "Good match. Add missing keywords." if pct >= 60
           else "Moderate match. Tailor your resume." if pct >= 40
           else "Low match. Significantly customize your resume.")
    return {"match_pct": pct, "jd_keywords": jd_sk, "resume_keywords": res_sk,
            "matched_keywords": matched, "missing_keywords": missing, "recommendation": rec}

def _fallback_sim(a: str, b: str) -> float:
    stop = set("the a an and or but in on at to for of with by from is was were are been be have has had this that i you we they it my your our their".split())
    wa = set(re.findall(r"[a-z]{3,}", a.lower())) - stop
    wb = set(re.findall(r"[a-z]{3,}", b.lower())) - stop
    if not wa or not wb: return 0.0
    return round(len(wa & wb) / len(wa | wb) * 100, 1)

# ───────────────────────────────────────────────────────────────
# Copy-Paste Ready Improvement Suggestions
# ───────────────────────────────────────────────────────────────
def generate_improvements(text: str) -> list[dict]:
    """Find weak sentences and generate ready-to-paste improved versions."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]

    weak_re = re.compile(
        r"\b(responsible for|helped|assisted|worked on|was involved|participated|"
        r"was responsible|duties included|tasked with|in charge of|"
        r"did various|various tasks|day-to-day|handled various)\b", re.I)
    weak = [s for s in sents if weak_re.search(s)][:6]
    if len(weak) < 3:
        weak += [s for s in sents if 20 < len(s) < 200 and s not in weak][:4 - len(weak)]

    results = []
    try:
        tok, mdl = get_t5()
        for sent in weak:
            inp = f"paraphrase: {sent} </s>"
            enc = tok.encode_plus(inp, max_length=256, padding="max_length",
                                   truncation=True, return_tensors="pt")
            outs = mdl.generate(input_ids=enc["input_ids"],
                                 attention_mask=enc["attention_mask"],
                                 max_length=256, num_beams=5,
                                 num_return_sequences=2, early_stopping=True)
            paras = []
            for o in outs:
                d = tok.decode(o, skip_special_tokens=True)
                if d.lower().strip() != sent.lower().strip():
                    paras.append(d)
            # Also apply rule-based improvement
            rule_improved = _rule_improve(sent)
            if rule_improved and rule_improved != sent:
                paras.append(rule_improved)
            results.append({"original": sent, "improved": paras[:3],
                            "copy_ready": paras[0] if paras else sent})
    except Exception:
        results = _fallback_improve(weak)
    return results

def _rule_improve(sent: str) -> str:
    replacements = [
        (r"\bwas responsible for\b", "spearheaded"),
        (r"\bresponsible for\b", "led"),
        (r"\bhelped\b", "contributed to"),
        (r"\bassisted in\b", "supported"),
        (r"\bworked on\b", "developed"),
        (r"\bwas involved in\b", "played a key role in"),
        (r"\bparticipated in\b", "contributed to"),
        (r"\bduties included\b", "key contributions included"),
        (r"\btasked with\b", "drove"),
        (r"\bin charge of\b", "managed"),
        (r"\bhandled\b", "orchestrated"),
        (r"\bdid various\b", "executed diverse"),
        (r"\bvarious tasks\b", "cross-functional initiatives"),
    ]
    result = sent
    for pat, rep in replacements:
        result = re.sub(pat, rep, result, flags=re.I)
    return result

def _fallback_improve(sents: list[str]) -> list[dict]:
    results = []
    for s in sents:
        imp1 = _rule_improve(s)
        # Second variant
        alt = {
            r"\bwas responsible for\b": "owned and executed",
            r"\bresponsible for\b": "spearheaded",
            r"\bhelped\b": "drove",
            r"\bassisted in\b": "facilitated",
            r"\bworked on\b": "engineered",
            r"\bwas involved in\b": "orchestrated",
            r"\bparticipated in\b": "actively drove",
            r"\bhandled\b": "directed",
        }
        imp2 = s
        for p, r in alt.items():
            imp2 = re.sub(p, r, imp2, flags=re.I)
        improved = []
        if imp1 != s: improved.append(imp1)
        if imp2 != s and imp2 != imp1: improved.append(imp2)
        results.append({"original": s, "improved": improved,
                        "copy_ready": improved[0] if improved else s})
    return results

# ───────────────────────────────────────────────────────────────
# AI Content Detection + Humanization
# ───────────────────────────────────────────────────────────────
# Heuristic-based AI content detection using statistical text analysis.
# Looks for patterns common in AI-generated text:
#   - Low perplexity approximation (uniform word frequency distribution)
#   - Repetitive sentence structures
#   - Overuse of certain "AI-ish" phrases
#   - Low vocabulary diversity (type-token ratio)
#   - Uniform sentence lengths

AI_PHRASES = [
    "leveraging", "utilizing", "spearheaded", "synergy", "synergies",
    "cutting-edge", "state-of-the-art", "best-in-class", "world-class",
    "innovative solutions", "drive results", "proven track record",
    "passionate about", "dedicated to", "committed to excellence",
    "strong communicator", "self-motivated", "results-driven",
    "dynamic environment", "fast-paced environment", "go-to person",
    "think outside the box", "hit the ground running", "team player",
    "detail-oriented", "proactive approach", "strategic thinker",
    "effectively communicate", "cross-functional collaboration",
    "stakeholder engagement", "value proposition", "core competencies",
    "seamlessly", "holistic approach", "paradigm", "ecosystem",
    "deep understanding", "keen eye", "adept at", "well-versed",
    "comprehensive understanding", "robust experience",
    "instrumental in", "pivotal role", "significantly contributed",
]

def detect_ai_content(text: str) -> dict:
    """Detect likely AI-generated content using statistical heuristics."""
    sents = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 10]
    words = re.findall(r"[a-z]+", text.lower())

    if len(sents) < 3 or len(words) < 30:
        return {"ai_score": 0, "confidence": "low",
                "details": "Too little text to analyze.", "flagged_sentences": []}

    signals: list[float] = []
    details: list[str] = []

    # 1. AI phrase density
    lower = text.lower()
    phrase_hits = sum(1 for p in AI_PHRASES if p in lower)
    phrase_density = phrase_hits / len(sents)
    phrase_signal = min(1.0, phrase_density / 0.5)  # 0.5 phrases/sent = max signal
    signals.append(phrase_signal * 0.25)
    if phrase_hits > 3:
        details.append(f"Found {phrase_hits} AI-typical phrases (e.g., buzzwords and clichés).")

    # 2. Vocabulary diversity (type-token ratio) — AI tends to be more repetitive
    unique = len(set(words))
    ttr = unique / len(words) if words else 1
    # Low TTR = more repetitive. AI text on resumes: TTR ~ 0.3-0.5
    ttr_signal = max(0, min(1.0, (0.55 - ttr) / 0.2))  # below 0.55 is suspicious
    signals.append(ttr_signal * 0.2)
    if ttr < 0.45:
        details.append(f"Low vocabulary diversity (TTR: {ttr:.2f}) — text may be repetitive.")

    # 3. Sentence length uniformity — AI generates very uniform sentence lengths
    sent_lens = [len(s.split()) for s in sents]
    if len(sent_lens) >= 3:
        mean_len = statistics.mean(sent_lens)
        stdev_len = statistics.stdev(sent_lens) if len(sent_lens) > 1 else 0
        cv = stdev_len / mean_len if mean_len > 0 else 0
        # Low CV = very uniform lengths. Human writing: CV > 0.4
        uniform_signal = max(0, min(1.0, (0.4 - cv) / 0.25))
        signals.append(uniform_signal * 0.2)
        if cv < 0.3:
            details.append("Sentence lengths are unusually uniform — typical of AI text.")
    else:
        signals.append(0)

    # 4. Sentence start repetition — AI often starts sentences the same way
    starts = [s.split()[0].lower() if s.split() else "" for s in sents]
    start_counts = Counter(starts)
    max_repeat_ratio = max(start_counts.values()) / len(sents) if sents else 0
    repeat_signal = max(0, min(1.0, (max_repeat_ratio - 0.25) / 0.25))
    signals.append(repeat_signal * 0.15)
    if max_repeat_ratio > 0.35:
        top_start = start_counts.most_common(1)[0][0]
        details.append(f"Many sentences start with '{top_start}' — vary your openings.")

    # 5. Hedge / filler phrase absence — AI text tends to be unnaturally confident
    hedges = ["i think", "i believe", "in my experience", "from my perspective",
              "personally", "to be honest", "actually", "basically"]
    hedge_count = sum(1 for h in hedges if h in lower)
    # Absence of hedges in a longer text is slightly suspicious
    if len(sents) > 5 and hedge_count == 0:
        signals.append(0.05)
        details.append("No personal hedges or voice markers found — text feels impersonal.")
    else:
        signals.append(0)

    # 6. Passive voice density — AI often overuses passive
    passive_count = len(re.findall(
        r"\b(was|were|been|being|is|are)\s+\w+ed\b", text, re.I))
    passive_ratio = passive_count / len(sents)
    passive_signal = max(0, min(1.0, (passive_ratio - 0.15) / 0.3))
    signals.append(passive_signal * 0.15)
    if passive_ratio > 0.3:
        details.append("High passive voice usage — consider more active constructions.")

    total = sum(signals)
    pct = round(min(100, total * 100), 1)

    # Flag specific sentences that look most AI-generated
    flagged = []
    for s in sents:
        s_lower = s.lower()
        s_score = 0
        hits = sum(1 for p in AI_PHRASES if p in s_lower)
        s_score += hits * 15
        if len(s.split()) > 25: s_score += 5  # long complex sentences
        if re.search(r"\b(was|were|been|is|are)\s+\w+ed\b", s, re.I): s_score += 8
        if s_score > 15:
            flagged.append({"sentence": s, "score": min(100, s_score),
                            "humanized": _humanize_sentence(s)})

    confidence = "high" if pct > 60 else "medium" if pct > 35 else "low"
    return {
        "ai_score": pct,
        "confidence": confidence,
        "details": details,
        "flagged_sentences": flagged[:8],
    }

def _humanize_sentence(sent: str) -> str:
    """Rewrite an AI-sounding sentence to be more natural/human."""
    result = sent
    humanize_map = [
        (r"\bleveraging\b", "using"),
        (r"\butilizing\b", "using"),
        (r"\bspearheaded\b", "led"),
        (r"\bcutting-edge\b", "modern"),
        (r"\bstate-of-the-art\b", "latest"),
        (r"\bbest-in-class\b", "top"),
        (r"\bworld-class\b", "excellent"),
        (r"\binnovative solutions\b", "new approaches"),
        (r"\bproven track record\b", "consistent results"),
        (r"\bpassionate about\b", "enjoy"),
        (r"\bdedicated to\b", "focused on"),
        (r"\bcommitted to excellence\b", "aim to do great work"),
        (r"\bresults-driven\b", "focused on outcomes"),
        (r"\bdynamic environment\b", "changing environment"),
        (r"\bfast-paced environment\b", "busy workplace"),
        (r"\bthink outside the box\b", "find creative solutions"),
        (r"\bhit the ground running\b", "start contributing quickly"),
        (r"\bseamlessly\b", "smoothly"),
        (r"\bholistic approach\b", "complete approach"),
        (r"\bparadigm\b", "model"),
        (r"\becosystem\b", "system"),
        (r"\bdeep understanding\b", "solid grasp"),
        (r"\bkeen eye\b", "good sense"),
        (r"\badept at\b", "good at"),
        (r"\bwell-versed\b", "experienced"),
        (r"\bcomprehensive understanding\b", "thorough knowledge"),
        (r"\brobust experience\b", "solid experience"),
        (r"\binstrumental in\b", "key to"),
        (r"\bpivotal role\b", "important role"),
        (r"\bsignificantly contributed\b", "helped meaningfully"),
        (r"\bcross-functional collaboration\b", "working across teams"),
        (r"\bstakeholder engagement\b", "working with stakeholders"),
        (r"\bvalue proposition\b", "core value"),
        (r"\bcore competencies\b", "main skills"),
        (r"\bproactive approach\b", "hands-on style"),
        (r"\beffectively communicate\b", "clearly share ideas"),
    ]
    for pat, rep in humanize_map:
        result = re.sub(pat, rep, result, flags=re.I)
    return result

# ───────────────────────────────────────────────────────────────
# Main endpoint
# ───────────────────────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(""),
):
    content = await resume.read()
    fn = resume.filename or ""

    if fn.lower().endswith(".pdf"):
        text = parse_pdf(content)
    elif fn.lower().endswith(".docx"):
        text = parse_docx(content)
    else:
        return JSONResponse({"error": "Upload a PDF or DOCX file."}, status_code=400)

    if not text or len(text.strip()) < 50:
        return JSONResponse({"error": "Could not extract sufficient text."}, status_code=400)

    grammar = check_grammar(text)
    keywords = extract_keywords(text)
    ats = compute_ats_score(text, keywords)
    jd_match = match_job_description(text, job_description)
    improvements = generate_improvements(text)
    ai_detection = detect_ai_content(text)

    return JSONResponse({
        "ats": ats,
        "grammar": grammar,
        "keywords": keywords,
        "jd_match": jd_match,
        "improvements": improvements,
        "ai_detection": ai_detection,
        "word_count": len(text.split()),
        "char_count": len(text),
    })

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# ───────────────────────────────────────────────────────────────
# Serve React frontend in production
# ───────────────────────────────────────────────────────────────
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# In production, the built React app lives in ../frontend/dist
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    # Catch-all: serve index.html for any non-API route (React SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If a specific file exists, serve it
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html (React handles routing)
        return FileResponse(str(FRONTEND_DIR / "index.html"))

# ───────────────────────────────────────────────────────────────
# Run
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
