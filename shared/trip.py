"""Shared trip constants and time-formatting helpers, imported by
timeline/scripts/build.py and attendees/scripts/build.py — the two
features that both render arrival/departure legs and day-quarter labels
from the same trip window. Not a script: no CLI, imported like a plain
module (see shared/nav.py for the sibling esc()/require()/render_nav()/
render_folks_menu() helpers).

TRIP_START/TRIP_END and QUARTER_LABELS/MODE_TAGS/WORK_QUARTERS live here
so the two builders can't drift apart (e.g. a new travel mode or an
emoji change landing in one file's copy but not the other's). family-
tree/scripts/build.py doesn't need any of this — it never renders a leg
or a day-quarter label.
"""
from datetime import date

TRIP_START = date(2026, 8, 1)
TRIP_END = date(2026, 8, 15)

# 00-06 deliberately has no name of its own — see requirements/public.md
# -> Terminology for why: night reads as the tail end of the day before
# it, not the start of the one after, so the nav's live label identifies
# that quarter by the new day itself ("Tuesday") rather than a invented
# "Tuesday Night" — and everywhere else a quarter needs a display label
# (the jump-to-time panel, the Attendees page's fallback quarter label)
# follows the same rule: 00-06 shows only its bare time range, no name.
# QUARTER_NAMES is the single source of truth for that — empty string for
# 00-06, never "Night" — and QUARTER_LABELS (composed below) collapses
# cleanly to just the time range rather than leaving an orphaned "· " where
# a name would otherwise go.
QUARTER_NAMES = {
    "00-06": "",
    "06-12": "Morning",
    "12-18": "Afternoon",
    "18-24": "Evening",
}
QUARTER_TIMES = {
    "00-06": "12am–6am",
    "06-12": "6am–12pm",
    "12-18": "12pm–6pm",
    "18-24": "6pm–12am",
}
QUARTER_LABELS = {
    q: (f"{QUARTER_NAMES[q]} · {QUARTER_TIMES[q]}" if QUARTER_NAMES[q] else QUARTER_TIMES[q])
    for q in QUARTER_NAMES
}
# Fixed cycle order, derived from QUARTER_NAMES (Python dicts preserve
# insertion order) rather than a second hand-typed list that could drift
# out of sync with it.
QUARTERS = tuple(QUARTER_NAMES)
MODE_TAGS = {
    "plane": "✈️ Plane",
    "train": "🚆 Train",
    "car": "🚗 Car",
}
# The only quarters a `working_from` block may cover (see
# requirements/public.md -> Data -> travel.json -> working_from) — working
# from a structure isn't a concept this site tracks overnight.
WORK_QUARTERS = ("06-12", "12-18")


def format_clock(hhmm):
    hour, minute = (int(part) for part in hhmm.split(":"))
    period = "am" if hour < 12 else "pm"
    hour12 = hour % 12 or 12
    return f"{hour12}{period}" if minute == 0 else f"{hour12}:{minute:02d}{period}"


def format_time_range(time_range):
    start, end = time_range
    return format_clock(start) if start == end else f"{format_clock(start)}–{format_clock(end)}"


def ordinal(n):
    """11th/12th/13th are the exception to the usual 1st/2nd/3rd/4th-
    pattern (the "teens" always take -th, not just n%10==1/2/3), so this
    checks n%100 first before falling back to n%10."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def format_date_full(d):
    """Full weekday, full month, ordinal day — "Wednesday, August 5th".
    The natural-speech date format, for anywhere with room to say the
    whole thing: the Attendees page's day headings and inline "till..."
    mentions, and the Timeline's jump-to-time panel day groups. NOT the
    Timeline's own live nav label — that's a single-row control sharing
    space with three other nav items on a phone, so it uses
    format_date_abbrev() below instead (see requirements/public.md ->
    Navigation)."""
    return d.strftime("%A, %B ") + ordinal(d.day)


def quarter_screen_id(iso_date, quarter):
    """The Timeline's per-quarter-screen anchor id ("qc-2026-08-05-06-12"),
    shared so a cross-page link (the Folks panel's "Timeline" jump, see
    shared/nav.py -> render_folks_menu()) and an in-page one
    (timeline/scripts/build.py's own quarter screens and jump panel)
    always agree on the same id."""
    return f"qc-{iso_date}-{quarter}"


def format_date_abbrev(d):
    """Weekday-first, abbreviated — "Wed, Aug 5". Used only where nav-bar
    space is tight (the Timeline's own live current-quarter label, see
    timeline/scripts/build.py -> render_quarter_screen() and
    timeline/shared.js) — everywhere else on the site with room to spare
    uses format_date_full() above instead. Weekday-first either way: the
    order bug this replaced ("Aug 5 · Monday Morning") was never about
    abbreviation, only about which piece came first."""
    return d.strftime("%a, %b ") + str(d.day)
