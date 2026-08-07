# Way of Working

A tiny project: a requirements doc + an implementation. Keep it that way. This doc is about how we (human + AI) work together — the requirements-doc loop, git rhythm, session/state hygiene. For how the system is actually built (single-repo structure, scripts, the build pipeline, where CSS/JS changes go), see `technical.md`.

One requirements doc — see `00-index.md` for the full doc map:
- [requirements/public.md](requirements/public.md) — the public site (`site/`): the Timeline (homepage), Family Tree, Attendees, and Milestones features. There is no admin site for this project; the sole editor hand-edits data files directly (see `00-index.md` → *Editing data*).

## The loop

1. **Update requirements** — Human (with AI help) edits the relevant requirements doc to describe a desired change.
2. **Update implementation** — AI reads that doc and updates the corresponding implementation to match it.
3. **Review** — Human opens the implementation in a browser and checks it matches what the doc describes.
4. Repeat.

## Rules of thumb

- Each requirements doc describes *what its site* should do/look like, including scope/structure — that's defined there, not here.
- Each requirements doc is the source of truth for its own site. If the implementation and a requirements doc ever disagree, that's a bug — fix one to match the other.
- Keep the implementation as simple as the requirements docs allow — see `technical.md` → *Shape of the system* for the specific constraints (no npm/bundler/framework, the one build-step exception).
- Never remove working functionality just because a requirements doc says it belongs somewhere else, unless the replacement already exists and works, or the human has explicitly confirmed the interim gap is fine. Rewriting a requirements doc to describe a future split is not authorization to delete the current implementation before that split is actually built.
- When verifying a CSS transition/animation via the browser preview tool, trust a screenshot over `getComputedStyle`/`getBoundingClientRect` read through `eval`. Those reads can go stale for an element whose classList was mutated by an *earlier* `eval` call in the same session — reporting the pre-mutation style back with no error — while the actual rendered frame (and a fresh screenshot of it) is correct. A screenshot goes through the real render pipeline; a follow-up `eval` read of computed style doesn't reliably do the same.
- When clicking an element in the browser preview tool, use a `ref` from `read_page` rather than a raw pixel coordinate read off a screenshot. The screenshot image can be downscaled from the actual viewport (e.g. an 800×455 screenshot of a 1280×720 page) — a coordinate that looks right on the screenshot then lands on the wrong element with no error, and nothing about the click's own result reveals the miss. Confirm via a state check (console log, DOM read) tied to the *specific* element you meant to hit, not just "the click didn't error."
- `scrollIntoView({behavior: 'smooth'})` triggered inside the browser preview tool (via a mistargeted click, or via `javascript_tool` eval) may never visually complete — `scrollTop` can sit frozen indefinitely with no error, while the identical call with `behavior: 'instant'` or a correctly-`ref`-targeted real click works immediately. Don't conclude a smooth-scroll feature is broken from a frozen screenshot/`scrollTop` alone; verify the underlying logic (state transitions, event firing) via `console.log` or discrete DOM state instead, and cross-check against an already-shipped feature using the identical scroll pattern before treating it as a real bug.

## Data entry

Filling in real facts (`shared/data/people.json`, `timeline/data/travel.json`) is its own recurring loop, separate from *The loop* above — it doesn't change what the site does, only what's true. It's also where integrity is easiest to lose: `scripts/build_site.py`'s validation only checks that each record is internally well-formed (every reference points at something real) — it has no notion of whether a change still makes sense next to what everyone else's entry says. That's always a human judgment call, and it's easy to make it correctly for the person actively being edited while forgetting someone else's entry that the same change quietly affects (e.g. adding a new person into a room without also moving the people already in it — both entries stay independently valid, so nothing about the build would ever flag it).

For any change to `people.json` or `travel.json`:

1. **Name who else it touches** — not just the person being edited. Anyone sharing a room/structure on an overlapping date (`room`/`room_by_date`), anyone named in a `driver_id`, and any sibling/parent/partner relationship the change affects (a new person, a `birth_order` need).
2. **Name the affected date range** — every day quarter the change spans (arrival through departure, or just the specific dates touched), not only the date of the literal edit.
3. **Rebuild** (`scripts/build_site.py`) — a clean exit only proves the data is well-formed, not that it's *correct*.
4. **Run `scripts/report.py`** and read the printed transitions — it prints only the day quarters where an arrival, a departure, or a room/structure assignment actually changes, so a forgotten update on someone else's entry usually shows up as a lopsided or missing name right at the transition point. See the script's own `-h`/docstring for exactly what it does and doesn't check.
5. **Open the built pages for everyone named in step 1** — their own Attendees page, plus the Timeline quarter screens spanning the affected range — not just the page for the person you edited. This is also the only way to catch a rendering-level bug that's invisible in the raw JSON (e.g. sibling display order, or a milestone gap that silently didn't appear).
6. Only then commit — see *Git* below.

## Data model changes

Changing the *shape* of a data file — a new field, a renamed/removed one, a new allowed value, a whole new file — is a different kind of change from *Data entry* above, which only fills in facts within a shape that's already fixed. It's rarer, but it's also the one most likely to leave a script silently out of sync with what another script now expects, so it gets its own procedure:

1. **Update the schema doc first.** The relevant file's own `Data` subsection in `requirements/public.md` is the source of truth for its shape — write the change there before touching any script, so the new shape is fully specified before code follows it.
2. **Find every consumer.** Grep the field/file name across every feature's `build.py`, plus `shared/nav.py`, `shared/trip.py`, and `scripts/report.py`. `00-index.md`'s doc table (which script reads which file) is the starting checklist — a field four scripts read is four places to check, not one.
3. **Add or adjust validation** in the file's owning build script (the one already responsible for it — e.g. `timeline/scripts/build.py` owns `travel.json`/`structures.json`/`vehicles.json`). Fail loudly: a friendly message naming the record and field, never a raw `KeyError` — match the style every existing validator already uses (`shared/nav.py` → `require()`, each script's own `record_label()`).
4. **Update every consumer's rendering logic**, not just the one that motivated the change. A shared field going stale in a script nobody thought to touch is the same trap *Data entry* above warns about for data (two entries staying independently valid while quietly disagreeing) — just applied to code instead of data.
5. **Backfill existing records.** Decide and apply a default/migration so the file stays internally consistent — an optional field can lean on `.get()` with a sensible fallback, but a newly *required* field needs every existing record updated in the same commit, not left to fail the next build.
6. **Update `00-index.md`'s one-line description** of the file/script if the change alters what it's responsible for.
7. **Rebuild and review every affected page** (`scripts/build_site.py`). A clean exit only proves the new shape is well-formed — same limitation *Data entry* calls out for `scripts/report.py` — not that every consumer actually renders it correctly.
8. **Commit it all together** — schema doc, validation, every consumer update, and any backfilled data, in one commit. A data-model change is a code change, not a data-entry edit, so it doesn't follow *Data entry*'s separate one-person-at-a-time rhythm.

A **new data file** (not just a new field on an existing one) needs one more thing beyond the above: its own row in `00-index.md`'s doc table, and an entry in `technical.md`'s Scripts table naming what validates it.

## Git

- Commit before editing a data file by hand. `build.py` writes directly to the HTML pages; a clean working tree is your only rollback if something goes wrong.
- Normal commit rhythm: one commit per session, or one per batch of plan changes. Push to `main` when you want the live site to update — the GitHub Actions workflow deploys automatically (see `technical.md` → *Repo & deployment*).

## Local & session state

Nothing this project needs should live *only* outside version control. Two specific cases:

**Setup dependencies** — if a workflow step needs specific local machine setup to work, that dependency must be named somewhere in this repo, not just assumed or discovered by hitting an error. Currently just one: git authentication for pushing to the repo — see `operations.md` → *Push access* for the required account and how to check/switch it, once that's filled in.

**Ephemeral working artifacts** — AI tooling creates files outside this repo while working (plan-mode plan files, scratch/temp directories used to clone or inspect something, etc.). These are disposable by design: fine to use mid-session, expected to be discardable by the end of it. Anything that needs to survive past the session — a decision, a checklist, a doc update — must be written into this repo (typically `workbench/<milestone-name>.md` for in-flight plans, or the relevant root doc for a settled decision) before the session ends. Never leave a durable outcome resting only in a tool-managed file the project doesn't own.

See `technical.md` → *Architecture boundary* for the related rule about this repo not depending on anything outside itself.

## Milestones

Work that spans multiple sessions (a rebrand, an infra migration, anything bigger than one loop of *The loop* above) is tracked as a checklist in `workbench/<milestone-name>.md`. Check items off as they land. When the milestone is done, delete the file — git history keeps the record, and the outcome belongs in the commit message, not a changelog doc.
