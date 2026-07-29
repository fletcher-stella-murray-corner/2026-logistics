#!/usr/bin/env python3
"""Regenerate site/index.html — the Timeline feature, which doubles as the
site's homepage (see requirements/public.md -> Homepage = Timeline).

Reads shared/data/people.json, timeline/data/travel.json, and
timeline/data/meals.json. Renders August 1-15, 2026 split into four 6-hour
blocks per day, always starting from max(today, Aug 1) so past days quietly
drop off the site on every rebuild.

Run after hand-editing any of the three data files above, or use
scripts/build_site.py to rebuild every feature at once.

site/index.html is a pure build artifact — edit this template, not the HTML.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # timeline/
PROJECT_ROOT = ROOT.parent  # repo root — site/ and shared/ live here

sys.path.insert(0, str(PROJECT_ROOT / "shared"))
import nav  # noqa: E402

PAGE_TITLE = "Murray Corner 2026"
TRIP_SUBTITLE = "Murray Corner, New Brunswick · August 1–15, 2026"

TRIP_START = date(2026, 8, 1)
TRIP_END = date(2026, 8, 15)

BLOCKS = ["00-06", "06-12", "12-18", "18-24"]
BLOCK_INDEX = {b: i for i, b in enumerate(BLOCKS)}
BLOCK_LABELS = {
    "00-06": "12am–6am",
    "06-12": "6am–12pm",
    "12-18": "12pm–6pm",
    "18-24": "6pm–12am",
}
MODE_TAGS = {
    "plane": "✈️ Plane",
    "train": "🚆 Train",
    "car": "🚗 Car",
}

NAV_ITEMS = [
    ("Timeline", None, True),
    ("Family Tree", "family-tree/index.html", False),
]


def esc(s):
    return nav.esc(s)


def load_json(path):
    return json.loads(path.read_text())


def block_key(iso_date, block):
    return (iso_date, BLOCK_INDEX[block])


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def render_block(day, block, travel, people_by_id, meals):
    key = block_key(day.isoformat(), block)

    arrivals = []
    departures = []
    present = []

    for entry in travel:
        person = people_by_id.get(entry["person_id"])
        if person is None:
            continue

        arrival = entry.get("arrival")
        departure = entry.get("departure")
        arrival_key = block_key(arrival["date"], arrival["block"]) if arrival else None
        departure_key = block_key(departure["date"], departure["block"]) if departure else None

        if arrival_key == key:
            arrivals.append((person, arrival))
        if departure_key == key:
            departures.append((person, departure))

        arrived_by = True if arrival_key is None else key >= arrival_key
        not_departed = True if departure_key is None else key < departure_key
        if arrived_by and not_departed:
            present.append((person, entry.get("room", "")))

    rows = []

    if arrivals:
        lines = "".join(
            f'<span class="person-line">'
            f'<span class="mode-tag">{esc(MODE_TAGS.get(a["mode"], a["mode"]))}</span>'
            f'{esc(p["name"])} — {esc(a.get("detail", ""))}'
            f"</span>"
            for p, a in arrivals
        )
        rows.append(f'<div class="block-row"><span class="block-row-label">Arriving:</span>{lines}</div>')

    if departures:
        lines = "".join(
            f'<span class="person-line">'
            f'<span class="mode-tag">{esc(MODE_TAGS.get(d["mode"], d["mode"]))}</span>'
            f'{esc(p["name"])} — {esc(d.get("detail", ""))}'
            f"</span>"
            for p, d in departures
        )
        rows.append(f'<div class="block-row"><span class="block-row-label">Departing:</span>{lines}</div>')

    if present:
        by_room = {}
        for p, room in present:
            by_room.setdefault(room or "Unassigned", []).append(p["name"])
        room_lines = "".join(
            f'<span class="room-group"><span class="room-name">{esc(room)}:</span> '
            f'{esc(", ".join(sorted(names)))}</span>'
            for room, names in sorted(by_room.items())
        )
        rows.append(f'<div class="block-row"><span class="block-row-label">Sleeping:</span>{room_lines}</div>')

    meal = meals.get(day.isoformat(), {}).get(block)
    if meal:
        rows.append(f'<div class="block-row"><span class="block-row-label">Meal:</span> {esc(meal)}</div>')

    body = "".join(rows) if rows else '<div class="block-empty-hint">Nothing scheduled</div>'

    return f"""<div class="block">
<div class="block-label">{BLOCK_LABELS[block]}</div>
{body}
</div>"""


def render_day(day, travel, people_by_id, meals):
    heading = day.strftime("%A, %B ") + str(day.day)
    blocks_html = "\n".join(render_block(day, b, travel, people_by_id, meals) for b in BLOCKS)
    return f"""<section class="day">
<h2 class="day-heading">{heading}</h2>
<div class="blocks">
{blocks_html}
</div>
</section>"""


def build_timeline_html(people, travel, meals, today=None):
    people_by_id = {p["id"]: p for p in people}
    cutoff = max(today or date.today(), TRIP_START)

    if cutoff > TRIP_END:
        return '<p class="trip-done">The trip is over — thanks for a great one!</p>'

    return "\n".join(render_day(d, travel, people_by_id, meals) for d in daterange(cutoff, TRIP_END))


def build_page_html(people, travel, meals, shared_base_css, shared_css):
    nav_row = nav.render_row(NAV_ITEMS)
    timeline_html = build_timeline_html(people, travel, meals)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{PAGE_TITLE}</title>
<style>
{shared_base_css}
{shared_css}
</style>
</head>
<body>
{nav_row}
<h1 class="trip-title">{PAGE_TITLE}</h1>
<p class="trip-subtitle">{TRIP_SUBTITLE}</p>
<main>
{timeline_html}
</main>
</body>
</html>
"""


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    people = load_json(PROJECT_ROOT / "shared" / "data" / "people.json")
    travel = load_json(ROOT / "data" / "travel.json")
    meals = load_json(ROOT / "data" / "meals.json")
    shared_base_css = (PROJECT_ROOT / "shared" / "base.css").read_text()
    shared_css = (ROOT / "shared.css").read_text()

    html = build_page_html(people, travel, meals, shared_base_css, shared_css)
    out_path = PROJECT_ROOT / "site" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print("Updated site/index.html")


if __name__ == "__main__":
    main()
