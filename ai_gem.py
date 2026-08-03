import json
import os
from google import genai
from google.genai import types
from datetime import datetime
import time


def get_result(llama_json):
    """Принимает уже распарсенный JSON от LlamaParse (list/dict)."""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Не задан GEMINI_API_KEY. "
            "Добавьте Environment Variable на Render или в локальный .env."
        )

    client = genai.Client(api_key=api_key)

    print("get_gem_result start")

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

Ответ верни результат по номерам в виде текстовой таблицы: это набор строк с разделителями между ячейками табуляция "	".

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

Документ:

{json.dumps(llama_json, ensure_ascii=False)}

"""

    start_time = datetime.now()
    print(f"Время начала: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    start_perf = time.perf_counter()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="text/plain"
        )
    )

    end_perf = time.perf_counter()
    print(response.text)

    duration = end_perf - start_perf
    print(f"Время ожидания ответа: {duration:.2f} сек.")

    return response.text

# response.text уже содержит JSON
#result = json.loads(response.text)

#with open("hotel_result.json", "w", encoding="utf-8") as f:
#    json.dump(result, f, indent=4, ensure_ascii=False)

#with open("response.txt", "w", encoding="utf-8") as f:
#    f.write(response.text)


