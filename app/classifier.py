from groq import Groq
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class ClassificationOutput(BaseModel):
    type: str
    title: str
    content: str
    priority: str

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