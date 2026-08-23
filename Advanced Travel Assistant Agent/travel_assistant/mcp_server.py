"""MCP adapter for the travel assistant server layer.

Exposes the functions in `server.py` as MCP tools over stdio, so any local
MCP client (Claude Code included) can call them. This module owns nothing
except the protocol wiring — all the actual behavior lives in `server.py`.

Run directly (`python -m travel_assistant.mcp_server`) or via a client that
spawns this as a subprocess and speaks MCP over its stdin/stdout.
"""

from mcp.server.mcpserver import MCPServer

from . import server

mcp = MCPServer(
    "travel-assistant",
    instructions=(
        "Tools for planning and saving travel itineraries: look up a "
        "destination photo, save/read/list saved itineraries, and render a "
        "saved itinerary to PDF. This server holds no opinions about how "
        "to plan a trip — that judgment belongs to the calling agent."
    ),
)


@mcp.tool()
def get_destination_photo(place: str) -> str:
    """Look up a representative photo of a travel destination or landmark.

    Returns Markdown image syntax embeddable directly in a reply. If no
    photo is found, says so instead of inventing an image URL.

    Args:
        place: The place to find a photo for, e.g. "Lisbon" or "Eiffel Tower".
    """
    return server.get_destination_photo(place)


@mcp.tool()
def save_itinerary(trip_name: str, itinerary_markdown: str) -> str:
    """Save a finished trip itinerary to a local Markdown file.

    Call once the traveler has confirmed they're happy with the itinerary,
    not while it's still being drafted or revised.

    Args:
        trip_name: Short name for the trip, e.g. "Tokyo in April" — used to
            name the saved file.
        itinerary_markdown: The full itinerary, formatted as Markdown.
    """
    return server.save_itinerary(trip_name, itinerary_markdown)


@mcp.tool()
def list_trips() -> list[str]:
    """List the names of all previously saved trip itineraries."""
    return server.list_trips()


@mcp.tool()
def get_trip(trip_name: str) -> str:
    """Read back a previously saved itinerary's Markdown.

    Args:
        trip_name: The trip name used when it was saved (matched by slug).
    """
    return server.get_trip(trip_name)


@mcp.tool()
def render_trip_pdf(trip_name: str) -> str:
    """Render a saved itinerary to PDF, written next to its source Markdown.

    Args:
        trip_name: The trip name used when it was saved (matched by slug).

    Returns:
        The filesystem path to the generated PDF.
    """
    return server.render_trip_pdf(trip_name)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
