import os
import requests
import time
from dotenv import load_dotenv
from app.classifier import ClassificationOutput, generate_task_organization_plan
from typing import Optional

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

NOTION_TIMEOUT_SECONDS = 20
NOTION_MAX_RETRIES = 3


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {429, 500, 502, 503, 504}


def _notion_request(method: str, url: str, payload: Optional[dict] = None) -> dict:
    for attempt in range(NOTION_MAX_RETRIES + 1):
        try:
            response = requests.request(
                method,
                url,
                headers=HEADERS,
                json=payload,
                timeout=NOTION_TIMEOUT_SECONDS,
            )

            if _is_retryable_status(response.status_code) and attempt < NOTION_MAX_RETRIES:
                time.sleep(0.5 * (attempt + 1))
                continue

            response.raise_for_status()
            return response.json()
        except (requests.Timeout, requests.ConnectionError):
            if attempt < NOTION_MAX_RETRIES:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise


def _notion_get(url: str) -> dict:
    return _notion_request("GET", url)


def _notion_post(url: str, payload: dict) -> dict:
    return _notion_request("POST", url, payload)


def _notion_patch(url: str, payload: dict) -> dict:
    return _notion_request("PATCH", url, payload)


def _detect_tasks_schema(database_schema: dict) -> dict:
    properties = database_schema.get("properties", {})
    title_property = None
    priority_property = None
    status_property = None
    order_property = None

    for name, data in properties.items():
        property_type = data.get("type")
        lower_name = name.lower()

        if property_type == "title" and not title_property:
            title_property = name

        if not priority_property and lower_name == "priority" and property_type == "select":
            priority_property = name

        if not priority_property and property_type == "select":
            options = [opt.get("name", "").lower() for opt in data.get("select", {}).get("options", [])]
            if all(level in options for level in ["high", "medium", "low"]):
                priority_property = name

        if not status_property and lower_name == "status" and property_type in {"status", "select"}:
            status_property = name

        if not status_property and property_type == "status":
            status_property = name

        if (
            not order_property
            and lower_name in {"order", "ordem", "position", "posição"}
            and property_type == "number"
        ):
            order_property = name

    if not title_property:
        raise ValueError("Não foi possível identificar o campo de título no banco de Tasks.")

    return {
        "title": title_property,
        "priority": priority_property,
        "status": status_property,
        "order": order_property,
    }


def _read_property_text(page: dict, property_name: str, property_type: str) -> Optional[str]:
    prop = page.get("properties", {}).get(property_name, {})
    if property_type == "title":
        title_chunks = prop.get("title", [])
        return "".join(chunk.get("plain_text", "") for chunk in title_chunks).strip() or None
    if property_type == "rich_text":
        text_chunks = prop.get("rich_text", [])
        return "".join(chunk.get("plain_text", "") for chunk in text_chunks).strip() or None
    return None


def _read_select_name(page: dict, property_name: str, property_type: str) -> Optional[str]:
    prop = page.get("properties", {}).get(property_name, {})
    if property_type == "select":
        selected = prop.get("select")
        return selected.get("name") if selected else None
    if property_type == "status":
        selected = prop.get("status")
        return selected.get("name") if selected else None
    return None


def _get_tasks_schema() -> tuple[dict, dict]:
    database = _notion_get(f"https://api.notion.com/v1/databases/{NOTION_TASKS_ID}")
    schema_map = _detect_tasks_schema(database)
    return database.get("properties", {}), schema_map


def list_tasks_for_organization(limit: int = 50) -> tuple[list[dict], dict, dict]:
    properties, schema_map = _get_tasks_schema()

    payload = {
        "page_size": limit,
        "sorts": [
            {"timestamp": "last_edited_time", "direction": "descending"}
        ]
    }
    result = _notion_post(
        f"https://api.notion.com/v1/databases/{NOTION_TASKS_ID}/query",
        payload,
    )

    tasks = []
    for page in result.get("results", []):
        title_name = schema_map["title"]
        title_type = properties[title_name]["type"]
        title = _read_property_text(page, title_name, title_type) or "Sem título"

        priority = None
        if schema_map["priority"]:
            priority_name = schema_map["priority"]
            priority_type = properties[priority_name]["type"]
            priority = _read_select_name(page, priority_name, priority_type)

        status = None
        if schema_map["status"]:
            status_name = schema_map["status"]
            status_type = properties[status_name]["type"]
            status = _read_select_name(page, status_name, status_type)

        order = None
        if schema_map["order"]:
            order_value = page.get("properties", {}).get(schema_map["order"], {}).get("number")
            order = order_value

        tasks.append(
            {
                "page_id": page.get("id"),
                "title": title,
                "priority": priority,
                "status": status,
                "order": order,
                "notion_url": page.get("url"),
            }
        )

    return tasks, properties, schema_map


def _build_property_payload(
    properties: dict,
    schema_map: dict,
    current_task: dict,
    new_priority: Optional[str],
    new_status: Optional[str],
    new_order: Optional[int],
) -> dict:
    update_properties = {}

    if schema_map.get("priority") and new_priority:
        normalized = new_priority.lower().strip()
        if normalized in {"high", "medium", "low"} and (current_task.get("priority") or "").lower() != normalized:
            priority_name = schema_map["priority"]
            update_properties[priority_name] = {"select": {"name": normalized}}

    if schema_map.get("status") and new_status:
        status_name = schema_map["status"]
        status_type = properties[status_name]["type"]
        if (current_task.get("status") or "").lower() != new_status.strip().lower():
            if status_type == "status":
                update_properties[status_name] = {"status": {"name": new_status.strip()}}
            elif status_type == "select":
                update_properties[status_name] = {"select": {"name": new_status.strip()}}

    if schema_map.get("order") and new_order is not None and current_task.get("order") != new_order:
        order_name = schema_map["order"]
        update_properties[order_name] = {"number": new_order}

    return update_properties


def organize_existing_tasks(message: str) -> dict:
    tasks, properties, schema_map = list_tasks_for_organization(limit=50)
    supports_status = schema_map.get("status") is not None
    supports_order = schema_map.get("order") is not None

    if not tasks:
        return {
            "updated": 0,
            "requested": 0,
            "summary": "Nenhuma tarefa encontrada para organizar.",
        }

    ai_tasks = []
    for index, task in enumerate(tasks, start=1):
        ai_tasks.append(
            {
                "index": index,
                "title": task["title"],
                "priority": task.get("priority"),
                "status": task.get("status"),
                "order": task.get("order"),
            }
        )

    plan = generate_task_organization_plan(
        message=message,
        tasks=ai_tasks,
        supports_status=supports_status,
        supports_order=supports_order,
    )

    # If the first plan is empty, ask for at least one practical priority/status/order change.
    if len(plan.updates) == 0 and len(tasks) > 0:
        plan = generate_task_organization_plan(
            message=message,
            tasks=ai_tasks,
            supports_status=supports_status,
            supports_order=supports_order,
            force_updates=True,
        )

    updated_count = 0
    failed_count = 0
    for update in plan.updates:
        idx = update.task_index - 1
        if idx < 0 or idx >= len(tasks):
            continue

        current_task = tasks[idx]
        payload_properties = _build_property_payload(
            properties=properties,
            schema_map=schema_map,
            current_task=current_task,
            new_priority=update.priority,
            new_status=update.status,
            new_order=update.order,
        )

        if not payload_properties:
            continue

        try:
            _notion_patch(
                f"https://api.notion.com/v1/pages/{current_task['page_id']}",
                {"properties": payload_properties},
            )
            updated_count += 1
        except requests.HTTPError:
            failed_count += 1

    return {
        "updated": updated_count,
        "failed": failed_count,
        "requested": len(plan.updates),
        "summary": plan.summary,
        "supports_order": supports_order,
        "supports_status": supports_status,
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
    response_json = _notion_post("https://api.notion.com/v1/pages", payload)
    return response_json.get("url")