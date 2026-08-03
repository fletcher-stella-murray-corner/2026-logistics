#!/usr/bin/env python3
"""Regenerate site/attendees/ — the Attendees feature: one page per
attending person summarizing their own travel/room facts as a single
chronological timeline — not a night-by-night listing, and not grouped by
kind of fact either (see render_person_page() below): Arrival, Sleeping
stretches, Working from stretches, Departure, and Driving obligations are
all sorted together by date, a ranged fact (Sleeping/Working from) sorted
by the FIRST date of its range. No index page and no nav link of its own
— a person's page is reached by clicking them in the Family Tree (see
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

Also renders one "Working from" row per `working_from` block on the page
owner's own entry (see format_work_date() below and
requirements/public.md -> Data -> travel.json -> working_from) — sourced
straight from that entry, same single-source-of-truth guarantee as
Arrival/Sleeping/Departure above, just another kind of fact on it, and
merged into the same date-sorted timeline as everything else.

Also renders a "Driving" row for every OTHER person's leg where this
person is set as `driver_id` (see driving_assignments() below and
requirements/public.md -> Data -> travel.json -> driver_id) — this is the
one thing on this page NOT sourced from the page owner's own travel.json
entry, since a driving obligation is a fact about the driver, not just
about the traveler, and needs to show up on both pages from one piece of
data rather than as prose only the traveler's page would ever show.

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
from trip import TRIP_START, TRIP_END, QUARTER_LABELS, MODE_TAGS, WORK_QUARTERS, format_time_range  # noqa: E402

TITLE_SUFFIX = " — Murray Corner 2026"


def esc(s):
    return nav.esc(s)


def nav_items_for_person():
    # Plain two-item row — no third "Attendees" item, since there's no
    # index/home page for this feature to link to or indicate as active
    # (see module docstring). "Tree" is the natural way back, since
    # that's where every person page is linked from. "Murray Corner 2026"
    # is the site-wide permanent home link (see requirements/public.md ->
    # Navigation), same label/href every page uses to get back to the
    # Timeline.
    return [
        ("Murray Corner 2026", "../index.html", False),
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


def format_leg_date(leg):
    """Just the date+time portion of a leg, formatted the same way every
    other row's date column is (see fact_row() below) — kept separate from
    format_leg_body() so every fact-row on this page can lead with a
    consistently-positioned, consistently-formatted date, rather than the
    old flat-string format where the date led on Arrival/Departure but was
    buried mid-string or in parentheses on Sleeping/Working from/Driving."""
    d = date.fromisoformat(leg["date"])
    quarter_label = QUARTER_LABELS.get(leg["quarter"], leg["quarter"])
    time_range = leg.get("time_range")
    time_display = format_time_range(time_range) if time_range else quarter_label
    return f"{format_date_label(d)} · {time_display}"


def format_leg_body(leg, people_by_id):
    """The rest of a leg's facts — mode, hub, vehicle, detail, driver —
    with no date/time (see format_leg_date() above). Pre-escaped and
    joined, ready to drop straight into a fact_row()'s detail_html."""
    mode_label = MODE_TAGS.get(leg["mode"], leg["mode"])
    parts = [mode_label]
    if leg.get("hub"):
        parts.append(leg["hub"])
    if leg.get("vehicle"):
        parts.append(leg["vehicle"])
    if leg.get("detail"):
        parts.append(leg["detail"])
    driver = people_by_id.get(leg.get("driver_id"))
    if driver:
        parts.append(f"{driver['name']} driving")
    return " — ".join(esc(p) for p in parts)


def format_date_label(d):
    return d.strftime("%b ") + str(d.day)


def format_date_range(start, end):
    if start == end:
        return format_date_label(start)
    if start.month == end.month and start.year == end.year:
        return f"{start.strftime('%b ')}{start.day}–{end.day}"
    return f"{format_date_label(start)} – {format_date_label(end)}"


def format_work_quarters(quarters):
    labels = {"06-12": "mornings", "12-18": "afternoons"}
    if set(quarters) == set(WORK_QUARTERS):
        return "mornings & afternoons"
    return " & ".join(labels[q] for q in WORK_QUARTERS if q in quarters)


def format_work_date(block):
    start = date.fromisoformat(block["start_date"])
    end = date.fromisoformat(block["end_date"])
    quarters = block.get("quarters", list(WORK_QUARTERS))
    return f"{format_date_range(start, end)} · {format_work_quarters(quarters)}"


def fact_row(date_text, label, detail_html):
    """One row of the person's page timeline (see render_person_page()) —
    every kind of fact (Arrival, Sleeping, Working from, Departure,
    Driving) renders through this one function, so the date always leads
    in the same position and the same format instead of sometimes first
    and sometimes buried mid-string. `detail_html` is pre-escaped/joined
    HTML (from format_leg_body() or a plain esc()'d string) — not escaped
    again here."""
    return (
        '<div class="fact-row">'
        f'<span class="fact-date">{esc(date_text)}</span>'
        f'<span class="fact-label">{esc(label)}</span>'
        f'<span class="fact-detail">{detail_html}</span>'
        "</div>"
    )


def sleeping_end_date(departure):
    """The last calendar date someone actually has a sleeping assignment —
    mirrors the Timeline's own per-quarter presence check (`key <
    departure_key` in timeline/scripts/build.py's render_quarter_screen()):
    if the departure quarter is "00-06", the very first quarter of that
    date, the person isn't present in any quarter of the departure date at
    all, so the last sleeping date is the day before. Without this, the
    milestone walk below would show a trailing one-day "sleeping" range on
    a date the person was never actually there for."""
    if departure is None:
        return TRIP_END
    d = date.fromisoformat(departure["date"])
    if departure["quarter"] == "00-06":
        return d - timedelta(days=1)
    return d


def excursion_away_ranges(entry):
    """The date range(s) a person is away on an excursion (see
    requirements/public.md -> Data -> travel.json -> excursions), for
    room_milestones() below to skip. Mirrors sleeping_end_date()'s own
    quarter-based rule for the bookend departure: the depart date itself
    still counts as present unless its quarter is "00-06" (gone before any
    of it); the return date always counts as back, same as how the
    bookend arrival date always counts as present with no quarter
    adjustment — so the away range is exclusive of both ends."""
    ranges = []
    for exc in entry.get("excursions", []):
        depart, ret = exc["depart"], exc["return"]
        away_start = date.fromisoformat(depart["date"])
        if depart["quarter"] != "00-06":
            away_start += timedelta(days=1)
        away_end = date.fromisoformat(ret["date"]) - timedelta(days=1)
        if away_start <= away_end:
            ranges.append((away_start, away_end))
    return ranges


def room_milestones(entry, start_date, end_date):
    """Collapse a person's room/room_by_date into contiguous same-room date
    ranges, in chronological order — a milestone list (arrive, sleep here
    for a stretch, sleep there for a stretch, depart), not a night-by-night
    listing. See requirements/public.md -> Attendees -> Layout. Dates
    covered by an excursion (see excursion_away_ranges() above) are
    skipped entirely, splitting the stay into two milestones with a gap
    rather than one range that wrongly includes time the person was away
    — the excursion's own Departure/Arrival rows already say so."""
    away_ranges = excursion_away_ranges(entry)

    def is_away(d):
        return any(start <= d <= end for start, end in away_ranges)

    milestones = []
    current_room = None
    current_start = None
    prev_d = None
    d = start_date
    while d <= end_date:
        if is_away(d):
            if current_room is not None:
                milestones.append((current_room, current_start, prev_d))
                current_room = None
            d += timedelta(days=1)
            continue
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


def driving_assignments(person_id, travel, people_by_id):
    """Every arrival/departure leg — across EVERYONE's travel.json entries,
    not just this person's own — where this person is named as `driver_id`.
    Surfaced as extra rows on the driver's own page below; otherwise a
    driving obligation only ever shows up on the traveler's own page (as
    part of their formatted leg, see format_leg_body() above), never on the
    driver's, even though it's just as much the driver's fact to know as
    the traveler's (see requirements/public.md -> Attendees -> Layout ->
    Driving)."""
    assignments = []
    for entry in travel:
        traveler = people_by_id.get(entry["person_id"])
        if traveler is None:
            continue
        for field in ("arrival", "departure"):
            leg = entry.get(field)
            if leg and leg.get("driver_id") == person_id:
                assignments.append((traveler, field, leg))
        for exc in entry.get("excursions", []):
            for field, leg in (("excursion departure", exc["depart"]), ("excursion return", exc["return"])):
                if leg.get("driver_id") == person_id:
                    assignments.append((traveler, field, leg))
    assignments.sort(key=lambda a: (a[2]["date"], a[2]["quarter"]))
    return assignments


def render_person_page(person, entry, travel, people_by_id, shared_base_css, shared_css):
    title = f"{person['name']}{TITLE_SUFFIX}"
    nav_row = nav.render_row(nav_items_for_person())

    # One flat list of (sort_date, html) across every kind of fact on this
    # page — Arrival/Sleeping/Departure/Working from/Driving — sorted into
    # a single true timeline instead of one block per kind (grouping them
    # by kind put a same-week Driving or Working from entry after a much
    # later Departure, reading out of order). sort_date is always the
    # FIRST date of a range for a ranged fact (a Sleeping/Working from
    # stretch) — see requirements/public.md -> Attendees -> Layout.
    items = []

    if entry is not None:
        arrival = entry.get("arrival")
        departure = entry.get("departure")

        if arrival:
            items.append((
                arrival["date"],
                fact_row(format_leg_date(arrival), "Arrival", format_leg_body(arrival, people_by_id)),
            ))
        else:
            items.append((
                TRIP_START.isoformat(),
                fact_row(format_date_label(TRIP_START), "Arrival", "Already at the accommodation"),
            ))

        # Sleeping milestones — arrive, then one "Sleeping" row per
        # contiguous same-room stretch in date order. See room_milestones()
        # above.
        start_date = date.fromisoformat(arrival["date"]) if arrival else TRIP_START
        end_date = sleeping_end_date(departure)
        for room, range_start, range_end in room_milestones(entry, start_date, end_date):
            room_label = esc(room) if room else "Unassigned"
            items.append((
                range_start.isoformat(),
                fact_row(format_date_range(range_start, range_end), "Sleeping", room_label),
            ))

        # One row per working_from block, keyed by its own start date — not
        # merged or re-split like the Sleeping milestones above, since a
        # block is already exactly the range the editor intended (see
        # requirements/public.md -> Attendees -> Layout).
        for block in entry.get("working_from", []):
            items.append((
                block["start_date"],
                fact_row(format_work_date(block), "Working from", esc(block["structure"])),
            ))

        # Excursion legs — a mid-stay round trip (see requirements/public.md
        # -> Data -> travel.json -> excursions) — render exactly like the
        # bookend legs, just sorted into the middle of the timeline by
        # their own dates instead of always being first/last.
        for exc in entry.get("excursions", []):
            depart, ret = exc["depart"], exc["return"]
            items.append((
                depart["date"],
                fact_row(format_leg_date(depart), "Departure", format_leg_body(depart, people_by_id)),
            ))
            items.append((
                ret["date"],
                fact_row(format_leg_date(ret), "Arrival", format_leg_body(ret, people_by_id)),
            ))

        if departure:
            items.append((
                departure["date"],
                fact_row(format_leg_date(departure), "Departure", format_leg_body(departure, people_by_id)),
            ))
        else:
            items.append((
                TRIP_END.isoformat(),
                fact_row(format_date_label(TRIP_END), "Departure", "Staying past this date"),
            ))

    # Driving obligations for OTHER people's legs — shown regardless of
    # whether this person has their own travel.json entry, since driving
    # someone else doesn't depend on your own travel status. Keyed by the
    # leg's own date, so it lands in the same timeline as everything else.
    for traveler, field, leg in driving_assignments(person["id"], travel, people_by_id):
        detail_html = f"{esc(traveler['name'])}’s {field} — {format_leg_body(leg, people_by_id)}"
        items.append((leg["date"], fact_row(format_leg_date(leg), "Driving", detail_html)))

    if entry is None and not items:
        body = (
            '<p class="attendee-pending">We don’t have your travel details yet '
            '— check back soon, or let the organizers know your plans.</p>'
        )
    else:
        # Stable sort: items built in a sensible default order above
        # (Arrival, Sleeping, Working from, Departure, then Driving), so a
        # same-date tie keeps that relative order rather than an arbitrary
        # one.
        items.sort(key=lambda item: item[0])
        pending_note = (
            '<p class="attendee-pending">We don’t have your travel details yet '
            '— check back soon, or let the organizers know your plans.</p>'
            if entry is None else ""
        )
        body = pending_note + "".join(html for _, html in items)

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
<h1 class="attendees-title">{esc(person['name'])}</h1>
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
        html = render_person_page(p, entry, travel, people_by_id, shared_base_css, shared_css)
        (out_dir / f"{p['id']}.html").write_text(html)

    print(f"Updated site/attendees/ ({len(attending_people)} person page(s), no index — linked from the Family Tree)")


if __name__ == "__main__":
    main()
