# Job Monitoring & AI Scoring System PRD

## 1. Overview

This project builds an automated job monitoring system that: - Scrapes
LinkedIn job postings via Selenium - Filters relevant jobs - Scores jobs
using local LLM (Ollama - qwen2.5:14b) - Sends high-quality matches via
Telegram

## 2. Objectives

-   Detect new job postings
-   Avoid duplicates
-   Score relevance using AI
-   Notify only high-quality matches
-   Maintain low detection risk

## 3. Target User

Junior / New Grad Software Engineer\
Skills: Python, ML, NLP, Backend, Fullstack\
Experience: Turkcell (API), freelance dev, ML projects

## 4. Functional Requirements

### 4.1 Job Scraping

-   Selenium with cookies
-   Extract title, company, description, link

### 4.2 Query System

-   AI / ML roles
-   Backend / Fullstack roles
-   Data Analyst roles

### 4.3 Duplicate Detection

-   JSON or SQLite storage
-   Skip processed jobs

### 4.4 AI Scoring

Model: qwen2.5:14b

Prompt: You are evaluating job postings for a candidate...

Return JSON: { "score": number, "reason": "short explanation" }

### 4.5 Filtering

-   Score \>= 70
-   Boost: Junior, Remote
-   Penalize: Senior

### 4.6 Telegram Notification

Format: 🔥 Title - Company ⭐ Score 🧠 Reason 🔗 Link

### 4.7 Scheduling

Run 2-3 times daily

## 5. Non-Functional Requirements

-   Anti-detection (cookies, delays)
-   Reliability (error handling)
-   Performance (20-30 jobs/run)

## 6. Architecture

Scraper → Extractor → Filter → LLM → Notify

## 7. Tech Stack

Python, Selenium, Requests, Ollama, Telegram API

## 8. Storage

-   JSON or SQLite

## 9. Future Enhancements

-   Dashboard
-   Email alerts
-   Auto apply

## 10. Deployment

-   Local or VPS
-   Avoid GitHub Actions

## 11. Success Metrics

-   Relevance rate
-   Time saved
-   Interview conversion
