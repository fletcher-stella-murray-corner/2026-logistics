#!/usr/bin/env python3
"""Regenerate site/family-tree/index.html — the Family Tree feature.

Reads shared/data/people.json and renders a nested tree: each couple (or
single person) with no rendered parent yet at the top, their children
nested below them, recursively (see requirements/public.md -> Family Tree).
Also reads timeline/data/travel.json (read-only, same as the Attendees
feature) purely to compute each attending person's facts-collected/
collecting-facts status — shown on the box itself as a visual-only signal
(border style, background tint, opacity — see render_person() and
family-tree/shared.css) and explained once in the on-page legend
(render_legend() below), not per-entry in the nav's own "Folks ▾"
dropdown, which is a plain jump list now (see shared/nav.py ->
render_folks_menu()) — see requirements/public.md -> Family Tree ->
Layout and -> Navigation -> Folks panel. This is also the sole
entry point to the Attendees feature: an attending person's box (and
their "Folks ▾" entry) is a link straight to their site/attendees/<id>.html
page (the Attendees feature has no index page or nav link of its own —
see attendees/scripts/build.py); a not-attending person's box stays plain
text, since they have no such page to link to.

Validated at build time, as hard errors rather than silent typos: every
person has an 'id' (int), 'name' (non-empty string), and 'generation'
(int); every timeline/data/travel.json record has a 'person_id'; ids are
unique; parent_ids has at most 2 entries; every parent_ids/partner_id
reference points at an id that actually exists in people.json; nobody
lists themselves as their own parent or partner; a set partner_id is
reciprocated (if A's partner_id is B, B's partner_id must be A); nobody
has both married_in: true and a non-empty parent_ids (a contradiction —
see requirements/public.md -> people.json); a person's optional
birth_order (see requirements/public.md -> people.json -> birth_order)
is an integer when present; and, after the tree is
built, every person is actually reachable from a generation-1 root by
walking parent_ids/partner_id — someone who isn't (e.g. a generation/
parent_ids typo that never connects back to a root) would otherwise
silently never appear on the page at all, with no error.

Run after hand-editing shared/data/people.json, or use
scripts/build_site.py to rebuild every feature at once.

site/family-tree/index.html is a pure build artifact — edit this template,
not the HTML.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # family-tree/
PROJECT_ROOT = ROOT.parent  # repo root — site/ and shared/ live here

sys.path.insert(0, str(PROJECT_ROOT / "shared"))
import nav  # noqa: E402

# render_jump_panel() is timeline/scripts/build.py's — reused here rather
# than reimplemented, so the day/quarter jump list shown in this page's
# own "Timeline" split control can never drift from the Timeline's own
# (see requirements/public.md -> Navigation -> Timeline's panel). Same
# cross-import pattern scripts/report.py already established.
sys.path.insert(0, str(PROJECT_ROOT / "timeline" / "scripts"))
import build as timeline_build  # noqa: E402

PAGE_TITLE = "Family Tree — Murray Corner 2026"
TREE_SUBTITLE = "Where everyone fits"


def esc(s):
    return nav.esc(s)


def load_people():
    path = PROJECT_ROOT / "shared" / "data" / "people.json"
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {path}: {e}") from e


def load_travel():
    path = PROJECT_ROOT / "timeline" / "data" / "travel.json"
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {path}: {e}") from e


def collected_person_ids(travel):
    """The set of person_ids with a travel.json entry that isn't marked
    "pending": true — this script only needs that much, not the full
    referential/date validation timeline's build.py already owns, so just
    check the one field it reads plus the optional pending flag (see
    requirements/public.md -> Data -> travel.json -> pending)."""
    ids = set()
    for i, entry in enumerate(travel):
        label = f"Record at index {i} in timeline/data/travel.json"
        person_id = nav.require(entry, "person_id", label)
        if not entry.get("pending"):
            ids.add(person_id)
    return ids


def person_label(p, index):
    """A human-identifiable label for a record that might itself be missing
    'id' or 'name' — falls back to its position in the array so a build
    error always points somewhere findable instead of just KeyError-ing."""
    if "id" in p:
        return f"Person id {p['id']!r} (index {index}) in shared/data/people.json"
    return f"Person at index {index} in shared/data/people.json"


def validate_people_shape(people):
    for i, p in enumerate(people):
        label = person_label(p, i)
        pid = nav.require(p, "id", label)
        if not isinstance(pid, int):
            raise ValueError(f"{label} has a non-integer id {pid!r} — id must be an integer.")
        name = nav.require(p, "name", label)
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{label} has an empty or non-string name.")
        standalone = p.get("standalone")
        if standalone is not None and not isinstance(standalone, bool):
            raise ValueError(f"{label} has a non-boolean standalone {standalone!r} — standalone must be true or false.")
        # generation only exists to place someone within the generational
        # tree structure (see requirements/public.md -> people.json ->
        # generation) — meaningless, so not required, for someone marked
        # standalone (see -> standalone above), who renders in their own
        # section below that tree entirely, not nested anywhere in it.
        if not standalone:
            generation = nav.require(p, "generation", label)
            if not isinstance(generation, int):
                raise ValueError(f"{label} has a non-integer generation {generation!r} — generation must be an integer.")
        elif "generation" in p and not isinstance(p["generation"], int):
            raise ValueError(f"{label} has a non-integer generation {p['generation']!r} — generation must be an integer.")
        parent_ids = p.get("parent_ids") or []
        if len(parent_ids) > 2:
            raise ValueError(f"{name!r} has {len(parent_ids)} parent_ids — a person can have at most 2.")
        birth_order = p.get("birth_order")
        if birth_order is not None and not isinstance(birth_order, int):
            raise ValueError(f"{label} has a non-integer birth_order {birth_order!r} — birth_order must be an integer.")
        dogs = p.get("dogs")
        if dogs is not None:
            if not isinstance(dogs, list) or not dogs:
                raise ValueError(f"{label} has a non-list or empty dogs {dogs!r} — dogs must be a non-empty list when present.")
            for dog in dogs:
                if not isinstance(dog, str) or not dog.strip():
                    raise ValueError(f"{label} has a non-string or empty dog name in dogs {dogs!r}.")


def validate_people(people):
    validate_people_shape(people)

    people_by_id = {}
    for p in people:
        if p["id"] in people_by_id:
            raise ValueError(f"Duplicate id {p['id']!r} in shared/data/people.json — ids must be unique.")
        people_by_id[p["id"]] = p

    for p in people:
        if p["id"] in (p.get("parent_ids") or []):
            raise ValueError(f"{p['name']!r} lists themselves in their own parent_ids.")
        for parent_id in p.get("parent_ids") or []:
            if parent_id not in people_by_id:
                raise ValueError(
                    f"{p['name']!r}'s parent_ids references id {parent_id!r}, which doesn't "
                    f"exist in shared/data/people.json."
                )
        partner_id = p.get("partner_id")
        if partner_id is not None:
            if partner_id == p["id"]:
                raise ValueError(f"{p['name']!r} lists themselves as their own partner_id.")
            partner = people_by_id.get(partner_id)
            if partner is None:
                raise ValueError(
                    f"{p['name']!r}'s partner_id references id {partner_id!r}, which doesn't "
                    f"exist in shared/data/people.json."
                )
            if partner.get("partner_id") != p["id"]:
                raise ValueError(
                    f"{p['name']!r}'s partner_id points at {partner['name']!r}, but "
                    f"{partner['name']!r}'s partner_id doesn't point back — set "
                    f"{partner['name']!r}'s partner_id to {p['id']!r} (or clear {p['name']!r}'s) "
                    f"so the pairing is reciprocal."
                )
        if p.get("married_in") and p.get("parent_ids"):
            raise ValueError(
                f"{p['name']!r} has married_in: true but also has parent_ids set — "
                f"someone with documented parents is a blood descendant, not married in."
            )


def sibling_sort_key(p):
    """Left-to-right display order for siblings and for the top-level
    roots (see requirements/public.md -> people.json -> birth_order) —
    oldest first. `id` alone can't express this: ids are permanent and
    never renumbered, but people are entered in whatever order the editor
    learns about them, not birth order, so an older sibling added later
    usually ends up with a higher id than younger siblings already in the
    file. `birth_order` is the explicit override for exactly that case;
    everyone else just falls back to their own id, which is why the
    common case (siblings already entered oldest-to-youngest) needs no
    birth_order at all."""
    return (p.get("birth_order", p["id"]), p["id"])


def build_children_map(people):
    children_by_parent = {}
    for person in people:
        for parent_id in person.get("parent_ids") or []:
            children_by_parent.setdefault(parent_id, []).append(person)
    return children_by_parent


def person_status(person, collected_ids):
    """Not attending, plus the same two states the Attendees feature
    computes for everyone else (see requirements/public.md -> Attendees ->
    The two states) reused here for the Family Tree box's visual
    treatment — collecting facts (attending, no travel.json entry yet or
    the entry is marked "pending": true), or facts collected (attending,
    has a non-pending entry — the default box, nothing extra shown). Not
    attending isn't one of the Attendees feature's own two states (that
    feature only covers attending people at all) — its visual treatment is
    documented in requirements/public.md -> Family Tree -> Layout instead."""
    if not person.get("attending"):
        return "not-attending"
    if person["id"] in collected_ids:
        return "collected"
    return "needed"


def render_person(person, collected_ids):
    # Visual-only signal, no text caption — border style/color, a
    # background tint, and opacity are still how married-in/collecting-
    # facts/not-attending read on the tree itself (see
    # family-tree/shared.css -> .married-in/.status-needed/
    # .status-not-attending); the words themselves ("Married in",
    # "Collecting facts", "Not attending") are explained once by the
    # on-page legend instead (render_legend() below) — see
    # requirements/public.md -> Family Tree -> Layout for why.
    status = person_status(person, collected_ids)
    classes = ["person"]
    if person.get("married_in"):
        classes.append("married-in")
    if status == "needed":
        classes.append("status-needed")
    elif status == "not-attending":
        classes.append("status-not-attending")
    inner = f'<span class="person-name">{esc(person["name"])}</span>'

    # Attending people link straight to their own Attendees page — the
    # sole entry point to that feature (see module docstring). Not
    # attending means no such page exists, so stays plain text.
    if person.get("attending"):
        tag, extra = "a", f' href="../attendees/{person["id"]}.html"'
    else:
        tag, extra = "span", ""
    box = f'<{tag} class="{" ".join(classes)}"{extra}>{inner}</{tag}>'

    # A dog is an attribute of its owner, not a person of its own — no box,
    # no id, no travel/attending status (see requirements/public.md ->
    # people.json -> dogs). Rendered as a sibling tag beside the owner's
    # own box (not nested inside it), so the box itself still reads as
    # "just this person" — .couple's flex row is what actually places it
    # beside rather than below (see family-tree/shared.css -> .person-dogs).
    dogs = person.get("dogs")
    if dogs:
        box += f'<span class="person-dogs">+ {esc(", ".join(dogs))}</span>'
    return box


def render_legend():
    """A one-time key explaining the tree's visual-only language (see
    render_person() above and requirements/public.md -> Family Tree ->
    Layout) — shown once near the top of the page rather than a caption
    repeated under every third name, so someone new to the family can
    learn the convention in one glance instead of needing to already know
    it or go hunting in the "Folks ▾" dropdown for the words. Each swatch
    reuses the exact same classes as a real person box (.person plus its
    modifier), not a hand-drawn copy of the styling, so the key can never
    silently drift out of sync with what the boxes actually look like."""
    items = [
        ("married-in", "Married in"),
        ("status-needed", "Collecting facts"),
        ("status-not-attending", "Not attending"),
    ]
    swatches = "".join(
        f'<span class="legend-item"><span class="person legend-swatch {cls}"></span> {esc(label)}</span>'
        for cls, label in items
    )
    return f'<div class="tree-legend">{swatches}</div>'


def render_unit(person, people_by_id, children_by_parent, rendered_ids, collected_ids):
    if person["id"] in rendered_ids:
        return ""
    rendered_ids.add(person["id"])

    partner = people_by_id.get(person.get("partner_id"))
    member_ids = [person["id"]]
    couple_html = render_person(person, collected_ids)
    if partner is not None and partner["id"] not in rendered_ids:
        rendered_ids.add(partner["id"])
        member_ids.append(partner["id"])
        couple_html += '<span class="couple-joiner">&amp;</span>' + render_person(partner, collected_ids)

    kids = []
    seen_kid_ids = set()
    for member_id in member_ids:
        for kid in children_by_parent.get(member_id, []):
            if kid["id"] not in seen_kid_ids:
                seen_kid_ids.add(kid["id"])
                kids.append(kid)
    kids.sort(key=sibling_sort_key)

    kids_html = "".join(
        render_unit(k, people_by_id, children_by_parent, rendered_ids, collected_ids) for k in kids
    )
    children_block = f'<div class="children">{kids_html}</div>' if kids_html else ""

    return f'<div class="family-unit"><div class="couple">{couple_html}</div>{children_block}</div>'


def build_tree_html(people, collected_ids):
    # standalone people (see requirements/public.md -> people.json ->
    # standalone) opt out of the generational tree entirely — excluded
    # here so a standalone person with no `generation` set can't
    # accidentally default to generation 1 (see person.get("generation", 1)
    # below) and get swept into the roots list. They get their own
    # section instead — see render_standalone_section() below.
    tree_people = [p for p in people if not p.get("standalone")]

    if not tree_people:
        return '<p class="empty-hint">No one added to the family tree yet.</p>'

    people_by_id = {p["id"]: p for p in tree_people}
    children_by_parent = build_children_map(tree_people)
    min_generation = min(p.get("generation", 1) for p in tree_people)

    roots = [p for p in tree_people if p.get("generation", 1) == min_generation]
    roots.sort(key=sibling_sort_key)

    rendered_ids = set()
    units_html = "".join(
        render_unit(r, people_by_id, children_by_parent, rendered_ids, collected_ids) for r in roots
    )

    missing = [p for p in tree_people if p["id"] not in rendered_ids]
    if missing:
        missing.sort(key=lambda p: p["id"])
        names = ", ".join(f"{p['name']!r} (id {p['id']})" for p in missing)
        raise ValueError(
            f"The following people are never reached from a generation-{min_generation} "
            f"root and would silently be missing from the Family Tree page: {names}. "
            f"Check their generation and parent_ids — every non-root person needs a "
            f"parent_ids chain that eventually leads back to a root. If this person isn't "
            f"actually related to anyone in the tree, set standalone: true instead of trying "
            f"to connect them."
        )

    return f'<div class="generation">{units_html}</div>'


def render_standalone_section(people, collected_ids):
    """People marked standalone: true (see requirements/public.md ->
    people.json -> standalone) — genuinely unrelated to anyone else in the
    tree — render in their own flat section at the very bottom of the
    page, below the whole generational tree, instead of being forced into
    a parent_ids/partner_id chain back to a root, or treated as another
    top-level root sitting next to generation 1. Same box states/legend/
    Attendees-link behavior as everyone else (render_person() below) —
    only the nesting is different (none: one box per row, no couple
    pairing, no children)."""
    standalone_people = [p for p in people if p.get("standalone")]
    if not standalone_people:
        return ""
    standalone_people.sort(key=sibling_sort_key)
    boxes = "".join(
        f'<div class="family-unit"><div class="couple">{render_person(p, collected_ids)}</div></div>'
        for p in standalone_people
    )
    # A short heading, unlike the generational tree above it (which has no
    # per-generation label at all) — without one, a reader could easily
    # mistake this flat, unconnected group for another generation of the
    # same family rather than guests with no blood/marriage tie to anyone
    # in it.
    return (
        '<p class="standalone-heading">Also joining us</p>'
        f'<div class="generation standalone-section">{boxes}</div>'
    )


def build_page_html(people, travel, collected_ids, shared_base_css, shared_css, shared_nav_js):
    folks_menu = nav.render_folks_menu(people, travel, timeline_prefix="../index.html", attendees_prefix="../attendees/")
    attending_people = [p for p in people if p.get("attending")]
    nav_row = nav.render_nav(
        mc26_href="../index.html#trip-top",
        timeline_prefix="../index.html",
        tree_href="index.html",
        trip_start=timeline_build.TRIP_START.isoformat(),
        trip_end=timeline_build.TRIP_END.isoformat(),
        jump_panel_html=timeline_build.render_jump_panel(href_prefix="../index.html"),
        folks_panel_html=folks_menu,
        attending_people=attending_people,
        attendees_prefix="../attendees/",
        include_play=False,
    )
    tree_html = build_tree_html(people, collected_ids)
    standalone_html = render_standalone_section(people, collected_ids)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{PAGE_TITLE}</title>
<style>
{shared_base_css}
{shared_css}
</style>
</head>
<body>
{nav_row}
<h1 class="tree-title">Family Tree</h1>
<p class="tree-subtitle">{TREE_SUBTITLE}</p>
{render_legend()}
<main>
{tree_html}
{standalone_html}
</main>
<script>
{shared_nav_js}
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    people = load_people()
    validate_people(people)
    travel = load_travel()
    collected_ids = collected_person_ids(travel)
    shared_base_css = (PROJECT_ROOT / "shared" / "base.css").read_text()
    shared_css = (ROOT / "shared.css").read_text()
    shared_nav_js = (PROJECT_ROOT / "shared" / "nav.js").read_text()

    html = build_page_html(people, travel, collected_ids, shared_base_css, shared_css, shared_nav_js)
    out_dir = PROJECT_ROOT / "site" / "family-tree"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html)
    print("Updated site/family-tree/index.html")


if __name__ == "__main__":
    main()
