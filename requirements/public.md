# Requirements — Public Site

What the public-facing site (`site/`) should be/do. There is no admin site for this project — the sole editor hand-edits data files directly and reruns the build (see `technical.md` → *Repo & deployment*).

Three features: **Timeline** (the homepage), **Family Tree**, and **Attendees**. Attendees has no index page and no nav link of its own — it's reached through the Family Tree (click an attending person) or through the Timeline's "Folks ▾" disclosure (see *Navigation* below).

## Terminology

Each day is split into four fixed six-hour segments, officially called **day quarters** (`00-06`, `06-12`, `12-18`, `18-24`). The full-viewport-height slide that shows one day quarter is officially called a **quarter screen**, made of two distinct parts:

- **Day quarter canvas padding** — a blank spacer at the top of the quarter screen, sized to clear the sticky nav/jump bars. It holds no content and is a separate element from the canvas, not extra padding on it.
- **Day quarter canvas** — the actual content: the five arrivals/departures/sleeping/meal/activities rows. No date or time label here — that lives in the nav bar (see *Navigation*). This is the only part that counts as "the canvas" — the padding is explicitly *not* part of it.

Use these terms consistently in code, comments, and docs — not "block"/"block screen", and not "the canvas" to mean the whole quarter screen including its padding.

## Navigation

**Timeline page** — nav bar is a single sticky row, always visible, six items left to right:

1. **"Murray Corner 2026"** — a permanent, unchanging link back to the very top of the page (the intro screen). Unlike every other item in this nav, its content never changes as you scroll — it's the one fixed point in the row. On the Family Tree and Attendees pages this same label/link is how you get back to the Timeline (see below).
2. **Current day quarter label, doubling as jump-to-time** — live text showing which day quarter is currently in view, updated as you scroll (via `IntersectionObserver` in `timeline/shared.js`), in two parts, in this order: the bare month/day (e.g. "Aug 3"), shown smaller and in the secondary color as supporting detail; then the weekday name in full plus the bare quarter name, joined by " - " (e.g. "- Monday Morning"), shown large/bold/prominent since that's what you actually scan for while scrolling — no time-range suffix here (unlike the jump-to-time dropdown's own link text, e.g. "Morning · 6am–12pm", which keeps it) — plus a small "▾" indicating it's also a disclosure trigger. Empty (no text) before you've scrolled into any quarter screen, and is the only place this date/time information appears (see *Terminology* — it's deliberately not repeated on the canvas). Clicking/tapping the label itself — not a separate "Jump ▾" control next to it — expands a dropdown disclosure listing every day, each with its full set of day-quarter times as links. Clicking one does a smooth animated scroll to that quarter screen (`scrollIntoView({behavior: 'smooth'})` in `timeline/shared.js`, not the CSS `scroll-behavior` property — see that file for why) and closes the disclosure. This is the reliable way to reach any quarter screen; don't assume scroll/swipe alone is enough.
3. **"Now"** — jumps straight to whichever quarter screen is current *at the cottage* (Murray Corner, New Brunswick — Atlantic Time), computed fresh in the visitor's browser at the moment they click, not baked in at build time (see *Always the full trip, "now" computed live* below). Deliberately the cottage's own clock, not the visitor's device timezone — someone checking from home before they've travelled needs "who else is landing around now" answered for Murray Corner, not for wherever they happen to be. If "now" is past August 15, this lands on the trip's very last quarter screen instead.
4. **"▶" play/pause toggle** — an icon-only button (no text label, `aria-label` of "Play"/"Pause" for accessibility) that steps through every screen one at a time: jump to the next screen, pause so there's time to actually read it, jump to the next, pause — not a continuous scroll. The pause length is a single named constant (`PAUSE_MS` in `timeline/shared.js`, currently 1.8 seconds) meant to be retuned freely for a natural rhythm, not a fixed spec value. Mainly a testing/demo aid for checking the full sequence renders correctly, but it's a permanent, visible control, not hidden. Always starts from wherever you currently are, not the very first screen — clicking it partway through the trip continues forward from there. While running, native scroll-snap is suspended for the page — repeatedly firing a smooth jump at every screen while mandatory snap stays active is a known bad combination that can leave the page visibly stuck (see `timeline/shared.css`) — and the icon switches to "⏸"; clicking it again, or scrolling/swiping manually, stops the advance immediately (manual scroll always wins), restores snap, and reverts the icon to "▶". It also stops itself automatically on reaching the last screen. This is an intentional, scoped exception to `brand-guidelines.md`'s "no interactivity beyond scrolling and links" principle — see that doc's *Core Principles*.
5. **Tree** — a working link to the Family Tree page. No "Attendees" nav item — that feature has no index/home page to link to (see *Attendees* below).
6. **"Folks ▾"** — jump to a *person*, furthest right: a dropdown disclosure listing everyone who has a `timeline/data/travel.json` entry, alphabetically by name (people with no travel entry aren't on the trip, so aren't listed). Each entry shows the person's **name** as plain text, followed by two labeled links: **"Timeline"** scrolls to the quarter screen where they first appear (their arrival's day+quarter, or the very first quarter screen of the trip if they have no `arrival` at all) with the same click/scroll/close behavior as the current day quarter label's jump-to-time disclosure above; **"Detail"** instead goes straight to that person's own Attendees page (`site/attendees/<id>.html` — see *Attendees* below), leaving the Timeline entirely. Omitted entirely if `travel.json` is empty.

On a narrow phone width, all six items still fit on one line — the live label (item 2) is the one that shrinks/truncates first (down to a minimum width that always shows at least a sliver of text), and every item's own font shrinks slightly, before anything would overflow or disappear entirely.

**Family Tree page** — nav bar is the plain two-item row (`Murray Corner 2026` link, `Tree` active/current-page indicator). It does not have the live label, "Now", jump-to-person, or Run — those are Timeline-only, since only the Timeline has quarter screens to label, jump between, jump to "now" within, or auto-advance through.

**Attendees pages** — nav bar is also a plain two-item row (`Murray Corner 2026` link, `Tree` link), same shape as Family Tree's minus the active indicator (a person page isn't "the" Family Tree page, so `Tree` is just a normal link back) — see *Attendees* → *Layout* below.

All navs are one sticky row, always visible, at the top of every page — you're never more than a tap away from any other page or, on the Timeline, from any quarter screen or any person.

## Device support

Both features must work well on a computer and on a phone — this is critical, not a nice-to-have, since most family will be checking the Timeline from a phone while traveling. Prefer native browser behavior (CSS scroll-snap, normal scrolling) over custom JS gesture handling, since native scrolling already works correctly on both.

## Structures

The site tracks a fixed list of named physical locations relevant to the trip — where people sleep, and the airports/station travel routes through — so they're referred to consistently everywhere instead of ad-hoc free text.

**`shared/data/structures.json`** — flat array, shared by both features (currently only the Timeline reads it). Validated at build time: an unknown name elsewhere in the data is a build error, not a silently-ignored typo.

```json
[
  { "id": "cottage", "name": "Cottage", "category": "accommodation", "rooms": ["Blue Room", "Green Room", "Master Suite"] },
  { "id": "red-shed", "name": "Red Shed", "category": "accommodation", "always_shown": true },
  { "id": "sheogue-inn", "name": "Sheogue Inn", "category": "accommodation" },
  { "id": "camper-van", "name": "Camper Van", "category": "accommodation" },
  { "id": "tent", "name": "Tent", "category": "accommodation", "instances": ["Rachel's camping tent", "old worn out tent"] },
  { "id": "halifax-airport", "name": "Halifax Airport", "category": "transit" },
  { "id": "moncton-airport", "name": "Moncton Airport", "category": "transit" },
  { "id": "sackville-station", "name": "Sackville Station", "category": "transit" }
]
```

- `id` — stable slug, never reused or renumbered. A duplicate is a build error.
- `name` — canonical display name; must be referenced exactly by other data (see below).
- `category` — `"accommodation"` (referenced by `travel.json`'s `room`/`room_by_date`/`working_from` fields, grouped in the Timeline's Structures row) or `"transit"` (referenced by `travel.json`'s `hub` field — see *Homepage = Timeline* → *Data* below). Any other value is a build error.
- `rooms` — optional list of fixed room names within an accommodation structure (e.g. Cottage's `["Blue Room", "Green Room", "Master Suite"]`). If present, must be non-empty with no duplicates — a build error otherwise. A structure with `rooms` declared is a real, permanent physical place: it and every one of its named rooms always render in the Structures row (empty or not) for as long as the structure is active (see `active_from`/`active_to` below), never only when someone happens to be assigned there — see *Homepage = Timeline* → *Structures* → *Nested box display*. Mutually exclusive with `instances` below (a build error if a structure sets both) — most structures need neither, see *Accommodation — single vs. multi-instance* below.
- `instances` — optional list of valid free-text instance names within an accommodation structure that has many real, individually-named instances but no fixed physical rooms (e.g. Tent's `["Rachel's camping tent", "old worn out tent"]`, one per actual tent people bring). If present, must be non-empty with no duplicates — a build error otherwise. Unlike `rooms`, a structure with `instances` does *not* always render — each named instance only shows up in the Structures row when someone's actually assigned to it, same occupancy-driven behavior as no list at all. The only thing `instances` adds is validation: a `room` value referencing this structure must match one of the declared instance names exactly (a build error otherwise, e.g. a typo'd `"Tent — Rachels camping tent"` no longer silently creates a second, unlabeled tent) instead of being arbitrary free text. Mutually exclusive with `rooms`.
- `always_shown` — optional boolean, defaults to `false`. The same "always render this structure's box every quarter, even empty" behavior a `rooms` list grants, but for a structure with no fixed sub-rooms to declare (e.g. Red Shed — a real place people are actively at, sleeping or working, but not one with named rooms like Cottage). Independent of `rooms`/`instances`: a structure can set `always_shown` alone (bare outer box, no nested room boxes, occupants listed directly — same display a bare structure-name room value gets today), or combine it with `instances` (outer box always shows; individual instances still only appear nested when actually occupied). Setting it alongside `rooms` is harmless but redundant, since `rooms` already implies it.
- `active_from` / `active_to` — optional ISO dates (inclusive), independently settable. Default to the start/end of the trip window when omitted, so a structure with neither set is active the whole trip (August 1–15) — the common case today. Meant for a structure that only exists for part of the trip (an inn booked for a specific stretch, in the requirements author's own words: "airports will come and go, inns will exist for like a period") — no current structure narrows this yet, but the fields are validated (ISO date shape, `active_to` not before `active_from`) and ready to use. Only affects the "always shown" behavior of a structure with `rooms` or `always_shown` set — doesn't (yet) restrict which dates a `hub`/`vehicle`/free-text `room`/`working_from` reference is allowed on.

**Accommodation — single vs. multi-instance:** Sheogue Inn is used as-is, with no fixed rooms declared, occupancy-shown only. Red Shed is also used as-is with no fixed rooms, but is marked `always_shown` (see above) since it's in near-constant use — both for sleeping and for `working_from` (see *Homepage = Timeline* → *Data* below). Camper Van and Tent cover multiple actual instances (different families bring their own) — write the specific instance as `"<structure name> — detail"`, e.g. `"Camper Van — Smiths"` or `"Tent — Rachel's camping tent"`. A `room` value is valid if it exactly matches an accommodation structure's `name`, or starts with `"<name> — "` followed by free text — *unless* that structure has a `rooms` or `instances` list declared, in which case the text after `" — "` must exactly match one of the declared names (`"Cottage — Blue Room"` is valid, `"Cottage — Anything Else"` is a build error; likewise `"Tent — old worn out tent"` is valid, `"Tent — some other tent"` is a build error until it's added to Tent's `instances` list) rather than being arbitrary free text. A structure without `rooms` or `always_shown` set only ever shows up in the Structures row when someone's actually assigned there (sleeping or working); no permanent box for Sheogue Inn, or for a declared-but-currently-empty tent instance, just because it exists.

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

### Time-of-day background

The whole screen — not just the quarter canvas — carries a background tint signaling its day quarter at a glance while scrolling: a second, ambient, full-bleed cue alongside the nav bar's live text label, not a replacement for it. This covers the full browser viewport edge to edge, including the flanking margins outside the centered content column on a wide screen, and the sticky nav bar itself, which switches to match whichever quarter screen is actually in view as you scroll (the same live-tracking behind the nav's day/quarter label) — a single strip of unchanged color anywhere on screen would break the effect.

| Quarter key | Feel | Color |
|-----------|------|-------|
| `00-06` Night | Dark | Dark navy (a darkened tide blue) |
| `06-12` Morning | Cool/fresh | Pale sky blue |
| `12-18` Afternoon | Sunny | Driftwood sand (the existing `--accent`) |
| `18-24` Evening | Sunset | Warm peach/terracotta |

Each quarter screen holds its own color flat for most of its height, but blends smoothly in from the *previous* quarter's color over the first fifth of its height, rather than cutting hard at the section boundary — see `brand-guidelines.md` → *Materials/Design Language*, which is where this is a deliberate exception, not decoration for its own sake: the quarters cycle in a fixed order, so "the previous quarter's color" is always known ahead of time, needing no extra per-day data. The nav bar's own background continuously matches the exact color the canvas shows right at the nav's bottom edge (recomputed on scroll, not a fixed-threshold swap — see `timeline/shared.js`), so the two never visibly disagree. The structure/room boxes (see *Structures* → *Nested box display* below) keep their own always-white/paper background and always-dark text regardless of quarter — only the surrounding canvas and nav bar signal time of day, so a name inside a box is never harder to read on one quarter than another.

Text on top of all this — the canvas's own row labels and the nav bar's live label/actions alike — uses exactly one of two colors, chosen for genuinely best contrast rather than one blanket color regardless of background: Mist (near-white) on Night, the one dark background; Primary (deep tide blue) on Morning/Afternoon/Evening, all light backgrounds — see `brand-guidelines.md` → *Colours*. Nothing distinguishes one nav item's role from another's by color; that's weight and size only, so the whole row always reads as one coherent, evenly-lit system rather than each item's color being whatever felt closest when it was added.

Anything that isn't a specific day/quarter — the Timeline's own intro screen (before you've scrolled into a day), the Family Tree page, and the Attendees pages — shares one background instead: Grove, a soft sage green (see `brand-guidelines.md` → *Colours*). A fifth "place" in the palette alongside the four day-quarter colors, not a plain white default; Primary/Text stay the same dark, high-contrast text used on the other light backgrounds.

### Trip window

August 1–15, 2026, inclusive. Each day is split into four day quarters, always in this order:

| Quarter key | Label |
|-----------|-------|
| `00-06` | Night · 12am–6am |
| `06-12` | Morning · 6am–12pm |
| `12-18` | Afternoon · 12pm–6pm |
| `18-24` | Evening · 6pm–12am |

### Always the full trip, "now" computed live

Every quarter screen for every day, August 1–15, is always rendered — nothing is ever hidden or omitted from the page based on the date, and the build's output doesn't depend on when it happens to run (see `technical.md` → *Scripts*). "Which quarter is it right now" is instead a client-side question, answered fresh by `timeline/shared.js` every time the page loads — read in the trip's own timezone (Atlantic Time, Murray Corner, New Brunswick), not the visitor's own device timezone, so the answer is always "what's happening at the cottage right now," the same question for everyone regardless of where they're checking from — see *Navigation* → "Now" above. Two things happen with this:

- On first load, if the URL doesn't already point at a specific quarter screen (no `#qc-...` hash — e.g. someone shared a link to a particular moment), the page instantly (no scroll animation) lands on the visitor's own "now", clamped to the trip's last quarter screen if "now" is already past August 15. Scrolling down from there moves forward through the rest of the trip; scrolling back up moves backward through it, all the way past August 1 to the intro screen — nothing before "now" is hidden.
- The "Now" nav button (see *Navigation* above) jumps to the same place at any time, recomputed fresh at the moment it's clicked.

Because the trip window itself (August 1–15) is fixed data, not something computed from the clock, the same built page stays correct for the whole two weeks with no rebuild or redeploy needed as the trip progresses.

### What each day quarter canvas shows

Content is pinned to the **top-left** of the canvas (not centered) — just the five rows below, in this order, each showing nothing if it has no content for that day quarter. No date or quarter-time label here — that's already shown live in the nav bar (see *Navigation* above), so repeating it on the canvas would be redundant.

#### Row applicability by quarter

This table is the source of truth for how the canvas structurally varies by quarter — as of the Structures row's *always-there structures* behavior (see below), all five rows are now eligible in all four quarters; each simply renders nothing (Arrivals/Departures/Meal/Activities) or just its always-there structures with no one in them (Structures) when there's no further data for that specific day+quarter (see each row's own description below).

| Row | `00-06` Night | `06-12` Morning | `12-18` Afternoon | `18-24` Evening |
|-----|:---:|:---:|:---:|:---:|
| Arrivals | eligible | eligible | eligible | eligible |
| Departures | eligible | eligible | eligible | eligible |
| Structures | eligible | eligible | eligible | eligible |
| Meal | eligible | eligible (breakfast) | eligible (lunch) | eligible (dinner) |
| Activities | eligible | eligible | eligible | eligible |

"Eligible" means the row renders if it has content for that day+quarter, and is omitted if it doesn't (per each row's rule below) — normal data-driven emptiness, not a quarter restriction. Structures was previously the one exception (never shown in `12-18`/Afternoon, since sleeping location didn't seem to matter mid-day) — that restriction is gone: a structure with fixed rooms or `always_shown` set (see *Structures* above) is a real physical place, unaffected by time of day, so it and its rooms now render in every quarter, whether or not anyone's actually associated with it right now.

#### Row-by-row rules

1. **Arrivals** — people whose arrival falls in this exact day+quarter: name, mode (✈️ plane / 🚆 train / 🚗 car), a more precise time estimate if one is set (see `time_range` in *Data* below — otherwise no time shown here, since the quarter itself is already the time context), hub (which airport/station, if set — see *Structures* above), vehicle (if set — see *Vehicles* above), free-text detail (flight/train number, who's driving, etc). Omitted if nobody arrives in this day+quarter.
2. **Departures** — same shape and same omit-if-empty rule, for people leaving in this day+quarter.
3. **Structures** — labeled "Structures", not "Sleeping": deliberately reframed away from an overnight-only concept to "who's associated with which structure right now, and why." A structure someone's sleeping at and a structure someone's working from for the day render in the same outer box, but stay visually distinct within it — anyone working from a structure this quarter always gets their own labeled "Working" sub-box (dashed border, same "different category" signal as `.unassigned-box` and the Family Tree's married-in boxes — see *Nested box display* below), never merged into the sleeping-side name list, so it's never ambiguous whether a name is there for the night or just for the day. Three things merged into one row: (a) everyone present on the trip during this quarter (arrived by this quarter, not yet departed), grouped by room/structure — computed from each person's arrival/departure, not entered separately, so updating someone's travel dates automatically updates every day quarter canvas's structure lists; (b) everyone with a `working_from` block covering this exact day+quarter (see *Data* below), shown in that structure's own "Working" sub-box — the same person can appear in two different structure boxes on the same quarter screen (their overnight structure, and wherever they're working from that day), since those are two independent facts, not one; and (c) every accommodation structure with a fixed `rooms` list or `always_shown: true` (see *Structures* above) that's currently active, shown regardless of whether anyone's in it. A person's room can change night to night (see `room_by_date` in *Data* below) — someone moving from the Cottage to the Red Shed partway through shows under the correct room on each affected night. The row itself is only omitted if there's truly nothing to show at all — no always-there structure exists yet *and* nobody's present or working (shouldn't happen once any structure has `rooms`/`always_shown` set, since that structure alone guarantees the row always has something).

   **Nested box display** — rendered as boxes, matching the same plain-box motif as the Family Tree page's person boxes (see *Family Tree* → *Layout* below), not a flat text list, so a room's structure is visible at a glance rather than read out of a string:
   - One outer box per **structure**, labeled with the structure's name — either because someone's actually associated with it this quarter (sleeping or working), or because it has a fixed `rooms` list or `always_shown: true` and is currently active (see *Structures* above), even with nobody in any of its rooms right now.
   - A structure with a fixed `rooms` list (only Cottage today) always shows an inner box for *every* declared room, in a fixed order, whether or not anyone's assigned to it this quarter — an empty room box just has no names inside it, it doesn't disappear.
   - A structure *without* a fixed `rooms` list only ever gets an inner box for a specific `"<name> — detail"` value if someone's actually sleeping there this quarter (e.g. Tent instances) — no permanent placeholder box, since there's no fixed list of what those could be.
   - If a person's `room` is a bare structure name with no `" — detail"` suffix (e.g. `"Sheogue Inn"`), there's nothing to nest — the people are listed directly inside that structure's outer box, no inner box. Everyone `working_from` a structure for the quarter instead gets a dedicated "Working" sub-box within that structure's outer box, styled like a room box but dashed — never merged into the plain sleeping-side name list, and never nested under a specific room, since `working_from` names a structure, not a room.
   - People with no `room` set at all are grouped into a single plain "Unassigned" box, not nested under any structure. This only applies to the sleeping side — `working_from` always names a structure, so there's no "unassigned" case for it.
   - No third level of box per person — inside the innermost box, people are listed as plain text (comma-separated), not individually boxed. This is a deliberate balance call for a ~27-person roster: two box levels (structure, then room/detail) show real structure without the row turning into boxes-within-boxes-within-boxes. Revisit if the real data makes this row hard to scan once filled in.
   - The structure/detail split for sleeping is parsed from the existing `room`/`room_by_date` string values (already validated against `structures.json` at build time, see *Structures* above); `working_from` blocks contribute directly, since they already name a structure with no string to parse; the always-there behavior comes entirely from `structures.json`'s own `rooms`/`always_shown`/`active_from`/`active_to` fields.
4. **Meal** — a free-text note for this quarter, if one exists (e.g. "Lobster boil — Dave grilling"). Omitted if no note is set for this day+quarter in `meals.json`; most likely only `06-12` (breakfast), `12-18` (lunch), and `18-24` (dinner) will ever be filled in, but all four quarters support it.
5. **Activities** — a free-text note for this quarter, if one exists (e.g. "Beach volleyball", "Bonfire at Red Shed"). Same shape and omit-if-empty rule as Meal.

A day quarter canvas with nothing in all five rows still renders inside its own full-screen quarter screen — never collapsed or skipped — so scrolling always advances one quarter screen at a time and the five-part shape stays consistent (see `brand-guidelines.md` → *Signature visual conventions*).

### Data

Several data files, all hand-edited directly (no data-entry scripts):

**`shared/data/people.json`** — shared with the Family Tree and Attendees features. Flat array:

```json
[
  {
    "id": 1,
    "name": "Full Name",
    "generation": 1,
    "parent_ids": [],
    "partner_id": null,
    "attending": true
  }
]
```

- `id` — required integer, unique, stable. Never reuse or renumber an existing id. Validated at build time: every person needs one, and a duplicate id is a build error.
- `name` — required, non-empty display name. When two or more people in the roster share the same first name, disambiguate by appending the first letter of their last name (e.g. `"Helen S"`, `"Jim S"`) — last names are otherwise never shown. If a first name is unique in the roster, use it alone with no letter. Applies as soon as a second person with that first name is added; go back and add the letter to the existing person's `name` at that point if it wasn't already disambiguated. Validated at build time: two people can't end up with the exact same `name` string — a build error, not a silent look-alike, since a forgotten disambiguation letter would otherwise make two people indistinguishable everywhere a bare name is shown (Family Tree, "Folks ▾", the Structures row).
- `generation` — required integer, 1 = the eldest generation appearing in the tree, increasing by 1 per generation down. Used only by the Family Tree page. Validated at build time: every person needs one, and — after the tree is built — every person must actually be reachable from a generation-1 root by walking `parent_ids`/`partner_id`; a generation number or `parent_ids` chain that doesn't connect back to a root is a build error rather than a person silently missing from the page.
- `parent_ids` — list of 0–2 ids, this person's parent(s). Used only by the Family Tree page. Validated at build time: at most 2 entries, every id must reference a real person, and nobody can be their own parent.
- `partner_id` — id of this person's spouse/partner, or `null`. Used only by the Family Tree page. Validated at build time: if set, must reference a real person, nobody can be their own partner, and the pairing must be reciprocal — if A's `partner_id` is B, B's `partner_id` must be A.
- `married_in` — optional boolean, defaults to `false`/omitted. `true` marks someone who joined the family by marriage/partnership rather than being a blood descendant (a person with no parents of their own in the tree, e.g. a partner who married a blood descendant). Used only by the Family Tree page, to render them with a visually distinct (dashed-border) box — see *Family Tree* → *Layout* below. Not meant for the founding generation (`generation` 1): they're the root of the tree, not "married in" to anything documented, so leave `married_in` unset even though their `parent_ids` is also empty. Validated at build time: a person can't have both `married_in: true` and a non-empty `parent_ids` — that's a contradiction (someone with documented parents is a blood descendant by definition).
- `attending` — required boolean, no default — a build error if missing or not `true`/`false` on any person. Used only by the Attendees feature (see *Attendees* below): everyone in the family tree is listed there, but only people with `attending: true` appear on the Attendees feature at all, get their own facts page, or get a `timeline/data/travel.json` entry. Validated at build time: `attending: false` combined with an existing `travel.json` entry for that person is a contradiction (a build error) — remove one or the other rather than leaving both in place.

**`timeline/data/travel.json`** — one entry per person who has travel and/or a room assignment:

```json
[
  {
    "person_id": 1,
    "arrival": { "date": "2026-08-02", "quarter": "12-18", "time_range": ["15:00", "15:30"], "mode": "plane", "hub": "Moncton Airport", "detail": "AC 619" },
    "departure": { "date": "2026-08-09", "quarter": "06-12", "mode": "car", "vehicle": "White Dodge Caravan", "detail": "Driving back with the Smiths" },
    "room": "Cottage — Room 2",
    "room_by_date": {
      "2026-08-05": "Red Shed",
      "2026-08-06": "Red Shed"
    },
    "working_from": [
      { "structure": "Red Shed", "start_date": "2026-08-03", "end_date": "2026-08-06" },
      { "structure": "Red Shed", "start_date": "2026-08-07", "end_date": "2026-08-07", "quarters": ["06-12"] }
    ]
  }
]
```

- `person_id` — must match an id in `people.json`. Validated at build time: an unknown id is a build error, not a silently-dropped entry.
- `pending` — optional boolean, defaults to `false`/omitted. `true` marks an entry as still tentative/in progress — the Timeline and this person's own Attendees facts page still render whatever's actually filled in (nothing is hidden), but the Family Tree box keeps showing this person under "Collecting facts" rather than "Facts collected" until it's cleared. Meant for a person whose arrival/departure/room is entered but not yet finalized (e.g. a vehicle marked "TBD" in `detail`) — set it while details are still firming up, then remove it (or set `false`) once they're locked in.
- `arrival` / `departure` — both optional. Omit `arrival` if the person is already at their accommodation before August 1 (they'll show as present from day one, with no arrival row ever rendered). Omit `departure` if they're staying past August 15. If both are set, departure can't be before arrival — validated at build time.
- `date` — an ISO date (`YYYY-MM-DD`), validated at build time; applies to `arrival`/`departure`/`room_by_date` keys everywhere in this file.
- `quarter` — one of the day quarter keys above (`00-06`, `06-12`, `12-18`, `18-24`), validated at build time. Always required on `arrival`/`departure` — the coarse 6-hour bucket a leg is shown/grouped under, independent of whether a finer `time_range` estimate is also set.
- `time_range` — optional `[start, end]` pair of 24-hour `"HH:MM"` times, a finer time estimate than the quarter alone — anywhere from an exact time (`start` equal to `end`, e.g. `["18:00", "18:00"]`) to a narrower window than the full 6-hour quarter (e.g. `["14:00", "16:00"]`). Validated at build time: both times must be valid 24-hour `HH:MM`, `start` not after `end`, and both must fall within the quarter's own window (an exact boundary time like `"18:00"` validates against either adjacent quarter). Omit entirely when only the quarter is known — the full quarter window is shown instead, today's behavior. Shown on both the Timeline (in the Arrivals/Departures rows, alongside hub/vehicle/detail) and the person's own Attendees facts page (replacing the generic quarter label, e.g. `"Aug 2 · 3–3:30pm"` instead of `"Aug 2 · Afternoon · 12pm–6pm"`) — the same field, not entered twice.
- `mode` — required on every `arrival`/`departure`; one of `"plane"`, `"train"`, `"car"`. Validated at build time — missing or any other value is a build error, not a silently-blank travel-mode icon.
- `hub` — optional; must exactly match a transit structure's `name` in `shared/data/structures.json` (see *Structures* above). Omit for car travel or when no specific hub applies.
- `vehicle` — optional; must exactly match a vehicle's `name` in `shared/data/vehicles.json` (see *Vehicles* above). Typically used with `"mode": "car"`.
- `driver_id` — optional; the `id` of another person in `shared/data/people.json` who's driving this leg (e.g. David driving Rachel to the airport for her departure). Validated at build time: must reference a real person, and can't be the traveler's own id (omit `driver_id` entirely when someone drives themselves — it's only for naming someone *else*). Shown on the Timeline and the traveler's own Attendees page as "<driver name> driving", appended to the leg the same way `detail` is — but unlike every other field on a leg, it's also shown on the *driver's own* Attendees page, as a separate "Driving: <traveler name>'s arrival/departure — …" row (see *Attendees* → *Layout* below) — the one piece of data on this page that isn't only ever visible to the traveler it's attached to.
- `detail` — free text, shown as-is.
- `room` — the person's default sleeping location for their whole stay; must be a valid accommodation reference per *Structures* above (an exact structure name, or `"<name> — detail"`). Used to group the Structures row. People with the same resolved room are grouped together.
- `room_by_date` — optional map of ISO date → room, same validation as `room`. Overrides `room` for the specific dates listed, for people who change structures mid-stay. Omit entirely if the person sleeps in the same place their whole visit.
- `working_from` — optional list of blocks, each `{ "structure": <name>, "start_date": <ISO date>, "end_date": <ISO date>, "quarters": [<quarter key>, ...] }`, for someone working from a structure during the day rather than (or in addition to) sleeping there — e.g. `{ "structure": "Red Shed", "start_date": "2026-08-03", "end_date": "2026-08-06" }`. Independent of `room`/`room_by_date`: a person can sleep in one structure and work from a completely different one on the same day, and both show up (see *Structures* row above). `structure` must exactly match a name in `shared/data/structures.json` (any category). `start_date`/`end_date` are inclusive, validated as ISO dates with `end_date` not before `start_date`. `quarters` is optional, defaulting to `["06-12", "12-18"]` (morning and afternoon) when omitted — the normal case, e.g. Rachel's Aug 3–6 block — and when given must be a non-empty subset of just those two keys; `00-06`/`18-24` are build errors, since working from a structure isn't a concept this site tracks overnight. A single-day exception within a longer stretch (e.g. Rachel working only the morning of Aug 7, the last day of an otherwise Aug 3–7 stretch) is just its own extra block with a narrower `quarters` list, not a special case — see David and Rachel's entries below for both a multi-block (non-consecutive date ranges) and a narrowed-quarters example.

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

Anyone with `married_in: true` is rendered with a dashed border in the secondary (sea glass) color, plus a small "Married in" caption under their name — both together, so it's clear at a glance who's a blood descendant and who joined the family by marriage/partnership even without recalling what the border style means on its own. Within the site's plain/no-icon visual language (`brand-guidelines.md`), no icons are used for this or the states below — only border style/color, a background tint, opacity, and a small caption.

Each person's box also reflects the same states the Attendees feature computes (see *Attendees* → *The two states* below — the Family Tree reads `timeline/data/travel.json` read-only, same as Attendees, purely to compute this; nothing is entered a second time):
- **Facts collected** (attending, has a `travel.json` entry that isn't marked `pending`) — the default box, no extra treatment. This is the expected/common case, so it's the one state that isn't decorated.
- **Collecting facts** (attending, no `travel.json` entry yet, or the entry is marked `"pending": true`) — a sand-tinted background (the accent color, whose documented use is exactly this: a background tint) plus a "Collecting facts" caption under the name.
- **Not attending** (`attending: false`) — the whole box rendered at reduced opacity (faded), plus a "Not attending" caption under the name.

A person who is both married-in and one of the non-default states shows both signals together (e.g. the dashed sea-glass border and "Married in" caption, plus a faded box and "Not attending" caption) — the two are independent facts about a person and aren't mutually exclusive.

An attending person's box (either non-default state above, or the plain default box) is also a working link straight to their own Attendees page (`site/attendees/<id>.html` — see *Attendees* below) — this is the sole entry point to that feature, which has no index page or nav link of its own. A not-attending person's box stays plain text, not a link, since they have no such page.

### Purpose

Purely reference — so someone new to the family (a partner, a young cousin) can see where they fit. No editing UI beyond the links to each attending person's own Attendees page.

### Data

Backed by `shared/data/people.json` — see *Homepage = Timeline* → *Data* above for the file structure — plus a read-only look at `timeline/data/travel.json` for the facts-collected/collecting-facts visual only (see *Layout* above). No separate data file of this feature's own.

## Attendees (`site/attendees/`)

No index page and no nav link of its own (see *Navigation* above) — reached two ways: clicking an attending person's box on the Family Tree, or the "Detail" link next to their name in the Timeline's "Folks ▾" disclosure. Organizers checking who's still owed a "what are your plans" conversation use the Family Tree's "Collecting facts" captions for that now (see *Family Tree* → *Layout* above), rather than a dedicated grouped list.

### Purpose

A per-person summary of someone's own travel/room facts — "what's the summary of my facts, so I can just see my facts as me" — pulled out of the day-by-day Timeline schedule into one place, so a family member can check their own arrival/departure/room without scrolling the whole trip to find themselves. Purely reference, same as the Family Tree — no editing UI, no interactivity beyond the pages themselves. There's no way to actually submit or correct your own facts from this page; that still happens by the sole editor hand-editing `timeline/data/travel.json` (see `way-of-working.md` → *The loop*) — this is a read-only view of that same edit, not a new place to make one.

This feature only covers attending people — anyone with `attending: false` has no page here at all (see the Family Tree for the full family, attending or not).

### Data integrity

This is the load-bearing rule for the whole feature: **a person's facts page shows exactly the same `arrival`/`departure`/`room`/`room_by_date` data already in their `timeline/data/travel.json` entry — nothing is entered a second time for this feature.** Updating someone's travel.json entry updates both the Timeline schedule and their facts page from the same rebuild, so the two can never silently disagree. The only new data this feature introduces is `attending` on `shared/data/people.json` (see *Homepage = Timeline* → *Data* above) — everything else is a different view of data that already exists.

### The two states

Every attending person in `shared/data/people.json` falls into exactly one of these, computed at build time, never hand-assigned as its own field (not-attending people are excluded entirely — see *Purpose* above). This is what the Family Tree's caption reflects for each attending person's box (see *Family Tree* → *Layout* above) — there's no grouped listing of it on this feature itself anymore:

1. **Collecting facts** — no `timeline/data/travel.json` entry yet, or the entry is marked `"pending": true` (see *Data* → `travel.json` → `pending` below, for partial/tentative data that isn't finalized yet). Gets a facts page — if there's no entry at all it just says their travel details aren't in yet; if there's a pending entry, the page shows whatever's actually been entered so far.
2. **Facts collected** — has a `travel.json` entry that isn't marked pending. Gets a facts page showing their arrival, departure, and room, formatted for reading rather than the Timeline's day-quarter-grouped shape.

### Layout

**`site/attendees/<id>.html`** (one per person with `attending: true`, `<id>` is their stable `shared/data/people.json` id, e.g. `site/attendees/7.html` for David) — nav bar per *Navigation* above (the plain two-item `Timeline`/`Tree` row, `Tree` being the way back to wherever you clicked through from). Below it, the person's name as a heading, then:
- If they have no `travel.json` entry and no `driver_id` assignments on anyone else's leg (see *Driving* below): a single line saying their travel details aren't in yet.
- Otherwise, a **single chronological timeline**, not a flat Arrival/Departure/Room breakdown and not one block per kind of fact either — every row below (Arrival, Sleeping, Working from, Departure, Driving) is collected first, then sorted together by date into one list, so a Driving obligation or a Working from stretch that falls between two Sleeping stretches reads in its actual place in the trip rather than trailing after a much-later Departure. A **ranged** fact (Sleeping, Working from) sorts by the *first* date of its range — the whole row still shows the full range, only its position in the list is decided by where it starts. When two rows land on the exact same date, ties keep a sensible default order: Arrival, then Sleeping, then Working from, then Departure, then Driving.
  - **Every row shares the same three-part shape** — a fixed-position **date** (bold, leading, e.g. "Aug 1 · 6pm" or "Aug 4–6 · mornings & afternoons"), a short **label** (e.g. "Arrival", "Sleeping"), then the **detail**, in that order every time — deliberately consistent across all five kinds of row, so the date never leads on one row and gets buried mid-string or in parentheses on another (the difference between kinds is only what shows up in the label and detail columns, described below).
  - **Arrival** — date column: the `time_range` if one is set (e.g. "3–3:30pm") otherwise the day quarter label (e.g. "Afternoon · 12pm–6pm"), alongside the date. Detail column: mode, hub/vehicle, free-text detail. If `arrival` is omitted: date column shows "Aug 1", detail column reads "Already at the accommodation" (sorts as if dated August 1).
  - **Sleeping** — date column: the milestone's date range, e.g. "Aug 1–3". Detail column: the room, e.g. "Cottage — Blue Room". One row per contiguous same-room date range, in date order. Computed by walking every date from arrival (or August 1 if omitted) through the last date they're actually present for (the day before departure, if departure's quarter is `00-06` — the very first quarter of that date, meaning they're gone before any of it — otherwise the departure date itself; or August 15 if departure is omitted) and collapsing consecutive same-room dates into one range — the same `room`/`room_by_date` resolution and the same presence rule the Timeline's Structures row uses, just grouped into ranges instead of listed per night, and re-split into a new milestone if the same room recurs non-consecutively (e.g. Cottage → Tent → Cottage again shows as three separate Sleeping rows, not two, since the two Cottage stretches aren't adjacent). This page keeps the "Sleeping" label even though the Timeline's equivalent row is called "Structures" — here it's specifically framed as this person's own overnight story, not a shared live view of every structure, so the more personal label still fits.
  - **Working from** — date column: the block's date range plus its quarters, e.g. "Aug 3–6 · mornings & afternoons" or "Aug 7 · mornings". Detail column: the structure, e.g. "Red Shed". One row per `working_from` block (see *Homepage = Timeline* → *Data* → `working_from` above), sorted by each block's own start date — not merged or re-split like the Sleeping milestones above, since a block is already exactly the range the editor intended.
  - **Departure** — same shape as Arrival. If `departure` is omitted: date column shows "Aug 15", detail column reads "Staying past this date" (sorts as if dated August 15).
  - **Driving** — date column: the leg's date and time estimate, same as Arrival/Departure. Detail column: `"<traveler's name>'s arrival/departure — <mode, hub/vehicle, detail>"`, e.g. "Rachel's departure — ✈️ Plane — Moncton Airport — 6am flight · Departing Cottage at 3am". One row for every OTHER person's leg where this person is set as that leg's `driver_id` (see *Homepage = Timeline* → *Data* → `driver_id` above), sorted by that leg's own date. The only row sourced from someone else's entry, not this page owner's own — see *Data* → `driver_id` above — and the only one that can appear even when this person has no `travel.json` entry of their own (a driving obligation doesn't depend on the driver's own travel status).

## Favicon

None for this trip — not worth the setup for a two-week single-use site.
