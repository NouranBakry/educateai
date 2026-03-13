## The Architecture

### What EducateAI Does

Parents, schools, tutoring centers upload curriculum documents (PDF, DOCX, text).
EducateAI generates child-appropriate learning content:

- **Flashcards** — Q&A pairs, age-adapted language, PDF + Anki export
- **Quizzes** — multiple choice, true/false, fill-in-blank, AI-validated answers
- **Audio Lessons** — AI-written script narrated by Edge TTS, MP3 output
- **Study Guides** — structured summaries, key concepts, review questions
- **Lesson Plans** — for teachers/parents, includes activities and rubrics

---

### Full Data Flow

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE A: UPLOAD (happens once per curriculum)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[User uploads PDF / DOCX / text]
        │
        ▼
 Document Parser        ← PyPDF2 / python-docx
 (Strategy pattern)       extracts raw text
        │
        ▼
 Topic Extractor        ← Gemini call #1 (one-time per doc)
                          "What are the main topics?"
                          → ["Photosynthesis", "Water Cycle", ...]
        │
        ▼
 Smart Chunker          ← splits at TOPIC BOUNDARIES (not char count)
                          chunk_1 = "Photosynthesis is..."
                          chunk_2 = "Water cycle begins..."
        │
        ▼
 Embedder               ← all-MiniLM-L6-v2 (runs on your laptop, free)
                          chunk_1 → [0.23, -0.41, 0.87, ...] (384 numbers)
                          chunk_2 → [0.11,  0.93, 0.02, ...] (384 numbers)
                          Numbers = meaning. Similar text = similar vectors.
        │
        ▼
 ChromaDB               ← stores { vector + original text + metadata }
                          metadata: { topic, page, curriculum_id, age_group }

✅ ChromaDB now "knows" the curriculum semantically.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE B: GENERATE (every time user requests content)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User: "Generate flashcards about photosynthesis for a 10-year-old"
        │
        ▼
 Query Embedder         ← "photosynthesis" → [0.25, -0.39, 0.89, ...]
        │
        ▼
 ChromaDB Retrieval     ← COSINE SIMILARITY SEARCH
                          chunk_1 score: 0.94 ✅  (photosynthesis content)
                          chunk_2 score: 0.21 ❌  (water cycle, skip)
                          chunk_3 score: 0.91 ✅  (chlorophyll content)
                          → returns top 4 most relevant chunks
        │
        ▼
 Prompt Builder         ← Jinja2 template + retrieved chunks
                          "You are a teacher for a 10-year-old.
                           Use ONLY this curriculum content: {chunks}
                           Generate 10 flashcards. Return JSON."
        │
        ▼
 Gemini 2.5 Flash       ← generates flashcards grounded in actual curriculum
 (free tier: 250/day)     no hallucination — it has the source text
        │
        ▼
 Validator              ← Pydantic parses JSON
                          Flesch-Kincaid readability ≤ grade 5 for age 10
                          Factual accuracy: re-embed answer, check vs source
        │
        ▼
 [Flashcards displayed + PDF / Anki export]
```

---

### Why Vectors, Not Just Keyword Search

```
Curriculum: "Chlorophyll captures light energy to synthesize glucose"
Query:      "how do plants make food"

SQLite FTS:   ❌  No match — no shared keywords
ChromaDB:     ✅  0.87 similarity — same meaning, different words
```

Vectors bridge the vocabulary gap. Children ask questions in plain language.
Curricula use technical terms. ChromaDB matches them by meaning, not words.

---
## Tech Stack
| Layer | Tool | Free? | Laptop load |
|---|---|---|---|
| LLM | Gemini 2.5 Flash | Yes (250/day) | None (API call) |
| Embeddings | all-MiniLM-L6-v2 | Yes | Light (22M params) |
| Vector DB | ChromaDB | Yes | Light |
| RAG | LlamaIndex | Yes | None |
| TTS | edge-tts | Yes | None (API call) |
| API | FastAPI + uvicorn | Yes | Light |
| UI | Streamlit | Yes | Light |
| Deploy | Hugging Face Spaces | Yes (2-core, 16GB) | None (cloud) |
| CI/CD | GitHub Actions | Yes (public repos) | None (cloud) |
| PDF gen | ReportLab | Yes | Light |
| Testing | pytest | Yes | Light |
| Linting | Ruff | Yes | Light |