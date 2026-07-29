# Working on this project

Start at [00-index.md](00-index.md) — the map of every doc in this project and what each one is responsible for.

[way-of-working.md](way-of-working.md) is the one to read first: it's the human+AI operating process — the requirements-doc-driven loop, git rhythm, and the milestone-tracking convention (`workbench/`). [technical.md](technical.md) is the architecture reference alongside it: the two-repo structure, every script's job, the build pipeline, and where CSS/JS changes go. Anything durable learned while working on this project — a gotcha, a rule, a correction — belongs in a doc in this repo (this file, `way-of-working.md`, `technical.md`, or the relevant feature doc), not in AI-tool-side memory outside the repo.

**If `GETTING-STARTED.md` still exists at the repo root, this project hasn't been customized from the template yet.** Read that file first and work through it before treating any other doc's content as real project content — `example/`, `site/`, `admin/`, and every requirements doc currently describe a placeholder feature, not a real one.

**Before editing a feature's shared CSS/JS files, or previewing anything under `site/`/`admin/`, read `technical.md` → *Shape of the system* and *Where CSS and JS changes go*.** Every page under `site/` and `admin/` is a build artifact with shared CSS/JS inlined at build time — nothing there links to the source files at runtime. Editing a source file has zero visible effect until the feature's `build.py` is run; verifying against a stale `site/` page will look identical to no change at all having been made.
