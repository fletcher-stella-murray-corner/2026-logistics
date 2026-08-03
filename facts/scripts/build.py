#!/usr/bin/env python3
"""Regenerate site/facts/ — the Facts feature: one page per attending
person summarizing their own travel/room facts as a chronological
milestone list (arrive, sleep here for a stretch, sleep there for a
stretch, depart — not a night-by-night listing, see room_milestones()
below), plus an index page grouping everyone into the three states this
tracks (see requirements/public.md -> Facts): facts collected, facts
needed, not attending.

Reads shared/data/people.json and timeline/data/travel.json. Nothing is
entered separately here — a person's collected/needed status is computed
from whether they have a travel.json entry at all, and the facts shown
are exactly the arrival/departure/room fields already in that entry, the
same single source of truth the Timeline schedule is built from. That's
deliberate: updating travel.json updates both the schedule and a
person's own facts page at once, so there's no second copy of the data
that could drift out of sync (see requirements/public.md -> Facts ->
Data integrity).

Validated at build time: `attending` must be present and a boolean on
every shared/data/people.json entry; a person marked attending: false
must not have a timeline/data/travel.json entry (a contradiction).

Run after hand-editing shared/data/people.json or
timeline/data/travel.json, or use scripts/build_site.py to rebuild every
feature at once.

site/facts/*.html are pure build artifacts — edit this template, not the HTML.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # facts/
PROJECT_ROOT = ROOT.parent  # repo root — site/ and shared/ live here

sys.path.insert(0, str(PROJECT_ROOT / "shared"))
import nav  # noqa: E402

TITLE_SUFFIX = " — Murray Corner 2026"

TRIP_START = date(2026, 8, 1)
TRIP_END = date(2026, 8, 15)

QUARTER_LABELS = {
    "00-06": "Night · 12am–6am",
    "06-12": "Morning · 6am–12pm",
    "12-18": "Afternoon · 12pm–6pm",
    "18-24": "Evening · 6pm–12am",
}
MODE_TAGS = {
    "plane": "✈️ Plane",
    "train": "🚆 Train",
    "car": "🚗 Car",
}


def esc(s):
    return nav.esc(s)


def nav_items_for_index():
    return [
        ("Timeline", "../index.html", False),
        ("Tree", "../family-tree/index.html", False),
        ("Facts", None, True),
    ]


def nav_items_for_person():
    # "Facts" is a link back to the index here, not the active indicator —
    # a person page isn't the Facts feature's home, index.html is (see
    # nav_items_for_index above). Same directory as index.html, so the
    # bare filename is correct — unlike crossing from family-tree/ or
    # facts/ up to the site root, which needs "../" (see technical.md ->
    # Lessons learned for the bug that taught us to check this).
    return [
        ("Timeline", "../index.html", False),
        ("Tree", "../family-tree/index.html", False),
        ("Facts", "index.html", False),
    ]


def load_json(path):
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {path}: {e}") from e


def validate_people_attending(people):
    for p in people:
        if not isinstance(p.get("attending"), bool):
            raise ValueError(
                f"{p['name']!r} is missing a boolean 'attending' field in "
                f"shared/data/people.json — every person must be explicitly "
                f"marked true or false."
            )


def validate_attendance_vs_travel(people_by_id, travel):
    for entry in travel:
        person = people_by_id.get(entry["person_id"])
        if person is not None and person.get("attending") is False:
            raise ValueError(
                f"{person['name']!r} has a timeline/data/travel.json entry but is "
                f"marked attending: false in shared/data/people.json — remove one "
                f"or the other."
            )


def format_leg(leg):
    quarter_label = QUARTER_LABELS.get(leg["quarter"], leg["quarter"])
    mode_label = MODE_TAGS.get(leg["mode"], leg["mode"])
    parts = [f"{leg['date']} · {quarter_label}", mode_label]
    if leg.get("hub"):
        parts.append(leg["hub"])
    if leg.get("vehicle"):
        parts.append(leg["vehicle"])
    if leg.get("detail"):
        parts.append(leg["detail"])
    return " — ".join(esc(p) for p in parts)


def format_date_label(d):
    return d.strftime("%b ") + str(d.day)


def format_date_range(start, end):
    if start == end:
        return format_date_label(start)
    if start.month == end.month and start.year == end.year:
        return f"{start.strftime('%b ')}{start.day}–{end.day}"
    return f"{format_date_label(start)} – {format_date_label(end)}"


def room_milestones(entry, start_date, end_date):
    """Collapse a person's room/room_by_date into contiguous same-room date
    ranges, in chronological order — a milestone list (arrive, sleep here
    for a stretch, sleep there for a stretch, depart), not a night-by-night
    listing. See requirements/public.md -> Facts -> Layout."""
    milestones = []
    current_room = None
    current_start = None
    prev_d = None
    d = start_date
    while d <= end_date:
        room = entry.get("room_by_date", {}).get(d.isoformat(), entry.get("room", ""))
        if room != current_room:
            if current_room is not None:
                milestones.append((current_room, current_start, prev_d))
            current_room = room
            current_start = d
        prev_d = d
        d += timedelta(days=1)
    if current_room is not None:
        milestones.append((current_room, current_start, prev_d))
    return milestones


def render_person_page(person, entry, shared_base_css, shared_css):
    title = f"{person['name']}{TITLE_SUFFIX}"
    nav_row = nav.render_row(nav_items_for_person())

    if entry is None:
        body = (
            '<p class="facts-pending">We don’t have your travel details yet '
            '— check back soon, or let the organizers know your plans.</p>'
        )
    else:
        arrival = entry.get("arrival")
        departure = entry.get("departure")

        rows = []
        arrival_value = format_leg(arrival) if arrival else "Already at the accommodation before August 1"
        rows.append(f'<div class="fact-row"><span class="fact-label">Arrival:</span> {arrival_value}</div>')

        # Chronological milestones, not a flat "Room" block — arrive, then
        # one "Sleeping" row per contiguous same-room stretch in date order,
        # then depart. See room_milestones() above.
        start_date = date.fromisoformat(arrival["date"]) if arrival else TRIP_START
        end_date = date.fromisoformat(departure["date"]) if departure else TRIP_END
        for room, range_start, range_end in room_milestones(entry, start_date, end_date):
            room_label = esc(room) if room else "Unassigned"
            date_label = format_date_range(range_start, range_end)
            rows.append(
                '<div class="fact-row"><span class="fact-label">Sleeping:</span> '
                f'{room_label} <span class="fact-date-range">({date_label})</span></div>'
            )

        departure_value = format_leg(departure) if departure else "Staying past August 15"
        rows.append(f'<div class="fact-row"><span class="fact-label">Departure:</span> {departure_value}</div>')
        body = "".join(rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
{shared_base_css}
{shared_css}
</style>
</head>
<body>
{nav_row}
<h1 class="facts-title">{esc(person['name'])}’s facts</h1>
<main>
{body}
</main>
</body>
</html>
"""


def render_index_page(people, travel_by_person_id, shared_base_css, shared_css):
    nav_row = nav.render_row(nav_items_for_index())

    collected, needed, not_attending = [], [], []
    for p in sorted(people, key=lambda p: p["name"]):
        if not p.get("attending"):
            not_attending.append(p)
        elif p["id"] in travel_by_person_id:
            collected.append(p)
        else:
            needed.append(p)

    def linked_list(ppl):
        items = "".join(f'<li><a href="{p["id"]}.html">{esc(p["name"])}</a></li>' for p in ppl)
        return items or '<li class="facts-empty-hint">No one yet</li>'

    def plain_list(ppl):
        items = "".join(f'<li class="not-attending-name">{esc(p["name"])}</li>' for p in ppl)
        return items or '<li class="facts-empty-hint">No one</li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Facts{TITLE_SUFFIX}</title>
<style>
{shared_base_css}
{shared_css}
</style>
</head>
<body>
{nav_row}
<h1 class="facts-title">Facts</h1>
<p class="facts-subtitle">Who's got their travel details in, and who's still deciding</p>
<main>
<section class="facts-group">
<h2>Facts collected</h2>
<ul class="facts-list">{linked_list(collected)}</ul>
</section>
<section class="facts-group">
<h2>Facts needed</h2>
<ul class="facts-list">{linked_list(needed)}</ul>
</section>
<section class="facts-group">
<h2>Not attending</h2>
<ul class="facts-list">{plain_list(not_attending)}</ul>
</section>
</main>
</body>
</html>
"""


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    people = load_json(PROJECT_ROOT / "shared" / "data" / "people.json")
    travel = load_json(PROJECT_ROOT / "timeline" / "data" / "travel.json")
    shared_base_css = (PROJECT_ROOT / "shared" / "base.css").read_text()
    shared_css = (ROOT / "shared.css").read_text()

    validate_people_attending(people)
    people_by_id = {p["id"]: p for p in people}
    validate_attendance_vs_travel(people_by_id, travel)

    travel_by_person_id = {entry["person_id"]: entry for entry in travel}

    out_dir = PROJECT_ROOT / "site" / "facts"
    out_dir.mkdir(parents=True, exist_ok=True)

    attending_people = [p for p in people if p.get("attending")]
    for p in attending_people:
        entry = travel_by_person_id.get(p["id"])
        html = render_person_page(p, entry, shared_base_css, shared_css)
        (out_dir / f"{p['id']}.html").write_text(html)

    index_html = render_index_page(people, travel_by_person_id, shared_base_css, shared_css)
    (out_dir / "index.html").write_text(index_html)
    print(f"Updated site/facts/ ({len(attending_people)} person page(s) + index)")


if __name__ == "__main__":
    main()
