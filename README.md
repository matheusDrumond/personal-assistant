# Personal Assistant

An AI-powered personal assistant API that receives messages in natural language, automatically classifies the content type, and organizes everything in Notion — no friction, no switching between apps.

Built from scratch with a real understanding of every technical decision: from API structure to LLM integration and external service communication.

## The Problem

Tasks scattered across notes apps, ideas lost in chat messages, emails to reply forgotten. The lack of a centralized system causes important information to slip through the cracks every day.

## The Solution

Send a message describing anything — a task, an idea, an email you need to reply to — and the system classifies, structures, and automatically saves it to the right Notion database. Before saving, it checks if a similar item already exists to avoid duplicates.

**Example:**

```
Input: "need to study RAG concepts before the interview on Friday"

Output: saved to Tasks with title "Study RAG concepts", priority "medium"
```

```
Input: "study RAG before Friday" (sent again)

Output: similar item already exists — returns link to existing Notion entry
```

## Architecture

```
Request (message)
       ↓
ChromaDB (check for similar items)
       ↓
  duplicate? → return existing Notion link
       ↓
Gemini (classify + structure)
       ↓
Notion API (save) + ChromaDB (store embedding)
       ↑
React Frontend
```

Four components with separated responsibilities:

- **`app/main.py`** — receives and validates requests, configures CORS, orchestrates the flow
- **`app/classifier.py`** — classification logic with Gemini and Pydantic validation
- **`app/notion.py`** — Notion API integration
- **`app/memory.py`** — RAG memory layer with ChromaDB and sentence-transformers

## Technical Decisions

**FastAPI** was chosen for its straightforward endpoint structure, automatic input validation with Pydantic, and auto-generated Swagger documentation.

**Pydantic v2** to validate Gemini's output: if the model returns a field with the wrong type or missing entirely, the system raises an error immediately instead of silently propagating invalid data through the pipeline.

**Gemini Flash** for its generous free tier and quality sufficient for text classification — heavier models would be a waste of cost for this task.

**Notion** for its simple REST API, native support for structured databases, and a visual interface that end users can customize without touching the code.

**ChromaDB + sentence-transformers** for the RAG memory layer: instead of exact string matching, the system uses semantic embeddings to detect similar messages regardless of how they're phrased. This prevents duplicate entries in Notion.

**React + Vite** for the frontend due to fast development experience and optimized builds. CORS configured on the API to accept requests from the local frontend.

## Stack

**Backend**
- Python 3.13
- FastAPI + Uvicorn
- Pydantic v2
- Google Gemini API (`google-genai`)
- Notion API
- ChromaDB
- sentence-transformers (`all-MiniLM-L6-v2`)
- python-dotenv

**Frontend**
- React 19
- Vite
- Plain CSS

## Prerequisites

- Python 3.10+
- Node.js 18+
- Google AI Studio account (free)
- Notion account (free)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/matheusDrumond/personal-assistant
cd personal-assistant
```

### 2. Set up the backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_key
NOTION_TOKEN=your_integration_token
NOTION_TASKS_ID=your_tasks_database_id
NOTION_NOTES_ID=your_notes_database_id
NOTION_INBOX_ID=your_inbox_database_id
```

### 3. Set up Gemini

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Click **"Get API Key"**
3. Copy the key and add it to `.env`

### 4. Set up Notion

**Create the integration:**
1. Go to [notion.so/my-integrations](https://notion.so/my-integrations)
2. Click **"New integration"**
3. Name it `personal-assistant`
4. Copy the **"Internal Integration Token"** and add it to `.env`

**Create the databases:**
1. Create a Notion page called **"Personal Assistant"**
2. Inside it, create three **Table** databases:
   - `Tasks`
   - `Notes`
   - `Inbox`
3. In each database, add a property called **"Priority"** of type **Select** with options: `high`, `medium`, `low`

**Connect the integration:**
1. Open each database
2. Click **"..."** in the top right corner
3. Go to **"Connections"** and add `personal-assistant`

**Get the database IDs:**
1. Open each database as a full page
2. Copy the link — the ID is the sequence after the last `/` and before `?`
3. Add each ID to `.env`

### 5. Set up the frontend

```bash
cd frontend
npm install
```

## Running

**Backend** (from the project root):

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`  
Swagger docs at `http://localhost:8000/docs`

**Frontend** (from the `frontend` folder):

```bash
npm run dev
```

Interface available at `http://localhost:5173`

## Usage

### Via web interface

Go to `http://localhost:5173`, type your message and click Send. The result appears with a direct link to Notion. If a similar item already exists, you'll see a warning with a link to the existing entry.

### Via API

`POST /process`

```json
{
  "message": "call the client tomorrow at 10am to close the contract"
}
```

New item response:

```json
{
  "duplicate": false,
  "type": "task",
  "title": "Call client to close contract",
  "priority": "high",
  "notion_url": "https://notion.so/..."
}
```

Duplicate detected response:

```json
{
  "duplicate": true,
  "message": "Similar item already exists.",
  "existing": "call the client tomorrow at 10am to close the contract",
  "notion_url": "https://notion.so/..."
}
```

## Supported Types

| Type | When it's used | Notion Database |
|------|---------------|-----------------|
| `task` | Something that needs to be done, has a clear action | Tasks |
| `note` | Idea, insight, information to save | Notes |
| `inbox` | Email or message that needs a reply | Inbox |

## Project Structure

```
personal-assistant/
├── app/
│   ├── main.py          # FastAPI — endpoints, CORS, flow orchestration
│   ├── classifier.py    # Gemini integration and Pydantic validation
│   ├── notion.py        # Notion API integration
│   └── memory.py        # RAG memory layer — ChromaDB + embeddings
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Main component
│   │   ├── App.css      # Styles
│   │   └── constants.js # UI constants
│   └── package.json
├── requirements.txt
├── .env.example
└── README.md
```

## Roadmap

- WhatsApp integration via Evolution API
- Date and deadline support for tasks
- Message history log
- Production deploy (Railway + Vercel)
