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
  var menu = document.querySelector('.jump-menu');
  if (menu) {
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
  }

  // Keeps the nav bar's left-side label showing which day quarter is
  // currently in view, updated as you scroll. NAV_HEIGHT_PX must match
  // --nav-height in shared/base.css (3.75rem = 60px at the default root
  // font size) — it's hardcoded here since reading a CSS custom property
  // and converting rem to px reliably isn't worth the extra code for a
  // fixed, known value.
  var label = document.getElementById('current-quarter-label');
  var screens = document.querySelectorAll('.quarter-screen[data-quarter-label]');
  if (label && screens.length && 'IntersectionObserver' in window) {
    var NAV_HEIGHT_PX = 60;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          label.textContent = entry.target.getAttribute('data-quarter-label');
        }
      });
    }, { rootMargin: '-' + NAV_HEIGHT_PX + 'px 0px -90% 0px', threshold: 0 });
    screens.forEach(function (el) {
      observer.observe(el);
    });
  }
});
