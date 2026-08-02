# Requirements — Public Site

What the public-facing site (`site/`) should be/do. There is no admin site for this project — the sole editor hand-edits data files directly and reruns the build (see `technical.md` → *Repo & deployment*).

Two features: **Timeline** (the homepage) and **Family Tree**.

## Terminology

Each day is split into four fixed six-hour segments, officially called **day quarters** (`00-06`, `06-12`, `12-18`, `18-24`). The full-viewport-height slide that shows one day quarter is officially called a **quarter screen**, made of two distinct parts:

- **Day quarter canvas padding** — a blank spacer at the top of the quarter screen, sized to clear the sticky nav/jump bars. It holds no content and is a separate element from the canvas, not extra padding on it.
- **Day quarter canvas** — the actual content: the five arrivals/departures/sleeping/meal/activities rows. No date or time label here — that lives in the nav bar (see *Navigation*). This is the only part that counts as "the canvas" — the padding is explicitly *not* part of it.

Use these terms consistently in code, comments, and docs — not "block"/"block screen", and not "the canvas" to mean the whole quarter screen including its padding.

## Navigation

**Timeline page** — nav bar is a single sticky row, always visible, three items left to right:

1. **Current day quarter label** — live text showing which day quarter is currently in view (e.g. "Sat, Aug 1 · 12am–6am"), updated as you scroll (via `IntersectionObserver` in `timeline/shared.js`). Shows the site title before you've scrolled into any quarter, and is the only place this date/time information appears (see *Terminology* — it's deliberately not repeated on the canvas).
2. **"Jump ▾"** — a dropdown disclosure listing every remaining day, each with its four day-quarter times as links. Clicking one does a smooth animated scroll to that quarter screen (`scrollIntoView({behavior: 'smooth'})` in `timeline/shared.js`, not the CSS `scroll-behavior` property — see that file for why) and closes the disclosure. This is the reliable way to reach any quarter screen; don't assume scroll/swipe alone is enough.
3. **Tree** — currently disabled (plain muted text, not a link, `cursor: not-allowed`). Will become a working link to the Family Tree page once that page is ready to be reached this way.

**Family Tree page** — nav bar is the plain two-item row (`Timeline` link, `Tree` active/current-page indicator). It does not have the live label or the jump menu — those are Timeline-only, since only the Timeline has quarter screens to label or jump between.

Both navs are one sticky row, always visible, at the top of every page — you're never more than a tap away from the other page (once Tree is enabled) or, on the Timeline, from any quarter screen.

## Device support

Both features must work well on a computer and on a phone — this is critical, not a nice-to-have, since most family will be checking the Timeline from a phone while traveling. Prefer native browser behavior (CSS scroll-snap, normal scrolling) over custom JS gesture handling, since native scrolling already works correctly on both.

## Structures

The site tracks a fixed list of named physical locations relevant to the trip — where people sleep, and the airports/station travel routes through — so they're referred to consistently everywhere instead of ad-hoc free text.

**`shared/data/structures.json`** — flat array, shared by both features (currently only the Timeline reads it). Validated at build time: an unknown name elsewhere in the data is a build error, not a silently-ignored typo.

```json
[
  { "id": "cottage", "name": "Cottage", "category": "accommodation" },
  { "id": "red-shed", "name": "Red Shed", "category": "accommodation" },
  { "id": "sheogue-inn", "name": "Sheogue Inn", "category": "accommodation" },
  { "id": "camper-van", "name": "Camper Van", "category": "accommodation" },
  { "id": "tent", "name": "Tent", "category": "accommodation" },
  { "id": "halifax-airport", "name": "Halifax Airport", "category": "transit" },
  { "id": "moncton-airport", "name": "Moncton Airport", "category": "transit" },
  { "id": "sackville-station", "name": "Sackville Station", "category": "transit" }
]
```

- `id` — stable slug, never reused or renumbered. A duplicate is a build error.
- `name` — canonical display name; must be referenced exactly by other data (see below).
- `category` — `"accommodation"` (referenced by `travel.json`'s `room`/`room_by_date` fields, grouped in the Timeline's Sleeping row) or `"transit"` (referenced by `travel.json`'s `hub` field — see *Homepage = Timeline* → *Data* below). Any other value is a build error.

**Accommodation — single vs. multi-instance:** Cottage, Red Shed, and Sheogue Inn are used as-is. Camper Van and Tent cover multiple actual instances (different families bring their own) — write the specific instance as `"<structure name> — detail"`, e.g. `"Camper Van — Smiths"` or `"Tent — Sarah & Jon"`. A `room` value is valid if it exactly matches an accommodation structure's `name`, or starts with `"<name> — "`. The same `"<name> — detail"` shape also covers specific named rooms within a structure, e.g. `"Cottage — Green Room"`, `"Cottage — Blue Room"`, `"Cottage — Master Suite"`, `"Red Shed — Futon"` — these aren't separate structures.json entries, just free text after the structure name.

**Transit hubs:** Halifax Airport, Moncton Airport, and Sackville Station are the three hubs travel routes through. `arrival`/`departure` each get an optional `hub` field that must exactly match a transit structure's `name` — flight/train numbers and other free text stay in the existing `detail` field.

## Vehicles

The site also tracks a fixed list of named vehicles used for car travel, for the same reason as *Structures* above — consistent naming instead of ad-hoc free text.

**`shared/data/vehicles.json`** — flat array, validated at build time:

```json
[
  { "id": "camry", "name": "White Toyota Camry" },
  { "id": "caravan", "name": "White Dodge Caravan" }
]
```

- `id` — stable slug, never reused or renumbered. A duplicate is a build error.
- `name` — canonical display name, must be referenced exactly.

`arrival`/`departure` each get an optional `vehicle` field that must exactly match a vehicle's `name` (see *Homepage = Timeline* → *Data* below) — typically used with `"mode": "car"`. Free text (who's driving, route, etc) stays in the existing `detail` field.

## Homepage = Timeline (`site/index.html`)

### Layout

Nav bar per *Navigation* above. Below it, a full-screen, swipe/scroll-through experience: an intro screen with the trip title, then one **quarter screen** per day quarter, in order, using CSS scroll-snap on `html` (not `body` — `html`/`documentElement` is the actual scrolling element for the page, so scroll-snap-type must be set there or it silently does nothing) — scrolling or swiping down moves from one quarter screen straight to the next, each one filling the whole screen. `scroll-snap-stop: always` makes one scroll/swipe gesture advance exactly one quarter screen at a time — a fast fling never skips past several unnoticed. `scroll-behavior: smooth` is deliberately NOT used together with scroll-snap here — that combination is a known Safari/iOS bug that can break snapping entirely. This applies the same way on desktop (mouse wheel / trackpad) and mobile (swipe), since it's native browser scroll-snap, not a custom gesture handler. The homepage has no separate content of its own — the timeline IS the homepage, since that's the entire point of the site.

Each quarter screen is made of the **day quarter canvas padding** (blank spacer, clears the nav bar) followed by the **day quarter canvas** (the actual content) — see *Terminology* above; these are separate elements, not one padded box.

The Family Tree page does *not* use this full-screen snap layout — see *Navigation* above for its nav, and *Family Tree* → *Layout* below for the rest of its page; it's read top-to-bottom normally as a short reference page.

### Trip window

August 1–15, 2026, inclusive. Each day is split into four day quarters, always in this order:

| Quarter key | Label |
|-----------|-------|
| `00-06` | Night · 12am–6am |
| `06-12` | Morning · 6am–12pm |
| `12-18` | Afternoon · 12pm–6pm |
| `18-24` | Evening · 6pm–12am |

### Auto-hiding past days

The build always starts rendering from `max(today, August 1)` through August 15 — days before that are never rendered. This is computed from the system date at build time, not a value the editor sets by hand: rerunning the build on a later date automatically drops days that have passed. If today is after August 15, the page shows a plain "trip's over" message instead of an empty page.

### What each day quarter canvas shows

Content is pinned to the **top-left** of the canvas (not centered) — just the five rows below, in this order, each showing nothing if it has no content for that day quarter. No date or quarter-time label here — that's already shown live in the nav bar (see *Navigation* above), so repeating it on the canvas would be redundant.

1. **Arrivals** — people whose arrival falls in this exact day+quarter: name, mode (✈️ plane / 🚆 train / 🚗 car), hub (which airport/station, if set — see *Structures* above), vehicle (if set — see *Vehicles* above), free-text detail (flight/train number, who's driving, etc).
2. **Departures** — same shape, for people leaving in this day+quarter.
3. **Sleeping** — everyone present on the trip during this quarter (arrived by this quarter, not yet departed), grouped by room/structure (see *Structures* above — not everyone is at the Cottage itself). Computed from each person's arrival/departure, not entered separately — updating someone's travel dates automatically updates every day quarter canvas's sleeping list. A person's room can change night to night (see `room_by_date` in *Data* below) — someone moving from the Cottage to the Red Shed partway through shows under the correct room on each affected night.
4. **Meal** — a free-text note for this quarter, if one exists (e.g. "Lobster boil — Dave grilling"). Not every quarter has one; most likely only `06-12` (breakfast), `12-18` (lunch), and `18-24` (dinner) will ever be filled in, but all four quarters support it.
5. **Activities** — a free-text note for this quarter, if one exists (e.g. "Beach volleyball", "Bonfire at Red Shed"). Same shape as Meal — not every quarter has one, all four quarters support it.

A day quarter canvas with nothing in all five rows still renders inside its own full-screen quarter screen — never collapsed or skipped — so scrolling always advances one quarter screen at a time and the five-part shape stays consistent (see `brand-guidelines.md` → *Signature visual conventions*).

### Data

Several data files, all hand-edited directly (no data-entry scripts):

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

- `id` — integer, unique, stable. Never reuse or renumber an existing id. Validated at build time: a duplicate id is a build error.
- `name` — display name.
- `generation` — integer, 1 = the eldest generation appearing in the tree, increasing by 1 per generation down. Used only by the Family Tree page.
- `parent_ids` — list of 0–2 ids, this person's parent(s). Used only by the Family Tree page. Validated at build time: every id must reference a real person, and nobody can be their own parent.
- `partner_id` — id of this person's spouse/partner, or `null`. Used only by the Family Tree page. Validated at build time: if set, must reference a real person, and nobody can be their own partner.

**`timeline/data/travel.json`** — one entry per person who has travel and/or a room assignment:

```json
[
  {
    "person_id": 1,
    "arrival": { "date": "2026-08-02", "quarter": "12-18", "mode": "plane", "hub": "Moncton Airport", "detail": "AC 619, 3:10pm" },
    "departure": { "date": "2026-08-09", "quarter": "06-12", "mode": "car", "vehicle": "White Dodge Caravan", "detail": "Driving back with the Smiths" },
    "room": "Cottage — Room 2",
    "room_by_date": {
      "2026-08-05": "Red Shed",
      "2026-08-06": "Red Shed"
    }
  }
]
```

- `person_id` — must match an id in `people.json`. Validated at build time: an unknown id is a build error, not a silently-dropped entry.
- `arrival` / `departure` — both optional. Omit `arrival` if the person is already at their accommodation before August 1 (they'll show as present from day one, with no arrival row ever rendered). Omit `departure` if they're staying past August 15. If both are set, departure can't be before arrival — validated at build time.
- `date` — an ISO date (`YYYY-MM-DD`), validated at build time; applies to `arrival`/`departure`/`room_by_date` keys everywhere in this file.
- `quarter` — one of the day quarter keys above (`00-06`, `06-12`, `12-18`, `18-24`), validated at build time.
- `mode` — one of `"plane"`, `"train"`, `"car"`.
- `hub` — optional; must exactly match a transit structure's `name` in `shared/data/structures.json` (see *Structures* above). Omit for car travel or when no specific hub applies.
- `vehicle` — optional; must exactly match a vehicle's `name` in `shared/data/vehicles.json` (see *Vehicles* above). Typically used with `"mode": "car"`.
- `detail` — free text, shown as-is.
- `room` — the person's default sleeping location for their whole stay; must be a valid accommodation reference per *Structures* above (an exact structure name, or `"<name> — detail"`). Used to group the Sleeping row. People with the same resolved room are grouped together.
- `room_by_date` — optional map of ISO date → room, same validation as `room`. Overrides `room` for the specific dates listed, for people who change structures mid-stay. Omit entirely if the person sleeps in the same place their whole visit.

**`timeline/data/meals.json`** — keyed by date, then day quarter key, only for quarters that have a note:

```json
{
  "2026-08-02": {
    "12-18": "Arrival lunch — sandwiches on the dock",
    "18-24": "BBQ, Dave grilling"
  }
}
```

**`timeline/data/activities.json`** — same shape as `meals.json`, keyed by date then day quarter key, only for quarters that have a note:

```json
{
  "2026-08-03": {
    "12-18": "Beach volleyball",
    "18-24": "Bonfire at Red Shed"
  }
}
```

### Empty state

If `travel.json` is empty and no meals or activities are set, the timeline still renders every day quarter canvas as an empty card — never an error, never a blank page.

## Family Tree (`site/family-tree/index.html`)

### Layout

Nav bar per *Navigation* above. Below it, people grouped by `generation` (from `shared/data/people.json`), lowest number first. Within a generation, partners (`partner_id`) are shown paired together; each person/couple's children (people whose `parent_ids` includes them) are shown nested/indented below.

### Purpose

Purely reference — so someone new to the family (a partner, a young cousin) can see where they fit. No editing UI, no interactivity beyond the page itself.

### Data

Backed entirely by `shared/data/people.json` — see *Homepage = Timeline* → *Data* above for the file structure. No separate data file for this feature.

## Favicon

None for this trip — not worth the setup for a two-week single-use site.
