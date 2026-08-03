"""Shared nav helpers, imported by every feature's build.py.
Not a script: no CLI, imported like a plain module.

esc() is used by every feature for HTML-escaping. require() is used by
every feature to validate a required field on a hand-edited JSON record
with a friendly message (record + missing field) instead of a raw
KeyError traceback. render_row() — a flat nav row of links with one
active/current item — is used by family-tree/scripts/build.py and
attendees/scripts/build.py; the timeline feature builds its own richer
nav (live label, jump-to-time, jump-to-person, play/pause auto-advance,
working Tree/Attendees links) directly in timeline/scripts/build.py's
render_nav(), since render_row()'s flat link-row shape doesn't fit it.
"""


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def require(record, field, label):
    """Return record[field], or raise a friendly ValueError naming `label`
    (a human description of which record, e.g. "Person at index 3 (id 7)
    in shared/data/people.json") instead of letting a bare KeyError from
    record[field] surface as a raw traceback during hand-edited data entry."""
    if field not in record:
        raise ValueError(f"{label} is missing required field {field!r}.")
    return record[field]


def render_row(items):
    """Render one flat nav row.

    items: list of (label, href, is_active) tuples.
      - is_active True  -> <strong class="active"> — current page, non-linking.
      - is_active False -> <a href="..."> — a normal link.
    """
    parts = []
    for label, href, is_active in items:
        if is_active:
            parts.append(f'<strong class="active">{esc(label)}</strong>')
        else:
            parts.append(f'<a href="{href}">{esc(label)}</a>')
    return '<nav class="site-nav">' + ''.join(parts) + '</nav>'
