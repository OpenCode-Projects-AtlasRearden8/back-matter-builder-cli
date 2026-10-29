from __future__ import annotations

from backMatterBuilder.profile import load_profile_from_dict
from backMatterBuilder.sections import build_pages

MIN = {"title": "T", "author": "A", "year": 2026}


def test_section_print_order(profile_full):
    pages = build_pages(profile_full)
    kinds = [p.kind for p in pages]
    # endnotes first, then everything else in print order
    assert kinds == [
        "endnotes",
        "copyright",
        "also_by",
        "series",
        "review_ask",
        "newsletter",
        "about",
    ]


def test_endnotes_placement_last():
    p = load_profile_from_dict(
        {**MIN, "endnotes": {"heading": "Notes", "text": "1. note"}, "endnotes_placement": "last"}
    )
    kinds = [pg.kind for pg in build_pages(p)]
    assert kinds[0] == "copyright" and kinds[-1] == "endnotes"


def test_endnotes_omitted_when_no_text():
    kinds = [pg.kind for pg in build_pages(load_profile_from_dict(MIN))]
    assert "endnotes" not in kinds


def test_endnotes_placement_omit():
    p = load_profile_from_dict(
        {**MIN, "endnotes": {"text": "1. note"}, "endnotes_placement": "omit"}
    )
    assert all(pg.kind != "endnotes" for pg in build_pages(p))


def test_empty_sections_are_dropped():
    pages = build_pages(load_profile_from_dict(MIN))
    kinds = [pg.kind for pg in pages]
    assert kinds == ["copyright"]


def test_copyright_page_content(profile_full):
    page = next(pg for pg in build_pages(profile_full) if pg.kind == "copyright")
    assert "The Massive AI Manual" in page.body
    assert "Copyright (c) 2026 Dylan Asdale" in page.body
    assert "ISBN" not in page.body or "978" in page.body


def test_also_by_heading_defaults_to_author():
    p = load_profile_from_dict({**MIN, "also_by": {"books": ["Other Book"]}})
    page = next(pg for pg in build_pages(p) if pg.kind == "also_by")
    assert page.title == "Also by A"
    assert "- Other Book" in page.body


def test_series_this_book_marked(profile_full):
    page = next(pg for pg in build_pages(profile_full) if pg.kind == "series")
    assert "← this book" in page.body
    links = dict(page.links)
    assert links and "dylanasdale" in list(links.values())[0]


def test_newsletter_links(profile_full):
    page = next(pg for pg in build_pages(profile_full) if pg.kind == "newsletter")
    text, url = page.links[0]
    assert url == "https://dylanasdale.github.io/newsletter"


def test_minimal_profile_only_copyright():
    pages = build_pages(load_profile_from_dict(MIN))
    assert [pg.kind for pg in pages] == ["copyright"]
    assert "Copyright (c) 2026 A" in pages[0].body
