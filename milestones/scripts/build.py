#!/usr/bin/env python3
"""Regenerate site/milestones/ — the Milestones feature: five standalone
pages (Arrivals, Meals, Departures, Arrivals and Departures, All — see
requirements/public.md -> Milestones), each a flat, day-headed,
chronological list across the WHOLE trip, not scoped to any one day-
quarter screen the way the Timeline's own Arriving:/Departing: rows are.

Reads shared/data/people.json, timeline/data/travel.json, and
timeline/data/meals.json — read-only, same files timeline/scripts/
build.py already owns and validates; this script doesn't re-validate
their full shape (see load_json() below), trusting scripts/build_site.py
always runs timeline's build first (it already fails loudly on anything
malformed), the same division of responsibility family-tree/scripts/
build.py and attendees/scripts/build.py already rely on.

Arrivals/Departures grouping: several people sharing one real trip (e.g.
a family landing on the same flight) render as one combined row, not one
per person — see group_by_trip() below, which reimplements timeline/
scripts/build.py's own group_legs_by_detail() rule (same mode/hub/
vehicle/detail/driver, or actual partners with nothing else
distinguishing) rather than calling it directly, since that function is
only ever called with pairs already scoped to a single day+quarter and
so never needed the date itself in its own grouping key or return shape
— this one spans the whole trip, so it does, and it also needs to keep
each group's own representative leg (for its date/quarter/time), which
that function's return shape drops.

Arrivals and Departures / All interleave two (or three) different kinds
of row into one chronological list — each row gets a small "Arrival"/
"Departure"/"Meal" kind tag (reusing .fact-label) on those two pages
only; the three single-kind pages omit it, since the whole page already
says what kind it is.

Run after hand-editing shared/data/people.json, timeline/data/
travel.json, or timeline/data/meals.json, or use scripts/build_site.py
to rebuild every feature at once.

site/milestones/*.html are pure build artifacts — edit this template,
not the HTML.
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # milestones/
PROJECT_ROOT = ROOT.parent  # repo root — site/ and shared/ live here

sys.path.insert(0, str(PROJECT_ROOT / "shared"))
import nav  # noqa: E402
from trip import MODE_TAGS, QUARTER_NAMES, QUARTER_TIMES, format_time_range, format_date_full, quarter_screen_id  # noqa: E402

# group_by_trip()/travel_detail() reuse, and the shared TRIP_START/
# TRIP_END/QUARTER_INDEX/render_jump_panel() every page's nav needs — same
# cross-import pattern family-tree/scripts/build.py and attendees/scripts/
# build.py already use.
sys.path.insert(0, str(PROJECT_ROOT / "timeline" / "scripts"))
import build as timeline_build  # noqa: E402

esc = nav.esc

TITLE_SUFFIX = " — Murray Corner 2026"

PAGES = {
    "arrivals.html": ("Arrivals", "Every arrival across the whole trip, in order."),
    "meals.html": ("Meals", "The full meal plan, in order."),
    "departures.html": ("Departures", "Every departure across the whole trip, in order."),
    "arrivals-departures.html": ("Arrivals and Departures", "Everyone coming and going, in one chronological list."),
    "all.html": ("All", "Every arrival, departure, and meal, in one chronological list."),
}
"""title/subtitle for each of shared/nav.py's own MILESTONES_PAGES hrefs —
kept here rather than in that list itself since only this script needs
the subtitle text; nav.py only needs the label/href pair for its links."""


def load_json(path):
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {path}: {e}") from e


def time_label(leg):
    """Same fallback rule attendees/scripts/build.py's own time_label()
    uses: the exact time_range if one is set, otherwise the quarter's own
    bare name, otherwise (00-06, which has no name of its own — see
    requirements/public.md -> Terminology) its own bare time range."""
    time_range = leg.get("time_range")
    if time_range:
        return format_time_range(time_range)
    name = QUARTER_NAMES.get(leg["quarter"], "")
    return name if name else QUARTER_TIMES[leg["quarter"]]


def display_detail(leg, people_by_id, driver_label):
    """Same fields timeline/scripts/build.py's own travel_detail() joins
    — hub/vehicle, free-text detail, driver — EXCEPT time_range, which
    this page shows separately as its own bolded .fact-time (see
    render_group_row() below) rather than folded into the same string,
    unlike every other place travel_detail() is used (a single quarter
    screen, where there's no separate time column to show it in)."""
    parts = []
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


def group_by_trip(pairs, people_by_id, driver_label):
    """Group (person, leg) pairs spanning the WHOLE trip into the same
    "same real trip" buckets timeline/scripts/build.py's own
    group_legs_by_detail() computes for a single quarter (see that
    function's own docstring for the underlying rule this mirrors) — see
    this module's own docstring for why it's reimplemented here rather
    than called directly. Bucketed by (date, quarter, mode, the FULL
    travel_detail() text including time) — the time has to be part of the
    key so two different flights that happen to land in the same broad
    quarter (e.g. 6:30pm and 11:55pm, both "Evening") never merge just
    because they share a hub — see the real bug this exact reasoning
    already caught once, in attendees/scripts/build.py's own
    co_travelers(). Returns a list of {"mode", "detail" (WITHOUT time —
    see display_detail() above), "leg", "people"} dicts, order-preserving
    by first appearance."""
    buckets = {}
    order = []
    for p, leg in pairs:
        bucket_key_detail = timeline_build.travel_detail(leg, people_by_id, driver_label)
        key = (leg["date"], leg["quarter"], leg["mode"], bucket_key_detail)
        if key not in buckets:
            buckets[key] = {
                "mode": leg["mode"],
                "detail": display_detail(leg, people_by_id, driver_label),
                "leg": leg,
                "people": [],
            }
            order.append(key)
        buckets[key]["people"].append(p)

    groups = []
    for key in order:
        bucket = buckets[key]
        leg = bucket["leg"]
        has_distinguishing_detail = any([leg.get("hub"), leg.get("vehicle"), leg.get("detail"), leg.get("driver_id")])
        if has_distinguishing_detail or len(bucket["people"]) == 1:
            groups.append(bucket)
            continue
        bucket_ids = {p["id"] for p in bucket["people"]}
        paired = set()
        for p in bucket["people"]:
            if p["id"] in paired:
                continue
            partner_id = p.get("partner_id")
            if partner_id in bucket_ids and partner_id not in paired:
                partner = next(q for q in bucket["people"] if q["id"] == partner_id)
                groups.append({**bucket, "people": [p, partner]})
                paired.add(p["id"])
                paired.add(partner_id)
            else:
                groups.append({**bucket, "people": [p]})
                paired.add(p["id"])
    return groups


def gather_arrivals(people_by_id, travel):
    """Every attending person's own bookend arrival, plus every
    excursion's own return leg (counts as an arrival, same as everywhere
    else on the site — see requirements/public.md -> Data -> travel.json
    -> excursions) — but ONLY for someone who has a real bookend arrival
    to begin with. Someone with no `arrival` at all (just an
    `arrival_note` — e.g. Jim S/Helen S, "Never left"/"reading in a
    chair") is framed on this page as simply having been here for an
    unclear amount of time (see gather_no_arrival_groups() below), not a
    dated Arrival fact — their excursion's own return leg isn't a real
    "coming back" milestone either, then, since they never registered as
    "away from the trip" in the first place on this page's own terms."""
    pairs = []
    for entry in travel:
        person = people_by_id.get(entry["person_id"])
        if person is None or not person.get("attending"):
            continue
        if entry.get("arrival"):
            pairs.append((person, entry["arrival"]))
            for exc in entry.get("excursions", []):
                pairs.append((person, exc["return"]))
    return pairs


def gather_departures(people_by_id, travel):
    """Every attending person's own bookend departure, plus every
    excursion's own depart leg — same "only for someone with a real
    bookend arrival" exception gather_arrivals() above makes, and for
    the same reason: Jim S/Helen S's own mid-trip excursion isn't a real
    "leaving" milestone on this page, even though they DO have a real
    final departure (Aug 13) that still counts normally."""
    pairs = []
    for entry in travel:
        person = people_by_id.get(entry["person_id"])
        if person is None or not person.get("attending"):
            continue
        if entry.get("departure"):
            pairs.append((person, entry["departure"]))
        if entry.get("arrival"):
            for exc in entry.get("excursions", []):
                pairs.append((person, exc["depart"]))
    return pairs


def gather_no_arrival_groups(people_by_id, travel):
    """Attending people with no bookend `arrival` leg at all (see
    requirements/public.md -> Data -> travel.json -> arrival_note) —
    shown on this page as their own kind of row, "here for an unclear
    amount of time," grouped under the trip's very first day the same
    way the Attendees page's own render_person_page() groups this exact
    case (see that function's own `else` branch) — but reworded for this
    page's own framing rather than each person's own individual
    arrival_note text (Jim's "Never left," Helen's own wording), since
    here they're read as one shared fact about the household rather than
    each person's own story. Actual partners combine into one row, same
    partner-only exception every other grouping rule on this page uses.
    Returns a list of person-lists (one list per row)."""
    people = []
    for entry in travel:
        person = people_by_id.get(entry["person_id"])
        if person is None or not person.get("attending"):
            continue
        if not entry.get("arrival"):
            people.append(person)
    ids = {p["id"] for p in people}
    groups = []
    seen = set()
    for p in people:
        if p["id"] in seen:
            continue
        partner_id = p.get("partner_id")
        if partner_id in ids and partner_id not in seen:
            partner = next(q for q in people if q["id"] == partner_id)
            groups.append([p, partner])
            seen.add(p["id"])
            seen.add(partner_id)
        else:
            groups.append([p])
            seen.add(p["id"])
    return groups


def render_no_arrival_row(people_list, kind_label=None):
    label_html = f'<span class="fact-label">{esc(kind_label)}</span> ' if kind_label else ""
    names = nav.join_names([esc(p["name"]) for p in people_list])
    return f'<div class="fact-line">{label_html}<span class="fact-detail">{names} — here for an unclear amount of time</span></div>'


def gather_meals(meals):
    rows = []
    for day, quarters in meals.items():
        for quarter, entry in quarters.items():
            rows.append({"date": day, "quarter": quarter, "note": entry["note"], "structure": entry.get("structure")})
    return rows


def render_group_row(group, timeline_href, kind_label=None):
    leg = group["leg"]
    names = []
    for p in group["people"]:
        name = esc(p["name"])
        if p.get("dogs"):
            name += f' (+ {esc(", ".join(p["dogs"]))})'
        names.append(name)
    label_html = f'<span class="fact-label">{esc(kind_label)}</span> ' if kind_label else ""
    detail = nav.join_names(names)
    if group["detail"]:
        detail += f" — {esc(group['detail'])}"
    return (
        f'<div class="fact-line">{label_html}'
        f'<span class="fact-time">{esc(time_label(leg))}</span>'
        f'<span class="mode-tag">{esc(MODE_TAGS.get(leg["mode"], leg["mode"]))}</span>'
        f'<span class="fact-detail">{detail} <a href="{timeline_href}">Timeline</a></span>'
        f'</div>'
    )


def render_meal_row(meal, timeline_href, kind_label=None):
    label_html = f'<span class="fact-label">{esc(kind_label)}</span> ' if kind_label else ""
    qname = QUARTER_NAMES.get(meal["quarter"], "")
    time_text = qname if qname else QUARTER_TIMES[meal["quarter"]]
    detail = esc(meal["note"])
    if meal.get("structure"):
        detail += f" — {esc(meal['structure'])}"
    return (
        f'<div class="fact-line">{label_html}'
        f'<span class="fact-time">{esc(time_text)}</span>'
        f'<span class="fact-detail">{detail} <a href="{timeline_href}">Timeline</a></span>'
        f'</div>'
    )


def render_day_grouped(entries):
    """entries: list of (date_iso, html) pairs, already sorted
    chronologically. One <h2 class="fact-day"> per distinct date, exactly
    the same day-heading pattern attendees/scripts/build.py's own
    render_person_page() uses (see shared/base.css -> .fact-day, moved
    there from attendees/shared.css specifically so this feature could
    reuse it without duplicating the rules)."""
    if not entries:
        return '<p class="milestones-empty">Nothing here yet.</p>'
    out = []
    current_date = None
    for date_iso, html in entries:
        if date_iso != current_date:
            d = date.fromisoformat(date_iso)
            out.append(f'<h2 class="fact-day">{esc(format_date_full(d))}</h2>')
            current_date = date_iso
        out.append(html)
    return "".join(out)


def build_page_html(title, subtitle, content_html, shared_base_css, shared_css, shared_nav_js, nav_row):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}{TITLE_SUFFIX}</title>
<style>
{shared_base_css}
{shared_css}
</style>
</head>
<body>
{nav_row}
<h1 class="milestones-title">{esc(title)}</h1>
<p class="milestones-subtitle">{esc(subtitle)}</p>
<main>
{content_html}
</main>
<script>
{shared_nav_js}
</script>
</body>
</html>"""


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    people = load_json(PROJECT_ROOT / "shared" / "data" / "people.json")
    travel = load_json(PROJECT_ROOT / "timeline" / "data" / "travel.json")
    meals = load_json(PROJECT_ROOT / "timeline" / "data" / "meals.json")
    people_by_id = {p["id"]: p for p in people}
    attending_people = [p for p in people if p.get("attending")]

    shared_base_css = (PROJECT_ROOT / "shared" / "base.css").read_text()
    shared_css = (ROOT / "shared.css").read_text()
    shared_nav_js = (PROJECT_ROOT / "shared" / "nav.js").read_text()

    folks_menu = nav.render_folks_menu(people, travel, timeline_prefix="../index.html", attendees_prefix="../attendees/")
    milestones_menu = nav.render_milestones_menu("")
    nav_row = nav.render_nav(
        mc26_href="../index.html#trip-top",
        timeline_prefix="../index.html",
        tree_href="../family-tree/index.html",
        trip_start=timeline_build.TRIP_START.isoformat(),
        trip_end=timeline_build.TRIP_END.isoformat(),
        jump_panel_html=timeline_build.render_jump_panel(href_prefix="../index.html"),
        folks_panel_html=folks_menu,
        milestones_panel_html=milestones_menu,
        attending_people=attending_people,
        attendees_prefix="../attendees/",
        include_play=False,
    )

    arrival_groups = group_by_trip(gather_arrivals(people_by_id, travel), people_by_id, "pickup")
    departure_groups = group_by_trip(gather_departures(people_by_id, travel), people_by_id, "driving")
    meal_rows = gather_meals(meals)
    no_arrival_groups = gather_no_arrival_groups(people_by_id, travel)

    def href_for(iso_date, quarter):
        return f"../index.html#{quarter_screen_id(iso_date, quarter)}"

    def sort_triple(date_iso, quarter, time_range):
        return (date_iso, timeline_build.QUARTER_INDEX[quarter], time_range or [""])

    arrival_entries = [
        (g["leg"]["date"], sort_triple(g["leg"]["date"], g["leg"]["quarter"], g["leg"].get("time_range")), "Arrival", g)
        for g in arrival_groups
    ]
    # Sorted first (quarter index -1, before even 00-06) among Aug 1st's
    # own entries — "here for an unclear amount of time" reads best as
    # the very first thing on the list, not slotted in wherever a real
    # leg happened to land that day.
    arrival_entries += [
        (timeline_build.TRIP_START.isoformat(), (timeline_build.TRIP_START.isoformat(), -1, [""]), "Arrival", g)
        for g in no_arrival_groups
    ]
    departure_entries = [
        (g["leg"]["date"], sort_triple(g["leg"]["date"], g["leg"]["quarter"], g["leg"].get("time_range")), "Departure", g)
        for g in departure_groups
    ]
    meal_entries = [
        (m["date"], sort_triple(m["date"], m["quarter"], None), "Meal", m)
        for m in meal_rows
    ]

    def render_entry(entry, show_label):
        date_iso, _, kind, payload = entry
        label = kind if show_label else None
        if isinstance(payload, list):
            return date_iso, render_no_arrival_row(payload, kind_label=label)
        if kind == "Meal":
            return date_iso, render_meal_row(payload, href_for(payload["date"], payload["quarter"]), kind_label=label)
        leg = payload["leg"]
        return date_iso, render_group_row(payload, href_for(leg["date"], leg["quarter"]), kind_label=label)

    def page_content(entries, show_label):
        entries = sorted(entries, key=lambda e: e[1])
        rows = [render_entry(e, show_label) for e in entries]
        return render_day_grouped(rows)

    content_by_page = {
        "arrivals.html": page_content(arrival_entries, False),
        "meals.html": page_content(meal_entries, False),
        "departures.html": page_content(departure_entries, False),
        "arrivals-departures.html": page_content(arrival_entries + departure_entries, True),
        "all.html": page_content(arrival_entries + departure_entries + meal_entries, True),
    }

    out_dir = PROJECT_ROOT / "site" / "milestones"
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, (title, subtitle) in PAGES.items():
        html = build_page_html(title, subtitle, content_by_page[filename], shared_base_css, shared_css, shared_nav_js, nav_row)
        (out_dir / filename).write_text(html)
    print(f"Updated site/milestones/ ({len(PAGES)} pages)")


if __name__ == "__main__":
    main()
