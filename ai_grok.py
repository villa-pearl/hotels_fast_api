import json
import os
from openai import OpenAI
from datetime import datetime
import time


example_json = '''
{
  "prices": [
    {
      "price": "2,650,000",
      "room": "Family Wing Deluxe (39 sqm)",
      "headrs": ["HIGH SEASON", "1/1 - 31/8/2026", "1/11 - 31/12/2026","FIT<10 rooms","GIT"]
    },
    {
      "price": "2,250,000",
      "room": "Junior Rustic Elegance Suite",
      "headrs": ["LOW SEASON", "1/1 - 31/8/2026", "1/11 - 31/12/2026","FIT<10 rooms"]
    },
  ]
}
'''



def get_result(pdf_json):
    """Принимает уже распарсенный JSON от LlamaParse (list/dict)."""

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


    prompt = f"""
Ты — эксперт по анализу прайс-листов отелей.

На вход ты получаешь JSON после PyMuPDF.
Координаты блоков текста в формате bbox = [x0, y0, x1, y1] 

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

Цены находятся внутри таблицы.
Алгоритм такой: находи текст с ценой, затем извлекай текст который в самой левой колонки (это название номера отеля)по совпадении координат y0 и y1
Потом двигайся вверх, извлекай текст, который находится в верхних строках таблицы, там указывается период и признак периода FIT/GIT.
У одной цены может быть несколько заколовков в таблице, смотри по пересечению координат x0 и x1


Пример ответа:

{example_json}

Кроме интервалов времени, могут быть разделение цен по элементам "FIT" и "GIT"
Если такоего разделения нет, не указывай

Документ:

{json.dumps(pdf_json, ensure_ascii=False)}
"""


    start_time = datetime.now()
    print(f"Время начала: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    start_perf = time.perf_counter()

    response = client.chat.completions.create(
        model="grok-4-1-fast-non-reasoning",
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    end_perf = time.perf_counter()
    content = response.choices[0].message.content or ""
    print(content)

    duration = end_perf - start_perf
    print(f"Время ожидания ответа: {duration:.2f} сек.")

    return content
