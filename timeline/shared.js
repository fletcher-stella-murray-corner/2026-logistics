// Timeline feature — inlined into site/index.html at build time.
document.addEventListener('DOMContentLoaded', function () {
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
  // currently in view, updated as you scroll — the weekday name
  // (.cq-day, prominent) and the month/day + quarter (.cq-date,
  // smaller/secondary) as two separate spans, not one flat string, so
  // CSS can style them differently (see timeline/shared.css). NAV_HEIGHT_PX
  // must match --nav-height in shared/base.css (3.75rem = 60px at the
  // default root font size) — it's hardcoded here since reading a CSS
  // custom property and converting rem to px reliably isn't worth the
  // extra code for a fixed, known value.
  var dayEl = document.getElementById('cq-day');
  var dateEl = document.getElementById('cq-date');
  var screens = document.querySelectorAll('.quarter-screen[data-day-name]');
  if (dayEl && dateEl && screens.length && 'IntersectionObserver' in window) {
    var NAV_HEIGHT_PX = 60;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          dayEl.textContent = entry.target.getAttribute('data-day-name');
          dateEl.textContent = ' · ' + entry.target.getAttribute('data-date-quarter');
        }
      });
    }, { rootMargin: '-' + NAV_HEIGHT_PX + 'px 0px -90% 0px', threshold: 0 });
    screens.forEach(function (el) {
      observer.observe(el);
    });
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
    var RUN_NAV_HEIGHT_PX = 60; // matches NAV_HEIGHT_PX above (--nav-height in shared/base.css)
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
        if (runSections[i].getBoundingClientRect().top <= RUN_NAV_HEIGHT_PX + 1) {
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
