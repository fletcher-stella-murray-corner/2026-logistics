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
| 5 | [requirements/public.md](requirements/public.md) | What the public-facing site should be/do — the Timeline (homepage), Family Tree, and Facts features. Source of truth for desired behavior on the site. There is no admin site or admin requirements doc for this project. |
| 6 | [operations.md](operations.md) | Account inventory, domain/hosting facts. Not a build doc — reference only. Fill in once the real GitHub account/repo exist. |
| 7 | [open-questions.md](open-questions.md) | Unresolved project-level questions (naming, hosting, etc.) that don't block work but shouldn't be forgotten. |

Multi-session milestones (a rebrand, an infra migration) are tracked as a checklist in `workbench/<milestone-name>.md` — see `way-of-working.md` → *Milestones*. The folder is empty between milestones, so it has no permanent entry here.

A feature's own requirements (what it does, page by page) live in `requirements/public.md`, not in the feature's own folder. Each feature folder holds everything else: scripts, data, and shared CSS. There are three features, plus a `shared/` folder for what they need in common:

| # | Doc | Responsibility |
|---|-----|----------------|
| 8 | [shared/data/people.json](shared/data/people.json) | The family roster — shared by all three features. Not deployed directly; each feature's `build.py` reads it and embeds/renders from it at build time. |
| 9 | [shared/data/structures.json](shared/data/structures.json) | The fixed list of named accommodation/transit locations (cottage, red shed, airports, etc), each optionally with a fixed `rooms` list and an `active_from`/`active_to` date range. Validated against — not just referenced by — `timeline/data/travel.json`'s `room`/`room_by_date`/`hub` fields at build time (see `requirements/public.md` → *Structures*). |
| 10 | [shared/data/vehicles.json](shared/data/vehicles.json) | The fixed list of named vehicles used for car travel. Validated against `timeline/data/travel.json`'s `vehicle` field at build time (see `requirements/public.md` → *Vehicles*). |
| 11 | [shared/nav.py](shared/nav.py) | `esc()` used by every feature's `build.py`; the flat-link-row `render_row()` used by `family-tree` and `facts` — timeline builds its own richer nav directly (live label, jump-to-time, jump-to-person, play/pause auto-advance, Tree/Facts links — see `requirements/public.md` → *Navigation*). |
| 12 | [shared/base.css](shared/base.css) | Site-wide chrome shared by every feature: nav bar, color variables, base typography. |
| 13 | [timeline/scripts/build.py](timeline/scripts/build.py) | Regenerates `site/index.html` (the homepage) from `shared/data/people.json`, `shared/data/structures.json`, `shared/data/vehicles.json`, and `timeline/data/travel.json`/`meals.json`/`activities.json`. |
| 14 | [timeline/data/travel.json](timeline/data/travel.json) | Each person's arrival/departure (date, day quarter, mode, hub, vehicle, detail), default room, and optional per-date room overrides. Hand-edited directly — no data-entry script. Also the sole source of truth the Facts feature reads a person's own facts from — nothing is entered twice (see `requirements/public.md` → *Facts* → *Data integrity*). |
| 15 | [timeline/data/meals.json](timeline/data/meals.json) | The meal plan, keyed by date then day quarter. Hand-edited directly. |
| 16 | [timeline/data/activities.json](timeline/data/activities.json) | The activities plan, same shape as `meals.json` (keyed by date then day quarter). Hand-edited directly. |
| 17 | [timeline/shared.css](timeline/shared.css) | CSS specific to the timeline's day quarter canvas layout (see `requirements/public.md` → *Terminology*). |
| 18 | [timeline/shared.js](timeline/shared.js) | Smooth-scrolls and closes the "Jump ▾"/"People ▾" disclosures on link click, updates the nav bar's live current-quarter label as you scroll, and drives the play/pause auto-advance control. |
| 19 | [family-tree/scripts/build.py](family-tree/scripts/build.py) | Regenerates `site/family-tree/index.html` from `shared/data/people.json`. |
| 20 | [family-tree/shared.css](family-tree/shared.css) | CSS specific to the family-tree page's generation/couple/children layout. |
| 21 | [facts/scripts/build.py](facts/scripts/build.py) | Regenerates `site/facts/index.html` and one `site/facts/<id>.html` per attending person, from `shared/data/people.json`'s `attending` field and `timeline/data/travel.json` (see `requirements/public.md` → *Facts*). |
| 22 | [facts/shared.css](facts/shared.css) | CSS specific to the Facts index/person-page layout. |
| 23 | [scripts/build_site.py](scripts/build_site.py) | Root orchestrator — rebuilds every feature in one call. Run this after any data or template edit. |
| 24 | [.github/workflows/deploy.yml](.github/workflows/deploy.yml) | GitHub Actions workflow that publishes `site/` to GitHub Pages on every push to `main`. |

## Site (deployed)

Everything under `site/` is what goes online. GitHub Pages (via the Actions workflow above) points at this folder's contents.

| Path | Responsibility |
|------|----------------|
| [site/index.html](site/index.html) | The Timeline — also the homepage. Build artifact (generated by `timeline/scripts/build.py`) — do not edit directly. |
| [site/family-tree/index.html](site/family-tree/index.html) | The Family Tree page. Build artifact (generated by `family-tree/scripts/build.py`) — do not edit directly. |
| [site/facts/index.html](site/facts/index.html) | The Facts index, grouping everyone into facts collected / facts needed / not attending. Build artifact (generated by `facts/scripts/build.py`) — do not edit directly. |
| site/facts/&lt;id&gt;.html | One per attending person's own facts page (e.g. `site/facts/7.html`). Build artifact (generated by `facts/scripts/build.py`) — do not edit directly. |

## Editing data

There is no admin site and no data-entry scripts for this project — the sole editor hand-edits `shared/data/people.json`, `shared/data/structures.json`, `shared/data/vehicles.json`, `timeline/data/travel.json`, `timeline/data/meals.json`, or `timeline/data/activities.json` directly, then runs `scripts/build_site.py` (see `way-of-working.md` → *Git* for the commit-before-editing rule).
