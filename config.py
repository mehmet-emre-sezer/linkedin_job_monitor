import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CV_PATH = os.getenv("CV_PATH", "")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "70"))

# LinkedIn location filter (empty string = worldwide)
SEARCH_LOCATION = "Turkey"

# How many jobs to process per query per run
JOBS_PER_QUERY = 5

SEEN_JOBS_FILE = "seen_jobs.json"

# ─── Arama sorguları — istediğin zaman ekle/çıkar ────────────────────────────
# LinkedIn boolean syntax destekleniyor: AND, OR, NOT, "tırnak içi exact match"
SEARCH_QUERIES = [
    (
        '("Junior" OR "Entry Level" OR "Intern" OR "Graduate" OR "New Grad")'
        ' AND ("Data Scientist" OR "Machine Learning Engineer" OR "AI Engineer"'
        ' OR "Backend Developer" OR "Full Stack Developer" OR "Software Engineer"'
        ' OR "QA Engineer" OR "Test Engineer" OR "Automation Engineer" OR "SDET")'
        ' AND (Python OR SQL OR API OR "test automation")'
    ),
]

# ─── Candidate Profile (LLM scoring için) ────────────────────────────────────
CANDIDATE_PROFILE = """
Name: Mehmet Emre Sezer
Title: Data Scientist / ML Engineer (Student)
Location: Istanbul, Turkey
University: Turkish-German University — Computer Engineering (100% German, ongoing)

Technical Skills:
- Python (primary language), Java
- Machine Learning, Deep Learning
- LLM Fine-Tuning (fine-tuned a model for financial news sentiment analysis)
- NLP, Time Series Analysis, Feature Engineering
- Data Analysis, Statistics
- API integration, web services, mobile compatibility testing

Work Experience:
- Turkcell Digital Business Solutions — Solution Analyst (Part-Time, 2025-2026)
  Mobile integration of LifeCare web app, API/web service analysis, integration testing
- Feza Mühendislik — Data Entry & Analysis Specialist (2024)
  Analyzed production data of 50 employees across 100+ products, profitability analysis
- Univgates — Project contributor (full-stack/backend development)

Projects:
- LLM fine-tuning for financial news sentiment analysis (NLP + finance domain)
- Univgates platform (web/backend development)

Preferences:
- Junior / entry-level / intern roles
- Remote or hybrid
- Data Science, ML, NLP, AI, Backend (Python) roles
- Penalize: roles requiring 3+ years experience, senior titles, unrelated stacks (pure frontend, mobile-only, .NET-only)
"""
