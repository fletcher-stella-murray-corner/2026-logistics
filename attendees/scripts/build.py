#!/usr/bin/env python3
"""Regenerate site/attendees/ — the Attendees feature: one page per
attending person summarizing their own travel/room facts as a single
chronological timeline, grouped under one day heading per distinct date —
not a night-by-night listing, and not grouped by kind of fact either (see
render_person_page() below): Arrival, Sleeping stretches, Working from
days, Departure, and Driving obligations are all sorted together by date
first, then bucketed under whichever day each one falls on. Sleeping is
the only RANGED fact — grouped under the FIRST date of its range, with
the line itself stating a "till <end day>" clause. Working from is
deliberately NOT ranged this way despite its data also being a date
range: it's a fact about one specific day, true or not true that day, so
it renders as its own line under EVERY day it covers, one line per
calendar date, never summarized into a single range line (see
working_line() below). No index page and no nav link of its own — a
person's page is
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

Also renders one "Working from" line per DAY covered by each
`working_from` block on the page owner's own entry (see working_line()
below and requirements/public.md -> Data -> travel.json -> working_from)
— sourced straight from that entry, same single-source-of-truth guarantee
as Arrival/Sleeping/Departure above, just another kind of fact on it, and
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
    """Natural-speech date, full weekday + abbreviated month — "Wednesday,
    Aug 5th" (see shared/trip.py -> format_date_full(), and
    requirements/public.md -> Navigation for why the Timeline's own nav
    label abbreviates the weekday too instead). Critical that the weekday
    is never dropped on this page specifically, even inline mid-sentence:
    a family member checking their own facts needs the day of the week,
    not just the calendar date (see requirements/public.md -> Attendees
    -> Layout)."""
    return format_date_full(d)


def format_work_quarters(quarters):
    labels = {"06-12": "mornings", "12-18": "afternoons"}
    if set(quarters) == set(WORK_QUARTERS):
        return "mornings & afternoons"
    return " & ".join(labels[q] for q in WORK_QUARTERS if q in quarters)


FACT_RANK = {"Arrival": 0, "Airport run": 1, "Sleeping": 2, "Working from": 3, "Departure": 4, "Driving": 5}
"""The tie-break order for two facts landing on the exact same date (see
requirements/public.md -> Attendees -> Layout) — a causal order, not an
arbitrary one: you can't be asleep/working somewhere before the Arrival
that puts you there, and a still-running Sleeping/Working from stretch
always precedes the Departure that ends it. Used as an explicit sort key
below rather than relying on `items`' own append order, because append
order alone gets this wrong for an excursion's `return` (an Arrival) or
`depart` (a Departure) — those are appended in their own excursions loop,
which runs AFTER the Sleeping-milestones loop, so a same-date tie between
an excursion return and a Sleeping milestone starting that same day would
stable-sort with Sleeping first purely because of loop order, not because
that's the correct story (you arrive back, THEN that's where you sleep)."""


def fact_line(time_text, label, detail_html):
    """One line under a day heading (see render_person_page() below) —
    every kind of fact (Arrival, Sleeping, Working from, Departure,
    Driving) renders through this one function. Always LABEL-first (see
    requirements/public.md -> Attendees -> Layout) — "what happened"
    before "when" — never the reverse: `time_text`, when present, comes
    right after the label, not before it. `time_text` is the exact time
    or bare quarter name for a point-in-time fact (Arrival/Departure/
    Driving — see time_label() above); omitted (None) for a date-range
    fact (Sleeping/Working from), which has no single time of day to
    show at all — those lines already started at the label even before
    this, so this change only actually moves anything for the
    point-in-time kinds. `detail_html` is pre-escaped/joined HTML (from
    format_leg_body() or a plain esc()'d string) — not escaped again
    here."""
    time_html = f'<span class="fact-time">{esc(time_text)}</span> ' if time_text else ""
    return (
        '<div class="fact-line">'
        f'<span class="fact-label">{esc(label)}</span> '
        f'{time_html}'
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
    ("mornings & afternoons"). No "till <end day>" clause, ever — unlike
    Sleeping, a Working from block never renders as one summarized range
    line (see requirements/public.md -> Attendees -> Layout): working from
    a structure is true or not true on a given day, the same as any other
    daily fact, not a location that holds until it changes. The caller
    (render_person_page() below) renders this same line once per calendar
    date the block covers, so there's no date range to describe here at
    all — just the block's own fixed facts."""
    quarters = block.get("quarters", list(WORK_QUARTERS))
    detail = f"{esc(block['structure'])}, {esc(format_work_quarters(quarters))}"
    return fact_line(None, "Working from", detail)


def airport_run_line(run, people_by_id):
    """An airport run's own line — rendered as ONE fact line covering both
    the depart and return legs, not two (contrast excursions, which
    deliberately render as a separate Departure+Arrival pair — see
    requirements/public.md -> Data -> travel.json -> airport_runs for why
    those are different concepts). A driver doing an airport run hasn't
    left and rejoined the trip; showing it as a same-shaped Arrival/
    Departure pair on their own page reads that way regardless, which is
    exactly the confusion this single-line "Airport run" fact exists to
    avoid. Time is a range (depart time–return time, e.g. "5pm–6pm") when
    the two differ, or just the one label when they don't — e.g. neither
    leg has a precise time_range and both fall in the same quarter, which
    would otherwise render as a confusing "Evening–Evening" repeating the
    same bare quarter name for no reason. detail is the depart leg's own
    mode/hub/vehicle (reusing format_leg_body(), same as any other leg)
    plus who's actually being ferried, from passenger_ids — a real
    reference list, not free text."""
    depart, ret = run["depart"], run["return"]
    depart_label, return_label = time_label(depart), time_label(ret)
    time_text = depart_label if depart_label == return_label else f"{depart_label}–{return_label}"
    passengers = nav.join_names([esc(people_by_id[pid]["name"]) for pid in run["passenger_ids"]])
    detail = f"{format_leg_body(depart, people_by_id, lead_with_by=True)} — {passengers}"
    return fact_line(time_text, "Airport run", detail)


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

    # One flat list of (sort_date, rank, html) across every kind of fact on
    # this page — Arrival/Sleeping/Departure/Working from/Driving — sorted
    # into a single true timeline instead of one block per kind (grouping
    # them by kind put a same-week Driving or Working from entry after a
    # much later Departure, reading out of order). sort_date is the FIRST
    # date of a range for the one ranged fact (a Sleeping stretch), but is
    # its OWN calendar date for every other fact — including Working
    # from, which gets one item per day it covers, not one item for its
    # whole range (see working_line() below for why). rank is
    # FACT_RANK[label] — an explicit same-date tie-break, not the order
    # these get appended below, since append order alone doesn't match the
    # causal order the doc requires (see FACT_RANK's own comment above) —
    # see requirements/public.md -> Attendees -> Layout.
    items = []

    if entry is not None:
        arrival = entry.get("arrival")
        departure = entry.get("departure")

        if arrival:
            items.append((
                arrival["date"], FACT_RANK["Arrival"],
                fact_line(time_label(arrival), "Arrival", format_leg_body(arrival, people_by_id, lead_with_by=True)),
            ))
        else:
            # An entry's own arrival_note (see requirements/public.md ->
            # Data -> travel.json -> arrival_note), if set, replaces the
            # generic default text below with something specific to this
            # person's actual story (e.g. Jim's "Never left") — only
            # reachable here, since arrival_note has no effect once a real
            # `arrival` leg exists (the branch above always wins then).
            no_arrival_text = entry.get("arrival_note") or "Already at the accommodation"
            items.append((
                TRIP_START.isoformat(), FACT_RANK["Arrival"],
                fact_line(None, "Arrival", esc(no_arrival_text)),
            ))

        # Sleeping milestones — arrive, then one "Sleeping" line per
        # contiguous same-room stretch in date order. See room_milestones()
        # above.
        start_date = date.fromisoformat(arrival["date"]) if arrival else TRIP_START
        end_date = sleeping_end_date(departure)
        for room, range_start, range_end in room_milestones(entry, start_date, end_date):
            items.append((range_start.isoformat(), FACT_RANK["Sleeping"], sleeping_line(room, range_start, range_end)))

        # One line per DAY a working_from block covers, not one line per
        # block — deliberately different from the Sleeping milestones
        # above, which collapse a stretch into a single range-with-"till"
        # line. Working from a structure is a fact about one specific day,
        # true or not true that day, not a location that holds until it
        # changes, so the same identical line repeats under every day
        # heading the block spans (see requirements/public.md -> Attendees
        # -> Layout).
        for block in entry.get("working_from", []):
            block_start = date.fromisoformat(block["start_date"])
            block_end = date.fromisoformat(block["end_date"])
            line_html = working_line(block)
            d = block_start
            while d <= block_end:
                items.append((d.isoformat(), FACT_RANK["Working from"], line_html))
                d += timedelta(days=1)

        # Excursion legs — a mid-stay round trip (see requirements/public.md
        # -> Data -> travel.json -> excursions) — render exactly like the
        # bookend legs, just sorted into the middle of the timeline by
        # their own dates instead of always being first/last. Each still
        # gets the same FACT_RANK as its bookend counterpart (a `return` is
        # an Arrival, a `depart` is a Departure) so a same-date tie against
        # a Sleeping/Working from fact resolves the same causal way either
        # time — see FACT_RANK's own comment above.
        for exc in entry.get("excursions", []):
            depart, ret = exc["depart"], exc["return"]
            items.append((
                depart["date"], FACT_RANK["Departure"],
                fact_line(time_label(depart), "Departure", format_leg_body(depart, people_by_id, lead_with_by=True)),
            ))
            items.append((
                ret["date"], FACT_RANK["Arrival"],
                fact_line(time_label(ret), "Arrival", format_leg_body(ret, people_by_id, lead_with_by=True)),
            ))

        # Airport runs — see requirements/public.md -> Data -> travel.json
        # -> airport_runs and airport_run_line() above for why this is one
        # line, not a Departure+Arrival pair the way excursions render.
        for run in entry.get("airport_runs", []):
            items.append((run["depart"]["date"], FACT_RANK["Airport run"], airport_run_line(run, people_by_id)))

        if departure:
            items.append((
                departure["date"], FACT_RANK["Departure"],
                fact_line(time_label(departure), "Departure", format_leg_body(departure, people_by_id, lead_with_by=True)),
            ))
        else:
            items.append((
                TRIP_END.isoformat(), FACT_RANK["Departure"],
                fact_line(None, "Departure", "Staying past this date"),
            ))

    # Driving obligations for OTHER people's legs — shown regardless of
    # whether this person has their own travel.json entry, since driving
    # someone else doesn't depend on your own travel status. Keyed by the
    # leg's own date, so it lands in the same timeline as everything else.
    for traveler, field, leg in driving_assignments(person["id"], travel, people_by_id):
        detail_html = f"{esc(traveler['name'])}’s {field} — {format_leg_body(leg, people_by_id)}"
        items.append((leg["date"], FACT_RANK["Driving"], fact_line(time_label(leg), "Driving", detail_html)))

    if entry is None and not items:
        body = (
            '<p class="attendee-pending">We don’t have your travel details yet '
            '— check back soon, or let the organizers know your plans.</p>'
        )
    else:
        # Sort by (date, FACT_RANK) — a same-date tie resolves by the
        # explicit causal rank, not by append order (see FACT_RANK's own
        # comment above for why append order alone isn't reliable: an
        # excursion's `return`/`depart` are appended well after the
        # Sleeping-milestones loop, so relying on stable-sort-of-append-
        # order would put a same-date Sleeping milestone before an
        # excursion Arrival that actually started it).
        items.sort(key=lambda item: (item[0], item[1]))

        # Group into one <h2> day heading per distinct date (see
        # requirements/public.md -> Attendees -> Layout) — sort_date is
        # always the exact date a fact's own heading belongs under (a
        # leg's date, or a milestone/block's own start date), so grouping
        # by exact equality needs no separate "which day does this belong
        # to" logic of its own.
        day_blocks = []
        current_date = None
        current_lines = []
        for sort_date, _rank, line_html in items:
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

    # A dog is an attribute of the page owner, not a dated fact — shown
    # once, right under the heading, never folded into the day-grouped
    # timeline body above (see requirements/public.md -> people.json ->
    # dogs, and -> Attendees -> Layout).
    dogs = person.get("dogs")
    dogs_html = f'<p class="attendee-dogs">Traveling with: {esc(", ".join(dogs))}</p>' if dogs else ""

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
{dogs_html}
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
