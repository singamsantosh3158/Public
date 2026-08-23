import pytest

from travel_assistant import tools
from travel_assistant.tools import _slugify, save_itinerary
from agents.tool_context import ToolContext


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Tokyo in April", "tokyo-in-april"),
        ("  Leading/trailing spaces  ", "leading-trailing-spaces"),
        ("Multiple---dashes!!!", "multiple-dashes"),
        ("", "trip"),
        ("!!!", "trip"),
    ],
)
def test_slugify(text, expected):
    assert _slugify(text) == expected


def test_slugify_truncates_long_names():
    slug = _slugify("a" * 200)
    assert len(slug) <= 60


async def test_save_itinerary_writes_markdown_file(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "TRIPS_DIR", tmp_path)

    context = ToolContext(
        context=None,
        tool_name="save_itinerary",
        tool_call_id="call_1",
        tool_arguments='{"trip_name": "Tokyo in April", "itinerary_markdown": "# Day 1\\nArrive."}',
    )
    result = await save_itinerary.on_invoke_tool(context, context.tool_arguments)

    saved_path = tmp_path / "tokyo-in-april.md"
    assert saved_path.exists()
    assert saved_path.read_text() == "# Day 1\nArrive."
    assert str(saved_path) in result


async def test_save_itinerary_overwrites_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "TRIPS_DIR", tmp_path)
    existing = tmp_path / "paris-weekend.md"
    tmp_path.mkdir(exist_ok=True)
    existing.write_text("old draft")

    context = ToolContext(
        context=None,
        tool_name="save_itinerary",
        tool_call_id="call_2",
        tool_arguments='{"trip_name": "Paris Weekend", "itinerary_markdown": "final version"}',
    )
    await save_itinerary.on_invoke_tool(context, context.tool_arguments)

    assert existing.read_text() == "final version"
