from google import genai
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class ClassificationOutput(BaseModel):
    type: str
    title: str
    content: str
    priority: str

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    result = ClassificationOutput.model_validate_json(response.text)
    return result