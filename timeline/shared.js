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
      var target = document.getElementById(id);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
  var transitionAug1 = document.getElementById('transition-aug1');
  if (transitionAug1) {
    transitionAug1.addEventListener('click', function (event) {
      var target = document.getElementById(this.getAttribute('href').slice(1));
      if (target) {
        event.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }

  // Jump-menu links do a smooth animated scroll to their target, then
  // close the disclosure so it doesn't keep covering the day quarter
  // canvas just jumped to. Deliberately uses scrollIntoView({behavior:
  // 'smooth'}) on click rather than the CSS `scroll-behavior: smooth`
  // property — that property applies to ALL scrolling including native
  // scroll-snap settling, and pairing it with scroll-snap-type is a known
  // Safari/iOS bug (see timeline/shared.css). Scoping "smooth" to just
  // this explicit, deliberate jump action avoids that entirely. Covers
  // both split controls' own panels (the Timeline's day/quarter jump
  // list and "Folks") — a loop over ALL .jump-menu elements, not just the
  // first match.
  var menus = document.querySelectorAll('.jump-menu');
  menus.forEach(function (menu) {
    var links = menu.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
      links[i].addEventListener('click', function (event) {
        var target = document.getElementById(this.getAttribute('href').slice(1));
        if (target) {
          event.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
  if (dayEl && dateEl && screens.length && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          dateEl.textContent = entry.target.getAttribute('data-date');
          var quarterName = entry.target.getAttribute('data-quarter-name');
          dayEl.textContent = quarterName ? ' · ' + quarterName : '';
          if (navEl) {
            navEl.setAttribute('data-quarter', entry.target.getAttribute('data-quarter'));
          }
        }
      });
    }, { rootMargin: '-' + NAV_HEIGHT_PX + 'px 0px -90% 0px', threshold: 0 });
    screens.forEach(function (el) {
      observer.observe(el);
    });
  }

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
  var runSections = document.querySelectorAll('.quarter-screen');
  if (runButton && runSections.length) {
    var PAUSE_MS = 1800;
    var runTimerId = null;
    var runIndex = 0;

    // The section whose top edge has scrolled up to (or past) the nav —
    // i.e. whichever screen is currently occupying the viewport below the
    // sticky nav — found by walking forward while sections keep starting
    // at/above that line, same rootMargin logic as the nav-label observer
    // above just applied as a one-off lookup instead of a live observer.
    function currentSectionIndex() {
      var idx = 0;
      for (var i = 0; i < runSections.length; i++) {
        if (runSections[i].getBoundingClientRect().top <= NAV_HEIGHT_PX + 1) {
          idx = i;
        } else {
          break;
        }
      }
      return idx;
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
      if (runIndex >= runSections.length) {
        stopRun();
        return;
      }
      runSections[runIndex].scrollIntoView({ behavior: 'smooth', block: 'start' });
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
