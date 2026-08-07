#!/usr/bin/env python3
"""Regenerate site/index.html — the Timeline feature, which also
encompasses the Home view (see requirements/public.md -> Home & Timeline).

Reads shared/data/people.json, shared/data/structures.json,
shared/data/vehicles.json, timeline/data/travel.json,
timeline/data/meals.json, and timeline/data/activities.json. Renders
August 1-15, 2026 split into four day quarters (6-hour segments) per
day, one full-viewport-height "quarter screen" per quarter, ALWAYS in
full — every day, every quarter, regardless of the real-world date at
build time. This script no longer looks at the clock at all: which
quarter is "now" is entirely a client-side, browser-time concern (see
shared/nav.js), not a build-time one — so unlike the old cutoff-based
version, this build's output never depends on when it happens to run,
and never needs a rebuild+push just because a day has passed (see
requirements/public.md -> Home & Timeline -> Time-of-day background...
-> "Now").

Validated at build time, all as hard errors rather than silent typos:
every record in people.json/structures.json/vehicles.json/travel.json
has its required fields (a friendly message naming the record and field,
not a raw KeyError, when one's missing — likely during hand-editing);
every arrival/departure's `mode` is present and one of plane/train/car;
an arrival/departure's optional `driver_id` (someone else driving that
leg — see requirements/public.md -> Data -> travel.json -> driver_id)
references a real person and isn't the traveler's own id; no two people
in people.json share the exact same `name` (the last-
initial disambiguation convention would otherwise be silently forgettable
during bulk entry, and a collision makes two people indistinguishable
everywhere a bare name is shown); every `room`/`room_by_date`/`hub` value in travel.json against
shared/data/structures.json — including, for a structure with a fixed
`rooms` list (e.g. Cottage) or a validated `instances` list (e.g. The Field),
that the room detail is one of the declared names, not arbitrary free
text (the two lists differ only in whether the structure always shows in
the Structures row — see requirements/public.md -> Structures — and are
mutually exclusive on a single structure); a structure's optional
`always_shown` is a boolean when present (the same always-shown behavior
`rooms` grants, for a structure with no fixed sub-rooms to declare, e.g.
Red Shed); a structure's optional `spaces` list (see requirements/public.md
-> Structures -> spaces) has only valid, non-repeated `kind` values
(`"kitchen"`/`"working"` today); an entry's optional `working_from` blocks
(someone working from a structure during the day, independent of where
they're sleeping — see requirements/public.md -> Data -> travel.json ->
working_from) each reference a structure that actually declares a
`"working"` space (not just any structure name), have valid non-inverted
ISO start/end dates, and only use `06-12`/`12-18` quarters (working from a
structure isn't tracked overnight); every `meals.json` entry is an object
with a non-empty `note` and an optional `structure` that, if set, must
reference a structure declaring a `"kitchen"` space (see
requirements/public.md -> Data -> meals.json); an entry's optional `excursions` blocks (a mid-stay
round trip — see requirements/public.md -> Data -> travel.json ->
excursions) each have valid `depart`/`return` legs, in order, within the
entry's own arrival/departure window, and non-overlapping with each other; every `vehicle` value against
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
being a boolean when present; a structure's `rooms`/`instances` list (if
either is set — not both) is non-empty with no duplicates, and its
`active_from`/`active_to` (if set) are valid ISO dates with `active_to`
not before `active_from`; and
ids are unique within people.json/structures.json/vehicles.json.

The nav bar (see shared/nav.py -> render_nav(), the one shared shape
every page uses) is one single row: "MC26" on the far left, always
present, a plain link back to the intro screen (INTRO_SCREEN_ID) — unlike
every other nav item, this one's own text never changes; then "Timeline",
a split control whose label jumps straight to whichever quarter screen is
current at the cottage (Murray Corner, New Brunswick — Atlantic Time, not
the visitor's own device timezone), computed fresh in their browser at
click time (see shared/nav.js) — clamped to the trip's last quarter if
"now" is already past August 15 — showing the static word "Timeline"
normally, or the live "current day quarter" label instead once actually
scrolled into a quarter screen (updated by shared.js via
IntersectionObserver — the abbreviated weekday+date smaller/secondary
shown first, e.g. "Wed, Aug 5" (kept short since this one-row control
shares space with three other nav items on a phone — see
shared/trip.py -> format_date_abbrev()), then the bare quarter name
bold/prominent shown second, e.g. "· Morning"); its own caret opens a panel of
every day/quarter as links plus the "▶"/"⏸" play/pause auto-advance
control (see requirements/public.md -> Navigation -> Timeline's panel);
then "Folks", the same split-control shape, whose label jumps to a random
attending person's Details page and whose caret opens a disclosure
listing everyone with a travel.json entry, each entry showing the
person's name (plain text) and two labeled links: "Timeline" jumps to
their arrival's quarter screen, "Detail" goes to their own attendees page
instead; and finally "Tree", a plain link to the Family Tree page. No
Attendees nav item; an attendees page is reached via the Family Tree, a
Folks panel's "Detail" link, or the "Folks" label's own random jump, not
a nav entry of its own.

The page no longer auto-scrolls anywhere on load — see -> Always the full
trip, "now" computed live below for why: it now opens on the intro
screen (Home) every time, same as any other page, unless the URL already
has a #quarter-screen hash (a shared link to a specific moment), which is
honored directly via plain native anchor behavior. Scrolling down from
Home passes through a transition screen (see render_transition_screen()
below) offering an explicit "Jump to now" or "Aug 1st" choice, then the
trip itself; scrolling back up from anywhere returns the same way — the
full range is always in the page, nothing is ever hidden (see
requirements/public.md -> Home & Timeline).

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
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # timeline/
PROJECT_ROOT = ROOT.parent  # repo root — site/ and shared/ live here

sys.path.insert(0, str(PROJECT_ROOT / "shared"))
import nav  # noqa: E402
from trip import TRIP_START, TRIP_END, QUARTERS, QUARTER_LABELS, QUARTER_NAMES, MODE_TAGS, WORK_QUARTERS, format_time_range, format_date_abbrev, format_date_jump, quarter_screen_id  # noqa: E402

PAGE_TITLE = "Murray Corner 2026"
TRIP_SUBTITLE = "Murray Corner, New Brunswick · August 1–15, 2026"
# Anchor target for the permanent "MC26" nav link — see
# render_intro_screen() below and shared/nav.py -> render_nav().
INTRO_SCREEN_ID = "trip-top"

QUARTER_INDEX = {q: i for i, q in enumerate(QUARTERS)}
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
VALID_MODES = tuple(MODE_TAGS)

def esc(s):
    return nav.esc(s)


def load_json(path):
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {path}: {e}") from e


def structure_names(structures, category):
    return {s["name"] for s in structures if s["category"] == category}


# The allowed `kind` values for a structure's `spaces` list (see
# validate_structures_file() below and requirements/public.md -> Structures
# -> spaces) — extensible by adding a new string here, not a new field.
VALID_SPACE_KINDS = ("kitchen", "working")


def structures_with_space_kind(structures, kind):
    """Names of every structure declaring `{"kind": kind}` in its `spaces`
    list — the single general mechanism both `working_from` (kind
    "working") and a meal's kitchen tag (kind "kitchen") are validated
    against, replacing the old "any structure name is fine" rule for
    working_from (see requirements/public.md -> Structures -> spaces)."""
    return {s["name"] for s in structures if any(sp.get("kind") == kind for sp in s.get("spaces", []))}


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


def validate_unique_names(people, label):
    """Two people with the exact same `name` string are indistinguishable
    everywhere the site shows a bare name (Family Tree, "Folks ▾", the
    Sleeping row's grouped-by-name lists) — see requirements/public.md ->
    people.json for the last-initial disambiguation convention (e.g. "Jim
    S", "Helen S") this is meant to catch a forgotten instance of."""
    seen = {}
    for r in people:
        name = r["name"]
        if name in seen:
            raise ValueError(
                f"Duplicate name {name!r} in {label} (ids {seen[name]!r} and {r['id']!r}) — "
                f"two people can't share the exact same name; disambiguate by appending the "
                f"first letter of their last name (e.g. 'Jim S', 'Helen S')."
            )
        seen[name] = r["id"]


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
        instances = s.get("instances")
        if rooms is not None and instances is not None:
            raise ValueError(
                f"Structure {s['name']!r} in shared/data/structures.json has both 'rooms' and "
                f"'instances' set — a structure can only be one or the other ('rooms' are fixed "
                f"physical places that always show, even empty; 'instances' are a validated name "
                f"list that only shows up when actually occupied)."
            )
        if rooms is not None:
            if not rooms or len(set(rooms)) != len(rooms):
                raise ValueError(
                    f"Structure {s['name']!r} in shared/data/structures.json has an invalid "
                    f"'rooms' list — must be non-empty with no duplicate room names."
                )
        if instances is not None:
            if not instances or len(set(instances)) != len(instances):
                raise ValueError(
                    f"Structure {s['name']!r} in shared/data/structures.json has an invalid "
                    f"'instances' list — must be non-empty with no duplicate instance names."
                )
        always_shown = s.get("always_shown")
        if always_shown is not None and not isinstance(always_shown, bool):
            raise ValueError(
                f"Structure {s['name']!r} in shared/data/structures.json has a non-boolean "
                f"'always_shown' — must be true or false."
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
        spaces = s.get("spaces")
        if spaces is not None:
            if not isinstance(spaces, list):
                raise ValueError(
                    f"Structure {s['name']!r} in shared/data/structures.json has a non-list "
                    f"'spaces' — must be a list of {{\"kind\": ...}} objects."
                )
            seen_kinds = set()
            for i, sp in enumerate(spaces):
                kind = nav.require(sp, "kind", f"spaces[{i}] for structure {s['name']!r}")
                if kind not in VALID_SPACE_KINDS:
                    raise ValueError(
                        f"Invalid kind {kind!r} in spaces[{i}] for structure {s['name']!r} in "
                        f"shared/data/structures.json — must be one of {', '.join(VALID_SPACE_KINDS)}."
                    )
                if kind in seen_kinds:
                    raise ValueError(
                        f"Structure {s['name']!r} in shared/data/structures.json declares "
                        f"'spaces' kind {kind!r} more than once."
                    )
                seen_kinds.add(kind)


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
    validate_unique_names(people, "shared/data/people.json")


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
            detail = room[len(prefix):]
            # `rooms` (fixed physical places, always shown) and `instances`
            # (a validated name list, occupancy-shown only — see
            # requirements/public.md -> Structures) are mutually exclusive
            # per validate_structures_file(), so at most one of these is set.
            declared_rooms = s.get("rooms")
            declared_instances = s.get("instances")
            declared = declared_rooms or declared_instances
            if declared and detail not in declared:
                kind = "rooms" if declared_rooms else "instances"
                raise ValueError(
                    f"Unknown {kind[:-1]} {detail!r} for structure {name!r} in room for {context} — "
                    f"{name!r} has a fixed {kind} list, must be one of {', '.join(declared)}."
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


def validate_driver(driver_id, person_id, people_by_id, person_name, field):
    """driver_id — who's driving this leg, when it's someone other than the
    traveler themselves (see requirements/public.md -> Data -> travel.json
    -> driver_id). This is what lets "David drove Rachel to the airport"
    show up on BOTH Rachel's page (as part of her leg) and David's own page
    (as a "Driving" entry, see attendees/scripts/build.py) from one piece
    of data, instead of a driving obligation only ever being visible on the
    traveler's own page as unstructured prose the driver never sees."""
    if driver_id is None:
        return
    if driver_id not in people_by_id:
        raise ValueError(
            f"Unknown driver_id {driver_id!r} in {field} for {person_name!r} — must reference "
            f"a real person id in shared/data/people.json."
        )
    if driver_id == person_id:
        raise ValueError(
            f"driver_id in {field} for {person_name!r} references themselves — omit driver_id "
            f"entirely when someone is driving themselves, it's only for naming someone else."
        )


def validate_working_from(blocks, person_name, working_structure_names):
    """working_from — someone working from a structure during the day,
    independent of where they're sleeping (see requirements/public.md ->
    Data -> travel.json -> working_from). Optional list of {structure,
    start_date, end_date, quarters} blocks. `structure` must be one of
    `working_structure_names` — structures declaring {"kind": "working"}
    in their own `spaces` list (see structures_with_space_kind() above) —
    not just any structure name in shared/data/structures.json; a
    structure has to actually say it supports working."""
    if blocks is None:
        return
    if not isinstance(blocks, list):
        raise ValueError(f"working_from for {person_name!r} must be a list of blocks.")
    for i, block in enumerate(blocks):
        label = f"working_from[{i}] for {person_name!r}"
        structure = nav.require(block, "structure", label)
        if structure not in working_structure_names:
            raise ValueError(
                f"Unknown or non-working structure {structure!r} in {label} — must exactly "
                f"match the name of a structure in shared/data/structures.json that declares "
                f'{{"kind": "working"}} in its \'spaces\' list.'
            )
        start = nav.require(block, "start_date", label)
        end = nav.require(block, "end_date", label)
        validate_date_str(start, f"start_date in {label}")
        validate_date_str(end, f"end_date in {label}")
        if end < start:
            raise ValueError(f"end_date {end!r} is before start_date {start!r} in {label}.")
        quarters = block.get("quarters", list(WORK_QUARTERS))
        if not isinstance(quarters, list) or not quarters:
            raise ValueError(f"quarters in {label} must be a non-empty list of quarter keys.")
        for q in quarters:
            if q not in WORK_QUARTERS:
                raise ValueError(
                    f"Invalid quarter {q!r} in {label} — working_from only supports "
                    f"{' and '.join(WORK_QUARTERS)} (morning and afternoon)."
                )


def validate_leg(leg, person_id, person_name, field, transit_names, vehicle_names, people_by_id):
    if "date" not in leg or "quarter" not in leg or "mode" not in leg:
        raise ValueError(f"Missing 'date', 'quarter', or 'mode' in {field} for {person_name!r}.")
    validate_date_str(leg["date"], f"{field} for {person_name!r}")
    validate_quarter_value(leg["quarter"], f"{field} for {person_name!r}")
    if leg["mode"] not in VALID_MODES:
        raise ValueError(
            f"Invalid mode {leg['mode']!r} in {field} for {person_name!r} — must be one of "
            f"{', '.join(VALID_MODES)}."
        )
    validate_hub(leg.get("hub"), transit_names, person_name, field)
    validate_vehicle(leg.get("vehicle"), vehicle_names, person_name, field)
    validate_time_range(leg.get("time_range"), leg["quarter"], f"{field} for {person_name!r}")
    validate_driver(leg.get("driver_id"), person_id, people_by_id, person_name, field)


def validate_excursions(excursions, person_id, person_name, transit_names, vehicle_names, people_by_id, arrival, departure):
    """excursions — a mid-stay round trip (leave and come back), each block
    a {depart, return} pair of full legs (see requirements/public.md ->
    Data -> travel.json -> excursions). Unlike arrival/departure, which
    only capture joining and finally leaving the trip once, this covers a
    temporary absence in between."""
    if excursions is None:
        return
    if not isinstance(excursions, list):
        raise ValueError(f"excursions for {person_name!r} must be a list of {{depart, return}} blocks.")
    arrival_key = quarter_key(arrival["date"], arrival["quarter"]) if arrival else None
    departure_key = quarter_key(departure["date"], departure["quarter"]) if departure else None
    prev_return_key = None
    for i, exc in enumerate(excursions):
        label = f"excursions[{i}] for {person_name!r}"
        depart = nav.require(exc, "depart", label)
        ret = nav.require(exc, "return", label)
        validate_leg(depart, person_id, person_name, f"{label} depart", transit_names, vehicle_names, people_by_id)
        validate_leg(ret, person_id, person_name, f"{label} return", transit_names, vehicle_names, people_by_id)
        depart_key = quarter_key(depart["date"], depart["quarter"])
        return_key = quarter_key(ret["date"], ret["quarter"])
        if return_key < depart_key:
            raise ValueError(
                f"return ({ret['date']} {ret['quarter']}) is before depart "
                f"({depart['date']} {depart['quarter']}) in {label}."
            )
        if arrival_key is not None and depart_key < arrival_key:
            raise ValueError(f"{label} departs before arrival for {person_name!r}.")
        if departure_key is not None and return_key > departure_key:
            raise ValueError(f"{label} returns after the final departure for {person_name!r}.")
        if prev_return_key is not None and depart_key < prev_return_key:
            raise ValueError(
                f"{label} overlaps the previous excursion for {person_name!r} — excursions "
                f"must be in chronological, non-overlapping order."
            )
        prev_return_key = return_key


def validate_airport_runs(runs, person_id, person_name, transit_names, vehicle_names, people_by_id, arrival, departure):
    """airport_runs — a driver's own round trip to ferry OTHER attendees to
    or from a transit hub (see requirements/public.md -> Data ->
    travel.json -> airport_runs). Deliberately a separate concept from
    excursions above, not a variant of it: an excursion is about THIS
    person's own temporary absence from the trip, so it renders as a real
    Departure+Arrival pair on their page — an airport run is an errand
    *at* the accommodation's own transit hub, not a personal absence from
    the trip, and rendering it with the same Departure/Arrival labels
    reads as if the driver left and rejoined the trip a second time, which
    isn't true (see attendees/scripts/build.py -> airport_run_line() for
    how this renders as a single distinct "Airport run" line instead).
    Same {depart, return} leg shape and bounds-checking as excursions,
    plus passenger_ids: who's actually being ferried, a real reference
    list (not free text in `detail`) so a typo'd/renamed passenger is a
    build error, not a silently wrong caption."""
    if runs is None:
        return
    if not isinstance(runs, list):
        raise ValueError(f"airport_runs for {person_name!r} must be a list of {{depart, return, passenger_ids}} blocks.")
    arrival_key = quarter_key(arrival["date"], arrival["quarter"]) if arrival else None
    departure_key = quarter_key(departure["date"], departure["quarter"]) if departure else None
    for i, run in enumerate(runs):
        label = f"airport_runs[{i}] for {person_name!r}"
        depart = nav.require(run, "depart", label)
        ret = nav.require(run, "return", label)
        validate_leg(depart, person_id, person_name, f"{label} depart", transit_names, vehicle_names, people_by_id)
        validate_leg(ret, person_id, person_name, f"{label} return", transit_names, vehicle_names, people_by_id)
        depart_key = quarter_key(depart["date"], depart["quarter"])
        return_key = quarter_key(ret["date"], ret["quarter"])
        if return_key < depart_key:
            raise ValueError(
                f"return ({ret['date']} {ret['quarter']}) is before depart "
                f"({depart['date']} {depart['quarter']}) in {label}."
            )
        if arrival_key is not None and depart_key < arrival_key:
            raise ValueError(f"{label} departs before arrival for {person_name!r}.")
        if departure_key is not None and return_key > departure_key:
            raise ValueError(f"{label} returns after the final departure for {person_name!r}.")

        passenger_ids = nav.require(run, "passenger_ids", label)
        if not isinstance(passenger_ids, list) or not passenger_ids:
            raise ValueError(f"{label} passenger_ids must be a non-empty list of person ids.")
        for pid in passenger_ids:
            if pid == person_id:
                raise ValueError(f"{label} lists {person_name!r} as their own passenger — omit the driver from passenger_ids.")
            if pid not in people_by_id:
                raise ValueError(f"{label} passenger_ids references id {pid!r}, which doesn't exist in shared/data/people.json.")


def validate_travel(travel, people_by_id, structures, vehicles):
    accommodation_structures = [s for s in structures if s["category"] == "accommodation"]
    transit_names = structure_names(structures, "transit")
    vehicle_names = {v["name"] for v in vehicles}
    working_structure_names = structures_with_space_kind(structures, "working")

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
            validate_leg(arrival, person_id, person_name, "arrival", transit_names, vehicle_names, people_by_id)
        if departure:
            validate_leg(departure, person_id, person_name, "departure", transit_names, vehicle_names, people_by_id)
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
        # room_by_quarter — a targeted override for specific quarters of
        # specific dates, layered on top of room_by_date/room (see
        # requirements/public.md -> Data -> travel.json -> room_by_quarter
        # and room_for_quarter() below for the resolution order). Only
        # exists to override the quarter(s) that actually differ from
        # what room_by_date/room would otherwise resolve to for that
        # date — e.g. Brendan/Priscilla/Thiago's pre-dawn 00-06 quarter,
        # still the Red Shed from the night before, ahead of their own
        # room_by_date switching them to their tent later that same date.
        for room_date, by_quarter in entry.get("room_by_quarter", {}).items():
            validate_date_str(room_date, f"room_by_quarter for {person_name!r}")
            if not isinstance(by_quarter, dict) or not by_quarter:
                raise ValueError(
                    f"room_by_quarter for {person_name!r} on {room_date} must be a non-empty "
                    f"object mapping quarter keys to a room."
                )
            for quarter, room in by_quarter.items():
                validate_quarter_value(quarter, f"room_by_quarter for {person_name!r} on {room_date}")
                validate_room(room, accommodation_structures, f"{person_name!r} on {room_date} {quarter}")
        validate_working_from(entry.get("working_from"), person_name, working_structure_names)
        validate_excursions(entry.get("excursions"), person_id, person_name, transit_names, vehicle_names, people_by_id, arrival, departure)
        validate_airport_runs(entry.get("airport_runs"), person_id, person_name, transit_names, vehicle_names, people_by_id, arrival, departure)


def validate_day_quarter_notes(data, label):
    for day, quarters in data.items():
        validate_date_str(day, label)
        for q in quarters:
            validate_quarter_value(q, f"{label} on {day}")


def validate_meals_file(meals, kitchen_structure_names):
    """timeline/data/meals.json — keyed by date, then day quarter key, each
    quarter's value an object {"note": <free text>, "structure": <optional
    structure name>} (see requirements/public.md -> Data -> meals.json).
    Unlike activities.json (still a bare free-text string per quarter, see
    validate_day_quarter_notes() above), a meal entry is a small object so
    it can optionally name which structure's Kitchen it belongs to."""
    label = "timeline/data/meals.json"
    for day, quarters in meals.items():
        validate_date_str(day, label)
        for q, entry in quarters.items():
            validate_quarter_value(q, f"{label} on {day}")
            entry_label = f"{label} entry for {day} {q}"
            if not isinstance(entry, dict):
                raise ValueError(f"{entry_label} must be an object with a 'note' field, not a bare string.")
            note = nav.require(entry, "note", entry_label)
            if not isinstance(note, str) or not note:
                raise ValueError(f"'note' in {entry_label} must be a non-empty string.")
            structure = entry.get("structure")
            if structure is not None and structure not in kitchen_structure_names:
                raise ValueError(
                    f"Unknown or non-kitchen structure {structure!r} in {entry_label} — must "
                    f"exactly match the name of a structure in shared/data/structures.json that "
                    f'declares {{"kind": "kitchen"}} in its \'spaces\' list.'
                )


def quarter_key(iso_date, quarter):
    return (iso_date, QUARTER_INDEX[quarter])


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def travel_detail(leg, people_by_id, driver_label="driving"):
    parts = []
    time_range = leg.get("time_range")
    if time_range:
        parts.append(format_time_range(time_range))
    label = leg.get("hub") or leg.get("vehicle")
    if label:
        parts.append(label)
    detail = leg.get("detail")
    if detail:
        parts.append(detail)
    driver = people_by_id.get(leg.get("driver_id"))
    if driver:
        parts.append(f"{driver['name']} {driver_label}")
    return " · ".join(parts)


def group_legs_by_detail(pairs, people_by_id, driver_label="driving"):
    """Group (person, leg) pairs from the Arriving:/Departing: rows that
    represent the same real-world trip, so several people sharing one
    flight/car (e.g. four people landing on the same plane, all driven
    onward by the same person) read as the single event it is, not a
    repeated near-identical line per person (see requirements/public.md ->
    Home & Timeline -> Row-by-row rules -> Arrivals/Departures).

    First buckets by (mode, rendered detail via travel_detail() above) —
    same mode and identical time/hub/vehicle/free-text detail/driver. A
    bucket only renders as ONE combined line if that shared detail
    actually says something beyond the time (a hub, a named vehicle,
    free-text detail, or a driver) — real evidence it's the same trip.
    Two people who merely happen to arrive at the same rounded time (e.g.
    both "9pm", nothing else set) are NOT assumed to be traveling
    together just because the strings match — that produced a real bug:
    an unrelated third person's coincidentally-identical arrival time got
    folded into a couple's own line, implying they all traveled together
    when only the couple did. For a bucket with no distinguishing detail,
    only actual partners (reciprocal `partner_id`, see
    requirements/public.md -> people.json -> partner_id) sharing that
    bucket still combine into one line; everyone else in it renders on
    their own, even though their rendered detail text is identical.
    Order-preserving: a group renders at the position of its first
    member's first appearance in `pairs`."""
    buckets = {}
    order = []
    for p, leg in pairs:
        key = (leg["mode"], travel_detail(leg, people_by_id, driver_label))
        if key not in buckets:
            buckets[key] = {"mode": leg["mode"], "detail": key[1], "leg": leg, "people": []}
            order.append(key)
        buckets[key]["people"].append(p)

    groups = []
    for key in order:
        bucket = buckets[key]
        leg = bucket["leg"]
        has_distinguishing_detail = any([leg.get("hub"), leg.get("vehicle"), leg.get("detail"), leg.get("driver_id")])
        if has_distinguishing_detail or len(bucket["people"]) == 1:
            groups.append({"mode": bucket["mode"], "detail": bucket["detail"], "people": bucket["people"]})
            continue
        bucket_ids = {p["id"] for p in bucket["people"]}
        paired = set()
        for p in bucket["people"]:
            if p["id"] in paired:
                continue
            partner_id = p.get("partner_id")
            if partner_id in bucket_ids and partner_id not in paired:
                partner = next(q for q in bucket["people"] if q["id"] == partner_id)
                groups.append({"mode": bucket["mode"], "detail": bucket["detail"], "people": [p, partner]})
                paired.add(p["id"])
                paired.add(partner_id)
            else:
                groups.append({"mode": bucket["mode"], "detail": bucket["detail"], "people": [p]})
                paired.add(p["id"])
    return groups


def render_travel_row(label, pairs, people_by_id, driver_label="driving"):
    """The Arriving:/Departing: row body — one line per distinct trip (see
    group_legs_by_detail() above), not one per person. A `dogs` tag (see
    requirements/public.md -> people.json -> dogs) rides along on
    whichever name it belongs to, right where that person's name appears
    in the joined list — same "+ <name>" shape used everywhere else a dog
    shows (Family Tree, Attendees), just inline here instead of on its
    own line, since this row is already one line per trip. `driver_label`
    distinguishes an Arriving row's "<name> pickup" (someone meeting the
    traveler at a hub) from a Departing row's "<name> driving" (someone
    dropping the traveler off) — same `driver_id` fact, worded for which
    direction it actually is (see the "Arriving:"/"Departing:" call sites
    below)."""
    if not pairs:
        return ""
    lines = []
    for group in group_legs_by_detail(pairs, people_by_id, driver_label):
        names = []
        for p in group["people"]:
            name = esc(p["name"])
            if p.get("dogs"):
                name += f' (+ {esc(", ".join(p["dogs"]))})'
            names.append(name)
        lines.append(
            f'<span class="person-line">'
            f'<span class="mode-tag">{esc(MODE_TAGS.get(group["mode"], group["mode"]))}</span>'
            f'{nav.join_names(names)} — {esc(group["detail"])}'
            f"</span>"
        )
    return f'<div class="quarter-row"><span class="quarter-row-label">{esc(label)}</span>{"".join(lines)}</div>'


def room_for_quarter(entry, iso_date, quarter):
    """Resolve the room for one exact day+quarter (see
    requirements/public.md -> Data -> travel.json -> room_by_quarter):
    room_by_quarter for that exact quarter, if listed, wins first; then
    room_by_date for that whole date, if set; then the base room field.
    Reused by attendees/scripts/build.py's room_milestones() (imported as
    timeline_build), so the Structures row and the Attendees page's own
    Sleeping milestones can never resolve a person's room differently."""
    by_quarter = entry.get("room_by_quarter", {}).get(iso_date, {})
    if quarter in by_quarter:
        return by_quarter[quarter]
    return entry.get("room_by_date", {}).get(iso_date, entry.get("room", ""))


def parse_room(room, accommodation_structures):
    """Split a validated room string into (structure_name, detail) — detail
    is None for a bare structure name or an unset room (see
    requirements/public.md -> Structures -> Nested box display)."""
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


def person_working_here(entry, day_iso, quarter):
    """Every structure this travel entry's `working_from` blocks put this
    person at for this exact day+quarter (see requirements/public.md ->
    Data -> travel.json -> working_from) — usually zero or one, since
    working_from blocks aren't expected to overlap for the same person."""
    hits = []
    for block in entry.get("working_from", []):
        if block["start_date"] <= day_iso <= block["end_date"] and quarter in block.get("quarters", WORK_QUARTERS):
            hits.append(block["structure"])
    return hits


def render_structures_row(present, working, kitchen_by_structure, accommodation_structures, day_iso):
    """Labeled "Structures", not "Sleeping" — deliberately reframed away
    from an overnight-only concept to "who's associated with which
    structure right now, and why" (see requirements/public.md -> Homepage
    = Timeline -> Row-by-row rules -> Structures). Merges three independent
    sources into the same outer per-structure box, but keeps them visually
    distinct within it: `present` (people actually staying there this
    quarter, via room/room_by_date) render as today — a flat name list or
    named room boxes — while `working` (people working from there this
    quarter, via working_from — see person_working_here() below) always
    get their own labeled "Working" sub-box, and `kitchen_by_structure`
    (this exact day+quarter's meal note, if one is tagged to a structure —
    see render_quarter_screen() below) gets its own labeled "Kitchen"
    sub-box — neither ever merged into the sleeping-side list, so a name
    (or a meal) showing up for one of these reasons reads as clearly
    different from someone actually staying there. The same person can
    land in two different structure boxes on one quarter screen (their
    overnight structure, and wherever they're working from) since those
    are independent facts, not one; a Kitchen sub-box's "occupant" is a
    meal note string, not a person, since it says what's cooking, not
    who's cooking (see requirements/public.md -> Structures -> spaces)."""
    by_structure = {}
    for p, room in present:
        structure, detail = parse_room(room, accommodation_structures)
        by_structure.setdefault(structure, {}).setdefault(detail, []).append(p["name"])

    working_by_structure = {}
    for p, structure_name in working:
        working_by_structure.setdefault(structure_name, []).append(p["name"])

    # A structure with a fixed `rooms` list, or `always_shown: true`, is a
    # real, physical place that doesn't disappear just because nobody's
    # currently associated with it — it always gets a box (empty or not)
    # for as long as the structure itself is active (see
    # requirements/public.md -> Structures -> Active range and Structures
    # -> Nested box display). A `rooms` structure also always shows every
    # declared room; `always_shown` alone (no `rooms`, e.g. Red Shed) just
    # guarantees the outer box, with no forced-empty room boxes inside it.
    # Structures with neither keep the old occupancy-only behavior (e.g.
    # The Field/Camper Van, which are free-text-instance places).
    for s in accommodation_structures:
        if not structure_active(s, day_iso):
            continue
        rooms = s.get("rooms")
        if rooms:
            bucket = by_structure.setdefault(s["name"], {})
            for room_name in rooms:
                bucket.setdefault(room_name, [])
        elif s.get("always_shown"):
            by_structure.setdefault(s["name"], {})

    # working_by_structure/kitchen_by_structure can each name a structure
    # with nobody sleeping there at all (e.g. Red Shed occupied only by
    # day-workers, or a structure whose kitchen is in use but that nobody's
    # currently staying at) — the outer box still needs to exist for it, so
    # render every structure named by ANY of the three sources, not just
    # the sleeping side.
    all_structures = set(by_structure) | set(working_by_structure) | set(kitchen_by_structure)
    if not all_structures:
        return ""

    def sort_key(k):
        return (k is None, k or "")

    # The outer structure boxes render in the order structures.json's own
    # accommodation entries are written — Cottage, Red Shed, The Field,
    # etc. — not alphabetically (see requirements/public.md -> Structures
    # -> Nested box display). This mirrors the same "declared order, not
    # alphabetical" rule a structure's own `rooms` list already gets
    # below, just one level up: the file's own array order is the single
    # place this is declared, so reordering the row means reordering that
    # file, not touching this script. A structure absent from
    # accommodation_structures (shouldn't happen — every name here came
    # from validated data) sorts after every declared one rather than
    # crashing; "Unassigned" (None) always sorts last regardless.
    structure_order_index = {s["name"]: i for i, s in enumerate(accommodation_structures)}

    def structure_display_key(k):
        if k is None:
            return (True, 0)
        return (False, structure_order_index.get(k, len(structure_order_index)))

    # A structure's declared `rooms` list is a FIXED order (see
    # requirements/public.md -> Structures -> Nested box display) — the
    # order it's written in shared/data/structures.json, e.g. Cottage's
    # Master Suite/Green Room/Blue Room — not alphabetical. Only structures
    # with a `rooms` list get this; a structure with free-text `instances`
    # (The Field) or no fixed list at all has no declared order to honor,
    # so its details still sort alphabetically below.
    rooms_order_by_structure = {s["name"]: s["rooms"] for s in accommodation_structures if s.get("rooms")}

    boxes = []
    for structure in sorted(all_structures, key=structure_display_key):
        by_detail = by_structure.get(structure, {})
        if structure is None:
            names = sorted(by_detail.get(None, []))
            boxes.append(
                '<div class="structure-box unassigned-box">'
                '<span class="structure-label">Unassigned</span>'
                f'<span class="room-people">{esc(", ".join(names))}</span>'
                '</div>'
            )
            continue

        declared_rooms = rooms_order_by_structure.get(structure)
        if declared_rooms:
            # Declared order first, then anything unexpected (shouldn't
            # happen — validate_room() only allows declared names — but
            # sorted alphabetically rather than silently dropped if it ever
            # does), bare-structure occupants (detail=None) always last,
            # matching sort_key's existing None-sorts-last convention.
            detail_order = [d for d in declared_rooms if d in by_detail]
            detail_order += [d for d in sorted(by_detail, key=sort_key) if d not in declared_rooms]
        else:
            detail_order = sorted(by_detail, key=sort_key)

        inner = []
        for detail in detail_order:
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
        kitchen_note = kitchen_by_structure.get(structure)
        if kitchen_note:
            inner.append(
                '<div class="room-box kitchen-box">'
                '<span class="room-label">Kitchen</span>'
                f'<span class="room-people">{esc(kitchen_note)}</span>'
                '</div>'
            )
        working_names = sorted(working_by_structure.get(structure, []))
        if working_names:
            inner.append(
                '<div class="room-box working-box">'
                '<span class="room-label">Working</span>'
                f'<span class="room-people">{esc(", ".join(working_names))}</span>'
                '</div>'
            )
        boxes.append(
            '<div class="structure-box">'
            f'<span class="structure-label">{esc(structure)}</span>'
            f'<div class="structure-rooms">{"".join(inner)}</div>'
            '</div>'
        )

    return (
        '<div class="quarter-row"><span class="quarter-row-label">Structures:</span>'
        f'<div class="structure-boxes">{"".join(boxes)}</div></div>'
    )


def quarter_membership(key, day_iso, quarter, travel, people_by_id):
    """Everyone arriving, departing, present, or working this exact day
    quarter (`key`, from quarter_key(day_iso, quarter) — `day_iso` and
    `quarter` are also taken separately since `key` alone doesn't carry
    the quarter string person_working_here() needs) — the single
    source of truth for "who's where, when" that render_quarter_screen()
    below (the Timeline's own live Structures/Arriving/Departing rows) and
    scripts/report.py (a read-only cross-person review aid — see
    way-of-working.md -> Data entry) both call, so the two can never
    silently disagree about what counts as present (arrived_by/
    not_departed/away, including an excursion's away window) or working.
    Returns (arrivals, departures, present, working), each a list of
    (person, ...) tuples — present pairs a person with their resolved
    room, working pairs a person with the structure they're working from."""
    arrivals = []
    departures = []
    present = []
    working = []

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

        excursion_keys = []
        for exc in entry.get("excursions", []):
            exc_depart, exc_return = exc["depart"], exc["return"]
            exc_depart_key = quarter_key(exc_depart["date"], exc_depart["quarter"])
            exc_return_key = quarter_key(exc_return["date"], exc_return["quarter"])
            excursion_keys.append((exc_depart_key, exc_return_key))
            if exc_depart_key == key:
                departures.append((person, exc_depart))
            if exc_return_key == key:
                arrivals.append((person, exc_return))

        arrived_by = True if arrival_key is None else key >= arrival_key
        not_departed = True if departure_key is None else key < departure_key
        away = any(d_key <= key < r_key for d_key, r_key in excursion_keys)
        if arrived_by and not_departed and not away:
            present.append((person, room_for_quarter(entry, day_iso, quarter)))

        for structure_name in person_working_here(entry, day_iso, quarter):
            working.append((person, structure_name))

    return arrivals, departures, present, working


def render_quarter_screen(day, quarter, travel, people_by_id, meals, activities, accommodation_structures, is_first=False):
    key = quarter_key(day.isoformat(), quarter)
    arrivals, departures, present, working = quarter_membership(key, day.isoformat(), quarter, travel, people_by_id)

    rows = []

    arriving_row = render_travel_row("Arriving:", arrivals, people_by_id, driver_label="pickup")
    if arriving_row:
        rows.append(arriving_row)

    departing_row = render_travel_row("Departing:", departures, people_by_id)
    if departing_row:
        rows.append(departing_row)

    # A meal entry's optional `structure` tag (see requirements/public.md ->
    # Data -> meals.json) puts the SAME note text into that structure's own
    # "Kitchen" sub-box on the Structures row below — never a second,
    # separately-authored string. kitchen_by_structure is at most one entry
    # today, since meals.json holds one note per day+quarter, but is built
    # as a dict (not a bare tuple) so render_structures_row() doesn't need
    # to care how many there are.
    meal_entry = meals.get(day.isoformat(), {}).get(quarter)
    kitchen_by_structure = {}
    if meal_entry and meal_entry.get("structure"):
        kitchen_by_structure[meal_entry["structure"]] = meal_entry["note"]

    structures_row = render_structures_row(present, working, kitchen_by_structure, accommodation_structures, day.isoformat())
    if structures_row:
        rows.append(structures_row)

    if meal_entry:
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Meal:</span> {esc(meal_entry["note"])}</div>')

    activity = activities.get(day.isoformat(), {}).get(quarter)
    if activity:
        rows.append(f'<div class="quarter-row"><span class="quarter-row-label">Activities:</span> {esc(activity)}</div>')

    body = "".join(rows) if rows else '<div class="quarter-empty-hint">Nothing scheduled</div>'
    # Two pieces (see render_nav() and timeline/shared.js): the abbreviated
    # weekday+date (e.g. "Wed, Aug 5", from format_date_abbrev() — weekday
    # always leads, this one-row control just doesn't have room for the
    # full "Wednesday, August 5th" used elsewhere on the site), shown first
    # and smaller/secondary as supporting detail; the bare quarter name
    # (e.g. "Morning"), shown second and bold/prominent since that's what
    # you actually scan for while scrolling — no time-range suffix here.
    # render_jump_panel() below reads the same bare QUARTER_NAMES value for
    # its own three named chips now too (no more "· 6am–12pm" there
    # either) — QUARTER_LABELS' fuller value is only still used for a
    # validation error message (see validate_time_range() above), not
    # anywhere user-facing.
    # quarter_name comes from QUARTER_NAMES, not QUARTER_LABELS — 00-06 is
    # "" there (see shared/trip.py), so this quarter screen's own
    # data-quarter-name attribute is empty and shared.js's live label
    # renders just the weekday+date alone, no quarter suffix — never an
    # invented "Wed, Aug 5 · Night" — see requirements/public.md ->
    # Terminology for why.
    date_label = format_date_abbrev(day)
    quarter_name = QUARTER_NAMES[quarter]

    # first-quarter-screen (see timeline/shared.css) overrides --prev-quarter-bg
    # to Grove instead of the cyclical Evening value every other 00-06 screen
    # uses: the live scroll-linked blend (timeline/shared.js) actually needs a
    # correct "coming from" color now that it's a real, visible effect rather
    # than a static band mostly hidden under the nav — this is the one screen
    # whose true previous screen is the Grove intro, not an Evening that never
    # happened.
    first_quarter_class = " first-quarter-screen" if is_first else ""
    return f"""<section class="quarter-screen{first_quarter_class}" id="{quarter_screen_id(day.isoformat(), quarter)}" \
data-date="{esc(date_label)}" data-quarter-name="{esc(quarter_name)}" data-quarter="{quarter}">
<div class="quarter-canvas-padding"></div>
<div class="quarter-canvas">
{body}
</div>
</section>"""


def render_intro_screen():
    return f"""<section class="intro-screen" id="{INTRO_SCREEN_ID}">
<h1 class="trip-title">{PAGE_TITLE}</h1>
<p class="trip-subtitle">{TRIP_SUBTITLE}</p>
<p class="scroll-hint">Scroll or swipe down to start ↓</p>
</section>"""


def render_jump_panel(href_prefix=""):
    """The day/quarter jump list — the Timeline split control's own panel
    content (see shared/nav.py -> render_nav()). Always the full August
    1-15 range — every quarter screen always exists in the page (see
    build_timeline_html() below), so unlike the old cutoff-based version
    there's no day/quarter this could ever omit.

    Each day is one row of exactly four link chips — no separate day
    heading above them (see requirements/public.md -> Navigation ->
    Timeline's panel): the FIRST chip (still the 00-06 quarter's own
    link — same target as always) carries the day heading's own text
    instead of a bare time range, so the heading is folded into that chip
    rather than repeated as its own line above four separate ones —
    format_date_jump() (shared/trip.py), not format_date_full(), since
    this is a compact chip in a dropdown, not a page with room to spare:
    "Sat, Aug 1st", abbreviated weekday and month but still with the
    ordinal suffix. The other three read just the bare quarter name
    ("Morning"/"Afternoon"/"Evening", from QUARTER_NAMES, not
    QUARTER_LABELS — no "· 6am–12pm" suffix here anymore either). Every
    chip also carries `data-quarter` so timeline/shared.css can tint each
    one its own quarter's color (the same Morning/Afternoon/Evening/Night
    family the quarter screens themselves use), including the date chip,
    which gets Night's color since it's still literally the 00-06 slot —
    just also carrying that day's date as its label. `href_prefix` is ""
    on site/index.html itself (a same-page anchor) or e.g. "../index.html"
    from Family Tree/a Details page (a cross-page link — plain browser
    navigation handles those, no JS needed)."""
    groups = []
    for d in daterange(TRIP_START, TRIP_END):
        day_label = format_date_jump(d)
        links = []
        for q in QUARTERS:
            if q == "00-06":
                text, extra_class = day_label, " jump-link-date"
            else:
                text, extra_class = QUARTER_NAMES[q], ""
            links.append(
                f'<a href="{href_prefix}#{quarter_screen_id(d.isoformat(), q)}" '
                f'data-quarter="{q}" class="jump-link{extra_class}">{text}</a>'
            )
        groups.append(f'<div class="jump-links jump-day-links">{"".join(links)}</div>')

    return "".join(groups)


def render_transition_screen():
    """The screen between Home and the actual Timeline content (see
    requirements/public.md -> Home & Timeline -> Layout) — an explicit
    choice of where to start scrolling into the trip from, replacing the
    old auto-scroll-to-"now" behavior (see -> Always the full trip, "now"
    computed live, for why). "Jump to now" is client-computed
    (shared/nav.js's currentQuarterSectionId(), the identical computation
    the "Timeline" nav item's own click uses); "Aug 1st" is a plain
    anchor to the very first quarter screen — scrolling on past this
    screen without picking anything already leads there, so it's just a
    shortcut past the choice itself, not a separate code path."""
    first_id = quarter_screen_id(TRIP_START.isoformat(), QUARTERS[0])
    return f"""<section class="transition-screen" id="trip-transition">
<p class="transition-prompt">Where would you like to start?</p>
<div class="transition-choices">
<button type="button" id="transition-now" class="transition-choice" data-trip-start="{TRIP_START.isoformat()}" data-trip-end="{TRIP_END.isoformat()}">Jump to now</button>
<a href="#{first_id}" id="transition-aug1" class="transition-choice">Aug 1st</a>
</div>
</section>"""


def build_timeline_html(people, travel, meals, activities, accommodation_structures):
    people_by_id = {p["id"]: p for p in people}

    screens = [render_intro_screen(), render_transition_screen()]
    is_first = True
    for d in daterange(TRIP_START, TRIP_END):
        for q in QUARTERS:
            screens.append(render_quarter_screen(d, q, travel, people_by_id, meals, activities, accommodation_structures, is_first=is_first))
            is_first = False

    return "\n".join(screens)


def build_page_html(people, travel, meals, activities, structures, shared_base_css, shared_css, shared_nav_js, shared_js):
    jump_panel = render_jump_panel()
    folks_menu = nav.render_folks_menu(people, travel, timeline_prefix="", attendees_prefix="attendees/")
    milestones_menu = nav.render_milestones_menu(people, travel, timeline_prefix="", attendees_prefix="attendees/")
    attending_people = [p for p in people if p.get("attending")]
    nav_row = nav.render_nav(
        mc26_href=f"#{INTRO_SCREEN_ID}",
        timeline_prefix="",
        tree_href="family-tree/index.html",
        trip_start=TRIP_START.isoformat(),
        trip_end=TRIP_END.isoformat(),
        jump_panel_html=jump_panel,
        folks_panel_html=folks_menu,
        milestones_panel_html=milestones_menu,
        attending_people=attending_people,
        attendees_prefix="attendees/",
        include_play=True,
    )
    accommodation_structures = [s for s in structures if s["category"] == "accommodation"]
    timeline_html = build_timeline_html(people, travel, meals, activities, accommodation_structures)
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
{shared_nav_js}
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
    shared_nav_js = (PROJECT_ROOT / "shared" / "nav.js").read_text()
    shared_js = (ROOT / "shared.js").read_text()

    validate_people_file(people)
    validate_structures_file(structures)
    validate_vehicles_file(vehicles)

    people_by_id = {p["id"]: p for p in people}
    validate_travel(travel, people_by_id, structures, vehicles)
    validate_meals_file(meals, structures_with_space_kind(structures, "kitchen"))
    validate_day_quarter_notes(activities, "timeline/data/activities.json")

    html = build_page_html(people, travel, meals, activities, structures, shared_base_css, shared_css, shared_nav_js, shared_js)
    out_path = PROJECT_ROOT / "site" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print("Updated site/index.html")


if __name__ == "__main__":
    main()
