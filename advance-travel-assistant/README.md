# Travel Assistant — Server Layer + MCP Server

A pure Python "server layer" for trip planning, plus a local MCP server
that exposes it: no LLM, no agent framework, no web app baked in. The
actual planning judgment (what to ask, when to search the web, when to
save) belongs to whatever agent connects over MCP — this project just
gives it tools.

Saved itineraries live as Markdown files in `data/trips/`; PDFs are
generated on demand from that Markdown and are never stored as the source
of truth.

## Setup

```sh
python3 -m venv venv        # needs Python 3.10+ (required by the mcp package)
source venv/bin/activate
pip install -r requirements.txt
```

No API keys or `.env` are required — everything here is local file I/O plus
one unauthenticated call to Wikipedia's public REST API for photos.

## What's here

| Layer | File | Role |
|---|---|---|
| Server | [`travel_assistant/server.py`](travel_assistant/server.py) | The actual logic: `save_itinerary`, `get_trip`, `list_trips`, `get_destination_photo`, `render_trip_pdf`. Plain functions, no framework imports. |
| MCP adapter | [`travel_assistant/mcp_server.py`](travel_assistant/mcp_server.py) | Exposes each `server.py` function as an MCP tool, served over stdio. |

See [`Documentation/ARCHITECTURE.md`](Documentation/ARCHITECTURE.md) for details.

## Running the MCP server

```sh
python -m travel_assistant.mcp_server
```

This starts an MCP server on stdio — it's meant to be launched by an MCP
client (Claude Code, another agent, `mcp` Inspector), not run standalone
in a terminal you watch.

### Connecting Claude Code to it

`.mcp.json` at the repo root already registers it as a project-scoped MCP
server:

```json
{
  "mcpServers": {
    "travel-assistant": {
      "command": "<repo>/venv/bin/python",
      "args": ["-m", "travel_assistant.mcp_server"]
    }
  }
}
```

Open this project in Claude Code (or restart an existing session in it)
and approve the server when prompted. See
[`.claude/skills/travel-assistant/SKILL.md`](.claude/skills/travel-assistant/SKILL.md)
for how Claude uses these tools to actually plan/book a trip.

## Tests

```sh
pip install -r requirements-dev.txt
pytest
```

Tests cover `server.py` directly (no MCP transport involved).

## Notes

- `data/` is gitignored — trip data never gets committed.
- This package has no CLI and no web server of its own — the MCP server
  is the only front door.
