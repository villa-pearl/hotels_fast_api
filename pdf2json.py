import fitz
import json


def get_json(doc):
    pages_json = []

    for page_num, page in enumerate(doc, start=1):
        page_json = {
            "page": page_num,
            "width": round(page.rect.width, 2),
            "height": round(page.rect.height, 2),
            "lines": []
        }

        page_dict = page.get_text("dict")

        for block in page_dict["blocks"]:

            # только текстовые блоки
            if block["type"] != 0:
                continue

            for line in block["lines"]:

                # объединяем все spans в одну строку
                text = "".join(span["text"] for span in line["spans"]).strip()

                if text == "":
                    continue

                page_json["lines"].append({
                    "text": text,
                    "bbox": [round(v, 2) for v in line["bbox"]]
                })

        pages_json.append(page_json)

    return pages_json
