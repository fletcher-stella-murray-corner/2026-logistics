#!/usr/bin/env python3
"""Print a room/structure occupancy report across the whole trip — a
read-only cross-person review aid, not a validator. scripts/build_site.py
already validates every file's own structural correctness (every
reference points at something real); it has no notion of whether a
change still makes sense next to what everyone ELSE's entry says. That's
always a human judgment call (see way-of-working.md -> Data entry), and
it's easy to get right for the person actively being edited while
forgetting someone else's entry the same change quietly affects — e.g.
adding a new person into a room without also moving the people already
in it, which build_site.py has no way to flag since both entries are,
independently, perfectly well-formed.

Walks every day quarter of the trip and, for each one where an arrival,
a departure, or the resulting room/structure occupancy actually CHANGES
from the quarter before, prints who's arriving, departing, and where
everyone stands afterward. Every unchanged quarter is skipped, so a
13-day/4-quarter trip (52 screens) compresses down to just its actual
transition points — the places a forgotten update on someone else's
entry would show up as a lopsided or missing name.

Reuses quarter_membership() from timeline/scripts/build.py — the exact
same function render_quarter_screen() calls to build the Timeline's own
live Structures/Arriving/Departing rows — so this report can never show
something different from what the site itself will render, and a future
change to how presence/rooms are computed only has to happen once.

Run this after any hand-edit to shared/data/people.json or
timeline/data/travel.json, before committing — see way-of-working.md ->
Data entry. Read-only: loads and validates the same files
scripts/build_site.py does, but writes nothing.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root

sys.path.insert(0, str(ROOT / "timeline" / "scripts"))
import build as timeline_build  # noqa: E402


def load_data():
    people = timeline_build.load_json(ROOT / "shared" / "data" / "people.json")
    structures = timeline_build.load_json(ROOT / "shared" / "data" / "structures.json")
    vehicles = timeline_build.load_json(ROOT / "shared" / "data" / "vehicles.json")
    travel = timeline_build.load_json(ROOT / "timeline" / "data" / "travel.json")

    timeline_build.validate_people_file(people)
    timeline_build.validate_structures_file(structures)
    timeline_build.validate_vehicles_file(vehicles)
    people_by_id = {p["id"]: p for p in people}
    timeline_build.validate_travel(travel, people_by_id, structures, vehicles)

    return people, structures, travel, people_by_id


def occupancy_snapshot(present, working, accommodation_structures):
    """{label: sorted names} for both sleeping (a plain structure/room
    label) and working (a separate 'structure (working)' label, so the
    two never merge into one name list — mirrors the Timeline's own
    "Working" sub-box distinction) — a hashable, comparable snapshot so
    two quarters' occupancy can be diffed with a plain !=, no bespoke
    comparison logic needed."""
    by_label = {}
    for person, room in present:
        structure, detail = timeline_build.parse_room(room, accommodation_structures)
        label = f"{structure} — {detail}" if detail else (structure or "Unassigned")
        by_label.setdefault(label, set()).add(person["name"])
    for person, structure_name in working:
        by_label.setdefault(f"{structure_name} (working)", set()).add(person["name"])
    return {label: tuple(sorted(names)) for label, names in by_label.items()}


def format_snapshot(snapshot):
    if not snapshot:
        return "    (nobody assigned anywhere)"
    return "\n".join(f"    {label}: {', '.join(snapshot[label])}" for label in sorted(snapshot))


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    people, structures, travel, people_by_id = load_data()
    accommodation_structures = [s for s in structures if s["category"] == "accommodation"]

    prev_snapshot = None
    printed_any = False
    for day in timeline_build.daterange(timeline_build.TRIP_START, timeline_build.TRIP_END):
        day_iso = day.isoformat()
        for quarter in timeline_build.QUARTERS:
            key = timeline_build.quarter_key(day_iso, quarter)
            arrivals, departures, present, working = timeline_build.quarter_membership(
                key, day_iso, quarter, travel, people_by_id
            )
            snapshot = occupancy_snapshot(present, working, accommodation_structures)
            changed = snapshot != prev_snapshot
            if not (arrivals or departures or changed):
                continue

            printed_any = True
            weekday = day.strftime("%a")
            date_label = day.strftime("%b ") + str(day.day)
            print(f"{weekday}, {date_label} · {timeline_build.QUARTER_LABELS[quarter]}")
            if arrivals:
                print(f"  Arriving: {', '.join(p['name'] for p, _ in arrivals)}")
            if departures:
                print(f"  Departing: {', '.join(p['name'] for p, _ in departures)}")
            print("  Now:")
            print(format_snapshot(snapshot))
            print()
            prev_snapshot = snapshot

    if not printed_any:
        print("No arrivals, departures, or room/structure changes found in travel.json.")


if __name__ == "__main__":
    main()
