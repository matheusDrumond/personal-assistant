import os
import requests
from dotenv import load_dotenv
from app.classifier import ClassificationOutput
import json

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_TASKS_ID = os.getenv("NOTION_TASKS_ID")
NOTION_NOTES_ID = os.getenv("NOTION_NOTES_ID")
NOTION_INBOX_ID = os.getenv("NOTION_INBOX_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

DATABASE_MAP = {
    "task": NOTION_TASKS_ID,
    "note": NOTION_NOTES_ID,
    "inbox": NOTION_INBOX_ID
}

def save_to_notion(classification: ClassificationOutput) -> str:
    database_id = DATABASE_MAP.get(classification.type)

    if not database_id:
        raise ValueError(f"Tipo inválido: {classification.type}")
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {
                "title": [{"text": {"content": classification.title}}]
            },
            "Priority": {
                "select": {"name": classification.priority}
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": classification.content}}]
                }
            }
        ]
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json=payload
    )
    print(response.status_code)
    print(response.text)

    response.raise_for_status()
    return response.json().get("url")