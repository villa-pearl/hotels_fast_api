import asyncio
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import fitz  # PyMuPDF

#import ai_gem
import ai_grok
import ai_llama

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Hotel Price PDF Analyzer")


@app.get("/")
async def upload_form():
    return FileResponse(
        path=STATIC_DIR / "upload_pdf.html",
        media_type="text/html",
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_pdf(pdf_file: UploadFile = File(...)):
    print("def upload_pdf")

    if not pdf_file.filename or not pdf_file.filename.lower().endswith(".pdf"):
        return {"error": "Разрешены только PDF-файлы"}

    pdf_bytes = await pdf_file.read()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = doc.page_count
    print(pages)
    doc.close()

    # Тяжёлые sync-вызовы API — в отдельном потоке, чтобы не блокировать event loop
    llama_json = await asyncio.to_thread(ai_llama.get_llama_from_pdf, pdf_bytes)
    #ai_res = await asyncio.to_thread(ai_gem.get_result, llama_json)
    ai_res = await asyncio.to_thread(ai_grok.get_result, llama_json)

    return {
        "filename": pdf_file.filename,
        "size_bytes": len(pdf_bytes),
        "pages": pages,
        "ai_res": ai_res,
    }
