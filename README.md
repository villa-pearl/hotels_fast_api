# Hotel Price PDF Analyzer

FastAPI-приложение: загружает PDF прайс-листа отеля, парсит через LlamaParse и извлекает таблицу цен с помощью Gemini.

## Деплой на Render.com

### Вариант A — Blueprint (`render.yaml`)

1. Залейте содержимое папки `v1` в Git-репозиторий (корень сервиса = эти файлы).
2. На [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Подключите репозиторий — Render прочитает `render.yaml`.
4. Задайте секреты (синхронизация `sync: false`):
   - `GEMINI_API_KEY`
   - `LLAMA_CLOUD_API_KEY`
5. Дождитесь деплоя. URL вида `https://hotel-price-pdf-analyzer.onrender.com`.

### Вариант B — вручную (Web Service)

1. **New** → **Web Service** → подключите репозиторий.
2. Settings:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
3. **Environment** → добавьте `GEMINI_API_KEY` и `LLAMA_CLOUD_API_KEY`.
4. Deploy.

### Важно про таймауты

Обработка PDF (LlamaParse + Gemini) может занимать минуты. На **Free** плане Render запросы часто обрываются по таймауту (~30–100 с). 
Для стабильной работы лучше **Starter** или выше.

Free-инстанс «засыпает» без трафика — первый запрос после простоя может идти дольше.

## Локальный запуск

```bash
cp .env.example .env
# заполните ключи

pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Веб-форма загрузки PDF |
| GET | `/health` | Health-check для Render |
| POST | `/upload` | Загрузка `pdf_file`, ответ JSON с `ai_res` |
