"""Shared nav helpers, imported by every feature's build.py.
Not a script: no CLI, imported like a plain module.

esc() is used by every feature for HTML-escaping. render_row() — a flat
nav row of links with one active/current item — is used by
family-tree/scripts/build.py and facts/scripts/build.py; the timeline
feature builds its own richer nav (live label, jump-to-time,
jump-to-person, play/pause auto-advance, working Tree/Facts links)
directly in timeline/scripts/build.py's render_nav(), since
render_row()'s flat link-row shape doesn't fit it.
"""


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


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
