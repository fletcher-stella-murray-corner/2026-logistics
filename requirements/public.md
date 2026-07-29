# Requirements — Public Site

What the public-facing site (`site/`) should be/do. There is no admin site for this project — the sole editor hand-edits data files directly and reruns the build (see `technical.md` → *Repo & deployment*).

Two features: **Timeline** (the homepage) and **Family Tree**.

## Device support

Both features must work well on a computer and on a phone — this is critical, not a nice-to-have, since most family will be checking the Timeline from a phone while traveling. Prefer native browser behavior (CSS scroll-snap, normal scrolling) over custom JS gesture handling, since native scrolling already works correctly on both.

## Homepage = Timeline (`site/index.html`)

### Layout

Nav bar (`Timeline` active, `Family Tree` link) stays fixed/sticky at the top at all times, so Family Tree is always one tap away no matter where you've scrolled to. Directly below the nav, a sticky "Jump to a day ▾" disclosure lists every remaining day, each with its four block times as links — clicking one jumps straight there via anchor and closes the disclosure, independent of scroll-snap. This is the reliable way to reach any block; don't assume scroll/swipe alone is enough.

Below that, a full-screen, swipe/scroll-through experience: an intro screen with the trip title, then one full-viewport-height screen per 6-hour block, in order, using CSS scroll-snap on `html` (not `body` — `html`/`documentElement` is the actual scrolling element for the page, so scroll-snap-type must be set there or it silently does nothing) — scrolling or swiping down moves from one block straight to the next, each one filling the whole screen. `scroll-snap-stop: always` makes one scroll/swipe gesture advance exactly one block at a time — a fast fling never skips past several blocks unnoticed. `scroll-behavior: smooth` is deliberately NOT used together with scroll-snap here — that combination is a known Safari/iOS bug that can break snapping entirely. This applies the same way on desktop (mouse wheel / trackpad) and mobile (swipe), since it's native browser scroll-snap, not a custom gesture handler. The homepage has no separate content of its own — the timeline IS the homepage, since that's the entire point of the site.

The Family Tree page does *not* use this full-screen snap layout — it's a short reference page, read top-to-bottom normally.

### Trip window

August 1–15, 2026, inclusive. Each day is split into four fixed six-hour blocks, always in this order:

| Block key | Label |
|-----------|-------|
| `00-06` | 12am–6am |
| `06-12` | 6am–12pm |
| `12-18` | 12pm–6pm |
| `18-24` | 6pm–12am |

### Auto-hiding past days

The build always starts rendering from `max(today, August 1)` through August 15 — days before that are never rendered. This is computed from the system date at build time, not a value the editor sets by hand: rerunning the build on a later date automatically drops days that have passed. If today is after August 15, the page shows a plain "trip's over" message instead of an empty page.

### What each block shows

Every block always renders the same four rows, in this order, each showing nothing if it has no content for that block:

1. **Arrivals** — people whose arrival falls in this exact day+block: name, mode (✈️ plane / 🚆 train / 🚗 car), free-text detail (flight/train number, who's driving, etc).
2. **Departures** — same shape, for people leaving in this day+block.
3. **Sleeping** — everyone present at the cottage during this block (arrived by this block, not yet departed), grouped by room/house. Computed from each person's arrival/departure, not entered separately — updating someone's travel dates automatically updates every block's sleeping list.
4. **Meal** — a free-text note for this block, if one exists (e.g. "Lobster boil — Dave grilling"). Not every block has one; most likely only `06-12` (breakfast), `12-18` (lunch), and `18-24` (dinner) will ever be filled in, but all four blocks support it.

A block with nothing in all four rows still renders as its own full-screen slide — never collapsed or skipped — so scrolling always advances one block at a time and the four-part shape stays consistent (see `brand-guidelines.md` → *Signature visual conventions*).

### Data

Two data files, both hand-edited directly (no data-entry scripts):

**`shared/data/people.json`** — shared with the Family Tree feature. Flat array:

```json
[
  {
    "id": 1,
    "name": "Full Name",
    "generation": 1,
    "parent_ids": [],
    "partner_id": null
  }
]
```

- `id` — integer, unique, stable. Never reuse or renumber an existing id.
- `name` — display name.
- `generation` — integer, 1 = the eldest generation appearing in the tree, increasing by 1 per generation down. Used only by the Family Tree page.
- `parent_ids` — list of 0–2 ids, this person's parent(s). Used only by the Family Tree page.
- `partner_id` — id of this person's spouse/partner, or `null`. Used only by the Family Tree page.

**`timeline/data/travel.json`** — one entry per person who has travel and/or a room assignment:

```json
[
  {
    "person_id": 1,
    "arrival": { "date": "2026-08-02", "block": "12-18", "mode": "plane", "detail": "AC 619 into YQM, 3:10pm" },
    "departure": { "date": "2026-08-09", "block": "06-12", "mode": "car", "detail": "Driving back with the Smiths" },
    "room": "Main House — Room 2"
  }
]
```

- `person_id` — must match an id in `people.json`.
- `arrival` / `departure` — both optional. Omit `arrival` if the person is already at the cottage before August 1 (they'll show as present from day one, with no arrival row ever rendered). Omit `departure` if they're staying past August 15.
- `mode` — one of `"plane"`, `"train"`, `"car"`.
- `detail` — free text, shown as-is.
- `room` — free text, used to group the Sleeping row. People with the same `room` string are grouped together.

**`timeline/data/meals.json`** — keyed by date, then block, only for blocks that have a note:

```json
{
  "2026-08-02": {
    "12-18": "Arrival lunch — sandwiches on the dock",
    "18-24": "BBQ, Dave grilling"
  }
}
```

### Empty state

If `travel.json` is empty and no meals are set, the timeline still renders every day/block as empty cards — never an error, never a blank page.

## Family Tree (`site/family-tree/index.html`)

### Layout

Same nav bar (`Timeline` link, `Family Tree` active). Below it, people grouped by `generation` (from `shared/data/people.json`), lowest number first. Within a generation, partners (`partner_id`) are shown paired together; each person/couple's children (people whose `parent_ids` includes them) are shown nested/indented below.

### Purpose

Purely reference — so someone new to the family (a partner, a young cousin) can see where they fit. No editing UI, no interactivity beyond the page itself.

### Data

Backed entirely by `shared/data/people.json` — see *Homepage = Timeline* → *Data* above for the file structure. No separate data file for this feature.

## Favicon

None for this trip — not worth the setup for a two-week single-use site.
