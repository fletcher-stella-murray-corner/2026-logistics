#!/usr/bin/env python3
"""Regenerate site/family-tree/index.html — the Family Tree feature.

Reads shared/data/people.json and renders a nested tree: each couple (or
single person) with no rendered parent yet at the top, their children
nested below them, recursively (see requirements/public.md -> Family Tree).
Also reads timeline/data/travel.json (read-only, same as the Attendees
feature) purely to compute each attending person's facts-collected/
collecting-facts status for the box's visual treatment — see
render_person() below and requirements/public.md -> Family Tree -> Layout.
This is also the sole entry point to the Attendees feature: an attending
person's box is a link straight to their site/attendees/<id>.html page
(the Attendees feature has no index page or nav link of its own — see
attendees/scripts/build.py); a not-attending person's box stays plain
text, since they have no such page to link to.

Validated at build time, as hard errors rather than silent typos: every
person has an 'id' (int), 'name' (non-empty string), and 'generation'
(int); every timeline/data/travel.json record has a 'person_id'; ids are
unique; parent_ids has at most 2 entries; every parent_ids/partner_id
reference points at an id that actually exists in people.json; nobody
lists themselves as their own parent or partner; a set partner_id is
reciprocated (if A's partner_id is B, B's partner_id must be A); nobody
has both married_in: true and a non-empty parent_ids (a contradiction —
see requirements/public.md -> people.json); and, after the tree is
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

PAGE_TITLE = "Family Tree — Murray Corner 2026"
TREE_SUBTITLE = "Where everyone fits"

NAV_ITEMS = [
    ("Timeline", "../index.html", False),
    ("Tree", None, True),
]


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
        generation = nav.require(p, "generation", label)
        if not isinstance(generation, int):
            raise ValueError(f"{label} has a non-integer generation {generation!r} — generation must be an integer.")
        parent_ids = p.get("parent_ids") or []
        if len(parent_ids) > 2:
            raise ValueError(f"{name!r} has {len(parent_ids)} parent_ids — a person can have at most 2.")


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


def build_children_map(people):
    children_by_parent = {}
    for person in people:
        for parent_id in person.get("parent_ids") or []:
            children_by_parent.setdefault(parent_id, []).append(person)
    return children_by_parent


def person_status(person, collected_ids):
    """The same states the Attendees feature computes (see
    requirements/public.md -> Attendees -> The three states), reused here
    for the Family Tree box's visual treatment — not attending, collecting
    facts (attending, no travel.json entry yet or the entry is marked
    "pending": true), or facts collected (attending, has a non-pending
    entry — the default box, nothing extra shown)."""
    if not person.get("attending"):
        return "not-attending"
    if person["id"] in collected_ids:
        return "collected"
    return "needed"


def render_person(person, collected_ids):
    status = person_status(person, collected_ids)
    classes = ["person"]
    captions = []
    if person.get("married_in"):
        classes.append("married-in")
        captions.append("Married in")
    if status == "needed":
        classes.append("status-needed")
        captions.append("Collecting facts")
    elif status == "not-attending":
        classes.append("status-not-attending")
        captions.append("Not attending")
    caption_html = f'<span class="person-status">{esc(" · ".join(captions))}</span>' if captions else ""
    inner = f'<span class="person-name">{esc(person["name"])}</span>{caption_html}'

    # Attending people link straight to their own Attendees page — the
    # sole entry point to that feature (see module docstring). Not
    # attending means no such page exists, so stays plain text.
    if person.get("attending"):
        tag, extra = "a", f' href="../attendees/{person["id"]}.html"'
    else:
        tag, extra = "span", ""
    return f'<{tag} class="{" ".join(classes)}"{extra}>{inner}</{tag}>'


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
    kids.sort(key=lambda p: p["id"])

    kids_html = "".join(
        render_unit(k, people_by_id, children_by_parent, rendered_ids, collected_ids) for k in kids
    )
    children_block = f'<div class="children">{kids_html}</div>' if kids_html else ""

    return f'<div class="family-unit"><div class="couple">{couple_html}</div>{children_block}</div>'


def build_tree_html(people, collected_ids):
    if not people:
        return '<p class="empty-hint">No one added to the family tree yet.</p>'

    people_by_id = {p["id"]: p for p in people}
    children_by_parent = build_children_map(people)
    min_generation = min(p.get("generation", 1) for p in people)

    roots = [p for p in people if p.get("generation", 1) == min_generation]
    roots.sort(key=lambda p: p["id"])

    rendered_ids = set()
    units_html = "".join(
        render_unit(r, people_by_id, children_by_parent, rendered_ids, collected_ids) for r in roots
    )

    missing = [p for p in people if p["id"] not in rendered_ids]
    if missing:
        missing.sort(key=lambda p: p["id"])
        names = ", ".join(f"{p['name']!r} (id {p['id']})" for p in missing)
        raise ValueError(
            f"The following people are never reached from a generation-{min_generation} "
            f"root and would silently be missing from the Family Tree page: {names}. "
            f"Check their generation and parent_ids — every non-root person needs a "
            f"parent_ids chain that eventually leads back to a root."
        )

    return f'<div class="generation">{units_html}</div>'


def build_page_html(people, collected_ids, shared_base_css, shared_css):
    nav_row = nav.render_row(NAV_ITEMS)
    tree_html = build_tree_html(people, collected_ids)
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
<main>
{tree_html}
</main>
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

    html = build_page_html(people, collected_ids, shared_base_css, shared_css)
    out_dir = PROJECT_ROOT / "site" / "family-tree"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html)
    print("Updated site/family-tree/index.html")


if __name__ == "__main__":
    main()
