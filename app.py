import asyncio
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, Response

import ai_grok2

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
    xlsx_bytes = await asyncio.to_thread(ai_grok2.get_result, pdf_bytes)

    base_name = Path(pdf_file.filename).stem
    download_name = f"{base_name}.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
        },
    )
