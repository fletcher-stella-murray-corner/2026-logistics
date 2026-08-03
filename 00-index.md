# Index of Docs

This project has the following documents, each with one job. Don't blur these responsibilities.

[CLAUDE.md](CLAUDE.md), at the repo root, is the entry point an AI session loads automatically — it points here. Not listed in the table below since it's not part of the doc map itself, just the door into it.

## Project docs (not deployed)

Docs that apply to the whole site (not any one feature) live at the root:

| # | Doc | Responsibility |
|---|-----|----------------|
| 1 | [00-index.md](00-index.md) | This file. Map of the project — what each doc does and where things live. |
| 2 | [way-of-working.md](way-of-working.md) | How we (human + AI) operate this project: the requirements-doc loop, git rhythm, session/state hygiene. Process, not architecture — see `technical.md` for that. |
| 3 | [technical.md](technical.md) | How the system is actually built: single-repo structure, every script's job, the build pipeline, GitHub Actions Pages deployment, where CSS/JS/markup changes go. Architecture reference, not process. |
| 4 | [brand-guidelines.md](brand-guidelines.md) | Brand concept, audience, voice, visual direction for the public site. |
| 5 | [requirements/public.md](requirements/public.md) | What the public-facing site should be/do — the Timeline (homepage), Family Tree, and Attendees features. Source of truth for desired behavior on the site. There is no admin site or admin requirements doc for this project. |
| 6 | [operations.md](operations.md) | Account inventory, domain/hosting facts. Not a build doc — reference only. Fill in once the real GitHub account/repo exist. |
| 7 | [open-questions.md](open-questions.md) | Unresolved project-level questions (naming, hosting, etc.) that don't block work but shouldn't be forgotten. |

Multi-session milestones (a rebrand, an infra migration) are tracked as a checklist in `workbench/<milestone-name>.md` — see `way-of-working.md` → *Milestones*. The folder is empty between milestones, so it has no permanent entry here.

A feature's own requirements (what it does, page by page) live in `requirements/public.md`, not in the feature's own folder. Each feature folder holds everything else: scripts, data, and shared CSS. There are three features, plus a `shared/` folder for what they need in common:

| # | Doc | Responsibility |
|---|-----|----------------|
| 8 | [shared/data/people.json](shared/data/people.json) | The family roster — shared by all three features. Not deployed directly; each feature's `build.py` reads it and embeds/renders from it at build time. |
| 9 | [shared/data/structures.json](shared/data/structures.json) | The fixed list of named accommodation/transit locations (cottage, red shed, airports, etc), each optionally with a fixed always-shown `rooms` list (e.g. Cottage), a validated occupancy-shown `instances` list (e.g. Tent — mutually exclusive with `rooms`), an `always_shown` flag for a structure with no fixed rooms that should still always render (e.g. Red Shed), and an `active_from`/`active_to` date range. Validated against — not just referenced by — `timeline/data/travel.json`'s `room`/`room_by_date`/`hub`/`working_from` fields at build time (see `requirements/public.md` → *Structures*). |
| 10 | [shared/data/vehicles.json](shared/data/vehicles.json) | The fixed list of named vehicles used for car travel. Validated against `timeline/data/travel.json`'s `vehicle` field at build time (see `requirements/public.md` → *Vehicles*). |
| 11 | [shared/nav.py](shared/nav.py) | `esc()` used by every feature's `build.py`; the flat-link-row `render_row()` used by `family-tree` and `attendees` — timeline builds its own richer nav directly (live label, jump-to-time, jump-to-person, play/pause auto-advance, Tree link — see `requirements/public.md` → *Navigation*). |
| 12 | [shared/trip.py](shared/trip.py) | Trip-window constants (`TRIP_START`/`TRIP_END`, `QUARTER_LABELS`, `MODE_TAGS`, `WORK_QUARTERS`) and time-formatting helpers (`format_clock()`, `format_time_range()`), shared by `timeline/scripts/build.py` and `attendees/scripts/build.py` so the two builders can't drift apart on the same values. |
| 13 | [shared/base.css](shared/base.css) | Site-wide chrome shared by every feature: nav bar, color variables, base typography. |
| 14 | [timeline/scripts/build.py](timeline/scripts/build.py) | Regenerates `site/index.html` (the homepage) from `shared/data/people.json`, `shared/data/structures.json`, `shared/data/vehicles.json`, and `timeline/data/travel.json`/`meals.json`/`activities.json`. |
| 15 | [timeline/data/travel.json](timeline/data/travel.json) | Each person's arrival/departure (date, day quarter, time_range, mode, hub, vehicle, detail, optional `driver_id`), default room, optional per-date room overrides, optional `working_from` blocks (working from a structure during the day, independent of where they're sleeping), and an optional `pending` flag for tentative/in-progress entries. Hand-edited directly — no data-entry script. Also the sole source of truth the Attendees feature reads a person's own facts from — nothing is entered twice (see `requirements/public.md` → *Attendees* → *Data integrity*). |
| 16 | [timeline/data/meals.json](timeline/data/meals.json) | The meal plan, keyed by date then day quarter. Hand-edited directly. |
| 17 | [timeline/data/activities.json](timeline/data/activities.json) | The activities plan, same shape as `meals.json` (keyed by date then day quarter). Hand-edited directly. |
| 18 | [timeline/shared.css](timeline/shared.css) | CSS specific to the timeline's day quarter canvas layout (see `requirements/public.md` → *Terminology*). |
| 19 | [timeline/shared.js](timeline/shared.js) | Smooth-scrolls and closes the jump-to-time (the current-quarter label itself, doubling as the disclosure trigger) and "Folks ▾" disclosures on link click, updates the nav bar's live current-quarter label as you scroll, and drives the play/pause auto-advance control. |
| 20 | [family-tree/scripts/build.py](family-tree/scripts/build.py) | Regenerates `site/family-tree/index.html` from `shared/data/people.json`, plus a read-only look at `timeline/data/travel.json` for each box's facts-collected/collecting-facts/not-attending visual (see `requirements/public.md` → *Family Tree* → *Layout*). |
| 21 | [family-tree/shared.css](family-tree/shared.css) | CSS specific to the family-tree page's generation/couple/children layout. |
| 22 | [attendees/scripts/build.py](attendees/scripts/build.py) | Regenerates one `site/attendees/<id>.html` per attending person, from `shared/data/people.json`'s `attending` field and `timeline/data/travel.json` (see `requirements/public.md` → *Attendees*). No index page — reached via the Family Tree or the Timeline's "Folks ▾". |
| 23 | [attendees/shared.css](attendees/shared.css) | CSS specific to the Attendees person-page layout. |
| 24 | [scripts/build_site.py](scripts/build_site.py) | Root orchestrator — rebuilds every feature in one call. Run this after any data or template edit. |
| 25 | [.github/workflows/deploy.yml](.github/workflows/deploy.yml) | GitHub Actions workflow that publishes `site/` to GitHub Pages on every push to `main` — gated by a `verify-build` job that reruns `scripts/build_site.py` and fails the deploy if the committed `site/` doesn't match (see `technical.md` → *Repo & deployment*). |

## Site (deployed)

Everything under `site/` is what goes online. GitHub Pages (via the Actions workflow above) points at this folder's contents.

| Path | Responsibility |
|------|----------------|
| [site/index.html](site/index.html) | The Timeline — also the homepage. Build artifact (generated by `timeline/scripts/build.py`) — do not edit directly. |
| [site/family-tree/index.html](site/family-tree/index.html) | The Family Tree page. Build artifact (generated by `family-tree/scripts/build.py`) — do not edit directly. |
| site/attendees/&lt;id&gt;.html | One per attending person's own facts page (e.g. `site/attendees/7.html`), linked from their box on the Family Tree page and from the Timeline's "Folks ▾". No index page. Build artifact (generated by `attendees/scripts/build.py`) — do not edit directly. |

## Editing data

There is no admin site and no data-entry scripts for this project — the sole editor hand-edits `shared/data/people.json`, `shared/data/structures.json`, `shared/data/vehicles.json`, `timeline/data/travel.json`, `timeline/data/meals.json`, or `timeline/data/activities.json` directly, then runs `scripts/build_site.py` (see `way-of-working.md` → *Git* for the commit-before-editing rule).
