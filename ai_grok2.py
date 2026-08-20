import base64
import io
import os

import fitz
from openai import OpenAI
from openpyxl import Workbook
from PIL import Image

PROMPT = """
Ты — эксперт по анализу прайс-листов отелей.

Извлекай только указанные данные

Извлеки:

- название отеля
- категория отеля
- валюту документа

Для каждого номера извлеки:

- название и тип номера
- цену проживания в номере по периодам с датами
- если период проживания указан не в виде даты, а в виде названия периода - смотри дополнилнительные данные 
  где указаны названия периодов и указание дат

Обрати внимание, что полное название номера может быть составным, в предыдущей строке может быть общее название для группы номеров.

Обрати внимание, что кроме названий номеров отдельной строкой могут быть указаны другие отдельные элементы, 
например "Sofa Bed", "Setup Charge", "Extra bed".
Такие элементы нужно пропускать.
То есть нужно подумать - похоже ли это на название номера, или это дополнительные кровати, или оплаты.
 
Если поле отсутствует — null.

Ничего не придумывай.

Требования:
- Не используй Markdown-блоки с тройными обратными кавычками.
- Каждая строка должна быть отдельной строкой.
- Разделитель между колонками — символ tab "	".
- Верни только таблицу без дополнительных пояснений.
- В итоговой таблице должны быть названия колонок на английском языке.

"""

MAX_PAGES = 3


def _pdf_to_stitched_png(pdf_bytes: bytes) -> bytes:
    """Рендерит первые страницы PDF и склеивает их в одно PNG."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        print("Количество страниц:", len(doc))

        images = []
        for page_number in range(min(len(doc), MAX_PAGES)):
            print("Page:", page_number + 1)
            page = doc[page_number]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(image.copy())
    finally:
        doc.close()

    if not images:
        raise ValueError("PDF не содержит страниц")

    width = max(image.width for image in images)
    height = sum(image.height for image in images)
    big_img = Image.new("RGB", (width, height), "white")

    y = 0
    for image in images:
        big_img.paste(image, (0, y))
        y += image.height

    buffer = io.BytesIO()
    big_img.save(buffer, format="PNG")
    return buffer.getvalue()


def _tsv_to_xlsx_bytes(text_result: str) -> bytes:
    """Преобразует TSV-ответ модели в байты XLSX."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Hotel prices"

    for line in text_result.splitlines():
        if not line.strip():
            continue
        ws.append(line.split("\t"))

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def get_result(pdf_bytes: bytes) -> bytes:
    """
    Принимает загруженный PDF (байты), отправляет страницы в Grok
    и возвращает сформированный XLSX (байты) для скачивания.
    """
    api_key = os.environ.get("GROK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Не задан GROK_API_KEY. "
            "Добавьте Environment Variable на Render или в локальный .env."
        )

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )

    image_bytes = _pdf_to_stitched_png(pdf_bytes)
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    print("Send to Grok")
    response = client.responses.create(
        model="grok-4.5",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{image_base64}",
                        "detail": "high",
                    },
                    {
                        "type": "input_text",
                        "text": PROMPT,
                    },
                ],
            }
        ],
    )

    text_result = response.output_text or ""
    print(text_result)

    return _tsv_to_xlsx_bytes(text_result)
