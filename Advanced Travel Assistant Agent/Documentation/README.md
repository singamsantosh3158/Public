# Travel Assistant — Documentation

A server-layer rebuild plus a local MCP server on top of it: no agent
framework, no web app, no CLI baked in. `travel_assistant/server.py` is a
plain Python library of the deterministic operations a trip-planning agent
needs — save/read a saved itinerary, look up a destination photo, render a
saved itinerary to PDF. `travel_assistant/mcp_server.py` exposes each of
those as an MCP tool over stdio, so a local agent (Claude Code) can call
them directly. Anything that decides *what* to plan lives outside this
package, in the calling agent.

For how it's built internally — component breakdown, design tradeoffs —
see **[ARCHITECTURE.md](ARCHITECTURE.md)**.

## Project layout

```
advance-travel-assistant/
├── travel_assistant/
│   ├── server.py            # save_itinerary, get_trip, list_trips,
│   │                         # get_destination_photo, render_trip_pdf
│   ├── mcp_server.py         # MCP tool wrappers over server.py, stdio transport
│   └── pdf.py                # Markdown → PDF renderer (used by render_trip_pdf)
├── data/                     # gitignored — created at runtime
│   └── trips/                  # *.md = saved itineraries (source of truth)
│                                # *.pdf = generated on demand, not committed
├── tests/
│   └── test_server.py        # unit tests for server.py
├── .mcp.json                  # registers the MCP server for Claude Code
├── .claude/skills/travel-assistant/SKILL.md  # how an agent should use these tools
├── requirements.txt           # requests, fpdf2, pillow, mcp
├── requirements-dev.txt       # + pytest
├── pytest.ini
└── README.md                  # top-level quick-start (this folder has the fuller picture)
```

## Setup

```sh
python3 -m venv venv        # needs Python 3.10+ (the mcp package requires it)
source venv/bin/activate
pip install -r requirements.txt
```

No `.env` or API key is required. The only outbound network call this
package makes on its own is an unauthenticated request to Wikipedia's
public REST API in `get_destination_photo`.

## Using it

Directly as a library, imported by whatever drives it:

```python
from travel_assistant import server

server.get_destination_photo("Lisbon")
server.save_itinerary("Lisbon Weekend", "# Day 1\n...")
server.list_trips()
server.get_trip("Lisbon Weekend")
server.render_trip_pdf("Lisbon Weekend")
```

Or over MCP, by any client that can spawn a stdio server:

```sh
python -m travel_assistant.mcp_server
```

Claude Code picks this up automatically from `.mcp.json` in the repo root.

## Testing

```sh
pip install -r requirements-dev.txt
pytest
```

Covers `server.py`: slugify, save/read/list trips, and PDF rendering
(against a temp trips directory, so it never touches real saved data).

## Data & privacy notes

- `data/` is gitignored — trip data never gets committed.
- `get_destination_photo` calls Wikipedia's public REST API with whatever
  place name it's given; that's the only outbound call this package makes
  on its own.
- Always verify visa/entry requirements against an official government
  source before traveling — this package doesn't know anything about
  visas, an agent built on top of it does.
