# Technical Architecture

How this project is actually built: the single-repo structure, the build pipeline, what every script does, and where a CSS/JS/markup change belongs. This is architecture reference, not process — for how we (human + AI) actually work together (the requirements-doc loop, git rhythm, milestone tracking), see `way-of-working.md`. For account/domain/hosting facts, see `operations.md`.

## Shape of the system

- One site, one repo: the public site (`site/`) plus every feature's source (data, scripts, shared CSS/JS) live together — see `requirements/public.md` for what the site does, and *Repo & deployment* below for hosting. There is no admin/data-entry site; the sole editor edits data files directly and reruns the build.
- No runtime backend. Every page is a **build artifact**: a Python script renders static HTML directly from a feature's data file(s) at build time, so pages open via `file://` or a static host with nothing to serve and nothing to keep alive.
- No npm, no bundler, no framework. Each feature's `build.py` (and `scripts/build_site.py`, which calls every feature's build script in one go) is the one build step, and is the intentional exception to that rule — it's plain Python 3 with no dependencies.
- `.claude/launch.json` (committed, not gitignored) defines local static-server configs for AI-tool browser-preview integrations to serve pages over HTTP during a session. This doesn't change anything above: pages still open directly via `file://` with nothing to serve, this is just a convenience for previewing in a browser sandbox that can't load `file://` URLs.

## Repo & deployment

One GitHub repo, `fletcher-stella-murray-corner/2026-logistics`, holds everything: source data, scripts, docs, and the built `site/` output. It can be private or public — either way, GitHub Pages can serve from it.

**Deploying:** a GitHub Actions workflow (`.github/workflows/deploy.yml`) publishes the contents of `site/` to GitHub Pages on every push to `main`. There is no manual deploy script and no second repo — commit and `git push`, and the live site updates a minute or two later. One-time setup: in the repo's Settings → Pages, set *Source* to "GitHub Actions" (see `operations.md`).

**Normal update flow:** edit a data file (or run a feature's `build.py` after hand-editing it), review the regenerated page locally, commit, push. See `way-of-working.md` → *Git*.

## Scripts

Every script lives in a feature's `scripts/` folder, is plain Python 3 with no dependencies, and should support `-h`/`--help`.

**Data entry** — there is no add/set script pair. The sole editor (you) hand-edits a feature's JSON data file directly, then reruns its `build.py`. See each feature's data file structure in `requirements/public.md`.

**Build** — regenerate HTML from data. Run after hand-editing a data file or changing a page template.

| Script | Purpose |
|--------|---------|
| `scripts/build_site.py` | Root orchestrator — calls every feature's `build.py` in one go. The everyday command: run this after any data or template edit. |
| `timeline/scripts/build.py` | Regenerates `site/index.html` (the homepage, and the whole timeline feature) from `shared/data/people.json`, `shared/data/structures.json`, `shared/data/vehicles.json`, and `timeline/data/travel.json`/`meals.json`/`activities.json`. Fails loudly (never silently skips or mis-renders) on: an unknown `room`/`room_by_date`/`hub` not found in `structures.json`; an unknown `vehicle` not found in `vehicles.json`; a `person_id` not found in `people.json`; a malformed `date`/`quarter` anywhere; a departure before its arrival; or a duplicate `id` in `people.json`/`structures.json`/`vehicles.json`. |
| `family-tree/scripts/build.py` | Regenerates `site/family-tree/index.html` from `shared/data/people.json`. Fails loudly on a duplicate `id`, a `parent_ids`/`partner_id` referencing an id that doesn't exist, or someone listed as their own parent/partner. |
| `shared/nav.py` | Not a script — `esc()` is used by both features' `build.py` for HTML-escaping; `render_row()` (a flat nav-link row) is used only by `family-tree/scripts/build.py`. The timeline feature builds its own richer nav (live label, jump menu, disabled Tree item) directly, since `render_row()`'s shape doesn't fit it — see `requirements/public.md` → *Navigation*. |

## Where CSS and JS changes go

- **`shared/base.css`** — site-wide chrome shared by both features: nav bar, color variables, base typography. Change here affects every page.
- **A feature's `shared.css`** (e.g. `timeline/shared.css`) — CSS specific to that feature's page(s) only (day quarter canvas layout, family-tree diagram styling).
- **Inline `<style>`/`<script>` in the page** — page-specific setup only: rendered content and any page configuration constants. Nothing else belongs here.

When in doubt: if a change would need to be made in more than one page, it belongs in `shared/base.css` (site-wide) or the owning feature's `shared.css` (feature-wide), not copied into each page's inline block.

**After editing any of these, run `scripts/build_site.py` before previewing.** No page in `site/` links to `shared/base.css` or a feature's `shared.css`/`shared.js` at runtime — the build step inlines their contents into each page's `<style>`/`<script>` block (see *Shape of the system* above). Editing a source file and reloading a page already open from `site/` will show zero change, no matter how correct the edit is — the browser is still rendering whatever was embedded at the last build.

## Lessons learned

Empty for now. As you build on this template, a durable gotcha, root cause, and the rule it establishes going forward belongs here — not just the fix, and not left in AI-tool-side memory outside this repo (see `way-of-working.md` → *Local & session state*).

## Architecture boundary

This repo does not depend on other projects or systems on the machine (other codebases, a personal planning/documentation system, global tool config) to be built, deployed, or understood — everything needed is in this repo. If that ever stops being true (a script starts reading from outside the repo, a doc's meaning depends on external context), that dependency must be called out explicitly wherever it's introduced — in the relevant doc, not left implicit.
