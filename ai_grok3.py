import base64
import io
import os

import fitz
from openai import OpenAI
from openpyxl import Workbook

PROMPT = """
Ты — эксперт по анализу прайс-листов отелей.

Извлекай только указанные данные

Извлеки:

- название отеля

Для каждого номера извлеки:

- название и тип номера
- цену проживания в номере по периодам с датами
- если период проживания указан не в виде даты, а в виде названия периода - смотри дополнилнительные данные 
  где указаны названия периодов и указание дат
- Размещай начало и конец периода в разные колонки
- цену дополнительной кровати

Обрати внимание, что полное название номера может быть составным, в предыдущей строке может быть общее название для группы номеров.

То есть нужно подумать - похоже ли это на название номера, или это дополнительные кровати, или оплаты.
 
Если поле отсутствует — null.

Ничего не придумывай.

Требования:
- Не используй Markdown-блоки с тройными обратными кавычками.
- Каждая строка должна быть отдельной строкой.
- Разделитель между колонками — символ tab "	".
- Размещай начало и конец периода в разные колонки.
- Порядок названий номеров оставляй как есть, а внутри номеров сортируй даты начала периода.
- Верни только таблицу без дополнительных пояснений.
- Удаляй точки и запятые в разделителях в ценах номеров, если это НЕ разделить целой и дробной части. Тогда оставляй!
- В итоговой таблице должны быть названия колонок на английском языке.

Отдельно таблицей дополнительно извлеки стомость проживания в формате ключ-значение (в качестве значения - число):
- стоимость проживания ребенка возраст от 0 до 2 лет
- стоимость проживания ребенка возраст от 2 до 6 лет
- стоимость проживания ребенка возраст от 6 до 12 лет
- стоимость проживания ребенка возраст старше 12 лет

Пример этой таблицы:
Child age 0-2 years	0
Child age 2-6 years	0
Child age 6-12 years	250000
Child age over 12 years	500000


Отдельно таблицей дополнительно извлеки данные в виде ключ-значение:
- валюта
- входит ли VAT в стоимость номеров
- к чему относится документ (контракт или спец предложение)
- если это спец предложение, то условия предоставления акции (период бронирования/продолжительность проживания и др)
- базовый тип питания, на основе которого представлен прайс
- минимальное проживание и периоды действия ограничения на заезд/выезд

Отдельно таблицей дополнительно извлеки данные:
- условия и доплаты за праздничные дни и доп питание 
- отдельно раздели периоды праздничных дней


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

    return _tsv_to_xlsx_bytes(text_result)
