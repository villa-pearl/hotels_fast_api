import json
import os
from openai import OpenAI
from datetime import datetime
import time


def get_result(llama_json):
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

На вход ты получаешь JSON после LlamaParse.

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

Ответ верни результат по номерам в виде текстовой таблицы: это набор строк с разделителями между ячейками tab "	".

Пример таблицы:
Название номера  | Период 1 с ... по | Период 2 с ... по | Период 3 с ... по |
Название_Номера1 | Стоимость1        | Стоимость2        | Стоимость2        |
Название_Номера2 | Стоимость3        | Стоимость4        | Стоимость2        |

Требования:
- Не используй JSON.
- Не используй Markdown-блоки с тройными обратными кавычками.
- Каждая строка должна быть отдельной строкой.
- Разделитель между колонками — символ tab "	".
- Верни только таблицу без дополнительных пояснений.

- Разделитель между колонками — символ tab "	".

Документ:

{json.dumps(llama_json, ensure_ascii=False)}

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
