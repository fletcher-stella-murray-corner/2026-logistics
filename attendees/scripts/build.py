#!/usr/bin/env python3
"""Regenerate site/attendees/ — the Attendees feature: one page per
attending person summarizing their own travel/room facts as a
chronological milestone list (arrive, sleep here for a stretch, sleep
there for a stretch, depart — not a night-by-night listing, see
room_milestones() below). No index page and no nav link of its own — a
person's page is reached by clicking them in the Family Tree (see
family-tree/scripts/build.py's render_person(), which links an attending
person's box straight to their site/attendees/<id>.html). People marked
attending: false don't get a page here at all — see the Family Tree for
the full family, attending or not.

Reads shared/data/people.json and timeline/data/travel.json. Nothing is
entered separately here — the facts shown are exactly the
arrival/departure/room fields already in that entry, the same single
source of truth the Timeline schedule is built from. That's deliberate:
updating travel.json updates both the schedule and a person's own facts
page at once, so there's no second copy of the data that could drift out
of sync (see requirements/public.md -> Attendees -> Data integrity). The
facts-collected/collecting-facts distinction (whether a travel.json entry
exists and isn't marked "pending": true) is computed and shown on the
Family Tree page, not here — this script doesn't need it.

Validated at build time: every person has an 'id' and 'name' (a friendly
message naming the record, not a raw KeyError, when one's missing);
every travel.json entry has a 'person_id'; `attending` must be present
and a boolean on every shared/data/people.json entry; a person marked
attending: false must not have a timeline/data/travel.json entry (a
contradiction).

Run after hand-editing shared/data/people.json or
timeline/data/travel.json, or use scripts/build_site.py to rebuild every
feature at once.

site/attendees/*.html are pure build artifacts — edit this template, not the HTML.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # attendees/
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


def nav_items_for_person():
    # Plain two-item row — no third "Attendees" item, since there's no
    # index/home page for this feature to link to or indicate as active
    # (see module docstring). "Tree" is the natural way back, since
    # that's where every person page is linked from.
    return [
        ("Timeline", "../index.html", False),
        ("Tree", "../family-tree/index.html", False),
    ]


def load_json(path):
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {path}: {e}") from e


def record_label(r, index, file_label):
    """A human-identifiable label for a record that might itself be missing
    'id' — falls back to its position in the array so a build error always
    points somewhere findable instead of just KeyError-ing."""
    if "id" in r:
        return f"Record id {r['id']!r} (index {index}) in {file_label}"
    return f"Record at index {index} in {file_label}"


def validate_required_fields(records, fields, file_label):
    for i, r in enumerate(records):
        label = record_label(r, i, file_label)
        for field in fields:
            nav.require(r, field, label)


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


def format_clock(hhmm):
    hour, minute = (int(part) for part in hhmm.split(":"))
    period = "am" if hour < 12 else "pm"
    hour12 = hour % 12 or 12
    return f"{hour12}{period}" if minute == 0 else f"{hour12}:{minute:02d}{period}"


def format_time_range(time_range):
    start, end = time_range
    return format_clock(start) if start == end else f"{format_clock(start)}–{format_clock(end)}"


def format_leg(leg):
    quarter_label = QUARTER_LABELS.get(leg["quarter"], leg["quarter"])
    time_range = leg.get("time_range")
    time_display = format_time_range(time_range) if time_range else quarter_label
    mode_label = MODE_TAGS.get(leg["mode"], leg["mode"])
    parts = [f"{leg['date']} · {time_display}", mode_label]
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
    listing. See requirements/public.md -> Attendees -> Layout."""
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
            '<p class="attendee-pending">We don’t have your travel details yet '
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
<h1 class="attendees-title">{esc(person['name'])}’s facts</h1>
<main>
{body}
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

    validate_required_fields(people, ["id", "name"], "shared/data/people.json")
    validate_required_fields(travel, ["person_id"], "timeline/data/travel.json")
    validate_people_attending(people)
    people_by_id = {p["id"]: p for p in people}
    validate_attendance_vs_travel(people_by_id, travel)

    travel_by_person_id = {entry["person_id"]: entry for entry in travel}

    out_dir = PROJECT_ROOT / "site" / "attendees"
    out_dir.mkdir(parents=True, exist_ok=True)

    attending_people = [p for p in people if p.get("attending")]
    for p in attending_people:
        entry = travel_by_person_id.get(p["id"])
        html = render_person_page(p, entry, shared_base_css, shared_css)
        (out_dir / f"{p['id']}.html").write_text(html)

    print(f"Updated site/attendees/ ({len(attending_people)} person page(s), no index — linked from the Family Tree)")


if __name__ == "__main__":
    main()
