# Travel Assistant — Documentation

A conversational trip-planning assistant built on the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/). A triage agent routes each message to a specialist — an **Itinerary Planner** or **Trip Logistics** agent — both of which can look up a real photo of the destination and search the web for anything time-sensitive. Finished itineraries can be saved and downloaded as a PDF.

For how it's built internally — component breakdown, sequence diagrams, design tradeoffs — see **[ARCHITECTURE.md](ARCHITECTURE.md)**.

## Project layout

```
travel-assistant-agent/
├── travel_assistant/
│   ├── agent_defs.py      # the three agents: instructions, tools, handoffs
│   ├── tools.py            # save_itinerary, get_destination_photo
│   ├── pdf.py               # Markdown → PDF renderer (used by the web download route)
│   ├── main.py              # CLI entry point
│   ├── web.py                # Flask entry point (chat API + PDF download route)
│   └── templates/
│       └── chat.html          # the entire web frontend (single file, no build step)
├── data/                    # gitignored — created at runtime
│   ├── sessions.db            # conversation history (SQLiteSession)
│   ├── session_agents.json    # which agent is active per session
│   └── trips/*.md              # saved itineraries (source of truth; PDFs are generated on demand)
├── tests/
│   └── test_tools.py         # unit tests for tools.py
├── requirements.txt          # runtime dependencies
├── requirements-dev.txt      # + pytest / pytest-asyncio
├── pytest.ini
├── .env.example
└── README.md                 # top-level quick-start (this folder has the fuller picture)
```

## Setup

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (from https://platform.openai.com/api-keys). The key needs active billing/credits — the app will fail with a 429 `insufficient_quota` error otherwise.

**Note on Python version:** the venv in this project runs Python 3.9. The Agents SDK needs `eval_type_backport` (already in `requirements.txt`) to patch around modern type syntax at runtime, and this project's own code uses `from __future__ import annotations` in `web.py` for the same reason. Upgrading to Python 3.10+ removes the need for both. See "Known limitations" in [ARCHITECTURE.md](ARCHITECTURE.md) for why this matters.

**Note on the `openai` package version:** `requirements.txt` pins `openai>=2.19.0,<2.48.0`. A newer `openai` release changed a response schema in a way that's incompatible with `openai-agents==0.8.4` (crashes with a `pydantic` validation error on every request). Don't remove this pin without re-testing against whatever `openai-agents` version is current at the time.

## Running it

### CLI

```sh
python -m travel_assistant.main
```

Prompts for a session name (reuse a name to resume that trip later), then it's a plain back-and-forth REPL. Type `exit` to quit.

### Web chat UI

```sh
python -m travel_assistant.web
```

Open http://127.0.0.1:5000. The "Trip" field is empty by default — an unnamed chat still gets a unique session behind the scenes, so tabs don't collide. Type a trip name to start (or resume) a named, savable trip. Use **＋ New** to explicitly start over at any time.

This runs Flask's development server (`debug=True`) — fine for local personal use, not meant to be exposed beyond `localhost`.

## Testing

```sh
pip install -r requirements-dev.txt
pytest
```

Currently covers `tools.py` (`_slugify`, `save_itinerary`). There's no automated coverage yet for the agent routing/handoff behavior itself (that would mean stubbing the Agents SDK's `Model` interface to avoid live API calls — see `agents.models.interface.Model` if you want to add this).

## Data & privacy notes

- `data/` and `.env` are gitignored — trip data, conversation history, and your API key never get committed.
- `get_destination_photo` calls Wikipedia's public REST API with the place name you're discussing; `WebSearchTool` calls go through OpenAI's hosted web search. Both are outbound network calls made on your behalf during a chat turn.
- Web search and photo lookups cost money per OpenAI's API pricing. This is built for low-volume interactive use, not batch/bulk usage.
- Always verify visa/entry requirements against an official government source before traveling — the Trip Logistics agent is instructed to say this too, but it bears repeating.
