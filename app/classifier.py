from groq import Groq
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
import json

load_dotenv()

class ClassificationOutput(BaseModel):
    type: str
    title: str
    content: str
    priority: str


class TaskOrganizationUpdate(BaseModel):
    task_index: int
    priority: Optional[str] = None
    status: Optional[str] = None
    order: Optional[int] = None


class TaskOrganizationPlan(BaseModel):
    summary: str
    updates: list[TaskOrganizationUpdate]


class IntentOutput(BaseModel):
    intent: str
    confidence: Optional[float] = None

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _extract_json_payload(raw_text: str) -> str:
    text = raw_text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    return text


def _validate_model_from_llm(model_cls, raw_text: str):
    payload = _extract_json_payload(raw_text)
    try:
        return model_cls.model_validate_json(payload)
    except Exception:
        parsed = json.loads(payload)
        return model_cls.model_validate(parsed)

def classify_message(message: str) -> ClassificationOutput:
    prompt = f"""
    You are a personal organization assistant.
    
    Analyze the message below and return a JSON with exactly this structure:
    {{
        "type": "task" | "note" | "inbox",
        "title": "short and direct title",
        "content": "full organized content",
        "priority": "high" | "medium" | "low"
    }}
    
    Rules:
    - "task": something that needs to be done, has a clear action
    - "note": idea, thought, information to save
    - "inbox": email or message that needs a reply
    
    Return ONLY the JSON, no explanations, no markdown.
    
    Message: {message}
    """
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=1024
    )
    
    result = _validate_model_from_llm(ClassificationOutput, response.choices[0].message.content)
    return result


def detect_intent(message: str) -> IntentOutput:
    prompt = f"""
    You are an intent classifier for a personal assistant.

    Classify the message into ONE intent:
    - "organize_tasks": user asks to organize, reprioritize, reorder, or update statuses of existing tasks.
    - "capture_item": any other message that should be stored as task/note/inbox.

    Return ONLY JSON in this exact format:
    {{
      "intent": "organize_tasks" | "capture_item",
      "confidence": 0.0
    }}

    Message: {message}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.0,
        max_tokens=120
    )

    result = _validate_model_from_llm(IntentOutput, response.choices[0].message.content)
    normalized = result.intent.strip().lower()
    if normalized not in {"organize_tasks", "capture_item"}:
        normalized = "capture_item"
    result.intent = normalized
    return result


def generate_task_organization_plan(
    message: str,
    tasks: list[dict],
    supports_status: bool,
    supports_order: bool,
    force_updates: bool = False,
) -> TaskOrganizationPlan:
    force_rule = ""
    if force_updates:
        force_rule = "- You MUST include at least 1 update when there are tasks available.\\n"

    prompt = f"""
    You are a personal productivity assistant.

    The user asked you to organize their existing tasks.
    You must ONLY return updates for existing tasks. Do not create new tasks.

    Current tasks (1-based index):
    {tasks}

    User request:
    {message}

    Database capabilities:
    - supports_status: {supports_status}
    - supports_order: {supports_order}

    Return ONLY a valid JSON with this exact structure:
    {{
        "summary": "short summary in Portuguese",
        "updates": [
            {{
                "task_index": 1,
                "priority": "high" | "medium" | "low" | null,
                "status": "status text" | null,
                "order": 1 | null
            }}
        ]
    }}

    Rules:
    - task_index must reference only items in the provided list.
    - Include only tasks that should change.
    - If supports_status is false, set status as null.
    - If supports_order is false, set order as null.
    - Always prioritize using priority updates when status/order are unavailable.
    - Keep updates minimal and practical for today.
    - Use Portuguese for summary.
    - Return JSON only, without markdown.
    {force_rule}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=1024
    )

    return _validate_model_from_llm(TaskOrganizationPlan, response.choices[0].message.content)