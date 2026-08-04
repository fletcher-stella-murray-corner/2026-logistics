#!/usr/bin/env python3
"""Regenerate site/attendees/ — the Attendees feature: one page per
attending person summarizing their own travel/room facts as a single
chronological timeline, grouped under one day heading per distinct date —
not a night-by-night listing, and not grouped by kind of fact either (see
render_person_page() below): Arrival, Sleeping stretches, Working from
stretches, Departure, and Driving obligations are all sorted together by
date first, then bucketed under whichever day each one starts on, a
ranged fact (Sleeping/Working from) grouped under the FIRST date of its
range. No index page and no nav link of its own — a person's page is
reached by clicking them in the Family Tree (see
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

Also renders one "Working from" line per `working_from` block on the page
owner's own entry (see working_line() below and
requirements/public.md -> Data -> travel.json -> working_from) — sourced
straight from that entry, same single-source-of-truth guarantee as
Arrival/Sleeping/Departure above, just another kind of fact on it, and
merged into the same date-grouped timeline as everything else.

Also renders a "Driving" line for every OTHER person's leg where this
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
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # attendees/
PROJECT_ROOT = ROOT.parent  # repo root — site/ and shared/ live here

sys.path.insert(0, str(PROJECT_ROOT / "shared"))
import nav  # noqa: E402
from trip import TRIP_START, TRIP_END, QUARTER_NAMES, QUARTER_TIMES, MODE_TAGS, WORK_QUARTERS, format_time_range, format_date_full  # noqa: E402


def _import_build_module(name, path):
    """Load a sibling feature's build.py as a distinctly-named module —
    render_jump_panel() is timeline/scripts/build.py's, reused here rather
    than reimplemented so this page's nav bar (identical shape to every
    other page's — see requirements/public.md -> Navigation) can never
    drift from it. A plain `import build as X` (the pattern
    scripts/report.py uses for a single such cross-import) breaks the
    moment a script needs TWO different build.py files this way: Python's
    import cache keys on the module's own name ("build" either time), so
    the second `import build as ...` silently returns the first module
    again instead of loading the second file at all. Loading it under its
    own distinct name in sys.modules sidesteps that."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


timeline_build = _import_build_module("timeline_build", PROJECT_ROOT / "timeline" / "scripts" / "build.py")

TITLE_SUFFIX = " — Murray Corner 2026"


def esc(s):
    return nav.esc(s)


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


def time_label(leg):
    """The leading time-of-day text for a point-in-time fact line
    (Arrival/Departure/Driving — see fact_line() below): the exact
    time_range if one is set, otherwise the bare quarter name (e.g.
    "Afternoon"), falling back to the quarter's own bare time range for
    `00-06`, which has no name of its own (see requirements/public.md ->
    Terminology) — the same fallback rule the Timeline's live label and
    jump-to-time panel use."""
    time_range = leg.get("time_range")
    if time_range:
        return format_time_range(time_range)
    name = QUARTER_NAMES.get(leg["quarter"], "")
    return name if name else QUARTER_TIMES[leg["quarter"]]


def format_leg_body(leg, people_by_id, lead_with_by=False):
    """The rest of a leg's facts — mode, hub, vehicle, detail, driver —
    with no date/time (see time_label() above). Pre-escaped and joined,
    ready to drop straight into a fact_line()'s detail_html.
    `lead_with_by=True` prepends "by " to the mode (e.g. "by 🚗 Car"), for
    an Arrival/Departure line reading as a sentence ("5:15pm Arrival by
    🚗 Car") — left off for a Driving line, which already reads as one
    without it ("Rachel’s departure — ✈️ Plane — ...")."""
    mode_label = MODE_TAGS.get(leg["mode"], leg["mode"])
    parts = [f"by {mode_label}" if lead_with_by else mode_label]
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
    """Full natural-speech date — "Wednesday, August 5th" — this page has
    the room for it (see shared/trip.py -> format_date_full(), and
    requirements/public.md -> Navigation for why the Timeline's own nav
    label stays abbreviated instead). Critical that the weekday is never
    dropped on this page specifically, even inline mid-sentence: a family
    member checking their own facts needs the day of the week, not just
    the calendar date (see requirements/public.md -> Attendees ->
    Layout)."""
    return format_date_full(d)


def format_work_quarters(quarters):
    labels = {"06-12": "mornings", "12-18": "afternoons"}
    if set(quarters) == set(WORK_QUARTERS):
        return "mornings & afternoons"
    return " & ".join(labels[q] for q in WORK_QUARTERS if q in quarters)


def fact_line(time_text, label, detail_html):
    """One line under a day heading (see render_person_page() below) —
    every kind of fact (Arrival, Sleeping, Working from, Departure,
    Driving) renders through this one function. `time_text` is the exact
    time or bare quarter name leading a point-in-time fact (Arrival/
    Departure/Driving — see time_label() above); omitted (None) for a
    date-range fact (Sleeping/Working from), which has no single time of
    day to lead with — the line just starts at the label. `detail_html`
    is pre-escaped/joined HTML (from format_leg_body() or a plain
    esc()'d string) — not escaped again here."""
    time_html = f'<span class="fact-time">{esc(time_text)}</span> ' if time_text else ""
    return (
        '<div class="fact-line">'
        f'{time_html}<span class="fact-label">{esc(label)}</span> '
        f'<span class="fact-detail">{detail_html}</span>'
        "</div>"
    )


def sleeping_line(room, range_start, range_end):
    """A Sleeping fact's own line — the room, plus a "till <end day>"
    clause when the stretch spans more than one day (omitted for a
    single-day stretch, e.g. Susan's first night in the Master Suite —
    see requirements/public.md -> Attendees -> Layout)."""
    detail = esc(room) if room else "Unassigned"
    if range_end != range_start:
        detail += f" till {esc(format_date_label(range_end))}"
    return fact_line(None, "Sleeping", detail)


def working_line(block):
    """A Working from fact's own line — the structure, the quarters
    ("mornings & afternoons"), plus a "till <end day>" clause when the
    block spans more than one day (omitted for a single-day block)."""
    start = date.fromisoformat(block["start_date"])
    end = date.fromisoformat(block["end_date"])
    quarters = block.get("quarters", list(WORK_QUARTERS))
    detail = f"{esc(block['structure'])}, {esc(format_work_quarters(quarters))}"
    if end != start:
        detail += f", till {esc(format_date_label(end))}"
    return fact_line(None, "Working from", detail)


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
    room_milestones() below to skip. Unlike the bookend departure/arrival
    (sleeping_end_date() below), which count the calendar date itself as
    present because it's still preceded by a real night spent there, an
    excursion's depart date is never that: whatever time they leave, they
    aren't back at the accommodation again until the return leg, so the
    depart date itself is always the first away night — no quarter
    exception. The return date always counts as back, same as how the
    bookend arrival date always counts as present with no quarter
    adjustment. This deliberately shows a break for ANY excursion that
    crosses into a new calendar date, even a short one (e.g. leave one
    afternoon, back the next evening) — the point of a Sleeping-row gap is
    to show the person genuinely wasn't there for a stretch, not to hide
    it just because that stretch happened to be brief. Only a same-day
    round trip (depart and return on the identical date) produces no
    gap — away_start would be later than away_end, so nothing is added."""
    ranges = []
    for exc in entry.get("excursions", []):
        depart, ret = exc["depart"], exc["return"]
        away_start = date.fromisoformat(depart["date"])
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


def render_person_page(person, entry, travel, people_by_id, shared_base_css, shared_css, nav_row, shared_nav_js):
    title = f"{person['name']}{TITLE_SUFFIX}"

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
                fact_line(time_label(arrival), "Arrival", format_leg_body(arrival, people_by_id, lead_with_by=True)),
            ))
        else:
            items.append((
                TRIP_START.isoformat(),
                fact_line(None, "Arrival", "Already at the accommodation"),
            ))

        # Sleeping milestones — arrive, then one "Sleeping" line per
        # contiguous same-room stretch in date order. See room_milestones()
        # above.
        start_date = date.fromisoformat(arrival["date"]) if arrival else TRIP_START
        end_date = sleeping_end_date(departure)
        for room, range_start, range_end in room_milestones(entry, start_date, end_date):
            items.append((range_start.isoformat(), sleeping_line(room, range_start, range_end)))

        # One line per working_from block, keyed by its own start date — not
        # merged or re-split like the Sleeping milestones above, since a
        # block is already exactly the range the editor intended (see
        # requirements/public.md -> Attendees -> Layout).
        for block in entry.get("working_from", []):
            items.append((block["start_date"], working_line(block)))

        # Excursion legs — a mid-stay round trip (see requirements/public.md
        # -> Data -> travel.json -> excursions) — render exactly like the
        # bookend legs, just sorted into the middle of the timeline by
        # their own dates instead of always being first/last.
        for exc in entry.get("excursions", []):
            depart, ret = exc["depart"], exc["return"]
            items.append((
                depart["date"],
                fact_line(time_label(depart), "Departure", format_leg_body(depart, people_by_id, lead_with_by=True)),
            ))
            items.append((
                ret["date"],
                fact_line(time_label(ret), "Arrival", format_leg_body(ret, people_by_id, lead_with_by=True)),
            ))

        if departure:
            items.append((
                departure["date"],
                fact_line(time_label(departure), "Departure", format_leg_body(departure, people_by_id, lead_with_by=True)),
            ))
        else:
            items.append((
                TRIP_END.isoformat(),
                fact_line(None, "Departure", "Staying past this date"),
            ))

    # Driving obligations for OTHER people's legs — shown regardless of
    # whether this person has their own travel.json entry, since driving
    # someone else doesn't depend on your own travel status. Keyed by the
    # leg's own date, so it lands in the same timeline as everything else.
    for traveler, field, leg in driving_assignments(person["id"], travel, people_by_id):
        detail_html = f"{esc(traveler['name'])}’s {field} — {format_leg_body(leg, people_by_id)}"
        items.append((leg["date"], fact_line(time_label(leg), "Driving", detail_html)))

    if entry is None and not items:
        body = (
            '<p class="attendee-pending">We don’t have your travel details yet '
            '— check back soon, or let the organizers know your plans.</p>'
        )
    else:
        # Stable sort: items built in a sensible default order above
        # (Arrival, Sleeping, Working from, Departure, then Driving), so a
        # same-date tie keeps that relative order rather than an arbitrary
        # one — preserved by grouping below, since Python's sort is stable.
        items.sort(key=lambda item: item[0])

        # Group into one <h2> day heading per distinct date (see
        # requirements/public.md -> Attendees -> Layout) — sort_date is
        # always the exact date a fact's own heading belongs under (a
        # leg's date, or a milestone/block's own start date), so grouping
        # by exact equality needs no separate "which day does this belong
        # to" logic of its own.
        day_blocks = []
        current_date = None
        current_lines = []
        for sort_date, line_html in items:
            if sort_date != current_date:
                if current_lines:
                    day_blocks.append((current_date, current_lines))
                current_date = sort_date
                current_lines = []
            current_lines.append(line_html)
        if current_lines:
            day_blocks.append((current_date, current_lines))

        pending_note = (
            '<p class="attendee-pending">We don’t have your travel details yet '
            '— check back soon, or let the organizers know your plans.</p>'
            if entry is None else ""
        )
        body = pending_note + "".join(
            f'<h2 class="fact-day">{esc(format_date_label(date.fromisoformat(iso_date)))}</h2>' + "".join(lines)
            for iso_date, lines in day_blocks
        )

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
<script>
{shared_nav_js}
</script>
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
    shared_nav_js = (PROJECT_ROOT / "shared" / "nav.js").read_text()

    validate_required_fields(people, ["id", "name"], "shared/data/people.json")
    validate_required_fields(travel, ["person_id"], "timeline/data/travel.json")
    validate_people_attending(people)
    people_by_id = {p["id"]: p for p in people}
    validate_attendance_vs_travel(people_by_id, travel)

    travel_by_person_id = {entry["person_id"]: entry for entry in travel}

    out_dir = PROJECT_ROOT / "site" / "attendees"
    out_dir.mkdir(parents=True, exist_ok=True)

    attending_people = [p for p in people if p.get("attending")]

    # Same nav bar shape/content for every person's page — computed once,
    # not per page (see requirements/public.md -> Navigation): the Folks
    # panel (shared/nav.py -> render_folks_menu(), the same one every page
    # uses) and the day/quarter jump list (reused from timeline/scripts/
    # build.py, the feature that owns it), not reimplemented here.
    folks_menu = nav.render_folks_menu(people, travel, timeline_prefix="../index.html", attendees_prefix="")
    nav_row = nav.render_nav(
        mc26_href="../index.html#trip-top",
        timeline_prefix="../index.html",
        tree_href="../family-tree/index.html",
        trip_start=timeline_build.TRIP_START.isoformat(),
        trip_end=timeline_build.TRIP_END.isoformat(),
        jump_panel_html=timeline_build.render_jump_panel(href_prefix="../index.html"),
        folks_panel_html=folks_menu,
        attending_people=attending_people,
        attendees_prefix="",
        include_play=False,
    )

    for p in attending_people:
        entry = travel_by_person_id.get(p["id"])
        html = render_person_page(p, entry, travel, people_by_id, shared_base_css, shared_css, nav_row, shared_nav_js)
        (out_dir / f"{p['id']}.html").write_text(html)

    print(f"Updated site/attendees/ ({len(attending_people)} person page(s), no index — linked from the Family Tree)")


if __name__ == "__main__":
    main()
