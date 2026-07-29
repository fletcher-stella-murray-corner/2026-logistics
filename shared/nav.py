"""Shared nav-bar rendering — the component used by both the timeline
feature (which doubles as the homepage) and the family-tree feature.
Not a script: no CLI, imported like a plain module.

Covers one shape only: a flat row of links with one active/current item.
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
