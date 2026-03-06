"""
main.py — FastAPI Server
=========================
WHY THIS FILE EXISTS:
This is the HTTP API that connects the frontend to the agent pipeline.
It exposes three main endpoints:

1. POST /api/research — Starts a new research pipeline
   - Accepts a JSON body with { "query": "..." }
   - Returns Server-Sent Events (SSE) with agent progress
   - WHY SSE: The pipeline takes 30-60 seconds. Without streaming,
     the user sees nothing for a minute. SSE pushes real-time updates
     like "Planner is thinking..." → "Searching for sources..." etc.

2. GET /api/history — Returns past research tasks
   - Used by the history sidebar in the frontend
   - Returns only metadata (query, status, date) for performance

3. GET /api/research/{id} — Returns a specific research report
   - Used when clicking a history item to view the full report
   - Returns ALL data including the full Markdown report

WHY FastAPI (not Flask/Django):
- Native async support (crucial for SSE streaming)
- Automatic OpenAPI docs (visit /docs for interactive API testing)
- Pydantic validation (catches bad requests before they hit our code)
- High performance (built on Starlette/Uvicorn)
"""

import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.crew import run_research
from backend.config import get_supabase_client


# ─── Authentication ───────────────────────────────────────────
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Validates the Supabase JWT token sent from the frontend.
    Returns the user's data (including user_id) and the token string.
    Raises 401 Unauthorized if the token is invalid or missing.
    """
    token = credentials.credentials
    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid auth token")
        return user_response.user, token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# ─── Request/Response Models ───────────────────────────────
class ResearchRequest(BaseModel):
    query: str


class ResearchHistoryItem(BaseModel):
    id: str
    query: str
    status: str
    created_at: str


# ─── App Setup ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Multi-Agent Research Assistant API starting...")
    print("📚 Docs available at http://localhost:8000/docs")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Multi-Agent Research Assistant",
    description="AI-powered research report generation using 4 specialized agents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ─────────────────────────────────────────────

@app.post("/api/research")
async def start_research(
    request: ResearchRequest, 
    auth_data=Depends(get_current_user)
):
    """
    Start a new research pipeline.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Research query cannot be empty")

    user, token = auth_data
    user_id = user.id

    # Try to log to Supabase (graceful fallback if not configured)
    task_record = None
    try:
        from backend.supabase_client import log_research_task, update_research_task
        task_record = log_research_task(request.query, user_id, token)
    except Exception as e:
        print(f"⚠️  Supabase logging skipped: {e}")

    async def event_generator():
        event_queue = asyncio.Queue()

        async def progress_callback(agent_name, status, data=None):
            await event_queue.put({
                "agent": agent_name,
                "status": status,
                "data": str(data)[:500] if data else None,
            })

        async def run_pipeline():
            try:
                result = await run_research(request.query, progress_callback)
                await event_queue.put({
                    "agent": "complete",
                    "status": "done",
                    "report": result.get("report", ""),
                    "chart_data": result.get("chart_data"),
                    "task_id": task_record["id"] if task_record else None,
                })

                # Save to Supabase
                if task_record:
                    try:
                        update_research_task(task_record["id"], {
                            "status": "completed",
                            "sub_tasks": result.get("sub_tasks"),
                            "sources": result.get("sources"),
                            "analysis": result.get("analysis"),
                            "report": result.get("report"),
                        }, token)
                    except Exception as e:
                        print(f"⚠️  Supabase update failed: {e}")

            except Exception as e:
                await event_queue.put({
                    "agent": "error",
                    "status": "failed",
                    "data": str(e),
                })

                if task_record:
                    try:
                        update_research_task(task_record["id"], {
                            "status": "failed",
                        }, token)
                    except Exception:
                        pass

            finally:
                await event_queue.put(None)

        # Start pipeline in background
        asyncio.create_task(run_pipeline())

        # Yield events as they come
        while True:
            event = await event_queue.get()
            if event is None:
                break
            yield {
                "event": "message",
                "data": json.dumps(event),
            }

    return EventSourceResponse(event_generator())


@app.get("/api/history")
async def get_history(auth_data=Depends(get_current_user)):
    """
    Get list of past research tasks for the logged in user.
    """
    user, token = auth_data
    try:
        from backend.supabase_client import get_research_history
        history = get_research_history(user.id, token)
        return {"history": history}
    except Exception as e:
        return {"history": [], "warning": str(e)}


@app.get("/api/research/{task_id}")
async def get_research(task_id: str, auth_data=Depends(get_current_user)):
    """
    Get a specific research report by ID.
    RLS ensures users can only read their own reports.
    """
    user, token = auth_data
    try:
        from backend.supabase_client import get_research_by_id
        # The authenticated client respects RLS natively
        task = get_research_by_id(task_id, token)
        if not task:
            raise HTTPException(status_code=404, detail="Research task not found")
            
        # Extra security check: make sure the task belongs to the user
        if task.get("user_id") != user.id:
            raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this task")
            
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "multi-agent-research-assistant"}
