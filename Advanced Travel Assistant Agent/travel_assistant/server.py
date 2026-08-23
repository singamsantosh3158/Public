"""Pure business logic for the travel assistant.

No LLM, no agent framework, no web framework — just the deterministic
operations a travel-planning agent needs: reading and writing saved trips,
looking up a destination photo, and rendering a saved trip to PDF. This
module is the thing an MCP server (or any other front end) wraps; it has no
knowledge of MCP, Flask, or any particular caller.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

import requests

from .pdf import markdown_to_pdf

ROOT = Path(__file__).resolve().parent.parent
TRIPS_DIR = ROOT / "data" / "trips"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "trip"


def save_itinerary(trip_name: str, itinerary_markdown: str) -> str:
    """Save a finished trip itinerary to a local Markdown file.

    Call once the traveler has confirmed they're happy with the itinerary,
    not while it's still being drafted or revised.

    Args:
        trip_name: Short name for the trip, e.g. "Tokyo in April" — used to
            name the saved file.
        itinerary_markdown: The full itinerary, formatted as Markdown.

    Returns:
        A confirmation message including the saved file path.
    """
    TRIPS_DIR.mkdir(parents=True, exist_ok=True)
    path = TRIPS_DIR / f"{_slugify(trip_name)}.md"
    path.write_text(itinerary_markdown)
    return f"Saved itinerary to {path}"


def list_trips() -> list[str]:
    """List the names of all saved trip itineraries."""
    if not TRIPS_DIR.exists():
        return []
    return sorted(p.stem for p in TRIPS_DIR.glob("*.md"))


def get_trip(trip_name: str) -> str:
    """Read back a previously saved itinerary's Markdown.

    Args:
        trip_name: The trip name used when it was saved (matched by slug).

    Raises:
        FileNotFoundError: If no saved trip matches.
    """
    path = TRIPS_DIR / f"{_slugify(trip_name)}.md"
    if not path.is_file():
        raise FileNotFoundError(f"No saved trip found for '{trip_name}'.")
    return path.read_text()


def get_destination_photo(place: str) -> str:
    """Look up a representative photo of a travel destination or landmark.

    Returns Markdown image syntax embeddable directly in a reply. If no
    photo is found, says so instead of inventing an image URL.

    Args:
        place: The place to find a photo for, e.g. "Lisbon" or "Eiffel Tower".
    """
    try:
        response = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(place)}",
            headers={"User-Agent": "travel-assistant (personal project)"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return f"No photo found for {place}."

    # Prefer the thumbnail: Wikipedia's originalimage can be multi-megapixel,
    # which is overkill for a chat reply or embedded PDF and bloats both.
    thumbnail = (data.get("thumbnail") or data.get("originalimage") or {}).get("source")
    if not thumbnail:
        return f"No photo found for {place}."
    return f"![{place}]({thumbnail})"


def render_trip_pdf(trip_name: str) -> str:
    """Render a saved itinerary to PDF, written next to its source Markdown.

    Args:
        trip_name: The trip name used when it was saved (matched by slug).

    Returns:
        The path to the generated PDF file.

    Raises:
        FileNotFoundError: If no saved trip matches.
    """
    slug = _slugify(trip_name)
    md_path = TRIPS_DIR / f"{slug}.md"
    if not md_path.is_file():
        raise FileNotFoundError(f"No saved trip found for '{trip_name}'.")
    pdf_bytes = markdown_to_pdf(md_path.read_text(), title=slug.replace("-", " ").title())
    pdf_path = TRIPS_DIR / f"{slug}.pdf"
    pdf_path.write_bytes(pdf_bytes)
    return str(pdf_path)
