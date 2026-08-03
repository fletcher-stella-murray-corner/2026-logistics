// Timeline feature — inlined into site/index.html at build time.
document.addEventListener('DOMContentLoaded', function () {
  // Must match --nav-height in shared/base.css (3.75rem = 60px at the
  // default root font size) — hardcoded here since reading a CSS custom
  // property and converting rem to px reliably isn't worth the extra code
  // for a fixed, known value. Shared by both uses below (the live nav
  // label's IntersectionObserver rootMargin, and the play/pause run's
  // currentSectionIndex()) so the two can't drift to different values.
  var NAV_HEIGHT_PX = 60;

  // "Now" — the current day quarter AT THE COTTAGE (Murray Corner, New
  // Brunswick — Atlantic Time), computed fresh from the visitor's device
  // clock but read in the trip's own timezone, not whatever timezone the
  // visitor's device happens to be set to (never baked in at build time —
  // see timeline/scripts/build.py's module docstring) so the exact same
  // static page stays accurate for the whole trip with no rebuild. This
  // matters beyond just correctness: someone still at home checking "who
  // else is landing around now" (see brand-guidelines.md -> The Story)
  // needs that answered for the cottage's own clock — their own local
  // hour is meaningless here, and could even fall on a different
  // Atlantic-time calendar date entirely. TRIP_CONFIG is emitted by
  // build_page_html() just before this script, from the same
  // TRIP_START/TRIP_END shared/trip.py uses at build time — the trip
  // window itself is still fixed data, only "which quarter is now" is a
  // runtime, per-visitor question.
  var TRIP_TIMEZONE = 'America/Moncton';
  function quarterForHour(hour) {
    if (hour < 6) return '00-06';
    if (hour < 12) return '06-12';
    if (hour < 18) return '12-18';
    return '18-24';
  }
  // Intl.DateTimeFormat with an explicit timeZone reads the wall-clock
  // date/hour AT THE COTTAGE regardless of the visitor's own system
  // timezone — hourCycle: 'h23' pins the hour to a plain 0-23 range
  // (some engines otherwise return "24" for midnight with hour12: false
  // alone, a known cross-browser quirk).
  function tripLocalParts(d) {
    var parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: TRIP_TIMEZONE,
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', hourCycle: 'h23'
    }).formatToParts(d);
    var map = {};
    parts.forEach(function (p) { map[p.type] = p.value; });
    return { iso: map.year + '-' + map.month + '-' + map.day, hour: parseInt(map.hour, 10) };
  }
  function currentQuarterSectionId() {
    var now = tripLocalParts(new Date());
    var iso = now.iso;
    var quarter = quarterForHour(now.hour);
    // Clamp into the trip window: before it starts snaps to the very
    // first quarter; after it ends (the one edge case that matters —
    // see requirements/public.md -> Navigation) snaps to the very last.
    if (iso < TRIP_CONFIG.start) {
      iso = TRIP_CONFIG.start;
      quarter = '00-06';
    } else if (iso > TRIP_CONFIG.end) {
      iso = TRIP_CONFIG.end;
      quarter = '18-24';
    }
    return 'qc-' + iso + '-' + quarter;
  }

  // Land on "now" on first load, unless the URL already points somewhere
  // specific (a shared link to a particular quarter screen), which is
  // left alone — instant, not smooth, so opening the page doesn't
  // visibly fly through however many days have already passed. Scrolling
  // down from here moves forward through the rest of the trip; scrolling
  // back up moves backward, all the way past August 1 to the intro
  // screen — nothing before "now" is hidden, unlike the old cutoff-based
  // version (see requirements/public.md -> Homepage = Timeline).
  if (!location.hash && typeof TRIP_CONFIG !== 'undefined') {
    var nowTarget = document.getElementById(currentQuarterSectionId());
    if (nowTarget) {
      nowTarget.scrollIntoView({ behavior: 'instant', block: 'start' });
    }
  }

  // The "Now" nav button (render_nav() in timeline/scripts/build.py) —
  // same target as the auto-scroll above, but computed fresh at click
  // time rather than reused from page load, in case the page has been
  // open a while. A button, not a plain anchor link, since the target
  // quarter depends on the visitor's own clock and can't be baked into a
  // static href the way every other jump link's target can.
  var nowButton = document.getElementById('jump-now-toggle');
  if (nowButton && typeof TRIP_CONFIG !== 'undefined') {
    nowButton.addEventListener('click', function () {
      var target = document.getElementById(currentQuarterSectionId());
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (history.replaceState) {
          history.replaceState(null, '', '#' + target.id);
        }
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
  // this explicit, deliberate jump action avoids that entirely.
  // Both the jump-to-time disclosure (the current-quarter label itself,
  // see render_nav() in timeline/scripts/build.py) and "Folks ▾" share
  // the .jump-menu/.jump-panel markup and need the same smooth-scroll-
  // and-close behavior — this must stay a loop over ALL of them, not
  // just the first match.
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

  // Keeps the nav bar's left-side label showing which day quarter is
  // currently in view, updated as you scroll — the bare month/day
  // (.cq-date, smaller/secondary, e.g. "Aug 3") shown first, then the
  // weekday plus bare quarter name (.cq-day, bold/prominent, e.g.
  // "Monday Morning") shown second, as two separate spans rather than
  // one flat string so CSS can style them differently (see
  // timeline/shared.css) — cq-day's own leading " - " is part of its
  // text content, not static markup, so nothing floats on its own before
  // either span has actually been filled in. Also sets data-quarter on
  // the nav bar itself to match, so its time-of-day background
  // (timeline/shared.css -> .site-nav[data-quarter]) tracks the same
  // quarter as the label and the canvas beneath it, all off the one
  // observer.
  var dayEl = document.getElementById('cq-day');
  var dateEl = document.getElementById('cq-date');
  var navEl = document.querySelector('.site-nav');
  var screens = document.querySelectorAll('.quarter-screen[data-day-name]');
  if (dayEl && dateEl && screens.length && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          dateEl.textContent = entry.target.getAttribute('data-date');
          dayEl.textContent = ' - ' + entry.target.getAttribute('data-day-name') + ' ' + entry.target.getAttribute('data-quarter-name');
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

  // Keeps the nav bar's own background in exact visual agreement with
  // whatever's directly behind/below it, rather than a discrete swap at
  // a fixed scroll threshold (data-quarter above) — that swap alone
  // looked right most of the time, but for the ~20% of each quarter
  // screen's height where its own background is still blending in from
  // the PREVIOUS quarter's color (timeline/shared.css ->
  // .quarter-screen[data-quarter], the smooth-transition gradient), the
  // nav would already show the new quarter's fully-resolved flat color
  // while the canvas just below it was still mid-blend — a visible seam
  // right at the nav's bottom edge. Recomputed continuously on scroll
  // (rAF-throttled, not on every scroll event) since the nav is one
  // fixed, non-scrolling element with no natural "position within a
  // gradient" of its own the way each quarter screen has via its own box
  // height — reads --quarter-bg/--prev-quarter-bg straight off whichever
  // screen currently sits at the nav's bottom edge (already fully
  // resolved to concrete rgb() values by getComputedStyle, since nested
  // var() references inside a custom property resolve at computed-value
  // time), so the two colors this blends between can't drift from the
  // CSS's own values. Sets --quarter-bg as an inline style, which wins
  // over the plain attribute-driven rule above regardless of source
  // order (inline beats any stylesheet selector) — data-quarter above is
  // still what the Night-only text-contrast rules
  // (.site-nav[data-quarter="00-06"] ...) key off, untouched by this.
  var navBlendScreens = document.querySelectorAll('.quarter-screen[data-quarter]');
  if (navEl && navBlendScreens.length) {
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
    var navBlendRafId = null;
    function updateNavBlend() {
      navBlendRafId = null;
      var current = null;
      var rect = null;
      for (var i = 0; i < navBlendScreens.length; i++) {
        var r = navBlendScreens[i].getBoundingClientRect();
        if (r.top <= NAV_HEIGHT_PX && r.bottom > NAV_HEIGHT_PX) {
          current = navBlendScreens[i];
          rect = r;
          break;
        }
      }
      if (!current) {
        navEl.style.removeProperty('--quarter-bg');
        return;
      }
      var cs = getComputedStyle(current);
      var ownColor = parseRgb(cs.getPropertyValue('--quarter-bg'));
      var prevColor = parseRgb(cs.getPropertyValue('--prev-quarter-bg'));
      if (!ownColor || !prevColor) return;
      // Same 20%-of-height blend-in stop the CSS gradient itself uses —
      // keep these in sync if that stop ever changes.
      var fraction = (NAV_HEIGHT_PX - rect.top) / rect.height;
      var t = Math.max(0, Math.min(fraction / 0.20, 1));
      navEl.style.setProperty('--quarter-bg', mixRgb(prevColor, ownColor, t));
    }
    function scheduleNavBlendUpdate() {
      if (navBlendRafId === null) {
        navBlendRafId = requestAnimationFrame(updateNavBlend);
      }
    }
    window.addEventListener('scroll', scheduleNavBlendUpdate, { passive: true });
    updateNavBlend();
  }

  // Play/pause auto-advance — steps through every screen one at a time:
  // jump to the next screen, pause PAUSE_MS so there's time to actually
  // read it, jump to the next, pause, and so on — not a continuous scroll.
  // PAUSE_MS is the one knob to retune the rhythm (longer to linger on
  // each day quarter, shorter to move briskly).
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
  // reaches the last screen.
  var runButton = document.getElementById('run-toggle');
  var scrollRoot = document.documentElement;
  var runSections = document.querySelectorAll('main > section');
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
