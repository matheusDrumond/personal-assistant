from groq import Groq
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

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

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
    
    result = ClassificationOutput.model_validate_json(response.choices[0].message.content)
    return result


def generate_task_organization_plan(message: str, tasks: list[dict]) -> TaskOrganizationPlan:
        prompt = f"""
        You are a personal productivity assistant.

        The user asked you to organize their existing tasks.
        You must ONLY return updates for existing tasks. Do not create new tasks.

        Current tasks (1-based index):
        {tasks}

        User request:
        {message}

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
        - Keep updates minimal and practical for today.
        - Use Portuguese for summary.
        - Return JSON only, without markdown.
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

        return TaskOrganizationPlan.model_validate_json(response.choices[0].message.content)