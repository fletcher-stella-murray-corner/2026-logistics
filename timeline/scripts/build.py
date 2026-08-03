#!/usr/bin/env python3
"""Regenerate site/index.html — the Timeline feature, which doubles as the
site's homepage (see requirements/public.md -> Homepage = Timeline).

Reads shared/data/people.json, shared/data/structures.json,
shared/data/vehicles.json, timeline/data/travel.json,
timeline/data/meals.json, and timeline/data/activities.json. Renders
August 1-15, 2026 split into four day quarters (6-hour segments) per
day, one full-viewport-height "quarter screen" per quarter, always
starting from max(today, Aug 1) so past days quietly drop off the site
on every rebuild — and, on that first rendered day, from the CURRENT
quarter of the actual time-of-day at build time (see quarter_for_hour()),
so e.g. rebuilding at 9pm doesn't still show three quarters of today
that have already passed.

Validated at build time, all as hard errors rather than silent typos:
every record in people.json/structures.json/vehicles.json/travel.json
has its required fields (a friendly message naming the record and field,
not a raw KeyError, when one's missing — likely during hand-editing);
every `room`/`room_by_date`/`hub` value in travel.json against
shared/data/structures.json — including, for a structure with a fixed
`rooms` list (e.g. Cottage), that the room detail is one of the declared
names, not arbitrary free text; every `vehicle` value against
shared/data/vehicles.json (see requirements/public.md -> Structures /
Vehicles); every `person_id` in travel.json against people.json, and
that no person_id appears more than once in travel.json (a duplicate —
e.g. from a copy/pasted entry with the id left unchanged — would
otherwise silently double-render that person everywhere); every
`date`/`quarter` value everywhere (travel.json, meals.json,
activities.json) for valid ISO-date/quarter-key shape; an arrival/
departure's optional `time_range` (24-hour HH:MM start/end estimate,
narrower than the full quarter — see requirements/public.md -> Data ->
time_range) for valid shape and that both times fall within their
quarter's window; a travel entry's
departure isn't before its arrival; a travel entry's optional `pending`
flag (see requirements/public.md -> Data -> travel.json -> pending) for
being a boolean when present; a structure's `rooms` list (if any)
is non-empty with no duplicates, and its `active_from`/`active_to` (if
set) are valid ISO dates with `active_to` not before `active_from`; and
ids are unique within people.json/structures.json/vehicles.json.

The nav bar is one single row: a live "current day quarter" label on the
left (updated by shared.js via IntersectionObserver as you scroll — the
weekday name prominent, the month/day + quarter smaller/secondary) that
doubles as the jump-to-time trigger — click/tap it to expand a disclosure
of every remaining day/quarter as links, rather than a separate "Jump ▾"
control — plus a "Folks ▾" disclosure, each entry showing the person's
name (plain text) and two labeled links: "Timeline" jumps to their
arrival's quarter screen, "Detail" goes to their own attendees page
instead (both the label's own links and these land via anchor,
independent of scroll-snap), a "▶"/"⏸" play/pause button that
auto-advances through every screen (see requirements/public.md ->
Navigation), and the Family Tree link on the right — no Attendees link;
an attendees page is reached via the Family Tree or the "Details" link
above, not a nav entry of its own.

Each quarter screen has two parts, per requirements/public.md ->
Terminology: a "day quarter canvas padding" spacer (blank space reserved
so the sticky nav bar doesn't cover real content), and the "day quarter
canvas" itself (the actual arrivals/departures/sleeping/meal/activities
rows — no date or time label, since the nav bar's live label already
shows that). The padding is explicitly NOT part of the canvas.

Run after hand-editing any of the data files above, or use
scripts/build_site.py to rebuild every feature at once.

site/index.html is a pure build artifact — edit this template, not the HTML.
"""
import json
import sys
from datetime import date, datetime, timedelta
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
    "00-06": "Night · 12am–6am",
    "06-12": "Morning · 6am–12pm",
    "12-18": "Afternoon · 12pm–6pm",
    "18-24": "Evening · 6pm–12am",
}
# Minute-of-day (0-1440) bounds for each quarter, used to sanity-check an
# optional time_range against the quarter it's attached to. Inclusive on
# both ends, so an exact boundary instant (e.g. "18:00") validates against
# either adjacent quarter — the quarter key itself is the source of truth
# for which one a leg belongs to, this just catches a time_range that's
# wildly inconsistent with the chosen quarter.
QUARTER_MINUTES = {
    "00-06": (0, 360),
    "06-12": (360, 720),
    "12-18": (720, 1080),
    "18-24": (1080, 1440),
}
MODE_TAGS = {
    "plane": "✈️ Plane",
    "train": "🚆 Train",
    "car": "🚗 Car",
}

def esc(s):
    return nav.esc(s)


def load_json(path):
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {path}: {e}") from e


def structure_names(structures, category):
    return {s["name"] for s in structures if s["category"] == category}


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


def validate_unique_ids(records, label):
    seen = set()
    for r in records:
        if r["id"] in seen:
            raise ValueError(f"Duplicate id {r['id']!r} in {label} — ids must be unique.")
        seen.add(r["id"])


def validate_structures_file(structures):
    validate_required_fields(structures, ["id", "name", "category"], "shared/data/structures.json")
    validate_unique_ids(structures, "shared/data/structures.json")
    for s in structures:
        if s["category"] not in ("accommodation", "transit"):
            raise ValueError(
                f"Invalid category {s['category']!r} for structure {s['name']!r} in "
                f"shared/data/structures.json — must be 'accommodation' or 'transit'."
            )
        rooms = s.get("rooms")
        if rooms is not None:
            if not rooms or len(set(rooms)) != len(rooms):
                raise ValueError(
                    f"Structure {s['name']!r} in shared/data/structures.json has an invalid "
                    f"'rooms' list — must be non-empty with no duplicate room names."
                )
        active_from = s.get("active_from")
        active_to = s.get("active_to")
        if active_from is not None:
            validate_date_str(active_from, f"active_from for structure {s['name']!r}")
        if active_to is not None:
            validate_date_str(active_to, f"active_to for structure {s['name']!r}")
        if active_from is not None and active_to is not None and active_to < active_from:
            raise ValueError(
                f"Structure {s['name']!r} in shared/data/structures.json has active_to "
                f"({active_to}) before active_from ({active_from})."
            )


def structure_active(structure, iso_date):
    start = structure.get("active_from") or TRIP_START.isoformat()
    end = structure.get("active_to") or TRIP_END.isoformat()
    return start <= iso_date <= end


def validate_vehicles_file(vehicles):
    validate_required_fields(vehicles, ["id", "name"], "shared/data/vehicles.json")
    validate_unique_ids(vehicles, "shared/data/vehicles.json")


def validate_people_file(people):
    validate_required_fields(people, ["id", "name"], "shared/data/people.json")
    validate_unique_ids(people, "shared/data/people.json")


def validate_date_str(value, context):
    try:
        date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid date {value!r} in {context} — must be an ISO date (YYYY-MM-DD).")


def validate_quarter_value(value, context):
    if value not in QUARTER_INDEX:
        raise ValueError(
            f"Invalid quarter {value!r} in {context} — must be one of {', '.join(QUARTERS)}."
        )


def parse_time_str(value, context):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":" \
            or not value[:2].isdigit() or not value[3:].isdigit():
        raise ValueError(
            f"Invalid time {value!r} in {context} — must be 24-hour HH:MM (e.g. '06:00', '18:30')."
        )
    hour, minute = int(value[:2]), int(value[3:])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid time {value!r} in {context} — hour must be 00-23 and minute 00-59.")
    return hour * 60 + minute


def validate_time_range(time_range, quarter, context):
    """Optional [start, end] 24-hour-time estimate narrower than the full
    quarter window (equal start/end means an exact time) — see
    requirements/public.md -> Data -> time_range. Omitted entirely means
    the full quarter window, the existing default behavior."""
    if time_range is None:
        return
    if not isinstance(time_range, list) or len(time_range) != 2:
        raise ValueError(
            f"time_range in {context} must be a two-item [start, end] list of 24-hour HH:MM times."
        )
    start, end = time_range
    start_min = parse_time_str(start, f"time_range start in {context}")
    end_min = parse_time_str(end, f"time_range end in {context}")
    if end_min < start_min:
        raise ValueError(f"time_range end ({end!r}) is before its start ({start!r}) in {context}.")
    q_start, q_end = QUARTER_MINUTES[quarter]
    if not (q_start <= start_min <= q_end) or not (q_start <= end_min <= q_end):
        raise ValueError(
            f"time_range {time_range!r} in {context} falls outside its quarter's window "
            f"({quarter}, {QUARTER_LABELS[quarter]}) — both times must fall within it."
        )


def validate_room(room, accommodation_structures, context):
    if not room:
        return
    for s in accommodation_structures:
        name = s["name"]
        if room == name:
            return
        prefix = f"{name} — "
        if room.startswith(prefix):
            declared_rooms = s.get("rooms")
            detail = room[len(prefix):]
            if declared_rooms and detail not in declared_rooms:
                raise ValueError(
                    f"Unknown room {detail!r} for structure {name!r} in room for {context} — "
                    f"{name!r} has a fixed rooms list, must be one of {', '.join(declared_rooms)}."
                )
            return
    raise ValueError(
        f"Unknown structure {room!r} in room for {context} — must exactly match an "
        f"accommodation name in shared/data/structures.json, or start with '<name> — '."
    )


def validate_hub(hub, transit_names, person_name, field):
    if hub is None:
        return
    if hub not in transit_names:
        raise ValueError(
            f"Unknown hub {hub!r} in {field} for {person_name!r} — must exactly match a "
            f"transit structure name in shared/data/structures.json."
        )


def validate_vehicle(vehicle, vehicle_names, person_name, field):
    if vehicle is None:
        return
    if vehicle not in vehicle_names:
        raise ValueError(
            f"Unknown vehicle {vehicle!r} in {field} for {person_name!r} — must exactly match "
            f"a vehicle name in shared/data/vehicles.json."
        )


def validate_leg(leg, person_name, field, transit_names, vehicle_names):
    if "date" not in leg or "quarter" not in leg:
        raise ValueError(f"Missing 'date' or 'quarter' in {field} for {person_name!r}.")
    validate_date_str(leg["date"], f"{field} for {person_name!r}")
    validate_quarter_value(leg["quarter"], f"{field} for {person_name!r}")
    validate_hub(leg.get("hub"), transit_names, person_name, field)
    validate_vehicle(leg.get("vehicle"), vehicle_names, person_name, field)
    validate_time_range(leg.get("time_range"), leg["quarter"], f"{field} for {person_name!r}")


def validate_travel(travel, people_by_id, structures, vehicles):
    accommodation_structures = [s for s in structures if s["category"] == "accommodation"]
    transit_names = structure_names(structures, "transit")
    vehicle_names = {v["name"] for v in vehicles}

    validate_required_fields(travel, ["person_id"], "timeline/data/travel.json")
    seen_person_ids = set()
    for entry in travel:
        person_id = entry["person_id"]
        if person_id in seen_person_ids:
            raise ValueError(
                f"person_id {person_id!r} appears more than once in timeline/data/travel.json "
                f"— each person may have only one entry (a duplicate silently double-renders "
                f"them everywhere). Merge the entries or remove the extra one."
            )
        seen_person_ids.add(person_id)

    for entry in travel:
        person_id = entry["person_id"]
        person = people_by_id.get(person_id)
        if person is None:
            raise ValueError(
                f"travel.json references person_id {person_id!r}, which doesn't exist in "
                f"shared/data/people.json."
            )
        person_name = person["name"]

        pending = entry.get("pending")
        if pending is not None and not isinstance(pending, bool):
            raise ValueError(f"pending in timeline/data/travel.json for {person_name!r} must be true or false.")

        arrival = entry.get("arrival")
        departure = entry.get("departure")
        if arrival:
            validate_leg(arrival, person_name, "arrival", transit_names, vehicle_names)
        if departure:
            validate_leg(departure, person_name, "departure", transit_names, vehicle_names)
        if arrival and departure:
            arrival_key = quarter_key(arrival["date"], arrival["quarter"])
            departure_key = quarter_key(departure["date"], departure["quarter"])
            if departure_key < arrival_key:
                raise ValueError(
                    f"Departure ({departure['date']} {departure['quarter']}) is before arrival "
                    f"({arrival['date']} {arrival['quarter']}) for {person_name!r}."
                )
        validate_room(entry.get("room", ""), accommodation_structures, person_name)
        for room_date, room in entry.get("room_by_date", {}).items():
            validate_date_str(room_date, f"room_by_date for {person_name!r}")
            validate_room(room, accommodation_structures, f"{person_name!r} on {room_date}")


def validate_day_quarter_notes(data, label):
    for day, quarters in data.items():
        validate_date_str(day, label)
        for q in quarters:
            validate_quarter_value(q, f"{label} on {day}")


def quarter_key(iso_date, quarter):
    return (iso_date, QUARTER_INDEX[quarter])


def quarter_for_hour(hour):
    """Which quarter a given hour-of-day (0-23) falls in — used to start
    the site at the CURRENT quarter of today, not the start of today, so
    e.g. loading the site at 9pm doesn't show three quarters that have
    already passed today (see requirements/public.md -> Auto-hiding past
    days and quarters)."""
    if hour < 6:
        return "00-06"
    if hour < 12:
        return "06-12"
    if hour < 18:
        return "12-18"
    return "18-24"


def quarter_screen_id(iso_date, quarter):
    return f"qc-{iso_date}-{quarter}"


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def format_clock(hhmm):
    hour, minute = (int(part) for part in hhmm.split(":"))
    period = "am" if hour < 12 else "pm"
    hour12 = hour % 12 or 12
    return f"{hour12}{period}" if minute == 0 else f"{hour12}:{minute:02d}{period}"


def format_time_range(time_range):
    start, end = time_range
    return format_clock(start) if start == end else f"{format_clock(start)}–{format_clock(end)}"


def travel_detail(entry):
    parts = []
    time_range = entry.get("time_range")
    if time_range:
        parts.append(format_time_range(time_range))
    label = entry.get("hub") or entry.get("vehicle")
    if label:
        parts.append(label)
    detail = entry.get("detail")
    if detail:
        parts.append(detail)
    return " · ".join(parts)


def room_for_date(entry, iso_date):
    return entry.get("room_by_date", {}).get(iso_date, entry.get("room", ""))


def parse_room(room, accommodation_structures):
    """Split a validated room string into (structure_name, detail) — detail
    is None for a bare structure name or an unset room (see
    requirements/public.md -> Sleeping -> Nested box display)."""
    if not room:
        return None, None
    for s in accommodation_structures:
        name = s["name"]
        if room == name:
            return name, None
        prefix = f"{name} — "
        if room.startswith(prefix):
            return name, room[len(prefix):]
    return room, None


def render_sleeping_row(present, accommodation_structures, day_iso):
    by_structure = {}
    for p, room in present:
        structure, detail = parse_room(room, accommodation_structures)
        by_structure.setdefault(structure, {}).setdefault(detail, []).append(p["name"])

    # A structure with a fixed `rooms` list is a real, physical place that
    # doesn't disappear just because nobody's currently assigned to one of
    # its rooms — every declared room always gets a box (empty or not) for
    # as long as the structure itself is active (see requirements/public.md
    # -> Structures -> Active range and Sleeping -> Nested box display).
    # Structures without a `rooms` list keep the old occupancy-only
    # behavior (e.g. Tent/Camper Van, which are free-text-instance places).
    for s in accommodation_structures:
        rooms = s.get("rooms")
        if not rooms or not structure_active(s, day_iso):
            continue
        bucket = by_structure.setdefault(s["name"], {})
        for room_name in rooms:
            bucket.setdefault(room_name, [])

    if not by_structure:
        return ""

    def sort_key(k):
        return (k is None, k or "")

    boxes = []
    for structure in sorted(by_structure, key=sort_key):
        by_detail = by_structure[structure]
        if structure is None:
            names = sorted(by_detail[None])
            boxes.append(
                '<div class="structure-box unassigned-box">'
                '<span class="structure-label">Unassigned</span>'
                f'<span class="room-people">{esc(", ".join(names))}</span>'
                '</div>'
            )
            continue

        inner = []
        for detail in sorted(by_detail, key=sort_key):
            names = sorted(by_detail[detail])
            if detail is None:
                inner.append(f'<span class="room-people">{esc(", ".join(names))}</span>')
            else:
                inner.append(
                    '<div class="room-box">'
                    f'<span class="room-label">{esc(detail)}</span>'
                    f'<span class="room-people">{esc(", ".join(names))}</span>'
                    '</div>'
                )
        boxes.append(
            '<div class="structure-box">'
            f'<span class="structure-label">{esc(structure)}</span>'
            f'<div class="structure-rooms">{"".join(inner)}</div>'
            '</div>'
        )

    return (
        '<div class="quarter-row"><span class="quarter-row-label">Sleeping:</span>'
        f'<div class="structure-boxes">{"".join(boxes)}</div></div>'
    )


def render_quarter_screen(day, quarter, travel, people_by_id, meals, activities, accommodation_structures):
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
            present.append((person, room_for_date(entry, day.isoformat())))

    rows = []

    if arrivals:
        lines = "".join(
            f'<span class="person-line">'
            f'<span class="mode-tag">{esc(MODE_TAGS.get(a["mode"], a["mode"]))}</span>'
            f'{esc(p["name"])} — {esc(travel_detail(a))}'
            f"</span>"
            for p, a in arrivals
        )
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Arriving:</span>{lines}</div>')

    if departures:
        lines = "".join(
            f'<span class="person-line">'
            f'<span class="mode-tag">{esc(MODE_TAGS.get(d["mode"], d["mode"]))}</span>'
            f'{esc(p["name"])} — {esc(travel_detail(d))}'
            f"</span>"
            for p, d in departures
        )
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Departing:</span>{lines}</div>')

    sleeping_row = render_sleeping_row(present, accommodation_structures, day.isoformat())
    if sleeping_row:
        rows.append(sleeping_row)

    meal = meals.get(day.isoformat(), {}).get(quarter)
    if meal:
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Meal:</span> {esc(meal)}</div>')

    activity = activities.get(day.isoformat(), {}).get(quarter)
    if activity:
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Activities:</span> {esc(activity)}</div>')

    body = "".join(rows) if rows else '<div class="quarter-empty-hint">Nothing scheduled</div>'
    # Split into two pieces (see render_nav() and timeline/shared.js): the
    # full weekday name, shown prominent, and the month/day + quarter
    # label, shown smaller/secondary — rather than one flat string, per
    # the requested nav-bar typography (day name is what you actually
    # scan for while scrolling; the date is supporting detail).
    day_name = day.strftime("%A")
    date_quarter = day.strftime("%b ") + str(day.day) + " · " + QUARTER_LABELS[quarter]

    return f"""<section class="quarter-screen" id="{quarter_screen_id(day.isoformat(), quarter)}" \
data-day-name="{esc(day_name)}" data-date-quarter="{esc(date_quarter)}">
<div class="quarter-canvas-padding"></div>
<div class="quarter-canvas">
{body}
</div>
</section>"""


def render_intro_screen():
    return f"""<section class="intro-screen">
<h1 class="trip-title">{PAGE_TITLE}</h1>
<p class="trip-subtitle">{TRIP_SUBTITLE}</p>
<p class="scroll-hint">Scroll or swipe down to start ↓</p>
</section>"""


def quarters_from(current_quarter):
    """The quarter keys from current_quarter through the end of the day, in
    order — QUARTERS itself when current_quarter is None (a day after the
    cutoff day, always rendered/linked in full)."""
    if current_quarter is None:
        return QUARTERS
    return QUARTERS[QUARTER_INDEX[current_quarter]:]


def render_jump_panel(cutoff, current_quarter):
    """Inner jump-to-time content only (no <details>/<summary> wrapper) —
    the current-quarter-label itself is the disclosure trigger this sits
    behind, not a separate "Jump ▾" control, see render_nav() below."""
    if cutoff > TRIP_END:
        return ""

    groups = []
    for d in daterange(cutoff, TRIP_END):
        day_label = d.strftime("%a, %b ") + str(d.day)
        quarters = quarters_from(current_quarter) if d == cutoff else QUARTERS
        links = "".join(
            f'<a href="#{quarter_screen_id(d.isoformat(), q)}">{QUARTER_LABELS[q]}</a>' for q in quarters
        )
        groups.append(
            f'<div class="jump-day-group"><span class="jump-day-label">{day_label}</span>'
            f'<div class="jump-links">{links}</div></div>'
        )

    return "".join(groups)


def render_folks_menu(travel, people_by_id, cutoff, current_quarter):
    """Jump-to-person, labeled "Folks" — each entry shows the person's name
    (plain text, not itself a link) plus two labeled links: "Timeline"
    jumps to wherever they first appear (their arrival's quarter screen if
    it's still being rendered, otherwise the very first quarter screen
    currently shown, covering "arrived before the rendering window
    starts", "no arrival at all", and today's already-past quarters being
    skipped, see quarter_for_hour()), and "Detail" goes to their own
    attendees page (site/attendees/<id>.html, see
    attendees/scripts/build.py) instead — see requirements/public.md ->
    Navigation."""
    if cutoff > TRIP_END or not travel:
        return ""

    first_quarter = current_quarter or "00-06"
    first_key = quarter_key(cutoff.isoformat(), first_quarter)
    entries = []
    for entry in travel:
        person = people_by_id.get(entry["person_id"])
        if person is None:
            continue
        arrival = entry.get("arrival")
        if arrival and quarter_key(arrival["date"], arrival["quarter"]) >= first_key:
            target_date, target_quarter = arrival["date"], arrival["quarter"]
        else:
            target_date, target_quarter = cutoff.isoformat(), first_quarter
        entries.append((person["name"], person["id"], target_date, target_quarter))

    if not entries:
        return ""

    entries.sort(key=lambda e: e[0])
    links = "".join(
        f'<span class="jump-person">'
        f'<span class="jump-person-name">{esc(name)}</span>'
        f'<a href="#{quarter_screen_id(d, q)}">Timeline</a>'
        f'<a href="attendees/{pid}.html" class="jump-person-details">Detail</a>'
        f'</span>'
        for name, pid, d, q in entries
    )
    return f"""<details class="jump-menu">
<summary>Folks ▾</summary>
<div class="jump-panel"><div class="jump-links">{links}</div></div>
</details>"""


def render_nav(jump_panel, folks_menu):
    """The live current-quarter label doubles as the jump-to-time trigger —
    click/tap it to expand the same day/quarter link list a separate
    "Jump ▾" control used to hold (see requirements/public.md ->
    Navigation). Only made an expandable <details> when there's actually
    something to jump to (jump_panel non-empty, i.e. the trip hasn't
    ended) — otherwise it's a plain, non-interactive label, same as
    before "Jump ▾" would have been omitted entirely in that case."""
    day_date_html = (
        f'<span class="cq-day" id="cq-day">{esc(PAGE_TITLE)}</span>'
        f'<span class="cq-date" id="cq-date"></span>'
    )
    if jump_panel:
        label_html = (
            # "jump-menu" too — reuses shared.js's existing smooth-scroll-
            # and-close wiring (querySelectorAll('.jump-menu')) and the
            # cursor/marker-hiding CSS it already gets for free; the
            # "current-quarter-menu" flex-sizing rule is later in
            # timeline/shared.css so it correctly wins over
            # ".jump-menu { flex-shrink: 0 }" for this element specifically.
            '<details class="jump-menu current-quarter-menu">'
            f'<summary id="current-quarter-label">{day_date_html}<span class="cq-caret">▾</span></summary>'
            f'<div class="jump-panel">{jump_panel}</div>'
            '</details>'
        )
    else:
        label_html = f'<span class="current-quarter-label" id="current-quarter-label">{day_date_html}</span>'
    return f"""<nav class="site-nav">
{label_html}
{folks_menu}
<button type="button" id="run-toggle" class="run-toggle" aria-label="Play">▶</button>
<a href="family-tree/index.html">Tree</a>
</nav>"""


def build_timeline_html(people, travel, meals, activities, cutoff, accommodation_structures, current_quarter):
    people_by_id = {p["id"]: p for p in people}

    screens = [render_intro_screen()]

    if cutoff > TRIP_END:
        screens.append(
            '<section class="trip-done-screen"><p>The trip is over — thanks for a great one!</p></section>'
        )
    else:
        for d in daterange(cutoff, TRIP_END):
            quarters = quarters_from(current_quarter) if d == cutoff else QUARTERS
            for q in quarters:
                screens.append(render_quarter_screen(d, q, travel, people_by_id, meals, activities, accommodation_structures))

    return "\n".join(screens)


def build_page_html(people, travel, meals, activities, structures, shared_base_css, shared_css, shared_js, now=None):
    now = now or datetime.now()
    today = now.date()
    cutoff = max(today, TRIP_START)
    # Only meaningful for the cutoff day itself — a future cutoff day (the
    # trip hasn't started yet) or any day after it always renders/links in
    # full, so current_quarter is None (see quarters_from() above).
    current_quarter = quarter_for_hour(now.hour) if cutoff == today else None
    people_by_id = {p["id"]: p for p in people}
    jump_panel = render_jump_panel(cutoff, current_quarter)
    folks_menu = render_folks_menu(travel, people_by_id, cutoff, current_quarter)
    nav_row = render_nav(jump_panel, folks_menu)
    accommodation_structures = [s for s in structures if s["category"] == "accommodation"]
    timeline_html = build_timeline_html(people, travel, meals, activities, cutoff, accommodation_structures, current_quarter)
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
    structures = load_json(PROJECT_ROOT / "shared" / "data" / "structures.json")
    vehicles = load_json(PROJECT_ROOT / "shared" / "data" / "vehicles.json")
    travel = load_json(ROOT / "data" / "travel.json")
    meals = load_json(ROOT / "data" / "meals.json")
    activities = load_json(ROOT / "data" / "activities.json")
    shared_base_css = (PROJECT_ROOT / "shared" / "base.css").read_text()
    shared_css = (ROOT / "shared.css").read_text()
    shared_js = (ROOT / "shared.js").read_text()

    validate_people_file(people)
    validate_structures_file(structures)
    validate_vehicles_file(vehicles)

    people_by_id = {p["id"]: p for p in people}
    validate_travel(travel, people_by_id, structures, vehicles)
    validate_day_quarter_notes(meals, "timeline/data/meals.json")
    validate_day_quarter_notes(activities, "timeline/data/activities.json")

    html = build_page_html(people, travel, meals, activities, structures, shared_base_css, shared_css, shared_js)
    out_path = PROJECT_ROOT / "site" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print("Updated site/index.html")


if __name__ == "__main__":
    main()
