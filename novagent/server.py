import json
from uuid import uuid4
from pydantic import BaseModel
from cachetools import TTLCache
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from novagent.config import NovagentConfig


# --- Configuration and Cache Setup ---
SESSION_TTL_SECONDS = 1500  # cache session for 20 minutes
cache = TTLCache(maxsize=100, ttl=SESSION_TTL_SECONDS)


class TaskRequest(BaseModel):
    task: str


# --- Server Factory ---
def create_server(config: NovagentConfig) -> FastAPI:
    app = FastAPI()

    @app.post("/session")
    async def create_session():
        session_id = str(uuid4())
        session = config.session()
        cache[session_id] = session
        return {"session_id": session_id}

    @app.post("/run")
    async def run_task(
        body: TaskRequest, session_id: str = Header(..., alias="X-Session-ID")
    ):
        if session_id not in cache:
            raise HTTPException(status_code=404, detail="Session not found")

        session = cache[session_id]

        async def event_generator():
            try:
                async for message in session.arun(body.task):
                    yield f"data: {json.dumps({'type': message.type.name, 'content': message.content})}\n\n"

                yield f"[DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app
