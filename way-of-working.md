# Way of Working

A tiny project: a requirements doc + an implementation. Keep it that way. This doc is about how we (human + AI) work together — the requirements-doc loop, git rhythm, session/state hygiene. For how the system is actually built (single-repo structure, scripts, the build pipeline, where CSS/JS changes go), see `technical.md`.

One requirements doc — see `00-index.md` for the full doc map:
- [requirements/public.md](requirements/public.md) — the public site (`site/`): the Timeline (homepage), Family Tree, and Attendees features. There is no admin site for this project; the sole editor hand-edits data files directly (see `00-index.md` → *Editing data*).

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
