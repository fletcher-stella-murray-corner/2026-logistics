# Murray Corner 2026

# Brand Guidelines

**Scope: this document applies to the public-facing website only** (`site/`). There is no separate admin site for this project.

---

# The Brand

A shared trip itinerary for one big family cottage gathering in Murray Corner, New Brunswick — who's arriving when, how, where they're sleeping, and what's for dinner, for 27 people converging over two weeks by plane, train, and car, many of them travelling a long way for a weekend that only comes around once a year.

Two things have to both be true at once, in this priority order:

1. **Easy to read and understand** — the information structure, the navigation, and the presentation all have to get someone to their own facts fast, with zero hunting. This is non-negotiable and comes first.
2. **A unique feel** — the site should read as *this* weekend's own thing, not a generic scheduling tool that could belong to any trip. It's the one weekend of the year everyone's traveled for; the site should feel like part of the occasion, not the spreadsheet you tolerate to find your gate time.

Neither is optional, and neither excuses the other — decoration that gets in the way of #1 doesn't belong, and clarity so bare it feels like a spreadsheet fails #2.

---

# The Story

Someone's at an airport gate, phone in hand, trying to answer one question: "is anyone else landing around when I do, and where am I sleeping tonight?" They pull up the site, scroll to today, and have the answer in five seconds. That's the bar every page is checked against — not "is this pretty," but "does this answer that question standing in a security line with one bar of signal."

---

# Audience

Family members of all ages (young kids to grandparents), most viewing on a phone, often on the move (airports, cars, trains) with unreliable connectivity. Not everyone is techy. The reaction to aim for: "oh good, I can just check this instead of texting the group chat."

---

# Personality

Clear first, memorable second — in that order, every time. Never corporate or spreadsheet-flat; never so decorated that finding your own arrival time takes longer than it should. A little coastal, warm, unfussy — but every trace of personality (the palette, the time-of-day atmosphere, the paper-itinerary feel) has to earn its place by making the site feel like *this* trip specifically, not by being decoration for its own sake.

---

# What Makes It Different

It's not a group chat and not a spreadsheet — it's a single always-current source of truth, computed live from whoever's actually looking at it, so the page always opens on "now" no matter when someone checks it, with zero rebuilds and zero stale info. And it doesn't look or feel like a scheduling tool: the day-quarter-by-day-quarter rhythm, the shifting time-of-day atmosphere, and the "torn from a paper itinerary at the cottage" feel are what make it read as Murray Corner's own thing rather than a generic itinerary app.

---

# Visual Identity

## Overall Feeling

A page torn from a simple paper travel itinerary someone left on the kitchen table at the cottage, on the one weekend of the year everyone's there — plain and legible where it needs to be read, but unmistakably about *this* trip, not a generic app or product.

## Materials / Design Language

Two different jobs, two different rules — this is the resolution of the tension in *The Brand* above, not a single blanket rule:

- **The information itself** (arrival/departure/meal/structure rows, names, times — anything someone actually needs to read to find their own facts) stays flat, plain, high-contrast, no ornamentation competing with the text. No illustration, no decorative icons. This is what makes #1 (easy to read) true.
- **The canvas that information sits on** is where the site is allowed to feel like Murray Corner specifically, not a spreadsheet — the shifting time-of-day atmosphere as you scroll through a day (see *Signature visual conventions* below) is the site's main device for #2 (a unique feel), and it's allowed to be soft, blended, alive — a smooth transition, not just a flat swap — because that's what makes scrolling through the day feel like moving through an actual day at the cottage. A gradient used *here* isn't decoration for its own sake; it's doing the "feels like this weekend" job. The old blanket "no gradients anywhere" rule is retired — the real rule is narrower: never let a background effect slow down or compete with reading the information sitting on top of it.

## Craftsmanship

Precision in the information layer is what makes the site fast to scan — every day quarter canvas laid out exactly the same way, alignment and spacing consistent, nothing ornamental competing with the facts. The atmosphere layer (palette, time-of-day feel, the paper-itinerary framing) is where craftsmanship shows up differently: restraint and cohesion, not absence. Craftsmanship here means knowing which of the two jobs (see *Materials / Design Language* above) a given part of the page is doing, and holding it to the right standard — not defaulting everything to bare and undecorated.

## Colours

A Maritime coastal palette (tide, sea glass, sand) that's calm and legible rather than a designed brand palette — it should read as "the colors of the place," not "a logo system." Ten colors total, in two groups that do different jobs — not ten arbitrary picks, and not one blanket color reused everywhere regardless of what it's sitting on:

**Core — text, links, dividers:**
* Primary — Deep tide blue `#1b4965` (headings, the brand/home link, the best-contrast text choice against any light background)
* Secondary — Sea glass `#5fa8a0` (muted/supporting text and dividers — captions, subtitles, room labels)
* Text — Charcoal `#23282b` (default body copy)
* Mist — Soft mist white `#edf1f2` (the one color that reads clearly against a *dark* background — see Night below)

**Backgrounds — a family, each paired with whichever text color is genuinely its best contrast, not a single default applied everywhere:**
* Background (paper) — Off-white `#faf8f4` — the fixed "paper card" color (the structure/room boxes on the Timeline), always the same regardless of time of day or page, since a card is a physical object, not part of the atmosphere. Pairs with Primary/Text.
* Night `#16232e` — dark navy. Pairs with **Mist** — the one background dark enough to need it.
* Morning `#e4f1f8` — pale sky blue. Pairs with Primary.
* Afternoon `#e8d9b5` — driftwood sand (same value as Accent). Pairs with Primary.
* Evening `#f0c9a8` — warm peach. Pairs with Primary.
* Grove `#dde8d4` — soft sage green — the background for anything that *isn't* a specific day/quarter: the Timeline's own intro screen (before you've scrolled into a day), the Family Tree page, and the Attendees pages. A fifth "place," not a time. Pairs with Primary.

So in practice there are only two text treatments in play at once — Mist on Night, Primary everywhere else — because those are genuinely the best-contrast choices; there's no reason to invent a bespoke hue per background just to have one. Role and hierarchy (a title vs. a label vs. an action) come from weight and size, not from switching colors — see *Signature visual conventions* below for how this plays out in the Timeline's nav bar specifically.

## Typography

System sans throughout — no webfont loading, since some family will read this on flaky airport wifi.

### Headlines
`system-ui, -apple-system, sans-serif`, bold, Primary color. Day headings and the site title.

### Body Text
Same system-sans stack, regular weight, Text color. Arrival/departure/meal/sleeping lines.

### Labels / Small Text
Same stack, smaller size, Secondary color — day quarter labels ("6am–12pm"), mode tags (plane/train/car).

---

# Illustration / Imagery Style

None. No icons beyond a small text/emoji tag for travel mode (✈️ / 🚆 / 🚗) — functional, not decorative.

---

# Signature visual conventions

- Every day quarter canvas, whether or not it has content, always shows the same five-part shape (arrivals, departures, sleeping, meal, activities), content pinned top-left, so the eye learns one layout and can skip straight to what's filled in.
- The full trip (August 1–15) is always in the page, but it always *opens* on "now" (computed live from the visitor's own clock, not baked into the build) — scrolling forward moves ahead through what's next, scrolling back moves through what's already happened. See `requirements/public.md` → *Homepage = Timeline* → *Always the full trip, "now" computed live*.
- Each quarter screen carries a time-of-day background (dark navy for Night, pale sky blue for Morning, driftwood sand for Afternoon, warm peach for Evening) that transitions smoothly as you scroll from one quarter into the next, rather than cutting hard at the boundary — see `requirements/public.md` → *Homepage = Timeline* → *Time-of-day background*. This is the site's main "unique feel" device (see *Materials / Design Language* above) — the structure/room boxes stay paper-colored regardless, so the information itself is never harder to read on one quarter's background than another's.
- The Timeline's nav bar shares whichever quarter color the canvas beneath it is showing, with its own text switching between Mist (on Night) and Primary (everywhere else) for best contrast — see *Colours* above. Every nav item (the live label, "Now", "▶", "Tree", "Folks ▾") uses that one color; only weight and size distinguish one from another, not a different hue per item — a deliberate, coherent system, not each item picking whatever felt closest at the time.
- Anything that isn't a specific day/quarter — the Timeline's own intro screen, the Family Tree page, the Attendees pages — shares one background, Grove (soft sage green), instead of a plain white default. A fifth "place" in the palette, not a time.

---

# Logo

None — this is a one-trip family site, not a brand. The page title text is the identity.

---

# Name

**Murray Corner 2026**

Named plainly after the place and the year — the point is clarity, not cleverness.

### Associated Properties

* Domain: `https://fletcher-stella-murray-corner.github.io/2026-logistics/`
* Email: n/a
* Socials: n/a — shared by direct link only

---

# Core Principles

* Easy to read comes first, unique feel comes second — never the other way around (see *The Brand*). If a decoration slows down finding your own facts, it doesn't belong, full stop.
* The information layer (rows, names, times, facts) stays flat and undecorated so it's fast to read; the atmosphere layer (background, time-of-day feel, palette) is where the site is allowed to be soft, alive, and specific to Murray Corner — see *Materials / Design Language*.
* "Now" (today's actual current day quarter) is always where the page opens, and always one tap away via the nav bar's "Now" button — never buried, even though the full trip is in the page and finished days are just a scroll away.
* Every day quarter canvas shows the same five things, top-left, in the same order, filled in or not.
* Legible on a phone, one-handed, in bad light, on bad wifi, beats anything visually clever.
* No login, almost no interactivity beyond scrolling and links — a page anyone in the family can open cold. Two narrowly-scoped exceptions, neither of which adds a mode, a setting, or anything to configure: the Timeline's "▶" play/pause auto-advance toggle (see `requirements/public.md` → *Navigation*), just a single icon-only button that plays the same scroll you'd do by hand; and the "Now" button, which jumps to the same place opening the page fresh already would.
