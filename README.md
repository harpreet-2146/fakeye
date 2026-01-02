# Fakeye 🔍

AI-powered claim verification system that automatically fact-checks claims by searching the web and analyzing evidence.

## Overview

Fakeye is a full-stack web application that helps users verify claims by:

- Searching the web for relevant sources
- Analyzing evidence using semantic similarity and AI-based stance detection
- Providing verdicts (True / False / Unverifiable) with confidence scores
- Explaining why a verdict was reached using natural language reasoning
- Presenting clickable source evidence for manual review

Built as an academic project demonstrating machine learning, natural language processing, and full-stack web development.

## Features

✅ **Automated Fact-Checking** – Enter any claim and get instant verification  
✅ **Semantic Search** – Uses sentence transformers for intelligent source ranking  
✅ **AI Stance Detection** – Determines whether evidence supports, contradicts, or is neutral  
✅ **Verdict Reasoning** – Generates a clear, human-readable explanation for each verdict  
✅ **Numerical Verification** – Handles quantity-based claims (e.g., "15 months in a year")  
✅ **Role & Location Verification** – Detects incorrect role–location associations  
✅ **Evidence Cards** – View sources with stance labels and confidence scores  
✅ **Clean UI** – Modern, responsive interface with animated feedback

## Tech Stack

### Backend

- **Python 3.11+**
- **FastAPI** – Web framework
- **Sentence Transformers** – Semantic similarity (all-MiniLM-L6-v2)
- **Groq API (LLM)** – AI-powered stance detection and reasoning
- **SerpAPI** – Web search integration
- **NumPy** – Numerical computations

### Frontend

- **React 19**
- **Vite**
- **Tailwind CSS**
- **Framer Motion**

## Installation

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- [SerpAPI key](https://serpapi.com/) (get free key)
- [Groq API key](https://console.groq.com/) (get free key)

### Backend Setup

```bash
cd backend

python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

# Create .env file
SERPAPI_API_KEY=your_serpapi_key
GROQ_API_KEY=your_groq_key

uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

npm install

# Optional (defaults to localhost:8000)
VITE_API_URL=http://localhost:8000

npm run dev
```

Frontend runs at `http://localhost:5173`

## Usage

1. Start both backend and frontend servers
2. Open browser at `http://localhost:5173`
3. Enter a claim (e.g., "Is Florida in India?")
4. Review the verdict with confidence score
5. Read the reasoning explanation
6. Inspect evidence sources for transparency

## How It Works

### 1. Web Search

- Claim is sent to SerpAPI
- Retrieves top web results with snippets

### 2. Semantic Ranking

- Sentence transformer encodes claim and snippets
- Cosine similarity ranks evidence by relevance

### 3. AI Stance Detection

Each evidence snippet is analyzed using an LLM to determine whether it:

- **Supports** the claim
- **Contradicts** the claim
- Is **Neutral / Unverifiable**

The model also generates a short explanation for its decision.

### 4. Aggregation

- Evidence is weighted by semantic relevance and stance confidence
- Support and contradiction scores are aggregated
- Final verdict confidence is calculated

### 5. Verdict Reasoning

- The strongest supporting or contradicting explanation is surfaced
- Displayed prominently in the UI as a **Reason** section

## API Endpoints

### `POST /predict`

**Request**

```json
{
  "text": "Is Florida in India?"
}
```

**Response**

```json
{
  "ok": true,
  "input": "Is Florida in India?",
  "verdict_percent": 95.2,
  "verdict_raw_label": "False",
  "verdict_summary": "High confidence. Multiple sources contradict this claim.",
  "verdict_reason": "Florida is a U.S. state and not part of India.",
  "top_matches": [
    {
      "publisher": "britannica.com",
      "url": "https://www.britannica.com/place/Florida",
      "snippet": "Florida is a state in the southeastern United States.",
      "stance": "contradict",
      "stance_conf": 0.96,
      "semantic_sim": 0.91
    }
  ]
}
```

## Limitations

- Relies on publicly available web sources
- English-language claims only
- Subject to SerpAPI rate limits
- Not suitable for opinions or future predictions
- Should not replace professional fact-checking

## Future Enhancements

- Multi-language support
- Source credibility scoring
- Integration with fact-check databases
- User accounts and saved history
- Browser extension
- Advanced NLI models
- Temporal claim verification
- Image and video claim analysis

## Disclaimer

**Fakeye is an academic project.**  
It should not be used as the sole authority for verifying important or sensitive claims. Always cross-check information with trusted sources.

---

**License:** MIT  
**Contact:** harpreetk2146@gmail.com
