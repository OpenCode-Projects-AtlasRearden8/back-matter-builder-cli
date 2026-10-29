from __future__ import annotations

import pytest

from backMatterBuilder import trims


def test_default_trim_is_kdp_trade():
    assert trims.DEFAULT_TRIM == "6x9"


def test_get_trim_dimensions():
    t = trims.get_trim("5.5x8.5")
    assert (t.width, t.height) == (5.5, 8.5)
    assert t.css_size == "5.5in 8.5in"


def test_unknown_trim_raises():
    with pytest.raises(KeyError):
        trims.get_trim("13x19")


def test_gutter_bands_match_kdp_rules():
    assert trims.gutter_margin(24) == 0.375
    assert trims.gutter_margin(150) == 0.375
    assert trims.gutter_margin(151) == 0.5
    assert trims.gutter_margin(300) == 0.5
    assert trims.gutter_margin(301) == 0.625
    assert trims.gutter_margin(500) == 0.625
    assert trims.gutter_margin(700) == 0.75
    assert trims.gutter_margin(820) == 0.875


def test_outside_bands_match_kdp_rules():
    assert trims.outside_margin(10) == 0.5
    assert trims.outside_margin(100) == 0.25
    assert trims.outside_margin(400) == 0.5
    assert trims.outside_margin(600) == 0.625
    assert trims.outside_margin(800) == 0.75


def test_geometry_text_block():
    geo = trims.page_geometry(200, "6x9")
    assert geo.width == 6
    assert 0 < geo.text_width < 6
    assert 0 < geo.text_height < 9
    both = trims.page_geometry(800, "8x10")
    assert both.gutter == 0.875 and both.outside == 0.75
    assert both.text_width == 8 - 0.875 - 0.75


def test_over_limit_fails():
    with pytest.raises(ValueError):
        trims.page_geometry(900)
    with pytest.raises(ValueError):
        trims.page_geometry(0)
