import asyncio
from pathlib import Path

import fitz
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, Response

import ai_grok3
import send_to_table
import ai_grok_epress

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Hotel Price PDF Analyzer")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


@app.get("/")
async def upload_form():
    return FileResponse(
        path=STATIC_DIR / "upload_pdf.html",
        media_type="text/html",
    )

@app.get("/express")
async def upload_form():
    return FileResponse(
        path=STATIC_DIR / "express_pdf.html",
        media_type="text/html",
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_pdf(request: Request, pdf_file: UploadFile = File(...)):
    print("def upload_pdf")

    if not pdf_file.filename or not pdf_file.filename.lower().endswith(".pdf"):
        return {"error": "Разрешены только PDF-файлы"}

    pdf_bytes = await pdf_file.read()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        pages = doc.page_count
    finally:
        doc.close()

    await asyncio.to_thread(
        send_to_table.add_baserow_record,
        _client_ip(request),
        pdf_file.filename,
        str(pages),
    )

    xlsx_bytes = await asyncio.to_thread(ai_grok3.get_result, pdf_bytes)

    base_name = Path(pdf_file.filename).stem
    download_name = f"{base_name}.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
        },
    )



@app.post("/express_upload")
async def upload_pdf(request: Request, pdf_file: UploadFile = File(...)):
    print("def express_upload_pdf")

    if not pdf_file.filename or not pdf_file.filename.lower().endswith(".pdf"):
        return {"error": "Разрешены только PDF-файлы"}

    pdf_bytes = await pdf_file.read()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        pages = doc.page_count
    finally:
        doc.close()

    await asyncio.to_thread(
        send_to_table.add_baserow_record,
        _client_ip(request),
        pdf_file.filename,
        str(pages) +' express', #f"{pages}express"
    )

    ai_res = await asyncio.to_thread(ai_grok_epress.get_result, pdf_bytes)

    return {
        "filename": pdf_file.filename,
        "size_bytes": len(pdf_bytes),
        "pages": pages,
        "ai_res": ai_res,
    }

