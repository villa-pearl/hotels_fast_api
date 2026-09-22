import base64
import io
import os

import fitz
from openai import OpenAI

PROMPT = """
Ты — эксперт по анализу прайс-листов отелей.


Извлеки:

- название отеля
- страну отеля
- город
- Букинг код
- Тип документа - Контракт или Специальное предложение
- Глобальные сроки действия документа
- Сроки бронирования

В ответе  Не используй разметку Markdown
Используй простой текст

"""


def _pdf_to_png_pages(pdf_bytes: bytes) -> list[bytes]:
    """Рендерит все страницы PDF в отдельные PNG (по одному изображению на страницу)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        print("Количество страниц:", len(doc))
        if len(doc) == 0:
            raise ValueError("PDF не содержит страниц")

        pages_png: list[bytes] = []
        for page_number in range(len(doc)):
            print("Page:", page_number + 1)
            page = doc[page_number]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pages_png.append(pix.tobytes("png"))
        return pages_png
    finally:
        doc.close()


def get_result(pdf_bytes: bytes) -> bytes:
    """
    Принимает загруженный PDF (байты), отправляет все страницы как
    отдельные изображения в Grok и возвращает сформированный XLSX (байты).
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

    pages_png = _pdf_to_png_pages(pdf_bytes)

    content = []
    for image_bytes in pages_png:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{image_base64}",
                "detail": "high",
            }
        )

    content.append(
        {
            "type": "input_text",
            "text": PROMPT,
        }
    )

    print(f"Send to Grok: {len(pages_png)} image(s)")
    response = client.responses.create(
        model="grok-4.5",
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    text_result = response.output_text or ""
    print(text_result)

    return text_result
