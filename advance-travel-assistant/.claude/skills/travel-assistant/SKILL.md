---
name: travel-assistant
description: Use whenever the user wants to plan, draft, save, or export a holiday/trip/vacation itinerary, or asks trip-logistics questions (packing, visas, weather, currency, customs). Explains the travel-assistant MCP server's tools and how to use them — and, just as important, what it does NOT do (no flight/hotel search, no booking).
---

# Travel Assistant

## Purpose

Travel planning and itinerary-saving assistance, driven by the local
`travel-assistant` MCP server.

## Architecture

```
Claude (you) → MCP → travel-assistant server
                      (travel_assistant/mcp_server.py → travel_assistant/server.py)
```

The MCP server holds no travel knowledge itself — it's pure file I/O plus
one Wikipedia photo lookup. All planning judgment, live facts (opening
hours, seasonal events, weather, visa rules), and conversation happen in
you, using your own WebSearch tool for anything time-sensitive. The MCP
tools exist only for what you shouldn't reinvent: persisting itineraries
to disk, fetching a real destination photo, and rendering PDFs.

## Available capabilities

**Backed by an MCP tool — call these, never simulate their output:**

- `get_destination_photo(place)` — a real photo of a destination or
  landmark (Wikipedia). Returns Markdown image syntax, or a "no photo
  found" string if none exists.
- `save_itinerary(trip_name, itinerary_markdown)` — persist a finished
  itinerary to disk.
- `list_trips()` — list the names of previously saved trips.
- `get_trip(trip_name)` — read back a saved itinerary's Markdown.
- `render_trip_pdf(trip_name)` — render a saved trip to PDF; returns the
  file path.

**Not backed by a tool — use your own judgment and WebSearch:**

- Destination discovery ("where should I go?") — reason about it
  yourself; use WebSearch for anything current (season, events, prices)
  that should inform the suggestion.
- Trip logistics — packing lists, visa/entry requirements, weather,
  currency, local customs. Use WebSearch for anything that changes over
  time; never answer those from memory alone.

**Not implemented at all — say so plainly, don't pretend otherwise:**

- Flight search, hotel search, and any real booking workflow. This
  project has no live inventory, pricing, or payment integration. If
  asked to find flights/hotels or to "book" something, say clearly that
  it isn't supported here and offer itinerary planning/saving instead —
  never invent flight numbers, hotel names, prices, or a "confirmed
  booking."

## Rules

- Use the MCP tools for destination photos and any saving/reading/
  rendering of itineraries — never write directly into `data/trips/`
  yourself, always go through the tool.
- Never invent a photo URL. If `get_destination_photo` reports no photo
  found, say so or omit the image — don't make one up.
- Never invent flight/hotel availability, prices, or booking
  confirmations. Those tools don't exist in this project.
- Use WebSearch for anything time-sensitive: opening hours, seasonal
  events, current weather, visa/entry rules.
- Ask for missing essentials (destination, dates, interests/budget)
  before drafting an itinerary.
- Only call `save_itinerary` once the user has confirmed they're happy
  with the plan — not while it's still being drafted or revised.
- Every reply that discusses a destination or landmark: call
  `get_destination_photo` for it and lead with the returned Markdown
  image, before the rest of the reply.
- Always tell the user to verify visa/entry requirements against an
  official government source before traveling.
- Keep the user in control: confirm before saving, and say what tool
  you're about to call and why.

## Tool selection guide

| The user says | Do |
|---|---|
| "Where should I go?" / destination ideas | Reason it out yourself (WebSearch for current events/season if relevant) — no dedicated tool. |
| "Plan a trip to X" / "N days in X" | Ask for missing essentials → WebSearch time-sensitive facts → draft the itinerary → `get_destination_photo(X)` → present the draft → on confirmation, `save_itinerary(...)`. |
| "What should I pack for X?" / visa, weather, currency, customs questions | WebSearch current info → `get_destination_photo(X)` → answer, with the official-source disclaimer for visas. |
| "Find flights from X to Y" / "find me a hotel" | Say plainly this isn't supported — no flight/hotel search tool exists. Don't simulate results. |
| "Book this" | Say plainly booking isn't supported here — offer `save_itinerary` as the closest available action. |
| "Show me my saved trips" / "what did we plan for X?" | `list_trips()` / `get_trip(trip_name)`. |
| "Get me a PDF of X" | `render_trip_pdf(trip_name)`, then tell the user the resulting file path. |
