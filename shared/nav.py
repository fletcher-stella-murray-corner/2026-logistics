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

from trip import TRIP_START, QUARTERS, quarter_screen_id


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


def render_nav(*, mc26_href, timeline_prefix, tree_href, trip_start, trip_end,
                jump_panel_html, folks_panel_html, attending_people, attendees_prefix,
                include_play):
    """The site's one shared nav bar shape — MC26 (fixed identity + link to
    Home), Timeline (split control: label jumps to "now", caret opens a
    panel with the day/quarter jump list and, on site/index.html only,
    play/pause), Folks (split control: label jumps to a random attending
    person, caret opens a person-picker panel), Tree (plain link) — see
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
    identically by every feature.
    `attending_people` — the full attending roster as a list of dicts with
    at least 'id'/'name', for the Folks split control's random-click (the
    same roster regardless of which Folks panel variant is shown).
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

    return f"""<nav class="site-nav">
<a href="{mc26_href}" class="site-title">MC26</a>
{timeline_split}
{folks_split}
<a href="{tree_href}">Tree</a>
</nav>"""
