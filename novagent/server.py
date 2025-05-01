import asyncio
from uuid import uuid4
from pydantic import BaseModel
from cachetools import TTLCache
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from novagent.agent import NovagentConfig
from novagent.outputs import QueueOutput


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
        queue = asyncio.Queue()
        session = config.session(QueueOutput(queue))
        cache[session_id] = (session, queue)
        return {"session_id": session_id}

    @app.post("/run")
    async def run_task(
        body: TaskRequest, session_id: str = Header(..., alias="X-Session-ID")
    ):
        if session_id not in cache:
            raise HTTPException(status_code=404, detail="Session not found")

        session, queue = cache[session_id]

        async def event_stream():
            asyncio.create_task(session.arun(body.task))

            try:
                while True:
                    type, message = await queue.get()
                    yield f"[{type}] {message}\n\n"
            except asyncio.CancelledError:
                pass

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return app
