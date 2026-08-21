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

It's not a group chat and not a spreadsheet — it's a single always-current source of truth, computed live from whoever's actually looking at it, so "now" is always correct no matter when someone checks it, with zero rebuilds and zero stale info — one tap away from anywhere on the site, or one deliberate choice at the top of the Timeline itself (see `requirements/public.md` → *Navigation* and → *Home & Timeline* → *Layout*), rather than something decided for the visitor the instant the page loads. And it doesn't look or feel like a scheduling tool: the day-quarter-by-day-quarter rhythm, the shifting time-of-day atmosphere, and the "torn from a paper itinerary at the cottage" feel are what make it read as Murray Corner's own thing rather than a generic itinerary app.

---

# Visual Identity

## Overall Feeling

A page torn from a simple paper travel itinerary someone left on the kitchen table at the cottage, on the one weekend of the year everyone's there — plain and legible where it needs to be read, but unmistakably about *this* trip, not a generic app or product.

## Materials / Design Language

Two different jobs, two different rules — this is the resolution of the tension in *The Brand* above, not a single blanket rule:

- **The information itself** (arrival/departure/meal/structure rows, names, times — anything someone actually needs to read to find their own facts) stays flat, plain, high-contrast, no ornamentation competing with the text. No illustration, no decorative icons. This is what makes #1 (easy to read) true.
  **One narrow, deliberate exception: a person's name, specifically on the Structures stage and the Timeline's Arrivals/Departures rows, renders as a small initials chip (see *Illustration / Imagery Style* below) that reveals the full name on tap, rather than the name itself sitting in the row.** This isn't decoration competing with the text — it's the text, just disclosed in two steps instead of one, and it exists to solve a real conflict between the two Structures-stage promises that came before it: the stage's own map (`brand-guidelines.md` → *Materials / Design Language* → "the stage is a map, not a list") reserves a permanent, unchanging spot for every place that will ever matter across the whole trip, all at once — a genuinely large, fixed quantity of space that a bare name list made taller than a phone's own screen (see `technical.md` → *The Structures stage*). Initials read at a glance for "who, roughly, is here" and "how many"; a tap gets the exact name for the rare case that matters. The reveal itself (`<details>`/`<summary>`, matching `shared/nav.py`'s existing jump-menu convention, not a new interaction pattern) is `position: absolute` and never changes the row's own size when opened — the same "never grows, never shrinks" promise the stage's own boxes already keep, just applied one level deeper, to what's inside them.
- **The canvas that information sits on** is where the site is allowed to feel like Murray Corner specifically, not a spreadsheet — the shifting time-of-day atmosphere as you scroll through a day (see *Signature visual conventions* below) is the site's main device for #2 (a unique feel), and it's allowed to be soft, blended, alive — a smooth transition, not just a flat swap — because that's what makes scrolling through the day feel like moving through an actual day at the cottage. A gradient used *here* isn't decoration for its own sake; it's doing the "feels like this weekend" job. The old blanket "no gradients anywhere" rule is retired — the real rule is narrower: never let a background effect slow down or compete with reading the information sitting on top of it. This blend belongs to the *act of scrolling*, not to the screen itself: the moment you stop moving — settled on a quarter screen, no gesture in progress — the whole thing reads as one clean flat color. A gradient that's still visibly half-blended while you're just sitting there reading isn't "alive," it's a rendering bug wearing the effect's clothes; see `requirements/public.md` → *Time-of-day background* for the exact behavior this implies.
- **Structures (physical places) sit on neither of the above — they're pinned, not on the canvas at all.** A place doesn't move as the days pass, so it shouldn't move on screen either; only time does. Structures live on their own fixed stage, stationary while the quarter canvas and its time-of-day atmosphere scroll past above/behind it — see *Signature visual conventions* below. Each box itself is still squarely Job #1, the information layer (flat, paper-colored, no ornamentation) — going on a fixed stage instead of the scrolling canvas is a placement decision, not a license to decorate the boxes themselves. **The stage's own backdrop — the surface the boxes sit ON, not the boxes' own surfaces — is the one deliberate exception, and it's not paper-colored at all: it's transparent**, so whichever time-of-day blue the canvas is currently showing continues straight through behind the boxes, uninterrupted, rather than a separate neutral panel bolted on underneath them. A place still never moves and never borrows the day's color onto its OWN surface (see *Signature visual conventions* below) — only the empty space around and behind it does.

  **The stage is a map, not a list — this is the whole point, stated as plainly as possible.** A map's geometry (where every named place sits, relative to every other one) is fixed and complete before a single pin on it ever lights up; the passage of time doesn't get to rearrange the map, it only lights up or dims pins on one that was already finished. So every structure, and every room inside it, that will EVER matter across the whole trip gets its own position decided exactly once — before the visitor has scrolled to a single quarter, not incrementally as places happen to become relevant, and not influenced in any way by what else is currently lit. A structure (a room, a Working/Kitchen sub-box) gets exactly one dynamic behavior for the entire rest of the trip: lighting up or going dark — and going dark means fading to a faint ghost of itself, still legibly there, not vanishing outright (a dimmer switch, not an on/off one). It is never allowed to move, grow, shrink, or change which places sit next to it — not even as a one-time, seemingly-harmless side effect of something ELSE appearing or disappearing nearby. A dark, not-yet-relevant place sitting quietly and faintly in its own already-assigned spot is the map working correctly, the same way a building directory lists a not-yet-occupied office rather than removing it from the board — reserving space (and showing it, even dim) ahead of need is the cost of this promise, not a bug in it. **That accepted cost is a reason to be disciplined about area everywhere else, not an excuse to be loose about it.** Once a place's existence and position are fixed, its own size should still be the smallest that fits its actual content — a long room name wraps onto a second line rather than stretching its box wide to fit on one, and a box's height never inflates just because a sibling sharing its row happens to be taller (see `requirements/public.md` → *The Structures stage* → *Layout* → "Minimize total area covered" for the specifics). The map reserves generously where it has to; it shouldn't waste space anywhere it doesn't have to.

## Craftsmanship

Precision in the information layer is what makes the site fast to scan — every day quarter canvas laid out exactly the same way, alignment and spacing consistent, nothing ornamental competing with the facts. The atmosphere layer (palette, time-of-day feel, the paper-itinerary framing) is where craftsmanship shows up differently: restraint and cohesion, not absence. Craftsmanship here means knowing which of the two jobs (see *Materials / Design Language* above) a given part of the page is doing, and holding it to the right standard — not defaulting everything to bare and undecorated.

## Colours

Pastel art deco, 1970s-leaning — soft, tonal, nothing shouts. The four day-quarter backgrounds in particular read as one family now, not four unrelated picks: a single dusty blue, palest at Morning and darkest at Night, quietly deepening through the day rather than cycling through different hues. Ten colors total, in three groups that do different jobs:

**Core — text, links, dividers:**
* Primary — Deep tide blue `#1b4965` (headings, the brand/home link, the one text color used against every background on the site — see *Backgrounds* below)
* Secondary — Sea glass `#5fa8a0` (muted/supporting text and dividers — captions, subtitles, room labels)
* Text — Charcoal `#23282b` (default body copy)

**Backgrounds — a family, all light enough for Primary/Text to read on directly. No background on the site is dark enough to need a separate light-on-dark text color anymore — one text treatment, not two:**
* Background (paper) — Parchment `#f2e9d6`, a warm pale tint of Accent — the fixed "paper card" color (structure/room boxes, Family Tree boxes, the nav's own jump/Folks panels), always the same regardless of time of day or page, since a card is a physical object, not part of the atmosphere. Warmer than a neutral off-white on purpose — a flat near-white paper read as generic UI chrome rather than an actual paper card.
* Morning `#e6f1f7` — palest pastel blue, the lightest of the four day-quarter tones.
* Afternoon `#cbe1ec` — light pastel blue.
* Evening `#b0cede` — medium pastel blue.
* Night `#8fb0c7` — dustiest, darkest pastel blue — deliberately still light enough that Primary text reads on it cleanly, so the day quarters need no color exception at their darkest point, only their most saturated.
* Grove `#c9e2c0` — soft pastel green, more visibly green than a gray-leaning sage — the background for anything that isn't a specific day/quarter: the Home view (the intro screen, before you've scrolled into a day), the Family Tree page, and the Attendees pages. A fifth "place," not a time.

**Accent — a status flag, not a background:**
* Accent — Driftwood sand `#e8d9b5` — used narrowly for one job: flagging an attending person whose travel facts haven't been entered yet (Family Tree, `.person.status-needed`), plus a couple of small decorative borders (the Timeline's room boxes). Deliberately outside the Backgrounds family above and no longer tied to Afternoon's color — it's the one warm color in an otherwise cool, tonal palette, which is what makes "needs attention" actually pop.

**Utility — plain structural neutrals, not part of the ten-color brand palette above:**
* Border `#ddd6c4` — the one divider/outline color used everywhere something needs a hairline (card borders, row dividers, the nav's own bottom rule) — `--border` in `shared/base.css`. A muted tint in the same warm-neutral family as Parchment, deliberately unbranded so it never competes with the ten colors above.
* Muted hint text `#8a8378` — the italic "no one added yet" empty-state copy (`.empty-hint`, Family Tree) — a plain low-emphasis gray rather than a designed brand color, since an empty state is explicitly not something to make eye-catching. The Timeline's own day quarter canvas no longer has an empty-state hint at all (`.quarter-empty-hint` removed) — reviewer feedback found "Nothing scheduled" unhelpful rather than reassuring, so an empty canvas is now simply blank, same four-part shape either way.

Role and hierarchy (a title vs. a label vs. an action) come from weight and size, not from switching colors — see *Signature visual conventions* below for how this plays out in the Timeline's nav bar specifically.

## Typography

System sans for everything read as data or body copy — arrival/departure/meal/sleeping lines, labels, the whole nav bar — since some family will read this on flaky airport wifi and it has to render instantly no matter what. One deliberate exception, scoped tightly: *Headlines* (below) load a single Art Deco display webfont, with the system stack as a same-meaning fallback and `font-display: swap` — so a connection too slow or broken to fetch it just shows today's plain system-sans look instead, never invisible text and never a layout shift. Nothing else on the site loads a webfont.

### Headlines
**Limelight** (Google Fonts) — a high-contrast Art Deco display face, weight 400 (its only weight; never synthetic-bolded by the browser), Primary color, falling back to `system-ui, -apple-system, sans-serif` if it doesn't load. The site title, every page's own `<h1>`, and every day heading wherever one appears — the Attendees page's own (`<h2 class="fact-day">`) is the running example. The one deliberate exception: the Timeline's jump-panel date chip (see `requirements/public.md` → *Navigation* → *Timeline's panel*) is also, structurally, a day heading, but stays in the same plain face as the three quarter-name chips beside it — four chips in one row need to read as one consistent set of buttons first; color (that chip's own Night background) is what marks it as different, not typeface. This is the site's one piece of genuine period character; everything else stays deliberately plain per *Materials / Design Language* above.

### Body Text
System sans, regular weight, Text color. Arrival/departure/meal/sleeping lines.

### Labels / Small Text
System sans, smaller size, uppercase, letter-spaced, Secondary or Primary color (whichever that label already used) — day quarter row labels ("Sleeping," "Arriving"), structure/room labels, Attendees fact labels ("Arrival," "Departure"), the Family Tree legend, and the Folks panel's own "Timeline"/"Detail" actions. One consistent typographic signature for "this word is a label, not data," used identically everywhere a label appears rather than varying by feature — see `shared/base.css` → `.jump-person-actions a` for the canonical values (0.08em letter-spacing; other instances use a slightly tighter 0.04–0.06em where the label sits inline within a sentence instead of standing alone). Mode tags (plane/train/car) are the one exception — left in mixed case since they're an inline tag mid-sentence, not a standalone label.

---

# Illustration / Imagery Style

Almost none. No icons beyond a small text/emoji tag for travel mode (✈️ / 🚆 / 🚗) — functional, not decorative — plus one deliberate second exception: a person's initials in a small filled circle (the Structures stage, the Timeline's Arrivals/Departures rows — see *Materials / Design Language* above and `requirements/public.md` for exactly where), standing in for that person's name until tapped. Still text, not a picture or a per-person avatar/illustration — one letter per word of the same display name already shown everywhere else on the site for a multi-word name ("Helen S" → "HS"), or the name's own first two letters when it's a single word ("Stella" → "ST", chosen specifically because plain first-letter-only collided 5 ways on this roster's own "S" names alone), same typographic spirit as the mode tag, not a new visual language. **A known, accepted gap, not yet solved:** several real pairs on this roster still share initials even with the two-letter rule (Stella/Steven, Margaret/Matt, and others) and render identically until tapped — the real, current list is logged in `open-questions.md` rather than guessed at here.

---

# Signature visual conventions

- Every day quarter canvas, whether or not it has content, always shows the same four-part shape (arrivals, departures, meal, activities), content pinned top-left, so the eye learns one layout and can skip straight to what's filled in. Structures isn't part of this shape — see the fixed-stage bullet below.
- **Structures live on a fixed stage, pinned to the screen, not inside the scrolling canvas — a vertical list (a responsive grid on a wide screen), never a sideways-scrolling row.** A bottom-docked strip, stationary for the whole Timeline view, showing every structure and room that will EVER matter across the whole trip in its own permanently-assigned spot, computed once, in full, before any of them is first relevant — not a strip that grows as more places turn out to matter, however rarely (see *Materials / Design Language* → "The stage is a map, not a list" above: growing at all, even once, even for a good reason, is already breaking the promise, since it moves everything already on screen along with it). A structure (Cottage, Red Shed, etc.) either shows or doesn't; a room inside it does the same, independently, one level down — but neither one's own position, nor anyone else's, ever depends on which of them currently happen to be lit. Only text content (who's sleeping/working/cooking where) updates within an already-lit place; nothing about the layout itself is still being decided once the visitor starts scrolling. The boxes themselves always read as Parchment (paper) — a place isn't "in" any one quarter, so its own surface never borrows one's color. The stage's own backdrop, in contrast, is transparent, not Parchment: whichever time-of-day blue the canvas above is currently showing continues straight through behind the boxes with nothing separating them, one continuous sea of the day's own color rather than a neutral shelf underneath it (see *Materials / Design Language* above for the full reasoning — a reversal of an earlier version of this doc, which had the whole stage, backdrop included, reading as fixed Parchment). This is the literal, on-screen version of the site's own framing: the cottage doesn't scroll past you as the days go by; the days scroll past the cottage — and the cottage, quite literally, never moves, even while sitting directly in the middle of the very color that's doing the moving.
- The full trip (August 1–13) is always in the page. The page itself opens on Home, not "now" — but "now" (computed live from the visitor's own clock, not baked into the build) is always one deliberate choice away, at the transition screen right below Home or via the nav bar's "Timeline" item from anywhere — scrolling forward from there moves ahead through what's next, scrolling back moves through what's already happened. See `requirements/public.md` → *Home & Timeline* → *Always the full trip, "now" computed live*.
- Each quarter screen carries a time-of-day background (palest pastel blue for Morning, light pastel blue for Afternoon, medium pastel blue for Evening, dustiest/darkest pastel blue for Night — one tonal family, not four different hues) that transitions smoothly as you scroll from one quarter into the next, rather than cutting hard at the boundary — see `requirements/public.md` → *Home & Timeline* → *Time-of-day background*. This is the site's main "unique feel" device (see *Materials / Design Language* above) — the structure/room boxes stay paper-colored regardless, so the information itself is never harder to read on one quarter's background than another's.
- The Timeline's nav bar shares whichever quarter color the canvas beneath it is showing, with its own text staying Primary throughout — no per-quarter color switch needed, since none of the four quarter backgrounds are dark enough to require one (see *Colours* above). Every nav item (MC26, Timeline, Folks, Tree, and the Timeline panel's own trigger/Play/jump-list contents) uses that one color; only weight and size distinguish one from another, not a different hue per item — a deliberate, coherent system, not each item picking whatever felt closest at the time. See `requirements/public.md` → *Navigation* for the full item roster.
- Anything that isn't a specific day/quarter — the Home view (the intro screen), the Family Tree page, the Attendees pages — shares one background, Grove (soft pastel green), instead of a plain white default. A fifth "place" in the palette, not a time.
- **The nav's disclosure panels (the day/quarter jump list, the Folks panel) carry the site's one geometric ornament**: a small notched/stepped clip at the panel's own top corners (a ticket stub torn off the paper itinerary), and, in the Folks panel specifically, a small diamond (◆, Accent color) centered on the rule between each person. Both are pure geometry — shapes, not pictures — so they stay inside the site's "no icons/illustration" rule (see *Illustration / Imagery Style* below) while still giving the chrome layer a genuine Art Deco signature instead of being generically flat. Scoped to these two panels only, not applied to the information layer itself (structure/room boxes, fact lines) — restraint over decoration, per *Materials / Design Language* above.
- **The night quarter (`00-06`) has no name in any text the site shows you.** Every other quarter is named in the nav's live label as you scroll ("Tuesday Morning," "Tuesday Afternoon," "Tuesday Evening") — night alone is just the day itself ("Tuesday"). This isn't an omission, it's a small piece of voice: night reads as the tail end of the day before it, not the start of the one after, so scrolling from Monday evening into the trip's next quarter and being told "Tuesday Night" would feel like the day hasn't actually turned over yet. Saying just "Tuesday" instead is what makes the day-by-day rhythm of scrolling feel like walking through an actual week at the cottage rather than reading labeled time slots off a schedule — see `requirements/public.md` → *Terminology* for exactly where this shows up (the nav's live label, the jump-to-time panel, the Attendees page). `00-06` still exists as data and is still called "Night" in this document's own color language (*Colours* above) — this is a rule about what the site says out loud, not about the quarter's identity.

---

# Logo

None — this is a one-trip family site, not a brand. The page title text is the identity.

---

# Name

**Murray Corner 2026**

Named plainly after the place and the year — the point is clarity, not cleverness. Shortened to **MC26** in exactly one place — the nav bar's fixed identity item (see `requirements/public.md` → *Navigation*) — where every other item is competing for the same row's width; the full name stays everywhere else (page `<title>`s, the intro screen's own heading, this document).

### Associated Properties

* Domain: `https://fletcher-stella-murray-corner.github.io/2026-logistics/`
* Email: n/a
* Socials: n/a — shared by direct link only

---

# Core Principles

* Easy to read comes first, unique feel comes second — never the other way around (see *The Brand*). If a decoration slows down finding your own facts, it doesn't belong, full stop.
* The information layer (rows, names, times, facts) stays flat and undecorated so it's fast to read; the atmosphere layer (background, time-of-day feel, palette) is where the site is allowed to be soft, alive, and specific to Murray Corner — see *Materials / Design Language*.
* The page opens on the landing page (Home), not "now" — but "now" (today's actual current day quarter) is always just one tap away via the nav bar's "Timeline" item, or one deliberate choice at the transition screen right below Home, from anywhere on the site — never buried, and never silently auto-selected for the visitor either, even though the full trip is in the page and finished days are just a scroll away.
* Every day quarter canvas shows the same four things (arrivals, departures, meal, activities), top-left, in the same order, filled in or not — Structures isn't one of the four: it lives on its own fixed stage instead, so a physical place never has to scroll past and reappear as the canvas moves through the day above it (see *Signature visual conventions*).
* Legible on a phone, one-handed, in bad light, on bad wifi, beats anything visually clever.
* No login, almost no interactivity beyond scrolling and links — a page anyone in the family can open cold. A few narrowly-scoped exceptions, none of which adds a mode, a setting, or anything to configure (see `requirements/public.md` → *Navigation*): the Timeline's "▶" play/pause auto-advance toggle, just a single icon-only control that plays the same scroll you'd do by hand; the "Timeline" and "Folks" nav items' own client-computed jumps (to "now," or to a random attending person); the transition screen's "Jump to now"/"Aug 1st" choice, right below Home; and a person's initials chip on the Structures stage/Arrivals/Departures rows, tapped to reveal that one name (see *Materials / Design Language* above) — the only one of this list that reveals information rather than navigating or toggling a mode, and still bounded the same way the others are: one tap, one plain fact, nothing to configure or leave in a changed state.
