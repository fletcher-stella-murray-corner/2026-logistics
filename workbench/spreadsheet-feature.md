# Future feature idea: Spreadsheet (NOT STARTED)

**Status: parked.** This is a design that was worked out but deliberately not built — no code has been written, and `requirements/public.md` does not describe this as current site behavior (see its own *Future feature ideas* section, which points here). Don't treat anything below as authorized to implement; if this gets picked up later, run it through `way-of-working.md` → *The loop* like any other requirements change (confirm the design still holds, update `requirements/public.md` properly, then implement) rather than building straight from this file.

## The idea

A fourth feature: a **people × days** grid across the whole trip at once, so someone can see everyone's accommodation/travel status at a glance instead of scrolling ~60 quarter screens or checking 27 individual Attendees pages. Complements, not replaces, the existing three features.

## Design, as worked out

- **Grid axes**: rows = attending people (`attending: true` only, same roster as Attendees), ordered by `generation` then `birth_order`/`id` (same tie-break Family Tree uses for siblings, flattened rather than nested). Columns = trip days, Aug 1–15 (day level, not day-quarter — 15 columns is scannable, 60 isn't).
- **Cell content**: resolved room/structure for that night (reuse the existing `room`/`room_by_date` resolution), a compact arrival/departure marker (reuse `MODE_TAGS`) on the day it happens, "Away" for an excursion date, blank before arrival/after departure. A short legend explains the notation once — note this would be a new pattern for the site, not a reuse of Family Tree's own legend, which was removed (see `family-tree/scripts/build.py` -> `render_person()`).
- **Nav placement**: a genuine 5th top-level nav item ("Spreadsheet"), plain link like "Tree" — not hidden behind Family Tree/Folks the way Attendees is. Requires updating `requirements/public.md` → *Navigation* from four items to five, and `shared/nav.py` → `render_nav()` (new `spreadsheet_href` param) plus its three existing call sites.
- **Mobile**: explicitly desktop-only, with an on-page disclaimer — the one deliberate, documented exception to *Device support*'s normal phone-parity rule. Still wrapped in a horizontally-scrolling container so it's not actually broken on a phone, just not optimized for one.
- **Data**: no new data — pure read-only re-render of `people.json`/`travel.json`/`structures.json`. No new integrity concerns.
- **Implementation reuse**: `spreadsheet/scripts/build.py` (new, mirrors `family-tree/scripts/build.py`'s single-page structure) should reuse `timeline/scripts/build.py` → `quarter_membership()` (cross-imported the same way `attendees/scripts/build.py` already does) for room/presence/arrival/departure — the same single source of truth `scripts/report.py` already reuses, so the grid can't silently disagree with the Timeline about who's where. Also reuses `shared/trip.py` (`TRIP_START`/`TRIP_END`/`MODE_TAGS`/`format_date_jump()`) and `shared/nav.py` (`esc()`, `render_nav()`, `render_folks_menu()`).

## If/when this gets picked up — checklist

- [ ] `requirements/public.md` → *Navigation*: four items → five, add Spreadsheet; new `## Spreadsheet` section (Purpose/Layout/Data/Device support exception); remove the *Future feature ideas* stub once the real section exists
- [ ] `shared/nav.py` → `render_nav()`: new `spreadsheet_href` param, plain link after Tree; update the 3 existing call sites (`timeline/`, `family-tree/`, `attendees/`)
- [ ] New `spreadsheet/scripts/build.py` + `spreadsheet/shared.css` + self-referencing nav link
- [ ] `scripts/build_site.py` — add the 4th `subprocess.run(...)` call + docstring mention
- [ ] `00-index.md` — new rows for the feature's files; "three features" → "four features" language repo-wide
- [ ] Rebuild, browser-check the new page + the nav item on the other three pages (correct relative path per folder depth), phone-width sanity check (scrolls, disclaimer visible)

## Also landed in this session (kept, independent of whether Spreadsheet ever ships)

A general **data-model-change procedure** was added to `way-of-working.md` (new `## Data model changes` section, cross-referenced from `technical.md`) — this was motivated by the discussion around adding a 4th consumer of the shared data files, but stands on its own as a repo-wide process doc and was *not* reverted alongside the rest of this feature.
