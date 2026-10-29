"""Render back-matter pages to print-ready HTML or shared Markdown."""

from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

from . import trims
from .profile import Profile
from .sections import Page
from .trims import Trim


def _md_inline(text: str) -> str:
    """Very small inline markdown subset: **bold**, links, em dashes stay as-is."""
    text = html_mod.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{html_mod.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        text,
    )
    return text


def _md_blocks(body: str) -> list[str]:
    """Split markdown body into html-ish blocks: paragraphs vs bullet lists."""
    blocks: list[str] = []
    para: list[str] = []
    bullets: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("- "):
            if para:
                blocks.append(" ".join(para))
                para = []
            bullets.append(s[2:])
        elif not s:
            if para:
                blocks.append(" ".join(para))
                para = []
            if bullets:
                blocks.append("\n".join(f"<li>{_md_inline(b)}</li>" for b in bullets))
                bullets = []
        else:
            if bullets:
                blocks.append("\n".join(f"<li>{_md_inline(b)}</li>" for b in bullets))
                bullets = []
            para.append(s)
    if bullets:
        blocks.append("\n".join(f"<li>{_md_inline(b)}</li>" for b in bullets))
    if para:
        blocks.append(" ".join(para))
    return blocks


_HTML_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Back Matter</title>
<!--
  backMatterBuilder print sheet
  trim: {trim_name} ({trim_key})
  margins for ~{page_count} pages: gutter {gutter_in}in, outside {outside_in}in
  (KDP no-bleed minimums; set your page count before final print PDF)
-->
<style>
  @page {{
    size: {css_size};
    margin: {margin_css};
  }}
  html, body {{
    margin: 0;
    padding: 0;
    background: #fff;
  }}
  body {{
    font-family: Georgia, 'Iowan Old Style', 'Times New Roman', serif;
    font-size: {base_pt}pt;
    line-height: 1.45;
    color: #111;
    text-align: center;
  }}
  section.page {{
    page-break-after: always;
    break-after: page;
  }}
  section.page:last-child {{
    page-break-after: auto;
    break-after: auto;
  }}
  section.page h1 {{
    font-size: {head_pt}pt;
    font-weight: normal;
    letter-spacing: 0.06em;
    margin: 0 0 1.2em;
    text-transform: uppercase;
  }}
  section.page p {{
    margin: 0 0 0.9em;
  }}
  section.page ul {{
    list-style: none;
    padding: 0;
    margin: 0.6em 0 1.2em;
    text-align: center;
  }}
  section.page li {{
    margin: 0 0 0.45em;
  }}
  a {{
    color: inherit;
    text-decoration: none;
  }}
  .copyright p {{
    max-width: 34em;
    margin-left: auto;
    margin-right: auto;
  }}
  .kind {{
    font-size: 0.4em;
    color: #999; /* remove in final typeset; marks the page kind */
  }}
</style>
</head>
<body>
{pages}
</body>
</html>
"""

_PAGE_TMPL = """<section class="page {kind}" id="{id}">
  <h1>{title}</h1>
  <span class="kind">[{kind}]</span>
{blocks}
</section>
"""


def render_html(
    pages: list[Page],
    profile: Profile,
    trim_key: str | None = None,
) -> str:
    key = (trim_key or profile.trim or trims.DEFAULT_TRIM).strip()
    trim: Trim = trims.get_trim(key)
    geo = trims.page_geometry(profile.page_count, key)
    css = (
        f"{trims.margin_points(geo.outside)} {trims.margin_points(geo.gutter)} "
        f"{trims.margin_points(geo.outside)} {trims.margin_points(geo.outside)}"
    )
    base_pt = 11 if trim.height <= 8 else 12
    head_pt = base_pt + 3

    rendered: list[str] = []
    for i, page in enumerate(pages, start=1):
        html_blocks = []
        for block in _md_blocks(page.body):
            if block.startswith("<li>"):
                html_blocks.append("<ul>\n" + block + "\n</ul>")
            else:
                html_blocks.append(f"<p>{_md_inline(block)}</p>")
        body = "\n".join(html_blocks) or "<p></p>"
        rendered.append(
            _PAGE_TMPL.format(
                kind=html_mod.escape(page.kind, quote=True),
                id=f"page-{i:02d}",
                title=_md_inline(page.title),
                blocks=body,
            )
        )
    return _HTML_TMPL.format(
        title=_md_inline(profile.title),
        trim_key=trim.key,
        trim_name=trims.format_trim_name(trim.key),
        page_count=profile.page_count,
        gutter_in=f"{geo.gutter:g}",
        outside_in=f"{geo.outside:g}",
        css_size=trim.css_size,
        margin_css=css,
        base_pt=base_pt,
        head_pt=head_pt,
        pages="\n".join(rendered),
    )


def render_markdown(pages: list[Page], profile: Profile) -> str:
    lines: list[str] = [
        f"<!-- Back matter for {profile.title} by {profile.author} "
        f"(backMatterBuilder) -->",
        "",
        f"# {profile.title} - Back Matter",
        "",
    ]
    for i, page in enumerate(pages, start=1):
        if i > 1:
            lines += ["", "---", ""]
        lines += [f"## {page.title}", ""]
        lines += [page.body.rstrip()]
        links = [(t, u) for t, u in page.links if u]
        if any(u not in page.body for _, u in links):
            shown = [t for t, u in links if f"({u})" not in page.body]
            if shown:
                lines += [""]
                lines += [f"- {t}: {u}" for t in shown]
    return "\n".join(lines).rstrip() + "\n"


def write_output(html_str: str, md_str: str, html_path: str, md_path: str | None = None) -> None:
    Path(html_path).write_text(html_str, encoding="utf-8")
    if md_path:
        Path(md_path).write_text(md_str, encoding="utf-8")
