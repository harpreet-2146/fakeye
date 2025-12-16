# Fakeye 🔍

AI-powered claim verification system that automatically fact-checks claims by searching the web and analyzing evidence.

## Overview

Fakeye is a full-stack web application that helps users verify claims by:
- Searching the web for relevant sources
- Analyzing evidence using semantic similarity and stance detection
- Providing verdicts (True/False/Unverifiable) with confidence scores
- Presenting clickable source evidence for manual review

Built as an academic project demonstrating machine learning, natural language processing, and web development.

## Features

✅ **Automated Fact-Checking** - Enter any claim and get instant verification  
✅ **Semantic Search** - Uses sentence transformers for intelligent source ranking  
✅ **Stance Detection** - Analyzes whether sources support, contradict, or are neutral  
✅ **Numerical Verification** - Special handling for quantity claims (e.g., "15 months in a year")  
✅ **Location Verification** - Detects mismatches in role-location claims  
✅ **Evidence Cards** - View all sources with stance labels and confidence scores  
✅ **Clean UI** - Modern, responsive design with visual feedback  

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Web framework
- **Sentence Transformers** - Semantic similarity (all-MiniLM-L6-v2)
- **SerpAPI** - Web search integration
- **NumPy** - Numerical computations

### Frontend
- **React 19** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations

## Installation

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- SerpAPI key ([get free key](https://serpapi.com/))

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "SERPAPI_API_KEY=your_api_key_here" > .env

# Run server
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (optional - defaults to localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

Frontend runs at `http://localhost:5173`

## Usage

1. **Start both backend and frontend servers**
2. **Open browser** to `http://localhost:5173`
3. **Enter a claim** (e.g., "Is Modi the PM of India?")
4. **Review verdict** - True/False/Unverifiable with confidence %
5. **Check evidence** - Click on source cards to verify manually

### Example Queries

✅ **Factual Claims**
- "Is Biden the president of USA?"
- "Is the Earth round?"
- "Are there 12 months in a year?"

✅ **Role Verification**
- "Is Modi the prime minister of India?"
- "Is Elon Musk the CEO of Tesla?"

✅ **Numerical Claims**
- "Are there 365 days in a year?"
- "Does water boil at 100 degrees Celsius?"

❌ **Not Suitable For**
- Opinions ("Is pizza the best food?")
- Future predictions ("Will it rain tomorrow?")
- Personal information ("What is my phone number?")

## How It Works

### 1. Web Search
- Query sent to SerpAPI
- Returns top 10 web results with snippets

### 2. Semantic Ranking
- Uses `all-MiniLM-L6-v2` sentence transformer
- Calculates cosine similarity between claim and snippets
- Ranks sources by relevance

### 3. Stance Detection
Analyzes each source with priority checks:
- **Contradictions** - Explicit negations, false claims
- **Numerical verification** - Exact number matching
- **Death claims** - Requires explicit evidence
- **Role claims** - Verifies person + role + location
- **General claims** - Keyword matching with high thresholds

### 4. Aggregation
- Weighted scoring: `(support_score - contradict_score) / total_weight`
- Confidence boosting for support/contradict stances
- Final verdict based on aggregate confidence

### 5. Verdict Mapping
- **True**: 60-100% confidence
- **False**: 0-40% confidence
- **Unverifiable**: 40-60% confidence (mixed or insufficient evidence)


## API Endpoints

### `POST /predict`
Main prediction endpoint

**Request:**
```json
{
  "text": "Is Modi the PM of India?"
}
```

**Response:**
```json
{
  "ok": true,
  "input": "Is Modi the PM of India?",
  "verdict_percent": 85.3,
  "verdict_label": "Very Likely True",
  "verdict_raw_label": "True",
  "verdict_summary": "High confidence. Multiple sources (5) support this claim.",
  "top_matches": [
    {
      "publisher": "example.com",
      "url": "https://example.com/article",
      "snippet": "Narendra Modi serves as Prime Minister...",
      "stance": "support",
      "stance_conf": 0.87,
      "semantic_sim": 0.92
    }
  ]
}
```

### `POST /predict_debug`
Debug endpoint with full breakdown

Returns additional `evidence` array and `aggregate_breakdown` object.

## Configuration

### Backend (`backend/.env`)
```env
SERPAPI_API_KEY=your_key_here
```

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000
```

## Limitations

- **Knowledge Cutoff**: Relies on current web content
- **Search Quality**: Limited by SerpAPI result quality
- **Language**: English only
- **Context**: Cannot verify claims requiring complex reasoning
- **Bias**: May reflect biases in web sources
- **Rate Limits**: Subject to SerpAPI free tier limits (100 searches/month)

## Future Enhancements

- [ ] Multi-language support
- [ ] Source credibility scoring
- [ ] Fact-check database integration (Snopes, PolitiFact)
- [ ] User accounts and history
- [ ] Chrome extension
- [ ] Advanced NLI models (RoBERTa-large-MNLI)
- [ ] Temporal claim verification
- [ ] Image/video claim analysis

## Contributing

This is an academic project. For improvements:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -m "feat: add improvement"`)
4. Push to branch (`git push origin feature/improvement`)
5. Open Pull Request

## Acknowledgments

- **Sentence Transformers** - HuggingFace model library
- **SerpAPI** - Web search API
- **FastAPI** - Modern Python web framework
- **React & Vite** - Frontend tooling

## Contact

For questions or feedback about this academic project, please open an issue on GitHub.

---

**⚠️ Disclaimer**: Fakeye is an academic project and should not be used as the sole source for fact-checking important claims. Always verify information through multiple reliable sources.