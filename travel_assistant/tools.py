import re
from pathlib import Path
from urllib.parse import quote

import requests
from agents import function_tool

ROOT = Path(__file__).resolve().parent.parent
TRIPS_DIR = ROOT / "data" / "trips"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "trip"


@function_tool
def save_itinerary(trip_name: str, itinerary_markdown: str) -> str:
    """Save a finished trip itinerary to a local Markdown file.

    Call this once the user has confirmed they're happy with the itinerary,
    not while it's still being drafted or revised.

    Args:
        trip_name: Short name for the trip, e.g. "Tokyo in April" — used to
            name the saved file.
        itinerary_markdown: The full itinerary, formatted as Markdown.
    """
    TRIPS_DIR.mkdir(parents=True, exist_ok=True)
    path = TRIPS_DIR / f"{_slugify(trip_name)}.md"
    path.write_text(itinerary_markdown)
    return f"Saved itinerary to {path}"


@function_tool
def get_destination_photo(place: str) -> str:
    """Look up a representative photo of a travel destination or landmark.

    Returns Markdown image syntax you can embed directly in your reply so the
    user sees the photo. If no photo is found, says so instead — don't invent
    an image URL yourself.

    Args:
        place: The place to find a photo for, e.g. "Lisbon" or "Eiffel Tower".
    """
    try:
        response = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(place)}",
            headers={"User-Agent": "travel-assistant-agent (personal project)"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return f"No photo found for {place}."

    # Prefer the thumbnail: Wikipedia's originalimage can be multi-megapixel,
    # which is overkill for a chat bubble or embedded PDF and bloats both.
    thumbnail = (data.get("thumbnail") or data.get("originalimage") or {}).get("source")
    if not thumbnail:
        return f"No photo found for {place}."
    return f"![{place}]({thumbnail})"
