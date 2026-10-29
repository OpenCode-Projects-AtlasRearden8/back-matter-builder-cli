from __future__ import annotations

import re

from backMatterBuilder import render, sections, trims


def test_html_page_sized_for_trim(profile_full):
    html = render.render_html(sections.build_pages(profile_full), profile_full)
    t = trims.get_trim("6x9")
    assert f"@page {{\n    size: {t.css_size};" in html
    assert "page-break-after" in html
    assert html.count('<section class="page') == len(sections.build_pages(profile_full))


def test_html_margins_follow_page_count(profile_full):
    geo = trims.page_geometry(200, "6x9")
    html = render.render_html(sections.build_pages(profile_full), profile_full)
    assert f"margin: {trims.margin_points(geo.outside)}" in html


def test_html_trim_override(profile_full):
    html = render.render_html(sections.build_pages(profile_full), profile_full, "5.5x8.5")
    assert "size: 5.5in 8.5in;" in html


def test_markdown_headings_and_links(profile_full):
    md = render.render_markdown(sections.build_pages(profile_full), profile_full)
    assert md.startswith("<!-- Back matter for The Massive AI Manual")
    assert "# The Massive AI Manual - Back Matter" in md
    assert "## Notes" in md
    assert "(https://dylanasdale.github.io/newsletter)" in md
    assert "md.split" not in md


def test_markdown_separators(profile_full):
    md = render.render_markdown(sections.build_pages(profile_full), profile_full)
    assert md.count("\n---\n") == len(sections.build_pages(profile_full)) - 1


def test_markdown_link_card(profile_full):
    pages = sections.build_pages(profile_full)
    md = render.render_markdown(pages, profile_full)
    assert re.search(r"Join the Newsletter link", md)
