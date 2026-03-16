# EducateAI

Turn any curriculum document into child-appropriate learning content.
Upload a PDF or DOCX → get flashcards, quizzes, audio lessons, and study guides tailored to your child's age.

---

## How It Works

```
Upload PDF/DOCX
      │
      ▼
  parser.py        extract text, detect headers with pdfplumber
      │
      ▼
  chunker.py       split at headers/paragraphs, merge tiny pieces, break oversized ones
      │
      ▼
  embedder.py      convert each chunk to a 384-dim vector (all-MiniLM-L6-v2, runs locally)
      │
      ▼
  store.py         persist vectors + metadata to ChromaDB (survives restarts)
      │
      ▼
  generator.py     user asks a question → retrieve top chunks → Gemini writes the answer
```

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| LLM | Gemini 2.0 Flash Lite | Free tier, fast, grounded answers |
| Embeddings | all-MiniLM-L6-v2 | Runs locally, no API cost, 384-dim |
| Vector DB | ChromaDB | Persistent, local, no infra needed |
| API | FastAPI + uvicorn | Async, auto-generated docs at /docs |
| UI | Streamlit | Fast to build, no frontend boilerplate |
| PDF parsing | pdfplumber | Preserves font sizes for header detection |
| Validation | Pydantic v2 | Type-safe data models throughout |

---

## Setup

```bash
# 1. Install dependencies
uv pip install -e ".[dev]"

# 2. Set your Gemini API key
cp .env.example .env
# edit .env and add: GEMINI_API_KEY=your_key_here
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

---

## Run

**API:**
```bash
uv run uvicorn educateai.api.app:app --reload
```
Open `http://localhost:8000/docs` — interactive upload and query UI.

**Streamlit UI:**
```bash
uv run streamlit run src/educateai/ui/app.py
```

---

## Testing

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only
uv run pytest tests/unit/ -v

# With coverage report
uv run pytest tests/ --cov=educateai --cov-report=term-missing
```

**What is tested:**
- `test_chunker.py` — structural_split, merge_small_chunks, split_large_chunks, smart_chunker
- `test_parser.py` — parse_uploaded_file dispatches correctly per file type

---

## Project Structure

```
src/educateai/
├── core/
│   └── models.py          Chunk — the shared data model for the whole pipeline
├── ingestion/
│   ├── parser.py          extract text from PDF/DOCX/TXT with header detection
│   ├── chunker.py         split text into Chunk objects, derive topic from headers
│   ├── embedder.py        encode chunk text → 384-dim vectors
│   └── store.py           save/search chunks in ChromaDB
├── generators/
│   └── generator.py       retrieve chunks + call Gemini → answer (Phase 2)
├── api/
│   └── app.py             FastAPI: POST /api/upload, POST /api/query
└── ui/
    └── app.py             Streamlit frontend
```
