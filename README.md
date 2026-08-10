# Travel Assistant Agent

A conversational trip-planning assistant built on the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/). A triage agent routes each message to a specialist:

- **Itinerary Planner** — builds day-by-day plans for a destination and dates, using live web search for anything time-sensitive (opening hours, seasonal events). Saves the finished itinerary to `data/trips/` once you confirm it.
- **Trip Logistics** — packing lists, visa/entry requirements, weather, currency, local customs. Always double-check visa/entry rules against an official government source before traveling — the assistant will tell you this too, but it bears repeating.

Conversations persist locally (SQLite) by session name, so you can close the CLI and resume a trip later under the same name.

## Setup

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` from https://platform.openai.com/api-keys.

**Note on Python version:** the SDK needs Python 3.10+ for its native type syntax. If you're on 3.9, `eval_type_backport` (already in `requirements.txt`) patches around it, but upgrading to 3.10+ is the more robust long-term fix.

## Usage

```sh
python -m travel_assistant.main
```

You'll be asked for a session name — reuse the same name to continue planning a trip across separate runs. Type `exit` to quit.

## Notes

- `data/` and `.env` are gitignored — trip data and your API key never get committed.
- Web search costs apply per OpenAI's pricing for the `WebSearchTool`; this is a low-volume conversational tool, not a batch job, so costs should stay small.
