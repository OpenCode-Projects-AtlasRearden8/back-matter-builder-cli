from __future__ import annotations

import pytest

from backMatterBuilder.profile import ProfileError, load_profile, load_profile_from_dict
from backMatterBuilder import trims


def test_load_json_profile(profile_full):
    assert profile_full.title == "The Massive AI Manual"
    assert profile_full.author == "Dylan Asdale"
    assert profile_full.year == 2026
    assert profile_full.series.this_book.startswith("Book 1")
    assert profile_full.endnotes_placement == "first"


def test_load_toml_profile(fixture_dir):
    p = load_profile(fixture_dir / "profile_full.toml")
    assert p.page_count == 300
    assert p.series.url == "https://dylanasdale.github.io"
    assert p.endnotes_placement == "last"


def test_minimal_profile_defaults(profile_minimal):
    p = profile_minimal
    assert p.trim == trims.DEFAULT_TRIM
    assert p.page_count == 200
    assert p.also_by.books == []
    assert p.rewrite["base_url"] == "http://localhost:11434/v1"


def test_missing_required_field(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"title": "No Author"}')
    with pytest.raises(ProfileError):
        load_profile(path)


def test_unparseable_profile(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    with pytest.raises(ProfileError):
        load_profile(path)


def test_missing_file(tmp_path):
    with pytest.raises(ProfileError):
        load_profile(tmp_path / "nope.json")


def test_bad_url_rejected():
    base = {
        "title": "T",
        "author": "A",
        "year": 2026,
        "newsletter": {"url": "not a url"},
    }
    with pytest.raises(ProfileError):
        load_profile_from_dict(base)


def test_endnotes_placement_validation():
    base = {"title": "T", "author": "A", "year": 2026, "endnotes_placement": "middle"}
    with pytest.raises(ProfileError):
        load_profile_from_dict(base)


def test_rewrite_validation():
    with pytest.raises(ProfileError) as exc:
        load_profile_from_dict(
            {"title": "T", "author": "A", "year": 2026, "rewrite": {"nope": 1}}
        )
    assert "rewrite" in str(exc.value)
    with pytest.raises(ProfileError):
        load_profile_from_dict(
            {"title": "T", "author": "A", "year": 2026, "rewrite": {"temperature": 9}}
        )


def test_copyright_notice(profile_full):
    assert profile_full.copyright_notice == (
        "Copyright (c) 2026 Dylan Asdale. All rights reserved."
    )
