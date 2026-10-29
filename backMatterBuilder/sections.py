"""Build back-matter pages from a validated profile.

Pages are produced in print order:
  endnotes (if placement is 'first'), copyright, also-by, series,
  review ask, newsletter, about-the-author, endnotes (if 'last').

Each Page holds a title, kind, and a body of Markdown text plus optional
plain-text links; the renderers turn that into HTML or Markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .profile import Profile


@dataclass
class Page:
    kind: str  # 'copyright' | 'endnotes' | 'also_by' | 'series' | 'review_ask' | 'newsletter' | 'about'
    title: str
    body: str = ""  # markdown body
    links: list[tuple[str, str]] = field(default_factory=list)  # (text, url)


def build_pages(profile: Profile) -> list[Page]:
    pages: list[Page] = []

    if profile.endnotes_placement == "first":
        pages.extend(_endnotes_pages(profile))

    pages.extend(_copyright_page(profile))
    pages.extend(_also_by_page(profile))
    pages.extend(_series_page(profile))
    pages.extend(_review_ask_page(profile))
    pages.extend(_newsletter_page(profile))
    pages.extend(_about_page(profile))

    if profile.endnotes_placement == "last":
        pages.extend(_endnotes_pages(profile))

    return pages


def _endnotes_pages(profile: Profile) -> list[Page]:
    if not profile.endnotes.text.strip() or profile.endnotes_placement == "omit":
        return []
    return [Page("endnotes", profile.endnotes.heading, profile.endnotes.text)]


def _copyright_page(profile: Profile) -> list[Page]:
    lines = [f"{profile.title}", f"by {profile.author}", "", profile.copyright_notice]
    if profile.publisher:
        lines += [f"Published by {profile.publisher}"]
    if profile.edition:
        lines += [profile.edition]
    if profile.isbn.strip("-"):
        lines += [f"ISBN {profile.isbn}"]
    lines += ["", "All rights reserved. No part of this book may be reproduced in any form"]
    lines += ["or by any electronic or mechanical means, including information storage"]
    lines += ["and retrieval systems, without written permission from the author,"]
    lines += ["except by a reviewer who may quote brief passages in a review."]
    lines += ["", f"First published in {profile.year}."]
    if profile.copyright_.extras:
        lines += [""]
        lines += [line for line in profile.copyright_.extras if line.strip()]
    cover_owner = "Asdale Dynamics, LLC" if profile.publisher == "Asdale Dynamics, LLC" else ""
    if cover_owner:
        lines += [f"Cover and interior design by {cover_owner}."]
    return [Page("copyright", "Copyright", "\n".join(lines))]


def _also_by_page(profile: Profile) -> list[Page]:
    books = [b for b in profile.also_by.books if str(b).strip()]
    if not books:
        return []
    heading = profile.also_by.heading or f"Also by {profile.author}"
    items = [f"- {b.strip()}" for b in books]
    body = "\n".join(items)
    return [Page("also_by", heading, body)]


def _series_page(profile: Profile) -> list[Page]:
    s = profile.series
    if not s.name.strip() and not s.books:
        return []
    heading = s.name.strip() or "The Series"
    lines: list[str] = [f"**{heading}**"]
    if s.blurb:
        lines.append(s.blurb)
    if s.books:
        lines.append("")
        for b in s.books:
            b = str(b).strip()
            if b == s.this_book:
                lines.append(f"- **{b}** ← this book")
            else:
                lines.append(f"- {b}")
    page_links: list[tuple[str, str]] = []
    if s.url:
        lines.append("")
        lines.append(f"[{heading} series page]({s.url})")
        page_links = [(f"{heading} series page", s.url)]
    return [Page("series", heading, "\n".join(lines), links=page_links)]


def _review_ask_page(profile: Profile) -> list[Page]:
    if not profile.review_ask.text.strip():
        return []
    heading = profile.review_ask.heading
    text = profile.review_ask.text
    return [Page("review_ask", heading, text)]


def _newsletter_page(profile: Profile) -> list[Page]:
    n = profile.newsletter
    if not n.url.strip() and not n.blurb.strip():
        return []
    heading = n.heading
    lines = [n.blurb.strip()] if n.blurb.strip() else []
    if n.url.strip():
        lines += ["", f"[{heading} link]({n.url.strip()})"]
    return [Page("newsletter", heading, "\n".join(lines), links=[(heading, n.url.strip())])]


def _about_page(profile: Profile) -> list[Page]:
    if not profile.about_author.text.strip():
        return []
    heading = profile.about_author.heading
    return [Page("about", heading, profile.about_author.text)]


def default_review_text() -> str:
    return (
        "If this book helped you understand something you thought was out of reach, "
        "please take a minute to leave an honest review wherever you bought it. "
        "Reviews are how other beginners find books like this one, and every one "
        "genuinely helps."
    )
