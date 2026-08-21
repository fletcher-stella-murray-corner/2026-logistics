// Timeline feature — inlined into site/index.html at build time, after
// shared/nav.js (which supplies currentQuarterSectionId() — the single
// "what quarter is it right now at the cottage" computation this file
// reuses rather than duplicating, since shared/nav.js's own "Timeline"
// split-control click needs the identical answer).
document.addEventListener('DOMContentLoaded', function () {
  // Must match --nav-height in shared/base.css (3.75rem = 60px at the
  // default root font size) — hardcoded here since reading a CSS custom
  // property and converting rem to px reliably isn't worth the extra code
  // for a fixed, known value. Shared by both uses below (the live nav
  // label's IntersectionObserver rootMargin, and the play/pause run's
  // currentSectionIndex()) so the two can't drift to different values.
  var NAV_HEIGHT_PX = 60;

  // The transition screen's own two choices (see requirements/public.md
  // -> Home & Timeline -> Layout) — reached by scrolling down from Home,
  // not on load: this page no longer auto-scrolls anywhere on a hash-less
  // load (see requirements/public.md -> Always the full trip, "now"
  // computed live, for why that changed) — a fresh visit just opens on
  // Home, same as any other page, and a `#qc-...` hash still lands the
  // browser directly on that quarter screen via plain native anchor
  // behavior, no JS needed for that case at all.
  var transitionNow = document.getElementById('transition-now');
  if (transitionNow) {
    transitionNow.addEventListener('click', function () {
      var id = currentQuarterSectionId(transitionNow.dataset.tripStart, transitionNow.dataset.tripEnd);
      jumpToSection(document.getElementById(id));
    });
  }
  var transitionAug1 = document.getElementById('transition-aug1');
  if (transitionAug1) {
    transitionAug1.addEventListener('click', function (event) {
      var target = document.getElementById(this.getAttribute('href').slice(1));
      if (target) {
        event.preventDefault();
        jumpToSection(target);
      }
    });
  }

  // Jump-menu links do a smooth animated scroll to their target (via
  // jumpToSection() in shared/nav.js — see that function's own comment
  // for why a multi-screen jump like this needs to suspend the live
  // color blend below, not just animate the scroll), then close the
  // disclosure so it doesn't keep covering the day quarter canvas just
  // jumped to. Deliberately uses scrollIntoView({behavior: 'smooth'})
  // (inside jumpToSection()) rather than the CSS `scroll-behavior:
  // smooth` property — that property applies to ALL scrolling including
  // native scroll-snap settling, and pairing it with scroll-snap-type is
  // a known Safari/iOS bug (see timeline/shared.css). Scoping "smooth"
  // to just this explicit, deliberate jump action avoids that entirely.
  // Covers both split controls' own panels (the Timeline's day/quarter
  // jump list and "Folks") — a loop over ALL .jump-menu elements, not
  // just the first match.
  var menus = document.querySelectorAll('.jump-menu');
  menus.forEach(function (menu) {
    var links = menu.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
      links[i].addEventListener('click', function (event) {
        var target = document.getElementById(this.getAttribute('href').slice(1));
        if (target) {
          event.preventDefault();
          jumpToSection(target);
          if (history.replaceState) {
            history.replaceState(null, '', this.getAttribute('href'));
          }
        }
        menu.open = false;
      });
    }
  });

  // Keeps the Timeline split control's own label showing which day
  // quarter is currently in view, updated as you scroll — the abbreviated
  // weekday+date (.cq-date, smaller/secondary, e.g. "Wed, Aug 5", already
  // weekday-first — see timeline/scripts/build.py -> render_quarter_
  // screen() and shared/trip.py -> format_date_abbrev()) shown first,
  // then the bare quarter name (.cq-day, bold/prominent, e.g. "Morning")
  // shown second, as two separate spans rather than one flat string so
  // CSS can style them differently (see shared/base.css) — cq-day's own
  // leading " · " is part of its text content, not static markup, so
  // nothing floats on its own before either span has actually been
  // filled in. The middot (not a hyphen) matches the separator used
  // everywhere else two related pieces of info sit together on this site
  // (QUARTER_LABELS' own "Morning · 6am–12pm") — see
  // requirements/public.md -> Navigation.
  //
  // data-quarter-name is EMPTY for 00-06 (see QUARTER_NAMES in
  // shared/trip.py and render_quarter_screen() in
  // timeline/scripts/build.py) — that quarter has no name of its own on
  // this site: night reads as the tail end of the day before it, not the
  // start of the one after, so scrolling into a new day's first quarter
  // shows just the weekday+date alone ("Wed, Aug 5"), never an invented
  // "Wed, Aug 5 · Night" — see requirements/public.md -> Terminology. The
  // conditional below leaves cq-day empty entirely in that case, rather
  // than a dangling "· " with nothing after it.
  //
  // Also sets data-quarter on the nav bar itself to match, so its
  // time-of-day background (timeline/shared.css -> .site-nav[data-quarter])
  // tracks the same quarter as the label and the canvas beneath it, all
  // off the one observer.
  var dayEl = document.getElementById('cq-day');
  var dateEl = document.getElementById('cq-date');
  var navEl = document.querySelector('.site-nav');
  var screens = document.querySelectorAll('.quarter-screen[data-date]');

  // The current-section geometry lookup — shared by the play/pause
  // control further down (currentSectionIndex()) and the settle-time
  // correction below (window.__syncStructuresStage()), not a second
  // live-tracking mechanism running alongside the observer below: this
  // is a plain, on-demand answer, computed fresh only when actually
  // called, same rootMargin logic as the observer just applied as a
  // one-off walk instead of a live subscription.
  function currentQuarterScreen() {
    var current = null;
    for (var i = 0; i < screens.length; i++) {
      if (screens[i].getBoundingClientRect().top <= NAV_HEIGHT_PX + 1) {
        current = screens[i];
      } else {
        break;
      }
    }
    return current;
  }

  // Structures stage (see requirements/public.md -> Home & Timeline ->
  // The Structures stage, and technical.md -> The Structures stage) — a
  // complete, fixed map (structure > [building >] room/instance/Working/
  // Kitchen, plus Unassigned) decided once, in full, at build time: every
  // element that will EVER be relevant anywhere in the trip is already in
  // the DOM, in its own permanent layout position, before this code ever
  // runs — nothing here adds or removes anything from the page, only
  // toggles visibility. Each carries its own data-mount-from/
  // data-mount-to (timeline/scripts/build.py -> compute_structures_
  // stage()). Every such element is cached once into a plain array, not
  // re-queried on every scroll — there are at most a couple hundred of
  // these across the whole page (a handful of structures, a few rooms
  // each, a handful of text variants per room), trivial to walk on every
  // quarter change.
  var stageEl = document.getElementById('structures-stage');
  var mountRangeEls = stageEl
    ? Array.prototype.slice.call(document.querySelectorAll('[data-mount-from]'))
    : [];
  // The one generic rule applied to every such element regardless of
  // nesting depth: a whole structure box, a room/Working/Kitchen sub-box,
  // and a single pre-rendered occupant-text variant span are all just "is
  // the current quarter inside my own [from, to] range" — see
  // requirements/public.md -> The Structures stage -> "The map is decided
  // once, in full, before the stage is ever shown" for why one mechanism
  // covers every level rather than a different one per nesting depth.
  // Plain string comparison works directly on "qc-..." ids with no
  // parsing — the zero-padded ISO date and fixed quarter suffixes already
  // sort in chronological order as strings (see quarter_screen_id() in
  // shared/trip.py).
  //
  // #structures-stage itself is the one exception: it still uses the
  // native `hidden` property (display:none) for the whole-strip Home/
  // transition-screen-vs-Timeline swap, same as before — safe there
  // specifically because it's `position: fixed`, already outside document
  // flow. Every DESCENDANT instead gets a `slot-dark` class toggled
  // (`visibility: hidden` in timeline/shared.css, never `display: none`),
  // so its own reserved space in the grid/flex layout stays reserved
  // whether it's lit or dark — see that file's own comment on
  // `.slot-dark` for why that one substitution is the actual fix.
  function applyStructuresMountRanges(currentId) {
    mountRangeEls.forEach(function (el) {
      var from = el.getAttribute('data-mount-from');
      var to = el.getAttribute('data-mount-to');
      var inRange = !!(currentId && from <= currentId && currentId <= to);
      if (el === stageEl) {
        el.hidden = !inRange;
      } else {
        el.classList.toggle('slot-dark', !inRange);
        // A ghosted (dark) box stays visually present on purpose (see
        // .slot-dark in timeline/shared.css — opacity, not display:none
        // or visibility:hidden), but a screen reader shouldn't announce
        // every not-currently-relevant place on the stage just because
        // it's still faintly paintable — aria-hidden keeps assistive
        // tech's own notion of "present" matching what a sighted visitor
        // would actually treat as relevant right now, independent of the
        // CSS that handles the visual side.
        el.setAttribute('aria-hidden', String(!inRange));
      }
    });
  }

  // Keeps .quarter-canvas's own bottom-padding reservation (timeline/
  // shared.css) in sync with the stage's REAL current height. The stage
  // still has no height cap — it reserves space for every structure/room/
  // etc that will EVER be relevant across the whole trip, all at once,
  // from the moment it first renders (see requirements/public.md -> The
  // Structures stage -> Layout and technical.md -> The Structures stage
  // for the concrete numbers) — so a static guess could never stay
  // correct there; this is the live mechanism that guess's own CSS
  // fallback only covers briefly, before this runs. Its job is narrower
  // than it used to be, though: the stage's height no longer changes as a
  // CONSEQUENCE of scrolling through quarters at all (nothing mounts or
  // unmounts anymore, ever, once first rendered — going lit/dark is a
  // pure visibility change, see applyStructuresMountRanges() above), so
  // this observer is only still doing real work for a genuine viewport-
  // driven reflow: a window resize crossing one of .structures-stage-
  // inner's own column-count breakpoints, a font loading late, mobile
  // browser chrome collapsing/expanding. Entirely independent of the
  // quarter-change logic above either way; "how tall is the stage right
  // now" and "which quarter is current" don't need to be the same
  // trigger.
  if (stageEl && 'ResizeObserver' in window) {
    var stageResizeObserver = new ResizeObserver(function (entries) {
      document.documentElement.style.setProperty('--stage-height', entries[0].contentRect.height + 'px');
    });
    stageResizeObserver.observe(stageEl);
  }

  // Applies `current` (a .quarter-screen element, or null) to both the
  // nav label and the Structures stage in one place — used by the live
  // observer below AND by window.__syncStructuresStage()'s one-off
  // settle-time correction, so the two can't drift into applying the
  // "current screen -> visible state" rule slightly differently.
  function applyCurrentScreen(current) {
    if (current) {
      if (dateEl) dateEl.textContent = current.getAttribute('data-date');
      if (dayEl) {
        var quarterName = current.getAttribute('data-quarter-name');
        dayEl.textContent = quarterName ? ' · ' + quarterName : '';
      }
      if (navEl) {
        navEl.setAttribute('data-quarter', current.getAttribute('data-quarter'));
      }
      applyStructuresMountRanges(current.id);
    } else {
      // Scrolled back off every quarter screen (Home, or the transition
      // screen) — nothing here has a "now" to report, so both the label
      // and the stage revert. cq-day reverts to the literal static
      // "Timeline" text (must match shared/nav.py -> render_nav()'s own
      // build-time default on the same span), NOT an empty string — an
      // empty cq-date alongside an empty cq-day would leave the split
      // control's label reading as nothing at all, rather than the
      // static word every other view is supposed to show (see
      // requirements/public.md -> Navigation -> Timeline's panel).
      if (dateEl) dateEl.textContent = '';
      if (dayEl) dayEl.textContent = 'Timeline';
      // Clears the nav's own stale data-quarter too, falling back to its
      // CSS default (--grove, shared/base.css -> .site-nav) — left set to
      // whatever quarter you scrolled away from otherwise, which is wrong
      // on Home/the transition screen per requirements/public.md -> Time-
      // of-day background ("Grove... for anything that isn't a specific
      // day/quarter").
      if (navEl) navEl.removeAttribute('data-quarter');
      applyStructuresMountRanges('');
    }
  }

  if (dayEl && dateEl && screens.length && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function () {
      // Deliberately ignores the `entries` argument entirely — a real,
      // confirmed bug (found live: the stage/label would flash correctly
      // on scrolling into a new quarter, then immediately revert to
      // empty, inconsistently, worse scrolling down than up) came from
      // trusting it. An IntersectionObserver batch only reports elements
      // whose OWN intersection state changed since the last callback —
      // NOT "the full current truth of every observed element" — so when
      // the outgoing screen's exit and the incoming screen's entry land
      // in two SEPARATE callback invocations (common enough while
      // scrolling, and not something this code controls), a batch
      // containing only the exit looks — by the old logic — like "nothing
      // is intersecting anywhere," incorrectly reverting the stage/label
      // a moment after the correct one had already been shown by the
      // entry's own (earlier or later) callback. The observer firing at
      // all is only a "something changed, go check" trigger now — the
      // actual answer always comes from currentQuarterScreen()'s own
      // synchronous geometry walk (same helper the settle-time
      // correction and play/pause use), which has no notion of "this
      // batch" to be incomplete about: it re-derives the true current
      // screen from scratch, every time.
      //
      // Skipped for the duration of a suspended multi-screen jump (see
      // shared/nav.js -> jumpToSection() and window.__scrollJumpActive)
      // so the stage doesn't flicker lit/dark through every structure
      // relevant to the screens crossed in between — window.
      // __syncStructuresStage() below settles it directly on the correct
      // destination the instant the jump actually finishes, regardless
      // of what this observer did or didn't fire in the meantime. The
      // label freezing too for that same short window is a deliberate
      // side effect, not a separate fix — it was already prone to the
      // identical flicker-through-intermediate-quarters risk during a
      // fast jump, just for text instead of color.
      if (window.__scrollJumpActive) return;
      applyCurrentScreen(currentQuarterScreen());
    }, { rootMargin: '-' + NAV_HEIGHT_PX + 'px 0px -90% 0px', threshold: 0 });
    screens.forEach(function (el) {
      observer.observe(el);
    });
  }

  // A one-off, definitive correction run once a multi-screen jump
  // actually finishes — called from shared/nav.js -> jumpToSection()'s
  // own settle(), after window.__scrollJumpActive has already cleared.
  // Not a second live-tracking mechanism: currentQuarterScreen()'s same
  // one-off geometry lookup, applied once, so the label and stage end up
  // definitively correct regardless of exactly when (or whether) the
  // IntersectionObserver above managed to fire around the jump settling
  // — see requirements/public.md -> The Structures stage -> "The map is
  // decided once, in full, before the stage is ever shown". Exposed as a
  // global (rather than staying a private
  // closure variable) specifically so shared/nav.js, loaded and run
  // before this file, can still reach it from its own settle() callback,
  // which fires long after both files' own DOMContentLoaded setup has
  // already completed.
  window.__syncStructuresStage = function () {
    applyCurrentScreen(currentQuarterScreen());
  };

  // Time-of-day background blend — see requirements/public.md -> Time-of-
  // day background and timeline/shared.css -> .quarter-screen[data-quarter]
  // for the rule this exists to satisfy: a quarter screen at rest is
  // ALWAYS one flat color, never a gradient. The blend into the previous
  // quarter's color is purely a function of live scroll position, applied
  // to exactly ONE screen at a time — whichever one is currently sliding
  // into place — and it resolves fully to that screen's own flat color
  // (--quarter-bg, untouched) the instant it finishes settling. The same
  // one computed value also paints the nav bar, so the two can never
  // visibly disagree.
  //
  // Colors are read ONCE per screen at setup, not on every scroll frame —
  // reading a screen's --quarter-bg via getComputedStyle AFTER this code
  // has already set an inline override on it would read back its own
  // previous output instead of the CSS's real value, corrupting every
  // later frame's math. Caching upfront sidesteps that entirely.
  var blendScreens = document.querySelectorAll('.quarter-screen[data-quarter]');
  if (navEl && blendScreens.length) {
    function parseRgb(str) {
      str = (str || '').trim();
      var m = str.match(/^#([0-9a-f]{6})$/i);
      if (m) {
        var n = parseInt(m[1], 16);
        return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
      }
      m = str.match(/^rgba?\(([^)]+)\)$/i);
      if (m) {
        var parts = m[1].split(',');
        return [parseFloat(parts[0]), parseFloat(parts[1]), parseFloat(parts[2])];
      }
      return null;
    }
    function mixRgb(a, b, t) {
      return 'rgb(' + Math.round(a[0] + (b[0] - a[0]) * t) + ', ' +
        Math.round(a[1] + (b[1] - a[1]) * t) + ', ' +
        Math.round(a[2] + (b[2] - a[2]) * t) + ')';
    }
    var blendData = [];
    blendScreens.forEach(function (el) {
      var cs = getComputedStyle(el);
      blendData.push({
        el: el,
        own: parseRgb(cs.getPropertyValue('--quarter-bg')),
        prev: parseRgb(cs.getPropertyValue('--prev-quarter-bg'))
      });
    });
    // How much of a screen's own height the live blend plays out over,
    // right as its top edge approaches the viewport top — the one knob to
    // retune (a taller fraction = a longer, more gradual cross-fade during
    // the scroll gesture; 0 would make it a hard cut). Mirrors the 20%
    // stop the old static gradient used, just applied live now instead of
    // baked in.
    var BLEND_FRACTION = 0.20;
    var blendRafId = null;
    var lastOverridden = null;
    function updateQuarterBlend() {
      blendRafId = null;
      // Closes a race scheduleQuarterBlendUpdate()'s own check can't catch
      // alone: a frame can already be queued (blendRafId set from a
      // 'scroll' event fired a moment before the jump started) and still
      // fire after window.__scrollJumpActive flips true — bail here too
      // rather than let that one stray frame paint a mid-jump color.
      if (window.__scrollJumpActive) return;
      // The entering/current screen: among every quarter screen whose top
      // hasn't yet scrolled past the viewport top, the one closest to it.
      // At rest this is exactly the settled screen (its own top sits at
      // 0) — every other screen is either far below (not yet arrived) or
      // already fully scrolled past (excluded by the >= 0 check), so this
      // never needs a separate "which screen is settled" lookup.
      var best = null;
      for (var i = 0; i < blendData.length; i++) {
        var rect = blendData[i].el.getBoundingClientRect();
        if (rect.top >= 0 && (!best || rect.top < best.rect.top)) {
          best = { data: blendData[i], rect: rect };
        }
      }
      if (!best) {
        // Every screen's top has scrolled past — resting on/past the very
        // last one (or a sub-pixel overscroll bounce). Use it directly.
        var last = blendData[blendData.length - 1];
        best = { data: last, rect: last.el.getBoundingClientRect() };
      }
      if (lastOverridden && lastOverridden !== best.data.el) {
        lastOverridden.style.removeProperty('--quarter-bg');
      }
      if (!best.data.own || !best.data.prev) return;
      var t = Math.max(0, Math.min(1, 1 - best.rect.top / (best.rect.height * BLEND_FRACTION)));
      var color = mixRgb(best.data.prev, best.data.own, t);
      best.data.el.style.setProperty('--quarter-bg', color);
      lastOverridden = best.data.el;
      navEl.style.setProperty('--quarter-bg', color);
    }
    function scheduleQuarterBlendUpdate() {
      // window.__scrollJumpActive (set by jumpToSection() in shared/nav.js
      // for a genuine multi-screen jump — see that function's own comment)
      // is the fix for a real bug: without this check, every 'scroll'
      // event fired during the browser's own smooth-scroll animation
      // across several quarter screens used to schedule (and run) a fresh
      // blend computation, racing through each crossed screen's color in
      // well under a second — a strobe, not the gentle cross-fade this
      // effect is supposed to be (see requirements/public.md -> Time-of-
      // day background). The flag is never set for organic scrolling or a
      // one-screen jump, so neither loses the live blend — only an actual
      // multi-screen jump skips it, and jumpToSection()'s own settle()
      // callback fires one final synthetic 'scroll' once the flag clears,
      // so the destination still ends up painted correctly the instant
      // the jump finishes, just without any of the in-between repaints.
      if (window.__scrollJumpActive) return;
      if (blendRafId === null) {
        blendRafId = requestAnimationFrame(updateQuarterBlend);
      }
    }
    window.addEventListener('scroll', scheduleQuarterBlendUpdate, { passive: true });
    updateQuarterBlend();
  }

  // Play/pause auto-advance — steps through every QUARTER screen one at a
  // time (deliberately excludes Home and the transition screen — nothing
  // there to auto-advance through, and interactive choice buttons aren't
  // a screen to "read"): jump to the next screen, pause PAUSE_MS so
  // there's time to actually read it, jump to the next, pause, and so on
  // — not a continuous scroll. PAUSE_MS is the one knob to retune the
  // rhythm (longer to linger on each day quarter, shorter to move
  // briskly).
  //
  // Jumps use scrollIntoView({behavior: 'smooth'}), same as the Jump/
  // People links above, but ONLY while the `.auto-scrolling` class is on
  // <html> (see timeline/shared.css, which sets scroll-snap-type: none
  // for it) — suspending native scroll-snap for the duration. Leaving
  // scroll-snap-type: y mandatory active while repeatedly firing
  // scrollIntoView(smooth) is a known bad combination (each new call
  // interrupts the previous one mid-snap) that left this control visibly
  // stuck the first time it was built; suspending snap for the run and
  // restoring it on stop avoids that fight entirely while still landing
  // precisely on each quarter screen.
  //
  // Starts from whichever screen is currently in view, not always the
  // very first — see currentSectionIndex() below. Stops — restoring
  // scroll-snap and resetting the icon-only button back to "▶" — the
  // moment the user scrolls or swipes manually (listened on 'wheel'/
  // 'touchmove', real user gestures, not 'scroll', which also fires for
  // the scrollIntoView calls below and would cancel itself), or once it
  // reaches the last screen. While running, the Timeline split control's
  // own caret also swaps to "⏸" (see requirements/public.md ->
  // Navigation -> Timeline's panel) so the running state stays visible
  // even with the panel closed — Play now lives inside that panel, not
  // as its own top-level nav item, so without this the running state
  // would otherwise be invisible until reopening the panel.
  var runButton = document.getElementById('run-toggle');
  var timelineCaret = document.getElementById('timeline-caret');
  var scrollRoot = document.documentElement;
  if (runButton && screens.length) {
    var PAUSE_MS = 1800;
    var runTimerId = null;
    var runIndex = 0;

    // Delegates to the shared currentQuarterScreen() lookup above (same
    // one the Structures stage's settle-time correction uses) and turns
    // its answer into an index into `screens` — falls back to 0 (the
    // very first quarter screen) when nothing's currently in view, e.g.
    // Play clicked from Home, matching this function's own original
    // default before the geometry walk itself moved into the shared
    // helper.
    function currentSectionIndex() {
      var current = currentQuarterScreen();
      if (!current) return 0;
      var idx = Array.prototype.indexOf.call(screens, current);
      return idx < 0 ? 0 : idx;
    }

    function stopRun() {
      if (runTimerId) {
        clearTimeout(runTimerId);
        runTimerId = null;
      }
      scrollRoot.classList.remove('auto-scrolling');
      runButton.textContent = '▶';
      runButton.setAttribute('aria-label', 'Play');
      if (timelineCaret) timelineCaret.textContent = '▾';
      window.removeEventListener('wheel', stopRun);
      window.removeEventListener('touchmove', stopRun);
    }

    function advanceRun() {
      if (runIndex >= screens.length) {
        stopRun();
        return;
      }
      screens[runIndex].scrollIntoView({ behavior: 'smooth', block: 'start' });
      runIndex++;
      runTimerId = setTimeout(advanceRun, PAUSE_MS);
    }

    function startRun() {
      scrollRoot.classList.add('auto-scrolling');
      runIndex = currentSectionIndex();
      runButton.textContent = '⏸';
      runButton.setAttribute('aria-label', 'Pause');
      if (timelineCaret) timelineCaret.textContent = '⏸';
      window.addEventListener('wheel', stopRun, { passive: true });
      window.addEventListener('touchmove', stopRun, { passive: true });
      advanceRun();
    }

    runButton.addEventListener('click', function () {
      if (runTimerId) {
        stopRun();
      } else {
        startRun();
      }
    });
  }
});
