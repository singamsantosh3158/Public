"""FastAPI backend for the React (Vite) Audit Chat Agent frontend.

Reuses agent.py / fabric_client.py / viz.py unchanged.

Multi-user isolation: each request that talks to the model constructs its own
FabricAgent, seeded only with that ONE conversation's own `agent_items` and
discarded afterward — so concurrent requests for different conversations can
never cross-contaminate each other's memory (the earlier design mutated a
single shared FabricAgent instance, which was a real race condition under
FastAPI's threadpool-per-sync-request model). A per-conversation lock still
serializes two requests racing on the *same* conversation (e.g. a double
send). The parsed schema is cached process-wide since it's the same for every
conversation and doesn't change.

Caveat this does NOT fix: Fabric sign-in (`fabric_client`) is still one
shared credential for the whole process, regardless of FABRIC_AUTH_MODE —
there's no per-visitor Fabric identity without a real OAuth redirect flow
(bigger change, not done here).
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import uuid

sys.path.insert(0, os.path.dirname(__file__))

import db
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import FabricAgent
from fabric_client import FabricSemanticModelClient

load_dotenv()

REQUIRED_ENV_VARS = ("FABRIC_WORKSPACE_ID", "FABRIC_DATASET_ID", "OPENAI_API_KEY")
missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
if missing:
    raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
fabric_client = FabricSemanticModelClient(os.environ["FABRIC_WORKSPACE_ID"], os.environ["FABRIC_DATASET_ID"])

conversations: dict[str, dict] = db.load_all()

_schema_cache_lock = threading.Lock()
_schema_cache: dict[str, str | None] = {"value": None}

_conv_locks: dict[str, threading.Lock] = {}
_conv_locks_lock = threading.Lock()


def _lock_for(conv_id: str) -> threading.Lock:
    with _conv_locks_lock:
        return _conv_locks.setdefault(conv_id, threading.Lock())


app = FastAPI(title="Audit Chat Agent API")


def _serialize_agent_items(items: list) -> list:
    """SDK response items (Pydantic models) aren't JSON-serializable as-is."""
    return [item.model_dump() if hasattr(item, "model_dump") else item for item in items]


def _persist(conv_id: str) -> None:
    conv = conversations[conv_id]
    db.save(conv_id, conv["title"], conv["history"], _serialize_agent_items(conv["agent_items"]))

TABLE_REF_RE = re.compile(r"'([^']+)'\s*\[|\b([A-Z][A-Za-z0-9_ ]*?)\s*\[")


def build_analysis_note(dax_calls: list[dict]) -> str | None:
    if not dax_calls:
        return None
    tables: set[str] = set()
    total_rows = 0
    errors = 0
    for call in dax_calls:
        for match in TABLE_REF_RE.finditer(call["query"]):
            name = (match.group(1) or match.group(2) or "").strip()
            if name:
                tables.add(name)
        if call["error"]:
            errors += 1
        else:
            try:
                total_rows += len(json.loads(call["result"]))
            except (TypeError, ValueError):
                pass
    n = len(dax_calls)
    note = f"Ran {n} DAX quer{'y' if n == 1 else 'ies'}"
    if tables:
        shown = sorted(tables)[:5]
        note += " against " + ", ".join(shown) + (" and more" if len(tables) > 5 else "")
    note += f" — {total_rows} row{'s' if total_rows != 1 else ''} returned"
    if errors:
        note += f" ({errors} error{'s' if errors != 1 else ''} encountered)"
    return note


def serialize_conversation(conv_id: str) -> dict:
    conv = conversations[conv_id]
    return {"id": conv_id, "title": conv["title"], "messages": conv["history"]}


class SendMessageRequest(BaseModel):
    content: str


@app.get("/api/auth/status")
def auth_status():
    return {
        "signedIn": fabric_client.is_signed_in,
        "user": fabric_client.signed_in_user,
        "deviceCode": fabric_client.pending_device_code,
    }


@app.post("/api/auth/signin")
def auth_signin():
    # A sync path-operation function: FastAPI runs it in a thread pool automatically, so
    # this blocking call doesn't stall the event loop. In browser mode it opens a real
    # browser window and waits for the full sign-in. In device_code mode it only waits
    # for the code to be issued (a few seconds) and returns that — the frontend then
    # polls /api/auth/status until the user finishes the flow on their own device.
    try:
        device_code = fabric_client.sign_in()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "signedIn": fabric_client.is_signed_in,
        "user": fabric_client.signed_in_user,
        "deviceCode": device_code,
    }


@app.post("/api/auth/signout")
def auth_signout():
    fabric_client.sign_out()
    return {"signedIn": False, "user": None, "deviceCode": None}


@app.get("/api/conversations")
def list_conversations():
    return [serialize_conversation(cid) for cid, conv in conversations.items() if conv["history"]]


@app.post("/api/conversations")
def new_conversation():
    conv_id = str(uuid.uuid4())
    conversations[conv_id] = {"title": None, "history": [], "agent_items": []}
    return serialize_conversation(conv_id)


class RenameRequest(BaseModel):
    title: str


@app.patch("/api/conversations/{conv_id}")
def rename_conversation(conv_id: str, body: RenameRequest):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversations[conv_id]["title"] = body.title
    _persist(conv_id)
    return serialize_conversation(conv_id)


@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del conversations[conv_id]
    db.delete(conv_id)
    return {"ok": True}


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return serialize_conversation(conv_id)


def _run_turn(conv_id: str, content: str) -> dict:
    """Runs entirely in a worker thread. Builds a fresh FabricAgent scoped to just this
    conversation's own memory — never touches any other conversation's state, and the
    lock below only serializes a second request racing on this SAME conversation."""
    with _lock_for(conv_id):
        conv = conversations[conv_id]

        agent = FabricAgent(fabric_client, OPENAI_API_KEY)
        agent.input_items = list(conv["agent_items"])
        with _schema_cache_lock:
            agent._schema_cache = _schema_cache["value"]

        answer = agent.ask(content)
        dax_calls = agent.last_dax_queries
        conv["agent_items"] = agent.input_items

        with _schema_cache_lock:
            _schema_cache["value"] = agent._schema_cache

        return {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": answer,
            "dax": dax_calls,
            "analysisNote": build_analysis_note(dax_calls),
        }


@app.post("/api/conversations/{conv_id}/messages")
async def send_message(conv_id: str, body: SendMessageRequest):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not fabric_client.is_signed_in:
        # Hard gate: never let a request fall through into agent.ask() while signed out —
        # that would call _get_token() mid-request, which can pop an unexpected interactive
        # browser window on whichever machine is running this server.
        raise HTTPException(status_code=401, detail="Not signed in to Fabric. Click \"Log in\" first.")
    conv = conversations[conv_id]

    conv["history"].append({"id": str(uuid.uuid4()), "role": "user", "content": body.content})
    if conv["title"] is None:
        conv["title"] = body.content

    reply = await run_in_threadpool(_run_turn, conv_id, body.content)

    conv["history"].append(reply)
    _persist(conv_id)
    return reply


# Serves the built React app (frontend/dist) when present, so this one process can be
# the whole deployment — no separate static host or CORS setup needed. Mounted last so
# it never shadows the /api/* routes above. Absent in local dev (frontend runs via its
# own `npm run dev` + vite proxy instead), so this is skipped there.
_frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
