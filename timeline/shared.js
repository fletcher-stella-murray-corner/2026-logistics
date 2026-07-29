// Timeline feature — inlined into site/index.html at build time. Closes the
// "Jump to a day" disclosure once a link inside it is clicked, so it doesn't
// keep covering the day quarter canvas you just jumped to.
document.addEventListener('DOMContentLoaded', function () {
  var menu = document.querySelector('.jump-menu');
  if (!menu) return;
  var links = menu.querySelectorAll('a');
  for (var i = 0; i < links.length; i++) {
    links[i].addEventListener('click', function () {
      menu.open = false;
    });
  }
});
