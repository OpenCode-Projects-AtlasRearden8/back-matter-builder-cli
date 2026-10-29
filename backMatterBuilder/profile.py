"""Profile loading, defaults, and validation for back-matter profiles.

Profiles may be JSON (.json) or TOML (.toml). Example TOML:

    title = "The Massive AI Manual"
    author = "Dylan Asdale"
    year = 2026

    [review_ask]
    text = "Reviews help other beginners find books like this one."
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


class ProfileError(ValueError):
    """Raised when a profile file is missing required fields or has bad values."""


@dataclass
class ReviewAsk:
    heading: str = "Leave a Review"
    text: str = ""


@dataclass
class NewsletterLink:
    heading: str = "Join the Newsletter"
    url: str = ""
    blurb: str = ""


@dataclass
class AlsoBy:
    heading: str = ""
    books: list[str] = field(default_factory=list)


@dataclass
class SeriesBlock:
    name: str = ""
    this_book: str = ""
    books: list[str] = field(default_factory=list)
    blurb: str = ""
    url: str = ""


@dataclass
class CopyrightBlock:
    extras: list[str] = field(default_factory=list)


@dataclass
class AboutAuthor:
    heading: str = "About the Author"
    text: str = ""


@dataclass
class EndnotesBlock:
    heading: str = "Notes"
    text: str = ""


@dataclass
class Profile:
    title: str
    author: str
    year: int
    publisher: str = ""
    isbn: str = ""
    edition: str = ""
    series_no: str = ""
    trim: str = "6x9"
    page_count: int = 200
    copyright_: CopyrightBlock = field(default_factory=CopyrightBlock)
    also_by: AlsoBy = field(default_factory=AlsoBy)
    series: SeriesBlock = field(default_factory=SeriesBlock)
    review_ask: ReviewAsk = field(default_factory=ReviewAsk)
    newsletter: NewsletterLink = field(default_factory=NewsletterLink)
    about_author: AboutAuthor = field(default_factory=AboutAuthor)
    endnotes: EndnotesBlock = field(default_factory=EndnotesBlock)
    endnotes_placement: str = "first"
    rewrite: dict = field(default_factory=dict)
    source_path: str = ""

    @property
    def copyright_notice(self) -> str:
        return f"Copyright (c) {self.year} {self.author}. All rights reserved."


_R = {
    "enabled": False,
    "base_url": "http://localhost:11434/v1",
    "model": "llama3.2",
    "temperature": 0.4,
    "timeout": 60,
    "sections": ["review_ask", "newsletter", "about", "endnotes"],
}

_REWRITE_KEYS = set(_R)
_REWRITE_URL = re.compile(r"https?://[^\s\"')>\]]+", re.IGNORECASE)


def _section(raw: dict, name: str, defaults: dict) -> dict:
    val = raw.get(name, {})
    if val is None:
        val = {}
    if not isinstance(val, dict):
        raise ProfileError(f"'{name}' must be a table/object, not {type(val).__name__}")
    merged = dict(defaults)
    unknown = set(val) - set(defaults)
    if unknown:
        raise ProfileError(f"unknown '{name}' keys: {', '.join(sorted(unknown))}")
    merged.update(val)
    return merged


_ALSO_BY_DEFAULTS = {"heading": "", "books": []}
_SERIES_DEFAULTS = {"name": "", "this_book": "", "books": [], "blurb": "", "url": ""}
_REVIEW_DEFAULTS = {
    "heading": "Leave a Review",
    "text": "",
}

_NEWSLETTER_DEFAULTS = {"heading": "Join the Newsletter", "url": "", "blurb": ""}

_COPYRIGHT_DEFAULTS = {"extras": []}

_ABOUT_DEFAULTS = {"heading": "About the Author", "text": ""}

_ENDNOTES_DEFAULTS = {"heading": "Notes", "text": ""}

_PLACEMENTS = ("first", "last", "omit")


def _check_links(raw: dict) -> None:
    for name in ("series", "newsletter"):
        section = raw.get(name) or {}
        if isinstance(section, dict) and section.get("url"):
            _validate_url(section["url"], name)


def _validate_url(url: str, where: str) -> None:
    if not _REWRITE_URL.fullmatch(url):
        raise ProfileError(f"{where}.url looks malformed: {url!r} (expect https://...)")


def load_profile(path: str | Path) -> Profile:
    path = Path(path)
    if not path.exists():
        raise ProfileError(f"profile file not found: {path}")
    raw = _parse(path)
    return _from_dict(raw, source_path=str(path))


def _parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".toml":
            return tomllib.loads(text)
        return json.loads(text)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ProfileError(f"could not parse {path}: {exc}") from exc


def _from_dict(raw: dict, source_path: str = "") -> Profile:
    if not isinstance(raw, dict):
        raise ProfileError("profile must be a JSON object / TOML table")
    _check_links(raw)
    for required in ("title", "author", "year"):
        if not raw.get(required):
            raise ProfileError(f"profile is missing required field '{required}'")
    year = raw["year"]
    if not isinstance(year, int) or isinstance(year, bool):
        raise ProfileError("'year' must be an integer")
    trim = raw.get("trim", "6x9")
    placement = raw.get("endnotes_placement", "first")
    if placement not in _PLACEMENTS:
        raise ProfileError(
            f"endnotes_placement must be one of {', '.join(_PLACEMENTS)} (got {placement!r})"
        )
    page_count = raw.get("page_count", 200)
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        raise ProfileError("'page_count' must be a positive integer")
    rewrite_raw = raw.get("rewrite") or {}
    if not isinstance(rewrite_raw, dict):
        raise ProfileError("'rewrite' must be a table/object")
    unknown = set(rewrite_raw) - _REWRITE_KEYS
    if unknown:
        raise ProfileError(f"unknown 'rewrite' keys: {', '.join(sorted(unknown))}")
    rewrite = dict(_R)
    base_url = rewrite_raw.get("base_url")
    if base_url:
        _validate_url(base_url, "rewrite")
        rewrite["base_url"] = str(base_url).rstrip("/")
    for k in ("model", "enabled"):
        if k in rewrite_raw:
            rewrite[k] = rewrite_raw[k]
    if "temperature" in rewrite_raw:
        t = rewrite_raw["temperature"]
        if not isinstance(t, (int, float)) or isinstance(t, bool) or not 0 <= t <= 2:
            raise ProfileError("rewrite.temperature must be a number between 0 and 2")
        rewrite["temperature"] = t
    if "timeout" in rewrite_raw:
        to = rewrite_raw["timeout"]
        if not isinstance(to, (int, float)) or isinstance(to, bool) or to <= 0:
            raise ProfileError("rewrite.timeout must be a positive number of seconds")
        rewrite["timeout"] = to
    if "sections" in rewrite_raw:
        secs = rewrite_raw["sections"]
        allowed = {"review_ask", "newsletter", "about", "endnotes"}
        if not isinstance(secs, list) or not set(secs) <= allowed:
            raise ProfileError(f"rewrite.sections must be a list drawn from: {sorted(allowed)}")
        rewrite["sections"] = secs

    isbn = str(raw.get("isbn", "") or "").replace("-", "").strip()

    return Profile(
        title=str(raw["title"]).strip(),
        author=str(raw["author"]).strip(),
        year=year,
        publisher=str(raw.get("publisher", "") or "").strip(),
        isbn=isbn,
        edition=str(raw.get("edition", "") or "").strip(),
        series_no=str(raw.get("series_no", "") or "").strip(),
        trim=str(trim),
        page_count=page_count,
        copyright_=CopyrightBlock(**_section(raw, "copyright", _COPYRIGHT_DEFAULTS)),
        also_by=AlsoBy(**_section(raw, "also_by", _ALSO_BY_DEFAULTS)),
        series=SeriesBlock(**_section(raw, "series", _SERIES_DEFAULTS)),
        review_ask=ReviewAsk(**_section(raw, "review_ask", _REVIEW_DEFAULTS)),
        newsletter=NewsletterLink(**_section(raw, "newsletter", _NEWSLETTER_DEFAULTS)),
        about_author=AboutAuthor(**_section(raw, "about", _ABOUT_DEFAULTS)),
        endnotes=EndnotesBlock(**_section(raw, "endnotes", _ENDNOTES_DEFAULTS)),
        endnotes_placement=placement,
        rewrite=rewrite,
        source_path=source_path,
    )


def load_profile_from_dict(raw: dict) -> Profile:
    return _from_dict(raw)
