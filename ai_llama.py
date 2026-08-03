import os
import tempfile
from llama_parse import LlamaParse


def get_llama_from_pdf(pdf_bytes: bytes):
    """Принимает байты PDF, возвращает JSON-результат LlamaParse (list/dict)."""

    api_key = os.environ.get("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Не задан LLAMA_CLOUD_API_KEY. "
            "Добавьте Environment Variable на Render или в локальный .env."
        )

    os.environ["LLAMA_CLOUD_API_KEY"] = api_key

    parser = LlamaParse(
        result_type="json",
        verbose=True,
    )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        return parser.get_json_result(tmp_path)
    finally:
        os.unlink(tmp_path)
