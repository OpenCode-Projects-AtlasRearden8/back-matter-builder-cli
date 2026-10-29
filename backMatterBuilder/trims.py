"""KDP trim-size geometry: common trim sizes, margin rules, text-block math."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Trim:
    """A KDP trim size, in inches."""

    key: str
    width: float
    height: float
    note: str = ""

    @property
    def css_size(self) -> str:
        return f"{self.width:g}in {self.height:g}in"


# Common Amazon KDP paperback trims (inches).
TRIMS: dict[str, Trim] = {
    "5x8": Trim("5x8", 5, 8, "novellas, poetry"),
    "5.06x7.81": Trim("5.06x7.81", 5.06, 7.81, "128pp de facto standard"),
    "5.25x8": Trim("5.25x8", 5.25, 8, "novellas"),
    "5.5x8.5": Trim("5.5x8.5", 5.5, 8.5, "novellas"),
    "6x9": Trim("6x9", 6, 9, "US trade, general fiction/nonfiction"),
    "6.14x9.21": Trim("6.14x9.21", 6.14, 9.21, "UK A5 trade"),
    "6.69x9.61": Trim("6.69x9.61", 6.69, 9.61, "Royal UK"),
    "7x10": Trim("7x10", 7, 10, "textbooks, reports"),
    "7.44x9.69": Trim("7.44x9.69", 7.44, 9.69, "textbooks"),
    "8x10": Trim("8x10", 8, 10, "workbooks, graph-heavy"),
    "8.25x11": Trim("8.25x11", 8.25, 11, "official KDP trim"),
}

DEFAULT_TRIM = "6x9"


def get_trim(key: str) -> Trim:
    t = TRIMS.get((key or "").strip())
    if t is None:
        raise KeyError(f"unknown trim {key!r}; known trims: {', '.join(sorted(TRIMS))}")
    return t


def format_trim_name(key: str) -> str:
    """'6x9' -> '6 x 9 in'."""
    t = get_trim(key)
    return f"{t.width:g} x {t.height:g} in"


@dataclass(frozen=True)
class PageGeometry:
    """Margins and text block for one trim + page-count combination."""

    page_count: int
    width: float
    height: float
    outside: float  # head/foot/outer margin minimum
    gutter: float  # binding-edge margin

    @property
    def text_width(self) -> float:
        return self.width - self.outside - self.gutter

    @property
    def text_height(self) -> float:
        return self.height - 2 * self.outside


# KDP no-bleed minimums: outside margin by page-count band; gutter margin separately.
_OUTSIDE_BANDS = (
    (24, 0.5),
    (150, 0.25),
    (300, 0.25),
    (500, 0.5),
    (700, 0.625),
    (820, 0.75),
)

_GUTTER_BANDS = (
    (150, 0.375),
    (300, 0.5),
    (500, 0.625),
    (700, 0.75),
    (820, 0.875),
)


def _margin_for(page_count: int, bands: tuple[tuple[int, float], ...], label: str) -> float:
    if page_count < 1:
        raise ValueError("page_count must be >= 1")
    if page_count > 820:
        raise ValueError(
            "KDP paperback reflowable limit is 820 pages; split long books into two volumes"
        )
    for upper, margin in bands:
        if page_count <= upper:
            return margin
    raise AssertionError("unreachable")


def outside_margin(page_count: int) -> float:
    """KDP minimum outside margin (top/bottom/outer), inches."""
    return _margin_for(page_count, _OUTSIDE_BANDS, "outside margin")


def gutter_margin(page_count: int) -> float:
    """KDP minimum binding (gutter) margin, inches."""
    return _margin_for(page_count, _GUTTER_BANDS, "gutter margin")


def page_geometry(page_count: int, trim_key: str = DEFAULT_TRIM) -> PageGeometry:
    t = get_trim(trim_key)
    return PageGeometry(
        page_count=page_count,
        width=t.width,
        height=t.height,
        outside=outside_margin(page_count),
        gutter=gutter_margin(page_count),
    )


def margin_points(value: float) -> str:
    """Inches -> CSS points ('0.5in' -> '36pt')."""
    return f"{round(value * 72):g}pt"
