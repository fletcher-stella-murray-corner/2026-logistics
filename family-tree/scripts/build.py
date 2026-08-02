#!/usr/bin/env python3
"""Regenerate site/family-tree/index.html — the Family Tree feature.

Reads shared/data/people.json and renders a nested tree: each couple (or
single person) with no rendered parent yet at the top, their children
nested below them, recursively (see requirements/public.md -> Family Tree).

Validated at build time, as hard errors rather than silent typos: ids
are unique; every parent_ids/partner_id reference points at an id that
actually exists in people.json; nobody lists themselves as their own
parent or partner.

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
    ("Timeline", "index.html", False),
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


def validate_people(people):
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
            if partner_id not in people_by_id:
                raise ValueError(
                    f"{p['name']!r}'s partner_id references id {partner_id!r}, which doesn't "
                    f"exist in shared/data/people.json."
                )


def build_children_map(people):
    children_by_parent = {}
    for person in people:
        for parent_id in person.get("parent_ids") or []:
            children_by_parent.setdefault(parent_id, []).append(person)
    return children_by_parent


def render_person(person):
    return f'<span class="person">{esc(person["name"])}</span>'


def render_unit(person, people_by_id, children_by_parent, rendered_ids):
    if person["id"] in rendered_ids:
        return ""
    rendered_ids.add(person["id"])

    partner = people_by_id.get(person.get("partner_id"))
    member_ids = [person["id"]]
    couple_html = render_person(person)
    if partner is not None and partner["id"] not in rendered_ids:
        rendered_ids.add(partner["id"])
        member_ids.append(partner["id"])
        couple_html += '<span class="couple-joiner">&amp;</span>' + render_person(partner)

    kids = []
    seen_kid_ids = set()
    for member_id in member_ids:
        for kid in children_by_parent.get(member_id, []):
            if kid["id"] not in seen_kid_ids:
                seen_kid_ids.add(kid["id"])
                kids.append(kid)
    kids.sort(key=lambda p: p["id"])

    kids_html = "".join(render_unit(k, people_by_id, children_by_parent, rendered_ids) for k in kids)
    children_block = f'<div class="children">{kids_html}</div>' if kids_html else ""

    return f'<div class="family-unit"><div class="couple">{couple_html}</div>{children_block}</div>'


def build_tree_html(people):
    if not people:
        return '<p class="empty-hint">No one added to the family tree yet.</p>'

    people_by_id = {p["id"]: p for p in people}
    children_by_parent = build_children_map(people)
    min_generation = min(p.get("generation", 1) for p in people)

    roots = [p for p in people if p.get("generation", 1) == min_generation]
    roots.sort(key=lambda p: p["id"])

    rendered_ids = set()
    units_html = "".join(render_unit(r, people_by_id, children_by_parent, rendered_ids) for r in roots)

    return f'<div class="generation">{units_html}</div>'


def build_page_html(people, shared_base_css, shared_css):
    nav_row = nav.render_row(NAV_ITEMS)
    tree_html = build_tree_html(people)
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
    shared_base_css = (PROJECT_ROOT / "shared" / "base.css").read_text()
    shared_css = (ROOT / "shared.css").read_text()

    html = build_page_html(people, shared_base_css, shared_css)
    out_dir = PROJECT_ROOT / "site" / "family-tree"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html)
    print("Updated site/family-tree/index.html")


if __name__ == "__main__":
    main()
