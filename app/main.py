import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.classifier import classify_message, detect_intent
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


def _keyword_organize_fallback(message: str) -> bool:
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


def _build_organize_response(message: str) -> dict:
    result = organize_existing_tasks(message)
    details = (
        f"(solicitadas: {result.get('requested', 0)}, "
        f"falhas: {result.get('failed', 0)}, "
        f"status: {'ok' if result.get('supports_status') else 'não'}, "
        f"ordem: {'ok' if result.get('supports_order') else 'não'})"
    )

    message_text = result["summary"]
    if result.get("updated", 0) == 0:
        message_text = f"{result['summary']} Nenhuma tarefa foi alterada {details}."

    return {
        "duplicate": False,
        "type": "task",
        "title": f"Tarefas organizadas ({result['updated']} atualizadas)",
        "message": message_text,
    }


def _raise_external_service_error(error: requests.HTTPError):
    status = error.response.status_code if error.response is not None else None
    if status in {429, 500, 502, 503, 504}:
        raise HTTPException(
            status_code=503,
            detail="Notion está indisponível no momento. Tente novamente em alguns segundos.",
        )
    raise HTTPException(status_code=502, detail=f"Erro na API do Notion (status {status}).")

@app.get("/")
def root():
    return {"status": "online", "message": "Personal Assistant API"}


@app.post("/organize-tasks")
def organize_tasks(request: MessageRequest):
    try:
        return _build_organize_response(request.message)
    except requests.HTTPError as error:
        _raise_external_service_error(error)
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
def process_message(request: MessageRequest):
    try:
        intent = None
        try:
            intent = detect_intent(request.message)
        except Exception:
            intent = None

        if intent and intent.intent == "organize_tasks":
            return _build_organize_response(request.message)

        if intent is None and _keyword_organize_fallback(request.message):
            return _build_organize_response(request.message)

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
    except requests.HTTPError as error:
        _raise_external_service_error(error)
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))