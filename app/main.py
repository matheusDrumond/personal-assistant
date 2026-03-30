import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.classifier import classify_message
from app.notion import save_to_notion
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
def root():
    return {"status": "online", "message": "Personal Assistant API"}

@app.post("/process")
def process_message(request: MessageRequest):
    try:
        print(f"Message received: {request.message}")
        classification = classify_message(request.message)
        print(f"Classification: {classification}")
        url = save_to_notion(classification)
        return {
            "type": classification.type,
            "title": classification.title,
            "priority": classification.priority,
            "notion_url": url
        }
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))