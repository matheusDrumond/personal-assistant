import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.classifier import classify_message
from app.notion import save_to_notion, organize_existing_tasks
from fastapi.middleware.cors import CORSMiddleware
from app.memory import add_to_memory, search_similar

load_dotenv()

app = FastAPI(title="Personal Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    message: str


def _is_organize_tasks_request(message: str) -> bool:
    text = message.lower()
    keywords = [
        "organizar tarefas",
        "organize tasks",
        "priorizar tarefas",
        "prioritize tasks",
        "reordenar tarefas",
        "ordenar tarefas",
        "mais urgentes",
        "tarefas do dia",
        "lista de tarefas",
    ]
    return any(keyword in text for keyword in keywords)

@app.get("/")
def root():
    return {"status": "online", "message": "Personal Assistant API"}

@app.post("/process")
def process_message(request: MessageRequest):
    try:
        if _is_organize_tasks_request(request.message):
            result = organize_existing_tasks(request.message)
            return {
                "duplicate": False,
                "type": "task",
                "title": f"Tarefas organizadas ({result['updated']} atualizadas)",
                "message": result["summary"],
            }

        similar = search_similar(request.message)
        
        if similar:
            return {
                "duplicate": True,
                "message": "Similar item already exists.",
                "existing": similar["text"],
                "notion": similar["notion"]
            }

        classification = classify_message(request.message)

        url = save_to_notion(classification)

        add_to_memory(message_id=url, text=request.message, url=url)
        return {
            "duplicate": False,
            "type": classification.type,
            "title": classification.title,
            "priority": classification.priority,
            "notion_url": url
        }
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))