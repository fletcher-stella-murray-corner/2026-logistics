// Shared client-side nav logic — inlined into every page at build time
// (see technical.md -> Where CSS and JS changes go). currentQuarterSectionId()
// is a plain top-level function (not wrapped in DOMContentLoaded), so it's
// available immediately once this script tag runs, before timeline/shared.js
// (site/index.html only, loaded after this file) needs to reuse it for its
// own Play/pause and transition-screen wiring — one computation, not two
// copies that could drift on "what quarter is it right now at the cottage."
//
// The DOMContentLoaded block below wires the "Timeline" and "Folks" split
// controls' own default-click behavior (see requirements/public.md ->
// Navigation) — the two items every page's nav bar has, including Family
// Tree and Attendees pages, which have no other JS of their own to hang
// this off.

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
        var target = document.getElementById(id);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
});
