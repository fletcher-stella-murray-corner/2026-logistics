// Shared client-side nav logic — inlined into every page at build time
// (see technical.md -> Where CSS and JS changes go). currentQuarterSectionId()
// is a plain top-level function (not wrapped in DOMContentLoaded), so it's
// available immediately once this script tag runs, before timeline/shared.js
// (site/index.html only, loaded after this file) needs to reuse it for its
// own Play/pause and transition-screen wiring — one computation, not two
// copies that could drift on "what quarter is it right now at the cottage."
//
// The DOMContentLoaded block below wires the "Timeline" and "Folks" split
// controls' own default-click behavior, and the shared close-a-panel
// behavior every .jump-menu disclosure needs (see requirements/public.md
// -> Navigation -> Closing a panel) — every page's nav bar has these,
// including Family Tree and Attendees pages, which have no other JS of
// their own to hang this off.

var NAV_TRIP_TIMEZONE = 'America/Moncton';

function navQuarterForHour(hour) {
  if (hour < 6) return '00-06';
  if (hour < 12) return '06-12';
  if (hour < 18) return '12-18';
  return '18-24';
}

// Intl.DateTimeFormat with an explicit timeZone reads the wall-clock
// date/hour AT THE COTTAGE regardless of the visitor's own system timezone
// — hourCycle: 'h23' pins the hour to a plain 0-23 range (some engines
// otherwise return "24" for midnight with hour12: false alone).
function navTripLocalParts(d) {
  var parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: NAV_TRIP_TIMEZONE,
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', hourCycle: 'h23'
  }).formatToParts(d);
  var map = {};
  parts.forEach(function (p) { map[p.type] = p.value; });
  return { iso: map.year + '-' + map.month + '-' + map.day, hour: parseInt(map.hour, 10) };
}

// tripStart/tripEnd are ISO date strings ("2026-08-01") read off whichever
// element triggered the call (its own data-trip-start/data-trip-end), not
// a single shared global — this same function works identically whether
// called from site/index.html or a page two directory levels away from it.
function currentQuarterSectionId(tripStart, tripEnd) {
  var now = navTripLocalParts(new Date());
  var iso = now.iso;
  var quarter = navQuarterForHour(now.hour);
  // Clamp into the trip window: before it starts snaps to the very first
  // quarter; after it ends snaps to the very last.
  if (iso < tripStart) {
    iso = tripStart;
    quarter = '00-06';
  } else if (iso > tripEnd) {
    iso = tripEnd;
    quarter = '18-24';
  }
  return 'qc-' + iso + '-' + quarter;
}

// A deliberate "jump to this section" action — used by every call site
// that can land more than one quarter screen away from where the visitor
// currently is: this file's own "Timeline" nav item click, and (in
// timeline/shared.js) the transition screen's two choices and every
// jump-menu link. Plain top-level function, same reasoning as
// currentQuarterSectionId() above — needed before timeline/shared.js's
// own DOMContentLoaded block runs, and shared rather than duplicated
// since call sites live in both files.
//
// Exists specifically to fix a real flashing-content bug (see
// requirements/public.md -> Home & Timeline -> Time-of-day background):
// timeline/shared.js's live scroll-position color blend repaints on
// every scroll event, which is exactly right for an organic scroll or a
// one-screen jump (a gentle cross-fade into the next quarter's color),
// but a browser's smooth-scroll animation takes roughly the same short
// duration to cross ANY distance — so a jump of, say, five screens fires
// that same per-frame repaint five times faster, racing through five
// quarters' colors in under a second. That reads as a strobe, not a
// cross-fade. window.__scrollJumpActive is the flag
// updateQuarterBlend() (timeline/shared.js) checks to skip its own
// per-frame work while a jump is in flight, so a multi-screen jump shows
// no color changes at all for its duration and settles in one clean
// step on the destination's own correct color the instant it lands —
// nothing skipped for a single-screen jump or organic scrolling, since
// isMultiScreenJump() below only sets the flag for a jump that actually
// crosses more than one quarter screen.
//
// Also suspends scroll-snap for the duration, same fix and same reason
// timeline/shared.js's play/pause run already applies (see its own
// startRun()/stopRun() comments and timeline/shared.css ->
// html.timeline-page.auto-scrolling): scrollIntoView({behavior:
// 'smooth'}) while an ancestor has scroll-snap-type: y mandatory active
// is a known bad combination on mobile Safari/iOS specifically — for a
// jump of more than one screen (the Home screen's "Aug 1st"/"Now"
// buttons, or any jump-menu link landing more than a screen away) it can
// silently fail to scroll at all, not just animate roughly, since the
// play/pause fix only ever covered its OWN repeated calls, not this
// function every other jump path (transition screen, jump-menu links,
// the Timeline nav item) actually goes through. Harmless on any page
// other than site/index.html — .auto-scrolling only matches CSS scoped
// under html.timeline-page (timeline/shared.css), which no other page's
// <html> carries. Unlike the blend suspension above, this part is NOT
// scoped to multi-screen jumps only — a single-screen jump goes through
// this exact same scrollIntoView(smooth) call and hits the identical
// Safari/iOS snap bug, so scroll-snap is suspended for every jump
// regardless of distance.
//
// isMultiScreenJump() reads target's own current bounding rect rather
// than tracking "which screen is current" as a separate piece of state:
// quarter screens stack at one viewport height each (100svh — see
// timeline/shared.css), so before any scrolling starts, a target at most
// one screen away always sits within about one viewport height of the
// current scroll position (roughly 0 for the same screen, roughly
// +/-100vh for an adjacent one); anything further is unambiguously a
// multi-screen jump. The 1.5x margin absorbs the small, expected slack
// from the nav bar's own height and mobile toolbar collapse/expand,
// without ever mistaking a genuinely-adjacent screen for a far one.
function isMultiScreenJump(target) {
  var top = target.getBoundingClientRect().top;
  return Math.abs(top) > window.innerHeight * 1.5;
}
var scrollJumpSettleTimer = null;
function jumpToSection(target) {
  if (!target) return;
  var suspendBlend = isMultiScreenJump(target);
  if (suspendBlend) {
    window.__scrollJumpActive = true;
  }
  document.documentElement.classList.add('auto-scrolling');
  if (scrollJumpSettleTimer) clearTimeout(scrollJumpSettleTimer);
  var settle = function () {
    if (suspendBlend) {
      window.__scrollJumpActive = false;
    }
    document.documentElement.classList.remove('auto-scrolling');
    document.removeEventListener('scrollend', settle);
    // A one-off, definitive correction for the Structures stage (and the
    // nav label alongside it) — timeline/shared.js exposes this only on
    // site/index.html (the one page with quarter screens/a stage to
    // correct), so it's guarded here rather than assumed to exist; see
    // that file's own window.__syncStructuresStage comment for why this
    // can't just piggyback on the synthetic 'scroll' event below the way
    // the blend does — IntersectionObserver doesn't listen for 'scroll'
    // at all, so nudging one wouldn't reach it.
    if (typeof window.__syncStructuresStage === 'function') {
      window.__syncStructuresStage();
    }
    // Nudge timeline/shared.js's own scroll listener to recompute now
    // that we've landed — without this, a suspended blend would stay
    // frozen at whatever it was showing right before the jump until the
    // visitor's next real scroll/swipe. Harmless to dispatch even when
    // suspendBlend was false (the blend was never frozen in the first
    // place, so this just repaints with the same answer it already had).
    window.dispatchEvent(new Event('scroll'));
  };
  // 'scrollend' (supported in every current evergreen browser) fires the
  // instant the browser's own smooth-scroll animation actually finishes
  // — far more reliable than guessing a fixed duration. The setTimeout
  // is only a fallback for a browser missing it entirely.
  if ('onscrollend' in window) {
    document.addEventListener('scrollend', settle, { once: true });
  } else {
    scrollJumpSettleTimer = setTimeout(settle, 700);
  }
  target.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.addEventListener('DOMContentLoaded', function () {
  // "Timeline" nav item's own click (see requirements/public.md ->
  // Navigation) — jumps to "now": scrolls in place when already on
  // site/index.html (data-prefix empty), or navigates there when on
  // Family Tree/a Details page (data-prefix e.g. "../index.html").
  var timelineJump = document.getElementById('timeline-jump');
  if (timelineJump) {
    timelineJump.addEventListener('click', function () {
      var id = currentQuarterSectionId(timelineJump.dataset.tripStart, timelineJump.dataset.tripEnd);
      var prefix = timelineJump.dataset.prefix || '';
      if (prefix) {
        window.location.href = prefix + '#' + id;
      } else {
        jumpToSection(document.getElementById(id));
      }
    });
  }

  // "Folks" nav item's own click — jumps to a random attending person's
  // Details page, computed fresh each time. data-people is the full
  // attending roster ([{id, name}, ...], JSON-encoded); data-attendees-
  // prefix the page-relative path to site/attendees/.
  var folksRandom = document.getElementById('folks-random');
  if (folksRandom) {
    folksRandom.addEventListener('click', function () {
      var people = JSON.parse(folksRandom.dataset.people || '[]');
      if (!people.length) return;
      var person = people[Math.floor(Math.random() * people.length)];
      window.location.href = (folksRandom.dataset.attendeesPrefix || '') + person.id + '.html';
    });
  }

  // Folks panel — freshly shuffled display order on every page load (see
  // requirements/public.md -> Navigation -> Folks panel), so no single
  // person is always first or last. A build-time order would be the same
  // every time this static page loads, which isn't actually random — has
  // to happen here instead. Fisher-Yates on the real DOM nodes, each
  // person shuffled independently (not grouped by couple/family), then
  // re-appended in the new order; re-appending an already-attached node
  // moves it rather than duplicating it.
  var folksList = document.querySelector('.folks-list');
  if (folksList) {
    var people = Array.prototype.slice.call(folksList.children);
    for (var i = people.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = people[i];
      people[i] = people[j];
      people[j] = tmp;
    }
    people.forEach(function (el) { folksList.appendChild(el); });
  }

  // Closing a disclosure (see requirements/public.md -> Navigation ->
  // Closing a panel) — a plain <details> does neither of these two on
  // its own: opening one leaves any other already-open one (a nav panel,
  // or — see below — a person-chip's revealed name) sitting open too,
  // overlapping on screen, and clicking anywhere outside an open one
  // does nothing at all — the only way to close it is clicking the exact
  // same tiny trigger again. Both read as "hard to close." Lives here
  // (not timeline/shared.js) so it applies on every page with one of
  // these, including Family Tree and Attendees pages, which have no
  // other JS of their own.
  //
  // Covers two visually different but mechanically identical things:
  // the nav's own split-control panels (.jump-menu — Timeline's day/
  // quarter jump list, Folks, Milestones) and a person-chip's tap-to-
  // reveal name (.person-chip — render_person_chip() in
  // timeline/scripts/build.py, see requirements/public.md -> The
  // Structures stage -> Nested box display and -> Row-by-row rules ->
  // Arrivals) — both are just <details>/<summary>, so one shared "only
  // one open at a time, click away or Escape closes it" rule covers
  // every one of them site-wide, not a second bespoke mechanism for
  // chips. A page can have a couple hundred person-chips (every occupant
  // ever shown on the Structures stage, every traveler on every Arrivals/
  // Departures row, all pre-rendered — see technical.md -> The
  // Structures stage) — trivial to attach one listener each on a static
  // page this size.
  var disclosures = document.querySelectorAll('.jump-menu, .person-chip');
  if (disclosures.length) {
    // Opening one closes any other open one first — 'toggle' fires
    // whenever a <details>'s own open state changes, native or scripted,
    // so this also catches one opened programmatically (e.g. a future
    // change), not just a direct click on its own trigger.
    disclosures.forEach(function (menu) {
      menu.addEventListener('toggle', function () {
        if (!menu.open) return;
        disclosures.forEach(function (other) {
          if (other !== menu) other.open = false;
        });
      });
    });
    // A click anywhere outside every open one closes it — checked via
    // .contains() so a click on its own trigger or a link inside it is
    // correctly left alone (the trigger's native toggle, or
    // timeline/shared.js's own close-after-acting logic, handle those).
    document.addEventListener('click', function (event) {
      disclosures.forEach(function (menu) {
        if (menu.open && !menu.contains(event.target)) {
          menu.open = false;
        }
      });
    });
    // Escape closes whatever's open — the keyboard equivalent of
    // clicking away, for anyone not using touch/mouse.
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      disclosures.forEach(function (menu) { menu.open = false; });
    });
  }
});
