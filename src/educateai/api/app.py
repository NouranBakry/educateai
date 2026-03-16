from fastapi import FastAPI, UploadFile, File, HTTPException
from educateai.ingestion import parser, chunker, embedder, store
import tempfile
import os

app = FastAPI(title="EducateAI API", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    contents = await file.read()
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        text = parser.parse_uploaded_file(tmp_path)

        if not text.strip():
            raise HTTPException(status_code=422, detail="File appears to be empty or unreadable.")

        chunks = chunker.smart_chunker(text, source_file=file.filename)
        chunks = embedder.embed_chunks(chunks)
        store.save_chunks(chunks)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {"filename": file.filename, "chunk_count": len(chunks)}
