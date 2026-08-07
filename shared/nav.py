"""Shared nav helpers, imported by every feature's build.py.
Not a script: no CLI, imported like a plain module.

esc() is used by every feature for HTML-escaping. require() is used by
every feature to validate a required field on a hand-edited JSON record
with a friendly message (record + missing field) instead of a raw
KeyError traceback. render_nav() builds the one shared nav bar shape
every page uses — see its own docstring and requirements/public.md ->
Navigation.
"""
import json
from datetime import date

from trip import TRIP_START, QUARTERS, QUARTER_NAMES, quarter_screen_id, format_date_jump, format_time_range


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def require(record, field, label):
    """Return record[field], or raise a friendly ValueError naming `label`
    (a human description of which record, e.g. "Person at index 3 (id 7)
    in shared/data/people.json") instead of letting a bare KeyError from
    record[field] surface as a raw traceback during hand-edited data entry."""
    if field not in record:
        raise ValueError(f"{label} is missing required field {field!r}.")
    return record[field]


def join_names(names):
    """Plain-English join for a short list of names — "Ann", "Ann & Bo", or
    "Ann, Bo & Cy". Used by both timeline/scripts/build.py (grouping
    several people who share one arrival/departure leg into a single line
    — see render_travel_row()) and attendees/scripts/build.py (an airport
    run's passenger list — see airport_run_line()), so the two can't drift
    on the join style. Not esc()'d here — callers pass already-escaped
    names."""
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} & {names[-1]}"


def render_folks_menu(people, travel, *, timeline_prefix, attendees_prefix):
    """The Folks split control's panel content — one shape, one roster,
    used identically on every page (Home/Timeline, Family Tree, Details)
    now, replacing what used to be two different implementations that had
    to be kept in sync by hand (a travel.json-sourced list on Home/
    Timeline, a people.json-sourced one everywhere else) — see
    requirements/public.md -> Navigation -> Folks panel.

    Every ATTENDING person in shared/data/people.json, no one left out for
    lacking a travel.json entry yet. Each entry is a plain-text name plus
    two links: "Timeline" jumps to their arrival's quarter screen, or the
    trip's very first quarter screen if they have no arrival entry at all
    (same fallback the old Home/Timeline variant already used for this
    case); "Detail" goes to their own Attendees page. No status text
    (no "Collecting facts") — that distinction now lives only on the
    Family Tree box itself and the person's own Attendees page, not
    narrated a second time here.

    `timeline_prefix` is the same value the caller already passes to
    render_nav() below ("" on site/index.html itself, e.g. "../index.html"
    elsewhere) — a same-page anchor or a cross-page link to the exact same
    target either way. Display order is NOT decided here: every entry
    renders in whatever order `people` is passed in, and shared/nav.js
    shuffles the actual DOM order fresh on every page load (see
    requirements/public.md -> Navigation -> Folks panel) — a random order
    baked in at build time would be the same every time this static page
    is loaded, which isn't actually random."""
    travel_by_person = {t["person_id"]: t for t in travel}
    attending = [p for p in people if p.get("attending")]
    if not attending:
        return ""

    entries = []
    for person in attending:
        entry = travel_by_person.get(person["id"])
        arrival = entry.get("arrival") if entry else None
        if arrival:
            target_date, target_quarter = arrival["date"], arrival["quarter"]
        else:
            target_date, target_quarter = TRIP_START.isoformat(), QUARTERS[0]
        timeline_href = f"{timeline_prefix}#{quarter_screen_id(target_date, target_quarter)}"
        entries.append(
            f'<span class="jump-person">'
            f'<span class="jump-person-name">{esc(person["name"])}</span>'
            f'<span class="jump-person-actions">'
            f'<a href="{timeline_href}">Timeline</a>'
            f'<a href="{attendees_prefix}{person["id"]}.html">Detail</a>'
            f'</span>'
            f'</span>'
        )
    return "".join(entries)


def render_milestones_menu(people, travel, *, timeline_prefix, attendees_prefix):
    """The Milestones panel's two lists — every attending person's own
    arrival and every attending person's own departure, one flat
    chronological row per person, oldest first (see
    requirements/public.md -> Navigation -> Milestones panel). Computed
    once here and reused identically by every feature's build.py, same
    reasoning render_folks_menu() above already documents (one shape, one
    roster, no per-feature copy to drift out of sync).

    An excursion's own `return` leg counts as an arrival and its `depart`
    leg counts as a departure, same as everywhere else on the site (the
    Timeline's own Arriving:/Departing: rows, driving_assignments() on the
    Attendees page) — someone with a mid-stay round trip shows up twice in
    these two lists. Not-attending people, and anyone with no arrival (or
    no departure) leg at all, simply don't appear in that one list — no
    synthesized fallback the way the Folks panel's random-click target
    needs one.

    Deliberately ONE ROW PER PERSON, never grouped the way the Timeline's
    own rows combine several people sharing one real trip (see
    requirements/public.md -> Home & Timeline -> Row-by-row rules ->
    Arrivals) — this panel is a scannable flat roster of individual facts,
    not a day-quarter canvas, so there's no "same trip" concept to fold
    rows into here.

    Returns (arrivals_html, departures_html) — render_nav() below wraps
    each in its own tab panel."""
    travel_by_person = {t["person_id"]: t for t in travel}
    attending = [p for p in people if p.get("attending")]

    def sort_key(item):
        _, leg = item
        return (leg["date"], QUARTERS.index(leg["quarter"]), leg.get("time_range") or [""])

    def render_list(events):
        events.sort(key=sort_key)
        rows = []
        for person, leg in events:
            d = date.fromisoformat(leg["date"])
            time_range = leg.get("time_range")
            if time_range:
                when = f"{esc(format_date_jump(d))} · {esc(format_time_range(time_range))}"
            else:
                qname = QUARTER_NAMES[leg["quarter"]]
                when = esc(format_date_jump(d)) + (f" · {esc(qname)}" if qname else "")
            timeline_href = f"{timeline_prefix}#{quarter_screen_id(leg['date'], leg['quarter'])}"
            rows.append(
                f'<span class="jump-person milestone-row">'
                f'<span class="jump-person-name">{esc(person["name"])}</span>'
                f'<span class="milestone-time">{when}</span>'
                f'<span class="jump-person-actions">'
                f'<a href="{timeline_href}">Timeline</a>'
                f'<a href="{attendees_prefix}{person["id"]}.html">Detail</a>'
                f'</span>'
                f'</span>'
            )
        return "".join(rows)

    arrivals, departures = [], []
    for person in attending:
        entry = travel_by_person.get(person["id"])
        if not entry:
            continue
        if entry.get("arrival"):
            arrivals.append((person, entry["arrival"]))
        if entry.get("departure"):
            departures.append((person, entry["departure"]))
        for exc in entry.get("excursions", []):
            departures.append((person, exc["depart"]))
            arrivals.append((person, exc["return"]))

    return render_list(arrivals), render_list(departures)


def render_nav(*, mc26_href, timeline_prefix, tree_href, trip_start, trip_end,
                jump_panel_html, folks_panel_html, milestones_panel_html, attending_people, attendees_prefix,
                include_play):
    """The site's one shared nav bar shape — MC26 (fixed identity + link to
    Home), Timeline (split control: label jumps to "now", caret opens a
    panel with the day/quarter jump list and, on site/index.html only,
    play/pause), Folks (split control: label jumps to a random attending
    person, caret opens a person-picker panel), Milestones (caret-only
    disclosure — no default click of its own, see render_milestones_menu()
    above — opens a panel with two tab-switched flat lists, every
    arrival/every departure), Tree (plain link) — see
    requirements/public.md -> Navigation. Identical shape on every page;
    only hrefs/prefixes and panel contents differ, supplied by the caller,
    so the three build scripts can never drift apart on what this looks
    like.

    `timeline_prefix` — relative path to site/index.html: "" when this
    page IS index.html (shared/nav.js reads the empty data-prefix and
    scrolls in place instead of navigating), otherwise e.g. "../index.html".
    `jump_panel_html` / `folks_panel_html` — pre-rendered panel contents:
    the day/quarter jump list is still feature-specific (see
    timeline/scripts/build.py's render_jump_panel()), but the Folks panel
    is now this same module's own render_folks_menu() above, called
    identically by every feature. `milestones_panel_html` is a
    (arrivals_html, departures_html) pair — this module's own
    render_milestones_menu() above, same "computed once, called
    identically by every feature" shape as the Folks panel.
    `attending_people` — the full attending roster as a list of dicts with
    at least 'id'/'name', for the Folks split control's random-click (the
    same roster regardless of which Folks panel variant is shown), and to
    decide whether the Milestones item renders at all (no roster, nothing
    to list).
    `include_play` — True only for site/index.html, the one page with an
    actual scroll sequence to auto-advance through.
    """
    play_html = (
        '<button type="button" id="run-toggle" class="run-toggle" aria-label="Play">▶</button>'
        if include_play else ""
    )
    timeline_split = f"""<span class="nav-split current-quarter-menu">
<button type="button" id="timeline-jump" class="nav-split-label current-quarter-label" data-trip-start="{esc(trip_start)}" data-trip-end="{esc(trip_end)}" data-prefix="{esc(timeline_prefix)}"><span class="cq-date" id="cq-date"></span><span class="cq-day" id="cq-day">Timeline</span></button>
<details class="jump-menu">
<summary><span class="nav-caret" id="timeline-caret">▾</span></summary>
<div class="jump-panel">{jump_panel_html}{play_html}</div>
</details>
</span>"""

    folks_split = ""
    if attending_people:
        people_attr = esc(json.dumps([{"id": p["id"], "name": p["name"]} for p in attending_people]))
        folks_split = f"""<span class="nav-split">
<button type="button" id="folks-random" class="nav-split-label" data-attendees-prefix="{esc(attendees_prefix)}" data-people="{people_attr}">Folks</button>
<details class="jump-menu">
<summary><span class="nav-caret">▾</span></summary>
<div class="jump-panel"><div class="folks-list">{folks_panel_html}</div></div>
</details>
</span>"""

    milestones_menu = ""
    if attending_people:
        arrivals_html, departures_html = milestones_panel_html
        milestones_menu = f"""<details class="jump-menu">
<summary><span class="nav-split-label">Milestones</span> <span class="nav-caret">▾</span></summary>
<div class="jump-panel milestones-panel">
<div class="milestones-tabs">
<button type="button" class="milestones-tab is-active" data-milestones-tab="arrivals">Arrivals</button>
<button type="button" class="milestones-tab" data-milestones-tab="departures">Departures</button>
</div>
<div class="milestones-list" data-milestones-panel="arrivals">{arrivals_html}</div>
<div class="milestones-list" data-milestones-panel="departures" hidden>{departures_html}</div>
</div>
</details>"""

    return f"""<nav class="site-nav">
<a href="{mc26_href}" class="site-title">MC26</a>
{timeline_split}
{folks_split}
{milestones_menu}
<a href="{tree_href}">Tree</a>
</nav>"""
