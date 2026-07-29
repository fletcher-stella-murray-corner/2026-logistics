// Timeline feature — inlined into site/index.html at build time.
document.addEventListener('DOMContentLoaded', function () {
  // Closes the "Jump" disclosure once a link inside it is clicked, so it
  // doesn't keep covering the day quarter canvas you just jumped to.
  var menu = document.querySelector('.jump-menu');
  if (menu) {
    var links = menu.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
      links[i].addEventListener('click', function () {
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
