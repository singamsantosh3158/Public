from __future__ import annotations

import json
import re
from pathlib import Path

from agents import Runner, SQLiteSession
from dotenv import load_dotenv
from flask import Flask, Response, abort, jsonify, render_template, request

from .agent_defs import itinerary_agent, logistics_agent, triage_agent
from .pdf import markdown_to_pdf
from .tools import TRIPS_DIR

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_PATH = ROOT / "data" / "sessions.db"
AGENT_STATE_PATH = ROOT / "data" / "session_agents.json"

app = Flask(__name__)

_SAVE_ITINERARY_PATTERN = re.compile(r"Saved itinerary to (.+)$")

_AGENTS_BY_NAME = {a.name: a for a in (triage_agent, itinerary_agent, logistics_agent)}


def _load_current_agents() -> dict[str, str]:
    try:
        return json.loads(AGENT_STATE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_current_agents(state: dict[str, str]) -> None:
    AGENT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    AGENT_STATE_PATH.write_text(json.dumps(state))


def _find_saved_itinerary(new_items) -> str | None:
    """If this turn called save_itinerary, return the saved .md file's stem."""
    for item in new_items:
        if getattr(item, "type", None) != "tool_call_output_item":
            continue
        match = _SAVE_ITINERARY_PATTERN.search(str(getattr(item, "output", "")))
        if match:
            return Path(match.group(1).strip()).stem
    return None


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/trips/<stem>.pdf")
def download_trip(stem):
    md_path = (TRIPS_DIR / f"{stem}.md").resolve()
    if TRIPS_DIR.resolve() not in md_path.parents or not md_path.is_file():
        abort(404)
    title = stem.replace("-", " ").title()
    pdf_bytes = markdown_to_pdf(md_path.read_text(), title)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{stem}.pdf"'},
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    session_name = (data.get("session_name") or "default").strip() or "default"
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    session = SQLiteSession(session_name, db_path=str(DB_PATH))

    current_agents = _load_current_agents()
    agent = _AGENTS_BY_NAME.get(current_agents.get(session_name), triage_agent)

    result = Runner.run_sync(agent, message, session=session)

    current_agents[session_name] = result.last_agent.name
    _save_current_agents(current_agents)

    response = {"agent": result.last_agent.name, "reply": result.final_output}
    saved_trip = _find_saved_itinerary(result.new_items)
    if saved_trip:
        response["download_url"] = f"/trips/{saved_trip}.pdf"

    return jsonify(response)


def main() -> None:
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
