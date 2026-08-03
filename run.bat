@echo off
REM Локальный запуск. Ключи: GEMINI_API_KEY и LLAMA_CLOUD_API_KEY в .env

uvicorn app:app --reload --host 0.0.0.0 --port 8000
