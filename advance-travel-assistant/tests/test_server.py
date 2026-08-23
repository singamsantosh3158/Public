import pytest

from travel_assistant import server
from travel_assistant.server import (
    _slugify,
    get_trip,
    list_trips,
    render_trip_pdf,
    save_itinerary,
)


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


def test_save_itinerary_writes_markdown_file(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "TRIPS_DIR", tmp_path)

    result = save_itinerary("Tokyo in April", "# Day 1\nArrive.")

    saved_path = tmp_path / "tokyo-in-april.md"
    assert saved_path.exists()
    assert saved_path.read_text() == "# Day 1\nArrive."
    assert str(saved_path) in result


def test_save_itinerary_overwrites_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "TRIPS_DIR", tmp_path)
    tmp_path.mkdir(exist_ok=True)
    existing = tmp_path / "paris-weekend.md"
    existing.write_text("old draft")

    save_itinerary("Paris Weekend", "final version")

    assert existing.read_text() == "final version"


def test_list_trips_returns_sorted_slugs(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "TRIPS_DIR", tmp_path)
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "tokyo.md").write_text("x")
    (tmp_path / "paris.md").write_text("x")

    assert list_trips() == ["paris", "tokyo"]


def test_list_trips_empty_when_dir_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "TRIPS_DIR", tmp_path / "missing")

    assert list_trips() == []


def test_get_trip_reads_back_saved_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "TRIPS_DIR", tmp_path)
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "tokyo-in-april.md").write_text("# Day 1\nArrive.")

    assert get_trip("Tokyo in April") == "# Day 1\nArrive."


def test_get_trip_raises_for_missing_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "TRIPS_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        get_trip("Nonexistent Trip")


def test_render_trip_pdf_writes_pdf_next_to_source(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "TRIPS_DIR", tmp_path)
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "tokyo-in-april.md").write_text("# Tokyo\nDay 1: Arrive.")

    pdf_path = render_trip_pdf("Tokyo in April")

    assert pdf_path == str(tmp_path / "tokyo-in-april.pdf")
    assert (tmp_path / "tokyo-in-april.pdf").is_file()


def test_render_trip_pdf_raises_for_missing_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "TRIPS_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        render_trip_pdf("Nonexistent Trip")
