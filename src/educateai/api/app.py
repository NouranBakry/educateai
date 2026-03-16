from fastapi import FastAPI, UploadFile, File
from educateai.ingestion import parser, chunker, embedder, store
import tempfile
import os

app = FastAPI(title="EducateAI API", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    contents = await file.read()

    # save to temp file so parser can read it from disk
    suffix = os.path.splitext(file.filename)[1]  # .pdf or .docx
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    text = parser.parse_uploaded_file(tmp_path)
    chunks = chunker.smart_chunker(text, source_file=file.filename)
    chunks = embedder.embed_chunks(chunks)
    store.save_chunks(chunks)
    os.unlink(tmp_path)  # clean up temp file

    return {"filename": file.filename, "chunk_count": len(chunks)}
