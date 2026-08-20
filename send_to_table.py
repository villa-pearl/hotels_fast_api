import os
from datetime import datetime, timezone

import requests

BASEROW_URL = "https://api.baserow.io"
TABLE_ID = 1144738


def add_baserow_record(
    ip_address: str,
    file_name: str,
    description: str,
):
    token = os.environ.get("BASE_TABLE_API_KEY")
    if not token:
        raise RuntimeError(
            "Не задан BASE_TABLE_API_KEY. "
            "Добавьте Environment Variable на Render или в локальный .env."
        )

    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_ID}/?user_field_names=true"

    data = {
        "date_add": datetime.now(timezone.utc).isoformat(),
        "ip_adress": ip_address,
        "file_name": file_name,
        "description": description,
    }

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=10,
    )

    #    response.raise_for_status()

    print(response.status_code)
    print(response.text)
    #    return response.json()


# add_baserow_record()
