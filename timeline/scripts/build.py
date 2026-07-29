#!/usr/bin/env python3
"""Regenerate site/index.html — the Timeline feature, which doubles as the
site's homepage (see requirements/public.md -> Homepage = Timeline).

Reads shared/data/people.json, timeline/data/travel.json, and
timeline/data/meals.json. Renders August 1-15, 2026 split into four day
quarters (6-hour segments) per day, one full-viewport-height "quarter
screen" per quarter, always starting from max(today, Aug 1) so past days
quietly drop off the site on every rebuild.

The nav bar is one single row: a live "current day quarter" label on the
left (updated by shared.js via IntersectionObserver as you scroll), the
"Jump" disclosure in the middle (links straight to any quarter screen
via anchor, independent of scroll-snap), and the Family Tree link on
the right.

Each quarter screen has two parts, per requirements/public.md ->
Terminology: a "day quarter canvas padding" spacer (blank space reserved
so the sticky nav bar doesn't cover real content), and the "day quarter
canvas" itself (the actual date/label/rows content) — the padding is
explicitly NOT part of the canvas.

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

QUARTERS = ["00-06", "06-12", "12-18", "18-24"]
QUARTER_INDEX = {q: i for i, q in enumerate(QUARTERS)}
QUARTER_LABELS = {
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

def esc(s):
    return nav.esc(s)


def load_json(path):
    return json.loads(path.read_text())


def quarter_key(iso_date, quarter):
    return (iso_date, QUARTER_INDEX[quarter])


def quarter_screen_id(iso_date, quarter):
    return f"qc-{iso_date}-{quarter}"


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def render_quarter_screen(day, quarter, travel, people_by_id, meals):
    key = quarter_key(day.isoformat(), quarter)

    arrivals = []
    departures = []
    present = []

    for entry in travel:
        person = people_by_id.get(entry["person_id"])
        if person is None:
            continue

        arrival = entry.get("arrival")
        departure = entry.get("departure")
        arrival_key = quarter_key(arrival["date"], arrival["quarter"]) if arrival else None
        departure_key = quarter_key(departure["date"], departure["quarter"]) if departure else None

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
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Arriving:</span>{lines}</div>')

    if departures:
        lines = "".join(
            f'<span class="person-line">'
            f'<span class="mode-tag">{esc(MODE_TAGS.get(d["mode"], d["mode"]))}</span>'
            f'{esc(p["name"])} — {esc(d.get("detail", ""))}'
            f"</span>"
            for p, d in departures
        )
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Departing:</span>{lines}</div>')

    if present:
        by_room = {}
        for p, room in present:
            by_room.setdefault(room or "Unassigned", []).append(p["name"])
        room_lines = "".join(
            f'<span class="room-group"><span class="room-name">{esc(room)}:</span> '
            f'{esc(", ".join(sorted(names)))}</span>'
            for room, names in sorted(by_room.items())
        )
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Sleeping:</span>{room_lines}</div>')

    meal = meals.get(day.isoformat(), {}).get(quarter)
    if meal:
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Meal:</span> {esc(meal)}</div>')

    body = "".join(rows) if rows else '<div class="quarter-empty-hint">Nothing scheduled</div>'
    date_label = day.strftime("%A, %B ") + str(day.day)
    nav_label = day.strftime("%a, %b ") + str(day.day) + " · " + QUARTER_LABELS[quarter]

    return f"""<section class="quarter-screen" id="{quarter_screen_id(day.isoformat(), quarter)}" \
data-quarter-label="{esc(nav_label)}">
<div class="quarter-canvas-padding"></div>
<div class="quarter-canvas">
<div class="quarter-date">{date_label}</div>
<h2 class="quarter-label">{QUARTER_LABELS[quarter]}</h2>
{body}
</div>
</section>"""


def render_intro_screen():
    return f"""<section class="intro-screen">
<h1 class="trip-title">{PAGE_TITLE}</h1>
<p class="trip-subtitle">{TRIP_SUBTITLE}</p>
<p class="scroll-hint">Scroll or swipe down to start ↓</p>
</section>"""


def render_jump_menu(cutoff):
    if cutoff > TRIP_END:
        return ""

    groups = []
    for d in daterange(cutoff, TRIP_END):
        day_label = d.strftime("%a, %b ") + str(d.day)
        links = "".join(
            f'<a href="#{quarter_screen_id(d.isoformat(), q)}">{QUARTER_LABELS[q]}</a>' for q in QUARTERS
        )
        groups.append(
            f'<div class="jump-day-group"><span class="jump-day-label">{day_label}</span>'
            f'<div class="jump-links">{links}</div></div>'
        )

    return f"""<details class="jump-menu">
<summary>Jump ▾</summary>
<div class="jump-panel">{"".join(groups)}</div>
</details>"""


def render_nav(jump_menu):
    return f"""<nav class="site-nav">
<span class="current-quarter-label" id="current-quarter-label">{esc(PAGE_TITLE)}</span>
{jump_menu}
<a href="family-tree/index.html">Family Tree</a>
</nav>"""


def build_timeline_html(people, travel, meals, cutoff):
    people_by_id = {p["id"]: p for p in people}

    screens = [render_intro_screen()]

    if cutoff > TRIP_END:
        screens.append(
            '<section class="trip-done-screen"><p>The trip is over — thanks for a great one!</p></section>'
        )
    else:
        for d in daterange(cutoff, TRIP_END):
            for q in QUARTERS:
                screens.append(render_quarter_screen(d, q, travel, people_by_id, meals))

    return "\n".join(screens)


def build_page_html(people, travel, meals, shared_base_css, shared_css, shared_js, today=None):
    cutoff = max(today or date.today(), TRIP_START)
    jump_menu = render_jump_menu(cutoff)
    nav_row = render_nav(jump_menu)
    timeline_html = build_timeline_html(people, travel, meals, cutoff)
    return f"""<!DOCTYPE html>
<html lang="en" class="timeline-page">
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
<main>
{timeline_html}
</main>
<script>
{shared_js}
</script>
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
    shared_js = (ROOT / "shared.js").read_text()

    html = build_page_html(people, travel, meals, shared_base_css, shared_css, shared_js)
    out_path = PROJECT_ROOT / "site" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print("Updated site/index.html")


if __name__ == "__main__":
    main()
